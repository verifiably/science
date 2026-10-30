Reviewer: claude-code/claude-opus-5-5
Source: full review relayed by the user in this session
Artifact: docs/specs/2026-10-30-readable-stores-design.md
Revision: 6d83468c5aa242ffd2ab8a10a3476dcfefa8c4ff

Full returned review:

I checked the revision at 6d83468 against what I reviewed at 915409e, and all six of my findings are properly addressed. I have nothing that blocks approval. Whether to approve the design is still your decision; once you do, the controller session drafts the implementation plan.

- Read admission (the Important finding): fixed. The spec now checks each store with read_lifecycle_state and accepts only the writable and read-only-serviceable states. The three states it refuses are the remaining three of atoms' five lifecycle states (I checked the names in coordinator/lifecycle.py). Inspection errors fail closed. The tests now cover all five states, an interrupted restore, and a check that nothing on disk changes. It also says plainly that run's staging records a digest but never compares it to the declaration, and leaves that to separate work, which is what I suggested.
- Snapshot: keeps the current refusal, says why, and now has its own tests through evaluate and gather_inputs.
- Ordering: states the sort order, that the write store gets no preference, and that there is no fallback to another copy after an I/O error or digest mismatch.
- Blocked datasets: states that one blocked location blocks the whole dataset, both in the spec and in runbook step 4. It also no longer assumes mm-62e2da's current state.
- Paths: the example is now store-working, a real sibling of store, with the metadata rule written out and a concrete check that neither new tree overlaps either old one.
- Config writers: names the three test-only writers.

I'd add one item for the plan, not the spec. The new admission check also applies to store_root, so an existing single-store world whose store isn't in an admitted state would start refusing reads. Stores created before the lifecycle model existed are the likely case; beliefs has a migration for those. The plan should check the state of every store currently configured (the mm30 world, the GSE24080 spike config, and any others) before this lands. I didn't check how those older stores read today.

I wrote no review note. If the controller records one, it is: review: spec round 4 — verdict: accept; findings: none; reviewer: claude-code/claude-opus-5-5. Round 4 because the fresh review already took round 3. Nothing was pushed and no processes are left.
