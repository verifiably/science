---
id: sci-eccb43
title: "dataset: StoreWriteRefused escapes as internal-error and leaves the invocation unclosed"
status: doing
priority: 2
size: s
complexity: mid
process: direct
owner: main
created: 2026-10-30T19:15:45Z
updated: 2026-10-31T18:21:54Z
started: 2026-10-31T18:21:54Z
depends: []
tags: [holdings]
source: mm-62e2da
agent: claude-code/claude-opus-5-5
origin: mixed
---

`dispatch.py`'s KERNEL_REFUSALS does not include beliefs' StoreWriteRefused. When the holdings write in `commands/dataset.py` is refused by the store (observed: a read-only-serviceable store root), the exception propagates out of `_invoke_write`. The person sees JSON-RPC internal-error (exit 1) instead of a classified refusal (exit 3), and the ledger keeps `invocation-open` without an `invocation-close`.

The holdings intent is appended before the store write, so the invocation has acted on the observer corpus by the time of the refusal. Mapping therefore needs to decide how an acted-then-refused write closes: refused with the intent recorded, or `_close_acted`. A caller cannot tell a refused write from an unknown outcome until this is mapped.

Same class as the uncaught RuleNotHeld found under sci-0d00d2. Observed in invocation 6cf80d367660d05be56a00f686e7f23c, 2026-10-30, for mm-62e2da.

## Notes

- 2026-10-30T19:15:45Z (add): created
  provenance: {"harness_session":"claude-code:a2943a1d-dd3d-4577-a43b-8347da7f11bf","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"mixed"}
- 2026-10-31T18:21:54Z (main): started
  provenance: {"harness_session":"claude-code:2d4f1b44-70f6-4dcf-877c-e39755156302","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-31T18:21:54Z (main): halt override: started past sci-0bea23 by 2d4f1b44-70f6-4dcf-877c-e39755156302: User explicitly requested sci-eccb43 despite open test-latency halt sci-0bea23
