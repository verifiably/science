"""Single-request actor transport authenticated by its kernel peer and token."""
from __future__ import annotations

from dataclasses import dataclass
import hmac
import json
import os
from pathlib import Path
import select
import socket
import struct

from science.dispatch import Outcome
from science.refusal import Refusal, Refused
from science.serve import answer_request
from science.run_endpoint.control import wire

_LIMIT = 1 << 20
_SO_PEERPIDFD = getattr(socket, "SO_PEERPIDFD", 77)


def authenticate(stream, namespace, expected, presented):
    if namespace is None:
        raise Refused(Refusal("bad-peer", "The run has no bound actor namespace"))
    try:
        pid, _, _ = struct.unpack("3i", stream.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
        pidfd = stream.getsockopt(socket.SOL_SOCKET, _SO_PEERPIDFD)
        try:
            peer = os.stat(f"/proc/{pid}/ns/pid")
            poll = select.poll()
            poll.register(pidfd, select.POLLIN)
            matches = os.path.samestat(peer, os.fstat(namespace)) and not poll.poll(0)
        finally:
            os.close(pidfd)
    except OSError:
        matches = False
    if not matches:
        raise Refused(Refusal("bad-peer", "Cannot verify the connecting actor namespace"))
    if type(presented) is not str or not presented.isascii() or not hmac.compare_digest(expected, presented.encode()):
        raise Refused(Refusal("bad-token", "Actor authentication failed"))


def answer(dispatcher, request, *, can_execute):
    def admit(command, inputs, invocation_id, cursor):
        if command in ("run", "derive") and not can_execute:
            raise Refused(Refusal("confinement-unavailable", "Run child containment is unavailable"), invocation_id)
    return answer_request(dispatcher, request, admit=admit)


def _receive(stream):
    with stream.makefile("rb") as reader:
        data = reader.readline(_LIMIT + 1)
    if not data.endswith(b"\n") or len(data) > _LIMIT:
        raise Refused(Refusal("invalid-input", "Invalid actor frame length"))
    try:
        value = json.loads(data.decode("utf-8"))
    except (ValueError, RecursionError):
        raise Refused(Refusal("invalid-input", "Malformed actor frame")) from None
    if type(value) is not dict:
        raise Refused(Refusal("invalid-input", "Expected an actor frame object"))
    return value


def receive_actor(stream, namespace, token):
    frame = _receive(stream)
    if set(frame) != {"version", "request", "token"} or frame["version"] != "actor.v1":
        raise Refused(Refusal("invalid-input", "Invalid actor frame fields or version"))
    authenticate(stream, namespace, token, frame["token"])
    return frame["request"]


@dataclass(frozen=True)
class Handle:
    endpoint: Path
    token_file: Path

    @classmethod
    def from_env(cls, env, *, config=None):
        ep = env.get("VERIFIABLY_ENDPOINT")
        token = env.get("VERIFIABLY_TOKEN_FILE")
        if ep is None and token is None:
            return None
        if not ep or not token or config is not None or "SCIENCE_CONFIG" in env:
            raise Refused(Refusal("handle-incomplete", "Run mode requires both handle paths and no configuration"))
        return cls(Path(ep), Path(token))

    def request(self, request):
        try:
            with self.token_file.open("rb") as source:
                token = source.read(65)
            if len(token) != 64 or not token.isascii():
                raise Refused(Refusal("bad-token", "Invalid actor credential file"))
            data = wire({"version": "actor.v1", "token": token.decode(), "request": request})
            if len(data) > _LIMIT:
                raise Refused(Refusal("invalid-input", "Actor request exceeds its size limit"))
            with socket.socket(socket.AF_UNIX) as stream:
                stream.connect(str(self.endpoint))
                stream.sendall(data)
                reply = _receive(stream)
        except OSError:
            raise Refused(Refusal("handle-incomplete", "The run endpoint or credential is unavailable")) from None
        if reply.get("ok") is False:
            r = reply["refusal"]
            raise Refused(Refusal(r["code"], r["message"], r.get("data", {})), reply.get("invocation_id"))
        return reply

    def invoke(self, command, inputs, *, invocation_id=None, cursor=None, project=None):
        reply = self.request({"command": command, "inputs": inputs, "invocation_id": invocation_id,
                              "cursor": cursor, "project": project})
        return Outcome(reply["text"], reply["invocation_id"])
