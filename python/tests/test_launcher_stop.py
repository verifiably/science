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
