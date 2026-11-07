"""verify: replay an assessment or dataset-production run and mint the verification."""
from __future__ import annotations

import socket
from pathlib import Path

from beliefs import stored
from beliefs.adapter import WorkflowDefinition
from beliefs.boundary import RunMinted, RunRefused
from beliefs.confinement import host_prerequisites
from beliefs.errors import MalformedRecord
from beliefs.recipe import CONFINED_POLICY
from beliefs.replay import DATASET_CONTENT_EQUALITY, derive_scope, replay
from beliefs.rules import REFERENCE_RULES
from beliefs.runrecord import decode_run_closure
from beliefs.runrecord import run_ref as run_ref_of
from beliefs.session import KernelRefusalValue
from beliefs.spec import DATASET_EQUIVALENCE_RULE
from beliefs.verify import (
    AssessmentVerification,
    DatasetProductionVerification,
    build_verification,
    publication_node,
)

from science.closure import NO_EPOCH_VERIFICATION
from science.commands.run import _check_staged_collisions, _stage_binding_for, now, prepare
from science.holdings import dataset_at
from science.refusal import Refusal, Refused
from science.report import Report, record_block


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def handle(ctx, writer, *, assessment=None, run=None, code, entrypoint, cores=None) -> Report:
    if (assessment is None) == (run is None):
        _refuse("verify requires exactly one of --assessment or --run")

    if assessment is not None:
        try:
            value = stored.assessment_value(ctx.cited(assessment).view.get(assessment), profile=ctx.config.profile)
        except MalformedRecord as caught:
            _refuse(f"{assessment}: {caught}")
        run_ref = stored.typed_ref("run", value.run)
        spec_ref = stored.typed_ref("analysis-spec", value.spec)
        try:
            original = decode_run_closure(ctx.cited(run_ref).view.get(run_ref))
            spec_value = stored.analysis_spec_value(
                ctx.cited(spec_ref).view.get(spec_ref), profile=ctx.config.profile
            )
        except MalformedRecord as caught:
            _refuse(str(caught))
        if original.recipe.boundary_policy == CONFINED_POLICY:
            reason = host_prerequisites()
            if reason is not None:
                _refuse(f"confinement is unavailable on this host: {reason}")
        observes_roles = [r for r in spec_value.input_roles if r.role == "observes"]
        if len(observes_roles) != 1:
            _refuse(f"{spec_ref} must declare exactly 1 observes role; found {len(observes_roles)}")
        (role,) = observes_roles
        found = dataset_at(tuple((mount.corpus_id, mount.view) for mount in ctx.session_mounts()), role.dataset)
        if found is None:
            elsewhere = ctx.dataset_at(role.dataset)
            if elsewhere is not None:
                ctx.cited(elsewhere[1].id)
            _refuse(f"the spec's dataset {role.dataset} is not in the session's corpora")
        dataset_ref = found[1].id
        prepared = prepare(ctx, spec_ref, dataset_ref, code, entrypoint, original.recipe.invocation.targets)
        spec = prepared.pop("spec")
        equivalence = REFERENCE_RULES.get(spec.equivalence_rule)
        if equivalence is None:
            _refuse(f"the spec's equivalence rule {spec.equivalence_rule!r} is not a reference rule")
        bound = dict(original.recipe.rule_bindings).get(spec.equivalence_rule)
        if bound != equivalence.identity:
            _refuse(
                f"the original run bound {spec.equivalence_rule!r} to {bound!r}; "
                f"the kernel now ships {equivalence.identity!r}"
            )
        outcome = replay(
            original,
            port=writer.operation_port(),
            spec=spec,
            observer=writer.actor,
            started_at=now(),
            scratch_base=ctx.config.operations_root / "scratch" / writer.invocation_id,
            cores=cores or 1,
            **prepared,
        )
        if isinstance(outcome, RunRefused):
            raise KernelRefusalValue(outcome)
        assert isinstance(outcome, RunMinted)
        view = ctx.write_view()
        replayed = decode_run_closure(view.get(run_ref_of(outcome.run.address())))
        derive_scope(original, replayed, certification=None)
        verification = build_verification(
            original,
            replayed,
            specs={spec.identity: spec},
            held_rules={equivalence.identity: equivalence},
            contract_identity=ctx.pins().science_contract,
            epoch=ctx.epoch_identity(absent=NO_EPOCH_VERIFICATION),
        )
        if not isinstance(verification, AssessmentVerification):
            raise RuntimeError(
                f"build_verification over an assessment run returned {type(verification).__name__}"
            )
        node = writer.add(publication_node(verification, assessment_ref=assessment))
        return (record_block(node),)

    assert run is not None
    try:
        original = decode_run_closure(ctx.cited(run).view.get(run))
    except MalformedRecord as caught:
        _refuse(str(caught))
    if original.recipe.shape != "dataset-production":
        _refuse(f"{run} has shape {original.recipe.shape!r}; verify --run requires a dataset-production run")
    if original.recipe.boundary_policy == CONFINED_POLICY:
        reason = host_prerequisites()
        if reason is not None:
            _refuse(f"confinement is unavailable on this host: {reason}")
    bound = dict(original.recipe.rule_bindings).get(DATASET_EQUIVALENCE_RULE)
    if bound != DATASET_CONTENT_EQUALITY.identity:
        _refuse(
            f"the original run bound {DATASET_EQUIVALENCE_RULE!r} to {bound!r}; "
            f"the kernel now ships {DATASET_CONTENT_EQUALITY.identity!r}"
        )
    code_root = Path(code)
    if not code_root.is_dir():
        _refuse(f"code {code!r} is not a directory")
    snakefile = code_root.parent / entrypoint
    if not snakefile.is_file():
        _refuse(f"entrypoint {entrypoint!r} is not a file under {code_root.parent}")
    held_inputs: dict[str, dict[str, Path]] = {}
    expected_inputs: dict[str, dict[str, str]] = {}
    mounts = tuple((mount.corpus_id, mount.view) for mount in ctx.session_mounts())
    for inp in original.recipe.inputs:
        found = dataset_at(mounts, inp.dataset)
        if found is None:
            elsewhere = ctx.dataset_at(inp.dataset)
            if elsewhere is not None:
                ctx.cited(elsewhere[1].id)
            _refuse(f"the run's input dataset {inp.dataset} is not in the session's corpora")
        try:
            declaration = stored.dataset_declaration(found[1])
        except MalformedRecord as caught:
            _refuse(str(caught))
        held_entry, expected_entry, _ = _stage_binding_for(ctx, inp.dataset, declaration)
        held_inputs[inp.dataset] = held_entry
        expected_inputs[inp.dataset] = expected_entry
    _check_staged_collisions(held_inputs)
    outcome = replay(
        original,
        port=writer.operation_port(),
        spec=None,
        definition=WorkflowDefinition(snakefile=snakefile.read_bytes(), family_streams={}),
        code_roots=(code_root,),
        held_inputs=held_inputs,
        expected_inputs=expected_inputs,
        entrypoint=entrypoint,
        targets=original.recipe.invocation.targets,
        declared_outputs=original.recipe.invocation.declared_outputs,
        observer=writer.actor,
        started_at=now(),
        host_realization=socket.gethostname(),
        scratch_base=ctx.config.operations_root / "scratch" / writer.invocation_id,
        cores=cores or 1,
    )
    if isinstance(outcome, RunRefused):
        raise KernelRefusalValue(outcome)
    assert isinstance(outcome, RunMinted)
    view = ctx.write_view()
    replayed = decode_run_closure(view.get(run_ref_of(outcome.run.address())))
    derive_scope(original, replayed, certification=None)
    verification = build_verification(
        original,
        replayed,
        specs={},
        held_rules={DATASET_CONTENT_EQUALITY.identity: DATASET_CONTENT_EQUALITY},
        contract_identity=ctx.pins().science_contract,
        epoch=ctx.epoch_identity(absent=NO_EPOCH_VERIFICATION),
    )
    if not isinstance(verification, DatasetProductionVerification):
        raise RuntimeError(
            f"build_verification over a dataset-production run returned {type(verification).__name__}"
        )
    node = writer.add(publication_node(verification))
    return (record_block(node),)
