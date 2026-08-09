---
title: Open questions
status: living
created: 2026-08-08
updated: 2026-08-09
sources:
  - ../designs/2026-08-02-epistemic-kernel-design.md
  - ../designs/2026-08-02-substrate-consolidation-design.md
  - ../designs/2026-08-02-world-addressing-design.md
  - ../designs/2026-08-02-computation-reproducibility-design.md
  - ../designs/2026-08-03-correction-lifecycle-design.md
  - ../designs/2026-08-03-world-index-packaging-design.md
  - ../designs/2026-08-03-normative-contract-design.md
  - ../designs/2026-08-03-tamper-evident-log-design.md
  - ../designs/2026-08-04-domain-extension-boundary-design.md
  - ../designs/2026-08-04-formal-model-and-claim-calculus-design.md
  - ../designs/2026-08-05-belief-policy-design.md
  - ../designs/2026-08-05-review-disposition-and-conformance-cut-1.md
  - ../designs/2026-08-09-admission-ramp-design.md
---

# Open questions

This page groups the material open edges that remain after later designs closed
or narrowed earlier questions. It is a navigation aid, not a new docket: follow
the cited source before deciding or implementing an item.

Two things are deliberately **not** here. A **limitation** — a bound the designs
state and accept, such as finite witnesses proving reachability rather than
correctness, or code-lineage independence staying an authored claim — is not a
design uncertainty and is not listed as one. Neither is **deferred
implementation**: a guarantee row awaiting code is work, not a question.

## Foundations

- **Non-empirical knowledge route.** Mathematical, algorithmic,
  model-conditional, proof, derivation, and simulation claims cannot satisfy the
  empirical `observes` route. Do they get a second eligibility and answer model,
  or remain outside computed belief? ([kernel question](../designs/2026-08-02-epistemic-kernel-design.md#11-open-questions))
- **Empirical-observation facet.** What demonstrates an acquisition boundary,
  rather than merely asserting that a dataset is observational? This contract is
  the hinge of empirical eligibility. ([kernel question](../designs/2026-08-02-epistemic-kernel-design.md#11-open-questions))
- **Kernel-adjacent structures.** Are inquiries, patch definitions, structural
  chains, and coverage searches new kinds or derived views over existing kinds?
  ([kernel question](../designs/2026-08-02-epistemic-kernel-design.md#11-open-questions))
- **Package and durability seam.** Where is the Science profile distributed,
  and how should Python-only `atoms` capabilities compose with portable
  Python/TypeScript `nodes` without breaking the layering? ([substrate question](../designs/2026-08-02-substrate-consolidation-design.md#12-open-questions))
- **Which layer adopts `atoms` first.** Science waiting for `atoms` A7–A8 is one
  route; `nodes` adopting `atoms` is the other, and it buys durability without
  Science depending on `atoms` directly. But `atoms` is Python-only and
  platform-specific while `nodes` holds normative Python/TypeScript parity, so
  that route either breaks parity or forces a second `atoms`.
  ([substrate question](../designs/2026-08-02-substrate-consolidation-design.md#12-open-questions))
- **Pre-run fixation is not pre-registration.** Science can guarantee that a
  spec was frozen before its run. Calling that *pre-registered* additionally
  claims it preceded data access, which needs external evidence. The two must
  not merge in the user-facing vocabulary.
  ([kernel question](../designs/2026-08-02-epistemic-kernel-design.md#11-open-questions))

## Claims and belief

- **Binding-check lifecycle.** If vocabulary membership is checked separately,
  where is the receipt stored, how is it discovered or corrected, and may an
  unchecked claim be assessed? ([ρO1](../designs/2026-08-04-formal-model-and-claim-calculus-design.md#11-open-questions))
- **Entailment and estimand match.** Can evidence bear across related claims,
  and is estimand compatibility derived from claim entailment or governed by an
  independent typed relation? ([ρO3](../designs/2026-08-04-formal-model-and-claim-calculus-design.md#11-open-questions))
- **Qualifier grammar.** Quantitative restrictions, multiple restrictions,
  adjustment sets, modality, comparison, and disjunction remain outside the
  flat fragment. Adjustment placement depends separately on scientific target
  and identification method. ([formal-model questions](../designs/2026-08-04-formal-model-and-claim-calculus-design.md#11-open-questions), [adjustment ruling](../designs/2026-08-05-review-disposition-and-conformance-cut-1.md#8-open-questions))
- **Vocabulary gaps.** A population vocabulary, term-synonym resolution, and
  the namespace and ownership of a general-purpose operator contract remain
  unsettled. The **layer** set is declared — `contracts/science/CONTRACT.yaml`
  fixes it and editing it re-identifies every claim — so what is open there is
  admission to it, under the survey's agreement-exercise-reader rule.
  ([formal-model questions](../designs/2026-08-04-formal-model-and-claim-calculus-design.md#11-open-questions), [admission rule](../designs/2026-08-07-corpus-survey-and-vocabulary-admission-design.md#4-ruling-admission-by-agreement-and-exercise))
- **Higher-order records.** Eleven authored mm30 records concern claims,
  analyses, decisions, or the record system. Their re-homing must be settled
  before claim arguments widen from external referents to internal records.
  ([review classification](../designs/2026-08-05-review-disposition-and-conformance-cut-1.md#24-the-eleven-k-records--a-classification-and-a-moratorium))
- **Weighted belief.** Estimand typing needs an owner before study-design or
  precision weights can be compared; a successor must also decide whether any
  constants are global or domain-scoped. ([belief questions](../designs/2026-08-05-belief-policy-design.md#9-open-questions))
- **Losing the last held copy.** Nothing records the destruction of a final held
  artifact. The recorded-loss repair was withdrawn as premature and stays
  withdrawn, so the gap is a stated residue rather than an oversight.
  ([ρO2](../designs/2026-08-04-formal-model-and-claim-calculus-design.md#11-open-questions))
- **Whether the nine † labels are adopted.** The formal model froze none of
  them. Adopting commits the banked tables to a vocabulary; declining leaves the
  classifications as annotations. Cheap to decide now and expensive once the
  labels reach oracle prose.
  ([formal-model questions](../designs/2026-08-04-formal-model-and-claim-calculus-design.md#11-open-questions))

## Identity, world, and change

- **Which external authorities are accepted, and who decides.** Every rendered
  label and the ambiguous-search refusal resolve against a pinned local snapshot
  of an authority. How a snapshot is pinned, versioned, distributed and bumped —
  and whether a bump is an amendment act — is owed and undesigned.
  ([ruling question](../designs/2026-08-08-world-address-ruling.md#11-open-questions))
- **Whether a coreference balance belongs in any audit.** A coreference edge is
  outside belief by construction, but an active edge standing at `1` with a
  contested history is a different object from one standing at `12` with none.
  Nothing currently surfaces the difference.
  ([ruling question](../designs/2026-08-08-world-address-ruling.md#11-open-questions))
- **Attester reliability.** Every attestation carries unit weight, which is an
  honest default rather than a finding that attesters are equally reliable. The
  data collection that would inform per-source priors does not exist.
  ([ruling question](../designs/2026-08-08-world-address-ruling.md#11-open-questions))
- **Authority and coordination.** The designs assume one writer and no access
  control; multi-writer semantics, authority to retract, and propagation of
  cross-project blockers still need concrete rules. ([review writer question](../designs/2026-08-05-review-disposition-and-conformance-cut-1.md#8-open-questions))
- **Storage and retention.** Map/log serialization, epoch retention, redirect
  growth, and garbage collection need measurements before format or pruning
  rules are chosen. ([index questions](../designs/2026-08-03-world-index-packaging-design.md#12-open-questions), [log questions](../designs/2026-08-03-tamper-evident-log-design.md#12-open-questions))
- **Observer distribution.** Which independent holders keep world-log anchors,
  what continuity they attest, and what happens when the last observer is lost
  wait on a second installation. ([log question](../designs/2026-08-03-tamper-evident-log-design.md#12-open-questions))
- **Whether a dataset's own standing is retractable.** An upstream withdrawal
  already grounds retractions of dependent assessments. Whether a dataset's
  empirical-observation standing can be retracted directly is deferred until a
  concrete case forces it — the eligible-target test admits it with no new
  mechanism if so. ([correction question](../designs/2026-08-03-correction-lifecycle-design.md#9-open-questions))
- **Chain verification cost.** Full-timeline replay at mm30 scale sits behind
  the ledger's measurement gate. A Merkle overlay is the known upgrade path and
  is deliberately not built on speculation.
  ([log question](../designs/2026-08-03-tamper-evident-log-design.md#12-open-questions))

## Computation and reproducibility

- **Artifact lifetime.** Held code, environments, inputs, and outputs accumulate;
  pruning cannot silently destroy verification closure. A disk policy remains
  undesigned. ([computation question](../designs/2026-08-02-computation-reproducibility-design.md#13-open-questions))
- **Multi-product workflows.** Dataset-production v1 emits one product. A later
  shape needs to say whether one differing product fails the whole replay or
  creates separately verifiable results. ([computation question](../designs/2026-08-02-computation-reproducibility-design.md#13-open-questions))
- **A publishable belief-input snapshot.** Recomputing a belief without holding
  the corpora needs the digest's members published apart from the content they
  name. The world index already carries one such member, which argues for a
  single artifact — an argument, not yet a decision.
  ([computation question](../designs/2026-08-02-computation-reproducibility-design.md#13-open-questions))
- **Where the scope-derivation rule is versioned.** That rule's identity enters
  every verification address, so it needs one: with the belief policy, with
  `science.identity.v1`, or on its own.
  ([computation question](../designs/2026-08-02-computation-reproducibility-design.md#13-open-questions))

## Contracts and adoption

- **Admission ramp.** How does a corpus reach a useful admitted set without
  weakening held-ness or inventing a compatibility route? Now owned and
  specified, and narrowed to **externally sourced** input — what a corpus cannot
  re-author. The measurement is gated and **has not been run**, so the question
  stays open. ([admission ramp design](../designs/2026-08-09-admission-ramp-design.md),
  [review question](../designs/2026-08-05-review-disposition-and-conformance-cut-1.md#8-open-questions))
- **Contract governance.** Facet-breaking changes, compatibility ranges,
  parallel `genesis` contracts in one namespace, domain distribution, and
  Python/TypeScript parity policy remain open. ([domain questions](../designs/2026-08-04-domain-extension-boundary-design.md#12-open-questions))
- **Normative artifact shape.** Whether a contract cut becomes a world node and
  how legacy checks pass the adoption gate remain decisions for the first full
  contract cut. ([normative-contract questions](../designs/2026-08-03-normative-contract-design.md#11-open-questions))
- **Certifying the instruments that already exist.** An immutable spec cannot
  acquire the witnesses its falsification declaration lacks, so retroactive
  certification is unspellable and existing instruments certify only through a
  successor spec. Open is the cadence: sweep, mint on next authored use, or
  never. ([normative-contract questions](../designs/2026-08-03-normative-contract-design.md#11-open-questions))
- **Next conformance expansion.** A later cut should widen only when a designed
  boundary can exercise complete assertion arms; likely candidates are run
  capture, world persistence, or belief, each with different prerequisites.
  ([cut-1 deferrals](../designs/2026-08-05-review-disposition-and-conformance-cut-1.md#53-step-3--fully-deferred-rows-grouped-by-untouched-subsystem))
