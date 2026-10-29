---
id: sci-4b5ec4
title: "Retirement reports: name adopt as the lag-state remedy and report reconciled retirements when the target was retired"
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-10-29T15:48:17Z
updated: 2026-10-29T15:48:17Z
depends: []
tags: [commons]
source: sci-9104fb
agent: claude-code/claude-opus-5-5
origin: agent
---

Two report and remedy gaps the retirement tail's whole-branch review found (deferred minors 1 and 2, sci-9104fb plan ledger). Both are rare and recoverable, with no data loss.

1. **Lag state.** A `mounted` pin over a kernel-retired corpus exists after a crash between the kernel's status write and the `retired` line, after a crash between the line and the pin write, or after a reconcile door refusal. `load_config` mounts by pin state and never replays, so every open mounts the retired corpus again. Citing writes and `publish` refuse `corpus-retired ... reopen the session`, and reopening repeats the refusal; `science epoch` reaches the kernel's `CoverageNotLive` un-normalized; `show` says `retired: yes` with no remedy. Only an `adopt` (of any corpus) repairs it. Smallest fix: both `corpus-retired` messages and the `show` prompt name `adopt` as the remedy when the refusal persists after reopening; the alternative, the loader replaying or filtering by kernel liveness, is a design call to record if chosen.
2. **Reconcile retires the requested target.** `adopt` then refuses `invalid-input` "is already adopted: its pin is retired", which reads as success, and the refused invocation closes without pin blocks, so every retirement reconcile recorded in that invocation goes unreported (1b design §5.7 says `already adopted` refuses only when nothing was written). Fix: when lines were written, return the tail with the retired blocks plus a Finding that the target is retired and not re-adopted; otherwise reword. Add the missing test (the limit is documented in commons design §10 but untested).

## Notes

- 2026-10-29T15:48:17Z (add): created
  provenance: {"harness_session":"claude-code:e9952dfd-ee2b-47b3-84ef-d176d9d3cc57","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
