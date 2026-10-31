---
id: sci-62e5aa
title: "Write dispatch: a kernel refusal after a published act closes refused and drops the act"
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-31T18:28:44Z
updated: 2026-10-31T18:28:44Z
depends: []
tags: [command-framework]
source: sci-eccb43
agent: claude-code/claude-opus-5-5
origin: agent
---

`Dispatcher._invoke_write` closes every KERNEL_REFUSALS exception through `_close_refused` without consulting `invocation_acts`, while a surface `Refused` after an act goes to `_close_acted` (done with the act pairs, HandlerContractViolation). A multi-act handler whose later act is refused by the kernel (e.g. `dataset`: the holdings observation publishes, then `writer.add` raises a WriteRefused) closes refused, so the outcome and its replay omit an act that committed. Decide the closing rule for kernel-refused-after-act (likely the `_close_acted` path, as `_invoke_sharing` already does for both refusal kinds) and test it through a real two-act handler. Found while fixing sci-eccb43.

## Notes

- 2026-10-31T18:28:44Z (add): created
  provenance: {"harness_session":"claude-code:2d4f1b44-70f6-4dcf-877c-e39755156302","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
