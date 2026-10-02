# World Fixture Snapshots Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build each expensive test world once per xdist worker and restore it per test, so the suite's setup time stops scaling with test count and the sci test-latency halt (`sci-5937be`) clears.

**Architecture:** A small test helper, `tests/helpers/snapshot.py`, builds a world into a fixed per-worker directory, copies it aside, and before each test evicts beliefs' per-process registries and copies the image back to the same path. Builders stay plain functions in `helpers/world.py` that close their sessions and return data; function-scoped fixtures restore, then open whatever rig a test needs.

**Tech Stack:** Python 3.13, pytest 9 with pytest-xdist (`--dist worksteal`) and pytest-testmon; beliefs (editable path dependency) for the registries.

**Spec:** `docs/specs/2026-10-02-world-fixture-snapshots-design.md` (accepted, review round 3).

## Global Constraints

- Test code only: no change under `python/src/`.
- Both copies use `shutil.copytree(..., symlinks=True)` (spec §2.1).
- Restore evicts with `beliefs.corpus._forget_roots_under(work)` and `beliefs.world.registry._forget_worlds_under(work)` before touching files (spec §2.2).
- A snapshot value is checked by shape: walk tuples, lists and `str`-keyed dicts; accept as leaves only `ScienceConfig`, `Path`, `str`, `int`, `bool`, `None`; refuse anything else by type name. `ScienceConfig` is a trusted leaf, never walked (spec §2.4a).
- Builders close every session they open before returning (spec §2.4a).
- Build-time monkeypatches use `pytest.MonkeyPatch.context()` inside the builder; a fixture that needs a patch while its test runs sets it itself on the test's `monkeypatch` (spec §2.5).
- No assertion is weakened or removed; the only assertion change is pinning `test_belief_answers_for_each_corpus_proposition_whatever_is_selected` (spec §2.6, §4.1).
- Tests run only through the justfile: `just test-one <args>` (from the worktree root; args are relative to `python/`), `just test-fast`, `just test`. Never call `pytest` directly.
- Paths shown to the user are written `.worktrees/test-latency/…`.

## Review Focus

1. A test that passes only because an earlier test on the same worker wrote to the world: caught by the reverse-order runs in Task 5, which every converted module goes through.
2. A process-wide cache keyed by a world path that the two `_forget_*` seams do not cover: the `CollisionRefused` restore case in Task 1 pins the known one; any other shows up as an order-dependent failure in Task 5.
3. A confined world whose sandbox links fail to copy: Task 1's confined case restores a real confined walk twice and compares every link.
4. A builder that returns a live object (a dispatcher, a context): `snapshot()` refuses it by type name, pinned in Task 1.
5. A service socket left under a world when the next restore runs: `restore()` refuses naming the socket rather than deleting it, pinned in Task 1.

---

### Task 1: The snapshot helper and its checks

**Files:**
- Create: `python/tests/helpers/snapshot.py`
- Modify: `python/tests/conftest.py` (add `certified_worker_work` after `certified_module_work`)
- Create: `python/tests/test_snapshot.py`

**Interfaces:**
- Produces:
  - In `helpers/world.py`: `build_shared_world_with_evidence(work: Path) -> tuple[ScienceConfig, dict[str, str]]`; `walk_belief_path(work: Path, *, confined: bool) -> tuple[ScienceConfig, str]` (config, proposition ref) and `BELIEF_PATH_COMMANDS`.
  - `snapshot(work_base: Path, name: str, build: Callable[[Path], object]) -> WorldSnapshot`: builds once per process per `name` into `work_base / name`, checks the value, copies to `work_base / f"{name}.image"`.
  - `WorldSnapshot(work: Path, image: Path, value: object)` with `restore() -> None`.
  - `check_value(value: object) -> None`: raises `TypeError` naming the first refused type and where it sits.
  - Fixture `certified_worker_work` (session scope): one certified directory per worker process.

- [ ] **Step 1: Write the failing tests**

`python/tests/test_snapshot.py`:

```python
"""Spec §4.3: a restore discards a test's writes, evicts beliefs' registries,
keeps sandbox links as links, and a snapshot holds data only."""
import os
import socket

import pytest

from beliefs.confinement import host_prerequisites
from helpers.snapshot import check_value, snapshot
from helpers.world import (
    build_belief_world, build_shared_world_with_evidence, hold_fixture_dataset, open_rig, walk_belief_path,
)
from science.config import ReadContext


def _belief_world(work):
    return build_belief_world(work)


def _files(root):
    return {(p.relative_to(root), p.read_bytes()) for p in root.rglob("*") if p.is_file() and not p.is_symlink()}


def _datasets(cfg):
    return [n.id for n in ReadContext.open(cfg).write_view().iter_stored() if n.kind == "dataset"]


def test_a_restore_discards_the_previous_tests_writes(certified_worker_work):
    snap = snapshot(certified_worker_work, "snapshot-check", _belief_world)
    snap.restore()
    before = _datasets(snap.value)
    ref = hold_fixture_dataset(snap.value, "data.txt", b"restore\n", "expression")
    assert ref in _datasets(snap.value)
    snap.restore()
    assert _datasets(snap.value) == before
    assert _files(snap.work) == _files(snap.image)


def test_the_same_write_succeeds_after_every_restore(certified_worker_work):
    """Without eviction the second write is CollisionRefused: the open corpus
    still indexes the first test's dataset (spec §2.2)."""
    snap = snapshot(certified_worker_work, "snapshot-check", _belief_world)
    for _ in range(2):
        snap.restore()
        hold_fixture_dataset(snap.value, "data.txt", b"twice\n", "expression")


def _links(root):
    return {p.relative_to(root): os.readlink(p) for p in root.rglob("*") if p.is_symlink()}


@pytest.mark.skipif(host_prerequisites() is not None, reason="confinement unavailable")
def test_a_confined_world_restores_its_sandbox_links_as_links(certified_worker_work):
    snap = snapshot(certified_worker_work, "walked-confined",
                    lambda work: walk_belief_path(work, confined=True))
    links = _links(snap.image)
    assert links, "a confined walk left no links; this check exercises nothing"
    for _ in range(2):
        snap.restore()
        assert _links(snap.work) == links


def test_a_live_dispatcher_is_refused_by_type_name(certified_worker_work):
    snap = snapshot(certified_worker_work, "snapshot-check", _belief_world)
    snap.restore()
    with open_rig(snap.value, ("spec",)) as (d, _):
        with pytest.raises(TypeError, match=type(d).__name__):
            check_value((snap.value, {"rig": d}))


def test_a_real_builders_config_and_refs_are_accepted(certified_worker_work):
    snap = snapshot(certified_worker_work, "shared-with-evidence", build_shared_world_with_evidence)
    check_value(snap.value)


def test_a_socket_under_the_world_refuses_the_restore(certified_worker_work):
    snap = snapshot(certified_worker_work, "snapshot-check", _belief_world)
    snap.restore()
    path = snap.work / "ops" / "s.sock"
    path.parent.mkdir(parents=True, exist_ok=True)
    server = socket.socket(socket.AF_UNIX)
    try:
        server.bind(str(path))  # under the certified root, well inside AF_UNIX's 107 bytes
        with pytest.raises(RuntimeError, match="s.sock"):
            snap.restore()
    finally:
        server.close()
        path.unlink()
```

- [ ] **Step 2: Run to verify they fail**

Run: `just test-one tests/test_snapshot.py`
Expected: collection error, `ModuleNotFoundError: No module named 'helpers.snapshot'`.

- [ ] **Step 3: Implement the helper**

`python/tests/helpers/snapshot.py`:

```python
"""Build a test world once per process and restore it per test (spec
docs/specs/2026-10-02-world-fixture-snapshots-design.md). A world records its
absolute path in atoms' metadata and in run records, so it is restored to the
directory it was built in, never moved."""
import shutil
import stat
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from science.config import ScienceConfig

_LEAVES = (ScienceConfig, Path, str, int, bool, type(None))


@dataclass
class WorldSnapshot:
    work: Path
    image: Path
    value: object

    def restore(self) -> None:
        from beliefs.corpus import _forget_roots_under
        from beliefs.world.registry import _forget_worlds_under
        sockets = [p for p in self.work.rglob("*") if stat.S_ISSOCK(p.lstat().st_mode)]
        if sockets:
            raise RuntimeError(f"a live socket under the world blocks the restore: {sockets}")
        _forget_roots_under(self.work)
        _forget_worlds_under(self.work)
        shutil.rmtree(self.work)
        shutil.copytree(self.image, self.work, symlinks=True)


_SNAPSHOTS: dict[str, WorldSnapshot] = {}


def check_value(value: object, where: str = "value") -> None:
    """Data only: a snapshot outlives the files under it, so it must not hold a
    session, dispatcher or context (spec §2.4a). `ScienceConfig` is trusted
    whole; around it only containers of plain leaves pass."""
    if isinstance(value, _LEAVES):
        return
    if isinstance(value, (tuple, list)):
        for i, item in enumerate(value):
            check_value(item, f"{where}[{i}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{where} has a {type(key).__name__} key; a snapshot holds str-keyed dicts")
            check_value(item, f"{where}[{key!r}]")
        return
    raise TypeError(f"{where} is a {type(value).__name__}; a snapshot holds a config, refs and plain data")


def snapshot(work_base: Path, name: str, build: Callable[[Path], object]) -> WorldSnapshot:
    """The world `build` makes in `work_base / name`, built on this process's
    first call for `name`. The caller restores it before use."""
    snap = _SNAPSHOTS.get(name)
    if snap is None:
        work, image = work_base / name, work_base / f"{name}.image"
        work.mkdir()
        value = build(work)
        check_value(value)
        shutil.copytree(work, image, symlinks=True)
        snap = _SNAPSHOTS[name] = WorldSnapshot(work, image, value)
    return snap
```

Add to `python/tests/conftest.py`, after `certified_module_work`:

```python
@pytest.fixture(scope="session")
def certified_worker_work():
    """One certified directory per worker process, holding the worlds
    `helpers.snapshot` builds once and restores per test."""
    with _certified_dir() as work:
        yield work
```

Add two builders to `python/tests/helpers/world.py` (add `import pytest` to its imports). After `add_mounted_evidence`:

```python
def build_shared_world_with_evidence(work: Path) -> tuple[ScienceConfig, dict[str, str]]:
    """`build_shared_contract_world` with `add_mounted_evidence`: the shape the
    mount-citation and epoch tests start from. Every session it opens is closed."""
    cfg = build_shared_contract_world(work)
    return cfg, add_mounted_evidence(cfg, work)
```

`add_mounted_evidence` mints its run through `mint_fixture_run`, which uses `MINIMAL_POLICY` itself, so no build-time patch is needed. At the end of the file, the belief-path walk moved out of `test_belief_path.py`'s `walk` (which Task 4 deletes), with its rig closed:

```python
BELIEF_PATH_COMMANDS = ("claim", "dataset", "spec", "run", "assess", "verify", "belief", "next")


def walk_belief_path(work: Path, *, confined: bool) -> tuple[ScienceConfig, str]:
    """claim -> dataset -> spec -> run -> assess -> verify through one dispatcher,
    the dispatcher closed at the end. Unconfined, the run command is patched to
    the minimal policy for the walk only."""
    import science.commands.run as run_module
    from beliefs.recipe import MINIMAL_POLICY

    def ref(text, prefix):
        return next(t for t in text.split() if t.startswith(prefix))
    with pytest.MonkeyPatch.context() as monkeypatch:
        if not confined:
            monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
            monkeypatch.setattr(run_module, "host_prerequisites", lambda: None)
        cfg = build_fixture_world_with_contract(work)
        code, entrypoint, targets = fixture_bundle(work, "supported")
        data = work / "data.txt"
        data.write_bytes(b"x\n")
        with open_rig(cfg, BELIEF_PATH_COMMANDS) as (d, _):
            prop = ref(d.invoke("claim", {"subject": "concept:disease-stage", "predicate": "affects",
                                          "object": "protein:PHF19", "layer": "causal",
                                          "polarity": "positive"}).text, "proposition:")
            dataset = ref(d.invoke("dataset", {"path": str(data), "title": "expression",
                                               "locator": "accession:GSE-FIXTURE"}).text, "dataset:")
            spec = ref(d.invoke("spec", dict(SPEC_FIELDS, target=prop, dataset=dataset)).text, "analysis-spec:")
            run = ref(d.invoke("run", {"spec": spec, "dataset": dataset, "code": str(code),
                                       "entrypoint": entrypoint, "targets": list(targets)}).text, "run:")
            assessment = ref(d.invoke("assess", {"run": run}).text, "assessment:")
            d.invoke("verify", {"assessment": assessment, "code": str(code), "entrypoint": entrypoint})
    return cfg, prop
```

`_SNAPSHOTS` is keyed by name alone because `certified_worker_work` is one directory per process; the session fixture's teardown removes every world and image.

- [ ] **Step 4: Run to verify they pass**

Run: `just test-one tests/test_snapshot.py`
Expected: 6 passed (5 passed, 1 skipped on a host without confinement). If the confined case fails on `assert links`, stop and report: spec §2.1's premise would not hold on this host.

- [ ] **Step 5: Commit**

```bash
git add python/tests/helpers/snapshot.py python/tests/conftest.py python/tests/test_snapshot.py python/tests/helpers/world.py
git commit -m "test: snapshot a built world per worker and restore it per test"
```

### Task 2: Shared-contract worlds: `test_mount_citations.py` and `test_epoch_verb.py`

**Files:**
- Modify: `python/tests/test_mount_citations.py:30-44` (fixtures) and the five `shared_read` tests' parameter lists
- Modify: `python/tests/test_epoch_verb.py:24-28`
- Modify: `python/tests/conftest.py` (remove `certified_module_work`, now unused)
- Modify: `docs/specs/2026-10-02-world-fixture-snapshots-design.md` §5 (drop `certified_module_work` from what does not change)

**Interfaces:**
- Consumes: `snapshot`, `certified_worker_work` (Task 1).
- Consumes: `build_shared_world_with_evidence` (Task 1). Snapshot name `"shared-with-evidence"`, shared by both modules and `test_snapshot.py`.

- [ ] **Step 1: Record setup before**

Run: `just test-one tests/test_mount_citations.py tests/test_epoch_verb.py -n auto --dist worksteal --durations=0 -q`
Sum the `setup` lines per module and note them: `tasks note sci-5937be "before: test_mount_citations setup <s> s, test_epoch_verb setup <s> s"`.

- [ ] **Step 3: Convert `test_mount_citations.py`**

Replace the `shared` and `shared_read` fixtures with:

```python
@pytest.fixture
def shared(certified_worker_work, monkeypatch):
    snap = snapshot(certified_worker_work, "shared-with-evidence", build_shared_world_with_evidence)
    snap.restore()
    _confine(monkeypatch)
    return snap.value
```

Import `snapshot` from `helpers.snapshot` and `build_shared_world_with_evidence` from `helpers.world`; drop `add_mounted_evidence` and `build_shared_contract_world` from the import if nothing else uses them. In the five tests taking `shared_read` (`test_a_mounted_record_is_cited_from_its_holder`, `test_with_coordination_off_a_mounted_ref_refuses_naming_the_mount`, `test_has_read_mounts_opens_no_corpus`, `test_own_refuses_a_mounted_record_naming_the_mount`, `test_an_unheld_ref_refuses_without_a_hint`), rename the parameter and its uses to `shared`; bodies otherwise unchanged. A restore costs milliseconds, so the read-only tests need no fixture of their own.

- [ ] **Step 4: Convert `test_epoch_verb.py`**

```python
@pytest.fixture
def shared(certified_worker_work):
    snap = snapshot(certified_worker_work, "shared-with-evidence", build_shared_world_with_evidence)
    snap.restore()
    cfg, _ = snap.value
    return cfg
```

Tests that take `certified_work` beside `shared` keep it: they use it for scratch (`extra_root`, bundles) outside the world.

- [ ] **Step 5: Remove `certified_module_work`, amend spec §5**

Delete the `certified_module_work` fixture from `conftest.py` (no user remains: `grep -rn certified_module_work python/tests` prints nothing). In the spec's §5, change "`certified_work` and `certified_module_work`, which non-converted tests keep using" to "`certified_work`, which non-converted tests keep using (`certified_module_work` had one user, `shared_read`, and is removed)".

- [ ] **Step 6: Run the two modules and the helper tests**

Run: `just test-one tests/test_mount_citations.py tests/test_epoch_verb.py tests/test_snapshot.py -n auto --dist worksteal --durations=0 -q`
Expected: all pass. Note the setup sums: `tasks note sci-5937be "after: test_mount_citations setup <s> s, test_epoch_verb setup <s> s"`.

- [ ] **Step 7: Commit**

```bash
git add python/tests docs/specs/2026-10-02-world-fixture-snapshots-design.md tasks/
git commit -m "test: mount citation and epoch tests restore one shared world"
```

### Task 3: `test_two_corpora.py`: full and refusal snapshots, the pinned belief

**Files:**
- Modify: `python/tests/helpers/world.py` (add `build_two_corpus_walked_world` after `add_archived_assessment`)
- Modify: `python/tests/test_two_corpora.py:35-69` (fixture), the four refusal tests' parameter, `:94-102` (pinned assertion)

**Interfaces:**
- Consumes: `snapshot`, `certified_worker_work`.
- Produces: `build_two_corpus_walked_world(work: Path) -> ScienceConfig`; snapshot names `"two-corpus-walked"` and `"two-corpus"`.

- [ ] **Step 1: Record setup before; take sci-9b20ea**

Run: `just test-one tests/test_two_corpora.py -n auto --dist worksteal --durations=0 -q`, then `tasks note sci-5937be "before: test_two_corpora setup <s> s"` and `tasks start sci-9b20ea` (absorbed by this task; closed in Step 7).

- [ ] **Step 2: Pin the belief test on the current fixture**

Replace the loop's last assertion in `test_belief_answers_for_each_corpus_proposition_whatever_is_selected`:

```python
    for proposition in ("proposition:archived", "proposition:claimed"):
        report = belief(ctx, proposition=proposition)
        assert report[0].text == f"Belief: {proposition}"
        assert dict(report[1].pairs) == {"kind": "NoBelief", "reason": "no-eligible-assessment", "detail": ""}
```

and its docstring's second sentence with: "Both runs are minted under `MINIMAL_POLICY`, so neither assessment is eligible: the archive's is unverified and the write root's verification replays a minimal-policy run; each answer is read under its own corpus's profile." Observed 2026-10-02 on the current fixture (confinement available): both propositions answer `NoBelief`, `no-eligible-assessment`, empty detail. Run `just test-one tests/test_two_corpora.py::test_belief_answers_for_each_corpus_proposition_whatever_is_selected` before converting: expected PASS. If it fails on this host, record the observed pairs in a note and stop: the answer is host-dependent and the pin needs a decision.

- [ ] **Step 3: Move the walked build into `helpers/world.py`**

```python
def build_two_corpus_walked_world(work: Path) -> ScienceConfig:
    """`build_two_corpus_world` with the archive's assessment, and in the write
    root proposition:claimed walked run → assess → verify and proposition:queued
    with a spec only; two projects and a published epoch. Every session it
    opens is closed."""
    import science.commands.run as run_module
    from beliefs.confinement import host_prerequisites
    from beliefs.recipe import MINIMAL_POLICY
    from science.world_belief import publish_session_epoch
    claim = {"subject": "concept:disease-stage", "predicate": "affects", "object": "protein:PHF19",
             "layer": "causal", "polarity": "positive", "slug": "claimed"}
    queued = dict(claim, object="protein:EZH2", slug="queued")

    def query(clause):
        return json.dumps({"version": "science.view-query.v1", "clauses": [{"all": [clause]}]})

    with pytest.MonkeyPatch.context() as monkeypatch:
        if host_prerequisites() is not None:
            monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
        cfg = build_two_corpus_world(work)
        add_archived_assessment(cfg, work)
        data = hold_fixture_dataset(cfg, "data.txt", b"y\n", "expression", **OBSERVED)
        bundle = fixture_bundle(work)
        with open_rig(cfg, ("claim", "spec")) as (d, _):
            d.invoke("claim", claim)
            d.invoke("claim", queued)
            spec = _minted_ref(d.invoke("spec", dict(SPEC_FIELDS, target="proposition:claimed", dataset=data)).text,
                               "analysis-spec")
            d.invoke("spec", dict(SPEC_FIELDS, target="proposition:queued", dataset=data))
        run = mint_fixture_run(cfg, spec, data, bundle)
        code, entrypoint, _ = bundle
        with open_rig(cfg, ("assess", "verify")) as (d, _):
            assessment = _minted_ref(d.invoke("assess", {"run": run}).text, "assessment")
            d.invoke("verify", {"assessment": assessment, "code": str(code), "entrypoint": entrypoint})
        with open_rig(cfg, ("project",)) as (d, _):
            d.invoke("project", {"name": "all three", "query": query({"addresses": [
                "proposition:archived", "proposition:claimed", "proposition:queued"]})})
            d.invoke("project", {"name": "all", "query": query({"kinds": ["proposition"]})})
        publish_session_epoch(cfg)
    return cfg
```

This is the current `world` fixture's body, its patch scoped to the build. Add `import json` and `import pytest` to `helpers/world.py`'s imports if absent.

- [ ] **Step 4: Replace the fixture; add the refusal fixture**

In `test_two_corpora.py`, replace `world` with:

```python
@pytest.fixture
def world(certified_worker_work):
    """The walked two-corpus world (`build_two_corpus_walked_world`), restored."""
    snap = snapshot(certified_worker_work, "two-corpus-walked", build_two_corpus_walked_world)
    snap.restore()
    return snap.value


@pytest.fixture
def two_corpora(certified_worker_work):
    """`build_two_corpus_world` alone, for refusals that read nothing the walk mints."""
    snap = snapshot(certified_worker_work, "two-corpus", build_two_corpus_world)
    snap.restore()
    return snap.value
```

The current `world` fixture's patch is build-only (the module's tests call no `run`), so the new fixture takes no `monkeypatch`. Drop imports the module no longer uses (`OBSERVED`, `SPEC_FIELDS`, `add_archived_assessment`, `_minted_ref`, `fixture_bundle`, `hold_fixture_dataset`, `mint_fixture_run`, `CLAIM`, `QUEUED` if unused).

- [ ] **Step 5: Move four refusal tests to `two_corpora`, one at a time**

For each of `test_activating_read_contracts_in_the_writer_is_refused_by_the_write_root_pins`, `test_a_selected_record_no_configured_corpus_holds_refuses_naming_it`, `test_one_id_in_two_corpora_refuses_selected_next_as_the_kernel_duplicate_location` and `test_a_read_mount_without_a_manifest_refuses_at_the_read_entry_points`: change the parameter `world` to `two_corpora` and add `world = two_corpora` as the body's first line (the body is unchanged). Read the body against `build_two_corpus_world`: it holds both contract documents, both roots, the vocabularies and `proposition:archived`, but no claimed or queued proposition, run, assessment, verification, project or epoch. Run the test alone: `just test-one tests/test_two_corpora.py::<name>`. If it fails, revert that test to `world` and note why: `tasks note sci-5937be "two_corpora: <name> stays on the walked world: <reason>"`. `test_one_id_in_two_corpora_refuses_naming_both_in_belief_and_unselected_next` stays on `world` (spec §2.6).

- [ ] **Step 6: Run the module**

Run: `just test-one tests/test_two_corpora.py -n auto --dist worksteal --durations=0 -q`
Expected: 11 passed. `tasks note sci-5937be "after: test_two_corpora setup <s> s"`.

- [ ] **Step 7: Commit, closing sci-9b20ea**

```bash
tasks done sci-9b20ea "test_two_corpora restores a walked snapshot and a cheaper two-corpus snapshot for refusals; belief test pinned to NoBelief/no-eligible-assessment (sci-5937be)"
git add python/tests tasks/
git commit -m "test: two-corpus tests restore built worlds; pin each proposition's belief"
```

### Task 4: `test_belief_path.py`, `test_cmd_spec.py`, `test_cmd_verify.py`

**Files:**
- Modify: `python/tests/helpers/world.py` (add `build_spec_rig_world`, `build_verify_rig_world`; `walk_belief_path` exists since Task 1)
- Modify: `python/tests/test_belief_path.py:15-59`
- Modify: `python/tests/test_cmd_spec.py:10-15`
- Modify: `python/tests/test_cmd_verify.py:7-23`

**Interfaces:**
- Consumes: `snapshot`, `certified_worker_work`.
- Consumes: `walk_belief_path`, `BELIEF_PATH_COMMANDS` (Task 1).
- Produces: `build_spec_rig_world(work: Path) -> tuple[ScienceConfig, str]` (config, dataset ref); `build_verify_rig_world(work: Path) -> tuple[ScienceConfig, str, tuple[Path, str, tuple[str, ...]]]` (config, assessment ref, bundle). Snapshot names `"walked-portable"`, `"walked-confined"`, `"spec-rig"`, `"verify-rig"`.

- [ ] **Step 1: Confirm the belief-path builder**

`walk_belief_path` and `BELIEF_PATH_COMMANDS` are in `helpers/world.py` since Task 1 (Step 3 there). Nothing to add.

- [ ] **Step 2: Record setup before**

Run: `just test-one tests/test_belief_path.py tests/test_cmd_spec.py tests/test_cmd_verify.py -n auto --dist worksteal --durations=0 -q`, then note the three setup sums on `sci-5937be`.

- [ ] **Step 3: Convert `test_belief_path.py`**

Delete `walk`. Replace the two fixtures:

```python
def _walked(work_base, monkeypatch, *, confined: bool):
    import science.commands.run as run_module
    from beliefs.recipe import MINIMAL_POLICY
    name = "walked-confined" if confined else "walked-portable"
    snap = snapshot(work_base, name, lambda work: walk_belief_path(work, confined=confined))
    snap.restore()
    if not confined:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
        monkeypatch.setattr(run_module, "host_prerequisites", lambda: None)
    cfg, prop = snap.value
    return cfg, prop


@pytest.fixture
def walked_portable(certified_worker_work, monkeypatch):
    cfg, prop = _walked(certified_worker_work, monkeypatch, confined=False)
    with open_rig(cfg, BELIEF_PATH_COMMANDS) as (d, ctx):
        yield d, ctx, prop, cfg


@pytest.fixture
def walked_confined(certified_worker_work, monkeypatch):
    if not CONFINED:
        pytest.skip(f"confinement unavailable: {host_prerequisites()}")
    cfg, prop = _walked(certified_worker_work, monkeypatch, confined=True)
    with open_rig(cfg, BELIEF_PATH_COMMANDS) as (d, ctx):
        yield d, ctx, prop, cfg
```

The test-time patch keeps what today's fixture gives its tests (the patch stays active while the test invokes `belief` and `next`). Import `walk_belief_path`, `BELIEF_PATH_COMMANDS` from `helpers.world` and `snapshot` from `helpers.snapshot`; drop `SPEC_FIELDS`, `build_fixture_world_with_contract`, `fixture_bundle` if unused.

Run: `just test-one tests/test_belief_path.py`. Expected: 3 passed (2 passed, 1 skipped without confinement).

- [ ] **Step 4: Convert `test_cmd_spec.py`'s `rig`**

In `helpers/world.py`:

```python
def build_spec_rig_world(work: Path) -> tuple[ScienceConfig, str]:
    """`build_belief_world` holding one expression dataset: the spec command's
    starting point."""
    cfg = build_belief_world(work)
    return cfg, hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
```

In `test_cmd_spec.py`:

```python
@pytest.fixture
def rig(certified_worker_work):
    snap = snapshot(certified_worker_work, "spec-rig", build_spec_rig_world)
    snap.restore()
    cfg, ref = snap.value
    with open_rig(cfg, ("spec",)) as (d, ctx):
        yield d, ctx, ref
```

The three tests that build their own world from `certified_work` stay as they are. Run: `just test-one tests/test_cmd_spec.py`. Expected: all pass.

- [ ] **Step 5: Convert `test_cmd_verify.py`'s `rig`**

In `helpers/world.py`:

```python
def build_verify_rig_world(work: Path) -> tuple[ScienceConfig, str, tuple[Path, str, tuple[str, ...]]]:
    """`build_belief_world` with one observed dataset, a spec, a minimal-policy
    run and its assessment: verify's starting point. The bundle lives under
    `work`, so a test that rewrites it is undone by the next restore."""
    cfg = build_belief_world(work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression", **OBSERVED)
    bundle = fixture_bundle(work, "supported")
    with open_rig(cfg, ("spec", "assess")) as (d, _):
        spec_ref = _minted_ref(d.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=ref)).text,
                               "analysis-spec")
        run_ref = mint_fixture_run(cfg, spec_ref, ref, bundle)
        assessment_ref = _minted_ref(d.invoke("assess", {"run": run_ref}).text, "assessment")
    return cfg, assessment_ref, bundle
```

In `test_cmd_verify.py`:

```python
@pytest.fixture
def rig(certified_worker_work, monkeypatch):
    import science.commands.run as run_module
    from beliefs.confinement import host_prerequisites
    from beliefs.recipe import MINIMAL_POLICY
    snap = snapshot(certified_worker_work, "verify-rig", build_verify_rig_world)
    snap.restore()
    if host_prerequisites() is not None:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
    cfg, assessment_ref, bundle = snap.value
    with open_rig(cfg, ("spec", "assess", "verify")) as (d, ctx):
        yield d, ctx, assessment_ref, bundle
```

The patch stays test-time: verify's replay runs during the test. `_minted_ref` returns the same token the old inline `next(...)` did (both take the first `assessment:`/`analysis-spec:` token). Run: `just test-one tests/test_cmd_verify.py`. Expected: 5 passed.

- [ ] **Step 6: Record setup after and commit**

Run the Step 2 command again and note the three setup sums.

```bash
git add python/tests tasks/
git commit -m "test: belief path, spec and verify tests restore built worlds"
```

### Task 5: Isolation, the full suite, and the latency measurement

**Files:**
- Modify: `docs/specs/2026-10-02-world-fixture-snapshots-design.md` (status line)

- [ ] **Step 1: Each converted module serially, in order and reversed**

For each of `test_two_corpora`, `test_mount_citations`, `test_epoch_verb`, `test_belief_path`, `test_cmd_spec`, `test_cmd_verify`, `test_snapshot`:

```bash
m=tests/<module>.py
just test-one "$m"
ids=$(just test-one "$m" --collect-only -q | grep '::' | tac | tr '\n' ' ')
just test-one $ids
```

`--collect-only` lists node ids and runs no test; `tac` reverses them, and pytest runs explicit node ids in the order given. Expected: both runs pass for every module. A failure in only one order means a test depends on another's writes or on a first build: fix the fixture (never the assertion) and rerun both orders.

- [ ] **Step 2: The full suite**

Run: `just test`
Expected: every test passes.

- [ ] **Step 3: Timing, before and after, from cold testmon**

On main and on this branch head, in turn, with the host otherwise quiet (`host-load` first; if it shows competing load, park with `--reason quiet` per the tasks skill):

```bash
rm -f python/.testmondata*   # cold testmon: test-fast selects everything
just test-fast
just test
```

Note: `tasks note sci-5937be "timing: main test-fast <s> s, test <s> s; branch test-fast <s> s, test <s> s; setup sum <s> s -> <s> s"`. If branch test-fast is not under 90 s, note the slowest remaining setups and calls, file the follow-ups named in spec §2.6 ("Not here") that the numbers implicate, and report before merging.

- [ ] **Step 4: Status and commit**

Set the spec's status line to `Status: implemented 2026-10-02 (sci-5937be); latency verify pending.` and commit:

```bash
git add docs/specs/2026-10-02-world-fixture-snapshots-design.md tasks/
git commit -m "docs(specs): world fixture snapshots implemented"
```

Closing `sci-5937be` is not part of this plan: after the merge, `tt-latency verify sci-5937be --after <merge timestamp>` must exit 0 on every host the breach notes name, and its output goes in the `tasks done` message.
