import json
import io
import re
import socket
import threading

import pytest

from science.serve import serve
from helpers.world import build_fixture_world


@pytest.mark.parametrize("state", ["clean", "unclosed", "failing-stream"])
def test_startup_findings(certified_work, tmp_path, state):
    """An open peer produces session-unclosed, even while alive; classification
    of uncovered commits as session-outcome-unknown belongs to beliefs."""
    from beliefs.session import open_attended_session

    cfg = build_fixture_world(certified_work)
    peer = None
    if state != "clean":
        peer = open_attended_session(cfg.world, cfg.operations_root, profile=cfg.profile)
        peer.claim_invocation("unfinished", "test-command", "a" * 64)

    class FailingStream:
        def write(self, text):
            raise OSError("stderr unavailable")

    stderr = FailingStream() if state == "failing-stream" else io.StringIO()
    socket_path = tmp_path / "service.sock"
    try:
        if state == "failing-stream":
            with pytest.raises(OSError, match="stderr unavailable"):
                serve(cfg, socket_path, stderr=stderr)
            assert not socket_path.exists()
        else:
            server = serve(cfg, socket_path, stderr=stderr)
            try:
                if peer is None:
                    assert stderr.getvalue() == ""
                else:
                    (line,) = stderr.getvalue().splitlines()
                    finding = json.loads(line)
                    assert finding["code"] == "session-unclosed"
                    assert finding["ref"] == peer.session_id
                    assert "unfinished" in finding["detail"]
                    assert re.fullmatch(r"[0-9a-f]{32}", finding["reported_by"])
                    assert finding["reported_by"] != peer.session_id
            finally:
                server.server_close()
        (ledger,) = [path for path in (cfg.operations_root / "sessions").glob("*/ledger.v1")
                     if peer is None or path.parent.name != peer.session_id]
        assert json.loads(ledger.read_text().splitlines()[-1])["line"] == "session-close"
    finally:
        if peer is not None:
            peer.close()


# The certified work root is long and AF_UNIX caps the socket path at 107
# bytes, so every bound socket lives under the short `tmp_path` instead.
def _running(cfg, sock_path, **kwargs):
    server = serve(cfg, sock_path, **kwargs)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _ask(sock_path, payload):
    with socket.socket(socket.AF_UNIX) as s:
        s.connect(str(sock_path))
        s.sendall(json.dumps(payload).encode() + b"\n")
        return json.loads(s.makefile().readline())


def test_service_round_trip_and_cli_routing(certified_work, tmp_path):
    from helpers.synthetic import synthetic_decls_and_handlers
    cfg = build_fixture_world(certified_work)
    decls, handlers = synthetic_decls_and_handlers()
    sock_path = tmp_path / "service.sock"
    server = _running(cfg, sock_path, declarations=decls, handlers=handlers)
    try:
        with socket.socket(socket.AF_UNIX) as s:
            s.connect(str(sock_path))
            s.sendall(json.dumps({"command": "mint-claim", "inputs": {"slug": "hi"},
                                  "invocation_id": None, "cursor": None}).encode() + b"\n")
            reply = json.loads(s.makefile().readline())
        assert reply["ok"] and "proposition:hi" in reply["text"]
        assert len(reply["invocation_id"]) == 32
    finally:
        server.shutdown()
        server.server_close()


def test_service_refusal_carries_envelope_and_replays(certified_work, tmp_path):
    from helpers.synthetic import synthetic_decls_and_handlers
    cfg = build_fixture_world(certified_work)
    decls, handlers = synthetic_decls_and_handlers()
    sock_path = tmp_path / "service.sock"
    server = _running(cfg, sock_path, declarations=decls, handlers=handlers)
    try:
        req = {"command": "overreach", "inputs": {}, "invocation_id": "K" * 8,
               "cursor": None}
        first = _ask(sock_path, req)
        again = _ask(sock_path, req)
        assert not first["ok"]
        assert set(first["refusal"]) == {"code", "message", "data"}
        assert first["invocation_id"] == "K" * 8
        assert again == first  # code, message, data, id — all replay exactly
    finally:
        server.shutdown()
        server.server_close()


def test_malformed_requests_get_structured_refusals_on_one_connection(certified_work, tmp_path):
    """Bad JSON and bad shapes all come back as invalid-input replies over a
    SINGLE connection — the handler loop survives every malformed line and
    still serves a valid request afterwards."""
    from helpers.synthetic import synthetic_decls_and_handlers
    cfg = build_fixture_world(certified_work)
    decls, handlers = synthetic_decls_and_handlers()
    sock_path = tmp_path / "service.sock"
    server = _running(cfg, sock_path, declarations=decls, handlers=handlers)
    try:
        with socket.socket(socket.AF_UNIX) as s:
            s.connect(str(sock_path))
            reader = s.makefile()
            for raw in (b"{not json",
                        b'["not", "an", "object"]',
                        b'{"command": 7, "inputs": {}}',
                        b'{"command": "mint-claim", "inputs": ["list"]}',
                        b'{"command": "mint-claim", "inputs": {}, "cursor": 3}',
                        b'{"command": "mint-claim", "inputs": {}, "stray": true}'):
                s.sendall(raw + b"\n")
                reply = json.loads(reader.readline())
                assert reply["ok"] is False
                assert reply["refusal"]["code"] == "invalid-input"
            s.sendall(json.dumps({"command": "mint-claim",
                                  "inputs": {"slug": "after"}}).encode() + b"\n")
            final = json.loads(reader.readline())
            reader.close()  # makefile holds the socket open past the with-block
        assert final["ok"] and "proposition:after" in final["text"]
    finally:
        server.shutdown()
        server.server_close()


def test_server_close_failure_still_closes_session(certified_work, tmp_path, monkeypatch):
    """The finally holds: even when socket teardown raises, the session's
    ledger ends with session-close."""
    import socketserver
    cfg = build_fixture_world(certified_work)
    server = serve(cfg, tmp_path / "service.sock")

    def boom(self):
        raise OSError("teardown failed")

    monkeypatch.setattr(socketserver.ThreadingUnixStreamServer, "server_close", boom)
    with pytest.raises(OSError):
        server.server_close()
    ledgers = list((cfg.operations_root / "sessions").glob("*/ledger.v1"))
    assert len(ledgers) == 1
    last = json.loads(ledgers[0].read_text().splitlines()[-1])
    assert last["line"] == "session-close"


def test_setup_failure_after_the_session_opens_closes_it(certified_work, tmp_path):
    """A socket whose parent is a regular file fails after the session opened —
    the constructor must close it on the way out, which the ledger's
    session-close line proves."""
    cfg = build_fixture_world(certified_work)
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("")
    with pytest.raises(OSError):
        serve(cfg, blocker / "service.sock")  # the parent mkdir raises
    ledgers = list((cfg.operations_root / "sessions").glob("*/ledger.v1"))
    assert len(ledgers) == 1
    last = json.loads(ledgers[0].read_text().splitlines()[-1])
    assert last["line"] == "session-close"


def test_overlong_socket_path_refuses_before_the_session(certified_work, tmp_path):
    """Past the AF_UNIX limit, `bind` raises a bare `OSError: AF_UNIX path too
    long`. Refuse first, naming the path and the limit — and before the session
    exists, so nothing leaks into the ledger."""
    from science.refusal import Refused
    from science.serve import MAX_SOCKET_PATH_BYTES
    cfg = build_fixture_world(certified_work)
    long_sock = tmp_path / ("s" * 200 + ".sock")
    with pytest.raises(Refused) as caught:
        serve(cfg, long_sock)
    assert caught.value.refusal.code == "invalid-input"
    assert str(MAX_SOCKET_PATH_BYTES) in caught.value.refusal.message
    assert not (cfg.operations_root / "sessions").exists()


def test_existing_socket_refuses_startup(certified_work, tmp_path):
    from science.refusal import Refused
    cfg = build_fixture_world(certified_work)
    sock_path = tmp_path / "service.sock"
    sock_path.parent.mkdir(parents=True, exist_ok=True)
    sock_path.touch()  # a stale socket is the operator's to remove
    with pytest.raises(Refused):
        serve(cfg, sock_path)
    # The refusal precedes session opening, so nothing leaked into the ledger.
    assert not (cfg.operations_root / "sessions").exists()


def test_cli_write_without_service_refuses(certified_work, tmp_path, capsys):
    """No socket: exit 3 with the same JSON refusal wire as every command."""
    import argparse
    from science.cli import _via_service
    from helpers.synthetic import MINT_CLAIM
    from helpers.world import write_cli_config
    cfg_path = write_cli_config(certified_work, operations_root=tmp_path / "ops")
    ns = argparse.Namespace(config=str(cfg_path), invocation_id=None, cursor=None)
    code = _via_service(ns, MINT_CLAIM, {"slug": "x"})
    assert code == 3
    payload = json.loads(capsys.readouterr().err)
    assert payload["refusal"]["code"] == "permit-exceeded"
    assert "science serve" in payload["refusal"]["message"]
    assert payload["invocation_id"]


def test_cli_write_routes_through_service(certified_work, tmp_path, capsys):
    """The success path end to end: CLI -> socket -> dispatcher -> reply."""
    import argparse
    from science.cli import _via_service
    from science.config import load_config
    from helpers.synthetic import MINT_CLAIM, synthetic_decls_and_handlers
    from helpers.world import write_cli_config
    cfg_path = write_cli_config(certified_work, operations_root=tmp_path / "ops")
    cfg = load_config(cfg_path)
    decls, handlers = synthetic_decls_and_handlers()
    server = _running(cfg, cfg.operations_root / "service.sock",
                      declarations=decls, handlers=handlers)
    try:
        ns = argparse.Namespace(config=str(cfg_path), invocation_id=None, cursor=None)
        code = _via_service(ns, MINT_CLAIM, {"slug": "via"})
        captured = capsys.readouterr()
        assert code == 0
        assert "proposition:via" in captured.out
        assert json.loads(captured.err)["invocation_id"]
    finally:
        server.shutdown()
        server.server_close()
