# World fixture snapshots: build each test world once per worker, restore it per test

Status: draft 2026-10-02, revised after review round 1, for review. Task `sci-5937be` (test-latency halt), which absorbs
`sci-9b20ea`.

Sources: the breach note on `sci-5937be` (test-fast median 93.984 s against 90 s);
the profiles recorded on that task's notes on 2026-10-02; atoms task `atoms-257797`
(volume certification cache, filed from this task and out of its scope).

## 1. What this is

The suite spends most of its worker time building worlds, not testing them. A
`--durations=0` run at `46698e5` (683 tests, 211 s wall on the breach host under load) summed per module:

| module | setup s | call s | tests |
|---|---:|---:|---:|
| `test_two_corpora.py` | 353 | 25 | 11 |
| `test_mount_citations.py` | 208 | 102 | 21 |
| `test_epoch_verb.py` | 199 | 53 | 17 |
| `test_belief_path.py` | 69 | 7 | 3 |
| `test_cmd_spec.py` | 66 | 20 | 18 |
| `test_cmd_verify.py` | 38 | 25 | 4 |
| whole suite | 1107 | 867 | 683 |

Each of these modules builds its world in a function-scoped fixture: two corpora, a world
root, a store, held datasets, and often a walked spec → run → assess path through the
commands. One `build_shared_contract_world` plus `add_mounted_evidence` costs 11 s; of that,
atoms' per-bind SQLite-WAL certification is 2.7 s (100 child processes), YAML loading 1.1 s,
and the fixture run 4.9 s. The fixtures are function-scoped because most of their tests
write to the world.

This design keeps every test's world private and writable while building it once per
xdist worker: the fixture builds the world into a fixed directory, snapshots it, and
restores the snapshot to that same directory before each test.

## 2. Decisions

### 2.1 Restore to the same path, never relocate

A built world cannot move. atoms records each root's absolute path in its metadata
database (`root_lifecycle`, `root_operation`), and run records embed paths under the
fixture's `ops/scratch`. Relocating would mean rewriting kernel state the tests are
meant to exercise. A world restored to the path it was built at is byte-for-byte the
world the builder left, so no record changes meaning.

Probe (2026-10-02, scratch script, not kept): build `build_shared_contract_world`,
`copytree` it aside (11 ms), then three times: evict, `rmtree`, `copytree` back (15–18 ms)
and run `add_mounted_evidence` through the commands. All three writes succeeded and
minted the same four records each time.

Both copies, snapshot and restore, use `shutil.copytree(..., symlinks=True)` and copy
links as links. A confined run materializes environment links that point at sandbox
paths (`/science/env/...`, beliefs `adapter.SANDBOX_ENV`) which do not exist on the
host; the default `copytree` follows links and fails on them (review round 1, P1,
reproduced). A world is restored exactly as the builder left it, dangling links
included.

### 2.2 Evict beliefs' per-process registries on every restore

beliefs keeps one open `Corpus` per root path (`corpus._ROOT_STATES`) and one registry
view per world path (`world.registry._WORLD_STATES`). Restoring files under a live entry
leaves the entry's indexes describing the previous test's writes: the probe's second
restore without eviction failed with `CollisionRefused` on a dataset the restored files
no longer held. beliefs already ships the seam for this case, a root deleted and
recreated at one path under a live process: `corpus._forget_roots_under(directory)` and
`world.registry._forget_worlds_under(directory)`. Restore calls both on the world
directory before touching files.

No other process-wide state keyed by these paths was found: `helpers.world.STORE_IDS`
is keyed by the build path and written once at build; `beliefs.recipe`'s `lru_cache` is
over recipe content. The acceptance check in §4 is what proves the list complete.

### 2.3 One snapshot per worker per builder, made on first use

xdist workers are separate processes and a world's path is fixed, so workers cannot
share one snapshot. Each worker builds a given world the first time one of its tests
asks for it. Under `--dist worksteal` a module's tests start out in contiguous blocks,
so a module is typically built by one to three workers rather than by every test. The
build cost moves from per test to per worker; the saving is measured, not assumed (§4).

`--dist loadgroup` (one worker per module) was rejected: it would make
`test_mount_citations.py`'s 102 s of calls a single worker's long pole.

### 2.4 The shape: a snapshot is a builder plus its directory

`tests/helpers/snapshot.py` holds one small type:

```python
@dataclass
class WorldSnapshot:
    work: Path          # the fixed directory the world lives in
    image: Path         # its sibling copy
    value: object       # the builder's plain data: a config and record refs

    def restore(self) -> None: ...   # evict, rmtree work, copytree image -> work
```

and one function, `snapshot(work_base, name, build) -> WorldSnapshot`, which builds once
per process per `name` (a dict on the module), copies `work` to `image`, and returns the
snapshot. Builders stay ordinary functions of a `work: Path`; nothing in
`helpers/world.py` learns about snapshots.

A per-worker certified directory, session-scoped in `conftest.py`
(`certified_worker_work`, same `_certified_dir()` as today), is the `work_base`. Its
teardown removes every world and image under it.

A module's fixture becomes:

```python
@pytest.fixture
def shared(certified_worker_work):
    snap = snapshot(certified_worker_work, "shared-with-evidence", _build_shared)
    snap.restore()
    return snap.value
```

The test then writes freely; the next test's restore discards it. A test that removes
or corrupts a root (several do, to provoke refusals) is covered the same way, because
restore replaces the whole directory.

### 2.4a What a snapshot may hold: data, never open sessions

The snapshot caches only what outlives the files being replaced: the `ScienceConfig`,
record refs, and other plain values (review round 1, P2). Several fixtures today yield
live objects backed by an open session: `rig` in `test_cmd_spec.py` and
`test_cmd_verify.py`, and `walked_portable`/`walked_confined` in `test_belief_path.py`,
yield the dispatcher and context of an `open_rig`. Registry eviction cannot reset a
dispatcher's invocation index, a context's cached properties, or a session's open
ledger handles, and a snapshot taken while a session is open copies a ledger mid-write.

So a builder closes every session it opened (its `open_rig` block ends) before it
returns, and returns data only; `snapshot()` asserts the value is built from `Path`,
`str`, `int`, tuples, dicts and frozen dataclasses of those (`ScienceConfig` qualifies)
and refuses anything else by type name. A function-scoped fixture that hands tests a
dispatcher opens a fresh `open_rig` over the restored world after `restore()` and
closes it at teardown:

```python
@pytest.fixture
def rig(certified_worker_work):
    snap = snapshot(certified_worker_work, "spec-rig", _build_spec_world)
    snap.restore()
    cfg, ref = snap.value
    with open_rig(cfg, ("spec",)) as (d, ctx):
        yield d, ctx, ref
```

Opening a rig is cheap next to building the world: the build cost in §1 sits in the
corpora, the store, the datasets and the walked run, all of which the snapshot holds.

### 2.5 Build-time patches are applied twice, explicitly

Some builders run under a monkeypatch (`test_two_corpora.world` sets `run.POLICY` to
`MINIMAL_POLICY` when the host lacks confinement prerequisites). The build runs once,
outside any test, so its patch is applied with `pytest.MonkeyPatch.context()` inside the
build function and undone when the build returns. A test that also needs the patch
while it runs keeps taking `monkeypatch` and sets it itself. No fixture relies on a
patch leaking out of the build.

### 2.6 Scope: the six modules in the table

Converted: the world fixtures of `test_two_corpora.py`, `test_mount_citations.py`
(`shared`; `shared_read` becomes a restore of the same snapshot), `test_epoch_verb.py`,
`test_belief_path.py`, `test_cmd_spec.py` and `test_cmd_verify.py`. Each conversion is
its own commit with its module's setup time before and after. A module whose builder
turns out to read state the snapshot does not carry (§2.2) stays function-scoped, and
the plan records why.

`test_two_corpora.py` also takes the two requirements of `sci-9b20ea` that are not about
snapshots (review round 1, P2):

- The refusal tests that need no walked run, assessment or verification
  (`test_activating_read_contracts_in_the_writer_is_refused_by_the_write_root_pins`,
  `test_a_selected_record_no_configured_corpus_holds_refuses_naming_it`, the two
  `test_one_id_in_two_corpora_*` tests and
  `test_a_read_mount_without_a_manifest_refuses_at_the_read_entry_points`) take a
  second, cheaper snapshot of `build_two_corpus_world` alone. The plan confirms per
  test, by reading it, that it touches nothing the walked path mints; a test that does
  stays on the full world.
- `test_belief_answers_for_each_corpus_proposition_whatever_is_selected` today accepts
  `Belief` or `NoBelief`. It is pinned to each proposition's actual kind and reason,
  observed on the full world before the conversion and asserted after it.

Not here: the 49 s call in `test_belief_path_transports.py` and the call-time cost in
`test_cli_surface.py` and `test_selection_query.py` (no setup to save); YAML parse
caching in beliefs; atoms' certification cache (`atoms-257797`). Each is filed as a
follow-up if §4's measurement leaves the target unmet.

## 3. Surface

Test code only. New: `python/tests/helpers/snapshot.py`, the `certified_worker_work`
fixture. Changed: the six modules' fixtures, and the one pinned assertion in
`test_two_corpora.py` (§2.6). `sci-9b20ea` is closed by the `test_two_corpora.py`
conversion, which carries all three of its requirements.

## 4. Testing and acceptance

1. Behaviour: `just test` passes with no assertion weakened or removed. A conversion
   may change a fixture's body and its scope; the only assertion change is the
   tightening named in §2.6.
2. Isolation: each converted module passes serially on one worker
   (`just test-one tests/<module>.py`), where every test after the first runs on a
   restored world, and passes with its test ids passed in reverse order on the
   command line (pytest runs explicit node ids in the order given), so a test that
   depends on a previous test's writes, or on a pristine first build, fails here. No
   ordering plugin is added.
3. Restore check: a test in `tests/test_snapshot.py` builds a small world, writes a
   record, restores, and asserts the record is gone from both the files and a fresh
   read through the commands; then writes the same record again and restores again,
   which fails with `CollisionRefused` if eviction is skipped. This pins §2.2. A
   second case snapshots a world after a confined walk, where the host has the
   confinement prerequisites, and restores it twice: the sandbox links come back as
   links with their targets unchanged (§2.1). Without the prerequisites the case is
   skipped by the same `host_prerequisites()` check the confined fixtures use. A third
   case passes a value holding a dispatcher to `snapshot()` and expects the refusal
   (§2.4a).
4. Timing: `just test` and `just test-fast` from cold testmon on the breach host, before (main) and
   after (branch head), recorded as task notes with the summed setup per module. The
   target is the halt's: test-fast's median under 90 s. The task closes when
   `tt-latency verify sci-5937be --after <merge timestamp>` exits 0 on every host its breach notes name.

## 5. What does not change

Production code; the builders in `helpers/world.py`; `certified_work` and
`certified_module_work`, which non-converted tests keep using; the test recipes.

## 6. Limitations

1. Worker count multiplies builds. On a host whose budget gives many workers, a small
   module may be built by as many workers as it has tests and save little. §4's
   measurement says how much this costs on the breach host.
2. Restore relies on beliefs' `_forget_*` seams, which are private names. They exist
   for the test harness (their docstrings say so); if beliefs renames them, the
   restore check fails loudly rather than silently sharing state.
3. A test that leaves a live process (a service on `ops/service.sock`) holding files
   under the world would race the next restore. The converted fixtures' tests stop
   their services at teardown today; restore refuses if a socket file is present
   under the world directory rather than deleting it.

## 7. Task linkage

`sci-5937be` carries this spec. `sci-9b20ea` is absorbed with all three of its
requirements (§2.6) and closed when the `test_two_corpora.py` conversion lands. `atoms-257797` is independent.
