"""Persistence of the supervisor's seal witness."""
import json
import os

import pytest


def test_seal_file_is_synced_before_and_after_replacement(tmp_path, monkeypatch):
    from science.run_endpoint.service import persist_seal
    from science.run_endpoint.control import wire
    name = tmp_path / "seal.json"
    document = {"cause": "stop", "basis_seal": None, "sealed_tips": []}
    calls = []
    fsync = os.fsync

    def sync(fd):
        calls.append(name.exists())
        fsync(fd)

    monkeypatch.setattr(os, "fsync", sync)
    persist_seal(tmp_path, document)
    assert calls == [False, True]
    assert name.read_bytes() == wire(document)
    assert name.stat().st_mode & 0o777 == 0o600


@pytest.mark.parametrize("after_rename", [False, True])
def test_failed_sync_propagates_and_leaves_only_the_published_name(tmp_path, monkeypatch, after_rename):
    from science.run_endpoint.service import persist_seal
    name = tmp_path / "seal.json"

    def sync(fd):
        if name.exists() == after_rename:
            raise OSError("sync failed")

    monkeypatch.setattr(os, "fsync", sync)
    with pytest.raises(OSError, match="sync failed"):
        persist_seal(tmp_path, {"cause": "eof"})
    assert list(tmp_path.iterdir()) == ([name] if after_rename else [])
    if after_rename:
        assert json.loads(name.read_bytes()) == {"cause": "eof"}


def test_repeated_sweep_uses_one_deadline():
    from science.run_endpoint.drain import drain_workers
    elapsed = 0.0
    sweeps = []

    def wait(duration):
        nonlocal elapsed
        elapsed += duration

    def sweep():
        sweeps.append(elapsed)

    assert drain_workers(lambda: elapsed >= 0.1, sweep, 1.0, clock=lambda: elapsed, wait=wait)
    assert sweeps == pytest.approx([0, 0.05, 0.1, 0.1])
    elapsed = 0.0
    assert not drain_workers(lambda: False, sweep, 0.12, clock=lambda: elapsed, wait=wait)
    assert elapsed == pytest.approx(0.12)


@pytest.mark.parametrize("cause", ["stop", "eof", "term"])
def test_service_closes_ledger_after_persisting_seal(launch_file, cause):
    import signal
    import socket
    import threading
    from pathlib import Path
    from science.run_endpoint.control import wire
    from science.run_endpoint.launch import read_launch
    from science.run_endpoint.service import serve_run

    source, doc = launch_file
    # Take over the disposable supervisor path with a listener owned by this test.
    path = Path(doc["control_socket"])
    path.unlink()
    reports = []
    errors = []
    with socket.socket(socket.AF_UNIX) as supervisor:
        supervisor.bind(str(path))
        supervisor.listen(1)
        supervisor.settimeout(20)

        def supervise():
            try:
                connection, _ = supervisor.accept()
                with connection, connection.makefile("rb") as stream:
                    connection.settimeout(20)
                    reports.append(json.loads(stream.readline()))
                    if cause == "eof":
                        return
                    if cause == "stop":
                        connection.sendall(wire({"type": "seal", "version": "control.v1"}))
                    else:
                        os.kill(os.getpid(), signal.SIGTERM)
                    reports.append(json.loads(stream.readline()))
            except Exception as error:
                errors.append(error)

        peer = threading.Thread(target=supervise)
        peer.start()
        try:
            result = serve_run(read_launch(source))
        finally:
            peer.join(25)
    assert not peer.is_alive()
    assert errors == []
    assert result == 0
    document = json.loads((Path(doc["run_dir"]) / "seal.json").read_bytes())
    assert document["cause"] == cause
    assert document["sealed_tips"]
    if cause != "eof":
        assert reports[1] == {"version": "control.v1", "type": "sealed", **document}
    assert json.loads(Path(reports[0]["ledger_path"]).read_bytes().splitlines()[-1])["line"] == "session-close"
    assert not Path(doc["socket"]).exists()


@pytest.mark.parametrize("fault", ["ledger", "hold", "unclosed", "sync", "basis"])
def test_failure_evidence_uses_the_original_session(tmp_path, monkeypatch, fault, capfd):
    from types import SimpleNamespace
    from unittest.mock import Mock
    from beliefs.errors import SessionLedgerFailed, SealTimeout
    from beliefs.session.writer import ChainTip, SealedTips
    from science.run_endpoint import service
    from science.run_endpoint.control import wire

    session = Mock(session_id="a"*32, current_invocation=None)
    session.seal.return_value = SealedTips(ChainTip("a"*32, "1"*64, "1"*64),
                                          ChainTip("b"*32, "2"*64, "6"*64))
    launch = SimpleNamespace(run_dir=tmp_path, seal_timeout_seconds=1,
                             config=SimpleNamespace(operations_root=tmp_path))
    actors = Mock(can_execute=False)
    actors.scratch.owned = {}
    actors.finished.return_value = True
    actors.failed.is_set.return_value = False
    control = Mock(writable=False)
    if fault == "hold":
        session.seal.side_effect = SealTimeout("held")
    elif fault == "ledger":
        session.seal.side_effect = SessionLedgerFailed("append failed")
    elif fault == "unclosed":
        session.current_invocation = "one"
    elif fault == "sync":
        def failed_parent_sync(fd):
            if (tmp_path / "seal.json").exists():
                raise OSError("parent sync")
        monkeypatch.setattr(os, "fsync", failed_parent_sync)
    monkeypatch.setattr(service, "seal_basis", lambda *args: None)
    result = service._shutdown(launch, SimpleNamespace(session=session, basis={}), actors, control, "eof", lambda: 10)
    path = tmp_path / "seal.json"
    if fault == "basis":
        from pathlib import Path
        samples = Path(__file__).parents[1] / "fixtures/run_endpoint"
        assert result == 0
        assert path.read_bytes() == (samples / "seal.json").read_bytes()
        assert wire(control.queue.call_args.args[0]) == (samples / "sealed.control.v1.jsonl").read_bytes()
        session.close.assert_called_once_with()
    else:
        assert result == 1
        session.close.assert_not_called()
        assert path.exists() == (fault == "sync")
        assert control.queue.call_args.args[0]["type"] == ("seal-timeout" if fault == "hold" else "seal-failed")
        assert json.loads(capfd.readouterr().err)["session"] == session.session_id


def test_kernel_shutdown_waits_for_an_admitted_claim_to_close(certified_work, tmp_path):
    import threading
    from pathlib import Path
    from types import SimpleNamespace
    from unittest.mock import Mock
    from beliefs.permit import WritePermit
    from beliefs.session import open_run_session
    from beliefs.session.ledger import ledger_path
    from helpers.world import build_fixture_world
    from science.run_endpoint import service
    from science.run_endpoint.basis import open_basis
    from science.run_endpoint.paths import Scratch

    cfg = build_fixture_world(certified_work)
    session = open_run_session(cfg.world, cfg.operations_root, write_root=cfg.write_root,
                               profile=cfg.profile, ceiling=WritePermit(frozenset(), frozenset()))
    claimed = threading.Event()
    after_seal = threading.Event()
    original = session.seal
    with Scratch(tmp_path, cfg.operations_root, threading.Event()) as scratch:
        actors = service._Actors(b"", scratch, False, {"note"})

        def work():
            with actors.condition:
                actors.pending.add(threading.get_ident())
            session.claim_invocation("request", "note", "0"*64)
            claimed.set()
            assert after_seal.wait(8)
            session.close_invocation("request", {"refusal": {"code": "run-sealed", "message": "sealed", "data": {}}})
            actors.complete()

        def seal(timeout):
            tips = original(timeout)
            after_seal.set()
            return tips

        session.seal = seal
        worker = threading.Thread(target=work)
        worker.start()
        try:
            assert claimed.wait(5)
            launch = SimpleNamespace(run_dir=tmp_path, config=cfg, seal_timeout_seconds=5)
            opened = SimpleNamespace(session=session, basis=open_basis(cfg))
            result = service._shutdown(launch, opened, actors, Mock(writable=False), "stop", service.time.monotonic)
            assert result == 0
        finally:
            after_seal.set()
            worker.join(10)
            session.close()
    ledger = Path(ledger_path(cfg.operations_root, session.session_id))
    assert [json.loads(row)["line"] for row in ledger.read_bytes().splitlines()][-2:] == ["invocation-close", "session-close"]


def test_lease_expires_with_an_incomplete_control_frame(launch_file):
    import socket
    import threading
    from pathlib import Path
    from science.run_endpoint.launch import read_launch
    from science.run_endpoint.service import serve_run

    source, doc = launch_file
    now = [0.0]
    path = Path(doc["control_socket"])
    path.unlink()
    replies = []
    with socket.socket(socket.AF_UNIX) as supervisor:
        supervisor.bind(str(path))
        supervisor.listen(1)
        supervisor.settimeout(10)

        def renew():
            conn, _ = supervisor.accept()
            with conn, conn.makefile("rb") as stream:
                conn.settimeout(10)
                replies.append(json.loads(stream.readline()))
                conn.sendall(b'{"type":"renew","version":"control.v1"}\n')
                replies.append(json.loads(stream.readline()))
                conn.sendall(b'{"type":"ren')
                now[0] = 90
                replies.append(json.loads(stream.readline()))

        peer = threading.Thread(target=renew)
        peer.start()
        try:
            assert serve_run(read_launch(source), clock=lambda: now[0]) == 0
        finally:
            peer.join(12)
    assert [r["type"] for r in replies] == ["open", "renewed", "sealed"]
    assert replies[-1]["cause"] == "lease"


@pytest.mark.parametrize("cut", ["capture", "store"])
def test_seal_during_dataset_request_preserves_committed_effects(certified_work, tmp_path, monkeypatch, cut):
    import hashlib
    import threading
    from types import SimpleNamespace
    from unittest.mock import Mock

    from beliefs.holdings import boundary
    from beliefs.permit import WritePermit
    from beliefs.session import open_run_session
    from beliefs.session.ledger import ledger_path
    from helpers.world import build_fixture_world
    from science.config import ReadContext
    from science.dispatch import Dispatcher
    from science.loader import production_tree, resolve_handlers
    from science.run_endpoint import service
    from science.run_endpoint.basis import open_basis
    from science.run_endpoint.paths import Scratch

    cfg = build_fixture_world(certified_work)
    source = tmp_path / "data.txt"
    source.write_bytes(b"some data")
    decl = next(d for d in production_tree() if d.name == "dataset")
    permit = WritePermit(frozenset(decl.write_class.kinds), frozenset(decl.write_class.routes.values()))
    session = open_run_session(cfg.world, cfg.operations_root, write_root=cfg.write_root, profile=cfg.profile,
                               store_root=cfg.store_root, ceiling=permit)
    arrived, release = threading.Event(), threading.Event()
    replies = []
    try:
        with Scratch(tmp_path, cfg.operations_root, threading.Event()) as scratch:
            owner, name = (scratch, "_copy") if cut == "capture" else (boundary, "_publish_record")
            original = getattr(owner, name)

            def stopped(*args, **kwargs):
                arrived.set()
                assert release.wait(10)
                return original(*args, **kwargs)
            monkeypatch.setattr(owner, name, stopped)
            actors = service._Actors(b"", scratch, False, {"dataset"})
            dispatcher = Dispatcher([decl], resolve_handlers([decl]), ReadContext.open(cfg),
                                    session=session, run_inputs=scratch, on_invocation_close=actors.complete)
            request = {"command": "dataset", "invocation_id": "data", "inputs": {"path": str(source), "title": "small table"}}
            worker = threading.Thread(target=lambda: replies.append(actors._dispatch(dispatcher, request)))
            control = Mock(writable=False)
            control.receive.side_effect = lambda: release.set()
            basis = open_basis(cfg)
            worker.start()
            try:
                assert arrived.wait(8)
                result = service._shutdown(SimpleNamespace(config=cfg, run_dir=tmp_path, seal_timeout_seconds=6),
                                           SimpleNamespace(session=session, basis=basis), actors, control, "stop", service.time.monotonic)
            finally:
                release.set()
                worker.join(12)
            assert result == 0
    finally:
        session.close()
    assert replies[0]["refusal"]["code"] == "run-sealed"
    rows = [json.loads(row) for row in ledger_path(cfg.operations_root, session.session_id).read_bytes().splitlines()]
    assert [r["line"] for r in rows[-2:]] == ["invocation-close", "session-close"]
    content_path = cfg.store_root / hashlib.sha256(source.read_bytes()).hexdigest() / source.name
    if cut == "capture":
        assert rows[-2]["outcome"]["refusal"]["code"] == "run-sealed"
        assert not content_path.exists()
    else:
        assert rows[-2]["outcome"] == {"done": []}
        assert content_path.read_bytes() == source.read_bytes()
    assert not (cfg.operations_root / "capture/data").exists()


def test_renewal_during_drain_gets_a_refusal(tmp_path, monkeypatch):
    import socket
    from types import SimpleNamespace
    from unittest.mock import Mock
    from beliefs.session.writer import ChainTip, SealedTips
    from science.run_endpoint import service
    from science.run_endpoint.control import Control, wire

    launch = SimpleNamespace(config=SimpleNamespace(operations_root=tmp_path), run_dir=tmp_path, seal_timeout_seconds=1)
    session = Mock(current_invocation=None)
    session.seal.return_value = SealedTips(ChainTip("a"*32, "1"*64, "1"*64), None)
    actors = Mock(can_execute=False)
    actors.finished.return_value = True
    actors.failed.is_set.return_value = False
    monkeypatch.setattr(service, "seal_basis", lambda *args: None)
    local, remote = socket.socketpair()
    with Control(local) as control, remote, remote.makefile("rb") as reader:
        remote.settimeout(2)
        remote.sendall(wire({"type": "renew", "version": "control.v1"}))
        assert service._shutdown(launch, SimpleNamespace(basis={}, session=session), actors, control, "lease", lambda: 10) == 0
        assert json.loads(reader.readline()) == {"type": "refused", "code": "run-sealed", "version": "control.v1"}
        assert json.loads(reader.readline())["cause"] == "lease"


def test_hold_deadline_keeps_the_incomplete_ledger_for_recovery(certified_work, tmp_path, capfd):
    import threading
    from types import SimpleNamespace
    from unittest.mock import Mock
    from beliefs.permit import WritePermit
    from beliefs.session import open_run_session
    from beliefs.session.ledger import ledger_path
    from helpers.world import build_fixture_world
    from science.run_endpoint import service
    from science.run_endpoint.paths import Scratch

    cfg = build_fixture_world(certified_work)
    session = open_run_session(cfg.world, cfg.operations_root, write_root=cfg.write_root, profile=cfg.profile,
                               ceiling=WritePermit(frozenset(), frozenset()))
    held, release = threading.Event(), threading.Event()
    scratch = Scratch(tmp_path, cfg.operations_root, threading.Event())
    actors = service._Actors(b"", scratch, False, {"note"})
    session.claim_invocation("held", "note", "0"*64)

    def hold():
        with session._hold("held"):
            held.set()
            release.wait(5)

    worker = threading.Thread(target=hold)
    worker.start()
    try:
        assert held.wait(3)
        start = service.time.monotonic()
        control = Mock(writable=False)
        result = service._shutdown(SimpleNamespace(config=cfg, run_dir=tmp_path, seal_timeout_seconds=0.03),
                                   SimpleNamespace(session=session), actors, control, "stop", service.time.monotonic)
        assert result == 1 and service.time.monotonic() - start < 2
        assert control.queue.call_args.args[0]["type"] == "seal-timeout"
        assert not (tmp_path / "seal.json").exists()
        rows = [json.loads(row) for row in ledger_path(cfg.operations_root, session.session_id).read_bytes().splitlines()]
        assert rows[-1]["line"] == "invocation-open"
        assert json.loads(capfd.readouterr().err)["invocation"] == "held"
    finally:
        release.set()
        worker.join(5)
        session.close_invocation("held", {"done": []})
        session.close()
        scratch.cleanup()


def test_response_render_after_ledger_close_does_not_hold_the_seal(certified_work, tmp_path, monkeypatch):
    import threading
    from types import SimpleNamespace
    from unittest.mock import Mock
    from beliefs.permit import WritePermit
    from beliefs.session import open_run_session
    from beliefs.session.ledger import ledger_path
    from helpers.world import build_fixture_world
    from science.config import ReadContext
    from science.dispatch import Dispatcher
    from science.loader import production_tree, resolve_handlers
    from science.run_endpoint import service
    from science.run_endpoint.basis import open_basis
    from science.run_endpoint.paths import Scratch

    cfg = build_fixture_world(certified_work)
    decl = next(d for d in production_tree() if d.name == "dataset")
    permit = WritePermit(frozenset(decl.write_class.kinds), frozenset(decl.write_class.routes.values()))
    session = open_run_session(cfg.world, cfg.operations_root, write_root=cfg.write_root,
                               profile=cfg.profile, ceiling=permit, store_root=cfg.store_root)
    data = tmp_path / "table"
    data.write_bytes(b"table")
    rendering, release = threading.Event(), threading.Event()
    replies = []
    try:
        with Scratch(tmp_path, cfg.operations_root, threading.Event()) as scratch:
            actors = service._Actors(b"", scratch, False, {"dataset"})
            dispatcher = Dispatcher([decl], resolve_handlers([decl]), ReadContext.open(cfg),
                                    session=session, run_inputs=scratch, on_invocation_close=actors.complete)
            real_render = dispatcher._render_write

            def hold_reply(*args):
                rendering.set()
                assert release.wait(6)
                return real_render(*args)

            monkeypatch.setattr(dispatcher, "_render_write", hold_reply)
            request = {"command": "dataset", "invocation_id": "reply", "inputs": {"title": "table", "path": str(data)}}
            worker = threading.Thread(target=lambda: replies.append(actors._dispatch(dispatcher, request)))
            basis = open_basis(cfg)
            worker.start()
            try:
                assert rendering.wait(5)
                result = service._shutdown(SimpleNamespace(config=cfg, run_dir=tmp_path, seal_timeout_seconds=1),
                                           SimpleNamespace(session=session, basis=basis), actors, Mock(writable=False),
                                           "stop", service.time.monotonic)
                assert result == 0 and worker.is_alive()
                ledger = ledger_path(cfg.operations_root, session.session_id)
                assert [json.loads(line)["line"] for line in ledger.read_bytes().splitlines()][-2:] == [
                    "invocation-close", "session-close"]
            finally:
                release.set()
                worker.join(8)
    finally:
        session.close()
    assert replies[0]["ok"]


@pytest.mark.parametrize("fault", ["lost-ack", "before-rename", "after-rename"])
def test_private_evidence_after_endpoint_exit(launch_file, tmp_path, fault):
    import socket
    import subprocess
    import sys
    from pathlib import Path

    from science.run_endpoint.control import wire

    source, doc = launch_file
    control = Path(doc["control_socket"])
    control.unlink()
    run = Path(doc["run_dir"])
    # Interrupt only persistence of this fixture's seal in the child process.
    child = """
import os, sys
from pathlib import Path
from science.run_endpoint.launch import read_launch
from science.run_endpoint.service import serve_run

launch = read_launch(Path(sys.argv[1]))
fault = sys.argv[2]
sync = os.fsync
def fsync(fd):
    path = Path(os.readlink(f"/proc/self/fd/{fd}"))
    if fault == "before-rename" and path.parent == launch.run_dir and path.name.startswith(".seal-"):
        raise OSError("fixture seal file fsync")
    if fault == "after-rename" and path == launch.run_dir and (path / "seal.json").exists():
        raise OSError("fixture seal directory fsync")
    sync(fd)
os.fsync = fsync
sys.exit(serve_run(launch))
"""
    with socket.socket(socket.AF_UNIX) as supervisor, (run / "endpoint.log").open("wb") as log:
        supervisor.bind(str(control))
        supervisor.listen(1)
        supervisor.settimeout(15)
        with subprocess.Popen(
            [sys.executable, "-I", "-c", child, str(source), fault],
            stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True,
            env={"HOME": str(tmp_path), "PATH": os.defpath},
        ) as endpoint:
            try:
                conn, _ = supervisor.accept()
                with conn, conn.makefile("rb") as stream:
                    conn.settimeout(15)
                    opened = json.loads(stream.readline())
                    if fault != "lost-ack":
                        conn.sendall(wire({"type": "seal", "version": "control.v1"}))
                        assert json.loads(stream.readline())["type"] == "seal-failed"
                assert endpoint.wait(timeout=15) == (0 if fault == "lost-ack" else 1)
            finally:
                if endpoint.poll() is None:
                    endpoint.kill()
    ledger = [json.loads(line) for line in Path(opened["ledger_path"]).read_bytes().splitlines()]
    assert (ledger[-1]["line"] == "session-close") == (fault == "lost-ack")
    assert (run / "seal.json").exists() == (fault != "before-rename")
    if fault != "before-rename":
        assert json.loads((run / "seal.json").read_bytes())["sealed_tips"]
