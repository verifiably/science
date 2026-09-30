---
id: sci-65b5ea
title: "Coordination part 2: cover unexpected session failures and project record isolation"
status: todo
priority: 3
size: xs
complexity: low
process: direct
created: 2026-09-30T14:40:23Z
updated: 2026-09-30T14:40:24Z
depends: [sci-f95f8b]
parent: sci-c5528e
tags: [projects]
source: sci-f95f8b
agent: codex
---

Two deferred Minor findings from the part 2 review, preserved on sci-f95f8b; the implementation was accepted and no runtime defect was observed.

1. In python/tests/test_session_class.py, cover a session handler raising RuntimeError before and after port.select. Assert no close ledger line, retry refuses outcome-unknown, and any recorded selection remains current. Reuse the existing rig and ledger helpers; keep both cases in one parametrized test.
2. Strengthen test_project_binds_this_show_only in python/tests/test_cmd_projects.py: give two projects distinct subordinate records, then assert ambient and explicit project-show reads contain only their respective records while the endpoint selection stays unchanged. Extend the existing test rather than add another harness.

Use just test-one for the affected tests and just test-fast before commit. This is coverage of existing behavior, not a change to exception or project-filter semantics. Execute in coordination-part2 or after its integration.

## Notes

- 2026-09-30T14:40:23Z (coordination-part2): Pre-close review follow-up from sci-f95f8b: deferred coverage minors.
