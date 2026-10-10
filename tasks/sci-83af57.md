---
id: sci-83af57
title: "quarry: Register quarry in ops and add its CLI rows"
status: done
priority: 2
complexity: low
process: direct
owner: quarry-design
created: 2026-10-10T19:11:12Z
updated: 2026-10-10T20:23:40Z
started: 2026-10-10T20:17:46Z
completed: 2026-10-10T20:23:40Z
depends: [sci-005df0]
parent: sci-ba7150
tags: []
agent: claude-code/claude-opus-5-5
plan: docs/plans/2026-10-10-quarry-foundation.md
step: "Task 2: Register quarry in ops and add its CLI rows"
---

## Notes

- 2026-10-10T20:17:46Z (quarry-design): started
  provenance: {"harness_session":"codex:01a12769-e196-7e72-829a-066a98c2baa4","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-10T20:17:46Z (quarry-design): halt override: started past sci-5937be by 01a12769-e196-7e72-829a-066a98c2baa4: Approved quarry foundation plan: separate-project registration and CLI table, no science runtime or tests changed.
- 2026-10-10T20:19:48Z (quarry-design): Execution adjustment: ops-projects pull validates generated mirror fields before pulling; seed exact name/purpose from quarry main identity.toml, then run pull. No shared-tool code changes.
- 2026-10-10T20:20:12Z (quarry-design): Authority-table adjustment: add role=bound to shared since/until search rows to satisfy current CLI validator and existing scientific-search convention; option names/types unchanged.
- 2026-10-10T20:23:02Z (quarry-design): review: impl round 1 — verdict: accept; findings: none; reviewer: codex/gpt-6.1-sol
- 2026-10-10T20:23:40Z (quarry-design): done
  provenance: {"harness_session":"codex:01a12769-e196-7e72-829a-066a98c2baa4","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-10T20:23:40Z (quarry-design): Registration, generated Projects source and CLI rows landed in ops main ab844c8 after clean independent review. Focused CLI 7 passed; ops fast suite 1444 with existing skip; check passed. Worktree removed after ignored-file and host-pointer audit and tt-report. Live global assembly separated to lore-e8a9ca pending user approval; later implementation does not depend on it.
  provenance: {"harness_session":"codex:01a12769-e196-7e72-829a-066a98c2baa4","harness_session_source":"CODEX_THREAD_ID"}
