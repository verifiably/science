"""The science CLI: sessionless reads, service-routed writes (spec §9.2)."""
from __future__ import annotations

import argparse
import sys

from science.config import ReadContext, load_config, resolve_config_path
from science.dispatch import Dispatcher
from science.loader import production_tree, resolve_handlers
from science.refusal import Refused
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


def _protocol_options() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config")
    common.add_argument("--invocation-id", dest="invocation_id")
    common.add_argument("--continue", dest="cursor")
    return common


def build_parser(decls) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="science")
    common = _protocol_options()
    subparsers = parser.add_subparsers(dest="command", required=True)
    for decl in decls:
        _add_command(subparsers, decl, common)
    for verb in ("serve", "build"):
        subparsers.add_parser(verb, parents=[common])
    mcp = subparsers.add_parser("mcp", parents=[common])
    mcp.add_argument("mode", choices=["serve"])
    adapters = subparsers.add_parser("adapters", parents=[common])
    adapters.add_argument("mode", choices=["build"])
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        declarations = production_tree()
        namespace = build_parser(declarations).parse_args(argv)
        if namespace.command in {"serve", "mcp", "adapters", "build"}:
            return _framework_verb(namespace)
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
            invocation_id=namespace.invocation_id,
            cursor=namespace.cursor,
        )
        sys.stdout.write(output.text)
        return EXIT_OK
    except Refused as error:
        sys.stderr.write(f"refused [{error.refusal.code}] {error.refusal.message}\n")
        return EXIT_REFUSED
    except Exception as error:  # noqa: BLE001 -- CLI last resort
        sys.stderr.write(f"internal error: {error}\n")
        return EXIT_INTERNAL


def _framework_verb(namespace) -> int:
    raise NotImplementedError(f"{namespace.command} arrives in a later task")


def _via_service(namespace, declaration: Declaration, inputs: dict[str, object]) -> int:
    raise NotImplementedError("write routing arrives with the service process (Task 13)")


if __name__ == "__main__":
    raise SystemExit(main())
