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

## Round 2 — User / External Review (d32cbf1ae6a0613c48d93d6ec900a334d34a78a0)

- Reviewer: claude-code/claude-opus-5-5
- Verdict: accept
- Findings: minor 3

### Rulings

1. **Minor 1 — Task 7 Step 6.2 `tasks attach sci-6af05a -` reads from stdin with nothing piped in; pass the ledger's actual file path.**
   - Ruling: accepted and updated in `docs/plans/2026-11-02-test-execution-policy.md` (Task 7 Step 6.2 now updates `tasks/files/sci-6af05a/plan-review-ledger.md` and runs `tasks attach sci-6af05a tasks/files/sci-6af05a/plan-review-ledger.md --name plan-review-ledger.md ...`).
   - Why: Avoids hanging or attaching an empty file when `tasks attach` runs at closure.
   - Cost: None.
2. **Minor 2 — Note in Task 5 Step 3 that if `git merge --ff-only` fails because another session committed to `main` between review and integration, merge `main` into the branch again, rerun `just check` and `just test-full`, and record the merge commit in the ledger.**
   - Ruling: accepted and updated in `docs/plans/2026-11-02-test-execution-policy.md` (Task 5 Step 3).
   - Why: Handles a concurrent advance on `main` during the review window without rebasing.
   - Cost: None.
3. **Minor 3 — Pin the `Spec:` header line in `docs/plans/2026-11-02-test-execution-policy.md` to the approved spec revision (`8cd98e827a9de0df9836a353349f2cfed23915a7`).**
   - Ruling: accepted and updated in `docs/plans/2026-11-02-test-execution-policy.md` (line 11).
   - Why: Keeps the plan's spec reference pinned to the approved revision.
   - Cost: None.

### Minor (deferred)

- None.

## Task 3 & Task 4 Execution Rulings

1. **Task 3 — `test_pre_commit_routes_docs_paths_only_when_every_staged_file_matches` appends `# changed` rather than overwriting `justfile`.**
   - Ruling: appended `\n# changed\n` to `target_file` in `python/tests/test_front_door.py` (`83a6d01`).
   - Why: Overwriting `justfile` deleted the recipes before `.githooks/pre-commit` invoked `just hook-pre-commit`.
   - Cost: None; appending stages a real modification to `justfile` while preserving its recipes.
2. **Task 4 — Place `README.md` sibling checkout and test-command note under `## Install` and avoid backticked non-local paths in `AGENTS.md`.**
   - Ruling: updated `## Install` in `README.md` and wrote sibling repo names (`beliefs`, `atoms`, `nodes`) and artifact names (`JUnit and module-inventory artifacts`) without path-style backticks in `AGENTS.md` (`1a0a94e`).
   - Why: `tools/family.toml` restricts top-level `README.md` headings to `["Install", "Usage", "Layout", "Documentation", "License"]`, and `python3 tools/ops-docs check` validates backticked path-like tokens in `AGENTS.md` as tracked local files.
   - Cost: None; all required content is preserved in `README.md` and `AGENTS.md` and passes `ops-docs check`.

## Phase 1 Whole-Branch Final Review (dc39b31716328fae9dcc633985eadb9888e0f85d..1a0a94e0ef186882ee51171d12eab3cc371402d9)

- Reviewer: antigravity/pro (session:84826be2-0d66-411f-85dd-134da839362f)
- Verdict: accept
- Findings: minor 3

### Rulings on Declined-to-Judge Items

1. **Activation of `.tt.toml` (`automatic_broad = false`) and widening of `ci_suite_refs := "refs/heads/*"`**
   - Ruling: stands as intentionally deferred to Task 7 after hosted CI verification in Task 6.
   - Why: Spec §7.1–§7.3 and Global Constraints forbid disabling automatic local broad runs before an approved hosted CI run finishes with a nonzero executed test count.
   - Cost: None; Phase 1 must land with local policy enabled.
2. **Local `main` commit lead in sibling repositories (`beliefs`, `atoms`, `nodes` ahead of `origin/main`)**
   - Ruling: stands as scoped to Task 6 Step 1 (Publication Packet).
   - Why: Pushing sibling repositories is an external side effect requiring explicit user approval in the Publication Packet.
   - Cost: None; nothing is pushed in Phase 1.
3. **Host-level SSH keepalive configuration in `~/.ssh/config`**
   - Ruling: stands as host-level configuration outside the repository tree.
   - Why: `.githooks/pre-push` probes `ssh -G` at runtime and refuses before running the gate when `ServerAliveInterval` is `0`.
   - Cost: None.

### Minor (deferred)

- `.github/workflows/ci.yml:80`: `Require coverage evidence` step omits `if: always()` (step 11 `Upload coverage evidence` still has `if: always()`, and omitting `if: always()` on step 10 avoids masking earlier setup/hygiene failures with `missing JUnit report`).
- `.github/workflows/ci.yml:72`: `module-inventory.txt` records the 4 repo SHAs and sorted `[test modules]` list without appending `cat pyproject.toml`.
- `python/tests/conftest.py:57-58`: Three blank lines instead of two after `pytest_runtest_teardown`.

## Task 6 Hosted CI Fix

1. **Task 6 — `AGENTS.md:40` backticked `ops` path under hosted CI without `~/.config/tasks/projects.toml`.**
   - Ruling: wrote `ops's 2026-10-29 test-execution-policy design` without backticks in `AGENTS.md` and added `test_live_ops_check_passes_without_tasks_registry` in `python/tests/test_front_door.py` (RED -> GREEN).
   - Why: On a GitHub Actions runner where `~/.config/tasks/projects.toml` is absent (`registry(env) == {}`), `tools/ops-check` resolves `ops \`docs/specs/2026-10-29-test-execution-policy-design.md\`` against `science` rather than `ops` and exits 1 (run `41447264420`).
   - Cost: None; matches how `beliefs/AGENTS.md` writes external design references without path backticks and adds a permanent regression test with `XDG_CONFIG_HOME` isolated.

## Task 7 Execution Rulings & Phase 3 Activation Review (353d2f1c7ceb45d58a56ba750d68e600101d9937..d124639a7fabf023c895537b5c377ae64712fae5)

- Reviewer: antigravity/pro (session:95cf17ec-3e2f-4fbb-a5e0-c00140d7a23a)
- Verdict: accept
- Findings: minor 1

### Task 7 Execution Rulings

1. **Task 7 — `test_unreadable_policy_refuses_push` tests both uncovered (`refs/tags/v1`) and covered (`refs/heads/main`) pushes under `ci_suite_refs := "refs/heads/*"`.**
   - Ruling: updated `test_unreadable_policy_refuses_push` in `python/tests/test_front_door.py` (`d124639`).
   - Why: Once `ci_suite_refs` is `"refs/heads/*"`, pushing `refs/heads/main` to `origin` routes to `hook-pre-push-fast` where `tt` exits 2 on invalid `.tt.toml`, whereas uncovered `refs/tags/v1` routes to `hook-pre-push` where `.githooks/pre-push`'s policy check exits 2 before `just`.
   - Cost: None; both refusal paths are asserted.
2. **Task 7 — `test_live_repository_policy_and_ci_suite_refs` omits non-JSON-serializable `'path'` `PosixPath` key from `tt.read_policy(root)` before `json.dumps`.**
   - Ruling: serialized `{k: v for k, v in policy.items() if k != 'path'}` in `python/tests/test_front_door.py` (`d124639`).
   - Why: `tt.read_policy` returns `{"path": PosixPath(...), "automatic_broad": ..., "broad_targets": ...}`.
   - Cost: None.

### Rulings on Declined-to-Judge Items

1. **Hosted GitHub Actions runner execution and artifact download verification performed in Task 6 (run `41448141023`)**
   - Ruling: stands as verified and attached in Task 6 (`ci-module-inventory.txt` and `ci-junit-summary.md`).
   - Why: Task 6 already verified the hosted CI run and attached both artifacts before Task 7 began.
   - Cost: None.
2. **Post-activation verification steps (Task 7 Step 5)**
   - Ruling: stands as the next step in Task 7 Step 5 immediately following integration of `d124639` to `main`.
   - Why: Post-activation verification tests the live integrated policy on `main` and `.worktrees/sci-6af05a`.
   - Cost: None.

### Minor (deferred)

- `python/tests/test_front_door.py:648-650`: File ends with trailing blank lines instead of a single trailing newline.




