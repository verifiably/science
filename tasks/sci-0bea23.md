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
updated: 2026-10-31T19:03:59Z
started: 2026-10-31T18:41:31Z
depends: []
tags: [halt, test-latency, testing]
source: "tt-latency:titan:2026-10-30T18:00:00Z"
spec: docs/specs/2026-10-31-snapshot-lineages-design.md
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
