---
id: sci-4e8adb
title: Resolve existing tilde-layout findings before checker rollout
status: doing
priority: 2
size: s
complexity: mid
process: direct
owner: fix/sci-4e8adb
created: 2026-10-22T19:07:45Z
updated: 2026-10-29T20:54:05Z
started: 2026-10-29T20:26:47Z
depends: []
tags: []
source: ops-295f8d
agent: codex
---

Why: the final candidate from ops-295f8d reports existing home-relative machine-layout paths that the current checker misses. Resolve these before the stricter vendored copy arrives, so unrelated commits are not blocked. These are scanner findings to classify, not an instruction to discard historical documents.

Done: inspect each listed file in context. Replace accidental checkout/storage paths in shared docs, examples or fixtures with repository-relative paths, project-role references or portable URLs as appropriate. For intentional host configuration, use only the narrow existing layout_allowed mechanism where this repository is host configuration by design; do not exempt ordinary docs wholesale. Preserve historical evidence, attachments and every spec/plan review ledger; follow the task attachment CLI and retention rules instead of editing attached artifacts by hand. If a runtime-path correction needs an unsettled public contract, change that piece to planned before implementation. Run the project-declared checks and the reviewed candidate checker by explicit path, then record every listed file disposition and the clean verdict on this task. Do not repoint shared launchers, vendor the checker, publish, push or activate global guidance in this task.

Where: the current project guide/profile, listed tracked files, existing layout_allowed, and ops-295f8d for candidate branch/path and canonical report. The full sweep reached 36 registered repositories with no unavailable roots; counts here are capped scanner records, not an estimate of all occurrences. No source snippets are copied.

Reported files:
- docs/plans/2026-09-09-belief-path-commands.md: first reported line 508; 4 reported finding(s)

## Notes

- 2026-10-29T20:26:47Z (main): started
  provenance: {"harness_session":"claude-code:0abf3f61-62e6-4a09-a944-9063cc887bf3","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-29T20:27:34Z (fix/sci-4e8adb): resumed
  provenance: {"harness_session":"claude-code:0abf3f61-62e6-4a09-a944-9063cc887bf3","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-29T20:39:12Z (fix/sci-4e8adb): dispositions: docs/plans/2026-09-09-belief-path-commands.md:508,738,1129,1443 — reworded: host checkout path in four grep commands replaced with the project-role placeholder <beliefs checkout>/python/src/beliefs/...; path text only, plan wording and checkboxes unchanged; no layout_allowed entry added
- 2026-10-29T20:52:57Z (fix/sci-4e8adb): verification: candidate rc=0 at d64ecb7 (rechecked rc=0 at e6642a7); just check rc=0 (ops-check, ops-docs check, tasks check); git diff --check clean; docs-only change, no focused tests owed; worktree baseline just test (policy enabled, no .tt.toml) 1070 passed in 1489s under host-budget 1 worker; worktree .worktrees/sci-4e8adb (locked, WORK_ROOT storage, branch fix/sci-4e8adb) retained for controller review and integration, remove after merge
- 2026-10-29T20:52:58Z (fix/sci-4e8adb): parked (waiting on agent): controller: review fix/sci-4e8adb at bbc306b in .worktrees/sci-4e8adb, then integrate
  provenance: {"harness_session":"claude-code:0abf3f61-62e6-4a09-a944-9063cc887bf3","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-29T20:54:05Z (fix/sci-4e8adb): resumed
  provenance: {"harness_session":"claude-code:0abf3f61-62e6-4a09-a944-9063cc887bf3","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
