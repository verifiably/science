---
id: sci-4e0f7f
title: Design the first causal-analysis workflow around one real question
status: todo
priority: 2
size: m
complexity: high
process: planned
created: 2026-10-24T02:16:32Z
updated: 2026-10-24T02:18:16Z
depends: [beliefs-d6060a]
parent: sci-35af80
tags: []
source: sci-35af80
agent: codex
---

Why: sci-35af80 needs one reviewable end-to-end design that composes the existing beliefs records into a usable science workflow. The user accepted the direction and asked for task capture; implementation choices and written artifacts still need their normal reviews.

Where to start: the captured requirements in sci-35af80, sci-33eb94 and sci-87c165; beliefs-d6060a's semantic findings; tasks doc beliefs-8060d0 context; and [ref:commands]. Check the chosen project's actual question and data rather than inventing a demonstration that avoids the missing semantics.

Bound: design only. Choose one real causal question and a supported estimand, define the node-to-measurement bindings and explicit causal assumptions, then specify the narrowest author/read, scope-comparison and identification/analysis sequence that answers it. Prefer one established causal-analysis implementation, selected on required semantics, correctness checks, reproducibility and integration cost; no library choice is pre-approved. The exact composite revision, query, observed-variable set, assumptions, software version and returned result must be linked through governed records. Preserve the separation of structure, estimator and generator. Identify any required beliefs contract extension and file it there instead of silently adding meaning in science.

Acceptance design: distinguish evidence for a total effect from evidence for a direct arrow; an incomplete sketch from a committed composite's absent-edge assertions; and authored identification terms from a computed identification verdict. Specify distinct outcomes for identified by a named method, no valid adjustment set, non-identifiability established under stated assumptions, and unsupported/incomplete input. Never equate failed adjustment search with non-identifiability. Cover measurement units/time/population/selection, typed scope equality's limits, and the rule that fitted-model artifacts are reads rather than observes inputs. Separate diagnostic computation and storage from admitting claims about a model. The example must return and inspect results, not merely export a script, and must not strengthen belief by drawing a graph or running a diagnostic.

Expected result: [ref:design], reviewed before implementation planning, with an exact worked-example acceptance procedure and ownership/dependency decisions. After approval, scope the existing component ideas and file only missing execution and integration work; each implementation plan retains its review gate. Keep weighted-belief research, structural sensitivity, general model criticism and priority policy outside this first milestone.

Ideas it wakes: on completion, add the design findings with tasks note --no-reviewed to sci-33eb94, sci-87c165 and sci-1fa085, and name the approved design revision.

## References

- commands (input, required, kind=spec): docs/specs/2026-08-31-command-framework-design.md — command construction and kernel writes
- design (output, kind=spec): docs/specs/causal-analysis-workflow-design.md — first workflow and worked-example acceptance
