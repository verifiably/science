# Conformance cut 6 — discharge results

**Date:** 2026-08-20
**Subject:** the authoritative world-registry slice
(`docs/designs/2026-08-20-world-registry-design.md`), measured against
conformance cut 6's frozen selection
(`docs/designs/2026-08-20-conformance-cut-6.md`).

**The frozen source rows, selected bullets, and accounting are not edited
here.** Cut 6 froze on 2026-08-20 and results are recorded separately, which
is what this document is.

## 1. What ran, and where

The Science commands used the reviewed editable `nodes` prerequisite at
commit `7cd9bd143216511f48c44160d16a65a2a1c190ad`. The `nodes` gates ran in
that repository's `python/` and `ts/` directories; the Science gates ran from
this repository's `python/` directory. In the table,
`$NODES_PROJECTION_PYTHON` denotes that reviewed `nodes` Python worktree.

| suite | command | result | claim |
|---|---|---|---|
| `nodes` Python behavior | `uv run --frozen pytest -q` | 530 passed | public `projection.v1` prerequisite behavior |
| `nodes` Python static checks | `uv run --frozen ruff check .`; `uv run --frozen pyright src` | passed; 0 errors | prerequisite code quality and typing |
| `nodes` TypeScript behavior | `npm test` | 358 passed in 44 files | public `projection.v1` prerequisite behavior and parity |
| `nodes` TypeScript static checks | `npm run typecheck`; `npm run check` | passed; Biome checked 64 files | prerequisite typing and formatting |
| portable Science tests | `uv run --frozen --with-editable "$NODES_PROJECTION_PYTHON" pytest` | 1,401 passed | behavior; **no** durability claim |
| contributor-guide links and freshness | `uv run --frozen --with-editable "$NODES_PROJECTION_PYTHON" python tools/check_guide.py` | passed | documentation consistency |
| design-corpus guard | `uv run --frozen --with-editable "$NODES_PROJECTION_PYTHON" pytest tests/test_designs_corpus.py -q` | 12 passed | frozen design inventory and accounting |
| Science static checks | `uv run --frozen --with-editable "$NODES_PROJECTION_PYTHON" ruff check .`; `uv run --frozen --with-editable "$NODES_PROJECTION_PYTHON" pyright src` | passed; 0 errors | code quality and typing |
| durable cut-6 and N2 acceptance | `uv run --frozen --with-editable "$NODES_PROJECTION_PYTHON" python -m tools.cut6_acceptance` | 19 passed | cut-6 discharge on the certified tuple |
| repository whitespace | `git diff --check` in Science and `nodes` | passed in both repositories | no whitespace errors |

The exact portable output was:

```text
1401 passed in 229.78s (0:03:49)
```

The exact certified acceptance output was:

```text
...................                                                      [100%]
19 passed in 11.37s
```

The portable suite excludes `tests/acceptance` by configuration. It proves
portable behavior only. The certified runner probes the volume before
collection and errors rather than skips when the engine refuses the tuple;
only that runner proves the durable registration-entry arms.

## 2. The selected rows and labeled behavior

Cut 6 discharged exactly **14 selected + 8 labeled = 22** declaration units
from 5 frozen rows. Row accounting remains **2 full + 2 part + 1 deferred =
5**.

**Selected in full: X4 and X6.** Their five units establish:

- X4: no registry purge, replace, or delete operation is spellable through the
  public API; raw admission deletion remains undetected and emits no finding.
- X6: retirement is terminal with no return-to-live act; restoring one byte-copy
  replica recomputes presence without another admission; and status reduction
  is invariant under registry-record arrival order.

**Selected in part: X5 and W13.** Their nine units establish:

- X5: a known `corpus_id` refuses both differing `fresh` and `replica-of`
  admission provenance without writing a record.
- W13: fresh corpus ids are opaque and stable across moves and re-clones; no
  ordinary API re-mints an existing manifest; node content and add/remove/
  retarget changes to `produces` relations move corpus state while semantic
  identity stands; relation reordering moves corpus state; file renames,
  non-manifest formatting, manifest formatting and domain-map ordering, mtimes,
  and location are inert; every semantic manifest member moves corpus state;
  unknown, duplicate, and malformed manifest input refuses before digesting;
  and git state is not a corpus-state identity member.

**Fully deferred: X7.** Its two build-side arms wait on slice 2's epoch build.
X5's build-side duplicate-carrier refusal and W13's other build, receipt,
coverage, fork-construction, world-resolution, and project-coordination clauses
remain outside this discharge.

The eight labeled declarations establish behavior added by the slice but not
assigned to a frozen row:

- exact admission retry succeeds without a second file;
- exact status retry succeeds, while a differing terminal act refuses;
- world initialization recovers between genesis registration and mirror
  creation and remains idempotent;
- the committed mirror registration names `world.yaml`;
- the committed manifest registration names `corpus.yaml`;
- committed admission and status registrations name their `registry/` paths;
- duplicate carriers produce a distinct error-severity finding and do not count
  as ordinary absence; and
- corpus checking distinguishes a malformed manifest from an absent one.

N2 declares those 22 units as data and audits their exact test nodes against
source mutations for `vacuous`, `mixed`, `uncollected`, `stale`, and collapsed
class-node coverage. The certified command includes that audit; the baseline
and every sabotage resolved.

## 3. Feasibility clarification and prerequisite

Science commit `c309db9a33cd71954f2b5baa66e5c05d35ccee17`
clarified the identity seam before implementation: `nodes` owns versioned RFC
8785 canonical projection text, while Science parses its JSON numbers as
`Decimal`, uniformly tags every JSON value type, and owns the
`science.node-content.v1` digest. The clarification changed neither frozen row
text nor cut accounting.

The prerequisite then landed in `nodes` at
`7cd9bd143216511f48c44160d16a65a2a1c190ad`: both language implementations
ship the public `projection.v1` value and RFC 8785 text APIs, with shared text
parity and invalid-value refusal. Science consumed that reviewed worktree as an
editable overlay; no projection implementation was copied into Science.

## 4. Propagated-claim audit

Before close-out, the required grep found four classes of text:

- live drift in `python/README.md`, ledger rows 1 and 2, and the ledger's Plan B
  gate note; these claims were corrected in this landing;
- the cut's dated second-reader statement that implementation was prospective
  **at freeze**, which remains valid history;
- the packaging design's dated statement that the world index was the largest
  unbuilt artifact when that design banked, which remains historical context;
  and
- the world-registry design's close-out instruction to grep for claims that the
  world index is wholly unbuilt, which is choreography rather than a current
  implementation claim.

After close-out, only the latter three historical or procedural hits remain.
None claims that the authoritative registry core is still unbuilt.

## 5. What this run does not claim

- No epoch or world-index build, derived map, derivation receipt, rules-store,
  `current`, staleness, or garbage-collection behavior is implemented.
- X7 and X5's build-side duplicate-carrier refusal remain deferred to slice 2.
- No fork constructor is implemented; `fork-of` admission uses fixture-authored
  manifests.
- Committed registration entries are not full chain replay or refutation, and
  the ordinary open path does not verify genesis/mirror agreement.
- No anchor carriage or anchor verification is implemented.
- Raw registry deletion is not detected; the chain remains unanchored.
- Locks serialize cooperating writers in one process only; cross-process
  single-writer operation remains a deployment obligation.
