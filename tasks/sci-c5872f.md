---
id: sci-c5872f
title: "A closure clause never selects its anchor: coarse views omit their dataset and the findings level omits its assessment"
status: todo
priority: 2
size: s
complexity: mid
process: planned
created: 2026-10-27T12:47:23Z
updated: 2026-10-27T12:47:23Z
depends: []
tags: [projects]
source: sci-0d00d2
agent: claude-code/claude-opus-5-5
origin: agent
---

beliefs' traversal is start-excluding, so the projects design §6.2 queries select what the GSE179929 closure reaches but not dataset:sha256:a6bf229e itself, and the findings-level query of §8.1 (closure from the assessment, outward) selects the assessment's run, proposition and dataset but not the assessment: a findings view without its finding. The design predicted the anchor selected (9/12/5 against 8/11/4 observed). Each query that wants its anchor must name it in an addresses clause, or the clause semantics change. Evidence: docs/records/2026-10-26-second-project-milestone.md §4 (R1 and R3 marks), §5 F8 (design-gap), §6 M5.

## Notes

- 2026-10-27T12:47:23Z (add): created
  provenance: {"harness_session":"claude-code:8b479072-91d3-4b9c-b77c-d178525b6574","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
