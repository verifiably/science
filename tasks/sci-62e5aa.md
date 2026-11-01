---
id: sci-62e5aa
title: "Write dispatch: a kernel refusal after a published act closes refused and drops the act"
status: done
priority: 2
size: s
complexity: mid
process: direct
owner: fix/kernel-refusal-after-act
created: 2026-10-31T18:28:44Z
updated: 2026-11-01T02:16:59Z
started: 2026-11-01T01:56:13Z
completed: 2026-11-01T02:16:24Z
closed: 2026-11-01T02:16:24Z
depends: []
tags: [command-framework]
source: sci-eccb43
model: claude-opus-5-5
agent: claude-code/claude-opus-5-5
origin: agent
---

`Dispatcher._invoke_write` closes every KERNEL_REFUSALS exception through `_close_refused` without consulting `invocation_acts`, while a surface `Refused` after an act goes to `_close_acted` (done with the act pairs, HandlerContractViolation). A multi-act handler whose later act is refused by the kernel (e.g. `dataset`: the holdings observation publishes, then `writer.add` raises a WriteRefused) closes refused, so the outcome and its replay omit an act that committed. Decide the closing rule for kernel-refused-after-act (likely the `_close_acted` path, as `_invoke_sharing` already does for both refusal kinds) and test it through a real two-act handler. Found while fixing sci-eccb43.

## Notes

- 2026-10-31T18:28:44Z (add): created
  provenance: {"harness_session":"claude-code:2d4f1b44-70f6-4dcf-877c-e39755156302","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
- 2026-11-01T01:56:13Z (main): started
  provenance: {"harness_session":"claude-code:83e6ed02-8814-4b88-8d94-828898b574a0","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-11-01T01:56:13Z (main): halt override: started past sci-0bea23 by 83e6ed02-8814-4b88-8d94-828898b574a0: user asked in session to take sci-62e5aa; halt sci-0bea23 remedy merged f57543a and waits only on tt-latency verify runs
- 2026-11-01T01:57:26Z (fix/kernel-refusal-after-act): resumed
  provenance: {"harness_session":"claude-code:83e6ed02-8814-4b88-8d94-828898b574a0","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-11-01T02:15:00Z (fix/kernel-refusal-after-act): baseline at worktree creation: just test, 1191 passed in 1021 s (one xdist worker: host loaded by other sessions' suites); worktree .worktrees/kernel-refusal-after-act on branch fix/kernel-refusal-after-act
- 2026-11-01T02:16:22Z (fix/kernel-refusal-after-act): decision: a kernel refusal after a published act closes done with the act pairs and raises HandlerContractViolation (the _close_acted path, as surface refusals and _invoke_sharing already do). Why: the ledger records act truth; closing refused dropped a committed act from the outcome and its replay. Cost if wrong: a legitimate post-act kernel refusal (e.g. a concurrent session minting the same dataset between the handler's pre-check and writer.add) surfaces as internal-error rather than a classified refusal; the acts stay correct either way. Rejected: an outcome carrying both acts and a refusal envelope (needs a beliefs close-outcome shape change; out of scope). Spec amendment added to framework design §6.1.
- 2026-11-01T02:16:24Z (fix/kernel-refusal-after-act): done
  provenance: {"harness_session":"claude-code:83e6ed02-8814-4b88-8d94-828898b574a0","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-11-01T02:16:24Z (fix/kernel-refusal-after-act): A kernel refusal after a published act now closes done with the act and raises HandlerContractViolation (e7b3fa1). Verification: focused RED->GREEN on test_dispatch_refusals::test_a_kernel_refusal_after_an_act_closes_done_and_is_an_internal_error (second add of one proposition) and test_cmd_dataset::test_a_kernel_refused_record_after_held_bytes_closes_done_with_the_holding (real dataset handler, writer.add refused after the holdings publish, retry replays the holding); 71 passed over test_dispatch_refusals, test_cmd_dataset, test_write_dispatch, test_dispatch_sharing; pre-commit test-fast and check green. Baseline just test at creation: 1191 passed. Limitation: post-act kernel refusals from races read as internal-error. Disclosures: nothing pushed; merged locally into main; no surviving processes; no host pointers repointed.
  provenance: {"harness_session":"claude-code:83e6ed02-8814-4b88-8d94-828898b574a0","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-11-01T02:16:59Z (main): retained: worktree .worktrees/kernel-refusal-after-act released on titan after merge 9fc06b9; ignored entries python/.venv and python/.pytest_cache discarded as regenerable; tt-report run; branch fix/kernel-refusal-after-act deleted after merge; no host pointers resolved into it. host-load: no processes left by this session (baseline and focused runs exited).
