---
id: sci-d1e874
title: Hold and use processed packages with production lineage through science
status: todo
priority: 2
created: 2026-10-14T09:31:55Z
updated: 2026-10-14T09:58:08Z
depends: []
tags: [command-framework]
source: docs/notes/2026-10-14-production-runs-brief.md
agent: claude-code
---

A workspace's processed package (several files plus a manifest) is held as one dataset whose lineage reaches its raw bytes and the workflow that produced it, through science commands, and analyses can read its named members and be replayed. Today the GSE24080 spike (multiple-myeloma docs/reports/2026-10-09-gse24080-spike.md, F1/F2) shows no surface for it, the kernel's own path has gaps, run and verify stage one file per dataset, and a produced package cannot be observed as empirical evidence until beliefs-8ecbb5 is designed. Brief: docs/notes/2026-10-14-production-runs-brief.md. multiple-myeloma's first milestone (mm-a32d58: the GSE24080 pilot package held with lineage) waits on this.
