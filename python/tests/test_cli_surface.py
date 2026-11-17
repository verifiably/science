"""science's parser surface equals its rows in tools/cli.toml; help, version, and usage
errors follow the CLI vocabulary. science is a protocol CLI: its envelope and exit-3
refusals are covered by test_cli.py and are not under the general output contract."""
import importlib.util
import io
import os
import tempfile
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from helpers.world import write_cli_config
from science.cli import build_parser, main, production_tree

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("cli_surface", ROOT / "tools" / "cli_surface.py")
cli_surface = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli_surface)
TABLE = ROOT / "tools" / "cli.toml"
COMMANDS = sorted(row[1] for row in cli_surface.table_rows(TABLE, "science") if row[0] == "command")


def run(*args):
    with tempfile.TemporaryDirectory() as home:
        return subprocess.run([sys.executable, "-m", "science.cli", *args], capture_output=True, text=True,
                              env={"PATH": os.environ["PATH"], "HOME": home, "PYTHONDONTWRITEBYTECODE": "1"})


def invoke(capsys, *args):
    """`main` in-process: help and usage errors leave through argparse's SystemExit.
    A spawned interpreter costs about a second under a loaded xdist run, so only
    test_version pays for one, to keep the module entry point covered."""
    capsys.readouterr()
    try:
        code = main(list(args))
    except SystemExit as exit:
        code = exit.code
    out = capsys.readouterr()
    return SimpleNamespace(returncode=code, stdout=out.out, stderr=out.err)


def test_surface_equals_table():
    live = cli_surface.argparse_rows(build_parser(production_tree()))
    assert cli_surface.diff(live, cli_surface.table_rows(TABLE, "science")) == []


@pytest.mark.parametrize("path", [()] + COMMANDS, ids=lambda p: " ".join(p) or "root")
def test_help_on_every_command(path, capsys):
    for flag in ("--help", "-h"):
        out = invoke(capsys, *path, flag)
        assert (out.returncode, out.stderr) == (0, "") and out.stdout, (path, flag)
    if path:
        assert invoke(capsys, "help", *path).stdout == invoke(capsys, *path, "--help").stdout


def test_version():
    for flag in ("--version", "-V"):
        out = run(flag)
        assert out.returncode == 0 and out.stdout.startswith("science ")


@pytest.mark.parametrize("args", [["bogus"], ["status", "--bogus"], ["mcp"], ["help", "bogus"]])
def test_usage_error_exits_two(args, capsys):
    out = invoke(capsys, *args)
    assert out.returncode == 2 and out.stdout == "" and out.stderr.strip()
    assert len(out.stderr.strip().splitlines()) <= 2


def test_enum_baselines_cover_every_enum_row(certified_work, monkeypatch, capsys):
    cfg = str(write_cli_config(certified_work))
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(b"")))
    baselines = {
        (("mcp",), "mode"): ["mcp", "serve", "--config", cfg],          # serve returns at stdin EOF
        (("adapters",), "mode"): ["adapters", "build", "--out", str(certified_work / "adapters")],  # a real build, into the fixture; adapters takes no --config
    }
    table = {(row[1], row[3]) for row in cli_surface.table_rows(TABLE, "science") if row[0] == "arg" and "enum" in row}
    assert set(baselines) == table, "every enum row needs a baseline"
    for (path, _), argv in baselines.items():
        assert main(argv) == 0, argv
        bad = list(argv); bad[len(path)] = "__not_in_set__"
        out = invoke(capsys, *bad)
        assert out.returncode == 2 and "mode" in out.stderr and "__not_in_set__" in out.stderr, bad


def test_native_spec_inputs_and_belief_key_parse_with_required_repeating_fields():
    parser = build_parser(production_tree())
    base = ["spec", "--target", "proposition:p1", "--dataset", "dataset:d1", "--estimand", "estimand.json",
            "--standing", "empirical", "--evidence-mode", "observation", "--rule-procedures", "rule=procedure:p1",
            "--method", "fit", "--assumptions", "iid", "--falsification", "null", "--interpretation-rule", "rule",
            "--equivalence-rule", "equivalence"]
    namespace = parser.parse_args(base + ["--rule-procedures", "equivalence=procedure:p2",
                                        "--registers", "register:a", "--registers", "register:b"])
    assert namespace.estimand == "estimand.json"
    assert namespace.rule_procedures == ["rule=procedure:p1", "equivalence=procedure:p2"]
    assert namespace.registers == ["register:a", "register:b"]
    for flag in ("--estimand", "--standing", "--evidence-mode", "--rule-procedures"):
        missing = base.copy()
        index = missing.index(flag)
        del missing[index:index+2]
        with pytest.raises(SystemExit) as caught:
            parser.parse_args(missing)
        assert caught.value.code == 2
    for mode in ("observation", "annotation", "simulation", "derivation", "literature-extraction"):
        args = base.copy()
        args[args.index("--evidence-mode") + 1] = mode
        assert parser.parse_args(args).evidence_mode == mode
    assert parser.parse_args(["belief", "--proposition", "proposition:p1", "--key", "target-key"]).key == "target-key"
