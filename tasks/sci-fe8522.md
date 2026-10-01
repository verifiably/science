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
updated: 2026-10-01T00:12:10Z
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
- 2026-09-30T23:37:11Z (science-commons): review: spec round 2 — verdict: revise; findings: P1 7, P2 6, P3 3; reviewer: claude-code/claude-fable-5-1
- 2026-09-30T23:37:11Z (science-commons): Round 2 disposition: all 7 P1 accepted (corpus_id required everywhere, container listing is the catalog; attribution inputs are address map + registry provenance + adopted markers, frozen with the selection snapshot; loader unions registry roots into corpus_roots and adopt takes effect at next open; accept filter stated as outcomes before any pool rule, science pre-filter as default; retirement is a kernel act the sharing class reaches, 1b requirement; conflict exit rule in §10; milestone 1 needs fetch, plus verify/run/assess over mounts). P2 fixed (bind --world argument; keep flag; aggregator refuses differing pins; overlap covers every kind; ledger evidence named; registry writes are acts). P3: §9 ordering left to beliefs; §11 gains fetch, mounts resolution, assesses-edge question, sci-923d3a; push idempotence is a test row.
- 2026-09-30T23:37:28Z (science-commons): parked (waiting on user, review): User reviews docs/specs/2026-09-30-science-commons-design.md (two independent review rounds folded in); on approval, file the beliefs requirements from §11 as beliefs tasks, then write the framework amendments and the milestone 1a plan
  provenance: {"harness_session":"claude-code:5f4da271-d57c-4d0d-9d69-fb6c4c6a0101","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-09-30T23:44:26Z (science-commons): resumed
  provenance: {"harness_session":"codex:01a0f47e-0750-7060-9543-df2764d43697","harness_session_source":"CODEX_SESSION_ID"}
- 2026-09-30T23:45:07Z (science-commons): review: spec round 3 — verdict: revise; findings: P1 4, P2 2; reviewer: codex
- 2026-09-30T23:45:08Z (science-commons): Round 3 P1: §9 accepts records by their containing publication, so accepted B can carry unaccepted A's assessments/verifications through closure and change their acceptance without changing the records. Use authenticated record provenance consistently across carriers; a provenance claim alone is insufficient. Also state the local authored-record case explicitly: a write root has neither a publication marker nor an origin-confirmed pin.
- 2026-09-30T23:45:08Z (science-commons): Round 3 P1: §9 names assessments and verifications but omits retractions. beliefs.evaluation.gather applies retraction standing before gathering either, so an unaccepted retraction can suppress accepted evidence or an accepted failed verification before the proposed filter sees it. Define accepted correction/standing inputs and apply the policy before those effects, including provenance in the result context.
- 2026-09-30T23:45:08Z (science-commons): Round 3 P1: §10 begins after successor admission but its conflict exit leaves the successor pinned and unmounted. An admitted corpus without terminal status remains live; §10.3 itself explains why that produces selection-incomplete. Preflight while restored but unadmitted, and admit/mount only after conflict and dependency checks succeed; define recoverable transitions so refusal leaves the prior world usable.
- 2026-09-30T23:45:09Z (science-commons): Round 3 P1: §5/§11 list verify, run and assess for mount resolution but omit spec. science.commands.spec.handle reads target and dataset through ctx.write_view() and refuses either absent there. Milestone 1a cannot create B's changed spec over A's mounted proposition without a copy that violates its no-overlap setup. Include spec in the mount-read changes and exercise this exact authoring step.
- 2026-09-30T23:45:09Z (science-commons): Round 3 P2: §5 assumes the reproducible publication names a workspace commit, but §7 defines no carrier for repository location/commit or retrievable execution material. Current publish markers carry selection and source epoch/view; run recipes contain code/environment identities, not a retrievable Git revision. Specify the carrier and integrity checks, or explicitly require externally supplied workspace inputs for milestone 1a.
- 2026-09-30T23:45:09Z (science-commons): Round 3 P2: §6 merges catalog entries with a single §7.2 inclusion block and only a contributed_by set. Two catalogs can agree on a pin while giving different reasons, relations and preservation promises. Define merge semantics preserving each cataloguer's statement and who owns each preservation promise; the aggregator must not silently inherit another host's promise.
- 2026-09-30T23:45:10Z (science-commons): parked (waiting on user, review): Spec author resolves round 3 findings in .worktrees/science-commons/docs/specs/2026-09-30-science-commons-design.md, then requests re-review before filing requirements or planning milestone 1a
  provenance: {"harness_session":"codex:01a0f47e-0750-7060-9543-df2764d43697","harness_session_source":"CODEX_SESSION_ID"}
- 2026-10-01T00:10:30Z (science-commons): resumed
  provenance: {"harness_session":"claude-code:5f4da271-d57c-4d0d-9d69-fb6c4c6a0101","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-01T00:11:58Z (science-commons): review: spec round 3 — verdict: revise; findings: P1 4, P2 2; reviewer: codex (pasted by the user)
- 2026-10-01T00:12:10Z (science-commons): Round 3 disposition: all accepted. §9 acceptance is per record by provenance world with authenticated attribution (carried records need an origin-confirmed pin of the origin publication; own-world records need none) and covers correction records before their effects. §10 checks marker layout, supersession and conflicts on a fetched, unadmitted root; pin states fetched/admitted/mounted/retired; refusal leaves the world untouched. §5/§7.2: workspace locator supplied out of band in 1a, checked against code identity; catalog carries execution claims from milestone 2; marker locator filed as a question. §11 adds spec over mounts. §7.2 inclusions are per-cataloguer statements; promises owned by their author; aggregators never inherit.
