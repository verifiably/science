"""The science CLI: sessionless reads, service-routed writes."""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import time
from dataclasses import replace
from pathlib import Path

from science.config import ReadContext, load_config, resolve_config_path
from science.dispatch import Dispatcher
from science.loader import production_tree, resolve_handlers
from science.refusal import INVOCATION_ID_RE, WORLD_READ_ERRORS, Refusal, Refused, envelope, kernel_refusal, mint_token
from science.report import serialize_block
from science.run_endpoint.handle import Handle
from science.schema import Declaration
from science.stop import stop_signals_exit, stop_signals_held

EXIT_OK, EXIT_INTERNAL, EXIT_USAGE, EXIT_REFUSED = 0, 1, 2, 3


_LAUNCHER_PROJECT_HELP = "Open the session under this project, by name or coord: address."


# A declared input named for a shared CLI vocabulary option takes the
# vocabulary's short names too, so the generated surface is the shared option
# See tools/cli.toml for the parser inventory.
_VOCABULARY_ALIASES = {"limit": ("-n",)}
_WORKFLOW_ENV_COMMANDS = frozenset({"derive", "run", "verify"})
# Path inputs resolved in the caller's directory: a write's are read by the service, which runs in another.
_CALLER_PATHS = {
    "acquire-import": ("log", "members", "journals"),
    "exposure-event": ("payload",),
    "reservation-assignment": ("payload",),
    "reservation-statement": ("check",),
    "spec": ("estimand",),
}
# A read whose directory input the attended CLI may write instead: exactly one of the two is given. The option is
# no declared input, so MCP, run handles and cursors never carry it.
_WRITABLE_INPUTS = {"reservation-statement": "check"}


def _add_command(
    subparsers: argparse._SubParsersAction,
    decl: Declaration,
    common: argparse.ArgumentParser,
    name: str | None = None,
) -> None:
    parser = subparsers.add_parser(name or decl.name, help=decl.purpose, parents=[common])
    parser.set_defaults(command=decl.name)
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
        target = parser
        if _WRITABLE_INPUTS.get(decl.name) == spec.name:
            kwargs["required"] = False
            target = parser.add_mutually_exclusive_group(required=True)
            target.add_argument("--write", dest="write_directory", type=Path,
                                help="Directory whose files to replace; attended CLI only.")
        target.add_argument("--" + spec.name.replace("_", "-"), *_VOCABULARY_ALIASES.get(spec.name, ()), **kwargs)

    if decl.name in _WORKFLOW_ENV_COMMANDS:
        parser.add_argument(
            "--workflow-project",
            dest="workflow_project",
            type=Path,
            help="Local workflow project directory (pyproject.toml + uv.lock) to prepare into a workflow environment before dispatch.",
        )

    if decl.selects:
        parser.add_argument(
            "--project", dest="project",
            help="Read through this project, by name or coord: address, for this invocation only.",
        )


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
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="<command>")
    from science.acquisition.operator import add_local_parsers
    acquire = subparsers.add_parser("acquire", help="Retrieve and accept static acquisition sets")
    verbs = acquire.add_subparsers(required=True, metavar="<operation>")
    add_local_parsers(verbs)
    for decl in decls:
        if decl.name in {"acquire-seal", "acquire-import"}:
            _add_command(verbs, decl, common, decl.name.removeprefix("acquire-"))
        else:
            _add_command(subparsers, decl, common)
    subparsers.add_parser("build", help="Build the world from its corpora")
    epoch = subparsers.add_parser("epoch", help="Publish an epoch over the session's corpora, or report the current one")
    epoch.add_argument("--config", type=Path)
    serve_parser = subparsers.add_parser("serve", help="Serve an attended session or launch a supervised run")
    serve_parser.add_argument("--run", type=Path)
    serve_parser.add_argument("--config", type=Path)
    serve_parser.add_argument("--project", help=_LAUNCHER_PROJECT_HELP)
    mcp = subparsers.add_parser("mcp", help="Serve commands over MCP on stdio or bridge to a run endpoint")
    mcp.add_argument("mode", choices=["serve", "bridge"])
    mcp.add_argument("--config", type=Path)
    mcp.add_argument("--project", help=_LAUNCHER_PROJECT_HELP)
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


_SELECTION_QUERY = b'{"query":"selection"}\n'
_SELECTION_TIMEOUT_SECONDS = 5


def _ambient_selection(config):
    """the live session's selection, asked
    over the service socket, and the configuration's `default_project` only
    when no session is live. A live session's null is the answer. Any failure
    but "nothing listens" propagates: a live session this read could not ask
    is not an absent one."""
    from beliefs.coordination import CoordinationAddress

    from science.serve import MAX_SOCKET_PATH_BYTES

    if config.coordination is None:
        return None  # no resolver: nothing can be selected
    path = str(config.service_socket)
    if len(path.encode()) > MAX_SOCKET_PATH_BYTES:
        return config.default_project  # no launcher can bind it, so none is live
    try:
        deadline = time.monotonic() + _SELECTION_TIMEOUT_SECONDS
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(max(0, deadline - time.monotonic()))
            connection.connect(path)
            connection.settimeout(max(0, deadline - time.monotonic()))
            connection.sendall(_SELECTION_QUERY)
            response = bytearray()
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError("the selection query deadline expired")
                connection.settimeout(remaining)
                chunk = connection.recv(4096)
                response.extend(chunk)
                if not chunk or b"\n" in chunk:
                    break
            reply = json.loads(response.partition(b"\n")[0].decode())
    except (FileNotFoundError, ConnectionRefusedError):
        return config.default_project
    if type(reply) is not dict or set(reply) != {"project"}:
        raise RuntimeError("the live session did not answer the selection query")
    if reply["project"] is None:
        return None
    address = CoordinationAddress.parse(reply["project"])
    if address.local is not None or address.revision is not None:
        raise RuntimeError("the live session answered with something other than a project address")
    return address


def main(argv: list[str] | None = None) -> int:
    invocation_id = None
    prepared_environment: str | None = None
    try:
        declarations = production_tree()
        namespace = build_parser(declarations).parse_args(argv)
        if namespace.command == "help":
            build_parser(declarations).parse_args([*namespace.words, "--help"])
            return EXIT_OK
        handle = Handle.from_env(os.environ, config=getattr(namespace, "config", None))
        if namespace.command in {"acquire-start", "acquire-resume", "acquire-status"}:
            if handle is not None:
                raise Refused(Refusal("handle-mode", "Local acquisition work is unavailable in handle mode"))
            from science.acquisition.operator import operate
            operate(namespace)
            return EXIT_OK
        if namespace.command == "mcp" and namespace.mode == "bridge":
            if handle is None:
                raise Refused(Refusal("handle-incomplete", "The MCP bridge requires both handle paths"))
            if namespace.project is not None:
                raise Refused(Refusal("handle-mode", "The supervisor selects the run project"))
            from science.mcp import bridge

            with stop_signals_exit():
                bridge(handle)
            return EXIT_OK
        if namespace.command in {"mcp", "adapters", "build", "serve", "epoch"}:
            if handle is not None:
                raise Refused(Refusal("handle-mode", f"{namespace.command} is unavailable in handle mode"))
            return _framework_verb(namespace)
        invocation_id = _bind_invocation_id(namespace.invocation_id)
        namespace.invocation_id = invocation_id
        declaration = next(decl for decl in declarations if decl.name == namespace.command)
        inputs = {
            spec.name: value
            for spec in declaration.inputs
            if (value := getattr(namespace, spec.name)) is not None
        }
        workflow_project = getattr(namespace, "workflow_project", None)
        prepared_config = None
        if workflow_project is not None:
            if handle is not None:
                raise Refused(
                    Refusal("handle-mode", "--workflow-project is unavailable in handle mode"),
                    invocation_id,
                )
            if namespace.command not in _WORKFLOW_ENV_COMMANDS:
                raise Refused(
                    Refusal("invalid-input", f"{namespace.command} does not accept --workflow-project"),
                    invocation_id,
                )
            if "workflow_environment" in inputs:
                raise Refused(
                    Refusal("invalid-input", "--workflow-project and --workflow-environment are mutually exclusive"),
                    invocation_id,
                )
            if namespace.cursor is not None:
                raise Refused(
                    Refusal(
                        "invalid-input",
                        "--workflow-project cannot be used with --continue; pass --workflow-environment <key> instead",
                    ),
                    invocation_id,
                )
            from science.workflow_environment import prepare_environment

            prepared_config = load_config(resolve_config_path(namespace.config))
            prepared_environment = prepare_environment(workflow_project, prepared_config.operations_root)
            inputs["workflow_environment"] = prepared_environment
        if getattr(namespace, "write_directory", None) is not None:
            return _write_files(namespace, inputs, handle, invocation_id)
        project = getattr(namespace, "project", None)
        if handle is not None:
            dispatcher = handle
        elif declaration.write_class.kind != "read-only":
            return _via_service(
                namespace,
                declaration,
                inputs,
                prepared_environment=prepared_environment,
                config=prepared_config,
            )
        else:
            inputs = _from_caller(declaration, inputs)
            config = load_config(resolve_config_path(namespace.config))
            if namespace.command in {"heads", "log"}:
                # These handlers inspect the configured chains themselves. Opening
                # an attended world here would settle the pending evidence first.
                ctx = ReadContext(world=None, config=config)
                selection = None
            else:
                ctx = ReadContext.open(config)
                selection = None if project is not None else _ambient_selection(config)
            dispatcher = Dispatcher(declarations, resolve_handlers(declarations), ctx, selection=selection)
        output = dispatcher.invoke(
            namespace.command,
            inputs,
            invocation_id=invocation_id,
            cursor=namespace.cursor,
            project=project,
        )
        sys.stdout.write(output.text)
        meta: dict[str, object] = {"invocation_id": output.invocation_id}
        if prepared_environment is not None:
            meta["workflow_environment"] = prepared_environment
        _json_line(meta)
        return EXIT_OK
    except Refused as error:
        payload: dict[str, object] = {"refusal": envelope(error.refusal)}
        bound_id = error.invocation_id or invocation_id
        if bound_id is not None:
            payload["invocation_id"] = bound_id
        if prepared_environment is not None:
            payload["workflow_environment"] = prepared_environment
        _json_line(payload)
        return EXIT_REFUSED
    except Exception:  # noqa: BLE001 -- CLI last resort
        payload = {"error": {"code": "internal-error", "message": "Internal error"}}
        if invocation_id is not None:
            payload["invocation_id"] = invocation_id
        if prepared_environment is not None:
            payload["workflow_environment"] = prepared_environment
        _json_line(payload)
        return EXIT_INTERNAL


def _framework_verb(namespace) -> int:
    declarations = production_tree()
    if namespace.command == "mcp":
        from science.mcp import serve

        with stop_signals_exit():
            serve(resolve_config_path(namespace.config), project=namespace.project)
        return EXIT_OK
    if namespace.command == "build":
        from science.adapters import preflight_build
        from science.loader import COMMANDS_ROOT, REPO_ROOT

        preflight_build(declarations, COMMANDS_ROOT, REPO_ROOT / "skills")
        sys.stdout.write(f"ok: {len(declarations)} command(s)\n")
        return EXIT_OK
    if namespace.command == "serve":
        if namespace.run is not None:
            if namespace.config is not None or namespace.project is not None or "SCIENCE_CONFIG" in os.environ:
                raise Refused(Refusal("invalid-input", "Run startup takes its configuration and project from the launch file"))
            from science.run_endpoint.launch import read_launch
            from science.run_endpoint.service import serve_run

            return serve_run(read_launch(namespace.run))
        from science.serve import serve as build_server

        config = load_config(resolve_config_path(namespace.config))
        server = None
        with stop_signals_exit(), stop_signals_held() as release:
            try:
                server = build_server(config, config.service_socket, project=namespace.project)
                release()
                server.serve_forever()
            finally:
                if server is not None:
                    with stop_signals_held():
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
    if namespace.command == "epoch":
        from science.world_belief import publish_session_epoch

        published = publish_session_epoch(load_config(resolve_config_path(namespace.config)))
        sys.stdout.write(f"{published.state}: {published.packaging_identity}\n")
        sys.stdout.writelines(f"  {corpus_id} {state}\n" for corpus_id, state in published.coverage)
        return EXIT_OK
    raise NotImplementedError(f"{namespace.command} arrives in a later task")


def _from_caller(declaration: Declaration, inputs: dict[str, object]) -> dict[str, object]:
    return {**inputs, **{key: str(Path(inputs[key]).absolute())
                         for key in _CALLER_PATHS.get(declaration.name, ()) if key in inputs}}


def _write_files(namespace, inputs: dict[str, object], handle, invocation_id: str) -> int:
    """`reservation-statement --write`: render in this process and replace the two files."""
    if handle is not None:
        raise Refused(Refusal("handle-mode", "--write is unavailable in handle mode"), invocation_id)
    checked = sorted({"block_on", "all_considered"} & set(inputs))
    if namespace.cursor is not None or checked:
        refused = ", ".join("--" + name.replace("_", "-") for name in (*checked, *(("continue",) if namespace.cursor else ())))
        raise Refused(Refusal("invalid-input", f"--write does not combine with {refused}"), invocation_id)
    from science.commands.reservation_statement import write
    from science.coordination import resolve_project_ref

    config = load_config(resolve_config_path(namespace.config))
    ctx = ReadContext.open(config)
    selection = _ambient_selection(config) if namespace.project is None else resolve_project_ref(ctx, namespace.project)
    try:
        report = write(replace(ctx, selection=selection), directory=namespace.write_directory.absolute(), **inputs)
    except WORLD_READ_ERRORS as caught:
        raise Refused(kernel_refusal(caught), invocation_id) from caught
    sys.stdout.write("".join(serialize_block(block) for block in report))
    _json_line({"invocation_id": invocation_id})
    return EXIT_OK


def _via_service(
    namespace,
    declaration: Declaration,
    inputs: dict[str, object],
    *,
    prepared_environment: str | None = None,
    config=None,
) -> int:
    """Any write-class command goes over the service socket, preserving the
    read path's public wire: text on stdout, one JSON line on stderr."""
    invocation_id = namespace.invocation_id or mint_token()
    inputs = _from_caller(declaration, inputs)

    def _meta(payload: dict[str, object]) -> dict[str, object]:
        if prepared_environment is not None:
            payload["workflow_environment"] = prepared_environment
        return payload

    try:
        resolved_config = config if config is not None else load_config(resolve_config_path(namespace.config))
        with socket.socket(socket.AF_UNIX) as connection:
            connection.connect(str(resolved_config.service_socket))
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
        _json_line(_meta({"invocation_id": invocation_id, "refusal": envelope(refusal)}))
        return EXIT_REFUSED
    except Refused as error:
        _json_line(_meta({"invocation_id": error.invocation_id or invocation_id,
                          "refusal": envelope(error.refusal)}))
        return EXIT_REFUSED
    if reply["ok"]:
        sys.stdout.write(reply["text"])
        _json_line(_meta({"invocation_id": reply["invocation_id"]}))
        return EXIT_OK
    _json_line(_meta({"invocation_id": reply.get("invocation_id", invocation_id),
                      "refusal": reply["refusal"]}))
    return EXIT_REFUSED


if __name__ == "__main__":
    raise SystemExit(main())
