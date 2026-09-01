"""Load the production command tree and bind handlers by convention."""
from __future__ import annotations

import importlib
import inspect
from pathlib import Path

from science.schema import (
    Declaration,
    DeclarationError,
    handler_module,
    load_command_tree,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
COMMANDS_ROOT = REPO_ROOT / "commands"


def production_kind_acts() -> dict[str, frozenset[str]]:
    # Explicitly empty until Task 12 imports beliefs.permit.KIND_ACTS.
    return {}


def production_tree() -> tuple[Declaration, ...]:
    kind_acts = production_kind_acts()
    declarations = load_command_tree(
        COMMANDS_ROOT,
        kind_acts=kind_acts,
        contract_kinds=frozenset(kind_acts),
    )
    for declaration in declarations:
        if declaration.write_class.kind != "read-only":
            raise DeclarationError(
                declaration.directory / "command.toml",
                "write_class",
                "production write commands require beliefs capabilities",
            )
    return declarations


def resolve_handlers(declarations) -> dict:
    handlers = {}
    for declaration in declarations:
        module_name = handler_module(declaration.name)
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError as caught:
            raise DeclarationError(
                declaration.directory,
                "handler",
                f"cannot import {module_name}: {caught}",
            ) from caught
        handle = getattr(module, "handle", None)
        if not callable(handle):
            raise DeclarationError(
                declaration.directory,
                "handler",
                f"{module_name} has no callable handle()",
            )
        try:
            parameters = list(inspect.signature(handle).parameters.values())
        except (TypeError, ValueError) as caught:
            raise DeclarationError(
                declaration.directory, "handler", f"cannot inspect handle(): {caught}"
            ) from caught

        positional_or_keyword = inspect.Parameter.POSITIONAL_OR_KEYWORD
        keyword_only = inspect.Parameter.KEYWORD_ONLY

        def shape_error(reason: str):
            raise DeclarationError(declaration.directory, "handler", reason)

        forbidden = (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
            inspect.Parameter.POSITIONAL_ONLY,
        )
        if any(parameter.kind in forbidden for parameter in parameters):
            shape_error("no *args, **kwargs, or positional-only parameters")
        lead = (
            ["ctx", "writer"]
            if declaration.write_class.kind != "read-only"
            else ["ctx"]
        )
        if [parameter.name for parameter in parameters[: len(lead)]] != lead or any(
            parameter.kind is not positional_or_keyword
            for parameter in parameters[: len(lead)]
        ):
            shape_error(f"handler must lead with exactly {lead}")
        rest = parameters[len(lead) :]
        if any(parameter.kind is not keyword_only for parameter in rest):
            shape_error("declared inputs must be keyword-only (after a bare *)")
        declared = {input_spec.name: input_spec for input_spec in declaration.inputs}
        accepted = {parameter.name for parameter in rest}
        if set(declared) != accepted:
            shape_error(
                f"handler accepts {sorted(accepted)}, declaration says {sorted(declared)}"
            )
        by_name = {parameter.name: parameter for parameter in rest}
        for name, input_spec in declared.items():
            default = by_name[name].default
            if input_spec.required and default is not inspect.Parameter.empty:
                shape_error(f"required input {name!r} must have no handler default")
            if not input_spec.required and default is not None:
                shape_error(f"optional input {name!r} must default to None")
        handlers[declaration.name] = handle
    return handlers
