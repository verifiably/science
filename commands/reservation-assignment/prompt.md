Freeze which units of data have which role under a named rule version: `open`, `reserved`, `unresolved` or `withheld`, with the frozen input digests and the exact exposure events the derivation considered.
No selected project is required. Write the JSON payload first and pass its path: `schema_version` 1, a one-line `title`, and the `facet`; `docs/commands.md` has a complete example.
Omit `assigned_by`, which the session supplies, and omit an optional field instead of giving it null or an empty value.
Leave out `predecessor` for the first assignment of a `chain` and `scope`; otherwise name the current head, which `reservation-head` shows and which the write root itself must hold.
Any group changed, dropped or added needs `evidence`; a `reserved` group changed or dropped also needs `flagged`, the assessments already made against it (an empty list when there are none).
Record a new exposure event first with `exposure-event` and cite the address it returns: the two writes are separate, so a refused assignment leaves the event recorded and the old head current.
The roles are the program's decision under its own rule; this command records them and checks the chain.
