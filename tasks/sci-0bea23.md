---
id: sci-0bea23
title: "Test latency over limit: test-fast 142.736 s against 90 s"
status: doing
priority: 0
size: m
complexity: high
process: planned
owner: perf/test-latency
created: 2026-10-30T18:00:08Z
updated: 2026-11-01T01:56:13Z
started: 2026-10-31T18:41:31Z
depends: []
tags: [halt, test-latency, testing]
source: "tt-latency:titan:2026-10-30T18:00:00Z"
spec: docs/specs/2026-10-31-snapshot-lineages-design.md
plan: docs/plans/2026-10-31-snapshot-lineages.md
---

Filed by tt-latency on titan: the median of successful, uncontended, unwidened runs over the trailing window is over the limit in latency.toml (ops). The sci project is halted while this task is open: tasks start refuses new lower-priority work there. Each pair in a `breach:` note below is an obligation on the host it names. Fix the suite, then run `tt-latency verify <this id> --after <remedy timestamp>` on each host named; the task closes when verify exits 0, and the tasks done message carries its output.

Process: planned

## Notes

- 2026-10-30T18:00:08Z (add): created
- 2026-10-30T18:00:10Z (main): breach: titan window 2026-10-23T18:00:00Z..2026-10-30T18:00:00Z: test-fast median 142.736 s, limit 90 s, 20 runs on 4 days
- 2026-10-30T19:45:58Z (main): halt override: attempted sci-300dab by 01a18e58-0cdf-75c2-bf7d-f4ac22417069: User explicitly requested sci-300dab; investigate and prepare its design despite the existing test-latency halt sci-0bea23.
- 2026-10-30T23:02:03Z (sci-300dab-stores): halt override: attempted sci-14a324 by 01a18e58-0cdf-75c2-bf7d-f4ac22417069: Execute approved readable-stores plan despite open timing halt sci-0bea23
- 2026-10-30T23:15:29Z (sci-300dab-stores): halt override: attempted sci-bb8611 by 01a18e58-0cdf-75c2-bf7d-f4ac22417069: Execute approved readable-stores plan despite open timing halt sci-0bea23
- 2026-10-30T23:26:25Z (sci-300dab-stores): halt override: attempted sci-e5d803 by 01a18e58-0cdf-75c2-bf7d-f4ac22417069: Execute approved readable-stores plan despite open timing halt sci-0bea23
- 2026-10-31T18:21:54Z (main): halt override: attempted sci-eccb43 by 2d4f1b44-70f6-4dcf-877c-e39755156302: User explicitly requested sci-eccb43 despite open test-latency halt sci-0bea23
- 2026-10-31T18:41:31Z (main): started
  provenance: {"harness_session":"claude-code:e1c106c7-398b-4f30-8ca8-d851dbb5e76b","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-31T18:42:27Z (perf/test-latency): resumed
  provenance: {"harness_session":"claude-code:e1c106c7-398b-4f30-8ca8-d851dbb5e76b","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-31T19:03:16Z (perf/test-latency): diagnosis 2026-10-31 (titan, c701049): full suite 1140 tests 179-195 s; 82 per-worker snapshot builds sum 1591 s (53-149 s/worker) because each commons builder rebuilds its whole prefix chain; testmon ~1.5x per test; one profiled test 84 s, 76 s building sibling_publications, ~40 s in atoms chain decode/validate. Filed atoms-eaadf0 (decode memo). sysmon coverage core rejected (no dynamic contexts). Spec: docs/specs/2026-10-31-snapshot-lineages-design.md at ced2be9 in worktree .worktrees/test-latency (branch perf/test-latency).
- 2026-10-31T19:03:42Z (perf/test-latency): attached: snapshot-builds-baseline-2026-10-31.jsonl (4678 bytes): Per-worker first snapshot() build times, full suite at c701049 on titan, 16 workers, 179 s run: 82 builds, 1591 s
- 2026-10-31T19:03:44Z (perf/test-latency): attached: snaptime-plugin.py (536 bytes): pytest plugin that logs each first snapshot() build (run: SNAP_OUT=<file> PYTHONPATH=<dir> just test-one tests -p snaptime -n auto --dist worksteal)
- 2026-10-31T19:03:46Z (perf/test-latency): retained: {"host":"titan","kind":"worktree","path":".worktrees/test-latency","state":"kept","verification":"verified","purpose":"branch perf/test-latency holding the snapshot-lineages spec (ced2be9) and the coming implementation","next_owner":"task:sci-0bea23","cleanup_trigger":"perf/test-latency merged into main and tt-latency verify recorded"}
- 2026-10-31T19:03:59Z (perf/test-latency): retention checkpoint: observed 2026-10-31T19:03:59Z on titan; basis sci in-tree . d15fecd7fad48f7cc4d870c2df74a0b2539c73ce:tasks/sci-0bea23.md; retained by refs/heads/perf/test-latency; this host: kept verified 1, kept unknown 0, released 0; changed 1. Rechecked all kept/verified items on this host. Other hosts retain their own dated observations. Next: user reviews the spec, then write the plan.
  provenance: {"harness_session":"claude-code:e1c106c7-398b-4f30-8ca8-d851dbb5e76b","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-31T19:04:11Z (perf/test-latency): parked (waiting on user, review): User reviews docs/specs/2026-10-31-snapshot-lineages-design.md at ced2be9 (branch perf/test-latency, worktree .worktrees/test-latency); on accept, the agent writes the implementation plan
  provenance: {"harness_session":"claude-code:e1c106c7-398b-4f30-8ca8-d851dbb5e76b","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-31T20:04:24Z (perf/test-latency): resumed
  provenance: {"harness_session":"claude-code:e1c106c7-398b-4f30-8ca8-d851dbb5e76b","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-31T20:04:26Z (perf/test-latency): review: spec round 1 — verdict: revise; findings: P1 3, P2 1; reviewer: codex/gpt-6.1-sol
- 2026-10-31T20:15:32Z (perf/test-latency): review: spec round 2 — verdict: revise; findings: P2 3, P3 9; reviewer: claude-code/claude-opus-5-5
- 2026-10-31T20:16:53Z (perf/test-latency): spec revision 3 at 0471907 answers round 1 (codex: copy_value for mappingproxy leaves, declaration objects for ancestry, construction vs live restores, build_bound_fetched_only) and round 2 (self: restore_tree for step-internal restores, per-kind identity, isolation runs, P3s incl. limitations §2.6)
- 2026-10-31T20:16:55Z (perf/test-latency): retention checkpoint: observed 2026-10-31T20:16:55Z on titan; basis sci in-tree . 86c2aa10ba37f02b0a54af6e79ef719a5e5f30ae:tasks/sci-0bea23.md; retained by refs/heads/perf/test-latency; this host: kept verified 1, kept unknown 0, released 0; changed 0. Rechecked all kept/verified items on this host. Other hosts retain their own dated observations. Next: spec review round 3.
  provenance: {"harness_session":"claude-code:e1c106c7-398b-4f30-8ca8-d851dbb5e76b","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-31T20:16:57Z (perf/test-latency): parked (waiting on user, review): User (or codex) reviews spec revision 3: docs/specs/2026-10-31-snapshot-lineages-design.md at 0471907 on perf/test-latency (.worktrees/test-latency); on accept, the agent writes the plan
  provenance: {"harness_session":"claude-code:e1c106c7-398b-4f30-8ca8-d851dbb5e76b","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-31T20:27:08Z (perf/test-latency): resumed
  provenance: {"harness_session":"claude-code:e1c106c7-398b-4f30-8ca8-d851dbb5e76b","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-31T20:27:10Z (perf/test-latency): review: spec round 3 — verdict: accept; findings: P3 1; reviewer: codex/gpt-6.1-sol
- 2026-10-31T20:27:11Z (perf/test-latency): spec revision 3 (0471907) accepted for planning by Keith 2026-10-31; P3 carried into the plan: the warm test-fast benchmark uses a temporary executable-code change in one test module and records the selected count
- 2026-10-31T20:31:05Z (perf/test-latency): retention checkpoint: observed 2026-10-31T20:31:05Z on titan; basis sci in-tree . 1a7f718b07c5fe998994ee75d24ee4eb6dc3a122:tasks/sci-0bea23.md; retained by refs/heads/perf/test-latency; this host: kept verified 1, kept unknown 0, released 0; changed 0. Rechecked all kept/verified items on this host. Other hosts retain their own dated observations. Next: plan review.
  provenance: {"harness_session":"claude-code:e1c106c7-398b-4f30-8ca8-d851dbb5e76b","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-31T20:31:07Z (perf/test-latency): parked (waiting on user, review): User reviews docs/plans/2026-10-31-snapshot-lineages.md at dc48b68 (perf/test-latency, .worktrees/test-latency); on accept, the agent runs Setup then steps sci-6ef17c, sci-f84065, sci-1a9c25
  provenance: {"harness_session":"claude-code:e1c106c7-398b-4f30-8ca8-d851dbb5e76b","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-31T20:49:31Z (perf/test-latency): resumed
  provenance: {"harness_session":"claude-code:e1c106c7-398b-4f30-8ca8-d851dbb5e76b","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-31T20:49:32Z (perf/test-latency): review: plan round 1 — verdict: revise; findings: P2 3, P3 1; reviewer: codex/gpt-6.1-sol
- 2026-10-31T20:50:22Z (perf/test-latency): plan revision 2 at 4254cf3 answers plan round 1: ancestor identity checks + impostor-ancestor test, plugin file snaptime_lineage.py + pilot step, reverse-order snippet under explicit bash, retry test asserts half.txt absent at step entry
- 2026-10-31T20:50:24Z (perf/test-latency): retention checkpoint: observed 2026-10-31T20:50:24Z on titan; basis sci in-tree . b9a175683abad880b0c363c1124e3dc32d12b62a:tasks/sci-0bea23.md; retained by refs/heads/perf/test-latency; this host: kept verified 1, kept unknown 0, released 0; changed 0. Rechecked all kept/verified items on this host. Other hosts retain their own dated observations. Next: plan review round 2.
  provenance: {"harness_session":"claude-code:e1c106c7-398b-4f30-8ca8-d851dbb5e76b","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-31T20:50:25Z (perf/test-latency): parked (waiting on user, review): User reviews plan revision 2: docs/plans/2026-10-31-snapshot-lineages.md at 4254cf3 (perf/test-latency, .worktrees/test-latency); on accept, the agent runs Setup then sci-6ef17c, sci-f84065, sci-1a9c25 inline with a fresh whole-branch review
  provenance: {"harness_session":"claude-code:e1c106c7-398b-4f30-8ca8-d851dbb5e76b","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-31T20:54:32Z (perf/test-latency): resumed
  provenance: {"harness_session":"claude-code:e1c106c7-398b-4f30-8ca8-d851dbb5e76b","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-31T20:54:34Z (perf/test-latency): review: plan round 2 — verdict: accept; findings: none; reviewer: codex/gpt-6.1-sol
- 2026-10-31T20:54:36Z (perf/test-latency): plan revision 2 (4254cf3) approved for implementation by Keith 2026-10-31; execution inline (executing-plans) with a fresh whole-branch review
- 2026-10-31T22:02:10Z (perf/test-latency): attached: snaptime_lineage.py (707 bytes): pytest plugin logging each lineage link build (wraps helpers.snapshot._build_link); run: SNAP_OUT=<file> PYTHONPATH=<dir> just test-one tests -p snaptime_lineage -n auto --dist worksteal
- 2026-10-31T22:02:12Z (perf/test-latency): attached: snapshot-links-after-run1-loaded-2026-10-31.jsonl (12913 bytes): Lineage link builds, full suite at 2fb2d8d, run 1 under a concurrent suite (load 11.6 -> 53.8): 223 links, 1196 s, worst worker 138 s
- 2026-10-31T22:02:13Z (perf/test-latency): attached: snapshot-links-after-run2-quiet-2026-10-31.jsonl (13514 bytes): Lineage link builds, full suite at 2fb2d8d, run 2 at load 7.2 start: 234 links, 937 s, worst worker 110 s, best 14 s
- 2026-10-31T22:02:15Z (perf/test-latency): measurements 2026-10-31 titan (before = 4254cf3 tree, after = 2fb2d8d): snapshot builds 1591 s / worst worker 149 s (82 builds) -> 937 s / 110 s quiet run (234 links, each at most once per worker; projection 845/95; threshold 1000 met) and 1196 s / 138 s in a run contaminated by a concurrent suite (load to 54); full suite just test 1140 in 164.8 s (user 24m09) -> 1155 in 136.3 s (user 17m44); test-fast cold (all selected) 1140 in 288.4 s -> 1155 in 223.9 s; test-fast warm (one test-body edit in test_snapshot.py) 1 selected 3.7 s -> 1 selected 3.6 s. Broad test-fast selections stay well over 90 s, as the spec anticipated (§4).
- 2026-10-31T22:10:00Z (perf/test-latency): review: impl round 1 — verdict: accept; findings: Minor 4; reviewer: claude-code/claude-opus-5-5
- 2026-10-31T22:21:35Z (perf/test-latency): review: impl round 2 — verdict: accept; findings: Minor 3; reviewer: claude-code/claude-opus-5-5
- 2026-10-31T22:21:51Z (perf/test-latency): attached: snapshot-lineages-ledger.md (5803 bytes): Execution ledger for plan docs/plans/2026-10-31-snapshot-lineages.md: setup baselines, per-task results, rulings, deferred minors
- 2026-10-31T22:21:53Z (perf/test-latency): attached: final-review-report.md (10668 bytes): Final whole-branch review c701049..09367a9 (claude-opus-5-5): ready to merge, Minor 4
- 2026-10-31T22:21:54Z (perf/test-latency): attached: fix-rereview-report.md (5897 bytes): Scoped re-review of fix e2a5236 (claude-opus-5-5): resolved, Minor 3
- 2026-10-31T22:21:56Z (perf/test-latency): rulings and deferred minors for the snapshot-lineages plan are in files:snapshot-lineages-ledger.md (4 execution rulings, 2 final-review re-grades, 5 minor (deferred))
- 2026-10-31T22:25:25Z (main): retained: {"host":"titan","kind":"worktree","path":".worktrees/test-latency","state":"released","verification":"verified","purpose":"merged into main as f57543a (merged suite 1157 passed in 139 s); ignored files discarded as regenerable (.venv, caches, .testmondata) or attached (ledger, review reports); branch perf/test-latency deleted after ancestry check","next_owner":"none","cleanup_trigger":"none"}
- 2026-10-31T22:25:27Z (main): merged perf/test-latency into main as f57543a (2026-10-31T22:22:06Z, the tt-latency verify cutoff); merged-result just test 1157 passed in 139.3 s; worktree removed, branch deleted; tt-report run. Halt stays open until tt-latency verify passes on titan.
- 2026-10-31T22:25:29Z (main): retention checkpoint: observed 2026-10-31T22:25:29Z on titan; basis sci in-tree . 931852b9d3c1a3e7ec23d4e9979af28178c33eea:tasks/sci-0bea23.md; retained by refs/heads/main; this host: kept verified 0, kept unknown 0, released 1; changed 1. No kept items remain on this host. Other hosts retain their own dated observations.
  provenance: {"harness_session":"claude-code:e1c106c7-398b-4f30-8ca8-d851dbb5e76b","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-31T22:25:31Z (main): parked (waiting on agent): Once 3+ successful test-fast runs after 2026-10-31T22:22:06Z exist on titan, run from the main checkout: tt-latency verify sci-0bea23 --after 2026-10-31T22:22:06Z (attach output as verify-titan.txt). If it fails (broad selections measured 224 s cold), the user chooses between adopting sci-6af05a and a reviewed latency.toml exception.
  provenance: {"harness_session":"claude-code:e1c106c7-398b-4f30-8ca8-d851dbb5e76b","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-31T22:52:00Z (main): halt override: attempted sci-409235 by c721656d-65c9-4353-b42b-9116120745b0: user asked in session to take sci-409235; halt remedy merged f57543a, halt waits only on tt-latency verify runs accumulating
- 2026-11-01T00:18:02Z (feat/holdings-recheck): halt override: attempted sci-3578d6 by 224a01cb-bb9b-421b-ac3d-a55e9a312f6f: step of sci-409235, which the user asked to execute in session; halt sci-0bea23 waits only on tt-latency verify runs
- 2026-11-01T00:21:06Z (feat/holdings-recheck): halt override: attempted sci-08833f by 224a01cb-bb9b-421b-ac3d-a55e9a312f6f: step of sci-409235, user asked to execute it in session; halt sci-0bea23 waits only on tt-latency verify
- 2026-11-01T00:31:55Z (feat/holdings-recheck): halt override: attempted sci-f4109b by 224a01cb-bb9b-421b-ac3d-a55e9a312f6f: step of sci-409235, user asked to execute it in session; halt sci-0bea23 waits only on tt-latency verify
- 2026-11-01T00:39:59Z (feat/holdings-recheck): halt override: attempted sci-5e18bc by 224a01cb-bb9b-421b-ac3d-a55e9a312f6f: step of sci-409235, user asked to execute it in session; halt sci-0bea23 waits only on tt-latency verify
- 2026-11-01T01:56:13Z (main): halt override: attempted sci-62e5aa by 83e6ed02-8814-4b88-8d94-828898b574a0: user asked in session to take sci-62e5aa; halt sci-0bea23 remedy merged f57543a and waits only on tt-latency verify runs
