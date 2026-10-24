---
id: sci-b5c2e9
title: "Prior exposure and validation reservation as records, not a markdown ledger"
status: idea
priority: 2
created: 2026-10-18T19:19:53Z
updated: 2026-10-24T10:46:02Z
depends: []
parent: sci-8f15d4
tags: []
agent: claude-code
---

Filed 2026-10-18 from the multiple-myeloma program. Its protocol keeps two pieces of state outside the world: the prior-exposure ledger (which datasets and findings have already informed decisions; 592 dated entries so far) and the reservation assignment (each overlap group's role: discovery, unresolved, reserved, with the frozen inputs and digests it was computed from). Both are markdown under docs/, enforced by the program's own roster tool and a preflight recipe, and invisible to science and to any other project that adopts the same rules. sci-3eb5ef makes the rules a reusable skill; this is the complementary question of where the state lives: whether exposure and reservation are records science writes (a view over datasets and groups, append-only, with evidence), so a second program does not rebuild the ledger in prose and a belief read can see that an assessment rests on exposed data.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-24-exposure-reservation-reuse-brief.md — context and questions for this work
