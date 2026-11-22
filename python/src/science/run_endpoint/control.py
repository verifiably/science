"""Nonblocking private supervisor stream and one-time PID namespace binding."""
from __future__ import annotations

import array
import fcntl
import json
import os
import socket

from science.refusal import Refusal, Refused

_NS_GET_NSTYPE = 0xb703
_CLONE_NEWPID = 0x20000000
_LIMIT = 16384


def _invalid(message):
    raise Refused(Refusal("invalid-input", message))


def wire(value):
    return json.dumps(value, allow_nan=False, sort_keys=True, separators=(",", ":")).encode() + b"\n"


def seal_evidence(cause, tips, basis):
    """Build the durable file and its control acknowledgement from the same kernel tips."""
    chains = [
        {"role": role, "id": tip.chain_id, "genesis": tip.genesis, "tip": tip.tip}
        for role, tip in (("corpus", tips.corpus), ("store", tips.store)) if tip is not None
    ]
    document = {"cause": cause, "sealed_tips": chains, "basis_seal": basis}
    return document, {"version": "control.v1", "type": "sealed", **document}


class Control:
    def __init__(self, stream):
        self.stream = stream
        self.stream.setblocking(False)
        self.namespace: int | None = None
        self._data = bytearray()
        self._fds: list[int] = []
        self._out = bytearray()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def _discard(self):
        self._data.clear()
        while self._fds:
            os.close(self._fds.pop())

    def close(self):
        self._discard()
        if self.namespace is not None:
            os.close(self.namespace)
            self.namespace = None
        self.stream.close()

    @property
    def writable(self):
        return bool(self._out)

    def queue(self, message):
        data = wire(message)
        if len(data) + len(self._out) > _LIMIT:
            _invalid("Control reply buffer is full")
        self._out.extend(data)
        self.flush()

    def flush(self):
        if self._out:
            try:
                count = self.stream.send(self._out)
            except BlockingIOError:
                return
            if count == 0:
                raise EOFError
            del self._out[:count]

    def receive(self):
        # A stream recvmsg can combine plain bytes with the next sendmsg's
        # control data. One byte identifies the precise frame owning the fd.
        # Cap each turn so the selector still observes the lease and SIGTERM.
        try:
            for _ in range(256):
                try:
                    data, ancillary, flags, _ = self.stream.recvmsg(
                        1, socket.CMSG_SPACE(2 * array.array("i").itemsize), socket.MSG_CMSG_CLOEXEC)
                except BlockingIOError:
                    return None
                for level, typ, raw in ancillary:
                    if (level, typ) != (socket.SOL_SOCKET, socket.SCM_RIGHTS):
                        _invalid("Unexpected control ancillary data")
                    fds = array.array("i")
                    fds.frombytes(raw)
                    self._fds.extend(fds)
                if flags & socket.MSG_CTRUNC or len(self._fds) > 1:
                    _invalid("Extra or truncated control descriptors")
                if not data:
                    raise EOFError
                if data == b"\n":
                    return self._finish()
                self._data.extend(data)
                if len(self._data) > _LIMIT:
                    _invalid("Oversized control frame")
            return None
        except BaseException:
            self._discard()
            raise

    def _finish(self):
        try:
            msg = json.loads(self._data.decode("utf-8"))
        except (ValueError, RecursionError):
            _invalid("Malformed control frame")
        self._data.clear()
        if not isinstance(msg, dict) or set(msg) != {"type", "version"} or msg["version"] != "control.v1":
            _invalid("Unexpected control frame")
        kind = msg["type"]
        if kind == "bind-actor":
            if self.namespace is not None or len(self._fds) != 1:
                _invalid("bind-actor requires exactly one initial PID namespace")
            fd, = self._fds
            try:
                pid_namespace = fcntl.ioctl(fd, _NS_GET_NSTYPE) == _CLONE_NEWPID
                same = os.path.samestat(os.fstat(fd), os.stat("/proc/self/ns/pid"))
            except OSError:
                _invalid("Invalid PID namespace descriptor")
            if not pid_namespace or same:
                _invalid("The actor must have a distinct PID namespace")
            self.namespace = self._fds.pop()
        elif kind not in ("seal", "renew") or self._fds:
            _invalid("Unexpected control request or descriptor")
        return kind
