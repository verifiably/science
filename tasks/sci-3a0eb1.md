---
id: sci-3a0eb1
title: Coordination part 1 final-review minors
status: done
priority: 3
size: xs
complexity: low
process: direct
owner: coordination-closeout
created: 2026-09-24T14:26:54Z
updated: 2026-10-26T23:34:44Z
started: 2026-10-26T23:28:12Z
completed: 2026-10-26T23:34:44Z
closed: 2026-10-26T23:34:44Z
depends: []
parent: sci-c5528e
tags: [projects]
agent: claude-code/claude-opus-5-5
---

Deferred Minor findings from the 2026-09-24 reviews of coordination part 1: revise.py decides the address shape by counting '/' and then calls parse_address, duplicating science.coordination.parse_unpinned — use it; the divergent-view refusal is built twice (revise.py and coordination.resolve_one) — one helper; no test reuses a hypothesis source (only question); revise --repair demands every field even with a single standing tip (spec §3.6 literal — decide whether repair on one tip should carry over); spec §6's unamended sentence still says every coordination-class command refuses CoordinationUnavailable, which the dated amendment below it corrects — fold the amendment in, and name the version-mismatch message too.

## Notes

- 2026-10-26T23:17:21Z (main): item 2 (divergent-view refusal built twice) is done by sci-dce3b2: science.coordination.refuse_coordination now backs resolve_one, selected_project and revise
- 2026-10-26T23:28:12Z (main): started
  provenance: {"harness_session":"claude-code:c826b605-87ec-4aa8-8aea-62a46a0d13b8","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-26T23:28:19Z (coordination-closeout): resumed
  provenance: {"harness_session":"claude-code:c826b605-87ec-4aa8-8aea-62a46a0d13b8","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-26T23:30:20Z (coordination-closeout): baseline: just test in .worktrees/coordination-closeout, 860 passed
- 2026-10-26T23:34:43Z (coordination-closeout): item 4 ruling: repair on one standing tip keeps the every-field rule (spec §3.6 amendment 2026-10-26). Why: a caller cannot see the tip count at write time, so a repair a concurrent repair beat must not silently carry content over or refuse valid full content. Rejected: carry over on one tip, refuse repair on one tip.
- 2026-10-26T23:34:44Z (coordination-closeout): done
  provenance: {"harness_session":"claude-code:c826b605-87ec-4aa8-8aea-62a46a0d13b8","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-26T23:34:44Z (coordination-closeout): revise uses parse_unpinned; hypothesis reuse covered; single-tip repair pinned and recorded in spec §3.6; spec §6 amendment folded with the version-mismatch message; item 2 landed in sci-dce3b2. just test-fast 862 passed
  provenance: {"harness_session":"claude-code:c826b605-87ec-4aa8-8aea-62a46a0d13b8","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
