# Command Framework Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the `science` command framework — declaration schema, budgeted renderer, dispatcher, CLI, MCP server, Claude Code adapter generator, and the shipped `status` command — against today's `beliefs` kernel reads.

**Architecture:** Commands are the tools: each is a TOML declaration + a deterministic handler + a prompt, and CLI/MCP expose handlers 1:1 through one dispatcher and one renderer. Writes flow only through the `beliefs` writer session (built in the beliefs repo); reads run sessionless. Tasks 1–11 are read-path complete and unblocked; Tasks 12–13 consume the beliefs-side session/permit API and are gated on that repo's work.

**Tech Stack:** Python ≥ the floor in beliefs' `pyproject.toml` (match it exactly), stdlib only for the CLI (`argparse`, `tomllib`), hand-rolled JSON-RPC over stdio for MCP, `pytest` for tests.

**Spec:** `docs/specs/2026-08-31-command-framework-design.md` (this repo). The beliefs-side contract is that spec's §§4–5, implemented in the beliefs repository under its tasks `beliefs-96a24a` (permits) and the writer-session task created alongside this plan.

## Global Constraints

- Package: distribution `verifiably-science`, import name `science`, console script `science`.
- CLI has zero third-party dependencies; `pytest` is a dev dependency only.
- Command name grammar `^[a-z][a-z0-9]*(-[a-z0-9]+)*$`, max 32 bytes; module = name with `-`→`_`.
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
- Produces: `Declaration(name, purpose, write_class: WriteClass, output_budget: int, inputs: tuple[InputSpec, ...], reads: tuple[str, ...], directory: Path)`; `InputSpec(name, type, required, doc, default, choices)`; `WriteClass(kind: str, kinds: tuple[str, ...], routes: Mapping[str, str])` where `kind` is one of `read-only|coordination|mints|publishes`; `DeclarationError(path, field, reason)`; `load_declaration(dir_path, *, kind_acts, contract_kinds) -> Declaration`; `load_command_tree(root, *, kind_acts, contract_kinds) -> tuple[Declaration, ...]`; `handler_module(name) -> str`; `NAME_RE`, `RESERVED_COMMANDS`, `RESERVED_INPUTS`, `INPUT_TYPES` constants.

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
requires-python = ">=3.12"
dependencies = []

[project.scripts]
science = "science.cli:main"

[dependency-groups]
dev = ["pytest>=8"]

[tool.hatch.build.targets.wheel]
packages = ["src/science"]
```

Check beliefs' `python/pyproject.toml` `requires-python` first and copy its floor verbatim if it differs from 3.12. `python/src/science/__init__.py` and `python/src/science/commands/__init__.py` are empty files.

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


def test_tree_refuses_duplicates_and_lists_all(tmp_path):
    write_command(tmp_path, "status", GOOD)
    write_command(tmp_path, "mint-run", MINTS)
    decls = load_command_tree(tmp_path, kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert [d.name for d in decls] == ["mint-run", "status"]


def test_handler_module_mapping():
    assert handler_module("mint-run") == "science.commands.mint_run"
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
MAX_NAME_BYTES = 32
RESERVED_COMMANDS = frozenset({"continue", "serve", "mcp", "adapters", "build"})
RESERVED_INPUTS = frozenset({"cursor", "invocation_id", "view", "session", "config"})
INPUT_TYPES = frozenset({"string", "int", "bool", "enum", "list-of-string"})
WRITE_CLASS_KINDS = frozenset({"read-only", "coordination", "mints", "publishes"})
SCHEMA_VERSION = 1


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
        _require(bool(NAME_RE.match(name.replace("_", "-"))), path, f"inputs.{name}", "bad input name")
        typ = spec.get("type")
        _require(typ in INPUT_TYPES, path, f"inputs.{name}.type", f"must be one of {sorted(INPUT_TYPES)}")
        required = spec.get("required")
        _require(isinstance(required, bool), path, f"inputs.{name}.required", "must be a bool")
        doc = spec.get("doc")
        _require(isinstance(doc, str) and doc, path, f"inputs.{name}.doc", "must be a non-empty string")
        choices = tuple(spec.get("choices", ()))
        if typ == "enum":
            _require(len(choices) > 0 and len(set(choices)) == len(choices)
                     and all(isinstance(c, str) for c in choices),
                     path, f"inputs.{name}.choices", "enum requires unique string choices")
        else:
            _require(not choices, path, f"inputs.{name}.choices", "only enum takes choices")
        default = spec.get("default")
        if required:
            _require(default is None, path, f"inputs.{name}.default", "required input forbids default")
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
    raw = tomllib.loads(path.read_text())
    _require(raw.get("schema_version") == SCHEMA_VERSION, path, "schema_version",
             f"must be {SCHEMA_VERSION}")
    name = raw.get("name")
    _require(isinstance(name, str) and bool(NAME_RE.match(name or "")), path, "name", "bad grammar")
    _require(len(name.encode()) <= MAX_NAME_BYTES, path, "name", "over 32 bytes")
    _require(name not in RESERVED_COMMANDS, path, "name", "reserved name")
    _require(dir_path.name == name, path, "name", f"directory {dir_path.name!r} != name {name!r}")
    purpose = raw.get("purpose")
    _require(isinstance(purpose, str) and purpose, path, "purpose", "must be a non-empty string")
    budget = raw.get("output_budget")
    _require(isinstance(budget, int) and budget > 0, path, "output_budget", "must be a positive int")
    write_raw = raw.get("write_class")
    _require(isinstance(write_raw, str), path, "write_class", "missing")
    write_tbl = raw.get("write", {})
    routes_raw = write_tbl.get("routes", {}) if isinstance(write_tbl, dict) else {}
    write_class = _parse_write_class(write_raw, routes_raw, path, kind_acts, contract_kinds)
    reads_tbl = raw.get("reads", {})
    reads = tuple(reads_tbl.get("families", ())) if isinstance(reads_tbl, dict) else ()
    _require(all(isinstance(r, str) and r for r in reads), path, "reads.families", "strings only")
    inputs = _parse_inputs(raw.get("inputs", {}), path)
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
- Produces: `canonicalize(decl, provided: Mapping) -> dict` (validates, applies defaults, drops absent optionals; raises `Refused` with code `invalid-input`); `input_digest(canonical: Mapping) -> str` (64-hex SHA-256 of canonical JSON); `Refusal(code, message, data)` frozen dataclass; `Refused(Exception)` with `.refusal`; `CODES` frozenset; `INVOCATION_ID_RE`; `mint_token() -> str` (32 lowercase hex).

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
    def __init__(self, refusal: Refusal) -> None:
        self.refusal = refusal
        super().__init__(f"{refusal.code}: {refusal.message}")


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
    known = {i.name: i for i in decl.inputs}
    unknown = set(provided) - set(known)
    if unknown:
        _refuse(f"unknown inputs {sorted(unknown)}", command=decl.name)
    out: dict[str, object] = {}
    for spec in decl.inputs:
        value = provided.get(spec.name, spec.default)
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


def test_field_bounds_enforced_on_decode():
    # Construct an over-long command by hand-encoding:
    import base64, json
    raw = {"f": "r", "c": "s" * 33, "i": "a" * 64, "r": "b" * 64, "b": 1, "o": 1}
    token = "scur1." + base64.urlsafe_b64encode(
        json.dumps(raw, sort_keys=True, separators=(",", ":")).encode()).decode().rstrip("=")
    with pytest.raises(Refused):
        decode(token)


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
    if not isinstance(value, int) or not (0 <= value <= _U64_MAX):
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
from science.report import Finding, Heading, RecordBlock, Text


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
    for block in (Heading("h"), Finding("f"), Text("t")):
        with pytest.raises(AuditViolation):  # any non-record block
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
- Test: `python/tests/test_config.py`

**Interfaces:**
- Consumes: `from beliefs.world import WorldConfig` (the canonical import — a frozen dataclass at `beliefs/world/registry.py:137` with fields `world_root: Path`, `world_id: str`, `corpus_roots: tuple[Path, ...]`; its `__post_init__` requires `world_id` to be exactly 32 lowercase hex characters and `corpus_roots` to be an exact `tuple`, and resolves both path fields); `from beliefs.root import open_world` (`root.py:1674`, `(config: WorldConfig) -> World`); `Refusal`, `Refused` (Task 2).
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

Add beliefs as a dependency: in `python/pyproject.toml` set `dependencies = ["verifiably-beliefs"]` and, until it is published, a `[tool.uv.sources]` (or pip `-e`) entry pointing at the beliefs checkout — never a vendored copy.

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
    raw = tomllib.loads(path.read_text())
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
git add python/pyproject.toml python/src/science/config.py python/tests/test_config.py
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
        if invocation_id is not None and not INVOCATION_ID_RE.match(invocation_id):
            raise Refused(Refusal("invalid-input", "invocation_id outside its grammar"))
        if cursor is not None:
            return self._continue(command, inputs, decode(cursor), invocation_id)
        decl = self._decls.get(command)
        if decl is None:
            raise Refused(Refusal("unknown-command", f"no command {command!r}"))
        canonical = canonicalize(decl, inputs)
        if decl.write_class.kind != "read-only":
            raise NotImplementedError("write dispatch lands with the beliefs session API")
        report = self._handlers[decl.name](self._ctx, **canonical)
        iid = invocation_id or mint_token()
        page = self._render(decl, canonical, report, (0, 0))
        return Outcome(page, iid)

    def _render(self, decl: Declaration, canonical: Mapping, report: Report,
                position: tuple[int, int]) -> str:
        digest = input_digest(canonical)

        def cursor_for(pos: tuple[int, int], rdigest: str) -> str:
            return encode(ReadCursor(decl.name, digest, rdigest, pos[0], pos[1]))

        return render_page(report, budget=decl.output_budget, position=position,
                           cursor_for=cursor_for).text

    def _continue(self, command: str, inputs: Mapping, cur, invocation_id) -> Outcome:
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
        iid = invocation_id or mint_token()
        page = self._render(decl, canonical, report, (cur.block, cur.offset))
        return Outcome(page, iid)

    @staticmethod
    def _check_position(report, block: int, offset: int) -> None:
        """Semantic position validation: within the report the digest just proved."""
        from science.report import serialize_block
        if block >= len(report) or offset >= len(serialize_block(report[block]).encode()):
            raise Refused(Refusal("stale-cursor", "cursor position is outside the report"))
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

(Add `.framework-test/` to `.gitignore` in the same commit.)

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
    try:
        from beliefs.permit import KIND_ACTS  # arrives with beliefs-96a24a
        return dict(KIND_ACTS)
    except ImportError:
        return {}  # only read-only commands can ship until then; that is `status`


def production_tree() -> tuple[Declaration, ...]:
    kind_acts = production_kind_acts()
    return load_command_tree(COMMANDS_ROOT, kind_acts=kind_acts,
                             contract_kinds=frozenset(kind_acts))


def resolve_handlers(decls) -> dict:
    handlers = {}
    for decl in decls:
        module = importlib.import_module(handler_module(decl.name))
        handle = getattr(module, "handle", None)
        if handle is None:
            raise DeclarationError(decl.directory, "handler", f"{handler_module(decl.name)} has no handle()")
        params = inspect.signature(handle).parameters
        declared = {i.name for i in decl.inputs}
        accepted = {n for n in params if n not in ("ctx", "writer")}
        if declared != accepted:
            raise DeclarationError(decl.directory, "handler",
                                   f"handler accepts {sorted(accepted)}, declaration says {sorted(declared)}")
        handlers[decl.name] = handle
    return handlers
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `cd python && uv run --group dev pytest tests/test_status.py -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add commands/ python/src/science/commands/status.py python/src/science/loader.py \
        python/src/science/config.py python/tests .gitignore
git commit -m "feat(status): shipped read exemplar over a beliefs fixture world"
```

### Task 9: CLI with sessionless reads

**Files:**
- Create: `python/src/science/cli.py`
- Test: `python/tests/test_cli.py`

**Interfaces:**
- Consumes: `production_tree`, `resolve_handlers` (Task 8); `Dispatcher` (Task 7); `load_config`, `resolve_config_path`, `ReadContext` (Task 6); `Refused` (Task 2).
- Produces: `main(argv: list[str] | None = None) -> int` (the console script); `build_parser(decls) -> argparse.ArgumentParser`; option mapping: input `foo-bar` → `--foo-bar`, `bool` → `--foo/--no-foo` pair via `argparse.BooleanOptionalAction`, `list-of-string` → `action="append"`, `enum` → `choices=`; global `--config`, `--invocation-id`, `--continue` (dest `cursor`).

- [ ] **Step 1: Write the failing tests**

`python/tests/test_cli.py`:

```python
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
    out = capsys.readouterr().out
    assert code == 0
    assert "World status" in out


def test_refusal_exits_3(certified_work, capsys):
    cfg_path = write_cli_config(certified_work)
    code = main(["status", "--config", str(cfg_path), "--continue", "scur1.garbage"])
    assert code == 3
    assert "unknown-cursor" in capsys.readouterr().err


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
import sys

from science.config import ReadContext, load_config, resolve_config_path
from science.dispatch import Dispatcher
from science.loader import production_tree, resolve_handlers
from science.refusal import Refused
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


def _protocol_options() -> argparse.ArgumentParser:
    """Shared parent so `science status --config …` parses: argparse only
    accepts an option after the subcommand if the subparser declares it."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--config")
    common.add_argument("--invocation-id", dest="invocation_id")
    common.add_argument("--continue", dest="cursor")
    return common


def build_parser(decls) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="science")
    common = _protocol_options()
    sub = parser.add_subparsers(dest="command", required=True)
    for decl in decls:
        _add_command(sub, decl, common)
    for verb in ("serve", "build"):
        sub.add_parser(verb, parents=[common])
    mcp = sub.add_parser("mcp", parents=[common])
    mcp.add_argument("mode", choices=["serve"])
    adapters = sub.add_parser("adapters", parents=[common])
    adapters.add_argument("mode", choices=["build"])
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        decls = production_tree()
        parser = build_parser(decls)
        ns = parser.parse_args(argv)
        if ns.command in ("serve", "mcp", "adapters", "build"):
            return _framework_verb(ns)
        decl = next(d for d in decls if d.name == ns.command)
        inputs = {s.name: getattr(ns, s.name) for s in decl.inputs
                  if getattr(ns, s.name, None) is not None}
        if decl.write_class.kind != "read-only":
            return _via_service(ns, decl, inputs)  # Task 13; until then unreachable
        config = load_config(resolve_config_path(ns.config))
        dispatcher = Dispatcher(decls, resolve_handlers(decls), ReadContext.open(config))
        out = dispatcher.invoke(ns.command, inputs,
                                invocation_id=ns.invocation_id, cursor=ns.cursor)
        sys.stdout.write(out.text)
        return EXIT_OK
    except Refused as e:
        sys.stderr.write(f"refused [{e.refusal.code}] {e.refusal.message}\n")
        return EXIT_REFUSED
    except Exception as e:  # noqa: BLE001 — the CLI's last resort
        sys.stderr.write(f"internal error: {e}\n")
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
- Produces: `build_adapter(decls, commands_root: Path, skills_root: Path, out: Path) -> None` (idempotent, deterministic); the committed `adapters/claude-code/` tree: `.claude-plugin/plugin.json`, `skills/<name>/SKILL.md` per command, `.mcp.json`; CLI verbs `science adapters build` and `science build` (tree validation only).

- [ ] **Step 1: Write the preamble**

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

- [ ] **Step 2: Write the failing tests**

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

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd python && uv run --group dev pytest tests/test_adapters.py -q`
Expected: FAIL — no module `science.adapters`.

- [ ] **Step 4: Implement `adapters.py` and wire the verbs**

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
    if out.exists():
        shutil.rmtree(out)
    (out / ".claude-plugin").mkdir(parents=True)
    (out / ".claude-plugin" / "plugin.json").write_text(json.dumps(PLUGIN, indent=2) + "\n")
    (out / ".mcp.json").write_text(json.dumps(MCP, indent=2) + "\n")
    preamble = (commands_root / "PREAMBLE.md").read_text()
    generated = set()
    for decl in decls:
        prompt = (decl.directory / "prompt.md").read_text()
        skill_dir = out / "skills" / decl.name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(_skill_md(decl, preamble, prompt))
        generated.add(decl.name)
    if skills_root.is_dir():
        for authored in sorted(p for p in skills_root.iterdir() if p.is_dir()):
            if authored.name in generated:
                raise DeclarationError(authored, "skill", "collides with a generated command skill")
            shutil.copytree(authored, out / "skills" / authored.name)
```

In `cli.py`, replace `_framework_verb` so `adapters build` (the spec's verb, `ns.mode` from Task 9's parser) regenerates the committed tree and `build` validates:

```python
def _framework_verb(ns) -> int:
    from science.loader import COMMANDS_ROOT, REPO_ROOT, production_tree
    decls = production_tree()  # build refusals surface here
    if ns.command == "build":
        from science.loader import resolve_handlers
        resolve_handlers(decls)
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

- [ ] **Step 5: Generate the committed tree, then run tests to verify they pass**

Run: `cd python && uv run science adapters build && cd .. && git add adapters/ && cd python && uv run --group dev pytest tests/test_adapters.py -q`
Expected: PASS.

- [ ] **Step 6: Commit**

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
`initialize`/`initialized` handshake, requires request `_meta`, and made
protocol sessions explicit. The design's "one attended session per server
lifetime" (spec §9.3) is unaffected: the **writer** session binds to the
server *process* (spawn to exit), not to any MCP protocol session, and if a
harness runs several protocol sessions over one process they share that one
attended writer session — same person, full permit, one ledger. This ruling
is recorded in spec §9.3. **Step 0 of this task:** read the pinned
revision's tools page and release notes
(`modelcontextprotocol.io/specification/2026-07-28/server/tools`,
`blog.modelcontextprotocol.io/posts/2026-07-28/`) and mirror the exact
request/response envelope — the code below fixes the dispatch logic and our
side of the contract; field spellings come from the spec page, and the
tests are written from it, not from memory.

**Interfaces:**
- Consumes: `Dispatcher`, `production_tree`, `resolve_handlers`, `ReadContext`, `load_config`, `Refused`.
- Produces: `PROTOCOL_VERSION = "2026-07-28"`; `tool_schema(decl) -> dict` (JSON Schema: declared inputs + optional `invocation_id` and `cursor` string properties); `handle_request(req, dispatcher, decls) -> dict` — a JSON-RPC 2.0 responder for `tools/list` and `tools/call` that **rejects a request without `params._meta`** (`-32600`); no `initialize` handling exists to keep obsolete clients honest; `serve(config_path, stdin, stdout, session=None) -> None` (the `session` parameter is wired to the attended writer session in Task 12; until then every command it can serve is read-only). Tool results carry the rendered text as content, `isError` on refusals with text `refused [<code>] <message>`, and `structuredContent: {"invocation_id": …}` so callers can reuse minted ids.

- [ ] **Step 1: Write the failing tests**

`python/tests/test_mcp.py`:

```python
import io
import json

from science.mcp import handle_request, tool_schema
from science.loader import production_tree


def rpc(method, params=None, id=1):
    body = dict(params or {})
    body.setdefault("_meta", {})  # required by MCP 2026-07-28
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


def test_missing_meta_is_a_protocol_error():
    req = {"jsonrpc": "2.0", "id": 9, "method": "tools/list", "params": {}}
    res = handle_request(req, dispatcher=None, decls=())
    assert res["error"]["code"] == -32600


def test_initialize_is_gone():
    res = handle_request(rpc("initialize"), dispatcher=None, decls=())
    assert res["error"]["code"] == -32601  # retired by MCP 2026-07-28; no legacy shim


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
```

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

_TYPES = {"string": {"type": "string"}, "int": {"type": "integer"},
          "bool": {"type": "boolean"},
          "list-of-string": {"type": "array", "items": {"type": "string"}}}


def tool_schema(decl: Declaration) -> dict:
    props: dict = {}
    required = []
    for spec in decl.inputs:
        entry = dict(_TYPES.get(spec.type, {"type": "string"}))
        if spec.type == "enum":
            entry = {"type": "string", "enum": list(spec.choices)}
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


def handle_request(req: dict, dispatcher: Dispatcher, decls) -> dict:
    rid, method = req.get("id"), req.get("method")
    params = req.get("params") or {}
    if not isinstance(params.get("_meta"), dict):  # required by 2026-07-28
        return {"jsonrpc": "2.0", "id": rid,
                "error": {"code": -32600, "message": "request _meta is required"}}
    if method == "tools/list":
        return _result(rid, {"tools": [tool_schema(d) for d in decls]})
    if method == "tools/call":
        arguments = dict(params.get("arguments", {}))
        cursor = arguments.pop("cursor", None)
        invocation_id = arguments.pop("invocation_id", None)
        try:
            out = dispatcher.invoke(params.get("name", ""), arguments,
                                    invocation_id=invocation_id, cursor=cursor)
            return _result(rid, {"content": [{"type": "text", "text": out.text}],
                                 "structuredContent": {"invocation_id": out.invocation_id},
                                 "isError": False})
        except Refused as e:
            return _result(rid, {"content": [{"type": "text",
                                              "text": f"refused [{e.refusal.code}] {e.refusal.message}"}],
                                 "isError": True})
    return {"jsonrpc": "2.0", "id": rid,
            "error": {"code": -32601, "message": f"method not found: {method}"}}


def _result(rid, payload) -> dict:
    return {"jsonrpc": "2.0", "id": rid, "result": payload}


def serve(config_path: Path, stdin=None, stdout=None, session=None) -> None:
    from science.config import ReadContext, load_config
    from science.loader import production_tree, resolve_handlers
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    decls = production_tree()
    dispatcher = Dispatcher(decls, resolve_handlers(decls),
                            ReadContext.open(load_config(config_path)),
                            session=session)  # Task 12 wires the attended session
    for line in stdin:
        if not line.strip():
            continue
        response = handle_request(json.loads(line), dispatcher, decls)
        if response is not None:
            stdout.write(json.dumps(response) + "\n")
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

**BLOCKED until the beliefs repo delivers `beliefs-96a24a` (permits) and the writer-session task.** Do not stub or mock the session; the whole point is exercising the real permit path.

**Files:**
- Modify: `python/src/science/dispatch.py`
- Test: `python/tests/test_write_dispatch.py`

**Interfaces:**
- Consumes (the beliefs contract; verify names against what beliefs actually shipped and adjust once, here):
  - `beliefs.permit.RequiredCapabilities` with `.none()`, `.coordination()`, `.for_kinds(kinds: Iterable[str], routes: Mapping[str, str])`, `.publishes()`
  - `beliefs.permit.PermitExceeded(WriteRefused)` with `.requirement` and `.capability` attributes
  - `beliefs.session.open_attended_session(world_config, operations_root) -> WriterSession`
  - `WriterSession.session_id: str` (32 hex), `WriterSession.actor: str`
  - `WriterSession.scoped(required) -> ScopedWriter` (raises `PermitExceeded` when the requirement exceeds the session permit — the declaration-time refusal)
  - `WriterSession.claim_invocation(invocation_id, command, input_digest) -> Claim` where `Claim` is one of `Fresh`, `Done(outcome)`, `Open`, `Mismatch` (ledger-backed, called under the dispatch lock)
  - `WriterSession.close_invocation(invocation_id, outcome)` where outcome is `{"done": [[uid, id], …]}` or `{"refusal": {code, message, data}}` — the persisted envelope of spec §5.2
  - `WriterSession.invocation_acts(invocation_id) -> tuple[ActLine, ...]` with `ActLine.record_ids: tuple[tuple[str, str], ...]` — `(uid, id)` pairs
  - `beliefs.session.open_ledger_reader(operations_root, session_id) -> LedgerReader` with `LedgerReader.invocation(invocation_id) -> InvocationRecord | None` carrying `.acts` (as above) and `.outcome` — the accessor write continuation resolves cursors through
  - `ScopedWriter` mirroring the `CorpusWriter` write methods, permit-checked per act
- Produces: the write branch of `Dispatcher.invoke` (spec §6.1 steps 3–7 for writes, §6.2 dedup under one `threading.Lock`, §7.4 audit via `audit_write_report`); **completion ordering** (spec §6.1/§5.2, ruled here): handler → collect minted `(uid, id)` pairs from the session's acts → `audit_write_report` → `close_invocation` → render → return. The ledger records act truth, never rendering success: an audit violation still closes `done` with the minted pairs (the acts committed) and then raises `AuditViolation` as an internal error — the caller sees exit 1, never the echoed report, and a dedup retry replays canonically from the ledger. A handler refusal closes with the persisted refusal envelope, in that order, before re-raising as `Refused`. Write-cursor continuation resolves the ledger via `open_ledger_reader`, re-renders from the ledger's `(uid, id)` pairs only, and never calls the write handler or canonicalizes inputs. Refusal translation: `PermitExceeded` → `permit-exceeded`, other `WriteRefused` → `kernel-refused` with the subclass name in `data`. Write handler signature: `handle(ctx, writer, **inputs) -> Report`; record blocks come from `record_block(node)` over what the writer returned. Also produced here: `science.mcp.serve` and `science.serve` open the attended session (`open_attended_session`) and pass it to their dispatchers — until this task the MCP server runs with `session=None`.

- [ ] **Step 1: Write the failing tests**

`python/tests/test_write_dispatch.py` — these run against a real attended session over the fixture world; the synthetic commands live in the test module and are passed to `Dispatcher` directly (handler injection is the fixture path; production resolution stays convention-bound):

```python
import threading

import pytest

from science.dispatch import Dispatcher
from science.cursor import MIN_OUTPUT_BUDGET
from science.refusal import Refused
from science.report import Text, record_block
from science.schema import Declaration, InputSpec, WriteClass
from pathlib import Path
from tests.helpers.world import (
    build_fixture_world, fixture_proposition_node, fixture_source_node,
)

# Real contract kinds only: proposition is the simplest mintable kind
# (Task 8's fixture already writes them); source is the foreign kind the
# lying handler reaches for.
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


@pytest.fixture
def rig(certified_work):
    from beliefs.session import open_attended_session
    from science.config import ReadContext
    cfg = build_fixture_world(certified_work)
    session = open_attended_session(cfg.world, cfg.operations_root)
    decls = (MINT_CLAIM, OVERREACH)
    handlers = {"mint-claim": mint_claim_handler, "overreach": overreach_handler}
    return Dispatcher(decls, handlers, ReadContext.open(cfg), session=session), session


def test_write_returns_only_its_record(rig):
    d, _ = rig
    out = d.invoke("mint-claim", {"slug": "hello"})
    assert "proposition:hello" in out.text and "audit echo" not in out.text


def test_act_time_refusal_when_body_exceeds_declaration(rig):
    d, _ = rig
    with pytest.raises(Refused) as e:
        d.invoke("overreach", {})
    assert e.value.refusal.code in ("permit-exceeded", "kernel-refused")


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
    assert len(results) + len(errors) == 8 and results


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
    assert again.value.refusal.code == first.value.refusal.code
    assert again.value.refusal.message == first.value.refusal.message
    assert len(session.invocation_acts("F" * 8)) == acts_after_first  # not re-executed


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

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd python && uv run --group dev pytest tests/test_write_dispatch.py -q`
Expected: FAIL — `NotImplementedError` from the read-only dispatcher (or `ImportError` if beliefs has not landed; in that case this task is not startable yet).

- [ ] **Step 3: Implement the write branch in `dispatch.py`**

Replace the `NotImplementedError` branches:

```python
# __init__ gains: self._lock = threading.Lock()

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

    def _invoke_write(self, decl, canonical, invocation_id):
        from beliefs.permit import PermitExceeded
        from beliefs.errors import WriteRefused
        from science.render import audit_write_report
        if self._session is None:
            raise Refused(Refusal("permit-exceeded", "no writer session on this surface"))
        try:
            writer = self._session.scoped(self._required(decl))
        except PermitExceeded as e:
            raise Refused(Refusal("permit-exceeded", str(e),
                                  {"requirement": str(e.requirement), "capability": str(e.capability)}))
        iid = invocation_id or mint_token()
        with self._lock:
            claim = self._session.claim_invocation(iid, decl.name, input_digest(canonical))
            kind = type(claim).__name__
            if kind == "Done":
                return Outcome(self._replay_outcome(decl, claim.outcome, iid, (0, 0)), iid)
            if kind == "Open":
                raise Refused(Refusal("outcome-unknown",
                                      "a prior attempt is open; its outcome is unknown"))
            if kind == "Mismatch":
                raise Refused(Refusal("input-mismatch",
                                      "invocation_id was used with a different payload"))
            try:
                report = self._handlers[decl.name](self._ctx, writer, **canonical)
            except PermitExceeded as e:
                return self._close_refused(iid, Refusal("permit-exceeded", str(e)))
            except WriteRefused as e:
                return self._close_refused(
                    iid, Refusal("kernel-refused", str(e), {"kind": type(e).__name__}))
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
            # internal error; the echoed report is never rendered. Otherwise:
            return Outcome(self._render_write(decl.output_budget, report, iid, (0, 0)), iid)

    def _close_refused(self, iid, refusal: Refusal):
        envelope = {"code": refusal.code, "message": refusal.message,
                    "data": dict(refusal.data)}
        self._session.close_invocation(iid, {"refusal": envelope})
        raise Refused(refusal)

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
            raise Refused(Refusal(r["code"], r["message"], r.get("data", {})))
        report = self._minted_report(outcome["done"])
        return self._render_write(decl.output_budget, report, iid, position)
```

The write arm of `_continue` (replacing its `NotImplementedError`) — never a
handler call, never canonicalization:

```python
        if isinstance(cur, WriteCursor):
            from beliefs.session import open_ledger_reader
            operations_root = self._ctx.config.operations_root
            try:
                reader = open_ledger_reader(operations_root, cur.session_id)
            except FileNotFoundError:
                raise Refused(Refusal("unknown-cursor", "no such session ledger"))
            record = reader.invocation(cur.invocation_id)
            if record is None:
                raise Refused(Refusal("unknown-cursor", "no such invocation in that session"))
            if "refusal" in record.outcome:
                raise Refused(Refusal("unknown-cursor",
                                      "that invocation refused; nothing to page"))
            report = self._minted_report(record.outcome["done"])
            from science.render import report_digest as fresh_digest
            if fresh_digest(report) != cur.report_digest:
                raise Refused(Refusal("stale-cursor", "the records changed; re-run"))
            self._check_position(report, cur.block, cur.offset)
            iid = invocation_id or mint_token()
            budget = self._decls[command].output_budget if command in self._decls \
                else max(d.output_budget for d in self._decls.values())
            page = render_page(report, budget=budget, position=(cur.block, cur.offset),
                               cursor_for=lambda pos, rd: encode(
                                   WriteCursor(cur.session_id, cur.invocation_id, rd,
                                               pos[0], pos[1])))
            return Outcome(page.text, iid)
```

`ReadContext` (Task 6's `config.py`) gains `load_record(uid, record_id)`:
resolve through the read path the fixture already exercises and refuse
`unknown-cursor` if the record is absent. `_render_write` uses the actual
per-invocation `Report` digest exactly as the read path does, so replayed
pages and first-render pages share cursors. Finally, wire the attended
session into the servers: `science.mcp.serve` and `science.serve` call
`open_attended_session(config.world, config.operations_root)` and pass the
session to their `Dispatcher` (this replaces Task 11's `session=None`).

- [ ] **Step 4: Run the full suite to verify it passes**

Run: `cd python && uv run --group dev pytest -q`
Expected: PASS, including every earlier task's tests.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/dispatch.py python/tests/test_write_dispatch.py python/tests/helpers/world.py
git commit -m "feat(dispatch): write dispatch with scoped permits, atomic claims, and dedup"
```

### Task 13: Service process, CLI write routing, synthetic exemplars end-to-end (beliefs-gated)

**BLOCKED with Task 12 (same beliefs prerequisites).**

**Files:**
- Create: `python/src/science/serve.py`
- Modify: `python/src/science/cli.py` (`serve` verb; `_via_service`)
- Create: `python/tests/fixtures/commands/` (synthetic declarations: `mint-claim/`, `overreach/`, `coord-note/`, `pub-view/` — each a real `command.toml` + one-line `prompt.md`)
- Create: `python/tests/helpers/synthetic.py` (the one definition of the synthetic declarations + handlers, shared by Tasks 12–13 tests)
- Test: `python/tests/test_serve.py`, `python/tests/test_synthetic_tree.py`

**Interfaces:**
- Consumes: `Dispatcher` with write branch (Task 12); `open_attended_session` (beliefs); `Refusal/Refused`, `production_tree`.
- Produces: `serve(config: ScienceConfig, socket_path: Path, declarations=None, handlers=None) -> Server` — a Unix-socket JSON-lines service holding one attended session for its lifetime; `declarations`/`handlers` default to the production tree and are injection points for tests (production code never imports test modules); a socket path that already exists **refuses at startup** with a message naming the path — never a silent unlink (a stale socket from a crash is the operator's to remove); wire protocol: request `{"command": str, "inputs": {…}, "invocation_id": str | null, "cursor": str | null}`, response `{"ok": true, "text": str, "invocation_id": str}` or `{"ok": false, "refusal": {code, message, data}}`; socket at `<operations_root>/service.sock`; CLI `science serve` runs it, and `_via_service` connects for any write-class command — printing the reply's `invocation-id: <id>` to stderr so callers can retry safely — refusing with a plain message naming `science serve` when the socket is absent. **Landing step:** update this repo's `README.md` ("Nothing is built yet" is false once this task lands) and the spec's Status header to implemented, in the same commit — a doc's status goes stale at the merge, not later.

- [ ] **Step 1: Write the synthetic declarations**

`python/tests/fixtures/commands/mint-claim/command.toml` (the others follow the same shape with `write_class = "coordination"` and `write_class = "publishes"`; `overreach/` duplicates `mint-claim`'s declaration under its own name):

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
    session = open_attended_session(cfg.world, cfg.operations_root)
    d = Dispatcher(decls, {"pub-view": lambda ctx, writer: ()}, ReadContext.open(cfg), session=session)
    with pytest.raises(Refused) as e:
        d.invoke("pub-view", {})
    assert e.value.refusal.code == "permit-exceeded"
```

(If beliefs' attended full permit includes `publish` before sub-project 5 exists, change the test to open the session with whatever narrower constructor beliefs provides for tests, or assert on the act-time refusal instead — the declaration-time check against a permit lacking the family is the behavior under test, not one particular session shape.)

- [ ] **Step 2: Write the failing service tests**

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


def test_existing_socket_refuses_startup(certified_work):
    from science.refusal import Refused
    cfg = build_fixture_world(certified_work)
    sock_path = cfg.operations_root / "service.sock"
    sock_path.parent.mkdir(parents=True, exist_ok=True)
    sock_path.touch()  # a stale socket is the operator's to remove
    with pytest.raises(Refused):
        serve(cfg, sock_path)


def test_cli_write_without_service_refuses(certified_work, capsys, monkeypatch):
    """_via_service with no socket: exit 3 and a message naming `science serve`."""
    from science.cli import _via_service
    import argparse
    cfg = build_fixture_world(certified_work)
    ns = argparse.Namespace(config=None, invocation_id=None, cursor=None)
    monkeypatch.setattr("science.cli._service_socket", lambda config: cfg.operations_root / "service.sock")
    code = _via_service(ns, None, {})
    assert code == 3
    assert "science serve" in capsys.readouterr().err
```

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd python && uv run --group dev pytest tests/test_serve.py tests/test_synthetic_tree.py -q`
Expected: FAIL — no module `science.serve`; synthetic fixtures load test fails until the fixture directories exist.

- [ ] **Step 4: Implement `serve.py` and the CLI routing**

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
    if declarations is None:
        from science.loader import production_tree, resolve_handlers
        declarations = production_tree()
        handlers = resolve_handlers(declarations)
    session = open_attended_session(config.world, config.operations_root)
    dispatcher = Dispatcher(declarations, handlers, ReadContext.open(config),
                            session=session)
    if socket_path.exists():
        raise Refused(Refusal("invalid-input",
                              f"socket already exists: {socket_path}; a stale one "
                              "from a crashed service is the operator's to remove"))

    class Handler(socketserver.StreamRequestHandler):
        def handle(self) -> None:
            for line in self.rfile:
                req = json.loads(line)
                try:
                    out = dispatcher.invoke(req["command"], req.get("inputs") or {},
                                            invocation_id=req.get("invocation_id"),
                                            cursor=req.get("cursor"))
                    reply = {"ok": True, "text": out.text, "invocation_id": out.invocation_id}
                except Refused as e:
                    reply = {"ok": False, "refusal": {"code": e.refusal.code,
                                                      "message": e.refusal.message,
                                                      "data": dict(e.refusal.data)}}
                self.wfile.write(json.dumps(reply).encode() + b"\n")

    socket_path.parent.mkdir(parents=True, exist_ok=True)
    if socket_path.exists():
        socket_path.unlink()
    return socketserver.ThreadingUnixStreamServer(str(socket_path), Handler)
```

Move the synthetic declarations/handlers used by Tasks 12–13 tests into `tests/helpers/synthetic.py` (`synthetic_decls_and_handlers()` loads `tests/fixtures/commands` through `load_command_tree` and returns the declarations with the handler functions Task 12 defined) so both the write-dispatch tests and this task share one definition. In `cli.py`: `_service_socket(config) = config.operations_root / "service.sock"`; `_via_service` connects, sends one request line, prints `text` on stdout and `invocation-id: <id>` on stderr (so callers can retry safely), or the refusal (exit 3); on `ConnectionRefusedError`/missing socket it writes `refused [permit-exceeded] no writer service; start one with: science serve` to stderr and returns 3. The `serve` verb loads config, builds the production server, and calls `serve_forever()`.

- [ ] **Step 5: Run the full suite, then the whole tree build**

Run: `cd python && uv run --group dev pytest -q && uv run science build`
Expected: PASS; `ok: 1 command(s)`.

- [ ] **Step 6: Land the status truth with the code**

In the same commit as step 7: update `README.md` — replace the "Nothing is
built yet; the first sub-project here is #2 …" sentence with a short
paragraph saying the command framework is implemented (declaration schema,
budgeted renderer, dispatcher, CLI, MCP server, Claude Code adapter,
`status`) and pointing at the spec — and change the spec's
(`docs/specs/2026-08-31-command-framework-design.md`) Status header to
"implemented" with the date. A doc's status goes stale at the merge, not
later; then grep the README for any other claim this landing falsifies.

- [ ] **Step 7: Commit**

```bash
git add python/src/science/serve.py python/src/science/cli.py python/tests \
        README.md docs/specs/2026-08-31-command-framework-design.md
git commit -m "feat(serve): unix-socket write service and CLI routing with synthetic exemplars"
```

---

## Execution notes

- Tasks 1–5 are pure-Python and parallel-safe after Task 2; Tasks 6–11 chain (each consumes the previous); Tasks 12–13 are blocked on the beliefs repo delivering `beliefs-96a24a` and the writer-session task, and their Consumes blocks are the contract to reconcile against what actually shipped there — reconcile the names once, in Task 12's step 3, before writing any code.
- Live-world tests always take the `certified_work` fixture, never `tmp_path`: beliefs' real engine refuses tmpfs roots (no barrier-option table), which is why the fixture defaults under the repo and honors `SCIENCE_TEST_ROOT`.
- After Task 11 lands, `status` is demonstrable end-to-end: `SCIENCE_CONFIG=… science status`, the MCP server, and the committed Claude Code plugin all render the same bytes.
