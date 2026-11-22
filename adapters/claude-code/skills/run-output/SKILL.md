---
name: "run-output"
description: "Read one declared output of a run from operations scratch after verifying its manifest digest."
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

Run `run-output` to read one declared output file from a run's result manifest:
name `run` (the run ref) and `output` (the logical output path from the run's
manifest). Bytes are read from local operations scratch and verified against the
manifest's SHA-256 digest before rendering. The reply prints the run ref, output
path, verified digest and byte length ahead of the UTF-8 content, paged within
the output budget; continue with the cursor if truncated. Missing or reclaimed
scratch copies, digest mismatches and non-UTF-8 outputs refuse.
