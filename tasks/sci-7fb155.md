---
id: sci-7fb155
title: "Brainstorm and spec sub-project 2, the command framework"
status: todo
priority: 1
size: l
created: 2026-08-30T20:15:38Z
updated: 2026-08-31T14:55:14Z
depends: []
tags: [command-framework]
---

Spec per the user/autonomy layer design §5 and §8 item 2 (in ~/d/beliefs/docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md): declaration schema, write classes, budgeted renderer, shared preamble, adapter generator with the Claude Code target, CLI and MCP over beliefs reads; the writer endpoint with bound permit, endpoint-set actor and session ledger lands in beliefs alongside. Carry in the four knowledge-model pressure points where they touch commands (view query language is sub-project 1's; output budget is a contract here).

## Notes

- 2026-08-31T10:41:58Z (command-framework): spec drafted in .worktrees/command-framework at docs/specs/2026-08-31-command-framework-design.md; session rulings: commands are the tools, dir-per-command TOML source, one WriterSession API with three frontings; user review pending
- 2026-08-31T14:55:14Z (command-framework): review round 1 incorporated: invocation-scoped writer, declaration-selected mint routes, registry/epoch command-unreachable, atomic invocation claim + reuse refusal, all-block write audit, MIN_OUTPUT_BUDGET, stateless read cursors (ledger stays write evidence), preamble view exception
