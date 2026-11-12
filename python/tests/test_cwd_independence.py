"""P1: no configuration is discovered from the working
directory, and a configuration's relative paths resolve against the file."""
import io
import json
import socket
import threading
from pathlib import Path

import pytest

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
        + ("" if "service_socket" in extra else f'service_socket = "{cfg.service_socket}"\n')
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


def _default_project_config(work: Path, extra: str = "") -> tuple[Path, object]:
    """A relative-path configuration whose `default_project` is a standing project."""
    from helpers.world import mint_projects
    from science.config import load_config

    config = _relative_config(work, extra=extra)
    (health,) = mint_projects(load_config(config), "health")
    config.write_text(config.read_text() + f'default_project = "{health}"\n')
    return config, health


def test_a_cli_read_takes_the_selection_the_file_names_from_a_decoy_directory(certified_work, tmp_path,
                                                                             monkeypatch, capsys):
    from science.cli import main

    config, _ = _default_project_config(certified_work)
    monkeypatch.chdir(certified_work)
    assert main(["project-show", "--config", str(config)]) == 0
    from_home = capsys.readouterr().out
    monkeypatch.chdir(_decoy(tmp_path / "decoy"))
    assert main(["project-show", "--config", str(config)]) == 0
    assert capsys.readouterr().out == from_home
    assert from_home.startswith("## Project: health\n")


@pytest.mark.parametrize("kind", ["serve", "mcp serve"])
def test_a_launcher_opens_under_the_selection_the_file_names_from_a_decoy_directory(
        certified_work, short_tmp, tmp_path, monkeypatch, kind):
    from test_mcp_socket import _request
    from test_selection_query import launcher

    sock = short_tmp / "service.sock"
    config, health = _default_project_config(certified_work, extra=f'service_socket = "{sock}"\n')
    monkeypatch.chdir(_decoy(tmp_path / "decoy"))
    with launcher(kind, config, sock):
        assert _request(sock, {"query": "selection"}) == {"project": str(health)}


def test_cli_spec_reads_the_client_source_path_with_service_in_another_directory(
        certified_work, short_tmp, tmp_path, monkeypatch, capsys):
    import os
    import signal
    import subprocess
    import sys
    import time
    from decimal import Decimal
    from beliefs import stored
    from helpers.analysis import spec_inputs
    from helpers.world import build_belief_world, hold_fixture_dataset, write_config_for
    from science.cli import main
    from science.config import ReadContext
    from test_launcher_stop import _wait_for_socket

    cfg = build_belief_world(certified_work)
    data = hold_fixture_dataset(cfg, "data.txt", b"observations\n", "observations")
    inputs = spec_inputs(cfg, target="proposition:p1", dataset=data)
    client, server, home = (tmp_path / name for name in ("client", "server", "child-home"))
    for directory in (client, server, home):
        directory.mkdir()
    filename = "authoring.json"
    (client / filename).write_bytes(Path(inputs["estimand"]).read_bytes())
    (server / filename).write_text('{"schema_version": false}')
    inputs["estimand"] = filename
    sock = short_tmp / "service.sock"
    config = write_config_for(cfg, service_socket=sock)
    # No inherited environment or credentials enter the service process.
    environment = {"PATH": os.environ["PATH"], "HOME": str(home), "PYTHONDONTWRITEBYTECODE": "1"}
    child = subprocess.Popen([sys.executable, "-m", "science.cli", "serve", "--config", str(config)],
        cwd=server, env=environment, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    try:
        _wait_for_socket(child, sock, time.monotonic() + 30)
        monkeypatch.chdir(client)
        argv = ["spec", "--config", str(config)]
        for key, value in inputs.items():
            for item in value if isinstance(value, list) else [value]:
                argv.extend(("--" + key.replace("_", "-"), str(item)))
        assert main(argv) == 0, capsys.readouterr().err
        text = capsys.readouterr().out
        assert "[analysis-spec]" in text
    finally:
        if child.poll() is None:
            child.send_signal(signal.SIGTERM)
        try:
            _, stderr = child.communicate(timeout=15)
        finally:
            if child.poll() is None:
                child.kill()
                child.communicate()
    assert child.returncode == 128 + signal.SIGTERM, stderr.decode()
    assert not sock.exists()
    spec, = [n for n in ReadContext.open(cfg).write_view().iter_stored() if n.kind == "analysis-spec"]
    assert stored.analysis_spec_value(spec, profile=cfg.profile).estimand.reference.value == Decimal("0.5")
