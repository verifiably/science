---
id: sci-00b45a
title: Bound service socket request and reply frames
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-09-30T14:40:23Z
updated: 2026-09-30T14:40:24Z
depends: [sci-f95f8b]
tags: [command-framework]
source: sci-f95f8b
agent: codex
---

Deferred transport ceiling explicitly recorded during coordination part 2 (sci-f95f8b): its five-second selection-query deadline bounds waiting but not response bytes. Current _ambient_selection in python/src/science/cli.py appends received chunks without a size bound; _via_service reads a reply with an unbounded readline; service_server in python/src/science/serve.py iterates unbounded request lines. A local peer can consume substantial memory with an oversized frame. This was outside the approved part 2 scope, not a newly discovered selection defect.

Set explicit byte bounds at these existing socket boundaries before JSON parsing. Choose bounds consistent with supported request and report budgets; inspect/reuse the existing MCP request ceiling where applicable, without inventing a generic transport layer. Preserve newline framing, the total selection-query deadline, and absent-listener-only default fallback. Define predictable oversized-request refusal/connection behavior and treat an oversized client reply as internal-error rather than fallback.

Add focused real AF_UNIX checks with small patched limits: oversized service input creates no invocation/ledger effects, oversized replies terminate with the defined error, and ordinary selection queries and command traffic still work. Keep broader authentication, write-response deadlines, and launcher shutdown changes out of scope; lifecycle work is already sci-6ffb7f.

## Notes

- 2026-09-30T14:40:23Z (coordination-part2): Pre-close ruling follow-up from sci-f95f8b: existing unbounded socket framing was deliberately retained; this task addresses that known ceiling.
