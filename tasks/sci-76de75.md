---
id: sci-76de75
title: Establish whether a source record can cite reference bytes held in the store
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-10-14T09:32:40Z
updated: 2026-10-14T09:32:40Z
depends: []
parent: sci-f6c61b
tags: []
source: docs/notes/2026-10-14-reference-files-brief.md
agent: claude-code
---

Question: Can a beliefs source record (addressed source:<digest> from DOI, PMID, ISBN or accession) be tied to a file held in the session's store by content digest, the way a dataset declares resources and holdings observations attest them, or does holding a PDF today require minting it as a dataset, which would make a paper an empirical dataset?
Where to start: beliefs python/src/beliefs/stored.py source_node (identifiers facet only) and dataset_node; holdings/boundary.py write and holdings observations; the glossary entries Source address, Acquisition and Holdings; science python/src/science/commands/dataset.py (holds one file through holdings.boundary.write); lit docs/specs/2026-09-21-corpus-design.md (Paperpile is the system of record for PDFs); the brief docs/notes/2026-10-14-reference-files-brief.md.
Bound: read code and docs, and search beliefs, lit and quarry tasks; no implementation and no write to any world.
Expected result: Which of the brief's alternatives the kernel supports today, what each would need, and a recommendation; recorded on this task and in the brief.
Ideas it wakes: On completion, run `tasks note sci-b9f9d4 --no-reviewed "<finding>"`, before this result's branch merges.
