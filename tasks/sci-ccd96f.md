---
id: sci-ccd96f
title: "Processing runs and multi-resource datasets: shape the science surface from the GSE24080 spike"
status: idea
priority: 2
created: 2026-10-09T22:29:07Z
updated: 2026-10-09T22:29:08Z
depends: [mm-2c4a7a]
tags: [command-framework]
agent: claude-code/claude-fable-5-1
---

Today dataset holds one regular file and run executes an analysis-spec that targets a proposition and yields an assessment. The kernel defines dataset-production runs (produces and transforms inputs, lineage-basis stamped on the produced dataset) and multi-resource dataset declarations, but no science command mints either. Phase 1 of the multiple-myeloma program needs a normalized package (several files plus manifest) held with lineage to its raw bytes and the workflow that produced it. Whether that is a new command or an extension of run and dataset is decided by the spike's record (mm-2c4a7a), not here. Scope this when that record exists.
