---
title: Glossary
status: living
created: 2026-08-08
updated: 2026-08-08
sources:
  - ../designs/2026-08-02-epistemic-kernel-design.md
  - ../designs/2026-08-02-world-addressing-design.md
  - ../designs/2026-08-02-computation-reproducibility-design.md
  - ../designs/2026-08-03-normative-contract-design.md
  - ../designs/2026-08-04-formal-model-and-claim-calculus-design.md
  - ../designs/2026-08-05-belief-policy-design.md
---

# Glossary

Terms are defined in their Science-specific sense. Follow the topic link for
context and the linked design references for normative detail.

- **Address** — A canonical lookup key, `kind:<basis-digest>`, distinct from
  alias, location, and historical continuity. ([identity](identity-world-and-change.md#identity-is-not-one-field))
- **Alias** — A human-facing, non-unique name that resolves to zero or more
  records and does not affect identity. ([identity](identity-world-and-change.md#identity-is-not-one-field))
- **Analysis spec** — An immutable preregistered plan naming a proposition,
  estimand, interpretation, inputs, parameters, nondeterminism, and equivalence
  rule for an assessment run. ([computation](computation-and-reproducibility.md#the-analysis-spec-freezes-the-scientific-plan))
- **Assessment** — A run-derived result that evaluates one proposition and is
  the only record kind allowed to enter empirical belief. ([claims](claims-and-belief.md#assessments-are-the-only-empirical-route))
- **Belief** — A policy-bound computed view over a complete set of eligible,
  directional, independence-filtered assessments; v1 returns a signed integer.
  ([claims](claims-and-belief.md#a-belief-is-a-reproducible-view))
- **Belief input digest** — The identity of the exact world, records, standing,
  rules, and bindings consulted by a belief computation. ([claims](claims-and-belief.md#a-belief-is-a-reproducible-view))
- **Canonical projection** — The prescribed meaning-bearing representation
  hashed for an identity, excluding presentation and location fields.
  ([foundations](foundations.md#contracts-compile-into-profiles))
- **Claim** — The opaque runtime value of a proposition after its operator,
  arguments, qualifiers, polarity, and layer pass the active profile.
  ([claims](claims-and-belief.md#a-claim-is-typed-by-its-operator))
- **Clean-environment verification** — A passed comparison of equal recipes
  with qualifying fresh-environment and confinement evidence; the only scope
  that can admit an assessment. ([computation](computation-and-reproducibility.md#replay-verification-and-belief-are-different-decisions))
- **Conformance cut** — A prospectively selected subset of guarantee assertion
  arms that one implementation slice can exercise without crossing an
  undesigned boundary. ([adoption](contracts-and-adoption.md#adoption-follows-legal-partial-states))
- **Contract cut** — An immutable, content-addressed version of the normative
  Science contract and its exact oracle-case identities. ([contracts](contracts-and-adoption.md#designs-explain-contract-cuts-will-govern))
- **Corpus** — An admitted collection with a durable opaque `corpus_id`, a
  profile-pinning manifest, and identity-changing states. ([identity](identity-world-and-change.md#there-is-one-world-projects-are-views))
- **Corpus state identity** — A digest of the complete canonical corpus manifest
  plus the sorted identities of its nodes. ([identity](identity-world-and-change.md#there-is-one-world-projects-are-views))
- **Dataset-production run** — A run shape that transforms data and produces one
  dataset without a proposition, spec, or assessment. ([computation](computation-and-reproducibility.md#one-run-kind-has-two-shapes))
- **Domain contract** — A namespaced declaration of domain sorts, operators,
  qualifier dimensions, facets, and vocabulary bindings. ([foundations](foundations.md#contracts-compile-into-profiles))
- **Epoch** — An immutable world-index publication over explicit corpus states,
  world records, rules, and derivation receipts. ([identity](identity-world-and-change.md#the-world-index-is-a-named-covered-view))
- **Held** — Exactly reproducible bytes available on demand under a content
  identity; not a synonym for raw, public, local, or checked into Git.
  ([foundations](foundations.md#the-epistemic-invariant))
- **Identity basis** — The kind-specific semantic fields whose canonical
  projection determines a record's content identity. ([identity](identity-world-and-change.md#identity-is-not-one-field))
- **Independence** — A pairwise, three-valued judgment derived from complete
  dataset-lineage closure: independent, shared-source, or not-certified.
  ([claims](claims-and-belief.md#assessments-are-the-only-empirical-route))
- **Instrument certification** — A recomputable witness that a specific rule and
  implementation binding conforms and can reach its required outcomes.
  ([contracts](contracts-and-adoption.md#rules-bind-meaning-to-the-code-that-ran))
- **Mutation log** — A per-root hash-linked chain registering boundary
  transactions and destructive intent, with heads observed outside their own
  deletable set. ([identity](identity-world-and-change.md#mutation-history-is-detectable-relative-to-observers))
- **NoBelief** — A successful answer saying belief cannot be produced because
  inputs are unavailable, no assessment is eligible, or only non-directional
  outcomes remain. ([claims](claims-and-belief.md#a-belief-is-a-reproducible-view))
- **Operator** — A contract-declared claim predicate whose arity, argument
  sorts, qualifiers, polarity aptitude, and layers determine valid claims.
  ([claims](claims-and-belief.md#a-claim-is-typed-by-its-operator))
- **Oracle** — A frozen guarantee obligation identified by a permanent label
  and made executable through a check plus a mutation that must break it.
  ([contracts](contracts-and-adoption.md#every-oracle-must-be-falsifiable))
- **Policy binding** — The required pair of belief-policy rule identity and
  implementation content identity used for one belief computation.
  ([claims](claims-and-belief.md#a-belief-is-a-reproducible-view))
- **Profile** — The runtime specification compiled from one Science base
  contract and the domain contracts pinned by a corpus manifest.
  ([foundations](foundations.md#contracts-compile-into-profiles))
- **Proposition** — An immutable record whose semantic identity is its typed
  claim structure, not its prose rendering. ([claims](claims-and-belief.md#structure-not-prose-determines-identity))
- **Reads** — A run-input role for literature, configuration, ontologies, and
  other context that never confers empirical eligibility. ([foundations](foundations.md#closed-routes-inert-by-default))
- **Refused** — A fail-early boundary outcome for malformed, contradictory, or
  out-of-contract input; it never guesses or repairs. ([foundations](foundations.md#valid-transitions-refuse-audit-detects-bypasses))
- **Retraction** — An immutable, attributed record that subtracts an exact
  target's standing at read time without deleting or modifying it.
  ([identity](identity-world-and-change.md#correction-is-additive))
- **Rule binding** — The exact pair of a fixture-defined rule identity and the
  held implementation content identity that executed it. ([contracts](contracts-and-adoption.md#rules-bind-meaning-to-the-code-that-ran))
- **Run** — A complete immutable execution closure consisting of a recipe,
  result, and occurrence. ([computation](computation-and-reproducibility.md#a-run-has-three-complete-parts))
- **Source assertion** — A record of what a source asserts, denies, or
  hypothesizes about a proposition; it is useful but has no edge into belief.
  ([foundations](foundations.md#the-epistemic-invariant))
- **Standing** — The active status calculated from an acyclic retraction graph,
  including counter-retractions, rather than stored as a mutable flag.
  ([identity](identity-world-and-change.md#correction-is-additive))
- **Supersession** — An additive relation naming a replacement or continuation;
  unlike retraction, it does not subtract the predecessor's standing.
  ([identity](identity-world-and-change.md#correction-is-additive))
- **UID** — A durable continuity identifier used when addresses change through
  correction or merge. ([identity](identity-world-and-change.md#identity-is-not-one-field))
- **Verification** — An immutable comparison of two runs under a frozen
  equivalence rule, with a derived scope and verdict. ([computation](computation-and-reproducibility.md#replay-verification-and-belief-are-different-decisions))
- **World** — The union of admitted corpora and world-level records; projects
  are views over it, not separate epistemic universes. ([identity](identity-world-and-change.md#there-is-one-world-projects-are-views))
