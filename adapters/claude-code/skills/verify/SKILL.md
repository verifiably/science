---
name: "verify"
description: "Replay an assessment's run, derive scope and verdict, and mint the verification."
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

Run `verify` after `assess`: name the assessment and the same code directory
and entrypoint the run used. The original run is replayed, the two are
compared under the spec's equivalence rule, and the verification is minted
with its scope and verdict. `clean-environment` with `passed` is what admits
the assessment to belief; ask `belief` to see whether it did.
