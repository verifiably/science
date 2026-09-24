"""P1 (projects design §10): no configuration is discovered from the working
directory, and a configuration's relative paths resolve against the file."""
import io
import json
import socket
import threading
from pathlib import Path

from helpers.world import build_fixture_world, build_fixture_world_with_contract, DOMAINS


def _relative_config(work: Path, *, build=build_fixture_world, contracts=(), extra: str = "") -> Path:
    """The fixture world's launcher TOML with every path relative to `work`."""
    cfg = build(work)
    path = work / "science.toml"
    path.write_text(
        'world_root = "world"\n'
        f'world_id = "{cfg.world.world_id}"\n'
        'corpus_roots = ["corpus"]\n'
        'operations_root = "ops"\n'
        f"domains = {list(DOMAINS)!r}\n"
        f"contracts = {list(contracts)!r}\n"
        'store_root = "store"\n'
        "coordination = 2\n"
        + extra
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


def test_serve_reads_the_configured_world_from_a_decoy_directory(certified_work, short_tmp, tmp_path, monkeypatch,
                                                                 capsys):
    """P1's `science serve` arm: the service launched from a decoy directory
    answers over its socket from the world the file names. The socket is an
    absolute short path: AF_UNIX caps it at 107 bytes."""
    from science.cli import main
    from science.config import load_config
    from science.serve import serve

    sock = short_tmp / "service.sock"
    config = _relative_config(certified_work, extra=f'service_socket = "{sock}"\n')
    monkeypatch.chdir(certified_work)
    assert main(["status", "--config", str(config)]) == 0
    from_home = capsys.readouterr().out
    monkeypatch.chdir(_decoy(tmp_path / "decoy"))
    loaded = load_config(config)
    server = serve(loaded, loaded.service_socket, stderr=io.StringIO())
    runner = threading.Thread(target=server.serve_forever)
    runner.start()
    try:
        with socket.socket(socket.AF_UNIX) as connection:
            connection.connect(str(sock))
            connection.sendall(json.dumps({"command": "status"}).encode() + b"\n")
            reply = json.loads(connection.makefile().readline())
    finally:
        server.shutdown()
        runner.join()
        server.server_close()
    assert reply["ok"] is True
    assert reply["text"] == from_home


def test_a_relative_contracts_entry_resolves_against_the_file(certified_work, tmp_path, monkeypatch):
    """P1 for `contracts`: the contract document beside the file compiles into
    the profile from a decoy directory, which holds no such document."""
    from science.config import load_config

    config = _relative_config(certified_work, build=build_fixture_world_with_contract,
                              contracts=["testing.yaml"])
    monkeypatch.chdir(certified_work)
    from_home = load_config(config).profile.compiled_identity
    monkeypatch.chdir(_decoy(tmp_path / "decoy"))
    assert load_config(config).profile.compiled_identity == from_home
