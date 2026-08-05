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

Ten documents in `docs/designs/`, banked 2026-08-02 through 2026-08-04. Read
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
| `2026-08-03-redesign-adoption-ledger.md` | dependency order between the above, and the legal partial states in between |

The ledger is the entry point for "what is built, what is not, and what waits on
what." Every guarantee table is frozen under its identifiers: designs extend and
amend in place, never renumber.

## Status

Design complete, implementation not started. The guarantee tables are the
acceptance criteria — each row must be a failing test before it is a passing
one.
