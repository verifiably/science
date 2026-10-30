# Plan review round 4

Reviewer: claude-code/claude-opus-5-5 (supplied in relayed review).
Revision: science 0ddb1ad1df3c1d4c1a4ff4b43d08065eeeb0671a, docs/plans/2026-10-30-readable-stores.md.
Verdict: accept; findings: none. Full review follows.

I accept revision 0ddb1ad with no findings. Implementation can start once you approve the plan; inline execution is already agreed, and the controller starts the child tasks under the halt override the plan documents.

What I checked
- Refusal handling (my Important finding): fixed. Dispatcher._kernel_refusal moves to science.refusal.kernel_refusal, and its output stays the same unless a root is passed. The dispatcher's catch list is unchanged, and new tests pin the existing refusal shapes.
- Import cost of that move: refusal.py now needs beliefs imports. That adds nothing at startup, because cli.py already imports dispatch, which imports beliefs.session at top level. beliefs doesn't import science, so the move creates no import cycle.
- Non-public error names: the plan now calls them non-public, ties the stopgap import to a removal comment, and tracks the proper export in beliefs-1dfd8c. That task exists and is open.
- Test files: every file the RED step names exists, including test_dispatch_refusals.py.
- Halt override: each child task's start is spelled out with a scoped reason, and the slow just test-fast is flagged.
- Admission tests: the restore-failure injection is gone. The unserviceable replica now only checks for the state, a refusal, and unchanged files.
- Blocked-holding test: it now patches only science.holdings.reduced_heads and runs the real dataset_observations. The blocked row carries the location, heads and reasons keys the adapter reads, so it reaches held_path the way the spec describes.
- Store inventory: one pass, capped at 20 minutes, over named places, with each gap needing a disposition before integration.

The State line now records the design approval accurately: the controller approved it, under a decision the plan says you left to it.

Review note for the controller to record (I wrote no note): review: plan round 4 — verdict: accept; findings: none; reviewer: claude-code/claude-opus-5-5. That follows my round 2 and the controller's round-3 self-review.
