"""Spec §5.2, §5.3 and P8: a read in any process finds the live session's selection."""
import io
import json
import re
import socket
import socketserver
import subprocess
import sys
import threading
from contextlib import contextmanager
from dataclasses import replace

import pytest

from helpers.world import QUERY, build_fixture_world, mint_projects, write_cli_config
from test_mcp_socket import _BlockingStdin, _request, _wait_for

LAUNCHERS = ("serve", "mcp serve")


@contextmanager
def launcher(kind, config_path, sock):
    """One of the two launchers, live on a thread until the block ends."""
    if kind == "serve":
        from science.config import load_config
        from science.serve import serve

        server = serve(load_config(config_path), sock, stderr=io.StringIO())
        thread = threading.Thread(target=server.serve_forever)
        thread.start()
        try:
            yield
        finally:
            server.shutdown()
            thread.join(timeout=30)
            server.server_close()
            assert not thread.is_alive()
        return
    from science.mcp import serve as mcp_serve

    stdin = _BlockingStdin()
    thread = threading.Thread(target=mcp_serve, args=(config_path,),
                              kwargs={"stdin": io.BufferedReader(stdin), "stdout": io.StringIO(),
                                      "stderr": io.StringIO()}, daemon=True)
    thread.start()
    try:
        _wait_for(sock)
        yield
    finally:
        stdin.release()
        thread.join(timeout=30)
        assert not thread.is_alive()
        stdin.close()  # only now: the reader thread is done with the fd


def _cli(*args):
    return subprocess.run([sys.executable, "-m", "science.cli", *args],
                          capture_output=True, text=True, timeout=120)


def _mint(sock, name):
    reply = _request(sock, {"command": "project", "inputs": {"name": name, "query": QUERY}})
    return "coord:" + re.search(r"project:([0-9a-f]{32})\.", reply["text"]).group(1)


def _ledger_lines(config_path):
    from science.config import load_config

    root = load_config(config_path).operations_root / "sessions"
    return sum(len(path.read_text().splitlines()) for path in root.glob("*/ledger.v1"))


@pytest.mark.parametrize("kind", LAUNCHERS)
def test_a_new_process_reads_the_live_sessions_selection(certified_work, short_tmp, kind):
    """P8: selected through the endpoint, observed by a fresh CLI process;
    `--project` observes another project and changes nothing."""
    sock = short_tmp / "service.sock"
    config_path = write_cli_config(certified_work, service_socket=sock)
    with launcher(kind, config_path, sock):
        health = _mint(sock, "health")
        _mint(sock, "cancer")
        # The CLI routes the `session` class to whichever launcher bound the socket.
        selected = _cli("project-select", "--config", str(config_path), "--target", "health")
        shown = _cli("project-show", "--config", str(config_path))
        other = _cli("project-show", "--config", str(config_path), "--project", "cancer")
        listed = _cli("projects", "--config", str(config_path))
        after = _request(sock, {"query": "selection"})
    assert selected.returncode == 0 and selected.stdout.startswith(f"selected: {health}@"), selected.stderr
    assert shown.returncode == 0 and shown.stdout.startswith("## Project: health\n"), shown.stderr
    assert other.returncode == 0 and other.stdout.startswith("## Project: cancer\n"), other.stderr
    assert listed.stdout.count("(selected)") == 1 and f"{health}: health" in listed.stdout
    assert after == {"project": health}


@pytest.mark.parametrize("kind", LAUNCHERS)
def test_the_query_answers_from_state_and_ledgers_nothing(certified_work, short_tmp, kind):
    sock = short_tmp / "service.sock"
    config_path = write_cli_config(certified_work, service_socket=sock)
    with launcher(kind, config_path, sock):
        health = _mint(sock, "health")
        assert _request(sock, {"query": "selection"}) == {"project": None}
        _request(sock, {"command": "project-select", "inputs": {"target": "health"}})
        before = _ledger_lines(config_path)
        assert _request(sock, {"query": "selection"}) == {"project": health}  # no invocation id in or out
        assert _ledger_lines(config_path) == before
        unknown = _request(sock, {"query": "epoch"})
        mixed = _request(sock, {"query": "selection", "command": "status"})
        for query in (None, True, 1, [], {}):
            invalid = _request(sock, {"query": query})
            assert invalid["ok"] is False and invalid["refusal"]["code"] == "invalid-input"
    assert unknown["ok"] is False and unknown["refusal"]["code"] == "invalid-input"
    assert mixed["ok"] is False and mixed["refusal"]["code"] == "invalid-input"


def test_each_launcher_refuses_to_start_beside_the_other(certified_work, short_tmp):
    from science.config import load_config
    from science.mcp import serve as mcp_serve
    from science.refusal import Refused
    from science.serve import serve

    sock = short_tmp / "service.sock"
    config_path = write_cli_config(certified_work, service_socket=sock)
    with launcher("mcp serve", config_path, sock):
        with pytest.raises(Refused):
            serve(load_config(config_path), sock)
    with launcher("serve", config_path, sock):
        with pytest.raises(Refused):
            mcp_serve(config_path, stdin=io.BytesIO(), stdout=io.StringIO(), stderr=io.StringIO())


def _config_with_default(work, sock):
    cfg = replace(build_fixture_world(work), service_socket=sock)
    (health,) = mint_projects(cfg, "health")
    return replace(cfg, default_project=health), health


def test_with_no_session_live_a_read_takes_the_default_project(certified_work, short_tmp):
    from science.cli import _ambient_selection

    cfg, health = _config_with_default(certified_work, short_tmp / "service.sock")
    assert _ambient_selection(cfg) == health
    assert _ambient_selection(replace(cfg, default_project=None)) is None


def test_a_stale_socket_reads_as_no_live_session(certified_work, short_tmp):
    """A crashed launcher leaves its socket file; connecting to it is refused."""
    from science.cli import _ambient_selection

    sock = short_tmp / "service.sock"
    cfg, health = _config_with_default(certified_work, sock)
    dead = socket.socket(socket.AF_UNIX)
    dead.bind(str(sock))
    dead.close()  # the file stays; nothing listens
    assert sock.exists()
    assert _ambient_selection(cfg) == health


def test_a_socket_path_no_launcher_could_bind_reads_as_no_live_session(certified_work, short_tmp):
    from science.cli import _ambient_selection

    cfg, health = _config_with_default(certified_work, short_tmp / ("s" * 200 + ".sock"))
    assert _ambient_selection(cfg) == health


def test_a_live_sessions_null_is_the_answer_not_the_default(certified_work, short_tmp):
    from science.cli import _ambient_selection
    from science.serve import serve

    sock = short_tmp / "service.sock"
    cfg, health = _config_with_default(certified_work, sock)
    server = serve(cfg, sock, stderr=io.StringIO())
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        assert _ambient_selection(cfg) == health
        _request(sock, {"command": "project-select", "inputs": {"clear": True}})
        assert _ambient_selection(cfg) is None
    finally:
        server.shutdown()
        thread.join(timeout=30)
        server.server_close()
        assert not thread.is_alive()


@pytest.mark.parametrize("answer", [
    b'{"ok": true}\n', b'not json\n', b'[]\n', b'{"project": false}\n',
    b'{"project": "health"}\n',
    b'{"project": "coord:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa@bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}\n',
    b'{"project": "coord:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/cccccccccccccccccccccccccccccccc"}\n',
])
def test_a_listener_that_answers_something_else_is_an_internal_error(certified_work, short_tmp, capsys, answer):
    """A live session the read could not ask is not an absent one (spec §5.2)."""
    from science.cli import main

    sock = short_tmp / "service.sock"
    config_path = write_cli_config(certified_work, service_socket=sock)

    class Garbage(socketserver.StreamRequestHandler):
        def handle(self):
            self.rfile.readline()
            self.wfile.write(answer)

    server = socketserver.ThreadingUnixStreamServer(str(sock), Garbage)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        assert main(["projects", "--config", str(config_path)]) == 1
    finally:
        server.shutdown()
        thread.join(timeout=30)
        server.server_close()
        assert not thread.is_alive()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err)["error"]["code"] == "internal-error"


def test_a_read_with_project_does_not_ask_the_socket(certified_work, short_tmp, capsys, monkeypatch):
    import science.cli as cli

    sock = short_tmp / "service.sock"
    config_path = write_cli_config(certified_work, service_socket=sock)
    from science.config import load_config
    (health,) = mint_projects(load_config(config_path), "health")
    monkeypatch.setattr(cli, "_ambient_selection", lambda config: pytest.fail("step 1 binds the invocation"))
    assert cli.main(["project-show", "--config", str(config_path), "--project", "health"]) == 0
    assert capsys.readouterr().out.startswith("## Project: health\n")


def test_a_live_listener_timeout_is_an_internal_error(certified_work, short_tmp, capsys, monkeypatch):
    import science.cli as cli
    from science.config import load_config

    sock = short_tmp / "service.sock"
    config_path = write_cli_config(certified_work, service_socket=sock)
    (health,) = mint_projects(load_config(config_path), "health")
    config_path.write_text(config_path.read_text() + f'default_project = "{health}"\n')
    monkeypatch.setattr(cli, "_SELECTION_TIMEOUT_SECONDS", 0.05)
    release = threading.Event()

    class Silent(socketserver.StreamRequestHandler):
        def handle(self):
            self.rfile.readline()
            release.wait(timeout=30)

    server = socketserver.ThreadingUnixStreamServer(str(sock), Silent)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        assert cli.main(["project-show", "--config", str(config_path)]) == 1
    finally:
        release.set()
        server.shutdown()
        thread.join(timeout=30)
        server.server_close()
        assert not thread.is_alive()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err)["error"]["code"] == "internal-error"
