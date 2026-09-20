"""science's parser surface equals its rows in tools/cli.toml; help, version, and usage
errors follow the CLI vocabulary. science is a protocol CLI: its envelope and exit-3
refusals are covered by test_cli.py and are not under the general output contract."""
import importlib.util
import io
import subprocess
import sys
from pathlib import Path

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
    return subprocess.run([sys.executable, "-m", "science.cli", *args], capture_output=True, text=True)


def test_surface_equals_table():
    live = cli_surface.argparse_rows(build_parser(production_tree()))
    assert cli_surface.diff(live, cli_surface.table_rows(TABLE, "science")) == []


@pytest.mark.parametrize("path", [()] + COMMANDS, ids=lambda p: " ".join(p) or "root")
def test_help_on_every_command(path):
    for flag in ("--help", "-h"):
        out = run(*path, flag)
        assert (out.returncode, out.stderr) == (0, "") and out.stdout, (path, flag)
    if path:
        assert run("help", *path).stdout == run(*path, "--help").stdout


def test_version():
    for flag in ("--version", "-V"):
        out = run(flag)
        assert out.returncode == 0 and out.stdout.startswith("science ")


@pytest.mark.parametrize("args", [["bogus"], ["status", "--bogus"], ["mcp"], ["help", "bogus"]])
def test_usage_error_exits_two(args):
    out = run(*args)
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
        out = run(*bad)
        assert out.returncode == 2 and "mode" in out.stderr and "__not_in_set__" in out.stderr, bad
