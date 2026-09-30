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
updated: 2026-09-30T16:05:53Z
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
- 2026-09-30T15:25:41Z (coordination-part3): resumed
  provenance: {"harness_session":"claude-code:44b120ba-4c5c-4a3e-b096-03eca2443281","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-30T15:25:41Z (coordination-part3): review: plan round 1 — verdict: revise; findings: P1 1, P2 2; reviewer: unknown (pasted by the user, source not stated)
- 2026-09-30T15:27:51Z (coordination-part3): Plan round 1 findings, all three verified and taken: (P1) dataset ids derive from content and dataset is a world kind, so re-holding a read mount's bytes makes a duplicate-location that refuses every selected next — dataset now refuses bytes any mount declares, naming the record; spec/run/verify take a dataset record from any mount (the run boundary needs only the address and held path); Task 4's headline selected next runs over a working spec observing the archive's dataset; (P2) mounts() read manifests before the profile translation — profiles first, corpus ids through corpus_id_at, and entry-point tests for sessionless belief and unselected next; (P2) selected next's duplicate refuses at the live capture as kernel-refused AddressMapConflict — spec §5.5 amendment corrected, both paths tested.
- 2026-09-30T15:27:52Z (coordination-part3): parked (waiting on user, review): Re-review the revised part 3 plan at .worktrees/coordination-part3/docs/plans/2026-09-30-coordination-multi-corpus.md (round 1's three findings taken: Task 3's dataset rule and tests, Task 2's mounts() ordering and corpus_id_at, Task 4's duplicate-id and entry-point tests; spec §5.5 amendment) and choose an execution method; then the agent runs tasks start sci-e7e630 in .worktrees/coordination-part3
  provenance: {"harness_session":"claude-code:44b120ba-4c5c-4a3e-b096-03eca2443281","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-30T16:03:37Z (coordination-part3): resumed
  provenance: {"harness_session":"claude-code:44b120ba-4c5c-4a3e-b096-03eca2443281","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-30T16:03:37Z (coordination-part3): review: plan round 2 — verdict: revise; findings: P1 1; reviewer: codex (model not stated)
- 2026-09-30T16:05:53Z (coordination-part3): Plan round 2 finding verified and taken: CorpusWriter._refuse_ineligible reads eligibility through the writer's own view, so a read mount's dataset would pass spec/run and fail assess with EligibilityUnmet. Write-command dataset inputs stay in the write root (spec/run refuse a read mount's dataset naming it); dataset keeps refusing bytes any mount declares; cross-corpus inputs filed as beliefs-9ce6e4 (committed in beliefs cbcba20), and sci-0d00d2 now depends on it. Task 4's fixture walks claim → spec → run → assess → verify in the write root with the archive mounted, and next/belief read all three propositions. Rejected: blocking all of part 3 on beliefs-9ce6e4 — the read-across and config work do not need it.
