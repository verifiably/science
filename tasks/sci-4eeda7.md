---
id: sci-4eeda7
title: Test + CI iteration cost audit
status: done
priority: 2
size: m
complexity: mid
process: direct
owner: main
created: 2026-09-04T21:44:54Z
updated: 2026-09-24T03:22:07Z
started: 2026-09-24T02:55:24Z
completed: 2026-09-24T03:22:07Z
depends: [ops-31f038]
tags: [testing]
model: "claude-opus-5-5[1m]"
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
- 2026-09-24T03:22:07Z (test-audit): baseline 2026-09-23 (tt-report --project sci): test 52 runs, median 42.7 s, p90 301.9 s, fail 0.3; test-fast 44 runs, median 62.5 s, p90 833.9 s, fail 0.7; fast/full by agents 0.83; bypasses 54. Growth: 226 tests 12 s (09-05) -> 393 tests 626-660 s (09-23).
- 2026-09-24T03:22:07Z (test-audit): cause: every test builds its own certified world (~3.3 s floor, 1.5 s of it atoms' certify_sqlite_wal spawning 62 children per build); boundary-run tests 13-40 s. I/O and subprocess bound, not CPU (load ~6 at 16 workers). Certification cost filed as atoms-06c32b.
- 2026-09-24T03:22:07Z (test-audit): after 2026-09-23: pytest-xdist -n 8 --dist worksteal in both test recipes. test 626 s -> 79 s (load dist 107 s, 16 workers 102 s); test-fast on an 8-test selection 104 s -> 52 s, bounded by the slowest test. Hygiene: no sleeps or network; test_serve socket paths moved to a short /tmp dir (tmp_path under xdist exceeded the 107-byte AF_UNIX cap). Worktrees run the suite unset (sci-9116e9).
- 2026-09-24T03:22:07Z (test-audit): done
  provenance: {"harness_session":"claude-code:dde7b5c4-c65b-4f4c-9ec0-bc965ee48ee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-24T03:22:07Z (test-audit): full suite 626 s -> 79 s via xdist (8 workers, worksteal); worktree test root fixed; test_serve socket hygiene; AGENTS.md points at test-fast; certification cost filed to atoms-06c32b
  provenance: {"harness_session":"claude-code:dde7b5c4-c65b-4f4c-9ec0-bc965ee48ee6","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
