# World address — the §4.1 ruling

**Status:** Ruled 2026-08-08. Closes **F9** and re-litigation docket **§4.1**
(`2026-08-05-review-disposition-and-conformance-cut-1.md`). Upholds basis-derived
addressing, and rules four things the docket's binary could not reach: a
generalized basis rule, derived labels in place of stored aliases, coreference as
a graded claim in place of structural merge, and an eleventh kernel kind to carry
it. **Un-couples F10**, which the docket folded into this ruling on a coupling
that does not hold, and returns it to the docket as its own item.

Amends: world addressing §2.1, §3, §4.2–§4.4, §5, §5.1, §7, §8, §9; kernel §4.4
and **G3**; formal model §2.1, §3.4, §6.5 and its W coverage map; the
domain-extension boundary; the normative contract's row count; the adoption
ledger; the README; three contributor-guide pages; and the corpus guard's `W`
table. Adds **W14–W16**, taking the frozen corpus to **138 rows** across eleven
tables, and the kernel to **eleven kinds**. The full site list, and what is
deliberately *not* amended, is §8.

---

## 1. What this rules, and what it does not

Docket §4.1 asks whether a world entity's stored address should be derived from
its identity basis, or should stay a nominal `kind:slug` made unique at the write
boundary with the basis demoted to a coreference check.

This document answers that question, and then answers a larger one the docket did
not pose, because the honest answer to the first is *"neither side's framing
survives contact with §4.2."*

**Not ruled here.** Docket §4.2 (tamper log versus git) and §4.3 (normative
contract strata) are untouched. §4.2 is explicitly free to defer — every L row is
gated on `atoms` A7–A8 regardless. §4.3's substance is already settled by its own
table; what remains there is execution.

---

## 2. The docket asked the wrong question

> **The binary is a category error, and the corpus has already named this one.**
> World §4.2 opens: *"A basis assigned by category rather than per kind produced
> three defects in the first draft, so each of the eight kernel kinds is ruled
> individually."* §4.1's binary is that same move, one level up — a scheme
> assigned to the world rather than to its kinds.

Applied per kind, the alternative does not have a subject. Of the ten world
kinds, **eight have no human-typed slug to promote into an address**:

| kind | basis | is there a slug to promote? |
|---|---|---|
| `proposition` | `I_claim` (kernel §4.1, typed since 2026-08-05) | no — and it is built and frozen in cut 1 |
| `run` | content identity of the execution closure | no |
| `verification` | content identity over the ordered closure | no |
| `analysis-spec` | content identity, frozen pre-run | no |
| `assessment` | key over (spec, run, proposition) | no |
| `instrument-certification` | content identity over the certification closure | no |
| `retraction` | content-derived over target, reason, grounds, actor, event token | no |
| `dataset` | content identity | no — provider identifiers name a *programme* |
| `source` | normalized external identifier | **yes** — the citekey |
| *(handles generally)* | — | only on `source`, and on `dataset`'s provider fields |

To run the alternative on the first eight you would have to **mint** nominal
slugs for kinds that have none, purely to have something for boundary uniqueness
to enforce over. That is not a simplification; it is a second identity system
laid beside a sufficient one.

And the collision evidence sits entirely in the last two rows. §1.3's three
`paper:` pairs — `Chen2023`, `Liu2020`, `Shi2025` — are `source` handles. §1.1's
two dataset rows are provider programmes. The docket's strongest empirical case
applies to exactly the kinds this ruling handles by **not storing handles at
all** (§4).

> **The review's surviving point, kept.** F9's sharpest observation is not
> defeated by the above and is adopted: **W1** and **W2** test that the basis was
> *chosen and encoded correctly*, which follows from `encode ∘ πᵢ` being injective
> on admissible values together with domain separation and collision resistance.
> They do not test what the *address scheme* adds beyond that. **W14** is added to
> close it (§10).

**Verdict.** Basis-derived addressing is upheld. F9 is closed.

---

## 3. The generalized basis rule

World §4.2 rules the basis per kind and states the missing-basis rule only for
`source` and `dataset`. It generalizes, and stating it generally is what makes
the per-kind table a rule rather than a list.

> **Rule (2026-08-08).** Every addressable world entity has the basis declared
> for its kind: an **intrinsic** basis, or an identifier from an **accepted
> authority**. If that basis is missing, the record is a project-scoped
> **curation note** — not a weakened world entity.

Two clauses carry over unchanged from §4.2 and now bind all eleven kinds: the
refusal and the note are **two operations**, never a silent coercion; and **no
fallback basis is derived at any point**, because a fabricated identity is
indistinguishable from a real one everywhere downstream.

One clause is **new**, and it closes a back door §4.2 left open:

> **A curation note cannot be the target of a semantic reference.** Notes are
> belief-inert prose, which constrains what a note can *do* to belief but not
> what may *point at* one. Without this clause an unbased record is reachable
> anyway — through a relation endpoint, a facet ref, or a view — which is the
> refusal being routed around rather than enforced.

**Where an accepted identifier does not exist**, the sequence is: retain the
record as a project-scoped curation note; prevent semantic references to it;
batch it into the migration queue; and mint a **governed local identifier** only
if recurring real cases prove external-only coverage insufficient. The local
identifier is deliberately not designed here — the trigger is recorded so the
option is not lost, and nothing is built for a case that has not occurred.

---

## 4. Labels are derived, never stored

> **Rule.** The stored reference is the **canonical identifier**. A **label** is
> computed on read and is never stored as world content. **Search terms** are
> authority-provided synonyms. A label never becomes a persistent world alias.

This is not new machinery. The formal model already banks it for `proposition`,
in the split that separates `render(Claim, Locale)` — *"a deterministic function
of the typed form, the consulted vocabulary, and an explicit locale — never an
ambient one"*, **not stored, computed on read** — from `display_statement`,
authored, optional and identity-inert. This ruling generalizes that split to
every kind, and reuses the `VocabularyBinding` + `ResolutionSnapshot` pair cut 1
already ships, whose D3 arms test exactly the resolution discipline it needs.

### 4.1 The renderer is per value, not per kind

An earlier draft of this ruling stated two *kind* families and was wrong:
`dataset` is intrinsically addressed by content identity, and only its
`programme` / `release` fields carry authority identifiers. The rule is over
values:

| value | renderer |
|---|---|
| an **authority identifier** | `preferred_label(identifier, pinned_authority_release)` |
| a **record** | kind-specific rendering from immutable record content, **recursively rendering any authority identifiers it holds** |

`source` is the pure first case — its basis *is* an authority identifier.
`dataset` is the second, holding authority identifiers in its fields.
`proposition` is the second and is the worked example already banked, consulting
vocabulary for its term labels only.

### 4.2 Resolution is against a pinned snapshot

Authority resolution uses a **pinned local snapshot, never a live network
lookup**. Builds stay reproducible, and an authority update becomes an explicit
amendment rather than a silent retroactive change. This is the ruling world §4.2
already makes for vocabulary, applied to labels.

**What CI can decide from a pinned snapshot:** two records carrying the same
canonical identifier; a non-canonical spelling; an identifier in the wrong
namespace or for the wrong kind; a label differing from the authority's preferred
label; an authority's explicit equivalence or replacement declaration; a record
missing its required identifier.

**What CI cannot decide:** that "DepMap" and "Cancer Dependency Map" denote one
thing. That is establishable only if both resolve to one identifier, or the
pinned authority lists one as a synonym of the other. Inference from strings
alone is refused.

**Fuzzy matching is candidate generation, never a decision.** A fuzzy label match
enters the review queue; authority evidence normalizes **form only**; missing
evidence leaves the record unresolved. Fuzzy matching never decides identity.

### 4.3 What this deletes

The **alias facet** on nodes, the **alias map** (one of the world index's four),
and the alias arm of the `ambiguous` resolution state. World §2.1 rejected three
alternatives for *where aliases live* — adding them to `nodes`, storing them only
in the index, reusing `deprecated_ids` — and never considered **not storing
them**. That is the identical defect F9 charges against §4, recurring one level
down, and it is recorded here rather than quietly repaired.

---

## 5. Coreference is a graded claim

**Same-basis coreference is unchanged and stays mechanical** — W2, *"a shared
basis establishes coreference mechanically … no curator assertion required."*
Nothing below touches it.

**Different-basis coreference** — a corrected identifier, an authority
`replacedBy`, "these two records are one work" — is where an attester enters, and
where structural merge used to fire.

> **Rule.** Different-basis coreference is an **attributed, additive attestation
> carrying a signed stance**. The pair's balance is **derived**. Nothing
> collapses: both records stand, both addresses persist, and no reference is
> retired or rewritten. **Structural merge is retired.**

### 5.1 `coreference-attestation` — the eleventh kernel kind

```text
coreference-attestation
  endpoints    sorted canonical pair
  stance       +1 | -1
  actor
  grounds
  event_token
```

**Basis:** content-derived over (endpoints, stance, actor, grounds, event token)
— the `retraction` shape exactly, which world §4.2 records as *"a content-derived
basis over target, reason, grounds, actor, and a minted event token."*

Sorting the endpoint pair makes `{A, B}` one identity regardless of authoring
order. The event token keeps two genuinely distinct attestation *events* distinct,
as the occurrence token does for `run`.

**Rejected realizations, recorded so they are not re-proposed:**

- **Extending relation instances.** An edge cannot carry attribution, grounds, a
  stance and a derived balance. Giving it those makes it a node with worse
  ergonomics.
- **Reusing `source-assertion`.** Its stance is about a *proposition*, and its
  role-typing is what keeps literature→belief unspellable — the corpus's first
  must-survive item. Overloading it trades a structural guarantee for a saved
  kind.
- **A generic attestation framework.** Larger than the thing it would generalize,
  with exactly one instance. YAGNI.

All three are larger changes than the eleventh kind.

### 5.2 Balance is derived, and duplication cannot manufacture it

```text
balance(A, B) = Σ stance over distinct (endpoints, stance, actor, grounds)
```

The event token preserves event provenance and is deliberately **outside** the
deduplication key: repeated identical submissions must not manufacture weight.
A positive standing balance activates the semantic coreference edge; **zero or
negative does not**.

**Unit weight, and no attester privilege.** Every attestation counts ±1. A human
attester and an agent attester carry identical weight, and the record carries
`actor` so that reliability becomes *measurable* rather than assumed. This is the
belief policy's ruling applied to attesters: `science.belief.v1` fixes `V = ℤ`
with unit weight so a value is a signed evidence balance and never odds, and
weighting by study design or precision is **blocked on ρO3, not deferred by
choice**. Privileging an attester class by category before the data exists is the
same arm-waving, relocated.

**A negative attestation offsets; it does not retract.** Both records stand and
both remain recorded. `retraction` enters only if invalidating an *individual*
attestation ever becomes necessary — the trigger is recorded, the machinery is
not built.

### 5.3 Closure is a query-layer operation

> **Rule.** Coreference closure **never rewrites a stored reference, an identity,
> or a belief input.** Retraction targets, `π_claim` positions,
> `belief_input_digest` members and every content-identity basis read **exact
> addresses**, always. Closure expands **queries**.

This is load-bearing in two directions.

**It preserves the property retiring merge was meant to buy.** Retraction targets
stay exact-address references. If closure rewrote them, coreferencing two
retractions would recreate exactly the cycle structural merge could close — the
hazard W4 refuses today — through a new route.

**It keeps coreference out of belief.** A `dataset` coreference could otherwise
reach `belief_input_digest` through lineage and the producers map. Under the rule
it cannot, because belief reads exact addresses.

> **Correction to an earlier draft of this ruling, recorded in place.** A draft
> claimed that retiring merge upgrades the retraction graph's acyclicity from
> **RF†** to **US†**. That is an overclaim. Retiring merge makes the
> *merge-created cycle route* unspellable; it does not make the DAG invariant
> unconstructible. Bundle import still validates acyclicity over the bundle
> **union the resolved world context** and refuses one admitting no topological
> order (ρA9), **M3** still owns that oracle, and a raw write remains auditable
> corruption. One route closes. The invariant still needs checking.

### 5.4 `consolidate` — the duplicate-location exit

Retiring merge would otherwise leave §5's `duplicate location` state with no
resolution, since world §5 records its only exit as *"resolved by an authored
merge."* Duplicate location is **one identity in two corpora** — same basis, same
address, same `uid`. That is storage duplication, not coreference, and it needs
its own named operation rather than a share of a retired one.

> **`consolidate`.** Requires **one canonical address**. Reconciles content and
> location, selecting continuity where necessary. **Unions outgoing relations**
> and **preserves divergent lineage bases**. Performs **no redirect and no
> inbound rewrite** — no address retires, so nothing needs rewriting.

W4's equal-basis arm already described an operation of this shape without naming
it: *"the merge succeeds, the retraction's content identity is unchanged, and `R`
is not rewritten and not re-minted."* Naming it separates a storage repair from
an identity claim, which is the distinction the single word "merge" was hiding.

---

## 6. Programme and release are identifiers, not entities

A held dataset carries `programme` and `release` as **authority identifiers in
its own record**. Searching "DepMap" resolves against the pinned snapshot to an
identifier, not to a node. The only node is the held dataset.

```text
programme        authority identifier   (a field)
release/version  authority identifier   (a field, when the authority issues one)
held dataset     content identity       (the entity)
```

**The three levels must never be collapsed by a normalizer.** "Cancer Dependency
Map", "DepMap 24Q4" and a downloaded matrix are not interchangeable — this is
§1.1's observed confusion, and world §4.2 already refuses it (*"a provider
identifier names a programme, not data"*). Keeping the levels as distinct fields
is what makes the refusal structural instead of a check.

**What this costs:** a claim *about* a release — "24Q4 supersedes 23Q2" — is not
expressible, because a release is not an entity. Accepted. Promoting the levels
to entities would cost a twelfth and thirteenth kind for a capability nothing
currently needs.

---

## 7. F10 is un-coupled and returns to the docket

The docket folds F10 — *"world §5's receipt apparatus is 42% of the document and
its evidence expires"* — into F9, with the disposition *"its fate follows the
address ruling."*

**It does not follow.** §5's bulk is the producer snapshot, the coverage
declaration, the derivation receipt, the
`malformed` / `unresolvable` / `validated` / `refuted` evaluation lattice, and the
`checked` / `unchecked` / `contradicted` snapshot reduction. Those exist because:

1. corpora **federate**, so a corpus can be absent;
2. the producers map is a **belief input** — kernel §5.1 digests the producer
   snapshot's semantic identity;
3. a **derived enumeration needs completeness evidence**, or a snapshot that is
   merely hashed proves nothing about what it omitted.

All three hold identically under any address scheme. What *is* downstream of the
address scheme is the alias map, the alias arm of `ambiguous`, and W9 — and §4
deletes those on grounds that have nothing to do with receipts.

> **Disposition.** F10 is **not closed by this ruling** and is **not folded into
> F9**. It returns to the docket as its own item, with its question restated
> fairly: *is a receipt apparatus whose evidence expires on the next commit worth
> 42% of the world design?* That is live. It is not this question, and answering
> this one told us nothing about it.

The docket's cost list for F9 is corrected in the same move: it priced
basis-derived addressing at the address/alias duality, the alias map, the fourth
resolution state, W9, §4.4's rename machinery **and §5's receipt apparatus**. The
last item was never F9's to pay.

---

## 8. What this amends

| site | amendment |
|---|---|
| world §2.1 | the alias facet and the alias map retire; the fourth rejected alternative — not storing handles — is recorded |
| world §3 | tier table gains `coreference-attestation` |
| world §4.2 | basis table gains `coreference-attestation`; the missing-basis rule generalizes (§3 here); `dataset`'s provider identifiers stop being "aliases" and become authority-identifier **fields** |
| world §4.3 | structural merge retires; §5.4's `consolidate` takes its duplicate-location role; "curator assertion" → attester |
| world §4.4 | the middle case **splits**, and the boundary moves from a judgement about *works* to a fact about *identifiers*: a **mis-transcribed** basis is still a rename with `uid` preserved and the old address in `deprecated_ids`; an **authority replacement** is a coreference attestation; a genuinely different work is unchanged. *"Only a person can say"* is withdrawn here |
| world §5, §5.1 | four derived maps become three; `ambiguous` leaves the resolution table and the refusal relocates to search time |
| world §5 conflicts | `duplicate location` exits via `consolidate`; "ambiguous alias" → "ambiguous search term" |
| world §7 | W4, W6, W9 restated; **W14–W16** added |
| world §8 | limitation 3 retires; **3a–3c** replace it |
| world §9 | records the machinery this design proposed and will now **not** build, so the world layer's scope is not over-estimated from the banked text |
| kernel §4.4 | kind inventory and totals: ten → eleven |
| kernel **G3** | the alias mutation is **deleted without replacement** — location already tests OInv, G7 tests display invariance, and an authority-release bump is **not** a substitute because a consulted release may legitimately move the digest under **D6** |
| formal model §2.1 | heading count, and the player table gains a `coreference-attestation` row |
| formal model §3.4 | observational invariance drops **alias** from its declared inert dimensions — there is no stored alias to be inert in. The rows it cites are untouched |
| formal model §6.5 | the `render` row generalizes to a per-**value** renderer; "authored **by a human**" → attributed |
| formal model W map | W9 restated; W14–W16 added |
| domain boundary §1, §5 | "the ten kernel kinds" ×2 → eleven |
| normative contract | the frozen-row count: 135 → **138** |
| adoption ledger | **artifact 11** (the pinned authority snapshot, owed and undesigned); a §0 note carrying the kind count, the merge retirement and the F9/F10 disposition |
| README | the design table gains this document; the frozen-row count → 138 |
| guide `foundations.md` | the kind inventory gains `coreference-attestation`; heading, count and one inbound anchor follow |
| guide `identity-world-and-change.md` | `sources`; "Current state" gains the ruling; the W-range reference → W1–W16 |
| guide `contracts-and-adoption.md` | the frozen-row count → 138 |
| `python/tests/test_designs_corpus.py` | `GUARANTEE_TABLES["W"]` extends to W16, so the range and count guards see the new rows |

**Not amended, deliberately:**

- **W1, W2, W5, D2, M3**, and every G (but for G3), S, L, R, C, X, N and P row.
  W5 and D2 carry **no alias arm** — the formal model's invariance row cited them
  for the *dimension*, which is what changes, not for a test that mentions it.
- **Correction lifecycle §3.** `retraction`'s basis is the *model* for the new
  kind, which cites it; nothing in correction lifecycle changes. Its import
  acyclicity obligation is explicitly **unchanged** (§5.3).
- **Computation §, and normative contract §7.2**, which call
  `instrument-certification` the *tenth* kernel kind. It still is. Only the
  **total** moved, and only where a total is stated.
- **The disposition record's own measurements** (§1's "126 rows across ten frozen
  tables", W 16), which are dated evidence and stay at their date under §5.4's
  discipline. Cut 1's denominator of 126 is likewise frozen and untouched.

---

## 9. Guarantees, and how each is tested

Certified by mutation, per the kernel's §5 discipline. Three rows are added; three
are rewritten.

| # | Guarantee | Mutation test |
|---|---|---|
| **W14** | The address scheme adds a property the basis alone does not: a stored reference is unambiguous **by construction**, and no handle is ever stored to compete with it. Labels are rendered, never persisted, and rendering is locale-explicit | Author a reference to a record whose label collides with another's; assert the stored ref holds the **canonical identifier** and that **no** stored field anywhere holds the handle. Render the same record under two locales; assert **two labels, one address, no stored difference, and no identity movement**. **Recursive rendering:** render a `dataset` and assert its `programme` / `release` fields render through the pinned snapshot while the dataset itself renders from content. **Sabotage:** persist a rendered label as node content → the corpus must refuse it, since a stored label is an alias by another name. **Negative — this is not W1/W2:** hold the bases fixed and correct, mutate only the *handle*, and assert nothing observable moves — pinning that W14 tests the scheme and W1/W2 test the encoding |
| **W15** | A coreference balance is derived, ignores duplicate submissions, and privileges no attester class; closure rewrites nothing | Post `+1` from a human actor and `+1` from an agent actor over one pair; assert balance `2` and an **active** edge, and assert **swapping the two actors changes nothing** — the symmetry is the assertion. Post a `-1`; assert balance `1`, the edge still active, and **both prior records still present**. Post a second `-1` from a distinct actor; assert balance `0` and the edge **inactive**, with every record retained. **Duplication:** submit the same `(endpoints, stance, actor, grounds)` ten times under ten event tokens; assert **balance is unchanged** and that ten distinct records exist — provenance is kept, weight is not manufactured. **Closure does not rewrite:** with an active edge between `A` and `B`, assert a retraction targeting `A` still names `A` exactly, that `π_claim`, `belief_input_digest` and every content-identity basis are **byte-unchanged**, and that only **query expansion** observes the edge. **Negative — the cycle route stays shut:** activate coreference between two retractions and assert **no cycle is constructible**, and that M3's import validation is still what refuses a raw one |
| **W16** | `consolidate` repairs storage and asserts nothing about identity | Hold one identity in two corpora; `consolidate`; assert **one canonical address**, outgoing relations **unioned**, divergent lineage bases **both preserved**, **no redirect written**, **no inbound reference rewritten**, and `uid` continuity selected rather than minted. **Negative:** attempt `consolidate` on two records at **different** canonical addresses and assert **refusal** — that is a coreference question and `consolidate` must not answer it. **Negative:** assert no `deprecated_ids` entry is created, since no address retired |
| **W4** | *(rewritten)* A coreference claim is attributed and additive, and never collapses the graph | Assert no operation retires an address on coreference grounds. Its equal-basis consolidation arm moves to **W16**; its distinct-basis retraction refusal moves to **W15**'s cycle arm; its lineage-divergence arm — *"both survive, no field-selection path offers a choice, the dataset becomes `lineage-divergent`"* — moves to **W16**, where the union rule now carries it |
| **W6** | *(rewritten)* Three resolution states never collapse | `not-present`, `unknown`, `resolved` remain distinct; `ambiguous` is no longer among them. **Negative:** assert removing a corpus does not convert its ids to `unknown` — unchanged |
| **W9** | *(rewritten)* An ambiguous **search term** refuses and names its candidates | Search a term the pinned snapshot maps to two identifiers; assert refusal listing both, and that **no binding was written**. **Negative:** assert the ambiguity is a property of the **pinned snapshot**, reproducible across installations holding that snapshot — not of accumulated authoring |

---

## 10. Limitations

1. **An eleventh kernel kind is spent.** Adding a kind is a cross-corpus
   amendment — the same cost F8 records for removing one. Priced at §8 and judged
   worth paying only because all three cheaper realizations (§5.1) are larger
   changes in disguise.
2. **Two addresses persist for one work, permanently.** There is no longer an
   operation that reduces them. Query-layer searches expand over active
   coreference closure; the underlying records never merge.
3. **Attester reliability is unmeasured.** Unit weight is the honest default, not
   a finding that attesters are equally reliable. The `meta/` data collection that
   would inform per-source priors does not exist and is not opened here. Until it
   does, a coordinated set of low-quality attestations outweighs a single careful
   one, and nothing detects that.
4. **`consolidate` selects continuity.** Where two copies disagree on content it
   reconciles, and reconciliation is a judgement recorded rather than derived —
   the same standing merge had, narrowed to storage repair.
5. **The pinned authority snapshot is a new dependency with no design.** Which
   authorities are accepted, how a snapshot is pinned, versioned, distributed and
   bumped, and whether a bump is an amendment act — none of that is ruled here.
   §4.2 states the discipline; the artifact is owed.
6. **A claim about a release is not expressible** (§6). Accepted.

---

## 11. Open questions

1. **Which authorities are accepted, and who decides.** Limitation 5's artifact.
   The vocabulary-admission design (2026-08-07) is the nearest precedent and may
   be the right home rather than a new document.
2. **Does a coreference balance belong in any audit?** It is outside belief by
   §5.3, but an active edge with balance `1` and a contested history is a
   different epistemic object from one with balance `12` and none. Nothing
   currently surfaces the difference.
3. **The `meta/` reliability programme.** Collecting attester-agreement data is a
   research question the system should be able to answer about itself, and
   `instrument-certification` is the adjacent mechanism. Not opened.
4. **F10**, returned to the docket (§7).
