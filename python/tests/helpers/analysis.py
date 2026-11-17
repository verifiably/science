"""Synthetic measurement and authoring inputs; never production defaults.

The fixture compares protein abundance between rule-defined early/late classes,
with synthetic causal identification and a probability-of-superiority target.
The outcome-file rule interprets a verdict; it does not pretend to estimate it.
"""
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path

from nodes.core.node import Node
from beliefs import stored
from beliefs.classification_rule import ClassificationRule
from beliefs.measurement import Observable, Measure, measure_projection
from beliefs.procedure import Procedure, Scale
from beliefs.profile import ProfileSpec
from beliefs.root import open_corpus
from science.config import ScienceConfig

__all__ = ["analysis_nodes", "bootstrap_analysis", "write_estimand_document", "spec_inputs", "refreeze_spec"]


def _namespace(profile: ProfileSpec) -> str:
    return next(term.rsplit("/", 1)[0] for term in profile.sorts if term.endswith("/protein"))


def analysis_nodes(profile: ProfileSpec) -> tuple[Node, ...]:
    ns = _namespace(profile)
    observable = Observable("general/relative-abundance", f"{ns}/protein")
    assay = Procedure("general/assay", "Fixture assay", "Measure synthetic protein abundance.",
                      (observable,), Scale(Fraction(0), Fraction(1), "higher-is-more"), {}, (), (), None, None, {}, None)
    classes = ClassificationRule(f"{ns}/level", (observable,),
                                 "Assign synthetic early and late classes.", None, None, "fixture")
    estimator = Procedure("general/estimator", "Fixture verdict reader",
                          "Read the explicit outcome-file verdict without estimating a statistic.",
                          (), None, {}, (), (), None, None, {}, None)
    nodes = (stored.procedure_node(assay), stored.classification_rule_node(classes),
             stored.procedure_node(estimator))
    # A pure fixture source must produce equal copies across independent corpora.
    return tuple(node.model_copy(update={"uid": node.id.partition(":")[2][:32]}) for node in nodes)


def bootstrap_analysis(cfg: ScienceConfig) -> None:
    from helpers.world import FIXTURE_AUTHORITY
    writer = open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile)
    for node in analysis_nodes(cfg.profile):
        writer.add(node)


def write_estimand_document(cfg: ScienceConfig, *, reference: Decimal = Decimal("0.5")) -> Path:
    if type(reference) is not Decimal or not reference.is_finite():
        raise ValueError("fixture reference must be a finite Decimal")
    ns = _namespace(cfg.profile)
    assay, classes, _ = analysis_nodes(cfg.profile)
    measure = Measure(Observable("general/relative-abundance", f"{ns}/protein"), None, assay.id,
                      "ratio", "level", "general/identity", assay.id)
    document = {
        "schema_version": 1, "form": "contrast", "functional": "general/probability-of-superiority",
        "bindings": {
            "response": {"role": "response", "measure": measure_projection(measure)},
            "grouping": {"source": "rule-classes", "rule": classes.id,
                         "classes": [{"sort": f"{ns}/level", "term": term}
                                     for term in ("level:early", "level:late")]},
        },
        "outputs": {"estimate": {"typing": "dimensionless", "domain": "unit-interval"}},
        "reference": {"kind": "value", "value": "EXACT_DECIMAL"},
        "control": {"identification": f"{ns}/randomized", "conditioning": [],
                    "design": "general/independent-groups", "selection": "general/cohort-enrolment"},
        "uncertainty": "interval", "assumptions": [],
    }
    path = cfg.world.world_root.parent / "estimand.json"
    path.write_text(json.dumps(document, indent=2).replace('"EXACT_DECIMAL"', str(reference)) + "\n")
    return path


def spec_inputs(cfg: ScienceConfig, *, target: str, dataset: str, **overrides) -> dict:
    """One explicit native fixture input; prerequisite holdings are separate."""
    values = {
        "target": target, "dataset": dataset, "estimand": str(write_estimand_document(cfg)),
        "standing": "empirical", "evidence_mode": "observation",
        "rule_procedures": ["beliefs/outcome-file/v1=" + analysis_nodes(cfg.profile)[2].id],
        "method": "rank comparison", "assumptions": "independent samples",
        "falsification": "no difference at alpha", "interpretation_rule": "beliefs/outcome-file/v1",
        "equivalence_rule": "beliefs/content-identity-equality/v1",
    }
    return values | overrides


def refreeze_spec(cfg: ScienceConfig, spec, *, supersedes=None, **overrides):
    """Vary a native frozen fixture through the public authoring/freeze context."""
    from dataclasses import fields
    from beliefs.decode import claim_from_stored
    from beliefs.rules import REFERENCE_RULES
    from beliefs.spec import SpecDraft, freeze
    from science.authoring_records import session_records
    from science.config import ReadContext
    ctx = ReadContext.open(cfg)
    with session_records(ctx) as records:
        claim, _ = claim_from_stored(records.read(spec.target), profile=cfg.profile,
                                     snapshot=ctx.authoring_snapshot(records=records))
        draft = SpecDraft(**({f.name: getattr(spec, f.name) for f in fields(SpecDraft)} | overrides))
        return freeze(draft, held_rules=REFERENCE_RULES,
            rule_procedures={b.rule: b.procedure for b in spec.rule_bindings if b.procedure is not None},
            profile=cfg.profile, claim=claim, records=records,
            assessment_dependency=records.assessment_dependency, supersedes=supersedes)


def assess_target(cfg, work, *, reference=Decimal("0.5"), target="proposition:p1", outcome="supported"):
    """A real spec and completed minimal-policy run, then the public assessment command."""
    from helpers.world import hold_fixture_dataset, fixture_bundle, mint_fixture_run, open_rig, OBSERVED
    data = hold_fixture_dataset(cfg, "data.txt", f"{reference} {outcome}\n".encode(), "expression", **OBSERVED)
    inputs = spec_inputs(cfg, target=target, dataset=data)
    inputs["estimand"] = str(write_estimand_document(cfg, reference=reference))
    with open_rig(cfg, ("spec",)) as (d, _):
        spec = next(t for t in d.invoke("spec", inputs).text.split() if t.startswith("analysis-spec:"))
    run = mint_fixture_run(cfg, spec, data, fixture_bundle(work, outcome))
    with open_rig(cfg, ("assess",)) as (d, ctx):
        ref = next(t for t in d.invoke("assess", {"run": run}).text.split() if t.startswith("assessment:"))
        return ref, stored.assessment_value(ctx.write_view().get(ref), profile=cfg.profile)
