---
id: sci-dfec5b
title: Establish whether the kernel or science mints a production run's dataset and stages multi-file inputs
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-14T09:32:16Z
updated: 2026-10-14T09:58:07Z
depends: []
parent: sci-d1e874
tags: [command-framework]
source: docs/notes/2026-10-14-production-runs-brief.md
agent: claude-code
---

Question: (1) Is a dataset-production run's produced dataset record (its stored resources and its stamped lineage basis) and the staging of a multi-resource input meant to be kernel work behind execute_production_run, or the caller's? Today runrecord.publication_plan writes only the run record, whose produces edge names production.mint_dataset's address with no dataset record behind it; the run's output bytes are only hashed in scratch; no code turns a StampedBasis into the stored lineage-basis facet; and boundary._stage_inputs refuses any held input that is not one regular file. (2) Where does the eligibility boundary leave a produced package: assessment writes refuse an ineligible observed dataset (corpus._refuse_ineligible) and the kernel refuses the empirical-observation facet beside a lineage basis or producer (acquisition.py bearer_refusal), so should the first milestone include assessments that observe a produced package (unshelving beliefs-8ecbb5) or defer them, and which multiple-myeloma phase first needs one?
Where to start: beliefs python/src/beliefs/boundary.py (execute_production_run, _stage_inputs), runrecord.py publication_plan, production.py mint_dataset, stored.py dataset_node(basis=…), acquisition.py, corpus.py eligibility_refusal; beliefs docs/designs/2026-08-02-computation-reproducibility-design.md §5.2 and its one-output-per-run rule; beliefs-8ecbb5 and its shelf condition; git log -S mint_dataset; multiple-myeloma's program goal mm-a32d58 and phase-1 protocol for when packages are first analysed; the brief docs/notes/2026-10-14-production-runs-brief.md.
Bound: read the design, code and history, and search beliefs tasks; no implementation, no new kernel requirement filed, and beliefs-8ecbb5 left shelved (recommend only).
Expected result: For each of the four gaps, whether the design assigns it to the kernel (unbuilt) or the caller, with evidence; an include-or-defer recommendation on produced-package eligibility naming the first consumer; recorded on this task and in the brief's Unanswered questions, with the beliefs requirements sci-ccd96f's spec must file.
Ideas it wakes: On completion, run `tasks note sci-ccd96f --no-reviewed "<finding>"`, before this result's branch merges.
