---
name: "exposure-log"
description: "List recorded exposure events, narrowed by subject or proposition."
---

You are working over one world of governed records through the `science`
commands. The current project is chosen with `project-select`. A command
that enumerates the world reads through the selected project's query, and
sees the whole world when none is selected; a command given an identity
answers for that identity whatever is selected. A question or any
coordination record needs a selected project, except a project itself; a
fact does not. Corpus writes are kernel acts that return their own records;
session writes return the selection they recorded. Report refusals verbatim,
and never retry with altered inputs, repair, or write around one. Results are
budgeted: a truncated result ends with a cursor, and continuing with that
cursor is the only way to see the rest. A command's declared inputs are its
whole interface; there is nothing to reach around.

List the exposure events recorded in every configured live corpus, oldest observation first, then by address.
`subject` (a `dataset:` or `source:` address) and `proposition` (a `proposition:` address) narrow the list, and together they intersect; each matches the address as the event stores it.
A well-formed filter nothing matches is an empty list, not an error. Copies that differ between corpora refuse, naming their holders.
Use `record` with an event's address for its whole facet: the account, the bound digests and the evidence.
