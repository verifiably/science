# Coordination command set, part 1: the write surface — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sessions open with the coordination contract, and a person can mint and revise projects, questions, hypotheses, tasks and decisions and make a same-query copy, over a configuration that names one world from any directory and a service socket both launchers serve.

**Architecture:** The launcher configuration gains a required `coordination` key compiled into the one profile the session binds and passed as its coordination profile; relative paths resolve against the configuration file. Seven `coordination`-class commands call the scoped writer's `mint_coordination` / `revise_coordination`; subordinate kinds read a selection slot on the read context, which this plan adds and tests inject (the command that sets it arrives in part 2). `science mcp serve` binds the service socket with the same dispatcher as its stdio loop.

**Tech Stack:** Python 3.13, `beliefs` (editable path dependency), pytest with pytest-xdist and pytest-testmon, `just` recipes over `tools/tt`.

**Spec:** `docs/specs/2026-09-24-coordination-command-set-design.md` (read it with this plan).

**Part 2 and part 3.** Selection (`project-select`, the `session` write class, the selection block), `projects` and `project-show`, the `project` read protocol field and the `selects` key, the CLI's selection resolution over the socket (P8), `next` through the selection and the preamble need `beliefs-cc0aea` (S1), `beliefs-1148ad` (S2) and `beliefs-1af3fd` (S3); their plan is written when those land. `write_root`, `read_contracts`, per-mount profiles and cross-corpus classification need `beliefs-fe7149` and S1 and are part 3. This plan references none of their APIs.

**Where to work.** Merge the `coordination-spec` branch (spec and this plan) to `main` first. Then, from the main checkout: `work-link --ensure .worktrees`, `git worktree add .worktrees/coordination-commands -b coordination-commands`, lock it (`git worktree lock --reason "on WORK_ROOT storage (host: $(uname -n))" .worktrees/coordination-commands`), and `tasks start <task id>` before each task.

## Global Constraints

- Tests run through the front door only, never bare `pytest`: a focused run is `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q <node id>'`; the inner loop is `just test-fast`; `just gate` before the branch merges.
- `tasks check` before every commit; each task's `tasks done <id> "<what landed>"` goes in that task's final commit.
- Conventional commits; no AI attribution lines.
- A new command is four artifacts plus tests: `commands/<name>/command.toml`, `commands/<name>/prompt.md`, `python/src/science/commands/<module>.py` with `handle`, and the regenerated `adapters/claude-code/` tree (`cd python && uv run science adapters build`, pinned by `test_generated_tree_matches_committed`). Plus one `[[cli.science.commands]]` row in the ops repository's `cli.toml`, committed there first and copied byte-identical to `tools/cli.toml` (`cp "$OPS/cli.toml" tools/cli.toml`, where `$OPS` is the ops checkout that `tasks projects --pretty` lists), pinned by `test_cli_surface.py`.
- Every coordination record's content is the kernel's full field set: `name`, `body`, `author`, `at` on every kind; `query` on view kinds; `status`, `depends` on `task`. `author` is `writer.actor`; `at` is `datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")`. Neither is an input.
- Write handlers validate before their first act; a surface refusal raised before any act closes the invocation and replays (belief path §6.3). Kernel refusals arrive as `kernel-refused`.
- No docs or comments name absolute host paths.

## Review Focus

- A query given as JSON text rather than YAML — must parse (YAML is a JSON superset); Task 4 pins it.
- A query that is YAML but not a mapping (`"- a"`, `"3"`, empty string) — refuses `invalid-input` before any act and replays; Task 4 pins it.
- A `revise` on an address that has never been minted — refuses `invalid-input` naming the address, not a kernel error or a crash; Task 6 pins it.
- A `reuse` whose source is a `task` or a `decision` — refuses `invalid-input` naming the kind; Task 7 pins it.
- A configuration whose paths are relative, loaded from another directory through `science status` — reads the same world; Task 1 pins it through the CLI.

---

### Task 1: Relative configuration paths resolve against the file (P1)

**Files:**
- Modify: `python/src/science/config.py` (`load_config`)
- Modify: `python/tests/test_config.py:55-72` (the two relative-path tests)
- Create: `python/tests/test_cwd_independence.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `load_config(path)` resolves `world_root`, each `corpus_roots` entry, `operations_root`, `service_socket`, `store_root` and each `contracts` entry against `path.resolve().parent`.

- [ ] **Step 1: Change the two pinned tests to the new rule, and add one for the world roots**

In `python/tests/test_config.py`, replace `test_load_config_resolves_relative_operations_root` and `test_service_socket_is_configurable_and_resolved` with:

```python
def test_relative_paths_resolve_against_the_config_file(tmp_path, monkeypatch):
    """Not the working directory: one file names one world from anywhere (P1)."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    cfg = load_config(write_config(tmp_path, operations_root="operations", store_root="store"))
    assert cfg.operations_root == (tmp_path / "operations").resolve()
    assert cfg.store_root == (tmp_path / "store").resolve()


def test_service_socket_is_configurable_and_resolved(tmp_path, monkeypatch):
    """The AF_UNIX path limit is 107 bytes and a worktree's operations root
    already exceeds it, so the operator can name a short path; a relative one
    resolves against the configuration file like every other path."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    cfg = load_config(write_config(tmp_path, extra='service_socket = "run/s.sock"\n'))
    assert cfg.service_socket == (tmp_path / "run" / "s.sock").resolve()


def test_world_and_corpus_roots_resolve_against_the_config_file(tmp_path, monkeypatch):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    path = tmp_path / "science.toml"
    path.write_text(
        f'world_root = "world"\nworld_id = "{WORLD_ID}"\ncorpus_roots = ["corpora/one"]\n'
        'operations_root = "ops"\ndomains = []\ncontracts = []\nstore_root = "store"\n'
    )
    cfg = load_config(path)
    assert cfg.world.world_root == (tmp_path / "world").resolve()
    assert cfg.world.corpus_roots == ((tmp_path / "corpora" / "one").resolve(),)
```

- [ ] **Step 2: Run them to verify they fail**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_config.py -k "relative or resolved or roots_resolve"'`
Expected: FAIL — the paths resolve under `elsewhere/`.

- [ ] **Step 3: Resolve against the file**

In `load_config`, after the type checks and before `domains = …`, add:

```python
    base_dir = path.resolve().parent

    def located(value: str) -> Path:
        # Relative paths name places beside the configuration file, never the
        # process's working directory (projects design P1); an absolute value
        # is unchanged by the join.
        return (base_dir / value).resolve()
```

Then use it everywhere a path is built:

```python
    local = [load_contract_document(located(value), base) for value in raw["contracts"]]
    ...
    operations_root = located(raw["operations_root"])
    service_socket = (
        located(raw["service_socket"])
        if "service_socket" in raw
        else operations_root / "service.sock"
    )
    return ScienceConfig(
        world=WorldConfig(
            world_root=located(raw["world_root"]),
            world_id=raw["world_id"],
            corpus_roots=tuple(located(value) for value in raw["corpus_roots"]),
        ),
        operations_root=operations_root,
        profile=profile,
        service_socket=service_socket,
        store_root=located(raw["store_root"]),
        plans=plans,
    )
```

- [ ] **Step 4: Run them to verify they pass**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_config.py'`
Expected: PASS.

- [ ] **Step 5: Write the launcher-level P1 test**

Create `python/tests/test_cwd_independence.py`:

```python
"""P1 (projects design §10): no configuration is discovered from the working
directory, and a configuration's relative paths resolve against the file."""
import json
from pathlib import Path

import pytest

from helpers.world import build_fixture_world, DOMAINS


def _relative_config(work: Path) -> Path:
    """The fixture world's launcher TOML with every path relative to `work`."""
    cfg = build_fixture_world(work)
    path = work / "science.toml"
    path.write_text(
        'world_root = "world"\n'
        f'world_id = "{cfg.world.world_id}"\n'
        'corpus_roots = ["corpus"]\n'
        'operations_root = "ops"\n'
        f"domains = {list(DOMAINS)!r}\n"
        "contracts = []\n"
        'store_root = "store"\n'
    )
    return path


def _decoy(where: Path) -> Path:
    """A directory holding every file the predecessor discovered from cwd."""
    where.mkdir()
    (where / "science.yaml").write_text("project: decoy\n")
    (where / "science.toml").write_text('world_root = "/nowhere"\n')
    (where / "corpus.yaml").write_text("corpus: decoy\n")
    return where


def test_status_reads_the_configured_world_from_a_decoy_directory(certified_work, tmp_path, monkeypatch, capsys):
    from science.cli import main

    config = _relative_config(certified_work)
    monkeypatch.chdir(certified_work)
    assert main(["status", "--config", str(config)]) == 0
    from_home = capsys.readouterr().out
    monkeypatch.chdir(_decoy(tmp_path / "decoy"))
    assert main(["status", "--config", str(config)]) == 0
    assert capsys.readouterr().out == from_home


def test_no_config_is_discovered_from_the_working_directory(tmp_path, monkeypatch, capsys):
    from science.cli import main

    monkeypatch.chdir(_decoy(tmp_path / "decoy"))
    monkeypatch.delenv("SCIENCE_CONFIG", raising=False)
    assert main(["status"]) == 3  # refused: no --config and no SCIENCE_CONFIG
    refusal = json.loads(capsys.readouterr().err)["refusal"]
    assert refusal["code"] == "invalid-input"
    assert "SCIENCE_CONFIG" in refusal["message"]


def test_mcp_serve_reads_the_configured_world_from_a_decoy_directory(certified_work, tmp_path, monkeypatch):
    import io

    from science.mcp import serve
    from test_mcp import rpc

    config = _relative_config(certified_work)
    monkeypatch.chdir(_decoy(tmp_path / "decoy"))
    stdout = io.StringIO()
    stdin = io.BytesIO((json.dumps(rpc("tools/call", {"name": "status", "arguments": {}})) + "\n").encode())
    serve(config, stdin=stdin, stdout=stdout, stderr=io.StringIO())
    (line,) = stdout.getvalue().splitlines()
    assert "World status" in json.loads(line)["result"]["content"][0]["text"]
```

- [ ] **Step 6: Run it**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_cwd_independence.py'`
Expected: PASS (Step 3 made the relative paths work; the second test pins behaviour that already holds).

- [ ] **Step 7: Commit**

```bash
tasks check
git add python/src/science/config.py python/tests/test_config.py python/tests/test_cwd_independence.py tasks
git commit -m "fix(config): resolve relative paths against the configuration file (P1)"
```

---

### Task 2: The `coordination` key and the coordination profile at session open (`sci-17851d`)

**Files:**
- Modify: `python/src/science/config.py` (`_KEYS`, `ScienceConfig`, `load_config`, `ReadContext`)
- Create: `python/src/science/session.py`
- Modify: `python/src/science/serve.py:70-73`, `python/src/science/mcp.py:374-377`
- Modify: `python/tests/helpers/world.py` (profiles, pins, configs, `open_rig`)
- Modify: `python/tests/test_config.py` (`write_config`, `_TAIL`, the parametrized cases at :111-116), `python/tests/test_status.py:47-53`, `python/tests/test_cwd_independence.py` (`_relative_config`)
- Test: `python/tests/test_config.py`, `python/tests/test_session_open.py` (create)

**Interfaces:**
- Consumes: Task 1's `located`.
- Produces:
  - `ScienceConfig.coordination: int | None` — the shipped coordination contract version, or `None` for `coordination = false`.
  - `science.session.open_session(config: ScienceConfig) -> WriterSession` — `open_attended_session` with `coordination=config.profile` when `config.coordination` is set.
  - `ReadContext.coordination() -> CoordinationResolver` — refuses `invalid-input` when `config.coordination is None`.
  - `helpers.world.COORDINATION = 2`, and fixture worlds pin base + `biology` + coordination.

- [ ] **Step 1: Write the failing configuration tests**

Add to `python/tests/test_config.py`:

```python
def test_coordination_key_is_required(tmp_path):
    path = write_config(tmp_path)
    path.write_text(path.read_text().replace("coordination = 2\n", ""))
    assert_invalid_config(path)


def test_coordination_version_compiles_into_the_profile(tmp_path):
    cfg = load_config(write_config(tmp_path, coordination="2"))
    assert cfg.coordination == 2
    assert "coordination" in cfg.profile.activated_contracts
    assert "project" in cfg.profile.coordination_kinds


def test_coordination_false_compiles_without_it(tmp_path):
    cfg = load_config(write_config(tmp_path, coordination="false"))
    assert cfg.coordination is None
    assert "coordination" not in cfg.profile.activated_contracts


@pytest.mark.parametrize("value", ["true", "3", '"2"', "0"])
def test_coordination_value_outside_its_forms_is_refused(tmp_path, value):
    assert_invalid_config(write_config(tmp_path, coordination=value))
```

and give `write_config` a `coordination: str = "2"` parameter that appends `f"coordination = {coordination}"` to `lines`. Append `coordination = 2\n` to `_TAIL` and to the two literal cases at lines 115-116, so each parametrized case still refuses for the reason it names rather than for the missing key.

- [ ] **Step 2: Run them to verify they fail**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_config.py -k coordination'`
Expected: FAIL — `coordination` is an unknown key.

- [ ] **Step 3: Load the key and compile it in**

In `config.py`: add `"coordination"` to `_KEYS`; add the field `coordination: int | None` to `ScienceConfig` after `store_root` (no default: every construction states it); import `shipped_coordination` from `beliefs.profile`. After the other type checks:

```python
    coordination = raw["coordination"]
    if coordination is False:
        coordination = None
    elif type(coordination) is not int or coordination < 1:
        _refuse("config coordination must be a coordination contract version (an integer) or false")
```

and compile it into the profile:

```python
    try:
        profile = compile_profile(
            base,
            domains + [contract for contract, _ in local],
            coordination=None if coordination is None else shipped_coordination(coordination),
        )
    except ProfileError as caught:
        _refuse(f"config contracts do not compile: {caught}")
```

passing `coordination=coordination` to `ScienceConfig(...)`. `shipped_coordination` raises `ProfileError` for an unshipped version, which the existing `except` reports.

- [ ] **Step 4: Run them to verify they pass**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_config.py'`
Expected: PASS.

- [ ] **Step 5: Put the fixture worlds on coordination**

In `python/tests/helpers/world.py`:

```python
from beliefs.profile import compile_profile, shipped_base_contract, shipped_coordination, shipped_domain_contract

DOMAINS = ("biology",)
COORDINATION = 2
PROFILE = compile_profile(
    shipped_base_contract(),
    [shipped_domain_contract(namespace) for namespace in DOMAINS],
    coordination=shipped_coordination(COORDINATION),
)
```

`PINS` stays derived from `PROFILE.activated_contracts`, so it now carries `coordination`. In `build_fixture_world_with_contract` compile with `coordination=shipped_coordination(COORDINATION)` too. Add `coordination=COORDINATION` to both `ScienceConfig(...)` constructions, and a `coordination = {COORDINATION}` line to both TOML templates (`write_cli_config`, `write_config_for`). Add `coordination=cfg.coordination` to the `ScienceConfig(...)` in `test_status.py:47`, and `"coordination = 2\n"` to `_relative_config` in `test_cwd_independence.py`.

Add a builder for the `false` case:

```python
BARE_PROFILE = compile_profile(
    shipped_base_contract(), [shipped_domain_contract(namespace) for namespace in DOMAINS]
)


def build_world_without_coordination(work: Path) -> ScienceConfig:
    """A corpus adopted before coordination: its pins carry no coordination contract."""
    corpus_root = work / "corpus"
    config = WorldConfig(work / "world", secrets.token_hex(16), (corpus_root,))
    init_world_root(config, authority=FIXTURE_AUTHORITY)
    init_corpus_root(corpus_root, authority=FIXTURE_AUTHORITY)
    writer = open_corpus(corpus_root, authority=FIXTURE_AUTHORITY, profile=BARE_PROFILE)
    writer.adopt_manifest(profile=CorpusPins(
        science_contract="science:" + BARE_PROFILE.base_contract_identity,
        domains={ns: f"{ns}:{identity}" for ns, identity in BARE_PROFILE.activated_contracts.items()},
    ))
    open_world(config, authority=FIXTURE_AUTHORITY).admit(corpus_root, provenance=Fresh())
    STORE_IDS[work] = init_store_root(work / "store", authority=FIXTURE_AUTHORITY)
    return ScienceConfig(world=config, operations_root=work / "ops", profile=BARE_PROFILE,
                         service_socket=work / "ops" / "service.sock", store_root=work / "store",
                         coordination=None)
```

- [ ] **Step 6: Run the whole suite to see the fixture change is inert**

Run: `just test-fast`
Expected: PASS — the belief path's tests do not depend on the coordination contract being absent.

- [ ] **Step 7: Write the failing session-open tests**

Create `python/tests/test_session_open.py`:

```python
import pytest

from helpers.world import build_fixture_world, build_world_without_coordination


def _project_content(writer):
    return {"name": "health", "body": "", "author": writer.actor, "at": "2026-09-24T00:00:00Z",
            "query": {"version": "science.view-query.v1", "clauses": []}}


def test_session_opened_by_science_can_mint_a_project(certified_work):
    from beliefs.permit import RequiredCapabilities
    from science.session import open_session

    session = open_session(build_fixture_world(certified_work))
    try:
        writer = session.scoped(RequiredCapabilities.coordination(), "a" * 32)
        node = writer.mint_coordination("project", project=None, content=_project_content(writer))
        assert node.kind == "project" and node.title == "health"
    finally:
        session.close()


def test_without_coordination_a_project_mint_is_unavailable(certified_work):
    from beliefs.errors import CoordinationUnavailable
    from beliefs.permit import RequiredCapabilities
    from science.session import open_session

    session = open_session(build_world_without_coordination(certified_work))
    try:
        writer = session.scoped(RequiredCapabilities.coordination(), "b" * 32)
        with pytest.raises(CoordinationUnavailable):
            writer.mint_coordination("project", project=None, content=_project_content(writer))
    finally:
        session.close()


def test_coordination_asked_of_a_corpus_that_does_not_pin_it_refuses_at_open(certified_work):
    from dataclasses import replace

    from beliefs.errors import ContractMismatch
    from helpers.world import PROFILE
    from science.session import open_session

    bare = build_world_without_coordination(certified_work)
    with pytest.raises(ContractMismatch):
        open_session(replace(bare, profile=PROFILE, coordination=2))


def test_read_context_resolver_needs_coordination(certified_work):
    from science.config import ReadContext
    from science.refusal import Refused

    ctx = ReadContext.open(build_world_without_coordination(certified_work))
    with pytest.raises(Refused) as caught:
        ctx.coordination()
    assert caught.value.refusal.code == "invalid-input"
    assert "coordination = false" in caught.value.refusal.message
```

- [ ] **Step 8: Run them to verify they fail**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_session_open.py'`
Expected: FAIL — `science.session` does not exist.

- [ ] **Step 9: One opener, and the read-side resolver**

Create `python/src/science/session.py`:

```python
"""The one place a science launcher opens its attended session."""
from __future__ import annotations

from science.config import ScienceConfig


def open_session(config: ScienceConfig):
    """The kernel requires the coordination profile to equal the writer's in
    compiled identity (`require_profile_compatible`), so with coordination on
    the one compiled profile is passed as both."""
    from beliefs.session import open_attended_session

    return open_attended_session(
        config.world, config.operations_root, profile=config.profile,
        coordination=config.profile if config.coordination is not None else None,
        store_root=config.store_root,
    )
```

Replace the `open_attended_session(...)` calls in `serve.py` and `mcp.py` with `open_session(config)` (importing it from `science.session`), and the one in `helpers/world.py` `open_rig` likewise. Add to `ReadContext`:

```python
    def coordination(self):
        """A live resolver over the configured roots (coordination §6.2). One
        root today, mounted under the session's profile; part 3 mounts each
        root under its own manifest's profile."""
        from beliefs.corpus import CoordinationResolver

        if self.config.coordination is None:
            raise Refused(Refusal("invalid-input",
                                  "coordination = false in this configuration; there is no resolver to ask"))
        return CoordinationResolver({root: self.config.profile for root in self.config.world.corpus_roots})
```

- [ ] **Step 10: Run them to verify they pass, then the suite**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_session_open.py'` then `just test-fast`
Expected: PASS both.

- [ ] **Step 11: Amend the framework design and close `sci-17851d`**

In `docs/specs/2026-08-31-command-framework-design.md` §9.1, after the `contracts and store_root` paragraph, add:

```markdown
`coordination` (**added 2026-09-24**: coordination command set design §6) is
required: the shipped coordination contract version compiled into the one profile
the session binds and passed as its coordination profile, or `false` for a corpus
adopted without it. Relative paths in the file resolve against the file's own
directory (the same design, decision 8), never the process's working directory.
```

and in §5.1, replace "`coordination` stays unset until a coordination-class command exists" through the end of that sentence with "`coordination` is set from the configuration's `coordination` key (**amended 2026-09-24**)". Then:

```bash
tasks check
git add python docs/specs/2026-08-31-command-framework-design.md tasks
tasks done sci-17851d "coordination config key compiled into the session profile and passed as its coordination profile; open_session; ReadContext.coordination(); fixture worlds pin coordination"
git add tasks
git commit -m "feat(config): open sessions with the coordination contract (sci-17851d)"
```

---

### Task 3: Selection slot, refusal codes and the coordination helpers

**Files:**
- Modify: `python/src/science/refusal.py` (`CODES`)
- Modify: `python/src/science/config.py` (`ReadContext.selection`, `current_project`)
- Modify: `python/src/science/dispatch.py` (constructor `selection`, per-invocation context)
- Modify: `python/tests/test_dispatch.py` (a dataclass stub context in place of `object()`)
- Create: `python/src/science/coordination.py`
- Test: `python/tests/test_coordination_helpers.py` (create), `python/tests/test_write_dispatch.py`

**Interfaces:**
- Consumes: Task 2's `ReadContext.coordination()`.
- Produces:
  - Refusal codes `no-current-project`, `unknown-project`, `ambiguous-project`.
  - `ReadContext.selection: CoordinationAddress | None = None` and `ReadContext.current_project() -> CoordinationAddress` (refuses `no-current-project`; the message names `project-select` and `reuse`).
  - `Dispatcher(..., session=None, selection=None)`; handlers receive `dataclasses.replace(ctx, selection=self._selection)`.
  - In `science.coordination`: `now() -> str`; `parse_query_text(text: str) -> dict`; `parse_address(text: str, *, subordinate: bool) -> CoordinationAddress`; `content_of(node) -> dict`; `resolve_one(ctx, address) -> Node`; `standing_tips(ctx, address) -> tuple[CoordinationRevision, ...]`.

- [ ] **Step 1: Write the failing helper tests**

Create `python/tests/test_coordination_helpers.py`:

```python
import pytest

from science.refusal import Refused


def _refused(call, code="invalid-input"):
    with pytest.raises(Refused) as caught:
        call()
    assert caught.value.refusal.code == code
    return caught.value.refusal


@pytest.mark.parametrize("text", [
    "version: science.view-query.v1\nclauses: []\n",
    '{"version": "science.view-query.v1", "clauses": []}',
])
def test_query_text_parses_yaml_or_json_to_a_mapping(text):
    from science.coordination import parse_query_text
    assert parse_query_text(text) == {"version": "science.view-query.v1", "clauses": []}


@pytest.mark.parametrize("text", ["- a\n", "3", "", "{unclosed"])
def test_query_text_that_is_not_a_mapping_refuses(text):
    from science.coordination import parse_query_text
    _refused(lambda: parse_query_text(text))


def test_addresses_parse_by_shape():
    from science.coordination import parse_address
    project, local = "a" * 32, "b" * 32
    assert str(parse_address(f"coord:{project}", subordinate=False)) == f"coord:{project}"
    assert str(parse_address(f"coord:{project}/{local}", subordinate=True)) == f"coord:{project}/{local}"
    _refused(lambda: parse_address(f"coord:{project}", subordinate=True))
    _refused(lambda: parse_address(f"coord:{project}/{local}@{'c' * 32}", subordinate=True))
    _refused(lambda: parse_address("health", subordinate=False))


def test_current_project_refuses_without_a_selection(certified_work):
    from helpers.world import build_fixture_world
    from science.config import ReadContext
    refusal = _refused(lambda: ReadContext.open(build_fixture_world(certified_work)).current_project(),
                       code="no-current-project")
    assert "project-select" in refusal.message and "reuse" in refusal.message
```

- [ ] **Step 2: Run them to verify they fail**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_coordination_helpers.py'`
Expected: FAIL — `science.coordination` does not exist.

- [ ] **Step 3: Add the codes, the slot and the helpers**

In `refusal.py`, add `"no-current-project", "unknown-project", "ambiguous-project"` to `CODES`.

In `config.py`, add to `ReadContext` a field `selection: object = None` (a `CoordinationAddress` or `None`; typed `object` because `beliefs.coordination` is imported lazily like the rest of this module's kernel reads) and:

```python
    def current_project(self):
        """The selected project's unpinned address, or refuse: a subordinate
        record's address is (project identity, local id), and with nothing
        selected there is no project identity to bind (projects design §5.3)."""
        if self.selection is None:
            raise Refused(Refusal(
                "no-current-project",
                "no project is selected; select one with `project-select`, or copy a view "
                "into the current project with `reuse`",
            ))
        return self.selection
```

Create `python/src/science/coordination.py`:

```python
"""Shared reads and input parsing for the coordination commands (spec §3)."""
from __future__ import annotations

from datetime import UTC, datetime

import yaml

from science.refusal import Refusal, Refused

# Stored in the coordination facet beside the content fields; never content.
_ADDRESS_FIELDS = frozenset({"project", "local"})


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_query_text(text: str) -> dict:
    """YAML (JSON is a subset) that must be a mapping; the kernel validates the
    query language and the profile's world kinds at the act."""
    try:
        value = yaml.safe_load(text)
    except yaml.YAMLError as caught:
        _refuse(f"query is not YAML or JSON: {caught}")
    if not isinstance(value, dict):
        _refuse("query must be a mapping with `version` and `clauses`")
    return value


def parse_address(text: str, *, subordinate: bool):
    """An unpinned `coord:` address: `coord:<project>/<local>` when
    `subordinate`, else `coord:<project>`."""
    from beliefs.coordination import CoordinationAddress

    try:
        address = CoordinationAddress.parse(text)
    except ValueError as caught:
        _refuse(str(caught))
    if address.revision is not None:
        _refuse(f"{text!r} pins a revision; name the address unpinned")
    if subordinate and address.local is None:
        _refuse(f"{text!r} is a project address; this input takes coord:<project>/<local>")
    if not subordinate and address.local is not None:
        _refuse(f"{text!r} is a subordinate address; this input takes coord:<project>")
    return address


def content_of(node) -> dict:
    """The full content a revision was minted with: name, body and every facet
    field except the address. `query` is the stored canonical projection, which
    the kernel accepts back as-is."""
    from beliefs import stored

    facet = node.facets[stored.COORDINATION_FACET]
    return {"name": node.title, "body": node.body,
            **{field: value for field, value in facet.items() if field not in _ADDRESS_FIELDS}}


def standing_tips(ctx, address):
    """Every standing tip of `address`; refuses when the address was never minted."""
    tips = ctx.coordination().tips(address)
    if not tips:
        _refuse(f"{address} names no coordination record in the configured corpora")
    return tips


def resolve_one(ctx, address):
    """The address's one standing tip, or refuse — `divergent-view` naming every tip."""
    from beliefs.coordination import CoordinationRefused

    resolved = ctx.coordination().resolve(address)
    if resolved is None:
        _refuse(f"{address} names no coordination record in the configured corpora")
    if isinstance(resolved, CoordinationRefused):
        raise Refused(Refusal(
            "kernel-refused",
            f"{address} has {len(resolved.tips)} standing tips; revise it with `repair` to reconcile them",
            {"kind": resolved.reason, "tips": list(resolved.tips)},
        ))
    return resolved
```

`yaml` is already a dependency (the contract loader imports it).

- [ ] **Step 4: Run the helper tests to verify they pass**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_coordination_helpers.py'`
Expected: PASS.

- [ ] **Step 5: Write the failing dispatcher test for the slot**

Add to `python/tests/test_write_dispatch.py`:

```python
def test_handlers_see_the_dispatchers_selection(certified_work):
    from beliefs.coordination import CoordinationAddress
    from beliefs.session import open_attended_session
    from science.config import ReadContext
    cfg = build_fixture_world(certified_work)
    session = open_attended_session(cfg.world, cfg.operations_root, profile=cfg.profile)
    seen = []

    def spy(ctx, writer, *, slug):
        seen.append(ctx.selection)
        return mint_claim_handler(ctx, writer, slug=slug)

    selected = CoordinationAddress("a" * 32)
    d = Dispatcher((MINT_CLAIM,), {"mint-claim": spy}, ReadContext.open(cfg),
                   session=session, selection=selected)
    try:
        d.invoke("mint-claim", {"slug": "sel"})
    finally:
        session.close()
    assert seen == [selected]
```

importing `mint_claim_handler` from `helpers.synthetic` at the top of the file.

- [ ] **Step 6: Run it to verify it fails**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_write_dispatch.py::test_handlers_see_the_dispatchers_selection'`
Expected: FAIL — `Dispatcher` takes no `selection`.

- [ ] **Step 7: Carry the selection into every handler call**

In `dispatch.py`: `import dataclasses`; the constructor gains `selection=None` and stores `self._selection = selection`; add

```python
    def _context(self):
        """The read context a handler receives: the dispatcher's, with the
        selection standing when the invocation runs."""
        return dataclasses.replace(self._ctx, selection=self._selection)
```

and pass `self._context()` instead of `self._ctx` at the three handler calls (the read call in `invoke`, the read call in `_continue`, the write call in `_invoke_write`). `_minted_report` and `_continue_write` keep `self._ctx`: they render records, not handler reads.

- [ ] **Step 8: Give the bare-object test contexts a selection field**

`python/tests/test_dispatch.py` builds three dispatchers with `read_context=object()` (lines 29, 158, 178), which `dataclasses.replace` cannot copy. Add near its imports:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class StubContext:
    """The read context shape the dispatcher now relies on: a dataclass carrying `selection`."""
    selection: object = None
```

and replace each `read_context=object()` with `read_context=StubContext()`.

- [ ] **Step 9: Run the dispatcher tests, then the suite**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_write_dispatch.py tests/test_dispatch.py'` then `just test-fast`
Expected: PASS.

- [ ] **Step 10: Commit**

```bash
tasks check
git add python tasks
git commit -m "feat(dispatch): selection slot, coordination refusal codes and helpers"
```

---

### Task 4: `project` — project genesis

**Files:**
- Create: `commands/project/command.toml`, `commands/project/prompt.md`, `python/src/science/commands/project.py`
- Delete: `python/tests/fixtures/commands/coord-note/` and its binding in `python/tests/helpers/synthetic.py`
- Modify: `python/tests/test_synthetic_tree.py` (drop `coord-note` from its expected names)
- Modify: ops `cli.toml`, then `tools/cli.toml`; regenerate `adapters/claude-code/`
- Test: `python/tests/test_cmd_project.py` (create)

**Interfaces:**
- Consumes: `science.coordination.parse_query_text`, `now`; Task 2's fixture world.
- Produces: `helpers.world.coordination_rig(work, names, *, selection=None, extra=())` — a context manager yielding `(dispatcher, ctx)` over the named production commands (plus `(declaration, handler)` pairs in `extra`) on a coordination fixture world; `helpers.world.QUERY`; and the `project` command.

- [ ] **Step 1: Write the failing tests**

Add to `python/tests/helpers/world.py`:

```python
@contextmanager
def coordination_rig(work: Path, names: tuple[str, ...], *, selection=None, extra=()):
    """A dispatcher over the named production commands (plus `extra`,
    `(declaration, handler)` pairs of synthetic ones — a Declaration holds a
    dict and is not hashable) on a coordination fixture world, with an
    attended session and the given selection."""
    from science.config import ReadContext
    from science.dispatch import Dispatcher
    from science.loader import production_tree, resolve_handlers
    from science.session import open_session
    cfg = build_fixture_world(work)
    decls = tuple(d for d in production_tree() if d.name in names)
    handlers = resolve_handlers(decls)
    for decl, handler in extra:
        decls += (decl,)
        handlers[decl.name] = handler
    session = open_session(cfg)
    ctx = ReadContext.open(cfg)
    try:
        yield Dispatcher(decls, handlers, ctx, session=session, selection=selection), ctx
    finally:
        session.close()


QUERY = "version: science.view-query.v1\nclauses:\n  - all:\n      - kinds: [proposition]\n"
```

Create `python/tests/test_cmd_project.py`:

```python
import re

import pytest

from helpers.world import QUERY, coordination_rig
from science.refusal import Refused

ADDRESS = re.compile(r"\[project\] project:([0-9a-f]{32})\.([0-9a-f]{32})")


def test_project_genesis_needs_no_selection(certified_work):
    """P2's genesis arm: a fresh world's first act."""
    with coordination_rig(certified_work, ("project",)) as (d, ctx):
        out = d.invoke("project", {"name": "health", "query": QUERY})
        project, revision = ADDRESS.search(out.text).groups()
        from beliefs.coordination import CoordinationAddress
        node = ctx.coordination().resolve(CoordinationAddress(project))
    assert node.title == "health" and node.uid == revision
    assert node.facets["coordination"]["query"]["clauses"][0]["all"][0]["kinds"] == ["proposition"]


def test_project_accepts_a_json_query(certified_work):
    with coordination_rig(certified_work, ("project",)) as (d, _):
        out = d.invoke("project", {"name": "j", "query": '{"version": "science.view-query.v1", "clauses": []}'})
    assert ADDRESS.search(out.text)


@pytest.mark.parametrize("query", ["- a\n", "3", ""])
def test_a_query_that_is_not_a_mapping_refuses_before_any_act_and_replays(certified_work, query):
    with coordination_rig(certified_work, ("project",)) as (d, _):
        for _ in range(2):
            with pytest.raises(Refused) as caught:
                d.invoke("project", {"name": "bad", "query": query}, invocation_id="Q" * 8)
            assert caught.value.refusal.code == "invalid-input"


def test_a_query_the_kernel_rejects_is_kernel_refused(certified_work):
    bad = "version: science.view-query.v1\nclauses:\n  - all:\n      - kinds: [task]\n"
    with coordination_rig(certified_work, ("project",)) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("project", {"name": "bad", "query": bad})
    assert caught.value.refusal.code == "kernel-refused"
```

- [ ] **Step 2: Run them to verify they fail**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_cmd_project.py'`
Expected: FAIL — no `project` command.

- [ ] **Step 3: The declaration, the prompt and the handler**

`commands/project/command.toml`:

```toml
schema_version = 1
name = "project"
purpose = "Start a project: a name and a query over the world."
write_class = "coordination"
output_budget = 4096

[inputs.name]
type = "string"
required = true
doc = "The project's name; content, and it may be shared with another project."
[inputs.query]
type = "string"
required = true
doc = "The view query as YAML or JSON text (science.view-query.v1)."
[inputs.body]
type = "string"
required = false
doc = "What the project is for."

[reads]
families = ["coordination"]
```

`commands/project/prompt.md`:

```markdown
Run `project` to start a project: a name and a query over the world
(`science.view-query.v1`, as YAML or JSON text). A project is a label over
a query, never a container — the world facts its query selects are its
content, and they belong to every other project whose query selects them
too. Minting a project needs no selected project. Report the minted
record; its address is `coord:<project>`, the identity every later
reference uses, since names may be shared.
```

`python/src/science/commands/project.py`:

```python
"""project: mint a project, the root of its own address space (spec §3.1)."""
from __future__ import annotations

from science.coordination import now, parse_query_text
from science.report import Report, record_block


def handle(ctx, writer, *, name, query, body=None) -> Report:
    content = {"name": name, "body": body or "", "author": writer.actor, "at": now(),
               "query": parse_query_text(query)}
    node = writer.mint_coordination("project", project=None, content=content)
    return (record_block(node),)
```

- [ ] **Step 4: Drop the synthetic exemplar**

Delete `python/tests/fixtures/commands/coord-note/`; in `helpers/synthetic.py` remove the `handlers["coord-note"] = unreachable` line and "`coord-note` and" from the docstring; in `test_synthetic_tree.py` remove `coord-note` from the expected declaration names. `project` is the coordination class's loaded, reachable exemplar now.

- [ ] **Step 5: The CLI row and the adapters**

In the ops repository's `cli.toml`, after the `[[cli.science.commands]]` row for `next`, add:

```toml
[[cli.science.commands]]
path = ["project"]
summary = "Start a project: a name and a query over the world"
options = [
  { shared = "config", value = "path" },
  { names = ["--invocation-id"], value = "string" },
  { names = ["--continue"], value = "string" },
  { names = ["--name"], value = "string", required = true },
  { names = ["--query"], value = "string", required = true },
  { names = ["--body"], value = "string" },
]
```

Commit it in ops (`feat(cli): science project row`), then `cp "$OPS/cli.toml" tools/cli.toml` and `cd python && uv run science adapters build`.

- [ ] **Step 6: Run the command tests, then the suite**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_cmd_project.py tests/test_cli_surface.py tests/test_adapters.py tests/test_synthetic_tree.py'` then `just test-fast`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
tasks check
git add commands/project adapters tools/cli.toml python tasks
git commit -m "feat(commands): project"
```

---

### Task 5: `question`, `hypothesis`, `task`, `decide` — subordinate genesis (P2)

**Files:**
- Create: `commands/{question,hypothesis,task,decide}/command.toml` and `prompt.md`; `python/src/science/commands/{question,hypothesis,task,decide}.py`
- Modify: ops `cli.toml`, then `tools/cli.toml`; regenerate `adapters/claude-code/`
- Test: `python/tests/test_cmd_subordinate.py` (create)

**Interfaces:**
- Consumes: `ReadContext.current_project()`, `parse_query_text`, `now`, `coordination_rig`, `QUERY`.
- Produces: `helpers.world.mint_project(d, name="health") -> CoordinationAddress` — mints through the `project` command and returns the unpinned address; the four commands.

- [ ] **Step 1: Write the failing tests**

Add to `helpers/world.py`:

```python
def mint_project(dispatcher, name: str = "health"):
    import re
    from beliefs.coordination import CoordinationAddress
    out = dispatcher.invoke("project", {"name": name, "query": QUERY})
    return CoordinationAddress(re.search(r"project:([0-9a-f]{32})\.", out.text).group(1))
```

Create `python/tests/test_cmd_subordinate.py`:

```python
import pytest

from helpers.synthetic import MINT_CLAIM, mint_claim_handler
from helpers.world import QUERY, coordination_rig, mint_project
from science.refusal import Refused

NAMES = ("project", "question", "hypothesis", "task", "decide")
INPUTS = {
    "question": {"name": "Does PHF19 track stage?", "query": QUERY},
    "hypothesis": {"name": "PHF19 rises with stage", "query": QUERY},
    "task": {"name": "Hold GSE179929"},
    "decide": {"name": "Use the coarse query", "body": "No disease vocabulary is bound yet."},
}
KIND = {"question": "question", "hypothesis": "hypothesis", "task": "task", "decide": "decision"}


@pytest.mark.parametrize("command", sorted(INPUTS))
def test_without_a_selection_refuses_before_any_act_and_replays(certified_work, command):
    """P2's subordinate arm."""
    with coordination_rig(certified_work, NAMES) as (d, _):
        for _ in range(2):
            with pytest.raises(Refused) as caught:
                d.invoke(command, INPUTS[command], invocation_id="N" * 8)
            assert caught.value.refusal.code == "no-current-project"


def test_a_world_kind_write_needs_no_selection(certified_work):
    """P2's world-kind arm."""
    with coordination_rig(certified_work, NAMES, extra=((MINT_CLAIM, mint_claim_handler),)) as (d, _):
        assert "proposition:free" in d.invoke("mint-claim", {"slug": "free"}).text


@pytest.mark.parametrize("command", sorted(INPUTS))
def test_under_a_selection_mints_the_kind_in_that_project(certified_work, command):
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        project = mint_project(d)
        d._selection = project  # part 2's project-select sets this through the session port
        out = d.invoke(command, INPUTS[command])
    assert f"[{KIND[command]}] {KIND[command]}:{project.project}." in out.text


def test_task_depends_on_another_task(certified_work):
    import re
    with coordination_rig(certified_work, NAMES) as (d, _):
        d._selection = mint_project(d)
        first = d.invoke("task", {"name": "hold"})
        project, local = re.search(r"task:([0-9a-f]{32})\.([0-9a-f]{32})\.", first.text).groups()
        second = d.invoke("task", {"name": "run", "depends": [f"coord:{project}/{local}"]})
    assert "[task]" in second.text


def test_decide_requires_its_reasoning(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        d._selection = mint_project(d)
        with pytest.raises(Refused) as caught:
            d.invoke("decide", {"name": "no body"})
    assert caught.value.refusal.code == "invalid-input"  # canonicalization: body is required
```

- [ ] **Step 2: Run them to verify they fail**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_cmd_subordinate.py'`
Expected: FAIL — no such commands.

- [ ] **Step 3: The four declarations**

`commands/question/command.toml` (and `commands/hypothesis/command.toml` identical except `name = "hypothesis"`, `purpose = "Ask a hypothesis in the current project: a name and a query over the world."`):

```toml
schema_version = 1
name = "question"
purpose = "Ask a question in the current project: a name and a query over the world."
write_class = "coordination"
output_budget = 4096

[inputs.name]
type = "string"
required = true
doc = "The question, as a person would ask it."
[inputs.query]
type = "string"
required = true
doc = "The world facts that bear on it, as a view query in YAML or JSON text."
[inputs.body]
type = "string"
required = false
doc = "Context for the question."

[reads]
families = ["coordination"]
```

`commands/task/command.toml`:

```toml
schema_version = 1
name = "task"
purpose = "Add an open task to the current project."
write_class = "coordination"
output_budget = 4096

[inputs.name]
type = "string"
required = true
doc = "What is to be done."
[inputs.body]
type = "string"
required = false
doc = "Detail."
[inputs.depends]
type = "list-of-string"
required = false
doc = "Tasks this one waits on, as coord:<project>/<local> addresses."

[reads]
families = ["coordination"]
```

`commands/decide/command.toml`:

```toml
schema_version = 1
name = "decide"
purpose = "Record a decision in the current project, with its reasoning."
write_class = "coordination"
output_budget = 4096

[inputs.name]
type = "string"
required = true
doc = "What was decided."
[inputs.body]
type = "string"
required = true
doc = "Why: the reasoning a later reader needs."

[reads]
families = ["coordination"]
```

- [ ] **Step 4: The prompts**

`commands/question/prompt.md`:

```markdown
Run `question` to ask a question in the current project. It needs a
selected project: with none it refuses `no-current-project`, and the
answer to "which project does this belong to" is the one you are in —
another project that wants it copies it with `reuse`. The query names
the world facts that bear on the question. Report the minted record.
```

`commands/hypothesis/prompt.md`: the same text with "question" replaced by "hypothesis" and "ask a question" by "state a hypothesis".

`commands/task/prompt.md`:

```markdown
Run `task` to add an open task to the current project; `depends` names
tasks it waits on by `coord:` address. Closing it is a `revise` with
`status` `done` or `dropped`. It needs a selected project. Report the
minted record.
```

`commands/decide/prompt.md`:

```markdown
Run `decide` to record a decision in the current project: what was
decided and, in `body`, why. The reasoning is required — a decision
without it is the part a later reader cannot reconstruct. It needs a
selected project. Report the minted record.
```

- [ ] **Step 5: The handlers**

`python/src/science/commands/question.py`:

```python
"""question: a view minted under the current project (spec §3.2)."""
from __future__ import annotations

from science.coordination import now, parse_query_text
from science.report import Report, record_block


def handle(ctx, writer, *, name, query, body=None) -> Report:
    project = ctx.current_project()
    content = {"name": name, "body": body or "", "author": writer.actor, "at": now(),
               "query": parse_query_text(query)}
    return (record_block(writer.mint_coordination("question", project=project, content=content)),)
```

`python/src/science/commands/hypothesis.py`: identical with `"question"` replaced by `"hypothesis"` in the docstring and the `mint_coordination` call.

`python/src/science/commands/task.py`:

```python
"""task: an open task under the current project (spec §3.3)."""
from __future__ import annotations

from science.coordination import now
from science.report import Report, record_block


def handle(ctx, writer, *, name, body=None, depends=None) -> Report:
    project = ctx.current_project()
    content = {"name": name, "body": body or "", "author": writer.actor, "at": now(),
               "status": "open", "depends": list(depends or ())}
    return (record_block(writer.mint_coordination("task", project=project, content=content)),)
```

`python/src/science/commands/decide.py`:

```python
"""decide: a decision and its reasoning under the current project (spec §3.4)."""
from __future__ import annotations

from science.coordination import now
from science.report import Report, record_block


def handle(ctx, writer, *, name, body) -> Report:
    project = ctx.current_project()
    content = {"name": name, "body": body, "author": writer.actor, "at": now()}
    return (record_block(writer.mint_coordination("decision", project=project, content=content)),)
```

- [ ] **Step 6: The CLI rows and the adapters**

In the ops `cli.toml`, after the `project` row, add four rows in this shape (options per the declarations; `required = true` exactly where the declaration says so; `list-of-string` is `value = "string", repeatable = true`):

```toml
[[cli.science.commands]]
path = ["question"]
summary = "Ask a question in the current project: a name and a query over the world"
options = [
  { shared = "config", value = "path" },
  { names = ["--invocation-id"], value = "string" },
  { names = ["--continue"], value = "string" },
  { names = ["--name"], value = "string", required = true },
  { names = ["--query"], value = "string", required = true },
  { names = ["--body"], value = "string" },
]

[[cli.science.commands]]
path = ["hypothesis"]
summary = "Ask a hypothesis in the current project: a name and a query over the world"
options = [
  { shared = "config", value = "path" },
  { names = ["--invocation-id"], value = "string" },
  { names = ["--continue"], value = "string" },
  { names = ["--name"], value = "string", required = true },
  { names = ["--query"], value = "string", required = true },
  { names = ["--body"], value = "string" },
]

[[cli.science.commands]]
path = ["task"]
summary = "Add an open task to the current project"
options = [
  { shared = "config", value = "path" },
  { names = ["--invocation-id"], value = "string" },
  { names = ["--continue"], value = "string" },
  { names = ["--name"], value = "string", required = true },
  { names = ["--body"], value = "string" },
  { names = ["--depends"], value = "string", repeatable = true },
]

[[cli.science.commands]]
path = ["decide"]
summary = "Record a decision in the current project, with its reasoning"
options = [
  { shared = "config", value = "path" },
  { names = ["--invocation-id"], value = "string" },
  { names = ["--continue"], value = "string" },
  { names = ["--name"], value = "string", required = true },
  { names = ["--body"], value = "string", required = true },
]
```

Check an existing `list-of-string` row in the table first (`grep -n repeatable tools/cli.toml`) and match its exact spelling if it differs. Commit in ops, copy, and regenerate adapters as in Task 4 Step 5.

- [ ] **Step 7: Run the tests, then the suite**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_cmd_subordinate.py tests/test_cli_surface.py tests/test_adapters.py'` then `just test-fast`
Expected: PASS.

- [ ] **Step 8: Commit**

```bash
tasks check
git add commands adapters tools/cli.toml python tasks
git commit -m "feat(commands): question, hypothesis, task, decide"
```

---

### Task 6: `revise`

**Files:**
- Create: `commands/revise/command.toml`, `commands/revise/prompt.md`, `python/src/science/commands/revise.py`
- Modify: ops `cli.toml`, then `tools/cli.toml`; regenerate `adapters/claude-code/`
- Test: `python/tests/test_cmd_revise.py` (create)

**Interfaces:**
- Consumes: `parse_address`, `parse_query_text`, `content_of`, `standing_tips`, `now`, `coordination_rig`, `mint_project`.
- Produces: the `revise` command.

- [ ] **Step 1: Write the failing tests**

Create `python/tests/test_cmd_revise.py`:

```python
import re

import pytest

from helpers.world import QUERY, coordination_rig, mint_project
from science.refusal import Refused

NAMES = ("project", "task", "revise")


def _task(d):
    out = d.invoke("task", {"name": "hold", "body": "the matrix"})
    project, local = re.search(r"task:([0-9a-f]{32})\.([0-9a-f]{32})\.", out.text).groups()
    return f"coord:{project}/{local}"


def test_rename_carries_every_other_field(certified_work):
    from beliefs.coordination import CoordinationAddress
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        project = mint_project(d, "health")
        d.invoke("revise", {"address": str(project), "name": "human health"})
        node = ctx.coordination().resolve(CoordinationAddress(project.project))
    assert node.title == "human health"
    assert node.facets["coordination"]["query"]["clauses"][0]["all"][0]["kinds"] == ["proposition"]


def test_closing_a_task_is_a_status_revision(certified_work):
    from beliefs.coordination import CoordinationAddress
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        d._selection = mint_project(d)
        address = _task(d)
        d.invoke("revise", {"address": address, "status": "done"})
        node = ctx.coordination().resolve(CoordinationAddress.parse(address))
    assert node.facets["coordination"]["status"] == "done" and node.body == "the matrix"


def test_a_field_the_kind_lacks_refuses_before_any_act(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        project = mint_project(d)
        with pytest.raises(Refused) as caught:
            d.invoke("revise", {"address": str(project), "status": "done"})
    assert caught.value.refusal.code == "invalid-input"
    assert "status" in caught.value.refusal.message and "project" in caught.value.refusal.message


def test_an_address_never_minted_refuses_naming_it(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("revise", {"address": "coord:" + "f" * 32, "name": "x"})
    assert caught.value.refusal.code == "invalid-input"
    assert "f" * 32 in caught.value.refusal.message


def test_a_revision_with_no_field_refuses(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        project = mint_project(d)
        with pytest.raises(Refused) as caught:
            d.invoke("revise", {"address": str(project)})
    assert caught.value.refusal.code == "invalid-input"


class _Tip:
    def __init__(self, node):
        self.node = node


def test_divergence_refuses_without_repair_and_names_every_tip_with_it(certified_work, monkeypatch):
    """Two tips cannot arise in one root under the lock (coordination §4.3);
    the resolver is stubbed to report them, and the writer is stubbed to
    capture the predecessors the repair names. Part 3's two-corpus fixture
    exercises a real divergence end to end."""
    import science.commands.revise as revise_module
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        project = mint_project(d)
        real = ctx.coordination().tips(project)[0].node
        # Node is a pydantic model: a sibling revision differs in its revision id alone.
        twin = real.model_copy(update={"id": real.id.rsplit(".", 1)[0] + "." + "e" * 32, "uid": "e" * 32})
        monkeypatch.setattr(revise_module, "standing_tips", lambda ctx, address: (_Tip(real), _Tip(twin)))
        with pytest.raises(Refused) as caught:
            d.invoke("revise", {"address": str(project), "name": "x"})
        assert caught.value.refusal.data["kind"] == "divergent-view"
        assert sorted(caught.value.refusal.data["tips"]) == sorted([real.uid, twin.uid])
        with pytest.raises(Refused) as partial:
            d.invoke("revise", {"address": str(project), "name": "x", "repair": True})
        assert partial.value.refusal.code == "invalid-input"  # repair needs every content field
        captured = {}
        monkeypatch.setattr(revise_module, "_revise", lambda writer, kind, address, predecessors, content:
                            captured.update(predecessors=sorted(predecessors)) or real)
        d.invoke("revise", {"address": str(project), "name": "x", "body": "", "query": QUERY,
                            "repair": True})
    assert captured["predecessors"] == sorted([real.uid, twin.uid])
```

- [ ] **Step 2: Run them to verify they fail**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_cmd_revise.py'`
Expected: FAIL — no `revise` command.

- [ ] **Step 3: The declaration and prompt**

`commands/revise/command.toml`:

```toml
schema_version = 1
name = "revise"
purpose = "Revise a project, question, hypothesis, task or decision."
write_class = "coordination"
output_budget = 4096

[inputs.address]
type = "string"
required = true
doc = "coord:<project> for a project, coord:<project>/<local> for the rest."
[inputs.name]
type = "string"
required = false
doc = "A new name."
[inputs.body]
type = "string"
required = false
doc = "A new body."
[inputs.query]
type = "string"
required = false
doc = "A new view query (projects, questions, hypotheses), YAML or JSON text."
[inputs.status]
type = "enum"
required = false
choices = ["open", "done", "dropped"]
doc = "A task's new status."
[inputs.depends]
type = "list-of-string"
required = false
doc = "A task's new dependencies, replacing the old."
[inputs.repair]
type = "bool"
required = false
default = false
doc = "Supersede every standing tip of a divergent address; every content field must then be given."

[reads]
families = ["coordination"]
```

`commands/revise/prompt.md`:

```markdown
Run `revise` to change a project, question, hypothesis, task or decision
by address. Fields not given carry over from the current revision; a
field the record's kind lacks refuses. Closing a task is `status` `done`
or `dropped`. An address whose record has diverged into several standing
revisions refuses and names them; `repair` reconciles them into one, and
then every field must be given, since there is no single revision to
carry over from. Report the minted revision.
```

- [ ] **Step 4: The handler**

`python/src/science/commands/revise.py`:

```python
"""revise: a whole new revision naming its predecessors (spec §3.6)."""
from __future__ import annotations

from science.coordination import content_of, now, parse_address, parse_query_text, standing_tips
from science.refusal import Refusal, Refused
from science.report import Report, record_block

# The content fields each kind carries beyond name and body (coordination v2 contract).
_FIELDS = {
    "project": {"query"}, "question": {"query"}, "hypothesis": {"query"},
    "task": {"status", "depends"}, "decision": set(),
}


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def _revise(writer, kind, address, predecessors, content):
    return writer.revise_coordination(kind, address, predecessors=predecessors, content=content)


def handle(ctx, writer, *, address, name=None, body=None, query=None, status=None, depends=None,
           repair=False) -> Report:
    parsed = parse_address(address, subordinate=address.count("/") == 1)
    given = {field: value for field, value in
             (("name", name), ("body", body), ("query", query), ("status", status), ("depends", depends))
             if value is not None}
    if not given:
        _refuse("revise names no field to change")
    tips = standing_tips(ctx, parsed)
    kind = tips[0].node.kind
    if kind not in _FIELDS:
        _refuse(f"{address} is a {kind}, which `revise` does not edit")
    lacking = sorted(set(given) - {"name", "body"} - _FIELDS[kind])
    if lacking:
        _refuse(f"a {kind} has no {', '.join(lacking)} field")
    if "query" in given:
        given["query"] = parse_query_text(given["query"])
    if "depends" in given:
        given["depends"] = list(given["depends"])
    if len(tips) > 1 and not repair:
        raise Refused(Refusal(
            "kernel-refused",
            f"{address} has {len(tips)} standing tips; revise it with `repair` to reconcile them",
            {"kind": "divergent-view", "tips": sorted(tip.node.uid for tip in tips)},
        ))
    if repair:
        missing = sorted(({"name", "body"} | _FIELDS[kind]) - set(given))
        if missing:
            _refuse(f"repair takes every field, since no one tip carries over; missing {', '.join(missing)}")
        content = dict(given)
    else:
        content = {**content_of(tips[0].node), **given}
    content.update(author=writer.actor, at=now())
    node = _revise(writer, kind, parsed, [tip.node.uid for tip in tips], content)
    return (record_block(node),)
```

- [ ] **Step 5: The CLI row and the adapters**

In the ops `cli.toml`, after the `decide` row:

```toml
[[cli.science.commands]]
path = ["revise"]
summary = "Revise a project, question, hypothesis, task or decision"
options = [
  { shared = "config", value = "path" },
  { names = ["--invocation-id"], value = "string" },
  { names = ["--continue"], value = "string" },
  { names = ["--address"], value = "string", required = true },
  { names = ["--name"], value = "string" },
  { names = ["--body"], value = "string" },
  { names = ["--query"], value = "string" },
  { names = ["--status"], value = "enum", values = ["open", "done", "dropped"] },
  { names = ["--depends"], value = "string", repeatable = true },
  { names = ["--repair"], value = "none" },
]
```

Match the table's existing spelling for a `bool` input (`grep -n 'value = "none"' tools/cli.toml`; the CLI builds `--repair/--no-repair` for bools, as `test_parser_compiles_inputs` shows for `--no-dry-run`) and for `enum`. Commit in ops, copy, regenerate adapters.

- [ ] **Step 6: Run the tests, then the suite**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_cmd_revise.py tests/test_cli_surface.py tests/test_adapters.py'` then `just test-fast`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
tasks check
git add commands/revise adapters tools/cli.toml python tasks
git commit -m "feat(commands): revise"
```

---

### Task 7: `reuse` — the same-query mint (P4)

**Files:**
- Create: `commands/reuse/command.toml`, `commands/reuse/prompt.md`, `python/src/science/commands/reuse.py`
- Modify: ops `cli.toml`, then `tools/cli.toml`; regenerate `adapters/claude-code/`
- Test: `python/tests/test_cmd_reuse.py` (create)

**Interfaces:**
- Consumes: `parse_address`, `resolve_one`, `content_of`, `now`, `ctx.current_project()`, `coordination_rig`, `mint_project`.
- Produces: the `reuse` command.

- [ ] **Step 1: Write the failing tests**

Create `python/tests/test_cmd_reuse.py`:

```python
import re

import pytest

from helpers.world import QUERY, coordination_rig, mint_project
from science.refusal import Refused

NAMES = ("project", "question", "task", "reuse")
LOCAL = re.compile(r"\[(\w+)\] \w+:([0-9a-f]{32})\.([0-9a-f]{32})\.([0-9a-f]{32})")


def test_reuse_copies_the_query_into_the_current_project_and_leaves_the_source(certified_work):
    """P4."""
    from beliefs.coordination import CoordinationAddress
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        myeloma, health = mint_project(d, "multiple-myeloma"), mint_project(d, "health")
        d._selection = myeloma
        kind, project, local, revision = LOCAL.search(
            d.invoke("question", {"name": "PHF19 and stage", "query": QUERY, "body": "why"}).text).groups()
        source = CoordinationAddress(project, local)
        before = ctx.coordination().resolve(source)
        d._selection = health
        copied = LOCAL.search(d.invoke("reuse", {"source": str(source)}).text).groups()
        after = ctx.coordination().resolve(source)
        copy = ctx.coordination().resolve(CoordinationAddress(copied[1], copied[2]))
    assert copied[0] == "question" and copied[1] == health.project
    assert copy.facets["coordination"]["query"] == before.facets["coordination"]["query"]
    assert copy.title == "PHF19 and stage"
    assert copy.body.startswith(f"Same query as {source}@{revision}.\n\nwhy")
    assert after.uid == before.uid  # the source is untouched


def test_reuse_takes_a_new_name(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        d._selection = mint_project(d)
        _, project, local, _ = LOCAL.search(d.invoke("question", {"name": "q", "query": QUERY}).text).groups()
        out = d.invoke("reuse", {"source": f"coord:{project}/{local}", "name": "renamed"})
    assert "renamed" in out.text


def test_reuse_needs_a_selection(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        d._selection = mint_project(d)
        _, project, local, _ = LOCAL.search(d.invoke("question", {"name": "q", "query": QUERY}).text).groups()
        d._selection = None
        with pytest.raises(Refused) as caught:
            d.invoke("reuse", {"source": f"coord:{project}/{local}"})
    assert caught.value.refusal.code == "no-current-project"


@pytest.mark.parametrize("make", ["task", "project"])
def test_reuse_of_a_non_view_or_a_project_refuses(certified_work, make):
    with coordination_rig(certified_work, NAMES) as (d, _):
        project = mint_project(d)
        d._selection = project
        if make == "task":
            _, p, local, _ = LOCAL.search(d.invoke("task", {"name": "t"}).text).groups()
            source = f"coord:{p}/{local}"
        else:
            source = str(project)
        with pytest.raises(Refused) as caught:
            d.invoke("reuse", {"source": source})
    assert caught.value.refusal.code == "invalid-input"
```

- [ ] **Step 2: Run them to verify they fail**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_cmd_reuse.py'`
Expected: FAIL — no `reuse` command.

- [ ] **Step 3: The declaration, prompt and handler**

`commands/reuse/command.toml`:

```toml
schema_version = 1
name = "reuse"
purpose = "Copy a question or hypothesis into the current project with the same query."
write_class = "coordination"
output_budget = 4096

[inputs.source]
type = "string"
required = true
doc = "The question or hypothesis to copy, as coord:<project>/<local>."
[inputs.name]
type = "string"
required = false
doc = "A name for the copy; absent, the source's."

[reads]
families = ["coordination"]
```

`commands/reuse/prompt.md`:

```markdown
Run `reuse` when a question or hypothesis from another project belongs
in the current one too. A question belongs to the project it was asked
in and never moves; `reuse` mints the current project's own record with
the same query, naming the source in its body. The source is untouched.
Report the minted record.
```

`python/src/science/commands/reuse.py`:

```python
"""reuse: the same-query mint, one act (spec §3.5, decision 7)."""
from __future__ import annotations

from science.coordination import content_of, now, parse_address, resolve_one
from science.refusal import Refusal, Refused
from science.report import Report, record_block

_REUSABLE = frozenset({"question", "hypothesis"})


def handle(ctx, writer, *, source, name=None) -> Report:
    project = ctx.current_project()
    if source.count("/") != 1:
        raise Refused(Refusal("invalid-input",
                              f"{source!r} is a project; copy its query into `project --query` instead"))
    address = parse_address(source, subordinate=True)
    tip = resolve_one(ctx, address)
    if tip.kind not in _REUSABLE:
        raise Refused(Refusal("invalid-input", f"{source} is a {tip.kind}; `reuse` copies a question or hypothesis"))
    original = content_of(tip)
    body = f"Same query as {address.pinned(tip.uid)}.\n\n{original['body']}"
    content = {"name": name or original["name"], "body": body, "author": writer.actor, "at": now(),
               "query": original["query"]}
    return (record_block(writer.mint_coordination(tip.kind, project=project, content=content)),)
```

- [ ] **Step 4: The CLI row and the adapters**

In the ops `cli.toml`, after the `revise` row:

```toml
[[cli.science.commands]]
path = ["reuse"]
summary = "Copy a question or hypothesis into the current project with the same query"
options = [
  { shared = "config", value = "path" },
  { names = ["--invocation-id"], value = "string" },
  { names = ["--continue"], value = "string" },
  { names = ["--source"], value = "string", required = true },
  { names = ["--name"], value = "string" },
]
```

Commit in ops, copy, regenerate adapters.

- [ ] **Step 5: Run the tests, then the suite**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_cmd_reuse.py tests/test_cli_surface.py tests/test_adapters.py'` then `just test-fast`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
tasks check
git add commands/reuse adapters tools/cli.toml python tasks
git commit -m "feat(commands): reuse, the same-query mint"
```

---

### Task 8: `science mcp serve` serves the service socket

**Files:**
- Modify: `python/src/science/serve.py` (split the socket checks and the server out of `serve`)
- Modify: `python/src/science/mcp.py` (`serve` binds the socket)
- Modify: `docs/specs/2026-08-31-command-framework-design.md` §9.3, `docs/specs/2026-09-24-coordination-command-set-design.md` §5.3
- Test: `python/tests/test_serve.py`, `python/tests/test_mcp_socket.py` (create)

**Interfaces:**
- Consumes: Task 2's `open_session`.
- Produces:
  - `science.serve.check_socket_path(socket_path: Path) -> None` — the length and existence refusals, before any session.
  - `science.serve.service_server(dispatcher, socket_path: Path, on_close: Callable[[], None]) -> socketserver.ThreadingUnixStreamServer` — binds the protocol; `server_close()` removes the socket it bound (only while the path is still the inode it bound) and then calls `on_close`.
  - `science.serve.serve(...)` unchanged in signature and behaviour except the clean-close unlink.

- [ ] **Step 1: Write the failing tests**

Add to `python/tests/test_serve.py`:

```python
def test_clean_close_removes_the_socket_it_bound(certified_work, short_tmp):
    cfg = build_fixture_world(certified_work)
    sock = short_tmp / "service.sock"
    server = serve(cfg, sock)
    assert sock.exists()
    server.server_close()
    assert not sock.exists()  # the next launcher can start


def test_close_leaves_a_socket_that_is_no_longer_the_one_bound(certified_work, short_tmp):
    cfg = build_fixture_world(certified_work)
    sock = short_tmp / "service.sock"
    server = serve(cfg, sock)
    sock.unlink()
    sock.touch()  # someone else's file now sits at the path
    server.server_close()
    assert sock.exists()
```

Create `python/tests/test_mcp_socket.py`:

```python
"""Decision 6: both launchers serve the whole service protocol on the socket."""
import io
import json
import os
import socket
import threading
import time

import pytest

from helpers.world import write_cli_config


class _BlockingStdin(io.RawIOBase):
    """Stdin that stays open until released, so the MCP server keeps running."""
    def __init__(self):
        self._read, self._write = os.pipe()

    def readable(self):
        return True

    def readinto(self, buffer):
        data = os.read(self._read, len(buffer))
        buffer[:len(data)] = data
        return len(data)

    def release(self):
        os.close(self._write)


def _wait_for(path, timeout=30):
    deadline = time.monotonic() + timeout
    while not path.exists():
        if time.monotonic() > deadline:
            raise AssertionError(f"{path} never appeared")
        time.sleep(0.05)


def _request(path, payload):
    with socket.socket(socket.AF_UNIX) as client:
        client.connect(str(path))
        client.sendall(json.dumps(payload).encode() + b"\n")
        return json.loads(client.makefile().readline())


def test_mcp_serve_accepts_cli_writes_on_the_socket_and_blocks_a_second_launcher(certified_work, short_tmp):
    from science.config import load_config
    from science.mcp import serve as mcp_serve
    from science.refusal import Refused
    from science.serve import serve as service_serve

    sock = short_tmp / "service.sock"
    config_path = write_cli_config(certified_work, service_socket=sock)
    stdin = _BlockingStdin()
    thread = threading.Thread(target=mcp_serve, args=(config_path,),
                              kwargs={"stdin": io.BufferedReader(stdin), "stdout": io.StringIO(),
                                      "stderr": io.StringIO()}, daemon=True)
    thread.start()
    try:
        _wait_for(sock)
        reply = _request(sock, {"command": "project",
                                "inputs": {"name": "via-socket",
                                           "query": "version: science.view-query.v1\nclauses: []\n"}})
        assert reply["ok"] and "[project]" in reply["text"]
        with pytest.raises(Refused) as caught:
            service_serve(load_config(config_path), sock)
        assert "socket already exists" in caught.value.refusal.message
    finally:
        stdin.release()
        thread.join(timeout=30)
    assert not thread.is_alive()
    assert not sock.exists()  # clean shutdown removed it
```

`short_tmp` is `test_serve.py`'s fixture; move it to `python/tests/conftest.py` so both files share it (cut it from `test_serve.py` with its imports of `shutil`, `tempfile` and `Path` where no longer used).

- [ ] **Step 2: Run them to verify they fail**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_serve.py tests/test_mcp_socket.py'`
Expected: FAIL — the socket survives a clean close, and the MCP server binds none.

- [ ] **Step 3: Split `serve.py`**

Restructure `python/src/science/serve.py` so the socket checks and the server are reusable:

```python
def check_socket_path(socket_path: Path) -> None:
    """Every pre-session socket refusal, so a launcher refuses before its session exists."""
    encoded = len(str(socket_path).encode())
    if encoded > MAX_SOCKET_PATH_BYTES:
        raise Refused(Refusal(
            "invalid-input",
            f"socket path is {encoded} bytes; the AF_UNIX limit is "
            f"{MAX_SOCKET_PATH_BYTES}: {socket_path}",
        ))
    if socket_path.exists():
        raise Refused(Refusal(
            "invalid-input",
            f"socket already exists: {socket_path}; another launcher holds this world, or a "
            "crashed one left it — a stale one is the operator's to remove",
        ))


def service_server(dispatcher, socket_path: Path, on_close):
    """The service protocol for `dispatcher` at `socket_path`. Closing removes the
    socket this server bound — only while the path is still that inode, so a file
    someone else put there survives — then calls `on_close`."""

    class Handler(socketserver.StreamRequestHandler):
        def handle(self) -> None:
            ...  # the existing request loop, unchanged, calling dispatcher.invoke

    class Server(socketserver.ThreadingUnixStreamServer):
        daemon_threads = True  # (keep the existing comment)

        def server_bind(self) -> None:
            super().server_bind()
            self.bound_inode = os.stat(self.server_address).st_ino

        def server_close(self) -> None:
            try:
                super().server_close()
                try:
                    if os.stat(socket_path).st_ino == self.bound_inode:
                        os.unlink(socket_path)
                except FileNotFoundError:
                    pass
            finally:
                on_close()

    socket_path.parent.mkdir(parents=True, exist_ok=True)
    return Server(str(socket_path), Handler)


def serve(config: ScienceConfig, socket_path: Path, declarations=None, handlers=None, stderr=None):
    """`declarations`/`handlers` default to the production tree; tests inject
    their synthetic set here — production code never imports test modules."""
    if declarations is None:
        from science.loader import production_tree, resolve_handlers

        declarations = production_tree()
        handlers = resolve_handlers(declarations)
    check_socket_path(socket_path)
    session = open_session(config)
    try:
        report_findings(session.findings, reported_by=session.session_id,
                        stream=sys.stderr if stderr is None else stderr)
        dispatcher = Dispatcher(declarations, handlers, ReadContext.open(config), session=session)
        return service_server(dispatcher, socket_path, on_close=session.close)
    except BaseException:
        session.close()
        raise
```

Move the existing `Handler.handle` body verbatim into the new `Handler`. Replace the old "No unlink anywhere" comment: the unlink is now the bound server's own socket at clean close; a stale socket still refuses at start. Import `os`.

- [ ] **Step 4: The MCP launcher binds it**

In `mcp.py` `serve`, after `config = load_config(config_path)`:

```python
    from science.serve import check_socket_path, service_server
    import threading

    check_socket_path(config.service_socket)
    session = open_session(config)
    server, serving = None, False
    try:
        report_findings(...)  # unchanged
        dispatcher = Dispatcher(declarations, resolve_handlers(declarations), ReadContext.open(config),
                                session=session)
        # One live session per world (projects design §5.1a): CLI writes and, in
        # part 2, the selection query reach this session over the same socket
        # `science serve` would bind, and a second launcher refuses on it.
        server = service_server(dispatcher, config.service_socket, on_close=lambda: None)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        serving = True
        while True:
            ...  # the stdio loop, unchanged
    finally:
        if server is not None:
            if serving:
                server.shutdown()  # blocks until serve_forever returns, so only once it runs
            server.server_close()
        session.close()
```

The dispatcher's lock already serializes writes arriving from the two transports.

- [ ] **Step 5: Run the tests, then the suite**

Run: `python3 tools/tt test-one -- sh -c 'cd python && uv run pytest -q tests/test_serve.py tests/test_mcp_socket.py tests/test_mcp.py'` then `just test-fast`
Expected: PASS. If an existing MCP test drives `serve` with a `service_socket` longer than 107 bytes, give it a short one through `write_cli_config(..., service_socket=short_tmp / "service.sock")`.

- [ ] **Step 6: Amend the designs**

In the framework design §9.3, append:

```markdown
**Amended 2026-09-24** (coordination command set design, decision 6).
`science mcp serve` also binds the configuration's `service_socket` and serves the
§9.2 service protocol on it with the dispatcher its stdio loop uses, so a CLI write
made while an MCP session is live reaches that one session, and whichever launcher
starts second refuses on the existing socket. A launcher removes the socket it bound
at clean shutdown; a stale socket from a crash still refuses at start.
```

In the coordination spec §5.3, append the same last sentence as a dated line:
"**Amended 2026-09-24 (planning):** a launcher removes the socket it bound at clean shutdown, while the path is still that inode; a stale socket from a crash still refuses at start, so the MCP launcher's restart after a clean exit does not."

- [ ] **Step 7: Commit**

```bash
tasks check
git add python docs/specs tasks
git commit -m "feat(mcp): serve the service socket; launchers remove the socket they bound"
```

---

### Task 9: Close out part 1

**Files:**
- Modify: `docs/specs/2026-09-24-coordination-command-set-design.md` (status line), `docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md` §7
- Modify: `tasks/` (goal notes)

- [ ] **Step 1: The dated notes**

In the projects design §7, after the bullet describing the same-query mint, add: "*Amended 2026-09-24:* the source address is carried in the new view's `body`, one act; a separate `note` record would be a second act and cannot hold a `coord:` address (coordination command set design, decision 7)."

Set the coordination spec's status line to: "**Status:** reviewed and approved 2026-09-24; part 1 (the write surface) implemented <date>, plan `docs/plans/2026-09-24-coordination-write-surface.md`. Parts 2 and 3 wait on `beliefs-cc0aea`, `beliefs-1148ad`, `beliefs-1af3fd` and `beliefs-fe7149`."

- [ ] **Step 2: The gate**

Run: `just gate`
Expected: PASS.

- [ ] **Step 3: Commit, and hand the branch to review**

```bash
tasks check
git add docs tasks
git commit -m "docs: coordination command set part 1 landed"
```

The goal `sci-c5528e` stays open: its part 2 and part 3 children wait on the `beliefs` seams.
