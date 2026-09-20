---
id: sci-1ef4b8
title: Conform science's help and version to the shared CLI vocabulary
status: done
priority: 2
size: xs
complexity: low
process: direct
owner: main
created: 2026-09-20T11:30:32Z
updated: 2026-09-20T14:00:53Z
started: 2026-09-20T13:51:21Z
completed: 2026-09-20T14:00:53Z
depends: []
tags: [cli, cross-project]
agent: claude-code/claude-opus-5
---

Adopt the shared CLI vocabulary: vendor tools/cli.toml (and tools/cli_surface.py), make the parser conform, add the conformance test. The steps are Task 5 in the ops plan docs/plans/2026-09-20-cli-conventions.md (spec docs/specs/2026-09-20-cli-conventions-design.md). Waits for the ops table task ops-c9ecf0 to land on ops main; the ops step ops-d42ad6 tracks this piece.

## Notes

- 2026-09-20T13:51:21Z (main): started
  provenance: {"harness_session":"claude-code:20e55bde-4aed-4a6f-993d-b44b058f509f","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-20T14:00:53Z (sci-1ef4b8): done
  provenance: {"harness_session":"claude-code:20e55bde-4aed-4a6f-993d-b44b058f509f","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-20T14:00:53Z (sci-1ef4b8): vendored the shared CLI table; science's help, help subcommand, -V/--version, --config as a path, and adapters --out now conform
  provenance: {"harness_session":"claude-code:20e55bde-4aed-4a6f-993d-b44b058f509f","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
