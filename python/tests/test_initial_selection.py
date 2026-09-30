"""Spec §5.1, §6: the launcher's initial selection and `default_project`."""
import io
import json
import socket
import threading
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import pytest

from helpers.world import (
    QUERY, build_fixture_world, build_world_without_coordination, mint_projects, write_cli_config,
)
from science.refusal import Refused

QUESTION = {"command": "question", "inputs": {"name": "q", "query": QUERY}}


def _ask(sock, payload):
    with socket.socket(socket.AF_UNIX) as client:
        client.connect(str(sock))
        client.sendall(json.dumps(payload).encode() + b"\n")
        return json.loads(client.makefile().readline())


@contextmanager
def _serving(cfg, sock, **kwargs):
    from science.serve import serve

    server = serve(cfg, sock, stderr=io.StringIO(), **kwargs)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def _recorded_selections(cfg):
    """The `project` of every session-open line under the operations root."""
    ledgers = sorted((cfg.operations_root / "sessions").glob("*/ledger.v1"))
    return [json.loads(path.read_text().splitlines()[0])["project"] for path in ledgers]


def test_serve_opens_under_the_default_project_and_ledgers_it(certified_work, short_tmp):
    from science.config import ReadContext

    cfg = build_fixture_world(certified_work)
    (health,) = mint_projects(cfg, "health")
    sock = short_tmp / "service.sock"
    with _serving(replace(cfg, default_project=health), sock):
        reply = _ask(sock, QUESTION)
    assert reply["ok"] and f"question:{health.project}." in reply["text"]
    revision = ReadContext.open(cfg).coordination().resolve(health).uid
    # The minting session opened with nothing selected; the launcher's is pinned.
    assert sorted(_recorded_selections(cfg), key=str) == sorted([None, f"{health}@{revision}"], key=str)


@pytest.mark.parametrize("named", ["name", "address"])
def test_the_launchers_project_wins_over_the_default(certified_work, short_tmp, named):
    cfg = build_fixture_world(certified_work)
    health, cancer = mint_projects(cfg, "health", "cancer")
    sock = short_tmp / "service.sock"
    project = "cancer" if named == "name" else str(cancer)
    with _serving(replace(cfg, default_project=health), sock, project=project):
        reply = _ask(sock, QUESTION)
    assert reply["ok"] and f"question:{cancer.project}." in reply["text"]


def test_with_neither_the_session_opens_unselected(certified_work, short_tmp):
    cfg = build_fixture_world(certified_work)
    mint_projects(cfg, "health")
    sock = short_tmp / "service.sock"
    with _serving(cfg, sock):
        reply = _ask(sock, QUESTION)
    assert reply["refusal"]["code"] == "no-current-project"


def test_a_default_that_names_no_project_refuses_the_start(certified_work, short_tmp):
    from beliefs.coordination import CoordinationAddress
    from science.serve import serve

    cfg = build_fixture_world(certified_work)
    sock = short_tmp / "service.sock"
    with pytest.raises(Refused) as caught:
        serve(replace(cfg, default_project=CoordinationAddress("f" * 32)), sock)
    assert caught.value.refusal.code == "unknown-project"
    assert not sock.exists()
    assert not (cfg.operations_root / "sessions").exists()  # refused before the session opened


def test_a_launcher_project_that_names_no_project_refuses_the_start(certified_work, short_tmp):
    from science.serve import serve

    cfg = build_fixture_world(certified_work)
    sock = short_tmp / "service.sock"
    with pytest.raises(Refused) as caught:
        serve(cfg, sock, project="nope")
    assert caught.value.refusal.code == "unknown-project"
    assert not sock.exists() and not (cfg.operations_root / "sessions").exists()


def test_a_launcher_project_without_coordination_refuses_naming_the_setting(certified_work, short_tmp):
    from science.serve import serve

    cfg = build_world_without_coordination(certified_work)
    with pytest.raises(Refused) as caught:
        serve(cfg, short_tmp / "service.sock", project="health")
    assert caught.value.refusal.code == "invalid-input"
    assert "coordination = false" in caught.value.refusal.message
    assert not (cfg.operations_root / "sessions").exists()


def _with_default(config_path, address):
    config_path.write_text(config_path.read_text() + f'default_project = "{address}"\n')
    return config_path


def test_mcp_serve_opens_under_the_default_project(certified_work, short_tmp):
    from science.config import load_config
    from science.mcp import serve
    from test_mcp import rpc

    config_path = write_cli_config(certified_work, service_socket=short_tmp / "service.sock")
    (health,) = mint_projects(load_config(config_path), "health")
    _with_default(config_path, health)
    call = rpc("tools/call", {"name": "question", "arguments": QUESTION["inputs"]})
    stdout = io.StringIO()
    serve(config_path, stdin=io.BytesIO((json.dumps(call) + "\n").encode()), stdout=stdout, stderr=io.StringIO())
    (line,) = stdout.getvalue().splitlines()
    assert f"question:{health.project}." in json.loads(line)["result"]["content"][0]["text"]


def test_mcp_serve_refuses_a_default_that_names_no_project(certified_work, short_tmp):
    from science.config import load_config
    from science.mcp import serve

    sock = short_tmp / "service.sock"
    config_path = _with_default(write_cli_config(certified_work, service_socket=sock), "coord:" + "f" * 32)
    with pytest.raises(Refused) as caught:
        serve(config_path, stdin=io.BytesIO(), stdout=io.StringIO(), stderr=io.StringIO())
    assert caught.value.refusal.code == "unknown-project"
    assert not sock.exists()
    assert not (load_config(config_path).operations_root / "sessions").exists()


def test_both_launcher_verbs_take_project(monkeypatch):
    import science.mcp as mcp
    from science.cli import build_parser, main
    from science.loader import production_tree

    parser = build_parser(production_tree())
    assert parser.parse_args(["serve", "--project", "health"]).project == "health"
    assert parser.parse_args(["mcp", "serve", "--project", "health"]).project == "health"
    captured = []
    monkeypatch.setattr(mcp, "serve", lambda path, project=None: captured.append((path, project)))
    assert main(["mcp", "serve", "--config", "science.toml", "--project", "health"]) == 0
    assert captured == [(Path("science.toml"), "health")]
