---
id: sci-a7cd0d
title: "quarry: The search framework and the search and show commands"
status: done
priority: 2
complexity: mid
process: direct
owner: quarry-design
created: 2026-10-10T19:11:12Z
updated: 2026-10-10T21:08:22Z
started: 2026-10-10T20:56:44Z
completed: 2026-10-10T21:08:21Z
depends: [sci-882f28]
parent: sci-ba7150
tags: []
agent: claude-code/claude-opus-5-5
plan: docs/plans/2026-10-10-quarry-foundation.md
step: "Task 7: The search framework and the search and show commands"
---

## Notes

- 2026-10-10T20:48:08Z (quarry-design): Pre-implementation probe: global hoisting steals --trace and -Cexample when they are the string value of --native. Task 7 must preserve option values verbatim while allowing real root globals in every supported position; add a CLI regression with a fake adapter.
- 2026-10-10T20:56:44Z (quarry-design): started
  provenance: {"harness_session":"codex:01a12769-e196-7e72-829a-066a98c2baa4","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-10T20:56:44Z (quarry-design): halt override: started past sci-5937be by 01a12769-e196-7e72-829a-066a98c2baa4: Approved quarry foundation search task changes only isolated quarry code, no science runtime or tests.
- 2026-10-10T21:00:07Z (quarry-design): Self-review correction authorized: normalize relative-date arithmetic overflow to ValueError so the CLI reports usage error exit 2; prove direct parser and CLI behavior RED→GREEN.
- 2026-10-10T21:04:40Z (quarry-design): review: impl round 1 — verdict: revise; findings: Important 2; reviewer: codex/gpt-6.1-sol
- 2026-10-10T21:08:21Z (quarry-design): review: impl round 2 — verdict: accept; findings: none; reviewer: codex/gpt-6.1-sol
- 2026-10-10T21:08:21Z (quarry-design): done
  provenance: {"harness_session":"codex:01a12769-e196-7e72-829a-066a98c2baa4","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-10T21:08:22Z (quarry-design): Search/query/results/adapter contract and CLI at7c2d358; blank-organism and native-failure coverage fixes1af1487 independently accepted. Native values preserved with Click metadata; refusal spies and date-overflow regressions cover boundaries. 205 tests/check pass.
  provenance: {"harness_session":"codex:01a12769-e196-7e72-829a-066a98c2baa4","harness_session_source":"CODEX_THREAD_ID"}
