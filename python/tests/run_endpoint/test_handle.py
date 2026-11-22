"""Run actor authentication precedes every service operation."""
import os
import socket
from unittest.mock import Mock

import pytest

from science.refusal import Refused


def test_host_peer_with_token_is_refused_before_query_or_continuation():
    from science.run_endpoint.handle import authenticate
    with socket.socket(socket.AF_UNIX) as endpoint:
        with pytest.raises(Refused) as caught:
            authenticate(endpoint, None, b"a" * 64, "a" * 64)
    assert caught.value.refusal.code == "bad-peer"


def test_token_is_checked_without_echoing_its_value():
    from science.run_endpoint.handle import authenticate
    a, b = socket.socketpair()
    namespace = os.open("/proc/self/ns/pid", os.O_RDONLY)
    try:
        with a, b:
            authenticate(b, namespace, b"a" * 64, "a" * 64)
            with pytest.raises(Refused) as caught:
                authenticate(b, namespace, b"a" * 64, "private-value")
            assert caught.value.refusal.code == "bad-token"
            assert "private-value" not in str(caught.value)
    finally:
        os.close(namespace)


@pytest.mark.parametrize("command", ["run", "derive"])
def test_job_requests_without_child_control_refuse_before_dispatch(command):
    from science.run_endpoint.handle import answer
    dispatcher = Mock()
    reply = answer(dispatcher, {"command": command, "inputs": {}, "invocation_id": "job"}, can_execute=False)
    assert reply["refusal"]["code"] == "confinement-unavailable"
    dispatcher.invoke.assert_not_called()
    dispatcher.invoke.return_value.text = "read"
    dispatcher.invoke.return_value.invocation_id = "read"
    assert answer(dispatcher, {"command": "status"}, can_execute=False)["text"] == "read"


@pytest.mark.parametrize("primitive", ["children", "open_pidfd", "signal_pidfd"])
def test_unavailable_child_primitive_refuses_jobs_without_ledger_or_chain_writes(certified_work, monkeypatch, primitive):
    from beliefs.root import log_seam
    from science.loader import production_tree, resolve_handlers
    from science.config import ReadContext
    from science.dispatch import Dispatcher
    from science.run_endpoint import drain
    from science.run_endpoint.handle import answer
    from beliefs.permit import WritePermit
    from beliefs.session import open_run_session
    from helpers.world import build_fixture_world

    def unavailable(*args):
        raise OSError("primitive unavailable")
    monkeypatch.setattr(drain, primitive, unavailable)
    available = drain.can_control_jobs()
    assert not available
    cfg = build_fixture_world(certified_work)
    session = open_run_session(cfg.world, cfg.operations_root, write_root=cfg.write_root,
                               profile=cfg.profile, ceiling=WritePermit.from_json(
                                   {"kinds": [], "act_families": [], "ungoverned": False}))
    try:
        from beliefs.session.ledger import ledger_path
        decls = production_tree()
        dispatcher = Dispatcher(decls, resolve_handlers(decls), ReadContext.open(cfg), session=session)
        ledger = ledger_path(cfg.operations_root, session.session_id)
        before = ledger.read_bytes()
        tips = [log_seam().inspect_detached(root).tip for root in (cfg.write_root, cfg.store_root)]
        for command in ("run", "derive"):
            reply = answer(dispatcher, {"command": command, "inputs": {}, "invocation_id": command}, can_execute=available)
            assert reply["refusal"]["code"] == "confinement-unavailable"
        assert answer(dispatcher, {"command": "status"}, can_execute=available)["ok"] is True
        assert ledger.read_bytes() == before
        assert [log_seam().inspect_detached(root).tip for root in (cfg.write_root, cfg.store_root)] == tips
    finally:
        session.close()


def test_certified_child_control():
    from science.run_endpoint.drain import can_control_jobs
    assert can_control_jobs()


@pytest.mark.parametrize("data", [b"{}\n", b"null\n", b'{"token":"never-echo",bad}\n', b"partial"])
def test_malformed_actor_frame_is_refused_without_disclosure(data):
    from science.run_endpoint.handle import receive_actor
    local, remote = socket.socketpair()
    with local, remote:
        local.sendall(data)
        local.shutdown(socket.SHUT_WR)
        with pytest.raises(Refused) as refused:
            receive_actor(remote, None, b"a" * 64)
        assert refused.value.refusal.code == "invalid-input"
        assert "never-echo" not in str(refused.value)


def test_example_actor_frame():
    from pathlib import Path
    from science.run_endpoint.handle import receive_actor
    a, b = socket.socketpair()
    ns = os.open("/proc/self/ns/pid", os.O_RDONLY)
    try:
        with a, b:
            a.sendall((Path(__file__).parents[1] / "fixtures/run_endpoint/actor.v1.jsonl").read_bytes())
            assert receive_actor(b, ns, b"0" * 64) == {"command": "status", "inputs": {}}
    finally:
        os.close(ns)
