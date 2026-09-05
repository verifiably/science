---
id: sci-4eeda7
title: Test + CI iteration cost audit
status: doing
priority: 2
size: m
owner: test-ci-audit
created: 2026-09-04T21:44:54Z
updated: 2026-09-05T08:22:47Z
depends: [ops-31f038]
tags: [testing]
---

Piece of ops-65837b (the cross-project audit in the ops hub). 1. Measure: full-suite wall time, and roughly how often agent full-suite runs fail here. 2. Add a fast or affected-only test target for the inner loop and point AGENTS.md at it; keep the full suite for commit and CI. 3. Use a quiet reporter so test output does not flood agent context. 4. Fix suite hygiene: sleeps, real network, unshared fixtures. Record the before and after numbers in a note on this task.

## Notes

- 2026-09-05T02:38:40Z (main): design: ops docs/specs/2026-09-04-test-ci-audit-design.md; follow §5: (1) justfile + vendored tools/tt, route existing hooks, CI, and documented test commands through it, verify a line lands under each agent; (2) after a week of runs, add a note reading 'baseline <date>: <tt-report --project numbers>'; (3) gates to §4.6, AGENTS.md line, hygiene; (4) close with before/after numbers
- 2026-09-05T08:22:08Z (test-ci-audit): step 1 baseline before wiring: 226 tests, 15 fail (all one TypeError from beliefs a1f7408 requiring authority on open_world; filed as an idea), pytest 1.0s, first uv run in a fresh worktree 19s to build .venv, then about 1s wall
- 2026-09-05T08:22:47Z (test-ci-audit): step 1 wired 2026-09-05: justfile + vendored tools/tt (version 2), .githooks installed with core.hooksPath, AGENTS.md created pointing at just test; verified three test-fast lines in the shared log with agent claude, null (by hand) and codex (env simulated, no Codex session available), none in a fallback log; testmon selects 15 of 226 on a repeat run
