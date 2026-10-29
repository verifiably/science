What this change does: Task 13 connects adoption’s retirement sweep and recovery path to the shipped kernel door. It also updates `show` and the connected fixtures for actual retirement.

**Spec verdict: compliant within Task 13’s assigned scope. Task quality: Approved.** No Critical, Important, or Minor findings. The controller can accept sci-9c0bba and continue Tasks 14–15; this does not approve integration of the retirement tail.

Checked the complete supplied diff once against base `02f784e5eba56194b22cc166d9f5c69d74928ee4` and head `bb1fad59b28dc48d76da891133d80a92d76fe2bd`. The worktree’s later commits contain no Python changes relative to that head, and its working tree was clean.

The main strengths are:

- `.worktrees/commons-1b/python/src/science/commands/adopt.py:207` passes the registry root, retained head-artifact observers, and existing pin evidence to `ScopedWriter.retire`. It projects the returned line only after the kernel has appended it.
- `.worktrees/commons-1b/python/src/science/commands/adopt.py:104` limits reconciliation to completed terminal effects, excludes departed corpora from the door, and converts retirement refusals into a Finding naming the corpus.
- `.worktrees/commons-1b/python/src/science/commands/adopt.py:167` performs new retirement after candidate admission and mounting. It checks configuration currency immediately before each new retirement.
- Live holders are reopened before each predecessor evaluation. I traced `live_mounts` and `required`: an earlier retirement cannot remain an equal-content holder or attribution source merely because the sweep’s original group snapshot still says `mounted`.
- The handler returns informational commentary. The dispatcher still builds every pin block from ledger lines before appending that commentary. The active two-retirement test drains cursor pages before checking this ordering.
- `.worktrees/commons-1b/python/src/science/commands/show.py:129` gives the usable pending remedy, with a regression checking that `show` leaves the pin, kernel status, and sharing ledger unchanged.

I independently assessed the retired-target distinction. After reconciliation retires the requested pin, `.worktrees/commons-1b/python/src/science/commands/adopt.py:55` refuses that target even though recovery lines persist. I accept this under Task 8’s explicit preservation of existing target-state behavior, together with the prohibition on re-adopting retired publications. The mounted-target recovery exception still works when the requested pin remains mounted. This is a recovery-evidence guarantee, not a guarantee that every recovery invocation returns success commentary.

I read the brief, binding constraints, implementation report, design §§5.7–5.8, amended kernel interface, changed tests, and surrounding code needed to check live-holder freshness, replay folding, target-state precedence, report ordering, and fixture reopening. No new command, adapter change, registry schema, or dependency was introduced.

Verification evidence inspected: the focused log reports **7 passed**, and the affected fast-check log reports **87 passed**. I did not rerun these checks or a broader suite, as instructed.

Reviewer identity: **codex/gpt-6.1-sol**, returned by a fresh identity command.

No files, task notes, or git state were changed; no processes were left running. Branch `commons-1b` remains unmerged at `.worktrees/commons-1b`, with the controller owning Tasks 14–15 and subsequent review.

Skipped the separate Task 14 safety gates and Task 15 prose work. Retirement remains irreversible, so the tail must remain unmerged until those gates and the phase review pass.
