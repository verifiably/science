---
id: sci-dfec5b
title: Establish whether the kernel or science mints a production run's dataset and stages multi-file inputs
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-14T09:32:16Z
updated: 2026-10-14T09:32:16Z
depends: []
parent: sci-d1e874
tags: [command-framework]
source: docs/notes/2026-10-14-production-runs-brief.md
agent: claude-code
---

Question: Is a dataset-production run's produced dataset record (its stored resources and its stamped lineage basis) and the staging of a multi-resource input meant to be kernel work behind execute_production_run, or the caller's? Today runrecord.publication_plan writes only the run record, whose produces edge names production.mint_dataset's address with no dataset record behind it; the run's output bytes are only hashed in scratch; no code turns a StampedBasis into the stored lineage-basis facet; and boundary._stage_inputs refuses any held input that is not one regular file.
Where to start: beliefs python/src/beliefs/boundary.py (execute_production_run, _stage_inputs), runrecord.py publication_plan, production.py mint_dataset, stored.py dataset_node(basis=…); beliefs docs/designs/2026-08-02-computation-reproducibility-design.md §5.2 and its one-output-per-run rule; git log -S mint_dataset for the cut that introduced it; the brief docs/notes/2026-10-14-production-runs-brief.md.
Bound: read the design, code and history, and search beliefs tasks; no implementation and no new kernel requirement filed.
Expected result: For each of the four gaps, whether the design assigns it to the kernel (and it is unbuilt) or to the caller, with the evidence; recorded on this task and in the brief's Unanswered questions, plus a recommendation for which beliefs requirements sci-ccd96f's spec must file.
Ideas it wakes: On completion, run `tasks note sci-ccd96f --no-reviewed "<finding>"`, before this result's branch merges.
