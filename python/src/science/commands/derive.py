"""derive: execute a dataset-production workflow under confinement, hold its outputs, and mint the run and derived dataset records."""
from __future__ import annotations

import shutil
import socket
import tempfile
from collections.abc import Mapping, Sequence
from hashlib import sha256
from pathlib import Path

from beliefs import stored
from beliefs.adapter import WorkflowDefinition
from beliefs.boundary import RunMinted, RunRefused, execute_production_run
from beliefs.confinement import host_prerequisites
from beliefs.dataset import DatasetDeclaration, dataset_address
from beliefs.errors import MalformedRecord
from beliefs.holdings.boundary import write
from beliefs.holdings.records import StoreLocator
from beliefs.recipe import CONFINED_POLICY, RecipeInput
from beliefs.runrecord import run_ref
from beliefs.session import KernelRefusalValue
from beliefs.spec import Deterministic

from science.commands.run import _check_staged_collisions, _stage_binding_for, now
from science.refusal import Refusal, Refused
from science.report import Report, record_block

POLICY = CONFINED_POLICY
INSTRUMENT = "science/derive.v1"
_RESERVED_PARAMETERS = frozenset({"seed_roots", "seed_derivation_rule"})


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def parse_string_parameters(parameters: Sequence[str] | None) -> dict[str, str]:
    if parameters is None:
        return {}
    parsed: dict[str, str] = {}
    for entry in parameters:
        if not isinstance(entry, str) or "=" not in entry:
            _refuse(f"parameter {entry!r} must have the form KEY=VALUE")
        key, _, value = entry.partition("=")
        if not key or key.strip() != key:
            _refuse(f"parameter {entry!r} has an empty or whitespace-padded key")
        if key in _RESERVED_PARAMETERS:
            _refuse(f"parameter {key!r} is reserved by the execution boundary")
        if key in parsed:
            _refuse(f"duplicate parameter key {key!r}")
        parsed[key] = value
    return parsed


def handle(
    ctx,
    writer,
    *,
    dataset: str,
    code: str,
    entrypoint: str,
    targets: Sequence[str],
    title: str,
    reads: Sequence[str] | None = None,
    parameters: Sequence[str] | None = None,
    cores: int | None = None,
) -> Report:
    reason = host_prerequisites()
    if reason is not None:
        _refuse(f"confinement is unavailable on this host: {reason}")
    if not isinstance(title, str) or not title.strip():
        _refuse("title must be a non-empty string")
    if cores is not None and cores < 1:
        _refuse("cores must be >= 1")
    if not targets:
        _refuse("targets must name at least one output")
    seen_targets: set[str] = set()
    for t in targets:
        if not isinstance(t, str) or not t or "\\" in t or t.startswith("/"):
            _refuse(f"invalid target path {t!r}")
        if t in seen_targets:
            _refuse(f"duplicate target {t!r}")
        seen_targets.add(t)
        try:
            StoreLocator(writer.store_id, f"{'0' * 64}/{t}")
        except MalformedRecord as caught:
            _refuse(f"invalid target path {t!r}: {caught}")
    parsed_params = parse_string_parameters(parameters)

    code_root = Path(code)
    if not code_root.is_dir():
        _refuse(f"code {code!r} is not a directory")
    snakefile = code_root.parent / entrypoint
    if not snakefile.is_file():
        _refuse(f"entrypoint {entrypoint!r} is not a file under {code_root.parent}")

    holdings = writer.holdings_context(instrument=INSTRUMENT)

    held_inputs: dict[str, dict[str, Path]] = {}
    expected_inputs: dict[str, dict[str, str]] = {}
    recipe_inputs: list[RecipeInput] = []
    seen_addresses: set[str] = set()

    role_refs: list[tuple[str, str]] = [("transforms", dataset)]
    for aux_ref in reads or ():
        role_refs.append(("reads", aux_ref))

    for role_name, ref in role_refs:
        view = ctx.cited(ref).view
        try:
            node = view.get(ref)
            if node.kind != "dataset":
                _refuse(f"{ref} is a {node.kind}, not a dataset")
            declaration: DatasetDeclaration = stored.dataset_declaration(node)
            address = dataset_address(declaration)
        except MalformedRecord as caught:
            _refuse(str(caught))
        if address is None:
            _refuse(f"{ref} has unpinned resource digests")
        if address in seen_addresses:
            _refuse(f"input dataset {address} is declared more than once across --dataset and --reads")
        seen_addresses.add(address)
        held_entry, expected_entry, content_id = _stage_binding_for(ctx, address, declaration)
        held_inputs[address] = held_entry
        expected_inputs[address] = expected_entry
        recipe_inputs.append(RecipeInput(role=role_name, dataset=address, content=content_id))

    _check_staged_collisions(held_inputs)

    scratch_base = ctx.config.operations_root / "scratch" / writer.invocation_id
    ctx.config.operations_root.mkdir(parents=True, exist_ok=True)
    export_dir = Path(tempfile.mkdtemp(prefix="export-", dir=ctx.config.operations_root))
    try:
        outcome = execute_production_run(
            inputs=tuple(recipe_inputs),
            port=writer.operation_port(),
            boundary_policy=POLICY,
            expected_inputs=expected_inputs,
            parameters=parsed_params,
            nondeterminism=Deterministic(),
            definition=WorkflowDefinition(snakefile=snakefile.read_bytes(), family_streams={}),
            code_roots=(code_root,),
            held_inputs=held_inputs,
            entrypoint=entrypoint,
            targets=tuple(targets),
            declared_outputs=tuple(targets),
            dataset_title=title,
            output_dir=export_dir,
            observer=writer.actor,
            started_at=now(),
            host_realization=socket.gethostname(),
            scratch_base=scratch_base,
            cores=cores or 1,
        )
        if isinstance(outcome, RunRefused):
            raise KernelRefusalValue(outcome)
        assert isinstance(outcome, RunMinted)
        view = ctx.write_view()
        for out_name, out_digest in outcome.run.result.outputs:
            location = StoreLocator(writer.store_id, f"{out_digest.removeprefix('sha256:')}/{out_name}")
            standing = tuple(
                stored.holdings_observation_value(n)
                for n in view.iter_stored()
                if n.kind == "holdings-observation"
                and stored.holdings_observation_value(n).location == location
            )
            content = (export_dir / out_name).read_bytes()
            if "sha256:" + sha256(content).hexdigest() != out_digest:
                raise RuntimeError(f"exported output {out_name!r} digest mismatch")
            write(holdings, location, content, expected=out_digest, standing=standing)
    finally:
        shutil.rmtree(export_dir, ignore_errors=True)
    view = ctx.write_view()
    return (record_block(view.get(run_ref(outcome.run.address()))),)
