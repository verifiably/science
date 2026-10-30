---
id: sci-cc4fb9
title: "Design /science:discuss, research-topic and research-paper: three authored skills and the note, topic, source and source-assertion commands"
status: todo
priority: 1
size: m
complexity: high
process: planned
created: 2026-10-29T20:02:26Z
updated: 2026-10-30T15:43:49Z
depends: []
tags: [heritage, skills]
agent: claude-code/claude-opus-5-5
origin: mixed
---

First slice of the proto-science sweep (sci-4c9e67): port proto's discuss, research-topics and research-papers as authored skills under skills/ (singular names: discuss, research-topic, research-paper), invoked as /science:<name> through the generated plugin. Every write goes through a command; none exists yet for the kinds they need: note and topic (coordination kinds, corpus-write), source and source-assertion (kernel kinds, corpus-write). Agent-proposed rulings for the spec, each open to the user: a discussion's text is a coordination note, since the kernel's prose discussion kind has no command-reachable route; text written from model knowledge stays in a note and only a paper's own claims become source-assertions anchored in a source; order discuss, then research-topic, then research-paper. Retrieval (Crossref, Unpaywall, arXiv, Europe PMC) belongs in quarry; held bytes depend on sci-a17882, sci-76de75 and sci-f6c61b.

User's direction, 2026-10-29, in their words: 'there should be a single record for each article (same world across all projects..); having multiple ways of refering to the same thing seems likely to introduce confusion and complexity.' Agent's reading: research-paper writes the kernel source record, whose address the kernel derives from its identifier (doi, then pmid, isbn, accession), so every project minting the same DOI reaches the same record; lit's paper records converge on that identity rather than holding a second one (lit task filed beside this one).

## Notes

- 2026-10-29T20:02:26Z (add): created
  provenance: {"harness_session":"claude-code:f7cf60bb-2dad-4284-ab1a-1810d990d023","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"mixed"}
- 2026-10-29T20:02:54Z (main): lit side of the one-record-per-article direction filed as lit-0b5019.
- 2026-10-30T15:43:49Z (main): Europe PMC retrieval prerequisite quarry-404f63 is now done and locally integrated at quarry daace321b77e86b7fbd91be250010200d38023b2, with shared identifier registry prerequisite refs-1d0cb0 at refs19f886a. Research-paper design can consume quarry search/show/files: provider-qualified Europe PMC identity, canonical publication cross-references, core availability/licence fields, and metadata-gated hosted PMC XML locations. No article bytes, extraction or exposure authorization are supplied. Keep the user-directed single canonical source-record identity; the provider-qualified index id is not a second scientific article record. Read quarry README and completed task spec/ledger when designing this integration.
