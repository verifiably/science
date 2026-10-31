# Snapshot lineages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build each commons test world once per worker from its base snapshot's image instead of rebuilding its whole prefix chain, cutting the suite's snapshot build time from 1,591 s to about 845 s.

**Architecture:** `tests/helpers/snapshot.py` gains declarations (`Root`, `Derived`), `materialize`, `restore_tree`, `copy_value` and a per-test live record. A derived declaration builds in its root's directory: restore the base's image, run its step on a copy of the base's value, save an image. The commons builders in `tests/helpers/commons.py` and `build_bound_fetched_only` in `tests/test_cmd_adopt.py` become module-level declarations; fixtures call `materialize`.

**Tech Stack:** Python 3.13, pytest 9 with pytest-xdist (worksteal) and pytest-testmon, run only through the `just` front door.

**Spec:** `docs/specs/2026-10-31-snapshot-lineages-design.md` (revision 3, accepted at 0471907). Read it with `docs/specs/2026-10-02-world-fixture-snapshots-design.md`, which it revises.

## Global Constraints

- Test changes only. Nothing under `python/src/` changes.
- Snapshot names stay exactly as they are today (`commons-1a-fresh`, `commons-1b-sibling-publications`, …), so the timing baseline stays comparable.
- An image is saved as `work_base / f"{name}.image"`, and a derived declaration builds in its root's directory, `work_base / <root name>`.
- Tests run only through `just test-one <pytest args>` (paths relative to `python/`) and `just test-fast`; never call `pytest` directly. Run `just test-fast` before each commit.
- Acceptance threshold: a total snapshot build time above 1,000 s in Task 3 means the lineages did not work as designed. Stop and report; do not merge.
- No `.tt.toml` exists, so the suite policy is enabled. Execution Setup runs the full baseline `just test` and records its count.

## Setup (before Task 1, in `.worktrees/test-latency`)

1. `just test`: record the pass count and wall time in the ledger. The 2026-10-31 run gave 1140 passed. sci-56d9ce's two known parallel-only failures may appear; if they do, record them, don't fix them here.
2. Before-timings for Task 3, at the current HEAD, with `S=<scratch dir>`:
   - **Cold:** `TESTMON_DATAFILE=$S/tm-before just test-fast`. The fresh data file selects every test. Record the wall time and the test count from the summary line.
   - **Warm:** add `assert True` as the first line of the body of `test_a_name_reused_with_another_builder_is_refused` in `python/tests/test_snapshot.py`. Run `TESTMON_DATAFILE=$S/tm-before just test-fast` and record the wall time and the selected count, which must be above 0. Then restore the file with `git checkout -- python/tests/test_snapshot.py`.

## Review Focus

1. **A step that raises partway.** The next request for that declaration on the worker builds it again from the base's image. No half-built link is recorded, and no partial image is used. (Task 1: `test_a_failed_step_is_rebuilt_from_its_base`.)
2. **A live socket left under a lineage directory by an earlier test.** The next construction in that lineage refuses with the socket's path in the message rather than copying over it. (Task 1: `test_a_socket_in_the_lineage_refuses_construction`.)
3. **Tuple-shaped values** (`late_chain`, `sibling_publications`) through `copy_value` and `check_value`. The copy is a fresh tuple with equal members. (Task 1: `test_copy_value_rebuilds_containers_and_keeps_leaves`.)
4. **One name under both `snapshot()` and a module-level declaration.** It raises `ValueError` naming the snapshot, whichever came first. (Task 1: `test_a_declaration_reusing_a_root_name_is_refused`.)
5. **`request.getfixturevalue` mid-test** (`test_cmd_show.py:330` picks `adopted` or `bound_fetched_only`). A single snapshot per test still restores and passes under the guard. (Task 2: covered by the module runs of `test_cmd_show.py`.)

---

### Task 1: Lineage machinery in `helpers/snapshot.py`

**Files:**
- Modify: `python/tests/helpers/snapshot.py` (whole module)
- Modify: `python/tests/helpers/commons.py:510-521` (`fork`/`restore` helpers)
- Modify: `python/tests/conftest.py` (add an autouse live-record fixture beside `_no_thread_left_running`)
- Test: `python/tests/test_snapshot.py`

**Interfaces:**
- Produces, all in `helpers.snapshot`:
  - `@dataclass(frozen=True, eq=False) class Root: name: str; build: Callable[[Path], object]`
  - `@dataclass(frozen=True, eq=False) class Derived: name: str; base: "Root | Derived"; step: Callable[[Path, object], object]`
  - `Declaration = Root | Derived`
  - `@dataclass class WorldSnapshot: work: Path; image: Path; value: object; declaration: Declaration`, with `restore(self) -> None` (the live restore)
  - `restore_tree(image: Path, target: Path) -> None`
  - `copy_value(value: object) -> object`
  - `materialize(work_base: Path, declaration: Declaration) -> WorldSnapshot`
  - `snapshot(work_base: Path, name: str, build: Callable[[Path], object]) -> WorldSnapshot`: unchanged signature, now `materialize(work_base, <memoized Root>)`
  - `clear_live() -> None`
  - `_build_link(work_base: Path, declaration: Declaration) -> WorldSnapshot`: builds exactly one link whose base is already built. Task 3's timing plugin wraps it.
  - Module state: `_SNAPSHOTS: dict[str, WorldSnapshot]`, `_ROOTS: dict[str, Root]`, `_LIVE: dict[Path, Declaration]`
- Produces, in `helpers.commons`: `fork(installation_home: Path) -> Path` (unchanged) and `restore(copy: Path, installation_home: Path) -> None`, which now calls `restore_tree(copy, installation_home)` and builds no `WorldSnapshot`.

Behaviour the tests pin (spec §2.1–§2.3):

- **`restore_tree`** keeps today's `WorldSnapshot.restore` body:
  - it refuses a live socket under `target` (and at `short_socket(target)`) with `RuntimeError` naming it;
  - it calls `_forget_roots_under` and `_forget_worlds_under`;
  - it runs `rmtree(target)` then `copytree(image, target, symlinks=True)`.
- **`WorldSnapshot.restore()`**:
  - checks the guard: `_LIVE.get(self.work)` exists and `is not self.declaration` → `RuntimeError` naming both declarations;
  - then calls `restore_tree(self.image, self.work)`;
  - then sets `_LIVE[self.work] = self.declaration`.
- **`materialize`**:
  - checks identity first: a built name whose declaration `is not` the requested one raises `ValueError` naming the snapshot;
  - then checks the guard against the lineage directory, before any build or restore;
  - then, for a `Derived` declaration, builds the missing ancestors top-down, each through `_build_link`.
- **`_build_link`**:
  - **Root:** `work.mkdir()`, `value = build(work)`.
  - **Derived:** `restore_tree(base_snap.image, lineage_dir)`, then `value = step(lineage_dir, copy_value(base_snap.value))`.
  - **Both:** `check_value(value)`, then `copytree(work, image, symlinks=True)`. `_SNAPSHOTS[name]` is recorded only after the image is complete.
  - It never touches `_LIVE`.
- **`snapshot()`**: `_ROOTS.setdefault(name, Root(name, build))`. A stored `Root` whose `build is not build` raises `ValueError` naming the snapshot, which is today's rule.
- **`copy_value`** rebuilds values whose `type(v)` is exactly `dict`, `list` or `tuple`. It returns `_LEAVES` instances (`ScienceConfig`, `Path`, `str`, `int`, `bool`, `None`) as the same object, and raises `TypeError` naming the type for anything else, including a tuple, list or dict subclass.

- [ ] **Step 1: Write the failing tests in `python/tests/test_snapshot.py`**

Import `helpers.snapshot as snapshot_module` and the new names. These tests use `tmp_path` as `work_base`, with toy builders that write plain files. Name every declaration with `uuid.uuid4().hex`, so `_SNAPSHOTS` state from other tests cannot satisfy it. Add a helper `_manifest(root) -> dict[str, bytes]` (relative path → bytes, files only) and a toy three-link lineage factory `_chain(calls: list[str]) -> tuple[Root, Derived, Derived]`. Its builders append their link's name to `calls`, write `<link>.txt`, and add the link's name to a list in the value.

```python
def test_a_cold_deep_descendant_builds_each_ancestor_once_in_order(tmp_path):
    calls = []
    root, mid, leaf = _chain(calls)
    snap = materialize(tmp_path, leaf)
    assert calls == [root.name, mid.name, leaf.name]
    assert snap.work == tmp_path / root.name and snap.image == tmp_path / f"{leaf.name}.image"
    assert materialize(tmp_path, mid).declaration is mid and calls == [root.name, mid.name, leaf.name]

def test_construction_starts_from_the_base_image_not_a_dirtied_directory(tmp_path):
    calls = []
    root, mid, leaf = _chain(calls)
    base = materialize(tmp_path, mid); base.restore()
    (base.work / "stray.txt").write_text("dirty"); (base.work / f"{root.name}.txt").unlink()
    clear_live()  # a fresh test
    seen = {}
    def probe_step(work, value):
        seen["files"] = _manifest(work)
        return value
    materialize(tmp_path, Derived(uuid.uuid4().hex, mid, probe_step))
    assert seen["files"] == _manifest(base.image)

def test_construction_restores_record_nothing_so_the_live_restore_succeeds(tmp_path):
    _, _, leaf = _chain([])
    snap = materialize(tmp_path, leaf)
    assert snapshot_module._LIVE == {}
    snap.restore()
    assert snapshot_module._LIVE == {snap.work: leaf}

def test_a_step_internal_restore_records_nothing(tmp_path):
    root = Root(uuid.uuid4().hex, lambda work: ((work / "sub").mkdir(), (work / "sub" / "f").write_text("1"), {})[2])
    def step(work, value):
        copy = fork(work / "sub"); (work / "sub" / "f").write_text("2"); restore(copy, work / "sub")
        return value
    snap = materialize(tmp_path, Derived(uuid.uuid4().hex, root, step))
    assert snapshot_module._LIVE == {} and (snap.image / "sub" / "f").read_text() == "1"

def test_copy_value_rebuilds_containers_and_keeps_leaves(fresh_value):
    copied = copy_value(fresh_value)
    assert copied == fresh_value and copied is not fresh_value
    assert copied["a"] is fresh_value["a"]  # a ScienceConfig leaf, shared
    nested = {"k": [1], "t": (1, {"x": 2})}
    out = copy_value(nested)
    assert out == nested and out["k"] is not nested["k"] and out["t"][1] is not nested["t"][1]
    with pytest.raises(TypeError, match="Point"):
        copy_value(collections.namedtuple("Point", "x")(1))

def test_a_step_mutating_its_copy_leaves_the_base_value_unchanged(tmp_path):
    root = Root(uuid.uuid4().hex, lambda work: {"k": [1], "t": (1, {"x": 2})})
    def step(work, value):
        value["k"].append(2); value["t"][1]["x"] = 3; value["new"] = True
        return value
    materialize(tmp_path, Derived(uuid.uuid4().hex, root, step))
    assert snapshot_module._SNAPSHOTS[root.name].value == {"k": [1], "t": (1, {"x": 2})}

def test_a_different_declaration_under_a_built_name_is_refused(tmp_path):
    root = Root(uuid.uuid4().hex, lambda work: {})
    materialize(tmp_path, root)
    with pytest.raises(ValueError, match=root.name):
        materialize(tmp_path, Root(root.name, root.build))

def test_snapshot_calls_share_one_root_per_name_and_builder(tmp_path):
    name = uuid.uuid4().hex
    build = lambda work: {}
    assert snapshot(tmp_path, name, build).declaration is snapshot(tmp_path, name, build).declaration
    with pytest.raises(ValueError, match=name):
        snapshot(tmp_path, name, lambda work: {})

def test_a_declaration_reusing_a_root_name_is_refused(tmp_path):
    name = uuid.uuid4().hex
    snapshot(tmp_path, name, lambda work: {})
    with pytest.raises(ValueError, match=name):
        materialize(tmp_path, Root(name, lambda work: {}))

def test_a_request_from_a_lineage_with_a_live_world_is_refused_untouched(tmp_path):
    _, mid, leaf = _chain([])
    live = materialize(tmp_path, mid); live.restore()
    files, images = _manifest(tmp_path), sorted(p.name for p in tmp_path.glob("*.image"))
    with pytest.raises(RuntimeError, match=f"{mid.name}.*{leaf.name}|{leaf.name}.*{mid.name}"):
        materialize(tmp_path, leaf)
    assert _manifest(tmp_path) == files and sorted(p.name for p in tmp_path.glob("*.image")) == images
    assert leaf.name not in snapshot_module._SNAPSHOTS

def test_a_restore_from_a_lineage_with_a_live_world_is_refused_untouched(tmp_path):
    _, mid, leaf = _chain([])
    other = materialize(tmp_path, leaf)
    live = materialize(tmp_path, mid); live.restore()
    files = _manifest(live.work)
    with pytest.raises(RuntimeError, match=leaf.name):
        other.restore()
    assert _manifest(live.work) == files

def test_a_failed_step_is_rebuilt_from_its_base(tmp_path):
    root = Root(uuid.uuid4().hex, lambda work: ((work / "base.txt").write_text("b"), {})[2])
    attempts = []
    def step(work, value):
        attempts.append(1); (work / "half.txt").write_text("x")
        if len(attempts) == 1:
            raise RuntimeError("step failed")
        return value
    leaf = Derived(uuid.uuid4().hex, root, step)
    with pytest.raises(RuntimeError, match="step failed"):
        materialize(tmp_path, leaf)
    assert leaf.name not in snapshot_module._SNAPSHOTS and not (tmp_path / f"{leaf.name}.image").exists()
    snap = materialize(tmp_path, leaf)
    assert set(_manifest(snap.image)) == {"base.txt", "half.txt"}

def test_a_socket_in_the_lineage_refuses_construction(tmp_path):
    root = Root(uuid.uuid4().hex, lambda work: {})
    live = materialize(tmp_path, root); live.restore()
    path = live.work / "s.sock"
    server = socket.socket(socket.AF_UNIX)
    try:
        server.bind(str(path))
        clear_live()
        with pytest.raises(RuntimeError, match="s.sock"):
            materialize(tmp_path, Derived(uuid.uuid4().hex, root, lambda work, value: value))
    finally:
        server.close(); path.unlink()
```

`tmp_path` may exceed AF_UNIX's 107-byte limit. If `bind` raises `OSError` for length, use the `short_tmp` fixture from `conftest.py` as `work_base` in that test instead. The existing tests stay as they are; their `snapshot()` calls keep their meaning.

- [ ] **Step 2: Run them to verify they fail**

Run: `just test-one tests/test_snapshot.py`
Expected: FAIL at import (`cannot import name 'materialize'`, or a similar error for `Root`, `Derived`, `copy_value` or `clear_live`).

- [ ] **Step 3: Implement the interfaces above in `python/tests/helpers/snapshot.py`; switch `commons.restore` to `restore_tree`; add the autouse fixture in `conftest.py`**

The autouse fixture is `_one_live_world_per_lineage`: it yields, then calls `helpers.snapshot.clear_live()`. Update the module docstring to cite both specs. `lineage_dir(declaration)` walks `.base` up to the `Root` and returns `work_base / root.name`.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `just test-one tests/test_snapshot.py`
Expected: every test passes, the existing ones included. The confined-link test may be skipped where confinement is unavailable.

- [ ] **Step 5: Run every module that uses `snapshot()` or the commons fork helper**

Run: `just test-one tests/test_snapshot.py tests/test_commons_1b.py tests/test_two_corpora.py tests/test_mount_citations.py tests/test_cmd_verify.py tests/test_cmd_spec.py tests/test_belief_path.py tests/test_belief_path_transports.py tests/test_epoch_verb.py -n auto --dist worksteal`
Expected: all pass. The commons fixtures are untouched in this task; they keep working through `snapshot()`.

- [ ] **Step 6: `just test-fast`, then commit**

```bash
git add python/tests/helpers/snapshot.py python/tests/helpers/commons.py python/tests/conftest.py python/tests/test_snapshot.py
git commit -m "test(snapshot): lineage declarations, construction restores and a live-world guard (sci-0bea23)"
```

### Task 2: The commons chain as declarations

**Files:**
- Modify: `python/tests/helpers/commons.py` (each snapshot builder from `build_published` through `build_spec_only`, plus the two roots)
- Modify: `python/tests/conftest.py:76-330` (commons fixtures)
- Modify: `python/tests/test_cmd_adopt.py:69-90` (`build_bound_fetched_only` and its fixture) and `:407-421` (`content_conflict`, `uid_corruption` fixtures)

**Interfaces:**
- Consumes: `Root`, `Derived`, `materialize` and `copy_value` from Task 1.
- Produces: module-level declarations in `helpers.commons`, one per row below. Each step is the old builder's body after its opening base call, as `step_<x>(work: Path, value) -> value`. The old `build_<x>` functions are removed, except `build_fresh` and `build_fresh_no_epoch`, which are the two roots' builds. `build_installation` is unchanged (spec §2.4).

| constant | snapshot name | base | step from |
|---|---|---|---|
| `FRESH` | `commons-1a-fresh` | Root(`build_fresh`) | — |
| `FRESH_NO_EPOCH` | `commons-1a-fresh-no-epoch` | Root(`build_fresh_no_epoch`) | — |
| `PUBLISHED` | `commons-1a-published` | `FRESH` | `build_published` |
| `BOUND` | `commons-1a-bound` | `PUBLISHED` | `build_bound` |
| `ADOPTED` | `commons-1a-adopted` | `BOUND` | `build_adopted` |
| `REOPENED` | `commons-1a-reopened` | `ADOPTED` | `build_reopened` |
| `VERIFIED` | `commons-1a-verified` | `REOPENED` | `build_verified` |
| `DERIVED` | `commons-1a-derived` | `VERIFIED` | `build_derived` |
| `CONFLICTING` | `commons-1a-conflicting` | `BOUND` | `build_conflicting` |
| `CONTENT_CONFLICT` | `commons-1b-content-conflict` | `REOPENED` | `build_content_conflict` |
| `UID_CORRUPTION` | `commons-1b-uid-corruption` | `REOPENED` | `build_uid_corruption` |
| `PUBLISHED_B` / `PUBLISHED_B_UNKEPT` | `commons-1b-published-b` / `-unkept` | `DERIVED` / `REOPENED` | `_build_published_b` |
| `A_BOUND_B` / `_UNKEPT` | `commons-1b-a-bound-b` / `-unkept` | `PUBLISHED_B` / `PUBLISHED_B_UNKEPT` | `_build_a_bound_b` |
| `OVERLAPPING` / `_UNKEPT` | `commons-1b-overlapping` / `-unkept` | `A_BOUND_B` / `A_BOUND_B_UNKEPT` | `_build_overlapping` |
| `UPDATED` / `_UNKEPT` | `commons-1b-updated` / `-unkept` | `OVERLAPPING` / `OVERLAPPING_UNKEPT` | `_build_updated` |
| `B_UPDATED` / `_UNKEPT` | `commons-1b-b-updated` / `-unkept` | `UPDATED` / `UPDATED_UNKEPT` | `_build_b_updated` |
| `SIBLING_PUBLICATIONS` / `_UNKEPT` | `commons-1b-sibling-publications` / `-unkept` | `OVERLAPPING` / `OVERLAPPING_UNKEPT` | `_build_sibling_publications` |
| `LATE_CHAIN` | `commons-1b-late-chain` | `OVERLAPPING_UNKEPT` | `_build_late_chain` |
| `LATE_CHAIN_UNADOPTED` | `commons-1b-late-chain-unadopted` | `BOUND` | `_build_late_chain` |
| `LATE_LINK` | `commons-1b-late-link` | `LATE_CHAIN` (value is the 4-tuple) | `build_late_link` |
| `EQUAL_HOLDERS` | `commons-1b-equal-holders` | `VERIFIED` | `build_equal_holders` |
| `SPEC_DROP` | `commons-1b-spec-drop` | `VERIFIED` | `build_spec_drop` |
| `SPEC_ONLY` | `commons-1b-spec-only` | `REOPENED` | `build_spec_only` |
| `BOUND_FETCHED_ONLY` (in `test_cmd_adopt.py`) | `commons-1a-bound-fetched-only` | `BOUND` | `build_bound_fetched_only` |

Shared steps (`_build_published_b`, `_build_late_chain`, …) drop their `base` keyword and become a single `step_<x>(work, value)` used by both declarations. Every fixture becomes `snap = materialize(certified_worker_work, <CONSTANT>); snap.restore()`, and returns its existing shape built from `copy_value(snap.value)`. Example: `fresh_value` returns `copy_value(snap.value)`; `sibling_publications` returns `Installations.of(value), *refs` from `value, *refs = copy_value(snap.value)`.

- [ ] **Step 1: Write the failing test in `python/tests/test_snapshot.py`**

```python
def test_the_commons_chain_is_one_lineage_rooted_at_fresh():
    from helpers import commons
    from helpers.snapshot import Derived, Root
    leaves = [commons.SIBLING_PUBLICATIONS, commons.SIBLING_PUBLICATIONS_UNKEPT, commons.LATE_LINK,
              commons.B_UPDATED, commons.B_UPDATED_UNKEPT, commons.EQUAL_HOLDERS, commons.SPEC_DROP,
              commons.SPEC_ONLY, commons.CONFLICTING, commons.CONTENT_CONFLICT, commons.UID_CORRUPTION,
              commons.LATE_CHAIN_UNADOPTED]
    for leaf in leaves:
        node = leaf
        while isinstance(node, Derived):
            node = node.base
        assert node is commons.FRESH, leaf.name
    assert isinstance(commons.FRESH_NO_EPOCH, Root)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `just test-one tests/test_snapshot.py::test_the_commons_chain_is_one_lineage_rooted_at_fresh`
Expected: FAIL with `AttributeError: module 'helpers.commons' has no attribute 'SIBLING_PUBLICATIONS'`.

- [ ] **Step 3: Convert the builders, fixtures and `test_cmd_adopt.py` declarations as in the table**

- [ ] **Step 4: Run the new test and the module runs**

1. `just test-one tests/test_snapshot.py`: expect all to pass.
2. Each of `tests/test_commons_1a.py`, `tests/test_commons_1b.py`, `tests/test_cmd_adopt.py`, `tests/test_cmd_show.py` and `tests/test_publish_ownership.py`, alone and serial: `just test-one <module>`. Expect all to pass.
3. The same five, each alone with its test ids reversed:

   ```sh
   mapfile -t ids < <(just test-one <module> --collect-only -q 2>&1 | grep '::' | tac)
   just test-one "${ids[@]}"
   ```

   Collection also goes through the front door. The array keeps parametrized ids that contain spaces whole. Expect all to pass.
4. The five combined under worksteal, the order-nondeterministic case (spec §2.5):

   ```sh
   just test-one tests/test_commons_1a.py tests/test_commons_1b.py tests/test_cmd_adopt.py tests/test_cmd_show.py tests/test_publish_ownership.py -n auto --dist worksteal
   ```

   Expect all to pass.

Record each run's count and wall time in the ledger.

- [ ] **Step 5: Full suite**

Run: `just test`
Expected: the Setup baseline count passes, plus Task 1's and Task 2's new tests. A sci-56d9ce failure that also appeared in the Setup baseline is recorded, not fixed here.

- [ ] **Step 6: `just test-fast`, then commit**

```bash
git add python/tests/helpers/commons.py python/tests/conftest.py python/tests/test_cmd_adopt.py python/tests/test_snapshot.py
git commit -m "test(commons): build each commons snapshot from its base's image (sci-0bea23)"
```

### Task 3: Measure against the baseline and record

**Files:**
- Create (scratch, attached to the task, not committed): `snaptime-lineage-plugin.py`, an adaptation of the attachment `snaptime-plugin.py` on sci-0bea23
- Modify: `docs/specs/2026-10-31-snapshot-lineages-design.md` status line

**Interfaces:**
- Consumes: `helpers.snapshot._build_link(work_base, declaration) -> WorldSnapshot` from Task 1.

- [ ] **Step 1: Adapt the timing plugin**

In `pytest_sessionstart`, wrap `helpers.snapshot._build_link`. For each call, append `{"w": PYTEST_XDIST_WORKER, "name": declaration.name, "s": seconds}` to `$SNAP_OUT`. Each line is now one link's own cost, and their sum is the worker's build time, comparable to the baseline's sum.

- [ ] **Step 2: Run the full suite under the plugin, on the same host as the 2026-10-31 baseline**

Run: `SNAP_OUT=$S/snaps-after.jsonl PYTHONPATH=$S just test-one tests -p snaptime_lineage -n auto --dist worksteal -q`
Expected:
- every test passes;
- total `s` at or below 1,000 (projection about 845);
- the worst worker's sum noted (projection about 95).

If the total is above 1,000, stop: record the numbers and park the task for the user instead of merging. Note the host load (`cat /proc/loadavg`) beside the result.

- [ ] **Step 3: After-timings for test-fast**

Same two runs as Setup step 2, with `TESTMON_DATAFILE=$S/tm-after`:
- **Cold:** a fresh data file.
- **Warm:** the temporary `assert True` in `test_a_name_reused_with_another_builder_is_refused`, then `git checkout -- python/tests/test_snapshot.py`.

Record the wall time and the selected count for each. Expected: a warm selected count above 0.

- [ ] **Step 4: Record the results**

1. `tasks attach sci-0bea23` the plugin and `snaps-after.jsonl`, with captions.
2. Add one `tasks note` with the before and after figures: build total, worst worker, full-suite wall time, and cold and warm test-fast wall times with their counts.
3. Set the spec's status line to `implemented <date> on perf/test-latency; latency verify pending`.

- [ ] **Step 5: `just check`, then commit**

```bash
git add docs/specs/2026-10-31-snapshot-lineages-design.md
git commit -m "docs(specs): snapshot lineages implemented; measurements on sci-0bea23"
```
