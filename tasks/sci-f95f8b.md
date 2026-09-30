---
id: sci-f95f8b
title: "Coordination part 2: selection, project reads, selection query, next through the selection"
status: doing
priority: 1
size: l
complexity: high
process: planned
owner: coordination-part2
created: 2026-09-24T10:54:38Z
updated: 2026-09-30T11:38:16Z
started: 2026-09-30T11:01:17Z
depends: [beliefs-cc0aea, beliefs-1148ad, beliefs-1af3fd, sci-c147e3]
parent: sci-c5528e
tags: [projects]
agent: claude-code/claude-opus-5-5
spec: docs/specs/2026-09-24-coordination-command-set-design.md
plan: docs/plans/2026-09-30-coordination-selection-and-reads.md
---

Spec docs/specs/2026-09-24-coordination-command-set-design.md §3.7, §3.8, §4.1, §4.2, §4.4, §5.1-5.3, §5.5 and P5/P8: project-select and the session write class with its selection block; projects and project-show; the selects key and the project read protocol field; launcher initial selection and default_project; the selection query on the socket and the CLI's resolution order; next through the selection; the preamble. Its plan is written when the beliefs seams land.

## Notes

- 2026-09-24T14:26:54Z (main): From part 1's final review: with coordination = N on a corpus that does not pin coordination, sessionless reads through ReadContext.coordination() build a CoordinationResolver that checks pins and raises a bare ContractMismatch (internal-error). open_session now refuses this by name (science.session._require_coordination_pinned); part 2's projects, project-show and --project reads need the same named refusal.
- 2026-09-25T13:52:46Z (main): All three beliefs seams landed on beliefs main (local, not pushed), 2026-09-25: beliefs-1af3fd CoordinationResolver.standing(kind, project=) (d0d964e); beliefs-1148ad session selection (7cf5d17): open_attended_session(..., project=), WriterSession.select_project(invocation_id, address) -> pinned CoordinationAddress | None, invocation_selection(invocation_id) -> SelectLine | None, the ledger's select line, LedgerReader.initial_project / InvocationRecord.selection / attributed_acts(), SelectLine exported from beliefs.session; beliefs-cc0aea cut 41 discharged: beliefs.world.live.evaluate_live_query(world, query) -> LiveSelection — render complete, absent and stamp (CaptureStamp: world_id, coverage). Part 2's plan can now be written.
- 2026-09-30T11:01:17Z (main): started
  provenance: {"harness_session":"claude-code:2dfb2b90-3871-4afc-bd8c-8f7d26431d3c","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-30T11:25:21Z (coordination-part2): Part 2 plan drafted: docs/plans/2026-09-30-coordination-selection-and-reads.md, eight steps sci-451329, sci-108756, sci-a66ca4, sci-b0b8cf, sci-1217b5, sci-1391bd, sci-5b8997, sci-103ec2 (a chain). The spec takes seven 2026-09-30 planning amendments reviewed with the plan: project-show refuses no-current-project with nothing selected; --project is on selects rows and the two launcher rows only; the launcher's --project takes a name; every CLI read asks the socket; next renders a selection block; the session handler's parameter is port; a project key on the socket request. The three beliefs seams were probed against a fixture world while planning.
- 2026-09-30T11:25:45Z (coordination-part2): parked (waiting on user, review): Review the part 2 plan at .worktrees/coordination-part2/docs/plans/2026-09-30-coordination-selection-and-reads.md and the seven 2026-09-30 planning amendments in .worktrees/coordination-part2/docs/specs/2026-09-24-coordination-command-set-design.md, and choose an execution method; then the agent runs tasks start sci-451329 (Task 1) in .worktrees/coordination-part2
  provenance: {"harness_session":"claude-code:2dfb2b90-3871-4afc-bd8c-8f7d26431d3c","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-30T11:37:10Z (coordination-part2): resumed
  provenance: {"harness_session":"claude-code:2dfb2b90-3871-4afc-bd8c-8f7d26431d3c","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-30T11:37:10Z (coordination-part2): review: plan round 1 — verdict: revise; findings: P2 3; reviewer: unknown (pasted by the user, source not stated)
- 2026-09-30T11:38:16Z (coordination-part2): Plan round 1 findings, all three verified and taken: (1) next opened its lookup view before the live capture, so a proposition minted in between was dropped under complete: true (probed: a view opened before a write does not hold the new record) — the view now opens after the capture, an unheld selected record is an internal error, two tests added; (2) project-show checked the selection before coordination, so coordination = false gave no-current-project — coordination() is now first; (3) the spec amendment said a refuse-after-select replays an internal error while the plan's test replays the block — amendment corrected: only a done close with no selection line errors on replay.
- 2026-09-30T11:38:16Z (coordination-part2): parked (waiting on user, review): Re-review the revised part 2 plan at .worktrees/coordination-part2/docs/plans/2026-09-30-coordination-selection-and-reads.md (round 1's three findings taken: Task 7's handler and tests, Task 4's project-show, spec §4.1 and §5.5 amendments) and choose an execution method; then the agent runs tasks start sci-451329 in .worktrees/coordination-part2
  provenance: {"harness_session":"claude-code:2dfb2b90-3871-4afc-bd8c-8f7d26431d3c","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
