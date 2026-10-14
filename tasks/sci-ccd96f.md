---
id: sci-ccd96f
title: "Processing runs and multi-resource datasets: shape the science surface from the GSE24080 spike"
status: idea
priority: 2
reviewed: true
created: 2026-10-09T22:29:07Z
updated: 2026-10-14T09:58:10Z
depends: [mm-2c4a7a, sci-dfec5b]
parent: sci-d1e874
tags: [command-framework]
agent: claude-code/claude-fable-5-1
---

Today dataset holds one regular file and run executes an analysis-spec that targets a proposition and yields an assessment. The kernel defines dataset-production runs (produces and transforms inputs, lineage-basis stamped on the produced dataset) and multi-resource dataset declarations, but no science command mints either. Phase 1 of the multiple-myeloma program needs a normalized package (several files plus manifest) held with lineage to its raw bytes and the workflow that produced it. Whether that is a new command or an extension of run and dataset is decided by the spike's record (mm-2c4a7a), not here. Scope this when that record exists.

## Notes

- 2026-10-09T23:58:47Z (main): evidence from the GSE24080 spike (multiple-myeloma docs/reports/2026-10-09-gse24080-spike.md): dataset holds one regular file, a 7-file package became 5 unrelated dataset records tied only by the locator string; run with a non-existent spec refuses 'not in the session's corpora' before execution; no surface reaches transforms/produces or lineage-basis. Needed shape, from the record: hold a manifest-declared multi-resource dataset, and record a production run whose inputs are held datasets and whose output is the package
- 2026-10-14T09:31:56Z (main): scope: briefed; dependency mm-2c4a7a is done and its record (F1, F2) is in; the kernel side has gaps too (produced dataset never minted or stored, lineage basis never stamped, multi-file inputs refused at staging), so parented under goal  with research , which this waits on; when it lands, scope this as a planned spec covering both the science surface and the beliefs requirements; brief: docs/notes/2026-10-14-production-runs-brief.md
- 2026-10-14T09:32:25Z (main): scope: correction to the preceding audit note, whose ids were lost to a shell error: the goal is sci-d1e874 and the research this waits on is sci-dfec5b
- 2026-10-14T09:58:10Z (main): scope: brief revised after review (2026-10-14): adds the eligibility boundary (beliefs-8ecbb5; include or defer), member resolution and staging in run and verify with replay in acceptance, and manifest identity (the spike's datapackage.json differed only in created); research sci-dfec5b widened to match
