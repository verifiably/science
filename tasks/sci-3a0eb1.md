---
id: sci-3a0eb1
title: Coordination part 1 final-review minors
status: todo
priority: 3
size: xs
complexity: low
process: direct
created: 2026-09-24T14:26:54Z
updated: 2026-09-24T14:26:54Z
depends: []
parent: sci-c5528e
tags: [projects]
agent: claude-code/claude-opus-5-5
---

Deferred Minor findings from the 2026-09-24 reviews of coordination part 1: revise.py decides the address shape by counting '/' and then calls parse_address, duplicating science.coordination.parse_unpinned — use it; the divergent-view refusal is built twice (revise.py and coordination.resolve_one) — one helper; no test reuses a hypothesis source (only question); revise --repair demands every field even with a single standing tip (spec §3.6 literal — decide whether repair on one tip should carry over); spec §6's unamended sentence still says every coordination-class command refuses CoordinationUnavailable, which the dated amendment below it corrects — fold the amendment in, and name the version-mismatch message too.
