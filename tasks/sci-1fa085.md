---
id: sci-1fa085
title: Integrate causal identification and return one analysis result with provenance
status: idea
priority: 2
reviewed: true
reviewed_at: 2026-10-24T10:04:52Z
created: 2026-10-24T02:16:33Z
updated: 2026-10-24T10:04:52Z
depends: [sci-4e0f7f, sci-33eb94, sci-87c165]
parent: sci-35af80
tags: []
source: sci-35af80
agent: codex
---

Why: the first workflow sci-35af80 needs a graph/query to produce a usable, reproducible identification result and feed the result into one analysis. Proto-science's exporters stopped at script text; this integration must consume and inspect its result.

Scope after sci-4e0f7f: integrate one established causal-analysis implementation behind the reviewed science command surface. Bind the exact composite revision, causal query/estimand, observed-variable set, measurement bindings, assumptions and tool version to the result using existing governed run/artifact routes. Computation and orchestration live in science; meanings, identity or admission changes need their owning beliefs design. Do not introduce a separate model store or generic multi-backend framework.

Required outcome distinctions: an estimand identified by the supported method (with the adjustment set or returned formula and its assumptions); no valid adjustment set; a justified non-identifiability verdict under an explicit model class; and unsupported or incomplete inputs. A backend that only searches adjustment sets must not issue general non-identifiability verdicts. Required checks include a supported identified case, an invalid adjustment/collider case, and a case where adjustment is unavailable but non-identifiability has not been established. Compare returned results to independent expected answers and exercise the round trip through persisted inputs and outputs.

One real question must proceed from identification to a supported analysis and interpretable returned result. Fitted artifacts remain reads inputs; simulated/generated outputs and model diagnostics do not automatically become empirical observations or admitted evidence. The example records estimates, uncertainty, diagnostics and any admission/refusal with provenance. Stop and file a semantic prerequisite when the kernel cannot represent the required contract.

Where to start: sci-4e0f7f's reviewed design; sci-33eb94; sci-87c165; beliefs-d6060a; beliefs-72b6f6; DAGitty's manual (https://www.dagitty.net/manual-3.x.pdf) and Shpitser/Pearl's identification results (https://jmlr.csail.mit.edu/papers/v9/shpitser08a.html). These are starting points, not a selected dependency. This remains an idea until the design settles the integration scope.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-24-causal-analysis-workflow-brief.md — scope boundaries, open questions and existing follow-ups

## Notes

- 2026-10-24T10:04:52Z (main): scope: briefed; checked science 6d936f3 and existing design/semantic research; no causal backend or persisted graph/query/result contract is selected yet. Reuse sci-4e0f7f, preserving component dependencies and independent correctness/round-trip checks; brief: docs/notes/2026-10-24-causal-analysis-workflow-brief.md
