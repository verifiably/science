---
id: sci-7fb155
title: "Brainstorm and spec sub-project 2, the command framework"
status: done
priority: 1
size: l
created: 2026-08-30T20:15:38Z
updated: 2026-09-01T00:33:16Z
depends: []
tags: [command-framework]
spec: docs/specs/2026-08-31-command-framework-design.md
---

Spec per the user/autonomy layer design §5 and §8 item 2 (in ~/d/beliefs/docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md): declaration schema, write classes, budgeted renderer, shared preamble, adapter generator with the Claude Code target, CLI and MCP over beliefs reads; the writer endpoint with bound permit, endpoint-set actor and session ledger lands in beliefs alongside. Carry in the four knowledge-model pressure points where they touch commands (view query language is sub-project 1's; output budget is a contract here).

## Notes

- 2026-08-31T10:41:58Z (command-framework): spec drafted in .worktrees/command-framework at docs/specs/2026-08-31-command-framework-design.md; session rulings: commands are the tools, dir-per-command TOML source, one WriterSession API with three frontings; user review pending
- 2026-08-31T14:55:14Z (command-framework): review round 1 incorporated: invocation-scoped writer, declaration-selected mint routes, registry/epoch command-unreachable, atomic invocation claim + reuse refusal, all-block write audit, MIN_OUTPUT_BUDGET, stateless read cursors (ledger stays write evidence), preamble view exception
- 2026-08-31T15:09:10Z (command-framework): review round 2 incorporated: corpus-write operation-kind amendment (session writes intent-fulfilling), fixed protocol grammars making MAX_CURSOR_BYTES/MIN_OUTPUT_BUDGET real, kind-to-route map as the one schema form, refusal envelope persisted in invocation-close (input digest only in open), sessionless CLI reads
- 2026-08-31T21:29:24Z (command-framework): spec and 13-task implementation plan approved and committed; deliverable tasks sci-829b37..sci-06e83a registered; beliefs-side contract tracked as beliefs-96a24a + beliefs-afbbff
- 2026-08-31T21:57:34Z (command-framework): plan review round 1 incorporated: MCP pinned to 2026-07-28 with process-lifetime writer session ruling (spec 9.3 amended), derived RecordBlock with (uid,id) audit, act-truth close ordering + concrete replay/continuation code, exact beliefs APIs from source (RegistryView tuples, EpochUnknown, ReadView.opened_at, certified_work fixture, world_case recipe), parser parents + adapters build + invocation-id emission + quoted frontmatter, cursor size cap, config validation, no test imports in serve, README/spec landing step
- 2026-08-31T22:20:06Z (command-framework): plan review round 2 incorporated: full 2026-07-28 _meta validation + resultType and no-protocol-sessions wording (spec 9.3), canonical ledger-rebuilt render on first write response + KeyVals audit mutation, spec 6.1 amended to close-before-render act-truth ordering, command-bound write continuation with declaration budget, near-fit renderer short-circuit + mid-character cursor refusal, beliefs dep pinned by name with uv source + worktree symlink and honest empty KIND_ACTS, null/bool/default/TOML refusal tests, socket unlink removed and 12/13 wiring split
- 2026-08-31T23:05:06Z (command-framework): plan review round 3 incorporated: namespaced io.modelcontextprotocol/* _meta keys, Tasks 12-13 fully executable (shared synthetic module, all four TOMLs, full __init__/loader/mcp/_via_service/serve-verb code, deterministic publishes ruling), refusal transport normalized (envelope helper, Refused.invocation_id, KernelRefusalValue, MCP/service structured replay tests), fail-closed typed claims + all-succeed race test, snake_case input grammar + handler default validation + one-line purpose + exactly-two-files checks, session-close finally paths, forged kind/title + command-bound cursor + declared-reads tests, python 3.11 floor, git-common-dir-derived symlink
- 2026-09-01T00:33:16Z (command-framework): plan review round 4 incorporated: invoke rewritten with early-minted iid attached to every refusal and exact _invoke_write routing line, KernelRefusalValue + WriterSession.close() recorded in spec (5.1, 6.3), serve() refuses socket before opening session and closes it on any constructor failure with malformed JSON inside the refusal boundary, real-config no-service test + successful _via_service test, resolve_handlers full signature-shape validation with falsifying tests, fences repaired, unknown-claim and absent-clientCapabilities N2 tests
