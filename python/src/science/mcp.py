"""MCP 2026-07-28 JSON-RPC server over newline-delimited stdio."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from science.dispatch import Dispatcher
from science.refusal import Refused, envelope
from science.schema import Declaration

PROTOCOL_VERSION = "2026-07-28"

_NS = "io.modelcontextprotocol/"
_SERVER_INFO = {"name": "science", "version": "0.1.0"}
_SERVER_CAPABILITIES = {"tools": {}}
_TYPES = {
    "string": {"type": "string"},
    "int": {"type": "integer"},
    "bool": {"type": "boolean"},
    "list-of-string": {"type": "array", "items": {"type": "string"}},
}


def tool_schema(declaration: Declaration) -> dict:
    properties = {}
    required = []
    for input_spec in declaration.inputs:
        if input_spec.type == "enum":
            field = {"type": "string", "enum": list(input_spec.choices)}
        else:
            field = dict(_TYPES[input_spec.type])
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
    input_schema = {"type": "object", "properties": properties}
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
    if type(request.get("id")) not in (str, int):
        return "id must be a non-null string or integer"
    if type(request.get("method")) is not str:
        return "method must be a string"
    return None


def _valid_implementation(value: object) -> bool:
    return (
        type(value) is dict
        and type(value.get("name")) is str
        and type(value.get("version")) is str
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
    if type(meta.get(_NS + "clientCapabilities")) is not dict:
        return -32602, f"{_NS}clientCapabilities is required", None
    if _NS + "clientInfo" in meta and not _valid_implementation(
        meta[_NS + "clientInfo"]
    ):
        return -32602, f"{_NS}clientInfo must be an Implementation", None
    return None


def _invalid_params(request_id, message: str) -> dict:
    return _rpc_error(request_id, -32602, message)


def handle_request(request: object, dispatcher: Dispatcher, decls) -> dict:
    problem = _envelope_error(request)
    if problem is not None:
        return _rpc_error(_request_id(request), -32600, problem)

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
                "capabilities": _SERVER_CAPABILITIES,
                "_meta": {_NS + "serverInfo": _SERVER_INFO},
            },
        )

    if method == "tools/list":
        if set(params) - {"_meta", "cursor"}:
            return _invalid_params(request_id, "tools/list has unknown fields")
        if "cursor" in params and type(params["cursor"]) is not str:
            return _invalid_params(request_id, "cursor must be a string")
        return _result(request_id, {"tools": [tool_schema(decl) for decl in decls]})

    if method == "tools/call":
        if set(params) - {"_meta", "name", "arguments"}:
            return _invalid_params(request_id, "tools/call has unknown fields")
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


def serve(config_path: Path, stdin=None, stdout=None, session=None) -> None:
    from science.config import ReadContext, load_config
    from science.loader import production_tree, resolve_handlers

    stdin = sys.stdin if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    declarations = production_tree()
    dispatcher = Dispatcher(
        declarations,
        resolve_handlers(declarations),
        ReadContext.open(load_config(config_path)),
        session=session,
    )
    for line in stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(
                line,
                object_pairs_hook=_object_without_duplicates,
                parse_constant=_reject_nonfinite_number,
            )
        except (json.JSONDecodeError, _MalformedJSON):
            response = _rpc_error(None, -32700, "Parse error")
        else:
            response = handle_request(request, dispatcher, declarations)
        stdout.write(json.dumps(response) + "\n")
        stdout.flush()
