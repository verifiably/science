"""next: the derived queue of layer §4.4, computed at read time (§4.8)."""
from __future__ import annotations

from beliefs import stored
from beliefs.admission import Admitted, admit
from beliefs.dataset import Held, admission_state, dataset_address

from science.report import Heading, KeyVals, Report

CLASSES = ("ready", "not-ready", "assessed-not-admitted", "admitted")


def _targeting_specs(view, proposition, profile):
    specs = (stored.analysis_spec_value(n, profile=profile) for n in view.iter_stored() if n.kind == "analysis-spec")
    return [spec for spec in specs if spec.target == proposition]


def _inputs_held(ctx, view, spec) -> bool:
    observations = ctx.observations()
    for role in spec.input_roles:
        node = next((n for n in view.iter_stored() if n.kind == "dataset"
                     and dataset_address(stored.dataset_declaration(n)) == role.dataset), None)
        if node is None:
            return False
        if not isinstance(admission_state(stored.dataset_declaration(node), observations.get(role.dataset, ())), Held):
            return False
    return True


def classify(ctx, proposition: str) -> str:
    _, view = ctx.single_view()
    profile = ctx.config.profile
    assessed = any(n.kind == "assessment" and stored.assessment_value(n, profile=profile).proposition == proposition
                   for n in view.iter_stored())
    if not assessed:
        return "ready" if any(_inputs_held(ctx, view, s) for s in _targeting_specs(view, proposition, profile)) else "not-ready"
    inputs = ctx.gather_inputs(proposition)
    observations = ctx.observations()
    for assessment in inputs.assessments:
        run = inputs.runs.get(assessment.run)
        if run is not None and isinstance(admit(assessment, run, observations, inputs.verifications), Admitted):
            return "admitted"
    return "assessed-not-admitted"


def handle(ctx, *, limit=None) -> Report:
    _, view = ctx.single_view()
    rows = []
    for node in view.iter_stored():
        if node.kind != "proposition":
            continue
        statement = stored.display_statement(node) or node.title
        rows.append((CLASSES.index(classify(ctx, node.id)), node.id, statement))
    rows.sort()
    shown = rows[: (limit or 10)]
    return (Heading("Next"),
            KeyVals("propositions", tuple((pid, f"{CLASSES[c]}: {statement}") for c, pid, statement in shown)
                    or (("none", "no propositions"),)))
