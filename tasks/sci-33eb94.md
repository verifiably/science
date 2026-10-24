---
id: sci-33eb94
title: "Composites on the daily surface: author, read and summarise dag composites"
status: idea
priority: 2
created: 2026-10-24T01:46:14Z
updated: 2026-10-24T10:04:40Z
depends: [sci-4e0f7f]
parent: sci-35af80
tags: []
agent: claude-code/claude-opus-5-5
---

Why: beliefs built dag composites at cut 32 (2026-09-16; beliefs docs/designs/2026-09-12-composite-claims-design.md). Its section 6.1 and limitation 7 assign presentation over member rows to science. The earlier handoff was not filed; the current science command implementation exposes no composite author/read command. The original models intent included working with structures, not only storing them. Context: tasks doc beliefs-8060d0 context.

Scope after sci-4e0f7f: author a deliberately committed node set and typed causal members, read via beliefs' read_composite, and present the graph alongside its target question/estimand, measurement choices, datasets, assumptions, runs and diagnostics using existing records. Preserve the structure/estimator/generator separation while giving the user one coherent view. Part of the first workflow sci-35af80; causal-tool integration is sci-1fa085.

Acceptance cases the design must carry: (1) a total effect through X -> M -> Y does not by itself support a direct X -> Y arrow; a member's belief answers the claim as stated, not automatically the structural role. (2) An unrecorded edge in a draft is not an absence assertion. Committing the composite's closed node set and absent edges must be deliberate; do not automatically turn an incomplete sketch into that assertion. (3) An admitted assessment's authored identification term is shown as such, separately from a computed graph/query identification verdict. (4) Unsupported latent/proxy/context semantics refuse or remain explicit limitations rather than being inferred from a drawing.

Show evidence coverage, identification, scope and unresolved assumptions separately, with links back to member rows and analysis records. Counts may be derived with clear denominators. Do not introduce a graph-confidence scalar or revive ladder levels unless later use demonstrates a need. No new generic model entity and no automatic belief increase from graph authorship. This remains an idea awaiting the workflow design, not an implementation-ready specification.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-24-causal-analysis-workflow-brief.md — scope boundaries, open questions and existing follow-ups
