---
name: discuss
description: Use when critically discussing one question, hypothesis, topic, proposition, source or note in a science project, or when asked for independent (double-blind) reasoning about one.
---

# Discuss

## Boundaries and preconditions

Write records only through science commands named here. Write no repository file,
make no commit, and edit no existing record. First check that science commands are
reachable and a project is selected. If either is missing, stop with a plain
message; tell the person to run `project-select` when needed, and never select a
project yourself. If a literature lookup needs quarry, first check that `quarry`
runs; stop if unavailable, without locating or installing it.

Before reading text reporting results, follow the workspace's exposure policy in
its agent guide or protocol. If a paper's status is unresolved, stop at its
bibliographic metadata and say so; an accessible abstract is not permission.

## Read and choose a mode

Read an addressed focus with `record` and its surroundings with `project-show`.
Narrow a focus in words with the person to one claim or question before writing.
Read [discussion-structure.md](discussion-structure.md) for the sections and
failure checks.

- Standard: one critical analysis, deciding evidence, prioritised follow-ups,
  then synthesis.
- Q&A: when the person brings several specific questions, one focused answer and
  its support per question, followed by follow-ups and synthesis.
- Double-blind: only when the person asks for independent reasoning. Agree the
  focus; write and mint the agent's analysis with `note` before asking for or
  reading the person's draft. Then mint their supplied draft verbatim as a
  second note, identifying whose draft it is. Finally mint a synthesis naming
  both notes at their pinned revisions, with agreements, disagreements and points
  only one side raised. Use `record` on each minted id to obtain its pinned address.

If the person's draft is already in the conversation, say double-blind is no
longer possible and offer Standard. In the synthesis state the limit: record
order shows the agent's analysis was committed first; it cannot show what the
agent had seen before the session.

## Write the discussion

Use `note`, named `Discussion: <focus>`. For double-blind use
`Discussion (agent): <focus>`, `Discussion (draft): <focus>` and
`Discussion (synthesis): <focus>`. Every note body starts with the applicable
Focus line below. In the draft note, identify whose draft it is after that line, then include the complete
supplied draft verbatim in a labelled block, with framing outside the block:

- `Focus: coord:<project>/<local>@<revision>` — the pinned address `record` printed.
- `Focus: <address> uid=<uid>` — a world record has no revision syntax; a source's
  uid persists across identifier corrections.
- `Focus: <the claim or question as narrowed>`.

Put a world focus and any source or proposition relied on in `about`.
Coordination focuses belong only in the body: `about` accepts world addresses.
Use unpinned addresses in commands and pinned coordination addresses in text.

## Attribution and wording

Label every statement as a named source's statement (address and reading depth),
a result already in the world (address), or the writer's own reasoning or
recollection. Model memory is orientation only, never a paper's evidence. Match
hedging to evidence: supports, suggests, is consistent with, one possibility is.
Store no strength or confidence grade.

Before writing about a published work, confirm its identity by the first route
available: an existing source found by `record`; quarry's index record; a DOI
registry's own metadata fetched by the harness at `doi.org`, with a matching
title; or identifiers the person supplies and confirms, explicitly labelled not
cross-checked. quarry has no DOI lookup: search each index using its native DOI
query (`--native`), then `show` the returned provider id. Use every confirmed
identifier together in world lookups. Compare titles after normalising case,
whitespace, markup and closing punctuation. A single identifier cannot rule out
an existing work recorded under a different identifier.

## Follow-ups and closing

List proposed questions and tasks in the note. Mint a `question` or `task` only
for those the person confirms. End with the addresses minted and anything that
could not be done.
