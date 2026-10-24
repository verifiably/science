---
id: sci-37f0c3
title: Derive and check a causal model's testable implications without automatic belief admission
status: idea
priority: 2
created: 2026-10-24T02:18:14Z
updated: 2026-10-24T10:04:59Z
depends: [sci-35af80, beliefs-d6060a]
tags: []
source: sci-35af80
agent: codex
---

Why: working with a model should include looking for observations it fails to explain. The recovered context grouped model-fit claims under the unbuilt non-empirical route, but computing a diagnostic, storing its result and admitting a belief-bearing claim about a model are separate operations.

Scope to decide after sci-35af80: for the supported graph semantics and measured variables, derive an explicit set of testable implications (for example, conditional independences) and execute suitable checks against observations. Name the causal/Markov assumptions, measurement bindings, scope, sample selection, test method and limitations. A discrepancy can challenge the assumptions jointly; passing checks does not prove a graph correct or uniquely identify it. Account for power, multiplicity and data reuse when deciding what a diagnostic says.

Preserve diagnostic inputs and results through existing governed run/artifact routes. Keep unsupported diagnostics explicit and do not require a generic model-confidence carrier. If making an admitted claim about a composite requires new semantics, identify that separate beliefs work rather than routing the diagnostic into empirical belief automatically. Simulation or fitted outputs used to validate a procedure remain distinct from observations that could support a scientific claim.

Expected scoping example: a model with an observable implication, an observed discrepancy, and a result that reports the discrepancy and its assumptions without strengthening belief merely because the check ran. Where to start: beliefs-d6060a's distinction between diagnostics and higher-order claims; sci-1fa085; DAGitty manual section 5.6 (https://www.dagitty.net/manual-3.x.pdf). This follow-on is outside the first workflow's closure criteria.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-24-causal-analysis-workflow-brief.md — scope boundaries, open questions and existing follow-ups
