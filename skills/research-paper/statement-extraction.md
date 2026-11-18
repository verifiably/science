# Extract source statements

- Keep the verbatim span separate from the reader's paraphrase and record who
  extracted it (person, or model and version).
- Preserve uncertainty; do not force ambiguous text into a stance. Text that
  cannot be copied exactly belongs in the reader's summary, not a statement.
- A claim is not sourced merely because a paper is cited nearby. Check what the
  quoted span actually says and where it occurs.
- Extraction is not belief. A statement paired with an existing proposition
  becomes an attributed `source-assertion` record inert in `belief`, while a
  statement with no proposition stays in the reading note; both remain one
  reader's unadjudicated extraction, not an independent check of that same
  reader's summary.
- Where agreement between extractors is measured, report kappa or alpha with raw
  agreement; this workflow measures no such agreement.
