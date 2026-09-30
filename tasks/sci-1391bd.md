---
id: sci-1391bd
title: Selection query and the CLI's resolution order (P8)
status: done
priority: 1
size: m
complexity: mid
process: direct
owner: coordination-part2
created: 2026-09-30T11:25:02Z
updated: 2026-09-30T13:01:44Z
started: 2026-09-30T12:55:01Z
completed: 2026-09-30T13:01:44Z
depends: [sci-1217b5]
parent: sci-f95f8b
tags: [projects]
agent: claude-code/claude-fable-5-1
plan: docs/plans/2026-09-30-coordination-selection-and-reads.md
step: "Task 6: The selection query and the CLI's resolution order (P8)"
---

## Notes

- 2026-09-30T12:55:01Z (coordination-part2): started
- 2026-09-30T13:01:44Z (coordination-part2): done
- 2026-09-30T13:01:44Z (coordination-part2): Socket selection queries answer without invocation or ledger writes; CLI reads resolve explicit project, live selection, then absent-session default
