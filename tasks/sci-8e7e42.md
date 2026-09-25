---
id: sci-8e7e42
title: "Adopt host-budget: test and test-fast under host-budget run with -n auto"
status: done
priority: 2
size: s
complexity: low
process: direct
owner: main
created: 2026-09-24T19:38:54Z
updated: 2026-09-25T15:22:35Z
started: 2026-09-25T15:16:00Z
completed: 2026-09-25T15:22:35Z
depends: []
tags: []
source: ops-6d19bb
model: claude-opus-5-5
agent: claude-code/claude-opus-5-5
---

ops docs/specs/2026-09-24-host-budget-design.md, Consumers. -n 8 becomes -n auto (PYTEST_XDIST_AUTO_NUM_WORKERS comes from the budget) under host-budget run, tt outside. Nothing else changes: atoms probes are sequential and science does not call the certification runner. Lands before ops-eb9f2d's acceptance runs.

## Notes

- 2026-09-25T15:16:00Z (main): started
  provenance: {"harness_session":"claude-code:a80a2e70-e4ce-4a9b-887c-fc0b56920174","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-25T15:22:35Z (sci-8e7e42): done
  provenance: {"harness_session":"claude-code:a80a2e70-e4ce-4a9b-887c-fc0b56920174","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-25T15:22:35Z (sci-8e7e42): test, test-fast and hook-pre-push run under host-budget run with -n auto; full suite 476 passed on 16 workers (idle budget) and 8 (budget shared with concurrent grants)
  provenance: {"harness_session":"claude-code:a80a2e70-e4ce-4a9b-887c-fc0b56920174","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
