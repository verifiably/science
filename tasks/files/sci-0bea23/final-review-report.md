Reviewer: fresh general-purpose subagent, model claude-opus-5-5 (final whole-branch review, c701049..09367a9)

## Final whole-branch review: snapshot lineages (c701049..09367a9)

**Reviewer:** Claude Opus 5.5 (`claude-opus-5-5`), read-only. I reviewed in one pass: the spec, the plan, the ledger, the code diff for the five named files, the old `snapshot.py` and `commons.py` at c701049, and every caller of `snapshot()`, `materialize()` and `getfixturevalue`. I ran one check: `just test-one tests/test_snapshot.py`, which gave **22 passed in 39.77s**. I did not review the task-record churn under `tasks/`.

### Strengths
- **`_build_link` records nothing until the image is complete** (`python/tests/helpers/snapshot.py:128-142`). `check_value` runs before the image copy, and `_SNAPSHOTS` is written only after `copytree` succeeds. A failed step or a rejected value never leaves a recorded link or an image that later code uses.
- **The guard runs before anything is touched.** In `materialize` (`snapshot.py:149-157`), the identity check for the requested declaration and every ancestor, and then the live-world guard, both run before any build or restore. No code path lets a lazy construction overwrite a live world: a live world implies its declaration and all its ancestors are built, so any request for a different declaration in that lineage is refused first.
- **The three kinds of restore are separated cleanly.** `restore_tree` records nothing, and `commons.restore` now calls it directly (`commons.py:511-514`). Only `WorldSnapshot.restore()` touches `_LIVE`.
- **The step conversion is faithful.** I compared every declaration's base with the base its old builder called directly. All 30 match, including `CONTENT_CONFLICT`/`UID_CORRUPTION`/`SPEC_ONLY`/`PUBLISHED_B_UNKEPT` → `REOPENED`, `PUBLISHED_B` → `DERIVED`, `LATE_CHAIN` → `OVERLAPPING_UNKEPT`, `LATE_CHAIN_UNADOPTED` → `BOUND`, and `EQUAL_HOLDERS`/`SPEC_DROP` → `VERIFIED`. The only lines removed from the step bodies are the `value = base(work)` openings. The remotes' bare repositories, the data directory and the sharing roots all live under the lineage directory, so a construction restore resets them as well. Nothing shared escapes the restore.
- **`copy_value` everywhere a fixture hands out a value** closes a real bug the old code had: `fresh_value` and `uid_corruption` handed out the cached dict itself.
- **The unit tests use toy declarations with uuid names**, so other tests' `_SNAPSHOTS` state cannot satisfy them. They cover cold builds, construction over a dirtied directory, both halves of the guard, impostor ancestors, a failed step and a socket.

### Review Focus, item by item
1. **Step raises partway.** This holds for `Derived`. The retry calls `restore_tree(base.image, work)`, which deletes and replaces the half-built directory, and the step runs again. `test_a_failed_step_is_rebuilt_from_its_base` proves both that nothing is recorded and that no image is left. Roots behave differently (Minor 1).
2. **Live socket left in the lineage.** This holds. `restore_tree` scans the target and `short_socket(target)` before `rmtree`, and raises with the socket list in the message. `test_a_socket_in_the_lineage_refuses_construction` pins it.
3. **Tuple values.** This holds. Only an exact `tuple` is rebuilt (`snapshot.py:113-114`) and its members are copied recursively. In `step_late_link`, `value["b"] = …` therefore changes the copy's inner dict, not the cached `LATE_CHAIN` value. A namedtuple passes `check_value` but is refused by `copy_value`; the spec chose that.
4. **One name under two declarations.** This holds in both directions:
   - `snapshot()` first, then a module-level declaration;
   - a module-level declaration first, then `snapshot()`;
   - an impostor reached as an ancestor (`test_a_descendant_of_an_impostor_ancestor_is_refused`).

   The one gap is a name repeated inside a single unbuilt chain (Minor 2).
5. **`getfixturevalue` mid-test.** This holds. All ten dynamic requests (`test_cmd_show.py:178,192,203,330`, `test_cmd_adopt.py:484,495,504,527,621`, `test_publish_ownership.py:177`) are the first statement of a test that takes no other commons fixture, so there is one snapshot per test. The autouse clear is torn down after a dynamically requested fixture, so it still runs.

### Issues

#### Critical
None.

#### Important
None.

#### Minor
1. **A failed root build is not retried; it fails with `FileExistsError`, and now every commons fixture on the worker is affected.**
   - **Where:** `python/tests/helpers/snapshot.py:132-134`.
   - **What happens:** if `build_fresh` raises partway (or the root's image copy fails), `work_base/commons-1a-fresh` remains on disk and is not recorded. The next request on that worker runs `work.mkdir()` and raises `FileExistsError`, which hides the original cause.
   - **What changed:** the old code had the same `mkdir` behaviour, but only for that one name. Now all ~30 commons declarations share one root, so every later commons test on the worker fails with an error that does not name the cause.
   - **Fix:** fail explicitly with a message naming the leftover directory and the earlier failure, or delete the unrecorded root directory before `mkdir`. Since nothing is recorded, the deletion is not a silent fallback.
2. **A name repeated inside one unbuilt chain is reused silently.**
   - **Where:** `snapshot.py:158-160`.
   - **What happens:** take `Derived("x", base=Derived("x", …))`. The identity walk passes because neither link is built. The loop builds the inner `"x"`, then skips the outer one because `link.name in _SNAPSHOTS`, and returns the inner world for the outer request.
   - **Scope:** no current declaration does this, so it is a latent hole in Focus 4's rule.
   - **Fix:** while walking the chain, raise `ValueError` on a name that appears twice.
3. **A partial image left by a failed image copy blocks the retry with an unhelpful error.**
   - **Where:** `snapshot.py:140`.
   - **What happens:** a step leaves a socket or FIFO, or the disk fills, and `copytree(work, image)` raises after writing part of `X.image`. If the socket is still there, the retry's construction restore refuses and names it, which is good. If it has since been removed, the retry rebuilds the step and then fails on `copytree` with `FileExistsError: …/X.image`, which names neither cause.
   - **Not harmful:** the partial image is never used, because nothing was recorded. This behaviour predates the branch.
   - **Fix:** copy to a temporary sibling and rename it into place, or refuse with a message naming the leftover image.
4. **Double copy in `conflicting_publication`.**
   - **Where:** `python/tests/conftest.py`, in the `conflicting_publication` fixture.
   - **What:** it calls `copy_value(snap.value)` twice in one return expression. This is harmless because `corpus_id` is a str, but it is inconsistent with `content_conflict` and `uid_corruption` in `test_cmd_adopt.py:412-424`, which copy once into `value`.

### Other things checked; no finding
- **Order dependence through `_SNAPSHOTS`/`_LIVE`.** None found. `_LIVE` is cleared after every test, by an autouse fixture that is set up before any restoring fixture. A construction always starts from the base's image with a copied value, and evicts beliefs' registries. `src/` has no path-keyed caches (I grepped for `lru_cache`, `cache` and module dicts). One path-keyed state remains: `STORE_IDS[lineage/c]`, written by both `step_uid_corruption` and `test_commons_1b.py:331`. Spec §2.6 already accepts this, and no current reader exists.
- **Patching active during an ancestor's build.** No fixture patches at setup ahead of a commons fixture, and every `getfixturevalue` call comes before any `monkeypatch` use. So an ancestor built in the middle of a test is not built under that test's patches. If a future test called `getfixturevalue` after a `monkeypatch.setattr`, the patched build would now taint the cached images of shared ancestors, not one name. Worth knowing, but not a defect today.
- **The guard refusing a legitimate pattern.** The only pattern it refuses is two different declarations of one lineage in a single test, and that is the design. The full suite passing with the guard in place (1155, per the ledger) shows no test does this. `snapshot()` roots each have their own directory and are unaffected.
- **Hard-coded snapshot directory names in tests** (`"commons-1…"` outside the declarations): none.

### Ledger rulings
- **Task 1 root-lambda index typo:** accepted.
- **Task 1 commit over the load-sensitive selection-deadline failure (sci-26ba4d):** accepted. It is unrelated to snapshots and passes when run alone.
- **Task 2 `step_<x>` naming:** accepted.
- **Task 3 quiet re-measurement after the contaminated 1196 s run:** accepted. The ledger also records directly that each link was built at most once per worker, which is the property the threshold stands in for. Both runs are reported. The quiet run (937 s) passes the threshold, though by a smaller margin than the 845 s projection.

### Recommendations
- Fix Minors 1 and 2 together: about five lines in `materialize`/`_build_link` that make the root's failure path and the name-uniqueness rule explicit.
- Optionally, add one sentence to `snapshot.py` or the conftest fixture comment saying that a lazy build runs under whatever the requesting test has patched so far.

### Declined to judge
- Reproducing the suite and build-time measurements (165 s → 136–145 s; 1591 s → 937 s). I relied on the ledger and did not rerun the full suite.
- testmon's lower selection precision (spec §2.6). The spec accepts it; the trade-off is a design choice, not an implementation defect.
- Whether test-fast will clear the 90 s limit. Spec §4 leaves that to `tt-latency verify` after merge.
- sci-56d9ce's parallel-only failures and sci-26ba4d's load-sensitive deadline test: tracked elsewhere.
- Task-record churn under `tasks/` and the spec and plan prose. I did not review them as code.
- The timing plugin's correctness. It is not committed, so I could not inspect it; its results live in the task attachments.

### Assessment
**Ready to merge:** Yes. The Minors are optional.

**Reasoning:** The implementation matches the spec and plan closely, and the step conversion matches the old builders' bases exactly. All five Review Focus items hold, with the edges noted in Minors 1 and 2: a failed root build is not retried, and a name repeated inside one chain slips past the identity rule. Every finding is an unhelpful error message or a contrived-input hole; none produces a wrong world silently in the current suite.
