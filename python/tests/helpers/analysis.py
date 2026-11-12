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

__all__ = ["analysis_nodes", "bootstrap_analysis", "write_estimand_document"]


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
    return (stored.procedure_node(assay), stored.classification_rule_node(classes),
            stored.procedure_node(estimator))


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
