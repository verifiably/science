---
id: sci-ad7335
title: "What a health contract needs from beliefs: the estimand shape and the disease-vocabulary admission route"
status: todo
priority: 3
size: s
complexity: mid
process: direct
created: 2026-10-29T16:27:34Z
updated: 2026-10-29T16:27:34Z
depends: []
parent: sci-c4d587
tags: [projects]
source: docs/notes/2026-10-29-health-contract-brief.md
agent: claude-code/claude-fable-5-1
origin: agent
---

Question: Can a corpus-local contract declare tissue levels and a TPM measure as its estimand (the shape option 3 of the milestone design §4.1 names), and what does binding a disease vocabulary (MONDO or EFO) cost in beliefs' biology pack, given that the admission ramp already observed a held mondo record?
Where to start: [ref:brief] for the question and its evidence; in beliefs, docs/designs/2026-09-08-biology-pack-design.md §9 (GO, HP, EFO and MONDO unmeasured; the pack binds one namespace), docs/designs/2026-08-09-admission-ramp-design.md §5.1 (the held mondo record), and docs/superpowers/specs/2026-09-05-mm30-reproduction-design.md §1c (how mm30's corpus-local sort vocabularies and contract are written and compiled by adopt); in science, docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md §6.3.
Bound: read the designs and the mm30 contract's compiled form and record what exists, what is missing and roughly how large each missing piece is (contract authoring, vocabulary binding, its measurement). No contract authoring, no vocabulary binding, no beliefs request; a beliefs task is proposed in the result, not filed, unless the user asks.
Expected result: an inventory on this task and in the brief's "Current behaviour and evidence" section: the estimand shape a contract can carry today, the binding route for a disease vocabulary and which project owns each piece, with a recommendation between the brief's alternatives 1 to 3.
Ideas it wakes: On completion, run `tasks note sci-036920 --no-reviewed "<finding>"` before this result's branch merges.

## References

- brief (input, required, kind=brief): docs/notes/2026-10-29-health-contract-brief.md — context and questions for this work

## Notes

- 2026-10-29T16:27:34Z (add): created
  provenance: {"harness_session":"claude-code:791cb76f-ef91-47dc-a6c1-9d9ddd6101ab","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
