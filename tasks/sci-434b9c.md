---
id: sci-434b9c
title: Show how plausible graph alternatives change a causal answer
status: idea
priority: 2
created: 2026-10-24T02:18:13Z
updated: 2026-10-24T10:04:56Z
depends: [sci-35af80]
tags: []
source: sci-35af80
agent: codex
---

Why: uncertainty about causal structure should help choose an investigation, without inventing probabilities over graphs. After the first workflow sci-35af80, compare a small set of explicitly authored alternatives for the same question, such as including a suspected confounder or changing one justified structural assumption.

Scope to decide: keep the target estimand, data bindings and analysis context fixed where possible; record every graph revision and changed assumption; rerun the supported identification/adjustment query through sci-1fa085; and explain which conclusions or required measurements change. An unrecorded edge is not automatically an absent edge, and alternatives must be deliberate hypotheses rather than all combinatorial graphs.

Acceptance direction: at least one example whose identification or valid adjustment set changes and one whose answer is stable across the declared alternatives, with provenance and explicit limits. No posterior over structures, aggregate model-confidence score or automatic belief update. The output can inform sci-171ad1's question-directed research candidates. This is a follow-on idea, not a prerequisite for the first workflow. Where to start: beliefs-d6060a's semantics and sci-1fa085's graph/query/result contract.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-24-causal-analysis-workflow-brief.md — scope boundaries, open questions and existing follow-ups
