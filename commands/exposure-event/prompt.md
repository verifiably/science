Record what someone saw or already knew, as soon as it happens: one look at data (`channel` `read`, naming its `dataset:` or `source:` subjects) or one piece of prior knowledge (`channel` `knowledge`, with no subjects).
No selected project is required. Write the JSON payload first and pass its path: `schema_version` 1, a one-line `title`, and the `facet`; `docs/commands.md` has a complete example.
Omit `recorded_by`, which the session supplies, and omit an optional field instead of giving it null or an empty value. `observer`, `observed_at` and the external `evidence` tokens are yours to state.
Every subject, proposition and `run:`, `act-report:` or `holdings-observation:` evidence token must resolve in the session's live corpora, and every term unit's sort must be one the configuration declares.
An event changes no assignment: the current `reservation-head` stays current and lists the new event as not considered.
When a refusal carries `data.existing`, the identical event is already recorded and is safe to cite; `data.occupied` means another kind of record holds that address.
