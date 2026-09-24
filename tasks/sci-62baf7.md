---
id: sci-62baf7
title: science mcp serve serves the service socket
status: done
priority: 1
size: m
complexity: mid
process: direct
owner: coordination-commands
created: 2026-09-24T10:54:38Z
updated: 2026-09-24T13:09:55Z
started: 2026-09-24T12:52:22Z
completed: 2026-09-24T13:09:55Z
depends: [sci-08e27f]
parent: sci-c5528e
tags: [projects]
agent: claude-code/claude-opus-5-5
plan: docs/plans/2026-09-24-coordination-write-surface.md
step: "Task 8: `science mcp serve` serves the service socket"
---

## Notes

- 2026-09-24T12:52:22Z (coordination-commands): started
  provenance: {"harness_session":"claude-code:9d2d64bd-cdd3-4a14-add8-aa234fa311c0","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-24T13:09:55Z (coordination-commands): done
  provenance: {"harness_session":"claude-code:9d2d64bd-cdd3-4a14-add8-aa234fa311c0","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-24T13:09:55Z (coordination-commands): science mcp serve binds the service socket alongside its stdio loop, sharing the dispatcher; both launchers remove the socket they bound at clean close
  provenance: {"harness_session":"claude-code:9d2d64bd-cdd3-4a14-add8-aa234fa311c0","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
