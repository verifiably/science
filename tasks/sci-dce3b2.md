---
id: sci-dce3b2
title: "Coordination refusals: one data.kind vocabulary, and surface ProjectNotResolvable's tips"
status: doing
priority: 2
size: s
complexity: mid
process: direct
owner: coordination-refusal-kinds
created: 2026-09-24T14:26:54Z
updated: 2026-10-26T23:00:50Z
started: 2026-10-26T23:00:38Z
depends: []
parent: sci-c5528e
tags: [projects]
agent: claude-code/claude-opus-5-5
---

Found by the 2026-09-24 final review of coordination part 1. A refusal's data.kind carries two vocabularies: revise and science.coordination.resolve_one emit reason codes ('divergent-view', per spec §3.6), while dispatch._kernel_refusal emits kernel exception class names ('ProjectNotResolvable', 'CoordinationUnavailable'). Clients switching on data.kind see both in one field. Separately, the generic WriteRefused branch in dispatch.py drops ProjectNotResolvable.tips, which spec §4.3/§7 imply a client needs to reconcile. Pick one vocabulary (or split into two fields), amend the spec with a dated line, and carry tips through the kernel-refused envelope; pin both with tests.

## Notes

- 2026-10-26T23:00:38Z (main): started
  provenance: {"harness_session":"claude-code:a32b916e-4ed3-4533-b453-d38ede488b81","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-26T23:00:50Z (coordination-refusal-kinds): resumed
  provenance: {"harness_session":"claude-code:a32b916e-4ed3-4533-b453-d38ede488b81","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
