---
id: sci-9c0bba
title: "Task 13: The retirement door and reconcile (blocked on `beliefs-a989fb`)"
status: doing
priority: 1
size: m
complexity: high
process: direct
owner: commons-1b
created: 2026-10-29T01:50:59Z
updated: 2026-10-29T13:57:12Z
started: 2026-10-29T13:50:58Z
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
- 2026-10-29T13:50:58Z (commons-1b): started
  provenance: {"harness_session":"codex:01a187eb-c21e-7a42-a216-2a6c5b309479","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-29T13:53:02Z (commons-1b): Resumed in retained .worktrees/commons-1b after verifying the overlap manifest and all 137 files; fast-forwarded to main 7a49152. Source session f666f956-1928-4c06-8bf1-80cd5a586d90 human turn 1814 accepts plan revision 7 and sequential subagent execution. Task 13 stays direct; scope is its retirement wiring and connected test expectations, with Tasks 14 and 15 remaining separate. Kernel implementation and design section 6 verify root/observers/evidence, any-actor idempotency, and retired/already-retired verdicts; plan interface amended accordingly. Setup baseline just test running before implementation; existing worktree-local environment and hooks verified.
- 2026-10-29T13:55:44Z (commons-1b): parked (waiting on agent): Controller dispatches Task 13 implementer in .worktrees/commons-1b after baseline; controller owns running baseline shell session 94411 and will send its result before code edits. Implementer completes Task 13 then parks for controller review.
  provenance: {"harness_session":"codex:01a187eb-c21e-7a42-a216-2a6c5b309479","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-29T13:57:12Z (commons-1b): resumed
  provenance: {"harness_session":"codex:01a187f2-a2e7-7d82-bd96-be8e5bf96a4b","harness_session_source":"CODEX_THREAD_ID"}
