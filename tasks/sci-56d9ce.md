---
id: sci-56d9ce
title: Two tests fail under the parallel full suite and pass alone
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-31T18:28:22Z
updated: 2026-10-31T18:28:22Z
depends: []
tags: [testing]
agent: claude-code/claude-opus-5-5
origin: agent
---

In the baseline `just test` run for sci-eccb43 on 2026-10-31 (titan, worktree at main 725adbd; 2 failed, 1137 passed, 202.7 s), two tests failed: tests/test_mount_citations.py::test_mounted_belief_needs_an_epoch (dispatch raised Refused kernel-refused: recipe-identity-mismatch) and tests/test_snapshot.py::test_a_confined_world_restores_its_sandbox_links_as_links. Both pass under `just test-one` in the main checkout and in the worktree. Find the shared state or load sensitivity that makes them order- or contention-dependent under -n auto, and fix it.

## Notes

- 2026-10-31T18:28:22Z (add): created
  provenance: {"harness_session":"claude-code:2d4f1b44-70f6-4dcf-877c-e39755156302","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
