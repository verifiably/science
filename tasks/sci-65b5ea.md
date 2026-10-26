---
id: sci-65b5ea
title: "Coordination part 2: cover unexpected session failures and project record isolation"
status: done
priority: 3
size: xs
complexity: low
process: direct
owner: coordination-closeout
created: 2026-09-30T14:40:23Z
updated: 2026-10-26T23:36:54Z
started: 2026-10-26T23:34:53Z
completed: 2026-10-26T23:36:54Z
closed: 2026-10-26T23:36:54Z
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
- 2026-10-26T23:17:18Z (main): also take the deferred minor from sci-dce3b2's review: test_project_not_resolvable_carries_its_tips_in_the_refusal (test_dispatch_refusals.py) raises ProjectNotResolvable synthetically; add a real-path case that diverges the selected project (as test_cmd_projects.py's _diverge does) and mints a question, asserting {kind: ProjectNotResolvable, tips}
- 2026-10-26T23:34:53Z (coordination-closeout): started
  provenance: {"harness_session":"claude-code:c826b605-87ec-4aa8-8aea-62a46a0d13b8","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-26T23:36:54Z (coordination-closeout): done
  provenance: {"harness_session":"claude-code:c826b605-87ec-4aa8-8aea-62a46a0d13b8","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-26T23:36:54Z (coordination-closeout): Session handler RuntimeError before/after port.select covered (no close line, retry outcome-unknown, selection stands); project-show isolation over distinct records; real-path ProjectNotResolvable mint (sci-dce3b2's deferred minor). Coverage only, no behaviour change
  provenance: {"harness_session":"claude-code:c826b605-87ec-4aa8-8aea-62a46a0d13b8","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
