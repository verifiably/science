# Commons 1a deferred evidence limits — brief

**Date:** 2026-10-24 · **Source:** sci-13050a · **Goal:** sci-6b6014

## 1. Problem

Resolve the three recorded limits left by the completed two-installation
collaboration: demonstrate acceptance changing a belief verdict (sci-b979ce),
authenticate a carried record's content against its origin (sci-4a3543), and
eventually retain URL observations without disguising a digest mismatch as
success (sci-9afbc8). These are maintenance follow-ups to the existing commons
effort. The first actionable milestone is the verdict-flip test.

## 2. Current behaviour and evidence

Checked science at `846772e`; the original milestone merged at `c8a2cd7`.
`python/tests/test_commons_1a.py` checks acceptance inputs and context, but both
answers are `NoBelief(no-eligible-assessment)`. In
`python/tests/helpers/commons.py`, `_add_a_evidence` uses `mint_fixture_run`
under the minimal policy; B's verification is therefore same-environment.
`python/tests/test_belief_path.py` already demonstrates the contrasting confined
path with a passed clean-environment verification and an admitted belief.

`python/src/science/acceptance.py` gives `Carrier` a selection and attributions
but no per-address content identity. `_origin_holds` authenticates the origin's
pin and address membership without comparing the carried content. The attached
`tasks/files/sci-13050a/sdd-ledger-commons-1a.md`, Task 10 I2b, records the
remaining exposure as corpus-local reads with origin and carrier configured;
1a's world reads refuse overlap. The ledger requires this gap to close with 1b.

`python/src/science/commands/fetch.py` retrieves and checks bytes before its
one store-write act. `render.audit_write_report` rejects `Finding` blocks;
`dispatch._invoke_write` persists minted identity pairs and rebuilds the reply
from those identities. Merely relaxing the renderer cannot preserve a finding
on replay. Commons design section 5's Deviation 4 explicitly defers URL
observations. No attached draft or existing local follow-up brief was found.

## 3. Constraints

Keep the portable commons fixture and its input/context assertions. The added
case must actually execute A's original run under confinement, then publish,
adopt, fetch and verify through the existing routes. Never relabel a minimal
run or mock admission to manufacture a clean-environment result. Follow the
existing explicit prerequisite skip on hosts that cannot confine, and record
an executed confined case before claiming the new acceptance check passed.

For carried records, preserve the five acceptance branches and the origin-pin
checks; address or uid equality alone is insufficient. Reuse the identity
decision in beliefs-918fd2, which already covers equal/differing content and
holder provenance for beliefs-81367e. Science milestone sci-9104fb already
requires sci-4a3543 to land with overlap. No new research is needed.

For URL observations, a mismatch must remain visible and no mismatching bytes
may enter the store. Ledger-backed outcome semantics, first response, retries
and continuation need a reviewed contract before changing the current flow.

## 4. Alternatives

- **Advance each follow-up at its existing boundary — lean:** scope the confined
  test now, brief the carried-content work against the existing overlap design,
  and shelve URL observations until the report capability exists.
- **Rewrite the common portable fixture.** Rejected as the default: many tests
  depend on it and hosts without confinement would lose their existing coverage.
- **Create a new report framework or a second identity investigation now.**
  Rejected: the URL task is conditional on that capability, while the identity
  question already has an open design owner.

## 5. Unanswered questions

- Which content identity and holder-provenance contract does acceptance consume?
  **beliefs-918fd2** settles it; then sci-4a3543 can be scoped before/with 1b.
- When will a write outcome support replayable findings beside minted records?
  **A future command-framework design** must establish it. There is no current
  implementation task for that prerequisite, so sci-9afbc8 is shelved with this
  explicit wake condition rather than given an invented dependency.
- Does the confined two-installation fixture reach the expected verdict?
  **sci-b979ce** checks that through real run/replay and asserts verification
  scope, admission and the returned belief, with independent expected answers.

## 6. Proposed decomposition

- **sci-6b6014**, sourced by this brief, groups the three previously
  unparented follow-ups; it does not expand milestone 1b's scope.
- **sci-b979ce — scoped:** priority 2, small, mid complexity, direct. Add one
  confined two-installation case; retain the portable case. Run
  `just test-one tests/test_commons_1a.py tests/test_belief_path.py`, then
  `just test-fast`; explicitly report whether confinement ran or skipped.
- **sci-4a3543 — briefed:** record its wait on **beliefs-918fd2**. That design's
  completion must add a finding note with `--no-reviewed` to sci-4a3543 before
  merging, in addition to its existing handoff to beliefs-81367e. Preserve its
  integration requirement in **sci-9104fb**; avoid a dependency on completing 1b,
  which would postpone a fix required by that same milestone.
- **sci-9afbc8 — shelved:** wake when an approved, implemented ledger-backed
  write outcome preserves digest-mismatch findings beside minted observations
  on the first response, retry and continuation. No report extension is filed
  by this pass.
