---
id: sci-f95f8b
title: "Coordination part 2: selection, project reads, selection query, next through the selection"
status: todo
priority: 1
size: l
complexity: high
process: planned
created: 2026-09-24T10:54:38Z
updated: 2026-09-25T13:52:46Z
depends: [beliefs-cc0aea, beliefs-1148ad, beliefs-1af3fd, sci-c147e3]
parent: sci-c5528e
tags: [projects]
agent: claude-code/claude-opus-5-5
---

Spec docs/specs/2026-09-24-coordination-command-set-design.md §3.7, §3.8, §4.1, §4.2, §4.4, §5.1-5.3, §5.5 and P5/P8: project-select and the session write class with its selection block; projects and project-show; the selects key and the project read protocol field; launcher initial selection and default_project; the selection query on the socket and the CLI's resolution order; next through the selection; the preamble. Its plan is written when the beliefs seams land.

## Notes

- 2026-09-24T14:26:54Z (main): From part 1's final review: with coordination = N on a corpus that does not pin coordination, sessionless reads through ReadContext.coordination() build a CoordinationResolver that checks pins and raises a bare ContractMismatch (internal-error). open_session now refuses this by name (science.session._require_coordination_pinned); part 2's projects, project-show and --project reads need the same named refusal.
- 2026-09-25T13:52:46Z (main): All three beliefs seams landed on beliefs main (local, not pushed), 2026-09-25: beliefs-1af3fd CoordinationResolver.standing(kind, project=) (d0d964e); beliefs-1148ad session selection (7cf5d17): open_attended_session(..., project=), WriterSession.select_project(invocation_id, address) -> pinned CoordinationAddress | None, invocation_selection(invocation_id) -> SelectLine | None, the ledger's select line, LedgerReader.initial_project / InvocationRecord.selection / attributed_acts(), SelectLine exported from beliefs.session; beliefs-cc0aea cut 41 discharged: beliefs.world.live.evaluate_live_query(world, query) -> LiveSelection — render complete, absent and stamp (CaptureStamp: world_id, coverage). Part 2's plan can now be written.
