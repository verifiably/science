---
name: "source-assertion"
description: "Record that a source asserts, denies or hypothesizes a proposition at a quoted span."
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

Record that a source asserts, denies or hypothesizes a proposition at an exact quoted span.
No selected project is required; both `source` and `proposition` must resolve in the session's live corpora.
Supply every text input (`quote`, `locator`, `media_type`, `source`, `proposition`, `extracted_by`, and optional `attributed_to`) already in Unicode NFC; non-NFC text refuses `invalid-input` without silent normalization, and `sha256` must be 64 lowercase hex digits of the exact representation bytes read.
Pass the reader or model-and-version who extracted the span in `extracted_by` (distinct from the source's authors and from optional inner `attributed_to`); `recorded_by` is stamped automatically from the writer session's actor.
When a refusal carries `data.existing`, the identical extraction on that same source is already recorded across configured live corpora and is safe to reuse as it stands.
Do not treat `data.anchor_conflict` or `data.occupied` as reusable duplicates: `data.anchor_conflict` means that assertion address is already anchored in a different source record, and `data.occupied` means a non-`source-assertion` record holds or redirects from that address.
