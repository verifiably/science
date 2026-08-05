# Formal model and claim calculus — design

**Status:** Draft — §2–§4 written; §5–§11 not yet drafted.

**Inherits:** the epistemic kernel (G1–G8, §4.1's signatures and semantic
identity, §8.7's recorded-history limit, limitation 4's predicate vocabulary),
substrate consolidation (S1–S8), world addressing (W1–W13), computation and
reproducibility (R1–R23), correction lifecycle (C1–C10), world-index packaging
(X1–X12), normative contract (N1–N10), tamper-evident log (L1–L13), domain
extension boundary (D1–D10).

**Constraints:** M₀ transcribes and cites; it never rules. Every entry carries
its banked citation, and a claim with no citation is a gap, recorded as one.
M\* revises only inside the claim neighbourhood, and every revision names the
guarantees it preserves, amends, or invalidates.

**Banking obligations (recorded now, discharged at banking).** When this design
is banked, **M1–M\<n\> must be added to the normative contract's exact oracle
inventory (its §4) and to ledger artifact 7's inventory**, the ledger gains an
artifact row, and the README's document count and table move. Both the L-table
and the N-table reached the inventory late; this note exists so M does not.

## 1. Why

Nine banked designs decide what the system means. They decide it in prose,
across roughly a hundred guarantee rows, and the properties those rows test are
never named as properties. Two consequences follow.

The first is that **completeness cannot be checked**. G3's belief-input closure
is the clearest case: the kernel's own text records that four of its members
"were live holes in earlier revisions, and none is reached by mutating a
member's value." Each was found by a reviewer noticing. Nothing in the method
distinguishes a closure that is complete from one whose next hole has not yet
been noticed.

The second is that **one stratum was never formalized at all**. On independent
axes — epistemic role, construction method, identity discipline, lifecycle —
the label family (`predicate`, `polarity`, `claim_layer`,
`identification_strength`, `scope`, `verdict`, resolution outcome, standing,
`MembershipRole`) has *no identity discipline and no construction method*, while
three of its members are inputs to proposition semantic identity. Kernel
limitation 4 records the visible corner of this: "The predicate vocabulary is
currently 9 terms; real claims will not fit cleanly."

This document is a two-ended refinement loop, not a transcription:

```text
intended epistemic behavior ──▶ candidate reference model (M*)
             ▲                          │
             │                          ▼
banked designs + guarantees (M₀) ◀── refinement / counterexamples
```

Neither end is authoritative. The intent constrains what the system should
mean; the banked designs carry commitments and hard-won edge cases. Where the
two cannot be connected, we have found either a design defect or an
underspecified goal.

Three columns stay conceptually separate throughout:

| layer | purpose |
|---|---|
| **M₀** — extracted model | what the banked designs currently rule |
| **M\*** — candidate model | the smallest system satisfying the intended guarantees |
| **ρ : M₀ → M\*** — refinement map | what is preserved, collapsed, renamed, or exposed as inconsistent |

**M₀ is wide and shallow; M\* is narrow and deep.** M₀ models the entire banked
system at interface depth — formal signatures and a dependency graph, not a
restatement of payload fields or mutation tests, for which the existing
documents remain the detailed source. M\* formalizes the claim neighbourhood
deeply. ρ is initially local to that neighbourhood, and M\* expands only when
another design question requires it.

## 2. M₀ — the formal inventory

Every player gets a compact entry: **construction** (authored, derived, or
external), **identity discipline** (the canonical projection πᵢ its commitment
is taken over), **lifecycle** (the legal transitions), **reads / produces**,
**readings affected**, **inertness** (the observational equivalences under which
it does not move), and **banked citations**.

The state space is many-sorted:

```text
Ω  =  Rec  ⊎  Proj  ⊎  Ext  ⊎  Art  ⊎  Con  ⊎  Cfg
      │        │        │       │       │       └─ corpus and world configuration
      │        │        │       │       └───────── contracts and rules
      │        │        │       └───────────────── held artifacts (bytes)
      │        │        └───────────────────────── external referents
      │        └────────────────────────────────── project-scoped records
      └─────────────────────────────────────────── world records
```

**The sorts are not a partition of concerns.** A `dataset` is a world record
*and* names held bytes; an `assessment` is a record, a derivation, and the
subject of several identities. The sorts partition the *carrier*; the axes
above cut across it, which is why each entry carries all seven fields
independently.

### 2.1 `Rec` — world records (the ten kernel kinds)

| player | construction | identity (πᵢ) | lifecycle | reads / produces | affects | inert under | banked |
|---|---|---|---|---|---|---|---|
| `proposition` | authored | **semantic identity** — normalized `statement` + `(subject, predicate, object, polarity, claim_layer)`; immutable for the life of the node. World-unique address | mint → semantic edit **mints a successor** linked by `supersedes`; display edits are ordinary revisions | reads nothing; target of `assesses`, `asserts\|denies\|hypothesizes`, `targets` | belief (closure member 2) | `title` overwrite; location; alias | kernel §4.1; **G7**; world §3, §4 |
| `source-assertion` | authored or extracted, attributed | world-unique address, derived. **No semantic identity is stated** — gap §2.7 (a) | authored; `anchored_in` a source span | reads `source`; produces nothing derived | none — belief-inert **by type** | everything in belief | kernel §4.1, §4.2; **G1**, **G6** |
| `assessment` | **derived** — an immutable derived output with no revision path | `(spec, run, proposition)` | minted by derivation; never revised; standing subtractable by `retraction` | reads spec, run, proposition; produces the **assessment facet** | belief (member 1); admission | location; alias; availability-with-copy-held | kernel §4.2.1, §5.1; comp §5.1; **G2b**, **G2c** |
| `analysis-spec` | authored, frozen pre-run | **spec identity** — the frozen hash | authored → **frozen** (immutable). The freeze also resolves `rule_bindings`, refusing on ambiguity | declares inputs, parameters, nondeterminism contract, interpretation and equivalence rules; `targets` a proposition | eligibility via **G2a**; belief transitively via assessment identity | — | kernel §4.1; comp §4.2a; 5b §6; **G2a** |
| `run` | executed through the boundary | **run address** over the execution recipe (comp §4.2); moves when **any** recipe member changes | begin is **refused** without an already-frozen spec identity, which is recorded first; recipe frozen pre-execution; result and occurrence recorded after | reads datasets by role (`observes`, `reads`, `transforms`), code, environment, workflow definition, parameters, `rule_bindings`; produces outputs manifest and a **nested** boundary receipt (not a node) | eligibility (≥1 `observes`); belief transitively | availability **in this checkout** while a controlled copy remains held | comp §4.2, §4.2a, §7.1; **R2**, **R5**; kernel **G2a** |
| `verification` | **derived** comparison of two runs, immutable | world address; basis = `(scope, verdict)` + equivalence-rule hash + differences + the comparison report **inline** | immutable; superseded by a later verification naming the failure it supersedes; **or** cleared by a standing retraction | reads two runs, the frozen equivalence rule; produces admission input | admission (fail-closed); belief (member 3) | location; alias | kernel §3.3; comp §7.3, §7.3b; **G8**, **R4**, **C6** |
| `dataset` | authored (acquired) or derived (`produces`) | **content identity** over the bytes; world address for the record | produced by a run; carries a stamped descendant-side **lineage basis**, tagged `single(route) \| conflict([route])` | read by runs under a role; carries facets, incl. `empirical-observation` | eligibility (heldness + facet); belief (members 4, 5) | availability in this checkout **while a controlled copy remains held** | kernel §2.2, §4.1; comp §5.2, §7.1; **R5** |
| `source` | authored record in a corpus | world address | authored; `member_of` a dataset (the corpus **is** a dataset) | read by extraction | none directly — only through `source-assertion` | everything in belief | kernel §4.1, §4.3 |
| `retraction` | authored, attributed, immutable | world address; **its identity covers its target's identity** — which is what makes cycles unconstructible | additive: the target stays byte-identical and resolvable. A counter-retraction removes **one** retraction from standing | reads its target; produces a standing subtraction | standing → admission → belief (member 6) | location; alias | correction §3, §4; **C1**, **C6** |
| `instrument-certification` | **content-derived** — no event token, exact-K | content-derived identity; a byte-identical re-mint **stays retracted** | minted from content; withdrawal answered by a superseding verification | certifies executable instruments, never authored lineage claims | rule-binding resolution; verification scope evidence | — | 5b §7.2, §7.5; N-table |

### 2.2 `Proj` — project-scoped records

| player | construction | identity | affects | banked |
|---|---|---|---|---|
| views — `hypothesis`, `question`, `theme`, `topic` | derived | project-scoped **name over a world query** | nothing in belief | world §3 |
| coordination — `task`, `decision` | authored | project-scoped; two projects may both hold a `t068` and always could | nothing in belief | world §3 |
| `note` | authored | project-scoped; **belief-inert prose** | nothing | world §3, §4.2, §4.3; kernel §4.3 |

These need no world identity, so they need no migration. That is a banked
consequence, not an omission.

### 2.3 `Ext` — external referents

| player | construction | identity | affects | banked |
|---|---|---|---|---|
| `term` | **external** | the ontology's own identifier; scope **external** | read as a `reads` input, which confers **no** eligibility in any quantity | world §3; kernel §4.1, §4.3; **G6** |

**`term` is the only sort member living outside the world's identity space**,
and proposition `subject`/`object` are today bare strings that do not reference
it. Gap §2.7 (b).

### 2.4 `Art` — held artifacts

| player | identity | notes | banked |
|---|---|---|---|
| dataset bytes | content identity | **held** = the exact bytes can be produced on demand. Held-ness is a *world* property; availability is a *checkout* property | kernel §2.2; comp §7.1 |
| code bundle | `code_identity` over the content-addressed bundle | recipe member | comp §4.2, §4.4 |
| environment artifacts | `environment_identity` over the manifest of held artifacts | recipe member | comp §4.2, §4.5 |
| workflow definition | `workflow_definition_identity` over the snapshot | recipe member; declared pre-execution | comp §4.2, §6 |
| rule fixtures | **fixture-set identity** | half of rule identity | 5b §6 |

### 2.5 `Con` — contracts and rules

| player | construction | identity | affects | banked |
|---|---|---|---|---|
| **science base contract** | authored, normative **SSOT** | contract identity | belief **unconditionally** — exactly one per semantic derivation; interpreting `assessment`, `dataset` or `assesses` *is* consulting it | D §8, §8.1; **D6**, **D7** |
| **domain contract** | authored, namespaced | contract identity | belief **conditionally** — each contract whose namespaced facets the derivation actually reads. Activated-but-unread domains stay out | D §3.3, §8; **D6** |
| `ProfileSpec` | **compiled** from the contracts | derived | the sole compiled runtime profile; **not** authoritative | D §6; substrate §12 (closed) |
| `KindSpec` | compiled from `ProfileSpec` | derived | input to `Registry.register()` | D §6 |
| **rule** | authored + fixtures | **rule identity = `(symbol, fixture-set identity)`** | binding frozen into `rule_bindings` at freeze; **refused** on ambiguity or an un-held / fixture-failing name | 5b §6; comp §4.2 |
| equivalence rule | declared in the spec, frozen with it | versioned rule id | `(original result, replay result) → passed \| failed \| inconclusive` | comp §7.2 |
| boundary policy | recipe member | names the **scope-derivation rule identity** | governs enforcement; scope is derived, never authored | comp §4.2, §4.4b; 5b §6; **R4** |
| **belief policy version** | authored | version | the aggregation rule itself (closure member 7) | kernel §5.1 |
| normative contract **cut** | derived | cut identity over normative rows + executable case identities — **never** the digest the cut produces | discovery from explicit cut + epoch | 5b §4, §5, §9 |

### 2.6 `Cfg` — corpus and world configuration

| player | construction | identity | affects | banked |
|---|---|---|---|---|
| corpus manifest | authored | `manifest_version: 2`; `corpus_id`, `profile` (one `science_contract` + a `domains` **mapping**), optional `forked_from` | pins the profile a corpus runs under | D §7; packaging §6; world §5 |
| **corpus-state identity** | derived | the **complete canonical manifest projection** + sorted node identities, under `science.identity.v1` | receipt material; **never** a belief-digest member | world §5 (amended 2026-08-04); D §8.1 |
| `corpus_id` | minted, opaque | stable identity; **never** a path, directory name, or project | admission refuses a duplicate | world §5; packaging §4; **X5** |
| admission record | authored | registry record | `known := admission record exists`; `live := known ∧ ¬terminal event`; `present := configuration resolves exactly one corpus carrying the id`. `retired` / `departed` are **terminal** | packaging §4; **X4**, **X6**, **X7** |
| world index (four maps) | **derived** | packaging identity | derived, never authoritative; carries the producers map, retraction enumeration, and certification inventory | world §5; packaging; **W8a** |
| **producer snapshot** | derived | **semantic identity** = producers map + the stable `corpus_id`s of covered corpora | a **required argument** to belief with no default, no implicit "latest", no stored selector — any of those would make belief follow the checkout | kernel §5.1; world §5 |
| log heads / anchors | appended | per-engine-root hash chains at a reserved in-corpus path | subject-bound anchors; five-step verification under an explicit selected subject | L-design; **L1–L13** |

### 2.7 Gaps found while transcribing

Recorded here rather than repaired; repair is ρ's job and only inside the claim
neighbourhood.

**(a) `source-assertion` has no stated semantic identity.** It has a world
address, and `proposition` has an identity discipline that survives semantic
edit. Nothing states what happens when a source-assertion's *content* is edited
— whether an extraction rerun that changes the asserted span or stance mints a
successor or revises in place. Since extraction is a fallible computation with a
measured 25–40% field-level disagreement rate (kernel limitation 3), this is not
hypothetical.

**(b) `subject` and `object` are bare strings while `term` exists.** The
referent side of every claim is unbound, and `term` is scoped *external*, so
binding it means proposition semantic identity would depend on an identifier
minted outside the world. This is the first thing M\* must resolve.

**(c) The label family has no construction method and no identity discipline.**
Nine enumerations, four different contract kinds needed (semantic vocabulary,
result codomain, ordered measure, structural), none supplied.
`identification_strength` is the sharpest: its own definition places five values
on a continuum and one off it, so it is not totally ordered, and nothing states
what the order is.

## 3. M₀ — the system-wide model

### 3.1 Commitments

Every identity in §2 has the same form:

```text
Iᵢ(x)  =  H( tagᵢ ‖ encode(πᵢ(x)) )
```

with `encode` the canonical encoding fixed by `science.identity.v1`, and `tagᵢ`
a domain separator. The property claimed is **not** mathematical injectivity of
`H`: it is that `encode ∘ πᵢ` is injective **on admissible values**, and that
`H` is domain-separated and collision-resistant. Every guarantee row that reads
"assert the digest changes" is a claim about `πᵢ` composed with a
collision-resistance assumption, and M₀ states it that way.

### 3.2 Transitions

`ω →ᵃ ω′`, where refusal is a **value**, not an exception:

| transition | precondition | banked |
|---|---|---|
| `write` | kind and facet validation under the compiled profile | substrate §6; D §6 |
| `freeze` (spec) | resolves `rule_bindings` to exactly one held conforming implementation; **refuses** on ambiguity or a fixture-failing name | 5b §6 |
| `begin` (run) | **refuses** without an already-frozen spec identity, and records it before any other observation | kernel **G2a** |
| `derive` | mints assessments, verifications, index maps. Divergence is **computed, never authored** | kernel **G5**; **W8a** |
| `supersede` | a later record naming what it supersedes | kernel §3.3, §4.1 |
| `retract` / `counter-retract` | additive; target stays byte-identical and resolvable | correction §4; **C1** |
| `admit` (corpus) | **refuses** a `corpus_id` already admitted | packaging §4; **X5**, **X7** |
| `retire` / `depart` | **terminal** — no API returns a corpus to `live` | packaging §4; **X6** |
| `move` | changes location only | world **W5** |
| `audit` | **mints nothing** — detection is split from correction | 5b §7.6 |

**These are not a group action.** Terminal transitions are noninvertible,
refusals make several partial, and admission refuses duplicates. M₀ therefore
takes **observational equivalence per reading** as the primitive and derives the
quotient intuition from it, rather than assuming algebraic structure the system
does not have.

### 3.3 The four readings

```text
standing   : Ω × Rec        → { standing, subtracted }
admission  : Ω × Assessment → { not-admitted, invalidated, admitted }
eligible   : Ω × AssessesEdge → Bool
B          : Ω × Q          → Belief  +  NotAvailable  +  Refused
```

**`standing`** is defined by structural recursion, not as a least fixpoint: an
input's standing is subtracted iff at least one **standing** retraction targets
it, and the operator is **antitone** through that negation. What makes the
recursion well-founded is banked and structural — *a retraction's identity
covers its target's identity, so a cycle would require two records each
containing the other's digest* (correction §4). Unique structural recursion, not
Knaster–Tarski.

**`admission`** is a reduction over the **fixed set of active verifications**
attached to an assessment, into a three-element order with `failed` absorbing:
none → `not-admitted`; any active `failed` → `invalidated` regardless of passing
siblings; ≥1 active `passed` at `clean-environment` with no active `failed` →
`admitted`. It is **not** monotone over record-set inclusion once retractions and
counter-retractions exist; the lattice statement is the narrower, defensible one.

**`eligible`** is kernel §4.1's predicate: the assessment's run has at least one
`observes` input, all inputs are held, and the assessment is `admitted`. `reads`
inputs never confer eligibility, in any quantity.

**`B`**'s codomain has three arms, and the third two are banked, not invented:
removing the corpus holding the records yields *"belief **not computable
here**"*, which is a computability state and not a belief that happens to be
unchanged — "reporting an unchanged belief in that situation would assert a
recomputation nobody performed" (comp §7.1).

### 3.4 Laws

| law | statement | tested by |
|---|---|---|
| **well-definedness / order-independence** | each reading is a function of the record set, hence independent of arrival order | argued packaging §4; **no row tests it directly** — X4 tests append-only, X6 tests status terminality |
| **observational invariance** | `ω ∼_B ω′ ⟹ B(ω,q) = B(ω′,q)`. Declared inert dimensions: location, alias, display fields, availability-with-a-copy-held | **W5**, **R5**, **G7** (converse half), **D2** |
| **commitment sensitivity** | a change to a declared semantic projection changes the encoded commitment, up to negligible collision probability | **G3**, **L4**, **D5** |
| **well-founded recursion** | `standing` terminates by content-address containment | argued correction §4; **no row tests it directly** — C5 tests chain-not-toggle and sibling-awareness |
| **fail-closure** | `admission` reduces into a three-element order with `failed` absorbing | **G2c**, **G8**, **C6** |
| **declared limit** | a *negative* row: the system provably **cannot** detect something, tested so the positive half is not over-read | **G4**, **G2a**, **G8** negatives; §8.7 |

**Two laws are argued in prose and tested by no row.** Order-independence is
what packaging §4's conclusion rests on — *"two registry copies that hold the
same records agree on every status regardless of arrival order"* — and
well-foundedness is what makes `standing` a definition at all. Both are load-
bearing, neither is an oracle. They are the first candidate M-rows, and finding
them took only the act of naming the laws separately from the rows; §5's
classification pass is the systematic version of the same move.

The **declared-limit** class is why the taxonomy needs six entries rather than
five. G4's row does not assert a property of the system; it asserts that
discarding a failed replay attempt is undetectable, and tests that the system
cannot detect it. Classified as well-definedness or invariance it would be
misfiled; dropped, §8.7's recorded-history limit would lose its carrier.

Note that packaging §4's phrase *"every predicate is monotone in the record
set"* is doing the work of **order-independence**, not monotonicity. `live :=
known ∧ ¬terminal-event` is anti-monotone — adding a record removes `live` — and
the conclusion the sentence draws (two registry copies with the same records
agree regardless of arrival order) follows from each predicate being a *function
of the record set*, which is what M₀ states.

## 4. The dependency graph and the closure check

### 4.1 Two graphs, and only one is well-founded

The **type-level** dependency graph is *not* a DAG: `standing` depends on
`standing`, and `verification` supersession depends on `verification`. Recursion
at the type level is normal and carries no obligation.

A **concrete derivation's instance graph** is well-founded exactly where the
banked identity rules force it — the retraction graph being the clearest case,
by content-address containment (§3.3). M₀ therefore records the well-foundedness
*argument* per recursive edge, not a blanket acyclicity claim. An edge with
recursion at the type level and no banked argument at the instance level is a
gap; none was found in the four readings.

### 4.2 What the check can and cannot establish

Writing `Dep₀` for the dependency relation declared by the §2 entries and
`Closure(r)` for a reading's declared closure:

```text
completeness   Dep₀*(r) ⊆ Closure(r)     every declared dependency is committed
minimality     Closure(r) ⊆ Dep₀*(r)     every committed member is a dependency
together                    equality
```

**The bound, stated plainly: a dependency omitted from both `Dep₀` and
`Closure` is invisible to this check.** It is a consistency check between two
declarations, not a proof about executed code. Closing that gap needs a
different instrument, recorded here as an M obligation: an **undeclared-read
oracle** that instruments a derivation to read an input it did not declare and
requires conformance to fail.

### 4.3 Running the check on `B`

`Closure(B)` is G3's eight members (kernel §5.1). `Dep₀*(B)` is what §2's
entries declare, transitively.

| declared dependency | reaches which closure member | verdict |
|---|---|---|
| assessment facet values, bound to the assessment carrying them | 1 — keyed assessment facets | ✅ |
| what is believed | 2 — proposition semantic identities | ✅ |
| admission ← active verifications `(scope, verdict, supersession state)` | 3 | ✅ |
| eligibility ← `observes` bytes | 4 — `observes` content identities | ✅ |
| independence ← ancestry | 5 — lineage snapshot | ✅ |
| standing ← retractions + coverage declaration | 6 — retraction enumeration | ✅ |
| the aggregation rule | 7 — belief policy version | ✅ |
| interpretation ← consulted contracts | 8 — profile contracts | ✅ |
| **`reads` inputs** — ontologies, literature corpora, reference graphs, simulator configuration | **1, transitively** | ⚠️ finding (a) |
| **held-ness of `observes` inputs** | **nothing** | ⚠️ finding (b) |

**Minimality holds:** each of the eight is reached by a declared dependency, so
no member is committed without being depended on.

**Finding (a) — a complete but undeclared transitive path.** A run's `reads`
inputs *do* reach the digest, by three hops that no design states together:
`inputs` is a recipe member carrying `(role, dataset address, content identity,
exclusion certification?)` for **every** role including `reads` (comp §4.2); a
run's address moves when any recipe member changes (**R2**); an assessment's
identity is `(spec, run, proposition)`, and member 1 keys facets by assessment
identity (kernel §5.1). So swapping the ontology a run read moves the digest.

The check therefore returns **complete**, but the completeness is **fragile**:
it rests entirely on `inputs` being role-partitioned rather than
`observes`-only, and nothing near G3 says so. Narrowing that recipe member — an
edit that would look local and reasonable — would silently break G3 without
touching G3's row, its mutation test, or any text that mentions belief. This is
exactly the class of defect the dependency graph exists to expose, and it is a
candidate M-row: *every input a run reads is in belief's transitive closure, and
the path runs through the recipe.*

**Finding (b) — a real incompleteness, already known and correctly reasoned.**
Held-ness is in `Dep₀*(B)` — `eligible` requires all inputs held, and destroying
the last held copy makes admission change (comp §7.1's three-case table). It is
in no closure member: the `observes` **content identity** is a recorded string
that does not move when the bytes cease to exist, and no other member moves
either. So two states differing in whether the last copy survives can share a
`belief_input_digest` while yielding different belief.

The designs know this. Comp §7.1 states that making that case computable *"would
require a separately published belief-input snapshot carrying the digest members
of kernel §5.1 — which the world index deliberately does not contain,"* and §13
records it as open. The gap is deliberate and reasoned: a digest cannot contain
a member the holder cannot compute, and held-ness is a world-wide property.

What M₀ adds is the **precise qualifier that G3's row currently lacks**. G3
reads "every belief state names its complete transitive input closure" and its
test asserts recomputation identity. The claim that actually holds is:

> G3's completeness is relative to the **locally computable** dependencies of
> `B`. Held-ness is a world property outside that set, and belief can therefore
> move without the digest moving in exactly one case: the destruction of the last
> held copy of an `observes` input.

That qualifier is a candidate amendment to G3's row rather than a new
guarantee — it narrows a claim to what is true, which is what §8.7 already does
for the recorded-history limit, and it classifies as **declared-limit**.

### 4.4 The other three readings

| reading | completeness | minimality | note |
|---|---|---|---|
| `standing` | ✅ retractions, counter-retractions, coverage declaration | ✅ | recursion well-founded by content-address containment |
| `admission` | ✅ active verifications only | ✅ | the fixed active set is the whole dependency |
| `eligible` | ⚠️ inherits finding (b) — held-ness | ✅ | `eligible` is where held-ness enters, and it has no commitment of its own |

## 5. Guarantee classification

*Not yet drafted.* Will classify ~100 banked rows under the closed taxonomy of
§3.4 (well-definedness, observational invariance, commitment sensitivity,
well-founded recursion, fail-closure, declared-limit), report every row that
classifies as none, and mint nothing.

## 6. M\* — the typed claim calculus

*Not yet drafted.*

## 7. M\* — term contracts and referent typing

*Not yet drafted.*

## 8. ρ — the refinement map

*Not yet drafted.*

## 9. Guarantees (M1–M\<n\>)

*Not yet drafted.*

## 10. Limitations

*Not yet drafted.*

## 11. Open questions

*Not yet drafted.*
