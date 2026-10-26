---
id: sci-bca8f1
title: "Launcher refuses a diverged initial project as unknown-project, while project-select refuses it as CoordinationRefused/divergent-view"
status: todo
priority: 3
size: xs
complexity: low
process: direct
created: 2026-10-26T23:17:15Z
updated: 2026-10-26T23:17:15Z
depends: []
tags: [projects]
agent: claude-code
origin: agent
---

Found while reviewing sci-dce3b2. A launcher (serve, mcp serve) whose --project or default_project names a project with two standing tips passes the address to the kernel, whose ProjectNotResolvable session.open_session maps to unknown-project with {tips} and no kind. project-select on the same project refuses kernel-refused {kind: CoordinationRefused, reason: divergent-view, tips}. Coordination spec §5.1's 2026-09-30 amendment says the launcher resolves its project as project-select does (§3.7), and §5.1 keeps unknown-project for a selection that resolves to no standing project; a diverged project does stand. Make the launcher refuse a diverged initial project in the project-select shape (refuse_coordination in science.coordination) before the session opens, keep unknown-project for no standing project, and pin both with a launcher test. sci-0d00d2 starts launchers against default_project, so it will hit this shape.

## Notes

- 2026-10-26T23:17:15Z (add): created
  provenance: {"harness_session":"claude-code:a32b916e-4ed3-4533-b453-d38ede488b81","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
