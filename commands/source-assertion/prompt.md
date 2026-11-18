Record that a source asserts, denies or hypothesizes a proposition at an exact quoted span.
No selected project is required; both `source` and `proposition` must resolve in the session's live corpora.
Supply every text input (`quote`, `locator`, `media_type`, `source`, `proposition`, `extracted_by`, and optional `attributed_to`) already in Unicode NFC; non-NFC text refuses `invalid-input` without silent normalization, and `sha256` must be 64 lowercase hex digits of the exact representation bytes read.
Pass the reader or model-and-version who extracted the span in `extracted_by` (distinct from the source's authors and from optional inner `attributed_to`); `recorded_by` is stamped automatically from the writer session's actor.
When a refusal carries `data.existing`, the identical extraction on that same source is already recorded across configured live corpora and is safe to reuse as it stands.
Do not treat `data.anchor_conflict` or `data.occupied` as reusable duplicates: `data.anchor_conflict` means that assertion address is already anchored in a different source record, and `data.occupied` means a non-`source-assertion` record holds or redirects from that address.
