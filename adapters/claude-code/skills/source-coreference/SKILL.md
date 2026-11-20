---
name: "source-coreference"
description: "Attest whether two source records identify the same citable version"
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

Attest that two existing source records describe the same citable version, or dispute that identification.
Use `record` to check each current address, then give both addresses, `stance` (`same` or `distinct`), and nonblank Unicode NFC `grounds` explaining the evidence.
Keep preprints, revisions and final articles distinct when they are separately citable.
The statement is signed by the session actor. Each source keeps its own address, identity and citations.
