"""verify: replay the assessment's run and mint the verification (§4.6)."""
from __future__ import annotations

from beliefs import stored
from beliefs.boundary import RunMinted, RunRefused
from beliefs.errors import MalformedRecord
from beliefs.replay import derive_scope, replay
from beliefs.rules import REFERENCE_RULES
from beliefs.runrecord import decode_run_closure
from beliefs.runrecord import run_ref as run_ref_of
from beliefs.session import KernelRefusalValue
from beliefs.verify import AssessmentVerification, build_verification, publication_node

from science.closure import NO_EPOCH_VERIFICATION
from science.commands.run import now, prepare
from science.refusal import Refusal, Refused
from science.report import Report, record_block


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def handle(ctx, writer, *, assessment, code, entrypoint, cores=None) -> Report:
    _, view = ctx.single_view()
    if not view.holds(assessment):
        _refuse(f"assessment {assessment!r} is not in the corpus")
    try:
        value = stored.assessment_value(view.get(assessment), profile=ctx.config.profile)
    except MalformedRecord as caught:
        _refuse(f"{assessment}: {caught}")
    run_ref = stored.typed_ref("run", value.run)
    spec_ref = stored.typed_ref("analysis-spec", value.spec)
    if not view.holds(run_ref) or not view.holds(spec_ref):
        _refuse(f"{assessment} names a run or spec this corpus does not hold")
    original = decode_run_closure(view.get(run_ref))
    (role,) = stored.analysis_spec_value(view.get(spec_ref), profile=ctx.config.profile).input_roles
    dataset_ref = next((n.id for n in view.iter_stored() if n.kind == "dataset"
                        and _address(n) == role.dataset), None)
    if dataset_ref is None:
        _refuse(f"the spec's dataset {role.dataset} is not in the corpus")
    prepared = prepare(ctx, spec_ref, dataset_ref, code, entrypoint, original.recipe.invocation.targets)
    spec = prepared.pop("spec")
    equivalence = REFERENCE_RULES.get(spec.equivalence_rule)
    if equivalence is None:
        _refuse(f"the spec's equivalence rule {spec.equivalence_rule!r} is not a reference rule")
    bound = dict(original.recipe.rule_bindings).get(spec.equivalence_rule)
    if bound != equivalence.identity:
        # The verification resolves the rule to the implementation the original
        # run bound; refused before the replay, never after it (RuleUnbound).
        _refuse(f"the original run bound {spec.equivalence_rule!r} to {bound!r}; "
                f"the kernel now ships {equivalence.identity!r}")
    # --- first act: the replay -----------------------------------------------
    outcome = replay(original, port=writer.operation_port(), spec=spec, observer=writer.actor,
                     started_at=now(), scratch_base=ctx.config.operations_root / "scratch" / writer.invocation_id,
                     cores=cores or 1, **prepared)
    if isinstance(outcome, RunRefused):
        raise KernelRefusalValue(outcome)  # the kernel path, as in run
    assert isinstance(outcome, RunMinted)
    # Both runs in their stored form, as the audit re-derives the verdict: an
    # in-memory result keeps the workflow's target order while the stored one is
    # sorted, and the equivalence rule compares them as tuples (beliefs-97075f).
    _, view = ctx.single_view()
    replayed = decode_run_closure(view.get(run_ref_of(outcome.run.address())))
    derive_scope(original, replayed, certification=None)
    verification = build_verification(original, replayed, specs={spec.identity: spec},
                                      held_rules={equivalence.identity: equivalence},
                                      contract_identity=ctx.pins().science_contract,
                                      epoch=ctx.epoch_identity(absent=NO_EPOCH_VERIFICATION))
    if not isinstance(verification, AssessmentVerification):
        raise RuntimeError(f"build_verification over an assessment run returned {type(verification).__name__}")
    node = writer.add(publication_node(verification, assessment_ref=assessment))
    return (record_block(node),)


def _address(node) -> str | None:
    from beliefs.dataset import dataset_address
    return dataset_address(stored.dataset_declaration(node))
