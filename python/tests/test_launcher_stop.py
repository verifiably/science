"""A launcher stopped the ordinary way — SIGTERM from an MCP client or a
service manager, SIGHUP from a closed terminal — runs its cleanup: the socket
it bound is gone, so the next launcher can start, and its session ledger
ends in `session-close`."""
import json
import signal
import subprocess
import sys
import time

import pytest

from helpers.world import write_cli_config

LAUNCHERS = {"mcp serve": ["mcp", "serve"], "serve": ["serve"]}
STARTUP_SECONDS = 60
STOP_SECONDS = 15
SURVIVAL_SECONDS = 1  # bounded wait: a launcher that dies on an ignored signal exits well within this


def _reset_sighup(disposition):
    """A `preexec_fn` that fixes the child's SIGHUP disposition, regardless of
    the disposition it would otherwise inherit from the process running the
    tests (e.g. SIG_IGN under `nohup`)."""
    def _preexec():
        signal.signal(signal.SIGHUP, disposition)
    return _preexec


def _wait_for_socket(child, sock, deadline):
    while not sock.exists():
        assert child.poll() is None, child.stderr.read().decode()
        assert time.monotonic() < deadline, "the launcher never bound its socket"
        time.sleep(0.05)


@pytest.mark.parametrize("stop", [signal.SIGTERM, signal.SIGHUP], ids=["SIGTERM", "SIGHUP"])
@pytest.mark.parametrize("launcher", sorted(LAUNCHERS))
def test_a_stopped_launcher_removes_its_socket_and_closes_its_session(certified_work, short_tmp, launcher, stop):
    from science.config import load_config

    sock = short_tmp / "service.sock"
    config_path = write_cli_config(certified_work, service_socket=sock)
    operations_root = load_config(config_path).operations_root
    child = subprocess.Popen(
        [sys.executable, "-m", "science.cli", *LAUNCHERS[launcher], "--config", str(config_path)],
        stdin=subprocess.PIPE,  # held open: an MCP server exits on EOF, which is not this test
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        # The suite itself may run under nohup, which starts with SIGHUP
        # ignored; force SIG_DFL so a SIGHUP case exercises the launcher's
        # own handler rather than an inherited ignore.
        preexec_fn=_reset_sighup(signal.SIG_DFL) if stop == signal.SIGHUP else None,
    )
    try:
        deadline = time.monotonic() + STARTUP_SECONDS
        _wait_for_socket(child, sock, deadline)
        child.send_signal(stop)
        _, stderr = child.communicate(timeout=STOP_SECONDS)
        assert child.returncode == 128 + stop, stderr.decode()
        assert not sock.exists()
        (ledger,) = (operations_root / "sessions").glob("*/ledger.v1")
        assert json.loads(ledger.read_text().splitlines()[-1])["line"] == "session-close"
    finally:
        if child.poll() is None:
            child.kill()
        child.communicate()  # reaps the child and closes its pipes


@pytest.mark.parametrize("launcher", sorted(LAUNCHERS))
def test_a_launcher_with_sighup_ignored_survives_a_sighup(certified_work, short_tmp, launcher):
    """A launcher that inherits SIGHUP as SIG_IGN (as it does under `nohup`)
    must stay ignored: the launcher's own stop-signal handling must not
    override an inherited ignore."""
    sock = short_tmp / "service.sock"
    config_path = write_cli_config(certified_work, service_socket=sock)
    child = subprocess.Popen(
        [sys.executable, "-m", "science.cli", *LAUNCHERS[launcher], "--config", str(config_path)],
        stdin=subprocess.PIPE,  # held open: an MCP server exits on EOF, which is not this test
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        preexec_fn=_reset_sighup(signal.SIG_IGN),
    )
    try:
        deadline = time.monotonic() + STARTUP_SECONDS
        _wait_for_socket(child, sock, deadline)
        child.send_signal(signal.SIGHUP)
        time.sleep(SURVIVAL_SECONDS)
        assert child.poll() is None, "the launcher exited on a SIGHUP it should have ignored"
        child.send_signal(signal.SIGTERM)
        _, stderr = child.communicate(timeout=STOP_SECONDS)
        assert child.returncode == 128 + signal.SIGTERM, stderr.decode()
        assert not sock.exists()
    finally:
        if child.poll() is None:
            child.kill()
        child.communicate()  # reaps the child and closes its pipes


@pytest.mark.parametrize("window", ["opening-the-session", "after-the-bind"])
@pytest.mark.parametrize("launcher", sorted(LAUNCHERS))
def test_a_stop_signal_in_a_startup_window_still_cleans_up(certified_work, short_tmp, monkeypatch, launcher, window):
    """A stop signal that lands while the session is opening, or after the
    socket is bound but before the launcher's cleanup owns it, still leaves no
    socket and closes the session. The signal is sent from inside the window,
    in-process: the handler only runs in the main thread, as here."""
    import os
    import threading

    import science.serve as serve_module
    import science.session as session_module
    from science.cli import main
    from science.config import load_config

    assert threading.current_thread() is threading.main_thread()
    sock = short_tmp / "service.sock"
    config_path = write_cli_config(certified_work, service_socket=sock)
    operations_root = load_config(config_path).operations_root
    module, name = (session_module, "open_session") if window == "opening-the-session" else (
        serve_module, "service_server")
    real = getattr(module, name)

    def signalled(*args, **kwargs):
        made = real(*args, **kwargs)
        os.kill(os.getpid(), signal.SIGTERM)
        return made

    monkeypatch.setattr(module, name, signalled)
    with pytest.raises(SystemExit) as caught:
        main([*LAUNCHERS[launcher], "--config", str(config_path)])
    assert caught.value.code == 128 + signal.SIGTERM
    assert not sock.exists()
    (ledger,) = (operations_root / "sessions").glob("*/ledger.v1")
    assert json.loads(ledger.read_text().splitlines()[-1])["line"] == "session-close"


def test_a_stop_signal_during_mcp_serves_eof_drain_lets_the_write_finish(certified_work, short_tmp, monkeypatch, capsys):
    """An MCP client closes stdin, then sends SIGTERM (the MCP stdio shutdown
    order) while a CLI write over the socket is still in flight: the drain
    still completes, the write closes its invocation before the session closes,
    and the launcher then exits on the deferred signal."""
    import io
    import os
    import socket
    import threading

    import science.dispatch as dispatch_module
    from helpers.world import QUERY
    from science.mcp import serve
    from science.stop import stop_signals_exit

    assert threading.current_thread() is threading.main_thread()
    sock = short_tmp / "service.sock"
    config_path = write_cli_config(certified_work, service_socket=sock)
    entered, release = threading.Event(), threading.Event()
    invoke = dispatch_module.Dispatcher.invoke

    def held(self, *args, **kwargs):
        entered.set()
        assert release.wait(timeout=30)
        return invoke(self, *args, **kwargs)

    monkeypatch.setattr(dispatch_module.Dispatcher, "invoke", held)
    import science.serve as serve_module
    servers, build = [], serve_module.service_server
    monkeypatch.setattr(serve_module, "service_server",
                        lambda *args, **kwargs: servers.append(build(*args, **kwargs)) or servers[-1])
    read_end, write_end = os.pipe()
    replies = []

    def client():
        try:
            deadline = time.monotonic() + STARTUP_SECONDS
            while not sock.exists():
                assert time.monotonic() < deadline
                time.sleep(0.05)
            with socket.socket(socket.AF_UNIX) as s:
                s.connect(str(sock))
                s.sendall(json.dumps({"command": "project", "inputs": {"name": "health", "query": QUERY},
                                      "invocation_id": "G" * 8, "cursor": None}).encode() + b"\n")
                replies.append(json.loads(s.makefile().readline()))
        finally:
            release.set()

    def stopper():
        try:
            assert entered.wait(timeout=STARTUP_SECONDS)
        finally:
            os.close(write_end)  # EOF: mcp serve begins its cleanup and drains the write
        deadline = time.monotonic() + STOP_SECONDS
        while not servers[0]._closing:  # the drain has begun
            assert time.monotonic() < deadline
            time.sleep(0.01)
        os.kill(os.getpid(), signal.SIGTERM)
        time.sleep(0.3)
        release.set()

    threads = [threading.Thread(target=client), threading.Thread(target=stopper)]
    for thread in threads:
        thread.start()
    try:
        with pytest.raises(SystemExit) as caught, stop_signals_exit(), open(read_end, "rb") as stdin:
            serve(config_path, stdin=stdin, stdout=io.StringIO(), stderr=io.StringIO())
    finally:
        release.set()
        for thread in threads:
            thread.join(timeout=30)
    assert caught.value.code == 128 + signal.SIGTERM
    assert replies and replies[0]["ok"], replies
    (ledger,) = (load_operations_root(config_path) / "sessions").glob("*/ledger.v1")
    lines = [json.loads(line) for line in ledger.read_text().splitlines()]
    assert lines[-1]["line"] == "session-close"
    assert any(line["line"] == "invocation-close" and line["invocation"] == "G" * 8 for line in lines)
    assert "Traceback" not in capsys.readouterr().err
    assert not sock.exists()


def load_operations_root(config_path):
    from science.config import load_config
    return load_config(config_path).operations_root


@pytest.mark.parametrize("ends", ["normally", "on-an-error"])
def test_a_held_stop_signal_raises_at_release_unless_an_error_ends_the_hold(ends):
    import os
    import threading

    from science.stop import stop_signals_exit, stop_signals_held

    assert threading.current_thread() is threading.main_thread()
    expected = SystemExit if ends == "normally" else RuntimeError
    with pytest.raises(expected) as caught, stop_signals_exit(), stop_signals_held():
        os.kill(os.getpid(), signal.SIGTERM)
        time.sleep(0.05)  # the handler has run, and deferred the stop
        if ends == "on-an-error":
            raise RuntimeError("the launcher's own failure")
    if ends == "normally":
        assert caught.value.code == 128 + signal.SIGTERM


def test_a_held_cleanup_reports_the_startup_error_over_a_stop_deferred_at_startup():
    """`mcp serve`'s shape: a stop deferred while starting, a startup failure,
    then cleanup under its own hold. The failure is what ends the launcher."""
    import os
    import threading

    from science.stop import stop_signals_exit, stop_signals_held

    assert threading.current_thread() is threading.main_thread()
    with pytest.raises(RuntimeError), stop_signals_exit(), stop_signals_held():
        try:
            os.kill(os.getpid(), signal.SIGTERM)
            time.sleep(0.05)
            raise RuntimeError("the session did not open")
        finally:
            with stop_signals_held():
                pass
