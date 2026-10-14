---
id: sci-76de75
title: Establish what binds a source record to held reference bytes and retrieves them
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-10-14T09:32:40Z
updated: 2026-10-14T09:58:08Z
depends: []
parent: sci-f6c61b
tags: []
source: docs/notes/2026-10-14-reference-files-brief.md
agent: claude-code
---

Question: What is missing between a beliefs source record (addressed source:<digest> from DOI, PMID, ISBN or accession; identifiers facet only) and reference bytes held without empirical standing: a governed relation binding source and content digest, a retrieval interface from such a citation to the held bytes, or both? Evaluate existing non-empirical holding first: science dataset without a locator mints a dataset with no empirical-observation facet, and holdings.boundary.write acts on a store location and bytes without requiring a dataset record. A citation must name source and digest (an article, its supplement and a corrected PDF share a DOI); a location manifest must not carry its meaning.
Where to start: beliefs python/src/beliefs/stored.py (source_node, dataset_node, relation kinds), holdings/boundary.py write and holdings observations, the profile's relation vocabulary; science python/src/science/commands/dataset.py and holdings.py (held_path_for, dataset_at); the glossary entries Source address and Holdings; lit docs/specs/2026-09-21-corpus-design.md; the brief docs/notes/2026-10-14-reference-files-brief.md.
Bound: read code and docs, and search beliefs, lit and quarry tasks; no implementation and no write to any world.
Expected result: Whether alternative A (non-empirical dataset plus a governed source binding) is supported today or what it needs, versus B (source plus digest cited directly, manifest as lookup); a recommendation recorded on this task and in the brief.
Ideas it wakes: On completion, run `tasks note sci-b9f9d4 --no-reviewed "<finding>"`, before this result's branch merges.
