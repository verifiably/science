---
id: sci-4eeda7
title: Test + CI iteration cost audit
status: doing
priority: 2
size: m
complexity: mid
process: direct
owner: main
created: 2026-09-04T21:44:54Z
updated: 2026-09-24T02:55:39Z
started: 2026-09-24T02:55:24Z
depends: [ops-31f038]
tags: [testing]
---

Piece of ops-65837b (the cross-project audit in the ops hub). 1. Measure: full-suite wall time, and roughly how often agent full-suite runs fail here. 2. Add a fast or affected-only test target for the inner loop and point AGENTS.md at it; keep the full suite for commit and CI. 3. Use a quiet reporter so test output does not flood agent context. 4. Fix suite hygiene: sleeps, real network, unshared fixtures. Record the before and after numbers in a note on this task.

## Notes

- 2026-09-05T02:38:40Z (main): design: ops docs/specs/2026-09-04-test-ci-audit-design.md; follow §5: (1) justfile + vendored tools/tt, route existing hooks, CI, and documented test commands through it, verify a line lands under each agent; (2) after a week of runs, add a note reading 'baseline <date>: <tt-report --project numbers>'; (3) gates to §4.6, AGENTS.md line, hygiene; (4) close with before/after numbers
- 2026-09-05T08:22:08Z (test-ci-audit): step 1 baseline before wiring: 226 tests, 15 fail (all one TypeError from beliefs a1f7408 requiring authority on open_world; filed as an idea), pytest 1.0s, first uv run in a fresh worktree 19s to build .venv, then about 1s wall
- 2026-09-05T08:22:47Z (test-ci-audit): step 1 wired 2026-09-05: justfile + vendored tools/tt (version 2), .githooks installed with core.hooksPath, AGENTS.md created pointing at just test; verified three test-fast lines in the shared log with agent claude, null (by hand) and codex (env simulated, no Codex session available), none in a fallback log; testmon selects 15 of 226 on a repeat run
- 2026-09-05T09:02:27Z (read-authority): baseline suite green again at sci-5fca8b: 226 passed in about 11s of pytest time (the fixtures now build real worlds, which the earlier 1s runs never reached)
- 2026-09-12T16:34:06Z (main): Complexity mid: read the linked ops test/CI audit design and existing notes; the tree already has tools/tt, test-fast via pytest-testmon, and commit/push gates. Remaining work is bounded baseline and before/after measurement, evidence-led suite hygiene, and the prescribed guidance update; the approach is established but the report still determines which fixes are needed.
- 2026-09-24T02:55:24Z (main): started
  provenance: {"harness_session":"claude-code:dde7b5c4-c65b-4f4c-9ec0-bc965ee48ee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-24T02:55:39Z (main): Process direct: the ops design §4–5 settles the approach; remaining work is measurement and evidence-led hygiene within that scope. Folding in sci-9116e9 (worktree test root) since it blocks every worktree run.
