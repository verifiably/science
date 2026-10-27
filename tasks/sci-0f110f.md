---
id: sci-0f110f
title: A kernel RuleNotHeld raised while reading holdings reaches the person as internal-error
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-27T12:47:34Z
updated: 2026-10-27T12:47:34Z
depends: []
tags: [command-framework]
source: sci-0d00d2
agent: claude-code/claude-opus-5-5
origin: agent
---

In a world without the holdings-reducer rule, `claim` over MCP answered JSON-RPC -32603 Internal error; an in-process reproduction gave beliefs.errors.RuleNotHeld from science.holdings.reduced_heads (via ReadContext.observations, the resolution snapshot). The command surface's rule is a named refusal for a configuration state, never an internal error. Evidence: docs/records/2026-10-26-second-project-milestone.md §1.1 C1a, §1.3 r2, §5 F10 (defect).

## Notes

- 2026-10-27T12:47:34Z (add): created
  provenance: {"harness_session":"claude-code:8b479072-91d3-4b9c-b77c-d178525b6574","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
