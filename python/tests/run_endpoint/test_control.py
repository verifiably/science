"""Ancillary fds belong to a single private control frame."""
import array
import json
import os
import socket

import pytest

from science.refusal import Refused


def frame(kind):
    return json.dumps({"version": "control.v1", "type": kind}).encode() + b"\n"


def test_segmented_control_does_not_consume_the_next_frames_descriptor():
    from science.run_endpoint.control import Control
    a, b = socket.socketpair()
    with a, b, Control(b) as control:
        a.sendall(frame("renew")[:3])
        assert control.receive() is None
        a.sendall(frame("renew")[3:])
        fd = os.open("/proc/self/ns/pid", os.O_RDONLY)
        try:
            a.sendmsg([frame("bind-actor")], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", [fd]))])
        finally:
            os.close(fd)
        assert control.receive() == "renew"
        with pytest.raises(Refused, match="distinct PID namespace"):
            control.receive()
        assert control.namespace is None


@pytest.mark.parametrize("kind,count", [("bind-actor", 0), ("bind-actor", 2), ("renew", 1), ("bind-actor", 8)])
def test_unexpected_descriptors_are_released(kind, count):
    from science.run_endpoint.control import Control
    a, b = socket.socketpair()
    with a, b, Control(b) as control:
        fd = os.open("/dev/null", os.O_RDONLY)
        try:
            ancillary = [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", [fd]*count))] if count else []
            a.sendmsg([frame(kind)], ancillary)
        finally:
            os.close(fd)
        before = len(os.listdir("/proc/self/fd"))
        with pytest.raises(Refused):
            control.receive()
        assert len(os.listdir("/proc/self/fd")) == before
