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
