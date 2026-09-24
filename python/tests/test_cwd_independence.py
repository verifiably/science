"""P1 (projects design §10): no configuration is discovered from the working
directory, and a configuration's relative paths resolve against the file."""
import json
from pathlib import Path

import pytest

from helpers.world import build_fixture_world, DOMAINS


def _relative_config(work: Path) -> Path:
    """The fixture world's launcher TOML with every path relative to `work`."""
    cfg = build_fixture_world(work)
    path = work / "science.toml"
    path.write_text(
        'world_root = "world"\n'
        f'world_id = "{cfg.world.world_id}"\n'
        'corpus_roots = ["corpus"]\n'
        'operations_root = "ops"\n'
        f"domains = {list(DOMAINS)!r}\n"
        "contracts = []\n"
        'store_root = "store"\n'
        "coordination = 2\n"
    )
    return path


def _decoy(where: Path) -> Path:
    """A directory holding every file the predecessor discovered from cwd."""
    where.mkdir()
    (where / "science.yaml").write_text("project: decoy\n")
    (where / "science.toml").write_text('world_root = "/nowhere"\n')
    (where / "corpus.yaml").write_text("corpus: decoy\n")
    return where


def test_status_reads_the_configured_world_from_a_decoy_directory(certified_work, tmp_path, monkeypatch, capsys):
    from science.cli import main

    config = _relative_config(certified_work)
    monkeypatch.chdir(certified_work)
    assert main(["status", "--config", str(config)]) == 0
    from_home = capsys.readouterr().out
    monkeypatch.chdir(_decoy(tmp_path / "decoy"))
    assert main(["status", "--config", str(config)]) == 0
    assert capsys.readouterr().out == from_home


def test_no_config_is_discovered_from_the_working_directory(tmp_path, monkeypatch, capsys):
    from science.cli import main

    monkeypatch.chdir(_decoy(tmp_path / "decoy"))
    monkeypatch.delenv("SCIENCE_CONFIG", raising=False)
    assert main(["status"]) == 3  # refused: no --config and no SCIENCE_CONFIG
    refusal = json.loads(capsys.readouterr().err)["refusal"]
    assert refusal["code"] == "invalid-input"
    assert "SCIENCE_CONFIG" in refusal["message"]


def test_mcp_serve_reads_the_configured_world_from_a_decoy_directory(certified_work, tmp_path, monkeypatch):
    import io

    from science.mcp import serve
    from test_mcp import rpc

    config = _relative_config(certified_work)
    monkeypatch.chdir(_decoy(tmp_path / "decoy"))
    stdout = io.StringIO()
    stdin = io.BytesIO((json.dumps(rpc("tools/call", {"name": "status", "arguments": {}})) + "\n").encode())
    serve(config, stdin=stdin, stdout=stdout, stderr=io.StringIO())
    (line,) = stdout.getvalue().splitlines()
    assert "World status" in json.loads(line)["result"]["content"][0]["text"]
