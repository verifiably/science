---
id: sci-03ddea
title: Design commons catalogs and mirror adoption from the brief
status: todo
priority: 2
size: m
complexity: high
process: planned
created: 2026-10-30T19:21:06Z
updated: 2026-10-30T19:21:06Z
depends: []
parent: sci-009431
tags: [commons]
source: sci-8363b5
agent: codex
origin: agent
---

Why: Milestone 1 landed, but catalog commands, candidate provider imports and mirror adoption remain unimplemented. Read [ref:brief] and the approved commons design §§4, 7, 12, 14.
Done: A reviewed milestone 2 design settles command contracts, side-artifact persistence and replay, candidate imports, mirror pin confirmation, aggregation conflicts, inclusion audit trail, relation vocabulary using a first real catalog, and reproducibility summaries. Define acceptance for a host, reader and two-catalog aggregation, including refusal cases and locator handoff evidence for beliefs-42d201. Identify required existing repairs (especially sci-347a36) without duplicating them. Produce the design for human review; no implementation in this task.
Where: python/src/science/sharing.py, commands/adopt.py, transport_git.py, acceptance.py, tools/cli.toml and docs/specs/2026-09-30-science-commons-design.md. The new command vocabulary must originate in ops.
Ideas it wakes: On completion, run tasks note sci-8363b5 --no-reviewed "<finding and reviewed design>" before the result branch merges; update the brief.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-30-commons-next-milestones-brief.md — evidence, remaining decisions and wake obligations

## Notes

- 2026-10-30T19:21:06Z (add): created
  provenance: {"harness_session":"codex:01a18e3f-26f0-78e1-91b3-23ee5a854fd2","harness_session_source":"CODEX_THREAD_ID","origin":"agent"}
