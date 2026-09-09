# Command Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `science` command framework — declaration schema, budgeted renderer, dispatcher, CLI, MCP server, Claude Code adapter generator, and the shipped `status` command — against today's `beliefs` kernel reads.

**Architecture:** Commands are the tools: each is a TOML declaration + a deterministic handler + a prompt, and CLI/MCP expose handlers 1:1 through one dispatcher and one renderer. Writes flow only through the `beliefs` writer session (built in the beliefs repo); reads run sessionless. Tasks 1–11 are read-path complete and unblocked; Tasks 12–13 consume the beliefs-side session/permit API and are gated on that repo's work.

**Tech Stack:** Python ≥ the floor in beliefs' `pyproject.toml` (match it exactly), stdlib only for the CLI (`argparse`, `tomllib`), hand-rolled JSON-RPC over stdio for MCP, `pytest` for tests.

**Spec:** `docs/specs/2026-08-31-command-framework-design.md` (this repo). The beliefs-side contract is that spec's §§4–5, implemented in the beliefs repository under its tasks `beliefs-96a24a` (permits) and the writer-session task created alongside this plan.

## Global Constraints

- Package: distribution `verifiably-science`, import name `science`, console script `science`.
- CLI has zero third-party dependencies; `pytest` is a dev dependency only.
- Command name grammar `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`, max 32 bytes; module = name with `-`→`_`. Input name grammar is snake_case (`^[a-z][a-z0-9]*(_[a-z0-9]+)*$`, max 32 bytes) so inputs bind as Python keyword parameters; CLI flags map `_`→`-`.
- Reserved command names: `continue`, `serve`, `mcp`, `adapters`, `build`. Reserved input names: `cursor`, `invocation_id`, `view`, `session`, `config`.
- Input types (closed): `string`, `int`, `bool`, `enum`, `list-of-string`.
- `invocation_id` grammar `^[A-Za-z0-9_-]{1,64}$`; minted ids and session ids are 32 lowercase hex.
- All digests are SHA-256, 64 lowercase hex.
- Refusal codes (closed): `unknown-command`, `invalid-input`, `permit-exceeded`, `outcome-unknown`, `unknown-cursor`, `stale-cursor`, `input-mismatch`, `kernel-refused`.
- Exit codes: 0 success, 1 internal error, 2 invalid invocation (argparse default), 3 refused.
- Every check is N2-shaped: the plan's tests must fail before their implementation exists (run them and watch them fail).
- Generated trees (`adapters/claude-code/`) are committed and never hand-edited.
- Conventional commits; no AI-attribution trailers.
- No absolute machine paths in code, docs, or generated trees.

**beliefs prerequisites for Tasks 12–13** (implemented in the beliefs repo, exact API in each task's Consumes block): `beliefs.permit` (`RequiredCapabilities`, `PermitExceeded`, `KIND_ACTS`) and `beliefs.session` (`open_attended_session`, `WriterSession.scoped/claim_invocation/close_invocation/invocation_acts`). Do not stub or mock these; the tasks stay blocked until they exist.

## Final-review contract (2026-09-01)

These corrections are authoritative over earlier illustrative code excerpts in
the task steps below:

- **Tasks 1–2:** source directories and files are real, regular, contained
  sources (never symlinks or special files); non-enum `choices` is forbidden by
  key presence; canonical input keys are exact strings before set/sort work.
  The single-root loader has no duplicate-command guard—a future multi-root
  loader owns collision validation if one is added.
- **Task 7:** a direct invocation resolves its command before validating the
  input mapping, so an unknown command deterministically wins over malformed
  inputs.
- **Task 8:** until Task 12 imports beliefs capabilities, `production_tree()`
  rejects every non-`read-only` declaration. Generic injected trees retain all
  four write classes.
- **Task 9:** protocol options are scoped to consumers: commands take config,
  invocation id, and cursor; `mcp serve` takes config only; build verbs take
  none. A command writes rendered text only to stdout and exactly one compact,
  key-sorted JSON stderr line: success has `invocation_id`; refusal has the
  bound id and full `{code,message,data}` envelope. Internal errors are generic.
  Task 9 does not register `science serve`.
- **Task 10:** `science build` and `science adapters build` share one preflight
  that validates handlers, collisions, source kind/containment, and pre-reads
  every command TOML, prompt, preamble, and authored-skill byte before adapter
  output mutation.
- **Task 11:** the pinned MCP 2026-07-28 primary schema governs. Discovery and
  tool listing implement `CacheableResult`; notifications receive no response;
  a supplied list cursor is validated (and refused because this complete list
  issues none); standard `inputResponses`/`requestState` fields are type-checked
  and refused as unsolicited because science never returns `input_required`;
  response structures are fresh. Stdio uses strict UTF-8 binary framing capped
  by `MAX_REQUEST_BYTES = 1_048_576`, draining an oversized line before serving
  the next request; malformed syntax, invalid UTF-8, and decoder recursion are
  parse failures that likewise leave the following frame serviceable.
- **Tasks 12–13 stay todo and beliefs-gated.** Task 12 replaces the temporary
  production write gate only when real capabilities land. Task 13 owns
  `science serve` parser registration and must preserve Task 9's stdout/stderr
  JSON wire when routing writes through the service.

---

### Task 1: Package scaffold and declaration schema

**Files:**
- Create: `python/pyproject.toml`
- Create: `python/src/science/__init__.py`
- Create: `python/src/science/schema.py`
- Create: `python/src/science/commands/__init__.py`
- Test: `python/tests/test_schema.py`

**Interfaces:**
- Consumes: nothing (kind/route validation data is injected, so this task has no beliefs dependency).
- Produces: `Declaration(name, purpose, write_class: WriteClass, output_budget: int, inputs: tuple[InputSpec, ...], reads: tuple[str, ...], directory: Path)`; `InputSpec(name, type, required, doc, default, choices)`; `WriteClass(kind: str, kinds: tuple[str, ...], routes: Mapping[str, str])` where `kind` is one of `read-only|coordination|mints|publishes`; `DeclarationError(path, field, reason)`; `load_declaration(dir_path, *, kind_acts, contract_kinds) -> Declaration`; `load_command_tree(root, *, kind_acts, contract_kinds) -> tuple[Declaration, ...]`; `handler_module(name) -> str`; `NAME_RE`, `RESERVED_COMMANDS`, `RESERVED_INPUTS`, `INPUT_TYPES` constants. The tree loader rejects command-directory, `command.toml`, `prompt.md`, and preamble symlinks/special files; its tests mutate the first three source forms directly. One root has no possible duplicate command entry, so no duplicate guard is specified.

- [ ] **Step 1: Write the package scaffold**

`python/pyproject.toml`:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "verifiably-science"
version = "0.1.0"
description = "The daily surface of Science: commands over the beliefs kernel."
requires-python = ">=3.11"
dependencies = []

[project.scripts]
science = "science.cli:main"

[dependency-groups]
dev = ["pytest>=8"]

[tool.hatch.build.targets.wheel]
packages = ["src/science"]
```

The floor matches beliefs' own `requires-python = ">=3.11"` — never a
higher one, since science imports beliefs into the same interpreter.
`python/src/science/__init__.py` and `python/src/science/commands/__init__.py` are empty files.

- [ ] **Step 2: Write the failing schema tests**

`python/tests/test_schema.py`:

```python
from pathlib import Path

import pytest

from science.schema import (
    Declaration, DeclarationError, handler_module,
    load_command_tree, load_declaration,
)

KIND_ACTS = {
    "note": frozenset({"corpus-write"}),
    "run": frozenset({"run", "corpus-write"}),
}
CONTRACT_KINDS = frozenset(KIND_ACTS)


def write_command(root: Path, name: str, toml: str, prompt: str = "Do it.") -> Path:
    d = root / name
    d.mkdir(parents=True)
    (d / "command.toml").write_text(toml)
    (d / "prompt.md").write_text(prompt)
    return d


GOOD = """
schema_version = 1
name = "status"
purpose = "Show the world."
write_class = "read-only"
output_budget = 16384

[inputs.corpus]
type = "string"
required = false
doc = "Restrict to one corpus."
"""


def test_good_declaration_loads(tmp_path):
    d = write_command(tmp_path, "status", GOOD)
    decl = load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert decl.name == "status"
    assert decl.write_class.kind == "read-only"
    assert decl.output_budget == 16384
    assert decl.inputs[0].name == "corpus" and not decl.inputs[0].required


@pytest.mark.parametrize("bad_name", ["Continue", "serve", "x" * 33, "9lives", "a_b", "a--b"])
def test_bad_names_refused(tmp_path, bad_name):
    toml = GOOD.replace('name = "status"', f'name = "{bad_name}"')
    d = write_command(tmp_path, "cmd", toml)
    (d / "command.toml").write_text(toml)
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


def test_newline_terminated_command_name_refuses_for_name_grammar(tmp_path):
    d = write_command(tmp_path, "status",
                      GOOD.replace('name = "status"', 'name = "status\\n"'))
    with pytest.raises(DeclarationError) as caught:
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert caught.value.reason == "bad grammar"


def test_reserved_input_refused(tmp_path):
    toml = GOOD + '\n[inputs.cursor]\ntype = "string"\nrequired = false\ndoc = "x"\n'
    d = write_command(tmp_path, "status", toml)
    with pytest.raises(DeclarationError) as e:
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert "cursor" in str(e.value)


def test_directory_name_mismatch_refused(tmp_path):
    d = write_command(tmp_path, "other", GOOD)
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


def test_enum_requires_choices_and_required_forbids_default(tmp_path):
    bad_enum = GOOD + '\n[inputs.mode]\ntype = "enum"\nrequired = true\ndoc = "x"\n'
    d = write_command(tmp_path, "status", bad_enum)
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    bad_default = GOOD + '\n[inputs.x]\ntype = "string"\nrequired = true\ndefault = "y"\ndoc = "x"\n'
    d2 = write_command(tmp_path, "status2", bad_default.replace('name = "status"', 'name = "status2"'))
    with pytest.raises(DeclarationError):
        load_declaration(d2, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


def test_non_enum_refuses_explicit_empty_choices(tmp_path):
    toml = GOOD.replace('doc = "Restrict to one corpus."',
                        'doc = "Restrict to one corpus."\nchoices = []')
    d = write_command(tmp_path, "status", toml)
    with pytest.raises(DeclarationError) as caught:
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert caught.value.field == "inputs.corpus.choices"


MINTS = """
schema_version = 1
name = "mint-run"
purpose = "Fixture."
write_class = "mints:run,note"
output_budget = 4096

[write.routes]
run = "run"
"""


def test_mints_routes_resolve(tmp_path):
    d = write_command(tmp_path, "mint-run", MINTS)
    decl = load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert decl.write_class.kinds == ("note", "run")
    # note is uniquely routed and omitted from the map; run is declared.
    assert decl.write_class.routes == {"note": "corpus-write", "run": "run"}


def test_ambiguous_kind_without_route_refused(tmp_path):
    toml = MINTS.replace("[write.routes]\nrun = \"run\"\n", "")
    d = write_command(tmp_path, "mint-run", toml)
    with pytest.raises(DeclarationError) as e:
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert "run" in str(e.value)


def test_route_key_outside_kinds_and_inadmissible_route_refused(tmp_path):
    stray = MINTS + 'dataset = "run"\n'
    d = write_command(tmp_path, "mint-run", stray)
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    wrong = MINTS.replace('run = "run"', 'run = "holdings"')
    d2 = write_command(tmp_path, "mint-run2", wrong.replace("mint-run", "mint-run2"))
    with pytest.raises(DeclarationError):
        load_declaration(d2, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


def test_unknown_kind_refused(tmp_path):
    toml = MINTS.replace("run,note", "widget").replace('[write.routes]\nrun = "run"\n', "")
    d = write_command(tmp_path, "mint-run", toml)
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


def test_tree_lists_all_commands_in_name_order(tmp_path):
    write_command(tmp_path, "status", GOOD)
    write_command(tmp_path, "mint-run", MINTS)
    decls = load_command_tree(tmp_path, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert [d.name for d in decls] == ["mint-run", "status"]


def test_handler_module_mapping():
    assert handler_module("mint-run") == "science.commands.mint_run"


def test_bool_never_passes_an_int_field(tmp_path):
    for bad in ('schema_version = true', 'output_budget = true'):
        field = bad.split(" ")[0]
        toml = GOOD.replace(f"{field} = " + ("1" if field == "schema_version" else "16384"), bad)
        d = write_command(tmp_path, "status", toml)
        with pytest.raises(DeclarationError):
            load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
        import shutil; shutil.rmtree(d)


def test_default_is_type_checked_at_build(tmp_path):
    bad_type = GOOD + '\n[inputs.n]\ntype = "int"\nrequired = false\ndefault = "three"\ndoc = "x"\n'
    d = write_command(tmp_path, "status", bad_type)
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    bad_enum = GOOD.replace('name = "status"', 'name = "st2"') + \
        '\n[inputs.m]\ntype = "enum"\nrequired = false\nchoices = ["a"]\ndefault = "z"\ndoc = "x"\n'
    d2 = write_command(tmp_path, "st2", bad_enum)
    with pytest.raises(DeclarationError):
        load_declaration(d2, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


def test_malformed_toml_is_a_declaration_error(tmp_path):
    d = write_command(tmp_path, "status", "this = is not [ toml")
    with pytest.raises(DeclarationError) as e:
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert "TOML" in str(e.value)


def test_hyphenated_input_name_refused(tmp_path):
    toml = GOOD + '\n[inputs.multi-word]\ntype = "string"\nrequired = false\ndoc = "x"\n'
    d = write_command(tmp_path, "status", toml)
    with pytest.raises(DeclarationError):  # cannot bind through **canonical
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


def test_multiline_purpose_refused(tmp_path):
    toml = GOOD.replace('purpose = "Show the world."', 'purpose = "Two\\nlines."')
    d = write_command(tmp_path, "status", toml)
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)


def test_stray_file_in_command_directory_refused(tmp_path):
    d = write_command(tmp_path, "status", GOOD)
    (d / "notes.txt").write_text("stray")
    with pytest.raises(DeclarationError) as e:
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert "notes.txt" in str(e.value)


BASE = """
schema_version = 1
name = "status"
purpose = "Show the world."
write_class = "read-only"
output_budget = 16384
"""


@pytest.mark.parametrize("mutation", [
    'inputs = "nope"',                        # inputs not a table
    '[write]\nextra = 1',                     # unknown write key
    'write = "x"',                            # write not a table
    '[write]\nroutes = "run"',                # routes not a table
    'reads = "families"',                     # reads not a table
    '[reads]\nfamilies = "registry"',         # families a string, not a list
    '[reads]\nextra = []',                    # unknown reads key
    '[inputs.m]\ntype = "enum"\nrequired = false\nchoices = "ab"\ndoc = "x"',  # choices a string
])
def test_malformed_tables_are_declaration_errors(tmp_path, mutation):
    """Every malformed table refuses as a DeclarationError — never silently
    normalized, never an uncaught TypeError/AttributeError. BASE has no
    inputs table, so each mutation exercises its own check rather than a
    TOML duplicate-key error."""
    d = write_command(tmp_path, "status", BASE + mutation + "\n")
    with pytest.raises(DeclarationError):
        load_declaration(d, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
```

Budget-floor refusal is added in Task 4 when `MIN_OUTPUT_BUDGET` exists; leave it out here.

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd python && uv run --group dev pytest tests/test_schema.py -q` (or `pip install -e . && pytest` if uv is absent; use one consistently from here on).
Expected: FAIL — `ModuleNotFoundError: No module named 'science.schema'`.

- [ ] **Step 4: Implement `schema.py`**

```python
"""Command declarations: the schema every command must fit (spec §3)."""
from __future__ import annotations

import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

NAME_RE = re.compile(r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$")
# Inputs are snake_case: they must bind as Python keyword parameters through
# `**canonical`, which a hyphenated name cannot. The CLI maps `_` -> `-` for
# its flags; the wire schemas carry the snake_case name verbatim.
INPUT_NAME_RE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")
MAX_NAME_BYTES = 32
RESERVED_COMMANDS = frozenset({"continue", "serve", "mcp", "adapters", "build"})
RESERVED_INPUTS = frozenset({"cursor", "invocation_id", "view", "session", "config"})
INPUT_TYPES = frozenset({"string", "int", "bool", "enum", "list-of-string"})
WRITE_CLASS_KINDS = frozenset({"read-only", "coordination", "mints", "publishes"})
SCHEMA_VERSION = 1

# Exact-type checks for TOML-supplied values: `bool` is an `int` in Python,
# so `type(...) is` guards every integer field against `true`.
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
        _require(bool(INPUT_NAME_RE.match(name)) and len(name.encode()) <= MAX_NAME_BYTES,
                 path, f"inputs.{name}", "input names are snake_case, max 32 bytes")
        typ = spec.get("type")
        _require(typ in INPUT_TYPES, path, f"inputs.{name}.type", f"must be one of {sorted(INPUT_TYPES)}")
        required = spec.get("required")
        _require(isinstance(required, bool), path, f"inputs.{name}.required", "must be a bool")
        doc = spec.get("doc")
        _require(type(doc) is str and doc, path, f"inputs.{name}.doc", "must be a non-empty string")
        raw_choices = spec.get("choices", [])
        _require(type(raw_choices) is list, path, f"inputs.{name}.choices",
                 "must be a list — a string would be read as characters")
        choices = tuple(raw_choices)
        if typ == "enum":
            _require(len(choices) > 0 and len(set(choices)) == len(choices)
                     and all(type(c) is str for c in choices),
                     path, f"inputs.{name}.choices", "enum requires unique string choices")
        else:
            _require("choices" not in spec, path, f"inputs.{name}.choices", "only enum takes choices")
        default = spec.get("default")
        if required:
            _require(default is None, path, f"inputs.{name}.default", "required input forbids default")
        if default is not None:  # build-time type check; bool is not an int here
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
    _require(isinstance(name, str) and bool(NAME_RE.match(name or "")), path, "name", "bad grammar")
    _require(len(name.encode()) <= MAX_NAME_BYTES, path, "name", "over 32 bytes")
    _require(name not in RESERVED_COMMANDS, path, "name", "reserved name")
    _require(dir_path.name == name, path, "name", f"directory {dir_path.name!r} != name {name!r}")
    purpose = raw.get("purpose")
    _require(type(purpose) is str and purpose and "\n" not in purpose,
             path, "purpose", "must be one non-empty line")
    budget = raw.get("output_budget")
    _require(type(budget) is int and budget > 0, path, "output_budget",
             "must be a positive integer (not a bool)")
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
    return tuple(decls)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd python && uv run --group dev pytest tests/test_schema.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add python/pyproject.toml python/src/science python/tests/test_schema.py
git commit -m "feat(schema): declaration schema with write classes and route selection"
```

### Task 2: Canonical inputs and the refusal envelope

**Files:**
- Create: `python/src/science/canonical.py`
- Create: `python/src/science/refusal.py`
- Test: `python/tests/test_canonical.py`

**Interfaces:**
- Consumes: `Declaration`, `InputSpec` from Task 1.
- Produces: `canonicalize(decl, provided: Mapping) -> dict` (validates, applies defaults, drops absent optionals; raises `Refused` with code `invalid-input`); `input_digest(canonical: Mapping) -> str` (64-hex SHA-256 of canonical JSON); `Refusal(code, message, data)` frozen dataclass; `Refused(Exception)` with `.refusal` and `.invocation_id: str | None` (set by the write dispatcher so a refusal never loses the minted id); `envelope(refusal) -> dict` — the one wire form `{code, message, data}` every transport uses; `CODES` frozenset; `INVOCATION_ID_RE`; `mint_token() -> str` (32 lowercase hex).

- [ ] **Step 1: Write the failing tests**

`python/tests/test_canonical.py`:

```python
import re

import pytest

from science.canonical import canonicalize, input_digest
from science.refusal import CODES, INVOCATION_ID_RE, Refusal, Refused, mint_token
from science.schema import Declaration, InputSpec, WriteClass
from pathlib import Path


def decl(*inputs: InputSpec) -> Declaration:
    return Declaration("t", "p", WriteClass("read-only"), 4096, tuple(inputs), (), Path("."))


def test_defaults_applied_and_absent_dropped():
    d = decl(InputSpec("a", "string", False, "d", default="x"),
             InputSpec("b", "int", False, "d"))
    assert canonicalize(d, {}) == {"a": "x"}


def test_unknown_and_wrong_type_refused():
    d = decl(InputSpec("a", "int", True, "d"))
    with pytest.raises(Refused) as e:
        canonicalize(d, {"a": 1, "zz": 2})
    assert e.value.refusal.code == "invalid-input"
    with pytest.raises(Refused):
        canonicalize(d, {"a": "not-int"})
    with pytest.raises(Refused):  # missing required
        canonicalize(d, {})
    with pytest.raises(Refused):  # bool is not an int
        canonicalize(d, {"a": True})


def test_non_exact_string_input_names_refuse_before_key_operations():
    class StringSubclass(str):
        pass
    d = decl(InputSpec("a", "int", True, "d"))
    for provided in ({1: "x", "stray": "y"}, {StringSubclass("a"): 1}):
        with pytest.raises(Refused) as caught:
            canonicalize(d, provided)
        assert caught.value.refusal.code == "invalid-input"


def test_explicit_null_is_refused_not_absent():
    d = decl(InputSpec("a", "string", False, "d", default="x"))
    with pytest.raises(Refused) as e:
        canonicalize(d, {"a": None})  # must NOT silently become the default
    assert e.value.refusal.code == "invalid-input"


def test_enum_and_list_validation():
    d = decl(InputSpec("m", "enum", True, "d", choices=("x", "y")),
             InputSpec("l", "list-of-string", False, "d"))
    assert canonicalize(d, {"m": "x", "l": ["a", "b"]}) == {"l": ["a", "b"], "m": "x"}
    with pytest.raises(Refused):
        canonicalize(d, {"m": "z"})
    with pytest.raises(Refused):
        canonicalize(d, {"m": "x", "l": [1]})


def test_digest_stable_and_order_free():
    d = decl(InputSpec("a", "string", True, "d"), InputSpec("b", "int", False, "d"))
    one = input_digest(canonicalize(d, {"a": "v", "b": 2}))
    two = input_digest(canonicalize(d, {"b": 2, "a": "v"}))
    assert one == two and re.fullmatch(r"[0-9a-f]{64}", one)


def test_refusal_shapes():
    assert "kernel-refused" in CODES and len(CODES) == 8
    r = Refusal("invalid-input", "bad", {"field": "a"})
    assert Refused(r).refusal is r
    assert INVOCATION_ID_RE.fullmatch("A-z_09")
    assert not INVOCATION_ID_RE.fullmatch("x" * 65) and not INVOCATION_ID_RE.fullmatch("a b")
    assert re.fullmatch(r"[0-9a-f]{32}", mint_token())
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && uv run --group dev pytest tests/test_canonical.py -q`
Expected: FAIL — no module `science.canonical`.

- [ ] **Step 3: Implement**

`python/src/science/refusal.py`:

```python
"""The structured refusal envelope (spec §6.3) and protocol identifier bounds."""
from __future__ import annotations

import re
import secrets
from collections.abc import Mapping
from dataclasses import dataclass, field

CODES = frozenset({
    "unknown-command", "invalid-input", "permit-exceeded", "outcome-unknown",
    "unknown-cursor", "stale-cursor", "input-mismatch", "kernel-refused",
})
INVOCATION_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


@dataclass(frozen=True)
class Refusal:
    code: str
    message: str
    data: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.code not in CODES:
            raise ValueError(f"unknown refusal code {self.code!r}")


class Refused(Exception):
    """Carries the structured envelope, and — when a write dispatcher had
    already minted or accepted an invocation id — that id, so no transport
    loses it on refusal and callers can still dedup a retry."""

    def __init__(self, refusal: Refusal, invocation_id: str | None = None) -> None:
        self.refusal = refusal
        self.invocation_id = invocation_id
        super().__init__(f"{refusal.code}: {refusal.message}")


def envelope(refusal: Refusal) -> dict:
    """The one wire form of a refusal: exactly the spec §6.3 triple."""
    return {"code": refusal.code, "message": refusal.message, "data": dict(refusal.data)}


def mint_token() -> str:
    return secrets.token_hex(16)
```

`python/src/science/canonical.py`:

```python
"""Input canonicalization: the one form digests and schemas are computed over."""
from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping

from science.refusal import Refusal, Refused
from science.schema import Declaration

_CHECKS = {
    "string": lambda v: isinstance(v, str),
    "int": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "bool": lambda v: isinstance(v, bool),
    "enum": lambda v: isinstance(v, str),
    "list-of-string": lambda v: isinstance(v, list) and all(isinstance(x, str) for x in v),
}


def _refuse(message: str, **data: object) -> None:
    raise Refused(Refusal("invalid-input", message, data))


def canonicalize(decl: Declaration, provided: Mapping[str, object]) -> dict[str, object]:
    if any(type(name) is not str for name in provided):
        _refuse("input names must be strings", command=decl.name)
    known = {i.name: i for i in decl.inputs}
    unknown = set(provided) - set(known)
    if unknown:
        _refuse(f"unknown inputs {sorted(unknown)}", command=decl.name)
    out: dict[str, object] = {}
    for spec in decl.inputs:
        if spec.name in provided:
            value = provided[spec.name]
            if value is None:  # explicit null is a caller error, never "absent"
                _refuse(f"input {spec.name!r} is null; omit it instead", field=spec.name)
        else:
            value = spec.default
        if value is None:
            if spec.required:
                _refuse(f"missing required input {spec.name!r}", field=spec.name)
            continue
        if not _CHECKS[spec.type](value):
            _refuse(f"input {spec.name!r} is not a {spec.type}", field=spec.name)
        if spec.type == "enum" and value not in spec.choices:
            _refuse(f"input {spec.name!r} must be one of {list(spec.choices)}", field=spec.name)
        out[spec.name] = value
    return dict(sorted(out.items()))


def input_digest(canonical: Mapping[str, object]) -> str:
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd python && uv run --group dev pytest tests/test_canonical.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/canonical.py python/src/science/refusal.py python/tests/test_canonical.py
git commit -m "feat(protocol): canonical inputs, digests, and the refusal envelope"
```

### Task 3: Report model

**Files:**
- Create: `python/src/science/report.py`
- Test: `python/tests/test_report.py`

**Interfaces:**
- Consumes: nothing (the factory takes any object with `uid`, `id`, `kind`, `title` attributes — the `nodes` `Node` shape — so this task needs no beliefs import).
- Produces: frozen block dataclasses `Heading(text)`, `KeyVals(title, pairs: tuple[tuple[str, str], ...])`, `RecordBlock(uid, record_id, kind, title)`, `Finding(text)`, `Text(text)`; the factory `record_block(node) -> RecordBlock` — **the only intended way to build one**: every field is derived from the kernel record, so a handler cannot author free text into a record block (that channel is the audit echo, spec §7.4); type alias `Block`; `Report = tuple[Block, ...]`; `serialize_block(block) -> str` (deterministic, newline-terminated).

- [ ] **Step 1: Write the failing test**

`python/tests/test_report.py`:

```python
from types import SimpleNamespace

from science.report import (
    Finding, Heading, KeyVals, RecordBlock, Text, record_block, serialize_block,
)


def test_record_block_is_derived_from_the_record():
    node = SimpleNamespace(uid="u" * 32, id="proposition:x", kind="proposition", title="claim")
    block = record_block(node)
    assert block == RecordBlock("u" * 32, "proposition:x", "proposition", "claim")


def test_serialization_is_deterministic_and_distinct():
    blocks = (
        Heading("World"),
        KeyVals("epoch", (("packaging", "abc"), ("coverage", "2"))),
        RecordBlock("u" * 32, "proposition:x", "proposition", "claim"),
        Finding("chain head moved"),
        Text("plain"),
    )
    outs = [serialize_block(b) for b in blocks]
    assert outs == [serialize_block(b) for b in blocks]  # stable
    assert all(o.endswith("\n") for o in outs)
    assert len(set(outs)) == len(outs)
    assert "## World" in outs[0]
    assert "packaging: abc" in outs[1]
    assert "[proposition] proposition:x" in outs[2] and "u" * 32 in outs[2]
    assert outs[3].startswith("! ")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd python && uv run --group dev pytest tests/test_report.py -q`
Expected: FAIL — no module `science.report`.

- [ ] **Step 3: Implement `report.py`**

```python
"""Typed report blocks: what handlers return instead of prose (spec §7.1)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Heading:
    text: str


@dataclass(frozen=True)
class KeyVals:
    title: str
    pairs: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class RecordBlock:
    uid: str
    record_id: str
    kind: str
    title: str


def record_block(node) -> RecordBlock:
    """Derive a record block from a kernel record; handlers never author one."""
    return RecordBlock(node.uid, node.id, node.kind, node.title)


@dataclass(frozen=True)
class Finding:
    text: str


@dataclass(frozen=True)
class Text:
    text: str


Block = Heading | KeyVals | RecordBlock | Finding | Text
Report = tuple[Block, ...]


def serialize_block(block: Block) -> str:
    match block:
        case Heading(text):
            return f"## {text}\n"
        case KeyVals(title, pairs):
            lines = [f"{title}:"] + [f"  {k}: {v}" for k, v in pairs]
            return "\n".join(lines) + "\n"
        case RecordBlock(uid, record_id, kind, title):
            return f"[{kind}] {record_id} uid={uid}\n{title}\n"
        case Finding(text):
            return f"! {text}\n"
        case Text(text):
            return text + "\n"
    raise TypeError(f"not a block: {block!r}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd python && uv run --group dev pytest tests/test_report.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/report.py python/tests/test_report.py
git commit -m "feat(report): typed report blocks with deterministic serialization"
```

### Task 4: Cursor encoding and the size constants

**Files:**
- Create: `python/src/science/cursor.py`
- Modify: `python/src/science/schema.py` (budget-floor refusal)
- Test: `python/tests/test_cursor.py`

**Interfaces:**
- Consumes: `INVOCATION_ID_RE`, `Refusal`, `Refused` (Task 2); `NAME_RE`, `MAX_NAME_BYTES` (Task 1).
- Produces: `ReadCursor(command, input_digest, report_digest, block, offset)`; `WriteCursor(session_id, invocation_id, report_digest, block, offset)`; `encode(cursor) -> str`; `decode(token) -> ReadCursor | WriteCursor` (raises `Refused` with `unknown-cursor` on any parse failure); `MAX_CURSOR_BYTES: int`; `MIN_OUTPUT_BUDGET: int`; `MARKER_TEMPLATE = "\n… truncated at {budget} bytes; continue with cursor {cursor}\n"`.

- [ ] **Step 1: Write the failing tests**

`python/tests/test_cursor.py`:

```python
import pytest

from science.cursor import (
    MAX_CURSOR_BYTES, MIN_OUTPUT_BUDGET, ReadCursor, WriteCursor, decode, encode,
)
from science.refusal import Refused

U64_MAX = 2**64 - 1


def test_round_trip_both_forms():
    r = ReadCursor("status", "a" * 64, "b" * 64, 3, 17)
    w = WriteCursor("c" * 32, "x" * 64, "d" * 64, 0, 0)
    assert decode(encode(r)) == r
    assert decode(encode(w)) == w


def test_maximal_cursor_fits_published_bound():
    r = ReadCursor("x" * 32, "f" * 64, "f" * 64, U64_MAX, U64_MAX)
    w = WriteCursor("f" * 32, "z" * 64, "f" * 64, U64_MAX, U64_MAX)
    assert len(encode(r).encode()) <= MAX_CURSOR_BYTES
    assert len(encode(w).encode()) <= MAX_CURSOR_BYTES
    assert MIN_OUTPUT_BUDGET > MAX_CURSOR_BYTES


@pytest.mark.parametrize("junk", ["", "scur1.", "nope", "scur1.!!!!", "scur2.AAAA",
                                  "scur1." + "A" * 4096])  # last: over the size cap
def test_garbage_refuses_unknown_cursor(junk):
    with pytest.raises(Refused) as e:
        decode(junk)
    assert e.value.refusal.code == "unknown-cursor"


def _hand_encode(raw: dict) -> str:
    import base64, json
    return "scur1." + base64.urlsafe_b64encode(
        json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()).decode().rstrip("=")


def test_field_bounds_enforced_on_decode():
    # An over-long command:
    over_long = {"f": "r", "c": "s" * 33, "i": "a" * 64, "r": "b" * 64, "b": 1, "o": 1}
    with pytest.raises(Refused):
        decode(_hand_encode(over_long))


def test_boolean_position_refused():
    # JSON true is a Python bool — an int subclass that must not pass as u64.
    forged = {"f": "r", "c": "status", "i": "a" * 64, "r": "b" * 64, "b": True, "o": 0}
    with pytest.raises(Refused) as e:
        decode(_hand_encode(forged))
    assert e.value.refusal.code == "unknown-cursor"


def test_budget_floor_refused_in_schema(tmp_path):
    from science.schema import DeclarationError, load_declaration
    toml = f"""
schema_version = 1
name = "tiny"
purpose = "p"
write_class = "read-only"
output_budget = {MIN_OUTPUT_BUDGET - 1}
"""
    d = tmp_path / "tiny"
    d.mkdir()
    (d / "command.toml").write_text(toml)
    (d / "prompt.md").write_text("x")
    with pytest.raises(DeclarationError) as e:
        load_declaration(d, kind_acts={}, contract_kinds=frozenset())
    assert "MIN_OUTPUT_BUDGET" in str(e.value)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && uv run --group dev pytest tests/test_cursor.py -q`
Expected: FAIL — no module `science.cursor`.

- [ ] **Step 3: Implement `cursor.py` and the schema floor**

`python/src/science/cursor.py`:

```python
"""Bounded, versioned cursor encoding (spec §7.3, §3.2 constants)."""
from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass

from science.refusal import INVOCATION_ID_RE, Refusal, Refused
from science.schema import MAX_NAME_BYTES, NAME_RE

_PREFIX = "scur1."
_HEX32 = re.compile(r"^[0-9a-f]{32}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_U64_MAX = 2**64 - 1


@dataclass(frozen=True)
class ReadCursor:
    command: str
    input_digest: str
    report_digest: str
    block: int
    offset: int


@dataclass(frozen=True)
class WriteCursor:
    session_id: str
    invocation_id: str
    report_digest: str
    block: int
    offset: int


def _refuse(detail: str) -> None:
    raise Refused(Refusal("unknown-cursor", f"cursor does not parse: {detail}"))


def _check_u64(value: object, name: str) -> int:
    # `type(...) is int`: a JSON boolean is a Python bool, which is an int
    # subclass and must not pass as a position.
    if type(value) is not int or not (0 <= value <= _U64_MAX):
        _refuse(f"{name} out of range")
    return value


def encode(cursor: ReadCursor | WriteCursor) -> str:
    if isinstance(cursor, ReadCursor):
        raw = {"f": "r", "c": cursor.command, "i": cursor.input_digest,
               "r": cursor.report_digest, "b": cursor.block, "o": cursor.offset}
    else:
        raw = {"f": "w", "s": cursor.session_id, "n": cursor.invocation_id,
               "r": cursor.report_digest, "b": cursor.block, "o": cursor.offset}
    payload = json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()
    return _PREFIX + base64.urlsafe_b64encode(payload).decode().rstrip("=")


def decode(token: str) -> ReadCursor | WriteCursor:
    if len(token.encode()) > MAX_CURSOR_BYTES:  # cap before any parsing
        _refuse("over the size bound")
    if not token.startswith(_PREFIX):
        _refuse("bad prefix")
    body = token[len(_PREFIX):]
    try:
        payload = base64.urlsafe_b64decode(body + "=" * (-len(body) % 4))
        raw = json.loads(payload)
    except Exception:
        _refuse("bad encoding")
    if not isinstance(raw, dict):
        _refuse("not an object")
    form = raw.get("f")
    if form == "r":
        command = raw.get("c", "")
        if not (isinstance(command, str) and NAME_RE.match(command)
                and len(command.encode()) <= MAX_NAME_BYTES):
            _refuse("bad command")
        for key in ("i", "r"):
            if not (isinstance(raw.get(key), str) and _HEX64.match(raw[key])):
                _refuse(f"bad digest {key}")
        return ReadCursor(command, raw["i"], raw["r"],
                          _check_u64(raw.get("b"), "block"), _check_u64(raw.get("o"), "offset"))
    if form == "w":
        if not (isinstance(raw.get("s"), str) and _HEX32.match(raw["s"])):
            _refuse("bad session id")
        if not (isinstance(raw.get("n"), str) and INVOCATION_ID_RE.match(raw["n"])):
            _refuse("bad invocation id")
        if not (isinstance(raw.get("r"), str) and _HEX64.match(raw["r"])):
            _refuse("bad digest")
        return WriteCursor(raw["s"], raw["n"], raw["r"],
                           _check_u64(raw.get("b"), "block"), _check_u64(raw.get("o"), "offset"))
    _refuse("unknown form")
    raise AssertionError  # unreachable


def _max_cursor_bytes() -> int:
    read_max = ReadCursor("x" * MAX_NAME_BYTES, "f" * 64, "f" * 64, _U64_MAX, _U64_MAX)
    write_max = WriteCursor("f" * 32, "z" * 64, "f" * 64, _U64_MAX, _U64_MAX)
    return max(len(encode(read_max).encode()), len(encode(write_max).encode()))


MAX_CURSOR_BYTES = _max_cursor_bytes()
MARKER_TEMPLATE = "\n… truncated at {budget} bytes; continue with cursor {cursor}\n"
_MARKER_FIXED = len(MARKER_TEMPLATE.format(budget=9 * 10**19, cursor="").encode())
MIN_OUTPUT_BUDGET = _MARKER_FIXED + MAX_CURSOR_BYTES + 4
```

In `schema.py`, add the floor check inside `load_declaration` right after the budget check, importing lazily to avoid a cycle (`cursor` imports `schema`):

```python
    from science.cursor import MIN_OUTPUT_BUDGET
    _require(budget >= MIN_OUTPUT_BUDGET, path, "output_budget",
             f"below MIN_OUTPUT_BUDGET ({MIN_OUTPUT_BUDGET})")
```

- [ ] **Step 4: Run the full suite to verify it passes**

Run: `cd python && uv run --group dev pytest -q`
Expected: PASS (earlier schema tests still pass — their budgets exceed the floor; if any fixture budget in `test_schema.py` is below the computed floor, raise that fixture's number, not the floor).

- [ ] **Step 5: Commit**

```bash
git add python/src/science/cursor.py python/src/science/schema.py python/tests/test_cursor.py
git commit -m "feat(cursor): bounded cursor encoding with computed size constants"
```

### Task 5: Budgeted renderer

**Files:**
- Create: `python/src/science/render.py`
- Test: `python/tests/test_render.py`

**Interfaces:**
- Consumes: `Report`, `serialize_block` (Task 3); `MARKER_TEMPLATE`, `MIN_OUTPUT_BUDGET`, `encode` (Task 4).
- Produces: `RenderedPage(text: str, next_position: tuple[int, int] | None, report_digest: str)`; `render_page(report, *, budget: int, position: tuple[int, int] = (0, 0), cursor_for: Callable[[tuple[int, int], str], str]) -> RenderedPage`; `report_digest(report) -> str`; `AuditViolation(Exception)`; `audit_write_report(report, minted: frozenset[tuple[str, str]]) -> None` — `minted` is the ledger's `(uid, id)` identity pairs (spec §5.2), and a record block passes only when **both** identities match a minted pair.

- [ ] **Step 1: Write the failing tests**

`python/tests/test_render.py`:

```python
import pytest

from science.cursor import MIN_OUTPUT_BUDGET
from science.render import (
    AuditViolation, audit_write_report, render_page, report_digest,
)
from science.report import Finding, Heading, KeyVals, RecordBlock, Text


def cursor_for(position, digest):
    return f"CUR-{position[0]}-{position[1]}"


def paginate(report, budget):
    pages, pos = [], (0, 0)
    while pos is not None:
        page = render_page(report, budget=budget, position=pos, cursor_for=cursor_for)
        pages.append(page)
        pos = page.next_position
    return pages


def test_fits_in_one_page_untruncated():
    report = (Heading("a"), Text("b"))
    page = render_page(report, budget=MIN_OUTPUT_BUDGET, position=(0, 0), cursor_for=cursor_for)
    assert page.next_position is None and "truncated" not in page.text


def test_near_budget_fit_is_not_truncated():
    """A report inside the budget but inside the marker reserve too: still whole."""
    from science.render import render_full
    report = (Text("x" * (MIN_OUTPUT_BUDGET * 2)),)
    exact = len(render_full(report).encode())
    page = render_page(report, budget=exact, position=(0, 0), cursor_for=cursor_for)
    assert page.next_position is None and "truncated" not in page.text
    assert len(page.text.encode()) == exact


def test_budget_enforced_and_pages_cover_everything():
    report = tuple(Text(f"line {i} " + "x" * 40) for i in range(50))
    budget = MIN_OUTPUT_BUDGET
    pages = paginate(report, budget)
    assert len(pages) > 1
    assert all(len(p.text.encode()) <= budget for p in pages)
    joined = "".join(p.text.split("\n… truncated")[0] for p in pages)
    full = render_page(report, budget=10**9, position=(0, 0), cursor_for=cursor_for).text
    assert joined == full


def test_oversized_single_block_still_progresses():
    report = (Text("y" * (MIN_OUTPUT_BUDGET * 3)),)
    pages = paginate(report, MIN_OUTPUT_BUDGET)
    assert len(pages) >= 3  # split inside the block, at character boundaries


def test_multibyte_never_split():
    report = (Text("é" * MIN_OUTPUT_BUDGET),)
    for page in paginate(report, MIN_OUTPUT_BUDGET):
        page.text.encode()  # would raise if a char were split
        assert "�" not in page.text


def test_digest_stable():
    report = (Heading("a"), Finding("f"))
    assert report_digest(report) == report_digest((Heading("a"), Finding("f")))
    assert report_digest(report) != report_digest((Heading("a"),))


def test_write_audit_rules():
    minted = frozenset({("u" * 32, "note:n1")})
    audit_write_report((RecordBlock("u" * 32, "note:n1", "note", "t"),), minted)
    with pytest.raises(AuditViolation):  # foreign record id
        audit_write_report((RecordBlock("u" * 32, "note:other", "note", "t"),), minted)
    with pytest.raises(AuditViolation):  # right id, wrong uid — both must match
        audit_write_report((RecordBlock("v" * 32, "note:n1", "note", "t"),), minted)
    for block in (Heading("h"), KeyVals("k", ()), Finding("f"), Text("t")):
        with pytest.raises(AuditViolation):  # every non-record block kind
            audit_write_report((block,), minted)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && uv run --group dev pytest tests/test_render.py -q`
Expected: FAIL — no module `science.render`.

- [ ] **Step 3: Implement `render.py`**

```python
"""The one budgeted renderer (spec §7): budget, progress, audit."""
from __future__ import annotations

import hashlib
from collections.abc import Callable
from dataclasses import dataclass

from science.cursor import MARKER_TEMPLATE
from science.report import Block, RecordBlock, Report, serialize_block


class AuditViolation(Exception):
    pass


@dataclass(frozen=True)
class RenderedPage:
    text: str
    next_position: tuple[int, int] | None
    report_digest: str


def report_digest(report: Report) -> str:
    h = hashlib.sha256()
    for block in report:
        piece = serialize_block(block).encode()
        h.update(len(piece).to_bytes(8, "big"))
        h.update(piece)
    return h.hexdigest()


def audit_write_report(report: Report, minted: frozenset[tuple[str, str]]) -> None:
    for block in report:
        if not isinstance(block, RecordBlock):
            raise AuditViolation(f"write reports carry record blocks only, got {type(block).__name__}")
        if (block.uid, block.record_id) not in minted:
            raise AuditViolation(
                f"record ({block.uid!r}, {block.record_id!r}) was not minted by this invocation")


def _utf8_prefix(data: bytes, limit: int) -> bytes:
    """Longest prefix of at most `limit` bytes ending on a character boundary."""
    if len(data) <= limit:
        return data
    cut = limit
    while cut > 0 and (data[cut] & 0xC0) == 0x80:
        cut -= 1
    return data[:cut]


def render_page(report: Report, *, budget: int, position: tuple[int, int] = (0, 0),
                cursor_for: Callable[[tuple[int, int], str], str]) -> RenderedPage:
    digest = report_digest(report)
    block_index, offset = position
    # A report that fits the budget whole is emitted whole: the marker reserve
    # applies only when truncation is actually needed, so a near-budget fit is
    # never truncated for space the marker would not use.
    pieces = [serialize_block(b).encode() for b in report]
    remaining = ([pieces[block_index][offset:]] + pieces[block_index + 1:]
                 if block_index < len(pieces) else [])
    if sum(map(len, remaining)) <= budget:
        return RenderedPage(b"".join(remaining).decode(), None, digest)
    # Reserve worst-case marker space so the emitted page always fits the budget.
    probe = cursor_for((2**64 - 1, 2**64 - 1), digest)
    reserve = len(MARKER_TEMPLATE.format(budget=budget, cursor=probe).encode())
    room = budget - reserve
    out: list[bytes] = []
    i = block_index
    while i < len(report):
        piece = serialize_block(report[i]).encode()[offset:]
        offset = 0
        used = sum(map(len, out))
        if len(piece) <= room - used:
            out.append(piece)
            i += 1
            continue
        taken = _utf8_prefix(piece, max(room - used, 0))
        if not taken and not out:
            raise AuditViolation("budget below MIN_OUTPUT_BUDGET reached the renderer")
        if taken:
            out.append(taken)
            next_pos = (i, (len(serialize_block(report[i]).encode()) - len(piece)) + len(taken))
        else:
            next_pos = (i, len(serialize_block(report[i]).encode()) - len(piece))
        cursor = cursor_for(next_pos, digest)
        marker = MARKER_TEMPLATE.format(budget=budget, cursor=cursor)
        return RenderedPage(b"".join(out).decode() + marker, next_pos, digest)
    return RenderedPage(b"".join(out).decode(), None, digest)


def render_full(report: Report) -> str:
    return "".join(serialize_block(b) for b in report)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd python && uv run --group dev pytest tests/test_render.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/render.py python/tests/test_render.py
git commit -m "feat(render): budgeted renderer with guaranteed progress and write audit"
```

### Task 6: Configuration and the read context

**Files:**
- Create: `python/src/science/config.py`
- Modify: `python/pyproject.toml` (the beliefs dependency and uv source)
- Create: `.gitignore` (`.worktrees/` and `.framework-test/`)
- Test: `python/tests/test_config.py`

**Interfaces:**
- Consumes: `from beliefs.world import WorldConfig` (the canonical import — a frozen dataclass at `beliefs/world/registry.py:137` with fields `world_root: Path`, `world_id: str`, `corpus_roots: tuple[Path, ...]`; its `__post_init__` requires `world_id` to be exactly 32 lowercase hex characters and `corpus_roots` to be an exact `tuple`, and resolves both path fields); `from beliefs.root import open_world` (`root.py:1674`, `(config: WorldConfig) -> World`); `Refusal`, `Refused` (Task 2). *Amended 2026-09-05:* `open_world` binds an authority since `beliefs` a1f7408; the read context consumes `from beliefs.root import open_world_read` (`(config: WorldConfig) -> World`, bound to `permit.READ_ONLY`; write-permits design §16) instead.
- Produces: `ScienceConfig(world: WorldConfig, operations_root: Path)`; `load_config(path: Path) -> ScienceConfig`; `resolve_config_path(cli_value: str | None, env: Mapping) -> Path` (CLI flag beats `SCIENCE_CONFIG`; neither present raises `Refused` `invalid-input`); `ReadContext(world, config)` with `ReadContext.open(config: ScienceConfig) -> ReadContext` (Task 8 adds its corpus-read helpers).

- [ ] **Step 1: Write the failing tests**

`python/tests/test_config.py`:

```python
from pathlib import Path

import pytest

from science.config import load_config, resolve_config_path
from science.refusal import Refused


WORLD_ID = "deadbeef" * 4  # WorldConfig requires 32 lowercase hex characters


def write_config(tmp_path: Path, world_id: str = WORLD_ID, extra: str = "") -> Path:
    world_root = tmp_path / "world"
    ops = tmp_path / "ops"
    corpus = tmp_path / "corpora" / "one"
    cfg = tmp_path / "science.toml"
    cfg.write_text(f"""
world_root = "{world_root}"
world_id = "{world_id}"
corpus_roots = ["{corpus}"]
operations_root = "{ops}"
{extra}""")
    return cfg


def test_load_config_builds_beliefs_worldconfig(tmp_path):
    cfg = load_config(write_config(tmp_path))
    assert cfg.world.world_id == WORLD_ID
    assert cfg.operations_root == tmp_path / "ops"
    assert [Path(p).name for p in cfg.world.corpus_roots] == ["one"]


def test_missing_field_refused(tmp_path):
    p = tmp_path / "bad.toml"
    p.write_text('world_root = "/x"\n')
    with pytest.raises(Refused) as e:
        load_config(p)
    assert e.value.refusal.code == "invalid-input"


def test_bad_world_id_wrong_types_and_unknown_keys_refused(tmp_path):
    with pytest.raises(Refused):
        load_config(write_config(tmp_path, world_id="w-test"))  # not 32-hex
    with pytest.raises(Refused):
        load_config(write_config(tmp_path, extra='stray = 1\n'))  # unknown key
    p = tmp_path / "types.toml"
    p.write_text(f'world_root = 3\nworld_id = "{WORLD_ID}"\n'
                 'corpus_roots = "not-a-list"\noperations_root = "/x"\n')
    with pytest.raises(Refused):
        load_config(p)
    malformed = tmp_path / "malformed.toml"
    malformed.write_text("this = is not [ toml")
    with pytest.raises(Refused) as e:  # a refusal, never an internal error
        load_config(malformed)
    assert e.value.refusal.code == "invalid-input"


def test_resolution_order(tmp_path):
    cfg = write_config(tmp_path)
    assert resolve_config_path(str(cfg), {}) == cfg
    assert resolve_config_path(None, {"SCIENCE_CONFIG": str(cfg)}) == cfg
    with pytest.raises(Refused):
        resolve_config_path(None, {})
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && uv run --group dev pytest tests/test_config.py -q`
Expected: FAIL — no module `science.config`.

- [ ] **Step 3: Implement `config.py`**

Add beliefs as a dependency — its distribution name today is **`beliefs`**
(beliefs' `python/pyproject.toml`), not the design's future
`verifiably-beliefs`. One mechanism, exactly this, in `python/pyproject.toml`:

```toml
[project]
dependencies = ["beliefs"]

[tool.uv.sources]
beliefs = { path = "../../beliefs/python", editable = true }
```

The relative path resolves because the science and beliefs checkouts are
siblings. When executing inside `.worktrees/<branch>` (where `../..` is the
science checkout itself), make it resolve with one command that derives
**both** ends from `--git-common-dir`, so it works from any cwd in either
the main checkout or a worktree:

```bash
COMMON="$(git rev-parse --path-format=absolute --git-common-dir)"   # <science>/.git
mkdir -p "$COMMON/../.worktrees"
ln -sfn "$COMMON/../../beliefs" "$COMMON/../.worktrees/beliefs"
```

and create the repository `.gitignore` in this task, with both lines this
plan needs:

```text
.worktrees/
.framework-test/
```

Never a vendored copy, never a machine path in a committed file.

```python
"""Launcher configuration: one TOML file, loaded straight into beliefs' WorldConfig."""
from __future__ import annotations

import os
import re
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from beliefs.root import open_world
from beliefs.world import WorldConfig

from science.refusal import Refusal, Refused


@dataclass(frozen=True)
class ScienceConfig:
    world: WorldConfig
    operations_root: Path


def _refuse(message: str) -> None:
    raise Refused(Refusal("invalid-input", message))


_WORLD_ID_RE = re.compile(r"^[0-9a-f]{32}$")  # WorldConfig's own rule, checked here first
_KEYS = ("world_root", "world_id", "corpus_roots", "operations_root")


def load_config(path: Path) -> ScienceConfig:
    if not path.is_file():
        _refuse(f"config file not found: {path}")
    try:
        raw = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as e:
        _refuse(f"config is not valid TOML: {e}")
    unknown = set(raw) - set(_KEYS)
    if unknown:
        _refuse(f"config has unknown keys {sorted(unknown)}")
    for key in _KEYS:
        if key not in raw:
            _refuse(f"config missing {key!r}")
    for key in ("world_root", "world_id", "operations_root"):
        if not isinstance(raw[key], str):
            _refuse(f"config {key!r} must be a string")
    if not (isinstance(raw["corpus_roots"], list)
            and all(isinstance(p, str) for p in raw["corpus_roots"])):
        _refuse("config 'corpus_roots' must be a list of strings")
    if not _WORLD_ID_RE.match(raw["world_id"]):
        _refuse("config 'world_id' must be 32 lowercase hex characters")
    world = WorldConfig(
        world_root=Path(raw["world_root"]),
        world_id=raw["world_id"],
        corpus_roots=tuple(Path(p) for p in raw["corpus_roots"]),
    )
    return ScienceConfig(world=world, operations_root=Path(raw["operations_root"]))


def resolve_config_path(cli_value: str | None, env: Mapping[str, str] | None = None) -> Path:
    env = os.environ if env is None else env
    if cli_value:
        return Path(cli_value)
    if "SCIENCE_CONFIG" in env:
        return Path(env["SCIENCE_CONFIG"])
    _refuse("no --config and no SCIENCE_CONFIG")
    raise AssertionError


@dataclass(frozen=True)
class ReadContext:
    world: object
    config: ScienceConfig

    @classmethod
    def open(cls, config: ScienceConfig) -> "ReadContext":
        return cls(world=open_world(config.world), config=config)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd python && uv run --group dev pytest tests/test_config.py -q`
Expected: PASS (these tests never call `ReadContext.open`, so no live world is needed).

- [ ] **Step 5: Commit**

```bash
git add python/pyproject.toml python/src/science/config.py python/tests/test_config.py .gitignore
git commit -m "feat(config): launcher config loading beliefs WorldConfig directly"
```

### Task 7: Read dispatcher with stateless continuation

**Files:**
- Create: `python/src/science/dispatch.py`
- Test: `python/tests/test_dispatch.py`

**Interfaces:**
- Consumes: Tasks 1–6 (`load_command_tree`, `canonicalize`, `input_digest`, `Refusal/Refused`, cursors, `render_page`, `report_digest`, `ReadContext`).
- Produces: `Outcome(text: str, invocation_id: str)`; `Dispatcher(declarations, handlers: Mapping[str, Callable], read_context, session=None)` with `invoke(command: str, inputs: Mapping, *, invocation_id: str | None = None, cursor: str | None = None) -> Outcome` (raises `Refused`). Read handler signature (the convention Task 8's handler follows and the build check enforces): `handle(ctx: ReadContext, **inputs) -> Report`. The write branch (`session`, dedup, claims) arrives in Task 12; this task raises `NotImplementedError("write dispatch lands with the beliefs session API")` if a non-read-only command is invoked.

- [ ] **Step 1: Write the failing tests**

`python/tests/test_dispatch.py`:

```python
from pathlib import Path

import pytest

from science.dispatch import Dispatcher
from science.cursor import MIN_OUTPUT_BUDGET
from science.refusal import Refused
from science.report import Text
from science.schema import Declaration, InputSpec, WriteClass


def make_decl(name="lots", budget=MIN_OUTPUT_BUDGET, inputs=()):
    return Declaration(name, "p", WriteClass("read-only"), budget, tuple(inputs), (), Path("."))


def lots_handler(ctx, **inputs):
    return tuple(Text(f"row {i} " + "x" * 60) for i in range(200))


def small_handler(ctx, *, corpus=None):
    return (Text(f"corpus={corpus}"),)


def build(mutable_rows=None):
    decls = (make_decl("lots"),
             make_decl("small", inputs=(InputSpec("corpus", "string", False, "d"),)))
    handlers = {"lots": lots_handler, "small": small_handler}
    return Dispatcher(decls, handlers, read_context=object())


def test_unknown_command_refused():
    with pytest.raises(Refused) as e:
        build().invoke("nope", {})
    assert e.value.refusal.code == "unknown-command"


def test_unknown_command_resolves_before_invalid_inputs():
    with pytest.raises(Refused) as e:
        build().invoke("nope", [])
    assert e.value.refusal.code == "unknown-command"


def test_read_invocation_renders_and_mints_id():
    out = build().invoke("small", {"corpus": "c1"})
    assert "corpus=c1" in out.text
    assert len(out.invocation_id) == 32


def test_pagination_round_trip_through_cursor():
    d = build()
    first = d.invoke("lots", {})
    assert "continue with cursor scur1." in first.text
    cursor = first.text.rsplit("cursor ", 1)[1].strip()
    second = d.invoke("lots", {}, cursor=cursor)
    assert second.text and second.text != first.text


def test_stale_cursor_refused_when_world_moves():
    d = build()
    first = d.invoke("lots", {})
    cursor = first.text.rsplit("cursor ", 1)[1].strip()
    d._handlers["lots"] = lambda ctx, **i: (Text("changed"),)  # the world moved
    with pytest.raises(Refused) as e:
        d.invoke("lots", {}, cursor=cursor)
    assert e.value.refusal.code == "stale-cursor"


def test_input_mismatch_on_altered_inputs():
    d = build()
    first = d.invoke("lots", {})
    cursor = first.text.rsplit("cursor ", 1)[1].strip()
    with pytest.raises(Refused) as e:
        d.invoke("small", {"corpus": "other"}, cursor=cursor)
    assert e.value.refusal.code in ("input-mismatch", "unknown-cursor")


def test_bad_invocation_id_refused():
    with pytest.raises(Refused) as e:
        build().invoke("small", {}, invocation_id="has space")
    assert e.value.refusal.code == "invalid-input"


def test_forged_mid_character_offset_refused():
    from science.cursor import ReadCursor, decode, encode
    d = build()
    d._handlers["lots"] = lambda ctx, **i: (Text("é" * 4000),)  # 2-byte chars
    first = d.invoke("lots", {})
    token = first.text.rsplit("cursor ", 1)[1].strip()
    cur = decode(token)
    forged = encode(ReadCursor(cur.command, cur.input_digest, cur.report_digest,
                               cur.block, cur.offset + 1))  # lands mid-character
    with pytest.raises(Refused) as e:
        d.invoke("lots", {}, cursor=forged)
    assert e.value.refusal.code == "stale-cursor"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && uv run --group dev pytest tests/test_dispatch.py -q`
Expected: FAIL — no module `science.dispatch`.

- [ ] **Step 3: Implement `dispatch.py`**

```python
"""The dispatcher: the one path every invocation takes (spec §6.1, §7.3)."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from science.canonical import canonicalize, input_digest
from science.cursor import ReadCursor, WriteCursor, decode, encode
from science.refusal import INVOCATION_ID_RE, Refusal, Refused, mint_token
from science.render import render_page
from science.report import Report
from science.schema import Declaration


@dataclass(frozen=True)
class Outcome:
    text: str
    invocation_id: str


class Dispatcher:
    def __init__(self, declarations, handlers: Mapping[str, Callable],
                 read_context, session=None) -> None:
        self._decls = {d.name: d for d in declarations}
        self._handlers = dict(handlers)
        self._ctx = read_context
        self._session = session

    def invoke(self, command: str, inputs: Mapping[str, object], *,
               invocation_id: str | None = None, cursor: str | None = None) -> Outcome:
        valid_iid = type(invocation_id) is str and INVOCATION_ID_RE.fullmatch(invocation_id)
        iid = invocation_id if valid_iid else mint_token()
        try:
            if invocation_id is not None and not valid_iid:
                raise Refused(Refusal("invalid-input", "invocation_id outside its grammar"))
            if type(command) is not str:
                raise Refused(Refusal("invalid-input", "command must be a string"))
            # Direct calls resolve before the untrusted input mapping is
            # inspected, so unknown-command has deterministic precedence.
            decl = None
            if cursor is None:
                decl = self._decls.get(command)
                if decl is None:
                    raise Refused(Refusal("unknown-command", f"no command {command!r}"))
            if not isinstance(inputs, Mapping):
                raise Refused(Refusal("invalid-input", "inputs must be a mapping"))
            if cursor is not None:
                return self._continue(command, inputs, decode(cursor), iid)
            assert decl is not None
            canonical = canonicalize(decl, inputs)
            if decl.write_class.kind != "read-only":
                raise NotImplementedError("write dispatch lands with the beliefs session API")
            report = self._handlers[decl.name](self._ctx, **canonical)
            return Outcome(self._render(decl, canonical, report, (0, 0)), iid)
        except Refused as e:
            if e.invocation_id is None:
                raise Refused(e.refusal, iid) from None
            raise

    def _render(self, decl: Declaration, canonical: Mapping, report: Report,
                position: tuple[int, int]) -> str:
        digest = input_digest(canonical)

        def cursor_for(pos: tuple[int, int], rdigest: str) -> str:
            return encode(ReadCursor(decl.name, digest, rdigest, pos[0], pos[1]))

        return render_page(report, budget=decl.output_budget, position=position,
                           cursor_for=cursor_for).text

    def _continue(self, command: str, inputs: Mapping, cur, iid: str) -> Outcome:
        if isinstance(cur, WriteCursor):
            raise NotImplementedError("write continuation lands with the beliefs session API")
        assert isinstance(cur, ReadCursor)
        decl = self._decls.get(cur.command)
        if decl is None:
            raise Refused(Refusal("unknown-cursor", f"cursor names unknown command {cur.command!r}"))
        if command != cur.command:  # judged before canonicalization, so the
            # mismatch refusal wins over invalid-input against the wrong schema
            raise Refused(Refusal("input-mismatch", "cursor was issued for a different command"))
        canonical = canonicalize(decl, inputs)
        if input_digest(canonical) != cur.input_digest:
            raise Refused(Refusal("input-mismatch", "cursor was issued for different inputs"))
        report = self._handlers[decl.name](self._ctx, **canonical)
        from science.render import report_digest as fresh_digest
        if fresh_digest(report) != cur.report_digest:
            raise Refused(Refusal("stale-cursor", "the world moved; re-run the command"))
        self._check_position(report, cur.block, cur.offset)
        page = self._render(decl, canonical, report, (cur.block, cur.offset))
        return Outcome(page, iid)

    @staticmethod
    def _check_position(report, block: int, offset: int) -> None:
        """Semantic position validation: within the report the digest just
        proved, and on a UTF-8 character boundary — a forged mid-character
        offset must refuse here, not fail inside the renderer's decode."""
        from science.report import serialize_block
        if block >= len(report):
            raise Refused(Refusal("stale-cursor", "cursor position is outside the report"))
        data = serialize_block(report[block]).encode()
        if offset >= len(data) or (data[offset] & 0xC0) == 0x80:
            raise Refused(Refusal("stale-cursor", "cursor position is not a boundary"))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd python && uv run --group dev pytest tests/test_dispatch.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/dispatch.py python/tests/test_dispatch.py
git commit -m "feat(dispatch): read dispatch with stateless cursor continuation"
```

### Task 8: The `status` command over a fixture world

**Files:**
- Create: `commands/status/command.toml`
- Create: `commands/status/prompt.md`
- Create: `python/src/science/commands/status.py`
- Create: `python/src/science/loader.py`
- Modify: `python/src/science/config.py` (the `read_view` helper)
- Create: `python/tests/conftest.py`
- Create: `python/tests/helpers/__init__.py`
- Create: `python/tests/helpers/world.py`
- Test: `python/tests/test_status.py`

**Interfaces:**
- Consumes (exact, from the beliefs tree): `World.registry() -> RegistryView` — a frozen dataclass of tuples, **not iterable**: enumerate corpus ids as `[r.corpus_id for r in view.admissions]`, terminal ids as `{r.corpus_id for r in view.statuses}` (`world/registry.py:155`); `World.status(corpus_id) -> CorpusStatus(known, live, present, findings)` (`registry.py:162`); `current_epoch(world) -> Epoch` which **raises `EpochUnknown`** (import `from beliefs.errors import EpochUnknown`) when no epoch exists, with `Epoch.packaging_identity: str` (`world/read.py:203`, `errors.py:113`); `ReadView.opened_at(root)` — the read-only corpus opener, no writer involved (`corpus.py:152`), whose `iter_stored()` yields `nodes` `Node` objects (`.kind`, `.uid`, `.id`, `.title`), unvalidated; `load_manifest(root).corpus_id` (`world/registry.py:493`); the fixture recipe below, mirrored from beliefs' own `world_case` fixture (`python/tests/acceptance/test_n2_cut6.py:155`).
- Produces: `science.commands.status.handle(ctx) -> Report`; `loader.production_tree()` + `loader.resolve_handlers(decls)` (imports `science.commands.<module>` per Task 1's `handler_module`, refusing a missing or signature-mismatched handler with `DeclarationError`); `ReadContext.read_views() -> tuple[tuple[str, ReadView], ...]` and `ReadContext.load_record(uid, record_id) -> Node`; conftest fixture `certified_work` (a fresh directory on a certified volume — beliefs' real engine refuses tmpfs roots, so **never `tmp_path`** for a live world); fixture helpers `build_fixture_world(work) -> ScienceConfig`, `add_one_more_record(cfg)`, `fixture_proposition_node(slug)`, `fixture_source_node(slug)`.

- [ ] **Step 1: Write the declaration and prompt**

`commands/status/command.toml`:

```toml
schema_version = 1
name = "status"
purpose = "Show the world: corpora and their lifecycle status, the current epoch, record counts by kind."
write_class = "read-only"
output_budget = 16384

[reads]
families = ["registry", "epoch", "corpus-stored"]
```

`commands/status/prompt.md`:

```markdown
Run `status` when the user asks where things stand, what corpora exist, or
whether an epoch is current. It takes no inputs. Render its output as-is;
if it ends with a truncation marker, continue with the cursor it names
rather than summarizing what you have not seen.
```

- [ ] **Step 2: Write the conftest and the fixture-world helper**

`python/tests/conftest.py` — mirror beliefs' certified-volume discipline
(its acceptance conftest states `/tmp` is a tmpfs with no barrier-option
table, which the real engine refuses):

```python
import os
import shutil
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture()
def certified_work():
    base = Path(os.environ.get("SCIENCE_TEST_ROOT", REPO_ROOT / ".framework-test"))
    work = base / uuid.uuid4().hex
    work.mkdir(parents=True)
    try:
        yield work
    finally:
        shutil.rmtree(work, ignore_errors=True)  # metadata siblings live inside work
```

(`.framework-test/` is already ignored — Task 6 created `.gitignore`.)

`python/tests/helpers/world.py` — the exact recipe of beliefs'
`world_case` fixture (`acceptance/test_n2_cut6.py:155`), with pins in the
format `adopt_manifest` validates (`"<namespace>:<64 hex>"`, mirroring
beliefs' `fixtures_cut6.PINS`); `Fresh()` is the no-field provenance for a
local admission, and `proposition_node` is the simplest mintable record —
its factory stamps the semantic identity itself, so there is no separate
stamping step:

```python
import secrets
from pathlib import Path

from beliefs import stored
from beliefs.consulted import CorpusPins
from beliefs.root import init_corpus_root, init_world_root, open_corpus, open_world
from beliefs.world import Fresh, WorldConfig

from science.config import ScienceConfig

PINS = CorpusPins(science_contract="science:" + "a" * 64,
                  domains={"biology": "biology:" + "b" * 64})


def fixture_proposition_node(slug: str):
    return stored.proposition_node(slug, title=slug, claim={"operator": "affects"})


def fixture_source_node(slug: str):
    return stored.source_node(slug, title=slug, identifiers={"doi": "10.1/" + slug})


def build_fixture_world(work: Path) -> ScienceConfig:
    corpus_root = work / "corpus"
    config = WorldConfig(work / "world", secrets.token_hex(16), (corpus_root,))
    init_world_root(config)
    init_corpus_root(corpus_root)
    writer = open_corpus(corpus_root)
    writer.adopt_manifest(profile=PINS)
    world = open_world(config)
    world.admit(corpus_root, provenance=Fresh(), actor="fixture")
    writer.add(fixture_proposition_node("p1"))
    return ScienceConfig(world=config, operations_root=work / "ops")


def add_one_more_record(cfg: ScienceConfig) -> None:
    open_corpus(cfg.world.corpus_roots[0]).add(fixture_proposition_node("p2"))
```

- [ ] **Step 3: Write the failing tests**

`python/tests/test_status.py`:

```python
import pytest

from science.config import ReadContext
from science.commands.status import handle
from science.loader import production_tree, resolve_handlers
from science.report import Heading, KeyVals
from tests.helpers.world import build_fixture_world


def test_status_renders_registry_epoch_and_counts(certified_work):
    cfg = build_fixture_world(certified_work)
    ctx = ReadContext.open(cfg)
    report = handle(ctx)
    text = "".join(str(b) for b in report)
    assert isinstance(report[0], Heading)
    assert "no current epoch" in text.lower()  # the fixture publishes no epoch
    kinds = [b for b in report if isinstance(b, KeyVals)]
    assert any("proposition" in str(b) for b in kinds), "expected per-corpus counts by kind"
    assert "live=True" in text  # CorpusStatus of the admitted corpus


def test_status_mutation_is_caught(certified_work):
    # N2 shape: adding a record must change the counts the report carries.
    cfg = build_fixture_world(certified_work)
    before = handle(ReadContext.open(cfg))
    from tests.helpers.world import add_one_more_record
    add_one_more_record(cfg)
    after = handle(ReadContext.open(cfg))
    assert before != after


def test_production_tree_ships_only_status():
    decls = production_tree()
    assert [d.name for d in decls] == ["status"]
    handlers = resolve_handlers(decls)
    assert callable(handlers["status"])


def _star_args(ctx, *args): return ()
def _star_kwargs(ctx, **kwargs): return ()
def _positional_only(ctx, corpus, /): return ()
def _wrong_lead(world): return ()
def _positional_input(ctx, corpus=None): return ()  # not keyword-only
def _missing_writer(ctx, *, corpus=None): return ()  # write class needs writer
def _stray_writer(ctx, writer, *, corpus=None): return ()  # read-only takes none
def _good(ctx, *, corpus=None): return ()


def _bind_and_resolve(monkeypatch, name, handle, write_class, inputs):
    import sys
    import types
    from pathlib import Path
    from science.cursor import MIN_OUTPUT_BUDGET
    from science.loader import resolve_handlers
    from science.schema import Declaration
    mod = types.ModuleType(f"science.commands.{name}")
    mod.handle = handle
    monkeypatch.setitem(sys.modules, f"science.commands.{name}", mod)
    decl = Declaration(name, "p", write_class, MIN_OUTPUT_BUDGET, inputs, (), Path("."))
    return resolve_handlers((decl,))


@pytest.mark.parametrize("handle", [
    _star_args,          # *args alone
    _star_kwargs,        # **kwargs alone
    _positional_only,    # positional-only input
    _wrong_lead,         # first parameter is not ctx
    _positional_input,   # input not keyword-only
    _stray_writer,       # writer on a read-only handler
])
def test_each_bad_read_handler_shape_refused_in_isolation(monkeypatch, handle):
    from science.schema import DeclarationError, InputSpec, WriteClass
    inputs = () if handle is _wrong_lead else (InputSpec("corpus", "string", False, "d"),)
    with pytest.raises(DeclarationError):
        _bind_and_resolve(monkeypatch, "shapecase", handle, WriteClass("read-only"), inputs)


def test_write_handler_must_take_writer(monkeypatch):
    from science.schema import DeclarationError, InputSpec, WriteClass
    wc = WriteClass("mints", ("proposition",), {"proposition": "corpus-write"})
    inputs = (InputSpec("corpus", "string", False, "d"),)
    with pytest.raises(DeclarationError):
        _bind_and_resolve(monkeypatch, "shapecase", _missing_writer, wc, inputs)


def test_good_handler_shape_resolves(monkeypatch):
    from science.schema import InputSpec, WriteClass
    inputs = (InputSpec("corpus", "string", False, "d"),)
    handlers = _bind_and_resolve(monkeypatch, "shapecase", _good,
                                 WriteClass("read-only"), inputs)
    assert callable(handlers["shapecase"])


def test_status_performs_exactly_its_declared_read_families(monkeypatch):
    """N2: the declared `reads` families are a contract — record which read
    surfaces the handler touches through a spying context and compare to the
    declaration. Adding a read family to the handler, or dropping one from
    the declaration, fails this test."""
    from types import SimpleNamespace
    import science.commands.status as status_mod
    used = set()

    class SpyWorld:
        def registry(self):
            used.add("registry")
            return SimpleNamespace(admissions=(), statuses=(), log_heads=())
        def status(self, cid):
            raise AssertionError("no corpora in the spy world")

    def spy_current_epoch(world):
        used.add("epoch")
        from beliefs.errors import EpochUnknown
        raise EpochUnknown("spy world has none")

    monkeypatch.setattr(status_mod, "current_epoch", spy_current_epoch)
    spy_ctx = SimpleNamespace(world=SpyWorld(),
                              read_views=lambda: used.add("corpus-stored") or ())
    status_mod.handle(spy_ctx)
    declared = set(next(d for d in production_tree() if d.name == "status").reads)
    assert used == declared
```

- [ ] **Step 4: Run tests to verify they fail**

Run: `cd python && uv run --group dev pytest tests/test_status.py -q`
Expected: FAIL — no module `science.commands.status` / `science.loader`.

- [ ] **Step 5: Implement the handler and loader**

`python/src/science/commands/status.py`:

```python
"""status: the shipped read exemplar (spec §11)."""
from __future__ import annotations

from collections import Counter

from beliefs.errors import EpochUnknown
from beliefs.world.read import current_epoch

from science.report import Heading, KeyVals, Report, Text


def handle(ctx) -> Report:
    world = ctx.world
    blocks: list = [Heading("World status")]
    view = world.registry()  # RegistryView: tuples, not iterable itself
    corpus_ids = sorted(r.corpus_id for r in view.admissions)
    rows = []
    for cid in corpus_ids:
        s = world.status(cid)  # CorpusStatus(known, live, present, findings)
        rows.append((cid, f"known={s.known} live={s.live} present={s.present}"))
    blocks.append(KeyVals("corpora", tuple(rows) or (("none", "no corpora admitted"),)))
    try:
        epoch = current_epoch(world)
        blocks.append(KeyVals("epoch", (("packaging", epoch.packaging_identity),)))
    except EpochUnknown:
        blocks.append(Text("No current epoch."))
    for cid, read_view in ctx.read_views():
        counts = Counter(node.kind for node in read_view.iter_stored())
        blocks.append(KeyVals(f"records in {cid}",
                              tuple((k, str(v)) for k, v in sorted(counts.items()))))
    return tuple(blocks)
```

Add to `ReadContext` (Task 6's `config.py`) the corpus-read helpers —
`ReadView.opened_at` is the read-only opener, and the manifest carries the
corpus id, so no writer and no registry lookup is involved:

```python
    def read_views(self) -> tuple[tuple[str, "ReadView"], ...]:
        from beliefs.corpus import ReadView
        from beliefs.world.registry import load_manifest
        pairs = []
        for root in self.config.world.corpus_roots:
            pairs.append((load_manifest(root).corpus_id, ReadView.opened_at(root)))
        return tuple(sorted(pairs))

    def load_record(self, uid: str, record_id: str):
        from science.refusal import Refusal, Refused
        for _, view in self.read_views():
            if view.holds(record_id):
                node = view.get(record_id)  # validates the semantic stamp
                if node.uid == uid:
                    return node
        raise Refused(Refusal("unknown-cursor", f"record {record_id!r} not found"))
```

`python/src/science/loader.py`:

```python
"""Load the production command tree and bind handlers by convention."""
from __future__ import annotations

import importlib
import inspect
from pathlib import Path

from science.schema import Declaration, DeclarationError, handler_module, load_command_tree

REPO_ROOT = Path(__file__).resolve().parents[3]
COMMANDS_ROOT = REPO_ROOT / "commands"


def production_kind_acts() -> dict[str, frozenset[str]]:
    # Explicitly empty until beliefs-96a24a ships `beliefs.permit.KIND_ACTS`:
    # only read-only commands can ship, which is exactly `status`. Task 12
    # replaces this body with the exact import — no try/except, no fallback.
    return {}


def production_tree() -> tuple[Declaration, ...]:
    kind_acts = production_kind_acts()
    declarations = load_command_tree(COMMANDS_ROOT, kind_acts=kind_acts,
                                     contract_kinds=frozenset(kind_acts))
    for declaration in declarations:
        if declaration.write_class.kind != "read-only":
            raise DeclarationError(declaration.directory / "command.toml",
                                   "write_class",
                                   "production write commands require beliefs capabilities")
    return declarations


def resolve_handlers(decls) -> dict:
    handlers = {}
    for decl in decls:
        module = importlib.import_module(handler_module(decl.name))
        handle = getattr(module, "handle", None)
        if handle is None:
            raise DeclarationError(decl.directory, "handler", f"{handler_module(decl.name)} has no handle()")
        params = list(inspect.signature(handle).parameters.values())
        POK, KW = inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY

        def _shape_error(reason: str):
            raise DeclarationError(decl.directory, "handler", reason)

        if any(p.kind in (inspect.Parameter.VAR_POSITIONAL,
                          inspect.Parameter.VAR_KEYWORD,
                          inspect.Parameter.POSITIONAL_ONLY) for p in params):
            _shape_error("no *args, **kwargs, or positional-only parameters")
        lead = ["ctx", "writer"] if decl.write_class.kind != "read-only" else ["ctx"]
        if [p.name for p in params[:len(lead)]] != lead \
                or any(p.kind is not POK for p in params[:len(lead)]):
            _shape_error(f"handler must lead with exactly {lead}")
        rest = params[len(lead):]
        if any(p.kind is not KW for p in rest):
            _shape_error("declared inputs must be keyword-only (after a bare *)")
        declared = {i.name: i for i in decl.inputs}
        accepted = {p.name for p in rest}
        if set(declared) != accepted:
            _shape_error(f"handler accepts {sorted(accepted)}, declaration says {sorted(declared)}")
        by_name = {p.name: p for p in rest}
        for name, spec in declared.items():
            default = by_name[name].default
            if spec.required and default is not inspect.Parameter.empty:
                _shape_error(f"required input {name!r} must have no handler default")
            if not spec.required and default is not None:
                # An absent optional is absent from **canonical, so the
                # parameter's own default is what the handler sees: None.
                _shape_error(f"optional input {name!r} must default to None")
        handlers[decl.name] = handle
    return handlers
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd python && uv run --group dev pytest tests/test_status.py -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add commands/ python/src/science/commands/status.py python/src/science/loader.py \
        python/src/science/config.py python/tests
git commit -m "feat(status): shipped read exemplar over a beliefs fixture world"
```

### Task 9: CLI with sessionless reads

**Files:**
- Create: `python/src/science/cli.py`
- Test: `python/tests/test_cli.py`

**Interfaces:**
- Consumes: `production_tree`, `resolve_handlers` (Task 8); `Dispatcher` (Task 7); `load_config`, `resolve_config_path`, `ReadContext` (Task 6); `Refused` (Task 2).
- Produces: `main(argv: list[str] | None = None) -> int` (the console script); `build_parser(decls) -> argparse.ArgumentParser`; option mapping: input `foo_bar` → `--foo-bar`, `bool` → `--foo/--no-foo` pair via `argparse.BooleanOptionalAction`, `list-of-string` → `action="append"`, `enum` → `choices=`. Command subparsers alone consume `--config`, `--invocation-id`, and `--continue` (dest `cursor`); `mcp serve` consumes only config; build verbs consume none. Command success/refusal metadata is one compact, key-sorted JSON stderr line and rendered output alone goes to stdout. `science serve` is not registered in this task; Task 13 owns it.

- [ ] **Step 1: Write the failing tests**

`python/tests/test_cli.py`:

```python
import json

import pytest

from science.cli import build_parser, main
from science.cursor import MIN_OUTPUT_BUDGET
from science.schema import Declaration, InputSpec, WriteClass
from pathlib import Path
from tests.helpers.world import write_cli_config


def test_parser_compiles_inputs():
    decl = Declaration("small", "p", WriteClass("read-only"), MIN_OUTPUT_BUDGET,
                       (InputSpec("mode", "enum", True, "d", choices=("a", "b")),
                        InputSpec("tag", "list-of-string", False, "d")), (), Path("."))
    parser = build_parser((decl,))
    ns = parser.parse_args(["small", "--mode", "a", "--tag", "x", "--tag", "y"])
    assert ns.command == "small" and ns.mode == "a" and ns.tag == ["x", "y"]
    with pytest.raises(SystemExit) as e:  # argparse usage error
        parser.parse_args(["small", "--mode", "zz"])
    assert e.value.code == 2


def test_status_end_to_end(certified_work, capsys):
    cfg_path = write_cli_config(certified_work)
    code = main(["status", "--config", str(cfg_path)])
    captured = capsys.readouterr()
    assert code == 0
    assert "World status" in captured.out
    metadata = json.loads(captured.err)
    assert len(metadata["invocation_id"]) == 32


def test_refusal_exits_3(certified_work, capsys):
    cfg_path = write_cli_config(certified_work)
    code = main(["status", "--config", str(cfg_path), "--continue", "scur1.garbage"])
    assert code == 3
    payload = json.loads(capsys.readouterr().err)
    assert payload["refusal"]["code"] == "unknown-cursor"
    assert set(payload["refusal"]) == {"code", "message", "data"}
    assert payload["invocation_id"]


def test_missing_config_exits_3(capsys, monkeypatch):
    monkeypatch.delenv("SCIENCE_CONFIG", raising=False)
    assert main(["status"]) == 3
```

Add `write_cli_config(work)` to `tests/helpers/world.py` (both this task
and Task 11 use it):

```python
def write_cli_config(work: Path) -> Path:
    cfg = build_fixture_world(work)
    path = work / "science.toml"
    path.write_text(f"""
world_root = "{cfg.world.world_root}"
world_id = "{cfg.world.world_id}"
corpus_roots = ["{cfg.world.corpus_roots[0]}"]
operations_root = "{cfg.operations_root}"
""")
    return path
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && uv run --group dev pytest tests/test_cli.py -q`
Expected: FAIL — no module `science.cli`.

- [ ] **Step 3: Implement `cli.py`**

```python
"""The science CLI: sessionless reads, service-routed writes (spec §9.2)."""
from __future__ import annotations

import argparse
import json
import sys

from science.config import ReadContext, load_config, resolve_config_path
from science.dispatch import Dispatcher
from science.loader import production_tree, resolve_handlers
from science.refusal import INVOCATION_ID_RE, Refusal, Refused, envelope, mint_token
from science.schema import Declaration

EXIT_OK, EXIT_INTERNAL, EXIT_USAGE, EXIT_REFUSED = 0, 1, 2, 3


def _add_command(sub: argparse._SubParsersAction, decl: Declaration,
                 common: argparse.ArgumentParser) -> None:
    p = sub.add_parser(decl.name, help=decl.purpose, parents=[common])
    for spec in decl.inputs:
        flag = "--" + spec.name.replace("_", "-")
        kwargs: dict = {"required": spec.required, "help": spec.doc, "dest": spec.name}
        match spec.type:
            case "int":
                kwargs["type"] = int
            case "bool":
                kwargs["action"] = argparse.BooleanOptionalAction
            case "enum":
                kwargs["choices"] = list(spec.choices)
            case "list-of-string":
                kwargs["action"] = "append"
            case _:
                pass
        p.add_argument(flag, **kwargs)


def _command_options() -> argparse.ArgumentParser:
    """Shared parent so `science status --config …` parses: argparse only
    accepts an option after the subcommand if the subparser declares it."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config")
    common.add_argument("--invocation-id", dest="invocation_id")
    common.add_argument("--continue", dest="cursor")
    return common


def build_parser(decls) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="science")
    common = _command_options()
    sub = parser.add_subparsers(dest="command", required=True)
    for decl in decls:
        _add_command(sub, decl, common)
    sub.add_parser("build")
    mcp = sub.add_parser("mcp")
    mcp.add_argument("mode", choices=["serve"])
    mcp.add_argument("--config")
    adapters = sub.add_parser("adapters")
    adapters.add_argument("mode", choices=["build"])
    return parser


def _json_line(value: dict[str, object]) -> None:
    sys.stderr.write(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")


def _bind_invocation_id(value: object) -> str:
    if type(value) is str and INVOCATION_ID_RE.fullmatch(value):
        return value
    invocation_id = mint_token()
    if value is not None:
        raise Refused(Refusal("invalid-input", "invocation_id outside its grammar"),
                      invocation_id)
    return invocation_id


def main(argv: list[str] | None = None) -> int:
    invocation_id = None
    try:
        decls = production_tree()
        parser = build_parser(decls)
        ns = parser.parse_args(argv)
        if ns.command in ("mcp", "adapters", "build"):
            return _framework_verb(ns)
        invocation_id = _bind_invocation_id(ns.invocation_id)
        ns.invocation_id = invocation_id
        decl = next(d for d in decls if d.name == ns.command)
        inputs = {s.name: getattr(ns, s.name) for s in decl.inputs
                  if getattr(ns, s.name, None) is not None}
        if decl.write_class.kind != "read-only":
            return _via_service(ns, decl, inputs)  # Task 13; until then unreachable
        config = load_config(resolve_config_path(ns.config))
        dispatcher = Dispatcher(decls, resolve_handlers(decls), ReadContext.open(config))
        out = dispatcher.invoke(ns.command, inputs,
                                invocation_id=invocation_id, cursor=ns.cursor)
        sys.stdout.write(out.text)
        _json_line({"invocation_id": out.invocation_id})
        return EXIT_OK
    except Refused as e:
        payload = {"refusal": envelope(e.refusal)}
        if (bound_id := e.invocation_id or invocation_id) is not None:
            payload["invocation_id"] = bound_id
        _json_line(payload)
        return EXIT_REFUSED
    except Exception:  # noqa: BLE001 — the CLI's last resort
        payload = {"error": {"code": "internal-error", "message": "Internal error"}}
        if invocation_id is not None:
            payload["invocation_id"] = invocation_id
        _json_line(payload)
        return EXIT_INTERNAL


def _framework_verb(ns) -> int:
    raise NotImplementedError(f"{ns.command} arrives in a later task")


def _via_service(ns, decl, inputs) -> int:
    raise NotImplementedError("write routing arrives with the service process (Task 13)")


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd python && uv run --group dev pytest tests/test_cli.py -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/cli.py python/tests/test_cli.py
git commit -m "feat(cli): argparse surface with sessionless reads and exit-code contract"
```

### Task 10: Preamble and the Claude Code adapter generator

**Files:**
- Create: `commands/PREAMBLE.md`
- Create: `python/src/science/adapters.py`
- Create: `skills/.gitkeep`
- Create: `adapters/claude-code/` (generated then committed)
- Modify: `python/src/science/cli.py` (wire `adapters` and `build` verbs)
- Test: `python/tests/test_adapters.py`

**Interfaces:**
- Consumes: `production_tree` (Task 8).
- Produces: `preflight_build(decls, commands_root, skills_root)` — the one
  handler/collision/source-safety check and immutable content snapshot used by
  both build verbs; `build_adapter(decls, commands_root: Path, skills_root:
  Path, out: Path) -> None` (idempotent, deterministic, and mutates `out` only
  after preflight succeeds); the committed `adapters/claude-code/` tree:
  `.claude-plugin/plugin.json`, `skills/<name>/SKILL.md` per command,
  `.mcp.json`; CLI verbs `science adapters build` and `science build` (tree
  validation only).

- [x] **Step 1: Write the preamble**

`commands/PREAMBLE.md`:

```markdown
You are working over one world of governed records through the `science`
commands. Until the coordination layer lands there is no current view:
commands read world state directly. Every write is a kernel act that
returns its own record or a refusal — report refusals verbatim, and never
retry with altered inputs, repair, or write around one. Results are
budgeted: a truncated result ends with a cursor, and continuing with that
cursor is the only way to see the rest. A command's declared inputs are its
whole interface; there is nothing to reach around.
```

- [x] **Step 2: Write the failing tests**

`python/tests/test_adapters.py`:

```python
import json
from pathlib import Path

from science.adapters import build_adapter
from science.loader import COMMANDS_ROOT, REPO_ROOT, production_tree


def _tree_files(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}


def test_generated_tree_matches_committed(tmp_path):
    decls = production_tree()
    build_adapter(decls, COMMANDS_ROOT, REPO_ROOT / "skills", tmp_path)
    committed = REPO_ROOT / "adapters" / "claude-code"
    assert _tree_files(tmp_path) == _tree_files(committed)  # recursive, byte-exact


def test_skill_carries_preamble_and_prompt(tmp_path):
    decls = production_tree()
    build_adapter(decls, COMMANDS_ROOT, REPO_ROOT / "skills", tmp_path)
    skill = (tmp_path / "skills" / "status" / "SKILL.md").read_text()
    assert "one world" in skill            # preamble present
    assert "Run `status`" in skill         # prompt body present
    assert skill.startswith("---\n")       # frontmatter


def test_mcp_json_has_no_machine_paths(tmp_path):
    decls = production_tree()
    build_adapter(decls, COMMANDS_ROOT, REPO_ROOT / "skills", tmp_path)
    raw = json.loads((tmp_path / ".mcp.json").read_text())
    server = raw["mcpServers"]["science"]
    assert server["command"] == "science" and server["args"] == ["mcp", "serve"]
    assert "/home/" not in json.dumps(raw) and "/mnt/" not in json.dumps(raw)
```

Also add focused mutations that replace the command directory,
`command.toml`, `prompt.md`, and `PREAMBLE.md` with symlinks. Every mutation
must refuse; adapter-facing cases begin with a sentinel in `out` and assert it
survives. Add a missing-handler case, an out-of-root declaration case, and
authored/generated collision and authored-source symlink cases with the same
pre-mutation sentinel assertion.

- [x] **Step 3: Run tests to verify they fail**

Run: `cd python && uv run --group dev pytest tests/test_adapters.py -q`
Expected: FAIL — no module `science.adapters`.

- [x] **Step 4: Implement `adapters.py` and wire the verbs**

```python
"""Generate the Claude Code plugin from the command tree (spec §10)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from science.schema import Declaration, DeclarationError

PLUGIN = {
    "name": "science",
    "description": "Science commands over a beliefs world.",
    "version": "0.1.0",
}
MCP = {"mcpServers": {"science": {"command": "science", "args": ["mcp", "serve"]}}}


def _skill_md(decl: Declaration, preamble: str, prompt: str) -> str:
    # json.dumps produces a valid YAML double-quoted scalar, so a purpose
    # containing ':' or quotes cannot break the frontmatter.
    front = (f"---\nname: {json.dumps(decl.name)}\n"
             f"description: {json.dumps(decl.purpose)}\n---\n\n")
    return front + preamble.strip() + "\n\n" + prompt.strip() + "\n"


def build_adapter(decls, commands_root: Path, skills_root: Path, out: Path) -> None:
    # `preflight_build` resolves every handler, proves containment, rejects
    # symlink/special sources and skill collisions, and reads every TOML,
    # prompt, preamble, and authored-skill byte into `sources`.
    sources = preflight_build(decls, commands_root, skills_root)
    if out.exists():
        shutil.rmtree(out)
    (out / ".claude-plugin").mkdir(parents=True)
    (out / ".claude-plugin" / "plugin.json").write_text(json.dumps(PLUGIN, indent=2) + "\n")
    (out / ".mcp.json").write_text(json.dumps(MCP, indent=2) + "\n")
    for decl, prompt in zip(sources.declarations, sources.prompts, strict=True):
        skill_dir = out / "skills" / decl.name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            _skill_md(decl, sources.preamble, prompt), encoding="utf-8")
    # Recreate authored directories/files from the pre-read byte snapshot;
    # never reopen a source after `out` has been removed.
    for skill in sources.authored:
        root = out / "skills" / skill.name
        root.mkdir(parents=True)
        for directory in skill.directories:
            (root / directory).mkdir(parents=True)
        for relative, content in skill.files:
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
```

In `cli.py`, replace `_framework_verb` so `adapters build` (the spec's verb, `ns.mode` from Task 9's parser) regenerates the committed tree and `build` validates:

```python
def _framework_verb(ns) -> int:
    from science.loader import COMMANDS_ROOT, REPO_ROOT, production_tree
    decls = production_tree()  # build refusals surface here
    if ns.command == "build":
        from science.adapters import preflight_build
        preflight_build(decls, COMMANDS_ROOT, REPO_ROOT / "skills")
        sys.stdout.write(f"ok: {len(decls)} command(s)\n")
        return EXIT_OK
    if ns.command == "adapters":  # parser guarantees ns.mode == "build"
        from science.adapters import build_adapter
        build_adapter(decls, COMMANDS_ROOT, REPO_ROOT / "skills",
                      REPO_ROOT / "adapters" / "claude-code")
        return EXIT_OK
    raise NotImplementedError(f"{ns.command} arrives in a later task")
```

(`science adapters build` regenerating in place is fine: the tree is committed, so drift shows in `git diff`, and the test compares against a fresh build.)

- [x] **Step 5: Generate the committed tree, then run tests to verify they pass**

Run: `cd python && uv run science adapters build && cd .. && git add adapters/ && cd python && uv run --group dev pytest tests/test_adapters.py -q`
Expected: PASS.

- [x] **Step 6: Commit**

```bash
git add commands/PREAMBLE.md skills/.gitkeep python/src/science/adapters.py \
        python/src/science/cli.py adapters/ python/tests/test_adapters.py
git commit -m "feat(adapters): Claude Code plugin generator with committed tree diff"
```

### Task 11: MCP server and transport equivalence

**Files:**
- Create: `python/src/science/mcp.py`
- Modify: `python/src/science/cli.py` (wire `mcp serve`)
- Test: `python/tests/test_mcp.py`

**Protocol ruling (resolves the version question before any code):** the
server pins **MCP `2026-07-28`** — the current revision, which retired the
`initialize`/`initialized` handshake in favor of a mandatory
`server/discover` method, requires every request's `_meta` to carry the
protocol version and client capabilities (client info is optional), and
**removed protocol sessions entirely**: requests are independent. The
design's "one attended session per server lifetime" (spec §9.3) is not an
MCP concept and is unaffected — the writer session is **launcher-owned
process state**, bound to the server process from spawn to exit, that
those independent requests share: same person, full permit, one ledger.
This ruling is recorded in spec §9.3. **Step 0 of this task:** read the
pinned revision's base protocol, versioning, discovery, and tools pages
(`modelcontextprotocol.io/specification/2026-07-28/basic`,
`…/basic/versioning`, `…/server/discover`, `…/server/tools`) and mirror
the exact request/response shapes — the code below fixes the dispatch
logic and our side of the contract; field spellings for `_meta`'s members,
the discovery result, and the `resultType` marker come from those pages,
and the tests are written from them, not from memory.

**Interfaces:**
- Consumes: `Dispatcher`, `production_tree`, `resolve_handlers`, `ReadContext`, `load_config`, `Refused`.
- Produces: `PROTOCOL_VERSION = "2026-07-28"`; `tool_schema(decl) -> dict` (JSON Schema: declared inputs + optional `invocation_id` and `cursor` string properties); `handle_request(req, dispatcher, decls) -> dict | None` — a JSON-RPC 2.0 responder for the **mandatory `server/discover`**, `tools/list`, and `tools/call`, with layered validation: envelope first (`jsonrpc` marker, non-null string/integer `id` when present, string `method` → `-32600`), then notification silence for a valid omitted id, then the params object and `_meta` (`-32602` for a non-object `params` or missing required fields; **only protocol version and client capabilities are required — `clientInfo` is optional when absent but validated as an `Implementation` when present**; an unsupported version → `-32022` with `{supported, requested}` data), then per-method params (`-32602`, unknown tool names included — a protocol error, never a framework tool refusal); `server/discover` returns the discovery contract's shape — `supportedVersions`, `capabilities`, and the server's `Implementation` under `_meta["io.modelcontextprotocol/serverInfo"]`; no `initialize` handling exists to keep obsolete clients honest; `serve(config_path, stdin, stdout, session=None) -> None` whose loop answers malformed JSON with `-32700` and never terminates on bad input (the `session` parameter is wired to the attended writer session in Task 12; until then every command it can serve is read-only). Tool results carry the rendered text as content and `structuredContent: {"invocation_id": …}` so callers can reuse minted ids; a refusal result sets `isError`, keeps the human text `refused [<code>] <message>`, and carries the full spec §6.3 envelope (and the invocation id when one was bound) in `structuredContent` — structured `data` is never discarded into parseable text.

  Final wire additions: `handle_request(...) -> dict | None` returns `None`
  for JSON-RPC notifications (which omit `id`); discovery and list include
  `ttlMs = 300_000` and `cacheScope = "public"`; list refuses every supplied
  cursor because this complete implementation issues none. `tools/call`
  recognizes `inputResponses` (object) and `requestState` (string), validates
  their outer shapes, and refuses them as unsolicited multi-round state because
  science never emitted `input_required`. Every response is freshly allocated.
  `MAX_REQUEST_BYTES = 1_048_576`; `serve` takes a binary input stream, decodes
  strict UTF-8, bounds each `readline`, drains oversized frames through their
  newline, and continues with the following request. Invalid UTF-8 is `-32700`;
  an oversized frame is `-32600`.

- [ ] **Step 1: Write the failing tests**

`python/tests/test_mcp.py`:

```python
import io
import json

from science.mcp import handle_request, tool_schema
from science.loader import production_tree


META = {  # every 2026-07-28 request carries these namespaced keys
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientInfo": {"name": "science-tests", "version": "0"},
    "io.modelcontextprotocol/clientCapabilities": {},
}


def rpc(method, params=None, id=1):
    body = dict(params or {})
    body.setdefault("_meta", dict(META))
    return {"jsonrpc": "2.0", "id": id, "method": method, "params": body}


def test_tool_schema_carries_inputs_and_protocol_fields():
    decl = next(d for d in production_tree() if d.name == "status")
    schema = tool_schema(decl)
    props = schema["inputSchema"]["properties"]
    assert "invocation_id" in props and "cursor" in props
    assert schema["name"] == "status" and schema["description"] == decl.purpose


def test_tools_list_and_call(certified_work):
    from tests.helpers.world import build_fixture_world
    from science.config import ReadContext
    from science.dispatch import Dispatcher
    from science.loader import resolve_handlers
    cfg = build_fixture_world(certified_work)
    decls = production_tree()
    dispatcher = Dispatcher(decls, resolve_handlers(decls), ReadContext.open(cfg))
    listed = handle_request(rpc("tools/list"), dispatcher, decls)
    assert [t["name"] for t in listed["result"]["tools"]] == ["status"]
    called = handle_request(rpc("tools/call", {"name": "status", "arguments": {}}), dispatcher, decls)
    text = called["result"]["content"][0]["text"]
    assert "World status" in text
    assert len(called["result"]["structuredContent"]["invocation_id"]) == 32


def test_meta_requirements_match_the_revision():
    no_meta = rpc("tools/list")
    del no_meta["params"]["_meta"]
    assert handle_request(no_meta, dispatcher=None, decls=())["error"]["code"] == -32602
    no_caps = rpc("tools/list")
    del no_caps["params"]["_meta"]["io.modelcontextprotocol/clientCapabilities"]
    assert handle_request(no_caps, dispatcher=None, decls=())["error"]["code"] == -32602
    without_client_info = rpc("tools/list")  # clientInfo is OPTIONAL when absent
    del without_client_info["params"]["_meta"]["io.modelcontextprotocol/clientInfo"]
    assert "result" in handle_request(without_client_info, dispatcher=None, decls=())
    bad_client_info = rpc("tools/list")  # …but validated as Implementation when present
    bad_client_info["params"]["_meta"]["io.modelcontextprotocol/clientInfo"] = {"name": 7}
    assert handle_request(bad_client_info, dispatcher=None, decls=())["error"]["code"] == -32602
    null_client_info = rpc("tools/list")  # explicit null is present-and-malformed
    null_client_info["params"]["_meta"]["io.modelcontextprotocol/clientInfo"] = None
    assert handle_request(null_client_info, dispatcher=None, decls=())["error"]["code"] == -32602


def test_unsupported_version_is_32022_with_versions():
    wrong = rpc("tools/list")
    wrong["params"]["_meta"]["io.modelcontextprotocol/protocolVersion"] = "2025-06-18"
    err = handle_request(wrong, dispatcher=None, decls=())["error"]
    assert err["code"] == -32022
    assert err["data"] == {"supported": ["2026-07-28"], "requested": "2025-06-18"}


def test_envelope_validation():
    assert handle_request("not an object", dispatcher=None, decls=())["error"]["code"] == -32600
    for broken in (
        {"id": 1, "method": "tools/list", "params": {}},                       # no jsonrpc
        {"jsonrpc": "2.0", "id": True, "method": "tools/list", "params": {}},  # bool id
        {"jsonrpc": "2.0", "id": 1, "method": 7, "params": {}},                # bad method
    ):
        assert handle_request(broken, dispatcher=None, decls=())["error"]["code"] == -32600


def test_server_discover_matches_the_discovery_contract():
    res = handle_request(rpc("server/discover"), dispatcher=None, decls=())["result"]
    # Exact equality: a legacy top-level protocolVersion/serverInfo field or
    # a missing server version would slip past field-by-field assertions.
    assert res == {
        "supportedVersions": ["2026-07-28"],
        "capabilities": {"tools": {}},
        "ttlMs": 300_000,
        "cacheScope": "public",
        "_meta": {"io.modelcontextprotocol/serverInfo":
                  {"name": "science", "version": "0.1.0"}},
        "resultType": "complete",
    }


def test_results_carry_complete_result_type():
    listed = handle_request(rpc("tools/list"), dispatcher=None, decls=())
    assert listed["result"]["resultType"] == "complete"


def test_malformed_wire_shapes_are_protocol_errors():
    bad_params = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": []}
    assert handle_request(bad_params, dispatcher=None, decls=())["error"]["code"] == -32602
    bad_args = rpc("tools/call", {"name": "status", "arguments": ["not", "a", "dict"]})
    assert handle_request(bad_args, dispatcher=None, decls=())["error"]["code"] == -32602
    bad_name = rpc("tools/call", {"name": 7, "arguments": {}})
    assert handle_request(bad_name, dispatcher=None, decls=())["error"]["code"] == -32602
    bad_cursor = rpc("tools/call", {"name": "status", "arguments": {"cursor": 3}})
    assert handle_request(bad_cursor, dispatcher=None, decls=())["error"]["code"] == -32602
    bad_iid = rpc("tools/call", {"name": "status", "arguments": {"invocation_id": 3}})
    assert handle_request(bad_iid, dispatcher=None, decls=())["error"]["code"] == -32602


def test_unknown_tool_is_a_protocol_error():
    res = handle_request(rpc("tools/call", {"name": "nope", "arguments": {}}),
                         dispatcher=None, decls=())
    assert res["error"]["code"] == -32602  # protocol -32602, never a tool refusal


def test_initialize_is_gone():
    res = handle_request(rpc("initialize"), dispatcher=None, decls=())
    assert res["error"]["code"] == -32601  # retired by MCP 2026-07-28; no legacy shim


def test_parse_error_does_not_end_the_loop(certified_work):
    import io
    from science.mcp import serve
    from tests.helpers.world import write_cli_config
    cfg_path = write_cli_config(certified_work)
    stdin = io.BytesIO(("{bad json\n" + json.dumps(rpc("tools/list")) + "\n").encode())
    stdout = io.StringIO()
    serve(cfg_path, stdin=stdin, stdout=stdout)
    lines = [json.loads(l) for l in stdout.getvalue().splitlines()]
    assert lines[0]["error"]["code"] == -32700
    assert "result" in lines[1]  # the loop survived the parse error


def test_transport_equivalence_cli_vs_mcp(certified_work, capsys):
    """Spec §9.4: byte-identical payloads, not merely equivalent dispatch."""
    from science.cli import main
    from science.config import ReadContext, load_config
    from science.dispatch import Dispatcher
    from science.loader import resolve_handlers
    from tests.helpers.world import write_cli_config
    cfg_path = write_cli_config(certified_work)
    assert main(["status", "--config", str(cfg_path)]) == 0
    cli_text = capsys.readouterr().out
    decls = production_tree()
    dispatcher = Dispatcher(decls, resolve_handlers(decls),
                            ReadContext.open(load_config(cfg_path)))
    mcp_text = handle_request(
        rpc("tools/call", {"name": "status", "arguments": {}}), dispatcher, decls,
    )["result"]["content"][0]["text"]
    assert cli_text == mcp_text


def test_refusal_becomes_tool_error(certified_work):
    from tests.helpers.world import build_fixture_world
    from science.config import ReadContext
    from science.dispatch import Dispatcher
    from science.loader import resolve_handlers
    cfg = build_fixture_world(certified_work)
    decls = production_tree()
    dispatcher = Dispatcher(decls, resolve_handlers(decls), ReadContext.open(cfg))
    res = handle_request(
        rpc("tools/call", {"name": "status", "arguments": {"cursor": "junk"}}), dispatcher, decls)
    assert res["result"]["isError"] is True
    assert "unknown-cursor" in res["result"]["content"][0]["text"]
    structured = res["result"]["structuredContent"]["refusal"]
    assert structured["code"] == "unknown-cursor"
    assert isinstance(structured["message"], str) and isinstance(structured["data"], dict)
```

Add exact tests for both cache fields on discovery/list, fresh nested response
objects across calls, notification silence (direct and stdio, followed by a
valid request), rejection of every supplied list cursor, malformed and
unsolicited `inputResponses`/`requestState`, and a binary stream containing
invalid UTF-8, then a frame of `MAX_REQUEST_BYTES + 1`, then a valid request.
The first two frames return `-32700` and `-32600`; the valid request is still
served, proving drain/recovery rather than merely detecting the size.
Also send a sub-limit, deeply nested JSON frame followed by a valid request;
decoder `RecursionError` is `-32700` and the following request is served.

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && uv run --group dev pytest tests/test_mcp.py -q`
Expected: FAIL — no module `science.mcp`.

- [ ] **Step 3: Implement `mcp.py` and wire the verb**

```python
"""Hand-rolled MCP server: JSON-RPC 2.0 over stdio (spec §9.3)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from science.dispatch import Dispatcher
from science.refusal import Refused
from science.schema import Declaration

_JSON_TYPES = {"string": "string", "int": "integer", "bool": "boolean"}


def tool_schema(decl: Declaration) -> dict:
    props: dict = {}
    required = []
    for spec in decl.inputs:
        if spec.type == "enum":
            entry = {"type": "string", "enum": list(spec.choices)}
        elif spec.type == "list-of-string":
            entry = {"type": "array", "items": {"type": "string"}}
        else:
            entry = {"type": _JSON_TYPES[spec.type]}
        entry["description"] = spec.doc
        props[spec.name] = entry
        if spec.required:
            required.append(spec.name)
    props["invocation_id"] = {"type": "string", "description": "Optional idempotency token."}
    props["cursor"] = {"type": "string", "description": "Continuation cursor from a truncated result."}
    schema = {"type": "object", "properties": props}
    if required:
        schema["required"] = required
    return {"name": decl.name, "description": decl.purpose, "inputSchema": schema}


PROTOCOL_VERSION = "2026-07-28"  # the ruling above; no pre-2026 fallbacks
MAX_REQUEST_BYTES = 1_048_576
CACHE_TTL_MS = 300_000
CACHE_SCOPE = "public"


_NS = "io.modelcontextprotocol/"  # MCP's namespaced _meta keys


def _valid_implementation(value: object) -> bool:
    """The spec's Implementation shape: string name and version."""
    return (isinstance(value, dict)
            and isinstance(value.get("name"), str)
            and isinstance(value.get("version"), str))


def _meta_error(meta: object) -> tuple[int, str, dict] | None:
    """Required: protocol version and client capabilities. clientInfo is
    OPTIONAL — accepted when absent, but validated as an Implementation
    when present. Missing/malformed required fields are invalid params
    (-32602); an unsupported version is -32022 carrying the supported and
    requested versions."""
    if not isinstance(meta, dict):
        return (-32602, "request _meta is required", {})
    version = meta.get(_NS + "protocolVersion")
    if not isinstance(version, str):
        return (-32602, f"{_NS}protocolVersion is required", {})
    if version != PROTOCOL_VERSION:
        return (-32022, "unsupported protocol version",
                {"supported": [PROTOCOL_VERSION], "requested": version})
    if not isinstance(meta.get(_NS + "clientCapabilities"), dict):
        return (-32602, f"{_NS}clientCapabilities is required", {})
    if _NS + "clientInfo" in meta:
        # Presence is the test, not truthiness: an explicit null is a
        # malformed present value, never "absent".
        if not _valid_implementation(meta[_NS + "clientInfo"]):
            return (-32602, f"{_NS}clientInfo, when present, must be an Implementation", {})
    return None


def _envelope_error(req: object) -> str | None:
    """JSON-RPC envelope validation: jsonrpc marker, non-null string or
    integer id, string method."""
    if not isinstance(req, dict):
        return "request must be an object"
    if req.get("jsonrpc") != "2.0":
        return "jsonrpc must be \"2.0\""
    if "id" in req and type(req["id"]) not in (str, int):
        return "id must be a non-null string or integer"
    if not isinstance(req.get("method"), str):
        return "method must be a string"
    return None


def _rpc_error(rid, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": code, "message": message}}


def handle_request(req: dict, dispatcher: Dispatcher, decls) -> dict | None:
    envelope_problem = _envelope_error(req)
    if envelope_problem is not None:
        rid = req.get("id") if isinstance(req, dict) else None
        if isinstance(rid, bool) or not isinstance(rid, (str, int)):
            rid = None
        return _rpc_error(rid, -32600, envelope_problem)
    if "id" not in req:  # valid JSON-RPC notification: never respond
        return None
    rid, method = req["id"], req["method"]
    params = req.get("params")
    if not isinstance(params, dict):  # null, list, or absent: invalid params
        return _rpc_error(rid, -32602, "params must be an object")
    problem = _meta_error(params.get("_meta"))
    if problem is not None:
        code, message, data = problem
        err = _rpc_error(rid, code, message)
        if data:
            err["error"]["data"] = data
        return err
    if method == "server/discover":  # mandatory on 2026-07-28
        return _result(rid, {"supportedVersions": [PROTOCOL_VERSION],
                             "capabilities": {"tools": {}},
                             "ttlMs": CACHE_TTL_MS,
                             "cacheScope": CACHE_SCOPE,
                             "_meta": {_NS + "serverInfo":
                                       {"name": "science", "version": "0.1.0"}}})
    if method == "tools/list":
        if "cursor" in params:
            if type(params["cursor"]) is not str:
                return _rpc_error(rid, -32602, "cursor must be a string")
            return _rpc_error(rid, -32602, "cursor was not issued by this listing")
        return _result(rid, {"tools": [tool_schema(d) for d in decls],
                             "ttlMs": CACHE_TTL_MS,
                             "cacheScope": CACHE_SCOPE})
    if method == "tools/call":
        if "inputResponses" in params and type(params["inputResponses"]) is not dict:
            return _rpc_error(rid, -32602, "inputResponses must be an object")
        if "requestState" in params and type(params["requestState"]) is not str:
            return _rpc_error(rid, -32602, "requestState must be a string")
        if "inputResponses" in params or "requestState" in params:
            return _rpc_error(rid, -32602, "science did not request multi-round input")
        if not isinstance(params.get("name"), str):
            return _rpc_error(rid, -32602, "tool name must be a string")
        if params["name"] not in {d.name for d in decls}:
            # An unknown tool is a PROTOCOL error, not a framework refusal.
            return _rpc_error(rid, -32602, f"unknown tool {params['name']!r}")
        raw_args = params.get("arguments", {})
        if not isinstance(raw_args, dict):
            return _rpc_error(rid, -32602, "arguments must be an object")
        arguments = dict(raw_args)
        cursor = arguments.pop("cursor", None)
        invocation_id = arguments.pop("invocation_id", None)
        for label, value in (("cursor", cursor), ("invocation_id", invocation_id)):
            if value is not None and not isinstance(value, str):
                return _rpc_error(rid, -32602, f"{label} must be a string")
        try:
            out = dispatcher.invoke(params["name"], arguments,
                                    invocation_id=invocation_id, cursor=cursor)
            return _result(rid, {"content": [{"type": "text", "text": out.text}],
                                 "structuredContent": {"invocation_id": out.invocation_id},
                                 "isError": False})
        except Refused as e:
            from science.refusal import envelope
            structured = {"refusal": envelope(e.refusal)}
            if e.invocation_id is not None:
                structured["invocation_id"] = e.invocation_id
            return _result(rid, {"content": [{"type": "text",
                                              "text": f"refused [{e.refusal.code}] {e.refusal.message}"}],
                                 "structuredContent": structured,
                                 "isError": True})
    return {"jsonrpc": "2.0", "id": rid,
            "error": {"code": -32601, "message": f"method not found: {method}"}}


def _result(rid, payload) -> dict:
    payload = {**payload, "resultType": "complete"}  # required on 2026-07-28 results
    return {"jsonrpc": "2.0", "id": rid, "result": payload}


_END_OF_INPUT = object()
_OVERSIZED_FRAME = object()


def _read_frame(stream):
    frame = stream.readline(MAX_REQUEST_BYTES + 2)
    if not isinstance(frame, bytes):
        raise TypeError("MCP stdin must be a binary stream")
    if frame == b"":
        return _END_OF_INPUT
    if frame.endswith(b"\n"):
        return (_OVERSIZED_FRAME
                if len(frame) - 1 > MAX_REQUEST_BYTES else frame[:-1])
    if len(frame) > MAX_REQUEST_BYTES:
        while True:  # bounded drain through this frame's newline
            chunk = stream.readline(65_536)
            if not chunk or chunk.endswith(b"\n"):
                break
        return _OVERSIZED_FRAME
    return frame


def serve(config_path: Path, stdin=None, stdout=None, session=None) -> None:
    from science.config import ReadContext, load_config
    from science.loader import production_tree, resolve_handlers
    stdin = sys.stdin.buffer if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    decls = production_tree()
    dispatcher = Dispatcher(decls, resolve_handlers(decls),
                            ReadContext.open(load_config(config_path)),
                            session=session)  # Task 12 wires the attended session
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
                req = json.loads(
                    frame.decode("utf-8", errors="strict"),
                    object_pairs_hook=_object_without_duplicates,
                    parse_constant=_reject_nonfinite_number,
                )
            except (UnicodeDecodeError, ValueError, RecursionError):
                response = _rpc_error(None, -32700, "Parse error")
            else:
                response = handle_request(req, dispatcher, decls)
        if response is not None:  # notifications are silent
            stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            stdout.flush()
```

In `cli.py`'s `_framework_verb`, add before the fallthrough:

```python
    if ns.command == "mcp":  # Task 9's parser guarantees ns.mode == "serve"
        from science.config import resolve_config_path
        from science.mcp import serve
        serve(resolve_config_path(ns.config))
        return EXIT_OK
```

- [ ] **Step 4: Run the full suite to verify it passes**

Run: `cd python && uv run --group dev pytest -q`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/mcp.py python/src/science/cli.py python/tests/test_mcp.py
git commit -m "feat(mcp): stdio MCP server with CLI transport-equivalence test"
```

### Task 12: Write dispatch — requirements, claims, dedup (beliefs-gated)

**Unblocked 2026-09-09:** `beliefs-96a24a` (permits) and `beliefs-afbbff` (the
writer session) both landed; `beliefs.session` exports every name the pinned
contract below cites. Do not stub or mock the session; the whole point is
exercising the real permit path.

**Files:**
- Modify: `python/src/science/config.py` (the `domains` key and the compiled `ScienceConfig.profile`; added 2026-09-09 with the required `profile` keyword)
- Modify: `python/src/science/dispatch.py`
- Modify: `python/src/science/loader.py` (`production_kind_acts` exact import)
- Modify: `python/src/science/mcp.py` (open the attended session)
- Modify: `python/tests/helpers/world.py` (Step 0's fixture-world repair)
- Create: `python/tests/helpers/synthetic.py` (synthetic declarations + handlers, shared with Task 13)
- Test: `python/tests/test_write_dispatch.py`

**Interfaces:**
- Consumes — **the pinned companion contract.** These names are shared with
  the beliefs writer-session task (`beliefs-afbbff`, which cites this
  block) and beliefs implements exactly them. They are not a sketch to
  reconcile: if implementation there forces a change, that is a change
  request against both documents, made before either side codes on, never
  a local adjustment here:
  - `beliefs.permit.RequiredCapabilities` with `.none()`, `.coordination()`, `.for_kinds(kinds: Iterable[str], routes: Mapping[str, str])`, `.publishes()`
  - `beliefs.permit.WritePermit` carries a third dimension, `ungoverned` (spec §4.1 amendment of 2026-09-04); `RequiredCapabilities` never sets it and `science` never reads it
  - `beliefs.permit.PermitExceeded(WriteRefused)` with `.requirement` and `.capability` attributes
  - `beliefs.session.open_attended_session(world_config, operations_root, *, profile: ProfileSpec, coordination: ProfileSpec | None = None) -> WriterSession` — **changed 2026-09-05 by the beliefs writer-session design §3.1, decision 12**: the launcher supplies the compiled coordination profile for coordination-class commands; without it those commands refuse `CoordinationUnavailable` at the act. **Changed again 2026-09-09 by that design's integration amendment of 2026-09-07**: `profile`, the compiled `ProfileSpec` the session's writer and durable operation port bind, is **required**, and `beliefs.root.open_corpus` requires it alike. No profile is inferred from a manifest or from `coordination`. Spec §9.1's launcher configuration answers with a `domains` key, compiled at config load into `ScienceConfig.profile`; this task passes `coordination=None`, since the shipped base declares no coordination kinds and no coordination-class command exists in `commands/`. A world config naming other than exactly one corpus root raises `SessionRefused` at open — a launcher misconfiguration, left to propagate, never folded into a `Refusal`
  - `WriterSession.scoped(required, invocation_id) -> ScopedWriter` — **changed 2026-09-05 by the beliefs writer-session design §5, decision 12**: the writer is bound to the invocation id the dispatcher has already minted, and acts only while that invocation is the current one (raises `PermitExceeded` when the requirement exceeds the session permit — the declaration-time refusal)
  - **Note (2026-09-05, discharged):** `tests/helpers/world.py` called `open_corpus(corpus_root)` and `world.admit(..., actor="fixture")` without an `Authority`; beliefs cut 17 removed both forms. The `Authority` half landed before this task began.
  - **Note (2026-09-09):** the same helper still fails against beliefs cut 22 — `open_corpus` now requires `profile`, and the helper adopts fabricated pins (`"science:" + "a" * 64`) that `require_pins_agree` rejects. Fifteen tests are red on `main` for this reason. **Step 0** repairs it before any write test is written; that is what makes Step 2's red result meaningful.
  - **Note (2026-09-05):** a `delete`-class command, if ever declared, renders an empty canonical report — its `act` line carries no minted identities (beliefs writer-session design §8 item 8).
  - `WriterSession.session_id: str` (32 hex), `WriterSession.actor: str`
  - `WriterSession.close() -> None` — appends the ledger's `session-close` line (spec §5.2); idempotent, and every endpoint calls it in a `finally`
  - `WriterSession.claim_invocation(invocation_id, command, input_digest) -> Claim` where `Claim` is the closed union `ClaimFresh | ClaimDone(outcome) | ClaimOpen | ClaimMismatch` — importable types, matched exhaustively, anything else a hard error (fail closed, never fall through to execution)
  - `beliefs.session.KernelRefusalValue(value)` — the exception a `ScopedWriter` raises to carry a **value-style** kernel refusal (`RunRefused`, `AdmissionRefused`, …): a scoped writer never returns a refusal value, so the dispatcher has exactly one normalization path; the wrapped value exposes `.reason`
  - `WriterSession.close_invocation(invocation_id, outcome)` where outcome is `{"done": [[uid, id], …]}` or `{"refusal": {code, message, data}}` — the persisted envelope of spec §5.2
  - `WriterSession.invocation_acts(invocation_id) -> tuple[ActLine, ...]` with `ActLine.record_ids: tuple[tuple[str, str], ...]` — `(uid, id)` pairs
  - `beliefs.session.open_ledger_reader(operations_root, session_id) -> LedgerReader` with `LedgerReader.invocation(invocation_id) -> InvocationRecord | None` carrying `.command`, `.acts` (as above) and `.outcome` — the accessor write continuation resolves cursors through, and `.command` is what binds a cursor to its command
  - `ScopedWriter` mirroring the `CorpusWriter` write methods, permit-checked per act
- Produces: the write branch of `Dispatcher.invoke` (spec §6.1 steps 3–7 for writes, §6.2 dedup under one `threading.Lock`, §7.4 audit via `audit_write_report`); **completion ordering** (spec §6.1/§5.2, ruled here): handler → collect minted `(uid, id)` pairs from the session's acts → `audit_write_report` → `close_invocation` → render → return. The ledger records act truth, never rendering success: an audit violation still closes `done` with the minted pairs (the acts committed) and then raises `AuditViolation` as an internal error — the caller sees exit 1, never the echoed report, and a dedup retry replays canonically from the ledger. A handler refusal closes with the persisted refusal envelope, in that order, before re-raising as `Refused`. Write-cursor continuation resolves the ledger via `open_ledger_reader`, re-renders from the ledger's `(uid, id)` pairs only, and never calls the write handler or canonicalizes inputs. Refusal translation is one function, `_kernel_refusal`: `PermitExceeded` → `permit-exceeded` with requirement/capability data, `KernelRefusalValue` → `kernel-refused` with the value's type name and `.reason` in `data`, other `WriteRefused` → `kernel-refused` with the subclass name in `data`; every write-path `Refused` carries the invocation id. Write handler signature: `handle(ctx, writer, **inputs) -> Report`; the handler's report is audited, but **what renders — on the first response as much as on replay — is the canonical ledger-rebuilt report** (`_minted_report`), so authored kind/title text around a real identity pair has no path to the caller.

**Deviations the implementation took from the code blocks below** (recorded
2026-09-09; the Consumes block above is the pinned contract, these blocks are
not):

- Test imports are `from helpers.…`, not `from tests.helpers.…`. There is no
  `tests/__init__.py`; every existing module in this suite imports the helper
  package the first way.
- `close_invocation` takes `{"done": [[uid, id], …]}` — the ledger's
  `validated_outcome` requires *lists*, and refuses a list of tuples with
  `a done outcome must be a list of [uid, id] string pairs`.
- `mcp.serve` loses its `session=` injection parameter rather than keeping it
  alongside the real session. Task 11's
  `test_serve_passes_session_only_as_dispatcher_injection` was the placeholder
  for this task and is replaced by
  `test_serve_holds_one_attended_session_and_closes_it`, which asserts the
  32-hex session id, the derived actor, and the `session-close` ledger line.
- Removing `production_tree`'s fail-closed gate invalidates Task 8's
  `test_production_tree_rejects_every_write_class_until_capabilities_land` and
  Task 11's `test_write_paths_are_explicitly_deferred`. Both assert the
  temporary behavior this task retires, so both are replaced by tests of the
  behavior that succeeds it: the tree now admits every write class,
  `production_kind_acts()` equals `beliefs.permit.KIND_ACTS` exactly, and a
  write on a sessionless surface refuses `permit-exceeded` before its handler.

- [x] **Step 0: Repair the fixture world and add the `domains` key**

Fifteen tests are red on `main` because beliefs cut 22 made `profile` required
on `open_corpus`. Nothing below can produce a meaningful red result until they
are green, so this step lands first and its verification is those fifteen
tests, not a new one.

In `python/src/science/config.py`: add `domains` to `_KEYS`, validate it as a
list of strings, and compile the profile at load —
`compile_profile(shipped_base_contract(), [shipped_domain_contract(ns) for ns
in raw["domains"]])` — reporting `ProfileError` as `invalid-input`. Carry the
result on `ScienceConfig.profile`.

In `python/tests/helpers/world.py`: compile the same profile over the shipped
`biology` pack, derive `PINS` from it (`science:<base_contract_identity>` and
`biology:<activated identity>`) in place of the fabricated constants, pass
`profile=` to both `open_corpus` calls, return `ScienceConfig(…,
profile=PROFILE)`, and emit `domains = ["biology"]` from `write_cli_config`.

Run: `cd python && uv run --group dev pytest -q`
Expected: PASS — the fifteen `TypeError: open_corpus() missing 1 required
keyword-only argument: 'profile'` failures are gone and nothing else moved.

- [x] **Step 1: Write the shared synthetic module, then the failing tests**

`python/tests/helpers/synthetic.py` — the one definition of the synthetic
declarations and handlers; Task 13 extends this module with the
fixture-tree loader. Real contract kinds only: `proposition` is the
simplest mintable kind (Task 8's fixture already writes them); `source` is
the foreign kind the lying handler reaches for:

```python
from pathlib import Path

from science.cursor import MIN_OUTPUT_BUDGET
from science.report import Text, record_block
from science.schema import Declaration, InputSpec, WriteClass

from tests.helpers.world import fixture_proposition_node, fixture_source_node

MINT_CLAIM = Declaration("mint-claim", "fixture",
                         WriteClass("mints", ("proposition",), {"proposition": "corpus-write"}),
                         MIN_OUTPUT_BUDGET, (InputSpec("slug", "string", True, "d"),), (), Path("."))
OVERREACH = Declaration("overreach", "fixture",
                        WriteClass("mints", ("proposition",), {"proposition": "corpus-write"}),
                        MIN_OUTPUT_BUDGET, (), (), Path("."))


def mint_claim_handler(ctx, writer, *, slug):
    node = writer.add(fixture_proposition_node(slug))
    return (record_block(node),)


def overreach_handler(ctx, writer):
    # The body lies: declared proposition, mints a source -> act-time PermitExceeded.
    writer.add(fixture_source_node("sneaky"))
    return (Text("never rendered"),)


def echoing_handler(ctx, writer, *, slug):
    writer.add(fixture_proposition_node(slug))
    return (Text("audit echo!"),)  # non-record block in a write report


def forging_handler(ctx, writer, *, slug):
    from science.report import RecordBlock
    node = writer.add(fixture_proposition_node(slug))
    # A real (uid, id) pair wearing authored kind/title: passes the audit's
    # identity check, but the canonical render must not show it.
    return (RecordBlock(node.uid, node.id, "verification", "FORGED TITLE"),)


HANDLERS = {"mint-claim": mint_claim_handler, "overreach": overreach_handler}
```

`python/tests/test_write_dispatch.py` — runs against a real attended
session over the fixture world; handler injection is the fixture path,
production resolution stays convention-bound:

```python
import threading

import pytest

from science.dispatch import Dispatcher
from science.cursor import MIN_OUTPUT_BUDGET
from science.refusal import Refused
from science.schema import Declaration
from pathlib import Path
from tests.helpers.synthetic import (
    HANDLERS, MINT_CLAIM, OVERREACH, echoing_handler, forging_handler,
)
from tests.helpers.world import build_fixture_world


@pytest.fixture
def rig(certified_work):
    from beliefs.session import open_attended_session
    from science.config import ReadContext
    cfg = build_fixture_world(certified_work)
    session = open_attended_session(cfg.world, cfg.operations_root, profile=cfg.profile)
    dispatcher = Dispatcher((MINT_CLAIM, OVERREACH), dict(HANDLERS),
                            ReadContext.open(cfg), session=session)
    try:
        yield dispatcher, session
    finally:
        session.close()  # the session-close ledger line, exercised every test


def test_write_returns_only_its_record(rig):
    d, _ = rig
    out = d.invoke("mint-claim", {"slug": "hello"})
    assert "proposition:hello" in out.text and "audit echo" not in out.text


def test_act_time_refusal_when_body_exceeds_declaration(rig):
    d, _ = rig
    with pytest.raises(Refused) as e:
        d.invoke("overreach", {})
    # The contract is exact: exceeding the invocation-scoped permit is
    # permit-exceeded, never a generic kernel refusal.
    assert e.value.refusal.code == "permit-exceeded"


def test_dedup_replays_without_reexecution(rig):
    d, session = rig
    first = d.invoke("mint-claim", {"slug": "once"}, invocation_id="A" * 8)
    again = d.invoke("mint-claim", {"slug": "once"}, invocation_id="A" * 8)
    assert first.text == again.text
    assert len(session.invocation_acts("A" * 8)) == 1  # one act, not two


def test_id_reuse_with_different_payload_refused(rig):
    d, _ = rig
    d.invoke("mint-claim", {"slug": "x"}, invocation_id="B" * 8)
    with pytest.raises(Refused) as e:
        d.invoke("mint-claim", {"slug": "y"}, invocation_id="B" * 8)
    assert e.value.refusal.code == "input-mismatch"


def test_concurrent_same_id_executes_once(rig):
    d, session = rig
    results, errors = [], []

    def call():
        try:
            results.append(d.invoke("mint-claim", {"slug": "race"}, invocation_id="C" * 8))
        except Refused as e:
            errors.append(e)

    threads = [threading.Thread(target=call) for _ in range(8)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert len(session.invocation_acts("C" * 8)) == 1
    # All eight succeed identically: one executes, seven replay canonically.
    assert not errors and len(results) == 8
    assert len({r.text for r in results}) == 1
    assert {r.invocation_id for r in results} == {"C" * 8}


def test_audit_echo_is_unrepresentable_and_ledger_stays_true(rig):
    from science.render import AuditViolation
    d, session = rig
    d._handlers["mint-claim"] = echoing_handler
    with pytest.raises(AuditViolation):  # internal error; the echo is never rendered
        d.invoke("mint-claim", {"slug": "z"}, invocation_id="E" * 8)
    # The acts committed, so the ledger closed `done` — and a dedup retry
    # replays canonically from the ledger, bypassing the echoing handler.
    replay = d.invoke("mint-claim", {"slug": "z"}, invocation_id="E" * 8)
    assert "audit echo" not in replay.text and "proposition:z" in replay.text


def test_refusal_replay_is_exact(rig):
    d, session = rig
    with pytest.raises(Refused) as first:
        d.invoke("overreach", {}, invocation_id="F" * 8)
    acts_after_first = len(session.invocation_acts("F" * 8))
    with pytest.raises(Refused) as again:
        d.invoke("overreach", {}, invocation_id="F" * 8)
    # Code, message, data, AND the invocation id all survive replay.
    assert again.value.refusal.code == first.value.refusal.code
    assert again.value.refusal.message == first.value.refusal.message
    assert dict(again.value.refusal.data) == dict(first.value.refusal.data)
    assert first.value.invocation_id == again.value.invocation_id == "F" * 8
    assert len(session.invocation_acts("F" * 8)) == acts_after_first  # not re-executed


def test_value_style_kernel_refusal_normalizes(rig):
    from beliefs.session import KernelRefusalValue
    d, _ = rig

    class FakeRunRefused:
        reason = "recipe-mismatch: fixture"

    def value_refusing_handler(ctx, writer, *, slug):
        raise KernelRefusalValue(FakeRunRefused())

    d._handlers["mint-claim"] = value_refusing_handler
    with pytest.raises(Refused) as e:
        d.invoke("mint-claim", {"slug": "v"}, invocation_id="H" * 8)
    assert e.value.refusal.code == "kernel-refused"
    assert e.value.refusal.data["kind"] == "FakeRunRefused"
    assert "recipe-mismatch" in e.value.refusal.data["reason"]
    assert e.value.invocation_id == "H" * 8


def test_forged_kind_and_title_never_render(rig):
    d, _ = rig
    d._handlers["mint-claim"] = forging_handler
    out = d.invoke("mint-claim", {"slug": "forge"})
    # The identity pair is real, so the audit passes — but the canonical
    # ledger-rebuilt render shows the record's true kind and title.
    assert "FORGED TITLE" not in out.text and "verification" not in out.text
    assert "[proposition] proposition:forge" in out.text


def test_unknown_claim_type_fails_closed(rig, monkeypatch):
    """A claim outside the closed union must never execute as fresh."""
    d, session = rig
    monkeypatch.setattr(session, "claim_invocation", lambda *a, **k: object())
    with pytest.raises(TypeError):
        d.invoke("mint-claim", {"slug": "never"}, invocation_id="M" * 8)
    assert len(session.invocation_acts("M" * 8)) == 0  # nothing was written


def test_write_cursor_bound_to_its_command(rig):
    d, _ = rig
    small = Declaration("mint-claim", "fixture", MINT_CLAIM.write_class,
                        MIN_OUTPUT_BUDGET, MINT_CLAIM.inputs, (), Path("."))
    d._decls["mint-claim"] = small
    first = d.invoke("mint-claim", {"slug": "long-" + "n" * 200}, invocation_id="J" * 8)
    cursor = first.text.rsplit("cursor ", 1)[1].strip()
    with pytest.raises(Refused) as e:
        d.invoke("overreach", {}, cursor=cursor)  # a different command
    assert e.value.refusal.code == "input-mismatch"


def test_open_invocation_refuses_outcome_unknown(rig):
    d, session = rig
    # Simulate a crashed prior attempt: claimed and opened, never closed.
    from science.canonical import canonicalize, input_digest
    digest = input_digest(canonicalize(MINT_CLAIM, {"slug": "crashed"}))
    session.claim_invocation("G" * 8, "mint-claim", digest)
    with pytest.raises(Refused) as e:
        d.invoke("mint-claim", {"slug": "crashed"}, invocation_id="G" * 8)
    assert e.value.refusal.code == "outcome-unknown"


def test_write_cursor_rerenders_without_handler(rig):
    d, session = rig
    # A tiny declared budget forces truncation of even one record block.
    small = Declaration("mint-claim", "fixture", MINT_CLAIM.write_class,
                        MIN_OUTPUT_BUDGET, MINT_CLAIM.inputs, (), Path("."))
    d._decls["mint-claim"] = small
    first = d.invoke("mint-claim", {"slug": "long-" + "n" * 200}, invocation_id="D" * 8)
    assert "cursor" in first.text
    cursor = first.text.rsplit("cursor ", 1)[1].strip()
    d._handlers["mint-claim"] = lambda *a, **k: pytest.fail("write handler must not run on continuation")
    second = d.invoke("mint-claim", {}, cursor=cursor)
    assert second.text
```

(`fixture_proposition_node` and `fixture_source_node` are Task 8's helpers;
slugs must fit beliefs' slug rules, so keep them short lowercase-hyphen
strings.)

- [x] **Step 2: Run tests to verify they fail**

Run: `cd python && uv run --group dev pytest tests/test_write_dispatch.py -q`
Expected: FAIL — `NotImplementedError` from the read-only dispatcher (or `ImportError` if beliefs has not landed; in that case this task is not startable yet).

- [x] **Step 3: Implement the write branch in `dispatch.py`**

Three exact replacements, then the new methods. First, `Dispatcher.__init__`
in full (the lock is the only addition; add `import threading` at the top
of `dispatch.py`):

```python
    def __init__(self, declarations, handlers: Mapping[str, Callable],
                 read_context, session=None) -> None:
        self._decls = {d.name: d for d in declarations}
        self._handlers = dict(handlers)
        self._ctx = read_context
        self._session = session
        self._lock = threading.Lock()  # serializes write-class steps 4-7
```

Second, in `invoke`, replace the `NotImplementedError` write line — this is
what actually routes writes, and `iid` is already minted above it:

```python
            if decl.write_class.kind != "read-only":
                return self._invoke_write(decl, canonical, iid)
```

Third, the write arm of `_continue` (below). Then add the write-branch
methods:

```python
    def _required(self, decl: Declaration):
        from beliefs.permit import RequiredCapabilities
        wc = decl.write_class
        match wc.kind:
            case "read-only":
                return RequiredCapabilities.none()
            case "coordination":
                return RequiredCapabilities.coordination()
            case "mints":
                return RequiredCapabilities.for_kinds(wc.kinds, wc.routes)
            case "publishes":
                return RequiredCapabilities.publishes()
        raise AssertionError(wc.kind)

    @staticmethod
    def _kernel_refusal(e) -> Refusal:
        """The one normalization path for every kernel refusal shape."""
        from beliefs.permit import PermitExceeded
        from beliefs.session import KernelRefusalValue
        if isinstance(e, PermitExceeded):
            return Refusal("permit-exceeded", str(e),
                           {"requirement": str(e.requirement), "capability": str(e.capability)})
        if isinstance(e, KernelRefusalValue):
            value = e.value
            return Refusal("kernel-refused", str(value.reason),
                           {"kind": type(value).__name__, "reason": str(value.reason)})
        return Refusal("kernel-refused", str(e), {"kind": type(e).__name__})

    def _invoke_write(self, decl, canonical, iid: str):
        from beliefs.permit import PermitExceeded
        from beliefs.errors import WriteRefused
        from beliefs.session import (
            ClaimDone, ClaimFresh, ClaimMismatch, ClaimOpen, KernelRefusalValue,
        )
        from science.render import audit_write_report
        # iid was minted at the top of `invoke`; every refusal here names it.
        if self._session is None:
            raise Refused(Refusal("permit-exceeded",
                                  "no writer session on this surface"), iid)
        try:
            writer = self._session.scoped(self._required(decl), iid)
        except PermitExceeded as e:
            raise Refused(self._kernel_refusal(e), iid)
        with self._lock:
            claim = self._session.claim_invocation(iid, decl.name, input_digest(canonical))
            if isinstance(claim, ClaimDone):
                return Outcome(self._replay_outcome(decl, claim.outcome, iid, (0, 0)), iid)
            if isinstance(claim, ClaimOpen):
                raise Refused(Refusal("outcome-unknown",
                                      "a prior attempt is open; its outcome is unknown"), iid)
            if isinstance(claim, ClaimMismatch):
                raise Refused(Refusal("input-mismatch",
                                      "invocation_id was used with a different payload"), iid)
            if not isinstance(claim, ClaimFresh):  # fail closed, never execute
                raise TypeError(f"unknown claim type from the session: {claim!r}")
            try:
                report = self._handlers[decl.name](self._ctx, writer, **canonical)
            except (PermitExceeded, KernelRefusalValue, WriteRefused) as e:
                return self._close_refused(iid, self._kernel_refusal(e))
            minted = frozenset(
                tuple(pair) for act in self._session.invocation_acts(iid)
                for pair in act.record_ids)
            try:
                audit_write_report(report, minted)
            finally:
                # Close FIRST in every case: the ledger records act truth, and
                # the acts committed whether or not the report survives audit.
                self._session.close_invocation(iid, {"done": sorted(minted)})
            # An AuditViolation has propagated past the close above as an
            # internal error; the echoed report is never rendered. Even on
            # success the handler's report is only the audited *claim* — what
            # renders is the canonical ledger-rebuilt report, first response
            # and replay alike, so authored text around a real identity pair
            # has no path out (spec §7.4).
            canonical_report = self._minted_report(sorted(minted))
            return Outcome(self._render_write(decl.output_budget, canonical_report,
                                              iid, (0, 0)), iid)

    def _close_refused(self, iid, refusal: Refusal):
        from science.refusal import envelope
        self._session.close_invocation(iid, {"refusal": envelope(refusal)})
        raise Refused(refusal, iid)

    def _render_write(self, budget: int, report, iid: str,
                      position: tuple[int, int]) -> str:
        def cursor_for(pos, rdigest):
            return encode(WriteCursor(self._session.session_id, iid, rdigest,
                                      pos[0], pos[1]))
        return render_page(report, budget=budget, position=position,
                           cursor_for=cursor_for).text

    def _minted_report(self, pairs) -> Report:
        """The canonical write report: record blocks rebuilt from ledger pairs."""
        from science.report import record_block
        blocks = []
        for uid, record_id in pairs:
            node = self._ctx.load_record(uid, record_id)  # read-path lookup; see below
            blocks.append(record_block(node))
        return tuple(blocks)

    def _replay_outcome(self, decl, outcome: dict, iid: str,
                        position: tuple[int, int]) -> str:
        if "refusal" in outcome:
            r = outcome["refusal"]
            raise Refused(Refusal(r["code"], r["message"], r.get("data", {})), iid)
        report = self._minted_report(outcome["done"])
        return self._render_write(decl.output_budget, report, iid, position)
```

The write arm of `_continue` (replacing its `NotImplementedError`) — never a
handler call, never canonicalization:

```python
        if isinstance(cur, WriteCursor):
            from beliefs.session import open_ledger_reader
            decl = self._decls.get(command)
            if decl is None:
                raise Refused(Refusal("unknown-command", f"no command {command!r}"))
            operations_root = self._ctx.config.operations_root
            try:
                reader = open_ledger_reader(operations_root, cur.session_id)
            except FileNotFoundError:
                raise Refused(Refusal("unknown-cursor", "no such session ledger"))
            record = reader.invocation(cur.invocation_id)
            if record is None:
                raise Refused(Refusal("unknown-cursor", "no such invocation in that session"))
            if record.command != command:  # the cursor is bound to its command
                raise Refused(Refusal("input-mismatch",
                                      "cursor was issued for a different command"))
            if "refusal" in record.outcome:
                raise Refused(Refusal("unknown-cursor",
                                      "that invocation refused; nothing to page"))
            report = self._minted_report(record.outcome["done"])
            from science.render import report_digest as fresh_digest
            if fresh_digest(report) != cur.report_digest:
                raise Refused(Refusal("stale-cursor", "the records changed; re-run"))
            self._check_position(report, cur.block, cur.offset)
            page = render_page(report, budget=decl.output_budget,
                               position=(cur.block, cur.offset),
                               cursor_for=lambda pos, rd: encode(
                                   WriteCursor(cur.session_id, cur.invocation_id, rd,
                                               pos[0], pos[1])))
            return Outcome(page.text, iid)
```

`_render_write` uses the canonical report's digest exactly as the read
path does, so replayed pages and first-render pages share cursors.

Then two exact companion edits. In `loader.py`, replace the body of
`production_kind_acts`:

```python
def production_kind_acts() -> dict[str, frozenset[str]]:
    from beliefs.permit import KIND_ACTS  # exact import; no fallback
    return dict(KIND_ACTS)
```

In the same edit, remove Task 8's temporary `read-only` loop from
`production_tree()`. That gate is replaced only after this exact import and
the real write dispatcher exist; until Task 12 begins it remains fail-closed.

In `mcp.py`, retain Task 11's `_drain_frame`, `_read_frame`, strict UTF-8
decoder hooks, bounded binary loop, oversized-frame drain, parse-error
normalization, and notification `None` suppression unchanged. Change only
session construction/ownership: the MCP server opens one attended session for
its process lifetime and closes it in `finally` (the CLI's service process is
created, already session-bearing, in Task 13). The exact resulting function is:

```python
def serve(config_path: Path, stdin=None, stdout=None) -> None:
    from beliefs.session import open_attended_session
    from science.config import ReadContext, load_config
    from science.loader import production_tree, resolve_handlers

    stdin = sys.stdin.buffer if stdin is None else stdin
    stdout = sys.stdout if stdout is None else stdout
    declarations = production_tree()
    config = load_config(config_path)
    session = open_attended_session(config.world, config.operations_root, profile=config.profile)
    try:
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
```

- [x] **Step 4: Run the full suite to verify it passes**

Run: `cd python && uv run --group dev pytest -q`
Expected: PASS, including every earlier task's tests.

- [x] **Step 5: Commit**

```bash
git add python/src/science/dispatch.py python/src/science/loader.py \
        python/src/science/mcp.py python/tests/helpers/synthetic.py \
        python/tests/test_write_dispatch.py
git commit -m "feat(dispatch): write dispatch with scoped permits, atomic claims, and dedup"
```

### Task 13: Service process, CLI write routing, synthetic exemplars end-to-end (beliefs-gated)

**Unblocked 2026-09-09 with Task 12**, which landed the write branch this
task routes to.

**Files:**
- Create: `python/src/science/serve.py`
- Modify: `python/src/science/cli.py` (register the `serve` verb here, not
  earlier; implement `_via_service`)
- Modify: `python/src/science/dispatch.py` (the `publishes` refusal; added 2026-09-09, see below)
- Create: `python/tests/fixtures/commands/` (synthetic declarations: `mint-claim/`, `overreach/`, `coord-note/`, `pub-view/` — each a real `command.toml` + one-line `prompt.md`)
- Modify: `python/tests/helpers/synthetic.py` (add the fixture-tree loader; Task 12 created the module)
- Test: `python/tests/test_serve.py`, `python/tests/test_synthetic_tree.py`

**Correction to Task 12, carried here (2026-09-09).** Step 1's
`test_declaration_time_refusal_for_class_above_permit` reaches a path Task 12
shipped untested. `beliefs.permit.RequiredCapabilities.publishes()` does not
return an uncoverable requirement — it raises
`ValueError("publish is not an act family")`, because `ACT_FAMILIES` holds no
`publish` and will not until sub-project 5 (spec §4.1, §4.4). The note below —
that a `publishes` requirement always exceeds an attended session's permit —
reaches the right verdict by the wrong route: the requirement cannot be
constructed at all, so `Dispatcher._required` raises a bare `ValueError` and
the CLI reports exit 1 and `Internal error` instead of exit 3 and a
`permit-exceeded` envelope.

`_required`'s `publishes` arm therefore states the condition rather than
discovering it from an exception:

```python
            case "publishes":
                # The publish act family arrives with sub-project 5 (spec
                # §4.1, §4.4); until then the requirement is unconstructable,
                # so the class refuses at declaration time. `invoke`'s outer
                # handler binds the invocation id.
                raise Refused(Refusal(
                    "permit-exceeded",
                    "publishes commands need the publish act family, "
                    "which arrives with sub-project 5"))
```

`none()`, `coordination()` and `for_kinds()` are unaffected: each returns a
requirement, and a full permit covers all three.

**Interfaces:**
- Consumes: `Dispatcher` with write branch (Task 12); `open_attended_session` (beliefs); `Refusal/Refused`, `production_tree`.
- Produces: `serve(config: ScienceConfig, socket_path: Path, declarations=None, handlers=None) -> Server` — a Unix-socket JSON-lines service holding one attended session for its lifetime; `declarations`/`handlers` default to the production tree and are injection points for tests (production code never imports test modules); a socket path that already exists **refuses at startup** with a message naming the path — never a silent unlink (a stale socket from a crash is the operator's to remove); wire protocol: request `{"command": str, "inputs": {…}, "invocation_id": str | null, "cursor": str | null}`, response `{"ok": true, "text": str, "invocation_id": str}` or `{"ok": false, "refusal": {code, message, data}}`; socket at `<operations_root>/service.sock`. This task adds `science serve --config …` to `build_parser`; no earlier task registers it. `_via_service` connects for any write-class command while preserving Task 9's public wire: rendered text only on stdout and exactly one compact, key-sorted JSON stderr line—`{"invocation_id":"…"}` on success or `{"invocation_id":"…","refusal":{"code":"…","data":{},"message":"…"}}` on refusal. Missing service is a full `permit-exceeded` envelope naming `science serve`, never a plain ad-hoc line. **Landing step:** update this repo's README and the spec's Status header to implemented in the same commit; the README already records the Tasks 1–11 read path, so this replaces its beliefs-gated sentence rather than an obsolete “nothing built” sentence.

- [x] **Step 1: Write the synthetic declarations**

All four, in full. Each directory also gets a one-line `prompt.md`:
`Test fixture; never shipped.`

`python/tests/fixtures/commands/mint-claim/command.toml`:

```toml
schema_version = 1
name = "mint-claim"
purpose = "Synthetic write exemplar."
write_class = "mints:proposition"
output_budget = 4096
[inputs.slug]
type = "string"
required = true
doc = "Slug of the proposition."
```

`python/tests/fixtures/commands/overreach/command.toml`:

```toml
schema_version = 1
name = "overreach"
purpose = "Synthetic exemplar whose body exceeds its declaration."
write_class = "mints:proposition"
output_budget = 4096
```

`python/tests/fixtures/commands/coord-note/command.toml`:

```toml
schema_version = 1
name = "coord-note"
purpose = "Synthetic coordination exemplar; schema and dispatch shape only."
write_class = "coordination"
output_budget = 4096
[inputs.text]
type = "string"
required = true
doc = "Note text."
```

`python/tests/fixtures/commands/pub-view/command.toml`:

```toml
schema_version = 1
name = "pub-view"
purpose = "Synthetic publish exemplar; schema and dispatch shape only."
write_class = "publishes"
output_budget = 4096
```

Then extend `python/tests/helpers/synthetic.py` with the tree loader:

```python
def synthetic_decls_and_handlers():
    from science.schema import load_command_tree
    root = Path(__file__).parents[1] / "fixtures" / "commands"
    kind_acts = {"proposition": frozenset({"corpus-write"})}
    decls = load_command_tree(root, kind_acts=kind_acts,
                              contract_kinds=frozenset(kind_acts))
    def unreachable(ctx, writer, **inputs):
        raise AssertionError("dispatch must refuse before this handler runs")
    handlers = dict(HANDLERS)
    handlers["coord-note"] = unreachable  # no coordination contract yet
    handlers["pub-view"] = unreachable    # no publish act family yet
    return decls, handlers
```

`python/tests/test_synthetic_tree.py` proves the tree loads and classifies (schema + dispatch shape for `coordination` and `publishes`, which cannot act until sub-projects 1 and 5):

```python
import pytest

from science.schema import load_command_tree

KIND_ACTS = {"proposition": frozenset({"corpus-write"})}


def test_synthetic_tree_loads():
    from pathlib import Path
    root = Path(__file__).parent / "fixtures" / "commands"
    decls = load_command_tree(root, kind_acts=KIND_ACTS, contract_kinds=frozenset(KIND_ACTS))
    by_name = {d.name: d for d in decls}
    assert by_name["coord-note"].write_class.kind == "coordination"
    assert by_name["pub-view"].write_class.kind == "publishes"
    assert by_name["mint-claim"].write_class.routes == {"proposition": "corpus-write"}


def test_declaration_time_refusal_for_class_above_permit(certified_work):
    """A publishes-class command against an attended session without the publish
    family refuses before the handler runs (spec §6.1 step 3)."""
    from beliefs.session import open_attended_session
    from science.config import ReadContext
    from science.dispatch import Dispatcher
    from science.refusal import Refused
    from tests.helpers.world import build_fixture_world
    from pathlib import Path
    root = Path(__file__).parent / "fixtures" / "commands"
    decls = load_command_tree(root, kind_acts=KIND_ACTS, contract_kinds=frozenset(KIND_ACTS))
    cfg = build_fixture_world(certified_work)
    session = open_attended_session(cfg.world, cfg.operations_root, profile=cfg.profile)
    d = Dispatcher(decls, {"pub-view": lambda ctx, writer: ()}, ReadContext.open(cfg), session=session)
    try:
        with pytest.raises(Refused) as e:
            d.invoke("pub-view", {})
        assert e.value.refusal.code == "permit-exceeded"
    finally:
        session.close()
```

(This refusal is deterministic, not conditional: the act-family enumeration
gains `publish` only when sub-project 5 lands — spec §4.1 — so today's
`WritePermit.full()` cannot contain it, and a `publishes` requirement
always exceeds an attended session's permit at declaration time.
**Corrected 2026-09-09:** the verdict holds but the route does not — beliefs
refuses to *construct* the requirement rather than returning one no permit
covers, so the dispatcher must state the refusal itself. See the correction
under this task's file list.)

**Deviations the implementation took (2026-09-09).**

- `serve()` refuses an over-long socket path before opening the session.
  `<operations_root>/service.sock` is 117 bytes from a worktree checkout and
  the AF_UNIX limit is 107, so `bind` dies with a bare
  `OSError: AF_UNIX path too long` naming neither the path nor the limit — a
  reachable misconfiguration, not just a test artifact. Step 2's
  `test_bind_failure_closes_the_session` used that OSError to force a
  post-session failure; it is replaced by two tests, one for the new refusal
  (before the session, nothing in the ledger) and
  `test_setup_failure_after_the_session_opens_closes_it`, which makes the
  socket's parent a regular file so the parent `mkdir` raises after the
  session opened. Tests bind under `tmp_path` for the same reason.
- The `Server` sets `daemon_threads = True`. Without it `server_close` joins
  every handler thread, and a handler blocks in its read loop for as long as
  its client holds the connection — so one idle client wedges shutdown, and
  `_framework_verb`'s `finally: server.server_close()` would hang on Ctrl-C.
  Killing an in-flight write at shutdown is already a designed-for state: the
  invocation stays claimed and unclosed and a retry replays `outcome-unknown`.
- The ledger's line-kind field is `line`, not `type`, so the session-close
  assertions read `last["line"]`.
- Task 11's `test_protocol_options_are_scoped_to_the_verbs_that_consume_them`
  asserted bare `serve` exits 2 as an unknown verb. This task registers it, so
  that case is replaced by the same test's real intent for the new verb:
  `serve --config` parses, and `serve` rejects `--invocation-id`/`--continue`.

- [x] **Step 2: Write the failing service tests**

`python/tests/test_serve.py`:

```python
import json
import socket
import threading

import pytest

from science.serve import serve
from tests.helpers.world import build_fixture_world


def test_service_round_trip_and_cli_routing(certified_work):
    from tests.helpers.synthetic import synthetic_decls_and_handlers
    cfg = build_fixture_world(certified_work)
    decls, handlers = synthetic_decls_and_handlers()
    sock_path = cfg.operations_root / "service.sock"
    server = serve(cfg, sock_path, declarations=decls, handlers=handlers)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        with socket.socket(socket.AF_UNIX) as s:
            s.connect(str(sock_path))
            s.sendall(json.dumps({"command": "mint-claim", "inputs": {"slug": "hi"},
                                  "invocation_id": None, "cursor": None}).encode() + b"\n")
            reply = json.loads(s.makefile().readline())
        assert reply["ok"] and "proposition:hi" in reply["text"]
        assert len(reply["invocation_id"]) == 32
    finally:
        server.shutdown()
        server.server_close()


def _ask(sock_path, payload):
    with socket.socket(socket.AF_UNIX) as s:
        s.connect(str(sock_path))
        s.sendall(json.dumps(payload).encode() + b"\n")
        return json.loads(s.makefile().readline())


def test_service_refusal_carries_envelope_and_replays(certified_work):
    from tests.helpers.synthetic import synthetic_decls_and_handlers
    cfg = build_fixture_world(certified_work)
    decls, handlers = synthetic_decls_and_handlers()
    sock_path = cfg.operations_root / "service.sock"
    server = serve(cfg, sock_path, declarations=decls, handlers=handlers)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        req = {"command": "overreach", "inputs": {}, "invocation_id": "K" * 8,
               "cursor": None}
        first = _ask(sock_path, req)
        again = _ask(sock_path, req)
        assert not first["ok"]
        assert set(first["refusal"]) == {"code", "message", "data"}
        assert first["invocation_id"] == "K" * 8
        assert again == first  # code, message, data, id — all replay exactly
    finally:
        server.shutdown()
        server.server_close()


def test_malformed_requests_get_structured_refusals_on_one_connection(certified_work):
    """Bad JSON and bad shapes all come back as invalid-input replies over a
    SINGLE connection — the handler loop survives every malformed line and
    still serves a valid request afterwards."""
    from tests.helpers.synthetic import synthetic_decls_and_handlers
    cfg = build_fixture_world(certified_work)
    decls, handlers = synthetic_decls_and_handlers()
    sock_path = cfg.operations_root / "service.sock"
    server = serve(cfg, sock_path, declarations=decls, handlers=handlers)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        with socket.socket(socket.AF_UNIX) as s:
            s.connect(str(sock_path))
            reader = s.makefile()
            for raw in (b"{not json",
                        b'["not", "an", "object"]',
                        b'{"command": 7, "inputs": {}}',
                        b'{"command": "mint-claim", "inputs": ["list"]}',
                        b'{"command": "mint-claim", "inputs": {}, "cursor": 3}',
                        b'{"command": "mint-claim", "inputs": {}, "stray": true}'):
                s.sendall(raw + b"\n")
                reply = json.loads(reader.readline())
                assert reply["ok"] is False
                assert reply["refusal"]["code"] == "invalid-input"
            s.sendall(json.dumps({"command": "mint-claim",
                                  "inputs": {"slug": "after"}}).encode() + b"\n")
            final = json.loads(reader.readline())
        assert final["ok"] and "proposition:after" in final["text"]
    finally:
        server.shutdown()
        server.server_close()


def test_server_close_failure_still_closes_session(certified_work, monkeypatch):
    """The finally holds: even when socket teardown raises, the session's
    ledger ends with session-close."""
    import socketserver
    cfg = build_fixture_world(certified_work)
    server = serve(cfg, cfg.operations_root / "service.sock")

    def boom(self):
        raise OSError("teardown failed")

    monkeypatch.setattr(socketserver.ThreadingUnixStreamServer, "server_close", boom)
    with pytest.raises(OSError):
        server.server_close()
    ledgers = list((cfg.operations_root / "sessions").glob("*/ledger.v1"))
    assert len(ledgers) == 1
    last = json.loads(ledgers[0].read_text().splitlines()[-1])
    assert last["type"] == "session-close"


def test_bind_failure_closes_the_session(certified_work):
    """A socket path over the AF_UNIX length limit fails at bind, after the
    session opened — the constructor must close it on the way out, which the
    ledger's session-close line proves."""
    cfg = build_fixture_world(certified_work)
    long_sock = cfg.operations_root / ("s" * 200 + ".sock")
    with pytest.raises(OSError):
        serve(cfg, long_sock)  # production tree loads; bind raises
    ledgers = list((cfg.operations_root / "sessions").glob("*/ledger.v1"))
    assert len(ledgers) == 1
    last = json.loads(ledgers[0].read_text().splitlines()[-1])
    assert last["type"] == "session-close"


def test_existing_socket_refuses_startup(certified_work):
    from science.refusal import Refused
    cfg = build_fixture_world(certified_work)
    sock_path = cfg.operations_root / "service.sock"
    sock_path.parent.mkdir(parents=True, exist_ok=True)
    sock_path.touch()  # a stale socket is the operator's to remove
    with pytest.raises(Refused):
        serve(cfg, sock_path)
    # The refusal precedes session opening, so nothing leaked into the ledger.
    assert not (cfg.operations_root / "sessions").exists()


def test_cli_write_without_service_refuses(certified_work, capsys):
    """No socket: exit 3 with the same JSON refusal wire as every command."""
    import argparse
    from science.cli import _via_service
    from tests.helpers.synthetic import MINT_CLAIM
    from tests.helpers.world import write_cli_config
    cfg_path = write_cli_config(certified_work)
    ns = argparse.Namespace(config=str(cfg_path), invocation_id=None, cursor=None)
    code = _via_service(ns, MINT_CLAIM, {"slug": "x"})
    assert code == 3
    payload = json.loads(capsys.readouterr().err)
    assert payload["refusal"]["code"] == "permit-exceeded"
    assert "science serve" in payload["refusal"]["message"]
    assert payload["invocation_id"]


def test_cli_write_routes_through_service(certified_work, capsys):
    """The success path end to end: CLI -> socket -> dispatcher -> reply."""
    import argparse
    from science.cli import _via_service
    from science.config import load_config
    from tests.helpers.synthetic import MINT_CLAIM, synthetic_decls_and_handlers
    from tests.helpers.world import write_cli_config
    cfg_path = write_cli_config(certified_work)
    cfg = load_config(cfg_path)
    decls, handlers = synthetic_decls_and_handlers()
    server = serve(cfg, cfg.operations_root / "service.sock",
                   declarations=decls, handlers=handlers)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        ns = argparse.Namespace(config=str(cfg_path), invocation_id=None, cursor=None)
        code = _via_service(ns, MINT_CLAIM, {"slug": "via"})
        captured = capsys.readouterr()
        assert code == 0
        assert "proposition:via" in captured.out
        assert json.loads(captured.err)["invocation_id"]
    finally:
        server.shutdown()
        server.server_close()
```

- [x] **Step 3: Run tests to verify they fail**

Run: `cd python && uv run --group dev pytest tests/test_serve.py tests/test_synthetic_tree.py -q`
Expected: FAIL — no module `science.serve`; synthetic fixtures load test fails until the fixture directories exist.

- [x] **Step 4: Implement `serve.py` and the CLI routing**

```python
"""The CLI's service process: one attended session behind a Unix socket (spec §9.2)."""
from __future__ import annotations

import json
import socketserver
from pathlib import Path

from science.config import ReadContext, ScienceConfig
from science.dispatch import Dispatcher
from science.refusal import Refusal, Refused


def serve(config: ScienceConfig, socket_path: Path, declarations=None, handlers=None):
    """`declarations`/`handlers` default to the production tree; tests inject
    their synthetic set here — production code never imports test modules."""
    from beliefs.session import open_attended_session
    from science.refusal import envelope
    if declarations is None:
        from science.loader import production_tree, resolve_handlers
        declarations = production_tree()
        handlers = resolve_handlers(declarations)
    # Every pre-session refusal happens before the session exists; after it
    # is opened, any constructor failure closes it before propagating.
    if socket_path.exists():
        raise Refused(Refusal("invalid-input",
                              f"socket already exists: {socket_path}; a stale one "
                              "from a crashed service is the operator's to remove"))
    session = open_attended_session(config.world, config.operations_root, profile=config.profile)
    try:
        dispatcher = Dispatcher(declarations, handlers, ReadContext.open(config),
                                session=session)

        def _validated(req) -> tuple[str, dict, str | None, str | None]:
            def refuse(message: str):
                raise Refused(Refusal("invalid-input", message))
            if not isinstance(req, dict):
                refuse("request must be an object")
            unknown = set(req) - {"command", "inputs", "invocation_id", "cursor"}
            if unknown:
                refuse(f"unknown request keys {sorted(unknown)}")
            command = req.get("command")
            if not isinstance(command, str):
                refuse("command must be a string")
            inputs = req.get("inputs")
            if inputs is None:
                inputs = {}
            if not isinstance(inputs, dict):  # a list or scalar never becomes {}
                refuse("inputs must be an object or null")
            invocation_id, cursor = req.get("invocation_id"), req.get("cursor")
            for label, value in (("invocation_id", invocation_id), ("cursor", cursor)):
                if value is not None and not isinstance(value, str):
                    refuse(f"{label} must be a string or null")
            return command, inputs, invocation_id, cursor

        class Handler(socketserver.StreamRequestHandler):
            def handle(self) -> None:
                for line in self.rfile:
                    try:
                        command, inputs, invocation_id, cursor = _validated(json.loads(line))
                        out = dispatcher.invoke(command, inputs,
                                                invocation_id=invocation_id, cursor=cursor)
                        reply = {"ok": True, "text": out.text,
                                 "invocation_id": out.invocation_id}
                    except json.JSONDecodeError as e:
                        reply = {"ok": False, "refusal": envelope(
                            Refusal("invalid-input", f"request is not JSON: {e}"))}
                    except Refused as e:
                        reply = {"ok": False, "refusal": envelope(e.refusal)}
                        if e.invocation_id is not None:
                            reply["invocation_id"] = e.invocation_id
                    self.wfile.write(json.dumps(reply).encode() + b"\n")

        class Server(socketserver.ThreadingUnixStreamServer):
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
```

In `cli.py`, the exact routing code:

```python
def _service_socket(config) -> Path:
    return config.operations_root / "service.sock"


def _via_service(ns, decl, inputs) -> int:
    import json as _json
    import socket as _socket
    from science.config import load_config, resolve_config_path
    from science.refusal import Refusal, envelope, mint_token
    invocation_id = ns.invocation_id or mint_token()
    try:
        config = load_config(resolve_config_path(ns.config))
        sock_path = _service_socket(config)
        with _socket.socket(_socket.AF_UNIX) as s:
            s.connect(str(sock_path))
            s.sendall(_json.dumps({"command": decl.name, "inputs": inputs,
                                   "invocation_id": invocation_id,
                                   "cursor": ns.cursor}).encode() + b"\n")
            reply = _json.loads(s.makefile().readline())
    except (FileNotFoundError, ConnectionRefusedError):
        refusal = Refusal("permit-exceeded",
                          "no writer service; start one with: science serve")
        _json_line({"invocation_id": invocation_id,
                    "refusal": envelope(refusal)})
        return EXIT_REFUSED
    except Refused as e:
        _json_line({"invocation_id": e.invocation_id or invocation_id,
                    "refusal": envelope(e.refusal)})
        return EXIT_REFUSED
    if reply["ok"]:
        sys.stdout.write(reply["text"])
        _json_line({"invocation_id": reply["invocation_id"]})
        return EXIT_OK
    refusal = reply["refusal"]
    _json_line({"invocation_id": reply.get("invocation_id", invocation_id),
                "refusal": refusal})
    return EXIT_REFUSED
```

Task 13 first registers the config-consuming parser entry (the local name in
`build_parser` is `subparsers`, not `sub`):

```python
    serve_parser = subparsers.add_parser("serve")
    serve_parser.add_argument("--config")
```

**Added 2026-09-09:** `main` routes only a fixed set of verbs to
`_framework_verb`, so `serve` must join it or the branch below is
unreachable and `serve` falls through to the command path, which looks for a
declaration named `serve` and fails:

```python
        if namespace.command in {"mcp", "adapters", "build", "serve"}:
```

Then add the `serve` branch to `_framework_verb` before the fallthrough:

```python
    if ns.command == "serve":
        from science.config import load_config, resolve_config_path
        from science.serve import serve as build_server
        config = load_config(resolve_config_path(ns.config))
        server = build_server(config, _service_socket(config))
        try:
            server.serve_forever()
        finally:
            server.server_close()
        return EXIT_OK
```

- [x] **Step 5: Run the full suite, then the whole tree build**

Run: `cd python && uv run --group dev pytest -q && uv run science build`
Expected: PASS; `ok: 1 command(s)`.

- [x] **Step 6: Land the status truth with the code**

In the same commit as step 7: update `README.md` — replace the sentence
recording that the write path is unblocked and not yet implemented with a
short paragraph saying the command framework is implemented (declaration
schema, budgeted renderer, dispatcher, CLI, MCP server, writer service,
Claude Code adapter, `status`) and pointing at the spec — and change the
spec's (`docs/specs/2026-08-31-command-framework-design.md`) Status header to
"implemented" with the date. A doc's status goes stale at the merge, not
later; then grep the README for any other claim this landing falsifies.

(**Corrected 2026-09-09:** this step named a "Nothing is built yet; the first
sub-project here is #2 …" sentence. The README stopped saying that when the
read path landed, and Task 12 replaced its successor with the beliefs-gated
sentence this step now names.)

- [x] **Step 7: Commit**

```bash
git add python/src/science/serve.py python/src/science/cli.py python/tests \
        README.md docs/specs/2026-08-31-command-framework-design.md
git commit -m "feat(serve): unix-socket write service and CLI routing with synthetic exemplars"
```

---

## Execution notes

- Tasks 1–5 are pure-Python and parallel-safe after Task 2; Tasks 6–11 chain (each consumes the previous); Tasks 12–13 are blocked on the beliefs repo delivering `beliefs-96a24a` and the writer-session task (`beliefs-afbbff`). Task 12's Consumes block is the **pinned companion contract** both repositories implement verbatim; a divergence discovered on either side is a change request against both documents before any further code, never a local adjustment.
- **Test imports (noted 2026-09-09, applies to every task's code blocks):** the
  blocks write `from tests.helpers.…`, but the suite has no `tests/__init__.py`
  and every landed module imports the helper package as `from helpers.…`. Read
  the blocks accordingly; the landed code is the convention.
- Live-world tests always take the `certified_work` fixture, never `tmp_path`: beliefs' real engine refuses tmpfs roots (no barrier-option table), which is why the fixture defaults under the repo and honors `SCIENCE_TEST_ROOT`.
- After Task 11 lands, `status` is demonstrable end-to-end: `SCIENCE_CONFIG=… science status`, the MCP server, and the committed Claude Code plugin all render the same bytes.
