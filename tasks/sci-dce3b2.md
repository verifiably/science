---
id: sci-dce3b2
title: "Coordination refusals: one data.kind vocabulary, and surface ProjectNotResolvable's tips"
status: done
priority: 2
size: s
complexity: mid
process: direct
owner: coordination-refusal-kinds
created: 2026-09-24T14:26:54Z
updated: 2026-10-26T23:13:20Z
started: 2026-10-26T23:00:38Z
completed: 2026-10-26T23:13:20Z
closed: 2026-10-26T23:13:20Z
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
- 2026-10-26T23:13:02Z (coordination-refusal-kinds): review: impl round 1 — verdict: accept; findings: Minor 2; reviewer: claude-code/claude-opus-5-5
- 2026-10-26T23:13:20Z (coordination-refusal-kinds): done
  provenance: {"harness_session":"claude-code:a32b916e-4ed3-4533-b453-d38ede488b81","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-26T23:13:20Z (coordination-refusal-kinds): data.kind is the kernel class name everywhere; divergent-view moves to data.reason under CoordinationRefused via one helper (resolve_one, selected_project, revise); ProjectNotResolvable.tips carried in data.tips and pinned across replay; spec §3.6/§4.3 amended. Deferred minor from review: the tips test raises ProjectNotResolvable synthetically rather than minting under a really diverged selection
  provenance: {"harness_session":"claude-code:a32b916e-4ed3-4533-b453-d38ede488b81","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
