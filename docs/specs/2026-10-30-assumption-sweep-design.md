# Assumption sweep and research-question comparison

Date: 2026-10-30
Task: sci-b2755f
Status: draft for builder check, then user review; no implementation or pilot authorized by this draft.

## 1. Intent and origin

Help a researcher choose a question whose answer could clarify several important
unknowns across a field. Make premises explicit to expose those connections; the
output is three explained research-question candidates, not a claim to have found
the uniquely optimal question.

The original user ask covers hypotheses, propositions, questions, models and
analyses; implicit measurement assumptions matter alongside written assumptions.
The later clarification is decisive: “I would first survey questions and
assumptions, then see which ones are both impactful, and could be studied given
data available.” Discovery therefore precedes feasibility screening. Important
questions with unavailable data remain visible.

The “multiple myeloma is a single disease” example is one possible question
family. The user meant potentially different underlying disease-system states
(approximately attractor states), with different mechanisms or pathogenesis but
overlapping phenotypes. They did not mean precursor stages are separate diseases.
Neither discrete subtypes nor attractor dynamics are presumed; clusters alone
would not establish dynamics. The pilot must explore other framings too.

Origin evidence: the task's filing and scope notes; Claude session
`a96a86d4-06e5-4f80-a388-909eb54943aa`, human records 9 and 69 (original ask and
pasted agent proposals); Codex session `01a18a6a-6c3b-72b3-bb50-3dae23709299`,
human record 181 (the later clarification). Pasted agent proposals are attributed
as proposals. The task records the agreed one-skill, one-manual-pilot shape. The
budgets, report organization, and comparison procedure below are this designer's
calls, presented for review rather than attributed to the user.

## 2. Scope and approaches

Ship one authored `skills/sweep-assumptions/SKILL.md`, with a report template if
needed, through the existing adapter generator. The installed plugin is named
`science`, so its invocation is `/science:sweep-assumptions`; `/sci:` in the
captured discussion is shorthand, not an additional alias or a plugin rename.
The skill has two internal phases: discovery, then comparative assessment. Its
first use is a bounded multiple-myeloma pilot and one reviewable report.

Considered approaches:

1. **Chosen: an authored skill and a manual report.** Reuses the adapter build,
   keeps scientific judgments attributable, and tests representation needs before
   adding storage. The cost is manual extraction and review; identical inputs do
   not guarantee identical prose or ordering.
2. **Separate sweep/list/rank commands with a stored graph.** Useful only after a
   durable inventory and a demonstrated recurring consumer exist. It would force
   kernel and interface decisions the pilot is meant to inform. Deferred.
3. **Only inspect existing mm30 records.** Cheap and reproducible as a structural
   probe, but too narrow to support the user's broad question discovery. Retained
   as one input, rejected as the complete survey.

No deterministic handler, CLI row, new dependency, graph database, renderer,
kernel relation, scheduled execution, biological computation or data acquisition
is part of this task. `next` keeps its readiness semantics. The sweep does not
choose the research question for the user or change the mm phase-2 agenda.

## 3. Verified starting points and limits

Checked against science `d33f0ed` (pickup revision), beliefs
`cd4fe60adb35b301619d5a838ab835a4aeaa2a3d`, and mm
`a7250080ffa99369884eec670c42a21380482b6f` on 2026-10-30:

- Science's [framework §2 and §10](2026-08-31-command-framework-design.md)
  makes orchestration a skill and already copies authored skill trees through
  `python/src/science/adapters.py`. It does not prepend the command preamble to
  authored skills; the authored workflow must state its own write boundaries.
- `commands/next/prompt.md` and `python/src/science/commands/next.py` classify
  propositions by readiness and admission. They supply no scientific-impact
  ranking. Coordination hypotheses contain queries, not proposition identities.
- Beliefs `python/src/beliefs/spec.py` preserves prose `assumptions` and
  `falsification`. `python/src/beliefs/estimand.py` defines `co_scoped` as canonical
  applicability-map equality and `commensurable` as estimand equality after
  removing identification, retaining claim identity. Neither tests safe pooling.
- The mm30 cut-31 template, biology domain, and configured mm30 successor document
  all declare `dimensions: {}`. The reproduction spec distinguishes stages in
  contrast levels; its applicability is empty. Its method also carries an input
  validity restriction. Missing qualifiers alone establish no author's pooling
  decision. A `subtype-of-concept-concept` operator is not a qualifier dimension.
- The base contract has sources, source assertions and causal DAG composites,
  but no general reliance relation. A causal DAG is not a premise graph.
  The historical models-context report attached to beliefs-8060d0 supplies
  background, not proof that every described limitation remains current.
- The configured world file exists on this host. Filesystem inspection found two
  propositions, one analysis spec and one composite in its mm30 carrier; the
  working carrier has one proposition, one spec and three question files. Neither
  carrier had source/source-assertion or hypothesis files in those kind directories.
  These are file counts, not a validated world selection or a completeness claim.
  The separate old reproduction root also exists; its frozen-spec file was read.
  No kernel validation, dataset-byte read or current holding check ran here.
- The mm roster contains accession, modality, population/timing clues, access,
  overlap, exposure and disposition metadata. Its latest reservation heading is
  2026-10-27: 516 groups, 177 discovery, 339 unresolved, zero reserved, under
  amendment-7. These are recorded counts, not a fresh derivation. The earlier
  phase-2 design's 175/341 baseline is historical. Zero reserved groups neither
  licenses unresolved-data reads nor prevents metadata-based feasibility work.

The configured world's path stays in task notes; committed documents refer to
`SCIENCE_CONFIG`. The pilot rechecks all inputs and records revisions at its own
cutoff. A changed contract or assignment invalidates the relevant observation,
not the whole research goal.

## 4. Inputs, boundaries and report status

The reusable skill takes a topic/project, explicitly identified readable sources
and records, and a finite budget. For this pilot the topic is mm; its inputs are:

- The configured world and the old mm30 reproduction as a representation probe.
  Name each carrier, corpus identity, contract lineage, state/revision and read
  route. Never count the same semantic record twice merely because both carriers
  contain it. Source definitions and fixtures are separately labelled code evidence.
- A bounded literature seed spanning multiple question families, selected under
  §5, with source identities and locators for every attributed assertion.
- The mm roster, current reservation/exposure documents, and available package
  manifests or public metadata. Inspect schemas, assay descriptions, population,
  visit design, access and workflow status; do not open patient rows, expression
  matrices, private phase-2 outputs, mask keys or protected result bundles.

Use existing science read commands where they expose the needed information.
`project-show` supplies coordination metadata; `status` supplies coverage, not a
general record export, and sharing `show` is not such an export either. Where a
field is only inspectable in a record file, use an explicitly identified read-only
file inspection and label it unvalidated unless a supported kernel reader
validates that revision. Do not invent an export command or open a writer. Record
unsupported/missing reads and continue with the evidence actually available.

All scientific record writes remain permit-bound science commands into beliefs.
sci-cc4fb9 owns source/source-assertion and note/topic command routes; reuse them
when shipped, but do not implement them here. This pilot makes no world writes.
Literature is represented in the report as **attributed source-assertion
candidates**, with a stored address only where one already exists. Extraction
does not turn them into empirical belief. Uncited model suggestions are labelled
model-originated proposals, not assertions by a paper; mm-a0dd3f owns the wider
model-prior policy.

The report and its tables are a dated evaluation artifact, stored as a task
attachment, not science-owned record storage, a new inventory service, or world
records. Report-local row IDs are locators within that frozen report only.
Unsupported premises and links stay proposals in it; later ingestion would need
the appropriate governed route and a separate decision. There is no automatic
promotion on report acceptance. No raw paper collection or patient data is copied
into the code repository. Persistent working inputs use the task's declared
host-local storage and retained-item records.

Published literature, including abstracts and search snippets, may itself reveal
results about a cohort. Start screening with bibliographic/design metadata;
before deliberately reading a candidate source's results, check identified cohort
accessions against the current
reservation/exposure records. Previously exposed discovery sources can be read
with that origin recorded. For identified reserved/unresolved cohorts, use only
public bibliographic/design metadata in this pilot; do not open their result
tables or supplements to assess feasibility. Unknown cohort mapping is recorded
and treated the same way for results. If results are encountered incidentally,
record what was actually seen, mark possible new exposure and stop further reads
of that source pending the existing mm exposure/assignment workflow's disposition.
Do not silently mark it unexposed, assign a role, or change mm's policy here.

## 5. Phase A: discover, then freeze the inventory

Before extraction, record the date, repositories/revisions, available corpus
coverage, active contract dimensions, query plan and budget in the report's
coverage section. Proposed pilot budget: at most 24 search queries, 80 unique
title/abstract screens, and 18 full-text primary research articles; local code,
record and roster inspections are accounted separately. An inaccessible full text
remains an abstract-only source, not a completed full-text read. Search metadata
does not establish that a paper's claim was read. Record access restrictions and
the selection/disposition of every screened item. Stop at the caps; expanding
them is a new recorded scope decision, never an invisible retry loop.

Search Europe PMC/PubMed and citation trails through available retrieval tools;
record exact queries, dates, ordering and result positions. Start with six
question families: disease heterogeneity and generalization; initiation and
progression; measurement/proxy validity; microenvironment and immune interaction;
treatment response and resistance; persistence/relapse and temporal evolution.
These are coverage prompts, not selected hypotheses. An open “other” category
retains findings outside them. Use broad question/limitation searches as well as
each family's terms; do not require expression data, attractor language, positive
findings or existing local packages. Use reviews for navigation only; scientific
claims in the report must be traced to inspected primary sources, with unresolved
attribution marked when that is impossible.

Seek two primary articles per family, then use up to six remaining full-text
slots for counterexamples, conflicting findings and uncovered questions. One
article may inform multiple families but consumes one slot. Failure to cover a
family remains a coverage gap; do not fill it from model memory. Selection favors
explicit unanswered questions, premise-sensitive interpretations and contrasting
designs/populations, not citation volume or effect size. Recent literature and
earlier methodological or foundational sources are both eligible. The search is
a bounded survey, not a systematic review or a representative sample of mm.

For each inspected epistemic item, read its assertion and actual scope before
inferring a premise. Preserve the exact authored statement separately from the
sweep's paraphrase. Extract stated premises; suggest implicit premises only with
a reason and an identified dependent inference. A question's wording is not
itself a conclusion, and a query's selected proposition is not automatically a
premise of the hypothesis that carries the query.

Classify scope for each relevant item as explicitly broad, restricted elsewhere,
not recorded, or not expressible under the active contract. These observations
can coexist (for example a recorded contrast plus an unavailable subtype
dimension); retain the evidence for each, rather than forcing a single mutually
exclusive label. Inspect qualifiers, applicability, contrast, method and source
population text. Say “declared scope maps match” for `co_scoped`; judge adequacy
separately. Use `commensurable` only within its actual same-claim semantics.

Preserve all discovered questions, premises, source citations, exclusions and
aliases before considering available-data feasibility. Freeze this inventory by
commit or content hash and identify that version in phase B. Later discoveries
create a new version with a reason and a changed comparison; they never overwrite
the inventory used to justify an earlier shortlist.

## 6. Phase B: trace and compare

Each premise has a report-local ID, exact statement, scope, source locator and
revision, and provenance: source-stated, agent-inferred, or explicitly adopted
(by whom and when). Adoption is not evidence of truth and does not erase original
provenance. Reuse a stored proposition only when meaning and scope fit; otherwise
name the mismatch. Group duplicates by meaning and scope with a written reason,
retaining every occurrence and dissent. Do not merge merely similar language or
different populations, and do not count duplicate deposits as independent support.

Store no new graph. The report's link table names dependent item → premise,
binding both ends to inspected revisions/locators. Distinguish an actual stored
relation (with its original predicate) from a proposed reliance link, and record
the reason and author for the latter. `targets`, `composes`, `assesses`, citation,
query membership and biological causation do
not by themselves mean epistemic reliance. Follow a stored relation only as a
locator; the reliance judgment is separate. Report paths as dependency paths,
never causal paths. Cycles stay visible; traversal uses distinct visited items
so a cycle or multiple paths cannot inflate reach.

Reach is the set of distinct downstream questions and claims in the inspected
inventory, traced through the documented reliance judgments. Count questions and
claims separately and identify aliases and repeated-source dependence. Show which
links are stated, inferred or adopted; distinguish direct and transitive reach.
A source-stated edge is still attributed evidence, not an independently verified
fact. Reach outside the examined inventory is unknown, not zero.

Consequence is a separate per-dependent judgment: reverse, narrow, reinterpret,
refine, no demonstrated change, or unevaluated. State which alternative answer
would have that consequence, why, the supporting material and who judged it.
Do not propagate a reversal automatically along a whole path. Count evaluated
items, unevaluated items, and judgment provenance alongside link counts.

Assess remaining uncertainty from the inspected evidence, including contrary
findings and limits of identification, measurement, sampling and scope. Do not
mistake variability for ignorance, absent evidence for refutation, or a limitation
for a premise the author endorsed. Attribute model-originated additions.

Feasibility follows scientific impact. For each question record the observations
that would discriminate alternatives; required assays/data, population, timing
and comparison; candidate datasets and their current access/heldness/package
status; and unresolved identification, overlap, measurement or sample-design
limits. Availability is not suitability. A roster listing is not possession;
files on disk are not current kernel holding. Unknown is an allowed finding.

Quote relevant spec `falsification` text verbatim, with its spec revision and
target, as an authored lead. Separately explain whether and how it bears on the
premise; it may only concern the target proposition. No relevant text means
“none found in examined specs,” not “unfalsifiable.” Proposed observations do
not become frozen specs or verified feasible experiments.

Give every discovered question a concise comparison disposition. Then recommend
three candidates using qualitative, explicit comparisons of reach, consequence
and remaining uncertainty; explain why the nearest alternatives were not chosen
and disclose ties. Feasibility appears beside that impact judgment and may change
the recommended *next investigation*, but cannot erase a high-impact candidate
because its inputs are missing. No aggregate score, graph-centrality ranking or
“expected information gain” without a probability model and utility target.
For each finalist, test whether the rationale survives counting only source-stated
links; where it does not, label dependence on inferred links rather than quietly
reordering on imagined certainty. If fewer than three defensible candidates are
found, report the shortfall and what evidence is missing; do not fabricate a third
or close the pilot as successful.

## 7. The one report

Produce one Markdown report with these eight sections. Large tables may be
appendices in the same document; each section points to the relevant row IDs.

1. **Coverage:** cutoff, source-selection plan and actual budget usage, queries,
   examined source/record revisions, read and validation status, omissions,
   unavailable inputs, exposures and family coverage. The discovery inventory's
   frozen revision/hash and complete screened-source dispositions live here.
2. **Premise inventory:** exact text, scope evidence/classification, provenance,
   existing record correspondence or mismatch, duplicate groups and occurrences.
3. **Dependency paths:** stored predicates separately from proposed reliance
   links, bound endpoints, reasons, authors and explicit chain uncertainty.
4. **Reach:** distinct downstream questions/claims and paths, direct/transitive
   counts, duplicate-source accounting and link-provenance counts.
5. **Consequences:** per-item counterfactual change, rationale, judge, material,
   evaluated and unevaluated counts, remaining uncertainty and counterevidence.
6. **Tractability:** verbatim authored falsification leads and linking judgments;
   discriminating observations, assays, populations, timing, access, actual
   holding evidence or unknown, exposure/roles, and missing capabilities.
7. **Three candidate questions:** the retained broad question inventory and its
   dispositions, three explained recommendations, comparison with alternatives,
   separate impact and feasibility, and next investigable steps. Explicitly
   bounded by represented coverage, not a field-wide optimality claim.
8. **Representation gaps:** concrete examples, attempted existing representation,
   what failed or is missing, and classification as vocabulary, scope, relation,
   read/write surface, or other. Separate an untested proposed extension from a
   demonstrated contract limit. A proposition plus one reliance relation is a
   hypothesis to evaluate, not the required conclusion.

## 8. Implementation reach and verification

Expected change surface: the new authored skill and optional report template,
generated Claude Code adapter copies, a short README usage entry, and focused
adapter/skill behavior checks under the existing test front door. No new command
declaration, export API or configuration setting is needed. The pilot report is
attached through `tasks attach` to this task, with its source and inventory
revision references, rather than copied manually into task files.

The implementation plan must include a small rehearsal through the complete
report contract before the real survey. Use synthetic records covering empty
scope dimensions with a restriction in a contrast, target-only falsification,
duplicate sources and repeated paths, a cycle, an inferred high-reach chain,
a high-impact question with no suitable data, and absent/invalid read inputs.
The checks must catch unsupported pooling claims, fabricated source attribution,
double-counted reach, hidden unevaluated consequences and treating catalogued
data as held. Test adapter inclusion through the existing generation/fresh-build
checks; do not use prose-substring tests as proof of scientific judgment quality.

The manual pilot is accepted only when all eight sections are present, every
shortlist claim traces to inspected material or an explicit attributed judgment,
the broader pre-feasibility inventory remains inspectable, three defensible
candidates each name discriminating observations and feasibility limits, and
concrete representation gaps are supported by the inspected contracts/records.
A fresh review checks both source attribution and these failure cases. Record
what was not evaluated; missing capability is a result, not a silent fallback.

Full-suite baseline and policy-appropriate implementation tests happen at
implementation Setup, after design and plan approval. This document-only phase
runs `just check` and records its result; it makes no claim that runtime behavior
or the manual scientific workflow has been tested.

## 9. Gates and remaining builder decisions

The user reviews this frozen design before an implementation plan is written;
the plan has its own user review before the skill or pilot is implemented. A
fresh builder check precedes the design handoff. Implementation may choose table
layout, local row-ID prefixes and the smallest fixture organization without
changing these semantics. Exact papers are selected by the recorded survey,
never preselected around the disease-state example. No choice here grants live
desktop use, paid access, external publication or a persistent service.

The principal risks are biased coverage, attributing inferred premises to authors,
inflated reach through repetition, and feasible-data convenience displacing
scientific importance. The source ledger, revision binding, separate judgments,
pre-feasibility freeze and sensitivity check make those risks inspectable; they
do not make the ranking objective or eliminate model priors.
