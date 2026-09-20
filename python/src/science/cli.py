"""The science CLI: sessionless reads, service-routed writes (spec §9.2)."""
from __future__ import annotations

import argparse
import json
import socket
import sys
from pathlib import Path

from science.config import ReadContext, load_config, resolve_config_path
from science.dispatch import Dispatcher
from science.loader import production_tree, resolve_handlers
from science.refusal import INVOCATION_ID_RE, Refusal, Refused, envelope, mint_token
from science.schema import Declaration

EXIT_OK, EXIT_INTERNAL, EXIT_USAGE, EXIT_REFUSED = 0, 1, 2, 3


def _add_command(
    subparsers: argparse._SubParsersAction,
    decl: Declaration,
    common: argparse.ArgumentParser,
) -> None:
    parser = subparsers.add_parser(decl.name, help=decl.purpose, parents=[common])
    for spec in decl.inputs:
        kwargs: dict[str, object] = {
            "dest": spec.name,
            "help": spec.doc,
            "required": spec.required,
        }
        match spec.type:
            case "int":
                kwargs["type"] = int
            case "bool":
                kwargs["action"] = argparse.BooleanOptionalAction
            case "enum":
                kwargs["choices"] = spec.choices
            case "list-of-string":
                kwargs["action"] = "append"
        parser.add_argument("--" + spec.name.replace("_", "-"), **kwargs)


def _command_options() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config", type=Path)
    common.add_argument("--invocation-id", dest="invocation_id")
    common.add_argument("--continue", dest="cursor")
    return common


def build_parser(decls) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="science")
    parser.add_argument("-V", "--version", action="version", version="science 0.1.0")
    common = _command_options()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for decl in decls:
        _add_command(subparsers, decl, common)
    subparsers.add_parser("build", help="Build the world from its corpora")
    serve_parser = subparsers.add_parser("serve", help="Serve the world over HTTP")
    serve_parser.add_argument("--config", type=Path)
    mcp = subparsers.add_parser("mcp", help="Serve the world over MCP on stdio")
    mcp.add_argument("mode", choices=["serve"])
    mcp.add_argument("--config", type=Path)
    adapters = subparsers.add_parser("adapters", help="Build the corpus adapters")
    adapters.add_argument("mode", choices=["build"])
    adapters.add_argument(
        "--out",
        type=Path,
        help="directory to build into (default: the repository's adapters/claude-code)",
    )
    subparsers.add_parser("help", help="Print a command's help").add_argument(
        "words", nargs="*"
    )
    return parser


def _json_line(value: dict[str, object]) -> None:
    sys.stderr.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def _bind_invocation_id(value: object) -> str:
    if type(value) is str and INVOCATION_ID_RE.fullmatch(value) is not None:
        return value
    invocation_id = mint_token()
    if value is not None:
        raise Refused(
            Refusal("invalid-input", "invocation_id outside its grammar"),
            invocation_id,
        )
    return invocation_id


def main(argv: list[str] | None = None) -> int:
    invocation_id = None
    try:
        declarations = production_tree()
        namespace = build_parser(declarations).parse_args(argv)
        if namespace.command == "help":
            build_parser(declarations).parse_args([*namespace.words, "--help"])
            return EXIT_OK
        if namespace.command in {"mcp", "adapters", "build", "serve"}:
            return _framework_verb(namespace)
        invocation_id = _bind_invocation_id(namespace.invocation_id)
        namespace.invocation_id = invocation_id
        declaration = next(decl for decl in declarations if decl.name == namespace.command)
        inputs = {
            spec.name: value
            for spec in declaration.inputs
            if (value := getattr(namespace, spec.name)) is not None
        }
        if declaration.write_class.kind != "read-only":
            return _via_service(namespace, declaration, inputs)
        config = load_config(resolve_config_path(namespace.config))
        output = Dispatcher(
            declarations,
            resolve_handlers(declarations),
            ReadContext.open(config),
        ).invoke(
            namespace.command,
            inputs,
            invocation_id=invocation_id,
            cursor=namespace.cursor,
        )
        sys.stdout.write(output.text)
        _json_line({"invocation_id": output.invocation_id})
        return EXIT_OK
    except Refused as error:
        payload: dict[str, object] = {"refusal": envelope(error.refusal)}
        bound_id = error.invocation_id or invocation_id
        if bound_id is not None:
            payload["invocation_id"] = bound_id
        _json_line(payload)
        return EXIT_REFUSED
    except Exception:  # noqa: BLE001 -- CLI last resort
        payload = {"error": {"code": "internal-error", "message": "Internal error"}}
        if invocation_id is not None:
            payload["invocation_id"] = invocation_id
        _json_line(payload)
        return EXIT_INTERNAL


def _framework_verb(namespace) -> int:
    declarations = production_tree()
    if namespace.command == "mcp":
        from science.mcp import serve

        serve(resolve_config_path(namespace.config))
        return EXIT_OK
    if namespace.command == "build":
        from science.adapters import preflight_build
        from science.loader import COMMANDS_ROOT, REPO_ROOT

        preflight_build(declarations, COMMANDS_ROOT, REPO_ROOT / "skills")
        sys.stdout.write(f"ok: {len(declarations)} command(s)\n")
        return EXIT_OK
    if namespace.command == "serve":
        from science.serve import serve as build_server

        config = load_config(resolve_config_path(namespace.config))
        server = build_server(config, config.service_socket)
        try:
            server.serve_forever()
        finally:
            server.server_close()
        return EXIT_OK
    if namespace.command == "adapters":
        from science.adapters import build_adapter
        from science.loader import COMMANDS_ROOT, REPO_ROOT

        build_adapter(
            declarations,
            COMMANDS_ROOT,
            REPO_ROOT / "skills",
            namespace.out or REPO_ROOT / "adapters" / "claude-code",
        )
        return EXIT_OK
    raise NotImplementedError(f"{namespace.command} arrives in a later task")


def _via_service(namespace, declaration: Declaration, inputs: dict[str, object]) -> int:
    """Any write-class command goes over the service socket, preserving the
    read path's public wire: text on stdout, one JSON line on stderr."""
    invocation_id = namespace.invocation_id or mint_token()
    try:
        config = load_config(resolve_config_path(namespace.config))
        with socket.socket(socket.AF_UNIX) as connection:
            connection.connect(str(config.service_socket))
            connection.sendall(json.dumps({
                "command": declaration.name,
                "inputs": inputs,
                "invocation_id": invocation_id,
                "cursor": namespace.cursor,
            }).encode() + b"\n")
            reply = json.loads(connection.makefile().readline())
    except (FileNotFoundError, ConnectionRefusedError):
        refusal = Refusal("permit-exceeded",
                          "no writer service; start one with: science serve")
        _json_line({"invocation_id": invocation_id, "refusal": envelope(refusal)})
        return EXIT_REFUSED
    except Refused as error:
        _json_line({"invocation_id": error.invocation_id or invocation_id,
                    "refusal": envelope(error.refusal)})
        return EXIT_REFUSED
    if reply["ok"]:
        sys.stdout.write(reply["text"])
        _json_line({"invocation_id": reply["invocation_id"]})
        return EXIT_OK
    _json_line({"invocation_id": reply.get("invocation_id", invocation_id),
                "refusal": reply["refusal"]})
    return EXIT_REFUSED


if __name__ == "__main__":
    raise SystemExit(main())
