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
kernel **§5.1**'s G3 closure gains a member — **every domain contract the
derivation actually interprets**; substrate **§12**'s kind-SSOT question
**closes** (neither derives from the other; both compile); substrate **§6.1**'s
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
temporal record that a stamp would duplicate already exists twice: the mutation
log registers every change with `corpus.yaml` inside the registered surface,
and receipts already name the exact implementation that executed a check.

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

> **Reviewer note.** This correction is *derived* from §2.2 rather than
> separately ruled during design discussion. It is the single amendment here
> that changes a banked placement without an independent argument having been
> requested, and it should be confirmed or rejected explicitly rather than
> adopted by adjacency.

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
prevent. Resolution is separate from binding — a binding is well-formed whether
or not the ontology dataset is present here, and an absent one yields
`not-present` rather than an error, matching world §5.1. This also keeps
ontologies exactly where the kernel already put them: `reads` inputs that
confer no eligibility (kernel §4.1), and `term` entities identified by the
ontology's own identifier, scoped external (world §3).

## 6. The compiled registry — closing substrate §12

Substrate §12 asks which of `science_model.profiles`' `KIND_DESCRIPTORS` and
`nodes`' `KindSpec` registry derives from the other. **Neither.** Both are
compiled from a common source:

```text
science base profile  ─┐
                       ├─▶  compiler  ─▶  KindSpec set  ─▶  Registry.register()
active domain contracts┘
```

`KindSpec` is the **compiled runtime product**, not a source of truth. The
descriptors and the activated domain contributions are the authoritative
inputs, and the compiler merges contributions per kind before registration.

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
  domains:
    - biology:<contract-identity>
forked_from: ...   # optional, unchanged
```

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
manifest pins the normative domain contract
        ↓
corpus-state identity includes the canonical manifest projection
        ↓
each semantic derivation includes every domain contract it actually interprets
        ↓
the receipt additionally names the exact implementation executed
```

**Why the third level is mandatory.** Corpus-state identities live in receipts,
not in belief (world §5). If the chain stopped at level two, biology 0.4 could
reinterpret `gene-axis` without changing facet bytes, without changing
assessment bytes, and without moving `belief_input_digest` — two different
beliefs behind one digest, which is precisely what kernel §5.1's G3 guarantee
forbids. So **kernel §5.1's closure gains a member**: every domain contract the
derivation actually interprets, alongside the existing belief-policy version,
which is the exact precedent — a versioned rule entering the computed view as
an input rather than being stamped on records.

**Scope: consulted, not merely activated.** A domain activated in the manifest
but never interpreted by a given derivation does **not** enter that
derivation's digest. Belief moves when the rules it actually used move, not
when an unrelated contract is upgraded. Determining the consulted set is
mechanical rather than declared: walk the derivation's closure, collect the
namespaces of the facets it reads, and map each namespace to the contract
identity the manifest pins.

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
Rows D5 and D6 depend on the banking amendment set (header) having landed;
until then the banked closures stand and those rows are pending, not failing.

| # | guarantee | mutation test |
|---|---|---|
| D1 | Domain content never enters `nodes` | grep the `nodes` tree for any domain namespace, ontology name, or vocabulary term → **absent**; add a domain and assert `nodes`' `STANDARD.md` version, its conformance fixtures, and its TypeScript surface are **unchanged**; assert no `nodes` API accepts a domain, contract, or vocabulary argument |
| D2 | Interpretation is separable from identity | add a `biology/gene-axis` facet to a dataset node and assert the **dataset address is unchanged** (bytes did not move) while **node content identity and corpus-state identity both move**; correct the facet's payload and assert the same asymmetry again; **negative:** change the bytes and assert a **different dataset** is minted with no facet involvement |
| D3 | A vocabulary binding is exact or refused | bind `vocabulary: {namespace: MONDO}` with no release → **refused** at contract load; bind a namespace+release and a held-dataset content identity → both **accepted**; make the bound dataset absent and assert the binding stays **well-formed** with terms `not-present`, never an error and never a silent fallback to a newer release |
| D4 | `KindSpec` is a compiled product, not a source | have `science` and a domain both contribute facets to `dataset`; assert exactly **one** `KindSpec` is registered for it carrying the union, that `Registry.register()` is called **once** per kind, and that no duplicate-registration error is reachable; mutate a domain contract and assert the compiled spec changes with **no `nodes` code change**; assert a namespaced facet key round-trips **identically** through the Python and TypeScript canonical projections (the shared parity fixture) |
| D5 | The manifest pin is inside corpus-state identity | reformat `corpus.yaml` — whitespace, key order — and assert corpus-state identity is **unchanged**; change a pinned contract identity and assert it **moves**; change any other non-node file and assert it is **unchanged**; assert the digest covers the **complete** canonical manifest projection by adding a new permitted field and confirming it participates without a further amendment |
| D6 | Consulted contracts enter belief; activated ones do not | derive belief over an assessment reading `biology/gene-axis`, bump the biology contract, and assert `belief_input_digest` **moves**; activate an unrelated domain and bump *it*, and assert the digest is **unchanged**; **negative — the defect this closes:** reinterpret `gene-axis` in a new contract without changing any facet byte or assessment byte and assert the digest **still moves**, so two beliefs can never share one digest |
| D7 | Domain contributions compose without collision | two domains contributing same-named facets in **different** namespaces → both compose; two contributions to one namespaced facet key → **refused** at compile, never last-writer-wins; a domain attempting to define a **kernel kind** or a relation signature → **refused** |
| D8 | Practices carry no vocabulary | a `PRACTICE.yaml` declaring a vocabulary binding or a facet schema → **refused**; assert a practice contributes **nothing** to the compiled registry and therefore can never move `belief_input_digest` |
| D9 | Facets stay facets until the promotion trigger | assert no API retracts, supersedes, or attributes an individual facet payload — the three operations that define the trigger are **unspellable** over facets; assert correcting an interpretation is an ordinary node revision leaving no record of the prior claim, and that this is the stated cost (limitation 3) of not yet promoting |

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
   *open*, not closed. This needs its own conformance oracle when 5b's contract
   cut lands.
3. **Correcting an interpretation leaves no record of the prior claim.** While
   interpretations are facets, a corrected payload is an ordinary revision:
   the previous interpretation is simply gone from the node, recoverable only
   from the mutation log. That is the accepted cost of not promoting early
   (§2.3), and the first time it bites is the promotion trigger firing.
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
