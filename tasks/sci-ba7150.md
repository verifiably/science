---
id: sci-ba7150
title: "bio: a CLI and skills layer over common bioinformatics tools and resources"
status: doing
priority: 2
process: planned
owner: main
created: 2026-10-10T16:34:30Z
updated: 2026-10-10T18:03:58Z
started: 2026-10-10T17:12:51Z
depends: []
tags: []
agent: claude-code/claude-opus-5-5
---

Agents currently work out each bio resource themselves (GEO E-utilities, ENA portal, BioStudies, EGA, dbGaP, GDC, cBioPortal, Zenodo/figshare, PubMed), which produces inconsistent clients and reinvented workarounds. A new project would build a `bio` CLI plus skills: one simpler, more robust and consistent interface agents call instead of hand-rolling requests. Evidence from the myeloma dataset survey (mm-159cb7, 2026-10-10): ENA wildcard queries containing a hyphen, period or space silently return 0, so 22 of 38 cell-line terms never ran; BioStudies phrase queries expand via ontology with no off switch, and its search snippets omit organism; figshare returns publisher supplements as separate 'dataset' items; Zenodo refuses page sizes above 25 when unauthenticated; GEO needed a restructured client (esummary cross-refs, SuperSeries-only brief text) to drop a 1.5–6 h harvest to ~10 min; ENA returned HTTP 500 even on its count endpoint during a re-harvest. Scope questions: which resources first, what it owns (query grammar, pagination and truncation guards, rate limits and retries, canonical accession forms, recorded-response test fixtures), and how it relates to the existing projects' tooling.

## Notes

- 2026-10-10T17:12:51Z (main): Scoped with the user 2026-10-10: generalize first — design a domain-layer contract (bio first; physics/chem/astro later) so users and agents can switch layers and expect the same layout, command shapes and parameter names. Planned: new interface others depend on.
- 2026-10-10T17:12:51Z (main): started
  provenance: {"harness_session":"claude-code:812ecacd-3a65-4c38-8af4-57938f12afc5","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-10T17:12:51Z (main): halt override: started past sci-5937be by 812ecacd-3a65-4c38-8af4-57938f12afc5: design-only work on an unrelated idea; the test-latency halt concerns test-fast runtime, which a spec does not touch
- 2026-10-10T17:13:21Z (main): parked (waiting on user, decision): User answers what a domain layer contains (recommended: sources + identifier schemes + skills + the science domains rule set, over a shared core); then the agent continues brainstorming (approaches, design sections), creates the worktree and drafts the spec
  provenance: {"harness_session":"claude-code:812ecacd-3a65-4c38-8af4-57938f12afc5","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-10T17:28:26Z (main): resumed
  provenance: {"harness_session":"claude-code:812ecacd-3a65-4c38-8af4-57938f12afc5","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-10T17:28:26Z (main): Decision (user): a layer = data access + domain knowledge (sources, identifier schemes, skills, the science domains rule set). User adds: a core/shared layer of the same shape alongside the domain layers, and explicit types within the categories (identifier authority vs controlled vocabulary vs ontology vs data model; database vs repository vs API vs CLI).
- 2026-10-10T17:28:49Z (main): Proposed (default unless user objects): two axes — roles (identifier scheme, controlled vocabulary, ontology, data model; repository, knowledgebase, literature index; a resource may hold several) and access routes (REST, query endpoint, bulk download, local CLI); roles fix the verb set; reuse FAIRsharing terms and Bioregistry prefixes.
- 2026-10-10T17:28:49Z (main): parked (waiting on user, decision): User answers lens vs namespace for layers (recommended: lens over one CLI with global CURIE ids); then the agent continues brainstorming toward packaging, the worktree and the spec
  provenance: {"harness_session":"claude-code:812ecacd-3a65-4c38-8af4-57938f12afc5","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-10T17:36:54Z (main): resumed
  provenance: {"harness_session":"claude-code:812ecacd-3a65-4c38-8af4-57938f12afc5","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-10T17:36:54Z (main): Decision (user): layer is a lens over one CLI; ids are global CURIEs; the layer selects catalog, default search scope and skills, set per project or per command.
- 2026-10-10T17:37:16Z (main): Defaults stated (pending user override): one new repo (runtime + core + domain packs); layer names = science domain names via --domain; pack links the beliefs contract by name; plain automation CLI outside beliefs, fetch writes files + provenance manifest, science dataset mints; first scope core+biology over the roster's GEO/ENA/BioStudies/Zenodo/figshare/PubMed; recorded fixtures, no cache.
- 2026-10-10T17:37:16Z (main): parked (waiting on user, decision): User picks the project name (recommended: quarry); then the agent registers/creates the repo decision in the spec, creates the worktree and drafts the spec
  provenance: {"harness_session":"claude-code:812ecacd-3a65-4c38-8af4-57938f12afc5","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-10T18:03:57Z (main): resumed
  provenance: {"harness_session":"claude-code:812ecacd-3a65-4c38-8af4-57938f12afc5","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-10T18:03:57Z (main): Decision (user): the project is named quarry.
