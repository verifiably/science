---
id: sci-7315fb
title: "show: warn when keep names an unpinned corpus"
status: todo
priority: 3
size: xs
complexity: low
process: direct
created: 2026-10-29T08:58:56Z
updated: 2026-10-29T08:58:56Z
depends: []
parent: sci-9104fb
tags: [commons]
source: "sci-9104fb:overlap-final-review:minor-3"
agent: codex
origin: agent
---

The overlap phase final review deferred Minor 3: the accepted 1b plan Review Focus 1 requires both adopt and show to warn when configuration.keep names a corpus with no sharing-registry pin. adopt emits the Finding, but show.handle only renders whether the requested pin is kept. This was verified in the merged overlap tree; the complete finding is [ref:review], and the requirement is [ref:requirement].

When showing an existing pin, append one Finding for each configured keep ID absent from the sharing registry: "keep names corpus <id>, which the sharing registry does not pin". Keep accepting unpinned IDs in configuration because users may predeclare keep before adoption. The warning must not refuse the read or write registry/kernel state. Preserve existing no-pin refusal for the requested corpus, retention rows, and acceptance behavior; use existing helpers where they actually fit, without a new layer.

Done: a focused regression shows an existing pin with a different unpinned keep entry and verifies the warning; pinned keep entries do not warn, and ordinary output remains intact. Run just test-one tests/test_cmd_show.py, then the declared test-fast route. Coordinate with sci-cf4d58 if that task is editing show; this small diagnostic fix needs no retirement door and can run before Tasks 13–15. No banner cleanup, retirement implementation, or unrelated acceptance refactor belongs here.

## References

- review (input, required, kind=review): tasks/files/sci-9104fb/commons-1b-overlap-review.md — final overlap review Minor 3
- requirement (input, required, kind=plan): docs/plans/2026-10-28-science-commons-1b.md — Review Focus 1, unknown keep entry warning

## Notes

- 2026-10-29T08:58:56Z (add): created
  provenance: {"harness_session":"codex:01a1855d-6c10-77a2-82b3-d0457ea936da","harness_session_source":"CODEX_THREAD_ID","origin":"agent"}
