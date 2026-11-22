"""Private namespace binding and peer authentication on a real Unix socket."""
import array
import contextlib
import os
import socket
import struct
import subprocess
import sys

import pytest

from science.refusal import Refused
from science.run_endpoint.control import Control, wire
from science.run_endpoint.handle import authenticate, receive_actor

# The supervisor pins the namespace of a live process before releasing its gate.
_ACTOR = """
import os, socket, sys
sock = socket.socket(socket.AF_UNIX)
sock.connect(sys.argv[1])
print(os.readlink('/proc/self/ns/pid'), flush=True)
sys.stdin.buffer.read(1)
sock.sendall(sys.argv[2].encode())
sys.stdin.buffer.read(1)
"""


def bind(sock, fd):
    sock.sendmsg([wire({"version": "control.v1", "type": "bind-actor"})],
                 [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", [fd]))])


@pytest.mark.parametrize("token,code", [("a" * 64, None), (None, "bad-token"), ("incorrect", "bad-token")])
def test_namespace_handoff_and_authenticated_request(short_tmp, token, code):
    with contextlib.ExitStack() as stack:
        path = short_tmp / "actor.sock"
        listener = stack.enter_context(socket.socket(socket.AF_UNIX))
        listener.bind(str(path))
        listener.listen()
        listener.settimeout(5)
        endpoint, supervisor = socket.socketpair()
        control = stack.enter_context(Control(endpoint))
        stack.enter_context(supervisor)
        frame = {"version": "actor.v1", "token": token, "request": {"query": "selection"}}
        actor = stack.enter_context(subprocess.Popen(
            ["unshare", "--user", "--map-root-user", "--pid", "--fork", "--kill-child",
             sys.executable, "-I", "-c", _ACTOR, str(path), wire(frame).decode()],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={"HOME": str(short_tmp), "PATH": os.defpath},
        ))
        # Closing stdin releases both actor gates, including on an assertion failure.
        stack.callback(actor.stdin.close)
        ready = actor.stdout.readline()
        if not ready:
            detail = actor.stderr.read().decode()
            if "Operation not permitted" in detail and os.environ.get("VERIFIABLY_UNCERTIFIED_HOST") == "1":
                pytest.skip(f"certified tuple unavailable on this host: {detail.strip()}")
            pytest.fail(f"actor namespace setup failed: {detail}")
        assert ready.startswith(b"pid:[")
        peer, _ = listener.accept()
        stack.enter_context(peer)
        peer_pid, _, _ = struct.unpack("3i", peer.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        with contextlib.ExitStack() as namespace:
            fd = os.open(f"/proc/{peer_pid}/ns/pid", os.O_RDONLY)
            namespace.callback(os.close, fd)
            bind(supervisor, fd)
            assert control.receive() == "bind-actor"
            bind(supervisor, fd)
            with pytest.raises(Refused):
                control.receive()
        local, remote = socket.socketpair()
        with local, remote:
            with pytest.raises(Refused) as refused:
                authenticate(local, control.namespace, b"a" * 64, "a" * 64)
            assert refused.value.refusal.code == "bad-peer"
        actor.stdin.write(b"1")
        actor.stdin.flush()
        if code is None:
            assert receive_actor(peer, control.namespace, b"a" * 64) == frame["request"]
        else:
            with pytest.raises(Refused) as refused:
                receive_actor(peer, control.namespace, b"a" * 64)
            assert refused.value.refusal.code == code


@pytest.mark.parametrize("phase", ["kernel-hold", "worker-drain"])
def test_live_actor_and_supervisor_get_refusals_while_seal_waits(short_tmp, monkeypatch, phase):
    import json
    import threading
    import time
    from types import SimpleNamespace
    from unittest.mock import Mock
    from beliefs.session.writer import ChainTip, SealedTips
    from science.run_endpoint import service
    from science.run_endpoint.paths import Scratch

    token = "b" * 64
    actor_program = """
import socket, sys
from pathlib import Path
from science.refusal import Refused
from science.run_endpoint.handle import Handle
with socket.socket(socket.AF_UNIX) as ready:
    ready.connect(sys.argv[1])
    assert ready.recv(1) == b'g'
try:
    Handle(Path(sys.argv[1]), Path(sys.argv[2])).invoke('note', {}, invocation_id='late')
except Refused as error:
    print(error.refusal.code, flush=True)
"""
    with contextlib.ExitStack() as stack:
        path = short_tmp / "sock"
        token_file = short_tmp / "token"
        token_file.write_text(token)
        server = stack.enter_context(service._listener(path))
        server.settimeout(3)
        actor = stack.enter_context(subprocess.Popen(
            ["unshare", "--user", "--map-root-user", "--pid", "--fork", "--kill-child",
             sys.executable, "-I", "-c", actor_program, str(path), str(token_file)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env={"HOME": str(short_tmp), "PATH": os.defpath}))
        stack.callback(actor.kill)
        try:
            ready, _ = server.accept()
        except TimeoutError:
            if actor.poll() is not None:
                detail = actor.stderr.read().decode()
                if "Operation not permitted" in detail and os.environ.get("VERIFIABLY_UNCERTIFIED_HOST") == "1":
                    pytest.skip(f"certified tuple unavailable on this host: {detail.strip()}")
            raise
        stack.enter_context(ready)
        server.setblocking(False)
        local, supervisor = socket.socketpair()
        control = stack.enter_context(Control(local))
        stack.enter_context(supervisor)
        supervisor.settimeout(3)
        reader = stack.enter_context(supervisor.makefile("rb"))
        pid, _, _ = struct.unpack("3i", ready.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        with open(f"/proc/{pid}/ns/pid", "rb", buffering=0) as ns:
            bind(supervisor, ns.fileno())
        assert control.receive() == "bind-actor"

        scratch = stack.enter_context(Scratch(short_tmp, short_tmp, threading.Event()))
        actors = service._Actors(token.encode(), scratch, False, {"note"})
        worker = threading.get_ident()
        actors.pending.add(worker)
        dispatcher = Mock()
        replies = []
        session = Mock(current_invocation=None)
        released = threading.Event()

        def seal(timeout):
            ready.sendall(b"g")
            supervisor.sendall(wire({"type": "renew", "version": "control.v1"}))
            if phase == "kernel-hold":
                assert released.wait(timeout)
            return SealedTips(ChainTip("a"*32, "1"*64, "1"*64), None)
        session.seal.side_effect = seal

        def release_worker():
            try:
                replies.append(json.loads(reader.readline())["code"])
                stdout, _ = actor.communicate(timeout=3)
                replies.append(stdout.decode().strip())
            finally:
                with actors.condition:
                    actors.pending.discard(worker)
                    actors.condition.notify_all()
                released.set()

        peer = threading.Thread(target=release_worker)
        peer.start()
        monkeypatch.setattr(service, "seal_basis", lambda *args: None)
        launch = SimpleNamespace(config=SimpleNamespace(operations_root=short_tmp),
                                 run_dir=short_tmp, seal_timeout_seconds=5)
        try:
            assert service._shutdown(launch, SimpleNamespace(session=session, basis=None), actors, control,
                                     "stop", time.monotonic, server=server, dispatcher=dispatcher) == 0
        finally:
            actor.kill()
            peer.join(5)
        assert replies == ["run-sealed", "run-sealed"]
        assert dispatcher.mock_calls == []
