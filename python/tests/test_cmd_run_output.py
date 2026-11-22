"""run-output: governed reading of declared run outputs from operations scratch."""
from __future__ import annotations

import json
import re
import threading
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest
from beliefs.confinement import host_prerequisites
from beliefs.permit import WritePermit
from beliefs.recipe import MINIMAL_POLICY
from beliefs.runrecord import decode_run_closure
from beliefs.session import open_run_session

from helpers.analysis import spec_inputs
from helpers.world import OBSERVED, build_belief_world, hold_fixture_dataset, open_rig, write_config_for
from science.cli import main
from science.config import ReadContext
from science.cursor import MIN_OUTPUT_BUDGET
from science.dispatch import Dispatcher
from science.loader import production_tree, resolve_handlers
from science.refusal import Refused
from science.run_endpoint.paths import Scratch
from test_belief_path_transports import mcp_call


def _stats_bundle(root: Path, *, stats_body: str = "z\tp\tn\n1.1589\t0.2465\t51\n", outcome: str = "inconclusive"):
    code = root / "mm30_bundle"
    (code / "workflow").mkdir(parents=True, exist_ok=True)
    (code / "workflow" / "Snakefile").write_text(
        "rule analyze:\n"
        '    input: "inputs/data.txt"\n'
        '    output: "outputs/stats.tsv", "outputs/outcome.txt"\n'
        "    run:\n"
        "        import pathlib\n"
        "        pathlib.Path(input[0]).read_text()\n"
        "        pathlib.Path(output[0]).parent.mkdir(parents=True, exist_ok=True)\n"
        f"        pathlib.Path(output[0]).write_text({stats_body!r})\n"
        f"        pathlib.Path(output[1]).write_text({(outcome + chr(10))!r})\n"
    )
    return code, "mm30_bundle/workflow/Snakefile", ("outputs/stats.tsv", "outputs/outcome.txt")


def _scratch_file(node, output: str) -> Path:
    closure = decode_run_closure(node)
    execution = closure.occurrence.receipt.execution
    base = Path(execution.scratch_mapping)
    if execution.instance is not None:
        base = base / "out"
    return base / output


def _mint_stats_run(certified_work, monkeypatch, *, stats_body: str = "z\tp\tn\n1.1589\t0.2465\t51\n", outcome: str = "inconclusive"):
    import science.commands.run as run_module

    if host_prerequisites() is not None:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
        monkeypatch.setattr(run_module, "host_prerequisites", lambda: None)

    cfg = build_belief_world(certified_work)
    dataset_ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression", **OBSERVED)
    code, entrypoint, targets = _stats_bundle(certified_work, stats_body=stats_body, outcome=outcome)
    with open_rig(cfg, ("spec", "run", "assess", "run-output")) as (d, ctx):
        spec_out = d.invoke("spec", spec_inputs(cfg, target="proposition:p1", dataset=dataset_ref))
        spec_ref = next(t for t in spec_out.text.split() if t.startswith("analysis-spec:"))
        run_out = d.invoke(
            "run",
            {
                "spec": spec_ref,
                "dataset": dataset_ref,
                "code": str(code),
                "entrypoint": entrypoint,
                "targets": list(targets),
            },
        )
        run_ref = next(t for t in run_out.text.split() if t.startswith("run:"))
        return cfg, run_ref, run_out.text


def test_run_output_reads_verified_stats_with_source_identity_and_transport_equivalence(
    certified_work, monkeypatch, capsys
):
    stats = "z\tp\tn\n1.1589\t0.2465\t51\n"
    cfg, run_ref, run_text = _mint_stats_run(certified_work, monkeypatch, stats_body=stats)
    expected_digest = "sha256:" + sha256(stats.encode()).hexdigest()
    assert f"output: outputs/stats.tsv {expected_digest}\n" in run_text

    cfg_path = write_config_for(cfg)
    mcp_result = mcp_call(cfg_path, "run-output", {"run": run_ref, "output": "outputs/stats.tsv"})
    assert mcp_result["isError"] is False
    mcp_text = mcp_result["content"][0]["text"]

    assert main(["run-output", "--config", str(cfg_path), "--run", run_ref, "--output", "outputs/stats.tsv"]) == 0
    cli_text = capsys.readouterr().out

    assert cli_text == mcp_text
    assert f"  run: {run_ref}\n" in cli_text
    assert "  output: outputs/stats.tsv\n" in cli_text
    assert f"  digest: {expected_digest}\n" in cli_text
    assert f"  bytes: {len(stats.encode())}\n" in cli_text
    assert "1.1589\t0.2465\t51\n" in cli_text


def test_run_output_paginates_within_budget_and_reassembles_exactly(certified_work, monkeypatch):
    long_stats = "row\tvalue\n" + "".join(f"r{i:04d}\t{i * 0.125:.3f} µg\n" for i in range(120))
    cfg, run_ref, _ = _mint_stats_run(certified_work, monkeypatch, stats_body=long_stats)

    with open_rig(cfg, ("run-output",)) as (d, _):
        full = d.invoke("run-output", {"run": run_ref, "output": "outputs/stats.tsv"}).text
        d._decls["run-output"] = replace(d._decls["run-output"], output_budget=MIN_OUTPUT_BUDGET + 128)
        page = d.invoke("run-output", {"run": run_ref, "output": "outputs/stats.tsv"}).text
        pieces = []
        while match := re.search(r"\n… truncated at \d+ bytes; continue with cursor (\S+)\n$", page):
            assert len(page.encode()) <= MIN_OUTPUT_BUDGET + 128
            pieces.append(page[:match.start()])
            page = d.invoke("run-output", {"run": run_ref, "output": "outputs/stats.tsv"}, cursor=match[1]).text
        assert pieces and "".join([*pieces, page]) == full


def test_run_output_refuses_unknown_run_non_run_and_undeclared_output(certified_work, monkeypatch):
    cfg, run_ref, _ = _mint_stats_run(certified_work, monkeypatch)
    with open_rig(cfg, ("run-output",)) as (d, _):
        with pytest.raises(Refused) as missing:
            d.invoke("run-output", {"run": "run:" + "0" * 64, "output": "outputs/stats.tsv"})
        assert missing.value.refusal.code == "invalid-input"

        with pytest.raises(Refused) as wrong_kind:
            d.invoke("run-output", {"run": "proposition:p1", "output": "outputs/stats.tsv"})
        assert wrong_kind.value.refusal.code == "invalid-input"
        assert wrong_kind.value.refusal.data["kind"] == "proposition"

        with pytest.raises(Refused) as undeclared:
            d.invoke("run-output", {"run": run_ref, "output": "outputs/missing.tsv"})
        assert undeclared.value.refusal.code == "invalid-input"
        assert undeclared.value.refusal.data["available"] == ["outputs/outcome.txt", "outputs/stats.tsv"]


def test_run_output_refuses_missing_tampered_and_symlinked_scratch(certified_work, monkeypatch, tmp_path):
    cfg, run_ref, _ = _mint_stats_run(certified_work, monkeypatch)
    with open_rig(cfg, ("run-output",)) as (d, ctx):
        node = ctx.write_view().get(run_ref)
        target = _scratch_file(node, "outputs/stats.tsv")

        # 1. Tampered bytes fail digest verification before any content renders.
        original = target.read_bytes()
        target.write_bytes(b"z\tp\tn\n9.9999\t0.0001\t51\n")
        with pytest.raises(Refused) as tampered:
            d.invoke("run-output", {"run": run_ref, "output": "outputs/stats.tsv"})
        assert tampered.value.refusal.code == "read-unavailable"
        assert tampered.value.refusal.data["reason"] == "digest-mismatch"

        # 2. Symlink planted in scratch is refused even if its target matches the digest.
        outside = tmp_path / "outside.tsv"
        outside.write_bytes(original)
        target.unlink()
        target.symlink_to(outside)
        with pytest.raises(Refused) as symlinked:
            d.invoke("run-output", {"run": run_ref, "output": "outputs/stats.tsv"})
        assert symlinked.value.refusal.code == "read-unavailable"
        assert symlinked.value.refusal.data["reason"] == "scratch-unconfined"

        # 3. Missing / reclaimed scratch file refuses read-unavailable.
        target.unlink()
        with pytest.raises(Refused) as absent:
            d.invoke("run-output", {"run": run_ref, "output": "outputs/stats.tsv"})
        assert absent.value.refusal.code == "read-unavailable"
        assert absent.value.refusal.data["reason"] == "scratch-missing"


def test_run_output_refuses_scratch_mapping_outside_operations_scratch(certified_work, monkeypatch, tmp_path):
    cfg, run_ref, _ = _mint_stats_run(certified_work, monkeypatch)
    other_ops = tmp_path / "other-operations"
    other_ops.mkdir()
    foreign_cfg = replace(cfg, operations_root=other_ops)
    decls = tuple(d for d in production_tree() if d.name == "run-output")
    dispatcher = Dispatcher(decls, resolve_handlers(decls), ReadContext.open(foreign_cfg))
    with pytest.raises(Refused) as caught:
        dispatcher.invoke("run-output", {"run": run_ref, "output": "outputs/stats.tsv"})
    assert caught.value.refusal.code == "read-unavailable"
    assert caught.value.refusal.data["reason"] == "scratch-outside-operations-root"


def test_run_output_refuses_non_utf8_output_bytes(certified_work, monkeypatch):
    import science.commands.run as run_module

    if host_prerequisites() is not None:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
        monkeypatch.setattr(run_module, "host_prerequisites", lambda: None)

    cfg = build_belief_world(certified_work)
    dataset_ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression", **OBSERVED)
    code = certified_work / "bin_bundle"
    (code / "workflow").mkdir(parents=True, exist_ok=True)
    (code / "workflow" / "Snakefile").write_text(
        "rule analyze:\n"
        '    input: "inputs/data.txt"\n'
        '    output: "outputs/plot.bin", "outputs/outcome.txt"\n'
        "    run:\n"
        "        import pathlib\n"
        "        pathlib.Path(input[0]).read_text()\n"
        "        pathlib.Path(output[0]).parent.mkdir(parents=True, exist_ok=True)\n"
        "        pathlib.Path(output[0]).write_bytes(b'\\x89PNG\\xff\\xfe')\n"
        "        pathlib.Path(output[1]).write_text('supported\\n')\n"
    )
    with open_rig(cfg, ("spec", "run", "run-output")) as (d, _):
        spec_ref = next(
            t for t in d.invoke("spec", spec_inputs(cfg, target="proposition:p1", dataset=dataset_ref)).text.split()
            if t.startswith("analysis-spec:")
        )
        run_out = d.invoke(
            "run",
            {
                "spec": spec_ref,
                "dataset": dataset_ref,
                "code": str(code),
                "entrypoint": "bin_bundle/workflow/Snakefile",
                "targets": ["outputs/plot.bin", "outputs/outcome.txt"],
            },
        )
        run_ref = next(t for t in run_out.text.split() if t.startswith("run:"))
        with pytest.raises(Refused) as caught:
            d.invoke("run-output", {"run": run_ref, "output": "outputs/plot.bin"})
        assert caught.value.refusal.code == "invalid-input"
        assert caught.value.refusal.data["reason"] == "non-utf8"


def test_run_output_works_in_live_supervised_run_and_refuses_after_reclamation(certified_work):
    reason = host_prerequisites()
    if reason:
        pytest.skip(f"confinement unavailable: {reason}")
    cfg = build_belief_world(certified_work)
    dataset_ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression", **OBSERVED)
    with open_rig(cfg, ("spec",)) as (attended, _):
        spec_ref = next(
            t for t in attended.invoke("spec", spec_inputs(cfg, target="proposition:p1", dataset=dataset_ref)).text.split()
            if t.startswith("analysis-spec:")
        )

    scratch = certified_work / "actor"
    code, entrypoint, targets = _stats_bundle(scratch)
    decls = tuple(d for d in production_tree() if d.name in ("run", "run-output"))
    run_decl = next(d for d in decls if d.name == "run")
    permit = WritePermit(frozenset(run_decl.write_class.kinds), frozenset(run_decl.write_class.routes.values()))
    session = open_run_session(cfg.world, cfg.operations_root, write_root=cfg.write_root, profile=cfg.profile, ceiling=permit)
    try:
        with Scratch(scratch, cfg.operations_root, threading.Event()) as capture:
            dispatcher = Dispatcher(
                decls, resolve_handlers(decls), ReadContext.open(cfg), session=session, run_inputs=capture
            )
            run_out = dispatcher.invoke(
                "run",
                {
                    "spec": spec_ref,
                    "dataset": dataset_ref,
                    "code": str(code),
                    "entrypoint": entrypoint,
                    "targets": list(targets),
                },
                invocation_id="supervised-stats",
            )
            run_ref = next(t for t in run_out.text.split() if t.startswith("run:"))
            out = dispatcher.invoke("run-output", {"run": run_ref, "output": "outputs/stats.tsv"})
            assert "1.1589\t0.2465\t51\n" in out.text
            assert f"  run: {run_ref}\n" in out.text

        # After Scratch.cleanup() reclaims the session's scratch directory, reading refuses cleanly.
        after = Dispatcher(decls, resolve_handlers(decls), ReadContext.open(cfg))
        with pytest.raises(Refused) as caught:
            after.invoke("run-output", {"run": run_ref, "output": "outputs/stats.tsv"})
        assert caught.value.refusal.code == "read-unavailable"
        assert caught.value.refusal.data["reason"] == "scratch-missing"
    finally:
        session.close()
