---
id: sci-923d3a
title: "Coordination part 3: multi-corpus (write_root, read_contracts, per-mount profiles, cross-corpus classification)"
status: doing
priority: 2
size: l
complexity: high
process: planned
owner: coordination-part3
created: 2026-09-24T10:54:38Z
updated: 2026-09-30T15:01:10Z
started: 2026-09-30T14:51:09Z
depends: [beliefs-fe7149, beliefs-cc0aea, sci-f95f8b]
parent: sci-c5528e
tags: [projects]
agent: claude-code/claude-opus-5-5
plan: docs/plans/2026-09-30-coordination-multi-corpus.md
---

Spec §5.5 and §6: write_root and read_contracts; the per-mount profile rule in the session's and the sessionless read context's resolvers; next's classification across mounted corpora; each single_view() caller decided write-root-only or read-set-wide; the two-corpus check in §9. Milestone criterion 4 (sci-0d00d2) depends on it.

## Notes

- 2026-09-30T14:51:09Z (main): started
  provenance: {"harness_session":"claude-code:44b120ba-4c5c-4a3e-b096-03eca2443281","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-30T14:51:09Z (coordination-part3): resumed
  provenance: {"harness_session":"claude-code:44b120ba-4c5c-4a3e-b096-03eca2443281","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-30T15:01:04Z (coordination-part3): Part 3 plan drafted: docs/plans/2026-09-30-coordination-multi-corpus.md, five steps sci-e7e630..sci-ca4d61 (a chain). The spec takes three 2026-09-30 part 3 planning amendments reviewed with the plan: the single_view() callers decided (claim/dataset/spec/run/assess/verify write-root-only; belief/next read-set-wide; one store's holdings and vocabularies across mounts; duplicate ids and unmounted selected addresses refuse invalid-input); write_root/read_contracts defaults and the both-lists check by content identity; the two-corpus fixture types under testing + a second document archive rather than a biology operator.
- 2026-09-30T15:01:10Z (coordination-part3): parked (waiting on user, review): Review the part 3 plan at .worktrees/coordination-part3/docs/plans/2026-09-30-coordination-multi-corpus.md and the three 2026-09-30 part 3 planning amendments in .worktrees/coordination-part3/docs/specs/2026-09-24-coordination-command-set-design.md (§5.5, §6, §9), and choose an execution method; then the agent runs tasks start sci-e7e630 (Task 1) in .worktrees/coordination-part3
  provenance: {"harness_session":"claude-code:44b120ba-4c5c-4a3e-b096-03eca2443281","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
