"""MCP 2026-07-28 JSON-RPC server over newline-delimited stdio."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

from science.dispatch import Dispatcher
from science.findings import report_findings
from science.refusal import Refused, envelope
from science.schema import Declaration

PROTOCOL_VERSION = "2026-07-28"
MAX_REQUEST_BYTES = 1_048_576
CACHE_TTL_MS = 300_000
CACHE_SCOPE = "public"

_NS = "io.modelcontextprotocol/"
_EXTENSION_KEY = re.compile(
    r"[A-Za-z](?:[A-Za-z0-9-]*[A-Za-z0-9])?"
    r"(?:\.[A-Za-z](?:[A-Za-z0-9-]*[A-Za-z0-9])?)*"
    r"/(?:[A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)?"
)
_JSON_TYPES = {"string": "string", "int": "integer", "bool": "boolean"}


def tool_schema(declaration: Declaration) -> dict:
    properties = {}
    required = []
    for input_spec in declaration.inputs:
        if input_spec.type == "enum":
            field = {"type": "string", "enum": list(input_spec.choices)}
        elif input_spec.type == "list-of-string":
            field = {"type": "array", "items": {"type": "string"}}
        else:
            field = {"type": _JSON_TYPES[input_spec.type]}
        field["description"] = input_spec.doc
        properties[input_spec.name] = field
        if input_spec.required:
            required.append(input_spec.name)
    properties["invocation_id"] = {
        "type": "string",
        "description": "Optional idempotency token.",
    }
    properties["cursor"] = {
        "type": "string",
        "description": "Continuation cursor from a truncated result.",
    }
    input_schema = {
        "type": "object",
        "properties": properties,
        "additionalProperties": False,
    }
    if required:
        input_schema["required"] = required
    return {
        "name": declaration.name,
        "description": declaration.purpose,
        "inputSchema": input_schema,
    }


def _request_id(request: object):
    if type(request) is dict and type(request.get("id")) in (str, int):
        return request["id"]
    return None


def _rpc_error(request_id, code: int, message: str, data=None) -> dict:
    error = {"code": code, "message": message}
    if data is not None:
        error["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": error}


def _result(request_id, payload: dict) -> dict:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {**payload, "resultType": "complete"},
    }


def _envelope_error(request: object) -> str | None:
    if type(request) is not dict:
        return "Request must be an object"
    if set(request) - {"jsonrpc", "id", "method", "params"}:
        return "Request has unknown fields"
    if request.get("jsonrpc") != "2.0":
        return 'jsonrpc must be "2.0"'
    if "id" in request and type(request["id"]) not in (str, int):
        return "id must be a non-null string or integer"
    if type(request.get("method")) is not str:
        return "method must be a string"
    return None


def _valid_uri(value: object) -> bool:
    if type(value) is not str or any(character.isspace() for character in value):
        return False
    try:
        return bool(urlsplit(value).scheme)
    except ValueError:
        return False


def _valid_icon(value: object) -> bool:
    if type(value) is not dict or not _valid_uri(value.get("src")):
        return False
    if "mimeType" in value and type(value["mimeType"]) is not str:
        return False
    if "sizes" in value and (
        type(value["sizes"]) is not list
        or any(type(size) is not str for size in value["sizes"])
    ):
        return False
    return "theme" not in value or value["theme"] in ("dark", "light")


def _valid_implementation(value: object) -> bool:
    if type(value) is not dict:
        return False
    if any(type(value.get(field)) is not str for field in ("name", "version")):
        return False
    if any(
        field in value and type(value[field]) is not str
        for field in ("title", "description")
    ):
        return False
    if "websiteUrl" in value and not _valid_uri(value["websiteUrl"]):
        return False
    return "icons" not in value or (
        type(value["icons"]) is list
        and all(_valid_icon(icon) for icon in value["icons"])
    )


def _valid_object_fields(value: object, fields: tuple[str, ...]) -> bool:
    return type(value) is dict and all(
        field not in value or type(value[field]) is dict for field in fields
    )


def _valid_client_capabilities(value: object) -> bool:
    if type(value) is not dict:
        return False
    if "roots" in value and type(value["roots"]) is not dict:
        return False
    if "sampling" in value and not _valid_object_fields(
        value["sampling"], ("context", "tools")
    ):
        return False
    if "elicitation" in value and not _valid_object_fields(
        value["elicitation"], ("form", "url")
    ):
        return False
    for field in ("experimental", "extensions"):
        if field in value and (
            type(value[field]) is not dict
            or any(type(setting) is not dict for setting in value[field].values())
        ):
            return False
    return "extensions" not in value or all(
        type(key) is str and _EXTENSION_KEY.fullmatch(key)
        for key in value["extensions"]
    )


def _meta_error(meta: object):
    if type(meta) is not dict:
        return -32602, "Request _meta is required", None
    version = meta.get(_NS + "protocolVersion")
    if type(version) is not str:
        return -32602, f"{_NS}protocolVersion is required", None
    if version != PROTOCOL_VERSION:
        return (
            -32022,
            "Unsupported protocol version",
            {"supported": [PROTOCOL_VERSION], "requested": version},
        )
    if not _valid_client_capabilities(meta.get(_NS + "clientCapabilities")):
        return -32602, f"{_NS}clientCapabilities is required", None
    if _NS + "clientInfo" in meta and not _valid_implementation(
        meta[_NS + "clientInfo"]
    ):
        return -32602, f"{_NS}clientInfo must be an Implementation", None
    return None


def _invalid_params(request_id, message: str) -> dict:
    return _rpc_error(request_id, -32602, message)


def handle_request(request: object, dispatcher: Dispatcher, decls) -> dict | None:
    problem = _envelope_error(request)
    if problem is not None:
        return _rpc_error(_request_id(request), -32600, problem)
    if "id" not in request:
        return None

    request_id = request["id"]
    params = request.get("params")
    if type(params) is not dict:
        return _invalid_params(request_id, "params must be an object")
    problem = _meta_error(params.get("_meta"))
    if problem is not None:
        code, message, data = problem
        return _rpc_error(request_id, code, message, data)

    method = request["method"]
    if method == "server/discover":
        if set(params) != {"_meta"}:
            return _invalid_params(request_id, "server/discover takes only _meta")
        return _result(
            request_id,
            {
                "supportedVersions": [PROTOCOL_VERSION],
                "capabilities": {"tools": {}},
                "ttlMs": CACHE_TTL_MS,
                "cacheScope": CACHE_SCOPE,
                "_meta": {
                    _NS + "serverInfo": {"name": "science", "version": "0.1.0"}
                },
            },
        )

    if method == "tools/list":
        if set(params) - {"_meta", "cursor"}:
            return _invalid_params(request_id, "tools/list has unknown fields")
        if "cursor" in params and type(params["cursor"]) is not str:
            return _invalid_params(request_id, "cursor must be a string")
        if "cursor" in params:
            return _invalid_params(request_id, "cursor was not issued by this listing")
        return _result(
            request_id,
            {
                "tools": [tool_schema(decl) for decl in decls],
                "ttlMs": CACHE_TTL_MS,
                "cacheScope": CACHE_SCOPE,
            },
        )

    if method == "tools/call":
        if set(params) - {
            "_meta",
            "name",
            "arguments",
            "inputResponses",
            "requestState",
        }:
            return _invalid_params(request_id, "tools/call has unknown fields")
        if "inputResponses" in params and type(params["inputResponses"]) is not dict:
            return _invalid_params(request_id, "inputResponses must be an object")
        if "requestState" in params and type(params["requestState"]) is not str:
            return _invalid_params(request_id, "requestState must be a string")
        if "inputResponses" in params or "requestState" in params:
            return _invalid_params(
                request_id, "science did not request multi-round input"
            )
        name = params.get("name")
        if type(name) is not str:
            return _invalid_params(request_id, "tool name must be a string")
        if name not in {decl.name for decl in decls}:
            return _invalid_params(request_id, f"Unknown tool: {name}")
        if "arguments" in params and type(params["arguments"]) is not dict:
            return _invalid_params(request_id, "arguments must be an object")
        raw_arguments = params.get("arguments", {})
        arguments = dict(raw_arguments)
        cursor = arguments.pop("cursor", None)
        invocation_id = arguments.pop("invocation_id", None)
        for field, value in (("cursor", cursor), ("invocation_id", invocation_id)):
            if field in raw_arguments and type(value) is not str:
                return _invalid_params(request_id, f"{field} must be a string")
        try:
            outcome = dispatcher.invoke(
                name,
                arguments,
                invocation_id=invocation_id,
                cursor=cursor,
            )
        except Refused as error:
            structured = {"refusal": envelope(error.refusal)}
            if error.invocation_id is not None:
                structured["invocation_id"] = error.invocation_id
            return _result(
                request_id,
                {
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"refused [{error.refusal.code}] "
                                f"{error.refusal.message}"
                            ),
                        }
                    ],
                    "structuredContent": structured,
                    "isError": True,
                },
            )
        except Exception:  # noqa: BLE001 -- external protocol boundary
            return _rpc_error(request_id, -32603, "Internal error")
        return _result(
            request_id,
            {
                "content": [{"type": "text", "text": outcome.text}],
                "structuredContent": {"invocation_id": outcome.invocation_id},
                "isError": False,
            },
        )

    return _rpc_error(request_id, -32601, f"Method not found: {method}")


class _MalformedJSON(ValueError):
    pass


def _object_without_duplicates(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise _MalformedJSON
        value[key] = item
    return value


def _reject_nonfinite_number(value):
    raise _MalformedJSON


_END_OF_INPUT = object()
_OVERSIZED_FRAME = object()


def _drain_frame(stream) -> None:
    while True:
        chunk = stream.readline(65_536)
        if not chunk or chunk.endswith(b"\n"):
            return


def _read_frame(stream):
    frame = stream.readline(MAX_REQUEST_BYTES + 2)
    if not isinstance(frame, bytes):
        raise TypeError("MCP stdin must be a binary stream")
    if frame == b"":
        return _END_OF_INPUT
    if frame.endswith(b"\n"):
        if len(frame) - 1 > MAX_REQUEST_BYTES:
            return _OVERSIZED_FRAME
        return frame[:-1]
    if len(frame) > MAX_REQUEST_BYTES:
        _drain_frame(stream)
        return _OVERSIZED_FRAME
    return frame


def serve(config_path: Path, stdin=None, stdout=None, stderr=None) -> None:
    from beliefs.session import open_attended_session

    from science.config import ReadContext, load_config
    from science.loader import production_tree, resolve_handlers

    stdin = sys.stdin.buffer if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    declarations = production_tree()
    config = load_config(config_path)
    # One attended session for the process lifetime. A world config naming
    # other than exactly one corpus root raises SessionRefused here; that is a
    # launcher misconfiguration and propagates, never a command refusal.
    session = open_attended_session(
        config.world, config.operations_root, profile=config.profile,
        store_root=config.store_root,
    )
    try:
        report_findings(session.findings, reported_by=session.session_id,
                        stream=sys.stderr if stderr is None else stderr)
        dispatcher = Dispatcher(
            declarations,
            resolve_handlers(declarations),
            ReadContext.open(config),
            session=session,
        )
        while True:
            frame = _read_frame(stdin)
            if frame is _END_OF_INPUT:
                return
            if frame is _OVERSIZED_FRAME:
                response = _rpc_error(None, -32600, "Request exceeds maximum size")
            elif not frame.strip():
                continue
            else:
                try:
                    line = frame.decode("utf-8", errors="strict")
                    request = json.loads(
                        line,
                        object_pairs_hook=_object_without_duplicates,
                        parse_constant=_reject_nonfinite_number,
                    )
                except (UnicodeDecodeError, ValueError, RecursionError):
                    response = _rpc_error(None, -32700, "Parse error")
                else:
                    response = handle_request(request, dispatcher, declarations)
            if response is None:
                continue
            stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            stdout.flush()
    finally:
        session.close()  # the ledger's session-close line, crash or EOF alike
