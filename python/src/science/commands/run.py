"""run: execute a frozen spec's analysis once under confinement (§4.4)."""
from __future__ import annotations

import socket
from datetime import UTC, datetime
from pathlib import Path

from beliefs import stored
from beliefs.adapter import WorkflowDefinition
from beliefs.boundary import RunMinted, RunRefused, execute_assessment_run
from beliefs.confinement import host_prerequisites
from beliefs.dataset import dataset_address
from beliefs.errors import MalformedRecord
from beliefs.recipe import CONFINED_POLICY
from beliefs.runrecord import run_ref
from beliefs.session import KernelRefusalValue

from science.refusal import Refusal, Refused
from science.report import Report, record_block

POLICY = CONFINED_POLICY


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def prepare(ctx, spec_ref: str, dataset_ref: str, code: str, entrypoint: str, targets) -> dict:
    """Everything the boundary needs, validated; shared with verify."""
    _, view = ctx.single_view()
    if not view.holds(spec_ref):
        _refuse(f"spec {spec_ref!r} is not in the corpus")
    if not view.holds(dataset_ref):
        _refuse(f"dataset {dataset_ref!r} is not in the corpus")
    try:
        spec = stored.analysis_spec_value(view.get(spec_ref), profile=ctx.config.profile)
        address = dataset_address(stored.dataset_declaration(view.get(dataset_ref)))
    except MalformedRecord as caught:
        _refuse(str(caught))
    if address is None or all(role.dataset != address for role in spec.input_roles):
        _refuse(f"{dataset_ref} is not the dataset the spec observes")
    code_root = Path(code)
    if not code_root.is_dir():
        _refuse(f"code {code!r} is not a directory")
    snakefile = code_root.parent / entrypoint
    if not snakefile.is_file():
        _refuse(f"entrypoint {entrypoint!r} is not a file under {code_root.parent}")
    if not targets:
        _refuse("targets must name at least one output")
    return {
        "spec": spec,
        "definition": WorkflowDefinition(snakefile=snakefile.read_bytes(), family_streams={}),
        "code_roots": (code_root,),
        "held_inputs": {address: ctx.held_path(address)},
        "entrypoint": entrypoint,
        "targets": tuple(targets),
        "declared_outputs": tuple(targets),
        "host_realization": socket.gethostname(),
    }


def handle(ctx, writer, *, spec, dataset, code, entrypoint, targets, cores=None) -> Report:
    reason = host_prerequisites()
    if reason is not None:
        _refuse(f"confinement is unavailable on this host: {reason}")
    prepared = prepare(ctx, spec, dataset, code, entrypoint, targets)
    outcome = execute_assessment_run(
        port=writer.operation_port(), boundary_policy=POLICY, observer=writer.actor,
        started_at=now(), scratch_base=ctx.config.operations_root / "scratch" / writer.invocation_id,
        cores=cores or 1, **prepared,
    )
    if isinstance(outcome, RunRefused):
        # A kernel refusal, through the kernel path: the boundary may already
        # have written its act-report through the port, so this is never a
        # surface `Refused` (Task 1 would call that a handler defect). The
        # dispatcher normalizes it to `kernel-refused` carrying the reason.
        raise KernelRefusalValue(outcome)
    assert isinstance(outcome, RunMinted)
    _, view = ctx.single_view()
    return (record_block(view.get(run_ref(outcome.run.address()))),)
