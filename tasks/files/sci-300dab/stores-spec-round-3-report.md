Reviewer: codex/gpt-6.1-sol
Agent: /root/stores_spec_rereview
Artifact: docs/specs/2026-10-30-readable-stores-design.md
Revision: 6d83468c5aa242ffd2ab8a10a3476dcfefa8c4ff

Full returned review:

Verdict: **accept**. Nothing important left for the builder check. All six prior findings are addressed; new findings: **Critical 0, Important 0, Minor 0**. sci-300dab remains pending human design approval before implementation planning.

Reviewed the frozen spec at science commit `6d83468c5aa242ffd2ab8a10a3476dcfefa8c4ff`, `docs/specs/2026-10-30-readable-stores-design.md`, against original `915409e42b540287e3fce9f062a097cca1bda100` and its full round-2 review. Checked the connected science code, beliefs at `405f24995bf0934fe4fc3cdd9fdb98be4dd2516a`, and atoms at `1e83a241124f743574912e23a4be9946eb484d0c`.

1. **Important 1 — addressed.** Spec lines 91–118 require lifecycle validation for every mapped store, including `store_root`, admitting only `WRITABLE` and `READ_ONLY_SERVICEABLE`. Other states refuse; inspection errors fail closed. Validation precedes session-ledger creation and occurs lazily for read contexts. Acceptance criteria cover all five states, interrupted restore, inspection errors, and unchanged payload/metadata/sidecars. The selected API exists: beliefs delegates to atoms’ existing-only lifecycle query, whose database opening explicitly prevents sidecar creation. The spec correctly makes no payload-integrity guarantee from this check.

2. **Minor 2 — addressed.** Lines 140–148 explicitly preserve snapshot refusal when found observations have no configured store. Missing declarations, no found observations, and selected vocabulary digest mismatches remain unreadable bindings. Snapshot, `evaluate`, and `gather_inputs` coverage is required.

3. **Minor 3 — addressed.** Lines 128–154 state lexicographic `(digest, location)` order, no preference for the write store, and no fallback after selected-copy I/O failure or digest mismatch. This matches the reducer and existing vocabulary behavior.

4. **Minor 4 — addressed.** Lines 155–157 and runbook step 4 explicitly state that a matching blocked location blocks the entire dataset, even with another healthy copy. The spec requires inspecting the actual live reduction before claiming mm-62e2da unblocked and preserves separate authorization for settlement work.

5. **Minor 5 — addressed.** The example now uses sibling `store-working`. Runbook step 1 names the `<root>.metadata` rule and requires resolving and checking both new trees against both old trees for equality or nesting.

6. **Minor 6 — addressed.** Lines 244–251 identify the three test-only configuration writers and explicitly say no production serializer exists or is needed.

No revision introduces a material unanswered question. Concrete exception mapping and fixture placement can be settled during implementation planning within the stated constraints.

Reviewer identity: **codex/gpt-6.1-sol**, verified by a fresh successful `relay model` invocation. Suggested controller note: `review: spec round 3 — verdict: accept; findings: none; reviewer: codex/gpt-6.1-sol`.

Not checked: runtime tests or the live world; no files, task records, or live state changed.
Remaining risk: admitted payloads can still be altered; the spec explicitly leaves run/verify digest comparison outside this task.
