---
name: "reservation-head"
description: "Show a reservation chain's head, its changes and the events it did not consider."
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

Show the current assignment of one reservation chain: its rule and frozen input digests, the events it considered, each group's role and the changes from its predecessor.
Leave out `scope` for the program-level chain; a scoped chain is a different chain, named by its proposition.
The last section lists visible events the head did not consider. Being listed says nothing about relevance: an event can be older than the head or about other data, and deciding whether it changes a role is the program's rule to apply.
A chain with no record is an empty result. Two roots or two heads refuse as ambiguous: this command never picks one.
Use `record` with a historical assignment's address for its own facet and changes.
