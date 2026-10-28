---
id: sci-9104fb
title: "Science commons milestone 1b: update, overlap and retirement"
status: doing
priority: 1
size: l
complexity: high
process: planned
owner: commons-1b
created: 2026-10-01T02:21:10Z
updated: 2026-10-28T21:18:44Z
started: 2026-10-28T20:03:15Z
depends: [sci-13050a, beliefs-81367e, beliefs-a989fb]
tags: [commons]
source: sci-fe8522
agent: claude-code/claude-fable-5-1
spec: docs/specs/2026-09-30-science-commons-design.md
---

Spec §12 part 1b: A binds B, adopts B's publication; A publishes an update dropping one record; B adopts the update. Decisive cases: overlap (A's records held in both corpora read once and contribute once; with accept=[B] A's own assessment counts through its write-root copy only; shared records across A's revisions read once) and pinned derivation (B's derived analysis stays readable; the dropped record stays mounted from the retired revision; show says why). Builds: §10's adopt preflight on a fetched root, same-authority supersession, retirement through the sharing write class reaching World.retire, keep.

## References

- design-1b (output, required, kind=spec): docs/specs/2026-10-28-science-commons-1b-design.md — milestone 1b design: adopts cut 48, settles keep, current publication and retirement

## Notes

- 2026-10-23T18:45:09Z (main): from commons 1a: content identity per address in the Carried branch is sci-4a3543 and must land with overlap; adopting one's own publication back is unreachable in 1a (pin-unsourced points to provider-bind, which refuses the own world; Final M7), so the own-adopted-back branch of the accept policy needs a sourcing route in 1b; the SDD ledger with all deferred findings is attached to sci-13050a
- 2026-10-28T17:14:36Z (main): cut 48 (beliefs-918fd2) lands the kernel precondition for 1b (one address held in several live corpora with equal content); science's side is {"id":"sci-73c80e","action":"created","at":"2026-10-28T17:14:33Z","warnings":[]}, which this milestone now depends on
- 2026-10-28T17:15:01Z (main): the science-side task named in the previous note is sci-73c80e (the id was pasted as JSON there)
- 2026-10-28T20:03:13Z (main): sci-73c80e (science's side of cut 48, filed today as 'science's side of commons milestone 1b') is folded in as a child instead of a dependency: 1b's plan decomposes its amendment list; sci-4a3543 keeps its dependency on it
- 2026-10-28T20:03:15Z (main): started
  provenance: {"harness_session":"claude-code:f666f956-1928-4c06-8bf1-80cd5a586d90","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-28T20:03:32Z (commons-1b): resumed
  provenance: {"harness_session":"claude-code:f666f956-1928-4c06-8bf1-80cd5a586d90","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-28T20:14:25Z (commons-1b): 1b design drafted at docs/specs/2026-10-28-science-commons-1b-design.md (worktree .worktrees/commons-1b). Findings: the kernel has no retire door (record_sharing refuses retired; beliefs-c0d952 designs it, beliefs-a989fb implements it) so sci-9104fb now depends on beliefs-a989fb and the plan sequences retirement after it; keep becomes a config list (no sharing transition to ledger a pin flag under); the current publication is derived via publication_tip over authorized roots; sci-4a3543 is absorbed as a child
- 2026-10-28T20:23:53Z (commons-1b): builder check (claude-code subagent) raised 3: cross-side statement equality unsatisfiable (fixed: compare gathered identities, statements per side); A's kinds query would carry B's spec and run back in P3 (fixed: A's revised query names its own addresses); merge shape with the retire door unbuilt (ruled: two merges, overlap half first, pending-door Finding on main meanwhile; Keith to confirm at review). Design revision 2 committed in .worktrees/commons-1b
- 2026-10-28T20:23:55Z (commons-1b): parked (waiting on user, review): Keith reviews the 1b design revision 2 (worktree .worktrees/commons-1b, commit 5864b76, docs/specs/2026-10-28-science-commons-1b-design.md); on accept, tasks start sci-9104fb in the worktree and invoke writing-plans (one plan, two phases per §7); the retirement tail waits on beliefs-a989fb
  provenance: {"harness_session":"claude-code:f666f956-1928-4c06-8bf1-80cd5a586d90","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-28T21:02:55Z (commons-1b): review: spec round 1 — verdict: revise; findings: P1 2, P2 3; reviewer: codex/gpt-6-astra
- 2026-10-28T21:02:56Z (commons-1b): resumed
  provenance: {"harness_session":"claude-code:f666f956-1928-4c06-8bf1-80cd5a586d90","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-28T21:17:05Z (commons-1b): review: spec round 2 — verdict: revise; findings: Important 2, Minor 7; reviewer: claude-code
- 2026-10-28T21:18:42Z (commons-1b): round 2 (fresh claude-code reviewer over a8f7a85; model unverified from dispatch metadata) found 2 Important: retired roots missing from the tip fold turn a post-retirement sibling into an unresolved pair that mounts; _reconcile cannot ledger retired (record_sharing refuses it). Both verified against publication_tip and writer.record_sharing and fixed in revision 4 (8439319) with the 7 minors (P2 retired with P1, keep before a late predecessor, reopen remedy on retirement, registry version bump and rebuild, group keyed by world, missing link named as the (corpus_id, marker) pair, Carried content unit test, excluded wording). Kernel observation beliefs-a02e11 filed (executes declared, never emitted)
- 2026-10-28T21:18:44Z (commons-1b): parked (waiting on user, review): Keith reviews the 1b design revision 4 (worktree .worktrees/commons-1b, commit 8439319, docs/specs/2026-10-28-science-commons-1b-design.md); on accept, tasks start sci-9104fb in the worktree and invoke writing-plans (one plan, two phases per §7; the retirement tail waits on beliefs-a989fb)
  provenance: {"harness_session":"claude-code:f666f956-1928-4c06-8bf1-80cd5a586d90","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
