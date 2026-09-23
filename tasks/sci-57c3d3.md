---
id: sci-57c3d3
title: "Task 6: `spec` — freeze an analysis spec"
status: done
priority: 1
size: s
complexity: high
process: planned
owner: dogfood-commands
created: 2026-09-09T13:23:36Z
updated: 2026-09-23T17:10:38Z
started: 2026-09-23T16:42:42Z
completed: 2026-09-23T17:10:38Z
depends: [sci-98282e, beliefs-e5ab34]
parent: sci-66b26d
tags: [dogfood]
model: "claude-opus-5-5[1m]"
plan: docs/plans/2026-09-09-belief-path-commands.md
step: "Task 6: `spec` — freeze an analysis spec"
---

## Notes

- 2026-09-23T12:49:46Z (dogfood-commands): 2026-09-23 audit: the kernel requires SpecDraft.estimand as a typed Estimand built against the target claim (beliefs 9ad72e2, 71b2741) and applicability as Mapping[str, Qualifier]; the spec command's input surface (design §4.3) must grow contrast/measure/scale/reference/identification. Needs a reviewed design amendment before implementation; template beliefs tools/reproduction/spec.py.
- 2026-09-23T13:16:22Z (dogfood-commands): parked (waiting on user, review): Review the typed-estimand amendment to the belief-path design (commit f41834b: §4.3, §4.5, §5.2, §8.2–8.3); on approval, revise plan Tasks 6, 8 and 13 (and SPEC_FIELDS / TEST_CONTRACT estimands row), get the plan revision reviewed, then continue at Task 6. Rows for spec/run/assess/verify/next go to ops cli.toml as batch 2.
  provenance: {"harness_session":"claude-code:a03ed4ed-95bd-4e3d-b3c4-4d49a2c843f9","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-23T16:33:04Z (dogfood-commands): Amendment review round 1 (3 findings, all verified against kernel and dispatcher): §3 holds the three estimand vocabularies before spec; §4.3 enforces heldness from the estimand and applicability receipts; §4.3 maps ClaimError/DecodeError/ProfileError/ESTIMAND_ERRORS to invalid-input so refusals replay; §7 names the tests. Commit 8b17272.
- 2026-09-23T16:33:04Z (dogfood-commands): parked (waiting on user, review): Review the revised typed-estimand amendment (f41834b + 8b17272); on approval, revise plan Tasks 6, 8, 13 (SPEC_FIELDS, TEST_CONTRACT estimands row, three vocabulary holds), get the plan revision reviewed, then continue at Task 6; CLI rows batch 2 after.
  provenance: {"harness_session":"claude-code:a03ed4ed-95bd-4e3d-b3c4-4d49a2c843f9","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-23T16:42:42Z (dogfood-commands): started
  provenance: {"harness_session":"claude-code:a03ed4ed-95bd-4e3d-b3c4-4d49a2c843f9","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-23T16:48:01Z (dogfood-commands): parked (waiting on user, review): Review the plan revision (commit 5a7652f: Task 6 rewritten; Tasks 7, 8, 9, 11, 13 revised); on approval implement Task 6, then 7–9, 11, 12 with CLI batch 2, then Task 13.
  provenance: {"harness_session":"claude-code:a03ed4ed-95bd-4e3d-b3c4-4d49a2c843f9","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-23T16:50:02Z (dogfood-commands): resumed
  provenance: {"harness_session":"claude-code:a03ed4ed-95bd-4e3d-b3c4-4d49a2c843f9","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-23T17:10:38Z (dogfood-commands): done
  provenance: {"harness_session":"claude-code:a03ed4ed-95bd-4e3d-b3c4-4d49a2c843f9","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-23T17:10:38Z (dogfood-commands): spec command: typed estimand and applicability against the target claim, heldness enforced from the receipts, every authoring error a replayable invalid-input, deterministic draft frozen against the kernel's reference rules
  provenance: {"harness_session":"claude-code:a03ed4ed-95bd-4e3d-b3c4-4d49a2c843f9","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
