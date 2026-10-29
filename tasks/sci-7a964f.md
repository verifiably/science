---
id: sci-7a964f
title: "Commons 1b tidy: test helper duplication and retirement-tail document polish"
status: todo
priority: 4
size: xs
complexity: low
process: direct
created: 2026-10-29T16:15:31Z
updated: 2026-10-29T16:15:31Z
depends: []
tags: [commons]
source: sci-9104fb
agent: claude-code/claude-opus-5-5
origin: agent
---

Polish the reviews of milestone 1b's Tasks 14 and 15 deferred (sci-9104fb's attached plan ledger). Nothing here changes behaviour.

Tests (`python/tests/test_commons_1b.py`):
- Import `_show` from `test_cmd_show` instead of redefining it, and use it at the inline `read_rig(...).invoke("show", ...)` call.
- Use one reader for retired ledger lines (`_retired_lines` beside `test_cmd_adopt`'s `_sharing_lines` filter).
- Snapshot-cache the third reader the requirement-before-sweep test builds on every run.

Documents:
- The Task 12 amendments in the commons design §11 and the framework design §4.4 still say the door "remains pending" when read alone; mark them superseded by the Task 15 amendment beside them.
- Rewrap the overlong lines Task 15 left in `commands/adopt/prompt.md` and `commands/show/prompt.md` (then `science adapters build`).
- Move the commons design §12 Task 15 amendment after its paragraph, and split the long §10 Task 15 amendment.

## Notes

- 2026-10-29T16:15:31Z (add): created
  provenance: {"harness_session":"claude-code:e9952dfd-ee2b-47b3-84ef-d176d9d3cc57","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
