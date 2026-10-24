---
id: sci-1fd5e5
title: Establish the governed write/read route for exposure events and reservation assignments
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-24T10:46:00Z
updated: 2026-10-24T10:46:00Z
depends: []
parent: sci-8f15d4
tags: []
source: "sci-b5c2e9:scope:exposure-assignment-seams"
agent: codex
---

Question: What is the smallest permit-bound write/read route for a program's prior-exposure event and frozen reservation assignment, and which missing representation belongs upstream?

Where to start: [ref:brief] separates this representation question from existing aggregation research. Trace python/src/science/commands/dataset.py, commands/spec.py, commands/assess.py and the configured writer interface; inspect the current program protocol and one ledger event and assignment snapshot identified by mm-0f5df1 and mm-69f82e. Use sci-3eb5ef and sci-0c9e0f for protocol/guidance ownership. Check beliefs-9bf498 and beliefs-5e66ba outcomes when available; do not wait for them to begin this inventory.

Bound: Trace one existing exposure event and one assignment through their consumers. Inventory identities, evidence, input digests, supersession and invalidation, and compare those needs with the existing kernel writer and record contracts. Establish a minimal synthetic example and the observations a future implementation must preserve; mark unavailable evidence explicitly. No full-ledger migration, cohort/phenotype reads, fresh reservation run, downloads, new command or storage implementation. Do not repeat the belief-aggregation inventory, recommend a weighted policy, solve participant matching (mm-af6b59) or model-originated attribution (mm-245d2f), or choose a new program.

Expected result: Record a supported/unsupported seam table, source revisions, one minimal exposure/assignment example, and the smallest next owner and check on this task and in [ref:brief]. Distinguish observed current support from proposed records and design questions. Identify any kernel prerequisite by existing task id or recommend a bounded follow-up; do not silently create a second store. Done when both examples have an evidence-backed disposition and next work can be scoped without rediscovering the representation boundary.

Ideas it wakes: On completion, before this result's branch merges, run `tasks note sci-b5c2e9 --no-reviewed "<write/read support, missing representation and next owner>"` and `tasks note sci-861d8f --no-reviewed "<shared components available or missing; sequencing consequence>"`; update [ref:brief].

## References

- brief (input, required, kind=brief): docs/notes/2026-10-24-exposure-reservation-reuse-brief.md — bounded representation question and existing owners
