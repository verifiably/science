---
id: sci-103ec2
title: "Preamble, dated amendments, and close-out of part 2"
status: done
priority: 1
size: s
complexity: low
process: direct
owner: coordination-part2
created: 2026-09-30T11:25:02Z
updated: 2026-09-30T14:27:46Z
started: 2026-09-30T13:24:01Z
completed: 2026-09-30T14:27:46Z
depends: [sci-5b8997]
parent: sci-f95f8b
tags: [projects]
agent: claude-code/claude-fable-5-1
plan: docs/plans/2026-09-30-coordination-selection-and-reads.md
step: "Task 8: The preamble, the dated amendments, and the close-out"
---

## Notes

- 2026-09-30T12:30:20Z (coordination-part2): Ruling: correct the Task 8 sample preamble to distinguish corpus writes/records from session writes/recorded selection; session-class spec §4.1 supersedes the contradictory every-write-is-kernel-act sentence identified in Task 3 review.
- 2026-09-30T13:24:01Z (coordination-part2): started
- 2026-09-30T13:29:46Z (coordination-part2): Repository implementation, docs, and gate are committed; ops CLI publication awaits explicit approval.
- 2026-09-30T13:35:29Z (coordination-part2): review: impl round 1 — verdict: accept; findings: none; reviewer: codex/gpt-6.1-sol
- 2026-09-30T13:46:40Z (coordination-part2): resumed
- 2026-09-30T13:50:24Z (coordination-part2): Final review fix wave: total selection-query deadline and scratch-report untracking implemented; focused selection tests pass. Repository checks in progress; ops CLI publication still requires explicit approval, so this task and parent remain open.
- 2026-09-30T13:53:29Z (coordination-part2): Final review fixes verified: focused selection-query tests 19 passed, just gate 606 passed, just test-fast 50 passed. Total timeout enforced and two scratch reports untracked locally; ops CLI publication remains pending explicit approval, so this task and parent remain open.
- 2026-09-30T13:58:55Z (coordination-part2): resumed
  provenance: {"harness_session":"codex:01a0f21d-ccb2-7141-83c5-8d21fea93221","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-30T13:58:55Z (coordination-part2): parked (waiting on user, approval): Controller after user approval: apply the prepared science CLI patch to ops, commit under its guide, run just vendor-cli, verify branch table identity and affected CLI checks, then close Task 8 and parent
  provenance: {"harness_session":"codex:01a0f21d-ccb2-7141-83c5-8d21fea93221","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-30T14:08:47Z (coordination-part2): resumed
  provenance: {"harness_session":"codex:01a0f21d-ccb2-7141-83c5-8d21fea93221","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-30T14:08:47Z (coordination-part2): User approved ops CLI publication and cross-project vendoring; resuming final publication and task closure
- 2026-09-30T14:17:04Z (coordination-part2): Publication validation found four --project rows must reference the shared project vocabulary with role select; correcting table metadata preserves the CLI spelling and runtime behavior. Broader vendored audit also reports unrelated keys.toml drift, which this publication leaves untouched.
- 2026-09-30T14:27:46Z (coordination-part2): review: impl round 2 — verdict: accept; findings: none; reviewer: codex/gpt-6.1-sol
- 2026-09-30T14:27:46Z (coordination-part2): Ops publication complete in 6178374 (ops-9ff308); science table correction and final status in 0950d4e. Ops focused 4 and full fast 870 (1 skip) passed with a clean command-local TMPDIR; science CLI focused 31 passed. Verified all 11 CLI tables and 10 helpers plus this worktree byte-identical to ops. Broader vendored audit still reports unrelated keys.toml drift in mind6/tui, left untouched. Feedback: ops-ee3851 ordering, ops-3c531b temporary Git metadata, tack-89dff8 omitted source validation.
- 2026-09-30T14:27:46Z (coordination-part2): done
  provenance: {"harness_session":"codex:01a0f21d-ccb2-7141-83c5-8d21fea93221","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-30T14:27:46Z (coordination-part2): preamble, dated amendments, 606-test gate, reviewed ops CLI publication and re-vendoring
  provenance: {"harness_session":"codex:01a0f21d-ccb2-7141-83c5-8d21fea93221","harness_session_source":"CODEX_SESSION_ID"}
