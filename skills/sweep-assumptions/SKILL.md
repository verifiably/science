---
name: sweep-assumptions
description: Use when finding premises behind epistemic records or choosing research questions whose answers could clarify several unknowns across a field.
---

# Sweep assumptions

Produce a dated, eight-part research report using the [report template](report-template.md).
Discover broadly before comparing scientific impact and then feasibility. Recommend
three explained questions for the researcher to choose among; the ranking covers
only the inspected inventory, not the whole field or a uniquely optimal question.

## Set up the run

Record topic/project, explicit input locations and revisions, output destination,
active program read/exposure policy, available readers and a finite source budget.
Missing locations/records are unavailable inputs, not a corpus to invent. Use
supported science reads where available; label direct record-file inspection
unvalidated unless a supported kernel reader validates that revision. Record
carrier/corpus identity, contract lineage and state separately; old reproductions,
fixtures and source definitions are not a validated current world. A file existing
or dataset being catalogued establishes neither possession nor kernel holding.

For the mm pilot, default caps are 24 search attempts, 80 unique bibliographic
screens and 18 deliberate primary-article full-text retrieval attempts. Count
failed access and retries as attempts; count completed full texts separately.
Log metadata and isolated-section reads separately. Use other finite budgets for
other topics. Stop at applicable caps; expansion needs a recorded scope decision.

Plan broad question/limitation searches across distinct question families and an
open other category, including contrasting populations/designs and counterevidence.
For mm: heterogeneity/generalization, initiation/progression, measurement/proxies,
microenvironment/immunity, treatment/resistance, persistence/relapse/time. Seek
two primary articles per family, with up to six additional full-text attempts for
conflicts or gaps. Do not select only locally convenient assays or anchor on a
favored example; observed clusters alone do not establish attractor dynamics.
Record exact queries, ordering, positions, date, selection reasons and exclusions.

## Screen before results

1. Retrieve bibliographic identifiers/title/date without abstracts or result-bearing
   snippets. Match PMID, normalized DOI and accession aliases against all program
   roster publication fields, then overlap groups, current assignments and exposure
   evidence. Conflicting identifiers remain unresolved; a title match is only a lead.
2. For unknown, incomplete or additional-cohort mappings, request only separately
   addressable data-availability and necessary design/methods metadata. Recheck every
   accession. Extract/project sections before displaying them to the analyst;
   semantic reading of the whole document is already a read. Missing or ambiguous
   isolation means metadata-only, never a whole-body fallback. Prove the route with
   synthetic sentinels first, then one bounded live probe on a permitted source.
3. Read abstracts/results only under the active program's policy for ALL implicated
   cohorts and the specific results. One permitted cohort does not grant blanket
   permission. Mixed inseparable results and unresolved mappings stay metadata-only.
   Pure methods/theory without cohort results needs evidence of that condition;
   absence from the roster does not establish it. Reviews supply titles and isolated
   reference lists for navigation; trace scientific assertions to inspected primaries.
4. Incidental result text: record source, actual content seen, reader/date and known
   or unknown mapping; distinguish confirmed from possible exposure. Stop that source,
   retain evidence on the task and route it to the program's exposure/assignment
   workflow. Continue other sources. Pending disposition excludes its results from
   ranking/consequence evidence. The sweep changes no assignments or policy.

Log every screened source's permitted, attempted and actual reads, failures and
omissions. Offered/search-listed material is not read evidence. Attribute unresolved
assertions as unresolved; model suggestions are model-originated proposals.

## A. Discover and preserve

Read assertions and all scope locations: qualifiers, applicability, contrast,
method, source population and timing. Preserve exact authored statements separately
from paraphrases. Classify scope as explicitly broad, restricted elsewhere, not
recorded and/or not expressible under the active contract, with evidence for each.
Empty scope maps do not prove author pooling. `co_scoped` means “declared scope maps
match”; judge adequacy separately. `commensurable` compares same-claim estimands
without identification, not arbitrary related propositions.

Inventory questions and premises across the chosen families before feasibility
screening. Give premises exact text, scope, source/revision and provenance:
source-stated, agent-inferred, or explicitly adopted (who/when, preserving origin).
Infer a premise only with a dependent inference and reason. For example, an analyst
may infer “bulk signal tracks the intended process rather than cell mixture” from
an interpretation of a bulk proxy; that does not make it the paper's stated premise.
A question is not a conclusion. Reuse a stored proposition only when meaning AND
scope fit. Group duplicate meanings/scopes with reasons and retained occurrences,
aliases and dissent; repeated deposits are not independent support.

Freeze a self-contained Markdown discovery inventory with citations, coverage,
source dispositions and all alternatives. Compute SHA-256, attach a versioned copy
to the task, verify its `tasks show` entry and hash, then begin phase B. If a worker
cannot attach, it returns phase A and waits for controller confirmation. A path/hash
alone is not preservation. New discoveries produce a new version and changed
comparison, never edits to the freeze supporting an earlier shortlist.

## B. Trace and compare

Use report-local dependent → premise links bound at both endpoints to inspected
revisions/locators. Keep stored predicates separate from proposed reliance links;
name the latter's reason and author. `targets`, `composes`, `assesses`, citations,
query membership and biological causation are locators, not automatic reliance.
These are epistemic dependency paths, not causal paths. Store no new graph.

Count distinct downstream question and claim endpoints separately, with direct
and transitive counts. A visited-item set prevents cycles or repeated paths from
inflating reach; premise nodes are not extra claim/question endpoints. Show actual
endpoint sets, duplicate-source accounting and stated/inferred/adopted link counts.
Reach beyond the inventory is unknown. For each finalist, recompute reach using
ONLY source-stated links and explain whether the recommendation survives; flag
reliance on inferred chains explicitly.

Judge consequences per dependent and alternative answer: reverse, narrow,
reinterpret, refine, no demonstrated change or unevaluated; name why, judge and
supporting material. Reversal never propagates automatically. Show evaluated and
unevaluated endpoint sets/counts and judgment provenance separately from link
provenance. Assess remaining uncertainty and contrary evidence; variability is not
ignorance, absence is not refutation, and a limitation is not an endorsed premise.

Then assess discriminating observations, assays/data, population, comparison,
timing, access/heldness/package evidence, overlap and identification/measurement
limits. Keep unknowns explicit. Quote relevant spec `falsification` verbatim with
revision/target as an authored lead, and separately judge its link to the premise:
it may test only the target. None found means “none found in examined specs,” not
“unfalsifiable.” Do not edit frozen specs or claim an experiment is proven feasible.

Give every discovered question a disposition. Explain three recommendations and
nearest alternatives/ties using separate reach, consequence, uncertainty and
feasibility judgments. High-impact questions lacking suitable data remain visible;
feasibility can change the next investigation, not erase scientific importance.
No aggregate score, centrality ranking or expected information gain without a
probability model and utility target. Fewer than three defensible candidates is
an incomplete pilot, with missing evidence named rather than a fabricated third.

## Finish and boundaries

Report concrete representation failures and attempted existing representations:
vocabulary, scope, relation, read/write surface or other. A proposition plus a
reliance relation is a hypothesis to evaluate, not a predetermined kernel change.

This workflow is read-only: no world writes, data acquisition, biological analyses,
patient/matrix reads, protected results, policy changes, scheduling or services.
Scientific writes require existing permit-bound science commands into beliefs;
reuse source/source-assertion routes when shipped. Extracted literature remains
attributed source-assertion candidates, never empirical belief by extraction.
Reports/row IDs are dated task artifacts, not a scientific store or automatic
promotion on acceptance. Keep raw papers and patient data out of Git. Attach the
report and source/read ledger through `tasks attach`, verify presence/hashes, and
account for retained scratch. Review checks source attribution and judgments;
adapter tests establish packaging only.
