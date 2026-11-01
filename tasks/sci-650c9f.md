---
id: sci-650c9f
title: "recheck cannot take a store location whose path begins or ends in whitespace, and newline-bearing locations are ambiguous in refusals"
status: idea
priority: 2
created: 2026-11-01T01:07:36Z
updated: 2026-11-01T01:07:36Z
depends: []
tags: [holdings]
source: sci-409235
agent: claude-code/claude-opus-5-5
origin: agent
---

The kernel admits every character but NUL in a store relative path, and dataset/fetch name the location after the source file. science recheck refuses any --location with surrounding whitespace (a guard against pasted padding, plan review focus 1), so a location whose file name begins or ends in a space or NBSP can be blocked unsettled with no science route to settle it. A location containing a newline also splits across lines in the blocked-read refusal (one location per line) and needs shell quoting to pass. Found by the sci-409235 final review and re-reviews; the runbook (docs/stores.md, Settling an unsettled location) does not cover these cases. Possible directions: an exact-bytes input form, or refusing such names at write time.

## Notes

- 2026-11-01T01:07:36Z (add): created
  provenance: {"harness_session":"claude-code:224a01cb-bb9b-421b-ac3d-a55e9a312f6f","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
