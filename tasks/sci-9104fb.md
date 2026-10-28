---
id: sci-9104fb
title: "Science commons milestone 1b: update, overlap and retirement"
status: todo
priority: 1
size: l
complexity: high
process: planned
created: 2026-10-01T02:21:10Z
updated: 2026-10-28T20:03:13Z
depends: [sci-13050a, beliefs-81367e]
tags: [commons]
source: sci-fe8522
agent: claude-code/claude-fable-5-1
spec: docs/specs/2026-09-30-science-commons-design.md
---

Spec §12 part 1b: A binds B, adopts B's publication; A publishes an update dropping one record; B adopts the update. Decisive cases: overlap (A's records held in both corpora read once and contribute once; with accept=[B] A's own assessment counts through its write-root copy only; shared records across A's revisions read once) and pinned derivation (B's derived analysis stays readable; the dropped record stays mounted from the retired revision; show says why). Builds: §10's adopt preflight on a fetched root, same-authority supersession, retirement through the sharing write class reaching World.retire, keep.

## Notes

- 2026-10-23T18:45:09Z (main): from commons 1a: content identity per address in the Carried branch is sci-4a3543 and must land with overlap; adopting one's own publication back is unreachable in 1a (pin-unsourced points to provider-bind, which refuses the own world; Final M7), so the own-adopted-back branch of the accept policy needs a sourcing route in 1b; the SDD ledger with all deferred findings is attached to sci-13050a
- 2026-10-28T17:14:36Z (main): cut 48 (beliefs-918fd2) lands the kernel precondition for 1b (one address held in several live corpora with equal content); science's side is {"id":"sci-73c80e","action":"created","at":"2026-10-28T17:14:33Z","warnings":[]}, which this milestone now depends on
- 2026-10-28T17:15:01Z (main): the science-side task named in the previous note is sci-73c80e (the id was pasted as JSON there)
- 2026-10-28T20:03:13Z (main): sci-73c80e (science's side of cut 48, filed today as 'science's side of commons milestone 1b') is folded in as a child instead of a dependency: 1b's plan decomposes its amendment list; sci-4a3543 keeps its dependency on it
