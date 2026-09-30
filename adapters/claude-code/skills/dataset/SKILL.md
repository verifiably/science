---
name: "dataset"
description: "Hold a local file in the store and mint the dataset record under its content address."
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

Run `dataset` when the user has a data file on this machine that an analysis
will observe, or the vocabulary list a contract binds. Give the file's path
and a title; add `locator` for an accession the record should cite and
`facets` for domain facets the contract declares. The output is the minted
record only; if it refuses, report the refusal and change nothing.
