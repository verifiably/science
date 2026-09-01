"""Command declarations: the schema every command must fit (spec §3)."""
from __future__ import annotations

import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

NAME_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
INPUT_NAME_RE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
MAX_NAME_BYTES = 32
RESERVED_COMMANDS = frozenset({"continue", "serve", "mcp", "adapters", "build"})
RESERVED_INPUTS = frozenset({"cursor", "invocation_id", "view", "session", "config"})
INPUT_TYPES = frozenset({"string", "int", "bool", "enum", "list-of-string"})
WRITE_CLASS_KINDS = frozenset({"read-only", "coordination", "mints", "publishes"})
SCHEMA_VERSION = 1

_TOML_CHECKS = {
    "string": lambda v: type(v) is str,
    "int": lambda v: type(v) is int,
    "bool": lambda v: type(v) is bool,
    "enum": lambda v: type(v) is str,
    "list-of-string": lambda v: type(v) is list and all(type(x) is str for x in v),
}


class DeclarationError(Exception):
    def __init__(self, path: Path, field_name: str, reason: str) -> None:
        self.path, self.field, self.reason = path, field_name, reason
        super().__init__(f"{path}: [{field_name}] {reason}")


@dataclass(frozen=True)
class InputSpec:
    name: str
    type: str
    required: bool
    doc: str
    default: object = None
    choices: tuple[str, ...] = ()


@dataclass(frozen=True)
class WriteClass:
    kind: str
    kinds: tuple[str, ...] = ()
    routes: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Declaration:
    name: str
    purpose: str
    write_class: WriteClass
    output_budget: int
    inputs: tuple[InputSpec, ...]
    reads: tuple[str, ...]
    directory: Path


def handler_module(name: str) -> str:
    return "science.commands." + name.replace("-", "_")


def _require(cond: bool, path: Path, field_name: str, reason: str) -> None:
    if not cond:
        raise DeclarationError(path, field_name, reason)


def _parse_inputs(raw: Mapping, path: Path) -> tuple[InputSpec, ...]:
    specs = []
    for name, spec in raw.items():
        _require(isinstance(spec, dict), path, f"inputs.{name}", "must be a table")
        _require(name not in RESERVED_INPUTS, path, f"inputs.{name}", "reserved input name")
        _require(bool(INPUT_NAME_RE.fullmatch(name)) and len(name.encode()) <= MAX_NAME_BYTES,
                 path, f"inputs.{name}", "input names are snake_case, max 32 bytes")
        typ = spec.get("type")
        _require(type(typ) is str and typ in INPUT_TYPES, path, f"inputs.{name}.type",
                 f"must be one of {sorted(INPUT_TYPES)}")
        required = spec.get("required")
        _require(isinstance(required, bool), path, f"inputs.{name}.required", "must be a bool")
        doc = spec.get("doc")
        _require(type(doc) is str and doc, path, f"inputs.{name}.doc", "must be a non-empty string")
        raw_choices = spec.get("choices", [])
        _require(type(raw_choices) is list, path, f"inputs.{name}.choices",
                 "must be a list — a string would be read as characters")
        choices = tuple(raw_choices)
        if typ == "enum":
            _require(len(choices) > 0 and all(type(c) is str for c in choices)
                     and len(set(choices)) == len(choices),
                     path, f"inputs.{name}.choices", "enum requires unique string choices")
        else:
            _require(not choices, path, f"inputs.{name}.choices", "only enum takes choices")
        default = spec.get("default")
        if required:
            _require(default is None, path, f"inputs.{name}.default", "required input forbids default")
        if default is not None:
            _require(_TOML_CHECKS[typ](default), path, f"inputs.{name}.default",
                     f"default is not a {typ}")
            if typ == "enum":
                _require(default in choices, path, f"inputs.{name}.default",
                         "default is not one of choices")
        known = {"type", "required", "doc", "choices", "default"}
        extra = set(spec) - known
        _require(not extra, path, f"inputs.{name}", f"unknown keys {sorted(extra)}")
        specs.append(InputSpec(name, typ, required, doc, default, choices))
    return tuple(specs)


def _parse_write_class(raw: str, routes_raw: Mapping[str, str], path: Path,
                       kind_acts: Mapping[str, frozenset[str]],
                       contract_kinds: frozenset[str]) -> WriteClass:
    if raw in ("read-only", "coordination", "publishes"):
        _require(not routes_raw, path, "write.routes", f"{raw} takes no routes")
        return WriteClass(raw)
    _require(raw.startswith("mints:"), path, "write_class",
             "must be read-only | coordination | mints:<kinds> | publishes")
    kinds = tuple(sorted(k.strip() for k in raw[len("mints:"):].split(",") if k.strip()))
    _require(len(kinds) > 0, path, "write_class", "mints: names no kinds")
    routes: dict[str, str] = {}
    for kind in kinds:
        _require(kind in contract_kinds, path, "write_class", f"unknown kind {kind!r}")
        admissible = kind_acts[kind]
        declared = routes_raw.get(kind)
        if declared is not None:
            _require(declared in admissible, path, "write.routes",
                     f"route {declared!r} not admissible for {kind!r}")
            routes[kind] = declared
        else:
            _require(len(admissible) == 1, path, "write.routes",
                     f"kind {kind!r} is route-ambiguous; declare its route")
            routes[kind] = next(iter(admissible))
    stray = set(routes_raw) - set(kinds)
    _require(not stray, path, "write.routes", f"routes for undeclared kinds {sorted(stray)}")
    return WriteClass("mints", kinds, routes)


def load_declaration(dir_path: Path, *, kind_acts: Mapping[str, frozenset[str]],
                     contract_kinds: frozenset[str]) -> Declaration:
    path = dir_path / "command.toml"
    _require(path.is_file(), path, "command.toml", "missing")
    _require((dir_path / "prompt.md").is_file(), dir_path / "prompt.md", "prompt.md", "missing")
    entries = {p.name for p in dir_path.iterdir()}
    _require(entries == {"command.toml", "prompt.md"}, path, "directory",
             f"holds exactly command.toml and prompt.md; found {sorted(entries)}")
    try:
        raw = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as e:
        raise DeclarationError(path, "command.toml", f"not valid TOML: {e}")
    version = raw.get("schema_version")
    _require(type(version) is int and version == SCHEMA_VERSION, path, "schema_version",
             f"must be the integer {SCHEMA_VERSION}")
    name = raw.get("name")
    _require(isinstance(name, str) and bool(NAME_RE.fullmatch(name or "")), path, "name", "bad grammar")
    _require(len(name.encode()) <= MAX_NAME_BYTES, path, "name", "over 32 bytes")
    _require(name not in RESERVED_COMMANDS, path, "name", "reserved name")
    _require(dir_path.name == name, path, "name", f"directory {dir_path.name!r} != name {name!r}")
    purpose = raw.get("purpose")
    _require(type(purpose) is str and purpose and "\n" not in purpose,
             path, "purpose", "must be one non-empty line")
    budget = raw.get("output_budget")
    _require(type(budget) is int and budget > 0, path, "output_budget",
             "must be a positive integer (not a bool)")
    from science.cursor import MIN_OUTPUT_BUDGET
    _require(budget >= MIN_OUTPUT_BUDGET, path, "output_budget",
             f"below MIN_OUTPUT_BUDGET ({MIN_OUTPUT_BUDGET})")
    write_raw = raw.get("write_class")
    _require(type(write_raw) is str, path, "write_class", "missing or not a string")
    write_tbl = raw.get("write", {})
    _require(type(write_tbl) is dict, path, "write", "must be a table")
    _require(set(write_tbl) <= {"routes"}, path, "write",
             f"unknown keys {sorted(set(write_tbl) - {'routes'})}")
    routes_raw = write_tbl.get("routes", {})
    _require(type(routes_raw) is dict
             and all(type(k) is str and type(v) is str for k, v in routes_raw.items()),
             path, "write.routes", "must be a table of kind = \"route\" strings")
    write_class = _parse_write_class(write_raw, routes_raw, path, kind_acts, contract_kinds)
    reads_tbl = raw.get("reads", {})
    _require(type(reads_tbl) is dict, path, "reads", "must be a table")
    _require(set(reads_tbl) <= {"families"}, path, "reads",
             f"unknown keys {sorted(set(reads_tbl) - {'families'})}")
    families_raw = reads_tbl.get("families", [])
    _require(type(families_raw) is list, path, "reads.families",
             "must be a list — a string would be read as characters")
    reads = tuple(families_raw)
    _require(all(type(r) is str and r for r in reads), path, "reads.families",
             "non-empty strings only")
    inputs_tbl = raw.get("inputs", {})
    _require(type(inputs_tbl) is dict, path, "inputs", "must be a table")
    inputs = _parse_inputs(inputs_tbl, path)
    known_top = {"schema_version", "name", "purpose", "write_class", "write",
                 "output_budget", "inputs", "reads"}
    extra = set(raw) - known_top
    _require(not extra, path, "command.toml", f"unknown keys {sorted(extra)}")
    return Declaration(name, purpose, write_class, budget, inputs, reads, dir_path)


def load_command_tree(root: Path, *, kind_acts, contract_kinds) -> tuple[Declaration, ...]:
    decls = []
    for d in sorted(p for p in root.iterdir() if p.is_dir()):
        decls.append(load_declaration(d, kind_acts=kind_acts, contract_kinds=contract_kinds))
    names = [d.name for d in decls]
    if len(set(names)) != len(names):
        raise DeclarationError(root, "tree", "duplicate command names")
    return tuple(decls)
