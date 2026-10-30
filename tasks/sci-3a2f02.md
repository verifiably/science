---
id: sci-3a2f02
title: Determine whether preservation transport needs a commit boundary
status: todo
priority: 2
size: m
complexity: high
process: direct
created: 2026-10-30T19:21:08Z
updated: 2026-10-30T19:21:08Z
depends: []
parent: sci-009431
tags: [commons]
source: sci-65d6c9
agent: codex
origin: agent
---

Question: Can the existing transport contract reconcile a Zenodo draft-to-publication operation after interruption, or is a separate commit boundary necessary?
Where to start: [ref:brief], commons design §4.10 and §8, python/src/science/transport_git.py, commands/publish.py, commands/fetch.py, and the current beliefs transport and publication contracts. Verify current official service documentation before relying on API behavior.
Bound: One publication, one revision, and interruption before and after finalization with retry. Trace layout, visibility, digest verification and the kernel's evidence boundary; use a local model first and distinguish its evidence from a live experiment. Prepare any necessary sandbox write for separate user authorization. No production deposit and no full transport implementation. Existing fetch policy and byte bounds already work; identify only remaining preservation gaps.
Expected result: Record the observed behavior, evidence limits and recommendation on this task and in the brief, with an experiment artifact and the exact remaining design question if service behavior cannot be established locally.
Ideas it wakes: On completion, run tasks note sci-65d6c9 --no-reviewed "<finding>" before the result branch merges.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-30-commons-next-milestones-brief.md — evidence, remaining decisions and wake obligations

## Notes

- 2026-10-30T19:21:08Z (add): created
  provenance: {"harness_session":"codex:01a18e3f-26f0-78e1-91b3-23ee5a854fd2","harness_session_source":"CODEX_THREAD_ID","origin":"agent"}
