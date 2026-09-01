---
id: sci-51ab20
title: Preamble and the Claude Code adapter generator
status: done
priority: 1
size: m
owner: command-framework
created: 2026-08-31T21:29:15Z
updated: 2026-09-01T14:31:59Z
depends: [sci-cd5a04]
tags: [command-framework]
spec: docs/specs/2026-08-31-command-framework-design.md
plan: docs/plans/2026-08-31-command-framework.md
step: "Task 10: Preamble and the Claude Code adapter generator"
---

## Notes

- 2026-09-01T13:01:48Z (command-framework): Subagent-driven Task 10 started; compact shared preamble and deterministic committed Claude Code adapter tree.
- 2026-09-01T13:05:29Z (command-framework): Shared command preamble and deterministic Claude Code adapter generator with committed-tree diff implemented
- 2026-09-01T13:08:35Z (command-framework): Review round 1: preflight collisions and authored-skill filesystem shapes before mutating generated output; reject symlinks/special entries.
- 2026-09-01T13:10:50Z (command-framework): Fix round 1: preflight authored-skill collisions and reject symlink/special entries before output mutation; sentinel preservation and symlink tests added
- 2026-09-01T14:31:59Z (command-framework): Final review: use one source-safe shared build preflight for framework and adapter builds, validating handlers/collisions and pre-reading sources before output mutation.
