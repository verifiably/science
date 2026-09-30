# Coordination command set, part 2: selection and the project reads — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A person selects a current project in a session, lists and shows projects, and reads `next` through the selected project's query, with a read in any process finding the one live session's selection.

**Architecture:** The dispatcher of a session-bearing endpoint holds the selection, an unpinned project address. A new `session` write class changes it through a session port that appends the kernel's `select` ledger line; its report is one selection block rebuilt from that line. Read declarations that enumerate through the selection set `selects` and accept a `project` protocol field, which the dispatcher resolves for one invocation. Both launchers answer a selection query on the service socket, and a CLI read asks it before falling back to the configuration's `default_project`. `next` denotes the selected project's query live through `beliefs.world.live.evaluate_live_query`.

**Tech Stack:** Python 3.13, `beliefs` (editable path dependency), pytest with pytest-xdist and pytest-testmon, `just` recipes over `tools/tt`.

**Spec:** `docs/specs/2026-09-24-coordination-command-set-design.md` §3.7, §3.8, §4.1, §4.2, §4.4, §5.1–§5.3, §5.5, §6 (`default_project`), §9 (P5, P8 and the selection rows). Read it with this plan, including its 2026-09-30 planning amendments, which this plan's review also covers.

**Kernel seams this plan calls** (all on `beliefs` main since 2026-09-25; verified against a fixture world while planning):

- S1: `beliefs.world.live.evaluate_live_query(world, query) -> LiveSelection` with `.selected` (record ids, sorted), `.complete`, `.absent`, `.stamp.world_id`, `.stamp.coverage` (pairs of corpus id and state). `beliefs.view_query.stored_query(node) -> ViewQuery`, with `.projection()`.
- S2: `open_attended_session(..., project=<unpinned address>)`; `WriterSession.select_project(invocation_id, address | None) -> pinned address | None`; `WriterSession.invocation_selection(invocation_id) -> SelectLine | None` (`.project` is the pinned address or None); `open_ledger_reader(operations_root, session_id).invocation(id).selection`. An address that does not resolve to one standing project raises `beliefs.errors.ProjectNotResolvable` (a `WriteRefused`, with `.tips`).
- S3: `CoordinationResolver.standing(kind, *, project=None) -> Mapping[CoordinationAddress, Node | CoordinationRefused | None]`, in address order; `CoordinationResolver.revision(uid) -> Node | None`.

**Part 3.** `write_root`, `read_contracts`, per-mount profiles and classification across mounted corpora are `sci-923d3a` and are not touched here: every handler below keeps `single_view()`'s one-root rule.

**Where to work.** `.worktrees/coordination-part2` (branch `coordination-part2`), already created and locked. `tasks start <step id>` before each task. The steps, in order, each depending on the one before: `sci-451329` (Task 1), `sci-108756` (Task 2), `sci-a66ca4` (Task 3), `sci-b0b8cf` (Task 4), `sci-1217b5` (Task 5), `sci-1391bd` (Task 6), `sci-5b8997` (Task 7), `sci-103ec2` (Task 8); their parent is `sci-f95f8b`.

## Global Constraints

- Tests run through the front door only, never bare `pytest`: `just test-one <path relative to python/>` for the test at hand, `just test-fast` before each commit, `just gate` before the branch merges.
- `tasks check` before every commit; each task's `tasks done <id> "<what landed>"` goes in that task's final commit. Conventional commits; no AI attribution lines.
- The selection is an **unpinned project address** (`coord:<project>`) wherever the surface holds it — the dispatcher, the read context, the socket answer, `default_project`. Only the ledger line and the selection block carry the pinned form (`coord:<project>@<revision>`). A name is resolved to an address once and never stored.
- Selection scopes enumeration, never lookup by identity (spec decision 4): `next` and `project-show` set `selects`; `status`, `belief` and `projects` do not.
- No write takes `project` (spec decision 5). The dispatcher refuses it `invalid-input` before any claim.
- The refusal codes are the spec's: `no-current-project`, `unknown-project`, `ambiguous-project` (`data.candidates`: each `address` and `query_digest`). A kernel refusal arrives as `kernel-refused` with the kernel's class name or reason in `data.kind`. With `coordination = false`, every command here refuses `invalid-input` naming that setting.
- A `session` handler validates before it selects, and selects exactly once.
- A new command is four artifacts plus tests: `commands/<name>/command.toml`, `commands/<name>/prompt.md`, `python/src/science/commands/<module>.py` with `handle`, and the regenerated `adapters/claude-code/` tree (`cd python && uv run science adapters build`, pinned by `test_generated_tree_matches_committed`).
- `tools/cli.toml` is the ops repository's file, vendored byte-identical. On this branch, edit only its `# ---- science` section, in the step that changes the parser: `test_surface_equals_table` compares the two at every commit. Task 8 lands the same section in ops and re-vendors before the branch merges.
- No docs or comments name absolute host paths.

## Review Focus

- `project-select` naming a project whose address has two standing tips — a person expects a refusal that lists the tips and leaves the selection where it was, not half a project selected or a traceback. Task 3 pins it.
- A CLI read when the socket path exists but nothing listens (a crashed launcher), or the path is too long for any launcher to bind — a person expects the read to proceed under `default_project`; a listener that answers something else must be an internal error, never a silent fallback. Task 6 pins all three.
- `next` under a selection whose query names an address the world does not hold, or evaluated while a write holds the corpus — a person expects a refusal naming the address or the contention, never the whole world's queue. Task 7 pins both.
- A truncated read continued without the `project` field it was issued under, and a selection block whose project name exceeds the budget — the first must refuse `stale-cursor`, the second must continue from the ledger without running the handler. Tasks 1 and 2 pin them.
- A `project-select` target that starts with `coord:` but is not an address, an empty target, and `target` with `clear` — each must refuse `invalid-input` before any ledger line, and a malformed address must not be looked up as a name. Task 3 pins them.

---

### Task 1: The `selects` key and the `project` protocol field

**Files:**
- Modify: `python/src/science/schema.py` (`RESERVED_INPUTS`, `Declaration`, `load_declaration`)
- Modify: `python/src/science/config.py` (`require_coordination_pinned`, `ReadContext.coordination`)
- Modify: `python/src/science/session.py` (use the moved function)
- Modify: `python/src/science/coordination.py` (`tip_nodes`, `query_digest`, `resolve_project_ref`, `selected_project`)
- Modify: `python/src/science/dispatch.py` (`Dispatcher.selection`, `invoke(project=)`, `_read_context`, `_continue`)
- Modify: `python/src/science/cli.py` (`_add_command`, `main`), `python/src/science/mcp.py` (`tool_schema`, `handle_request`), `python/src/science/serve.py` (`_REQUEST_KEYS`, `_validated`, the handler)
- Modify: `python/tests/test_schema.py`, `python/tests/test_cli.py` (`SessionlessDispatcher.invoke`), `python/tests/test_session_open.py`
- Test: `python/tests/test_project_field.py` (create)

**Interfaces:**
- Consumes: `CoordinationResolver.standing`, `.revision`, `.resolve`; `science.coordination.parse_address`.
- Produces:
  - `Declaration.selects: bool = False` (last field), loaded from the top-level `selects` key; `project` is a reserved input name.
  - `science.config.require_coordination_pinned(config) -> None` (moved from `science.session`).
  - `science.coordination.tip_nodes(resolver, resolved) -> tuple[Node, ...]`; `query_digest(node) -> str` (64 hex); `resolve_project_ref(ctx, text) -> CoordinationAddress` (unpinned project address; refuses `unknown-project`, `ambiguous-project`, `invalid-input`); `selected_project(ctx) -> Node | None`.
  - `Dispatcher.selection` (property); `Dispatcher.invoke(command, inputs, *, invocation_id=None, cursor=None, project=None)`.
  - `science.serve._validated(request) -> (command, inputs, invocation_id, cursor, project)`.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_schema.py`:

```python
def test_selects_loads_on_a_read_only_declaration(tmp_path):
    plain = load_declaration(write_command(tmp_path, "status", GOOD),
                             kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert plain.selects is False
    toml = GOOD.replace('name = "status"', 'name = "peek"\nselects = true')
    decl = load_declaration(write_command(tmp_path, "peek", toml),
                            kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert decl.selects is True


def test_selects_on_a_write_is_a_build_refusal(tmp_path):
    toml = GOOD.replace('write_class = "read-only"', 'write_class = "coordination"\nselects = true')
    with pytest.raises(DeclarationError) as caught:
        load_declaration(write_command(tmp_path, "status", toml),
                         kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert caught.value.field == "selects"


def test_selects_must_be_a_bool(tmp_path):
    toml = GOOD.replace('name = "status"', 'name = "status"\nselects = "yes"')
    with pytest.raises(DeclarationError) as caught:
        load_declaration(write_command(tmp_path, "status", toml),
                         kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert caught.value.field == "selects"


def test_project_is_a_reserved_input_name(tmp_path):
    toml = GOOD.replace("[inputs.corpus]", "[inputs.project]")
    with pytest.raises(DeclarationError) as caught:
        load_declaration(write_command(tmp_path, "status", toml),
                         kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert caught.value.field == "inputs.project"
```

Append to `python/tests/test_session_open.py` (the sessionless half of the refusal `open_session` already makes by name; part 1's final review asked for it):

```python
def test_a_sessionless_resolver_names_a_corpus_that_does_not_pin_coordination(certified_work):
    from dataclasses import replace

    from helpers.world import PROFILE
    from science.config import ReadContext

    bare = build_world_without_coordination(certified_work)
    ctx = ReadContext.open(replace(bare, profile=PROFILE, coordination=2))
    with pytest.raises(Refused) as caught:
        ctx.coordination()
    refusal = caught.value.refusal
    assert refusal.code == "invalid-input"
    assert str(bare.world.corpus_roots[0]) in refusal.message
    assert "coordination = false" in refusal.message
```

Create `python/tests/test_project_field.py`:

```python
"""Spec §4.2: the `selects` key and the `project` protocol field."""
from pathlib import Path

import pytest

from helpers.world import QUERY, build_world_without_coordination, coordination_rig, mint_project
from science.cursor import MIN_OUTPUT_BUDGET
from science.refusal import Refused
from science.report import Text
from science.schema import Declaration, WriteClass

PEEK = Declaration("peek", "fixture", WriteClass("read-only"), MIN_OUTPUT_BUDGET, (), ("coordination",),
                   Path("."), selects=True)
PLAIN = Declaration("plain", "fixture", WriteClass("read-only"), MIN_OUTPUT_BUDGET, (), (), Path("."))
LONG = Declaration("long", "fixture", WriteClass("read-only"), MIN_OUTPUT_BUDGET, (), ("coordination",),
                   Path("."), selects=True)


def peek_handler(ctx):
    return (Text(f"selection={ctx.selection}"),)


def long_handler(ctx):
    return tuple(Text(f"{ctx.selection} row {i} " + "x" * 60) for i in range(200))


EXTRA = ((PEEK, peek_handler), (PLAIN, peek_handler), (LONG, long_handler))
NAMES = ("project", "revise")


def _refused(call, code):
    with pytest.raises(Refused) as caught:
        call()
    assert caught.value.refusal.code == code
    return caught.value.refusal


def test_project_binds_one_invocation_and_leaves_the_endpoint_selection(certified_work):
    with coordination_rig(certified_work, NAMES, extra=EXTRA) as (d, _):
        health, cancer = mint_project(d, "health"), mint_project(d, "cancer")
        d._selection = health  # project-select sets this through the session port (Task 2)
        assert d.invoke("peek", {}, project=str(cancer)).text == f"selection={cancer}\n"
        assert d.invoke("peek", {}, project="cancer").text == f"selection={cancer}\n"
        assert d.invoke("peek", {}).text == f"selection={health}\n"
        assert d.selection == health


def test_a_name_follows_the_projects_current_name(certified_work):
    with coordination_rig(certified_work, NAMES, extra=EXTRA) as (d, _):
        health = mint_project(d, "health")
        d.invoke("revise", {"address": str(health), "name": "human health"})
        assert d.invoke("peek", {}, project="human health").text == f"selection={health}\n"
        _refused(lambda: d.invoke("peek", {}, project="health"), "unknown-project")


def test_a_project_that_does_not_stand_refuses_unknown_project(certified_work):
    with coordination_rig(certified_work, NAMES, extra=EXTRA) as (d, _):
        _refused(lambda: d.invoke("peek", {}, project="nope"), "unknown-project")
        _refused(lambda: d.invoke("peek", {}, project="coord:" + "f" * 32), "unknown-project")


def test_a_malformed_or_subordinate_address_is_invalid_input_not_a_name(certified_work):
    with coordination_rig(certified_work, NAMES, extra=EXTRA) as (d, _):
        _refused(lambda: d.invoke("peek", {}, project="coord:zzz"), "invalid-input")
        _refused(lambda: d.invoke("peek", {}, project="coord:" + "a" * 32 + "/" + "b" * 32), "invalid-input")
        _refused(lambda: d.invoke("peek", {}, project=""), "invalid-input")


def test_a_shared_name_refuses_ambiguous_project_listing_each_candidate(certified_work):
    with coordination_rig(certified_work, NAMES, extra=EXTRA) as (d, _):
        first, second = mint_project(d, "health"), mint_project(d, "health")
        refusal = _refused(lambda: d.invoke("peek", {}, project="health"), "ambiguous-project")
        assert d.invoke("peek", {}, project=str(first)).text == f"selection={first}\n"
    candidates = refusal.data["candidates"]
    assert sorted(c["address"] for c in candidates) == sorted([str(first), str(second)])
    assert all(len(c["query_digest"]) == 64 for c in candidates)


def test_project_on_a_command_that_does_not_select_refuses(certified_work):
    with coordination_rig(certified_work, NAMES, extra=EXTRA) as (d, _):
        mint_project(d, "health")
        refusal = _refused(lambda: d.invoke("plain", {}, project="health"), "invalid-input")
    assert "plain" in refusal.message


def test_project_on_a_write_refuses_and_claims_nothing(certified_work):
    inputs = {"name": "health", "query": QUERY}
    with coordination_rig(certified_work, NAMES, extra=EXTRA) as (d, _):
        _refused(lambda: d.invoke("project", inputs, invocation_id="W" * 8, project="health"), "invalid-input")
        assert "[project]" in d.invoke("project", inputs, invocation_id="W" * 8).text  # the id was never claimed


def test_a_continuation_carries_the_field_again(certified_work):
    with coordination_rig(certified_work, NAMES, extra=EXTRA) as (d, _):
        health = mint_project(d, "health")
        first = d.invoke("long", {}, project=str(health))
        cursor = first.text.rsplit("cursor ", 1)[1].strip()
        assert d.invoke("long", {}, cursor=cursor, project=str(health)).text
        # Without the field the endpoint's selection (none) renders another report.
        _refused(lambda: d.invoke("long", {}, cursor=cursor), "stale-cursor")


def test_without_coordination_the_field_refuses_naming_the_setting(certified_work):
    from science.config import ReadContext
    from science.dispatch import Dispatcher

    ctx = ReadContext.open(build_world_without_coordination(certified_work))
    d = Dispatcher((PEEK,), {"peek": peek_handler}, ctx)
    refusal = _refused(lambda: d.invoke("peek", {}, project="health"), "invalid-input")
    assert "coordination = false" in refusal.message


def test_selected_project_reads_the_selections_one_tip(certified_work):
    from dataclasses import replace

    from beliefs.coordination import CoordinationAddress
    from science.coordination import selected_project

    with coordination_rig(certified_work, NAMES) as (d, ctx):
        health = mint_project(d, "health")
        assert selected_project(ctx) is None
        assert selected_project(replace(ctx, selection=health)).title == "health"
        gone = replace(ctx, selection=CoordinationAddress("f" * 32))
        _refused(lambda: selected_project(gone), "unknown-project")


def test_a_divergent_selection_refuses_with_every_tip(certified_work, monkeypatch):
    """Two tips cannot arise in one root (coordination §4.3), so the resolver
    is stubbed to report them, as `test_cmd_revise.py` does."""
    from dataclasses import replace

    from beliefs.coordination import CoordinationRefused
    from beliefs.corpus import CoordinationResolver
    from science.coordination import selected_project

    with coordination_rig(certified_work, NAMES) as (d, ctx):
        health = mint_project(d, "health")
        tips = (ctx.coordination().resolve(health).uid, "e" * 32)
        monkeypatch.setattr(CoordinationResolver, "resolve",
                            lambda self, address: CoordinationRefused("divergent-view", tips))
        refusal = _refused(lambda: selected_project(replace(ctx, selection=health)), "kernel-refused")
    assert refusal.data == {"kind": "divergent-view", "tips": sorted(tips)}


def test_the_cli_offers_project_on_selects_commands_only():
    from science.cli import build_parser

    parser = build_parser((PEEK, PLAIN))
    assert parser.parse_args(["peek", "--project", "health"]).project == "health"
    assert parser.parse_args(["peek"]).project is None
    with pytest.raises(SystemExit) as caught:
        parser.parse_args(["plain", "--project", "health"])
    assert caught.value.code == 2


def test_the_mcp_schema_offers_project_on_selects_commands_only():
    from science.mcp import tool_schema

    assert tool_schema(PEEK)["inputSchema"]["properties"]["project"]["type"] == "string"
    assert "project" not in tool_schema(PLAIN)["inputSchema"]["properties"]


def test_an_mcp_call_carries_project_to_the_dispatcher(certified_work):
    from science.mcp import handle_request
    from test_mcp import rpc

    with coordination_rig(certified_work, NAMES, extra=EXTRA) as (d, _):
        health = mint_project(d, "health")
        decls = (PEEK, PLAIN)
        shown = handle_request(rpc("tools/call", {"name": "peek", "arguments": {"project": "health"}}), d, decls)
        refused = handle_request(rpc("tools/call", {"name": "plain", "arguments": {"project": "health"}}), d, decls)
        wrong = handle_request(rpc("tools/call", {"name": "peek", "arguments": {"project": 3}}), d, decls)
    assert shown["result"]["content"][0]["text"] == f"selection={health}\n"
    assert refused["result"]["structuredContent"]["refusal"]["code"] == "invalid-input"
    assert wrong["error"]["message"] == "project must be a string"


def test_a_socket_request_carries_project():
    from science.serve import _validated

    assert _validated({"command": "peek", "project": "health"}) == ("peek", {}, None, None, "health")
    _refused(lambda: _validated({"command": "peek", "project": 3}), "invalid-input")
```

In `python/tests/test_cli.py`, `test_read_dispatch_is_sessionless_and_writes_exact_text`, change the fake's `invoke` to accept and check the new field:

```python
        def invoke(self, command, inputs, *, invocation_id=None, cursor=None, project=None):
            assert command == "status"
            assert inputs == {}
            assert re.fullmatch(r"[0-9a-f]{32}", invocation_id) and cursor is None and project is None
            return Outcome("dispatcher output", invocation_id)
```

- [ ] **Step 2: Run them to verify they fail**

Run: `just test-one tests/test_project_field.py tests/test_schema.py tests/test_session_open.py tests/test_cli.py`
Expected: FAIL — `Declaration` takes no `selects`; `invoke` takes no `project`; the sessionless resolver raises `ContractMismatch`.

- [ ] **Step 3: The schema**

In `python/src/science/schema.py`:

```python
RESERVED_INPUTS = frozenset({"cursor", "invocation_id", "view", "session", "config", "project"})
```

Add the field last in `Declaration`, so positional construction elsewhere is unchanged:

```python
    directory: Path
    # The command enumerates through the current project (coordination design
    # §4.2): it reads the selection and accepts the `project` protocol field.
    selects: bool = False
```

In `load_declaration`, after `write_class = _parse_write_class(...)`:

```python
    selects = raw.get("selects", False)
    _require(type(selects) is bool, path, "selects", "must be a bool")
    _require(not selects or write_class.kind == "read-only", path, "selects",
             "only a read-only command enumerates through the current project; "
             "a write binds to the session's selection")
```

Add `"selects"` to `known_top`, and return `Declaration(name, purpose, write_class, budget, inputs, reads, dir_path, selects)`.

- [ ] **Step 4: The named refusal on the sessionless resolver**

Move `_require_coordination_pinned` from `python/src/science/session.py` to `python/src/science/config.py`, below `resolve_config_path`, renamed `require_coordination_pinned`, body and docstring unchanged. Its imports move to the top of `config.py`: add `ManifestMalformed, ManifestMissing` to the `beliefs.errors` import (`shipped_coordination` and `load_manifest` are already imported there). In `session.py`, import it (`from science.config import ScienceConfig, require_coordination_pinned`), call it where the private one was called, and delete the private definition.

In `ReadContext.coordination`, check the pins before building the resolver:

```python
        if self.config.coordination is None:
            raise Refused(Refusal("invalid-input",
                                  "coordination = false in this configuration; there is no resolver to ask"))
        # The resolver checks each mount's pins and raises a bare ContractMismatch;
        # refuse the one mismatch a configuration upgrade produces by name first.
        require_coordination_pinned(self.config)
        return CoordinationResolver({root: self.config.profile for root in self.config.world.corpus_roots})
```

- [ ] **Step 5: The project helpers**

Append to `python/src/science/coordination.py`:

```python
def tip_nodes(resolver, resolved) -> tuple:
    """The standing tips behind one `standing()` or `resolve()` answer: none,
    the one tip, or every tip of a divergent address."""
    from beliefs.coordination import CoordinationRefused

    if resolved is None:
        return ()
    if isinstance(resolved, CoordinationRefused):
        return tuple(resolver.revision(uid) for uid in resolved.tips)
    return (resolved,)


def query_digest(node) -> str:
    """sha256 over a view revision's canonical query projection: what tells two
    projects that share a name apart."""
    import hashlib
    import json

    from beliefs.view_query import stored_query

    payload = json.dumps(stored_query(node).projection(), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode()).hexdigest()


def resolve_project_ref(ctx, text: str):
    """A project's name or `coord:<project>` address, as its unpinned address
    (spec §3.7, §5.2). A name matches a standing tip's name exactly; names are
    content, so none refuses `unknown-project` and two refuse `ambiguous-project`.
    A divergent project's address is returned: whoever reads through it refuses."""
    from beliefs.coordination import CoordinationRefused

    resolver = ctx.coordination()
    if text.startswith("coord:"):
        address = parse_address(text, subordinate=False)
        resolved = resolver.resolve(address)
        if resolved is None or (not isinstance(resolved, CoordinationRefused) and resolved.kind != "project"):
            raise Refused(Refusal("unknown-project", f"{text} names no standing project"))
        return address
    if not text:
        _refuse("a project is named by its name or its coord:<project> address")
    candidates = []
    for address, resolved in resolver.standing("project").items():
        named = [node for node in tip_nodes(resolver, resolved) if node.title == text]
        if named:
            candidates.append((address, named[0]))
    if not candidates:
        raise Refused(Refusal("unknown-project", f"no standing project is named {text!r}"))
    if len(candidates) > 1:
        raise Refused(Refusal(
            "ambiguous-project",
            f"{len(candidates)} projects are named {text!r}; name one by its address",
            {"candidates": [{"address": str(address), "query_digest": query_digest(node)}
                            for address, node in candidates]},
        ))
    return candidates[0][0]


def selected_project(ctx):
    """The selection's one standing tip, or None with nothing selected. A
    selection that no longer resolves to a project refuses `unknown-project`;
    one that diverged refuses `divergent-view` naming every tip (spec §7)."""
    from beliefs.coordination import CoordinationRefused

    if ctx.selection is None:
        return None
    resolved = ctx.coordination().resolve(ctx.selection)
    if isinstance(resolved, CoordinationRefused):
        raise Refused(Refusal(
            "kernel-refused",
            f"{ctx.selection} has {len(resolved.tips)} standing tips; reconcile them with `revise --repair`, "
            "or clear the selection with `project-select --clear`",
            {"kind": resolved.reason, "tips": list(resolved.tips)},
        ))
    if resolved is None or resolved.kind != "project":
        raise Refused(Refusal("unknown-project", f"{ctx.selection} names no standing project"))
    return resolved
```

- [ ] **Step 6: The dispatcher**

In `python/src/science/dispatch.py`, add the property after `__init__`:

```python
    @property
    def selection(self):
        """The endpoint's current project: an unpinned address, or None (spec §5.1)."""
        return self._selection
```

Add, after `_context`:

```python
    def _read_context(self, decl: Declaration, project):
        """The context a read handler receives. `project` is the invocation's
        protocol field (spec §4.2): offered on `selects` commands only, resolved
        here, and binding this invocation alone — the endpoint's selection is
        untouched, and the handler never sees the raw value."""
        if project is None:
            return self._context()
        if type(project) is not str:
            raise Refused(Refusal("invalid-input", "project must be a string"))
        if not decl.selects:
            raise Refused(Refusal(
                "invalid-input",
                f"`project` binds a command that enumerates through the current project; {decl.name} does not",
            ))
        from science.coordination import resolve_project_ref

        return dataclasses.replace(self._ctx, selection=resolve_project_ref(self._ctx, project))
```

Give `invoke` the keyword `project: str | None = None`, and replace the tail of its `try` block (from `if cursor is not None:`) with:

```python
            if cursor is not None:
                return self._continue(command, inputs, decode(cursor), iid, project)
            assert decl is not None
            canonical = canonicalize(decl, inputs)
            if decl.write_class.kind != "read-only":
                if project is not None:
                    raise Refused(Refusal(
                        "invalid-input", "no write takes `project`; a write binds to the session's selection"))
                return self._invoke_write(decl, canonical, iid)
            report = self._handlers[decl.name](self._read_context(decl, project), **canonical)
            return Outcome(self._render(decl, canonical, report, (0, 0)), iid)
```

`_continue` takes `project` as a fifth parameter. Its write-cursor branch becomes:

```python
        if isinstance(cursor, WriteCursor):
            if project is not None:
                raise Refused(Refusal(
                    "invalid-input", "no write takes `project`; a write binds to the session's selection"))
            return self._continue_write(command, cursor, iid)
```

and its handler call becomes `report = self._handlers[decl.name](self._read_context(decl, project), **canonical)`.

- [ ] **Step 7: The three transports**

`python/src/science/cli.py` — in `_add_command`, after the loop over `decl.inputs`:

```python
    if decl.selects:
        parser.add_argument(
            "--project", dest="project",
            help="Read through this project, by name or coord: address, for this invocation only.",
        )
```

and in `main`, pass it: add `project=getattr(namespace, "project", None),` to the `invoke(...)` call.

`python/src/science/mcp.py` — in `tool_schema`, after the `cursor` property:

```python
    if declaration.selects:
        properties["project"] = {
            "type": "string",
            "description": "Read through this project, by name or coord: address, for this call only.",
        }
```

and in `handle_request`, pop and check it beside the other two, then pass it:

```python
        cursor = arguments.pop("cursor", None)
        invocation_id = arguments.pop("invocation_id", None)
        project = arguments.pop("project", None)
        for field, value in (("cursor", cursor), ("invocation_id", invocation_id), ("project", project)):
            if field in raw_arguments and type(value) is not str:
                return _invalid_params(request_id, f"{field} must be a string")
        try:
            outcome = dispatcher.invoke(
                name,
                arguments,
                invocation_id=invocation_id,
                cursor=cursor,
                project=project,
            )
```

`python/src/science/serve.py` — `_REQUEST_KEYS = frozenset({"command", "inputs", "invocation_id", "cursor", "project"})`; `_validated` returns a five-tuple:

```python
    invocation_id, cursor, project = request.get("invocation_id"), request.get("cursor"), request.get("project")
    for label, value in (("invocation_id", invocation_id), ("cursor", cursor), ("project", project)):
        if value is not None and not isinstance(value, str):
            refuse(f"{label} must be a string or null")
    return command, inputs, invocation_id, cursor, project
```

(update its return annotation to `tuple[str, dict, str | None, str | None, str | None]`), and the handler unpacks and passes it:

```python
                    command, inputs, invocation_id, cursor, project = _validated(json.loads(line))
                    out = dispatcher.invoke(command, inputs, invocation_id=invocation_id,
                                            cursor=cursor, project=project)
```

- [ ] **Step 8: Run the tests, then the inner loop**

Run: `just test-one tests/test_project_field.py tests/test_schema.py tests/test_session_open.py tests/test_cli.py tests/test_mcp.py tests/test_serve.py`, then `just test-fast`
Expected: PASS. The CLI surface test is unchanged: no production command sets `selects` yet.

- [ ] **Step 9: Commit**

```bash
tasks check
git add python tasks
git commit -m "feat(dispatch): the selects key and the project protocol field"
```

---

### Task 2: The `session` write class and the selection block

**Files:**
- Modify: `python/src/science/schema.py` (`WRITE_CLASS_KINDS`, `_parse_write_class`)
- Modify: `python/src/science/report.py` (`SelectionBlock`, `Block`, `serialize_block`)
- Modify: `python/src/science/render.py` (`audit_session_report`)
- Modify: `python/src/science/dispatch.py` (`SessionPort`, `_claim`, `_invoke_session`, `_selection_report`, `_replay_session`, `_continue_write`)
- Modify: `python/tests/test_schema.py`, `python/tests/test_report.py`, `python/tests/test_render.py`
- Test: `python/tests/test_session_class.py` (create)

**Interfaces:**
- Consumes: Task 1's `Dispatcher.selection`; `WriterSession.select_project`, `.invocation_selection`; `open_ledger_reader(...).invocation(id).selection`.
- Produces:
  - Write class kind `"session"` (`WriteClass("session")`).
  - `science.report.SelectionBlock(address: str | None, name: str | None)` — `address` is the pinned `coord:<project>@<revision>` string, or None for a clear; it serializes `selected: <address>\nname: <name>\n` or `selected: none\n`.
  - `science.render.audit_session_report(report, recorded: str | None) -> None`, raising `AuditViolation`.
  - `science.dispatch.SessionPort` with one method, `select(address | None) -> pinned address | None`; a `session` handler is called `handle(ctx, port, **inputs)`.

- [ ] **Step 1: Write the failing tests**

In `python/tests/test_schema.py`, widen the existing parametrization to the new class:

```python
@pytest.mark.parametrize("write_class", ["coordination", "publishes", "session"])
def test_generic_tree_accepts_non_read_only_write_classes(tmp_path, write_class):
```

and append:

```python
def test_session_takes_no_routes(tmp_path):
    toml = GOOD.replace('write_class = "read-only"', 'write_class = "session"') + '\n[write.routes]\nnote = "corpus-write"\n'
    with pytest.raises(DeclarationError) as caught:
        load_declaration(write_command(tmp_path, "status", toml),
                         kind_acts=KIND_ACTS, contract_kinds=CONTRACT_KINDS)
    assert caught.value.field == "write.routes"
```

Append to `python/tests/test_report.py`:

```python
def test_a_selection_block_serializes_the_selection_or_none():
    from science.report import SelectionBlock

    address = "coord:" + "a" * 32 + "@" + "b" * 32
    assert serialize_block(SelectionBlock(address, "health")) == f"selected: {address}\nname: health\n"
    assert serialize_block(SelectionBlock(None, None)) == "selected: none\n"
```

Append to `python/tests/test_render.py`:

```python
def test_session_audit_admits_exactly_the_recorded_selection_block():
    from science.render import audit_session_report
    from science.report import SelectionBlock

    address = "coord:" + "a" * 32 + "@" + "b" * 32
    audit_session_report((SelectionBlock(address, "health"),), address)
    audit_session_report((SelectionBlock(None, None),), None)
    with pytest.raises(AuditViolation):  # another revision
        audit_session_report((SelectionBlock(address, "health"),), "coord:" + "a" * 32 + "@" + "c" * 32)
    with pytest.raises(AuditViolation):  # a clear reported as a selection
        audit_session_report((SelectionBlock(address, "health"),), None)
    with pytest.raises(AuditViolation):  # anything beside the block
        audit_session_report((SelectionBlock(address, "health"), Text("and more")), address)
    with pytest.raises(AuditViolation):  # a record block is a write's, not a session's
        audit_session_report((RecordBlock("u" * 32, "note:n1", "note", "t"),), address)
    with pytest.raises(AuditViolation):
        audit_session_report((), None)
```

Create `python/tests/test_session_class.py`:

```python
"""Spec §4.1: the `session` write class, its port, and the selection block."""
import json
from pathlib import Path

import pytest

from helpers.world import QUERY, build_fixture_world, mint_project
from science.cursor import MIN_OUTPUT_BUDGET
from science.dispatch import Dispatcher, HandlerContractViolation, SessionPort
from science.refusal import Refusal, Refused
from science.render import AuditViolation
from science.report import SelectionBlock, Text
from science.schema import Declaration, InputSpec, WriteClass

PICK = Declaration("pick", "fixture", WriteClass("session"), MIN_OUTPUT_BUDGET,
                   (InputSpec("address", "string", False, "d"),), (), Path("."))


def _address(text):
    from beliefs.coordination import CoordinationAddress
    return None if text is None else CoordinationAddress.parse(text)


def pick_handler(ctx, port, *, address=None):
    pinned = port.select(_address(address))
    if pinned is None:
        return (SelectionBlock(None, None),)
    return (SelectionBlock(str(pinned), ctx.coordination().resolve(pinned).title),)


@pytest.fixture
def rig(certified_work):
    from science.config import ReadContext
    from science.loader import production_tree, resolve_handlers
    from science.session import open_session

    cfg = build_fixture_world(certified_work)
    decls = tuple(d for d in production_tree() if d.name in ("project", "revise"))
    handlers = resolve_handlers(decls)
    handlers["pick"] = pick_handler
    session = open_session(cfg)
    dispatcher = Dispatcher(decls + (PICK,), handlers, ReadContext.open(cfg), session=session)
    try:
        yield dispatcher, session, cfg
    finally:
        session.close()


def _lines(cfg, session, kind):
    from beliefs.session import ledger_path
    text = ledger_path(cfg.operations_root, session.session_id).read_text()
    return [line for line in map(json.loads, text.splitlines()) if line["line"] == kind]


def test_selecting_sets_the_endpoint_selection_and_ledgers_one_line(rig):
    d, session, cfg = rig
    health = mint_project(d, "health")
    out = d.invoke("pick", {"address": str(health)}, invocation_id="S" * 8)
    pinned = session.invocation_selection("S" * 8).project
    assert out.text == f"selected: {pinned}\nname: health\n"
    assert pinned.unpinned() == health and d.selection == health
    assert [line["project"] for line in _lines(cfg, session, "select")] == [str(pinned)]
    (close,) = [line for line in _lines(cfg, session, "invocation-close") if line["invocation"] == "S" * 8]
    assert close["outcome"] == {"done": []}


def test_clearing_renders_none(rig):
    d, _, _ = rig
    d.invoke("pick", {"address": str(mint_project(d, "health"))})
    assert d.invoke("pick", {}).text == "selected: none\n"
    assert d.selection is None


def test_without_a_session_refuses_permit_exceeded(certified_work):
    from science.config import ReadContext

    d = Dispatcher((PICK,), {"pick": pick_handler}, ReadContext.open(build_fixture_world(certified_work)))
    with pytest.raises(Refused) as caught:
        d.invoke("pick", {})
    assert caught.value.refusal.code == "permit-exceeded"
    assert caught.value.refusal.message == "no writer session on this surface"


def test_the_handler_is_given_a_port_and_no_kernel_writer(rig):
    d, _, _ = rig
    seen = []

    def spy(ctx, port, *, address=None):
        seen.append(port)
        return pick_handler(ctx, port, address=address)

    d._handlers["pick"] = spy
    d.invoke("pick", {})
    (port,) = seen
    assert type(port) is SessionPort
    assert [name for name in dir(port) if not name.startswith("_")] == ["select"]


def test_a_replay_returns_the_recorded_outcome_and_appends_no_second_line(rig):
    d, session, cfg = rig
    health = mint_project(d, "health")
    first = d.invoke("pick", {"address": str(health)}, invocation_id="R" * 8)
    d._handlers["pick"] = lambda *a, **k: pytest.fail("a replay must not run the handler")
    again = d.invoke("pick", {"address": str(health)}, invocation_id="R" * 8)
    assert again.text == first.text
    assert len(_lines(cfg, session, "select")) == 1


def test_a_replay_after_a_rename_renders_what_the_selection_was(rig):
    d, _, _ = rig
    health = mint_project(d, "health")
    first = d.invoke("pick", {"address": str(health)}, invocation_id="N" * 8)
    d.invoke("revise", {"address": str(health), "name": "human health"})
    again = d.invoke("pick", {"address": str(health)}, invocation_id="N" * 8)
    assert again.text == first.text and "name: health\n" in again.text
    assert d.selection == health  # the selection is the address; the rename left it standing


def test_a_kernel_refusal_closes_the_invocation_and_replays(rig):
    d, session, cfg = rig
    health = mint_project(d, "health")
    d.invoke("pick", {"address": str(health)})
    for _ in range(2):
        with pytest.raises(Refused) as caught:
            d.invoke("pick", {"address": "coord:" + "f" * 32}, invocation_id="K" * 8)
        assert caught.value.refusal.code == "kernel-refused"
        assert caught.value.refusal.data["kind"] == "ProjectNotResolvable"
    assert d.selection == health
    assert len(_lines(cfg, session, "select")) == 1


def test_a_surface_refusal_before_selecting_closes_and_replays(rig):
    d, session, cfg = rig

    def refusing(ctx, port, *, address=None):
        raise Refused(Refusal("invalid-input", "nothing to select"))

    d._handlers["pick"] = refusing
    for _ in range(2):
        with pytest.raises(Refused) as caught:
            d.invoke("pick", {}, invocation_id="V" * 8)
        assert caught.value.refusal.message == "nothing to select"
    assert _lines(cfg, session, "select") == []


def test_a_report_with_anything_but_the_recorded_block_fails_the_audit(rig):
    d, _, _ = rig
    health = mint_project(d, "health")

    def echoing(ctx, port, *, address=None):
        return pick_handler(ctx, port, address=address) + (Text("audit echo!"),)

    d._handlers["pick"] = echoing
    with pytest.raises(AuditViolation):
        d.invoke("pick", {"address": str(health)}, invocation_id="E" * 8)
    # The selection was ledgered, so the invocation closed `done` and a replay
    # renders the canonical block, bypassing the echoing handler.
    replay = d.invoke("pick", {"address": str(health)}, invocation_id="E" * 8)
    assert "audit echo" not in replay.text and replay.text.startswith(f"selected: {health}@")


def test_a_forged_name_never_renders(rig):
    d, _, _ = rig
    health = mint_project(d, "health")

    def forging(ctx, port, *, address=None):
        return (SelectionBlock(str(port.select(_address(address))), "FORGED NAME"),)

    d._handlers["pick"] = forging
    out = d.invoke("pick", {"address": str(health)})
    assert "FORGED NAME" not in out.text and "name: health\n" in out.text


def test_a_handler_that_returns_without_selecting_is_a_defect(rig):
    d, _, _ = rig
    d._handlers["pick"] = lambda ctx, port, *, address=None: (SelectionBlock(None, None),)
    for _ in range(2):  # the first response and the replay alike
        with pytest.raises(HandlerContractViolation):
            d.invoke("pick", {}, invocation_id="Z" * 8)


def test_a_refusal_after_selecting_is_a_defect_and_the_selection_stands(rig):
    d, _, _ = rig
    health = mint_project(d, "health")

    def late(ctx, port, *, address=None):
        port.select(_address(address))
        raise Refused(Refusal("invalid-input", "refused after selecting"))

    d._handlers["pick"] = late
    with pytest.raises(HandlerContractViolation):
        d.invoke("pick", {"address": str(health)}, invocation_id="L" * 8)
    assert d.selection == health  # the ledger line is truth
    assert "name: health\n" in d.invoke("pick", {"address": str(health)}, invocation_id="L" * 8).text


def test_a_long_name_continues_from_the_ledger_without_the_handler(rig):
    d, _, _ = rig
    out = d.invoke("project", {"name": "n" * 600, "query": QUERY})
    import re
    address = "coord:" + re.search(r"project:([0-9a-f]{32})\.", out.text).group(1)
    first = d.invoke("pick", {"address": address}, invocation_id="C" * 8)
    cursor = first.text.rsplit("cursor ", 1)[1].strip()
    d._handlers["pick"] = lambda *a, **k: pytest.fail("a continuation must not run the handler")
    second = d.invoke("pick", {}, cursor=cursor)
    assert second.text and "n" * 50 in second.text
```

- [ ] **Step 2: Run them to verify they fail**

Run: `just test-one tests/test_session_class.py tests/test_schema.py tests/test_report.py tests/test_render.py`
Expected: FAIL — `SessionPort`, `SelectionBlock` and `audit_session_report` do not exist; `session` is not a write class.

- [ ] **Step 3: The class, the block and the audit**

`python/src/science/schema.py`:

```python
WRITE_CLASS_KINDS = frozenset({"read-only", "coordination", "mints", "publishes", "session"})
```

and in `_parse_write_class`:

```python
    if raw in ("read-only", "coordination", "publishes", "session"):
        _require(not routes_raw, path, "write.routes", f"{raw} takes no routes")
        return WriteClass(raw)
    _require(raw.startswith("mints:"), path, "write_class",
             "must be read-only | coordination | session | mints:<kinds> | publishes")
```

`python/src/science/report.py` — add after `Text`, and widen the union:

```python
@dataclass(frozen=True)
class SelectionBlock:
    """What a `session` invocation reports (coordination design §4.1): the
    selection it recorded, as the project's address pinned to the revision it
    resolved to and the name that revision carries, or nothing selected."""
    address: str | None
    name: str | None


Block = Heading | KeyVals | RecordBlock | Finding | Text | SelectionBlock
```

and in `serialize_block`, before the final `raise`:

```python
        case SelectionBlock(None, _):
            return "selected: none\n"
        case SelectionBlock(address, name):
            return f"selected: {address}\nname: {name}\n"
```

`python/src/science/render.py` — import `SelectionBlock` beside `RecordBlock`, and add after `audit_write_report`:

```python
def audit_session_report(report: Report, recorded: str | None) -> None:
    """Coordination design §4.1: a `session` report is exactly one selection
    block naming what the ledger recorded — the pinned address, or None."""
    if len(report) != 1 or type(report[0]) is not SelectionBlock:
        raise AuditViolation("a session report is exactly one selection block")
    if report[0].address != recorded:
        raise AuditViolation(
            f"the selection block names {report[0].address!r}; the ledger recorded {recorded!r}"
        )
```

- [ ] **Step 4: The dispatcher's session path**

In `python/src/science/dispatch.py`, import `SelectionBlock` from `science.report` (`from science.report import Report, SelectionBlock, serialize_block`). `HandlerContractViolation` now covers a second defect, so widen its docstring's first line to "A write handler raised a surface refusal after it had already acted, or a session handler broke its one-selection contract." and leave the rest. Add after `Outcome`:

```python
class SessionPort:
    """What a `session`-class handler receives in place of a scoped writer
    (coordination design §4.1): one method, and no way to act on a corpus."""

    def __init__(self, select: Callable) -> None:
        self._select = select

    def select(self, address):
        """Make `address` — an unpinned project address, or None to clear —
        the session's selection. Returns it pinned to the revision it resolved
        to, or None."""
        return self._select(address)
```

Factor the claim handling `_invoke_write` and the session path share. Add:

```python
    def _claim(self, decl: Declaration, canonical: Mapping[str, object], iid: str):
        """Claim `iid` for this command and payload: `ClaimDone` to replay or
        `ClaimFresh` to run, and every other claim refuses. The caller holds
        the dispatcher lock."""
        from beliefs.session import ClaimDone, ClaimFresh, ClaimMismatch, ClaimOpen

        claim = self._session.claim_invocation(iid, decl.name, input_digest(canonical))
        if isinstance(claim, ClaimOpen):
            raise Refused(
                Refusal("outcome-unknown", "a prior attempt is open; its outcome is unknown"), iid)
        if isinstance(claim, ClaimMismatch):
            raise Refused(
                Refusal("input-mismatch", "invocation_id was used with a different payload"), iid)
        if not isinstance(claim, (ClaimDone, ClaimFresh)):  # fail closed, never execute
            raise TypeError(f"unknown claim type from the session: {claim!r}")
        return claim
```

and in `_invoke_write`, replace the block from `claim = self._session.claim_invocation(...)` through the `raise TypeError(...)` with:

```python
            claim = self._claim(decl, canonical, iid)
            if isinstance(claim, ClaimDone):
                return Outcome(self._replay_outcome(decl, claim.outcome, iid, (0, 0)), iid)
```

(drop `ClaimFresh`, `ClaimMismatch` and `ClaimOpen` from that method's import). Route the class in `invoke`, ahead of the write branch:

```python
            if decl.write_class.kind != "read-only":
                if project is not None:
                    raise Refused(Refusal(
                        "invalid-input", "no write takes `project`; a write binds to the session's selection"))
                if decl.write_class.kind == "session":
                    return self._invoke_session(decl, canonical, iid)
                return self._invoke_write(decl, canonical, iid)
```

Add the session path after `_invoke_write`:

```python
    def _select(self, iid: str, address):
        # The ledger line first, the endpoint's state after it: a line that did
        # not append changed nothing, and a line that did is live even if this
        # invocation never closes (beliefs selection-ledger design decision 4).
        pinned = self._session.select_project(iid, address)
        self._selection = None if pinned is None else pinned.unpinned()
        return pinned

    def _invoke_session(self, decl: Declaration, canonical: Mapping[str, object], iid: str) -> Outcome:
        """A `session`-class invocation (coordination design §4.1): the write
        protocol's claim, open and close, a port instead of a writer, and one
        selection block rebuilt from the ledger as its report."""
        from beliefs.errors import WriteRefused
        from beliefs.session import ClaimDone

        from science.render import audit_session_report

        if self._session is None:
            raise Refused(Refusal("permit-exceeded", "no writer session on this surface"), iid)
        with self._lock:
            claim = self._claim(decl, canonical, iid)
            if isinstance(claim, ClaimDone):
                return Outcome(self._replay_session(decl, claim.outcome, iid), iid)
            port = SessionPort(lambda address: self._select(iid, address))
            try:
                report = self._handlers[decl.name](self._context(), port, **canonical)
            except WriteRefused as caught:
                # The port's one kernel refusal (ProjectNotResolvable) is raised
                # before the line is appended.
                return self._close_refused(iid, self._kernel_refusal(caught))
            except Refused as caught:
                if self._session.invocation_selection(iid) is None:
                    return self._close_refused(iid, caught.refusal)
                self._session.close_invocation(iid, {"done": []})
                raise HandlerContractViolation(
                    f"{decl.name} refused {caught.refusal.code!r} after selecting; "
                    "a session handler validates before it selects"
                ) from caught
            line = self._session.invocation_selection(iid)
            try:
                if line is None:
                    raise HandlerContractViolation(
                        f"{decl.name} returned without selecting; a session handler selects exactly once")
                audit_session_report(report, None if line.project is None else str(line.project))
            finally:
                # Close first in every case, as a write does: the ledger records
                # what happened whether or not the report survives its audit.
                self._session.close_invocation(iid, {"done": []})
            return Outcome(
                self._render_write(decl.output_budget, self._selection_report(line), iid, (0, 0)), iid)

    def _selection_report(self, line) -> Report:
        """The canonical session report, rebuilt from the ledger's selection
        line. The name is read from the pinned revision, which is immutable, so
        a replay after a rename renders what the selection was."""
        if line.project is None:
            return (SelectionBlock(None, None),)
        node = self._ctx.coordination().resolve(line.project)
        if node is None:
            raise RuntimeError(f"{line.project}: the recorded selection's revision is not in the configured corpora")
        return (SelectionBlock(str(line.project), node.title),)

    def _replay_session(self, decl: Declaration, outcome: Mapping[str, object], iid: str) -> str:
        if "refusal" in outcome:
            refusal = outcome["refusal"]
            raise Refused(Refusal(refusal["code"], refusal["message"], refusal.get("data", {})), iid)
        line = self._session.invocation_selection(iid)
        if line is None:
            raise HandlerContractViolation(f"{decl.name} closed done with no selection line for {iid}")
        return self._render_write(decl.output_budget, self._selection_report(line), iid, (0, 0))
```

In `_continue_write`, replace `report = self._minted_report(record.outcome["done"])` with:

```python
        if decl.write_class.kind == "session":
            if record.selection is None:
                raise HandlerContractViolation(
                    f"{command} closed done with no selection line for {cursor.invocation_id}")
            report = self._selection_report(record.selection)
        else:
            report = self._minted_report(record.outcome["done"])
```

- [ ] **Step 5: Run the tests, then the inner loop**

Run: `just test-one tests/test_session_class.py tests/test_schema.py tests/test_report.py tests/test_render.py tests/test_write_dispatch.py tests/test_dispatch_refusals.py`, then `just test-fast`
Expected: PASS — including the existing write-dispatch tests over the refactored `_claim`.

- [ ] **Step 6: Commit**

```bash
tasks check
git add python tasks
git commit -m "feat(dispatch): the session write class and the selection block"
```

---

### Task 3: `project-select`

**Files:**
- Create: `commands/project-select/command.toml`, `commands/project-select/prompt.md`, `python/src/science/commands/project_select.py`
- Modify: `python/src/science/loader.py` (the handler lead for a `session` declaration)
- Modify: `tools/cli.toml` (science section); regenerate `adapters/claude-code/`
- Modify: `python/tests/test_cmd_subordinate.py`, `python/tests/test_cmd_revise.py` (select through the command where they set `d._selection`)
- Test: `python/tests/test_cmd_project_select.py` (create)

**Interfaces:**
- Consumes: Task 1's `resolve_project_ref`; Task 2's `SessionPort.select`, `SelectionBlock`; `science.coordination.resolve_one`.
- Produces: the `project-select` command (`target`, `clear`); `resolve_handlers` requires a `session` handler to lead with `ctx, port`.

- [ ] **Step 1: Write the failing tests**

Create `python/tests/test_cmd_project_select.py`:

```python
"""Spec §3.7: project-select."""
import io
import json
import re

import pytest

from helpers.world import QUERY, build_world_without_coordination, coordination_rig, mint_project
from science.refusal import Refused

NAMES = ("project", "project-select", "question", "revise")


def _refused(call, code):
    with pytest.raises(Refused) as caught:
        call()
    assert caught.value.refusal.code == code
    return caught.value.refusal


def test_selecting_by_name_and_by_address(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        health, cancer = mint_project(d, "health"), mint_project(d, "cancer")
        by_name = d.invoke("project-select", {"target": "health"})
        assert d.selection == health
        revision = ctx.coordination().resolve(health).uid
        assert by_name.text == f"selected: {health}@{revision}\nname: health\n"
        assert "name: cancer\n" in d.invoke("project-select", {"target": str(cancer)}).text
        assert d.selection == cancer


def test_a_question_lands_under_the_selected_project_and_clear_unselects(certified_work):
    """P2 through the real command: selected, a question mints; cleared, it refuses."""
    question = {"name": "Does PHF19 track stage?", "query": QUERY}
    with coordination_rig(certified_work, NAMES) as (d, _):
        health = mint_project(d, "health")
        d.invoke("project-select", {"target": "health"})
        assert f"[question] question:{health.project}." in d.invoke("question", question).text
        assert d.invoke("project-select", {"clear": True}).text == "selected: none\n"
        assert d.selection is None
        _refused(lambda: d.invoke("question", question), "no-current-project")


def test_a_shared_name_is_ambiguous_and_the_address_still_selects(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        first, second = mint_project(d, "health"), mint_project(d, "health")
        refusal = _refused(lambda: d.invoke("project-select", {"target": "health"}), "ambiguous-project")
        assert sorted(c["address"] for c in refusal.data["candidates"]) == sorted([str(first), str(second)])
        assert d.selection is None
        d.invoke("project-select", {"target": str(second)})
        assert d.selection == second


def test_an_unknown_project_refuses_and_replays(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        for target in ("nope", "coord:" + "f" * 32):
            for _ in range(2):
                _refused(lambda: d.invoke("project-select", {"target": target}, invocation_id="U" * 8 + target[-1]),
                         "unknown-project")
        assert d.selection is None


def test_a_rename_leaves_the_selection_standing(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        health = mint_project(d, "health")
        d.invoke("project-select", {"target": "health"})
        d.invoke("revise", {"address": str(health), "name": "human health"})
        assert d.selection == health
        assert f"question:{health.project}." in d.invoke("question", {"name": "q", "query": QUERY}).text


@pytest.mark.parametrize("inputs", [{}, {"clear": False}, {"target": "health", "clear": True},
                                    {"target": ""}, {"target": "coord:zzz"},
                                    {"target": "coord:" + "a" * 32 + "/" + "b" * 32}])
def test_malformed_requests_refuse_before_any_selection(certified_work, inputs):
    with coordination_rig(certified_work, NAMES) as (d, _):
        health = mint_project(d, "health")
        d.invoke("project-select", {"target": "health"})
        _refused(lambda: d.invoke("project-select", inputs), "invalid-input")
        assert d.selection == health


def test_a_divergent_project_refuses_with_every_tip_and_selects_nothing(certified_work, monkeypatch):
    """Two tips cannot arise in one root, so the resolver is stubbed to report them."""
    from beliefs.coordination import CoordinationRefused
    from beliefs.corpus import CoordinationResolver

    with coordination_rig(certified_work, NAMES) as (d, ctx):
        health, cancer = mint_project(d, "health"), mint_project(d, "cancer")
        d.invoke("project-select", {"target": "cancer"})
        tips = (ctx.coordination().resolve(health).uid, "e" * 32)
        resolve = CoordinationResolver.resolve
        monkeypatch.setattr(
            CoordinationResolver, "resolve",
            lambda self, address: CoordinationRefused("divergent-view", tips)
            if address == health else resolve(self, address))
        refusal = _refused(lambda: d.invoke("project-select", {"target": str(health)}), "kernel-refused")
        assert refusal.data == {"kind": "divergent-view", "tips": sorted(tips)}
        assert d.selection == cancer


def test_without_coordination_every_form_refuses_naming_the_setting(certified_work):
    from science.config import ReadContext
    from science.dispatch import Dispatcher
    from science.loader import production_tree, resolve_handlers
    from science.session import open_session

    cfg = build_world_without_coordination(certified_work)
    decls = tuple(decl for decl in production_tree() if decl.name == "project-select")
    session = open_session(cfg)
    try:
        d = Dispatcher(decls, resolve_handlers(decls), ReadContext.open(cfg), session=session)
        for inputs in ({"clear": True}, {"target": "health"}):
            refusal = _refused(lambda: d.invoke("project-select", inputs), "invalid-input")
            assert "coordination = false" in refusal.message
    finally:
        session.close()


def test_a_session_handler_must_lead_with_ctx_and_port(monkeypatch):
    import science.commands.project_select as module
    from science.loader import production_tree, resolve_handlers
    from science.schema import DeclarationError

    decls = tuple(decl for decl in production_tree() if decl.name == "project-select")
    monkeypatch.setattr(module, "handle", lambda ctx, writer, *, target=None, clear=None: ())
    with pytest.raises(DeclarationError) as caught:
        resolve_handlers(decls)
    assert "['ctx', 'port']" in str(caught.value)


def test_over_mcp_stdio_a_selection_replays_and_a_refusal_carries_its_envelope(certified_work, short_tmp):
    """Framework §9.4: the new write through one transport, with replay and
    the refusal envelope."""
    from helpers.world import write_cli_config
    from science.mcp import serve
    from test_mcp import rpc

    def call(index, name, arguments):
        return json.dumps(rpc("tools/call", {"name": name, "arguments": arguments}, id=index))

    select = {"target": "health", "invocation_id": "S" * 8}
    unknown = {"target": "nope", "invocation_id": "U" * 8}
    frames = [call(1, "project", {"name": "health", "query": QUERY}),
              call(2, "project-select", select), call(3, "project-select", select),
              call(4, "project-select", unknown), call(5, "project-select", unknown)]
    stdout = io.StringIO()
    serve(write_cli_config(certified_work, service_socket=short_tmp / "service.sock"),
          stdin=io.BytesIO(("\n".join(frames) + "\n").encode()), stdout=stdout, stderr=io.StringIO())
    minted, first, again, refused, replayed = [json.loads(line)["result"] for line in stdout.getvalue().splitlines()]
    project = re.search(r"project:([0-9a-f]{32})\.", minted["content"][0]["text"]).group(1)
    assert first["content"][0]["text"].startswith(f"selected: coord:{project}@")
    assert first == again and first["structuredContent"] == {"invocation_id": "S" * 8}
    assert refused["isError"] is True and refused == replayed
    assert refused["structuredContent"]["refusal"]["code"] == "unknown-project"
    assert refused["structuredContent"]["invocation_id"] == "U" * 8
```

- [ ] **Step 2: Run them to verify they fail**

Run: `just test-one tests/test_cmd_project_select.py`
Expected: FAIL — no `project-select` command.

- [ ] **Step 3: The declaration, the prompt, the handler and the loader rule**

`commands/project-select/command.toml`:

```toml
schema_version = 1
name = "project-select"
purpose = "Select the current project for this session, or clear it."
write_class = "session"
output_budget = 2048

[inputs.target]
type = "string"
required = false
doc = "The project to select: its name, or its coord:<project> address."
[inputs.clear]
type = "bool"
required = false
default = false
doc = "Clear the selection, so that enumerations read the whole world."

[reads]
families = ["coordination"]
```

`commands/project-select/prompt.md`:

```markdown
Run `project-select` to choose the project this session works in: give
`target` a project's name, or its `coord:<project>` address when two
projects share a name. The selection is the address, so a later rename
leaves it standing. It scopes what `next` and `project-show` enumerate, and
it is the project a new question, hypothesis, task or decision lands under.
`clear` unselects, after which enumerations read the whole world. Report
the selection block as returned; on `ambiguous-project`, show the
candidates and ask which address was meant.
```

`python/src/science/commands/project_select.py`:

```python
"""project-select: the session's current project (spec §3.7)."""
from __future__ import annotations

from science.coordination import resolve_one, resolve_project_ref
from science.refusal import Refusal, Refused
from science.report import Report, SelectionBlock


def handle(ctx, port, *, target=None, clear=None) -> Report:
    # Canonicalization supplies `clear`'s declared false; the handler default
    # is None because the loader requires it of every optional input.
    ctx.coordination()  # `coordination = false` refuses by name, a clear included
    if (target is None) == (not clear):
        raise Refused(Refusal("invalid-input", "give exactly one of `target` and `clear`"))
    if clear:
        port.select(None)
        return (SelectionBlock(None, None),)
    address = resolve_project_ref(ctx, target)
    resolve_one(ctx, address)  # a divergent project refuses here, naming every tip
    pinned = port.select(address)
    return (SelectionBlock(str(pinned), ctx.coordination().resolve(pinned).title),)
```

In `python/src/science/loader.py`, replace the `lead = (...)` expression in `resolve_handlers`:

```python
        kind = declaration.write_class.kind
        # A session handler gets a session port, never a kernel writer
        # (coordination design §4.1); the name says which it was handed.
        lead = {"read-only": ["ctx"], "session": ["ctx", "port"]}.get(kind, ["ctx", "writer"])
```

- [ ] **Step 4: Select through the command in the part 1 tests**

`python/tests/test_cmd_subordinate.py` and `python/tests/test_cmd_revise.py` set `d._selection = ...` directly with a comment pointing here. Add `"project-select"` to each file's `NAMES`, and replace each assignment:

- `d._selection = project` → `d.invoke("project-select", {"target": str(project)})`
- `d._selection = mint_project(d)` → `d.invoke("project-select", {"target": str(mint_project(d))})`

Leave `test_project_field.py`'s one direct assignment: its rig has no session command by design.

- [ ] **Step 5: The CLI row and the adapters**

In `tools/cli.toml`, after the `[[cli.science.commands]]` row for `reuse`, add:

```toml
[[cli.science.commands]]
path = ["project-select"]
summary = "Select the current project for this session, or clear it"
options = [
  { shared = "config", value = "path" },
  { names = ["--invocation-id"], value = "string" },
  { names = ["--continue"], value = "string" },
  { names = ["--target"], value = "string" },
  { names = ["--clear", "--no-clear"], value = "none" },
]
```

Then `cd python && uv run science adapters build`.

- [ ] **Step 6: Run the tests, then the inner loop**

Run: `just test-one tests/test_cmd_project_select.py tests/test_cmd_subordinate.py tests/test_cmd_revise.py tests/test_cli_surface.py tests/test_adapters.py`, then `just test-fast`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
tasks check
git add commands/project-select adapters tools/cli.toml python tasks
git commit -m "feat(commands): project-select"
```

---

### Task 4: `projects` and `project-show`

**Files:**
- Create: `commands/projects/command.toml`, `commands/projects/prompt.md`, `python/src/science/commands/projects.py`
- Create: `commands/project-show/command.toml`, `commands/project-show/prompt.md`, `python/src/science/commands/project_show.py`
- Modify: `python/tests/helpers/world.py` (`mint_projects`)
- Modify: `tools/cli.toml` (science section); regenerate `adapters/claude-code/`
- Test: `python/tests/test_cmd_projects.py` (create)

**Interfaces:**
- Consumes: Task 1's `tip_nodes`, `selected_project`, the `project` field and the CLI's `--project`; Task 3's `project-select`; `CoordinationResolver.standing(kind, project=)`.
- Produces: the `projects` command (read-only, no inputs) and the `project-show` command (read-only, `selects = true`, no inputs); `helpers.world.mint_projects(cfg, *names) -> list[CoordinationAddress]`, which opens a session over `cfg`, mints one project per name and closes it.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/helpers/world.py`:

```python
def mint_projects(cfg: ScienceConfig, *names: str) -> list:
    """Open a session over `cfg`, mint one project per name, and close it: the
    addresses, in order. For tests that need projects standing before a
    launcher or a sessionless read starts."""
    with open_rig(cfg, ("project",)) as (dispatcher, _):
        return [mint_project(dispatcher, name) for name in names]
```

Create `python/tests/test_cmd_projects.py`:

```python
"""Spec §3.8: projects and project-show."""
import re

import pytest

from helpers.world import QUERY, build_world_without_coordination, coordination_rig, mint_project
from science.refusal import Refused

NAMES = ("project", "project-select", "projects", "project-show",
         "question", "hypothesis", "task", "decide", "revise")
CANONICAL_QUERY = '{"clauses":[{"all":[{"kinds":["proposition"]}]}],"version":"science.view-query.v1"}'


def _refused(call, code):
    with pytest.raises(Refused) as caught:
        call()
    assert caught.value.refusal.code == code
    return caught.value.refusal


def _task(d, name):
    out = d.invoke("task", {"name": name})
    project, local = re.search(r"task:([0-9a-f]{32})\.([0-9a-f]{32})\.", out.text).groups()
    return f"coord:{project}/{local}"


def _twin(node, title):
    """A sibling revision of `node`: pydantic copy differing in revision id and name."""
    return node.model_copy(update={"id": node.id.rsplit(".", 1)[0] + "." + "e" * 32, "uid": "e" * 32,
                                   "title": title})


def _diverge(monkeypatch, kind, address, real, twin):
    """Two tips cannot arise in one root (coordination §4.3), so the resolver's
    enumeration is stubbed to report them for one address."""
    from beliefs.coordination import CoordinationRefused
    from beliefs.corpus import CoordinationResolver

    standing, revision = CoordinationResolver.standing, CoordinationResolver.revision

    def fake_standing(self, asked, *, project=None):
        found = dict(standing(self, asked, project=project))
        if asked == kind:
            found[address] = CoordinationRefused("divergent-view", (real.uid, twin.uid))
        return found

    monkeypatch.setattr(CoordinationResolver, "standing", fake_standing)
    monkeypatch.setattr(CoordinationResolver, "revision",
                        lambda self, uid: twin if uid == twin.uid else revision(self, uid))


def test_projects_lists_by_name_then_address_and_marks_the_selected(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        zeta, first, second = mint_project(d, "zeta"), mint_project(d, "alpha"), mint_project(d, "alpha")
        d.invoke("project-select", {"target": "zeta"})
        text = d.invoke("projects", {}).text
        revision = {address: ctx.coordination().resolve(address).uid for address in (zeta, first, second)}
    low, high = sorted((first, second), key=str)
    assert text == ("## Projects\nprojects:\n"
                    f"  {low}: alpha @{revision[low]}\n"
                    f"  {high}: alpha @{revision[high]}\n"
                    f"  {zeta}: zeta @{revision[zeta]} (selected)\n")


def test_projects_with_none_says_so(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        assert d.invoke("projects", {}).text == "## Projects\nprojects:\n  none: no projects\n"


def test_a_divergent_project_renders_once_with_every_tip(certified_work, monkeypatch):
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        health = mint_project(d, "health")
        real = ctx.coordination().resolve(health)
        twin = _twin(real, "human health")
        _diverge(monkeypatch, "project", health, real, twin)
        text = d.invoke("projects", {}).text
    assert text.count(str(health)) == 1
    assert f"  {health}: divergent: " in text
    assert f"health @{real.uid}" in text and f"human health @{twin.uid}" in text


def test_project_show_renders_the_selection_in_section_order(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        health = mint_project(d, "health")
        d.invoke("project-select", {"target": "health"})
        hold, run = _task(d, "hold"), _task(d, "run")
        d.invoke("revise", {"address": run, "status": "done"})
        d.invoke("question", {"name": "Does PHF19 track stage?", "query": QUERY})
        d.invoke("hypothesis", {"name": "PHF19 rises with stage", "query": QUERY})
        d.invoke("decide", {"name": "Use the coarse query", "body": "No disease vocabulary is bound yet."})
        text = d.invoke("project-show", {}).text
        revision = ctx.coordination().resolve(health).uid
    assert text.startswith(
        "## Project: health\nproject:\n"
        f"  address: {health}\n  revision: {revision}\n  name: health\n  query: {CANONICAL_QUERY}\n"
        "open tasks:\n"
        f"  {hold}: open: hold\n")
    titles = ["open tasks:", "questions:", "hypotheses:", "decisions:", "closed tasks:"]
    positions = [text.index("\n" + title) for title in titles]
    assert positions == sorted(positions)
    assert text.endswith(f"closed tasks:\n  {run}: done: run\n")  # a `done` revision moved it (spec §9)
    assert ": Does PHF19 track stage?\n" in text and ": Use the coarse query\n" in text


def test_a_project_with_no_records_says_so(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        d.invoke("project-select", {"target": str(mint_project(d, "health"))})
        assert d.invoke("project-show", {}).text.endswith("No questions, hypotheses, tasks or decisions yet.\n")


def test_project_binds_this_show_only(certified_work):
    """P8 at the dispatcher: the field shows another project and the
    endpoint's selection is unchanged afterwards."""
    with coordination_rig(certified_work, NAMES) as (d, _):
        health, cancer = mint_project(d, "health"), mint_project(d, "cancer")
        d.invoke("project-select", {"target": "health"})
        assert d.invoke("project-show", {}, project="cancer").text.startswith("## Project: cancer\n")
        assert d.invoke("project-show", {}, project=str(cancer)).text.startswith("## Project: cancer\n")
        assert d.selection == health
        assert d.invoke("project-show", {}).text.startswith("## Project: health\n")


def test_nothing_selected_and_nothing_named_refuses(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        mint_project(d, "health")
        refusal = _refused(lambda: d.invoke("project-show", {}), "no-current-project")
        _refused(lambda: d.invoke("project-show", {}, project="nope"), "unknown-project")
    assert "project-select" in refusal.message and "--project" in refusal.message


def test_a_revised_project_shows_its_new_tip_without_reselecting(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        health = mint_project(d, "health")
        d.invoke("project-select", {"target": "health"})
        d.invoke("revise", {"address": str(health), "name": "human health"})
        assert d.invoke("project-show", {}).text.startswith("## Project: human health\n")


def test_a_divergent_task_renders_once_under_open_tasks_with_every_tip(certified_work, monkeypatch):
    from beliefs.coordination import CoordinationAddress

    with coordination_rig(certified_work, NAMES) as (d, ctx):
        d.invoke("project-select", {"target": str(mint_project(d, "health"))})
        hold = CoordinationAddress.parse(_task(d, "hold"))
        real = ctx.coordination().resolve(hold)
        twin = _twin(real, "hold it")
        _diverge(monkeypatch, "task", hold, real, twin)
        text = d.invoke("project-show", {}).text
    assert "closed tasks:" not in text and text.count(str(hold)) == 1
    assert f"open tasks:\n  {hold}: divergent: " in text
    assert f"hold @{real.uid}" in text and f"hold it @{twin.uid}" in text


def test_without_coordination_both_reads_refuse_naming_the_setting(certified_work):
    from science.config import ReadContext
    from science.dispatch import Dispatcher
    from science.loader import production_tree, resolve_handlers

    decls = tuple(decl for decl in production_tree() if decl.name in ("projects", "project-show"))
    d = Dispatcher(decls, resolve_handlers(decls),
                   ReadContext.open(build_world_without_coordination(certified_work)))
    for command in ("projects", "project-show"):
        assert "coordination = false" in _refused(lambda: d.invoke(command, {}), "invalid-input").message


def test_the_project_reads_render_identically_through_the_cli_and_mcp(certified_work, capsys):
    """Framework §9.4: each new read, byte for byte, through both transports."""
    from helpers.world import mint_projects, write_cli_config
    from science.cli import main
    from science.config import ReadContext, load_config
    from science.dispatch import Dispatcher
    from science.loader import production_tree, resolve_handlers
    from science.mcp import handle_request
    from test_mcp import rpc

    config_path = write_cli_config(certified_work)
    config = load_config(config_path)
    (health,) = mint_projects(config, "health")
    declarations = production_tree()
    dispatcher = Dispatcher(declarations, resolve_handlers(declarations), ReadContext.open(config))
    for argv, name, arguments in (
        (["projects"], "projects", {}),
        (["project-show", "--project", str(health)], "project-show", {"project": str(health)}),
    ):
        assert main([*argv, "--config", str(config_path)]) == 0
        cli_text = capsys.readouterr().out
        mcp_text = handle_request(rpc("tools/call", {"name": name, "arguments": arguments}),
                                  dispatcher, declarations)["result"]["content"][0]["text"]
        assert cli_text == mcp_text and "health" in cli_text
```

- [ ] **Step 2: Run them to verify they fail**

Run: `just test-one tests/test_cmd_projects.py`
Expected: FAIL — no `projects` or `project-show` command.

- [ ] **Step 3: `projects`**

`commands/projects/command.toml`:

```toml
schema_version = 1
name = "projects"
purpose = "List every project in the world, marking the selected one."
write_class = "read-only"
output_budget = 16384

[reads]
families = ["coordination"]
```

`commands/projects/prompt.md`:

```markdown
Run `projects` to list every project in the world: its `coord:<project>`
address, its name, the revision that stands, and a mark on the one this
session has selected. Two projects may share a name; the address tells
them apart and is what `project-select` takes when a name is ambiguous. A
project shown as `divergent` has more than one standing revision: report
it as listed, and do not pick one.
```

`python/src/science/commands/projects.py`:

```python
"""projects: every standing project, and which one is selected (spec §3.8)."""
from __future__ import annotations

from science.coordination import tip_nodes
from science.report import Heading, KeyVals, Report


def _revisions(tips) -> str:
    return "; ".join(f"{tip.title} @{tip.uid}" for tip in tips)


def handle(ctx) -> Report:
    resolver = ctx.coordination()
    rows = []
    for address, resolved in resolver.standing("project").items():
        tips = tip_nodes(resolver, resolved)
        if not tips:
            text = "no standing revision"
        elif len(tips) == 1:
            text = _revisions(tips)
        else:
            text = "divergent: " + _revisions(tips)  # listed once, never dropped
        if address == ctx.selection:
            text += " (selected)"
        rows.append((min((tip.title for tip in tips), default=""), str(address), text))
    rows.sort()
    return (Heading("Projects"),
            KeyVals("projects", tuple((address, text) for _, address, text in rows)
                    or (("none", "no projects"),)))
```

- [ ] **Step 4: `project-show`**

`commands/project-show/command.toml`:

```toml
schema_version = 1
name = "project-show"
purpose = "Show one project: its query and its questions, hypotheses, tasks and decisions."
write_class = "read-only"
selects = true
output_budget = 16384

[reads]
families = ["coordination"]
```

`commands/project-show/prompt.md`:

```markdown
Run `project-show` to see one project: the selected one, or the one named
with `project` for this call only, which leaves the session's selection
where it was. It shows the project's address, standing revision, name and
canonical query, then its records — open tasks first, then questions,
hypotheses, decisions, and closed tasks — each with its address. With
nothing selected and no project named it refuses; select one with
`project-select` or name one.
```

`python/src/science/commands/project_show.py`:

```python
"""project-show: one project and its subordinate records (spec §3.8)."""
from __future__ import annotations

import json

from beliefs import stored
from beliefs.view_query import stored_query

from science.coordination import selected_project, tip_nodes
from science.refusal import Refusal, Refused
from science.report import Heading, KeyVals, Report, Text

_VIEWS = (("question", "questions"), ("hypothesis", "hypotheses"), ("decision", "decisions"))


def _entries(resolver, kind: str, project) -> list:
    """(sort name, address, tips) for every address of `kind` under `project`,
    by name then address."""
    found = []
    for address, resolved in resolver.standing(kind, project=project).items():
        tips = tip_nodes(resolver, resolved)
        found.append((min((tip.title for tip in tips), default=""), str(address), tips))
    return sorted(found, key=lambda entry: entry[:2])


def _status(node) -> str:
    return node.facets[stored.COORDINATION_FACET]["status"]


def _label(tips, describe) -> str:
    if not tips:
        return "no standing revision"
    if len(tips) > 1:  # listed once, never dropped
        return "divergent: " + "; ".join(f"{tip.title} @{tip.uid}" for tip in tips)
    return describe(tips[0])


def _named(node) -> str:
    return node.title


def _task(node) -> str:
    return f"{_status(node)}: {node.title}"


def handle(ctx) -> Report:
    project = selected_project(ctx)
    if project is None:
        raise Refused(Refusal(
            "no-current-project",
            "no project is selected; select one with `project-select`, or name one with `--project`",
        ))
    resolver = ctx.coordination()
    query = json.dumps(stored_query(project).projection(), sort_keys=True, separators=(",", ":"))
    blocks: list = [
        Heading(f"Project: {project.title}"),
        KeyVals("project", (("address", str(ctx.selection)), ("revision", project.uid),
                            ("name", project.title), ("query", query))),
    ]
    open_tasks, closed_tasks = [], []
    for entry in _entries(resolver, "task", ctx.selection):
        tips = entry[2]
        # A task with no one tip has no one status, and wants attention: open.
        closed = len(tips) == 1 and _status(tips[0]) != "open"
        (closed_tasks if closed else open_tasks).append(entry)
    sections = [("open tasks", open_tasks, _task)]
    sections += [(title, _entries(resolver, kind, ctx.selection), _named) for kind, title in _VIEWS]
    sections.append(("closed tasks", closed_tasks, _task))
    for title, entries, describe in sections:
        if entries:
            blocks.append(KeyVals(title, tuple((address, _label(tips, describe))
                                               for _, address, tips in entries)))
    if len(blocks) == 2:
        blocks.append(Text("No questions, hypotheses, tasks or decisions yet."))
    return tuple(blocks)
```

- [ ] **Step 5: The CLI rows and the adapters**

In `tools/cli.toml`, after the `project-select` row, add:

```toml
[[cli.science.commands]]
path = ["projects"]
summary = "List every project in the world, marking the selected one"
options = [
  { shared = "config", value = "path" },
  { names = ["--invocation-id"], value = "string" },
  { names = ["--continue"], value = "string" },
]

[[cli.science.commands]]
path = ["project-show"]
summary = "Show one project: its query and its questions, hypotheses, tasks and decisions"
options = [
  { shared = "config", value = "path" },
  { names = ["--invocation-id"], value = "string" },
  { names = ["--continue"], value = "string" },
  { names = ["--project"], value = "string" },
]
```

`--project` is science's own option here, not the shared vocabulary entry, which means a tasks project prefix (spec §10). Then `cd python && uv run science adapters build`.

- [ ] **Step 6: Run the tests, then the inner loop**

Run: `just test-one tests/test_cmd_projects.py tests/test_cli_surface.py tests/test_adapters.py`, then `just test-fast`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
tasks check
git add commands/projects commands/project-show adapters tools/cli.toml python tasks
git commit -m "feat(commands): projects and project-show"
```

---

### Task 5: The launcher's initial selection and `default_project`

**Files:**
- Modify: `python/src/science/config.py` (`_OPTIONAL_KEYS`, `ScienceConfig.default_project`, `load_config`)
- Modify: `python/src/science/session.py` (`open_session(config, project=None)`)
- Modify: `python/src/science/serve.py` (`initial_selection`, `serve(..., project=None)`)
- Modify: `python/src/science/mcp.py` (`serve(..., project=None)`)
- Modify: `python/src/science/cli.py` (`--project` on `serve` and `mcp`; `_framework_verb`)
- Modify: `tools/cli.toml` (the `serve` and `mcp` rows)
- Modify: `python/tests/test_config.py`, `python/tests/test_cli.py`, `python/tests/test_mcp.py`, `python/tests/test_serve.py` (fakes and expected namespaces)
- Test: `python/tests/test_initial_selection.py` (create)

**Interfaces:**
- Consumes: Task 1's `resolve_project_ref`; Task 4's `mint_projects`; `open_attended_session(..., project=)`.
- Produces:
  - `ScienceConfig.default_project` — an unpinned `CoordinationAddress` or None, from the optional `default_project` key.
  - `science.session.open_session(config, project=None)` — `project` is an unpinned project address; an address that does not resolve to one standing project refuses `unknown-project`.
  - `science.serve.initial_selection(config, read_context, project: str | None) -> CoordinationAddress | None`.
  - `science.serve.serve(config, socket_path, declarations=None, handlers=None, stderr=None, project=None)` and `science.mcp.serve(config_path, stdin=None, stdout=None, stderr=None, project=None)`, where `project` is a name or address string; both construct their dispatcher with `selection=`.

- [ ] **Step 1: Write the failing tests**

Append to `python/tests/test_config.py`:

```python
def test_default_project_is_an_unpinned_project_address(tmp_path):
    address = "coord:" + "a" * 32
    cfg = load_config(write_config(tmp_path, extra=f'default_project = "{address}"\n'))
    assert str(cfg.default_project) == address
    assert load_config(write_config(tmp_path)).default_project is None


@pytest.mark.parametrize("value", ['"health"', f'"coord:{"a" * 32}/{"b" * 32}"',
                                   f'"coord:{"a" * 32}@{"c" * 32}"', "3"])
def test_default_project_that_is_not_a_project_address_refuses(tmp_path, value):
    refusal = assert_invalid_config(write_config(tmp_path, extra=f"default_project = {value}\n"))
    assert "default_project" in refusal.message


def test_default_project_without_coordination_refuses_naming_the_setting(tmp_path):
    refusal = assert_invalid_config(write_config(
        tmp_path, coordination="false", extra=f'default_project = "coord:{"a" * 32}"\n'))
    assert "coordination = false" in refusal.message
```

Create `python/tests/test_initial_selection.py`:

```python
"""Spec §5.1, §6: the launcher's initial selection and `default_project`."""
import io
import json
import socket
import threading
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import pytest

from helpers.world import (
    QUERY, build_fixture_world, build_world_without_coordination, mint_projects, write_cli_config,
)
from science.refusal import Refused

QUESTION = {"command": "question", "inputs": {"name": "q", "query": QUERY}}


def _ask(sock, payload):
    with socket.socket(socket.AF_UNIX) as client:
        client.connect(str(sock))
        client.sendall(json.dumps(payload).encode() + b"\n")
        return json.loads(client.makefile().readline())


@contextmanager
def _serving(cfg, sock, **kwargs):
    from science.serve import serve

    server = serve(cfg, sock, stderr=io.StringIO(), **kwargs)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield
    finally:
        server.shutdown()
        server.server_close()


def _recorded_selections(cfg):
    """The `project` of every session-open line under the operations root."""
    ledgers = sorted((cfg.operations_root / "sessions").glob("*/ledger.v1"))
    return [json.loads(path.read_text().splitlines()[0])["project"] for path in ledgers]


def test_serve_opens_under_the_default_project_and_ledgers_it(certified_work, short_tmp):
    from science.config import ReadContext

    cfg = build_fixture_world(certified_work)
    (health,) = mint_projects(cfg, "health")
    sock = short_tmp / "service.sock"
    with _serving(replace(cfg, default_project=health), sock):
        reply = _ask(sock, QUESTION)
    assert reply["ok"] and f"question:{health.project}." in reply["text"]
    revision = ReadContext.open(cfg).coordination().resolve(health).uid
    # The minting session opened with nothing selected; the launcher's is pinned.
    assert sorted(_recorded_selections(cfg), key=str) == sorted([None, f"{health}@{revision}"], key=str)


@pytest.mark.parametrize("named", ["name", "address"])
def test_the_launchers_project_wins_over_the_default(certified_work, short_tmp, named):
    cfg = build_fixture_world(certified_work)
    health, cancer = mint_projects(cfg, "health", "cancer")
    sock = short_tmp / "service.sock"
    project = "cancer" if named == "name" else str(cancer)
    with _serving(replace(cfg, default_project=health), sock, project=project):
        reply = _ask(sock, QUESTION)
    assert reply["ok"] and f"question:{cancer.project}." in reply["text"]


def test_with_neither_the_session_opens_unselected(certified_work, short_tmp):
    cfg = build_fixture_world(certified_work)
    mint_projects(cfg, "health")
    sock = short_tmp / "service.sock"
    with _serving(cfg, sock):
        reply = _ask(sock, QUESTION)
    assert reply["refusal"]["code"] == "no-current-project"


def test_a_default_that_names_no_project_refuses_the_start(certified_work, short_tmp):
    from beliefs.coordination import CoordinationAddress
    from science.serve import serve

    cfg = build_fixture_world(certified_work)
    sock = short_tmp / "service.sock"
    with pytest.raises(Refused) as caught:
        serve(replace(cfg, default_project=CoordinationAddress("f" * 32)), sock)
    assert caught.value.refusal.code == "unknown-project"
    assert not sock.exists()
    assert not (cfg.operations_root / "sessions").exists()  # refused before the session opened


def test_a_launcher_project_that_names_no_project_refuses_the_start(certified_work, short_tmp):
    from science.serve import serve

    cfg = build_fixture_world(certified_work)
    sock = short_tmp / "service.sock"
    with pytest.raises(Refused) as caught:
        serve(cfg, sock, project="nope")
    assert caught.value.refusal.code == "unknown-project"
    assert not sock.exists() and not (cfg.operations_root / "sessions").exists()


def test_a_launcher_project_without_coordination_refuses_naming_the_setting(certified_work, short_tmp):
    from science.serve import serve

    cfg = build_world_without_coordination(certified_work)
    with pytest.raises(Refused) as caught:
        serve(cfg, short_tmp / "service.sock", project="health")
    assert caught.value.refusal.code == "invalid-input"
    assert "coordination = false" in caught.value.refusal.message
    assert not (cfg.operations_root / "sessions").exists()


def _with_default(config_path, address):
    config_path.write_text(config_path.read_text() + f'default_project = "{address}"\n')
    return config_path


def test_mcp_serve_opens_under_the_default_project(certified_work, short_tmp):
    from science.config import load_config
    from science.mcp import serve
    from test_mcp import rpc

    config_path = write_cli_config(certified_work, service_socket=short_tmp / "service.sock")
    (health,) = mint_projects(load_config(config_path), "health")
    _with_default(config_path, health)
    call = rpc("tools/call", {"name": "question", "arguments": QUESTION["inputs"]})
    stdout = io.StringIO()
    serve(config_path, stdin=io.BytesIO((json.dumps(call) + "\n").encode()), stdout=stdout, stderr=io.StringIO())
    (line,) = stdout.getvalue().splitlines()
    assert f"question:{health.project}." in json.loads(line)["result"]["content"][0]["text"]


def test_mcp_serve_refuses_a_default_that_names_no_project(certified_work, short_tmp):
    from science.config import load_config
    from science.mcp import serve

    sock = short_tmp / "service.sock"
    config_path = _with_default(write_cli_config(certified_work, service_socket=sock), "coord:" + "f" * 32)
    with pytest.raises(Refused) as caught:
        serve(config_path, stdin=io.BytesIO(), stdout=io.StringIO(), stderr=io.StringIO())
    assert caught.value.refusal.code == "unknown-project"
    assert not sock.exists()
    assert not (load_config(config_path).operations_root / "sessions").exists()


def test_both_launcher_verbs_take_project(monkeypatch):
    import science.mcp as mcp
    from science.cli import build_parser, main
    from science.loader import production_tree

    parser = build_parser(production_tree())
    assert parser.parse_args(["serve", "--project", "health"]).project == "health"
    assert parser.parse_args(["mcp", "serve", "--project", "health"]).project == "health"
    captured = []
    monkeypatch.setattr(mcp, "serve", lambda path, project=None: captured.append((path, project)))
    assert main(["mcp", "serve", "--config", "science.toml", "--project", "health"]) == 0
    assert captured == [(Path("science.toml"), "health")]
```

Update the fakes and expectations the new keyword reaches:

- `python/tests/test_mcp.py`, `test_cli_mcp_serve_resolves_config_and_starts_server`: `monkeypatch.setattr(mcp, "serve", lambda path, project=None: captured.append((path, project)))` and `assert captured == [(Path("relative-science.toml"), None)]`.
- `python/tests/test_mcp.py`, `test_serve_holds_one_attended_session_and_closes_it`: `def __init__(self, declarations, handlers, context, session=None, selection=None):`.
- `python/tests/test_cli.py`, `test_protocol_options_are_scoped_to_the_verbs_that_consume_them`: both expected namespaces gain `"project": None`.
- `python/tests/test_serve.py`, `test_serve_verb_binds_the_configured_socket`: `def fake_build(config, socket_path, declarations=None, handlers=None, stderr=None, project=None):`.

- [ ] **Step 2: Run them to verify they fail**

Run: `just test-one tests/test_initial_selection.py tests/test_config.py`
Expected: FAIL — `default_project` is an unknown key; `serve` takes no `project`.

- [ ] **Step 3: The configuration key**

In `python/src/science/config.py`: `_OPTIONAL_KEYS = ("service_socket", "default_project")`; add the field after `plans`:

```python
    plans: tuple[OperatorPlan, ...] = ()
    # An unpinned beliefs.coordination.CoordinationAddress or None: the project a
    # launcher opens under and a CLI read falls back to with no live session.
    default_project: object = None
```

Add the parser above `load_config`:

```python
def _project_address(value: object):
    """`default_project` is an address, never a name: names are content and may
    collide or change (coordination design §6)."""
    from beliefs.coordination import CoordinationAddress

    try:
        address = CoordinationAddress.parse(value)
    except ValueError:
        address = None
    if address is None or address.local is not None or address.revision is not None:
        _refuse("config default_project must be a project address, coord:<project>; "
                "a name is content and may change")
    return address
```

In `load_config`, after the `coordination` checks:

```python
    default_project = None
    if "default_project" in raw:
        if coordination is None:
            _refuse("config default_project needs a resolver, and this configuration sets "
                    "`coordination = false`")
        default_project = _project_address(raw["default_project"])
```

and pass `default_project=default_project` to the returned `ScienceConfig`.

- [ ] **Step 4: The session opens under it**

`python/src/science/session.py`:

```python
def open_session(config: ScienceConfig, project=None):
    """Open the configured single corpus as the writer and optional read mount.

    `project`, an unpinned project address, is the initial selection: the
    kernel resolves and pins it into `session-open` before the session
    directory exists, so one that names no standing project refuses here."""
    from beliefs.errors import ProjectNotResolvable, SessionRefused
    from beliefs.session import open_attended_session

    if len(config.world.corpus_roots) != 1:
        raise SessionRefused(
            f"a session needs exactly one corpus root; the config names {len(config.world.corpus_roots)}"
        )
    (root,) = config.world.corpus_roots
    if config.coordination is not None:
        require_coordination_pinned(config)
    elif project is not None:
        raise Refused(Refusal(
            "invalid-input", "coordination = false in this configuration; no project can be selected"))
    try:
        return open_attended_session(
            config.world, config.operations_root, write_root=root, profile=config.profile,
            mounts={root: config.profile} if config.coordination is not None else None,
            store_root=config.store_root, project=project,
        )
    except ProjectNotResolvable as caught:
        raise Refused(Refusal(
            "unknown-project", f"the initial project does not resolve: {caught}",
            {"tips": list(caught.tips)} if caught.tips else {},
        )) from None
```

- [ ] **Step 5: Both launchers**

`python/src/science/serve.py` — add above `serve`:

```python
def initial_selection(config: ScienceConfig, read_context: ReadContext, project: str | None):
    """The session's selection at open (projects design §5.1): the launcher's
    `--project`, by name or address, else the configuration's `default_project`,
    else none."""
    if project is None:
        return config.default_project
    from science.coordination import resolve_project_ref

    return resolve_project_ref(read_context, project)
```

and in `serve` (signature gains `project=None`), replace the lines from `check_socket_path(socket_path)` to the `Dispatcher(...)` construction:

```python
    check_socket_path(socket_path)
    read_context = ReadContext.open(config)
    selection = initial_selection(config, read_context, project)
    session = open_session(config, project=selection)
    try:
        report_findings(session.findings, reported_by=session.session_id,
                        stream=sys.stderr if stderr is None else stderr)
        dispatcher = Dispatcher(declarations, handlers, read_context,
                                session=session, selection=selection)
        return service_server(dispatcher, socket_path, on_close=session.close)
```

`python/src/science/mcp.py` — `serve` gains `project=None`; import `initial_selection` beside `check_socket_path`; and:

```python
    check_socket_path(config.service_socket)
    read_context = ReadContext.open(config)
    selection = initial_selection(config, read_context, project)
    # One attended session for the process lifetime. A world config naming
    # other than exactly one corpus root raises SessionRefused here; that is a
    # launcher misconfiguration and propagates, never a command refusal.
    session = open_session(config, project=selection)
```

with the dispatcher built as `Dispatcher(declarations, resolve_handlers(declarations), read_context, session=session, selection=selection)`.

`python/src/science/cli.py` — in `build_parser`, give both launcher parsers the option:

```python
_LAUNCHER_PROJECT_HELP = "Open the session under this project, by name or coord: address."
```

```python
    serve_parser.add_argument("--project", help=_LAUNCHER_PROJECT_HELP)
    ...
    mcp.add_argument("--project", help=_LAUNCHER_PROJECT_HELP)
```

and in `_framework_verb`: `serve(resolve_config_path(namespace.config), project=namespace.project)` for `mcp`, and `build_server(config, config.service_socket, project=namespace.project)` for `serve`.

- [ ] **Step 6: The CLI rows**

In `tools/cli.toml`, the science `serve` and `mcp` rows each gain the option:

```toml
options = [
  { shared = "config", value = "path" },
  { names = ["--project"], value = "string" },
]
```

- [ ] **Step 7: Run the tests, then the inner loop**

Run: `just test-one tests/test_initial_selection.py tests/test_config.py tests/test_cli.py tests/test_mcp.py tests/test_serve.py tests/test_cli_surface.py tests/test_launcher_stop.py`, then `just test-fast`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
tasks check
git add tools/cli.toml python tasks
git commit -m "feat(launchers): initial selection from --project and default_project"
```

---

### Task 6: The selection query and the CLI's resolution order (P8)

**Files:**
- Modify: `python/src/science/serve.py` (`_answer_query`, the handler)
- Modify: `python/src/science/cli.py` (`_ambient_selection`, `main`)
- Modify: `python/tests/test_cli.py` (`SessionlessDispatcher.__init__`), `python/tests/test_cwd_independence.py` (P1's selection arms)
- Test: `python/tests/test_selection_query.py` (create)

**Interfaces:**
- Consumes: Task 1's `Dispatcher.selection` and `invoke(project=)`; Task 3's `project-select`; Task 4's `project-show`, `projects` and `mint_projects`; Task 5's `default_project` and launcher `project`.
- Produces:
  - The service socket answers the one-line request `{"query": "selection"}` with `{"project": "coord:<project>"}` or `{"project": null}`.
  - `science.cli._ambient_selection(config) -> CoordinationAddress | None`.
  - `test_selection_query.launcher(kind, config_path, sock)` — a context manager running `"serve"` or `"mcp serve"` on a thread, for other test modules.

- [ ] **Step 1: Write the failing tests**

Create `python/tests/test_selection_query.py`:

```python
"""Spec §5.2, §5.3 and P8: a read in any process finds the live session's selection."""
import io
import json
import re
import socket
import socketserver
import subprocess
import sys
import threading
from contextlib import contextmanager
from dataclasses import replace

import pytest

from helpers.world import QUERY, build_fixture_world, mint_projects, write_cli_config
from test_mcp_socket import _BlockingStdin, _request, _wait_for

LAUNCHERS = ("serve", "mcp serve")


@contextmanager
def launcher(kind, config_path, sock):
    """One of the two launchers, live on a thread until the block ends."""
    if kind == "serve":
        from science.config import load_config
        from science.serve import serve

        server = serve(load_config(config_path), sock, stderr=io.StringIO())
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            yield
        finally:
            server.shutdown()
            server.server_close()
        return
    from science.mcp import serve as mcp_serve

    stdin = _BlockingStdin()
    thread = threading.Thread(target=mcp_serve, args=(config_path,),
                              kwargs={"stdin": io.BufferedReader(stdin), "stdout": io.StringIO(),
                                      "stderr": io.StringIO()}, daemon=True)
    thread.start()
    try:
        _wait_for(sock)
        yield
    finally:
        stdin.release()
        thread.join(timeout=30)
        stdin.close()  # only now: the reader thread is done with the fd


def _cli(*args):
    return subprocess.run([sys.executable, "-m", "science.cli", *args],
                          capture_output=True, text=True, timeout=120)


def _mint(sock, name):
    reply = _request(sock, {"command": "project", "inputs": {"name": name, "query": QUERY}})
    return "coord:" + re.search(r"project:([0-9a-f]{32})\.", reply["text"]).group(1)


def _ledger_lines(config_path):
    from science.config import load_config

    root = load_config(config_path).operations_root / "sessions"
    return sum(len(path.read_text().splitlines()) for path in root.glob("*/ledger.v1"))


@pytest.mark.parametrize("kind", LAUNCHERS)
def test_a_new_process_reads_the_live_sessions_selection(certified_work, short_tmp, kind):
    """P8: selected through the endpoint, observed by a fresh CLI process;
    `--project` observes another project and changes nothing."""
    sock = short_tmp / "service.sock"
    config_path = write_cli_config(certified_work, service_socket=sock)
    with launcher(kind, config_path, sock):
        health = _mint(sock, "health")
        _mint(sock, "cancer")
        # The CLI routes the `session` class to whichever launcher bound the socket.
        selected = _cli("project-select", "--config", str(config_path), "--target", "health")
        shown = _cli("project-show", "--config", str(config_path))
        other = _cli("project-show", "--config", str(config_path), "--project", "cancer")
        listed = _cli("projects", "--config", str(config_path))
        after = _request(sock, {"query": "selection"})
    assert selected.returncode == 0 and selected.stdout.startswith(f"selected: {health}@"), selected.stderr
    assert shown.returncode == 0 and shown.stdout.startswith("## Project: health\n"), shown.stderr
    assert other.returncode == 0 and other.stdout.startswith("## Project: cancer\n"), other.stderr
    assert listed.stdout.count("(selected)") == 1 and f"{health}: health" in listed.stdout
    assert after == {"project": health}


@pytest.mark.parametrize("kind", LAUNCHERS)
def test_the_query_answers_from_state_and_ledgers_nothing(certified_work, short_tmp, kind):
    sock = short_tmp / "service.sock"
    config_path = write_cli_config(certified_work, service_socket=sock)
    with launcher(kind, config_path, sock):
        health = _mint(sock, "health")
        assert _request(sock, {"query": "selection"}) == {"project": None}
        _request(sock, {"command": "project-select", "inputs": {"target": "health"}})
        before = _ledger_lines(config_path)
        assert _request(sock, {"query": "selection"}) == {"project": health}  # no invocation id in or out
        assert _ledger_lines(config_path) == before
        unknown = _request(sock, {"query": "epoch"})
        mixed = _request(sock, {"query": "selection", "command": "status"})
    assert unknown["ok"] is False and unknown["refusal"]["code"] == "invalid-input"
    assert mixed["ok"] is False and mixed["refusal"]["code"] == "invalid-input"


def test_each_launcher_refuses_to_start_beside_the_other(certified_work, short_tmp):
    from science.config import load_config
    from science.mcp import serve as mcp_serve
    from science.refusal import Refused
    from science.serve import serve

    sock = short_tmp / "service.sock"
    config_path = write_cli_config(certified_work, service_socket=sock)
    with launcher("mcp serve", config_path, sock):
        with pytest.raises(Refused):
            serve(load_config(config_path), sock)
    with launcher("serve", config_path, sock):
        with pytest.raises(Refused):
            mcp_serve(config_path, stdin=io.BytesIO(), stdout=io.StringIO(), stderr=io.StringIO())


def _config_with_default(work, sock):
    cfg = replace(build_fixture_world(work), service_socket=sock)
    (health,) = mint_projects(cfg, "health")
    return replace(cfg, default_project=health), health


def test_with_no_session_live_a_read_takes_the_default_project(certified_work, short_tmp):
    from science.cli import _ambient_selection

    cfg, health = _config_with_default(certified_work, short_tmp / "service.sock")
    assert _ambient_selection(cfg) == health
    assert _ambient_selection(replace(cfg, default_project=None)) is None


def test_a_stale_socket_reads_as_no_live_session(certified_work, short_tmp):
    """A crashed launcher leaves its socket file; connecting to it is refused."""
    from science.cli import _ambient_selection

    sock = short_tmp / "service.sock"
    cfg, health = _config_with_default(certified_work, sock)
    dead = socket.socket(socket.AF_UNIX)
    dead.bind(str(sock))
    dead.close()  # the file stays; nothing listens
    assert sock.exists()
    assert _ambient_selection(cfg) == health


def test_a_socket_path_no_launcher_could_bind_reads_as_no_live_session(certified_work, short_tmp):
    from science.cli import _ambient_selection

    cfg, health = _config_with_default(certified_work, short_tmp / ("s" * 200 + ".sock"))
    assert _ambient_selection(cfg) == health


def test_a_live_sessions_null_is_the_answer_not_the_default(certified_work, short_tmp):
    from science.cli import _ambient_selection
    from science.serve import serve

    sock = short_tmp / "service.sock"
    cfg, health = _config_with_default(certified_work, sock)
    server = serve(cfg, sock, stderr=io.StringIO())
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        assert _ambient_selection(cfg) == health
        _request(sock, {"command": "project-select", "inputs": {"clear": True}})
        assert _ambient_selection(cfg) is None
    finally:
        server.shutdown()
        server.server_close()


def test_a_listener_that_answers_something_else_is_an_internal_error(certified_work, short_tmp, capsys):
    """A live session the read could not ask is not an absent one (spec §5.2)."""
    from science.cli import main

    sock = short_tmp / "service.sock"
    config_path = write_cli_config(certified_work, service_socket=sock)

    class Garbage(socketserver.StreamRequestHandler):
        def handle(self):
            self.rfile.readline()
            self.wfile.write(b'{"ok": true}\n')

    server = socketserver.ThreadingUnixStreamServer(str(sock), Garbage)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        assert main(["projects", "--config", str(config_path)]) == 1
    finally:
        server.shutdown()
        server.server_close()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err)["error"]["code"] == "internal-error"


def test_a_read_with_project_does_not_ask_the_socket(certified_work, short_tmp, capsys, monkeypatch):
    import science.cli as cli

    sock = short_tmp / "service.sock"
    config_path = write_cli_config(certified_work, service_socket=sock)
    from science.config import load_config
    (health,) = mint_projects(load_config(config_path), "health")
    monkeypatch.setattr(cli, "_ambient_selection", lambda config: pytest.fail("step 1 binds the invocation"))
    assert cli.main(["project-show", "--config", str(config_path), "--project", "health"]) == 0
    assert capsys.readouterr().out.startswith("## Project: health\n")
```

In `python/tests/test_cli.py`, `test_read_dispatch_is_sessionless_and_writes_exact_text`, the fake's constructor takes the selection:

```python
        def __init__(self, declarations, handlers, context, session=None, selection=None):
            assert session is None and selection is None
```

Append P1's selection arms to `python/tests/test_cwd_independence.py`:

```python
def _default_project_config(work: Path, extra: str = "") -> tuple[Path, object]:
    """A relative-path configuration whose `default_project` is a standing project."""
    from helpers.world import mint_projects
    from science.config import load_config

    config = _relative_config(work, extra=extra)
    (health,) = mint_projects(load_config(config), "health")
    config.write_text(config.read_text() + f'default_project = "{health}"\n')
    return config, health


def test_a_cli_read_takes_the_selection_the_file_names_from_a_decoy_directory(certified_work, tmp_path,
                                                                             monkeypatch, capsys):
    from science.cli import main

    config, _ = _default_project_config(certified_work)
    monkeypatch.chdir(certified_work)
    assert main(["project-show", "--config", str(config)]) == 0
    from_home = capsys.readouterr().out
    monkeypatch.chdir(_decoy(tmp_path / "decoy"))
    assert main(["project-show", "--config", str(config)]) == 0
    assert capsys.readouterr().out == from_home
    assert from_home.startswith("## Project: health\n")


@pytest.mark.parametrize("kind", ["serve", "mcp serve"])
def test_a_launcher_opens_under_the_selection_the_file_names_from_a_decoy_directory(
        certified_work, short_tmp, tmp_path, monkeypatch, kind):
    from test_mcp_socket import _request
    from test_selection_query import launcher

    sock = short_tmp / "service.sock"
    config, health = _default_project_config(certified_work, extra=f'service_socket = "{sock}"\n')
    monkeypatch.chdir(_decoy(tmp_path / "decoy"))
    with launcher(kind, config, sock):
        assert _request(sock, {"query": "selection"}) == {"project": str(health)}
```

(`test_cwd_independence.py` needs `import pytest` at its top.)

- [ ] **Step 2: Run them to verify they fail**

Run: `just test-one tests/test_selection_query.py tests/test_cwd_independence.py`
Expected: FAIL — the socket refuses `{"query": ...}` as unknown request keys; `_ambient_selection` does not exist.

- [ ] **Step 3: The selection query on the socket**

In `python/src/science/serve.py`, add above `service_server`:

```python
def _answer_query(dispatcher, query) -> dict:
    """The selection query (coordination design §5.2 step 2): answered from the
    endpoint's state — no invocation, no ledger line, no dispatcher lock."""
    if query != "selection":
        raise Refused(Refusal("invalid-input", f"unknown query {query!r}; the service answers `selection`"))
    selection = dispatcher.selection
    return {"project": None if selection is None else str(selection)}
```

and in the handler, tell the two request shapes apart by their key sets:

```python
                try:
                    request = json.loads(line)
                    if isinstance(request, dict) and set(request) == {"query"}:
                        reply = _answer_query(dispatcher, request["query"])
                    else:
                        command, inputs, invocation_id, cursor, project = _validated(request)
                        out = dispatcher.invoke(command, inputs, invocation_id=invocation_id,
                                                cursor=cursor, project=project)
                        reply = {"ok": True, "text": out.text,
                                 "invocation_id": out.invocation_id}
                except json.JSONDecodeError as caught:
```

`science mcp serve` builds its server with `service_server`, so it answers the query with no further change.

- [ ] **Step 4: The CLI's resolution order**

In `python/src/science/cli.py`, add above `main`:

```python
_SELECTION_QUERY = b'{"query":"selection"}\n'
_SELECTION_TIMEOUT_SECONDS = 5


def _ambient_selection(config):
    """Coordination design §5.2 steps 2–4: the live session's selection, asked
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
        with socket.socket(socket.AF_UNIX) as connection:
            connection.settimeout(_SELECTION_TIMEOUT_SECONDS)
            connection.connect(path)
            connection.sendall(_SELECTION_QUERY)
            reply = json.loads(connection.makefile().readline())
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
```

and in `main`, replace the read path from `config = load_config(...)` through the `invoke(...)` call:

```python
        config = load_config(resolve_config_path(namespace.config))
        project = getattr(namespace, "project", None)
        output = Dispatcher(
            declarations,
            resolve_handlers(declarations),
            ReadContext.open(config),
            # An explicit --project binds this invocation (step 1), so the
            # session is not asked.
            selection=None if project is not None else _ambient_selection(config),
        ).invoke(
            namespace.command,
            inputs,
            invocation_id=invocation_id,
            cursor=namespace.cursor,
            project=project,
        )
```

- [ ] **Step 5: Run the tests, then the inner loop**

Run: `just test-one tests/test_selection_query.py tests/test_cwd_independence.py tests/test_cli.py tests/test_serve.py tests/test_mcp_socket.py`, then `just test-fast`
Expected: PASS. Every CLI read test in the suite now passes through `_ambient_selection`; most configure a socket path past the AF_UNIX limit or one that does not exist, and read unselected as before.

- [ ] **Step 6: Commit**

```bash
tasks check
git add python tasks
git commit -m "feat(cli): reads resolve the live session's selection over the socket"
```

---

### Task 7: `next` reads through the selection (P5)

**Files:**
- Modify: `commands/next/command.toml`, `commands/next/prompt.md`
- Modify: `python/src/science/coordination.py` (`live_selection`)
- Modify: `python/src/science/commands/next.py` (`handle`)
- Modify: `tools/cli.toml` (the `next` row); regenerate `adapters/claude-code/`
- Test: `python/tests/test_cmd_next_selection.py` (create)

**Interfaces:**
- Consumes: Task 1's `selected_project` and the `project` field; Task 3's `project-select`; `beliefs.world.live.evaluate_live_query`; `beliefs.view_query.stored_query`.
- Produces: `science.coordination.live_selection(ctx, project_node) -> LiveSelection`, refusing `kernel-refused`; `next` with `selects = true`, rendering a `selection` block before its rows under a selection and exactly its former output under none.

- [ ] **Step 1: Write the failing tests**

Create `python/tests/test_cmd_next_selection.py`:

```python
"""Spec §5.5 and P5: next through the selected project's query, evaluated live."""
import json
import re

import pytest

from helpers.world import add_one_more_record, build_belief_world, build_fixture_world, open_rig
from science.refusal import Refused

NAMES = ("project", "project-select", "revise", "next", "belief")
VERSION = "science.view-query.v1"


def _addresses(*refs):
    return json.dumps({"version": VERSION, "clauses": [{"all": [{"addresses": list(refs)}]}]})


def _kinds(kinds):
    return json.dumps({"version": VERSION, "clauses": [{"all": [{"kinds": list(kinds)}]}]})


def _project(d, name, query):
    from beliefs.coordination import CoordinationAddress

    out = d.invoke("project", {"name": name, "query": query})
    return CoordinationAddress(re.search(r"project:([0-9a-f]{32})\.", out.text).group(1))


def _rows(text):
    return text.split("propositions:\n", 1)[1]


def _refused(call, code):
    with pytest.raises(Refused) as caught:
        call()
    assert caught.value.refusal.code == code
    return caught.value.refusal


@pytest.fixture
def world(certified_work):
    """The fixture world with two propositions, p1 and p2."""
    cfg = build_fixture_world(certified_work)
    add_one_more_record(cfg)
    return cfg


def test_next_under_a_selection_classifies_exactly_the_selected_propositions(world):
    """The mutation that falls back to the whole world shows p2."""
    with open_rig(world, NAMES) as (d, ctx):
        one = _project(d, "one", _addresses("proposition:p1"))
        d.invoke("project-select", {"target": "one"})
        text = d.invoke("next", {}).text
        revision = ctx.coordination().resolve(one).uid
    assert _rows(text) == "  proposition:p1: not-ready: p1\n"
    assert text.startswith(
        "## Next\nselection:\n"
        f"  project: {one}@{revision}\n  name: one\n  complete: true\n  absent: none\n"
        f"  world: {world.world.world_id}\n  corpus ")
    assert re.search(r"\n  corpus [0-9a-f]{32}: [0-9a-f]{64}\npropositions:\n", text)


def test_unselected_next_equals_next_under_a_whole_world_project(world):
    """P5: the unselected session reads the whole world."""
    with open_rig(world, NAMES) as (d, _):
        unselected = d.invoke("next", {}).text
        _project(d, "everything", _kinds(sorted(world.profile.coordination_query_kinds)))
        d.invoke("project-select", {"target": "everything"})
        selected = d.invoke("next", {}).text
    assert unselected == "## Next\npropositions:\n" + _rows(unselected)  # no selection block
    assert _rows(selected) == _rows(unselected)
    assert "proposition:p1" in _rows(selected) and "proposition:p2" in _rows(selected)


def test_belief_answers_for_its_proposition_whatever_is_selected(certified_work):
    """P5 and decision 4: selection scopes enumeration, never lookup by identity."""
    ask = {"proposition": "proposition:p1"}
    with open_rig(build_belief_world(certified_work), NAMES) as (d, _):
        _project(d, "empty", json.dumps({"version": VERSION, "clauses": []}))
        d.invoke("project-select", {"target": "empty"})
        selected = d.invoke("belief", ask).text
        assert _rows(d.invoke("next", {}).text) == "  none: no propositions\n"
        d.invoke("project-select", {"clear": True})
        assert d.invoke("belief", ask).text == selected
        assert "proposition:p1" in d.invoke("next", {}).text


def test_a_proposition_minted_after_selecting_appears_without_republishing(certified_work):
    """Decision 3: the queue is attention, evaluated live; no epoch mediates it."""
    cfg = build_fixture_world(certified_work)
    with open_rig(cfg, NAMES) as (d, _):
        _project(d, "claims", _kinds(["proposition"]))
        d.invoke("project-select", {"target": "claims"})
        assert "proposition:p2" not in d.invoke("next", {}).text
        add_one_more_record(cfg)
        assert "proposition:p2" in _rows(d.invoke("next", {}).text)


def test_a_revised_query_is_followed_without_reselecting(world):
    with open_rig(world, NAMES) as (d, _):
        one = _project(d, "one", _addresses("proposition:p1"))
        d.invoke("project-select", {"target": "one"})
        d.invoke("revise", {"address": str(one), "query": _addresses("proposition:p2")})
        assert _rows(d.invoke("next", {}).text) == "  proposition:p2: not-ready: p2\n"


def test_project_binds_one_next_and_leaves_the_session_unselected(world):
    with open_rig(world, NAMES) as (d, _):
        _project(d, "one", _addresses("proposition:p1"))
        assert _rows(d.invoke("next", {}, project="one").text) == "  proposition:p1: not-ready: p1\n"
        assert d.selection is None
        assert "proposition:p2" in d.invoke("next", {}).text


def test_a_query_naming_an_address_the_world_does_not_hold_is_kernel_refused(world):
    with open_rig(world, NAMES) as (d, _):
        _project(d, "ghost", _addresses("proposition:absent"))
        d.invoke("project-select", {"target": "ghost"})
        refusal = _refused(lambda: d.invoke("next", {}), "kernel-refused")
    assert refusal.data == {"kind": "SelectionRefused", "reason": "address-unknown",
                            "refs": ["proposition:absent"]}


def test_a_contended_capture_is_kernel_refused_not_a_traceback(world, monkeypatch):
    """A live capture never waits behind a corpus operation: the kernel raises
    BuildContended, and the person is told so."""
    import beliefs.world.live as live
    from beliefs.errors import BuildContended

    def contended(world_, query):
        raise BuildContended("the corpus operation lock is held")

    with open_rig(world, NAMES) as (d, _):
        _project(d, "one", _addresses("proposition:p1"))
        d.invoke("project-select", {"target": "one"})
        monkeypatch.setattr(live, "evaluate_live_query", contended)
        refusal = _refused(lambda: d.invoke("next", {}), "kernel-refused")
    assert refusal.data == {"kind": "BuildContended"}
    assert "operation lock" in refusal.message


def test_next_declares_the_selection_and_its_reads():
    from science.loader import production_tree

    decl = next(decl for decl in production_tree() if decl.name == "next")
    assert decl.selects is True
    assert set(decl.reads) == {"corpus-stored", "holdings", "epoch", "registry", "coordination"}


def test_next_renders_identically_through_the_cli_and_mcp(certified_work, capsys):
    from helpers.world import write_cli_config
    from science.cli import main
    from science.config import ReadContext, load_config
    from science.dispatch import Dispatcher
    from science.loader import production_tree, resolve_handlers
    from science.mcp import handle_request
    from test_mcp import rpc

    config_path = write_cli_config(certified_work)
    config = load_config(config_path)
    with open_rig(config, NAMES) as (d, _):
        one = _project(d, "one", _addresses("proposition:p1"))
    declarations = production_tree()
    dispatcher = Dispatcher(declarations, resolve_handlers(declarations), ReadContext.open(config))
    assert main(["next", "--config", str(config_path), "--project", str(one)]) == 0
    cli_text = capsys.readouterr().out
    mcp_text = handle_request(rpc("tools/call", {"name": "next", "arguments": {"project": str(one)}}),
                              dispatcher, declarations)["result"]["content"][0]["text"]
    assert cli_text == mcp_text and "selection:\n" in cli_text
```

- [ ] **Step 2: Run them to verify they fail**

Run: `just test-one tests/test_cmd_next_selection.py`
Expected: FAIL — `next` shows every proposition under a selection, renders no selection block, and refuses `project`.

- [ ] **Step 3: The declaration and the prompt**

`commands/next/command.toml` — add `selects = true` after `write_class`, and the family:

```toml
schema_version = 1
name = "next"
purpose = "Rank the propositions this world can act on, from the current view."
write_class = "read-only"
selects = true
output_budget = 16384

[inputs.limit]
type = "int"
required = false
default = 10
doc = "How many propositions to show."

[reads]
families = ["corpus-stored", "holdings", "epoch", "registry", "coordination"]
```

`commands/next/prompt.md`:

```markdown
Run `next` when the user asks what to work on. It lists propositions in a
fixed order — ready (a spec targets it and every input is held), not ready,
assessed but not admitted, admitted — with each one's statement. With a
project selected, or named with `project` for this call only, it lists the
propositions that project's query selects, evaluated over the world as it
stands now, and opens with a `selection` block: the project, whether every
corpus was present (`complete`, `absent`), and the states it read. With no
project it lists the whole world. Nothing is stored; the ranking is
recomputed every time. It names no priority function; that is a later
sub-project's.
```

- [ ] **Step 4: The live selection and the handler**

Append to `python/src/science/coordination.py`:

```python
def live_selection(ctx, project):
    """What the project's query denotes over the world's current state (beliefs
    live-query design): attention, never an epoch's answer. The kernel's
    refusals arrive as `kernel-refused`, its class name in `data.kind`."""
    from beliefs.errors import (
        AddressMapConflict, BuildContended, CaptureDrift, ResolutionRefused, SelectionRefused,
    )
    from beliefs.view_query import stored_query
    from beliefs.world import live

    try:
        return live.evaluate_live_query(ctx.world, stored_query(project))
    except SelectionRefused as caught:
        raise Refused(Refusal(
            "kernel-refused", str(caught),
            {"kind": "SelectionRefused", "reason": caught.reason, "refs": list(caught.refs)},
        )) from None
    except (AddressMapConflict, BuildContended, CaptureDrift, ResolutionRefused) as caught:
        raise Refused(Refusal("kernel-refused", str(caught), {"kind": type(caught).__name__})) from None
```

In `python/src/science/commands/next.py`, import `from science.coordination import live_selection, selected_project`, and replace `handle`:

```python
def _selection_pairs(selection, project, live) -> tuple:
    """What the rows were read through: the project's pinned address and name,
    and the live capture's completeness and stamp."""
    pairs = [
        ("project", str(selection.pinned(project.uid))),
        ("name", project.title),
        ("complete", "true" if live.complete else "false"),
        ("absent", ", ".join(live.absent) or "none"),
        ("world", live.stamp.world_id),
    ]
    pairs += [(f"corpus {corpus_id}", state) for corpus_id, state in live.stamp.coverage]
    return tuple(pairs)


def handle(ctx, *, limit=None) -> Report:
    _, view = ctx.single_view()
    project = selected_project(ctx)
    blocks: list = [Heading("Next")]
    if project is None:
        nodes = [node for node in view.iter_stored() if node.kind == "proposition"]
    else:
        # The project's query, denoted over the world as it stands: no epoch
        # mediates seeing a proposition just minted (coordination design
        # decision 3). A selected record that is not a proposition is not a row.
        live = live_selection(ctx, project)
        blocks.append(KeyVals("selection", _selection_pairs(ctx.selection, project, live)))
        nodes = [node for node in (view.get(ref) for ref in live.selected if view.holds(ref))
                 if node.kind == "proposition"]
    rows = sorted((CLASSES.index(classify(ctx, node.id)), node.id,
                   stored.display_statement(node) or node.title) for node in nodes)
    shown = rows[: (limit or 10)]
    blocks.append(KeyVals("propositions",
                          tuple((pid, f"{CLASSES[c]}: {statement}") for c, pid, statement in shown)
                          or (("none", "no propositions"),)))
    return tuple(blocks)
```

- [ ] **Step 5: The CLI row and the adapters**

In `tools/cli.toml`, the science `next` row gains the option after `limit`:

```toml
  { shared = "limit", value = "int" },
  { names = ["--project"], value = "string" },
```

Then `cd python && uv run science adapters build`.

- [ ] **Step 6: Run the tests, then the inner loop**

Run: `just test-one tests/test_cmd_next_selection.py tests/test_cmd_next.py tests/test_belief_path.py tests/test_cli_surface.py tests/test_adapters.py`, then `just test-fast`
Expected: PASS — `test_cmd_next.py` unchanged: with nothing selected `next` renders exactly what it did.

- [ ] **Step 7: Commit**

```bash
tasks check
git add commands/next adapters tools/cli.toml python tasks
git commit -m "feat(commands): next reads through the selected project"
```

---

### Task 8: The preamble, the dated amendments, and the close-out

**Files:**
- Modify: `commands/PREAMBLE.md`; regenerate `adapters/claude-code/`
- Modify: `python/tests/test_adapters.py` (`test_preamble_states_the_selected_project_rule`)
- Modify: `docs/specs/2026-08-31-command-framework-design.md` (§3.2, §3.3, §7.4, §8, §9.1, §9.2, §9.3)
- Modify: `docs/specs/2026-09-09-belief-path-commands-design.md` (§4.8)
- Modify: `docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md` (§5.1)
- Modify: `docs/specs/2026-09-24-coordination-command-set-design.md` (status line)
- Modify: the ops repository's `cli.toml` (science section), then re-vendor
- Modify: `tasks/` (close `sci-f95f8b`; note the goal)

**Interfaces:**
- Consumes: every earlier task.
- Produces: nothing a later task calls.

- [ ] **Step 1: Change the preamble test to the new sentences**

In `python/tests/test_adapters.py`, replace the body of `test_preamble_states_the_selected_project_rule` from its docstring down:

```python
    """Coordination design §4.4: selection landed, so the preamble states the
    rule itself — how the project is chosen, what reads through it, and what
    needs one."""
    from science.adapters import build_adapter

    build_adapter(production_tree(), COMMANDS_ROOT, REPO_ROOT / "skills", tmp_path)
    skill = (tmp_path / "skills" / "status" / "SKILL.md").read_text()
    # The adapter preserves the preamble's line breaks; the prose assertions
    # are about sentences, so compare with whitespace normalized. The
    # byte-for-byte check stays in test_generated_tree_matches_committed.
    prose = " ".join(skill.split())
    assert "no project can be selected yet" not in prose
    assert "The current project is chosen with `project-select`." in prose
    assert ("A command that enumerates the world reads through the selected project's query, "
            "and sees the whole world when none is selected") in prose
    assert "a command given an identity answers for that identity whatever is selected" in prose
    assert ("A question or any coordination record needs a selected project, "
            "except a project itself; a fact does not.") in prose
```

Run: `just test-one tests/test_adapters.py`
Expected: FAIL — the preamble still says no project can be selected.

- [ ] **Step 2: The preamble**

`commands/PREAMBLE.md`, whole file:

```markdown
You are working over one world of governed records through the `science`
commands. The current project is chosen with `project-select`. A command
that enumerates the world reads through the selected project's query, and
sees the whole world when none is selected; a command given an identity
answers for that identity whatever is selected. A question or any
coordination record needs a selected project, except a project itself; a
fact does not. Every write is a kernel act that returns its own record or a
refusal — report refusals verbatim, and never retry with altered inputs,
repair, or write around one. Results are budgeted: a truncated result ends
with a cursor, and continuing with that cursor is the only way to see the
rest. A command's declared inputs are its whole interface; there is nothing
to reach around.
```

Then `cd python && uv run science adapters build`, and `just test-one tests/test_adapters.py`.
Expected: PASS.

- [ ] **Step 3: The dated amendments**

Each is one paragraph added at the end of the named section, dated with the day it is written (`<date>` below).

Framework design (`docs/specs/2026-08-31-command-framework-design.md`):

- §3.2: "**Amended <date>** (coordination command set design §4.2). `project` joins the reserved input names. It is a protocol field offered exactly on declarations that set the new optional top-level key `selects` (bool, default false; read-only declarations only, a build refusal otherwise): the CLI's `--project`, an optional `project` property in the MCP tool schema, and a `project` key on the service request. The dispatcher resolves it to a project address for that one invocation; any other command's request carrying it refuses `invalid-input`. The documented `reads` families gain `coordination`."
- §3.3: "**Amended <date>** (coordination command set design §4.1). The closed set gains `session`: no record kinds and no act families, but a live session is required and the invocation follows §6.1's claim, open and close. Its handler receives a session port (`select`) in place of a scoped writer."
- §7.4: "**Amended <date>** (coordination command set design §4.1). A `session` invocation's canonical report is exactly one selection block, rebuilt from the session ledger's `select` line for that invocation on the first response, on replay and on continuation; its audit admits that block and nothing else."
- §8: "**Amended <date>** (coordination command set design §4.4). Selection landed: the preamble now says the current project is chosen with `project-select`, that enumerations read through its query and see the whole world when none is selected, that a command given an identity answers for it whatever is selected, and that any coordination record but a project needs a selected project. The 2026-09-23 amendment's interim sentence is retired."
- §9.1: "**Amended <date>** (coordination command set design §6). The file gains the optional key `default_project`, a `coord:<project>` address: the project a launcher opens under when it is given no `--project`, and the one a CLI read uses when no session is live. It refuses with `coordination = false`."
- §9.2: "**Amended <date>** (coordination command set design §5.2, §5.3). `science serve` takes `--project <name or address>`, the session's initial selection. The service protocol gains the selection query: the one-line request `{\"query\": \"selection\"}` is answered `{\"project\": <address> | null}` from the endpoint's state, with no invocation and no ledger line. A CLI read resolves its selection from `--project`, else that query, else — only when nothing listens on the socket — `default_project`; any other socket failure is an internal error."
- §9.3: "**Amended <date>** (coordination command set design §5.1, §5.3). `science mcp serve` takes `--project` as `science serve` does and answers the selection query on the socket it binds. Tool schemas of `selects` commands carry the optional `project` property."

Belief path design (`docs/specs/2026-09-09-belief-path-commands-design.md`), end of §4.8: "**Amended <date>.** \"From the current view\" is the coordination command set design's §5.5, taken by reference: with a project selected `next` classifies the propositions that project's query selects, evaluated live, and renders the selection it read through; with none it classifies every stored proposition, as above. The declaration gains `selects = true` and the `coordination` read family."

Projects design (`docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md`), end of §5.1: "*Amended <date>:* the `project` command's `select` form is the separate command `project-select` (coordination command set design decision 1), and the launcher's `--project` takes a name as well as an address, resolved once at start."

Coordination design status line: "**Status:** reviewed and approved 2026-09-24; part 1 (the write surface) implemented 2026-09-24, plan `docs/plans/2026-09-24-coordination-write-surface.md`; part 2 (selection and the project reads) implemented <date>, plan `docs/plans/2026-09-30-coordination-selection-and-reads.md`. Part 3 (multi-corpus, `sci-923d3a`) has no plan yet."

- [ ] **Step 4: The gate**

Run: `just gate`
Expected: PASS.

- [ ] **Step 5: Commit the close-out**

Close this step's own task first (`tasks done <step id> "preamble, amendments, gate"`): `done` refuses a parent while a child is open.

```bash
tasks done sci-f95f8b "project-select and the session class, projects and project-show, the project field, launcher initial selection and default_project, the selection query and CLI resolution (P8), next through the selection (P5), the preamble"
tasks note sci-c5528e "Part 2 (sci-f95f8b) landed on branch coordination-part2; part 3 (sci-923d3a) is next and unblocked"
tasks check
git add commands adapters docs python tasks
git commit -m "docs: coordination command set part 2 landed"
```

- [ ] **Step 6: Land the CLI rows in ops and re-vendor — with the person's go-ahead**

This step commits in the ops repository and its `just vendor-cli` writes `tools/cli.toml` into every project that vendors it, so stop and ask before running it. Then, with `$OPS` the ops checkout that `tasks projects --pretty` lists, on its default branch:

```bash
python3 - "$OPS/cli.toml" tools/cli.toml <<'PY'
import pathlib, sys
ops, ours = (pathlib.Path(p) for p in sys.argv[1:])
START, END = "# ---- science\n", "# ---- pilot\n"
def split(text):
    head, rest = text.split(START, 1)
    section, tail = rest.split(END, 1)
    return head, section, tail
head, _, tail = split(ops.read_text())
_, section, _ = split(ours.read_text())
ops.write_text(head + START + section + END + tail)
PY
git -C "$OPS" add cli.toml
git -C "$OPS" commit -m "feat(cli): science selection rows — project-select, projects, project-show, --project on next and the launchers"
(cd "$OPS" && just vendor-cli)
cmp "$OPS/cli.toml" tools/cli.toml
```

Expected: `cmp` prints nothing — the branch's copy is byte-identical to what ops now publishes. If it differs, ops moved other rows since this branch vendored: copy `$OPS/cli.toml` over `tools/cli.toml`, rerun `just test-one tests/test_cli_surface.py`, and commit the copy (`chore(cli): re-vendor from ops`). Follow the ops repository's own agent guide for its commit.

- [ ] **Step 7: Hand the branch to review**

Request the whole-branch review (superpowers:requesting-code-review), then superpowers:finishing-a-development-branch. The goal `sci-c5528e` stays open: part 3 (`sci-923d3a`) and the follow-ups `sci-dce3b2`, `sci-3a0eb1` and `sci-6ffb7f` remain.
