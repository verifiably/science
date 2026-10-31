# Snapshot lineages: build each commons world once from its base, not from scratch

Status: implemented 2026-10-31 on perf/test-latency; latency verify pending. Revision 3 (answers spec review rounds 1 and 2: §2 rewritten, §2.6 added). Task `sci-0bea23` (test-latency halt).

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
declaration, and a derived declaration holds its base declaration itself, not its
base's name:

- **`Root(name, build)`.** `build(work) -> value`, built in `work_base / name`.
- **`Derived(name, base, step)`.** `base` is a `Root` or `Derived` object, and
  `step(work, value) -> value`. It builds in its root's directory, which every
  declaration in the lineage shares, and `work` is always that directory.

**Lineage directory.** The root's directory, `work_base / <root name>`. Builders rely on
`work` being that directory: `build_verified` calls `fixture_bundle(work / "a")`, and
`build_uid_corruption` calls `build_installation(work, "c")`.

**The step's input.** A copy (§2.2) of the base's value, whatever its shape: a dict for
most links, and a tuple for `late_chain`, which `late_link` unpacks as
`value, _, missing, last`. Its result is checked by `check_value`, like any snapshot's
value.

`materialize(work_base, declaration)` returns the built `WorldSnapshot`. For a `Derived`
declaration it walks up `base` to the nearest ancestor already built in this process,
or to the root, and builds each missing link downwards. For each link it:

1. restores the base's image into the lineage directory (a construction restore,
   §2.3);
2. runs `step(work, copy_value(base.value))`;
3. runs `check_value` on the result;
4. saves the image as `work_base / f"{name}.image"`.

`WorldSnapshot` becomes `(work, image, value, declaration)`. Here `work` is the lineage
directory, and `declaration` takes the place of today's `build` field.

**Identity**, per kind of declaration:

- **Module-level declarations** (the commons chain, §2.4) compare by object identity.
  Each is made exactly once, at import, and `_SNAPSHOTS` keeps the declaration each
  name was built from. A request carrying a different declaration object under a
  built name raises.
- **`snapshot(work_base, name, build)`** stays the call for the single-level roots
  that several modules share (`shared-with-evidence`, `verify-rig`, `snapshot-check`).
  It memoizes one `Root(name, build)` per name. A later call with the same `build`
  gets the same `Root`, and a call with a different `build` raises, which is today's
  rule. So repeated calls never manufacture distinct declarations.

The cost of a snapshot on a worker becomes its own step, plus each ancestor step that
worker has not yet built. The cost of the whole prefix is no longer paid again.

### 2.2 Copying a value: rebuild the containers, share the leaves

A step must never change its base's cached value, and the base's value holds
`ScienceConfig` objects. `copy.deepcopy` cannot copy those: their compiled
`ProfileSpec` holds `mappingproxy` views, and deepcopy raises
`TypeError: cannot pickle 'mappingproxy' object`.

`copy_value(value)` therefore follows the shapes `check_value` admits (2026-10-02
§2.4a):

- it rebuilds every value whose type is exactly `dict`, `list` or `tuple`, and raises
  on a subclass, such as a namedtuple, rather than changing its type. No current value
  holds one;
- it returns every leaf (`ScienceConfig`, `Path`, `str`, `int`, `bool`, `None`) as the
  same object. These leaves are immutable: `ScienceConfig` is a frozen dataclass,
  trusted whole as `check_value` already trusts it.

A step that changes an installation replaces the leaf (`value["a"] = reopen(value["a"])`)
rather than mutating it, which the frozen dataclass enforces.

Fixtures hand tests `copy_value(snap.value)`, never the cached container. Today
`fresh_value` and `test_cmd_adopt.py`'s `uid_corruption` hand over the cached dict
itself. Under lineages, a test that mutated a root's cached value would corrupt every
descendant built after it on that worker.

### 2.3 Three kinds of restore, kept apart

Snapshots in one lineage now share a directory, so a test that used two of them would
silently get the second over the first. No test uses two snapshots at all today. This
was checked by scanning every test and fixture signature, plus every
`getfixturevalue` call: the `test_cmd_provider.py` case that looked like one
parametrizes `world` as an argument, not a fixture.

All three kinds go through one plain function, `restore_tree(image, target)`:

- it refuses a live socket under `target`;
- it evicts beliefs' registries for `target`;
- it replaces `target` with a copy of `image`.

It records nothing.

- **Construction restore.** Inside `materialize`: `restore_tree(base.image, lineage)`
  before each step.
- **Step-internal restore.** A step's own save-and-restore of a subdirectory.
  `_build_sibling_publications` forks A's home and later puts it back. The `fork` and
  `restore` helpers in `commons.py` call `restore_tree(copy, home)` directly and no
  longer build a `WorldSnapshot`.
- **Live restore.** `WorldSnapshot.restore()`, called by a fixture or test to use a world.
  It calls `restore_tree(self.image, self.work)`, then records
  `self.work → self.declaration` in a per-test live record. Keys are lineage
  directories compared by path equality, never by containment. An autouse fixture in
  `conftest.py` clears that record at teardown.

**The guard.** `materialize` checks the live record before any build or restore. If
the lineage directory is already recorded under a different declaration in this test,
it raises, naming both, and leaves the directory and the image set untouched. Without
that check, a lazy build would replace the live world before any restore could
object. `WorldSnapshot.restore()` makes the same check before restoring. Requesting
and restoring the same declaration again within one test is allowed.

### 2.4 The builders that become steps

Each commons chain builder opens by building its base: `value = build_<base>(work)` in
the 1a builders, `value = base(work)` in the kept/unkept helpers, and
`value, _, missing, last = build_late_chain(work)` in `build_late_link`. Each becomes a
module-level `Derived` declaration:

- its step is the code after that opening, receiving the base's value as described
  in §2.1;
- its base is the declaration of the builder it called.

**Roots.** `build_fresh` and `build_fresh_no_epoch`.

**Shared steps.** A shared helper becomes one step function in several declarations
with different bases:

- the kept/unkept pairs;
- `_build_late_chain`, under `late_chain` (base `overlapping_unkept`) and
  `late_chain_unadopted` (base `bound`).

**Covered:**

- every snapshot builder in `tests/helpers/commons.py`: the chain from `build_published`
  to `build_b_updated*` and `build_sibling_publications*`, plus `build_conflicting`,
  `build_content_conflict`, `build_uid_corruption`, `build_late_*`,
  `build_equal_holders`, `build_spec_drop` and `build_spec_only`;
- `build_bound_fetched_only` in `tests/test_cmd_adopt.py`, which calls
  `build_bound(work)` directly today. It becomes a `Derived` declaration on the `bound`
  declaration, in that module.

**Not covered.** `build_installation(work, name, *, hold_vocabulary)` is not a snapshot
builder: test bodies call it directly, and it stays as it is.

The fixtures in `conftest.py` and the three direct `snapshot()` calls in
`test_cmd_adopt.py` call `materialize` with the declaration. No test calls a chain
builder outside `snapshot()` (checked 2026-10-31), so no composite full-chain builder
is kept.

**Other snapshots stay on `snapshot(work_base, name, build)` unchanged:**

- `walked-confined`, `walked-portable`, `shared-with-evidence`, `verify-rig`,
  `spec-rig`, `snapshot-check`, `two-corpus` and `two-corpus-walked`.
- `two-corpus-walked` is itself two levels deep: its builder calls the `two-corpus`
  builder. Converting it is possible, but it is left out of this branch because its
  measured cost is 19 s across one build.

### 2.5 Acceptance

**Measurement.** The snapshot timing plugin, adapted to `materialize`, reruns the
full suite on the same host, and the plan records the totals beside the 2026-10-31
baseline:

- Projection from the baseline's per-worker build sets: total build time 1,591 s →
  about 845 s, worst worker 149 s → about 95 s.
- Threshold: a total above 1,000 s means the lineages did not remove the duplicated
  prefixes as designed. The implementation stops and reports instead of merging.
- `test-fast` is measured too: one run with a fresh testmon data file (every test
  selected) and one after touching a single test module. Both run before and after,
  on the same host, through `just test-fast` with `TESTMON_DATAFILE` pointed at
  scratch. These figures inform the closure route in §4. The halt's own gate is
  `tt-latency verify`.

**Isolation.** Under worksteal, an ancestor built early and a test that dirtied the
lineage directory since then happen in a nondeterministic order. As 2026-10-02 §4.2
required for its modules, each of these modules passes run serially and with its
test ids reversed:

- `test_commons_1a.py`;
- `test_commons_1b.py`;
- `test_cmd_adopt.py`;
- `test_cmd_show.py`;
- `test_publish_ownership.py`.

All five use `just test-one`, alone and in one combined run.

**Unit cases.** `test_snapshot.py` gains these cases. Each uses declarations of its own,
so `_SNAPSHOTS` state from other tests cannot satisfy them:

- **Cold deep descendant.** In a process with none of its ancestors built, requesting
  a declaration three links deep first builds every ancestor once, in order. A later
  request for an ancestor reuses its image without building it again.
- **Construction from a dirtied directory.** After a live restore of the base, the
  test writes and deletes files in the lineage directory. A request for a derived
  declaration (in a fresh test, after the live record is cleared) then builds from
  the base's image. Its step sees exactly the base's files.
- **Construction restores record nothing.** The fixture's live restore that follows a
  lazy build succeeds.
- **Step-internal restores record nothing.** A step that forks and restores a
  subdirectory leaves the live record empty.
- **Copy.** `copy_value` on a real commons value (with `ScienceConfig` leaves)
  succeeds. A step that rebinds or mutates containers in its copy leaves the base's
  cached value equal to what it was. A namedtuple raises.
- **Identity.**
  - A different declaration object under a built name raises.
  - Two `snapshot()` calls with the same name and builder share one `Root`; a
    different builder raises.
- **Live-world refusal, request half.** After a live restore of one declaration,
  requesting another from the same lineage raises before building anything. The
  lineage directory's file manifest and the set of images are byte-for-byte
  unchanged.
- **Live-world refusal, restore half.** After a live restore of one declaration,
  `restore()` of another declaration of the same lineage that is already built
  raises. The directory is unchanged.

### 2.6 Limitations

- **One directory for a whole lineage.** Different snapshots of a lineage now share
  absolute paths, so per-process state keyed by path can outlive a restore that
  swaps one snapshot's files for another's:
  - `STORE_IDS[lineage/c]` is written both by `build_uid_corruption` and by the
    `test_commons_1b.py` test that calls `build_installation(…, "c")`. No current
    caller of `hold_fixture_dataset` reads `c`.
  - A test that leaves a live socket under the lineage directory now blocks every
    later construction in that lineage on its worker, not one snapshot. The refusal
    names the socket.
- **Lower testmon precision.** testmon attributes a fixture's setup coverage to the test
  that ran it. An ancestor's step now runs only in the first test on each worker that
  needs it, so later descendants record no dependency on that step's code or the
  production code it exercises, and a change there selects fewer tests. Reused
  snapshots already had this gap, and the full suite at pre-push still covers it.
  The lineages widen it for test-fast.

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
