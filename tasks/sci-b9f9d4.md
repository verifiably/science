---
id: sci-b9f9d4
title: "Convention for a project's reference files (article, book and supplement PDFs)"
status: idea
priority: 3
reviewed: true
created: 2026-10-11T11:09:43Z
updated: 2026-10-14T09:32:42Z
depends: [sci-76de75]
parent: sci-f6c61b
tags: []
source: "mm:2026-10-11-reference-files"
agent: claude-code/claude-opus-5-5
---

context: in proto-science, each project kept the PDFs of its articles, books and supplements beside its other entities, in `papers/pdfs/` with a `references.bib`, outside version control. That made it possible to revisit a reference later. The current ecosystem has no equivalent:
- lit defers PDFs to Paperpile (corpus design 2026-09-21: "No PDF paths").
- quarry does not download files.
- The kernel `acquisition` operation (sci-a17882) hashes and stores dataset bytes, but says nothing about papers.

need: a workspace project (for example multiple-myeloma) needs somewhere to keep the reference files it consulted: review supplements scanned for accessions, and articles read for provenance. The store should be addressable from records by content hash and DOI/PMID, and kept out of git.

questions:
- Is this `acquisition` with a paper locator?
- Is it a per-workspace directory with a manifest?
- Is it lit's concern, linked to Paperpile?
- Where do the bytes live (Dropbox, WORK_ROOT storage), and what does a record cite?

interim: multiple-myeloma keeps its files in its gitignored `data/references/`, listed on the task that uses them (mm-0a147a).

## Notes

- 2026-10-14T09:32:42Z (main): scope: briefed; kernel source records carry identifiers only and holdings attest dataset resources, lit leaves PDFs to Paperpile and quarry downloads nothing, so where reference bytes live and what a record cites is open; parented under goal sci-f6c61b with research sci-76de75, which this waits on; interim stays multiple-myeloma's gitignored data/references/ (mm-0a147a); brief: docs/notes/2026-10-14-reference-files-brief.md
