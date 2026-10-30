---
id: sci-b2755f
title: Sweep epistemic records for the premises they rely on and rank the questions whose answers would clarify the most
status: idea
priority: 2
created: 2026-10-30T01:53:54Z
updated: 2026-10-30T01:53:54Z
depends: []
tags: []
origin: mixed
---

Why: the user asked (2026-10-29, beliefs session) which question in a field, if answered, would most reduce uncertainty across it, and proposed sweeping epistemic entities (hypotheses, propositions, questions, models, analyses) for the assumptions each relies on, aggregating them into a dependency graph and ranking what to clarify. Their example: "multiple myeloma is a single disease" may collapse related diseases under one name. The sweep's output is ranked research questions, each with an explanation of what resolving it could clarify; making assumptions explicit is the means.

Agreed shape (user + agents, same session): one `/sci:sweep-assumptions` skill, one bounded mm pilot, one report. Defer separate list/rank commands, scheduled sweeps (autonomy) and kernel changes; the pilot is a measurement lane whose job includes establishing what representation is missing. Literature enters as source assertions, never as empirical belief by extraction.

Report contract:
- Coverage: sources, records, revisions and areas of mm examined; what was unavailable or omitted. The ranking is over the represented field only.
- Premise inventory: exact statement, scope, source, and stated / inferred / adopted. Reuse an existing proposition where its meaning fits.
- Dependency paths: stored relations kept apart from proposed reliance links, each proposed link with its reason. These are "this inference relies on" edges, never causal edges.
- Reach: distinct downstream questions and claims, without double-counting repeated paths or duplicated source assertions.
- Consequences: per evaluated dependent item, what could change (reverse / narrow / reinterpret / refine), why, who judged it, supporting material; unevaluated items listed too. Link-provenance and consequence-judgment counts shown, so an inferred chain reads differently from a documented one.
- Tractability: relevant spec `falsification` text quoted verbatim as an authored lead (it may concern the target, not the premise), the judgment linking it, proposed discriminating observations, available inputs, unresolved feasibility.
- Three candidate questions: reach, consequence, remaining uncertainty and tractability explained separately; no aggregate score, no "expected information gain" without a probability model and utility target.
- Representation gaps: concrete premises that could not be represented, classified (vocabulary, scope, relation, other).

Code facts the design must respect (beliefs main, checked 2026-10-29):
- Propositions carry `qualifiers`; specs and assessments carry `applicability`. The mm30 reproduction contract and the biology domain both declare `dimensions: {}`, so no subtype qualifier is expressible today; mm30 distinguishes disease stages through the estimand's contrast levels, and `subtype-of-concept-concept` exists as an operator. A missing qualifier is therefore a candidate pooling premise or a representation gap, never by itself evidence that an author treated mm as one disease. Classify scope as explicitly broad / restricted elsewhere / not recorded / not expressible under the active contract.
- `co_scoped` is canonical equality of applicability maps (two empty maps are equal); report "declared scope maps match", then judge adequacy separately. `commensurable` compares estimands with identification removed.
- `SpecDraft.assumptions` and `falsification` are prose; the sweep never edits frozen specs.

Hypothesis under test, not a deliverable: a premise stated as a proposition plus one reliance relation (provenance, scope, revision binding, link to query-based hypotheses) may suffice in beliefs. The gap list is the evidence for or against.

Pilot question for the disease example: "Which distinctions within mm change which conclusions can be shared across patients, and which conclusions remain common?" Trace actual pooling and generalization choices; three candidates support the user's choice rather than establish an optimal question.

Open at scoping: the pilot's input set (mm30 reproduction records plus a bounded literature seed are the obvious start), and whether the skill lives in science alone or splits discovery from report rendering.

Related: sci-171ad1 is the causal-answer special case of this ranking; sci-434b9c (structural alternatives) and sci-37f0c3 (testable implications) can later supply consequence evidence; sci-87c165 (scope comparison view) shares the applicability reading; beliefs-8060d0's models context report (beliefs repo, tasks/files/beliefs-8060d0/models-context-report.md) records the model/composite background.

## Notes

- 2026-10-30T01:53:54Z (add): created
  provenance: {"harness_session":"claude-code:a96a86d4-06e5-4f80-a388-909eb54943aa","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"mixed"}
