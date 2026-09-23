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
    }
    # `serve` consumes --config and nothing else (registered by Task 13).
    assert vars(parser.parse_args(["serve", "--config", "science.toml"])) == {
        "command": "serve",
        "config": Path("science.toml"),
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
        def __init__(self, declarations, handlers, context, session=None):
            assert session is None

        def invoke(self, command, inputs, *, invocation_id=None, cursor=None):
            assert command == "status"
            assert inputs == {}
            assert re.fullmatch(r"[0-9a-f]{32}", invocation_id) and cursor is None
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
