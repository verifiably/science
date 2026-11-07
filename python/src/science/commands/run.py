"""run: execute a frozen spec's analysis once under confinement."""
from __future__ import annotations

import socket
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path

from beliefs import stored
from beliefs.adapter import WorkflowDefinition
from beliefs.boundary import RunMinted, RunRefused, execute_assessment_run
from beliefs.confinement import host_prerequisites
from beliefs.dataset import DatasetDeclaration, dataset_address
from beliefs.errors import MalformedRecord
from beliefs.recipe import CONFINED_POLICY
from beliefs.runrecord import run_ref
from beliefs.session import KernelRefusalValue

from science.holdings import dataset_at
from science.refusal import Refusal, Refused
from science.report import Report, record_block

POLICY = CONFINED_POLICY


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _stage_binding_for(
    ctx, address: str, declaration: DatasetDeclaration
) -> tuple[dict[str, Path], dict[str, str], str]:
    if not declaration.resources:
        _refuse(f"{address} declares no resources")
    computed = dataset_address(declaration)
    if computed is None or computed != address:
        _refuse(f"{address} has unpinned or mismatched resource digests")
    held_entry = ctx.held_resources(address)
    expected_entry = {r.name: r.digest for r in declaration.resources if r.digest is not None}
    if len(declaration.resources) == 1:
        content_id = declaration.resources[0].digest
        assert content_id is not None
    else:
        content_id = address.removeprefix("dataset:")
    return held_entry, expected_entry, content_id


def _check_staged_collisions(held_inputs: Mapping[str, Mapping[str, Path]]) -> None:
    files_staged: set[str] = set()
    dirs_staged: set[str] = set()
    for address, source in held_inputs.items():
        for rel_name in sorted(source.keys()):
            parts = rel_name.split("/")
            parents = ["/".join(parts[:i]) for i in range(1, len(parts))]
            if rel_name in files_staged or rel_name in dirs_staged or any(p in files_staged for p in parents):
                _refuse(f"staged input path collision at {rel_name!r} across input datasets (at {address})")
            files_staged.add(rel_name)
            dirs_staged.update(parents)


def prepare(ctx, spec_ref: str, dataset_ref: str, code: str, entrypoint: str, targets) -> dict:
    """Everything the boundary needs, validated; shared with verify. The spec
    and dataset are cited from whichever session corpus holds them, decoded
    under the writer's profile."""
    spec_view, dataset_view = ctx.cited(spec_ref).view, ctx.cited(dataset_ref).view
    try:
        spec = stored.analysis_spec_value(spec_view.get(spec_ref), profile=ctx.config.profile)
        declaration = stored.dataset_declaration(dataset_view.get(dataset_ref))
        address = dataset_address(declaration)
    except MalformedRecord as caught:
        _refuse(str(caught))
    observes_addresses = [role.dataset for role in spec.input_roles if role.role == "observes"]
    if address is None or observes_addresses != [address]:
        _refuse(f"{dataset_ref} is not the dataset the spec observes")
    held_inputs: dict[str, dict[str, Path]] = {}
    expected_inputs: dict[str, dict[str, str]] = {}
    mounts = tuple((mount.corpus_id, mount.view) for mount in ctx.session_mounts())
    for role in spec.input_roles:
        ds_address = role.dataset
        if ds_address in held_inputs:
            continue
        if ds_address == address:
            ds_declaration = declaration
        else:
            found = dataset_at(mounts, ds_address)
            if found is None:
                elsewhere = ctx.dataset_at(ds_address)
                if elsewhere is not None:
                    ctx.cited(elsewhere[1].id)
                _refuse(f"the spec's dataset {ds_address} is not in the session's corpora")
            try:
                ds_declaration = stored.dataset_declaration(found[1])
            except MalformedRecord as caught:
                _refuse(str(caught))
        held_entry, expected_entry, _ = _stage_binding_for(ctx, ds_address, ds_declaration)
        held_inputs[ds_address] = held_entry
        expected_inputs[ds_address] = expected_entry
    _check_staged_collisions(held_inputs)
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
        "held_inputs": held_inputs,
        "expected_inputs": expected_inputs,
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
        # surface `Refused`. The
        # dispatcher normalizes it to `kernel-refused` carrying the reason.
        raise KernelRefusalValue(outcome)
    assert isinstance(outcome, RunMinted)
    view = ctx.write_view()
    return (record_block(view.get(run_ref(outcome.run.address()))),)
