import io
import json
from pathlib import Path

import pytest

from science.loader import production_tree
from science.mcp import MAX_REQUEST_BYTES, handle_request, serve, tool_schema
from science.refusal import Refusal, Refused


META = {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientInfo": {"name": "science-tests", "version": "0"},
    "io.modelcontextprotocol/clientCapabilities": {},
}


def rpc(method, params=None, id=1):
    body = dict(params or {})
    body.setdefault("_meta", dict(META))
    return {"jsonrpc": "2.0", "id": id, "method": method, "params": body}


def dispatcher_for(certified_work):
    from helpers.world import build_fixture_world
    from science.config import ReadContext
    from science.dispatch import Dispatcher
    from science.loader import resolve_handlers

    config = build_fixture_world(certified_work)
    declarations = production_tree()
    return declarations, Dispatcher(
        declarations,
        resolve_handlers(declarations),
        ReadContext.open(config),
    )


def test_tool_schema_carries_inputs_and_protocol_fields():
    declaration = next(d for d in production_tree() if d.name == "status")

    schema = tool_schema(declaration)

    assert schema["name"] == "status"
    assert schema["description"] == declaration.purpose
    assert schema["inputSchema"]["type"] == "object"
    assert schema["inputSchema"]["additionalProperties"] is False
    assert schema["inputSchema"]["properties"] == {
        "invocation_id": {
            "type": "string",
            "description": "Optional idempotency token.",
        },
        "cursor": {
            "type": "string",
            "description": "Continuation cursor from a truncated result.",
        },
    }


def test_tool_schema_maps_every_declared_input_type():
    from science.cursor import MIN_OUTPUT_BUDGET
    from science.schema import Declaration, InputSpec, WriteClass

    declaration = Declaration(
        "shape",
        "Exercise every input type.",
        WriteClass("read-only"),
        MIN_OUTPUT_BUDGET,
        (
            InputSpec("text", "string", True, "text doc"),
            InputSpec("count", "int", False, "count doc"),
            InputSpec("enabled", "bool", False, "enabled doc"),
            InputSpec("mode", "enum", True, "mode doc", choices=("a", "b")),
            InputSpec("tags", "list-of-string", False, "tags doc"),
        ),
        (),
        Path("."),
    )

    schema = tool_schema(declaration)["inputSchema"]

    assert schema["required"] == ["text", "mode"]
    assert schema["properties"] | {
        "invocation_id": {},
        "cursor": {},
    } == {
        "text": {"type": "string", "description": "text doc"},
        "count": {"type": "integer", "description": "count doc"},
        "enabled": {"type": "boolean", "description": "enabled doc"},
        "mode": {"type": "string", "enum": ["a", "b"], "description": "mode doc"},
        "tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "tags doc",
        },
        "invocation_id": {},
        "cursor": {},
    }


def test_tools_list_and_call(certified_work):
    declarations, dispatcher = dispatcher_for(certified_work)

    listed = handle_request(rpc("tools/list"), dispatcher, declarations)
    called = handle_request(
        rpc("tools/call", {"name": "status", "arguments": {}}),
        dispatcher,
        declarations,
    )

    assert [tool["name"] for tool in listed["result"]["tools"]] == ["status"]
    assert listed["result"]["ttlMs"] == 300_000
    assert listed["result"]["cacheScope"] == "public"
    assert "World status" in called["result"]["content"][0]["text"]
    assert len(called["result"]["structuredContent"]["invocation_id"]) == 32
    assert called["result"]["isError"] is False


@pytest.mark.parametrize(
    "mutate",
    [
        lambda request: request["params"].pop("_meta"),
        lambda request: request["params"].update({"_meta": None}),
        lambda request: request["params"]["_meta"].pop(
            "io.modelcontextprotocol/protocolVersion"
        ),
        lambda request: request["params"]["_meta"].update(
            {"io.modelcontextprotocol/protocolVersion": None}
        ),
        lambda request: request["params"]["_meta"].pop(
            "io.modelcontextprotocol/clientCapabilities"
        ),
        lambda request: request["params"]["_meta"].update(
            {"io.modelcontextprotocol/clientCapabilities": None}
        ),
        lambda request: request["params"]["_meta"].update(
            {"io.modelcontextprotocol/clientCapabilities": []}
        ),
    ],
)
def test_required_meta_fields_reject_missing_null_and_wrong_types(mutate):
    request = rpc("tools/list")
    mutate(request)

    assert handle_request(request, dispatcher=None, decls=())["error"]["code"] == -32602


def test_optional_client_info_is_validated_when_present():
    absent = rpc("tools/list")
    del absent["params"]["_meta"]["io.modelcontextprotocol/clientInfo"]
    assert "result" in handle_request(absent, dispatcher=None, decls=())

    for malformed in (
        None,
        {},
        {"name": "client"},
        {"version": "1"},
        {"name": 7, "version": "1"},
        {"name": "client", "version": False},
    ):
        request = rpc("tools/list")
        request["params"]["_meta"]["io.modelcontextprotocol/clientInfo"] = malformed
        assert handle_request(request, dispatcher=None, decls=())["error"]["code"] == -32602


def test_complete_client_info_shape_accepts_schema_extensions():
    request = rpc("tools/list")
    request["params"]["_meta"]["io.modelcontextprotocol/clientInfo"] = {
        "name": "science-tests",
        "version": "1",
        "title": "Science Tests",
        "description": "MCP boundary fixture",
        "websiteUrl": "https://science.example/client",
        "icons": [
            {
                "src": "data:image/png;base64,AA==",
                "mimeType": "image/png",
                "sizes": ["48x48", "any"],
                "theme": "dark",
                "vendorIconField": True,
            }
        ],
        "vendorImplementationField": {"enabled": True},
    }

    assert "result" in handle_request(request, dispatcher=None, decls=())


@pytest.mark.parametrize(
    "malformed",
    [
        {"name": "client", "version": "1", "title": 7},
        {"name": "client", "version": "1", "description": []},
        {"name": "client", "version": "1", "websiteUrl": False},
        {"name": "client", "version": "1", "websiteUrl": "not a URI"},
        {"name": "client", "version": "1", "icons": 7},
        {"name": "client", "version": "1", "icons": [None]},
        {"name": "client", "version": "1", "icons": [{}]},
        {"name": "client", "version": "1", "icons": [{"src": 7}]},
        {"name": "client", "version": "1", "icons": [{"src": "icon.png"}]},
        {
            "name": "client",
            "version": "1",
            "icons": [{"src": "https://science.example/icon", "mimeType": 7}],
        },
        {
            "name": "client",
            "version": "1",
            "icons": [{"src": "https://science.example/icon", "sizes": "any"}],
        },
        {
            "name": "client",
            "version": "1",
            "icons": [
                {"src": "https://science.example/icon", "sizes": ["48x48", 48]}
            ],
        },
        {
            "name": "client",
            "version": "1",
            "icons": [{"src": "https://science.example/icon", "theme": "system"}],
        },
    ],
)
def test_client_info_rejects_malformed_present_known_fields(malformed):
    request = rpc("tools/list")
    request["params"]["_meta"]["io.modelcontextprotocol/clientInfo"] = malformed

    assert handle_request(request, dispatcher=None, decls=())["error"]["code"] == -32602


def test_complete_client_capabilities_shape_accepts_schema_extensions():
    request = rpc("tools/list")
    request["params"]["_meta"]["io.modelcontextprotocol/clientCapabilities"] = {
        "roots": {"futureRootsField": True},
        "sampling": {
            "context": {"supported": True},
            "tools": {},
            "futureSamplingField": [],
        },
        "elicitation": {
            "form": {},
            "url": {"modes": ["https"]},
            "futureElicitationField": 7,
        },
        "experimental": {"vendor-feature": {"enabled": True}},
        "extensions": {"com.example/client-feature": {}},
        "vendorCapability": 7,
    }

    assert "result" in handle_request(request, dispatcher=None, decls=())


@pytest.mark.parametrize(
    "malformed",
    [
        {"roots": []},
        {"sampling": []},
        {"sampling": {"context": True}},
        {"sampling": {"tools": []}},
        {"elicitation": False},
        {"elicitation": {"form": []}},
        {"elicitation": {"url": None}},
        {"experimental": []},
        {"experimental": {"vendor-feature": True}},
        {"extensions": []},
        {"extensions": {"com.example/client-feature": "enabled"}},
        {"extensions": {"unprefixed": {}}},
    ],
)
def test_client_capabilities_reject_malformed_present_known_fields(malformed):
    request = rpc("tools/list")
    request["params"]["_meta"]["io.modelcontextprotocol/clientCapabilities"] = malformed

    assert handle_request(request, dispatcher=None, decls=())["error"]["code"] == -32602


def test_unsupported_version_is_32022_with_versions():
    request = rpc("tools/list")
    request["params"]["_meta"][
        "io.modelcontextprotocol/protocolVersion"
    ] = "2025-06-18"

    error = handle_request(request, dispatcher=None, decls=())["error"]

    assert error == {
        "code": -32022,
        "message": "Unsupported protocol version",
        "data": {"supported": ["2026-07-28"], "requested": "2025-06-18"},
    }


@pytest.mark.parametrize(
    "broken",
    [
        "not an object",
        [],
        {"id": 1, "method": "tools/list", "params": {}},
        {"jsonrpc": "1.0", "id": 1, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": None, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": True, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 1.5, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 1, "method": 7, "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
            "extra": True,
        },
    ],
)
def test_exact_request_envelope_validation(broken):
    assert handle_request(broken, dispatcher=None, decls=())["error"]["code"] == -32600


def test_server_discover_matches_the_discovery_contract():
    result = handle_request(rpc("server/discover"), dispatcher=None, decls=())["result"]

    assert result == {
        "supportedVersions": ["2026-07-28"],
        "capabilities": {"tools": {}},
        "ttlMs": 300_000,
        "cacheScope": "public",
        "_meta": {
            "io.modelcontextprotocol/serverInfo": {
                "name": "science",
                "version": "0.1.0",
            }
        },
        "resultType": "complete",
    }


def test_server_discover_rejects_non_meta_params():
    response = handle_request(
        rpc("server/discover", {"cursor": "not-part-of-discovery"}),
        dispatcher=None,
        decls=(),
    )

    assert response["error"]["code"] == -32602


def test_tools_list_validates_its_optional_cursor_and_exact_fields():
    assert "result" in handle_request(rpc("tools/list"), dispatcher=None, decls=())
    for params in (
        {"cursor": "opaque"},
        {"cursor": None},
        {"cursor": 7},
        {"unknown": "field"},
    ):
        assert handle_request(rpc("tools/list", params), dispatcher=None, decls=())[
            "error"
        ]["code"] == -32602


def test_notifications_receive_no_response():
    notification = rpc("notifications/tools/list_changed")
    notification.pop("id")

    assert handle_request(notification, dispatcher=None, decls=()) is None


def test_discovery_and_tool_list_results_are_fresh():
    first_discovery = handle_request(
        rpc("server/discover"), dispatcher=None, decls=()
    )["result"]
    first_discovery["capabilities"]["tools"]["mutated"] = True
    first_discovery["_meta"]["io.modelcontextprotocol/serverInfo"]["name"] = "changed"
    second_discovery = handle_request(
        rpc("server/discover"), dispatcher=None, decls=()
    )["result"]

    first_list = handle_request(
        rpc("tools/list"), dispatcher=None, decls=production_tree()
    )["result"]
    first_list["tools"][0]["inputSchema"]["properties"]["cursor"]["type"] = "integer"
    second_list = handle_request(
        rpc("tools/list"), dispatcher=None, decls=production_tree()
    )["result"]

    assert second_discovery["capabilities"] == {"tools": {}}
    assert second_discovery["_meta"]["io.modelcontextprotocol/serverInfo"]["name"] == "science"
    assert second_list["tools"][0]["inputSchema"]["properties"]["cursor"]["type"] == "string"


def test_tools_call_rejects_unknown_protocol_fields_before_dispatch():
    response = handle_request(
        rpc(
            "tools/call",
            {"name": "status", "arguments": {}, "unknown": "field"},
        ),
        dispatcher=NeverDispatch(),
        decls=production_tree(),
    )

    assert response["error"]["code"] == -32602


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("inputResponses", [], "inputResponses must be an object"),
        ("requestState", 7, "requestState must be a string"),
    ],
)
def test_tools_call_validates_malformed_multi_round_fields(field, value, message):
    response = handle_request(
        rpc(
            "tools/call",
            {"name": "status", "arguments": {}, field: value},
        ),
        dispatcher=NeverDispatch(),
        decls=production_tree(),
    )

    assert response["error"] == {"code": -32602, "message": message}


@pytest.mark.parametrize(
    "state",
    [
        {"inputResponses": {}},
        {"requestState": "state-token"},
        {"inputResponses": {}, "requestState": "state-token"},
    ],
)
def test_tools_call_rejects_unsolicited_multi_round_state(state):
    response = handle_request(
        rpc("tools/call", {"name": "status", "arguments": {}, **state}),
        dispatcher=NeverDispatch(),
        decls=production_tree(),
    )

    assert response["error"] == {
        "code": -32602,
        "message": "science did not request multi-round input",
    }


def test_all_success_and_tool_error_results_are_complete(certified_work):
    declarations, dispatcher = dispatcher_for(certified_work)
    responses = (
        handle_request(rpc("server/discover"), dispatcher, declarations),
        handle_request(rpc("tools/list"), dispatcher, declarations),
        handle_request(
            rpc("tools/call", {"name": "status", "arguments": {}}),
            dispatcher,
            declarations,
        ),
        handle_request(
            rpc("tools/call", {"name": "status", "arguments": {"cursor": "junk"}}),
            dispatcher,
            declarations,
        ),
    )

    assert [response["result"]["resultType"] for response in responses] == [
        "complete",
        "complete",
        "complete",
        "complete",
    ]


def test_params_are_required():
    request = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}

    assert handle_request(request, dispatcher=None, decls=())["error"]["code"] == -32602


@pytest.mark.parametrize("params", [None, [], "bad", False])
def test_params_must_be_an_object(params):
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": params,
    }

    assert handle_request(request, dispatcher=None, decls=())["error"]["code"] == -32602


@pytest.mark.parametrize(
    "params",
    [
        {"name": "status", "arguments": []},
        {"name": "status", "arguments": None},
        {"name": 7, "arguments": {}},
        {"name": "status", "arguments": {"cursor": 3}},
        {"name": "status", "arguments": {"cursor": None}},
        {"name": "status", "arguments": {"invocation_id": 3}},
        {"name": "status", "arguments": {"invocation_id": None}},
    ],
)
def test_malformed_call_fields_are_protocol_errors(params):
    assert handle_request(
        rpc("tools/call", params),
        dispatcher=NeverDispatch(),
        decls=production_tree(),
    )["error"]["code"] == -32602


class NeverDispatch:
    def invoke(self, *args, **kwargs):
        raise AssertionError("unknown tools must not reach the dispatcher")


def test_unknown_tool_is_a_protocol_error_before_dispatch():
    response = handle_request(
        rpc("tools/call", {"name": "nope", "arguments": {}}),
        dispatcher=NeverDispatch(),
        decls=production_tree(),
    )

    assert response["error"]["code"] == -32602


def test_initialize_is_not_implemented():
    response = handle_request(rpc("initialize"), dispatcher=None, decls=())

    assert response["error"]["code"] == -32601


def test_parse_errors_and_non_objects_do_not_end_the_loop(certified_work):
    from helpers.world import write_cli_config

    config_path = write_cli_config(certified_work)
    duplicate = (
        '{"jsonrpc":"2.0","id":1,"id":2,"method":"tools/list","params":{}}\n'
    )
    stdin = io.BytesIO((
        "{bad json\n"
        + duplicate
        + "NaN\n"
        + json.dumps("not an object")
        + "\n"
        + json.dumps(rpc("tools/list"))
        + "\n"
    ).encode())
    stdout = io.StringIO()

    serve(config_path, stdin=stdin, stdout=stdout)

    assert stdout.getvalue().endswith("\n")
    lines = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert [line.get("error", {}).get("code") for line in lines[:4]] == [
        -32700,
        -32700,
        -32700,
        -32600,
    ]
    assert "result" in lines[4]


def test_oversized_json_integer_is_parse_error_and_loop_continues(certified_work):
    from helpers.world import write_cli_config

    config_path = write_cli_config(certified_work)
    oversized_id = "9" * 5000
    stdin = io.BytesIO((
        '{"jsonrpc":"2.0","id":'
        + oversized_id
        + ',"method":"tools/list","params":{}}\n'
        + json.dumps(rpc("tools/list"))
        + "\n"
    ).encode())
    stdout = io.StringIO()

    serve(config_path, stdin=stdin, stdout=stdout)

    lines = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert lines[0]["error"]["code"] == -32700
    assert "result" in lines[1]


def test_invalid_utf8_and_oversized_frames_do_not_desynchronize_stdio(certified_work):
    from helpers.world import write_cli_config

    valid = (json.dumps(rpc("tools/list")) + "\n").encode()
    stdin = io.BytesIO(
        b"\xff\n" + b"x" * (MAX_REQUEST_BYTES + 1) + b"\n" + valid
    )
    stdout = io.StringIO()

    serve(write_cli_config(certified_work), stdin=stdin, stdout=stdout)

    lines = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert lines[0]["error"]["code"] == -32700
    assert lines[1]["error"]["code"] == -32600
    assert "result" in lines[2]


def test_transport_equivalence_cli_vs_mcp(certified_work, capsys):
    from helpers.world import write_cli_config
    from science.cli import main
    from science.config import ReadContext, load_config
    from science.dispatch import Dispatcher
    from science.loader import resolve_handlers

    config_path = write_cli_config(certified_work)
    assert main(["status", "--config", str(config_path)]) == 0
    cli_text = capsys.readouterr().out
    declarations = production_tree()
    dispatcher = Dispatcher(
        declarations,
        resolve_handlers(declarations),
        ReadContext.open(load_config(config_path)),
    )

    mcp_text = handle_request(
        rpc("tools/call", {"name": "status", "arguments": {}}),
        dispatcher,
        declarations,
    )["result"]["content"][0]["text"]

    assert cli_text == mcp_text


def test_refusal_becomes_a_complete_tool_error_with_full_envelope():
    declaration = production_tree()[0]

    class RefusingDispatcher:
        def invoke(self, *args, **kwargs):
            raise Refused(
                Refusal("kernel-refused", "denied", {"kind": "fixture"}),
                "caller_id",
            )

    response = handle_request(
        rpc("tools/call", {"name": declaration.name, "arguments": {}}),
        RefusingDispatcher(),
        (declaration,),
    )

    assert response == {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "content": [{"type": "text", "text": "refused [kernel-refused] denied"}],
            "structuredContent": {
                "refusal": {
                    "code": "kernel-refused",
                    "message": "denied",
                    "data": {"kind": "fixture"},
                },
                "invocation_id": "caller_id",
            },
            "isError": True,
            "resultType": "complete",
        },
    }


def test_internal_dispatch_error_is_generic_and_does_not_leak():
    declaration = production_tree()[0]

    class BrokenDispatcher:
        def invoke(self, *args, **kwargs):
            raise RuntimeError("private implementation detail")

    response = handle_request(
        rpc("tools/call", {"name": declaration.name, "arguments": {}}),
        BrokenDispatcher(),
        (declaration,),
    )

    assert response == {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {"code": -32603, "message": "Internal error"},
    }
    assert "private implementation detail" not in json.dumps(response)


def test_serve_passes_session_only_as_dispatcher_injection(
    certified_work, monkeypatch
):
    import science.mcp as mcp
    from helpers.world import write_cli_config

    sentinel = object()
    captured = []

    class CapturingDispatcher:
        def __init__(self, declarations, handlers, context, session=None):
            captured.append(session)

    monkeypatch.setattr(mcp, "Dispatcher", CapturingDispatcher)

    serve(
        write_cli_config(certified_work),
        stdin=io.BytesIO(),
        stdout=io.StringIO(),
        session=sentinel,
    )

    assert captured == [sentinel]


def test_notification_frame_is_silent_and_following_request_is_served(
    certified_work,
):
    from helpers.world import write_cli_config

    notification = rpc("notifications/tools/list_changed")
    notification.pop("id")
    stdin = io.BytesIO(
        (
            json.dumps(notification)
            + "\n"
            + json.dumps(rpc("tools/list"))
            + "\n"
        ).encode()
    )
    stdout = io.StringIO()

    serve(write_cli_config(certified_work), stdin=stdin, stdout=stdout)

    lines = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert len(lines) == 1
    assert "result" in lines[0]


def test_cli_mcp_serve_resolves_config_and_starts_server(monkeypatch):
    import science.mcp as mcp
    from science.cli import main

    captured = []
    monkeypatch.setattr(mcp, "serve", captured.append)

    assert main(["mcp", "serve", "--config", "relative-science.toml"]) == 0
    assert captured == [Path("relative-science.toml")]
