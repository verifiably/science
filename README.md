# science

A system for recording scientific belief and the evidence it rests on, built on
two substrates: [`nodes`](https://github.com/khughitt/nodes) (the logical
entity/relation kernel) and [`atoms`](https://github.com/khughitt/atoms)
(durable atomic filesystem effects).

This repository is a clean start. Its predecessor is preserved, public and
unchanged, as [`proto-science`](https://github.com/khughitt/proto-science) —
where the design work below was done and reviewed. Nothing here imports it, and
records are reproduced under this system rather than migrated into it; the
reasoning is recorded in the adoption ledger's §0.

## The designs

Thirteen documents in `docs/designs/`, banked 2026-08-02 through 2026-08-05. Read
them in this order:

| document | what it rules |
|---|---|
| `2026-08-02-epistemic-kernel-design.md` | what belief is, what may change it, and what the system does not claim (guarantees G1–G8) |
| `2026-08-02-substrate-consolidation-design.md` | the `nodes`/`atoms` seam and the profile a corpus runs under (S1–S8) |
| `2026-08-02-world-addressing-design.md` | addresses, aliases, corpora, and the world index (W1–W13) |
| `2026-08-02-computation-reproducibility-design.md` | runs, recipes, replay, and lineage (R1–R23) |
| `2026-08-03-correction-lifecycle-design.md` | retraction and correction — subtracting standing without deleting a record (C1–C10) |
| `2026-08-03-world-index-packaging-design.md` | where the index lives, who writes it, and what freshness a consumer may assume (X1–X12) |
| `2026-08-03-normative-contract-design.md` | the versioned contract, its conformance oracles, and instrument certification (N1–N10) |
| `2026-08-03-tamper-evident-log-design.md` | pre-mutation registration and detectable removal (L1–L13) |
| `2026-08-04-domain-extension-boundary-design.md` | where domain-specific material lives, and how interpretation stays separable from identity (D1–D10) |
| `2026-08-04-formal-model-and-claim-calculus-design.md` | a formal model of the whole system, and what a claim *is* — typed, with identity over its structure rather than its prose (M1–M13) |
| `2026-08-05-review-disposition-and-conformance-cut-1.md` | disposition of an external review, measured against the trees, and the frozen first conformance cut |
| `2026-08-05-belief-policy-design.md` | what a belief *value* is, the exact binding it is pinned under, and the three answers to asking for one (P1–P9) |
| `2026-08-03-redesign-adoption-ledger.md` | dependency order between the above, and the legal partial states in between |

The ledger is the entry point for "what is built, what is not, and what waits on
what." Every guarantee table is frozen under its identifiers: designs extend and
amend in place, never renumber.

## Status

Design complete. The **conformance cut 1 vertical slice** (ledger §3, item 10)
landed 2026-08-07 — typed claim construction, canonical projection, identity,
decode and cross-language parity. It crosses no persistence boundary and
computes no belief, which is where the disposition record's §5.5 stop rule puts
its edge. Nothing beyond that edge is built.

The guarantee tables are the acceptance criteria — each row must be a failing
test before it is a passing one. Cut 1 selects **11 of the 126 rows**, arm by
arm, and was frozen *before* any code existed so that a row which fails is a
failure rather than a redefinition.

```
python/     the implementation (substrate §11 puts the composition root here)
ts/         the one shared encoding, and nothing else (formal model lim. 9)
fixtures/   the cross-language parity corpus, owned by neither
contracts/  the science base contract
```
