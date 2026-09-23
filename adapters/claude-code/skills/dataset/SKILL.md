---
name: "dataset"
description: "Hold a local file in the store and mint the dataset record under its content address."
---

You are working over one world of governed records through the `science`
commands. The world is read through the selected project's query when one is
selected and whole when none is; no project can be selected yet, so every
command reads the whole world. A question or task needs a selected project;
a fact does not. Every write is a kernel act that returns its own record or a
refusal — report refusals verbatim, and never retry with altered inputs,
repair, or write around one. Results are budgeted: a truncated result ends
with a cursor, and continuing with that cursor is the only way to see the
rest. A command's declared inputs are its whole interface; there is nothing
to reach around.

Run `dataset` when the user has a data file on this machine that an analysis
will observe, or the vocabulary list a contract binds. Give the file's path
and a title; add `locator` for an accession the record should cite and
`facets` for domain facets the contract declares. The output is the minted
record only; if it refuses, report the refusal and change nothing.
