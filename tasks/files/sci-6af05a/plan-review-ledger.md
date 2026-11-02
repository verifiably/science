# Plan Review Ledger

## Round 1 — User / External Review (e0ba174bd04bc7f2638529ecbadb9e4ca80560ce -> d32cbf1ae6a0613c48d93d6ec900a334d34a78a0)

- Reviewer: claude-code/claude-opus-5-5
- Verdict: revise
- Findings: 4 important, 4 minor

### Rulings

1. **Important 1 — Add a dedicated whole-branch final review task before merging Phase 1 to `main`, and a scoped review before merging the activation commit.**
   - Ruling: accepted and fixed in `d32cbf1ae6a0613c48d93d6ec900a334d34a78a0` (Task 5 added for whole-branch final review and Phase 1 integration; Task 7 Step 4 adds scoped review of the activation commit before merging to `main`).
   - Why: Global rules require a whole-branch final review (up to 5 rounds) and a base-branch movement check before integrating into `main`.
   - Cost: One fresh review subagent pass before Phase 1 integration and one scoped review pass before activation integration.
2. **Important 2 — `main` moved to `dc39b31` (`chore(tools): vendor tt version 10`), making the `tt v9` constraint stale and blocking `git merge --ff-only`.**
   - Ruling: accepted and fixed in `d32cbf1ae6a0613c48d93d6ec900a334d34a78a0` (merged `main` `dc39b31` into `feat/sci-6af05a-test-policy`, updated Spec §2.1 and Plan Global Constraints to reference the `tt` version `main` carries [currently v10], and added explicit `git rev-list --left-right --count main...HEAD` + `git merge --no-edit main` steps in Task 5 Step 1 and Task 7 Step 4).
   - Why: Merging `main` into the worktree branch keeps `feat/sci-6af05a-test-policy` a descendant of `main` so `git merge --ff-only` succeeds at integration.
   - Cost: None.
3. **Important 3 — Task 2's `test_uncertified_host.py` imported `ExecutionError` from `beliefs.errors` instead of `nodes.core.errors`.**
   - Ruling: accepted and fixed in `d32cbf1ae6a0613c48d93d6ec900a334d34a78a0` (Task 2 Step 1 now imports `from nodes.core.errors import ExecutionError`, matching `beliefs/python/src/beliefs/root.py:129`).
   - Why: `ExecutionError` is defined in `nodes.core.errors`; importing from `beliefs.errors` would fail with `ImportError` even after `uncertified_host.py` is implemented.
   - Cost: None.
4. **Important 4 — Make Task 7's forced-failure post-activation check exercise a forced broad target rather than `test-one -k nonexistent`.**
   - Ruling: accepted and fixed in `d32cbf1ae6a0613c48d93d6ec900a334d34a78a0` (Task 7 Step 5.3 writes an untracked failing test file `.worktrees/sci-6af05a/python/tests/test_forced_failure_probe.py`, runs `TT_FORCE=1 just test-fast`, verifies a nonzero exit code and a recorded `test-fast` row with `execution == "ran"`, `execution_reason == "forced"`, and `exit != 0`, and removes the probe file).
   - Why: `test-one` is a protected target; testing `TT_FORCE=1 just test-fast` against a real failing test proves that forcing a disabled broad target runs the suite and propagates test failures.
   - Cost: One deliberate failing `test-fast` run in the worktree during post-activation verification.
5. **Minor 5 — Task 7 Step 6 worktree removal must run `tt-report` first, attach the plan review ledger, and checkpoint retained/ignored items.**
   - Ruling: accepted and fixed in `d32cbf1ae6a0613c48d93d6ec900a334d34a78a0` (Task 7 Step 6 runs `tt-report`, attaches `plan-review-ledger.md`, verifies `tasks show sci-6af05a`, gives explicit dispositions to `git status --ignored --porcelain`, and checks host pointers before unlocking and removing `.worktrees/sci-6af05a`).
   - Why: Required by the worktree removal rule.
   - Cost: None.
6. **Minor 6 — Task 7 Activation Packet should state explicitly which pushes its approval covers.**
   - Ruling: accepted and fixed in `d32cbf1ae6a0613c48d93d6ec900a334d34a78a0` (Task 7 Step 1 lists both the activation commit push to `origin/main` and the final task-closure/lifecycle-note commit push to `origin/main`).
   - Why: Avoids ambiguity over whether a second push approval is needed for the final task record commit.
   - Cost: None.
7. **Minor 7 — Replace hardcoded post-implementation test count guesses (`1209 passed`, `~546 passed`, `skipped == 663`) with relative invariants.**
   - Ruling: accepted and fixed in `d32cbf1ae6a0613c48d93d6ec900a334d34a78a0` (Task 5 Step 1 and Task 6 Step 2 now require `0 failed, 0 errors`, `passed == baseline (1195) + new tests` locally and `executed >= pilot (532) + new tests` on hosted CI, comparing `skipped` against the 663 pilot count and verifying allowed skip prefixes).
   - Why: Parametrized test additions in `test_front_door.py` and `test_uncertified_host.py` determine the exact delta above 1,195 / 532.
   - Cost: None.
8. **Minor 8 — Attach hosted CI `module-inventory.txt` and a `pytest.xml` count summary to `sci-6af05a` before deleting `/tmp/sci-6af05a-ci-artifacts`.**
   - Ruling: accepted and fixed in `d32cbf1ae6a0613c48d93d6ec900a334d34a78a0` (Task 6 Step 2 attaches `ci-module-inventory.txt` and `ci-junit-summary.md` via `tasks attach` before removing the temporary download directory).
   - Why: Preserves durable evidence on the task record for the Activation Packet and 30-day evaluation.
   - Cost: Two small text attachments on `sci-6af05a`.

### Minor (deferred)

- None.
