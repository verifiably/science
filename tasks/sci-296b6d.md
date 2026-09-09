---
id: sci-296b6d
title: Surface session reconciliation findings at endpoint startup
status: todo
priority: 1
size: s
created: 2026-09-09T10:22:18Z
updated: 2026-09-09T10:22:18Z
depends: []
tags: [command-framework]
spec: docs/specs/2026-08-31-command-framework-design.md
---

Spec §5.3 rules that a crashed session's uncovered chain entry is classified outcome-unknown and 'surfaced as an audit finding naming the invocation and the entry ... interactively it is a finding for the person'. §6.2 calls that finding 'what tells them to look' at the crashed session's durable ledger.

beliefs already does the work: open_attended_session sets session.findings = reconcile_sessions(world_config, operations_root, exclude=session_id) on every open. Nothing in science reads it — 'grep -rn findings python/src/' returns no hit. science.serve and science.mcp.serve both discard it, so the mechanism the spec relies on to tell an operator to look does not exist.

Tasks 12 and 13 did not skip this; the plan never had a step for it.

Open questions for the work: where findings surface (a stderr line at startup, a Finding block on the first response, or a refusal to start when any are present), and whether the MCP server and the socket service answer the same way. Note that findings are per-endpoint-open, so a long-lived service reports once at startup.
