# Conformance cut 4 — scope for the first persistence slice

**Date:** 2026-08-17
**Status:** Approved scope for drafting the cut-4 selection document. This spec
records the brainstormed boundary decisions; the cut document itself is the
deliverable, and its freeze discipline is stated below.
**Inputs:** `atoms` A8 certification (adoption ledger row 4, landed
2026-08-17); `atoms` Plan B order
(`2026-07-23-recoverable-fs-effect-engine-design.md` §14); cut 3's deferral
groups (`2026-08-11-conformance-cut-3.md` §4.2, §5); substrate consolidation §7.

## 1. What cut 4 is

The first persistence slice: the certified `atoms` engine adopted at Science's
composition root, compiling generic corpus writes into `TransactionSpec`
against the certified Linux volume tuple, every other tuple failing closed.
Three scope decisions are settled:

1. **Operation surface: the corpus-write adapter only** (Plan B item 1).
   The family dialects — supersede, archive, import/cohort — are Plan B
   item 2 and wait for their own adapters in later cuts. Arms that require
   an edit (S2's mint-and-supersede, S5's snapshot walk, M5's edit half)
   stay partial, recorded under the rule that any unrun arm leaves a row
   partial.
2. **Tamper log: out, with the anchor seat reserved.** No L row is
   selected; the log ships in the next persistence cut. The adapter's
   `TransactionSpec` compilation names the position where the log append
   will join the same atomic commit, so the log later extends the spec
   rather than reworking the adapter. Records written before the log cut
   are pre-chain; the cut states this as a limitation.
3. **Freeze timing: draft now, freeze when the composition-root adapter
   design banks.** The adapter design waits on the `nodes`
   write-plan/executor seam freeze. Until it banks, the cut's status header
   reads draft and its freeze block is written but not in force.

## 2. The boundary

In scope:

- durable minting of new corpus records through the write API's add path;
- refusal of every volume tuple outside the certified binding;
- compilation-correctness obligations at the Science boundary — `atoms`'
  physical certification is relied on, never re-run;
- stored-corpus traversal over the durable store.

Out of scope, each named in the cut's boundary section: the family
dialects; the managed holdings root; the world index; retraction records;
the rules store; the registry compile; the tamper log (reserved seat and
pre-chain limitation per §1 item 2).

## 3. Candidate groups for the selection reading

The reading sweeps every row not fully exercised (117), row by row. Arms
are expected mainly in:

- **substrate write & traversal** — S1, S1a, S3, S4, S7, S8; S2 and S5
  contribute only their non-edit halves;
- **M5** — the founding mint walk's store half, not the edit;
- **G3** — the corpus-move negative;
- **G7** (the mint path) and possibly **G5** (the authoring surface);
- **D7** — the write-boundary half, the index half still deferred;
- **T1** — the import arm, as a store operation;
- **R19, R22** — their store-gated arms;
- any **W** row whose check fails at the write boundary alone, without the
  index.

No group pre-commits a selection; the draft's per-row cells make each
call.

## 4. Document shape

A new `docs/designs/<date>-conformance-cut-4.md`, dated the day the draft
lands, following cut 3's
structure: what the cut is drawn against; the boundary; selected rows with
per-arm selected/deferred cells; the deferred groups re-read against this
slice's boundary; accounting that sums to 151. Differences from cut 3:

- status header: **Draft — selection pending; freezes when the
  composition-root adapter design banks**;
- the freeze block is present but explicitly not yet in force;
- a second-reader section is reserved, to be discharged at freeze.

The acceptance suite belongs to the composition-root adapter design
(Plan B item 1), not to this cut; the cut selects the guarantee arms that
suite must discharge.

## 5. Verification

- The corpus guard tests stay green — the new document references
  composition-root adoption as the gate, which the pending-language guard
  permits; it must not pair a Plan A stage token with gating vocabulary
  outside preserved blockquotes.
- The accounting identity (selected in full + in part + fully exercised
  prior + part-exercised prior + fully deferred = 151) is checked by hand
  in the draft, as in prior cuts.
- Work happens on `docs/cut-4-selection`; the draft lands as a docs-only
  commit.

## 6. Dependencies and non-goals

The draft depends on nothing outside this repository. The **freeze**
depends on the `nodes` write-plan/executor seam freeze and the
composition-root adapter design banking, both owned by other fronts. This
spec does not design the adapter, the seam, the log anchoring, or any
family adapter, and it does not amend any prior cut.
