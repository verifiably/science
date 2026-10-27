---
id: sci-20aee0
title: No science command declares a dataset without holding it
status: todo
priority: 3
size: s
complexity: mid
process: planned
created: 2026-10-27T12:47:00Z
updated: 2026-10-27T12:47:00Z
depends: []
tags: [command-framework]
source: sci-0d00d2
agent: claude-code/claude-opus-5-5
origin: agent
---

`science dataset` always holds bytes; the kernel's Declared state (pinned digests, no holdings observation) was reachable only by adding a dataset node through the writer from a driver. A question over data not yet held cannot be asked through the surface. Evidence: docs/records/2026-10-26-second-project-milestone.md §3.1 (the declaration recipe), §5 F3 (surface-gap).

## Notes

- 2026-10-27T12:47:00Z (add): created
  provenance: {"harness_session":"claude-code:8b479072-91d3-4b9c-b77c-d178525b6574","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
