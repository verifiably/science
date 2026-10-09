---
id: sci-ccd96f
title: "Processing runs and multi-resource datasets: shape the science surface from the GSE24080 spike"
status: idea
priority: 2
created: 2026-10-09T22:29:07Z
updated: 2026-10-09T23:58:47Z
depends: [mm-2c4a7a]
tags: [command-framework]
agent: claude-code/claude-fable-5-1
---

Today dataset holds one regular file and run executes an analysis-spec that targets a proposition and yields an assessment. The kernel defines dataset-production runs (produces and transforms inputs, lineage-basis stamped on the produced dataset) and multi-resource dataset declarations, but no science command mints either. Phase 1 of the multiple-myeloma program needs a normalized package (several files plus manifest) held with lineage to its raw bytes and the workflow that produced it. Whether that is a new command or an extension of run and dataset is decided by the spike's record (mm-2c4a7a), not here. Scope this when that record exists.

## Notes

- 2026-10-09T23:58:47Z (main): evidence from the GSE24080 spike (multiple-myeloma docs/reports/2026-10-09-gse24080-spike.md): dataset holds one regular file, a 7-file package became 5 unrelated dataset records tied only by the locator string; run with a non-existent spec refuses 'not in the session's corpora' before execution; no surface reaches transforms/produces or lineage-basis. Needed shape, from the record: hold a manifest-declared multi-resource dataset, and record a production run whose inputs are held datasets and whose output is the package
