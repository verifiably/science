import json
import re
from pathlib import Path

import pytest

from science.cursor import MIN_OUTPUT_BUDGET
from science.schema import Declaration, InputSpec, WriteClass
from helpers.world import write_cli_config


def test_parser_compiles_inputs():
    from science.cli import build_parser

    decl = Declaration(
        "small",
        "p",
        WriteClass("read-only"),
        MIN_OUTPUT_BUDGET,
        (
            InputSpec("mode", "enum", True, "d", choices=("a", "b")),
            InputSpec("tag", "list-of-string", False, "d"),
            InputSpec("dry_run", "bool", False, "d"),
        ),
        (),
        Path("."),
    )
    parser = build_parser((decl,))
    ns = parser.parse_args(
        [
            "small",
            "--mode",
            "a",
            "--tag",
            "x",
            "--tag",
            "y",
            "--no-dry-run",
            "--config",
            "science.toml",
            "--invocation-id",
            "caller_id",
            "--continue",
            "scur1.cursor",
        ]
    )
    assert vars(ns) == {
        "command": "small",
        "mode": "a",
        "tag": ["x", "y"],
        "dry_run": False,
        "config": Path("science.toml"),
        "invocation_id": "caller_id",
        "cursor": "scur1.cursor",
    }
    with pytest.raises(SystemExit) as caught:
        parser.parse_args(["small", "--mode", "zz"])
    assert caught.value.code == 2


def test_protocol_options_are_scoped_to_the_verbs_that_consume_them():
    from science.cli import build_parser

    declaration = Declaration(
        "small", "p", WriteClass("read-only"), MIN_OUTPUT_BUDGET, (), (), Path(".")
    )
    parser = build_parser((declaration,))
    assert vars(parser.parse_args(["mcp", "serve", "--config", "science.toml"])) == {
        "command": "mcp",
        "mode": "serve",
        "config": Path("science.toml"),
        "project": None,
    }
    # Launcher selection is scoped to `serve` and `mcp`.
    assert vars(parser.parse_args(["serve", "--config", "science.toml"])) == {
        "command": "serve",
        "run": None,
        "config": Path("science.toml"),
        "project": None,
    }
    for argv in (
        ["build", "--config", "science.toml"],
        ["build", "--invocation-id", "caller_id"],
        ["adapters", "build", "--continue", "cursor"],
        ["mcp", "serve", "--invocation-id", "caller_id"],
        ["mcp", "serve", "--continue", "cursor"],
        ["serve", "--invocation-id", "caller_id"],
        ["serve", "--continue", "cursor"],
    ):
        with pytest.raises(SystemExit) as caught:
            parser.parse_args(argv)
        assert caught.value.code == 2


def test_status_end_to_end(certified_work, capsys):
    from science.cli import main

    cfg_path = write_cli_config(certified_work)
    assert main(["status", "--config", str(cfg_path)]) == 0
    captured = capsys.readouterr()
    assert "World status" in captured.out
    metadata = json.loads(captured.err)
    assert re.fullmatch(r"[0-9a-f]{32}", metadata["invocation_id"])
    assert captured.err == json.dumps(metadata, sort_keys=True, separators=(",", ":")) + "\n"


def test_refusal_exits_3(certified_work, capsys):
    from science.cli import main

    cfg_path = write_cli_config(certified_work)
    assert main([
        "status", "--config", str(cfg_path), "--invocation-id", "caller_id",
        "--continue", "scur1.garbage",
    ]) == 3
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        '{"invocation_id":"caller_id","refusal":{"code":"unknown-cursor",'
        '"data":{},"message":"cursor does not parse"}}\n'
    )


def test_missing_config_exits_3(capsys, monkeypatch):
    from science.cli import main

    monkeypatch.delenv("SCIENCE_CONFIG", raising=False)
    assert main(["status"]) == 3
    captured = capsys.readouterr()
    refusal = json.loads(captured.err)
    assert re.fullmatch(r"[0-9a-f]{32}", refusal["invocation_id"])
    assert refusal["refusal"] == {
        "code": "invalid-input",
        "message": "no --config and no SCIENCE_CONFIG",
        "data": {},
    }
    assert captured.err == json.dumps(refusal, sort_keys=True, separators=(",", ":")) + "\n"


def test_usage_error_exits_2():
    from science.cli import main

    with pytest.raises(SystemExit) as caught:
        main(["status", "--unknown"])
    assert caught.value.code == 2


def test_read_dispatch_is_sessionless_and_writes_exact_text(certified_work, capsys, monkeypatch):
    import science.cli as cli
    from science.dispatch import Outcome

    cfg_path = write_cli_config(certified_work)

    class SessionlessDispatcher:
        def __init__(self, declarations, handlers, context, session=None, selection=None):
            assert session is None and selection is None

        def invoke(self, command, inputs, *, invocation_id=None, cursor=None, project=None):
            assert command == "status"
            assert inputs == {}
            assert re.fullmatch(r"[0-9a-f]{32}", invocation_id) and cursor is None and project is None
            return Outcome("dispatcher output", invocation_id)

    monkeypatch.setattr(cli, "Dispatcher", SessionlessDispatcher)
    assert cli.main(["status", "--config", str(cfg_path)]) == 0
    captured = capsys.readouterr()
    assert captured.out == "dispatcher output"
    assert re.fullmatch(r'\{"invocation_id":"[0-9a-f]{32}"\}\n', captured.err)


def test_unexpected_error_exits_1(capsys, monkeypatch):
    import science.cli as cli

    monkeypatch.setattr(cli, "production_tree", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert cli.main(["status"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == '{"error":{"code":"internal-error","message":"Internal error"}}\n'
    assert "boom" not in captured.err


def test_build_validates_the_command_tree(capsys):
    from science.cli import main, production_tree

    assert main(["build"]) == 0
    assert capsys.readouterr().out == f"ok: {len(production_tree())} command(s)\n"


def test_workflow_project_cli_prechecks_refuse_before_preparation_and_service(
    certified_work, capsys, monkeypatch
):
    import science.cli as cli
    import science.workflow_environment as wf_env

    cfg_path = write_cli_config(certified_work)
    prep_calls: list[object] = []
    service_calls: list[object] = []
    monkeypatch.setattr(wf_env, "prepare_environment", lambda p, ops: prep_calls.append((p, ops)) or "a" * 64)
    monkeypatch.setattr(cli, "_via_service", lambda *a, **kw: service_calls.append((a, kw)) or 0)

    proj = certified_work / "wf-proj"
    proj.mkdir()
    base = [
        "derive",
        "--config", str(cfg_path),
        "--dataset", "dataset:d1",
        "--code", str(certified_work),
        "--entrypoint", "code/Snakefile",
        "--targets", "out.txt",
        "--title", "t",
    ]

    # 1. Mutually exclusive --workflow-project and --workflow-environment
    rc = cli.main([*base, "--workflow-project", str(proj), "--workflow-environment", "a" * 64])
    assert rc == 3
    err = capsys.readouterr().err
    assert len(err.splitlines()) == 1
    meta = json.loads(err)
    assert meta["refusal"]["code"] == "invalid-input"
    assert "workflow_environment" not in meta

    # 2. --continue with --workflow-project refuses invalid-input directing caller to --workflow-environment <key>
    rc = cli.main([*base, "--workflow-project", str(proj), "--continue", "scur1.fake"])
    assert rc == 3
    err = capsys.readouterr().err
    assert len(err.splitlines()) == 1
    meta = json.loads(err)
    assert meta["refusal"]["code"] == "invalid-input"
    assert "--workflow-environment" in meta["refusal"]["message"]
    assert "workflow_environment" not in meta

    # 3. Handle mode rejects --workflow-project before preparation
    monkeypatch.delenv("SCIENCE_CONFIG", raising=False)
    monkeypatch.setenv("VERIFIABLY_ENDPOINT", str(certified_work / "ep.sock"))
    monkeypatch.setenv("VERIFIABLY_TOKEN_FILE", str(certified_work / "tok"))
    rc = cli.main([
        "derive",
        "--dataset", "dataset:d1",
        "--code", str(certified_work),
        "--entrypoint", "code/Snakefile",
        "--targets", "out.txt",
        "--title", "t",
        "--workflow-project", str(proj),
    ])
    assert rc == 3
    err = capsys.readouterr().err
    assert len(err.splitlines()) == 1
    meta = json.loads(err)
    assert meta["refusal"]["code"] == "handle-mode"
    assert "workflow_environment" not in meta

    assert prep_calls == []
    assert service_calls == []


@pytest.mark.parametrize("outcome_mode", ["success", "service-refusal", "transport-failure", "prep-failure"])
def test_workflow_project_cli_stderr_single_json_line_and_key_reporting(
    certified_work, short_tmp, capsys, monkeypatch, outcome_mode
):
    import socket
    import threading
    import science.cli as cli
    import science.workflow_environment as wf_env
    from science.refusal import Refusal, Refused

    sock_path = short_tmp / f"svc-{outcome_mode}.sock"
    cfg_path = write_cli_config(certified_work, service_socket=sock_path)
    proj = certified_work / f"proj-{outcome_mode}"
    proj.mkdir()
    key = "a" * 64

    def fake_prepare(project, ops_root):
        if outcome_mode == "prep-failure":
            raise Refused(Refusal("invalid-input", "stale lock"))
        return key

    monkeypatch.setattr(wf_env, "prepare_environment", fake_prepare)

    received: list[dict[str, object]] = []
    server_sock = None
    thread = None
    if outcome_mode in ("success", "service-refusal"):
        server_sock = socket.socket(socket.AF_UNIX)
        server_sock.settimeout(5)
        server_sock.bind(str(sock_path))
        server_sock.listen(1)

        def serve_once():
            try:
                conn, _ = server_sock.accept()
            except OSError:
                return
            with conn:
                req = json.loads(conn.makefile().readline())
                received.append(req)
                if outcome_mode == "success":
                    reply = {"ok": True, "text": "ok\n", "invocation_id": req["invocation_id"]}
                else:
                    reply = {
                        "ok": False,
                        "invocation_id": req["invocation_id"],
                        "refusal": {"code": "invalid-input", "message": "bad", "data": {}},
                    }
                conn.sendall(json.dumps(reply).encode() + b"\n")

        thread = threading.Thread(target=serve_once, daemon=True)
        thread.start()

    try:
        rc = cli.main([
            "run",
            "--config", str(cfg_path),
            "--invocation-id", "inv-wf-1",
            "--spec", "analysis-spec:s1",
            "--dataset", "dataset:d1",
            "--code", str(certified_work),
            "--entrypoint", "code/Snakefile",
            "--targets", "out.txt",
            "--workflow-project", str(proj),
        ])
    finally:
        if thread is not None:
            thread.join(timeout=5)
        if server_sock is not None:
            server_sock.close()

    captured = capsys.readouterr()
    lines = captured.err.splitlines()
    assert len(lines) == 1, f"expected 1 stderr JSON line, got: {lines!r}"
    meta = json.loads(lines[0])
    assert meta["invocation_id"] == "inv-wf-1"

    if outcome_mode == "prep-failure":
        assert rc == 3
        assert "workflow_environment" not in meta
        assert meta["refusal"]["code"] == "invalid-input"
    elif outcome_mode == "success":
        assert rc == 0
        assert meta["workflow_environment"] == key
        assert received and received[0]["inputs"]["workflow_environment"] == key
        assert "workflow_project" not in received[0]["inputs"]
    elif outcome_mode == "service-refusal":
        assert rc == 3
        assert meta["workflow_environment"] == key
        assert meta["refusal"]["code"] == "invalid-input"
    else:
        assert rc == 3
        assert meta["workflow_environment"] == key
        assert meta["refusal"]["code"] == "permit-exceeded"


def test_exposure_and_reservation_from_mint_to_query_over_the_cli(certified_work, short_tmp, tmp_path, capsys):
    import threading
    from helpers.reservation import assignment_facet, event_facet, write_payload
    from helpers.world import build_fixture_world_with_contract, write_config_for
    from science.cli import main
    from science.config import load_config
    from science.serve import serve

    config = write_config_for(build_fixture_world_with_contract(certified_work), service_socket=short_tmp / "service.sock")

    def run(code, command, *args):
        assert main([command, "--config", str(config), *args]) == code, capsys.readouterr().err
        captured = capsys.readouterr()
        return captured.out, json.loads(captured.err)

    event_path = write_payload(tmp_path, event_facet(), name="event.json")
    loaded = load_config(config)
    server = serve(loaded, loaded.service_socket)
    runner = threading.Thread(target=server.serve_forever)
    runner.start()
    try:
        first, _ = run(0, "exposure-event", "--payload", event_path, "--invocation-id", "EVENT-ONE")
        event = re.search(r"exposure-event:[0-9a-f]{64}", first)[0]
        assert run(0, "exposure-event", "--payload", event_path, "--invocation-id", "EVENT-ONE")[0] == first
        _, line = run(3, "exposure-event", "--payload", event_path, "--invocation-id", "EVENT-TWO")
        assert line["refusal"]["code"] == "invalid-input"
        assert line["refusal"]["data"]["existing"][0]["address"] == event
        assignment_path = write_payload(tmp_path, assignment_facet(events=[event]), name="assignment.json")
        minted, _ = run(0, "reservation-assignment", "--payload", assignment_path)
        head = re.search(r"reservation-assignment:[0-9a-f]{64}", minted)[0]
        for kind, address in (("exposure-event", event), ("reservation-assignment", head)):
            assert f"{kind}:\n  address: {address}\n" in run(0, "record", "--address", address)[0]
        assert "events: 1" in run(0, "exposure-log")[0]
        assert "events: 0" in run(0, "exposure-log", "--subject", "dataset:none", "--proposition", "proposition:none")[0]
        assert f"  head: {head}\n" in run(0, "reservation-head", "--chain", "mm-roster")[0]
        assert "  head: none\n" in run(0, "reservation-head", "--chain", "mm-roster", "--scope", "proposition:p1")[0]
        assert run(3, "exposure-log", "--subject", "GSE24080")[1]["refusal"]["data"] == {"field": "subject"}
    finally:
        server.shutdown()
        runner.join()
        server.server_close()


@pytest.mark.parametrize("args,missing", [
    (["exposure-event"], "--payload"), (["reservation-assignment"], "--payload"), (["reservation-head"], "--chain"),
])
def test_exposure_and_reservation_commands_require_their_input(args, missing, capsys):
    from science.cli import main

    with pytest.raises(SystemExit) as caught:
        main(args)
    assert caught.value.code == 2 and missing in capsys.readouterr().err
