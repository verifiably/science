---
id: sci-b2755f
title: Sweep epistemic records for the premises they rely on and rank the questions whose answers would clarify the most
status: doing
priority: 2
size: l
complexity: high
process: planned
owner: feat/sci-b2755f-assumption-sweep
created: 2026-10-30T01:53:54Z
updated: 2026-10-30T07:33:45Z
started: 2026-10-30T07:08:27Z
depends: []
tags: []
origin: mixed
spec: docs/specs/2026-10-30-assumption-sweep-design.md
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
- `co_scoped` is canonical equality of applicability maps (two empty maps are equal); report "declared scope maps match", then judge adequacy separately. `commensurable` compares estimands with identification removed while retaining claim identity; it is not a general comparator across related propositions.
- `SpecDraft.assumptions` and `falsification` are prose; the sweep never edits frozen specs.

Hypothesis under test, not a deliverable: a premise stated as a proposition plus one reliance relation (provenance, scope, revision binding, link to query-based hypotheses) may suffice in beliefs. The gap list is the evidence for or against.

Candidate example only, not the selected pilot question: "Which distinctions within mm change which conclusions can be shared across patients, and which conclusions remain common?" The user clarified that other framings must be explored before selecting questions to pursue. Their intended disease example concerns potentially different underlying disease-system states (approximately attractor states) within the label multiple myeloma, with differences in mechanism or pathogenesis but overlapping phenotypes/endpoints; it is not a proposal to label precursor or disease stages as different diseases. This is a hypothesis to investigate, not an established model; observed clusters alone would not establish attractor dynamics. Trace actual pooling and generalization choices where this candidate warrants it. Three candidates support the user's choice rather than establish an optimal question.

User sequencing clarification (current discussion): "I would first survey questions and assumptions, then see which ones are both impactful, and could be studied given data available." Discover candidate questions broadly across mm before assessing impact and available-data feasibility; do not anchor the survey on the disease-state example or filter discovery to analyses convenient with the existing expression data. Retain scientifically important candidates lacking suitable data, with the missing capability explicit.

Scoping decisions (agent choices, open to correction): keep one science skill with two internal phases: discovery, then comparative assessment/reporting. Preserve the discovered inventory and citations before selecting the top three, so selection does not erase alternatives; no separate discovery service or report renderer is required for the pilot. Start from mm30 reproduction records as a representation probe, a bounded literature seed spanning multiple question families, and the mm dataset roster/package metadata for feasibility. The reproduction is not a representative sample of the field. Record source-selection criteria, search boundaries and a finite source budget before extraction; exact papers are discovered by the survey, not preselected around attractor states. Verify whether reproduction records are actually available, recording absent inputs rather than treating fixture definitions as an inspected corpus.

Execution scope: this is a planned task for one reusable science skill and its bounded manual pilot, not an instruction to start the pilot during scoping. Initial read-only discovery informs the written design before choosing research targets; spec and implementation-plan reviews precede skill implementation. The first pass inventories active domain dimensions, scope recorded elsewhere and missing scope representation. It carries the known empty-dimensions limitation into coverage from the start. Scope vocabulary/extensions may be the first beliefs-side need; a reliance relation is not a predetermined outcome.

Done when: the one skill and manual pilot produce the eight-part report above, with a broad discovered question inventory, three explained candidates, separate impact and feasibility judgments, and concrete representation gaps. Each shortlisted candidate identifies relevant data/assays, population and timing, observations needed to discriminate alternatives, access/heldness, and remaining feasibility limits. Dataset listing is not possession or suitability. Feasibility review initially uses metadata and respects existing exposure/reservation boundaries; it does not consume reserved data or run new biological analyses. No kernel changes, recurring execution or extra list/rank commands are included.

Where to start: beliefs python/tools/reproduction/mm30-cut31.yaml, python/tools/reproduction/spec.py, domains/biology/DOMAIN.yaml and python/src/beliefs/estimand.py; science commands/next and its command-framework design; mm docs/roster/roster.yaml, docs/roster/reservation.md and the phase-2 descriptive-report design. Reuse sci-cc4fb9 for authored research skills and source/source-assertion write routes rather than duplicate them; absence of those commands does not block read-only discovery or license an alternate scientific store. Keep literature statements attributed as source assertions and inferred premises explicitly separate. Consult mm-a0dd3f for model-prior attribution without conflating that policy work with this field-wide survey.

Related: sci-171ad1 is the causal-answer special case of this ranking; sci-434b9c (structural alternatives) and sci-37f0c3 (testable implications) can later supply consequence evidence; sci-87c165 (scope comparison view) shares the applicability reading; beliefs-8060d0's models context report (beliefs repo, tasks/files/beliefs-8060d0/models-context-report.md) records the model/composite background.

## Notes

- 2026-10-30T01:53:54Z (add): created
  provenance: {"harness_session":"claude-code:a96a86d4-06e5-4f80-a388-909eb54943aa","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"mixed"}
- 2026-10-30T02:04:27Z (main): scope: scoped; promoted to P2/l/high/planned for one science skill and a bounded manual pilot. Current user clarification keeps disease-system/attractor states within mm as one candidate, not a chosen question and not precursor-stage reclassification. Broad discovery precedes separate impact and available-data feasibility assessment; eight-part report retained. Agent decisions: one skill with discovery and assessment/report phases; mm30 as representation probe, broad bounded literature seed, mm roster/package metadata as feasibility inputs. Known empty scope dimensions are an initial finding, not a predetermined reliance-relation design. Evidence: beliefs cd4fe60, science bc0b6ae, existing sci-cc4fb9 and mm-a0dd3f; no duplicate research task or new brief needed. origin: filing matched in claude-code:a96a86d4-06e5-4f80-a388-909eb54943aa lines 96/101 (created result and timestamp); human turns 9 and 69 contain original user material and pasted agent proposals, kept distinct; latest clarification is the user in this session; mixed origin retained. Next executing agent performs initial read-only discovery to inform the written design, then obtains the required spec and plan reviews before implementing the skill. No pilot ran in this scope pass.
  provenance: {"harness_session":"codex:01a18a6a-6c3b-72b3-bb50-3dae23709299","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-30T07:08:27Z (main): started
  provenance: {"harness_session":"codex:01a18ba2-9d92-7f91-8f82-774c55ba33d3","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-30T07:09:13Z (feat/sci-b2755f-assumption-sweep): resumed
  provenance: {"harness_session":"codex:01a18ba2-9d92-7f91-8f82-774c55ba33d3","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-30T07:11:40Z (feat/sci-b2755f-assumption-sweep): Origin checked: Claude session a96a86d4-06e5-4f80-a388-909eb54943aa human records 9 and 69 carry the original ask and pasted proposals; Codex session 01a18a6a-6c3b-72b3-bb50-3dae23709299 human record 181 contains the later disease-system-state clarification and broad-survey-before-feasibility sequence. Pasted agent proposals are not treated as independent human authorship. No unanswered intent question requires repeating that discussion. Planned path: design in .worktrees/sci-b2755f, fresh builder check, user design review, then implementation-plan review.
- 2026-10-30T07:11:42Z (feat/sci-b2755f-assumption-sweep): Setup: created and locked .worktrees/sci-b2755f on feat/sci-b2755f-assumption-sweep; ran root-guide hook setup and README cd python && uv sync successfully. No tracked setup changes. Full-suite baseline deliberately deferred to implementation Setup under the planned-work rule; no product code changed or tests run. Preliminary discovery is read-only; configured-world paths and old reproduction files exist, but existence/raw file inspection is not kernel validation or current holding.
- 2026-10-30T07:18:03Z (feat/sci-b2755f-assumption-sweep): review: spec round 1 — verdict: accept; findings: none; reviewer: codex/gpt-6.1-sol
- 2026-10-30T07:18:09Z (feat/sci-b2755f-assumption-sweep): attached: builder-check-round-1-report.md (595 bytes): Full read-only builder review of design af4b359; accepted with no findings; reviewer codex/gpt-6.1-sol
- 2026-10-30T07:18:13Z (feat/sci-b2755f-assumption-sweep): attached: design-review-ledger.md (831 bytes): Design round 1 ledger; no rulings or deferred minors; user review remains
- 2026-10-30T07:18:46Z (feat/sci-b2755f-assumption-sweep): retained: {"host":"titan","kind":"worktree","path":".worktrees/sci-b2755f","state":"kept","verification":"verified","purpose":"User review of frozen design af4b359e88f2a51368c6eac711516f550136cc26, followed by implementation planning and its review; hydrated workspace on feat/sci-b2755f-assumption-sweep. Full builder report and ledger are attached; temporary plan-workspace copies removed after SHA-256 equality checks.","next_owner":"task:sci-b2755f","cleanup_trigger":"After approved implementation is completed and integrated, inspect all retained evidence and perform the worktree removal checks"}
- 2026-10-30T07:18:48Z (feat/sci-b2755f-assumption-sweep): Design phase verification: just check passed again after attaching the accepted builder review and ledger; git diff --check passed and tracked tree clean. No code tests, pilot, world writes, biological data reads, pushes or host-pointer changes. No extra task scratch/evidence copies remain; the worktree retains its hydrated environment. Next user gate is the frozen design; approval triggers agent implementation planning, not immediate pilot execution.
- 2026-10-30T07:18:51Z (feat/sci-b2755f-assumption-sweep): parked (waiting on user, review): User reviews science commit af4b359e88f2a51368c6eac711516f550136cc26, docs/specs/2026-10-30-assumption-sweep-design.md in .worktrees/sci-b2755f; after approval the agent resumes here and writes the implementation plan for its separate review. Builder check accepted with no findings; report and ledger attached. No pilot or implementation started.
  provenance: {"harness_session":"codex:01a18ba2-9d92-7f91-8f82-774c55ba33d3","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-30T07:33:45Z (feat/sci-b2755f-assumption-sweep): resumed
  provenance: {"harness_session":"codex:01a18ba2-9d92-7f91-8f82-774c55ba33d3","harness_session_source":"CODEX_THREAD_ID"}
