import io
import json
import socket
import threading
from contextlib import contextmanager

import pytest

from helpers.world import SPEC_FIELDS, build_fixture_world_with_contract, write_config_for
from test_mcp import rpc


@contextmanager
def _service(cfg_path, socket_path):
    """The CLI's launcher, bound only for the segment that needs it: one socket
    admits one launcher at a time (decision 6), and `mcp_call` binds the same
    path for the span of its own call."""
    from science.config import load_config
    from science.serve import serve
    server = serve(load_config(cfg_path), socket_path)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield server
    finally:
        server.server_close()


@pytest.fixture
def world(certified_work):
    cfg = build_fixture_world_with_contract(certified_work)
    return cfg, write_config_for(cfg)


def mcp_calls(cfg_path, calls):
    """Every call in one `serve()` lifetime — one attended session — so that
    invocation replay, which is session-scoped, is what gets tested."""
    from science.mcp import serve
    frames = []
    for index, (name, arguments, invocation_id) in enumerate(calls, 1):
        params = {"name": name, "arguments": dict(arguments)}
        if invocation_id is not None:
            params["arguments"]["invocation_id"] = invocation_id
        frames.append(json.dumps(rpc("tools/call", params, id=index)))
    stdin = io.BytesIO(("\n".join(frames) + "\n").encode())
    stdout = io.StringIO()
    serve(cfg_path, stdin=stdin, stdout=stdout, stderr=io.StringIO())
    return [json.loads(line)["result"] for line in stdout.getvalue().splitlines()]


def mcp_call(cfg_path, name, arguments, invocation_id=None):
    (result,) = mcp_calls(cfg_path, [(name, arguments, invocation_id)])
    return result


CLAIM = {"subject": "concept:disease-stage", "predicate": "affects", "object": "protein:PHF19",
         "layer": "causal", "polarity": "positive"}


def test_mcp_write_replays_under_one_invocation_id(world):
    cfg, cfg_path = world
    first, again = mcp_calls(cfg_path, [("claim", CLAIM, "A" * 8), ("claim", CLAIM, "A" * 8)])
    assert first["isError"] is False
    assert first["content"][0]["text"] == again["content"][0]["text"]
    assert first["structuredContent"]["invocation_id"] == "A" * 8
    from science.config import ReadContext
    _, view = ReadContext.open(cfg).single_view()
    assert sum(1 for n in view.iter_stored() if n.kind == "proposition") == 1
    # One act in the session's ledger, not two: the second call replayed.
    from beliefs.session import ledger_path
    (ledger,) = (cfg.operations_root / "sessions").glob("*/ledger.v1")
    assert sum(1 for line in ledger.read_text().splitlines() if '"act"' in line) == 1


def test_mcp_refusal_carries_the_envelope(world):
    _, cfg_path = world
    result = mcp_call(cfg_path, "claim", dict(CLAIM, subject="protein:PHF19", object="concept:disease-stage"))
    assert result["isError"] is True
    assert result["structuredContent"]["refusal"]["code"] == "invalid-input"
    assert "no plan row" in result["structuredContent"]["refusal"]["message"]


def test_cli_write_routes_through_the_service_and_refuses_with_the_json_line(world, tmp_path, capsys):
    from science.cli import main
    from science.serve import serve
    from science.config import load_config
    cfg, _ = world
    named = tmp_path / "svc.sock"
    cfg_path = write_config_for(cfg, service_socket=named)
    server = serve(load_config(cfg_path), named)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        data = tmp_path / "m.txt"
        data.write_bytes(b"x\n")
        assert main(["dataset", "--config", str(cfg_path), "--path", str(data), "--title", "m",
                     "--facets", "biology/gene-axis=axis:rows,namespace:HGNC"]) == 0
        out = capsys.readouterr()
        assert "[dataset] dataset:sha256:" in out.out
        assert json.loads(out.err)["invocation_id"]
        assert main(["dataset", "--config", str(cfg_path), "--path", str(tmp_path), "--title", "dir"]) == 3
        err = json.loads(capsys.readouterr().err)
        assert err["refusal"]["code"] == "invalid-input"
        assert main(["dataset", "--config", str(cfg_path), "--path", str(data), "--title", "m",
                     "--invocation-id", "R" * 8]) == 3  # same bytes: refuses naming the record
        assert main(["dataset", "--config", str(cfg_path), "--path", str(data), "--title", "m",
                     "--invocation-id", "R" * 8]) == 3  # and replays that refusal
    finally:
        server.server_close()


def test_every_write_reaches_its_transport_and_renders_the_canonical_report(world, tmp_path, capsys, monkeypatch):
    """spec and assess through MCP, run and verify through the CLI service:
    each write's text contains every record minted by its invocation, rebuilt
    from the corpus in (uid, record_id) order. Uids are minted per world, so
    writes are compared to the corpus, not byte-for-byte across transports
    (design §7)."""
    import science.commands.run as run_module
    from beliefs.confinement import host_prerequisites
    from beliefs.recipe import MINIMAL_POLICY
    from beliefs.session import open_ledger_reader
    from science.cli import main
    from science.config import ReadContext
    from science.report import record_block, serialize_block
    from helpers.world import fixture_bundle
    if host_prerequisites() is not None:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
        monkeypatch.setattr(run_module, "host_prerequisites", lambda: None)
    cfg, _ = world
    named = tmp_path / "svc.sock"
    cfg_path = write_config_for(cfg, service_socket=named)
    code, entrypoint, targets = fixture_bundle(tmp_path, "supported")
    data = tmp_path / "data.txt"
    data.write_bytes(b"x\n")

    def canonical(invocation_id):
        (invocation,) = [
            entry
            for path in (cfg.operations_root / "sessions").glob("*/ledger.v1")
            if (entry := open_ledger_reader(cfg.operations_root, path.parent.name).invocation(invocation_id)) is not None
        ]
        pairs = sorted({pair for act in invocation.acts for pair in act.record_ids})
        assert pairs
        assert invocation.outcome == {"done": [list(pair) for pair in pairs]}
        ctx = ReadContext.open(cfg)
        return "".join(serialize_block(record_block(ctx.load_record(uid, record_id)))
                       for uid, record_id in pairs)

    def ref_in(text, prefix):
        return next(t for t in text.split() if t.startswith(prefix))

    result = mcp_call(cfg_path, "claim", CLAIM)
    prop_text = result["content"][0]["text"]
    prop = ref_in(prop_text, "proposition:")
    assert prop_text == canonical(result["structuredContent"]["invocation_id"])
    # `mcp serve` now binds this same socket for the span of each `mcp_call`
    # (decision 6), so the CLI's own launcher is bound only around the
    # segments that need it, never while an `mcp_call` is in flight.
    with _service(cfg_path, named):
        assert main(["dataset", "--config", str(cfg_path), "--path", str(data), "--title", "expression",
                     "--locator", "accession:GSE-FIXTURE"]) == 0
        output = capsys.readouterr()
        dataset = ref_in(output.out, "dataset:")
        assert output.out == canonical(json.loads(output.err)["invocation_id"])
    result = mcp_call(cfg_path, "spec", dict(SPEC_FIELDS, target=prop, dataset=dataset))
    spec_text = result["content"][0]["text"]
    spec = ref_in(spec_text, "analysis-spec:")
    assert spec_text == canonical(result["structuredContent"]["invocation_id"])
    with _service(cfg_path, named):
        assert main(["run", "--config", str(cfg_path), "--spec", spec, "--dataset", dataset,
                     "--code", str(code), "--entrypoint", entrypoint, *sum((["--targets", t] for t in targets), [])]) == 0
        output = capsys.readouterr()
        run_text = output.out
        run = ref_in(run_text, "run:")
        assert run_text == canonical(json.loads(output.err)["invocation_id"])
    result = mcp_call(cfg_path, "assess", {"run": run})
    assess_text = result["content"][0]["text"]
    assessment = ref_in(assess_text, "assessment:")
    assert assess_text == canonical(result["structuredContent"]["invocation_id"])
    with _service(cfg_path, named):
        assert main(["verify", "--config", str(cfg_path), "--assessment", assessment,
                     "--code", str(code), "--entrypoint", entrypoint]) == 0
        output = capsys.readouterr()
        assert ref_in(output.out, "verification:")
        assert output.out == canonical(json.loads(output.err)["invocation_id"])
        # A kernel refusal through the service: the same bundle edited between
        # run and replay is a different recipe, refused by the boundary.
        (code / "workflow" / "Snakefile").write_text((code / "workflow" / "Snakefile").read_text().replace("supported", "refuted"))
        assert main(["verify", "--config", str(cfg_path), "--assessment", assessment,
                     "--code", str(code), "--entrypoint", entrypoint]) == 3
        assert json.loads(capsys.readouterr().err)["refusal"]["code"] == "kernel-refused"
    # And the two commands not yet seen on the other transport: assess's
    # refusal through the service, spec's refusal through MCP.
    result = mcp_call(cfg_path, "spec", dict(SPEC_FIELDS, target=prop, dataset=dataset, interpretation_rule="nope/v9"))
    assert result["isError"] is True and result["structuredContent"]["refusal"]["code"] == "invalid-input"


def test_reads_render_identically_through_mcp_and_cli(world, capsys):
    from science.cli import main
    cfg, cfg_path = world
    mcp_call(cfg_path, "claim", CLAIM)
    for name, arguments, argv in (
        ("belief", {"proposition": "proposition:concept-disease-stage-affects-protein-phf19"},
         ["--proposition", "proposition:concept-disease-stage-affects-protein-phf19"]),
        ("next", {}, []),
    ):
        text = mcp_call(cfg_path, name, arguments)["content"][0]["text"]
        assert main([name, "--config", str(cfg_path), *argv]) == 0
        assert capsys.readouterr().out == text
