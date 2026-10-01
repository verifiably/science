---
id: sci-dc0381
title: "Consume beliefs mount citations: write commands name mount records, belief over a world read"
status: doing
priority: 1
size: m
complexity: mid
process: planned
owner: feat/dc0381-mount-citations
created: 2026-10-01T11:07:18Z
updated: 2026-10-01T23:07:39Z
started: 2026-10-01T21:17:59Z
depends: [beliefs-9ce6e4]
tags: [commons, projects]
source: beliefs-9ce6e4
agent: claude-code/claude-opus-5-5
spec: docs/specs/2026-10-01-mount-citations-consumer-design.md
plan: docs/plans/2026-10-01-mount-citations-consumer.md
---

beliefs mount-citations spec (beliefs docs/superpowers/specs/2026-10-01-mount-citations-design.md §4), cut 44. Once beliefs-9ce6e4 lands: (1) spec, run, assess and verify may name a read mount's dataset, proposition and assessment; drop part 3's refusal of a read mount's dataset (dataset still refuses bytes a mount declares). (2) Remove ReadContext._refuse_foreign_observations: a corpus-local read now refuses input-outside-corpus in the kernel. (3) Cross-corpus belief is a world read at an epoch covering the write root and its mounts (decision 10), the commons design's 'belief evaluating over a world read' (§11). (4) status shows eligibility-unresolved warnings for cross-mount assessments; audit_world judges them. (5) A citation into a mount pinning a different identity of a shared namespace refuses CitationContractMismatch: check mm30's pins against the working corpus's before sci-0d00d2.

## Notes

- 2026-10-01T20:52:23Z (main): unblocked: beliefs-9ce6e4 (cut 44, mount citations) merged into beliefs main at 7932481 on 2026-10-01 — a session's writes can now cite records in its read mounts; see beliefs docs/plans/2026-10-01-conformance-cut-44-results.md
- 2026-10-01T21:17:58Z (main): absorbs sci-b1c777 (same two refusals: ReadContext.not_held and _refuse_foreign_observations; coordination spec §5.5 part 3 amendment moves here) and sci-498acb (publishes refusal retirement, rides along); user agreed 2026-10-01
- 2026-10-01T21:17:59Z (feat/dc0381-mount-citations): started
  provenance: {"harness_session":"claude-code:e278d911-5d98-4ab3-83dd-1a16988a96a4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T21:17:59Z (feat/dc0381-mount-citations): claimed by claude-code main session, pid 3790747
- 2026-10-01T21:22:34Z (feat/dc0381-mount-citations): spec drafted: belief in a mounted session is a world read at the current epoch (refuses no-epoch/epoch-stale), new operator verb 'science epoch', next gains assessed-unevaluated; mm30 pins match shipped biology/base (no CitationContractMismatch)
- 2026-10-01T21:22:39Z (feat/dc0381-mount-citations): parked (waiting on user, review): user reviews docs/specs/2026-10-01-mount-citations-consumer-design.md (decisions 7–9: epoch-bound belief, science epoch verb, next's fifth class); on approval the agent writes the plan via writing-plans
  provenance: {"harness_session":"claude-code:e278d911-5d98-4ab3-83dd-1a16988a96a4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T21:29:17Z (feat/dc0381-mount-citations): resumed
  provenance: {"harness_session":"claude-code:e278d911-5d98-4ab3-83dd-1a16988a96a4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T21:29:17Z (feat/dc0381-mount-citations): review: spec round 1 — verdict: revise; findings: P2 3; reviewer: human
- 2026-10-01T21:44:38Z (feat/dc0381-mount-citations): plan written: docs/plans/2026-10-01-mount-citations-consumer.md, 7 tasks (sci-c7aad5, -da8d69, -4464b6, -13a853, -0f8919, -405c46, -4dca02); spec amended in planning: inert coordination drift does not stale the epoch
- 2026-10-01T21:44:38Z (feat/dc0381-mount-citations): parked (waiting on user, review): user reviews docs/plans/2026-10-01-mount-citations-consumer.md and the spec's planning amendments (decision 7 inert drift; decisions 2, 5, 6, 11, 12), and picks an execution method; then the agent executes Task 1 (sci-c7aad5)
  provenance: {"harness_session":"claude-code:e278d911-5d98-4ab3-83dd-1a16988a96a4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T22:18:29Z (feat/dc0381-mount-citations): resumed
  provenance: {"harness_session":"claude-code:e278d911-5d98-4ab3-83dd-1a16988a96a4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T22:18:29Z (feat/dc0381-mount-citations): review: plan round 1 — verdict: revise; findings: P1 1, P2 4; reviewer: human
- 2026-10-01T22:21:14Z (feat/dc0381-mount-citations): plan round 1 revised: strict drift restored with the mixed-change regression; WORKING_FIELDS keeps write-root specs distinct; currency-check contention normalized; coordination-off next stays holder-local; input-outside-corpus is a named row reason. Follow-up beliefs-655c10 (inert-drift witness).
- 2026-10-01T22:21:14Z (feat/dc0381-mount-citations): parked (waiting on user, review): user re-reviews the revised plan (round 2) and picks an execution method; then the agent executes Task 1 (sci-c7aad5)
  provenance: {"harness_session":"claude-code:e278d911-5d98-4ab3-83dd-1a16988a96a4","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T23:07:32Z (feat/dc0381-mount-citations): review: plan round 2 — verdict: accept; findings: none; reviewer: human
- 2026-10-01T23:07:32Z (feat/dc0381-mount-citations): execution: subagent-driven, controller claude-code/claude-opus-5-5 pid 3790747
- 2026-10-01T23:07:39Z (feat/dc0381-mount-citations): resumed
  provenance: {"harness_session":"claude-code:6051398c-8f0e-4511-a835-e90a0c6e83e9","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
