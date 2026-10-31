Reviewer: fresh general-purpose subagent, model claude-opus-5-5 (scoped re-review of e2a5236)

**Scoped re-review of e2a5236: "fix(snapshot): rebuild an unrecorded link over what a failed attempt left"**

Reviewer: Claude Code subagent, model `claude-opus-5-5`.

**Verdict: resolved.** Both findings are fixed. The removal cannot delete a world in use under any name the repository declares today. It adds no silent fallback, and both new tests fail without the fix.

### Evidence
- I ran `just test-one tests/test_snapshot.py` in the worktree: 24 passed in 39.54 s.
- RED check: I loaded the parent commit's `snapshot.py` (`e2a5236^`) from a scratch copy and ran the same two scenarios against it. The worktree was not touched.
  - Finding 1 scenario: a root build fails, then the root is requested again. The parent module raised `FileExistsError: …/<root>` at `work.mkdir()`.
  - Finding 2 scenario: a partial `<mid>.image` is left on disk, then `mid` is requested. The parent module raised `FileExistsError: …/<mid>.image` at `copytree`.
  - The new tests drive these exact two paths, so both would fail without the fix. `test_a_failed_root_build_is_retried_from_an_empty_directory` also asserts inside `build` that each attempt starts with an empty directory, which proves the leftover was cleared and not merely tolerated.

### Can the removal delete something in use?
Not with any name declared today.
- **Only unrecorded names reach the removal.** `_build_link` runs only for links where `link.name not in _SNAPSHOTS` (`snapshot.py:169-171`). `_SNAPSHOTS` is never cleared or monkeypatched anywhere under `tests/` (grep).
- **An unrecorded root has no descendants and no live world.** A `Derived` link needs its root recorded first (`_SNAPSHOTS[declaration.base.name]`, `:147`). So when the root is unrecorded, nothing else in that lineage has been built, and no derived declaration's world can occupy the root's directory. A live world needs a `WorldSnapshot`, which exists only after recording, so `_LIVE` cannot hold that directory either.
- **The live-world check still runs first.** `materialize` calls `_refuse_another_live_world` (`:168`) before any `_build_link`, so a live world is refused before anything is removed.
- **No cross-process collision.** `certified_worker_work` is a fresh `uuid4` directory per worker process (`conftest.py:47-50`).
- **Eviction.** The root path goes through `_clear_tree`, not a bare `rmtree`. That evicts beliefs' `_forget_roots_under` and `_forget_worlds_under` entries for a corpus a half-finished build may have opened. It also refuses on a socket, with a message naming it.

### Silent fallback?
No.
- The original exception still reaches the test whose request triggered the build.
- A deterministic failure reappears with its real cause on every later request, where before it showed up as a `FileExistsError` that hid the cause. Each later request pays the rebuild cost again, which is correct.
- A leftover socket still fails loudly.
- This matches how a failed `Derived` step was already rebuilt from its base, and the prior review's Minor 1 explicitly allowed deleting the unrecorded directory.

### Critical
None.

### Important
None.

### Minor
1. **A name ending in `.image` turns the "never in use" claim into a deletion.** (Latent; no current name triggers it.)
   - **Where:** `python/tests/helpers/snapshot.py:138-143`, and the docstring at `:134-136`.
   - **The assumption:** every path under `work_base` belongs to exactly one name. Lineage directories are `<root name>` and images are `<name>.image`, so the two sets can collide.
   - **Scenario A:** declaration `a` is recorded and a `Root("a.image", …)` is requested. Before this commit, `work.mkdir()` raised `FileExistsError`. Now `_clear_tree` deletes `a`'s recorded image and builds the root into it. `_SNAPSHOTS["a"].image` then holds the root's world, a silently corrupted snapshot.
   - **Scenario B:** an unrecorded `Derived("x", …)` is requested while a `Root("x.image")` lineage is recorded, or even live. `rmtree(image)` at `:140` removes that lineage directory.
   - **Scope:** no current name ends in `.image` (commons-1a-…/1b-…, `snapshot-check`, `walked-confined`, `shared-with-evidence`, `verify-rig`).
   - **Possible fix:** refuse names containing a `.` (or ending in `.image`) when a `Root` or `Derived` is constructed, or keep images in a separate subdirectory.
2. **The `_clear_tree` behaviour on the root path is untested.**
   - **Where:** `python/tests/test_snapshot.py:289-304`.
   - **The gap:** replacing `_clear_tree(work)` at `snapshot.py:143` with a bare `shutil.rmtree(work)` would still pass both new tests. Nothing pins either:
     - the registry eviction for a corpus a failed root build opened (the `CollisionRefused` hazard described in `test_the_same_write_succeeds_after_every_restore`);
     - the socket refusal on a root rebuild.
   - **Why it matters:** the eviction is the part of the fix that makes a retried real commons root build succeed, not just make a directory.
3. **The refusal message names the wrong operation on a root rebuild.**
   - **Where:** `python/tests/helpers/snapshot.py:45`.
   - **What happens:** when a failed root build leaves a socket behind, the retry raises "a live socket under the world blocks the restore", but no restore is in progress. The message still lists the socket paths, so the cause is findable.
   - **Fix:** make the message neutral, e.g. "blocks clearing <target>".

Prior Minor 2 (a name repeated inside one unbuilt chain) and Minor 4 are outside this commit and still stand. Neither interacts with the new removal: a repeated name is skipped by the `not in _SNAPSHOTS` check, so it never reaches `_build_link` a second time.

Scratch files for the RED check are in `/mnt/ssd3/tmp/claude-1000/-mnt-ssd-Dropbox-science/e1c106c7-398b-4f30-8ca8-d851dbb5e76b/scratchpad/red/`.
