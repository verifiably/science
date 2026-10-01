---
id: sci-dc0381
title: "Consume beliefs mount citations: write commands name mount records, belief over a world read"
status: todo
priority: 1
size: m
complexity: mid
process: planned
created: 2026-10-01T11:07:18Z
updated: 2026-10-01T21:17:58Z
depends: [beliefs-9ce6e4]
tags: [commons, projects]
source: beliefs-9ce6e4
agent: claude-code/claude-opus-5-5
---

beliefs mount-citations spec (beliefs docs/superpowers/specs/2026-10-01-mount-citations-design.md §4), cut 44. Once beliefs-9ce6e4 lands: (1) spec, run, assess and verify may name a read mount's dataset, proposition and assessment; drop part 3's refusal of a read mount's dataset (dataset still refuses bytes a mount declares). (2) Remove ReadContext._refuse_foreign_observations: a corpus-local read now refuses input-outside-corpus in the kernel. (3) Cross-corpus belief is a world read at an epoch covering the write root and its mounts (decision 10), the commons design's 'belief evaluating over a world read' (§11). (4) status shows eligibility-unresolved warnings for cross-mount assessments; audit_world judges them. (5) A citation into a mount pinning a different identity of a shared namespace refuses CitationContractMismatch: check mm30's pins against the working corpus's before sci-0d00d2.

## Notes

- 2026-10-01T20:52:23Z (main): unblocked: beliefs-9ce6e4 (cut 44, mount citations) merged into beliefs main at 7932481 on 2026-10-01 — a session's writes can now cite records in its read mounts; see beliefs docs/plans/2026-10-01-conformance-cut-44-results.md
- 2026-10-01T21:17:58Z (main): absorbs sci-b1c777 (same two refusals: ReadContext.not_held and _refuse_foreign_observations; coordination spec §5.5 part 3 amendment moves here) and sci-498acb (publishes refusal retirement, rides along); user agreed 2026-10-01
