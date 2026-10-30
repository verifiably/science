---
id: sci-bb8611
title: Resolve inherited holdings and vocabularies through every admitted store
status: doing
priority: 1
size: s
complexity: mid
process: direct
owner: sci-300dab-stores
created: 2026-10-30T20:24:32Z
updated: 2026-10-30T23:26:21Z
started: 2026-10-30T23:15:29Z
depends: [sci-14a324]
parent: sci-300dab
tags: [holdings]
source: "sci-300dab:readable-stores-plan-task-2"
agent: codex
origin: agent
spec: docs/specs/2026-10-30-readable-stores-design.md
plan: docs/plans/2026-10-30-readable-stores.md
step: "Task 2: Resolve inherited holdings and vocabularies through every admitted store"
---

Implement plan Task 2 after plan approval and Task 1: shared identity mapping for holdings and vocabulary snapshots, exact resolver order, confinement, no fallback and explicit refusal semantics. Cover evaluate/gather_inputs and run/verify consumers with focused regression evidence.

## Notes

- 2026-10-30T20:24:32Z (add): created
  provenance: {"harness_session":"codex:01a18e58-0cdf-75c2-bf7d-f4ac22417069","harness_session_source":"CODEX_THREAD_ID","origin":"agent"}
- 2026-10-30T23:15:29Z (sci-300dab-stores): started
  provenance: {"harness_session":"codex:01a18e58-0cdf-75c2-bf7d-f4ac22417069","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-30T23:15:29Z (sci-300dab-stores): halt override: started past sci-0bea23 by 01a18e58-0cdf-75c2-bf7d-f4ac22417069: Execute approved readable-stores plan despite open timing halt sci-0bea23
- 2026-10-30T23:26:21Z (sci-300dab-stores): Implemented 265a896: held paths and vocabulary snapshots share the cached admitted-store mapping; exact identity, locator validation, path confinement and no fallback preserved. RED: 16 resolver failures plus both run/verify preparation failures; GREEN: 73 focused, 692 affected tests, hygiene and final 73 focused passed in 84.45s. Worktree and evidence remain owned by parent sci-300dab; no child-owned retained resources.
