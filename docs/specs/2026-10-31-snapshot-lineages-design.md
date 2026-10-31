# Snapshot lineages: build each commons world once from its base, not from scratch

Status: draft for review, 2026-10-31, revision 2 (answers spec review round 1: §2.1–§2.5 rewritten). Task `sci-0bea23` (test-latency halt).

Revises `docs/specs/2026-10-02-world-fixture-snapshots-design.md` (§2.3, §2.4): a snapshot
may now be derived from another snapshot's image instead of from an empty directory.
Everything else in that design stands: restore to the same path, evict beliefs' registries
on restore, data-only values, one snapshot per worker per name.

## 1. What this is

The halt's breach note: test-fast median 142.7 s against 90 s on the breach host over
2026-10-23..10-30. Its median over the trailing window on 2026-10-31 was 241 s.
The full suite is not breached (median 142.5 s against 300 s). Even so, it takes
179–205 s for 1140 tests, so any test-fast run in which testmon selects most of the
suite is far over 90 s.

Measured on the breach host, 2026-10-31, worktree at `c701049`:

- **Full suite.** 1140 tests, 179–195 s wall, 16 xdist workers, about 26 min user CPU.
  The slowest single tests take 20–55 s, nearly all of it in fixture setup in
  `test_commons_1a`, `test_commons_1b`, `test_cmd_adopt`, `test_cmd_show` and
  `test_publish_ownership`.
- **Snapshot builds.** A plugin that timed each first `snapshot()` call per worker found
  82 builds summing to 1,591 s of worker time, 53–149 s per worker, in a 179 s run.
  More than half of all worker time goes to building snapshots.
- **Why they cost that.** Every commons builder calls its base builder directly
  (`build_sibling_publications` → `build_overlapping` → `build_a_bound_b` → … →
  `build_fresh`). Each snapshot therefore rebuilds its whole prefix chain, up to 12
  links, even when the same worker already holds the base's image. A worker that
  needs `adopted`, `reopened`, `verified` and `sibling_publications` builds
  `fresh → bound → adopted` four times. The costliest names: `adopted` built 10 times
  (140 s), `reopened` 9 times (138 s), `late-link` 4 times at 32 s each, `updated`
  3 times at 40 s each, `sibling-publications` 2 times at 47 s each.
- **One test profiled.** `test_cmd_adopt::test_a_refused_sibling_…` took 84 s under
  cProfile. Building `sibling_publications` took 76 s of that. In-process CPU dominates:
  atoms chain decoding and validation take about 40 s, and 9,001 YAML loads take
  12.6 s. Subprocess spawns (410 `git`, 156 snakemake/ldd) cost under 5 s.
- **testmon overhead.** The same test took 36 s without `--testmon` and 56 s with it,
  about 1.5×.

The earlier halt `sci-5937be` was cleared by the per-worker snapshots of 2026-10-02.
The commons 1a/1b chains (2026-10-23 onward) brought the latency back by building
their prefixes again inside every snapshot.

## 2. Decisions

### 2.1 Snapshots are declared objects; a derived one holds its base

A world records its absolute path (2026-10-02 §2.1), so an image cannot be restored
anywhere but the directory it was built in. A derived snapshot therefore builds in its
base's directory.

Ancestry has to be known before anything is built: a cold worker whose first test asks
for `adopted` has never requested `bound`, `published` or `fresh`. So a snapshot is a
declaration, a module-level object made at import time, and a derived declaration
holds its base declaration itself, not its base's name:

- **`Root(name, build)`.** `build(work) -> value`, built in `work_base / name`.
- **`Derived(name, base, step)`.** `base` is a `Root` or `Derived` object, and
  `step(work, value) -> value`. It builds in its root's directory, which every
  declaration in the lineage shares.

`materialize(work_base, declaration)` returns the built `WorldSnapshot`. For a `Derived`
declaration it walks up `base` to the nearest ancestor already built in this process,
or to the root, and builds each missing link downwards. For each link it:

1. restores the base's image into the shared directory (a construction restore,
   §2.3);
2. runs `step(work, copy_value(base.value))`;
3. runs `check_value` on the result;
4. saves the image as `work_base / f"{name}.image"`.

The existing `snapshot(work_base, name, build)` stays as the call for single-level
roots: it is `materialize(work_base, Root(name, build))`, keeping today's identity
check that a name is built by one builder.

A name stays one identity (2026-10-02 §2.3). `_SNAPSHOTS` keeps the declaration each
name was built from, and a request carrying a different declaration object under a
built name raises, as a different builder does today. Declarations are compared by
identity, so each is declared exactly once at module level.

The cost of a snapshot on a worker becomes its own step, plus each ancestor step that
worker has not yet built. The cost of the whole prefix is no longer paid again.

### 2.2 Copying a value: rebuild the containers, share the leaves

A step must never change its base's cached value, and the base's value holds
`ScienceConfig` objects. `copy.deepcopy` cannot copy those: their compiled
`ProfileSpec` holds `mappingproxy` views, and deepcopy raises
`TypeError: cannot pickle 'mappingproxy' object`.

`copy_value(value)` therefore follows the shapes `check_value` admits (2026-10-02
§2.4a):

- it rebuilds every `dict`, `list` and `tuple`;
- it returns every leaf (`ScienceConfig`, `Path`, `str`, `int`, `bool`, `None`) as the
  same object. These leaves are immutable: `ScienceConfig` is a frozen dataclass,
  trusted whole as `check_value` already trusts it.

A step that changes an installation replaces the leaf (`value["a"] = reopen(value["a"])`)
rather than mutating it, which the frozen dataclass enforces.

### 2.3 Construction restores and the live-world guard are separate

Snapshots in one lineage now share a directory, so a test that used two of them would
silently get the second over the first. No test requests two snapshots from one lineage
today. The only multi-snapshot tests are three `test_cmd_provider.py` cases that use
`published` and `world`, which are different roots.

Two kinds of restore therefore exist, kept apart:

- **Construction restore.** Inside `materialize`, restoring a base's image to build the
  next link. It is internal and records nothing.
- **Live restore.** `WorldSnapshot.restore()`, called by a fixture or test to use a
  world. It records `(lineage directory → declaration)` in a per-test live record. An
  autouse fixture in `conftest.py` clears that record at teardown.

`materialize` checks the live record first, before any build or restore. If the lineage
directory already holds a live world of a different declaration in this test, it
raises, naming both, and leaves the directory and the image set untouched. Without that
check, a lazy build would replace the live world before any restore could object.
`restore()` repeats the same check. Requesting and restoring the same declaration again
within one test is allowed.

### 2.4 The builders that become steps

Each commons builder that starts with `value = build_<base>(work)` becomes a `Derived`
declaration:

- its step is the code after that line;
- its base is the declaration of the builder it called.

Root declarations are `build_fresh` and `build_fresh_no_epoch`. Kept and unkept pairs
share one step function in two declarations with different bases. Covered:

- every `build_X` in `tests/helpers/commons.py`, including `build_conflicting`,
  `build_content_conflict`, `build_uid_corruption`, `build_late_*`, `build_equal_holders`,
  `build_spec_drop` and `build_spec_only`;
- `build_bound_fetched_only` in `tests/test_cmd_adopt.py`, which calls `build_bound(work)`
  directly today. It becomes a `Derived` declaration on the `bound` declaration, in that
  module.

The fixtures in `conftest.py` and the three direct `snapshot()` calls in
`test_cmd_adopt.py` call `materialize` with the declaration. No test calls a commons
builder outside `snapshot()` (checked 2026-10-31), so no composite full-chain builder is
kept.

The other lineages are independent roots with a single level, and they stay on
`snapshot(work_base, name, build)`: `walked-*`, `shared-with-evidence`, `verify-rig`,
`spec-rig`, `two-corpus-walked`, `rig`, `world`, `shared` and `two_corpora`.

### 2.5 Acceptance by measurement

- The suite passes. The snapshot timing plugin, adapted to `materialize`, reruns on
  the same host, and the plan records its totals beside the 2026-10-31 baseline. The
  projection from that baseline's per-worker build sets: total build time 1,591 s →
  about 845 s, worst worker 149 s → about 95 s.
- `test_snapshot.py` gains cases, each with declarations of its own so that
  `_SNAPSHOTS` state from other tests cannot satisfy them:
  - **Cold deep descendant.** In a process with none of its ancestors built,
    requesting a declaration three links deep first builds every ancestor once, in
    order. A later request for an ancestor reuses its image without building it again.
  - **Construction restores.** A derived build restores its base's image before its
    step runs. Those restores do not enter the live record, so the fixture's following
    live restore succeeds.
  - **Copy.** `copy_value` on a real commons value (with `ScienceConfig` leaves)
    succeeds. A step that rebinds or mutates containers in its copy leaves the base's
    cached value equal to what it was.
  - **Identity.** A different declaration object under a built name raises.
  - **Live-world refusal.** After a live restore of one declaration, requesting another
    declaration from the same lineage raises before building anything. The lineage
    directory's file manifest and the set of images are byte-for-byte unchanged.

## 3. Rejected

- **Sharing images across workers.** The absolute path of a world ties an image to the
  directory it was built in, and two workers cannot use one directory at once.
- **A persistent cross-run image cache keyed by a hash of the code.** It needs fixed
  paths with locks against concurrent runs (the main checkout, worktrees, other
  sessions). Any change under `src/`, beliefs or atoms invalidates it, and that is
  exactly when testmon selects most of the suite, so the cache would miss on the runs
  that matter.
- **`COVERAGE_CORE=sysmon` to cut testmon's overhead.** coverage 7.16 warns that dynamic
  contexts are unsupported under sysmon. testmon's per-test attribution depends on
  `switch_context`, so test selection would become wrong.
- **Concentrating commons tests on a few workers** (`xdist_group` with `--dist loadgroup`).
  It would give up worksteal balancing for the rest of the suite. Revisit it only if the
  lineages leave builds dominant.

## 4. Outside this branch

- **atoms-eaadf0: memoize chain-entry decoding.** Every chain read re-decodes every
  durable entry; that work was 18.5 s of the 84 s profile. A memo on the decoded
  value would help science, beliefs and atoms alike. atoms owns the change.
- **Closing the halt.** It closes only through `tt-latency verify` on the breach host after the
  merge. The projection above suggests the lineages alone will not bring a test-fast run
  that selects most of the suite (about 1.5 × the full suite) under 90 s. Narrow
  selections should come in under it. If the median stays over the limit after this
  branch and atoms-eaadf0, the remaining routes are the user's decision:
  - the shared broad-test policy (`sci-6af05a`), under which test-fast is no longer a
    routine obligation;
  - a reviewed limit exception in ops' `latency.toml`.
- **sci-56d9ce** (two tests that fail only under the parallel suite) stays a separate
  task.

## 5. Task linkage

`sci-0bea23` links this spec. Its plan follows review.
