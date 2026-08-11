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

Start with the concise [contributor guide](docs/guide/README.md) for the system's
key ideas, reading paths, glossary, and open questions. Use the design corpus
below for rationale and frozen guarantees.

## The designs

Twenty-one documents in `docs/designs/`: the banked redesigns, review disposition,
adoption ledger, measurements, rulings, and contributor-guide design written
2026-08-02 through 2026-08-11. Read them in this order:

| document | what it rules |
|---|---|
| `2026-08-02-epistemic-kernel-design.md` | what belief is, what may change it, and what the system does not claim (guarantees G1–G9) |
| `2026-08-02-substrate-consolidation-design.md` | the `nodes`/`atoms` seam and the profile a corpus runs under (S1–S8) |
| `2026-08-02-world-addressing-design.md` | addresses, corpora, and the world index (W1–W16) |
| `2026-08-02-computation-reproducibility-design.md` | runs, recipes, replay, and lineage (R1–R23) |
| `2026-08-03-correction-lifecycle-design.md` | retraction and correction — subtracting standing without deleting a record (C1–C10) |
| `2026-08-03-world-index-packaging-design.md` | where the index lives, who writes it, and what freshness a consumer may assume (X1–X12) |
| `2026-08-03-normative-contract-design.md` | the versioned contract, its conformance oracles, and instrument certification (N1–N10) |
| `2026-08-03-tamper-evident-log-design.md` | pre-mutation registration and detectable removal (L1–L13) |
| `2026-08-04-domain-extension-boundary-design.md` | where domain-specific material lives, and how interpretation stays separable from identity (D1–D10) |
| `2026-08-04-formal-model-and-claim-calculus-design.md` | a formal model of the whole system, and what a claim *is* — typed, with identity over its structure rather than its prose (M1–M13) |
| `2026-08-05-review-disposition-and-conformance-cut-1.md` | disposition of an external review, measured against the trees, and the frozen first conformance cut |
| `2026-08-05-belief-policy-design.md` | what a belief *value* is, the exact binding it is pinned under, and the three answers to asking for one (P1–P9) |
| `2026-08-07-corpus-survey-and-vocabulary-admission-design.md` | what eight predecessor corpora actually contain, and what earns a vocabulary a place in the base profile |
| `2026-08-07-multi-corpus-typing-exercise.md` | the first executable multi-corpus claim-typing measurement and its vocabulary-admission result |
| `2026-08-03-redesign-adoption-ledger.md` | dependency order between the above, and the legal partial states in between |
| `2026-08-08-contributor-guide-design.md` | the organization, authority, freshness, and verification rules for the concise contributor guide |
| `2026-08-08-world-address-ruling.md` | closes docket §4.1: basis-derived addressing upheld, labels rendered rather than stored, coreference graded rather than merged |
| `2026-08-09-admission-ramp-design.md` | how externally sourced input reaches held — the measurement, and the ruling downstream of it: three states, `W3` narrowed, `G9` appended, F2 closed |
| `2026-08-09-conformance-cut-2.md` | the second frozen conformance cut, drawn at the belief seam over the 139-row corpus, with the admission ramp's three open questions as boundary conditions |
| `2026-08-10-verified-holdings-record-design.md` | where verified holdings are recorded: a per-location world record in the observer's corpus, act-minted, superseded never expired, projected under a declared coverage — H1–H4 |
| `2026-08-11-act-report-design.md` | the run boundary's report seam: the act-report, boundary-minted terminal record of an opened operation or pre-intent refusal record of a rejected run request; the operation intent's derived three-valued completion reading; the durable home of a look's non-report — T1–T8 |

The ledger is the entry point for "what is built, what is not, and what waits on
what." Every guarantee table is frozen under its identifiers: designs extend and
amend in place, never renumber.

## Status

Design complete. The **conformance cut 1 vertical slice** (ledger §3, item 10)
landed 2026-08-07 — typed claim construction, canonical projection, identity,
decode and cross-language parity. It crosses no persistence boundary and
computes no belief, which is where the disposition record's §5.5 stop rule puts
its edge. Cut 1 itself built nothing beyond that edge.

The guarantee tables are the acceptance criteria — each row must be a failing
test before it is a passing one. There are **151 rows** across **thirteen frozen
tables** (G, S, W, R, C, X, N, L, D, M, P, H, T). Cut 1 selects **11 of the 126 rows**
across the ten tables that existed when it was drawn, frozen *before* any code
existed so that a row which fails is a failure rather than a redefinition.
**Conformance cut 2** was frozen 2026-08-09 on the same discipline, before its
slice existed: it is drawn at the **belief seam** — the derived admission state,
the assessment admission gate, the belief input closure digest, and
`science.belief.v1` under an exact binding — selecting **13 rows in full and 11
in part**, including the belief policy's P1–P9 and the admission ramp's G9,
whose verified-holdings observations enter as supplied arguments because where
they are recorded was, at the freeze, an open design — closed 2026-08-10 by the
verified-holdings record design. Its slice landed 2026-08-09: derived admission
state, the assessment admission gate, the belief input closure digest, and
`science.belief.v1` under an exact binding now compute.

```
python/     the implementation (substrate §11 puts the composition root here)
ts/         the one shared encoding, and nothing else (formal model lim. 9)
fixtures/   the cross-language parity corpus, owned by neither
contracts/  the science base contract
```
