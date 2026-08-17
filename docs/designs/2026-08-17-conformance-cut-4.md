# Conformance cut 4 — the first persistence slice

**Status:** Draft — selection pending; freezes when the composition-root adapter design banks.

**Sources:** the cut-4 scope spec
(`docs/superpowers/specs/2026-08-17-conformance-cut-4-scope-design.md`);
`2026-08-11-conformance-cut-3.md`; `2026-08-03-redesign-adoption-ledger.md`;
and, by description, the `atoms` authority design §14 and Plan B §12.2.

## 1. What this cut is drawn against

Cut 4 is drawn against the certified `atoms` engine adopted at Science's
composition root: the corpus-write adapter compiles a generic corpus write
into a `TransactionSpec` and submits it against the certified Linux volume
tuple, per the `atoms` authority design §14. Every other volume tuple fails
closed — there is no fallback path that writes durably outside the certified
binding.

The slice is **add-only**. Edits, moves, and deletions are not built here;
they are the family adapters' surface — supersede, archive, import/cohort —
which Plan B item 2 assigns to their own adapters in later cuts. What this
cut selects is bounded by the corpus-write adapter alone, Plan B item 1.

The draft freezes when the composition-root adapter design banks, and that
design itself waits on the `nodes` write-plan/executor seam freeze. Until it
banks, this document's status header reads draft, and its freeze block, once
written, is present but not in force.

## 2. The boundary

In scope:

- durable minting of new corpus records through the write API's add path;
- refusal of every volume tuple outside the certified binding;
- compilation-correctness obligations at the Science boundary — `atoms`'
  physical certification is relied on, never re-run;
- stored-corpus traversal over the durable store.

Out of scope, each named with where it waits:

- **the family dialects** (supersede, archive, import/cohort) — wait for
  their own adapters, Plan B item 2;
- **the managed holdings root** — the verified-holdings store's own
  management surface is not the corpus-write adapter's target, and waits on
  an adapter this slice does not build;
- **the world index** — waits on composition-root adoption together with the
  `nodes` contract deltas, as cut 3 restated;
- **retraction records** — subtracting standing without deleting a record is
  an edit-shaped write, outside this slice's add-only surface;
- **the rules store and resolver** — remain unbuilt, exactly as cut 2's P1
  deferral recorded;
- **the registry compile** — remains unbuilt, so the kind-existence check it
  would ground stays unbuilt with it;
- **the L rows and anchor carriage** — wait on the next persistence cut, as
  the closing paragraph below states.

Registration is an engine facility. The `atoms` executor appends a
registration entry inside every transaction this slice commits, and
`TransactionSpec` already carries `consumer_tag`, `intent_digest`, and
`fulfills` — the corpus-write adapter reserves nothing and adds no effect of
its own. No L row is selected here: anchor carriage and Science-side
verification — cut 3's intent/reduction semantics meeting the durable chain
— are the next persistence cut's work, and it selects the L rows then. Until
anchor acts exist, every transaction this cut commits is **chained but
unanchored**, and the unbounded unanchored tail is this cut's stated
limitation.

## 3. Step 1 — what the slice crosses

## 4. Step 2 — the selection, arm by arm

### 4.1 Selected in full

### 4.2 Selected in part

### 4.3 Standing from prior cuts

## 5. Step 3 — fully deferred rows, grouped by unblocking subsystem

## 6. Accounting, freeze, and amendment discipline

## 7. The second reader — reserved
