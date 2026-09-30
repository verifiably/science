---
id: sci-fe8522
title: "Science commons: design spec (sub-project 5, the science half of publish)"
status: doing
priority: 1
size: l
complexity: high
process: planned
owner: science-commons
created: 2026-09-30T23:17:20Z
updated: 2026-09-30T23:29:38Z
started: 2026-09-30T23:17:27Z
depends: []
tags: [commons]
agent: claude-code/claude-fable-5-1
spec: docs/specs/2026-09-30-science-commons-design.md
---

Design the science commons in verifiably: a user publishes views to git and Zenodo destinations and adopts others' publications; a commons is an ordinary participant that catalogs, preserves and recommends publications it does not republish; trust is three separate local decisions (follow, hold, accept); mirrors and provider lists are ordinary versioned publications; forking is the kernel's lineage over runs. Milestone 1 is one complete collaboration between two installations over git without double-counting shared records. Success criteria: user — find useful work, understand why I trust it, reproduce or change it, share my contribution; commons — curate a collection, explain inclusion decisions, preserve what I promise to preserve, help others discover it. Prototype: the old science-commons store under ~/d/proto.

## Notes

- 2026-09-30T23:17:27Z (main): started
  provenance: {"harness_session":"claude-code:5f4da271-d57c-4d0d-9d69-fb6c4c6a0101","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-30T23:17:28Z (science-commons): resumed
  provenance: {"harness_session":"claude-code:5f4da271-d57c-4d0d-9d69-fb6c4c6a0101","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-30T23:21:20Z (science-commons): Design brainstormed with the user over two rounds (approach A: federated pull; commons catalogs, does not republish; follow/hold/accept; identity boundary; overlap and retirement into milestone 1). Spec drafted at docs/specs/2026-09-30-science-commons-design.md; independent review next, then user review.
- 2026-09-30T23:26:23Z (science-commons): review: spec round 1 — verdict: revise; findings: P1 9, P2 8, P3 5; reviewer: claude-code/claude-fable-5-1
- 2026-09-30T23:29:38Z (science-commons): Round 1 disposition: all 9 P1 accepted (catalog and provider list are side artifacts, not publications or epoch artifacts; inclusion travels as catalog content; attribution entries are a frozen facet, not identity; pins split origin-confirmed vs recommended; verifier-set moved to milestone 1a; milestone 1 publishes reproducible views; adopt needs a framework §4.4 write class and §9.1 sharing_root; intake is restore_root then admit_publication). P2 fixed (marker uid vs artifact identity; fetch record replaces holdings observation; containers never pruned; [fetch] replaces [holdings]; contributed_by is a set; mounted/unmounted replaces default index). P3: overlap and retirement stated as requirements not mechanism; milestone 1 split into 1a (no overlap) and 1b; verify/run over mounts and world-id discovery at bind added to §11.
