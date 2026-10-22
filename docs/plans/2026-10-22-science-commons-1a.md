# Science commons milestone 1a Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** One complete collaboration between two installations over git, with no
overlapping records: *A* publishes a reproducible view to a git remote; *B* binds *A*'s
location, adopts the publication, fetches the dataset's bytes, reproduces one
assessment, derives a changed analysis over *A*'s mounted records, and publishes to its
own remote; *B*'s belief honours an accept policy and says so.

**Architecture:** Science gains a sharing registry under `sharing_root` whose mounted
roots the loader unions into the kernel's `corpus_roots`; a `sharing` write class whose
commands (`provider-bind`, `adopt`) reach the kernel's `restore_root` and
`admit_publication` through session doors the kernel adds (`beliefs-f24fe9`) and whose
ledger evidence is the pin; a `publishes`-class `publish` command over a git
`Transport`, with a read-only `publish-preview` as its dry run; a `fetch` command that
composes the holdings boundary's `look` and store `write`; and an `AcceptancePolicy`
computed from the registry and the mounts' markers, handed to every belief read. No
science storage beyond the registry, which is the durable effect of ledgered acts.

**Tech Stack:** Python 3 stdlib (`argparse`, `json`, `subprocess` for `git`), the
`beliefs` kernel (editable path dependency), pytest with the certified-world fixtures and
`helpers.snapshot`.

**Spec:** `docs/specs/2026-09-30-science-commons-design.md` (§3, §4.4, §4.5, §4.8,
§4.11, §5, §7.4, §8, §9, §10, §11, §12 part 1a). Framework amendments:
`docs/specs/2026-08-31-command-framework-design.md` §3.3, §4.4 (2026-10-01), §9.1
(2026-10-01). Kernel designs consumed: beliefs
`docs/superpowers/specs/2026-09-26-publish-act-remote-design.md` §3.1, §7;
`2026-10-02-belief-acceptance-design.md` §4; `2026-10-02-publication-attribution-design.md`
§4; `2026-10-01-mount-citations-design.md` decision 2.

## Global Constraints

- Every durable thing is a governed record in a `beliefs` corpus; the sharing registry is
  the one exception the spec makes (§7.4) and every registry write is the effect of a
  ledgered `sharing` act.
- No command calls `pytest` directly: `just test-one <args>` while working,
  `just test-fast` before each commit. Paths given to `test-one` are relative to `python/`.
- A new command is a row in `tools/cli.toml` first (AGENTS.md). The authority is
  `cli.toml` at the root of the `ops` checkout (`tasks projects --paths` names it): edit
  its `[cli.science]` section there, commit in ops,
  then `python3 bin/vendored adopt cli.toml` here (the header's `just vendor-cli` no longer
  exists). Every command row repeats `--config`, `--invocation-id`, `--continue`, then one
  option per input, as the existing rows do (`tools/cli.toml:985-1266`).
- Adding or changing a command regenerates `adapters/claude-code` (`science adapters
  build`); `test_adapters.py::test_generated_tree_matches_committed` pins it.
- Command directories are `commands/<name>/` with exactly `command.toml` and `prompt.md`;
  handler module `science.commands.<name with - as _>`, function `handle`; signatures
  `handle(ctx, *, ...)` read-only, `handle(ctx, writer, *, ...)` every write class
  (`loader.resolve_handlers`). Optional inputs default to `None`.
- Refusal codes are the closed set `science/refusal.py:CODES`; this plan adds exactly
  `pin-unsourced`, `world-mismatch`, `adopt-conflict`. Everything else reuses
  `invalid-input` or `kernel-refused`.
- Write reports carry only record blocks this invocation minted
  (`render.audit_write_report`); a `sharing` report carries only pin blocks the ledger's
  sharing lines of this invocation support (Task 4).
- Remote destinations are canonical http(s) URLs (`beliefs.intents.publish.Destination`);
  a git remote is reached through such a URL. Tests use `https://remote.test/<name>`
  mapped to a bare repository.
- Coordination contract **v3** is required wherever a marker must carry attribution
  entries: both fixture worlds pin v3 (`shipped_coordination(3)`); the shipped fixtures'
  v2 profile is unchanged.
- Hyphenated multi-word commands (`provider-bind`, `publish-preview`), as
  `project-select` is.
- Kernel dependency: Tasks 4, 6, 7 and 8 consume the doors `beliefs-f24fe9` adds. Their
  Interfaces blocks state the names this plan assumes; when that task lands with other
  names, update the Interfaces block and the code together, never the design. A task
  that reaches a door before it exists stops and parks `--reason dependency`.
- Dates in this plan: the plan is written 2026-10-22; documents amended by Task 12 carry
  that date.

## Review Focus

Inputs the spec implies but no task's tests exercise directly, most likely to bite first;
each line's test is added to the owning task below.

1. **A `sharing_root` whose registry names a mounted root that no longer exists on disk**
   (moved or deleted): the loader must refuse `invalid-input` naming the pin, not open a
   session that silently mounts fewer corpora. Test in Task 1.
2. **`adopt` of a corpus id the remote does not hold, or a location that is not a git
   repository**: a clear `invalid-input` naming the location, nothing written to the
   registry, no scratch left behind. Test in Task 7.
3. **`provider-bind --world` given a world id in the wrong shape** (not 32 lowercase
   hex): `invalid-input` before any fetch. Test in Task 6.
4. **`fetch --from <path>` whose bytes do not match the declared digest**: refuse
   `invalid-input` naming both digests, write nothing to the store. Test in Task 8.
5. **A session opened with `accept` naming a world no pin confirms**: belief still
   answers; the acceptance context lists the policy and excludes nothing extra, and the
   unconfirmed world simply never admits a record. Test in Task 9.

---

## File structure

- Create `python/src/science/sharing.py` — registry types and the on-disk registry
  (Task 2).
- Modify `python/src/science/config.py` — three configuration keys, `ScienceConfig`
  fields, union of mounted roots (Task 1); `ReadContext.evaluate`/`gather_inputs` pass the
  acceptance policy (Task 9).
- Modify `python/src/science/schema.py`, `dispatch.py`, `render.py`, `report.py`,
  `refusal.py` — the `sharing` write class, its invocation path, `PinBlock`, three
  refusal codes (Task 4).
- Create `python/src/science/transport_git.py` — the git `Transport` plus
  `fetch_corpus` (Task 3).
- Create `python/src/science/publication.py` — shared reads: a corpus's marker,
  artifact identity, the head-artifact sibling, destination parsing (Task 5).
- Create `commands/publish/`, `commands/publish-preview/`, `commands/provider-bind/`,
  `commands/adopt/`, `commands/show/`, `commands/fetch/` and their handler modules under
  `python/src/science/commands/` (Tasks 5–8, 10).
- Create `python/src/science/acceptance.py` — the accept policy computation (Task 9);
  modify `closure.py` and `commands/belief.py`.
- Create `python/tests/helpers/commons.py` — the two-installation fixture (Task 11);
  `python/tests/test_commons_1a.py` — the milestone's decisive cases (Task 11).
- Modify `tools/cli.toml` (via ops), `adapters/claude-code/`, the commons spec, the
  framework spec's §9.1 pointer, `README.md`/`AGENTS.md` if `ops-docs check` asks
  (Task 12).

---

### Task 1: Configuration keys and mounts derived from the sharing registry

**Files:**
- Modify: `python/src/science/config.py:31-56` (`_OPTIONAL_KEYS`, `ScienceConfig`),
  `python/src/science/config.py:78-190` (`load_config`)
- Test: `python/tests/test_config_sharing.py`

**Interfaces:**
- Consumes: `science.sharing.SharingRegistry` (Task 2) — `SharingRegistry(root: Path)`,
  `.mounted_roots() -> tuple[Path, ...]`, raising `SharingRegistryMalformed(entry: str,
  reason: str)`. Task 1 is written against this interface; implement Task 2's registry
  first or stub it in the same commit series (Task 2 lands before Task 1's final
  commit; do them in order 2 then 1 if preferred).
- Produces: `ScienceConfig.sharing_root: Path | None = None`,
  `ScienceConfig.accept: tuple[str, ...] = ()`,
  `ScienceConfig.fetch: FetchPolicy = FetchPolicy("records-only", 0)` with
  `@dataclass(frozen=True) class FetchPolicy: policy: Literal["records-only", "fetch"];
  max_bytes: int`. `load_config` unions `SharingRegistry(sharing_root).mounted_roots()`
  into `WorldConfig.corpus_roots` (sorted, deduplicated by resolved path) before building
  `WorldConfig`; `write_root` and `read_contracts` validation runs over the union
  unchanged.

- [ ] **Step 1: Write the failing tests**

```python
# python/tests/test_config_sharing.py
def test_sharing_keys_load_with_defaults(tmp_path):
    cfg = load_config(write_minimal_config(tmp_path))          # existing helper pattern: test_config.py
    assert cfg.sharing_root is None and cfg.accept == () and cfg.fetch == FetchPolicy("records-only", 0)

def test_accept_must_be_world_ids(tmp_path):
    refusal = refused(lambda: load_config(write_minimal_config(tmp_path, accept=["abc"])))
    assert refusal.code == "invalid-input" and "accept" in refusal.message

def test_fetch_table_validates_policy_and_bound(tmp_path):
    assert load_config(write_minimal_config(tmp_path, fetch={"policy": "fetch", "max_bytes": 0})).fetch == FetchPolicy("fetch", 0)
    for bad in ({"policy": "maybe"}, {"policy": "fetch", "max_bytes": -1}, {"policy": "fetch", "extra": 1}):
        assert refused(lambda: load_config(write_minimal_config(tmp_path, fetch=bad))).code == "invalid-input"

def test_mounted_registry_roots_join_corpus_roots(tmp_path, certified_work):
    # a registry under tmp_path/sharing with one pin in state "mounted" whose root is a fixture corpus
    cfg = load_config(write_minimal_config(tmp_path, sharing_root="sharing"))
    assert mounted_root in cfg.world.corpus_roots and cfg.write_root == original_root

def test_a_mounted_root_missing_on_disk_refuses_naming_the_pin(tmp_path):
    refusal = refused(lambda: load_config(write_minimal_config(tmp_path, sharing_root="sharing")))  # pin names a vanished root
    assert refusal.code == "invalid-input" and corpus_id in refusal.message

def test_a_malformed_registry_refuses_naming_the_entry(tmp_path):
    (tmp_path / "sharing" / "pins" / "x.json").write_text("{")
    refusal = refused(lambda: load_config(write_minimal_config(tmp_path, sharing_root="sharing")))
    assert refusal.code == "invalid-input" and "pins/x.json" in refusal.message
```

`write_minimal_config` wraps `test_config.py`'s `write_config` with keyword overrides
for `accept`, `fetch` and `sharing_root`; `refused(call)` is `pytest.raises(Refused)`
returning `.refusal`, the shape `test_cmd_project_select.py::_refused` has. Both live in
`python/tests/helpers/commons.py` (Task 11's module; create it with these two helpers
here and let Task 11 extend it).

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_config_sharing.py -v`
Expected: FAIL — unknown config keys refused / `FetchPolicy` not defined.

- [ ] **Step 3: Implement the keys**

In `config.py`: add `"sharing_root", "accept", "fetch"` to `_OPTIONAL_KEYS`; define
`FetchPolicy`; parse `accept` as a list of 32-lowercase-hex strings (else `_refuse`
naming the key), `fetch` as a table with exactly `policy` (required, one of the two
values) and optional `max_bytes` (int ≥ 0, default 0); resolve `sharing_root` with
`located()`; when present, `roots = SharingRegistry(sharing_root).mounted_roots()`,
refuse `invalid-input` for `SharingRegistryMalformed` (message names `entry` and
`reason`) and for a mounted root with no `corpus.yaml` manifest (message names the pin's
corpus id and path); union into `corpus_roots` before the `write_root` check.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_config_sharing.py tests/test_config.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/config.py python/tests/test_config_sharing.py
git commit -m "feat(config): sharing_root, accept and fetch keys; mounts union the registry's mounted roots"
```

---

### Task 2: The sharing registry

**Files:**
- Create: `python/src/science/sharing.py`
- Test: `python/tests/test_sharing_registry.py`

**Interfaces:**
- Produces:

```python
@dataclass(frozen=True)
class PinSource:            # §4.4 layer 4
    kind: Literal["provider", "catalog"]
    reference: str          # the bound location URL, or the catalog artifact identity

@dataclass(frozen=True)
class FetchRecord:          # §4.5
    location: str           # canonical URL fetched from
    at: str                 # UTC "%Y-%m-%dT%H:%M:%SZ"
    verdict: str            # restore_root's LogReport.outcome, "validated" on success

@dataclass(frozen=True)
class Pin:
    corpus_id: str          # 32 hex
    marker: str             # 32 hex marker uid
    artifact: str           # 64 hex sha256 of the head-artifact sibling bytes
    world: str              # the marker's published_from.world_id (a claim, §4.4 layer 2)
    view: str               # the marker's view address
    source: PinSource | None
    fetch: FetchRecord
    state: Literal["fetched", "admitted", "mounted", "retired"]
    keep: bool = False
    def origin_confirmed(self, bindings: Mapping[str, "ProviderBinding"]) -> bool: ...
        # source.kind == "provider" and bindings[self.world].confirmed and source.reference in bindings[self.world].locations

@dataclass(frozen=True)
class ProviderBinding:      # §4.4 layer 3, §7.3
    world: str
    locations: tuple[str, ...]
    bound_since: str
    confirmed: bool
    via: tuple[str, ...] = ()

class SharingRegistryMalformed(Exception):
    entry: str; reason: str

class SharingRegistry:
    def __init__(self, root: Path) -> None: ...        # creates pins/ providers/ follows/ roots/ scratch/ on first write only
    def pins(self) -> tuple[Pin, ...]: ...             # sorted by corpus_id
    def pin(self, corpus_id: str) -> Pin | None: ...
    def write_pin(self, pin: Pin) -> None: ...         # atomic: temp file, fsync, rename
    def bindings(self) -> dict[str, ProviderBinding]: ...   # keyed by world
    def binding_for_location(self, location: str) -> ProviderBinding | None: ...
    def write_binding(self, binding: ProviderBinding) -> None: ...
    def root_for(self, corpus_id: str) -> Path: ...    # <root>/roots/<corpus_id>
    def scratch(self, token: str) -> Path: ...         # <root>/scratch/<token>
    def mounted_roots(self) -> tuple[Path, ...]: ...   # root_for of every pin in state "mounted"
```

  Layout: `pins/<corpus_id>.json`, `providers/<world>.json`, both JSON with sorted keys and
  a `"version": 1` member; `follows/` reserved (milestone 2); `roots/<corpus_id>/` the
  restored corpus root; `scratch/<token>/` transient. A file that fails to parse or whose
  fields fail validation (hex widths, state set, source kind) raises
  `SharingRegistryMalformed("pins/<name>", reason)`.

- [ ] **Step 1: Write the failing tests**

```python
def test_pin_round_trips_and_sorts(tmp_path):
    registry = SharingRegistry(tmp_path / "sharing")
    registry.write_pin(PIN_B); registry.write_pin(PIN_A)      # PIN_A.corpus_id < PIN_B.corpus_id
    assert registry.pins() == (PIN_A, PIN_B) and registry.pin(PIN_A.corpus_id) == PIN_A

def test_mounted_roots_are_exactly_the_mounted_pins(tmp_path):
    ...write PIN_A as "fetched", PIN_B as "mounted"...
    assert registry.mounted_roots() == (registry.root_for(PIN_B.corpus_id),)

def test_binding_for_location_matches_a_bound_location_only(tmp_path):
    registry.write_binding(ProviderBinding(WORLD_A, ("https://remote.test/a",), AT, True))
    assert registry.binding_for_location("https://remote.test/a").world == WORLD_A
    assert registry.binding_for_location("https://remote.test/b") is None

def test_origin_confirmed_needs_a_confirmed_binding_to_the_markers_world(tmp_path):
    pin = replace(PIN_A, source=PinSource("provider", "https://remote.test/a"))
    assert pin.origin_confirmed({WORLD_A: BINDING_A})
    assert not pin.origin_confirmed({WORLD_A: replace(BINDING_A, confirmed=False)})
    assert not pin.origin_confirmed({"f" * 32: BINDING_A})       # bound to another world
    assert not replace(pin, source=PinSource("catalog", "ab" * 32)).origin_confirmed({WORLD_A: BINDING_A})

@pytest.mark.parametrize("damage", ["{", '{"version": 1, "corpus_id": "short"}', '{"version": 2}'])
def test_malformed_pin_names_its_file(tmp_path, damage):
    (tmp_path / "sharing" / "pins").mkdir(parents=True)
    (tmp_path / "sharing" / "pins" / "x.json").write_text(damage)
    with pytest.raises(SharingRegistryMalformed) as caught:
        SharingRegistry(tmp_path / "sharing").pins()
    assert caught.value.entry == "pins/x.json"

def test_write_is_atomic_leaves_no_temp_file(tmp_path):
    registry.write_pin(PIN_A)
    assert sorted(p.name for p in (tmp_path / "sharing" / "pins").iterdir()) == [f"{PIN_A.corpus_id}.json"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_sharing_registry.py -v`
Expected: FAIL with `ModuleNotFoundError: science.sharing`.

- [ ] **Step 3: Implement `science/sharing.py` per the Interfaces block**

Serialize dataclasses with `dataclasses.asdict`; validate on read with explicit checks
(no silent defaults). Write with `tempfile.NamedTemporaryFile(dir=..., delete=False)`,
`os.fsync`, `os.replace`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_sharing_registry.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/sharing.py python/tests/test_sharing_registry.py
git commit -m "feat(sharing): the sharing registry: pins, provider bindings, adopted roots"
```

---

### Task 3: The git transport

**Files:**
- Create: `python/src/science/transport_git.py`
- Test: `python/tests/test_transport_git.py`

**Interfaces:**
- Consumes: `beliefs.transport.Transport`, `TransportAbandoned`, `transport_files`,
  `local_listing`; `beliefs.intents.publish.Destination`.
- Produces:

```python
def identity_remote(destination: Destination) -> str: ...   # the locator itself: a https git remote
class GitTransport:
    def __init__(self, cache: Path, *, remote_for: Callable[[Destination], str] = identity_remote,
                 git: str = "git", branch: str = "main") -> None: ...
    # test seams, None in production:
    fail_after_files: int | None   # raise GitTransportFault after copying this many files, before commit
    fail_after_push: bool          # raise GitTransportFault after a successful push, before returning
    def push(self, destination: Destination, files: Mapping[str, Path]) -> TransportAbandoned | None: ...
    def listing(self, destination: Destination, corpus_id: str) -> dict[str, str]: ...
    def fetch_corpus(self, destination: Destination, corpus_id: str, into: Path) -> tuple[Path, bytes]: ...
        # (into/<corpus_id>, sibling bytes); raises GitTransportFault naming the location when the
        # remote is unreachable or holds no such corpus
class GitTransportFault(Exception): ...   # transient: the act propagates it (remote design decision 4)
```

  `push`: local clone at `cache/<sha256(locator)[:16]>` (clone, or `git init` +
  `git remote add origin <remote>` when the remote has no branch yet; `git fetch origin`
  and reset to `origin/<branch>` when it has one); copy each named file to its name under
  the work tree; `git add -A -- <names>`; if `git diff --cached --quiet` exits 0 commit
  nothing and return `None`; else `git commit -m "publish <corpus_id>"` with
  `GIT_AUTHOR_*`/`GIT_COMMITTER_*` set from the environment or `science <world id>` defaults,
  then `git push origin HEAD:refs/heads/<branch>`. A non-fast-forward is retried once
  after a fetch and rebase-free reset (another publisher's commit does not touch these
  names); a second failure raises `GitTransportFault`. The container is never pruned:
  `push` only adds.
  `listing`: fetch, then `git ls-tree -r --name-only origin/<branch>` filtered to
  `<corpus_id>.head-artifact.v1` and `<corpus_id>/...`, each blob's bytes via
  `git cat-file blob <rev>:<name>` hashed with sha256.
  `fetch_corpus`: the same clone; `git archive`-free copy of the tree's `<corpus_id>/`
  directory into `into/<corpus_id>` and the sibling's bytes returned.
  Every subprocess runs with `env` built key by key: `PATH`, `HOME` (a directory under
  `cache`), `GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_NOSYSTEM=1`, the author/committer
  variables; never the inherited environment.

- [ ] **Step 1: Write the failing tests**

```python
@pytest.fixture
def remote(tmp_path):
    bare = tmp_path / "remotes" / "a.git"; bare.parent.mkdir()
    subprocess.run(["git", "init", "--bare", "-b", "main", str(bare)], check=True, env=GIT_ENV)
    return Destination.remote("https://remote.test/a"), bare

def transport(tmp_path, bare, **seams):
    return GitTransport(tmp_path / "cache", remote_for=lambda d: str(bare), **seams)

def test_push_then_listing_equals_local_listing(tmp_path, remote, export):   # export: a fixture dir with <cid>/ and sibling
    dest, bare = remote
    t = transport(tmp_path, bare)
    files = transport_files(export, CID)
    assert t.push(dest, files) is None
    assert t.listing(dest, CID) == local_listing(files)

def test_a_second_push_of_present_files_commits_nothing(tmp_path, remote, export):
    ...push twice...
    assert commit_count(bare) == 1

def test_push_failing_after_push_converges_on_retry(tmp_path, remote, export):
    t = transport(tmp_path, bare); t.fail_after_push = True
    with pytest.raises(GitTransportFault): t.push(dest, files)
    t.fail_after_push = False
    assert t.push(dest, files) is None and commit_count(bare) == 1 and t.listing(dest, CID) == local_listing(files)

def test_push_failing_before_commit_leaves_the_remote_untouched(tmp_path, remote, export):
    t = transport(tmp_path, bare); t.fail_after_files = 1
    with pytest.raises(GitTransportFault): t.push(dest, files)
    assert t.listing(dest, CID) == {} and commit_count(bare) == 0

def test_listing_sees_an_extra_file_the_act_did_not_ask_for(tmp_path, remote, export):
    ...push, then commit an extra file under <CID>/stray directly into the bare repo...
    assert f"{CID}/stray" in t.listing(dest, CID)

def test_fetch_corpus_materializes_the_root_and_sibling(tmp_path, remote, export):
    root, sibling = t.fetch_corpus(dest, CID, tmp_path / "into")
    assert sorted(p.relative_to(root) for p in root.rglob("*") if p.is_file()) == sorted(...export files...)
    assert sibling == (export / f"{CID}.head-artifact.v1").read_bytes()

def test_fetch_corpus_of_an_absent_corpus_names_the_location(tmp_path, remote):
    with pytest.raises(GitTransportFault) as caught: t.fetch_corpus(dest, "0" * 32, tmp_path / "into")
    assert "https://remote.test/a" in str(caught.value)

def test_subprocess_environment_is_built_not_inherited(tmp_path, remote, monkeypatch):
    monkeypatch.setenv("SECRET_TOKEN", "x")
    captured = {}
    monkeypatch.setattr(transport_git.subprocess, "run", lambda *a, **k: captured.update(k) or FakeCompleted())
    ...call listing...
    assert "SECRET_TOKEN" not in captured["env"] and captured["env"]["GIT_CONFIG_GLOBAL"] == "/dev/null"
```

`export` builds a two-file corpus directory plus sibling with arbitrary bytes under
`tmp_path`: the transport moves bytes and never reads them as records.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_transport_git.py -v`
Expected: FAIL with `ModuleNotFoundError: science.transport_git`.

- [ ] **Step 3: Implement `science/transport_git.py` per the Interfaces block**

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_transport_git.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/transport_git.py python/tests/test_transport_git.py
git commit -m "feat(transport): git transport: idempotent push, remote listing, corpus fetch"
```

---

### Task 4: The `sharing` write class, its invocation path and pin blocks

**Files:**
- Modify: `python/src/science/schema.py:17,136-161`; `python/src/science/dispatch.py:171-184,228-292,408-440`;
  `python/src/science/report.py`; `python/src/science/render.py:32-50`; `python/src/science/refusal.py:9-14`
- Test: `python/tests/test_dispatch_sharing.py`, extend `python/tests/test_schema.py`,
  `python/tests/test_report.py`

**Interfaces:**
- Consumes (kernel, `beliefs-f24fe9`; names assumed):
  `beliefs.permit.RequiredCapabilities.sharing()`;
  `WriterSession.invocation_sharing(iid) -> tuple[SharingLine, ...]` and
  `LedgerReader.invocation(iid).sharing` with
  `SharingLine(invocation, corpus, marker, artifact, world, source, location, verdict,
  transition)` where `transition ∈ {"inspected", "bound", "fetched", "admitted",
  "mounted", "retired"}`.
- Produces:
  - `WRITE_CLASS_KINDS` gains `"sharing"`; `_parse_write_class` accepts the bare word.
  - `Dispatcher._required` maps `sharing` to `RequiredCapabilities.sharing()`.
  - `Dispatcher._invoke_sharing(decl, canonical, iid)`: the write protocol (claim, scoped
    writer, handler `(ctx, writer, **inputs)`, close) whose report is rebuilt from the
    ledger: `self._pin_report(lines)` = one `PinBlock` per sharing line, in ledger order.
    `audit_sharing_report(report, lines)` requires every block to be a `PinBlock` equal
    to `pin_block(line)` for some line of this invocation. `_continue_write` and
    `_replay_outcome` branch on the class like `session` does.
  - `report.PinBlock(corpus_id, marker, artifact, world, source, location, verdict,
    transition)` and `pin_block(line) -> PinBlock`; `serialize_block` renders it as
    `[pin] <corpus_id> <transition>` then one `key: value` line per remaining field.
  - `refusal.CODES` gains `pin-unsourced`, `world-mismatch`, `adopt-conflict`.
  - A fixture declaration `python/tests/fixtures/commands/share-probe/command.toml`
    (`write_class = "sharing"`) with a handler the test registers through
    `coordination_rig(extra=...)`, mirroring `pub-view`.

- [ ] **Step 1: Write the failing tests**

```python
def test_sharing_is_a_write_class(fixture_decl_dir):
    assert load_declaration(fixture_decl_dir / "share-probe", kind_acts=KIND_ACTS, contract_kinds=KINDS).write_class.kind == "sharing"

def test_required_for_sharing_is_the_kernel_sharing_requirement(dispatcher):
    assert dispatcher._required(SHARE_PROBE) == RequiredCapabilities.sharing()

def test_a_sharing_invocation_reports_exactly_its_ledgered_pins(certified_work):
    # the probe handler calls writer.restore(...) on a prepared copy and returns (pin_block(line),)
    with coordination_rig(certified_work, (), extra=((SHARE_PROBE, probe_handler),)) as (d, _):
        text = d.invoke("share-probe", {"copy": str(copy)}).text
        assert text.startswith(f"[pin] {CID} fetched\n")

def test_a_sharing_report_with_a_block_the_ledger_does_not_show_is_an_audit_violation(certified_work):
    ...handler returns a PinBlock for another corpus id...
    with pytest.raises(AuditViolation): d.invoke("share-probe", {...})

def test_replay_of_a_sharing_invocation_re_renders_from_the_ledger(certified_work):
    first = d.invoke("share-probe", inputs, invocation_id="i1").text
    assert d.invoke("share-probe", inputs, invocation_id="i1").text == first

def test_new_refusal_codes_construct():
    for code in ("pin-unsourced", "world-mismatch", "adopt-conflict"):
        Refusal(code, "x")
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_dispatch_sharing.py tests/test_schema.py -v`
Expected: FAIL — `sharing` not a write class / `RequiredCapabilities.sharing` missing.
If the kernel door is not yet on `beliefs` main, stop here and park
`--reason dependency` naming `beliefs-f24fe9`.

- [ ] **Step 3: Implement per the Interfaces block**

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_dispatch_sharing.py tests/test_schema.py tests/test_report.py tests/test_dispatch.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/schema.py python/src/science/dispatch.py python/src/science/report.py python/src/science/render.py python/src/science/refusal.py python/tests/test_dispatch_sharing.py python/tests/fixtures/commands/share-probe
git commit -m "feat(framework): the sharing write class, its ledger-rebuilt pin report, three refusal codes"
```

---

### Task 5: `publish` and `publish-preview`

**Files:**
- Create: `commands/publish/command.toml`, `commands/publish/prompt.md`,
  `commands/publish-preview/command.toml`, `commands/publish-preview/prompt.md`,
  `python/src/science/commands/publish.py`, `python/src/science/commands/publish_preview.py`,
  `python/src/science/publication.py`
- Test: `python/tests/test_cmd_publish.py`

**Interfaces:**
- Consumes (kernel, `beliefs-f24fe9`; names assumed):
  `ScopedWriter.publish(*, view: CoordinationAddress, destination: Destination,
  operations_root: Path, staging_profile: ProfileSpec, transport: Transport | None)
  -> Published | PublishRefused | PublishUnresolved`;
  `beliefs.publish.publication_preview(world: World, resolver: CoordinationResolver,
  view: CoordinationAddress, *, own_profile: ProfileSpec) -> PublicationPreview` with
  fields `view (pinned)`, `selected: tuple[str, ...]`, `closure_missing: tuple[str, ...]`,
  `pins`, `attributions: tuple[tuple[str, str, str], ...]`, `contributing: tuple[str, ...]`.
  Also `science.coordination.resolve_project_ref(ctx, text)` (exists) for the `view`
  input; `science.transport_git.GitTransport` (Task 3).
- Produces:
  - `science/publication.py`: `parse_destination(text: str) -> Destination` (absolute
    path → `Destination.local`, `https://…` → `Destination.remote`, else `invalid-input`);
    `transport_for(config, destination) -> Transport | None` (`None` for local; a
    `GitTransport(config.operations_root / "transport", remote_for=REMOTE_FOR)` for remote,
    where module attribute `REMOTE_FOR = identity_remote` is the test seam);
    `marker_of(root: Path) -> Node` (the one `publication` record of a corpus root, via
    `ReadView.opened_at`), `marker_fields(node) -> MarkerFields(uid, world, view,
    selection, attributions: dict[str, tuple[str, str]], supersedes)`;
    `artifact_identity(sibling: bytes) -> str` (sha256 hex).
  - `publish` declaration: `write_class = "publishes"`, inputs `view` (string, required:
    a project name or `coord:` address), `to` (string, required), `[reads] families =
    ["coordination", "corpus-stored"]`. Handler: resolve the view, parse destination,
    `writer.publish(...)` with `staging_profile=ctx.config.profile` and the transport;
    `PublishRefused` → `Refused(Refusal("kernel-refused", f"publish refused: {outcome}",
    {"kind": "PublishRefused", "outcome": outcome}))`, `PublishUnresolved` likewise with
    `reason`; a `PublicationRefused` exception propagates as the dispatcher's
    `kernel-refused`. Report: the record blocks of the binding and the marker the ledger
    shows (the dispatcher rebuilds it; the handler returns `record_block` for the two
    nodes read back from `ctx.write_view()`).
  - `publish-preview` declaration: `write_class = "read-only"`, inputs `view`, `to`.
    Report: `Heading("Publish preview: <view> → <destination>")`,
    `KeyVals("selection", (("<kind>", "<n>"), …) + (("records", ", ".join(selected)),))`,
    `KeyVals("closure", (("complete", "yes"|"no"), ("missing", ", ".join(missing) or "-")))`,
    `KeyVals("attribution", ((address, f"{origin corpus} {origin marker}"), …))` or
    `Text("attribution: every selected record is this world's own")`,
    `KeyVals("inputs the destination will not carry", ((dataset address,
    f"bytes {'held' if ctx.is_held(node) else 'not held'}; redistribution unknown"), …))`
    over the selected `dataset` records (§4.11: a publication carries records, never bytes;
    redistribution is `unknown` until a dataset declares terms).

- [ ] **Step 1: Write the failing tests**

```python
# python/tests/test_cmd_publish.py — over the fixture world with coordination v3 (Task 11's helpers.commons.build_installation)
def test_preview_lists_selection_closure_and_uncarried_inputs(installation_a):
    text = read_rig(cfg_a, "publish-preview").invoke("publish-preview", {"view": "a", "to": "https://remote.test/a"}).text   # read_rig: helpers.commons (Task 11)
    for line in ("[selection]", "dataset: 1", "assessment: 1", "[closure]", "complete: yes", "[inputs the destination will not carry]"):
        assert line in text
    assert "bytes held; redistribution unknown" in text

def test_preview_of_an_unresolvable_view_refuses(installation_a):
    assert refused(lambda: ...invoke("publish-preview", {"view": "nope", "to": "/tmp/x"})).code == "unknown-project"

def test_publish_to_a_git_remote_mints_binding_and_marker_and_the_remote_lists_them(installation_a, remotes):
    with open_rig(cfg_a, ("publish",)) as (d, ctx):
        text = d.invoke("publish", {"view": "a", "to": "https://remote.test/a"}).text
    assert "[publication-binding]" in text and "[publication]" in text
    corpus_id = marker_fields(marker_in(text)).corpus_id_of_binding(...)  # read the binding's corpus_id
    assert GitTransport(...).listing(Destination.remote("https://remote.test/a"), corpus_id)  # non-empty

def test_publish_without_a_current_epoch_refuses_naming_the_remedy(installation_a_no_epoch):
    refusal = refused(lambda: d.invoke("publish", {...}))
    assert refusal.code == "kernel-refused" and "epoch" in refusal.message

def test_publish_to_a_relative_path_is_invalid_input(installation_a):
    assert refused(lambda: d.invoke("publish", {"view": "a", "to": "relative/dir"})).code == "invalid-input"

def test_publish_retried_after_a_partial_push_converges_and_commits_nothing_new(installation_a, remotes, monkeypatch):
    # §12 transport case: the first attempt's transport raises after its push succeeded; the act's attempt
    # stays unfinished; the retry (same invocation re-run with a new invocation id) converges.
    monkeypatch.setattr(publication, "REMOTE_FOR", remotes.remote_for)
    fault = GitTransport(...); fault.fail_after_push = True
    monkeypatch.setattr(publication, "transport_for", lambda config, dest: fault)
    with pytest.raises(GitTransportFault): d.invoke("publish", {...}, invocation_id="p1")
    fault.fail_after_push = False
    text = d.invoke("publish", {...}, invocation_id="p2").text
    assert commit_count(remotes.bare("a")) == 1 and "[publication]" in text
```

The retry's semantics are the kernel's: a stranded attempt with a transport mark blocks
the pair (`publish-unfinished`) and the kernel's `resume_publish` is the remedy. If the
first test run shows `publish-unfinished` on `p2`, the handler gains `resume` input
handling: `publish --resume <event_token>` calls `writer.resume_publish(event_token=…)`.
Decide from the observed outcome and record it in the task note; both shapes converge on
one remote commit.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_cmd_publish.py -v`
Expected: FAIL — unknown command `publish`.

- [ ] **Step 3: Add the two declarations, prompts, `publication.py` and the handlers**

`prompt.md` for `publish`: when to run it (a project view the person wants shared, after
`science epoch`), that `publish-preview` shows what would be frozen first, and that a
refusal is reported verbatim. For `publish-preview`: run before `publish`, read the four
blocks.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_cmd_publish.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add commands/publish commands/publish-preview python/src/science/commands/publish.py python/src/science/commands/publish_preview.py python/src/science/publication.py python/tests/test_cmd_publish.py
git commit -m "feat(publish): publish a view to a local or git destination, with publish-preview as its dry run"
```

---

### Task 6: `provider-bind`

**Files:**
- Create: `commands/provider-bind/command.toml`, `commands/provider-bind/prompt.md`,
  `python/src/science/commands/provider_bind.py`
- Test: `python/tests/test_cmd_provider_bind.py`

**Interfaces:**
- Consumes (kernel door, names assumed): `ScopedWriter.restore(copy: Path, subject:
  CorpusSubject, observers: ObserverSet, *, evidence: SharingEvidence) -> LogReport`,
  where `SharingEvidence(corpus, marker, artifact, world, source, location, verdict,
  transition)` is what the door ledgers (`verdict` filled by the door from the report);
  `ScopedWriter.record_sharing(evidence)` for a transition with no kernel act (`bound`).
  `beliefs.world.anchors.CorpusSubject`, `beliefs.world.verify.ArtifactCarrier.from_bytes`,
  `ObserverSet`. `GitTransport.fetch_corpus` (Task 3), `SharingRegistry` (Task 2),
  `publication.marker_of/marker_fields/artifact_identity` (Task 5).
- Produces: declaration `write_class = "sharing"`, inputs `location` (string, required),
  `corpus_id` (string, required), `world` (string, optional), `[reads] families =
  ["corpus-stored"]`. Handler:
  1. validate: `corpus_id` 32 hex, `world` 32 hex when given, `location` parses to a
     remote `Destination`; `sharing_root` configured, else `invalid-input` naming the key.
  2. `root, sibling = transport.fetch_corpus(destination, corpus_id, registry.scratch(iid))`
     (`GitTransportFault` → `invalid-input` with its message).
  3. `writer.restore(root, CorpusSubject(corpus_id), ObserverSet((ArtifactCarrier.from_bytes(sibling),)),
     evidence=…transition "inspected"…)`; a report whose `.outcome != "validated"` →
     `invalid-input` naming the outcome; marker read with `marker_of(root)`.
  4. no `world`: delete the scratch; report `(pin_block(line),)` for the `inspected` line
     (its `world` field is the answer the person confirms).
  5. `world` given and `!= marker world` → `world-mismatch` (data: `claimed`, `given`);
     equal → `registry.write_binding(ProviderBinding(world, (location,), now, confirmed=True))`
     merging locations into an existing binding of that world, `writer.record_sharing(…
     transition "bound"…)`, delete scratch, report both pin blocks.

- [ ] **Step 1: Write the failing tests**

```python
def test_bind_without_world_reports_the_claimed_world_and_records_nothing(installations):
    text = rig_b.invoke("provider-bind", {"location": LOC_A, "corpus_id": CID_A}).text
    assert f"[pin] {CID_A} inspected" in text and f"world: {WORLD_A}" in text
    assert SharingRegistry(cfg_b.sharing_root).bindings() == {} and not scratch_left(cfg_b)

def test_bind_with_the_claimed_world_records_a_confirmed_binding(installations):
    text = rig_b.invoke("provider-bind", {"location": LOC_A, "corpus_id": CID_A, "world": WORLD_A}).text
    assert f"[pin] {CID_A} bound" in text
    assert SharingRegistry(cfg_b.sharing_root).binding_for_location(LOC_A) == ProviderBinding(WORLD_A, (LOC_A,), ANY_AT, True)

def test_bind_with_another_world_refuses_world_mismatch(installations):
    refusal = refused(lambda: rig_b.invoke("provider-bind", {..., "world": "f" * 32}))
    assert refusal.code == "world-mismatch" and refusal.data == {"claimed": WORLD_A, "given": "f" * 32}

def test_bind_with_a_malformed_world_refuses_before_fetching(installations, monkeypatch):
    monkeypatch.setattr(GitTransport, "fetch_corpus", lambda *a, **k: pytest.fail("fetched"))
    assert refused(lambda: rig_b.invoke("provider-bind", {..., "world": "not-hex"})).code == "invalid-input"

def test_bind_of_an_absent_corpus_names_the_location(installations):
    refusal = refused(lambda: rig_b.invoke("provider-bind", {"location": LOC_A, "corpus_id": "0" * 32}))
    assert refusal.code == "invalid-input" and LOC_A in refusal.message

def test_bind_without_sharing_root_refuses_naming_the_key(installation_without_sharing):
    assert "sharing_root" in refused(...).message
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_cmd_provider_bind.py -v`
Expected: FAIL — unknown command.

- [ ] **Step 3: Implement the declaration, prompt and handler**

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_cmd_provider_bind.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add commands/provider-bind python/src/science/commands/provider_bind.py python/tests/test_cmd_provider_bind.py
git commit -m "feat(sharing): provider-bind inspects a publication's world and binds a location on confirmation"
```

---

### Task 7: `adopt`

**Files:**
- Create: `commands/adopt/command.toml`, `commands/adopt/prompt.md`,
  `python/src/science/commands/adopt.py`
- Test: `python/tests/test_cmd_adopt.py`

**Interfaces:**
- Consumes: Task 6's door names plus `ScopedWriter.admit_publication(root: Path,
  observers: ObserverSet, *, evidence: SharingEvidence) -> AdmissionRecord` (ledgers
  `admitted`); `beliefs.publication_arrival.require_publication_layout(records)`;
  `ReadView.opened_at(root).iter_stored()`; `ctx.world.registry().admissions` and
  `ctx.world.status(corpus_id)` for reconciliation.
- Produces: declaration `write_class = "sharing"`, inputs `location`, `corpus_id`,
  `[reads] families = ["corpus-stored"]`. Handler, every check before the kernel is
  touched (§10):
  1. validate inputs and `sharing_root` as Task 6 does; refuse `invalid-input` when the
     registry already holds a pin for `corpus_id` in state `admitted` or `mounted`
     ("already adopted") and reconcile first (step 2).
  2. **reconcile** (§10): for every pin in state `fetched` or `admitted` whose corpus the
     kernel registry lists admitted, write it as `mounted` and ledger `mounted`.
  3. fetch into `registry.root_for(corpus_id)` (refuse `invalid-input` if that directory
     already exists with a pin in state `fetched` from an earlier attempt: reuse it instead
     of fetching); `writer.restore(...)` with transition `fetched`; write the pin in state
     `fetched` with `source=None` yet.
  4. **source**: `binding = registry.binding_for_location(location)`; none →
     `pin-unsourced` (message names the world the marker claims and the remedies
     `provider-bind` and `follow`; data `{"world": …}`), pin stays `fetched`;
     `binding.world != marker world` → `world-mismatch`. Else
     `source = PinSource("provider", location)`.
  5. **layout**: `require_publication_layout(records)`; a `PublicationArrivalRefused` →
     `kernel-refused` (the dispatcher's normalization), pin stays `fetched`.
  6. **conflict**: build `held: dict[address, uid]` from the candidate's records; for every
     live root (write root, every configured root, every `mounted` registry root, every pin
     this invocation admitted) compare addresses; any shared address → `adopt-conflict`
     with data `{"addresses": [...], "corpus": <live corpus id>, "reason": "overlap is
     milestone 1b (beliefs-81367e)"}`; the candidate stays `fetched`.
  7. `writer.admit_publication(root, observers, evidence=…"admitted"…)`; write pin
     `admitted`; then write pin `mounted` and `writer.record_sharing(…"mounted"…)`.
  8. report: the pin blocks of this invocation's lines (`fetched`, `admitted`, `mounted`).
     `prompt.md` and the `mounted` block's rendering tell the person the mount takes
     effect at the next session open and that `publish` refuses `selection-incomplete`
     naming the corpus until then (§5 step 3).

- [ ] **Step 1: Write the failing tests**

```python
def test_adopt_unsourced_leaves_the_candidate_fetched_and_names_the_remedies(installations):
    refusal = refused(lambda: rig_b.invoke("adopt", {"location": LOC_A, "corpus_id": CID_A}))
    assert refusal.code == "pin-unsourced" and refusal.data == {"world": WORLD_A}
    assert "provider-bind" in refusal.message and "follow" in refusal.message
    assert SharingRegistry(cfg_b.sharing_root).pin(CID_A).state == "fetched"
    assert not ctx_b.world.status(CID_A).known

def test_adopt_after_bind_admits_and_marks_mounted(installations_bound):
    text = rig_b.invoke("adopt", {"location": LOC_A, "corpus_id": CID_A}).text
    assert [l.split()[2] for l in text.splitlines() if l.startswith("[pin]")] == ["fetched", "admitted", "mounted"]
    pin = SharingRegistry(cfg_b.sharing_root).pin(CID_A)
    assert pin.state == "mounted" and pin.source == PinSource("provider", LOC_A) and pin.fetch.verdict == "validated"
    assert ctx_b.world.status(CID_A).live
    assert "next session open" in text

def test_the_adopted_root_is_a_corpus_root_at_the_next_open(installations_adopted):
    cfg = load_config(write_config_for(cfg_b))      # the loader unions the mounted root
    assert SharingRegistry(cfg_b.sharing_root).root_for(CID_A) in cfg.world.corpus_roots
    assert ReadContext.open(cfg).cited(A_PROPOSITION).corpus_id == CID_A

def test_publish_before_reopen_refuses_selection_incomplete_naming_the_adopted_corpus(installations_adopted):
    refusal = refused(lambda: rig_b_same_session.invoke("publish", {"view": "b", "to": LOC_B}))
    assert refusal.code == "kernel-refused" and CID_A in refusal.message

def test_adopt_a_second_time_refuses_already_adopted(installations_adopted):
    assert refused(lambda: rig_b.invoke("adopt", {...})).code == "invalid-input"

def test_adopt_of_a_conflicting_candidate_refuses_before_admission(installations_bound, conflicting_copy):
    # a second publication of A holding one of B's own addresses (a dataset B also declared)
    refusal = refused(lambda: rig_b.invoke("adopt", {"location": LOC_A, "corpus_id": CID_A2}))
    assert refusal.code == "adopt-conflict" and SHARED_ADDRESS in refusal.data["addresses"]
    assert not ctx_b.world.status(CID_A2).known and SharingRegistry(...).pin(CID_A2).state == "fetched"

def test_adopt_reconciles_a_pin_the_kernel_admitted_but_the_registry_did_not_mark(installations_adopted):
    registry.write_pin(replace(pin, state="admitted"))
    rig_b.invoke("adopt", {"location": LOC_A, "corpus_id": OTHER})   # or any adopt; reconciliation runs first
    assert registry.pin(CID_A).state == "mounted"

def test_adopt_of_an_absent_corpus_writes_nothing(installations_bound):
    refusal = refused(lambda: rig_b.invoke("adopt", {"location": LOC_A, "corpus_id": "0" * 32}))
    assert refusal.code == "invalid-input" and registry.pin("0" * 32) is None and not registry.root_for("0" * 32).exists()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_cmd_adopt.py -v`
Expected: FAIL — unknown command.

- [ ] **Step 3: Implement the declaration, prompt and handler**

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_cmd_adopt.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add commands/adopt python/src/science/commands/adopt.py python/tests/test_cmd_adopt.py
git commit -m "feat(sharing): adopt fetches, verifies, checks source, layout and conflicts, then admits and mounts"
```

---

### Task 8: `fetch`

**Files:**
- Create: `commands/fetch/command.toml`, `commands/fetch/prompt.md`,
  `python/src/science/commands/fetch.py`
- Test: `python/tests/test_cmd_fetch.py`

**Interfaces:**
- Consumes: `ctx.cited(dataset)`, `beliefs.stored.dataset_declaration`,
  `beliefs.dataset.dataset_address`, `beliefs.holdings.boundary.look` and `write`,
  `beliefs.holdings.records.StoreLocator`, `url_locator`, `beliefs.holdings.transport.RetrievalBounds`,
  `url_seam`, `writer.holdings_context(instrument=INSTRUMENT)`, `writer.store_id`,
  `ctx.config.fetch` (Task 1). Pattern: `commands/dataset.py:105-113`.
- Produces: declaration `write_class = "mints:holdings-observation"`, `[write.routes]
  holdings-observation = "holdings"`, inputs `dataset` (string, required), `from`
  declared as input name `source` (string, required: an absolute path on this host or a
  `https://` URL), `[reads] families = ["corpus-stored", "holdings"]`. Handler:
  1. `ctx.config.fetch.policy == "records-only"` → `invalid-input` naming `[fetch] policy`.
  2. `mount = ctx.cited(dataset)`; declaration with exactly one resource (several →
     `invalid-input` naming `sci-d1e874` as where multi-resource staging is decided);
     the resource's `digest` (`sha256:<hex>`) and `name`.
  3. path form: read bytes; `sha256 != declared` → `invalid-input` naming both; size over
     `max_bytes` (when non-zero) → `invalid-input`. URL form: `look(holdings,
     url_locator(source), bounds=RetrievalBounds(max_bytes or default), seam=url_seam(),
     scratch=ctx.config.operations_root / "scratch" / "fetch" / iid, expected=digest)`;
     `InconclusiveLook` → `invalid-input` with `reason` and `report`; read
     `retrieved.path`, unlink after the write.
  4. `write(holdings, StoreLocator(writer.store_id, f"{hex}/{name}"), content, expected=digest)`.
  5. report: `(record_block(published.record_node),)` — the holdings observation minted
     (read back through `ctx.write_view()` by its ref as `dataset.py` does for its node).

- [ ] **Step 1: Write the failing tests**

```python
def test_fetch_from_a_path_holds_the_mounted_dataset_bytes(installations_reopened):   # B with A mounted
    text = rig_b.invoke("fetch", {"dataset": A_DATASET, "source": str(a_bytes_path)}).text
    assert "[holdings-observation]" in text
    assert ReadContext.open(cfg_b).held_path(A_DATASET).read_bytes() == a_bytes_path.read_bytes()

def test_fetch_with_mismatching_bytes_refuses_and_writes_nothing(installations_reopened, tmp_path):
    wrong = tmp_path / "wrong"; wrong.write_bytes(b"not the data\n")
    refusal = refused(lambda: rig_b.invoke("fetch", {"dataset": A_DATASET, "source": str(wrong)}))
    assert refusal.code == "invalid-input" and DECLARED_DIGEST in refusal.message
    assert refused(lambda: ReadContext.open(cfg_b).held_path(A_DATASET)).code == "invalid-input"

def test_fetch_under_records_only_refuses_naming_the_policy(installations_reopened):
    cfg = replace(cfg_b, fetch=FetchPolicy("records-only", 0))
    assert "[fetch] policy" in refused(lambda: rig(cfg).invoke("fetch", {...})).message

def test_fetch_over_max_bytes_refuses(installations_reopened):
    cfg = replace(cfg_b, fetch=FetchPolicy("fetch", 1))
    assert refused(lambda: rig(cfg).invoke("fetch", {...})).code == "invalid-input"

def test_fetch_from_a_url_goes_through_look_then_the_store_write(installations_reopened, monkeypatch):
    seen = {}
    monkeypatch.setattr(fetch_module, "look", lambda ctx, location, **k: seen.update(k) or FakePublishedLook(path_with_bytes))
    rig_b.invoke("fetch", {"dataset": A_DATASET, "source": "https://data.test/a.txt"})
    assert seen["expected"] == DECLARED_DIGEST and ReadContext.open(cfg_b).held_path(A_DATASET).exists()

def test_fetch_of_a_dataset_the_write_root_declares_is_still_a_fetch(installations_reopened):
    # composition from look + write never mints a dataset; the record stays where it was declared
    before = ReadContext.open(cfg_b).cited(A_DATASET).corpus_id
    rig_b.invoke("fetch", {...})
    assert ReadContext.open(cfg_b).cited(A_DATASET).corpus_id == before == CID_A
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_cmd_fetch.py -v`
Expected: FAIL — unknown command.

- [ ] **Step 3: Implement the declaration, prompt and handler**

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_cmd_fetch.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add commands/fetch python/src/science/commands/fetch.py python/tests/test_cmd_fetch.py
git commit -m "feat(fetch): hold a mounted dataset's bytes in the store from a path or URL, never redeclaring it"
```

---

### Task 9: The accept policy in every belief read

**Files:**
- Create: `python/src/science/acceptance.py`
- Modify: `python/src/science/closure.py:38-44`, `python/src/science/config.py:525-546`,
  `python/src/science/commands/belief.py`, `python/src/science/commands/next.py` (gather call)
- Test: `python/tests/test_acceptance.py`, extend `python/tests/test_cmd_belief.py`

**Interfaces:**
- Consumes: `beliefs.belief.AcceptancePolicy(counts, statement)`, `AcceptanceContext`;
  `gather(..., acceptance=)`, `evaluate_over(..., acceptance=)`; `SharingRegistry`
  (Task 2); `publication.marker_of/marker_fields` (Task 5); the write root's
  `publication-binding` records (facet `corpus_id`, `marker`, `artifact`).
- Produces:

```python
@dataclass(frozen=True)
class Carrier:
    corpus_id: str; world: str; marker: str; attributions: Mapping[str, tuple[str, str]]  # address -> (origin corpus, origin marker)

@dataclass(frozen=True)
class AcceptanceInputs:
    own_corpus: str
    verifiers: frozenset[str]                       # own world ∪ config.accept
    pins: Mapping[str, Pin]                         # by corpus id, state "mounted" only
    bindings: Mapping[str, ProviderBinding]
    own_bindings: frozenset[tuple[str, str, str]]   # (corpus_id, marker, artifact) from the write root
    carriers: Mapping[str, Carrier]                 # every session mount other than the write root that holds a marker

def acceptance_inputs(ctx: ReadContext) -> AcceptanceInputs: ...
def counts(inputs: AcceptanceInputs, corpus_id: str, address: str) -> bool: ...
    # §9 item 2, in order: Carried (origin pin origin-confirmed and origin world in verifiers),
    # Own (corpus is the write root, or carrier's (corpus, marker, artifact) in own_bindings),
    # Carrier's own (carrier world in verifiers and its pin origin-confirmed); else False.
    # A corpus with no carrier entry and not the write root (a configured read mount that is not a
    # publication) counts as Own only when it is the write root; otherwise False.
def statement(inputs: AcceptanceInputs) -> str: ...
    # json.dumps(sort_keys=True, separators=(",", ":")) of {"policy": "science.accept.v1", "verifiers": sorted,
    # "pins": [{corpus, world, source, confirmed, state}], "own_bindings": sorted triples,
    # "carriers": [{corpus, world, marker, attributed: n}]}
def policy(ctx: ReadContext) -> AcceptancePolicy: ...
def explain(context: AcceptanceContext, inputs: AcceptanceInputs) -> tuple[tuple[str, str], ...]: ...
    # ("verifiers", ...), ("excluded", f"{address} ({corpus} world {world})") per excluded pair, ("complete", yes|no)
```

  `closure.gather_inputs`/`closure.evaluate` gain `acceptance=None` and forward it;
  `ReadContext.gather_inputs`/`evaluate` pass `acceptance.policy(self)` in both read modes;
  `commands/belief.py` adds `KeyVals("acceptance", explain(answer.acceptance, inputs))`
  when `answer.acceptance is not None`.

- [ ] **Step 1: Write the failing tests**

```python
# unit, over hand-built AcceptanceInputs (no world needed)
def test_own_write_root_records_count_under_an_empty_policy():
    assert counts(INPUTS_EMPTY_ACCEPT, OWN, "assessment:x")

def test_a_carriers_own_record_counts_only_when_its_world_is_accepted_and_the_pin_is_origin_confirmed():
    assert not counts(INPUTS_EMPTY_ACCEPT, CID_A, A_ASSESSMENT)
    assert counts(replace(INPUTS_EMPTY_ACCEPT, verifiers=frozenset({OWN_WORLD, WORLD_A})), CID_A, A_ASSESSMENT)
    assert not counts(replace(..., pins={CID_A: replace(PIN_A, source=PinSource("catalog", "ab" * 32))}), CID_A, A_ASSESSMENT)

def test_a_carried_record_is_attributed_to_its_origin_not_its_carrier():
    # B carries A's dataset; accept = [B] alone never makes A's record count; accept = [A] with A's pin does
    assert not counts(INPUTS_ACCEPT_B, CID_B, A_DATASET)
    assert counts(INPUTS_ACCEPT_A_AND_PIN_A, CID_B, A_DATASET)

def test_own_records_adopted_back_count_through_the_binding():
    assert counts(INPUTS_WITH_OWN_BINDING, CID_OWN_PUB, "assessment:mine")

def test_a_marker_merely_claiming_our_world_never_takes_the_own_branch():
    assert not counts(INPUTS_CLAIMANT, CID_CLAIMANT, "assessment:theirs")

def test_statement_is_canonical_json_and_encodes():
    s = statement(INPUTS_ACCEPT_A); assert s == json.dumps(json.loads(s), sort_keys=True, separators=(",", ":")); v1.encode(s)

def test_accept_naming_an_unpinned_world_changes_nothing(installations_reopened):
    # Review Focus 5
    cfg = replace(cfg_b, accept=("e" * 32,))
    answer = ReadContext.open(cfg).evaluate(A_PROPOSITION)
    assert answer.acceptance is not None and "e" * 32 in answer.acceptance.statement

# command, over the two installations after adoption and reopen (Task 11's fixture)
def test_belief_with_empty_accept_excludes_a_and_says_so(installations_reopened):
    text = read_rig(cfg_b, "belief").invoke("belief", {"proposition": A_PROPOSITION}).text
    assert "[acceptance]" in text and f"{A_ASSESSMENT} ({CID_A} world {WORLD_A})" in text

def test_belief_with_accept_a_includes_a(installations_reopened):
    text = read_rig(replace(cfg_b, accept=(WORLD_A,)), "belief").invoke(...).text
    assert "excluded:" not in text.split("[acceptance]")[1] or "excluded: -" in text
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_acceptance.py -v`
Expected: FAIL with `ModuleNotFoundError: science.acceptance`.

- [ ] **Step 3: Implement `acceptance.py`, thread `acceptance=` through `closure.py`, `config.py`, `belief.py`, `next.py`**

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_acceptance.py tests/test_cmd_belief.py tests/test_cmd_next.py tests/test_belief_path.py -v`
Expected: PASS (existing belief tests unchanged: a world with no mounts and no registry
yields an all-Own policy whose exclusions are empty).

- [ ] **Step 5: Commit**

```bash
git add python/src/science/acceptance.py python/src/science/closure.py python/src/science/config.py python/src/science/commands/belief.py python/src/science/commands/next.py python/tests/test_acceptance.py python/tests/test_cmd_belief.py
git commit -m "feat(belief): compute the accept policy from pins, bindings and carriers; belief explains it"
```

---

### Task 10: `show`

**Files:**
- Create: `commands/show/command.toml`, `commands/show/prompt.md`,
  `python/src/science/commands/show.py`
- Test: `python/tests/test_cmd_show.py`

**Interfaces:**
- Consumes: `SharingRegistry`, `ctx.world.status(corpus_id)`, `acceptance.acceptance_inputs`.
- Produces: declaration `write_class = "read-only"`, input `corpus_id` (string,
  required), `[reads] families = ["corpus-stored"]`. Report:
  `Heading(f"Pin {corpus_id}")`, `KeyVals("pin", (("state", …), ("world", …), ("marker", …),
  ("artifact", …), ("view", …), ("keep", "yes"|"no")))`,
  `KeyVals("source", (("kind", "provider"|"catalog"|"none"), ("reference", …),
  ("confirmation", "origin-confirmed"|"recommended"|"unsourced")))`,
  `KeyVals("fetch", (("location", …), ("at", …), ("verdict", …)))`,
  `KeyVals("kernel", (("known", …), ("live", …), ("present", …)))`,
  `KeyVals("acceptance", (("world accepted", "yes"|"no"), ("counts", "yes"|"no")))`
  where `counts` is `counts(inputs, corpus_id, <the marker's address>)`'s carrier's-own
  answer, and a `Finding` when the kernel shows admitted and the registry does not show
  `mounted` ("registry lags the kernel: `adopt` reconciles it"). No pin → `invalid-input`.

- [ ] **Step 1: Write the failing tests**

```python
def test_show_a_mounted_origin_confirmed_pin(installations_adopted):
    text = read_rig(cfg_b, "show").invoke("show", {"corpus_id": CID_A}).text
    for line in ("state: mounted", f"world: {WORLD_A}", "confirmation: origin-confirmed", "verdict: validated", "live: yes", "world accepted: no"):
        assert line in text

def test_show_says_accepted_under_accept_a(installations_adopted):
    assert "world accepted: yes" in read_rig(replace(cfg_b, accept=(WORLD_A,)), "show").invoke(...).text

def test_show_reports_a_registry_that_lags_the_kernel(installations_adopted):
    registry.write_pin(replace(pin, state="admitted"))
    assert "registry lags the kernel" in read_rig(cfg_b, "show").invoke(...).text

def test_show_of_an_unknown_pin_refuses(installations_adopted):
    assert refused(lambda: ...invoke("show", {"corpus_id": "0" * 32})).code == "invalid-input"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_cmd_show.py -v`
Expected: FAIL — unknown command.

- [ ] **Step 3: Implement the declaration, prompt and handler**

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_cmd_show.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add commands/show python/src/science/commands/show.py python/tests/test_cmd_show.py
git commit -m "feat(sharing): show answers a pin's state, source, fetch record, kernel status and acceptance"
```

---

### Task 11: Two installations over git: the fixture and the milestone's decisive cases

**Files:**
- Create: `python/tests/helpers/commons.py`, `python/tests/test_commons_1a.py`
- Modify: `python/tests/helpers/world.py` (add `PROFILE_V3`, `PINS_V3`, and a
  `coordination=` parameter on `build_fixture_world`-style builders only where
  `commons.py` needs one)

**Interfaces:**
- Consumes: everything above; `helpers.world.hold_fixture_dataset`, `mint_fixture_run`,
  `fixture_bundle`, `open_rig`, `write_config_for`, `mint_project`; `helpers.snapshot.snapshot`;
  `science.world_belief.publish_session_epoch`.
- Produces:

```python
@dataclass(frozen=True)
class Remotes:
    base: Path
    def bare(self, name: str) -> Path: ...                   # <base>/<name>.git, created with `git init --bare -b main`
    def remote_for(self, destination: Destination) -> str: ...   # https://remote.test/<name> -> str(bare(name))

QUERY_1A = "version: science.view-query.v1\nclauses:\n  - all:\n      - kinds: [proposition, dataset, analysis-spec, run, assessment]\n"

def build_installation(work: Path, name: str, *, remotes: Remotes) -> ScienceConfig
    # one world root, one write root pinned to coordination v3 (PROFILE_V3/PINS_V3), a store, an operations
    # root, sharing_root = work/<name>/sharing, accept = (), fetch = FetchPolicy("fetch", 0); a project
    # <name> carrying QUERY_1A.
def build_a_published(work: Path) -> tuple[ScienceConfig, ScienceConfig, Path]
    # A with: dataset (bytes DATA_A), spec on proposition:p1 over it, a run (mint_fixture_run), its assessment;
    # `publish_session_epoch(cfg_a)`; publish view "a" to https://remote.test/a through the rig with
    # publication.REMOTE_FOR patched to remotes.remote_for. B fresh. Returns (cfg_a, cfg_b, remotes.base).
    # Snapshot name "commons-1a-published".
def bind_and_adopt(cfg_b, remotes) -> ScienceConfig   # provider-bind --world, adopt, then load_config(write_config_for(cfg_b)): the reopened B
def a_identity(cfg_a) -> dict[str, str]              # CID_A, WORLD_A, marker uid, A's dataset/spec/run/assessment refs
def read_rig(cfg: ScienceConfig, *names: str) -> Dispatcher
    # a Dispatcher over the named production declarations with ReadContext.open(cfg) and no session:
    # how every read-only command in this plan's tests is invoked (`read_rig(cfg, "belief").invoke(...)`)
def refused(call) -> Refusal                         # pytest.raises(Refused) around `call`, returning `.refusal`
def commit_count(bare: Path) -> int                  # `git rev-list --count main` in a bare repository, 0 when unborn
```

  Fixtures in `test_commons_1a.py`: `installations` (restored snapshot, `REMOTE_FOR`
  patched), `installations_bound`, `installations_adopted`, `installations_reopened`
  (the config the loader built with A's root mounted; `publish_session_epoch(cfg_b)` run
  so B's world read is current). Tasks 5–10's tests import these same fixtures from
  `helpers/commons.py` (a `conftest`-free import, as the other tests do with
  `helpers.world`).

- [ ] **Step 1: Write the failing tests**

```python
def test_a_publishes_a_reproducible_view_and_the_remote_holds_it(installations):
    cfg_a, cfg_b, remotes = installations
    ids = a_identity(cfg_a)
    listing = GitTransport(...).listing(Destination.remote(LOC_A), ids["corpus_id"])
    assert f"{ids['corpus_id']}.head-artifact.v1" in listing and len(listing) >= 6   # marker + 5 selected records

def test_b_reproduces_one_assessment_after_fetching_the_bytes(installations_reopened):
    rig_b.invoke("fetch", {"dataset": ids["dataset"], "source": str(DATA_A_PATH)})
    text = rig_b.invoke("verify", {"assessment": ids["assessment"], "code": str(code), "entrypoint": entrypoint}).text
    assert "[verification]" in text                         # the reproduction lands in B's write root

def test_b_derives_without_redeclaring_and_the_lineage_reaches_as_dataset(installations_reopened):
    spec_b = _minted_ref(rig_b.invoke("spec", dict(WORKING_FIELDS, target=ids["proposition"], dataset=ids["dataset"])).text, "analysis-spec")
    run_b = mint_fixture_run(cfg_b_reopened, spec_b, ids["dataset"], fixture_bundle(work, varying=False))   # one changed input: WORKING_FIELDS.method
    assessment_b = _minted_ref(rig_b.invoke("assess", {"run": run_b}).text, "assessment")
    assert assessment_b != ids["assessment"]                                            # distinct identity
    assert ReadContext.open(cfg_b_reopened).cited(ids["dataset"]).corpus_id == ids["corpus_id"]   # never redeclared
    closure = decode_run_closure(ReadContext.open(cfg_b_reopened).cited(run_b).view.get(run_b))
    assert ids["dataset"] in closure_input_addresses(closure)                            # lineage by identity

def test_bs_marker_attributes_the_carried_records_to_a(installations_derived):
    publish_session_epoch(cfg_b_reopened)
    rig_b.invoke("publish", {"view": "b", "to": LOC_B})
    root, sibling = GitTransport(...).fetch_corpus(Destination.remote(LOC_B), CID_B, tmp)
    fields = marker_fields(marker_of(root))
    assert fields.attributions[ids["dataset"]] == (ids["corpus_id"], ids["marker"])
    assert fields.attributions[ids["proposition"]] == (ids["corpus_id"], ids["marker"])
    assert assessment_b not in fields.attributions                                      # B's own record is unattributed

def test_belief_excludes_a_under_empty_accept_and_includes_it_under_accept_a(installations_derived):
    excluded = read_rig(cfg_b_reopened, "belief").invoke("belief", {"proposition": ids["proposition"]}).text
    assert f"{ids['assessment']} ({ids['corpus_id']} world {ids['world']})" in excluded
    included = read_rig(replace(cfg_b_reopened, accept=(ids["world"],)), "belief").invoke(...).text
    assert ids["assessment"] not in included.split("[acceptance]")[1]
    assert included.split("value:")[1].split()[0] != excluded.split("value:")[1].split()[0] or "NoBelief" in excluded

def test_publish_retried_after_a_partial_push_converges(installations):   # the §12 transport case, end to end over the real git remote
    ...as Task 5's retry test, asserting commit_count(remotes.bare("a")) == 1 after the retry and listing == local_listing...
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_commons_1a.py -v`
Expected: FAIL with `ModuleNotFoundError: helpers.commons`.

- [ ] **Step 3: Implement `helpers/commons.py` and make the tests pass**

Build the snapshot once per worker (`snapshot(certified_worker_work, "commons-1a-published",
build_a_published)`); the bare repositories live under the snapshot's work directory so
`restore()` copies them with it.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_commons_1a.py -v`
Expected: PASS. Then `just test-fast`.

- [ ] **Step 5: Commit**

```bash
git add python/tests/helpers/commons.py python/tests/helpers/world.py python/tests/test_commons_1a.py
git commit -m "test(commons): two installations over git: the 1a walk, lineage and transport cases"
```

---

### Task 12: Surface table, adapters and documents

**Files:**
- Modify: the `ops` checkout's root `cli.toml` (`[cli.science]` rows), then `tools/cli.toml`
  via `python3 bin/vendored adopt cli.toml`; `adapters/claude-code/` via
  `uv run --project python science adapters build`;
  `docs/specs/2026-09-30-science-commons-design.md` (§5 step 5, §11); `README.md`,
  `AGENTS.md` only if `just check` asks.
- Test: `python/tests/test_cli_surface.py`, `python/tests/test_adapters.py`, `just check`.

- [ ] **Step 1: Run the surface and adapter tests to see them fail**

Run: `just test-one tests/test_cli_surface.py tests/test_adapters.py -v`
Expected: FAIL — six command rows missing; adapter tree differs.

- [ ] **Step 2: Add the rows in ops and adopt them here**

Six `[[cli.science.commands]]` rows (`publish`, `publish-preview`, `provider-bind`,
`adopt`, `show`, `fetch`), each with `--config`, `--invocation-id`, `--continue` and one
option per input (`--view`, `--to`; `--location`, `--corpus-id`, `--world`; `--dataset`,
`--source`), `required = true` where the declaration says so. Commit in ops:
`git -C <ops checkout> commit -m "feat(cli): science commons 1a commands" -- cli.toml`
(ops is a `personal` checkout; this is the documented route). Then
`python3 bin/vendored adopt cli.toml` in this worktree.

- [ ] **Step 3: Regenerate the adapters**

Run: `cd python && uv run science adapters build`

- [ ] **Step 4: Amend the documents**

- Commons spec §5 step 5: dated note (2026-10-22) that the dry run is the read-only
  `publish-preview` command, because write reports carry only minted records (framework
  §7.4).
- Commons spec §11: under "Science builds", pointer to this plan and to `beliefs-f24fe9`
  (session doors), `beliefs-6d6bb6` (workspace-locator question filed); note that the
  "assesses edge in a mount" row is answered by the kernel's mount-citations decision 2.
- Commons spec §10 / §12 1a: note that `adopt` refuses any shared address
  (`adopt-conflict`) until `beliefs-81367e` lands, which 1b lifts.

- [ ] **Step 5: Run the gate**

Run: `just test-one tests/test_cli_surface.py tests/test_adapters.py -v && just check && just test-fast`
Expected: PASS, `check` prints nothing.

- [ ] **Step 6: Commit**

```bash
git add tools/cli.toml adapters/claude-code docs/specs/2026-09-30-science-commons-design.md
git commit -m "feat(surface): commons 1a commands in the CLI table and adapters; spec pointers"
```

---

## Self-review

**Spec coverage (§12 part 1a, §5, §7.4, §8, §9, §11).** Publish with dry run: Task 5.
Adopt, show, provider bind: Tasks 7, 10, 6. Fetch as look + store write, never acquire:
Task 8. Git transport with the idempotent retry as a test: Tasks 3, 5, 11. Spec/verify/
run/assess over mounts and belief over a world read: landed by `sci-dc0381`; exercised
over two installations in Task 11. Accept policy: Task 9. Sharing write class and
`sharing_root`: Tasks 4, 1, 2. Decisive cases: lineage (Task 11 tests 3–5), transport
(Tasks 5 and 11). `follow` and `find` are milestone 2 and not built here, as §5 step 1
says ("without any catalog, a user adopts by explicit location"); `pin-unsourced`'s
remedy text still names `follow` as the spec requires. Retirement and supersession are
1b (§10 "a milestone 1b obligation"); 1a's `adopt` refuses overlap outright.

**Kernel gaps surfaced, not papered over.** The permit model and the ledger cannot
express the `sharing` class today, the publish act has no session door, and there is no
public preview; all four are `beliefs-f24fe9`, a recorded dependency of `sci-13050a`.

**Type consistency.** `Pin`, `PinSource`, `ProviderBinding`, `SharingRegistry` (Task 2)
are used by Tasks 1, 6, 7, 9, 10 with the same names; `PinBlock`/`pin_block` (Task 4)
by Tasks 6, 7; `marker_of`/`marker_fields`/`artifact_identity` (Task 5) by Tasks 6, 7, 9,
11; `GitTransport.fetch_corpus` (Task 3) by Tasks 6, 7, 11; `FetchPolicy` (Task 1) by
Task 8. Kernel door names are assumed uniformly across Tasks 4–8 and flagged.

**Review Focus.** Each of the five lines has its test in the owning task (1: Task 1;
2: Task 7; 3: Task 6; 4: Task 8; 5: Task 9).

**Proportion.** Code appears only as signatures, test names with assertions, and
declaration field lists; no handler body is written out.
