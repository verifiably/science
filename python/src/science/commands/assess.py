"""assess: derive the assessment a run supports and mint it (§4.5)."""
from __future__ import annotations

from beliefs import stored
from beliefs.assess import AssessmentFinding, build_assessment
from beliefs.errors import MalformedRecord
from beliefs.rules import REFERENCE_RULES
from beliefs.runrecord import decode_run_closure

from science.refusal import Refusal, Refused
from science.report import Report, record_block


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def handle(ctx, writer, *, run) -> Report:
    _, view = ctx.single_view()
    if not view.holds(run):
        _refuse(f"run {run!r} is not in the corpus")
    try:
        closure = decode_run_closure(view.get(run))
    except MalformedRecord as caught:
        _refuse(f"{run}: {caught}")
    spec_ref = stored.typed_ref("analysis-spec", closure.recipe.spec_identity or "")
    if not closure.recipe.spec_identity or not view.holds(spec_ref):
        _refuse(f"{run} names no analysis-spec this corpus holds")
    spec = stored.analysis_spec_value(view.get(spec_ref), profile=ctx.config.profile)
    rule = REFERENCE_RULES.get(spec.interpretation_rule)
    if rule is None:
        _refuse(f"the spec's interpretation rule {spec.interpretation_rule!r} is not a reference rule")
    derived = build_assessment(closure, specs={spec.identity: spec}, implementations={rule.identity: rule})
    if isinstance(derived, AssessmentFinding):
        _refuse(f"assessment finding: {derived.reason}")
    # The estimand and applicability are required: the derived assessment
    # carries the frozen spec's typed pair (design §4.5, amended 2026-09-23).
    optional = {k: v for k, v in (("estimate", derived.estimate), ("uncertainty", derived.uncertainty))
                if v is not None}
    node = writer.add(stored.assessment_node(
        derived.identity()[:16], title=f"assessment of {spec.target}", spec=spec.identity, run=run,
        proposition=spec.target, outcome=derived.outcome, interpretation_rule=derived.interpretation_rule,
        estimand=derived.estimand, applicability=derived.applicability, **optional))
    stored_identity = stored.assessment_value(node, profile=ctx.config.profile).identity()
    if stored_identity != derived.identity():
        raise RuntimeError(f"stored assessment identity {stored_identity} differs from derived {derived.identity()}")
    return (record_block(node),)
