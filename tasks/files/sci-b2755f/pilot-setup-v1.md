# Bounded mm assumption-sweep pilot setup v1

Frozen before literature extraction on 2026-10-30. Controller/analyst: Codex.
Topic: broad mm questions/premises, not a selected attractor-state question.
Task: sci-b2755f; execution step sci-d3044e. Rehearsal accepted without findings by
codex/gpt-6-astra; no live provider proof claimed.

## Revisions and inputs

Science skill/fixtures: 461f4072b27825635887906892930da6ba7c0388.
Science Task-3 pickup: c194f6cd3f80a2472f030b5ea9bc32da935021d2.
Beliefs: cd4fe60adb35b301619d5a838ab835a4aeaa2a3d.
MM: a7250080ffa99369884eec670c42a21380482b6f.
Quarry: 7008433c8d3007b38a8fb08598e7e3ed49e965eb.
Use registered quarry checkout with its own environment and uv run --frozen quarry,
never an unrelated PATH install. Its inspected PubMed _row uses ESummary and
returns title, PMID, DOI/PMC xrefs, date and journal; no abstract/result snippet.
Ordering is ESearch service-default, no explicit sort; preserve returned positions.

Explicit configured world: SCIENCE_CONFIG, world aec951bc6becacced13df8f7ae6f8abf;
mm30 and working carriers. Successful worktree science status reports known/live/
present corpora 8b5d0c802677ee445e2b9d91ebf5d6a7 and
4b1c238d06cf7fa18def5ea2554d4f16. It is coverage, not a field export or holdings proof.
Direct record fields will be explicitly unvalidated file inspection. Code-declared
old mm30 reproduction root exists; inspect separately, not as the configured world.
Code/domain mm30 dimensions are empty; structured omissions do not prove pooling.
Local record/code inspections are separate from literature budgets.

Current mm policy: exposure ledger sections 1–2; phenotype-conditioned results in
any form count, with overlap-group propagation. Abstracts have no exemption.
Fresh assign(load_roster, load_catchments) using mm's own pure functions: 1559
entries, 516 groups, 177 discovery, 339 unresolved, 0 reserved. Group role and actual
exposure evidence must both be checked; no role change or unresolved data read.
Match all roster PMID/normalized DOI/alias fields, through cohort groups, before
results. Additional or conflicting cohorts require isolated availability/design
metadata, never an abstract to discover accessions. Record actual/possible
incidents separately, stop only the source, route real incidents to mm workflow.

## Finite discovery plan

Caps: 24 search attempts, 80 unique bibliography screens, 18 deliberate full-text
retrieval attempts including failures/retries; completed reads counted separately.
Metadata and isolated-section requests logged separately. No expansion assumed.
Start with a broad question/limitation query, then six families, each six metadata
hits. Queries listed below are fixed starting searches, not a promised source yield.
Use reviews only as titles/isolated-reference navigation; inspect primaries for
scientific assertions. Seek two primary sources per family; reserve up to six
full-text attempt slots for counterevidence and uncovered questions. Later query
adaptations must be logged within caps. Recent and older foundational studies are
eligible; default service ordering is a coverage bias. Do not filter on held data,
expression convenience, effect size or attractor terminology. Keep open other.

Before any abstract/results, demonstrate the rehearsed section extractor on one
permitted source; known relevant cohorts must already be exposed discovery groups.
One probe only; if the response cannot be isolated, mark the route unavailable and
skip sources that need it. Section-only reads happen before analyst display; no
semantic scanning of a full page or review body. Raw response bytes stay local,
not task/Git attachments. No patient rows, matrices, private phase-2 reports, masks,
new analysis, data acquisition, world writes, scientific record/assignment changes,
scheduling, service or external publication.

Freeze all discovered questions/premises with source dispositions/citations as
versioned discovery-inventory-v1.md on parent, verify tasks show and SHA-256 BEFORE
metadata-based feasibility comparisons. Then separate reach/consequence/uncertainty
from feasibility, retain important questions lacking data, and report a shortfall
honestly. No fabricated third question and no aggregate information-gain score.

## Input byte fingerprints

| Input | SHA-256 |
|---|---|
| mm roster | 1dcea1f26941333a7df000ce4c3d0f973df59f3dd34eb08caab186c42050d536 |
| mm catchments | b218e44744e5cbb7b23aa9b221a164cec09f8bda17757f9b93c30e064c1e47ab |
| mm reservation | ce570f657f1ba3236546846efbca1a98d420923afe76c72c092501830d4ecdaf |
| mm exposure policy | e09d9aad951e1b6005a5e675be5e66658ccaa8bd055012ed46c9567fdb5fd62a |
| biology contract | 876fc8920d63d391ad2b1962892c1ac945ca2dad9ba228db18d5d3974657b710 |
| active contract | 7aaa56b2abff1621daf016fe732ce3106c0e4d52ba246fc4ed3fa29406914903 |

## Starting queries

1. broad, limit 6: `"multiple myeloma"[Title/Abstract] AND (question* OR limitation* OR challenge*) AND ("1900/01/01"[Date - Publication] : "2026/10/30"[Date - Publication])`
2. heterogeneity, limit 6: `"multiple myeloma"[Title/Abstract] AND (heterogeneity OR subtype* OR generaliz*) NOT review[Publication Type] AND ("1900/01/01"[Date - Publication] : "2026/10/30"[Date - Publication])`
3. progression, limit 6: `"multiple myeloma"[Title/Abstract] AND (initiation OR progression OR precursor) NOT review[Publication Type] AND ("1900/01/01"[Date - Publication] : "2026/10/30"[Date - Publication])`
4. measurement, limit 6: `"multiple myeloma"[Title/Abstract] AND (measurement OR proxy OR "cell mixture" OR purity) NOT review[Publication Type] AND ("1900/01/01"[Date - Publication] : "2026/10/30"[Date - Publication])`
5. microenvironment, limit 6: `"multiple myeloma"[Title/Abstract] AND (microenvironment OR immune) NOT review[Publication Type] AND ("1900/01/01"[Date - Publication] : "2026/10/30"[Date - Publication])`
6. treatment, limit 6: `"multiple myeloma"[Title/Abstract] AND (response OR resistance) NOT review[Publication Type] AND ("1900/01/01"[Date - Publication] : "2026/10/30"[Date - Publication])`
7. persistence, limit 6: `"multiple myeloma"[Title/Abstract] AND (relapse OR persistence OR "clonal evolution") NOT review[Publication Type] AND ("1900/01/01"[Date - Publication] : "2026/10/30"[Date - Publication])`
