---
id: sci-5937be
title: "Test latency over limit: test-fast 93.984 s against 90 s"
status: doing
priority: 0
size: m
complexity: high
process: planned
owner: test-latency
created: 2026-10-02T01:00:04Z
updated: 2026-10-02T10:34:41Z
started: 2026-10-02T07:52:47Z
depends: []
tags: [halt, test-latency, testing]
source: "tt-latency:titan:2026-10-02T01:00:03Z"
spec: docs/specs/2026-10-02-world-fixture-snapshots-design.md
plan: docs/plans/2026-10-02-world-fixture-snapshots.md
---

Filed by tt-latency on titan: the median of successful, uncontended runs over the trailing window is over the limit in latency.toml (ops). The sci project is halted while this task is open: tasks start refuses new lower-priority work there. Each pair in a `breach:` note below is an obligation on the host it names. Fix the suite, then run `tt-latency verify <this id> --after <remedy timestamp>` on each host named; the task closes when verify exits 0, and the tasks done message carries its output.

Process: planned

## Notes

- 2026-10-02T01:00:04Z (main): breach: titan window 2026-09-25T01:00:03Z..2026-10-02T01:00:03Z: test-fast median 93.984 s, limit 90 s, 22 runs on 3 days
- 2026-10-02T01:32:00Z (feat/dc0381-mount-citations): halt override: attempted sci-0f8919 by 6051398c-8f0e-4511-a835-e90a0c6e83e9: halt sci-5937be (test-latency) filed mid-plan; continuing in-flight sci-dc0381 plan task per controller dispatch
- 2026-10-02T01:52:16Z (feat/dc0381-mount-citations): halt override: attempted sci-405c46 by 6051398c-8f0e-4511-a835-e90a0c6e83e9: halt sci-5937be filed mid-plan; continuing in-flight sci-dc0381 plan task per controller ruling
- 2026-10-02T01:59:47Z (feat/dc0381-mount-citations): halt override: attempted sci-4dca02 by 6051398c-8f0e-4511-a835-e90a0c6e83e9: halt sci-5937be filed mid-plan; continuing in-flight sci-dc0381 plan task per controller ruling
- 2026-10-02T02:15:33Z (main): sci-dc0381 (mount citations, branch feat/dc0381-mount-citations) adds ~30 world-fixture tests: final review estimates ~400-450 s serial, ~+50 s test-fast wall at 8 workers when testmon selects them (any config.py change). First step here: one pilot just test-fast from cold testmon on titan, main vs that branch head, record the delta
- 2026-10-02T07:52:47Z (main): started
  provenance: {"harness_session":"claude-code:fdd0a33b-81b7-41f1-82a2-bf45de0a4198","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-02T08:36:29Z (main): profile 2026-10-02 (titan, quiet-ish): full suite 683 passed in 140 s at 46698e5 on xdist; serial >2400 s (killed at 40 min). Cost is per-test fixture setup: test_mount_citations/test_epoch_verb ~10 s setup each (~40 tests), test_two_corpora 22-28 s each (13 tests, = sci-9b20ea); outliers test_belief_path_transports 49 s call, test_belief_path setup 14-34 s
- 2026-10-02T08:36:29Z (main): cProfile of build_shared_contract_world+add_mounted_evidence (11.0 s): atoms bind_project_volume runs certify_sqlite_wal on every bind (50 binds, 100 child processes, 2.7 s, uncached); 414 yaml.load calls 1.1 s; mint_fixture_run 4.9 s incl capture_environment 1.2 s. Remedy candidates: (a) atoms caches WAL certification per volume per process, (b) cache parsed contracts, (c) test fixtures build once per module and copy per test
- 2026-10-02T08:36:38Z (main): parked (waiting on user, decision): user picks remedy scope (recommended: science-side fixture snapshots + atoms task for cached WAL certification); then agent creates .worktrees/test-latency and drafts the spec
  provenance: {"harness_session":"claude-code:fdd0a33b-81b7-41f1-82a2-bf45de0a4198","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-02T08:58:54Z (test-latency): resumed
  provenance: {"harness_session":"claude-code:fdd0a33b-81b7-41f1-82a2-bf45de0a4198","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-02T08:59:04Z (test-latency): filed atoms-257797 (cache WAL certification per volume); science-side remedy is fixture snapshots, per user 2026-10-02
- 2026-10-02T09:06:17Z (test-latency): parked (waiting on user, review): user reviews docs/specs/2026-10-02-world-fixture-snapshots-design.md (in .worktrees/test-latency); on approval agent writes the plan
  provenance: {"harness_session":"claude-code:fdd0a33b-81b7-41f1-82a2-bf45de0a4198","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-02T09:23:04Z (test-latency): review: spec round 1 — verdict: revise; findings: P1 1, P2 2; reviewer: human
- 2026-10-02T09:23:56Z (test-latency): parked (waiting on user, review): user re-reviews docs/specs/2026-10-02-world-fixture-snapshots-design.md (round 2, in .worktrees/test-latency); on approval agent writes the plan
  provenance: {"harness_session":"claude-code:fdd0a33b-81b7-41f1-82a2-bf45de0a4198","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-02T09:32:56Z (test-latency): review: spec round 2 — verdict: revise; findings: P1 1; reviewer: human
- 2026-10-02T09:33:14Z (test-latency): parked (waiting on user, review): user re-reviews docs/specs/2026-10-02-world-fixture-snapshots-design.md (round 3, in .worktrees/test-latency); on approval agent writes the plan
  provenance: {"harness_session":"claude-code:fdd0a33b-81b7-41f1-82a2-bf45de0a4198","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-02T09:47:48Z (test-latency): review: spec round 3 — verdict: accept; findings: none; reviewer: human
- 2026-10-02T09:47:48Z (test-latency): resumed
  provenance: {"harness_session":"claude-code:fdd0a33b-81b7-41f1-82a2-bf45de0a4198","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-02T09:52:56Z (test-latency): parked (waiting on user, review): user reviews docs/plans/2026-10-02-world-fixture-snapshots.md (in .worktrees/test-latency) and picks execution; agent then executes step tasks sci-1e0712..sci-763b40
  provenance: {"harness_session":"claude-code:fdd0a33b-81b7-41f1-82a2-bf45de0a4198","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-02T10:05:23Z (test-latency): review: plan round 1 — verdict: revise; findings: P2 2; reviewer: human
- 2026-10-02T10:05:46Z (test-latency): parked (waiting on user, review): user re-reviews docs/plans/2026-10-02-world-fixture-snapshots.md (round 2, in .worktrees/test-latency) and picks execution; agent then executes sci-1e0712 first
  provenance: {"harness_session":"claude-code:fdd0a33b-81b7-41f1-82a2-bf45de0a4198","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-02T10:14:37Z (test-latency): review: plan round 2 — verdict: accept; findings: none; reviewer: human
- 2026-10-02T10:14:37Z (test-latency): resumed
  provenance: {"harness_session":"claude-code:fdd0a33b-81b7-41f1-82a2-bf45de0a4198","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-02T10:22:28Z (test-latency): before: test_mount_citations setup 217.8 s, test_epoch_verb setup 188.9 s
- 2026-10-02T10:24:00Z (test-latency): after: test_mount_citations setup 112.1 s, test_epoch_verb setup 57.5 s (one ~11.5 s build per worker, restores ~0.05 s)
- 2026-10-02T10:28:35Z (test-latency): before: test_two_corpora setup 292.7 s
- 2026-10-02T10:29:05Z (test-latency): halt override: attempted sci-9b20ea by fdd0a33b-81b7-41f1-82a2-bf45de0a4198: absorbed by the halt's own remedy (spec §7); closed in sci-16a04d's commit
- 2026-10-02T10:34:41Z (test-latency): after: test_two_corpora setup 193.2 s (module alone: ~1 test per worker, so each still builds; refusal tests build the cheap world, ~3.4 s)
