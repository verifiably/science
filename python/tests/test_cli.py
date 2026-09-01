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
        "config": "science.toml",
        "invocation_id": "caller_id",
        "cursor": "scur1.cursor",
    }
    with pytest.raises(SystemExit) as caught:
        parser.parse_args(["small", "--mode", "zz"])
    assert caught.value.code == 2


def test_status_end_to_end(certified_work, capsys):
    from science.cli import main

    cfg_path = write_cli_config(certified_work)
    assert main(["status", "--config", str(cfg_path)]) == 0
    assert "World status" in capsys.readouterr().out


def test_refusal_exits_3(certified_work, capsys):
    from science.cli import main

    cfg_path = write_cli_config(certified_work)
    assert main(["status", "--config", str(cfg_path), "--continue", "scur1.garbage"]) == 3
    assert "refused [unknown-cursor]" in capsys.readouterr().err


def test_missing_config_exits_3(capsys, monkeypatch):
    from science.cli import main

    monkeypatch.delenv("SCIENCE_CONFIG", raising=False)
    assert main(["status"]) == 3
    assert capsys.readouterr().err == "refused [invalid-input] no --config and no SCIENCE_CONFIG\n"


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
            assert invocation_id is None and cursor is None
            return Outcome("dispatcher output", "id")

    monkeypatch.setattr(cli, "Dispatcher", SessionlessDispatcher)
    assert cli.main(["status", "--config", str(cfg_path)]) == 0
    assert capsys.readouterr().out == "dispatcher output"


def test_unexpected_error_exits_1(capsys, monkeypatch):
    import science.cli as cli

    monkeypatch.setattr(cli, "production_tree", lambda: (_ for _ in ()).throw(RuntimeError("boom")))
    assert cli.main(["status"]) == 1
    assert capsys.readouterr().err == "internal error: boom\n"


def test_build_validates_the_command_tree(capsys):
    from science.cli import main

    assert main(["build"]) == 0
    assert capsys.readouterr().out == "ok: 1 command(s)\n"
