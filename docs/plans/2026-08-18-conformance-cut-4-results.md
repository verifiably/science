# Conformance cut 4 — discharge results

**Date:** 2026-08-18
**Subject:** the composition-root adapter implementation
(`docs/designs/2026-08-18-composition-root-adapter-design.md`), measured against
conformance cut 4's frozen selection
(`docs/designs/2026-08-17-conformance-cut-4.md`).

**The selection is not edited here.** Cut 4 froze on 2026-08-18 and results are
recorded separately, which is what this document is. Nothing below adds, drops,
or re-reads an arm; where an arm ran differently from the reading a row's text
suggests, that is written down as a deviation rather than repaired by re-reading
the row.

## 1. What ran, and where

| suite | command | claim |
|---|---|---|
| durable acceptance arms | `python -m tools.cut4_acceptance` | cut-4 discharge |
| portable unit tests | `pytest` | the code behaves; **no** cut-4 discharge |

The acceptance command **errors off the certified tuple and never skips**: it
registers and drops a throwaway root before collecting anything, and a refusal
ends the run with the engine's own words and its own exit code (`2`), distinct
from a failing arm. The portable suite excludes `tests/acceptance` by
configuration rather than by a skip inside it, so an ordinary run cannot report
a durable arm as green without having run it.

**The certified tuple was exercised, not simulated.** The host's ext4 volume
matched the `atoms` allowlist entry — `linux`/`linux-4`, kernel `7.1.8-arch1-3`,
`async`/`barrier=1`/`commit=5`/`data=ordered`, `flush-honoring-disk.v1` — so
every durable arm ran against the real engine on a real volume. The
uncertified-tuple negative ran on `/dev/shm` and observed the engine's
fail-closed refusal surfaced through the executor's §4 mapping.

## 2. The selected rows

**Selected in full.**

- **S7** — both boundaries. The add path refuses an inadmissible `assesses` edge
  before the record lands; the profile-level corpus check reports a raw-written
  violation as `eligibility-unmet` under Science's own code namespace, in
  `nodes`' finding envelope, ordered by `(ref, code, detail)`. The cross-node
  predicate is one implementation serving both, spanning assessment → run →
  `observes` → dataset → `empirical-observation` facet.
- **S8** — the static claim over `src/science`, checked by AST over the package
  as **imported** rather than as checked out, so a sabotaged copy is what a
  sabotaged run inspects. The negative ran as its own construction: a raw
  filesystem write lands a node the static check cannot see, is read without
  refusal, and is reported by nothing when self-consistent — while a raw write
  that moved the fields and not the stamp is refused (`semantic-hash-stale`).
  The `atoms`-import confinement is asserted beside S8 as architecture, not as
  an S8 arm.
- **W3** — a `source` with no accepted external identifier and a `dataset` with
  no content identity are both refused before landing; the accepted set is
  closed, with no title-and-year fallback to reach; supplying the basis
  afterwards is a second, separate mint.

**Selected in part.** S1, S1a, S5, R19(a)/(d)/(e), R22, G9, R23 and N2 each ran
their selected arms over records **minted through the add path into one durable
corpus root and walked back out after reload**. The lineage fixture's
unresolvable cases were minted, never produced by deleting anything; R22's
forgery and R23's basis/composition disagreement were constructed with the
raw-write fixture act.

**N2** audits cut 4's own arms as data — 32 arms, each with its row, its
assertion, its source mutation and its exact named checks — for `vacuous`,
`stale`, `mixed` and `uncollected`, refusing a check coarser than one test
function, and with the unsabotaged baseline verdict (`resolved`) taken over
every declared check before any result counts. The audit runs under the
acceptance command, because most of the checks it names are durable ones.

Six arms were rewritten during the audit rather than accepted: four were
`vacuous` (a sabotage whose defect the named check could not see), one was
`mixed`, and one sabotage was `stale` against the code it was written for. Two
acceptance checks were strengthened in the same pass — a producer set that could
not distinguish `produces` from any other inbound edge, and a reached set
compared as a set where the walk promises an order.

## 3. Deviations from the banked design

Both are engine constraints the design does not survive contact with, and
neither is worked around adapter-side: they are recorded here and marked in
place in the code, and they belong in design review.

1. **`consumer_tag`.** §3 step 6 names `science.corpus-write.v1`. `compile_spec`
   runs `require_valid_identifier` over the tag — the grammar is
   `[A-Za-z0-9_-]{1,64}`, because the tag is woven into a scratch-leaf path
   component — so the dotted spelling cannot be shipped at all. The
   implementation uses `science-corpus-write-v1`, the same name in the admitted
   grammar. Science's own identity domains are untouched:
   `science.corpus-write-intent.v1` answers to `science.identity.v1`'s grammar,
   not to the engine's.
2. **Missing parent directories.** §3 step 3's mapping is three operations to
   three effects and step 6 says the adapter adds no effect of its own. `nodes`
   keeps a node at `<kind>/<slug>.md`, and the engine refuses a create whose
   parent *"neither exists nor is created by this transaction"*. The
   implementation emits `CreateDirectory` effects for the missing parents
   **inside the same transaction**, ordered before the file effect. The
   alternative — an `mkdir` outside the transaction — would put a corpus
   mutation outside the engine and break all-or-nothing, which is the worse of
   the two.

## 4. What this run does not claim

- **The portable tests claim nothing about durability**, by construction: they
  run the write API against `DefaultExecutor` or a fake executor, which is the
  substrate's best-effort path.
- **Chained but unanchored.** Every transaction registers in the engine's chain;
  no anchor act exists, so the unanchored tail grows without bound and its
  extent is unreported.
- **The recorded-history bound is inherited, not narrowed.** A raw write
  producing a self-consistent record passes the stale-hash check and the corpus
  check, and both arms above assert exactly that.
- **`clean-environment` is no more reachable here than in cut 3**, so R19(a)'s
  admission assertions are that admission is *unchanged* across the artifacts
  becoming unreachable here, with no `inconclusive` recorded and no refusal on
  reload — not that the assessment admits.
- **Heldness stays fixture-supplied.** Nothing is mounted, acquired or deleted.
