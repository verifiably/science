# Domain extension boundary — design

**Status:** Draft for review, 2026-08-04. Rules where domain-specific material
lives across `nodes`, `science`, and downstream domains; closes substrate §12's
kind-SSOT question; and organizes the `science` repository so that a later
decomposition into distributable packs is a move, not a rewrite. No domain
exists yet: this design rules the **boundary** and the **organization**, and
deliberately builds no domain-pack machinery (ledger §5's materialization rule).
**Inherits:** substrate §2 (split by nature; the pricing argument;
defer-and-promote), §4.1/§6.1 (the arity-and-history test), §12 (the
`KIND_DESCRIPTORS`-versus-`KindSpec` open question, closed here); kernel §4.2
(the ten kernel kinds), §4.2.1/§5.1 (the G3 belief-input closure), §4.3
(Referents — `term`, external), limitation 4 (the predicate vocabulary);
world §4.2 (per-kind identity bases; `dataset` is content identity), §5
(corpus-state identity), limitation 9 (the manifest is not a node and nothing
checks it); packaging §6 (the manifest's closed field set); normative-contract
5b §7 (rule binding frozen at freeze, receipt naming the executed
implementation); ledger §5 (record the seam, materialize later).
**Constraints:** the guarantee tables extend, never renumber. This design adds
its own table (**D**) and, where a banked rule must change (world §5, W13,
limitation 9; packaging §6; kernel §5.1; substrate §6.1/§12), amends in place
under the retained identifier.

**Banking amendment set** (to apply across the corpus in the banking commit):
world **§5**'s corpus-state identity is redefined over the **complete canonical
manifest projection plus** the sorted node identities; world **W13**'s
non-node-file clause splits three ways (manifest formatting-only → unchanged;
manifest semantic change → moves; other non-node file → unchanged); world
**limitation 9** narrows to the residue that survives; packaging **§6**'s
"nothing else, deliberately" closure is **superseded** by the `profile` block;
kernel **§5.1**'s G3 closure gains a member — **every profile contract the
derivation consults**: exactly one `science_contract` **unconditionally**, plus
each domain contract whose namespaced facets are actually read;
**W5 is preserved unamended** by §8.1's agreement and move-refusal rules;
substrate **§12**'s kind-SSOT question **closes** by retiring
`KIND_DESCRIPTORS` in favour of a single compiled `ProfileSpec`; substrate
**§6.1**'s
placement of the `empirical-observation` facet as native to `nodes` is
**corrected** to the `science` profile (§3.4 here). The ledger gains this
design as a §5 companion.

## 1. Why

Two problems, one boundary.

**The observed problem.** `proto-science` accumulated domain-specific material
without a rule for where it goes. Its `skills/` tree carries fourteen sibling
groups that conflate three different things: field domains (`bio/` → genomics,
transcriptomics, proteomics), methods (`statistics`, `ml`, `study-design`,
`literature`), and system concerns (`epistemics`, `meta`, `data-management`,
`writing`). Fifty-three generated artifacts sit inside the same tree as
hand-authored source. Entity kinds are minted dynamically as project-local
(`layer/local`) with no declared vocabulary anywhere. And the one piece of real
domain machinery — bio identity: gene crosswalks, assembly registry, cytoband,
liftover — is embedded imperatively in the tool because there was nowhere
better to put it. Nothing here is wrong locally; there is simply no rule, so
each addition picked its own home.

**The unruled problem.** The banked designs are, on inspection, almost entirely
**silent** on domain modeling — and the silence is verified rather than
assumed. "Ontology" and "controlled vocabulary" do not appear at all in the
substrate or computation designs; they appear once in world (§3's tier table,
placing `term` external) and only as `reads` inputs in the kernel. There is no
schema registry, no per-corpus typing, no plugin framework, and no
generic-versus-domain boundary stated anywhere. Two consequences follow. First,
this design is answering an open question rather than overturning a ruling —
substrate §12 says outright that the kernel's kind descriptors and `nodes`'
`KindSpec` registry are two registries where "one must derive from the other,
and which direction is unresolved." Second, the absence is already producing
drift: substrate §6.1 places the `empirical-observation` facet and its payload
schema *native to `nodes`*, while the same document's governing argument is
that scientific policy in a structural kernel "contaminates" it. That facet is
the hinge the entire eligibility predicate turns on. The boundary is already
blurred at exactly the point this design exists to rule.

## 2. Framing rulings

**2.1 Identity answers *which bytes*; interpretation answers *what they mean*.**
These are different questions and stay separate mechanisms. A dataset's basis is
content identity (world §4.2) and remains so; nothing in this design puts a
type, shape, format, or schema into an address. What the bytes *mean* — that
this file is a matrix whose rows are genes in a named vocabulary — is a
separate, **checkable** claim carried alongside. The separation is what keeps
replay's bitwise comparison sound while making interpretation falsifiable.

**2.2 Domain content never enters `nodes`; mechanism may.** `nodes` may hold
the facility for declaring, composing, and validating facets. It may not hold
biology, a controlled vocabulary, or an ontology binding. The reasons are the
substrate design's own: every addition to `nodes` costs a Python
implementation, a TypeScript implementation, conformance fixtures, and a
`STANDARD.md` bump (§2); "a primitive is justified by who can call it, not by
how clean it looks" (§2); and *defer-and-promote* is the stated default.
Domain facets have exactly one class of caller. They start above, and this
design promotes nothing.

**2.3 Interpretation is a facet while it is mechanically checkable metadata.**
A facet is the right carrier precisely as long as the claim can be validated
against bytes by a checker. The **promotion trigger** is explicit: when
interpretations need *independent authorship*, *competing alternatives*, or
*retraction*, they become interpretation **nodes**, because those three
operations are defined over records, not payloads — retraction in particular is
a record-level act (5a). Until one of the three is actually needed, promoting
early buys a node kind and its lifecycle for nothing.

**2.4 A vocabulary binding is exact or it is absent.** A bare name — "HGNC" —
is not a binding, because the referent drifts underneath it. A binding names
either a defined namespace *release*, or, preferably, the content identity of a
**held ontology dataset**. Whether that dataset resolves locally is a separate
question with a legitimate `not-present` answer (world §5.1's vocabulary),
which keeps domains installable without carrying gigabytes.

**2.5 Contracts govern corpus states; nodes carry no creation stamps.** "This
body of records was authored under biology 0.3" is recorded once, for the
corpus, as the contract its **current state** must validate against — not
stamped on every node. A per-node creation stamp is an unfalsifiable claim
about the past; a corpus-level pin is checkable now and fails loudly. The
temporal record that a stamp would duplicate already exists, with its own
stated bound: the mutation log registers **boundary-mediated** changes, and
`corpus.yaml` is inside its registered surface, so a raw edit is *detectable*
by replay rather than registered — subject to that design's anchor limitations
(its L5 unanchored-tail residue and the surviving-observer bound). Receipts
independently name the exact implementation that executed a check. A per-node
stamp would duplicate both while inheriting the same bound, since a stamp is
itself raw-editable.

## 3. The ownership split

```text
nodes       facet / registry composition mechanics
science     kernel kinds and cross-node scientific policy
domains     namespaced facet contracts, schemas, validators, vocabulary adapters
practices   procedural guidance only — no vocabulary, no schema

        active domain contracts + science base profile
                            ↓
                   derived nodes Registry
```

### 3.1 `nodes` — mechanism only

`nodes` keeps what it already has: `Node`, `Relation`, `ShapeSpec`, `KindSpec`,
`Registry` with facet composition and invariant validation, indexes, and the
canonical projection. It gains **nothing** from this design (§6). It learns
about no domain, no ontology, and no vocabulary.

### 3.2 `science` — kernel kinds and cross-node policy

`science` owns the ten kernel kinds (kernel §4.2), the relation signatures that
close belief, the eligibility predicate, and every judgment spanning more than
one node — the arity-and-history test from substrate §4.1/§6.1 is unchanged.
It also owns the **base profile**: the facet contracts that are scientific
rather than domain-specific.

### 3.3 `domains` — namespaced facet contracts

A domain owns a **namespaced facet contract**: the facet's key namespace, its
payload schema, its validators, and its vocabulary adapters. A domain never
defines a kernel kind and never redefines a relation signature; it contributes
facets to kinds that already exist.

### 3.4 The `empirical-observation` correction

Substrate §6.1 rules the `empirical-observation` facet and its payload schema
"native to `nodes`." Under §2.2 that placement is wrong, and this design
corrects it in place: the facet belongs to the **`science` base profile**. It
is the hinge of the eligibility predicate (kernel §4.1) — a declared acquisition
boundary is scientific policy in the most direct sense, and its honesty is
explicitly outside the guarantee (kernel limitation 8). Nothing about it is
structural. The correction costs `nodes` nothing and removes the one existing
counterexample to the boundary this design draws.

**Confirmed on review, 2026-08-04**, on an independent argument: `dataset` is
itself a Science kernel kind, and acquisition-boundary semantics are scientific
policy, so leaving either in domain-free `nodes` would contradict `nodes`'
own ownership contract. The correction does not rest on §2.2 alone.

### 3.5 `practices` — procedure without vocabulary

A practice (statistics, causal modeling, study design) carries **skills and
procedural guidance only**. The distinguishing test is mechanical: a domain
brings a vocabulary binding, a practice does not. If a practice acquires one,
it was a domain.

## 4. Interpretation as facet conjunction

There is no `BioDataFrame` kind and no `BioDataFrame` class. There is a node of
kind `dataset` carrying independently validated facets:

```yaml
kind: dataset
facets:
  tabular:
    orientation: wide
  biology/gene-axis:
    axis: rows
    vocabulary: dataset:<content-identity>
```

Each facet validates on its own terms; their conjunction is the "type." This is
composition rather than inheritance, and it means a domain adds expressiveness
by contributing a facet contract rather than by subclassing anything.

**What this does to identity, precisely.** A dataset's address is its content
identity, so adding or correcting an interpretation **does not mint a different
dataset** — the bytes did not change. But whole-node identity covers `facets`
(world §5, over `nodes`' canonical projection), so the same act **does** move
node content identity and therefore corpus state. That is the desired
asymmetry: the data is the same data, and the corpus knows something changed.

**No per-node domain list.** A node states which domain semantics it uses by
the **namespace of the facets it carries**. A redundant `domains:` field on
each node would restate what the facet keys already say, and would be a second
place to go stale.

## 5. Vocabulary binding

A domain's vocabulary adapter declares what it binds to. Two forms, in
preference order:

```yaml
# preferred — a held ontology dataset, by content identity
vocabulary: dataset:<content-identity>

# acceptable — a defined namespace release
vocabulary:
  namespace: MONDO
  release: "2026-07-01"
```

A bare namespace with no release is **refused**: it is the drift §2.4 exists to
prevent.

**Resolution is separate from binding, and its outcomes are three distinct
things** — a distinction worth keeping precise, because world §5.1's vocabulary
is narrower than it is tempting to assume:

| outcome | when |
|---|---|
| `not-present` | the bound ontology **dataset has a world address** that the consulted index records, but the corpus holding it is absent — world §5.1's case exactly, and only this case |
| `not-available` | the dataset is identified but its **bytes are not held here**, so terms cannot be read — an artifact-availability fact, not an addressing one |
| `unknown` | the term is **outside the bound vocabulary** altogether, or the binding's namespace was never consulted — nothing was ever indexed to be absent |

A binding is well-formed in all three cases; none is an error, and none may
silently fall back to a different release. The distinction matters because
collapsing `not-available` into `not-present` would report an unindexed
artifact as though the index had spoken about it.

This also keeps ontologies exactly where the kernel already put them: `reads`
inputs that confer no eligibility (kernel §4.1), and `term` entities identified
by the ontology's own identifier, scoped external (world §3).

## 6. The compiled registry — closing substrate §12

Substrate §12 asks which of `science_model.profiles`' `KIND_DESCRIPTORS` and
`nodes`' `KindSpec` registry derives from the other. The question is closed by
**retiring the descriptors**, not by choosing a direction: two per-kind
sources of truth are the defect, and picking a winner leaves the loser as a
derived duplicate that can drift.

There is **one** authoritative source — the **profile source**: the declarative
`science` base contract together with the activated domain contracts. Every
per-kind artifact is compiled from it.

```text
science base contract  ─┐
                        ├─▶  ProfileSpec  ─┬─▶  KindSpec set ─▶ Registry.register()
active domain contracts ┘   (authoritative)└─▶  any further per-kind artifact
```

The two roles are distinct and should not both be called "authoritative": the
**contracts are the normative SSOT** — what a reviewer reads, what a version
names, what an amendment edits — while **`ProfileSpec` is the sole compiled
runtime profile**, the merged and validated in-memory form nothing authors by
hand. `KindSpec` is a further **compiled runtime product** derived from it.
`KIND_DESCRIPTORS` does not survive as a parallel
per-kind SSOT — under the clean-start ruling (ledger §0) it is not carried over
at all, so nothing is deprecated and no compatibility layer is created; the
descriptor concept simply has no successor. Any future artifact needing per-kind
information is compiled from `ProfileSpec` on the same terms, never authored
beside it.

**This is why the `nodes` delta is zero.** `Registry.register()` refuses a
duplicate kind name, and one `KindSpec` owns a kind's complete allowed-facet
set — so `Registry` as it stands cannot accept two contributors for one kind.
The compiled-product framing makes that irrelevant: merging happens *upstream*
of `register()`, and `Registry` only ever sees one fully-composed spec per
kind. No new `nodes` capability, no `STANDARD.md` bump, no TypeScript parity
cost — the strongest available position under substrate §2's pricing argument.

Facet-key namespacing needs no feature either: `STANDARD.md` imposes no
facet-key grammar and both implementations accept arbitrary string keys, so
`biology/gene-axis` survives the current canonical projection unchanged. The
only implementation obligation is **one shared parity fixture** pinning a
namespaced facet key through both projections, so the freedom stays deliberate
rather than incidental.

## 7. Corpus activation — the manifest profile

The corpus manifest pins the normative contract under which its facets and
kinds are legal:

```yaml
manifest_version: 2
corpus_id: ...
profile:
  science_contract: science:<contract-identity>
  domains:                        # a mapping, not a list
    biology: biology:<contract-identity>
forked_from: ...                  # optional, unchanged
```

**`domains` is a namespace-to-contract mapping, deliberately not a list.** A
list leaves two things undefined that a digest cannot tolerate: whether the same
namespace may appear twice, and whether order is significant. A mapping makes
duplicate namespaces unrepresentable rather than merely forbidden, and makes
ordering a non-question. The manifest is a **closed** shape: an unknown field,
a duplicate key, or a namespace whose contract identity is malformed is
**refused** at load, never ignored.

**The projection is defined through the existing canonical encoding.** The
manifest projection is the `science.identity.v1` canonical form (computation
§4.3's value contract — NFC strings, sorted object keys, type-preserving) of
the parsed manifest, taken over the **complete** closed field set. Defining it
through the existing encoding rather than a new one is what makes D5's
formatting-inert arm true by construction: YAML whitespace, key order, and
quoting style vanish at parse, so only a semantic change moves the digest.

**Why the manifest and not a node.** A singleton activation node would
technically enter corpus identity, but it would introduce bootstrap ordering
rules, singleton semantics, and a new category of control node — all to
preserve a manifest closure this design is free to correct deliberately.
Correcting the closure is the smaller change and the honest one.

**The amendment is two-part, and one part without the other reproduces the
defect.** Adding `profile` while leaving corpus-state identity defined over
`corpus_id` plus node identities would place the pin *outside* every check —
exactly world limitation 9's residue. So:

1. Packaging §6's closed field set is **superseded** to admit `profile`.
2. World §5's corpus-state identity is redefined over the **complete canonical
   manifest projection** together with the sorted node identities.

The projection covers the **whole closed manifest**, not selected fields.
Hashing a chosen subset would recreate limitation 9 for every field the
manifest is later allowed to grow.

## 8. What enters identity, and what enters belief

This is the load-bearing chain, and each level answers a different question:

```text
each corpus manifest pins its profile contracts
        ↓
corpus-state identity includes the canonical manifest projection
        ↓
each semantic derivation includes every profile contract it actually interprets
        ↓
the receipt additionally names the exact implementation executed
```

**Why the third level is mandatory.** Corpus-state identities live in receipts,
not in belief (world §5). If the chain stopped at level two, biology 0.4 could
reinterpret `gene-axis` without changing facet bytes, without changing
assessment bytes, and without moving `belief_input_digest` — two different
beliefs behind one digest, which is precisely what kernel §5.1's G3 guarantee
forbids. So **kernel §5.1's closure gains a member**: every profile contract the
derivation actually interprets, alongside the existing belief-policy version,
which is the exact precedent — a versioned rule entering the computed view as
an input rather than being stamped on records.

**The `science` base contract is unconditional; domain contracts are
conditional.** These are not the same rule, and collapsing them reopens the
defect.

`science_contract` governs the kernel kinds, the relation signatures that close
belief, the eligibility predicate, and the unnamespaced base-profile facets. A
Science semantic derivation therefore consults it **always** — interpreting
`assessment`, `dataset`, or a relation signature *is* consulting it, whether or
not the closure happens to read a base-profile facet. Making its membership
conditional on a facet read would let a successor contract reinterpret
`assesses` or the eligibility predicate itself without moving G3, which is the
original defect at a still more load-bearing place than §3.4's
`empirical-observation`.

So the consulted set is a set of **contract identities** built by two different
rules:

- **Exactly one `science_contract`, always.** Every Science semantic derivation
  includes it unconditionally. There is no closure walk that can omit it and no
  derivation that does not consult it.
- **Each domain contract, only if actually read.** A domain activated in a
  manifest but never interpreted does **not** enter the digest. Membership is
  computed rather than declared: walk the derivation's closure, collect the
  namespace of every facet it reads, and resolve each namespace to a contract
  identity by §8.1.

Belief therefore moves when the base contract moves, and when a domain contract
it actually used moves — not when an unrelated domain is upgraded.

### 8.1 Cross-corpus agreement, and why W5 survives

A derivation's closure can span corpora, so "the manifest" is not well defined
without a rule — and the obvious reading breaks a banked guarantee. **W5
requires that moving an entity between corpora changes only its location**, and
asserts specifically that moving a dataset in the producers map leaves
`belief_input_digest` unchanged *even though both corpus-state identities
moved*. If corpus A pinned `biology@0.3` and corpus B pinned `biology@0.4`,
then moving a dataset from A to B would change the consulted contract and move
belief — a pure relocation with an epistemic consequence. W5's own note records
that two successive revisions of the snapshot identity already violated this
row; this would have been the third.

**The rule, which removes the possibility rather than trading it off:**

1. **Resolution.** A facet namespace resolves to the contract identity pinned by
   the manifest of the corpus holding the node the facet sits on. The
   `science_contract` resolves the same way, per corpus.
2. **Agreement.** Across one derivation's closure, every consulted namespace
   must resolve to **exactly one** contract identity. Two corpora in one closure
   pinning different identities for one namespace is **refused**, not merged,
   not preferred-by-recency, and never silently resolved. **`science_contract`
   agreement is required unconditionally** — every corpus in the closure must
   pin the same one, whether or not any base-profile facet is read, since §8
   makes the base contract an unconditional member.
3. **Move and merge.** Moving or merging a node into a corpus whose profile
   pins a **different** identity for any namespace the node's facets use is
   **refused** at the write boundary. For a **Science node**, the receiving
   corpus must pin the same `science_contract` regardless of which facets the
   node carries — a node with no domain facets at all is still governed by the
   base contract, so relocation across base-contract identities is refused too.

Rule 3 is what makes rule 2 satisfiable in practice and what preserves W5
exactly: a *permitted* move never crosses a contract boundary, so a permitted
move never changes the consulted set, so `belief_input_digest` is unchanged —
W5 holds unamended. What was previously an invisible digest change becomes a
visible refusal at the moment of the move. Upgrading a domain across a world is
therefore a deliberate, coordinated act over the corpora that share the
namespace, not a per-corpus drift that surfaces later as a belief anomaly.

**Level four is the existing normative-binding pattern**, not a new one: the
manifest pins *meaning*, and a check receipt names the exact implementation
that executed — the same split 5b makes between a rule's identity and the
implementation that ran it.

## 9. Organization in the `science` repository

```text
science/
  src/science/          # kernel kinds, cross-node policy, the compiler
  domains/
    biology/
      DOMAIN.yaml       # contract identity, version, namespace
      schema/           # facet contracts
      vocab/            # vocabulary adapters and bindings
      skills/
  practices/
    statistics/
      PRACTICE.yaml
      skills/
  docs/  tests/
```

Three organizing rules, each aimed at a specific failure observed in
`proto-science`:

- **Generated artifacts never live in a source tree.** The 53 `science-*`
  generated skills are build output and belong in a build directory, not beside
  hand-authored material where the two become indistinguishable.
- **External provenance is retained.** `sources.yaml`'s per-source title,
  authors, license, upstream ref, and last-checked date is a genuinely good
  mechanism and survives, scoped per domain or practice rather than globally.
- **`aspects/` folds into `practices/`.** Causal modeling, computational
  analysis, hypothesis testing, and software development are methods, not
  fields; keeping a second parallel taxonomy is how the first one drifted.

Per ledger §5, these are **directories now**. A domain becomes a distribution
when there is an observed second consumer, and the layout is chosen so that
promotion is a move rather than a rewrite.

## 10. Guarantees, and how each is tested

New table, prefix **D**, certified by mutation per the estimator doctrine.
Rows D5, D6 and D7 depend on the banking amendment set (header) having landed;
until then the banked closures stand and those rows are pending, not failing.
D7's first arm is W5's own assertion, restated here because this design is
what must not break it.

| # | guarantee | mutation test |
|---|---|---|
| D1 | `nodes` assigns no domain semantics | assert `nodes` ships **no domain contract, schema, validator, or vocabulary adapter**, and that **no `nodes` API accepts** a domain, contract, or vocabulary argument; assert every domain-flavoured string in the `nodes` tree is **opaque** — its normative fixtures already carry `bio-axes` and `HGNC:7296` (`fixtures/gene_phf19.*`) purely as example payload the kernel never interprets, and that is **conforming, not a violation**; **negative:** add a `nodes` code path that reads a facet key's namespace and behaves differently for `biology/` → refused, since assigning meaning to a namespace is exactly what this row forbids. A grep for domain *names* is **not** the test and would fail against a conforming tree |
| D2 | Interpretation is separable from identity | add a `biology/gene-axis` facet to a dataset node and assert the **dataset address is unchanged** (bytes did not move) while **node content identity and corpus-state identity both move**; correct the facet's payload and assert the same asymmetry again; **negative:** change the bytes and assert a **different dataset** is minted with no facet involvement |
| D3 | A vocabulary binding is exact or refused, and its three unresolved states stay distinct | bind `vocabulary: {namespace: MONDO}` with no release → **refused** at contract load; bind a namespace+release and a held-dataset content identity → both **accepted**; then assert the three outcomes are **not collapsed** (§5): index the bound dataset's world address but make its corpus absent → **`not-present`**; identify the dataset but hold none of its bytes here → **`not-available`**, never reported as `not-present`; query a term outside the bound vocabulary → **`unknown`**. In every case assert the binding remains **well-formed**, no error is raised, and **no fallback to another release** occurs |
| D4 | `ProfileSpec` is the only per-kind source; `KindSpec` is compiled | have `science` and a domain both contribute facets to `dataset`; assert exactly **one** `KindSpec` is registered for it carrying the union, that `Registry.register()` is called **once** per kind, and that no duplicate-registration error is reachable; mutate a domain contract and assert the compiled spec changes with **no `nodes` code change**; assert **no second authored per-kind artifact exists** — nothing plays `KIND_DESCRIPTORS`' old role beside `ProfileSpec`, and any further per-kind artifact is compiled from it; assert a namespaced facet key round-trips **identically** through the Python and TypeScript canonical projections (the one shared parity fixture this design adds) |
| D5 | The manifest pin is inside corpus-state identity, over a canonical projection | reformat `corpus.yaml` — whitespace, key order, quoting style — and assert corpus-state identity is **unchanged**; **reorder the `domains` mapping** and assert it is **unchanged** (ordering is inert by construction, since the projection sorts object keys); change a pinned contract identity and assert it **moves**; change any other non-node file and assert it is **unchanged**; assert the digest covers the **complete** canonical projection by adding a new permitted field and confirming it participates without a further amendment; **refusals:** an unknown field, a duplicate `domains` key, and a malformed contract identity are each **refused at load**, never ignored and never digested |
| D6 | Every consulted profile contract enters belief; activated-but-unconsulted ones do not | derive belief over an assessment reading `biology/gene-axis`, bump the biology contract, and assert `belief_input_digest` **moves**; activate an unrelated domain and bump *it*, and assert the digest is **unchanged**; **the base-contract arm:** bump the **`science` base contract** in a way that reinterprets the **unnamespaced** `empirical-observation` facet (§3.4) and assert the digest **moves** — a consulted-set rule collecting only *domain* namespaces would miss exactly this, at the eligibility hinge; **the unconditional arm:** take a derivation whose closure reads **no base-profile facet at all**, bump the base contract so it reinterprets a **kernel kind or a relation signature** (`assessment`, `dataset`, `assesses`), and assert the digest **still moves** — membership of `science_contract` is unconditional, so no facet-triggered walk may be able to omit it; **negative — the defect this closes:** reinterpret a facet, kind, or signature in a successor contract without changing any facet byte or assessment byte and assert the digest **still moves**, so two beliefs can never share one digest |
| D7 | Contract agreement holds across a derivation, and W5 survives unamended | **W5 preservation:** move a dataset that appears in the producers map between two corpora pinning the **same** contract identities and assert `belief_input_digest` is **unchanged** even though both corpus-state identities moved — the row two prior snapshot-identity revisions violated; **agreement:** construct a closure spanning corpora pinning **different** identities for one namespace and assert the derivation is **refused**, never merged, never resolved by recency; **move refusal:** attempt to move a node whose facets use `biology/` into a corpus pinning a different `biology` identity and assert the **write boundary refuses**, so the belief-moving case is unreachable by relocation rather than tolerated; **the base-contract arms:** construct a closure spanning corpora that agree on every domain namespace but pin **different `science_contract`s** and assert the derivation is **refused** even though no base-profile facet is read; and attempt to move a Science node carrying **no domain facets whatsoever** into a corpus pinning a different `science_contract` and assert the move is **refused** — base-contract agreement is not conditional on facet content |
| D8 | Domain contributions compose without collision | two domains contributing same-named facets in **different** namespaces → both compose; two contributions to one namespaced facet key → **refused** at compile, never last-writer-wins; a domain attempting to define a **kernel kind** or a relation signature → **refused** |
| D9 | Practices carry no vocabulary | a `PRACTICE.yaml` declaring a vocabulary binding or a facet schema → **refused**; assert a practice contributes **nothing** to the compiled registry and therefore can never move `belief_input_digest` |
| D10 | Facets stay facets until the promotion trigger | assert no API retracts, supersedes, or attributes an individual facet payload — the three operations that define the trigger are **unspellable** over facets; assert correcting an interpretation is an ordinary node revision leaving no record of the prior claim, and that this is the stated cost (limitation 3) of not yet promoting |

## 11. Limitations

1. **Meaning can drift inside a validating revision.** A contract revision may
   change what a facet *means* while every stored payload still validates. The
   change is visible at corpus granularity — contract identity is
   content-derived, so the pin moves, corpus state moves, and every consulted
   derivation's digest moves (D6) — but it is **not adjudicated per node**.
   Nothing says which nodes' meanings actually changed. This is the same shape
   as the kernel's semantic-identity hazard and is stated, not closed.
2. **"Consulted" must be computed, and the computation is load-bearing.** D6's
   guarantee is only as good as the closure walk that collects facet
   namespaces. An under-collecting walk silently omits a contract from the
   digest, which is exactly the defect §8 exists to prevent — and it would fail
   *open*, not closed. The **unnamespaced** base-profile facets are the sharpest
   case: a walk keyed on the presence of a namespace separator would drop the
   `science` base contract entirely while looking correct on every domain facet,
   which is why §8 states the empty namespace explicitly. This needs its own
   conformance oracle when 5b's contract cut lands.
3. **Correcting an interpretation leaves no record of the prior claim.** While
   interpretations are facets, a corrected payload is an ordinary revision: the
   previous interpretation is simply gone from the node. It is recoverable only
   from the mutation log, and only to the extent that log reaches — a
   boundary-mediated correction is registered, while a raw edit is detectable
   at replay rather than recorded, under that design's anchor limitations. So
   "recoverable from the log" is a qualified claim, not a guarantee. That is
   the accepted cost of not promoting early (§2.3), and the first time it bites
   is the promotion trigger firing.
4. **Domain contract authorship is unverified.** That a contract's schema
   faithfully describes its field is authored, not checked — the same class as
   kernel limitation 8's acquisition boundary.
5. **No domain exists yet.** Every mechanism here is unexercised. The first
   real domain is expected to move details, and the boundary rulings (§2) are
   what this design commits to — not the file layout.
6. **The domain/practice line is a judgment at the margin.** The vocabulary
   test (§3.5) is mechanical, but whether a body of expertise *should* carry a
   vocabulary is not, and misfiling is cheap to fix only before consumers pin
   it.

## 12. Open questions

- **Domain contract versioning policy.** What constitutes a breaking change to
  a facet contract, and whether contract identity being content-derived is
  sufficient or a declared compatibility range is also needed. Interacts with
  5b's versioning rules and should be settled with them.
- **Parity for domains.** Whether a domain must ship Python and TypeScript
  validators or may be Python-first with parity declared per contract. The
  declarative form makes parity cheap but does not make it automatic.
- **Distribution.** Where domain contracts are published once they leave the
  repository, and whether a domain is ultimately a package, a corpus, or both.
  Ledger §5's split test governs, and nothing forces the answer yet.
- **The predicate vocabulary.** Kernel limitation 4 records nine predicates,
  declared inadequate, with no owner and no extension rule — while `predicate`
  feeds proposition semantic identity. Whether the predicate vocabulary becomes
  a domain contract like any other is the obvious question this design raises
  and does not answer.
