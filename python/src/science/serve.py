"""The CLI's service process: one attended session behind a Unix socket (spec §9.2)."""
from __future__ import annotations

import json
import socketserver
import sys
from pathlib import Path

from science.config import ReadContext, ScienceConfig
from science.dispatch import Dispatcher
from science.findings import report_findings
from science.refusal import Refusal, Refused, envelope

_REQUEST_KEYS = frozenset({"command", "inputs", "invocation_id", "cursor"})
# Linux `sockaddr_un.sun_path` is 108 bytes including the terminating NUL, so
# 107 are usable. `bind` past that raises a bare `OSError: AF_UNIX path too
# long`, which says nothing about which path or what the limit is.
MAX_SOCKET_PATH_BYTES = 107


def _validated(request) -> tuple[str, dict, str | None, str | None]:
    def refuse(message: str):
        raise Refused(Refusal("invalid-input", message))

    if not isinstance(request, dict):
        refuse("request must be an object")
    unknown = set(request) - _REQUEST_KEYS
    if unknown:
        refuse(f"unknown request keys {sorted(unknown)}")
    command = request.get("command")
    if not isinstance(command, str):
        refuse("command must be a string")
    inputs = request.get("inputs")
    if inputs is None:
        inputs = {}
    if not isinstance(inputs, dict):  # a list or scalar never becomes {}
        refuse("inputs must be an object or null")
    invocation_id, cursor = request.get("invocation_id"), request.get("cursor")
    for label, value in (("invocation_id", invocation_id), ("cursor", cursor)):
        if value is not None and not isinstance(value, str):
            refuse(f"{label} must be a string or null")
    return command, inputs, invocation_id, cursor


def serve(config: ScienceConfig, socket_path: Path, declarations=None, handlers=None, stderr=None):
    """`declarations`/`handlers` default to the production tree; tests inject
    their synthetic set here — production code never imports test modules."""
    from science.session import open_session

    if declarations is None:
        from science.loader import production_tree, resolve_handlers

        declarations = production_tree()
        handlers = resolve_handlers(declarations)
    # Every pre-session refusal happens before the session exists; after it
    # is opened, any constructor failure closes it before propagating.
    encoded = len(str(socket_path).encode())
    if encoded > MAX_SOCKET_PATH_BYTES:
        raise Refused(Refusal(
            "invalid-input",
            f"socket path is {encoded} bytes; the AF_UNIX limit is "
            f"{MAX_SOCKET_PATH_BYTES}: {socket_path}",
        ))
    if socket_path.exists():
        raise Refused(Refusal(
            "invalid-input",
            f"socket already exists: {socket_path}; a stale one from a crashed "
            "service is the operator's to remove",
        ))
    session = open_session(config)
    try:
        report_findings(session.findings, reported_by=session.session_id,
                        stream=sys.stderr if stderr is None else stderr)
        dispatcher = Dispatcher(declarations, handlers, ReadContext.open(config),
                                session=session)

        class Handler(socketserver.StreamRequestHandler):
            def handle(self) -> None:
                for line in self.rfile:
                    try:
                        command, inputs, invocation_id, cursor = _validated(json.loads(line))
                        out = dispatcher.invoke(command, inputs,
                                                invocation_id=invocation_id, cursor=cursor)
                        reply = {"ok": True, "text": out.text,
                                 "invocation_id": out.invocation_id}
                    except json.JSONDecodeError as caught:
                        reply = {"ok": False, "refusal": envelope(
                            Refusal("invalid-input", f"request is not JSON: {caught}"))}
                    except Refused as caught:
                        reply = {"ok": False, "refusal": envelope(caught.refusal)}
                        if caught.invocation_id is not None:
                            reply["invocation_id"] = caught.invocation_id
                    self.wfile.write(json.dumps(reply).encode() + b"\n")

        class Server(socketserver.ThreadingUnixStreamServer):
            # Without this, `server_close` joins every handler thread, and a
            # handler blocks in its read loop for as long as its client holds
            # the connection open. One idle client would then wedge shutdown
            # indefinitely. Killing an in-flight write at shutdown is already
            # a designed-for state: the invocation stays claimed and unclosed,
            # so a retry replays as `outcome-unknown` (spec §5.2).
            daemon_threads = True

            def server_close(self) -> None:
                try:
                    super().server_close()
                finally:
                    session.close()  # even when the socket teardown raises

        socket_path.parent.mkdir(parents=True, exist_ok=True)
        # No unlink anywhere: the existence check above refused already, and
        # if a socket appears in the race window, bind() fails loudly — never
        # clean up. A bind failure lands in the except below, which closes
        # the session before re-raising.
        return Server(str(socket_path), Handler)
    except BaseException:
        session.close()
        raise
