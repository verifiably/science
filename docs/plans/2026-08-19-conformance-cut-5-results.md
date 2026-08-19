# Conformance cut 5 — discharge results

**Date:** 2026-08-19
**Subject:** the family-adapter implementation
(`docs/designs/2026-08-19-family-adapters-design.md`), measured against
conformance cut 5's frozen selection
(`docs/designs/2026-08-19-conformance-cut-5.md`).

**The frozen source rows are not edited here.** Cut 5 froze on 2026-08-19 and
results are recorded separately, which is what this document is. Its two
post-freeze feasibility corrections remain dated in the cut document; they
narrowed unexecutable declarations rather than proxying them with weaker tests.

## 1. What ran, and where

| suite | command | result | claim |
|---|---|---|---|
| durable family and N2 acceptance | `uv run --frozen python -m tools.cut5_acceptance` | 39 passed | cut-5 discharge |
| portable unit tests | `uv run --frozen pytest tests -q` | 1,279 passed | behavior; **no** durability claim |
| contributor-guide links and freshness | `uv run --frozen python tools/check_guide.py` | passed | documentation consistency |
| static checks | `uv run --frozen ruff check .`; `uv run --frozen pyright` | passed; 0 errors | code quality and typing |

The certified acceptance output was:

```text
.......................................                                  [100%]
39 passed in 14.06s
```

The runner probes the volume before collection and returns error code `2`,
never a skip, when the engine refuses the tuple. This run exercised the
certified engine on the repository volume. Its explicit uncertified-volume arm
also observed fail-closed refusal on `/dev/shm`, with no payload write.

The portable suite excludes `tests/acceptance` by configuration. Its collection
enumerated 1,279 tests; the full run reached 100% with exit code `0`. It proves
the portable behavior, while only the acceptance command proves the durable
arms.

## 2. The selected rows

Cut 5 discharged exactly **28** selected declaration units from 24 frozen rows.
Row accounting is **8 full + 10 part + 6 deferred = 24**.

**Selected in full:** S2, S3, S4, G7, C1, C2, C4, and C5.

- Supersession creates one successor and preserves the predecessor and its
  evidence; semantic prose revisions replace in place without changing the
  digest or reaching rename.
- Explicit import refuses a stale stamp before payload, while a consistently
  restamped semantic edit remains inside the recorded-history bound.
- Retraction is additive and attributed. Standing, sibling
  counter-retractions, admission, belief direction, and closure digests respond
  to the standing retraction graph without editing the target.

**Selected in part:** M5, T1, T2, M3, R20, C3, C6, C10, G2c, and G8.

- The founding qualification edit forks identity and leaves prior evidence on
  the predecessor.
- Imported foreign act-reports remain structural, attributed, inert evidence.
  Successful and refused imports produce their exact intent/payload/report
  histories; intent-append failure starts no act.
- Local standing terminates over chains and siblings. The abstract validator
  returns a cycle witness, import consumes a forced cycle verdict, and ordinary
  retraction target resolution refuses missing targets.
- R20's locally decidable nondeterminism contradiction refuses. The selected
  C3/C6/C10/G2c/G8 arms exercise closure movement, eligible targets and routes,
  and retraction-driven admission and belief recomputation.

**Fully deferred:** R19, R22, R23, C7, C8, and C9. No selected arm or test
proxies R19, R22, or R23. Their semantic evidence, world-index, audit, and
registry prerequisites remain their named unblockers.

N2 declares those 28 units as data and audits their exact test nodes against
source mutations for `vacuous`, `stale`, `mixed`, `uncollected`, and collapsed
class-node coverage. The certified command includes that audit; the baseline
and every sabotage resolved.

## 3. Corrections and deviations

The selection history is **34 → 31 → 28** declarations:

1. The independent reader's bank-time result counted 34 units and classified
   the rows as 8 full + 12 part + 4 deferred.
2. The first dated feasibility correction deferred R19 and R22 because the
   persisted projections and `import_bundle(Sequence[Node])` do not carry the
   complete closure, result, comparison, frozen-specification, or callable-rule
   evidence their semantic checks require. This produced 31 units and the
   final row accounting, 8 full + 10 part + 6 deferred.
3. The second dated feasibility correction deferred T2's second-fulfillment
   classification until a durable-log consumer exists, and M3's two concrete
   cyclic-bundle arms until controlled cyclic retractions are spellable. T2 and
   M3 remained part rows, producing the final 28 units without changing row
   accounting.

Both corrections were recorded in the cut and family design on 2026-08-19
before discharge. No further design deviation was hidden or accepted by the
run.

## 4. What this run does not claim

- Local standing and import context are not authoritative world standing.
- The operation log is durable and chained but remains unanchored.
- A stranded intent or intent-plus-payload has no recovery-resumption path.
- Cross-process single-planner enforcement remains a deployment obligation.
- Consolidate, move/rename, deletion, the world index, global audit, holdings,
  anchor carriage, rules-store resolution, and registry compilation remain
  outside this cut.
