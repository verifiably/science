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
`admit_publication` through session doors the kernel adds (`beliefs-f24fe9`), with the
pin as ledger evidence written **before** the registry; a `publishes`-class `publish`
command over a git `Transport`, with a read-only `publish-preview` as its dry run and
`provider-inspect` as the read-only inspection; a `fetch` command over the holdings
transport and the store write; and an `AcceptancePolicy` computed from the registry and
the mounts' markers, handed to every belief read. No science storage beyond the
registry, which is rebuildable from the ledger's sharing lines.

**Tech Stack:** Python 3 stdlib (`argparse`, `json`, `subprocess` for `git`), the
`beliefs` kernel (editable path dependency), pytest with the certified-world fixtures and
`helpers.snapshot`.

**Spec:** `docs/specs/2026-09-30-science-commons-design.md` (§3, §4.4, §4.5, §4.8,
§4.11, §5, §7.4, §8, §9, §10, §11, §12 part 1a). Framework amendments:
`docs/specs/2026-08-31-command-framework-design.md` §3.3, §4.4 (2026-10-01), §9.1
(2026-10-01). Kernel designs consumed: beliefs
`docs/superpowers/specs/2026-09-26-publish-act-remote-design.md` §3.1, §4, §7;
`2026-10-02-belief-acceptance-design.md` §4; `2026-10-02-publication-attribution-design.md`
§4; `2026-10-01-mount-citations-design.md` decision 2.

**Review history:** revision 1 (`ca6d5d8`) reviewed 2026-10-22 by codex/gpt-6-astra
(revise: 7 P1, 4 P2) and claude-code/claude-fable-5-1 (revise: 2 Critical, 8 Important,
13 Minor). This is revision 2; the "Deviations" section records every departure from
the spec's letter with its reason.

## Global Constraints

- Every durable thing is a governed record in a `beliefs` corpus; the sharing registry is
  the one exception the spec makes (§7.4), and every registry write follows the ledger
  line that is its evidence, never precedes it.
- No command calls `pytest` directly: `just test-one <args>` while working,
  `just test-fast` before each commit. Paths given to `test-one` are relative to `python/`.
- A new command is a row in `tools/cli.toml` first (AGENTS.md). The authority is the
  `cli.toml` at the root of the `ops` checkout (`tasks projects --paths` names it): edit
  its `[cli.science]` section there, commit in ops (`git -C <ops checkout> commit -m
  "feat(cli): …" -- cli.toml`; ops is a `personal` checkout and this is its documented
  route), then run `python3 <ops checkout>/bin/vendored adopt cli.toml` **in this
  worktree**. Science has no `bin/`; `tools/cli.toml:6`'s `just vendor-cli` is stale and
  Task 13 corrects it. Every command row repeats `--config`, `--invocation-id`,
  `--continue`, then one option per input, as the existing rows do
  (`tools/cli.toml:985-1266`). **Each command task does this for its own rows**, and
  regenerates `adapters/claude-code` (`cd python && uv run science adapters build`), so
  `test_cli_surface.py` and `test_adapters.py` pass at every commit.
- Command directories are `commands/<name>/` with exactly `command.toml` and `prompt.md`;
  handler module `science.commands.<name with - as _>`, function `handle`; signatures
  `handle(ctx, *, ...)` read-only, `handle(ctx, writer, *, ...)` every write class
  (`loader.resolve_handlers`). Optional inputs default to `None`. Input names avoid
  `schema.RESERVED_INPUTS` = `cursor, invocation_id, view, session, config, project`.
- Refusal codes are the closed set `science/refusal.py:CODES`; this plan adds exactly
  `pin-unsourced`, `world-mismatch`, `adopt-conflict`. Everything else reuses
  `invalid-input` or `kernel-refused`.
- A write handler refuses only before its first act (`dispatch.py:252-262`); a kernel
  outcome that arrives after acts is raised as `beliefs.session.KernelRefusalValue`,
  which the dispatcher closes as `kernel-refused`. A `sharing` invocation may refuse
  after sharing lines (Task 4): sharing lines are not act lines.
- Write reports carry only record blocks this invocation minted
  (`render.audit_write_report`); a `sharing` report carries only pin blocks the ledger's
  sharing lines of this invocation support (Task 4).
- Remote destinations are canonical http(s) URLs (`beliefs.intents.publish.Destination`);
  a git remote is reached through such a URL and git's own configured authentication
  (spec §8: "credentials are git's own"). Tests use `https://remote.test/<name>` mapped to
  a bare repository and an isolated git environment.
- Coordination contract **v3** is required wherever a marker must carry attribution
  entries: both fixture worlds pin v3 (`shipped_coordination(3)`); the shipped fixtures'
  v2 profile is unchanged.
- Hyphenated multi-word commands (`provider-bind`, `provider-inspect`,
  `publish-preview`), as `project-select` is.
- **Kernel dependency.** Tasks 4, 6, 7 and 8 consume the doors `beliefs-f24fe9` adds
  (Task 5's fixture publishes, so Tasks 5–13 depend transitively). Task 9 (`fetch`),
  Task 10 (accept policy) and Task 11 (`show`) need no kernel change. Their Interfaces
  blocks state the names this plan assumes; when that task lands with other names, update
  the Interfaces block and the code together, never the design. A task that reaches a
  door before it exists stops and parks `--reason dependency` naming `beliefs-f24fe9`.
- A subprocess started by a test gets an environment built key by key
  (`helpers.commons.GIT_ENV`), never the inherited one.
- Dates: the plan is written 2026-10-22; documents amended by Task 13 carry that date.

## Deviations

1. **The dry run is a read-only sibling, `publish-preview`.** A write report carries only
   minted record blocks (`render.py:32-39`, framework §7.4), so `publish --dry-run` could
   render nothing. Spec §5 step 5 is amended in Task 13.
2. **Inspection is a read-only sibling, `provider-inspect`.** Spec §4.4 layer 3's
   no-`--world` form "records nothing": it needs no door and no grant
   (`beliefs.root.evaluate_copy` is `restore_root`'s evaluation granting nothing), so it
   is not a `sharing`-class invocation, whose every line must have a registry counterpart.
   `provider-bind` requires `--world`.
3. **`adopt` refuses any shared address (`adopt-conflict`).** The kernel's world index
   raises `duplicate-location` for one address in two corpora whatever the content
   (`beliefs/world/derive.py:434-443`), so an overlapping admission would break *B*'s
   next epoch. `beliefs-81367e` (1b) lifts it. Spec §10/§12 note in Task 13.
4. **`fetch --from <url>` retrieves through `beliefs.holdings.transport.retrieve`, not
   `look`.** `look` mints a URL observation before the digest can be compared, and the
   kernel records `expected` without enforcing it (`holdings/records.py:303-331`); a
   mismatch found after that act could not be refused under the write contract. 1a
   therefore uses look's retrieval step directly, compares, then writes the store
   observation. The URL observation record is deferred: Task 13 files the follow-up and
   amends spec §5 step 4.
5. **`bound` joins the sharing transitions.** Framework §4.4 names `fetched, admitted,
   mounted, retired`; a provider binding is registry state with no kernel counterpart, so
   its ledger evidence is a `bound` line whose registry counterpart is the binding. Task 13
   amends framework §4.4.
6. **Configured read mounts that are not publications count as Own.** Spec §9 names only
   the write root under Own; a root the operator lists by hand in `corpus_roots` is the
   installation's own corpus, learned from no location. Without this rule every existing
   multi-corpus belief read would change (`test_mount_citations.py:171-182`). Task 13
   adds the sentence to spec §9.
7. **`show` reports, `adopt` reconciles.** Spec §10 says the registry is reconciled "at
   the next `adopt` or `show`"; `show` is read-only and reports the discrepancy as a
   Finding.
8. **Independence is not shown in 1a.** `EvaluationInputs` (`beliefs/evaluation.py:111`)
   exposes assessments, runs and verifications after the policy filter but no
   independence certification; `show` reports the verification picture and says
   independence is not exposed. Spec §5 step 2 note in Task 13.

## Review Focus

Inputs the spec implies but no task's tests exercise directly, most likely to bite first;
each line's test is in the owning task.

1. **A `sharing_root` whose registry names a mounted root that no longer exists on disk**:
   the loader refuses `invalid-input` naming the pin. Task 2.
2. **`adopt` of a corpus id the remote does not hold, or a location that is not a git
   repository**: `invalid-input` naming the location, nothing written, no scratch left.
   Task 8.
3. **`provider-bind --world` with a malformed id, or the reader's own world id**:
   `invalid-input` before any fetch. Task 7.
4. **`fetch` whose bytes do not match the declared digest, from a path or a URL**:
   `invalid-input` naming both digests, nothing written to the store. Task 9.
5. **A session opened with `accept` naming a world no pin confirms**: belief answers, the
   context carries the policy, nothing extra is excluded. Task 10.

---

## File structure

- Create `python/src/science/sharing.py` — registry types, the on-disk registry, and
  `replay` from ledger lines (Task 1).
- Modify `python/src/science/config.py` — three configuration keys, `ScienceConfig`
  fields, union of mounted roots (Task 2); `ReadContext.evaluate`/`gather_inputs` pass the
  acceptance policy (Task 10).
- Create `python/src/science/transport_git.py` — the git `Transport` plus `fetch_corpus`
  (Task 3).
- Modify `python/src/science/schema.py`, `dispatch.py`, `render.py`, `report.py`,
  `refusal.py` — the `sharing` write class, its invocation path, `PinBlock`, three
  refusal codes (Task 4).
- Create `python/tests/helpers/commons.py` — the two-installation fixture and shared test
  helpers (Task 5, extended by Tasks 6–8).
- Create `python/src/science/publication.py` — shared reads: a corpus's marker, artifact
  identity, destination parsing, transport construction (Task 6).
- Create `commands/publish/`, `commands/publish-preview/`, `commands/provider-inspect/`,
  `commands/provider-bind/`, `commands/adopt/`, `commands/fetch/`, `commands/show/` and
  their handler modules (Tasks 6–9, 11).
- Create `python/src/science/acceptance.py` (Task 10); modify `closure.py`,
  `commands/belief.py`, `commands/next.py`.
- Create `python/tests/test_commons_1a.py` (Task 12).
- Modify documents (Task 13).

---

### Task 1: The sharing registry

**Files:**
- Create: `python/src/science/sharing.py`
- Test: `python/tests/test_sharing_registry.py`

**Interfaces:**
- Consumes: `beliefs.session.open_ledger_reader(operations_root, session_id)` and the
  assumed `LedgerReader.invocation(iid).sharing` / `InvocationRecord.sharing:
  tuple[SharingLine, ...]` (kernel, `beliefs-f24fe9`), where
  `SharingLine(invocation, corpus, marker, artifact, world, view, source, location,
  verdict, transition, at)` and `transition ∈ {"bound", "fetched", "admitted", "mounted",
  "retired"}`; `source` is `"provider:<location>"`, `"catalog:<artifact>"` or `""`.
- Produces:

```python
@dataclass(frozen=True)
class PinSource:            # §4.4 layer 4
    kind: Literal["provider", "catalog"]
    reference: str          # the bound location URL, or the catalog artifact identity
    @classmethod
    def parse(cls, text: str) -> "PinSource | None": ...   # "" -> None
    def render(self) -> str: ...                           # "provider:<ref>"

@dataclass(frozen=True)
class FetchRecord:          # §4.5
    location: str; at: str; verdict: str                   # verdict: restore's LogReport.outcome

@dataclass(frozen=True)
class Pin:
    corpus_id: str; marker: str; artifact: str; world: str; view: str
    source: PinSource | None
    fetch: FetchRecord
    state: Literal["fetched", "admitted", "mounted", "retired"]
    keep: bool = False
    def origin_confirmed(self, bindings: Mapping[str, "ProviderBinding"]) -> bool: ...
        # source.kind == "provider" and bindings.get(world) is confirmed and source.reference in its locations

STATE_ORDER = ("fetched", "admitted", "mounted", "retired")

@dataclass(frozen=True)
class ProviderBinding:      # §4.4 layer 3, §7.3
    world: str; locations: tuple[str, ...]; bound_since: str; confirmed: bool; via: tuple[str, ...] = ()

class SharingRegistryMalformed(Exception):
    entry: str; reason: str

class SharingRegistry:
    def __init__(self, root: Path) -> None: ...
    def pins(self) -> tuple[Pin, ...]: ...                    # sorted by corpus_id
    def pin(self, corpus_id: str) -> Pin | None: ...
    def write_pin(self, pin: Pin) -> None: ...                # atomic: temp file, fsync, os.replace
    def bindings(self) -> dict[str, ProviderBinding]: ...     # keyed by world
    def binding_for_location(self, location: str) -> ProviderBinding | None: ...
    def write_binding(self, binding: ProviderBinding) -> None: ...   # merges locations into an existing world's binding
    def root_for(self, corpus_id: str) -> Path: ...           # <root>/roots/<corpus_id>
    def scratch(self, token: str) -> Path: ...                # <root>/scratch/<token>
    def mounted_roots(self) -> tuple[Path, ...]: ...          # root_for of every "mounted" pin

def apply_line(registry: SharingRegistry, line: SharingLine) -> bool: ...
    # idempotent: "bound" ensures the binding (world, location, confirmed=True, bound_since=line.at);
    # "fetched" ensures a pin (state fetched, source parsed, fetch from the line) when none exists;
    # "admitted"/"mounted"/"retired" raise the pin's state to the line's when lower (STATE_ORDER);
    # returns True when it wrote.
def replay(registry: SharingRegistry, operations_root: Path) -> tuple[SharingLine, ...]: ...
    # every sharing line of every session ledger under <operations_root>/sessions, in (session dir name,
    # ledger order), applied through apply_line; returns the lines that wrote. The registry is rebuildable
    # from the ledger (spec §7.4), and every sharing command calls this first (Tasks 7, 8).
```

  Layout: `pins/<corpus_id>.json`, `providers/<world>.json`, both JSON with sorted keys and
  `"version": 1`; `follows/` reserved; `roots/<corpus_id>/`; `scratch/<token>/`. A file
  that fails to parse or validate raises `SharingRegistryMalformed("pins/<name>", reason)`.

- [ ] **Step 1: Write the failing tests**

```python
def test_pin_round_trips_and_sorts(tmp_path): ...                      # write B then A; pins() == (A, B)
def test_mounted_roots_are_exactly_the_mounted_pins(tmp_path): ...
def test_binding_for_location_matches_a_bound_location_only(tmp_path): ...
def test_write_binding_merges_locations_for_one_world(tmp_path):
    registry.write_binding(ProviderBinding(W, (L1,), AT, True)); registry.write_binding(ProviderBinding(W, (L2,), AT, True))
    assert registry.bindings()[W].locations == (L1, L2)
def test_origin_confirmed_needs_a_confirmed_binding_to_the_markers_world(tmp_path): ...  # four cases as before
@pytest.mark.parametrize("damage", ["{", '{"version": 1, "corpus_id": "short"}', '{"version": 2}'])
def test_malformed_pin_names_its_file(tmp_path, damage): ...
def test_write_is_atomic_and_leaves_no_temp_file(tmp_path): ...
def test_apply_line_is_idempotent_and_never_lowers_a_state(tmp_path):
    assert apply_line(registry, LINE_FETCHED) and not apply_line(registry, LINE_FETCHED)
    assert apply_line(registry, LINE_MOUNTED) and registry.pin(CID).state == "mounted"
    assert not apply_line(registry, LINE_ADMITTED) and registry.pin(CID).state == "mounted"
def test_replay_applies_every_sessions_lines_in_order(tmp_path, fake_ledgers):
    # fake_ledgers: two session directories whose ledgers (written through the kernel's LedgerWriter) hold
    # a bound line and a fetched+admitted+mounted sequence
    written = replay(registry, operations_root)
    assert [l.transition for l in written] == ["bound", "fetched", "admitted", "mounted"]
    assert registry.bindings()[W].locations == (L1,) and registry.pin(CID).state == "mounted"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_sharing_registry.py -v`
Expected: FAIL with `ModuleNotFoundError: science.sharing`.

- [ ] **Step 3: Implement `science/sharing.py` per the Interfaces block**

If `LedgerReader` does not yet expose sharing lines, implement `apply_line` and the
registry now and leave `replay` raising `NotImplementedError` naming `beliefs-f24fe9`;
mark the replay test `xfail(strict=True)` with that reason and remove the mark in Task 4.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_sharing_registry.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/sharing.py python/tests/test_sharing_registry.py
git commit -m "feat(sharing): the sharing registry: pins, provider bindings, adopted roots, ledger replay"
```

---

### Task 2: Configuration keys and mounts derived from the sharing registry

**Files:**
- Modify: `python/src/science/config.py:31-56`, `python/src/science/config.py:78-190`
- Create: `python/tests/helpers/commons.py` (first two helpers), `python/tests/test_config_sharing.py`

**Interfaces:**
- Consumes: `SharingRegistry` (Task 1); `tests/test_config.py::write_config(…, extra=…)`.
- Produces: `ScienceConfig.sharing_root: Path | None = None`,
  `ScienceConfig.accept: tuple[str, ...] = ()`,
  `ScienceConfig.fetch: FetchPolicy = FetchPolicy("records-only", 0)` with
  `@dataclass(frozen=True) class FetchPolicy: policy: Literal["records-only", "fetch"];
  max_bytes: int`. `load_config` unions `SharingRegistry(sharing_root).mounted_roots()`
  into `WorldConfig.corpus_roots` (deduplicated by resolved path, sorted) before building
  `WorldConfig`; `write_root`/`read_contracts` validation runs over the union.
  `helpers/commons.py` starts with `write_minimal_config(work, **overrides) -> Path`
  (wraps `write_config` with `extra` for `accept`, `fetch`, `sharing_root`) and
  `refused(call) -> Refusal` (`pytest.raises(Refused)` returning `.refusal`).

- [ ] **Step 1: Write the failing tests**

```python
def test_sharing_keys_load_with_defaults(tmp_path): ...
def test_accept_must_be_world_ids(tmp_path): ...                      # "abc" -> invalid-input naming accept
def test_fetch_table_validates_policy_and_bound(tmp_path): ...        # {"policy": "maybe"}, max_bytes -1, extra key
def test_mounted_registry_roots_join_corpus_roots(tmp_path, certified_work): ...
def test_a_fetched_pin_is_not_mounted(tmp_path, certified_work): ...  # state "fetched" root absent from corpus_roots
def test_a_mounted_root_missing_on_disk_refuses_naming_the_pin(tmp_path): ...   # Review Focus 1
def test_a_malformed_registry_refuses_naming_the_entry(tmp_path): ...  # "pins/x.json" in message
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_config_sharing.py -v`
Expected: FAIL — unknown config keys refused / `FetchPolicy` not defined.

- [ ] **Step 3: Implement the keys**

`_OPTIONAL_KEYS` gains `sharing_root`, `accept`, `fetch`; `accept` is a list of
32-lowercase-hex strings; `fetch` a table with exactly `policy` (required) and optional
`max_bytes` (int ≥ 0); `sharing_root` resolved with `located()`; `SharingRegistryMalformed`
→ `invalid-input` naming entry and reason; a mounted root without `corpus.yaml` →
`invalid-input` naming the pin's corpus id and path.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_config_sharing.py tests/test_config.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/config.py python/tests/helpers/commons.py python/tests/test_config_sharing.py
git commit -m "feat(config): sharing_root, accept and fetch keys; mounts union the registry's mounted roots"
```

---

### Task 3: The git transport

**Files:**
- Create: `python/src/science/transport_git.py`
- Modify: `python/tests/helpers/commons.py` (`GIT_ENV`, `commit_count`, `Remotes`)
- Test: `python/tests/test_transport_git.py`

**Interfaces:**
- Consumes: `beliefs.transport.Transport`, `TransportAbandoned`, `transport_files`,
  `local_listing`; `beliefs.intents.publish.Destination`.
- Produces:

```python
GIT_PASSTHROUGH = ("PATH", "HOME", "USER", "LANG", "LC_ALL", "SSH_AUTH_SOCK", "XDG_CONFIG_HOME", "XDG_CACHE_HOME")
def production_git_env(author: str) -> dict[str, str]: ...
    # the GIT_PASSTHROUGH keys present in os.environ, every os.environ key starting with "GIT_", plus
    # GIT_TERMINAL_PROMPT="0" and GIT_AUTHOR_NAME/EMAIL, GIT_COMMITTER_NAME/EMAIL derived from `author`
    # (name = author, email = "<author>@science.invalid"): git's own credential helpers and config stay
    # reachable (spec §8), and a missing credential fails instead of prompting.
def identity_remote(destination: Destination) -> str: ...        # the locator itself
class GitTransportFault(Exception): ...                           # transient: the act or handler sees it
class GitTransport:
    def __init__(self, cache: Path, *, author: str, remote_for: Callable[[Destination], str] = identity_remote,
                 env: Mapping[str, str] | None = None, git: str = "git", branch: str = "main") -> None: ...
        # env None -> production_git_env(author); tests pass helpers.commons.GIT_ENV
    fail_after_files: int | None = None   # test seam: raise GitTransportFault after copying this many files, before commit
    fail_after_push: bool = False         # test seam: raise GitTransportFault after a successful push, before returning
    def push(self, destination: Destination, files: Mapping[str, Path]) -> TransportAbandoned | None: ...
    def listing(self, destination: Destination, corpus_id: str) -> dict[str, str]: ...
    def fetch_corpus(self, destination: Destination, corpus_id: str, into: Path) -> tuple[Path, bytes]: ...
```

  `push`: local clone at `cache/<sha256(locator)[:16]>` (clone; or `git init -b <branch>`
  + `git remote add origin <remote>` when the remote has no branch yet; `git fetch origin`
  and `git reset --hard origin/<branch>` when it has one); copy each named file to its
  name; `git add -A -- <names>`; `git diff --cached --quiet` exit 0 → return `None`
  (nothing to commit); else commit `publish <corpus_id>` and `git push origin
  HEAD:refs/heads/<branch>`; a rejected push is retried once after a fetch and reset (a
  concurrent commit does not touch these names); a second failure raises
  `GitTransportFault`. The container is never pruned. `listing`: fetch, `git ls-tree -r
  --name-only origin/<branch>` filtered to the corpus namespace, each blob via `git
  cat-file blob` hashed sha256. `fetch_corpus`: copy the tree's `<corpus_id>/` into
  `into/<corpus_id>`, return the sibling's bytes; an unreachable remote or absent corpus
  raises `GitTransportFault` naming the locator.
  `helpers/commons.py`: `GIT_ENV = {"PATH": os.environ["PATH"], "HOME": <per-process tmp>,
  "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
  GIT_AUTHOR_*/GIT_COMMITTER_* = "test"/"test@science.invalid"}`;
  `commit_count(bare) -> int` (`git rev-list --count main`, 0 when unborn);
  `Remotes(base)` with `bare(name)` (creates `<base>/<name>.git` with `git init --bare -b
  main` under `GIT_ENV` on first use) and `remote_for(destination)` mapping
  `https://remote.test/<name>` to `str(bare(name))`.

- [ ] **Step 1: Write the failing tests**

```python
def test_push_then_listing_equals_local_listing(...)
def test_a_second_push_of_present_files_commits_nothing(...)             # commit_count == 1
def test_push_failing_after_push_converges_on_retry(...)                 # fault, then commit_count == 1, listing == local
def test_push_failing_before_commit_leaves_the_remote_untouched(...)     # listing == {}, commit_count == 0
def test_listing_sees_an_extra_file_the_act_did_not_ask_for(...)
def test_fetch_corpus_materializes_the_root_and_sibling(...)
def test_fetch_corpus_of_an_absent_corpus_names_the_location(...)
def test_production_env_keeps_gits_own_configuration_and_never_prompts(monkeypatch):
    monkeypatch.setenv("GIT_SSH_COMMAND", "ssh -i key"); monkeypatch.setenv("SECRET_TOKEN", "x"); monkeypatch.setenv("SSH_AUTH_SOCK", "/s")
    env = production_git_env("science abc")
    assert env["GIT_SSH_COMMAND"] == "ssh -i key" and env["SSH_AUTH_SOCK"] == "/s" and env["GIT_TERMINAL_PROMPT"] == "0"
    assert "SECRET_TOKEN" not in env and "GIT_CONFIG_GLOBAL" not in env and env["GIT_AUTHOR_NAME"] == "science abc"
def test_test_env_isolates_git_from_the_host(tmp_path, remote):
    captured = {}; monkeypatch.setattr(transport_git.subprocess, "run", capture(captured))
    GitTransport(tmp_path / "c", author="t", env=GIT_ENV).listing(dest, CID)
    assert captured["env"]["GIT_CONFIG_GLOBAL"] == "/dev/null" and captured["env"]["GIT_CONFIG_NOSYSTEM"] == "1"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_transport_git.py -v`
Expected: FAIL with `ModuleNotFoundError: science.transport_git`.

- [ ] **Step 3: Implement `science/transport_git.py` and the helpers per the Interfaces block**

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_transport_git.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/transport_git.py python/tests/helpers/commons.py python/tests/test_transport_git.py
git commit -m "feat(transport): git transport: idempotent push, remote listing, corpus fetch, git's own auth"
```

---

### Task 4: The `sharing` write class, its invocation path and pin blocks

**Files:**
- Modify: `python/src/science/schema.py:17,136-161`; `python/src/science/dispatch.py:171-184,228-292,408-440`;
  `python/src/science/report.py`; `python/src/science/render.py:32-50`; `python/src/science/refusal.py:9-14`;
  `python/src/science/sharing.py` (`replay`, if deferred in Task 1)
- Create: `python/tests/fixtures/commands/share-probe/command.toml`
- Test: `python/tests/test_dispatch_sharing.py`, extend `python/tests/test_schema.py`, `python/tests/test_report.py`

**Interfaces:**
- Consumes (kernel, `beliefs-f24fe9`; names assumed): `RequiredCapabilities.sharing()`;
  `ScopedWriter.record_sharing(evidence: SharingEvidence) -> SharingLine` (a line with no
  kernel act: `bound`, `mounted`); `WriterSession.invocation_sharing(iid) ->
  tuple[SharingLine, ...]`; `LedgerReader.invocation(iid).sharing`.
  `SharingEvidence(corpus, marker, artifact, world, view, source, location, verdict,
  transition)`.
- Produces:
  - `WRITE_CLASS_KINDS` gains `"sharing"`; `_parse_write_class` accepts the bare word.
  - `Dispatcher._required` maps `sharing` to `RequiredCapabilities.sharing()`.
  - `Dispatcher._invoke_sharing(decl, canonical, iid)`: claim, scoped writer, handler
    `(ctx, writer, **inputs)`; a `Refused` from the handler closes
    `{"refusal": envelope}` **whether or not sharing lines were written** (sharing lines
    are evidence of state the handler left behind by design, spec §10: "a refusal at this
    stage leaves the candidate fetched"); `invocation_acts(iid)` must be empty, else
    `HandlerContractViolation`. On success: `lines = session.invocation_sharing(iid)`,
    `audit_sharing_report(report, lines)` (every block is a `PinBlock` equal to
    `pin_block(line)` for a line of this invocation, in order), close `{"done": []}`,
    render `self._pin_report(lines)`. `_continue_write` and `_replay_outcome` branch on
    the class as they do for `session`, rebuilding from `record.sharing`.
  - `report.PinBlock(corpus_id, marker, artifact, world, view, source, location, verdict,
    transition)`, `pin_block(line)`; `serialize_block` renders `[pin] <corpus_id>
    <transition>` then `key: value` lines; a `mounted` block ends with the line
    `takes effect at the next session open`.
  - `refusal.CODES` gains `pin-unsourced`, `world-mismatch`, `adopt-conflict`.
  - `share-probe` fixture: `write_class = "sharing"`, input `corpus_id`; its test handler
    calls `writer.record_sharing(SharingEvidence(…transition "bound"…))` and returns
    `(pin_block(line),)` — a line the door records with no copy to restore.

- [ ] **Step 1: Write the failing tests**

```python
def test_sharing_is_a_write_class(...)
def test_required_for_sharing_is_the_kernel_sharing_requirement(...)
def test_a_sharing_invocation_reports_exactly_its_ledgered_lines(certified_work): ...   # "[pin] <cid> bound"
def test_a_block_the_ledger_does_not_show_is_an_audit_violation(...)
def test_a_refusal_after_a_sharing_line_closes_refused_and_keeps_the_line(certified_work):
    # probe handler records "bound" then raises Refused("world-mismatch")
    refusal = refused(lambda: d.invoke("share-probe", {...}, invocation_id="r1"))
    assert refusal.code == "world-mismatch"
    assert [l.transition for l in open_ledger_reader(ops, session_id).invocation("r1").sharing] == ["bound"]
def test_replay_of_a_sharing_invocation_re_renders_from_the_ledger(...)
def test_new_refusal_codes_construct(...)
def test_sharing_replay_reads_the_lines_the_door_wrote(certified_work):   # Task 1's deferred replay, now live
    ...after the probe ran, sharing.replay(SharingRegistry(tmp), cfg.operations_root) writes the binding...
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_dispatch_sharing.py tests/test_schema.py -v`
Expected: FAIL. If `RequiredCapabilities.sharing` is absent on `beliefs` main, park
`--reason dependency` naming `beliefs-f24fe9`.

- [ ] **Step 3: Implement per the Interfaces block; remove Task 1's xfail**

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_dispatch_sharing.py tests/test_schema.py tests/test_report.py tests/test_dispatch.py tests/test_sharing_registry.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/src/science/schema.py python/src/science/dispatch.py python/src/science/report.py python/src/science/render.py python/src/science/refusal.py python/src/science/sharing.py python/tests/test_dispatch_sharing.py python/tests/fixtures/commands/share-probe python/tests/test_sharing_registry.py
git commit -m "feat(framework): the sharing write class, its ledger-rebuilt pin report, three refusal codes"
```

---

### Task 5: Two installations: the fixture

**Files:**
- Modify: `python/tests/helpers/commons.py`, `python/tests/helpers/world.py` (`PROFILE_V3`, `PINS_V3`)
- Test: `python/tests/test_commons_fixture.py`

**Interfaces:**
- Consumes: `helpers.world.hold_fixture_dataset`, `mint_fixture_run`, `fixture_bundle`,
  `open_rig`, `mint_project`, `init_*`/`open_corpus`/`open_world` as `build_fixture_world`
  uses them; `helpers.snapshot.snapshot`; `science.world_belief.publish_session_epoch`.
- Produces:

```python
QUERY_1A = "version: science.view-query.v1\nclauses:\n  - all:\n      - kinds: [proposition, dataset, analysis-spec, run, assessment]\n"
DATA_A = b"gene\tvalue\nPHF19\t1\n"
LOC_A, LOC_B = "https://remote.test/a", "https://remote.test/b"

@dataclass(frozen=True)
class Installations:
    a: ScienceConfig; b: ScienceConfig; remotes: Path          # snapshot-storable: ScienceConfig, ScienceConfig, Path
    def data_a_path(self) -> Path: ...                          # <remotes parent>/data/a.txt holding DATA_A

def build_installation(work: Path, name: str) -> ScienceConfig
    # world root work/<name>/world, write root work/<name>/corpus pinned to PROFILE_V3/PINS_V3 (coordination v3,
    # domains biology), store work/<name>/store, operations work/<name>/ops, sharing_root work/<name>/sharing,
    # accept=(), fetch=FetchPolicy("fetch", 0); the holdings reducer installed; a project <name> carrying QUERY_1A.
def build_fresh(work: Path) -> Installations
    # A with evidence: dataset (DATA_A), spec on proposition:p1 over it (SPEC_FIELDS), run (mint_fixture_run),
    # assessment; publish_session_epoch(a). B empty. Remotes under work/remotes. Snapshot "commons-1a-fresh".
def write_commons_config(cfg: ScienceConfig) -> Path
    # the launcher TOML with every key, including corpus_roots (all configured roots), write_root,
    # sharing_root, accept and [fetch]; unlike helpers.world.write_config_for.
def reopen(cfg: ScienceConfig) -> ScienceConfig          # load_config(write_commons_config(cfg)): what the loader builds
def read_rig(cfg: ScienceConfig, *names: str) -> Dispatcher   # production declarations named, ReadContext.open(cfg), no session
def a_identity(a: ScienceConfig) -> dict[str, str]       # proposition, dataset, spec, run, assessment refs; world id
def with_remotes(installations: Installations):          # context manager: sets publication.REMOTE_FOR to Remotes(...).remote_for
                                                         # and the transport env to GIT_ENV, restoring both on exit (no monkeypatch)
```

- [ ] **Step 1: Write the failing tests**

```python
def test_both_installations_pin_coordination_v3(fresh):
    for cfg in (fresh.a, fresh.b):
        assert load_manifest(cfg.write_root).profile.domains["coordination"] == V3_PIN
def test_a_holds_the_reproducible_evidence_and_a_current_epoch(fresh):
    ids = a_identity(fresh.a); ctx = ReadContext.open(fresh.a)
    for ref in ids.values(): assert ctx.cited(ref) if ref.startswith(("proposition", "dataset", "analysis-spec", "run", "assessment")) else True
    assert ctx.held_path(ids["dataset"]).read_bytes() == DATA_A
    epoch_currency(ctx.world, ctx.session_ids())
def test_b_is_empty_with_fetch_policy_and_a_sharing_root(fresh):
    assert fresh.b.fetch == FetchPolicy("fetch", 0) and fresh.b.sharing_root.is_dir() is False  # created on first write
def test_reopen_round_trips_the_sharing_keys(fresh):
    cfg = reopen(fresh.b); assert cfg.sharing_root == fresh.b.sharing_root and cfg.fetch == fresh.b.fetch
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_commons_fixture.py -v`
Expected: FAIL — names missing from `helpers.commons`.

- [ ] **Step 3: Implement the fixture per the Interfaces block**

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_commons_fixture.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/tests/helpers/commons.py python/tests/helpers/world.py python/tests/test_commons_fixture.py
git commit -m "test(commons): two installations pinned to coordination v3, A with reproducible evidence"
```

---

### Task 6: `publish` and `publish-preview`

**Files:**
- Create: `commands/publish/`, `commands/publish-preview/`, `python/src/science/commands/publish.py`,
  `python/src/science/commands/publish_preview.py`, `python/src/science/publication.py`
- Modify: ops `cli.toml` → `tools/cli.toml`; `adapters/claude-code/`; `python/tests/helpers/commons.py` (`build_published`)
- Test: `python/tests/test_cmd_publish.py`

**Interfaces:**
- Consumes (kernel, `beliefs-f24fe9`; names assumed):
  `ScopedWriter.publish(*, view: CoordinationAddress, destination: Destination,
  operations_root: Path, staging_profile: ProfileSpec, transport: Transport | None)
  -> Published | PublishRefused | PublishUnresolved`;
  `ScopedWriter.resume_publish(*, event_token: str, operations_root, staging_profile,
  transport)`; both ledger the write-root records (binding, act report) as act lines and
  nothing from the publication corpus; `beliefs.publish.publication_preview(world,
  resolver, view, *, own_profile) -> PublicationPreview(view, selected, closure_missing,
  pins, attributions, contributing)`. Existing: `science.coordination.resolve_project_ref`,
  `beliefs.publish.pending_publishes`, `beliefs.session.KernelRefusalValue`.
- Produces:
  - `science/publication.py`: `parse_destination(text) -> Destination` (absolute path →
    local; `https://…` → remote; else `invalid-input`); module seams `REMOTE_FOR =
    identity_remote` and `GIT_ENV: Mapping | None = None`;
    `transport_for(config, destination) -> Transport | None` (`None` for local;
    `GitTransport(config.operations_root / "transport", author=f"science {config.world.world_id}",
    remote_for=REMOTE_FOR, env=GIT_ENV)` for remote); `marker_of(root) -> Node`;
    `marker_fields(node) -> MarkerFields(uid, world, view, selection: frozenset[str],
    attributions: dict[str, tuple[str, str]], supersedes)`; `artifact_identity(sibling) -> str`;
    `binding_fields(node) -> BindingFields(corpus_id, marker, artifact, destination)`.
  - `publish` declaration: `write_class = "publishes"`, inputs `target` (string, required:
    a project name or `coord:` address, as `project-select` names it), `to` (string,
    required), `resume` (string, optional: an event token), `[reads] families =
    ["coordination", "corpus-stored"]`. Handler: `resume` given → `writer.resume_publish(…)`;
    else resolve `target`, parse `to`, `writer.publish(… staging_profile=ctx.config.profile …)`.
    A `GitTransportFault` is caught and raised as `KernelRefusalValue(TransportFault(reason=
    "transport-fault", detail=str(fault)))` (a frozen value with `.reason` and `.detail`;
    the kernel's attempt stays unfinished with its mark); `PublishRefused` →
    `KernelRefusalValue(PublishRefusedValue(reason=outcome, detail=event_token))`;
    `PublishUnresolved` likewise with `reason`. Report: `(record_block(binding),)` read
    from `ctx.write_view()` at `binding_address(view, destination)`; the marker uid and
    corpus id are the binding's fields. **Limitation stated in `prompt.md`:** the kernel
    resumes an attempt only under its intent's actor (`publish.py:852`), so `--resume`
    works within the service session that began the attempt; a later session finds the
    pair blocked `publish-unfinished` (question raised on `beliefs-f24fe9`).
  - `publish-preview` declaration: `write_class = "read-only"`, inputs `target`, `to`.
    Report: `Heading`, `KeyVals("selection", per-kind counts + records)`,
    `KeyVals("closure", complete, missing)`, `KeyVals("attribution", address →
    "<origin corpus> <origin marker>")` or `Text("attribution: every selected record is
    this world's own")`, `KeyVals("inputs the destination will not carry", dataset →
    "bytes held|not held; redistribution unknown")`.
  - `helpers/commons.py`: `build_published(work) -> Installations` (`build_fresh`, then
    under `with_remotes`, `open_rig(a, ("publish",))` publishes `target="a"` to `LOC_A`);
    snapshot `"commons-1a-published"`; `a_identity` gains `corpus_id`, `marker`, `artifact`
    read from the binding in A's write root.
  - CLI rows for `publish` (`--target`, `--to`, `--resume`) and `publish-preview`
    (`--target`, `--to`); adapters regenerated.

- [ ] **Step 1: Write the failing tests**

```python
def test_preview_lists_selection_closure_and_uncarried_inputs(fresh): ...        # read_rig(fresh.a, "publish-preview")
def test_preview_of_an_unresolvable_target_refuses(fresh): ...                   # unknown-project
def test_publish_to_a_git_remote_mints_the_binding_and_the_remote_lists_the_corpus(fresh):
    with with_remotes(fresh), open_rig(fresh.a, ("publish",)) as (d, ctx):
        text = d.invoke("publish", {"target": "a", "to": LOC_A}).text
    assert "[publication-binding]" in text and "[publication]" not in text
    binding = binding_fields(ctx.write_view().get(binding_ref(text)))
    listing = GitTransport(..., env=GIT_ENV, remote_for=...).listing(Destination.remote(LOC_A), binding.corpus_id)
    assert f"{binding.corpus_id}.head-artifact.v1" in listing and any(k.startswith(f"{binding.corpus_id}/") for k in listing)
def test_publish_without_a_current_epoch_refuses_naming_the_remedy(fresh_no_epoch): ...   # kernel-refused, "epoch" in message
def test_publish_to_a_relative_path_is_invalid_input(fresh): ...
def test_a_transport_fault_closes_kernel_refused_and_a_fresh_attempt_is_blocked_until_resume(fresh):
    with with_remotes(fresh), open_rig(fresh.a, ("publish",)) as (d, ctx):
        fault = transport_with(fail_after_push=True); publication.transport_for = lambda c, dest: fault   # restored by the fixture
        r1 = refused(lambda: d.invoke("publish", {"target": "a", "to": LOC_A}, invocation_id="p1"))
        assert r1.code == "kernel-refused" and r1.data["reason"] == "transport-fault"
        r2 = refused(lambda: d.invoke("publish", {"target": "a", "to": LOC_A}, invocation_id="p2"))
        assert r2.data["reason"] == "publish-unfinished"
        token = pending_publishes(...)[0]
        fault.fail_after_push = False
        text = d.invoke("publish", {"target": "a", "to": LOC_A, "resume": token}, invocation_id="p3").text
        assert "[publication-binding]" in text and commit_count(Remotes(fresh.remotes).bare("a")) == 1
def test_preview_matches_what_publish_froze(published):
    # the preview's selection equals the marker's selection read back through fetch_corpus
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_cmd_publish.py -v`
Expected: FAIL — unknown command `publish`. If `ScopedWriter.publish` or
`publication_preview` is absent on `beliefs` main, park `--reason dependency`.

- [ ] **Step 3: Add the declarations, prompts, `publication.py`, the handlers, the CLI rows (ops then adopt) and regenerate the adapters**

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_cmd_publish.py tests/test_cli_surface.py tests/test_adapters.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add commands/publish commands/publish-preview python/src/science/commands/publish.py python/src/science/commands/publish_preview.py python/src/science/publication.py python/tests/test_cmd_publish.py python/tests/helpers/commons.py tools/cli.toml adapters/claude-code
git commit -m "feat(publish): publish a view to a local or git destination, resume a stranded attempt, preview the freeze"
```

---

### Task 7: `provider-inspect` and `provider-bind`

**Files:**
- Create: `commands/provider-inspect/`, `commands/provider-bind/`,
  `python/src/science/commands/provider_inspect.py`, `python/src/science/commands/provider_bind.py`
- Modify: ops `cli.toml` → `tools/cli.toml`; adapters; `python/tests/helpers/commons.py` (`build_bound`)
- Test: `python/tests/test_cmd_provider.py`

**Interfaces:**
- Consumes: `beliefs.root.evaluate_copy(dest_root, subject, observers) -> str`
  (`"validated"` on success; no authority, no grant); `CorpusSubject`,
  `ArtifactCarrier.from_bytes`, `ObserverSet`; `GitTransport.fetch_corpus`;
  `SharingRegistry`, `sharing.replay`; `writer.record_sharing` (Task 4);
  `publication.marker_of/marker_fields/artifact_identity`.
- Produces:
  - Shared helper `publication.inspect(config, destination, corpus_id, scratch) ->
    Inspection(root, sibling, verdict, fields: MarkerFields, artifact: str)`: fetch into
    `scratch`, `evaluate_copy`, read the marker; `GitTransportFault` → `invalid-input`
    naming the location; a verdict other than `"validated"` → `invalid-input` naming it.
  - `provider-inspect` (read-only): inputs `location`, `corpus_id`. Report:
    `KeyVals("publication", world, marker, artifact, view, verdict)`. Scratch under
    `config.operations_root / "scratch" / "inspect" / <token>`, deleted after.
  - `provider-bind` (sharing): inputs `location`, `corpus_id`, `world` (string,
    **required**). Handler: validate (`corpus_id` and `world` 32 hex; `world` equal to the
    reader's own world id → `invalid-input` "a provider is another world"); `sharing_root`
    configured; `replay(registry, operations_root)`; `inspect(...)` into
    `registry.scratch(iid)`; `world != fields.world` → `world-mismatch` (data `claimed`,
    `given`); else `line = writer.record_sharing(SharingEvidence(… transition "bound",
    source "provider:<location>", location, verdict …))`, **then**
    `registry.write_binding(ProviderBinding(world, (location,), line.at, True))`; delete
    scratch; report `(pin_block(line),)`.
  - `helpers/commons.py`: `build_bound(work) -> Installations` (`build_published`, then
    B runs `provider-bind` with `world=a_identity(a)["world"]`); snapshot `"commons-1a-bound"`.
  - CLI rows and adapters.

- [ ] **Step 1: Write the failing tests**

```python
def test_inspect_reports_the_claimed_world_and_leaves_no_scratch(published): ...
def test_inspect_of_an_absent_corpus_names_the_location(published): ...
def test_bind_with_the_claimed_world_records_the_line_then_the_binding(published):
    text = ...invoke("provider-bind", {"location": LOC_A, "corpus_id": CID_A, "world": WORLD_A}).text
    assert f"[pin] {CID_A} bound" in text and registry.binding_for_location(LOC_A).confirmed
def test_bind_with_another_world_refuses_world_mismatch_and_writes_nothing(published): ...
def test_bind_with_a_malformed_or_own_world_refuses_before_fetching(published, monkeypatch): ...   # Review Focus 3
def test_bind_without_sharing_root_refuses_naming_the_key(...)
def test_a_crash_between_the_line_and_the_binding_is_repaired_by_replay(published, monkeypatch):
    monkeypatch.setattr(SharingRegistry, "write_binding", raise_after_call)   # the line lands, the registry write raises
    with pytest.raises(RuntimeError): d.invoke("provider-bind", {...})
    monkeypatch.undo()
    assert registry.binding_for_location(LOC_A) is None
    replay(registry, cfg_b.operations_root)
    assert registry.binding_for_location(LOC_A).world == WORLD_A
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_cmd_provider.py -v`
Expected: FAIL — unknown commands.

- [ ] **Step 3: Implement declarations, prompts, handlers, rows, adapters, `build_bound`**

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_cmd_provider.py tests/test_cli_surface.py tests/test_adapters.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add commands/provider-inspect commands/provider-bind python/src/science/commands/provider_inspect.py python/src/science/commands/provider_bind.py python/src/science/publication.py python/tests/test_cmd_provider.py python/tests/helpers/commons.py tools/cli.toml adapters/claude-code
git commit -m "feat(sharing): provider-inspect reads a publication's world; provider-bind binds a confirmed location"
```

---

### Task 8: `adopt`

**Files:**
- Create: `commands/adopt/`, `python/src/science/commands/adopt.py`
- Modify: ops `cli.toml` → `tools/cli.toml`; adapters; `python/tests/helpers/commons.py` (`build_adopted`, `build_reopened`)
- Test: `python/tests/test_cmd_adopt.py`

**Interfaces:**
- Consumes (kernel doors assumed): `ScopedWriter.restore(copy: Path, subject, observers,
  *, evidence) -> SharingLine` (runs `restore_root` under the scoped authority and
  ledgers `fetched` with the report's outcome as `verdict`);
  `ScopedWriter.admit_publication(root: Path, observers, *, evidence) -> SharingLine`
  (ledgers `admitted`). Existing: `require_publication_layout`, `ReadView.opened_at`,
  `ctx.world.registry().admissions`, `ctx.world.status`.
- Produces: declaration `write_class = "sharing"`, inputs `location`, `corpus_id`.
  Handler, in this order:
  1. validate inputs and `sharing_root`; `replay(registry, operations_root)`; a pin for
     `corpus_id` in state `admitted` or `mounted` → `invalid-input` "already adopted".
  2. **reconcile** (§10): every pin in state `fetched` or `admitted` **with a source**
     whose corpus the kernel registry lists admitted → `record_sharing(mounted)` then
     write the pin `mounted`.
  3. fetch into `root = registry.root_for(corpus_id)` unless a `fetched` pin and that
     directory already exist (reuse the fetched candidate, spec §10); `line =
     writer.restore(root, …, evidence "fetched")`; write pin `fetched` with `source=None`.
  4. **source**: `binding_for_location(location)`; none → `pin-unsourced` (message names
     the claimed world and the remedies `provider-bind` and `follow`; data `{"world": …}`);
     `binding.world != fields.world` → `world-mismatch`. Else write the pin `fetched` with
     `source=PinSource("provider", location)` **now**, so a later recovery never mounts an
     unsourced pin.
  5. **layout**: `require_publication_layout(records)`; `PublicationArrivalRefused` →
     `Refused(Refusal("kernel-refused", str(e), {"kind": …, "reason": e.reason}))`.
  6. **conflict**: shared addresses with any live root (write root, configured roots,
     mounted registry roots, pins admitted this invocation) → `adopt-conflict` with data
     `{"addresses": [...], "corpus": <live corpus id>, "reason": "overlap is milestone 1b
     (beliefs-81367e)"}`.
  7. `writer.admit_publication(root, observers, evidence "admitted")` → write pin
     `admitted`; `writer.record_sharing(… "mounted" …)` → write pin `mounted`.
  8. report: the pin blocks of this invocation's lines.
  `helpers/commons.py`: `build_adopted(work)` (`build_bound` then B adopts; snapshot
  `"commons-1a-adopted"`); `build_reopened(work) -> Installations` whose `b` is
  `reopen(adopted.b)` with `publish_session_epoch(b)` run (snapshot `"commons-1a-reopened"`).

- [ ] **Step 1: Write the failing tests**

```python
def test_adopt_unsourced_leaves_the_candidate_fetched_and_names_the_remedies(published): ...
def test_adopt_after_bind_admits_and_marks_mounted(bound): ...        # transitions fetched, admitted, mounted; pin source set; kernel live
def test_the_adopted_root_is_a_corpus_root_at_the_next_open(adopted):
    cfg = reopen(adopted.b)
    assert SharingRegistry(adopted.b.sharing_root).root_for(CID_A) in cfg.world.corpus_roots
    assert ReadContext.open(cfg).cited(ids["proposition"]).corpus_id == CID_A
def test_publish_before_reopen_refuses_selection_incomplete_naming_the_adopted_corpus(adopted): ...
def test_adopt_a_second_time_refuses_already_adopted(adopted): ...
def test_adopt_of_a_conflicting_candidate_refuses_before_admission(bound, conflicting_publication): ...
def test_adopt_of_an_absent_corpus_writes_nothing(bound): ...          # Review Focus 2
def test_a_crash_after_admission_before_the_pin_write_recovers_with_its_source(bound, monkeypatch):
    # write_pin raises on the "admitted" write only; the kernel shows admitted; the pin is "fetched" with a source
    ...; replay + the next adopt's reconcile → pin "mounted", source preserved
def test_a_crash_between_the_mounted_line_and_the_pin_write_is_repaired_by_replay(bound, monkeypatch): ...
def test_recovery_never_mounts_a_pin_without_a_source(bound):
    registry.write_pin(replace(pin_fetched_unsourced)); ...adopt another corpus...; assert registry.pin(X).state == "fetched"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_cmd_adopt.py -v`
Expected: FAIL — unknown command. Park `--reason dependency` if the doors are absent.

- [ ] **Step 3: Implement declaration, prompt, handler, rows, adapters, fixtures**

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_cmd_adopt.py tests/test_cli_surface.py tests/test_adapters.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add commands/adopt python/src/science/commands/adopt.py python/tests/test_cmd_adopt.py python/tests/helpers/commons.py tools/cli.toml adapters/claude-code
git commit -m "feat(sharing): adopt fetches, verifies, sources, checks layout and conflicts, then admits and mounts"
```

---

### Task 9: `fetch`

**Files:**
- Create: `commands/fetch/`, `python/src/science/commands/fetch.py`
- Modify: ops `cli.toml` → `tools/cli.toml`; adapters
- Test: `python/tests/test_cmd_fetch.py`

**Interfaces:**
- Consumes: `ctx.cited`, `stored.dataset_declaration`, `dataset_address`,
  `beliefs.holdings.boundary.write`, `StoreLocator`, `url_locator`,
  `beliefs.holdings.transport.retrieve(location, bounds, seam, scratch) -> Retrieved |
  NotAttempted | Failed`, `RetrievalBounds(timeout_seconds, max_bytes, max_redirects)`,
  `url_seam()`, `refuse_scratch_root`; `writer.holdings_context(instrument=INSTRUMENT)`,
  `writer.store_id`; `ctx.config.fetch`. Pattern: `commands/dataset.py:105-113`.
- Produces: declaration `write_class = "mints:holdings-observation"`, `[write.routes]
  holdings-observation = "holdings"`, inputs `dataset` (required), `source` (required: an
  absolute path or a `https://` URL), `[reads] families = ["corpus-stored", "holdings"]`.
  Handler, all before the one act:
  1. `policy == "records-only"` → `invalid-input` naming `[fetch] policy`.
  2. `ctx.cited(dataset)`; one resource (else `invalid-input` naming `sci-d1e874`);
     declared `digest` and `name`.
  3. path: read bytes. URL: `retrieve(url_locator(source), RetrievalBounds(timeout_seconds=60,
     max_bytes=policy.max_bytes or 1 << 31, max_redirects=5), url_seam(), scratch)` with
     `scratch = operations_root / "scratch" / "fetch" / iid`; `NotAttempted`/`Failed` →
     `invalid-input` with the reason; bytes read from `retrieved.path`, which is unlinked
     in every exit.
  4. `sha256:<hex>` of the bytes `!= digest` → `invalid-input` naming both; `max_bytes`
     non-zero and exceeded → `invalid-input`.
  5. the act: `write(holdings, StoreLocator(writer.store_id, f"{hex}/{name}"), content,
     expected=digest)`; report `(record_block(observation node),)` read back from
     `ctx.write_view()`.

- [ ] **Step 1: Write the failing tests**

```python
def test_fetch_from_a_path_holds_the_mounted_dataset_bytes(reopened): ...          # held_path(A_DATASET) reads DATA_A
def test_fetch_with_mismatching_path_bytes_refuses_and_writes_nothing(reopened, tmp_path): ...
def test_fetch_with_mismatching_url_bytes_refuses_and_writes_nothing(reopened, monkeypatch):   # Review Focus 4
    monkeypatch.setattr(fetch_module, "retrieve", lambda *a, **k: Retrieved(path=wrong_file, digest="sha256:" + sha256(b"wrong").hexdigest()))
    refusal = refused(lambda: rig.invoke("fetch", {"dataset": A_DATASET, "source": "https://data.test/a.txt"}))
    assert refusal.code == "invalid-input" and DECLARED in refusal.message and not wrong_file.exists()
    assert refused(lambda: ReadContext.open(cfg).held_path(A_DATASET)).code == "invalid-input"
def test_fetch_from_a_url_stores_matching_bytes(reopened, monkeypatch): ...
def test_fetch_under_records_only_refuses_naming_the_policy(reopened): ...
def test_fetch_over_max_bytes_refuses(reopened): ...
def test_fetch_never_redeclares_the_dataset(reopened): ...                          # cited(A_DATASET).corpus_id stays CID_A
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_cmd_fetch.py -v`
Expected: FAIL — unknown command.

- [ ] **Step 3: Implement declaration, prompt, handler, row, adapters**

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_cmd_fetch.py tests/test_cli_surface.py tests/test_adapters.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add commands/fetch python/src/science/commands/fetch.py python/tests/test_cmd_fetch.py tools/cli.toml adapters/claude-code
git commit -m "feat(fetch): hold a mounted dataset's bytes from a path or URL after checking the declared digest"
```

---

### Task 10: The accept policy in every belief read

**Files:**
- Create: `python/src/science/acceptance.py`
- Modify: `python/src/science/closure.py:38-44`, `python/src/science/config.py:525-546`,
  `python/src/science/commands/belief.py`, `python/src/science/commands/next.py`
- Test: `python/tests/test_acceptance.py`, extend `python/tests/test_cmd_belief.py`

**Interfaces:**
- Consumes: `AcceptancePolicy`, `AcceptanceContext`; `gather(..., acceptance=)`,
  `evaluate_over(..., acceptance=)` (the kernel passes `(corpus_id, node.id)`,
  `evaluation.py:472,558`); `SharingRegistry`; `publication.marker_of/marker_fields`;
  the write root's `publication-binding` records.
- Produces:

```python
@dataclass(frozen=True)
class Carrier:                 # a session mount that is a publication
    corpus_id: str; world: str; marker: str; selection: frozenset[str]
    attributions: Mapping[str, tuple[str, str]]     # address -> (origin corpus, origin marker)

@dataclass(frozen=True)
class AcceptanceInputs:
    own_corpus: str
    own_roots: frozenset[str]                       # corpus ids of the write root and every configured (hand-listed) root
    verifiers: frozenset[str]                       # own world ∪ config.accept
    pins: Mapping[str, Pin]                         # mounted pins by corpus id
    bindings: Mapping[str, ProviderBinding]
    own_bindings: frozenset[tuple[str, str, str]]   # (corpus_id, marker, artifact) from the write root
    carriers: Mapping[str, Carrier]                 # every mounted publication (registry roots), by corpus id

def acceptance_inputs(ctx: ReadContext) -> AcceptanceInputs: ...
def counts(inputs: AcceptanceInputs, corpus_id: str, address: str) -> bool: ...
def statement(inputs: AcceptanceInputs) -> str: ...
def policy(ctx: ReadContext) -> AcceptancePolicy: ...
def explain(context: AcceptanceContext, inputs: AcceptanceInputs) -> tuple[tuple[str, str], ...]: ...
```

  `counts` is **first applicable branch decides**, spec §9 item 2:
  1. `corpus_id in inputs.own_roots` → **Own**, True (write root, and hand-listed
     configured roots: Deviation 6).
  2. `carrier = carriers.get(corpus_id)`; none → False (a mounted root with no marker is
     not a publication and not ours).
  3. `address in carrier.attributions` → **Carried** decides: `(origin, origin_marker) =
     carrier.attributions[address]`; True iff `origin in pins` and
     `pins[origin].marker == origin_marker` and `pins[origin].origin_confirmed(bindings)`
     and `pins[origin].world in verifiers` and `origin in carriers` and `address in
     carriers[origin].selection` (the authenticated origin publication actually holds the
     record); else False, whatever the carrier's own standing.
  4. `(corpus_id, carrier.marker, pins[corpus_id].artifact) in own_bindings` → **Own**,
     True (our own publication adopted back; a marker merely claiming our world id never
     reaches here because it has no binding).
  5. **Carrier's own**: `carrier.world in verifiers and pins[corpus_id].origin_confirmed(bindings)`.
  `statement`: canonical JSON (`sort_keys=True`, `separators=(",", ":")`) of
  `{"policy": "science.accept.v1", "verifiers": sorted, "own_roots": sorted, "pins": [{corpus,
  world, marker, source, confirmed, state}] sorted by corpus, "own_bindings": sorted,
  "carriers": [{corpus, world, marker, selected: n, attributed: n}] sorted}`; deterministic
  for a context. **Note:** once a policy is always supplied, `belief_input_digest`
  incorporates the statement (`beliefs/belief.py:514`); existing digest assertions in
  tests are updated, not weakened.
  `closure.gather_inputs`/`evaluate` gain `acceptance=None`; `ReadContext.gather_inputs`/
  `evaluate` pass `acceptance.policy(self)` in both modes; `belief.py` adds
  `KeyVals("acceptance", explain(...))` when `answer.acceptance is not None`.

- [ ] **Step 1: Write the failing tests**

```python
def test_own_write_root_and_configured_roots_count_under_an_empty_policy(): ...
def test_a_carriers_own_record_counts_only_when_accepted_and_origin_confirmed(): ...
def test_a_carried_record_is_decided_by_its_origin_even_in_an_accepted_confirmed_carrier():
    # INPUTS_ACCEPT_B: B origin-confirmed and accepted; A unaccepted. B carries A's assessment.
    assert not counts(INPUTS_ACCEPT_B, CID_B, A_ASSESSMENT)
    assert counts(INPUTS_ACCEPT_A_AND_PIN_A, CID_B, A_ASSESSMENT)
def test_a_forged_attribution_to_a_record_the_origin_does_not_hold_never_counts():
    # carrier B attributes "assessment:invented" to (CID_A, MARKER_A); A's selection lacks it
    assert not counts(INPUTS_ACCEPT_A_AND_PIN_A, CID_B, "assessment:invented")
def test_an_attribution_naming_another_marker_of_the_origin_never_counts(): ...   # pins[A].marker != origin marker
def test_own_records_adopted_back_count_through_the_binding(): ...
def test_a_marker_merely_claiming_our_world_never_takes_the_own_branch(): ...
def test_statement_is_canonical_json_and_encodes(): ...
def test_accept_naming_an_unpinned_world_changes_nothing(reopened): ...            # Review Focus 5
def test_belief_with_empty_accept_excludes_a_and_says_so(reopened): ...
def test_belief_with_accept_a_includes_a(reopened): ...
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_acceptance.py -v`
Expected: FAIL with `ModuleNotFoundError: science.acceptance`.

- [ ] **Step 3: Implement and thread `acceptance=` through**

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_acceptance.py tests/test_cmd_belief.py tests/test_cmd_next.py tests/test_belief_path.py tests/test_mount_citations.py -v`
Expected: PASS; `test_mount_citations.py:171-182` still sees the mount's assessment
(Deviation 6).

- [ ] **Step 5: Commit**

```bash
git add python/src/science/acceptance.py python/src/science/closure.py python/src/science/config.py python/src/science/commands/belief.py python/src/science/commands/next.py python/tests/test_acceptance.py python/tests/test_cmd_belief.py
git commit -m "feat(belief): compute the accept policy from pins, bindings and carriers; belief explains it"
```

---

### Task 11: `show`

**Files:**
- Create: `commands/show/`, `python/src/science/commands/show.py`
- Modify: ops `cli.toml` → `tools/cli.toml`; adapters
- Test: `python/tests/test_cmd_show.py`

**Interfaces:**
- Consumes: `SharingRegistry`, `ctx.world.status`, `acceptance.acceptance_inputs/counts`,
  `ctx.gather_inputs(proposition)` (returns `EvaluationInputs` after the policy filter:
  `assessments`, `verifications`, `acceptance`).
- Produces: declaration `write_class = "read-only"`, input `corpus_id`. Report:
  `Heading`, `KeyVals("pin", state, world, marker, artifact, view, keep)`,
  `KeyVals("source", kind, reference, confirmation: origin-confirmed|recommended|unsourced)`,
  `KeyVals("fetch", location, at, verdict)`, `KeyVals("kernel", known, live, present)`,
  `KeyVals("acceptance", ("world accepted", yes|no), ("counts as evidence", yes|no))` where
  the second is `counts(inputs, corpus_id, <an assessment address of the corpus>)` or
  `n/a` when the corpus holds none; `KeyVals("evidence", per assessment the corpus holds:
  "<assessment>: verifications <n total> from worlds <…>, <k> count under the policy")`
  computed from `ctx.gather_inputs(<its proposition>)` (verifications whose target is the
  assessment, each attributed to its holding corpus's world through `carriers`/own roots);
  `Text("independence: not exposed by the kernel's inputs (Deviation 8)")`; a `Finding`
  when the kernel shows admitted and the registry does not show `mounted` ("registry lags
  the kernel: `adopt` reconciles it"). No pin → `invalid-input`.

- [ ] **Step 1: Write the failing tests**

```python
def test_show_a_mounted_origin_confirmed_pin(adopted): ...
def test_show_distinguishes_accepted_evidence_from_confirmed_origin(reopened):
    unaccepted = read_rig(reopened.b, "show").invoke("show", {"corpus_id": CID_A}).text
    assert "confirmation: origin-confirmed" in unaccepted and "world accepted: no" in unaccepted and "0 count under the policy" in unaccepted
    accepted = read_rig(replace(reopened.b, accept=(WORLD_A,)), "show").invoke(...).text
    assert "world accepted: yes" in accepted and "counts as evidence: yes" in accepted
def test_show_lists_bs_verification_of_as_assessment_once_minted(reopened_verified): ...   # "verifications 1 from worlds <WORLD_B>"
def test_show_reports_a_registry_that_lags_the_kernel(adopted): ...
def test_show_of_an_unknown_pin_refuses(adopted): ...
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_cmd_show.py -v`
Expected: FAIL — unknown command.

- [ ] **Step 3: Implement declaration, prompt, handler, row, adapters**

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_cmd_show.py tests/test_cli_surface.py tests/test_adapters.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add commands/show python/src/science/commands/show.py python/tests/test_cmd_show.py tools/cli.toml adapters/claude-code
git commit -m "feat(sharing): show answers a pin's state, source, kernel status, acceptance and verification picture"
```

---

### Task 12: The milestone's decisive cases end to end

**Files:**
- Create: `python/tests/test_commons_1a.py`

**Interfaces:**
- Consumes: every fixture in `helpers.commons` (`reopened` is the start: B with A mounted,
  epoch current).

- [ ] **Step 1: Write the failing tests**

```python
def test_b_reproduces_one_assessment_after_fetching_the_bytes(reopened):
    rig.invoke("fetch", {"dataset": ids["dataset"], "source": str(reopened.data_a_path())})
    text = rig.invoke("verify", {"assessment": ids["assessment"], "code": str(code), "entrypoint": entrypoint}).text
    assert "[verification]" in text
def test_b_derives_without_redeclaring_and_the_lineage_reaches_as_dataset(reopened):
    spec_b = ...invoke("spec", dict(WORKING_FIELDS, target=ids["proposition"], dataset=ids["dataset"]))   # one changed input
    run_b = mint_fixture_run(reopened.b, spec_b, ids["dataset"], fixture_bundle(work))
    assessment_b = ...invoke("assess", {"run": run_b})
    assert assessment_b != ids["assessment"]
    assert ReadContext.open(reopened.b).cited(ids["dataset"]).corpus_id == CID_A
    assert ids["dataset"] in closure_input_addresses(decode_run_closure(...run_b...))
def test_bs_marker_attributes_the_carried_records_to_a_and_not_its_own(derived):
    publish_session_epoch(derived.b); ...invoke("publish", {"target": "b", "to": LOC_B})
    root, sibling = GitTransport(...).fetch_corpus(Destination.remote(LOC_B), CID_B, tmp)
    fields = marker_fields(marker_of(root))
    assert fields.attributions[ids["dataset"]] == (CID_A, ids["marker"]) and fields.attributions[ids["proposition"]] == (CID_A, ids["marker"])
    assert assessment_b in fields.selection and assessment_b not in fields.attributions
def test_belief_excludes_a_under_empty_accept_and_includes_it_under_accept_a(derived): ...
def test_publish_retried_after_a_partial_push_converges(fresh): ...   # the §12 transport case over the real git remote: fault, blocked, resume, one commit
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `just test-one tests/test_commons_1a.py -v`
Expected: FAIL at the first missing fixture or helper (`derived`, `closure_input_addresses`).

- [ ] **Step 3: Add the `derived` fixture and `closure_input_addresses` to `helpers/commons.py`; make the tests pass**

- [ ] **Step 4: Run the tests and the fast check**

Run: `just test-one tests/test_commons_1a.py -v && just test-fast`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add python/tests/test_commons_1a.py python/tests/helpers/commons.py
git commit -m "test(commons): the 1a walk end to end: reproduce, derive, attribute, accept, converge"
```

---

### Task 13: Documents and final verification

**Files:**
- Modify: `docs/specs/2026-09-30-science-commons-design.md`,
  `docs/specs/2026-08-31-command-framework-design.md` §4.4, `tools/cli.toml` header note
  (via ops), `README.md`/`AGENTS.md` only if `just check` asks.
- Test: `just gate`.

- [ ] **Step 1: Amend the documents (dated 2026-10-22)**

- Commons spec §5 step 5: the dry run is `publish-preview` (Deviation 1); step 2: `show`
  reports verifications and says independence is not exposed (Deviation 8); step 4:
  `fetch` retrieves through the holdings transport's `retrieve` and the URL observation is
  deferred (Deviation 4), with the follow-up task id; §4.4 layer 3: inspection is
  `provider-inspect`, binding requires `--world` (Deviation 2); §9: hand-listed configured
  roots take the Own branch (Deviation 6); §10/§12: `adopt-conflict` until `beliefs-81367e`
  (Deviation 3); §11: pointers to this plan, `beliefs-f24fe9`, `beliefs-6d6bb6`; the
  "assesses edge in a mount" row answered by the kernel's mount-citations decision 2.
- Framework §4.4: `bound` joins the sharing transitions, its registry counterpart the
  provider binding (Deviation 5).
- `tools/cli.toml:6` (via ops): replace `just vendor-cli` with the `vendored adopt` route.
- File the follow-up: `tasks add "fetch: record the URL observation through look once a
  post-act digest mismatch has a framework answer" --status idea --tag commons`.

- [ ] **Step 2: Run the full gate**

Run: `just gate`
Expected: `check` prints nothing; the suite passes.

- [ ] **Step 3: Commit**

```bash
git add docs/specs/2026-09-30-science-commons-design.md docs/specs/2026-08-31-command-framework-design.md tools/cli.toml
git commit -m "docs(commons): record milestone 1a's deviations and kernel pointers; bound joins the sharing transitions"
```

---

## Self-review

**Spec coverage (§12 part 1a, §5, §7.4, §8, §9, §10, §11).** Publish with dry run:
Task 6. Adopt, show, provider bind: Tasks 8, 11, 7. Fetch: Task 9 (Deviation 4). Git
transport with the idempotent retry: Tasks 3, 6, 12. Spec/verify/run/assess over mounts
and belief over a world read: landed by `sci-dc0381`, exercised in Task 12. Accept
policy: Task 10, with the Carried branch authenticating the origin's selection and marker.
Sharing write class and `sharing_root`: Tasks 4, 2, 1, with ledger-before-registry and
replay. `follow`/`find` are milestone 2; retirement and supersession are 1b.

**Review findings addressed.** Codex 1 → Task 10 branch 3 and the forged-attribution
tests; 2 → Task 9 step 4 and Deviation 4; 3 → Task 3 `production_git_env`; 4 → `target`;
5 → binding-only report, door ledgers write-root records; 6 → Task 8 step 4 and
recovery tests; 7 → ledger-first everywhere, `replay`, interruption tests in Tasks 7–8;
8 → `--resume` and the blocked-then-resume test; 9 → Task 5 fixture before its
consumers, extended per command; 10 → rows and adapters per command task; 11 → Task 11
evidence picture and Deviation 8. Fresh reviewer C1 → `target`; C2 → Deviation 6; I1 →
Task 6; I2 → binding-only; I3 → `KernelRefusalValue` and `_invoke_sharing`'s refusal
rule; I4 → Deviations 2 and 5; I5 → the dependency list; I6 → ledger-first; I7 → branch
rule and marker match; I8 → `write_commons_config`; M1–M12 folded into Tasks 3, 4, 5, 6,
7, 8, 9, 10, 11; M13 declined (spec §10's `fetched` state is the restored copy).

**Type consistency.** `Pin`, `PinSource`, `ProviderBinding`, `SharingRegistry`, `replay`
(Task 1) used by Tasks 2, 7, 8, 10, 11; `PinBlock`/`pin_block` (Task 4) by Tasks 7, 8;
`marker_of`/`marker_fields`/`binding_fields`/`inspect` (Tasks 6, 7) by Tasks 8, 10, 12;
`GitTransport`/`GIT_ENV`/`Remotes`/`commit_count` (Task 3) by Tasks 5, 6, 12;
`FetchPolicy` (Task 2) by Tasks 5, 9; `Installations` fixtures by Tasks 6–12.

**Review Focus.** Lines 1–5 are tested in Tasks 2, 8, 7, 9, 10.

**Proportion.** Signatures, test names with assertions, and declaration field lists; no
handler body.
