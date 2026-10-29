---
id: sci-9c0bba
title: "Task 13: The retirement door and reconcile (blocked on `beliefs-a989fb`)"
status: todo
priority: 1
size: m
complexity: high
process: direct
created: 2026-10-29T01:50:59Z
updated: 2026-10-29T13:46:55Z
depends: [beliefs-a989fb]
parent: sci-9104fb
tags: [commons]
agent: claude-code/claude-fable-5-1
origin: agent
plan: docs/plans/2026-10-28-science-commons-1b.md
step: "Task 13: The retirement door and reconcile (blocked on `beliefs-a989fb`)"
---

## Notes

- 2026-10-29T01:50:59Z (add): created
  provenance: {"harness_session":"claude-code:f666f956-1928-4c06-8bf1-80cd5a586d90","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
- 2026-10-29T13:46:55Z (main): dependency landed: beliefs-a989fb merged on beliefs main at f274822 (not pushed). Door is ScopedWriter.retire(root, observers, *, evidence) -> SharingLine, per beliefs docs/superpowers/specs/2026-10-29-publication-retirement-door-design.md section 6: pass root_for(cid) and the observer set built from head_artifact_for(cid), as adopt does for admission; verdict is retired or already-retired (any actor's prior retirement, no second status record), transition always retired; departed refuses StatusTerminal; a non-self-replica admission refuses StatusTargetUnknown. Revise Task 13's Interfaces against that before starting
