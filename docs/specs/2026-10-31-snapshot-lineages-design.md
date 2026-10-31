# Snapshot lineages: build each commons world once from its base, not from scratch

Status: draft for review, 2026-10-31. Task `sci-0bea23` (test-latency halt).

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

### 2.1 A snapshot may derive from a base snapshot in the same lineage directory

A world records its absolute path (2026-10-02 §2.1), so an image cannot be restored
anywhere but the directory it was built in. A derived snapshot therefore builds in its
base's directory:

- **Root snapshot.** Unchanged: `snapshot(work_base, name, build)` builds in
  `work_base / name`.
- **Derived snapshot.** `snapshot(work_base, name, step, base=<base name>)`. Its
  directory is its root's directory. To build it, `snapshot()` first makes sure the
  base exists, then restores the base's image into the shared directory, then runs
  `step(work, value)` on a deep copy of the base's value. The image is saved as
  `work_base / f"{name}.image"`.
- **Restore.** Unchanged: a derived snapshot's restore replaces the shared directory
  with its own image.

The cost of a snapshot on a worker becomes its own step, plus each ancestor step that
worker has not yet built. The cost of the whole prefix is no longer paid again.

The `base` argument names a snapshot rather than a builder function. A name stays one
identity (2026-10-02 §2.3): asking for a name with a different step or base raises, as
a different builder does today.

### 2.2 The commons builders become steps

Each `build_X` in `tests/helpers/commons.py` that starts with `value = build_<base>(work)`
splits in two:

- the step: the code after that line, taking `(work, value)`;
- the base name.

The shared `_build_X(work, *, base=…)` helpers keep their kept/unkept pairs as two
registrations of the same step with different bases. Fixtures in `conftest.py` and the
three direct `snapshot()` calls in `test_cmd_adopt.py` pass the base name. No test calls
a commons builder outside `snapshot()` (checked 2026-10-31), so no composite full-chain
builder is kept.

Builders that already copy in-process values (`{**value, "b": b}`, `value["a"] = reopen(…)`)
receive their own deep copy, so a step can never change its base's cached value.

The other lineages are independent roots with a single level, and they stay as they are:
`walked-*`, `shared-with-evidence`, `verify-rig`, `spec-rig`, `two-corpus-walked`, `rig`,
`world`, `shared` and `two_corpora`.

### 2.3 One live snapshot per lineage per test, enforced

Snapshots in one lineage now share a directory, so a test that restored two of them would
silently get the second over the first. No test requests two snapshot fixtures from one
lineage today. The only multi-snapshot tests are three `test_cmd_provider.py` cases that
use `published` and `world`, which are different roots. `restore()` records the name it
restored per lineage directory, and an autouse fixture clears that record between tests.
A second restore of a different name in the same directory within one test raises,
naming both snapshots.

### 2.4 Acceptance by measurement

- The suite passes. The snapshot timing plugin reruns on the same host, and the plan
  records its totals beside the 2026-10-31 baseline. The projection from that baseline's
  per-worker build sets: total build time 1,591 s → about 845 s, worst worker
  149 s → about 95 s.
- `test_snapshot.py` gains derived-snapshot cases:
  - a derived build restores its base's image first;
  - a step mutating its value does not reach the base's cached value;
  - a name re-registered with another base raises;
  - two restores from one lineage in one test raise.

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
