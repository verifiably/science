---
name: "spec"
description: "Freeze an analysis spec against the kernel's reference rules and mint its record."
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

Run `spec` to freeze an analysis for a proposition and its one observes dataset.
Supply a UTF-8 native estimand JSON document, explicit standing and evidence mode,
and rule-identity=procedure-id bindings for held procedures. The interpretation
rule must have a binding. Supply a held model or assumptions registers when the
scientific route requires them; absent registers means an empty list.

The document declares form, functional, named bindings, typed outputs, reference,
control, uncertainty and assumptions with schema_version 1. Decimal positions
use JSON numbers; restriction bounds use their native strings. The target claim
and held records determine frozen identities and dependencies. Missing scientific
facts or prerequisites refuse; never infer them or create records automatically.

Give method, assumptions and falsification in the user's words, and the shipped
interpretation/equivalence rule identities. Parameters are name=value decimals.
Applicability accepts dimension=quantifier:term only for declared applicability
term restrictions. A frozen spec can only be superseded.
