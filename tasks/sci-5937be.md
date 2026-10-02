---
id: sci-5937be
title: "Test latency over limit: test-fast 93.984 s against 90 s"
status: todo
priority: 0
size: m
complexity: high
process: planned
created: 2026-10-02T01:00:04Z
updated: 2026-10-02T02:15:33Z
depends: []
tags: [halt, test-latency, testing]
source: "tt-latency:titan:2026-10-02T01:00:03Z"
---

Filed by tt-latency on titan: the median of successful, uncontended runs over the trailing window is over the limit in latency.toml (ops). The sci project is halted while this task is open: tasks start refuses new lower-priority work there. Each pair in a `breach:` note below is an obligation on the host it names. Fix the suite, then run `tt-latency verify <this id> --after <remedy timestamp>` on each host named; the task closes when verify exits 0, and the tasks done message carries its output.

Process: planned

## Notes

- 2026-10-02T01:00:04Z (main): breach: titan window 2026-09-25T01:00:03Z..2026-10-02T01:00:03Z: test-fast median 93.984 s, limit 90 s, 22 runs on 3 days
- 2026-10-02T01:32:00Z (feat/dc0381-mount-citations): halt override: attempted sci-0f8919 by 6051398c-8f0e-4511-a835-e90a0c6e83e9: halt sci-5937be (test-latency) filed mid-plan; continuing in-flight sci-dc0381 plan task per controller dispatch
- 2026-10-02T01:52:16Z (feat/dc0381-mount-citations): halt override: attempted sci-405c46 by 6051398c-8f0e-4511-a835-e90a0c6e83e9: halt sci-5937be filed mid-plan; continuing in-flight sci-dc0381 plan task per controller ruling
- 2026-10-02T01:59:47Z (feat/dc0381-mount-citations): halt override: attempted sci-4dca02 by 6051398c-8f0e-4511-a835-e90a0c6e83e9: halt sci-5937be filed mid-plan; continuing in-flight sci-dc0381 plan task per controller ruling
- 2026-10-02T02:15:33Z (main): sci-dc0381 (mount citations, branch feat/dc0381-mount-citations) adds ~30 world-fixture tests: final review estimates ~400-450 s serial, ~+50 s test-fast wall at 8 workers when testmon selects them (any config.py change). First step here: one pilot just test-fast from cold testmon on titan, main vs that branch head, record the delta
