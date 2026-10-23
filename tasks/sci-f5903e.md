---
id: sci-f5903e
title: "Holdings writes select superseded observations by the full store locator, not the relative path alone"
status: done
priority: 2
size: xs
complexity: low
process: direct
owner: main
created: 2026-10-23T18:37:32Z
updated: 2026-10-23T18:44:09Z
started: 2026-10-23T18:37:34Z
completed: 2026-10-23T18:44:09Z
closed: 2026-10-23T18:44:09Z
depends: []
tags: [commons]
source: sci-13050a
agent: claude-code
---

fetch.py and dataset.py build the 'standing' observations a new holdings write supersedes by comparing only location.relative_path. A UrlLocator has no relative_path, so any URL observation in the write root raises AttributeError; an observation of the same relative path in another store is selected, the write lands, and the kernel then refuses with MalformedRecord, leaving bytes without the new observation. Compare the whole location against StoreLocator(writer.store_id, relative). Found by the codex/gpt-6.1-sol implementation review of commons 1a after merge; reproduced by its probes.

## Notes

- 2026-10-23T18:37:33Z (main): concerns: sci-13050a defect — fetch (and dataset, whose pattern it copied) selects superseded holdings observations by relative path alone: URL observations crash it, other stores' observations are wrongly superseded
- 2026-10-23T18:37:34Z (main): started
  provenance: {"harness_session":"claude-code:f3d948a6-1f74-4fd1-8fd0-6c6e2e0d81e1","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-23T18:44:08Z (main): baseline: just test in .worktrees/holdings-standing at 8d4d720, 855 passed; RED 3 failed (2 AttributeError on UrlLocator, 1 MalformedRecord), GREEN test_cmd_fetch+test_cmd_dataset 19 passed, just test-fast 858 passed
- 2026-10-23T18:44:09Z (main): done
  provenance: {"harness_session":"claude-code:f3d948a6-1f74-4fd1-8fd0-6c6e2e0d81e1","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-23T18:44:09Z (main): fixed at 2edb5f4 (fast-forwarded to main): fetch and dataset compare the whole StoreLocator; three regression tests
  provenance: {"harness_session":"claude-code:f3d948a6-1f74-4fd1-8fd0-6c6e2e0d81e1","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
