# Formal model and claim calculus — design

**Status:** Draft — §2–§9 written; §2–§4 corrected through review round 3, §5
and §6 through one review round, §7 through two, §8 through one; §10–§11 not
yet drafted.

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

The second is that **part of one family was never formalized**. The system's
labels are not homogeneous — `verdict` is a result codomain, `scope` a derived
label, `identification_strength` an ordered measure, `predicate` and
`claim_layer` semantic vocabulary — and they need different contracts, not one.
Sorted that way (§2.9 (c)), the codomains and derived labels are adequately
ruled. **The ordered measures lack their orders, and the semantic vocabulary
lacks term identity, an extension rule, and an owner** — while `predicate`,
`polarity` and `claim_layer` are three of the five inputs to proposition
semantic identity. Kernel limitation 4 records the visible corner: "The
predicate vocabulary is currently 9 terms; real claims will not fit cleanly."

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
external), **identities** (the canonical projections πᵢ its commitments are
taken over — plural, see below), **lifecycle** (the legal transitions),
**reads / produces**, **readings affected**, **inertness** (the observational
equivalences under which it does not move), and **banked citations**.

**The object universe is many-sorted; the state space is not the universe.**

```text
U  =  Rec  ⊎  Proj  ⊎  Ext  ⊎  Art  ⊎  Con  ⊎  Cfg  ⊎  Sub
      │        │        │       │       │       │       └─ subrecord artifacts
      │        │        │       │       │       └───────── corpus / world configuration
      │        │        │       │       └───────────────── contracts and rules
      │        │        │       └───────────────────────── held artifacts (bytes)
      │        │        └───────────────────────────────── external referents
      │        └─────────────────────────────────────────── project-scoped records
      └──────────────────────────────────────────────────── world records

ω ∈ Ω  =  ⟨ population ⊆ U,  relation instances,  derived maps,  configuration ⟩
```

A **configuration** `ω` is a finite population of objects drawn from `U`,
together with the relation instances among them, the derived maps standing over
them, and the corpus/world configuration they are addressed under. `U` is what
exists as a kind of thing; `Ω` is what the system is in at a moment. Conflating
them is what made the first draft treat `Ω` as a disjoint union.

**Identities are plural per player.** One player bears several commitments that
move independently, and D2 is the proof: adding a `biology/gene-axis` facet to a
dataset node leaves the **dataset address** unchanged while moving that node's
**content identity** and, through it, the **corpus-state identity**. An entry
whose identity column held one value could not express D2, so the column holds a
set.

**The sorts are not a partition of concerns.** A `dataset` is a world record
*and* names held bytes; an `assessment` is a record, a derivation, and the
subject of several identities. The sorts partition the *carrier*; the axes above
cut across it, which is why each entry carries all seven fields independently.

### 2.1 `Rec` — world records (the ten kernel kinds)

Each row's **identities** cell lists every commitment the player bears. All ten
additionally bear a **node-content identity** (moved by any facet or field
change) and contribute to their corpus's **corpus-state identity**; those two are
stated once here rather than repeated in every row.

| player | construction | identities (πᵢ) | lifecycle | reads / produces | affects | inert under | banked |
|---|---|---|---|---|---|---|---|
| `proposition` | authored | **semantic identity** — normalized `statement` + `(subject, predicate, object, polarity, claim_layer)`, immutable for the life of the node; **world address** derived from it | mint → semantic edit **mints a successor** linked by `supersedes`; display edits are ordinary revisions | reads nothing; target of `assesses`, `asserts\|denies\|hypothesizes`, `targets` | belief (closure member 2) | `title` overwrite; location; alias | kernel §4.1; **G7**; world §3, §4.2 |
| `source-assertion` | authored or extracted, attributed | **content identity over `(source identity, anchored span, stance, proposition identity)`** — the proposition hash alone would collapse forty assertions of P into one node and destroy the discourse counts | authored; `anchored_in` a source span. **Correction/continuity lifecycle unstated** — gap §2.9 (a) | reads `source`; produces nothing derived | none — belief-inert **by type** | everything in belief | world **§4.2**; kernel §4.1, §6; **G1**, **G6** |
| `assessment` | **derived** — an immutable derived output with no revision path | **`(analysis-spec identity, run identity, proposition identity)`** — a key over the derivation's inputs, not a content hash. `rule_bindings` reaches it through `run` | minted by derivation; never revised; standing subtractable by `retraction` | reads spec, run, proposition; produces the **assessment facet** | belief (member 1); admission | location; alias; availability-with-copy-held | world §4.2; kernel §4.2.1, §5.1; comp §5.1; **G2b**, **G2c** |
| `analysis-spec` | authored, frozen pre-run | **content identity**, frozen; immutable by construction | authored → **frozen**. The freeze also resolves `rule_bindings`, refusing on ambiguity | declares inputs, parameters, nondeterminism contract, interpretation and equivalence rules; `targets` a proposition | eligibility via **G2a**; belief transitively via assessment identity | — | world §4.2; comp §4.2a; 5b §6; **G2a** |
| `run` | executed through the boundary | **content identity of the execution closure — recipe + result + occurrence**; the occurrence's minted **event token** is what keeps two identical executions distinct. Moves when **any** closure member changes | begin is **refused** without an already-frozen spec identity, which is recorded first; recipe frozen pre-execution; result and occurrence recorded after | reads datasets by role (`observes`, `reads`, `transforms`), code, environment, workflow definition, parameters, `rule_bindings`; produces outputs manifest and a **nested** boundary receipt | eligibility (≥1 `observes`); belief transitively | availability **in this checkout** while a controlled copy remains held | world **§4.2**; comp §4.1, §4.2, §7.1; **R2**, **R5**; kernel **G2a** |
| `verification` | **derived** comparison of two runs, immutable | content identity over **(ordered run identities, equivalence-rule identity, comparison-report identity, scope-derivation rule identity, scope, verdict)** — the report's digest is what makes two differently-evidenced verifications two nodes | immutable; superseded by a later verification naming the failure it supersedes; **or** cleared by a standing retraction | reads two runs, the frozen equivalence rule; produces admission input | admission (fail-closed); belief (member 3) | location; alias | world **§4.2**; kernel §3.3; comp §7.3, §7.3b; **G8**, **R4**, **C6** |
| `dataset` | authored (acquired) or derived (`produces`) | **content identity** (manifest/content hash). Provider identifiers and accessions are **aliases**, never the basis | produced by a run; carries a stamped descendant-side **lineage basis**, tagged `single(route) \| conflict([route])` | read by runs under a role; carries facets, incl. `empirical-observation` | eligibility (held-ness + facet); belief (members 4, 5) | availability in this checkout **while a controlled copy remains held**; facet addition leaves the **address** unchanged (**D2**) | world §4.2; kernel §2.2, §4.1; comp §5.2, §7.1; **R5**, **D2** |
| `source` | authored record in a corpus | **normalized external identifier** — DOI, PMID, ISBN, accession. A work's identity is issued by the world, not computed by us | authored; `member_of` a dataset (the corpus **is** a dataset) | read by extraction | none directly — only through `source-assertion` | everything in belief | world **§4.2**; kernel §4.1, §4.3 |
| `retraction` | authored, attributed, immutable | world address; **its identity covers its target's identity** — which is what makes cycles unconstructible | additive: the target stays byte-identical and resolvable. A counter-retraction removes **one** retraction from standing | reads its target; produces a standing subtraction | standing → admission → belief (member 6) | location; alias | correction §3, §4; **C1**, **C6**, **C10** |
| `instrument-certification` | **content-derived**, no event token — a derived demonstration on the `verification` precedent | content identity over **(contract identity, discriminated subject, implementation content identity, witness evaluations)**; the rule identity inside carries the fixture-set identity | re-deriving unchanged is **idempotent**; a byte-identical re-mint of a retracted certification **stays retracted**. Withdrawal is by **retraction**, corrected by **counter-retraction**; under a **successor cut it is a different record**, so recertification-after-amendment is a new act, never a toggle | certifies executable instruments, never authored lineage claims | rule-binding resolution; verification scope evidence | — | 5b §7.1, §7.2; world §4.2; N-table |

### 2.2 Relation signatures and relation instances

Relations are not a sort of object; they are the edges of a configuration. Two
things must be inventoried separately, because they bear different disciplines.

A **relation signature** is a closed predicate over kinds, owned by `science` and
never redefined by a domain. The kernel's signatures:

```text
SourceAssertion ──asserts | denies | hypothesizes──▶ Proposition
Assessment  ──assesses──▶ Proposition          (the only belief-bearing edge)
AnalysisSpec──targets────▶ Proposition
Assessment  ──produced_by──▶ Run
Verification──verifies───▶ Assessment          (also ──replays──▶ Run ×2)
Run         ──executes───▶ AnalysisSpec
Run         ──observes───▶ Dataset             (empirical-observation facet required)
Run         ──reads──────▶ Dataset             (confers no eligibility, in any quantity)
Run         ──transforms─▶ Dataset             (lineage input; confers no eligibility)
Run         ──produces───▶ Dataset
SourceAssertion──anchored_in──▶ Source         (span-level)
Source      ──member_of──▶ Dataset             (the corpus is a dataset)
*           ──supersedes──▶ *                  (same-kind succession)
Retraction  ──retracts─────▶ EligibleTarget    ┐ adopted as-is into the normative
Retraction  ──grounded-in──▶ Ground            ├ relation vocabulary at the first
Retraction  ──succeeded-by─▶ Record            ┘ cut (5b §7.7, closing 5a §9)
```

**The three adopted names are hyphenated, and all three originate from
`Retraction`.** Both points are load-bearing: predicate matching is exact string
equality, so `grounded_in` is simply a different predicate from `grounded-in`
and would match nothing; and typing the latter two from `*` would let any record
ground or succeed anything, which 5a's fields do not permit — `grounds` and
`successor` are fields *of a retraction*.

`derived_from` is a **view** over `produces ∘ transforms` and is never a stored
edge — a distinction M₀ must keep, because a view has no instance identity.

**A relation instance has no identity of its own.** It is a stored occurrence
*embedded in* the source node, and it is committed by that node's content
identity — which is why editing an edge moves the node, and through it the
corpus-state identity, with no separate edge commitment anywhere. Predicate
matching on instances is **exact string equality** over a free string, a
different object from the proposition's `predicate` field (§2.9 (d)).

The tuple `(source live id, position, predicate, unresolved target)` is *not*
that identity: it is the shape of an **unresolved traversal entry** (substrate
§5) — what an adapter reports when a step fails to resolve. Its first two
components exist so a finding can say **whose** edge dangled, since
`(predicate, target)` alone deduplicates `X ─cites→ M` with `Y ─cites→ M`;
entries are totally ordered by `(source id, position)`. The first draft
transcribed a diagnostic shape as an identity.

**Effects are indexed by signature, not by "relation instance".** The signatures
carry different dependencies, and a single row for all of them would be the
roster this system's doctrine forbids:

| signature | what it affects | banked |
|---|---|---|
| `assesses` | the **only** belief-bearing edge; gates aggregation entirely | kernel §4.1; **G1** |
| `observes` | eligibility — at least one is required, and it demands the `empirical-observation` facet | kernel §4.1; **G6** |
| `reads`, `transforms` | confer **no** eligibility in any quantity; `transforms` feeds lineage | kernel §4.1; comp §5.2 |
| `produces` | lineage and the producer sets — belief member 5 | comp §5.2; kernel §5.1 |
| `verifies`, `replays` | admission; belief member 3 | kernel §3.3 |
| `executes`, `targets` | assessment identity's spec and proposition components | world §4.2 |
| `member_of` | corpus membership; discourse counts, never belief | kernel §4.3, §6 |
| `anchored_in` | part of `source-assertion`'s identity basis (the span) | world §4.2 |
| `supersedes` | active/superseded state → admission | kernel §3.3 |
| `retracts` | standing → admission → belief member 6 | correction §4; 5b §7.7 |
| `grounded-in` | the recorded evidence a retraction rests on; a groundless subtraction is **unspellable** | correction §5; **C2**; 5b §7.7 |
| `succeeded-by` | **nothing** — optional and informational, "a pointer for reviewers and diagnostics, **never an implicit redirect**"; nothing resolves through a retraction to its successor | correction §3; 5b §7.7 |

| player | construction | identities | banked |
|---|---|---|---|
| relation signature | authored, in the science base contract | contract identity of the declaring contract; a domain never redefines one | kernel §4.1; D §3.2, §8 |
| relation instance | authored | **none of its own** — committed by the source node's content identity. The stored ref and its **resolution** are recorded separately, which is what makes a deletion visible | substrate §5; kernel §5.1 |

### 2.3 `Sub` — identity-bearing artifacts that are not nodes

Four artifacts carry commitments, enter identities, and are **not** nodes. They
were absent from the first draft, which is why the inventory could not express
what a comparison report does.

| player | construction | identity | why not a node | banked |
|---|---|---|---|---|
| **boundary receipt** | constructed by the boundary | receipt identity; **nested inside the run**, never a node | a receipt names its inputs and holds none of them | comp §4.2, §4.4b; world §5 |
| **comparison report** | derived | **comparison-report identity** — a member of `verification`'s basis. Embeds boundary receipts, conformance results and certification evidence **inline** | the evidence must make two differently-evidenced verifications two nodes; a reference would let it drift | comp §7.3b; 5b §6, §7.6; world §4.2 |
| **lineage basis** | stamped descendant-side at production | tagged `single(route) \| conflict([route])`, the **tag inside the digest** | a durable descendant-side record, not an edge, so deleting the producing run leaves the loss **detectable** | comp §5.2; kernel §5.1 |
| **facet** | authored or derived, per contract | canonical facet digest; keyed to its carrier in belief member 1 | facets stay facets until the promotion trigger — no API retracts, supersedes, or attributes one | D §4, **D10**; kernel §5.1 |

### 2.4 `Proj` — project-scoped records

| player | construction | identity | affects | banked |
|---|---|---|---|---|
| views — `hypothesis`, `question`, `theme`, `topic` | derived | project-scoped **name over a world query** | nothing in belief | world §3 |
| coordination — `task`, `decision` | authored | project-scoped; two projects may both hold a `t068` and always could | nothing in belief | world §3 |
| `note` | authored | project-scoped; **belief-inert prose** | nothing | world §3, §4.2, §4.3; kernel §4.3 |

These need no world identity, so they need no migration. That is a banked
consequence, not an omission.

### 2.5 `Ext` — external referents

| player | construction | identity | affects | banked |
|---|---|---|---|---|
| `term` | **external** | the ontology's own identifier; scope **external** | read as a `reads` input, which confers **no** eligibility in any quantity | world §3; kernel §4.1, §4.3; **G6** |

**`term` is the only sort member living outside the world's identity space**,
and proposition `subject`/`object` are today bare strings that do not reference
it. Gap §2.9 (b).

### 2.6 `Art` — held artifacts

| player | identity | notes | banked |
|---|---|---|---|
| dataset bytes | content identity | **held** = the exact bytes can be produced on demand. Held-ness is a *world* property; availability is a *checkout* property | kernel §2.2; comp §7.1 |
| code bundle | `code_identity` over the content-addressed bundle | recipe member | comp §4.2, §4.4 |
| environment artifacts | `environment_identity` over the manifest of held artifacts | recipe member | comp §4.2, §4.5 |
| workflow definition | `workflow_definition_identity` over the snapshot | recipe member; declared pre-execution | comp §4.2, §6 |
| rule fixtures | **fixture-set identity** | half of rule identity | 5b §6 |

### 2.7 `Con` — contracts and rules

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

### 2.8 `Cfg` — corpus and world configuration

| player | construction | identity | affects | banked |
|---|---|---|---|---|
| corpus manifest | authored | `manifest_version: 2`; `corpus_id`, `profile` (one `science_contract` + a `domains` **mapping**), optional `forked_from` | pins the profile a corpus runs under | D §7; packaging §6; world §5 |
| **corpus-state identity** | derived | the **complete canonical manifest projection** + sorted node identities, under `science.identity.v1` | receipt material; **never** a belief-digest member | world §5 (amended 2026-08-04); D §8.1 |
| `corpus_id` | minted, opaque | stable identity; **never** a path, directory name, or project | admission refuses a duplicate | world §5; packaging §4; **X5** |
| admission record | authored | registry record | `known := admission record exists`; `live := known ∧ ¬terminal event`; `present := configuration resolves exactly one corpus carrying the id`. `retired` / `departed` are **terminal** | packaging §4; **X4**, **X6**, **X7** |
| world index (four maps) | **derived** | packaging identity | derived, never authoritative; carries the producers map, retraction enumeration, and certification inventory | world §5; packaging; **W8a** |
| **producer snapshot** | derived | **semantic identity** = producers map + the stable `corpus_id`s of covered corpora | a **required argument** to belief with no default, no implicit "latest", no stored selector — any of those would make belief follow the checkout | kernel §5.1; world §5 |
| log heads / anchors | appended | per-engine-root hash chains at a reserved in-corpus path | subject-bound anchors; five-step verification under an explicit selected subject | L-design; **L1–L13** |

### 2.9 Gaps found while transcribing

Recorded here rather than repaired; repair is ρ's job and only inside the claim
neighbourhood.

**(a) `source-assertion` has an identity basis but no correction lifecycle.**
World §4.2 rules the basis — a hash over `(source identity, anchored span,
stance, proposition identity)` — so the first draft's claim that it had none was
wrong. The gap is downstream of that: because the span and the stance are *in*
the basis, an extraction rerun that shifts either **produces a different node**,
and nothing states whether the earlier one is superseded, retracted, or left
standing beside its replacement. Since extraction is a fallible computation with
a measured 25–40% field-level disagreement rate (kernel limitation 3), a corpus
re-extracted twice yields two populations of assertion nodes with no declared
relation between them, and the discourse counts §6 of the kernel computes are
counts over that population.

**(b) `subject` and `object` are bare strings while `term` exists.** The
referent side of every claim is unbound, and `term` is scoped *external*, so
binding it means proposition semantic identity would depend on an identifier
minted outside the world. This is the first thing M\* must resolve.

**(c) The label family is heterogeneous, and only two of its four classes are
defective.** The first draft's blanket claim — that the family has no
construction method and no identity discipline — is false, and the correction
matters because it changes what M\* owes.

| class | members | construction | verdict |
|---|---|---|---|
| **result codomain** | `verdict`, resolution outcome (`not-present` / `not-available` / `unknown`), standing | ruled: `verdict` is the equivalence rule's codomain (comp §7.2); the three resolution outcomes are ruled distinct and non-collapsible (D §5); standing is defined by recursion (correction §4) | **adequate** |
| **derived label** | `scope`, divergence state | ruled: `scope` is **derived** from how two runs' recipes relate, never authored, with `not-certified` as the floor (comp §7.3, **R4**); divergence is computed, never authored (**G5**) | **adequate as construction** |
| **ordered measure** | `identification_strength`; `scope` wherever it is *compared* rather than matched | **defective** — no order is defined. `identification_strength`'s own definition places five values on a continuum and one (`analogical`) off it, so it is not totally ordered; and admission tests `scope` for equality with `clean-environment`, so nothing yet needs an order the design does not supply | **defective** |
| **semantic vocabulary** | `predicate`, `claim_layer`; `polarity` as currently coupled | **defective** — no term identity, no extension rule, no owner, and three of these feed proposition semantic identity. `polarity`'s admissible values are gated by a hard-coded three-element roster over `predicate` | **defective** |

So the finding is not "the labels are unformalized" but: **result codomains and
derived labels have adequate contracts; ordered measures lack their orders; and
semantic vocabulary lacks everything.** M\* owes the last two.

**(d) `predicate` names two unrelated objects.** The relation instance's
`predicate` is a free string matched by exact equality (substrate §5); the
proposition's `predicate` is a semantic-vocabulary term inside an identity hash.
They share a word, a field name, and nothing else. M\* must not let the term
contract leak onto edges.

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

Refusal is a **value**, so the transition is a function into a sum, not a
relation between configurations:

```text
step : Ω × Action  →  Ω  +  Refused
```

A relation `ω →ᵃ ω′` cannot simultaneously make refusal a value, because a
refused act has no `ω′` to relate to — the first draft wrote both and meant only
this one. `Refused` carries the reason; nothing in `Ω` records that an act was
attempted unless a record makes it so, which is §8.7's territory.

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
standing   : Ω × Target       → { standing, subtracted }
admission  : Ω × Assessment   → Adm
eligible   : Ω × AssessesEdge → Bool
B          : Ω × Q            → Belief  +  NotAvailable  +  Refused
```

`B` is **total** into that sum. `B(ω,q)↓` is written throughout for *"lands in
the `Belief` arm"* — not for definedness in the partial-function sense. The
distinction matters in §4.3: a `def` dependency does not make `B` undefined, it
routes the result to `NotAvailable`, which is a value the caller receives and can
act on rather than an absence.

`Target` is **not** all of `Rec`. Retraction targets are the eligible node and
route targets only: a retraction naming a note, or a proposition, is
**unspellable through the boundary** (**C10**). Typing `standing` over `Rec`
would make ill-formed targets expressible and then require a validator to
reject them — defensive where the type should refuse.

**`admission`** is an explicit reduction, and the unordered codomain it reduces
into must be defined before it can be named:

```text
Adm  =  { not-admitted,  invalidated,  admitted }        an unordered three-element set

admission(ω, a)  =  let V = active verifications of a in ω               (§3.3 lifecycle)
                    if  ∃v ∈ V.  verdict(v) = failed           → invalidated      (1)
                    if  ∃v ∈ V.  verdict(v) = passed
                        ∧ scope(v) = clean-environment          → admitted        (2)
                    otherwise                                   → not-admitted
```

**`Adm` carries no order**, and the first draft's `not-admitted < invalidated <
admitted` had no banked justification — it is neither an information order (an
invalidated assessment is not "more informative" than an unadmitted one) nor a
permissiveness order. What the lifecycle rules is a **precedence between
clauses**: clause (1) is tested before clause (2), which is the whole content of
"a passing sibling never clears an active failure" (**G2c**). `failed` is
absorbing as a **reduction rule**, not as a lattice fact.

The reduction is over the **fixed set of active verifications**, so it is a
function of that set and nothing wider; it is *not* monotone over record-set
inclusion once retractions and counter-retractions exist, and M₀ claims only the
narrower statement.

**`standing`** is defined by structural recursion, not as a least fixpoint: an
input's standing is subtracted iff at least one **standing** retraction targets
it, and the operator is **antitone** through that negation. What makes the
recursion well-founded is banked and structural — *a retraction's identity
covers its target's identity, so a cycle would require two records each
containing the other's digest* (correction §4). Unique structural recursion, not
Knaster–Tarski.

**`eligible`** is kernel §4.1's predicate: the assessment's run has at least one
`observes` input, all inputs are held, and the assessment is `admitted`. `reads`
inputs never confer eligibility, in any quantity.

**`B`**'s codomain has three arms, and the latter two are banked, not invented:
removing the corpus holding the records yields *"belief **not computable
here**"*, which is a computability state and not a belief that happens to be
unchanged — "reporting an unchanged belief in that situation would assert a
recomputation nobody performed" (comp §7.1).

### 3.4 Laws

| law | statement | tested by |
|---|---|---|
| **well-definedness** | each reading is a *function* of the configuration — one value, no ambient input | **G3** (recompute from the named closure alone; assert identity) |
| **order-independence** | `status : 𝒫(RegistryRecord) → RegistryStatus` — registry status is a function of the record **set**, so no arrival order can appear in it | **X6** — *"assert every status is invariant under record arrival order"*, the implementation oracle for that typing |
| **observational invariance** | `ω ∼_B ω′ ⟹ B(ω,q) = B(ω′,q)`. Declared inert dimensions: location, alias, display fields, availability-with-a-copy-held | **W5**, **R5**, **G7** (converse half), **D2** |
| **commitment sensitivity** | a change to a declared semantic projection changes the encoded commitment, up to negligible collision probability | **G3**, **L4**, **D5** |
| **well-founded recursion** | `standing` terminates by content-address containment | argued correction §4; **no row tests it directly** — C5 tests chain-not-toggle and sibling-awareness |
| **fail-closure** | `admission` reduces into an **unordered** three-element codomain under **failure-first precedence** | **G2c**, **G8**, **C6** |
| **declared limit** | a *negative* row: the system provably **cannot** detect something, tested so the positive half is not over-read | **G4**, **G2a**, **G8** negatives; §8.7 |

**Order-independence is a typing, not an equation.**

```text
status : 𝒫(RegistryRecord) → RegistryStatus
```

Writing it as `status(R) = status(R′) whenever R = R′` would be reflexivity, not
a law — it holds of every function whatsoever. The content is entirely in the
**domain**: `status` takes a *set*, so there is no place in its input for an
arrival order to sit, and independence follows from the type. X6 is the
implementation oracle for that typing, varying arrival order and asserting the
statuses agree.

M₀ claims nothing wider. In particular it does **not** claim `reduce(h) =
reduce(perm(h))` over whole configurations: that would assert equality of the
entire state under reordering, which nothing banked guarantees and which
occurrence-bearing records visibly violate — a `run` carries a minted event
token and `started_at`, so two histories differing in order do not produce equal
configurations even when they produce equal statuses. A system-wide history law
would need histories modeled, which M₀ does not do and does not yet need.

**Well-foundedness is argued in prose and tested by no row.** It is what makes
`standing` a definition rather than a description, and correction §4 argues it
structurally by content-address containment. C5 tests chain-not-toggle and
sibling-awareness — behaviour *given* that the recursion terminates — not
termination itself. That is a candidate M-row, and finding it took only the act
of naming the laws separately from the rows.

The **declared-limit** class is why the taxonomy needs seven entries rather than
six. G4's row does not assert a property of the system; it asserts that
discarding a failed replay attempt is undetectable, and tests that the system
cannot detect it. Classified as well-definedness or invariance it would be
misfiled; dropped, §8.7's recorded-history limit would lose its carrier.

Note that packaging §4's phrase *"every predicate is monotone in the record
set"* is doing the work of **order-independence**, not monotonicity. `live :=
known ∧ ¬terminal-event` is anti-monotone — adding a record removes `live` — and
the conclusion the sentence draws (two registry copies with the same records
agree regardless of arrival order) follows from each predicate being a *function
of the record set*, which is what M₀ states.

## 4. The typed dependency graph and the factorization check

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

### 4.2 One dependency relation is three

A single `Dep₀` conflates three edges that answer different questions, and the
first draft's check was unsound for exactly that reason — it compared a mixed
edge set against a digest and concluded about belief.

```text
x →ˢᵉᵐ r     semantic read   — x's value participates in computing r's value
x →ᵇⁱⁿᵈ r    binding         — x's identity is committed in r's projection
x →ᵈᵉᶠ r     arm selection   — x's state determines which arm of r's codomain is reached
```

**`def` selects an arm; it does not withhold a value.** Every reading here is
total — `B` always answers, and `NotAvailable` is one of its answers. The first
draft called this edge "definedness … whether `r` is defined at all," which
contradicts `B`'s totality two sections earlier. What a `def` edge decides is
whether the reading lands in its **primary computable arm**.

They are independent: an input can be `sem` without being committed (read but
uncommitted — the defect class G3 exists to forbid), committed without being
`sem`, and `def` without either.

**The law is factorization, not edge-set inclusion.** `sem ⊆ bind` is not
well-typed: a semantic value is almost never committed *as the same object*.
Dataset bytes participate semantically; what is committed is their content
identity. An inclusion between a set of value-dependencies and a set of
identity-members compares two different kinds of thing. The statement that does
type is:

```text
D_B   =  { (ω,q)  |  B(ω,q) ∈ Belief }        the belief arm's preimage

κ_B   :  D_B  →  CommittedProjection          the complete canonical committed projection
B|D_B =  B̄ ∘ κ_B                              factorization
I(B)  =  H( tag_B ‖ encode(κ_B(ω,q)) )  =  belief_input_digest,  for (ω,q) ∈ D_B
```

`κ_B` is typed over **`D_B`, not `Ω × Q`**. Outside the belief arm there is no
claim that the projection can be computed at all — that is precisely what
`NotAvailable` reports — so defining the digest there would assert a computation
nobody performed. The factorization is a statement about `B` restricted to
`D_B`, and every claim below is scoped to it.

Equivalently: **equal committed projections must yield equal beliefs.** That is
what G3's "recompute from the named closure alone; assert identity" asserts, and
it fails exactly when some `sem` dependency is not determined by `κ_B`.
Collision resistance is what connects `κ_B` to the digest — the factorization is
the property; the digest is its representation.

**Commitment sensitivity is a separate law, not the converse of this one**:
changing an admissible semantic dependency must change `κ_B`. Factorization
alone is satisfied by a constant projection; sensitivity alone is satisfied by a
projection that commits noise. G3's row tests both halves, which is why its
mutation battery has a positive and a negative arm.

The `sem` / `bind` / `def` vocabulary remains useful as **diagnostic shorthand**
for classifying an edge — but only once the projection mapping each `sem`
dependency to its committed representative is written down, which §2's entries
do not yet carry.

**The economy law is withdrawn.** The draft's `bind ⊆ sem ∪ def` would forbid
**intentional structural commitments**, which this system deliberately makes:
the assessment identity binds a facet *to its derivation*, defeating the
permutation attack even when two derivations yield byte-identical facet values;
a coverage declaration binds the meaning of an **absence**. Neither changes the
belief value nor its definedness, and both are necessary. Rather than invent a
fourth edge type to rescue the formula, M₀ drops it — §5's classification does
not need it.

**The bound, stated plainly: an edge omitted from both the declarations and the
closure is invisible to this check.** It is a consistency check between two
declarations, not a proof about executed code — a derivation that reads an input
nobody declared satisfies every check here. Closing that gap needs a different
instrument, recorded as an M obligation: an **undeclared-read oracle** that
instruments a derivation to read an input it did not declare and requires
conformance to fail.

### 4.3 Running the factorization check on `B`

The projection `κ_B` is G3's eight members (kernel §5.1). The semantic
dependencies are what §2's entries read, transitively. The middle column names
the **committed representative** of each — the identity or projection through
which the value reaches `κ_B`, since almost none of them is committed as itself.

| semantic dependency of `B` | committed member of `κ_B` it is represented by | factors |
|---|---|---|
| assessment facet values, keyed to their carrier | 1 — keyed assessment facets | ✅ |
| what is believed | 2 — proposition semantic identities | ✅ |
| active verifications `(scope, verdict, supersession state)` → admission | 3 | ✅ |
| `observes` bytes | 4 — `observes` content identities | ✅ |
| ancestry → independence | 5 — lineage snapshot | ✅ |
| retractions + coverage declaration → standing | 6 — retraction enumeration | ✅ |
| the aggregation rule | 7 — belief policy version | ✅ |
| consulted contracts → interpretation | 8 — profile contracts | ✅ |

Every verified semantic dependency of `B` factors through `κ_B`.

**Two further dependencies sit deliberately outside that table**, and the
findings below are about exactly why. Neither is an established semantic
dependency: one is bound without being shown semantic, the other's edge type is
undecided. Listing either as a row would let an unproven claim inherit a ✅, and
the first draft did precisely that.

The first draft additionally claimed minimality, on the grounds that each of the
eight members is reached by some declared dependency. That argument compared the
wrong objects — it ran before `sem`, `bind` and `def` were distinguished at all —
and the law it was aiming at is withdrawn as unsound (§4.2). Nothing replaces it
here.

**Finding (a) — a complete binding path that nothing declares.** A run's
non-`observes` inputs *do* move the digest, by three hops no design states
together: `inputs` is a recipe member carrying `(role, dataset address, content
identity, exclusion certification?)` for **every** role (comp §4.2); a run's
identity moves when any closure member changes (**R2**); an assessment's identity
is `(spec, run, proposition)`, and member 1 keys facets by assessment identity
(kernel §5.1).

**What this establishes is a binding path, not a semantic one.** Swapping the
ontology a run read moves `κ_B`. It does *not* show that the swap changes belief
— the stored result and the assessment facet could be byte-identical — and no
argument here is entitled to that stronger claim. Over-binding is the safe
direction, and it is what the recipe buys.

The binding is nonetheless **fragile**: it rests entirely on that recipe member
being role-partitioned rather than `observes`-only, and nothing near G3 says so.
Narrowing it — a local, reasonable-looking edit — would drop those inputs out of
`κ_B` without touching G3's row, its mutation test, or any text mentioning
belief. Candidate M-row, stated at its true strength: *every run input enters the
execution recipe and therefore the assessment's carrier identity.*

**Finding (b) — a genuine choice point, not a transcription.** Held-ness is a
dependency of `B`; the question the first draft never asked is **which edge type
it is**, and the two answers are incompatible.

First, a scope correction: kernel §4.1's predicate requires that **all** inputs
are held, not only `observes` ones. Destroying the last held copy of an ontology
a run `reads` therefore has the same standing as destroying an `observes`
dataset. The first draft scoped this to `observes` and was wrong.

| reading | consequence |
|---|---|
| held-ness is a **`sem`** edge — losing it yields a *different belief value* | **factorization fails**: two configurations differing only in whether the last copy survives share `κ_B`, and therefore share a `belief_input_digest`, while yielding different beliefs. That is a G3 violation, not a qualifier on G3 |
| held-ness is a **`def`** edge — losing it routes the result to `NotAvailable` | factorization survives, and the guarantee reads: **whenever `B` lands in the `Belief` arm, `κ_B` determines it**. `NotAvailable` is the honest answer — a computability state, not a belief that happens to be unchanged |

The first draft chose neither and wrote "G3's completeness is relative to the
locally computable dependencies of `B`". **That formulation is withdrawn.**
Locality is a property of a *holder*, not of the dependency relation; letting it
qualify the relation means the same system has different dependencies at
different checkouts, which makes the model unstable exactly where it must not be.

**Recommendation for ρ: `def`. The mechanism stays open.** Adopting `def` is a
revision, not a transcription — comp §7.1's second row currently reads `sem`,
*"eligibility fails and admission **changes**"* — so ρ must carry that amendment
explicitly, with the guarantees it touches named.

The first draft went further and recommended making loss of the last held copy a
**recorded act**, so that held-ness became an ordinary committed member. That
recommendation is **withdrawn as premature**, for two reasons:

- A local deletion act proves only that *one copy* disappeared. "No copy
  survives anywhere" is a world-wide **negative** fact, and recording it needs
  coverage, authority and discovery semantics — the same machinery the retraction
  enumeration needed, and none of it is designed.
- Routing to `NotAvailable` does not by itself make the case computable. Comp
  §7.1 is explicit that computing it requires a **separately published
  belief-input snapshot** carrying kernel §5.1's members, which the world index
  deliberately does not contain. Choosing `def` decides what the *answer* is; it
  does not supply the ability to compute which answer applies.

So §4 records the choice and leaves the mechanism to §8.

### 4.4 The other three readings

Reported on the same typed basis. `def` columns are stated because two of these
readings are where definedness actually enters.

| reading | factors through its commitment | `def` edges | note |
|---|---|---|---|
| `standing` | ✅ retractions, counter-retractions, coverage declaration | the target must be an eligible target (**C10**) | recursion well-founded by content-address containment |
| `admission` | ✅ active verifications only | none | the fixed active set is the whole dependency |
| `eligible` | n/a — `eligible` has no commitment of its own | **held-ness of every input** — finding (b) enters here | this is the reading finding (b) is *about*; `B` inherits it |

## 5. Guarantee classification

### 5.1 Method

**113 rows** across nine frozen tables: G (10), S (9), W (16), R (23), C (10),
X (12), N (10), L (13), D (10).

Classification is **per assertion, not per row** — 113 rows, 128 assertions — and a row may carry several
labels: many rows state a property in a positive arm and pin its limit in a
negative arm, and those are different classes. **No id is renamed, renumbered or
merged.** This section mints nothing — it labels what is already banked.

§3.4's labels are abbreviated **WD** (well-definedness), **OI**
(order-independence), **OInv** (observational invariance), **CS** (commitment
sensitivity), **WF** (well-founded recursion), **FC** (fail-closure), **DL**
(declared limit). Labels marked **†** are *proposed* in §5.4, not yet part of the
taxonomy; they are used here so the classification is complete and reviewable
rather than half-blank.

### 5.2 The classification

**G — epistemic kernel**

| id | assertions | classes |
|---|---|---|
| G1 | belief output byte-identical under a maximal source-assertion / the `assesses` edge is refused | OInv / RF† |
| G2a | the boundary refuses an unfrozen spec / it records that identity **first** / post-hoc attachment is undetectable | RF† / EO† / **DL** |
| G2b | unheld or unhashed input refused | RF† |
| G2c | admission only at `clean-environment, passed`; a passing sibling never clears a failure | **FC** |
| G3 | recompute from the named closure alone → identity / mutate each member → digest moves, incl. permutation and scope / move an entity or edit an alias → digest unmoved | **WD** / **CS** / **OInv** |
| G4 | an unreferenced successor to a recorded failure is refused / discarding the attempt is undetectable | RF† / **DL** |
| G5 | divergence is computed; no authored kind exists | CA† + US† |
| G6 | `reads` inputs confer no eligibility in any quantity or QA state | **OInv** |
| G7 | a semantic edit mints a new identity, prior bindings hold, old belief unmoved / a `title` overwrite mints nothing | **CS** + **OInv** / **OInv** |
| G8 | a failing verification invalidates and forces recomputation; cleared only by resolution or standing retraction / deleting it restores admission | **FC** / **DL** |

**S — substrate consolidation**

| id | assertions | classes |
|---|---|---|
| S1 | closure matches membership-traversal semantics; `directed` not reinterpreted | PC† |
| S1a | the lineage closure shares the algorithm, not the edge semantics | PC† |
| S2 | a semantic edit through the write API mints a new proposition | **CS** |
| S3 | a stale semantic hash is rejected on import / editing fields **and** hash passes | RF† / **DL** |
| S4 | no rename path is reachable from the semantic-change branch | US† |
| S5 | incomplete lineage never certifies independence / the deletion guarantee is scoped | EB† / **DL** |
| S6 | only certified independence confers multiplicity | EB† |
| S7 | eligibility is enforced at both boundaries, including raw writes | PC† |
| S8 | no module outside the write API holds a mutable handle (static) | US† |

**W — world addressing**

| id | assertions | classes |
|---|---|---|
| W1 | distinct bases never become one node | **CS** |
| W2 | a shared basis establishes coreference mechanically | **WD** |
| W3 | creating a world entity without its basis is refused | RF† |
| W4 | a merge is authored; content is never derived by precedence | RF† + CA† |
| W5 | a move changes only location — `uid`, identity, belief unmoved | **OInv** |
| W5a | a basis change is ruled by case, never by default | ED† |
| W6 | the four resolution states never collapse | ED† |
| W7 | views see the whole world, not a directory | *unclassified — direct requirement* |
| W8 | no conflict is resolved by precedence | RF† |
| W8a | all four index maps are derived, never authoritative | CA† |
| W8b | `uid` uniqueness is enforced; its two violations are distinguished | **CS** + ED† |
| W9 | an ambiguous alias refuses and names its candidates | RF† |
| W10 | cross-corpus edges are ordinary, not dangling | **OInv** |
| W11 | a world entity is never addressed by a coordination address, or the reverse | US† |
| W12 | renaming a project does not break coordination references | **OInv** |
| W13 | corpus identity is minted, opaque, stable / state identity is over content | **OInv** / **CS** |

**R — computation and reproducibility**

| id | assertions | classes |
|---|---|---|
| R1 | an incomplete closure is refused; no `run` node is minted | RF† |
| R2 | the address moves on every closure member; the recipe holds nothing post-execution | **CS** |
| R3 | two executions of one recipe are two runs | **CS** |
| R4 | scope is derived, never authored; it rests on evidence | CA† + RF† |
| R5 | belief does not depend on availability in this checkout | **OInv** |
| R6 | un-replayability creates no verification and moves no state | **OInv** |
| R7 | the two run shapes are structurally exclusive | RF† |
| R8 | the equivalence rule cannot be chosen after outputs are seen | **CS** |
| R9 | `inconclusive` never collapses into `passed` or `failed` | ED† + EB† |
| R10 | runs begin at the most upstream held form | RF† |
| R11 | dataset-production replay is bitwise; forking identity does not cancel the verdict | RF† + **CS** |
| R12 | the boundary refuses a run naming no frozen spec / the bound is pinned | RF† / **DL** |
| R13 | `code_identity` captures what ran, not what was committed | **CS** |
| R14 | identity canonicalization is **injective** and domain-separated | **CS** |
| R15 | execution is confined to the closure it declared | RF† |
| R16 | non-conformance blocks scope, not just reporting | EB† |
| R17 | a recipe cannot disagree with its spec; seeds are pre-declared | RF† |
| R18 | scope evidence is embedded and identity-bearing | **CS** |
| R19 | derivation is validated at import and audit / neither mounting nor a raw write is an epistemic event | CA† / **DL** |
| R20 | the nondeterminism contract cannot contradict itself; stream totality reaches both records | RF† + ED† |
| R21 | a recipe says what to execute, portably | *unclassified — direct requirement* |
| R22 | the assessment facet is derived through the ordinary API | US† + CA† |
| R23 | a produced dataset, its ancestry and its durable basis are minted by the boundary | CA† |

**C — correction lifecycle**

| id | assertions | classes |
|---|---|---|
| C1 | the target is byte-identical, addressed and resolvable after retraction | **OInv** |
| C2 | attribution, reason and ground are required at the boundary | RF† |
| C3 | the digest covers the enumeration, never exact corpus states | **CS** + **OInv** |
| C4 | subtraction is direction-free — support and refutation subtract identically | **OInv** |
| C5 | chain, not toggle; standing is sibling-aware | **WF** + **CS** |
| C6 | verification retraction recomputes admission fail-closed | **FC** |
| C7 | retiring both routes yields `not-certified`, never a silent selection | EB† |
| C8 | a retracted snapshot is refused where recomputation already happens | RF† |
| C9 | narrowing is succession plus retraction, never mutation behind an identity | **CS** |
| C10 | ineligible or ill-formed targets are unspellable | US† |

**X — world-index packaging**

| id | assertions | classes |
|---|---|---|
| X1 | a published epoch is immutable; members are never individually deleted | US† |
| X2 | publication is crash-atomic; `current` survives a persistence cut | DU† |
| X3 | belief never reads `current` | RF† |
| X4 | the registry is append-only through every API / the negative bound | US† / **DL** |
| X5 | a duplicate `corpus_id` is refused at admission and detected at build | RF† |
| X6 | terminal states are terminal / every status is invariant under arrival order | US† / **OI** |
| X7 | admission is the cross-root commit point | RF† |
| X8 | every epoch answer is bound-stamped; an unstamped answer is unspellable | US† |
| X9 | maps and anchored head members share one coherent state view per corpus | DU† |
| X10 | receipts resolve rule bindings against the epoch | **CS** |
| X11 | GC's two hard rules hold; severed references are named | RF† |
| X12 | the maps are complete over coverage, and their receipts can refute | ED† + **CS** |

**N — normative contract**

| id | assertions | classes |
|---|---|---|
| N1 | contract succession retains every id and names its predecessor | **CS** |
| N2 | **every oracle row can fail** — a row that passes under sabotage is itself defective | OF† |
| N3 | the fixture set is the normative half of rule identity; derivations name their exact binding | **CS** |
| N4 | certification is recomputable; recomputation detects disagreement, not authorship | **WD** + CA† |
| N5 | certification binds contract, rule **and** implementation | **CS** |
| N6 | witness coverage is total per instrument, in both directions | ED† |
| N7 | uncertified degrades and never blocks; standing is discovered from explicit inputs | EB† |
| N8 | certification retraction is prospective, not transitive | EB† |
| N9 | no falsification evaluator or execution path exists | US† |
| N10 | every legacy check appears in exactly one disposition class | ED† |

**L — tamper-evident log**

| id | assertions | classes |
|---|---|---|
| L1 | registration precedes application; no unregistered cooperative path | EO† + US† |
| L2 | settlement gates every absence test | EB† |
| L3 | valid-prefix truncation refutes; interior damage is `malformed` | ED† |
| L4 | chain removal refutes against any surviving anchor, bound to its subject | **CS** |
| L5 | the unanchored tail is the pinned residue | **DL** |
| L6 | the genesis baseline reaches pre-log history — once anchored | **DL** |
| L7 | intent claims are exactly as wide as stated | EB† |
| L8 | cross-chain order exists only through world-ancestry-ordered cuts | EO† + **DL** |
| L9 | anchor evaluation is total over the observer set, never best-reachable | ED† |
| L10 | a fork is a new chain; a replica is the same chain | **CS** |
| L11 | the world chain is anchored only by export | RF† |
| L12 | one state vocabulary; every typed state class round-trips | ED† |
| L13 | **logged is not permitted** — a removal is in the timeline *and* verification still fails | **DL** |

**D — domain extension boundary**

| id | assertions | classes |
|---|---|---|
| D1 | `nodes` assigns no domain semantics | US† |
| D2 | the dataset address is unchanged under facet addition; node and corpus identity move | **OInv** + **CS** |
| D3 | a bare namespace is refused; the three unresolved states stay distinct | RF† + ED† |
| D4 | `ProfileSpec` is the only per-kind source; `KindSpec` is compiled | US† + CA† |
| D5 | reformatting `corpus.yaml` does not move the identity; content does | **OInv** + **CS** |
| D6 | consulted contracts enter belief; activated-but-unconsulted ones do not | **CS** + **OInv** |
| D7 | W5 survives unamended; contract agreement holds across a derivation | **OInv** + PC† |
| D8 | domain contributions compose; same-namespace collisions refuse | RF† + **WD** |
| D9 | a practice declaring a vocabulary or schema is refused | RF† |
| D10 | no API retracts, supersedes or attributes an individual facet payload | US† |

### 5.3 What the existing taxonomy covers

The 113 rows contain **128 assertions**, since a row may state a property in a
positive arm and pin its limit in a negative one.

| label | rows | assertions |
|---|---|---|
| **CS** commitment sensitivity | 26 | 26 |
| **OInv** observational invariance | 17 | 18 |
| **DL** declared limit | 12 | 12 |
| **WD** well-definedness | 4 | 4 |
| **FC** fail-closure | 3 | 3 |
| **OI** order-independence | 1 | 1 |
| **WF** well-founded recursion | 1 | 1 |

**Both units, stated separately, because they measure different things:**

- **54 of 113 rows** contain at least one §3.4 label; **59 contain none.** This
  is a *row-level lower bound* on the gap — a row counts as covered when any one
  of its assertions is covered, so rows like G1 and G2a count as covered while
  part of their content lies outside the taxonomy.
- **59 of 128 assertions** carry a §3.4 label; **69 do not.** This is the
  coverage figure the classification is per-assertion in order to produce.

The taxonomy reaches **under half** of what the corpus asserts, and the half it
misses is not a scatter.

### 5.4 The residue, and why it exists

The 69 uncovered assertions are not miscellaneous. They are **covered by nine
recurring classes** — a cover, not a partition: the class counts sum well above
the assertion count because one assertion can carry several labels, and the
classes were derived to describe the residue rather than to divide it.

There is a structural reason the taxonomy missed all of them: **§3.4 derived its
laws from the four readings.** `standing`, `admission`, `eligible` and `B` are
functions of a configuration, so every law derived from them is a law about
*values in a state*. Roughly half of what the banked tables guarantee is about
**`step` instead** — what the system will accept, in which order, and what
cannot be expressed at all. A taxonomy built from the readings could not reach
them, and the gap is exactly as wide as that omission predicts.

| label | statement | rows |
|---|---|---|
| **RF†** refusal | `step` returns `Refused` on a stated precondition; nothing is written | 28 |
| **US†** unspellability | the act has no representation at all — tested statically, not by attempting it | 15 |
| **ED†** exhaustive discrimination | a fixed outcome set, no member collapsing into another, no unclassified residue | 12 |
| **EB†** evidence-bounded inference | a strong outcome requires a witness: `strong(r) ⟹ ∃e. Witness(e, r)` | 9 |
| **CA†** construction authority | each value has a **closed set of permitted constructors** — authored, derived, compiled, or boundary-minted — and no other path constructs it | 9 |
| **PC†** path coherence | two sanctioned paths from equivalent inputs must agree; the square commutes | 4 |
| **EO†** effect ordering | one effect durably precedes another within a single act | 3 |
| **DU†** durable atomicity | crash-atomic and survives a persistence cut (gated on atoms A6–A8) | 2 |
| **OF†** oracle falsifiability | every oracle row must be capable of failing; one that passes under sabotage is defective | 1 |

**RF and US must stay distinct.** Refusal is a runtime answer — the act was
expressible, the boundary declined it. Unspellability is a type-level absence:
G5's "assert no such kind exists", S8's static assertion, N9's "no evaluator
exists", D10's "no API". The designs use both deliberately, and collapsing them
would lose the difference between a guard and a design that needs no guard —
the difference the house rule *explicit over defensive* turns on.

**CA† replaces the first draft's "derivation, not authorship", which was
backwards on its own evidence.** W4 requires a merge to be **authored** and
forbids deriving content by precedence; classifying it as "derived, no authored
path" reversed it. What the rows share is not that authorship is absent but that
the **permitted constructor set is closed and named**: authored for W4, derived
for W8a and R4, compiled for D4, boundary-minted for R22 and R23. Stated that
way each row keeps its meaning.

**EB† is the largest unnamed principle in the corpus, and it is wider than a
default.** Comp §7.1 names its missing-value special case once — *"a failure to
look is not a finding of absence"* — and counts three appearances across
`t077`'s determinism test, world §5.1's `not-present` ≠ `unknown`, and its own
availability rule. But several of the nine rows are about **bounded inference**
rather than a default for an absent value: certification cannot be inferred
(N7), retraction effects do not propagate transitively (N8), and an intent claim
cannot widen beyond what it stated (L7). The unifying form is that a strong
reading requires a witness; the witness and the strength relation stay
reading-specific.

**PC† is path coherence, and only four rows earn it.** The first draft called it
"agreement" and stretched it over six. Defined properly — two sanctioned paths
from equivalent inputs must agree, as a commuting square — it fits S1 and S1a
(two closure algorithms), S7 (two enforcement boundaries), and D7 (contract
agreement across a derivation). W7 and R21 do not, and are reclassified in §5.5.

### 5.5 Assertions that classify as nothing

**Two rows, deliberately left unclassified:**

- **W7** — *views see the whole world, not a directory.* This names a view's
  scope. It is a direct functional requirement, not an instance of a reusable
  law, and forcing it into PC† required reading "two agreeing paths" into a row
  that states none.
- **R21** — *a recipe says what to execute, and says it portably.* Portability
  is promised; two-engine equality is not textually asserted. It would earn PC†
  only if the banked row were amended to say so, which §5 has no authority to do.

**Leaving them unclassified is the correct result, not a shortfall.** A
guarantee corpus is entitled to contain direct requirements that are not
instances of any law, and a taxonomy that absorbs every row is one that has
stopped discriminating. C4, by contrast, was genuinely misfiled: `standing`
never reads whether its target supports or refutes, so subtraction being
direction-free *is* observational invariance of that reading, and the first
draft's singleton "uniformity" class is withdrawn.

The remaining honest caveat: the nine classes of §5.4 were derived **from** the
residue, so their coverage of it is not independent evidence. What can be said
is that the residue was coherent — nine recurring classes, no class of size
zero, and only two rows left over.

### 5.6 What this changes

**§3.4's law table is incomplete, and structurally so.** M₀ states laws for the
readings and none for `step`. Refusal, unspellability, construction authority,
effect ordering and durable atomicity are properties of the transition function,
and nothing in §3 currently expresses them.

**Two of the classes are meta-level and do not belong in a system-law table.**
`OF†` constrains the **oracle suite** — that every row can fail — not `Ω`,
`step`, or any reading. `DL` is likewise documentary: it records what the system
cannot detect. Both are **assurance laws**, and grouping them with the others
would put a claim about the tests beside claims about the system.

The vocabulary §8 should draw on, stabilized:

| group | labels |
|---|---|
| **transition / type laws** | RF, US, CA, EO, DU |
| **state laws** (readings) | WD, OI, OInv, CS, WF, FC |
| **result laws** | ED, EB |
| **relational law** | PC |
| **assurance laws** | OF, DL |
| — | *plus unclassified direct requirements, explicitly permitted* |

**§5 freezes none of this.** The nine proposed labels keep their † marks until
adoption is decided; what §5 establishes is that ρ needs a vocabulary of roughly
this shape to state what M\* preserves or amends, and that manufacturing one
class per residue shape is not that vocabulary.

## 6. M\* — the typed claim calculus

This is the first section that **revises**. Everything above transcribes and
cites; what follows proposes, and §8 records what each proposal preserves,
amends or invalidates.

### 6.1 `Operator`, not `predicate`

Inside the calculus the relation term is an **`Operator`**. §2.9 (d) recorded
that `predicate` already names two unrelated objects — a relation instance's
free-string edge label, matched by exact equality, and the proposition's
vocabulary term inside an identity hash — and §4.1 of the kernel uses it in a
third sense, for a closed signature as opposed to a roster. A formal notation
that inherits a three-way overload starts by making its own statements
ambiguous.

`Operator` is therefore the name throughout M\*. `predicate` survives in M₀ for
relation instances, where it is what the substrate actually calls the field.

### 6.2 The type

```text
Claim  =  Σ (op : Operator).  Args(op) × Qualifiers(op) × Polarity(op) × Layer(op)
```

A claim is a **dependent sum**: choosing the operator determines the *types* of
everything else. The four indexed families are supplied by the operator's term
contract (§7).

Two levels have to stay distinct, and the first draft of this section collapsed
them. What a contract *declares* is a **schema**; what a claim *carries* is an
**inhabitant** of the type that schema induces. Writing `Args(op)` for both is
what made "wrong-sorted arguments are unconstructible" a slogan rather than a
consequence.

**Arguments.**

```text
arity(op)    :  ℕ                                          declared
ArgSort(op)  :  Fin(arity(op)) → Sort                      declared, one sort per slot

Args(op)     =  ∏ (i : Fin(arity(op))).  Referent(ArgSort(op, i))      induced
```

`Args(op)` is a **dependent product over slots**, and `Referent(s)` is the type
of bound referents of sort `s` — a `term` identifier drawn from the vocabulary
that sort declares (§2.9 (b) recorded that today they are bare strings). A slot
of the wrong sort is not a rejected value: `Referent(gene)` and
`Referent(phenotype)` are different types, so no term of one inhabits the other.
A slot that cannot be bound at all cannot be filled, which is what §6.6 is
about. Arity is declared per operator because it is not universally 2 —
`subtype-of` and `binds` do not take the same number or the same kinds of thing.

**Qualifiers.**

```text
Dims(op)             :  a finite set of dimension identifiers        declared
RestrictionSort(op)  :  Dims(op) → Sort                              declared, per dimension

Qualifiers(op)       =  the qualifier structure over ⟨Dims(op), RestrictionSort(op)⟩   induced
```

`Dims(op)` is the set of dimensions **permitted** for this operator — a
population restriction is meaningless for a structural operator — and
`RestrictionSort(op)(d)` fixes what a restriction on `d` may be bound to, so a
restriction is sorted exactly as an argument is. §6.4 defines the structure
itself, and states which fragment of it this pass inhabits.

**Polarity and layer.**

```text
signApt(op)  :  Bool                                       declared
Polarity(op) =  { positive, negative, unsigned }   if signApt(op)
             =  1                                  otherwise — the unit type

Layers(op)   :  a non-empty finite set of layer identifiers          declared
Layer(op)    =  that set, as a type                                  induced
```

Sign-aptness is a property of the operator, not of a central roster (§6.3).
`Layers(op)` is non-empty by construction — an operator admitting no layer would
make `Claim` uninhabited at that operator — and it is often a singleton:
`subtype-of` is structural and nothing else.

### 6.3 Unconstructibility inside the model; refusal at the boundary

The current model pairs a flat `Predicate` enum with a flat `Polarity` enum and
a **hard-coded three-element roster**, `SIGN_MEANINGFUL_PREDICATES`, consulted
by a validator that raises when the pair disagrees. That is a roster wearing a
predicate's clothes — the exact shape substrate §4.2.1 names and rejects, that
computation §1.3 records as already retired elsewhere, and that kernel §4.1
states as doctrine: *"A class is a roster — every new kind must be remembered
into it, so it has a hole by construction. A signature is a predicate."*

Under the dependent sum the invalid combination is unspellable:

```text
Polarity(op)  =  { positive, negative, unsigned }     when the contract declares op sign-apt
Polarity(op)  =  1                                    otherwise — the unit type
```

For a sign-less operator the polarity slot has **exactly one inhabitant**, so no
value can be wrong there and no `not_applicable` sentinel is needed. The
`SIGN_MEANINGFUL_PREDICATES` frozenset is **retired**, not relocated: sign-aptness
becomes a field of each operator's own contract, which is also what makes the
vocabulary extensible — a new operator declares its own sign-aptness instead of
requiring an edit to a central set.

The same argument disposes of the other two validators by construction: an
inadmissible layer is not a rejected value but an uninhabited type, and an
argument of the wrong sort has no slot to occupy.

This is *explicit over defensive* applied to the type rather than the guard, and
inside the model it classifies as **US†** — the invalid combination is
unspellable, not refused.

**But the model is not the only thing that produces claims.** Serialized YAML,
imported records, a restored corpus and a raw write can all *express* a
combination the type cannot hold. Unconstructibility eliminates the internal
guard; it does not eliminate the boundary. The two are different laws at
different places, and collapsing them would leave the actual entry points
unruled.

```text
decodeClaim  :  WireClaim × ProfileSpec × ResolutionSnapshot
                ──▶  (Claim × BindingCheckReceipt) + Refused
```

Decoding is where sign-aptness, arity, argument sorts, permitted dimensions,
restriction sorts and admissible layers are **checked against the profile**,
because only there does an untyped external value meet the contract that types
it. `ProfileSpec` is the second parameter for the reason D4 makes it the sole
compiled per-kind source: the operator contracts a decode consults are compiled
profile contracts, not a roster the decoder carries. The third parameter and the
receipt are §7.2's — referent membership depends on vocabulary availability,
which is in neither of the first two, and without them the decode would not be a
function of its arguments.

The split is therefore:

| where | law | what it means |
|---|---|---|
| the typed constructor, inside the model | **US†** | there is no ill-typed `Claim` value to guard against; internal code may trust a `Claim` unconditionally |
| `decodeClaim`, on every import, deserialization and restore | **RF†** | an ill-formed wire claim is refused as a value, and nothing is minted |
| a raw write that bypasses the boundary | neither | it produces an **audit finding**, on the same terms as every other bypass in the system |

The third row is the honest one. A hand-edited file on disk can hold bytes that
no constructor and no decode would produce; that case is detected, not
prevented, and it belongs to the audit surface rather than to the type. What the
dependent sum buys is that *once decoded*, no downstream reader needs to
re-check — the check happens exactly once, at the one place an external value
enters.

### 6.4 Qualifiers — kernel structure, domain terms

This is where the founding example lives. Kernel §4.1 exists because editing
*"X affects Y in adults"* into *"X affects Y in all humans"* must not be a
revision — and *"in adults"* is not a subject, an object, a polarity or a layer.
Under a bare 5-tuple with `statement` demoted, both claims have identical typed
values and one identity, and **the exact failure the kernel was built to prevent
becomes invisible**. The qualifier is therefore not an optional enrichment; it
is what makes the typed form admissible at all.

**`Qualifiers(op)` is a typed structure, and this pass inhabits one fragment of
it.** The temptation is to declare the structure to *be* a dimension-keyed map
and move on. That would be a quiet commitment to a logic, because a map has no
quantifier scope and no order:

```text
∀ population. ∃ condition. P      ≠      ∃ condition. ∀ population. P
```

A map also permits at most one restriction per dimension, so a claim restricted
to two populations, or to a range, has no representation. Those are real
expressive limits, and the honest move is to name them as the boundary of this
pass rather than to let a convenient encoding decide the logic by default.

So the kernel rules three things about the structure and defers the fourth:

1. it is a **canonical, inspectable typed term** — not an opaque string, and not
   a rendering of one (§6.7);
2. every restriction is a **bound referent, never prose**, sorted by
   `RestrictionSort(op)`;
3. every restriction carries an **explicit quantifier**, kernel-owned and
   closed: `{ generic, universal, existential }`;
4. its **grammar is versioned**, and a later revision may extend it to express
   scope order and composition without invalidating terms already written under
   the earlier grammar.

The fragment this pass inhabits — call it the **flat fragment** — is exactly the
dimension-keyed map: each permitted dimension carries at most one
`⟨quantifier, restriction⟩`, and dimensions are mutually independent, so scope
order is not merely unrepresented but **irrelevant** within the fragment.

```text
QualifiersFlat(op)  =  a finite partial map,  d : Dims(op)  ↦  ⟨ quantifier, Referent(RestrictionSort(op, d)) ⟩
```

Anything richer — a scoped alternation, a disjunction of restrictions, a
quantitative range — is **refused at `decodeClaim`** (§6.3) rather than
flattened into the map. Flattening is the failure mode to avoid: it would
produce a well-typed claim that means something other than the span it came
from, which is the scope-widening failure kernel §4.1 exists to prevent,
committed by the encoding instead of by an editor.

**The kernel owns the structure; domains own what fills it.** Which dimensions
exist — `population`, `condition`, `regime`, `time-scale` — is domain
vocabulary, declared per operator by its contract, along with each dimension's
restriction sort. That split is D3 applied one level up, and it is what keeps
`Claim` from silently becoming a biology type: a qualifier structure designed
around populations would breach the domain boundary inside the kernel's most
load-bearing object.

Under this structure the founding example separates mechanically. Kernel §4.1's
edit is *"X affects Y in adults"* → *"X affects Y in all humans"*, and the two
differ in both slots the qualifier provides:

```text
c_adults  = ⟨ affects, [X, Y], { population ↦ ⟨generic,   term:adults⟩ }, positive, causal ⟩
c_humans  = ⟨ affects, [X, Y], { population ↦ ⟨universal, term:humans⟩ }, positive, causal ⟩

π_claim(c_adults)  ≠  π_claim(c_humans)
```

*"in adults"* is a generic claim about a population; *"in all humans"* is
universal over one — so the quantifiers differ, and the restriction identifiers
differ independently of them. Either difference alone separates the identities:
holding the quantifier fixed, `term:adults ≠ term:humans` still forks, which is
the case that matters, since the widening a reviewer would miss is usually a
restriction swap and not a visible *"all"*.

Two identities, a `supersedes` link, and every prior assessment still bound to
the claim it actually assessed — with no prose anywhere in the projection.

### 6.5 The canonical projection, and why `statement` leaves identity

**Every position in the projection is an identifier.** A symbol is what a term
is *called*; an identifier is what it *is*. The distinction is the whole content
of the binding rule already settled for vocabulary (D6, D §8): **claim identity
binds the term identifier, and the consulted vocabulary contract enters
`belief_input_digest`.** Putting the contract release into claim identity would
fork every claim on every ontology release; leaving the contract out of belief
entirely would let a reinterpretation of a term move a belief silently. The
projection carries identifiers, and the release travels the other channel.

```text
π_claim(c)  =  ⟨ operator      — the operator's term identifier,
                 args          — by slot index, each a bound referent identifier,
                 qualifiers    — sorted by dimension identifier, each
                                 ⟨ quantifier tag, restriction referent identifier ⟩,
                 polarity      — the polarity tag, always emitted; the
                                 sign-inapt tag when Polarity(op) = 1 (§7.5),
                 layer ⟩       — the layer term identifier

I_claim(c)  =  H( tag_claim ‖ encode(π_claim(c)) )        under science.identity.v1
```

Five positions, five kinds of name, and none of them prose:

| position | what enters the hash | owned by |
|---|---|---|
| operator | the operator's **term identifier** | a domain contract, always (§7.1) |
| argument, per slot | the **referent identifier**, in the sort's vocabulary | a domain contract |
| qualifier key | the **dimension identifier** | a domain contract |
| qualifier restriction | the **referent identifier**, in the dimension's restriction sort | a domain contract |
| quantifier | a **canonical kernel tag** from the closed set | the kernel |
| polarity | a **canonical kernel tag** from the closed set | the kernel |
| layer | the **layer term identifier** | the base contract |

The two kernel-owned positions are tags rather than contract-issued identifiers
because their sets are closed and kernel-owned. Their canonical encodings are
pinned by the base contract (§7.1) — a tag that is stable in prose but unstable
in bytes would fork identities across implementations — and changing one is the
severe case §7.4 row 5 records.

`I_claim` therefore names an identity that survives an ontology release, and
`belief_input_digest` — not `I_claim` — is what moves when the contract behind
one of those identifiers is reinterpreted. §7 defines the contracts these
identifiers are issued by.

**`statement` is excluded from identity**, which is precisely the move kernel
§4.1 already made for `title`, with §4.1's own argument carrying it the last
step: *"A field cannot be both hand-editable prose and an identity input."* Once
the typed form is normative, `statement` is in exactly the position `title` was.

But "a derived gloss, freely overridable" was still one field with two
construction authorities — the defect CA† names, committed in the sentence that
was supposed to fix it. It splits in two:

| | `render(Claim)` | `display_statement` |
|---|---|---|
| produced by | a **deterministic function** of the typed form and the consulted vocabulary | **authored** by a human |
| stored | **no** — computed on read | yes, optional, may be absent |
| authority | derived | authored |
| in `π_claim` | no | no |
| in belief or matching | no | no |

Both are identity-inert; neither is ever read by identity, belief, standing or
estimand matching. Making `render` unstored is what keeps it honest: a stored
rendering is a cache that can disagree with what it renders, and a disagreement
between the gloss and the claim is exactly the confusion this section removes.
An authored `display_statement` is then an ordinary annotation with one
authority and no derived counterpart to drift from — a reader may prefer it, and
nothing downstream may consult it.

Three consequences worth stating.

**Kernel §11's normalization question largely dissolves.** It asks whether
whitespace, casing, term-synonym resolution and numeric formatting participate
in the hash, and frames the dilemma: *"too loose and a scope change slips
through as a revision; too tight and every typo forks the identity."* With no
prose in the projection there is no whitespace, casing or typo to rule on. What
remains is canonicalization of **typed values**, which `science.identity.v1`
already supplies, plus the separate question of whether two *referent terms* are
synonyms — which belongs to vocabulary binding (D §5), not to claim identity.

**The residual natural-language problem moves to extraction, where the system
already accounts for it.** Kernel §4.2 frames extraction as one-sided and
bounded — *"does this span assert P?"* — and limitation 3 already treats it as a
fallible computation with a measured 25–40% field-level disagreement rate. That
is the right home for linguistic ambiguity: a computation with an error rate,
not an immutable identity.

**Limitation 5 becomes stateable.** The estimand-match residue — extraction
records an estimand but nothing forces it to *match* the claim — is a relation
between two typed objects only once the claim is typed. `match(claim_type,
estimand_type)` is a predicate that can be written; over prose it could never be
more than a human judgment.

### 6.6 Untypeable spans produce work, not records

An extracted span that cannot be typed — no operator fits, or an argument cannot
be bound to a referent — **mints nothing**. The boundary refuses (**RF†**), and
the span becomes an ordinary typing-work item in the project-scoped tier (§2.4),
which needs no new kind and no fallback record.

The refusal reaches further than it first appears, and the reason is structural:
`source-assertion`'s identity basis **contains the proposition identity** (world
§4.2). A source-assertion for an untypeable claim is therefore not merely
disallowed — it is **unconstructible**, because one of its identity components
does not exist. No constructor and no `decodeClaim` path admits untyped prose
into the record set as an assertion; a raw write that fabricates one is an audit
finding, on the terms §6.3 already set out.

**The cost, stated plainly.** Coverage of the literature becomes gated by the
operator vocabulary's expressiveness. Kernel limitation 4 already says real
claims will not fit nine terms cleanly; under this design an unfitting claim is
not degraded, it is **queued**. That makes the vocabulary's extension rule
load-bearing for *throughput*, not only for correctness.

**This queue is a new operational consequence, not a banked precedent.** Kernel
limitation 1's ranked work queue is *widely-asserted-but-unassessed
propositions* — claims that exist, carry assertions, and lack assessments. An
untypeable span has no proposition at all and therefore cannot appear in that
row. Reusing the project-scoped `task` tier to hold it is sensible and needs no
new kind, but it introduces a **second** backlog with a different membership
condition and a different owner: the first is answered by running an analysis,
the second only by extending a vocabulary. §11 records it as such; nothing in
the kernel currently sizes it.

### 6.7 What is preserved for entailment, without defining it

Once a qualifier carries an explicit quantifier over a bound restriction
referent, `c_adults` and `c_humans` **retain the typed information a future
entailment relation would need**, and may become comparable under it. That is
the claim §6 makes, and it is weaker than the one the first draft made.

The first draft said the two were "ordered by entailment." They are not, and
`term:adults ⊆ term:humans` does not establish it. At least three things stand
between restriction inclusion and claim entailment:

| | why inclusion is not enough |
|---|---|
| operator variance | an operator need not be monotone in a restriction, and none has yet declared a variance |
| quantifier semantics | `generic` is not `universal` weakened — a generic claim tolerates exceptions, so it neither implies nor is implied by the universal over the same referent |
| ontology subsumption | `term:adults ⊆ term:humans` is a fact of a vocabulary contract at a release, not of the identifiers, and D6 deliberately keeps the release out of claim identity |

There is also a substantive reason to distrust the intuition rather than merely
its formalization: a statistical effect can **reverse** across a subpopulation,
so a claim true of adults may be false of humans, and a relation that concluded
otherwise from inclusion alone would be unsound about the world, not just
underspecified.

**§6 therefore does not define it.** Defining subsumption would pull ontology
reasoning, quantifier interaction, operator variance and partial orders over
restriction domains into a section whose job is the identity of a single claim.

What §6 *does* is keep such a relation **definable later**, which is a
requirement on the encoding and rules three of them out:

| ruled out | why |
|---|---|
| an opaque canonical string for the whole qualifier structure | nothing can be compared inside it |
| pre-normalizing restrictions to a most-general form | destroys the distinction being preserved |
| folding qualifiers into the operator identifier (`affects-in-adults`) | multiplies terms and loses the factorization the structure provides |

The estimand-match residue of limitation 5 is **related to** this relation and
not assumed to be the same one. `match(claim_type, estimand_type)` asks whether
a study's estimand answers a claim; entailment asks whether one claim follows
from another. They plainly share machinery — both compare typed restrictions
under a vocabulary — but whether one is definable from the other is an open
question, not a shortcut §6 may take.

Both are recorded in §11 as required-future with their motivation, so that a
later design inherits the constraint rather than rediscovering it.

## 7. M\* — term contracts and referent typing

§6 wrote `Operator`, `Sort`, `Dims` and `Layers` as though something issued
them. §7 says what does. It answers D §12's last open question directly — *"whether
the predicate vocabulary becomes a domain contract like any other"* — and it
closes the two halves of kernel limitation 4 that the nine-term roster left
open: **who owns the vocabulary, and by what rule it extends**.

A third half the roster never had is opened rather than closed. Once arguments
and restrictions are bound referents instead of strings, binding them acquires
a lifecycle, and §7.2 finds that lifecycle unspellable under the banked
correction rules. §7 takes the diagnostic fork deliberately and says so; the
claim being made is narrower than "limitation 4 is closed."

### 7.1 The contract split

The vocabulary is a contract like any other, but it does not sit in **one**
contract, because §6.4's D3-one-level-up ruling already divides it. The split
follows the existing base/domain line exactly:

| declared by | what it owns | why there |
|---|---|---|
| the **`science` base contract** | the claim grammar version; the closed quantifier tag set; the closed polarity tag set; the layer vocabulary; the canonical byte encoding of every kernel tag | these are the kernel-owned structure of `Claim` — the parts §6.4 refuses to let a domain choose |
| a **domain contract** | operator identifiers and their declarations; dimension identifiers; sort identifiers and their vocabulary bindings | `affects` is a claim *about* biology; the kernel has no opinion on which relations exist |

**Operators are domain-issued without exception**, and the base contract may not
issue one. The rule stays uniform for two reasons: a base-issued operator would
have the kernel opining on which relations exist, which is the boundary §6.4
draws; and because the base contract is unconditionally consulted, a base-issued
operator would sit outside the closure walk that every other operator goes
through, giving one class of operator a different belief rule for no reason.
Domain-neutral relations — `subtype-of` and its kin — belong to a
general-purpose domain contract, since nothing requires a "domain" to be a
natural science. §6.5's table said "a domain (or the base) contract"; that
hedge is withdrawn.

**D6's asymmetry survives; D6's trigger set does not.** The unconditional-base /
conditional-domain rule is exactly right and is inherited unchanged. But D6
computes domain participation by walking a derivation's closure and collecting
**the namespace of every facet it reads**, and claims introduce trigger kinds
that walk does not have: a contract can now be reached through an operator
identifier, a dimension identifier, a sort identifier, or a referent identifier
in a bound vocabulary — none of which is a facet key. A walk that collected only
facet namespaces would omit the contract declaring `affects` from a belief
derived over a claim at `affects`, and it would fail **open**, exactly as D
limitation 2 warns.

So the amendment is stated, not glossed:

> **Amendment to D6 (for §8 and D6's oracle).** The consulted set includes every
> contract reached through a **claim schema** — the contract declaring the
> operator, each dimension, each argument and restriction sort, and the
> vocabulary binding each sort resolves through — in addition to every contract
> reached through a facet namespace.

With that, the reach is what §7.1 wants and no wider: a derivation interpreting
a claim consults the contract declaring its operator, so a biology contract bump
still leaves beliefs over chemistry claims undisturbed.

```yaml
# science base contract — the kernel-owned structure
claim_grammar:
  version: 1
  quantifiers: [generic, universal, existential]
  polarities:  [positive, negative, unsigned]
  sign_inapt_tag: inapt          # the unit inhabitant; see §7.5
  layers:      [causal, structural, statistical, methodological]
```

```yaml
# a domain contract — biology
sorts:
  molecular-entity:
    vocabulary: {namespace: HGNC, release: "2026-05-01"}
  phenotype:
    vocabulary: dataset:<content-identity>
  condition:
    vocabulary: {namespace: MONDO, release: "2026-07-01"}
  population-group:
    vocabulary: <population vocabulary — none selected; see §11>

dimensions:
  population: {restriction_sort: population-group}
  condition:  {restriction_sort: condition}

operators:
  affects:
    arity: 2
    arg_sorts: [molecular-entity, phenotype]
    sign_apt: true
    layers: [causal]
    dimensions: [population, condition]
```

The `population-group` binding is a **placeholder, not a proposal**. No
population vocabulary has been selected, and none of the obvious candidates is
one — MONDO is a disease ontology, and appears above bound to `condition`, which
is what it is for. As written that contract would be **refused at load** under D
§5, since a binding is exact or absent; it stands here to show that the sort
mechanism does not supply the vocabularies, and §11 records the selection as
open. It is also the concrete form of §6.6's cost: a claim qualified by
population is untypeable until some contract binds a population vocabulary.

Every field of the operator declaration is one of §6.2's declared schemas, and
nothing else is: `arity`, `arg_sorts`, `sign_apt`, `layers`, `dimensions` are
exactly `arity(op)`, `ArgSort(op)`, `signApt(op)`, `Layers(op)`, `Dims(op)`.
`RestrictionSort(op)` is resolved through the dimension declarations rather than
restated per operator, so two operators sharing `population` cannot disagree
about what a population restriction is bound to.

The **layer set is base-owned but per-operator restricted** — `layers: [causal]`
selects from the base vocabulary and may not extend it. A domain that could mint
a layer would be redefining what kind of thing a claim is, which is the boundary
§6.4 draws.

### 7.2 Sorts and referent typing

A sort is a name bound to a vocabulary, and D §5 already rules how that binding
is written: a held ontology dataset by content identity, or a namespace with an
explicit release. A bare namespace is refused. §7 changes nothing about the
**form** of a binding — it uses the binding as the definition of `Referent` —
but it does refine the **outcomes** of resolving through one, below:

```text
Referent(s)  =  the terms of the vocabulary that sort s binds
```

**Binding a referent is not the same as resolving one.** This matters more for
claims than for facets, because a claim may legitimately name an ontology term
in a corpus that does not hold that ontology's bytes.

#### `unknown` cannot carry the decision, and D3 must be amended

The first draft of this section refused on D §5's `unknown`, treating it as
positive evidence that a term is not in its vocabulary. It is not.
D §5 defines `unknown` as a **disjunction**: the term is outside the bound
vocabulary, *or* the binding's namespace was never consulted. Refusing on it
would refuse a perfectly good identifier whenever a namespace went unconsulted —
and, worse, would report "not in the vocabulary" on evidence that no one looked.
That is the same error §7.2 was written to avoid, committed by the decoder.

The outcome set lacks the discriminator, so §7 **refines it**, which is a real
amendment to D §5 and to D3's oracle rather than a reading of them:

| outcome | when | replaces |
|---|---|---|
| `member` | the vocabulary was read and the term is in it | part of D §5's implicit success |
| `not-member` | the vocabulary **was read** and the term is **not** in it | half of `unknown` |
| `not-consulted` | the binding's namespace was never consulted — nothing was looked at | the other half of `unknown` |
| `not-present` | the bound dataset has a world address the consulted index records, but its corpus is absent | unchanged (world §5.1) |
| `not-available` | the dataset is identified but its bytes are not held here | unchanged |

`not-present` and `not-available` are carried over verbatim, so D3's
three-outcomes-stay-distinct test survives; what changes is that `unknown`
splits, and the two halves have opposite evidential force. `not-member` is a
finding; `not-consulted` is the absence of one.

> **Amendment to D §5 and D3 (for §8).** The term-resolution outcome is
> `member | not-member | not-consulted | not-present | not-available`. D3's
> oracle gains an arm asserting `not-member` and `not-consulted` are never
> collapsed, on the same terms it already asserts for `not-present` and
> `not-available`.

With the discriminator in place the decode rule is statable:

| outcome | `decodeClaim` | why |
|---|---|---|
| `member` | accept, check **performed and passed** | |
| `not-member` | **refuse** | positive evidence of a bad binding; admitting it would put an unbindable identifier into an immutable identity |
| `not-consulted`, `not-present`, `not-available` | accept, check **not performed** | all three are well-formed states, not errors; refusing would make claim typing require holding every bound ontology |

*"A failure to look is not a finding of absence"* appears nine times across five
banked documents; the bottom row is its **dual** — a failure to look is not a
finding of presence either. An unchecked binding must never be recorded,
reported, or later read as a checked one.

#### The decode interface needs an input and an output it did not have

§6.3 wrote `decodeClaim : WireClaim × ProfileSpec → Claim + Refused`. Both ends
are short. The decision depends on **vocabulary availability**, which is in
neither parameter, so as written the function is not a function — two holders
could decode identical inputs differently through ambient state, and which one
was right would be unanswerable. And "record the check as not performed" has no
carrier in the result type, so the record has nowhere to go.

```text
decodeClaim :  WireClaim × ProfileSpec × ResolutionSnapshot
               ──▶  (Claim × BindingCheckReceipt) + Refused
```

**`ResolutionSnapshot`** is the identified, content-derived state of vocabulary
availability the decode resolved against. Making it an explicit parameter is
what restores determinism: same three inputs, same outcome, anywhere, which is
the property §3.4's well-definedness law asks of every reading.

**`BindingCheckReceipt`** records, per referent position, which of the five
outcomes was obtained and under which snapshot identity. It is **not** in claim
identity: a corpus that happens to hold an ontology must not mint different
identities from one that does not, which would make `I_claim` depend on what
bytes are lying around — precisely what §6.5's identifier discipline exists to
prevent. It is emitted on the accepting arm only; the refusing arm produces no
claim and therefore no receipt.

It **reuses the boundary receipt's envelope, and is not the banked artifact.**
The first draft said "§2.3 already lists that as one of the four non-node
identity-bearers, so this needs no new kind." That was wrong on three counts
that matter. §2.3's boundary receipt is **nested inside a run** (comp §4.2,
§4.4b): it has no independent carrier, no lookup path by which a later process
could find it, and no `supersedes` lifecycle of its own. This receipt is
produced while decoding a claim rather than inside a run, and the use it was
introduced for — a later process finding it and recording that the check has now
been performed — needs exactly the independent carrier, lookup path and
succession the banked receipt lacks. Shared envelope, different artifact
contract, and the difference is what the next subsection has to resolve.

#### The correction path is unspellable under C, and §7 takes the diagnostic fork

The first draft said re-resolution to `not-member` becomes an audit finding and
"a human retracts." Nothing in the banked corpus permits that sentence. Four
independent rules block it:

| rule | consequence here |
|---|---|
| eligible targets are exactly the records whose standing a computed view reads — two arms, `node` and `route` (C §4) | a non-node receipt is in neither arm |
| propositions are **explicitly not retraction-eligible**; their lifecycle is `supersedes` (C §4) | the claim itself cannot be the target |
| audit mints nothing (5b §7.6) | detection cannot produce the correction |
| `supersedes` does not apply independently to a nested receipt | the receipt cannot be superseded in place |

So the correction, spelled out under the banked rules, would have to be some
combination of minting a corrected successor proposition, retracting the
**assessments and semantic snapshots** that carry the belief consequences, and
resolving the still-open `source-assertion` correction lifecycle (§2.9 (a)).
That is a lifecycle design, not a clause.

There are two clean options, and they are genuinely different designs:

1. **Binding checks stay diagnostic.** The receipt is a decode-time diagnostic
   with no independent addressing, no discovery path, and no succession. A
   `not-member` re-resolution is reported to a human, who decides what to do
   using the existing lifecycles. Persistence and correction remain **open**.
2. **Binding checks are promoted** to independently addressed records, with
   identity, a discovery path, succession, standing, and declared belief and
   eligibility consequences.

**§7 takes option 1, and says why option 2 is not available cheaply.** The
requirement that produced the question — needing independent supersession and
correction — *is* D's promotion trigger, the same one that decides when an
interpretation facet must become an interpretation node. Calling option 2 "no
new kind" would evade the design's own boundary, in the very document that
spent §6.4 defending that boundary. Option 2 is a kind with an eligibility
analysis, and this design's scope rule (§1) says M\* expands only when another
design question requires it.

**Therefore §7 does not close the referent-binding half of limitation 4.** It
narrows it: the ownership half is closed (§7.3), the term-identity and extension
half is closed (§7.3, §7.3a), and referent binding now has a defined check with
five honest outcomes and a decode boundary that cannot silently fabricate one.
What remains open is everything after the check — persistence, discovery,
succession, and the correction path for a claim found to name a term its
vocabulary does not contain. §11 records it, and records the promotion trigger
as the condition under which option 2 becomes the answer.

Two smaller questions go to §11 alongside it: when re-resolution runs at all,
and whether an unchecked claim may be assessed before its check is performed.

### 7.3 Term identity, and the extension rule

Kernel limitation 4's real content is not that nine terms are too few. It is
that a term has **no identity discipline**: nothing says what it means for two
uses of `affects` to be the same operator, and nothing says what may change
about `affects` without changing the claims already written with it.

Two identities, deliberately different in kind:

```text
operator term identifier   authored, stable, namespaced      enters claim identity
contract identity          content-derived, moves on edit    enters belief_input_digest
```

That pairing is what makes the first matrix row (§7.4) true. Making the term
identifier content-derived would fork every claim on every editorial change to a
contract; making the contract identity authored would let a reinterpretation
hide. Each is derived the way its job requires.

**The extension rule, in three cases.**

| operation | permitted | effect on existing claims |
|---|---|---|
| **issue** a new operator, dimension, or sort identifier | yes, freely — additive | none; no existing claim mentions it |
| **retire** an identifier | yes | existing claims keep their identity and stay readable; the **authoring constructor** may not select a retired identifier (§7.3a) |
| **redefine** an identifier — change `arity`, `arg_sorts`, `sign_apt`, `layers`, or `dimensions` | **no; refused at contract load** | would silently change what already-written claims mean |

The third row is the load-bearing one, and it is the guarantee tables' own
discipline — *extend, never renumber* — applied to vocabulary instead of to
guarantee ids. The reason is not aesthetic. Suppose `affects` flipped
`sign_apt` from `false` to `true`. Every stored claim at `affects` was
constructed with the unit polarity; after the flip the operator admits three
polarities, and a claim's meaning has changed underneath an identity that did
not move. Retiring `affects` and issuing `affects-directional` costs one
identifier and keeps every prior assertion bound to what it actually asserted —
the same trade kernel §4.1 made for propositions, one level up.

A change that is **purely editorial** — a description, a comment, an example —
moves the contract identity and therefore `belief_input_digest`, but touches no
declared schema and so needs no new identifier. That is D limitation 1's drift
case, inherited unchanged and not improved on here.

**Who owns a term** is then simply: the contract whose namespace issues it. That
is the answer to the "no owner" half of limitation 4, and it is the same answer
D gives for facets, which is the point — the predicate vocabulary is not a
special case needing its own governance.

### 7.3a What retirement and redefinition actually require

The two rules above are stated as though `decodeClaim` enforces them. It cannot
enforce either, and saying so precisely changes what has to be built.

**Retirement is not a decode-time property.** `decodeClaim` sees wire bytes. It
cannot tell whether those bytes are a claim being authored now or a historical
claim being restored from a backup, re-imported from an export, or replayed from
the mutation log — and the two must behave differently, or retiring an
identifier would make every corpus holding a prior claim un-restorable. Refusing
at decode would corrupt exactly the history retirement exists to preserve.

The enforceable split:

| path | rule |
|---|---|
| the typed **authoring** constructor | **cannot select a retired identifier** — it is not offered, on the same US† terms as every other unconstructible combination |
| **decode / import / restore** | accepts a retired identifier and types the claim against the **frozen retired declaration** |

Retirement therefore lives in authoring, not in validation, which is also the
only place it can live without a way to distinguish new bytes from old.

**That requires tombstones.** Typing a historical claim against a retired
operator means the declaration must still be readable, so a successor contract
**retains the retired declaration immutably**, marked retired, rather than
deleting it. A contract that drops a retired declaration is refused at load: it
would render an existing claim population untypeable, which is the same defect
as redefinition arriving by another route.

**And redefinition detection requires predecessor-aware validation.** "Refused
at contract load" compares a contract against something, and a content-derived
identity does not by itself say what it succeeds. So a contract **declares its
predecessor contract identity**, and load-time validation is a two-contract
check: every identifier present in both must have byte-identical declarations,
and every identifier in the predecessor must still be present, live or
tombstoned. Without the declared predecessor there is nothing to diff against,
and "never redefine" is an honour system.

This lands squarely on D §12's open **domain contract versioning policy**
question, and it constrains the answer: whatever that policy becomes, it must
carry a predecessor link and a tombstone-retention rule, because the vocabulary
extension rule is unenforceable without both. §8 records the constraint; §11
records that the policy itself is still open.

### 7.4 What moves, and what does not

The rows this section exists to pin — five, with the fourth split, because
missing and ambiguous refuse at **different boundaries**:

| # | change | claim identity | `belief_input_digest` |
|---|---|---|---|
| 1 | same term identifiers; consulted contract release changes | **unchanged** | **moves** |
| 2 | an operator / dimension / layer / referent identifier differs | **a different claim** | moves transitively |
| 3 | an activated but **unconsulted** contract changes | unchanged | **unchanged** |
| 4a | a required contract is **missing** from the profile | **decode refused** | none produced |
| 4b | contracts **conflict across corpora** a derivation spans | unaffected — each claim already decoded | none produced; **derivation refused** |
| 5 | a kernel tag's byte encoding changes | moves — **requires an explicit standard amendment** | moves |

Row by row, with the citation each rests on.

**Row 1 is the whole point of §6.5's identifier discipline.** An ontology
release, a corrected description, a new operator added elsewhere in the same
contract — all move the content-derived contract identity, and D6 puts that in
the digest. None of them touches an identifier already in `π_claim`. Beliefs
are re-derivable and known to be affected; claims do not fork.

**Row 2 is a mint, not a mutation**, and the wording matters for the same reason
it mattered in §6.7. A claim identity never "moves" — it is immutable by
construction. What the row says is that two claims differing in any identifier
position are **different claims** with different identities, and any belief over
the new one is a different belief. "Transitively" is exact: the digest moves
because its claim-side input moved, not by a second rule.

**Row 3 is D6's conditional arm, whose *rule* is unamended and whose *triggers*
are not.** A domain activated in a manifest but never interpreted still
contributes nothing — that half is inherited exactly. But §7.1 amends what
counts as reaching a contract, adding claim-schema triggers to facet
namespaces, so the walk this row depends on is a **wider** walk than D6's
oracle currently tests. D limitation 2 already warns that an under-collecting
walk fails *open*; §7 does not fix that, and should say the uncomfortable part:
**§7 enlarges the surface D limitation 2 can get wrong**, and the widened walk
needs its own oracle arm (§8).

**Row 4 was one row and is two, because the two failures refuse in different
places.** Collapsing them made `decodeClaim` look responsible for a condition it
cannot see.

*4a, missing,* is local and static: a claim names an operator whose declaring
contract is not in the profile at all. The check is inside a single
`ProfileSpec`, so `decodeClaim` refuses and nothing is minted.

*4b, conflict,* is D7's case, and it is **not** a decode failure. Each corpus in
the closure may be individually valid and internally consistent; every claim in
each may have decoded successfully long ago. What is inconsistent is the
*combination* — a closure spanning corpora that pin different identities for one
namespace — and that is only visible when a derivation assembles the closure.
So D7's refusal fires at **derivation/belief construction**, where D already
puts it, never resolved by recency and never merged.

The shared result is that no belief is produced. Nothing partial is minted, and
there is no arm in which an unresolved contract yields a claim carrying a
resolution to be settled later.

**Row 5 is the severe one and should read that way.** The kernel tags are
canonical bytes inside `science.identity.v1`. Changing an encoding re-identifies
**every claim in every corpus** — it is not a migration, it is a re-minting of
the entire claim population. It therefore requires an explicit amendment to the
identity standard, on the same terms as any other encoding change, and it is
listed here precisely so that it can never be done incidentally by an
implementation choosing a different serialization for a tag. This is also why
§6.5's note stands: a tag stable in prose and unstable in bytes forks identities
across implementations, so the base contract pins the bytes, not the spelling.

### 7.5 Corrections §7 forces on §6

Three, of which the first is §7.2's and is recorded there: `decodeClaim` gains
`ResolutionSnapshot` and returns a `BindingCheckReceipt`, because §6.3's
signature made the decode depend on state it did not take and produce a record
it could not carry. The remaining two:

**The projection's shape must not depend on the contract.** §6.5 wrote the
polarity position as *"absent when `Polarity(op) = 1`"*. That makes the arity of
`π_claim` a function of a contract field, so a `sign_apt` flip would re-project
existing claims even though nothing about them changed. §7.3 refuses such a flip
outright, but a projection whose shape is contract-dependent is fragile in a way
the rule alone does not fix — it means the correctness of an immutable identity
rests on a contract never being edited a certain way.

So the position is **always present**, carrying the base contract's
`sign_inapt_tag` for the unit inhabitant:

```text
polarity  ∈  { positive, negative, unsigned, inapt }        always emitted
```

`inapt` and `unsigned` are different facts and must not be collapsed: `unsigned`
says the operator has a sign and this claim does not assert one; `inapt` says
the operator has no sign to assert. With this, `π_claim`'s shape is determined
entirely by the claim's own content — operator, one entry per argument slot, one
entry per present dimension, polarity, layer — and no contract edit can
re-project a stored claim.

**`ProfileSpec` resolves; contracts authorize.** D §6 already separates the two
roles, and §7 must not blur them: the contracts are the normative SSOT, and
`ProfileSpec` is the sole compiled runtime profile. `decodeClaim` takes
`ProfileSpec` as its second parameter (§6.3) because that is the resolved,
merged, validated form the check needs — but **`ProfileSpec`'s own identity
never appears in `π_claim` or in the consulted set.** What enters
`belief_input_digest` is the set of **contract** identities (D6), not the
compiled artifact's.

The reason is `KIND_DESCRIPTORS`' defect one level up. If a compiled artifact
were an identity authority, recompiling — a different merge order, a compiler
version, a validated-but-reordered output — could change claim identity with no
contract edit anywhere. D closed substrate §12 by retiring the second per-kind
source of truth; §7 declines to create one for vocabulary.

## 8. ρ — the refinement map

§1's constraint was that no revision may masquerade as a transcription. §8 is
where that is enforced: every M\* proposal is placed against the banked prose it
touches, the oracle that would have to change, and the guarantee classes it
preserves, amends, or invalidates.

### 8.1 Three dispositions, kept apart

| disposition | what it means | what banking it costs |
|---|---|---|
| **amendment** (ρA) | banked prose is wrong, incomplete, or ill-typed under M\*, and must change | edit the design text **and** its oracle row |
| **constraint** (ρC) | a banked **open question** stays open, but its answer is now bounded | edit the open question to record the bound; no oracle changes yet |
| **open mechanism** (ρO) | M\* names a requirement and does **not** supply the mechanism | nothing is banked but the record that it is open |

The three are separated because they fail differently when confused. An
amendment recorded as a constraint leaves a false oracle in place. A constraint
recorded as an amendment claims a question is closed that no one has answered.
An open mechanism recorded as either claims a mechanism exists.

The binding check is the case that forced the distinction, and it appears under
**two** dispositions on purpose: the diagnostic check is adopted (§8.5), while
its persistence and epistemic effect are ρO1. Nothing in §8 may read as though ρ
settled the second.

### 8.2 Amendments

**ρA1 — Proposition semantic identity becomes typed claim identity.**

| | |
|---|---|
| banked prose | kernel §4.1's Rule: *"A proposition carries a **semantic identity**: a hash over its normalized `statement` plus its factored fields (`subject`, `predicate`, `object`, `polarity`, `claim_layer`)."* |
| replaced by | `I_claim(c) = H(tag_claim ‖ encode(π_claim(c)))` over the typed projection (§6.5) |
| oracle | **G7**. Its positive arm — *"Edit a proposition's scope in place; assert a new semantic identity is minted, that prior assessments still bind the old one"* — is preserved **verbatim** and still passes. Its converse arm, *"overwrite `title` alone and assert *no* mint"*, gains a parallel `statement` arm |
| preserved | **CS** — the property G7 actually tests, that a semantic edit forks identity and cannot retarget evidence. **WD**. The `supersedes` lifecycle. The node-invariant framing (no new addressing layer) |
| amended | the identity **basis**: prose leaves; `qualifiers` enters; `subject`/`object` become sorted bound referents; `predicate` becomes `operator` |
| invalidated | *"normalized `statement`"* as an identity input, and with it kernel §11's **semantic-identity normalization** open question insofar as it concerns prose — whitespace, casing and numeric formatting have nothing to normalize once no prose is in the projection. Term-synonym resolution survives, relocated to vocabulary binding (D §5) |

This is the largest single amendment in the document, and its safety rests on
G7's positive arm being *strengthened* rather than weakened: under M₀ a
scope-widening edit forks identity only if the prose changed enough to move the
hash, which is exactly the "too loose" horn kernel §11 names. Under ρA1 it forks
whenever a typed field differs, and prose cannot mask it.

**ρA2 — `statement` splits into a derived rendering and an authored annotation.**

| | |
|---|---|
| banked prose | kernel §4.1's `title` split and its stated reason, *"A field cannot be both hand-editable prose and an identity input."* |
| becomes | unstored `render(Claim)`, plus optional authored `display_statement`; both identity-inert (§6.5) |
| oracle | **G7**'s converse arm, extended as in ρA1 |
| preserved | the doctrine itself, applied one field further. **CA†** — each value keeps a single construction authority |
| amended | one field with two authorities becomes two fields with one each |
| invalidated | §6.5's own first draft, *"a derived gloss, freely overridable"* — an M\* internal correction, not a banked claim |

**ρA3 — `subject` and `object` become sorted bound referents.**

| | |
|---|---|
| banked prose | kernel §4.1's factored-field list, where `subject` and `object` are unqualified; §2.9 (b) records them as bare strings while `term` is an external scoped entity (world §3) |
| becomes | `Args(op) = ∏ᵢ Referent(ArgSort(op,i))` (§6.2), each slot a term identifier in a bound vocabulary |
| oracle | **none banked** — no row tests that an argument is a resolvable referent. This is a gap, and it is a candidate **M** row (§9) |
| preserved | world §3's scoped-external `term`; D §5's binding forms |
| amended | the field's type |
| invalidated | nothing banked; the M₀ state was under-specified rather than wrong |

**ρA4 — Qualification enters the identity basis as typed structure.**

| | |
|---|---|
| banked prose | kernel §4.1's factored-field list, which has no qualifier slot — while §4.1's own founding example turns on *"in adults"* versus *"in all humans"* |
| becomes | `Qualifiers(op)`, kernel-owned structure over domain-owned dimensions, flat fragment this pass (§6.4) |
| oracle | **none banked**; candidate **M** row (§9), and the sharpest one, since G7's positive arm currently passes only because prose carries the qualifier |
| preserved | G7's intent |
| amended | the basis gains a member |
| invalidated | nothing banked. The defect it closes is latent, not recorded: under ρA1 alone — prose demoted, no qualifier slot — the two claims of §4.1's own example would collapse to **one identity** |

ρA4 is why ρA1 cannot be banked without it. Demoting prose while leaving the
factored fields as they are would institutionalize the exact failure kernel §4.1
exists to prevent.

**ρA5 — `predicate` becomes `Operator`, owned by a domain contract.**

| | |
|---|---|
| banked prose | kernel limitation 4, *"The predicate vocabulary is currently 9 terms; real claims will not fit cleanly"* — no owner, no extension rule; and D §12's open question, *"Whether the predicate vocabulary becomes a domain contract like any other"* |
| becomes | operators declared by domain contracts, always (§7.1); term identity, issue/retire/never-redefine (§7.3) |
| oracle | **D4 is unchanged and does not cover this.** D4 governs the sole authored **per-kind** source and `KindSpec` compilation; a claim schema is not a per-kind artifact and an operator roster is not a `KindSpec`. Two new oracles are required, both **M** rows (§9): that no second authored operator artifact exists beside the contracts, and that retirement/redefinition behaves as §7.3 says |
| preserved | **D4** exactly as written, at its existing scope; D §6's contracts-are-normative / `ProfileSpec`-is-compiled **split** (§7.5); **US†** for the sign-aptness roster's retirement |
| amended | limitation 4's "no owner, no extension rule" is answered; D §12's question is **closed** — yes, a domain contract like any other. Separately, **D §6's compiled-registry prose widens**: `ProfileSpec` now compiles claim schemas alongside the `KindSpec` set, so *"any further per-kind artifact is compiled from it"* is no longer a complete description of what it compiles |
| invalidated | the closed nine-term enum as the vocabulary's shape |

The first draft of this row said D4 *"is preserved and now covers more."* That
was normative scope acquired without editing either the prose or the oracle — the
same move §8 exists to prevent. D4's reach is unchanged; the new obligations are
new rows.

**ρA6 — D6's consulted-set trigger widens to claim schemas.**

| | |
|---|---|
| banked prose | D §8: *"walk the derivation's closure, collect the namespace of every facet it reads, and resolve each namespace to a contract identity by §8.1"* |
| becomes | that, **plus** every contract reached through a claim schema — operator, dimension, argument and restriction sorts, and each sort's vocabulary binding (§7.1) |
| oracle | **D6** gains a claim-schema arm: derive belief over an assessment reading a claim at `affects`, bump the contract declaring `affects` while touching no facet, and assert `belief_input_digest` **moves**. **D limitation 2**'s under-collecting-walk warning widens with it |
| preserved | D6's **asymmetry** — unconditional base, conditional domain — entirely. D7. W5. The negative arm (bump an unconsulted domain, digest unchanged) |
| amended | the trigger set only |
| invalidated | nothing. The facet-namespace rule stays correct; it is now **insufficient alone**, which is a different fault from being wrong |

The failure mode this closes fails **open**, which is why it is an amendment and
not a note: a facet-only walk omits the contract declaring an operator from a
belief derived over a claim at that operator, and the omission is invisible in
every test that uses facets.

**ρA7 — Term resolution refines from three outcomes to five.**

| | |
|---|---|
| banked prose | D §5's table row: *"`unknown` — the term is **outside the bound vocabulary** altogether, or the binding's namespace was never consulted"* |
| becomes | `member \| not-member \| not-consulted \| not-present \| not-available` (§7.2) |
| oracle | **D3**, whose statement *"the three unresolved states stay distinct"* becomes **five-way exhaustive discrimination** over two groups that must not be mixed: two **resolved membership results**, `member` and `not-member`, and three **results of a check not performed**, `not-consulted`, `not-present` and `not-available`. `not-member` is a resolved finding, not an unresolved state, and describing it as one would reproduce the very collapse the refinement exists to undo. D3 gains an arm asserting no member of the five collapses into another |
| preserved | `not-present` and `not-available` **verbatim**, so D3's existing arms pass unchanged; *"a binding is well-formed in all cases, no error is raised, and no fallback to another release occurs"*; **ED†** |
| amended | `unknown` splits into a finding and the absence of one |
| invalidated | any reading of banked `unknown` as evidence of **non-membership** — the reading §7.2's first draft made, and the one that would let a decoder report "not in the vocabulary" on the strength of nobody having looked |

**ρA8 — Held-ness is a `def` dependency, and G3 is stated over the `Belief` arm.**

| | |
|---|---|
| banked prose | computation §7.1's three-case table, row 2: *"the **last held copy** of an `observes` input destroyed → the input is no longer **held**; eligibility fails and admission **changes**"*; and G3's unrestricted statement that a belief state names its complete transitive input closure |
| becomes | held-ness typed as a **`def`** edge — it selects which arm of `B`'s codomain is reached, not the value within the `Belief` arm (§4.3 finding (b)) |
| oracle | **R5** — all three arms, including negative (a) *"destroy the last held copy … assert eligibility fails and admission changes"*, are preserved **unchanged and still pass**. **G3**'s phrasing gains the arm restriction: whenever `B` lands in the `Belief` arm, `κ_B` determines it |
| preserved | R5 verbatim; comp §7.1's three cases and its *"a failure to look is not a finding of absence"* framing; **DL**; the factorization law of §3.4 |
| amended | G3's scope, from all of `B`'s codomain to its `Belief` arm |
| invalidated | the reading under which held-ness is a `sem` edge. That reading is not merely inelegant: two configurations differing only in whether the last copy survives would share `κ_B` and therefore one `belief_input_digest` while yielding different beliefs — a **G3 violation**, not a qualifier on G3 |

The mechanism that would make the `NotAvailable` case *recorded* rather than
merely correct is **not** supplied here; that is ρO2.

### 8.3 Contract succession — an adopted rule and a bound, not one thing

§7.3a does two different things in one passage, and filing them together would
have ρA5 promising enforceable retirement while ρC1 said no oracle exists. They
split the way the binding check does.

**Adopted (§8.5, with M rows) — the succession rules M\* actually asserts.**
These are normative now, not deferred:

| rule | §7.3a |
|---|---|
| a contract **declares its predecessor contract identity** | otherwise there is nothing to diff against |
| every identifier present in both must have **byte-identical declarations** | this is *never redefine*, made checkable |
| retired declarations are **retained immutably as tombstones** | historical claims are typed against them |
| a violation of any of the three is **refused at contract load** | RF†, at load, not at claim decode |

**ρC1 (constraint) — the broader versioning policy stays open.**

| | |
|---|---|
| banked open question | D §12: *"Domain contract versioning policy. What constitutes a breaking change to a facet contract, and whether contract identity being content-derived is sufficient or a declared compatibility range is also needed."* |
| constraint | the policy must be **compatible with** the four adopted rules above; it may not, for instance, permit a successor to drop a declaration or to reuse an identifier with different bytes |
| what stays open | what counts as a breaking change to a **facet** contract, whether a declared compatibility range is needed, and how ranges interact with 5b's versioning rules. None of that is settled here |
| status | **open.** ρC1 bounds the answer; it does not supply one |

D §12's own framing — whether content-derived identity is *sufficient* — is
answered in one direction only: it is not sufficient for vocabulary, because a
content-derived identity says what a contract *is* and never what it *succeeds*.

### 8.4 Open mechanisms

Named requirements with no mechanism. Each is a record that something is
missing, not a design.

**ρO1 — Binding-check persistence and epistemic effect.** §7.2 adopts the
diagnostic check (§8.5) and leaves open: whether the receipt persists at all,
how it would be discovered, how it would be superseded, and what corrects a
claim later found `not-member`. The banked correction rules make the obvious
path unspellable — C §4's eligible-target set is two arms and a non-node receipt
is in neither, propositions are not retraction-eligible, and 5b §7.6's audit
mints nothing — so the answer is either a lifecycle design or promotion to an
independently addressed record, which is **D's own promotion trigger** and
therefore a new kind with its own eligibility analysis. Also open: whether an
unchecked claim may be assessed, and when re-resolution runs. **ρ does not
settle any of this**, and no row in §8.2 depends on it.

**ρO2 — The held-ness mechanism.** ρA8 decides what the *answer* is when the
last held copy is destroyed. It does not make the case **recorded**: nothing
observes the destruction, so `NotAvailable` is reached by a check failing rather
than by an act being committed. §4.3 withdrew the recorded-loss repair as
premature, and it stays withdrawn.

**ρO3 — Entailment and estimand match.** §6.7 preserves the typed information a
future entailment relation would need and defines nothing. Kernel limitation 5's
estimand match becomes **stateable** as `match(claim_type, estimand_type)` and
is not stated. The two are related and not assumed identical.

**ρO4 — A population vocabulary.** §7.1's `population-group` sort has no
binding, and the contract as written would be refused at load under D §5. Until
one is selected, a population-qualified claim is untypeable — the concrete form
of §6.6's cost.

### 8.5 Adopted with no banked counterpart

M\* additions that amend nothing because M₀ has no corresponding claim. They
still enter §9 as candidate guarantees.

| adopted | classes | note |
|---|---|---|
| the dependent-sum `Claim` and its schema/inhabitant split (§6.2) | **US†** | no M₀ type to amend |
| `decodeClaim : WireClaim × ProfileSpec × ResolutionSnapshot → (Claim × BindingCheckReceipt) + Refused` (§6.3, §7.2) | **RF†**, **WD** | the boundary M₀ never stated; `ResolutionSnapshot` is what makes it a function of its arguments |
| the **diagnostic** binding check and its five outcomes | **ED†** | adopted; persistence and effect are ρO1 |
| unconstructible sign-inapt polarity; `SIGN_MEANINGFUL_PREDICATES` retired | **US†** | the roster is proto-science implementation, not banked prose |
| untypeable spans mint nothing; a source-assertion for one is **unconstructible** | **RF†**, **US†** | follows from world §4.2's identity basis, which is preserved, not amended |
| the polarity position is always emitted (§7.5) | **CS** | keeps `π_claim`'s shape independent of any contract field |
| contract succession: declared predecessor, byte-identical shared declarations, immutable tombstones, refusal at load (§8.3) | **RF†**, **CA†** | adopted now; only the **broader** versioning policy is ρC1 |
| retirement is enforced in the authoring constructor, never at decode (§7.3a) | **US†** | decode and restore must accept retired identifiers or history becomes un-restorable |

### 8.6 Preserved untouched — the negative list

Worth stating explicitly, because a claim-neighbourhood revision of this size
invites the assumption that more moved than did.

| preserved | why it is worth saying |
|---|---|
| world §4.2's identity bases, including `source-assertion`'s | §6.6's refusal is a **consequence** of that basis, not a change to it |
| C §4's eligible-target set — still exactly `node` and `route` | §7.2 explicitly declines to extend it |
| 5b §7.6, audit mints nothing | ρO1's open path must not be read as licensing an automatic retraction |
| D7 and W5 | ρA6 widens a walk; it does not touch agreement or location-invariance |
| kernel limitation 1's ranked queue | untypeable spans are a **second** backlog with a different membership condition, not an extension of that row (§6.6) |
| the nine banked guarantee tables' ids | no id is renumbered; every change above is an edit to a row's text or a new arm |

### 8.7 What banking this costs

**Design prose and oracles.**

| artifact | edit |
|---|---|
| kernel §4.1 | the Rule is restated over the typed projection (ρA1); the `title` split gains its `statement` case (ρA2) |
| kernel §11 | the semantic-identity normalization question is closed for prose, narrowed to term synonyms (ρA1) |
| kernel limitation 4 | answered — owner and extension rule (ρA5); the referent-binding half is **re-recorded as open** (ρO1), not deleted |
| kernel G7, G3 | G7 gains a `statement` converse arm; G3's statement gains the `Belief`-arm restriction (ρA1, ρA8) |
| computation §7.1, R5 | §7.1's row 2 gains its `def` typing; R5's arms are unchanged (ρA8) |
| D §5, D3 | the outcome set refines to five; D3 gains a five-way non-collapsing arm (ρA7) |
| D §6 | the compiled-registry prose widens: `ProfileSpec` compiles claim schemas alongside the `KindSpec` set (ρA5) |
| D §8, D6, D limitation 2 | the trigger set widens; D6 gains a claim-schema arm (ρA6) |
| D §12 | the predicate-vocabulary question is closed (ρA5); the versioning question records ρC1's bound |
| **M1–M\<n\>** | §9's new rows, plus the §1 banking obligations already recorded |

**Implementation authorities M\* introduces.** Editing design prose does not
make two implementations hash a typed claim identically, and none of these
exists today. Each needs a named home before M\* is buildable:

| authority | what it must fix | home |
|---|---|---|
| the **claim grammar** and the **canonical byte encoding of every kernel tag** — quantifiers, polarities including `sign_inapt_tag`, and the layer vocabulary | the closed sets and their bytes, not their spelling (§7.1, §7.4 row 5) | the `science` **base contract**, which is why it is a contract and not a constant |
| **`π_claim`'s canonical projection** and its domain-separation tag `tag_claim` | field order, encoding of each position, and the tag itself, as a first-class member of the identity standard | **`science.identity.v1`** (computation §4.3's value contract), extended — a new tag, not a new encoding |
| **`ProfileSpec` compilation of claim schemas** | that operator, dimension and sort declarations merge and validate into the compiled profile on the same terms as `KindSpec`, with no second authored artifact | D §6's compiled-registry path, widened as above |
| a shared **Python/TypeScript parity fixture for claim identity** | that one typed claim projects to identical bytes and hashes identically in both implementations | alongside D §6's existing namespaced-facet-key parity fixture, which is the precedent for exactly one such fixture per shared encoding |

The parity fixture is the one that would otherwise be discovered late. `nodes`
already imposes no facet-key grammar and both implementations accept arbitrary
string keys — D §6 pinned that freedom with a fixture rather than trusting it,
and a typed claim projection has strictly more ways to disagree: slot order,
map key sorting, tag bytes, and the absent-versus-unit distinction §7.5 exists
to remove.

## 9. Guarantees (M1–M14)

Fourteen rows. Six come from obligations this document raised before §8 — three
from the closure check and the laws (§3.4, §4.3), three from ρ cells that read
*"no banked oracle"*. The rest come from §8.5's adopted items, which amend
nothing and are therefore tested by nothing unless M tests them.

**The discipline is §5's OF†, applied to M itself: every row must be capable of
failing.** So each row below names a **sabotage** — a specific mutation that
must break it. A row whose sabotage still passes is defective and is the first
thing to fix, not a row that can be left in place because it is green.

Ids are frozen on banking and extended, never renumbered — the same rule the
nine banked tables use.

Two rows deliberately stay apart. **M2** (every run input reaches the
assessment's carrier identity) and **M3** (`standing` terminates) were both
raised by §4, but they have nothing in common operationally: M2's sabotage adds
an input outside the declared role partitions, M3's constructs a retraction
cycle. Sharing a row would let one pass on the other's evidence.

| id | guarantee | how it is tested |
|---|---|---|
| **M1** | **Undeclared reads are detected, not noticed.** Every value a semantic derivation actually reads is inside its declared input closure | Instrument the derivation so each value read is recorded at read time; assert the recorded read-set is contained in the declared closure, for a corpus exercising every closure member. **Sabotage:** add a code path that reads one value outside the closure — a facet, a contract, a producer set — changing nothing else, and assert the check **fails**. This is the row §1 asks for: G3's own text records four members that "were live holes in earlier revisions," each found by a reviewer noticing, and nothing in that method distinguishes a complete closure from one whose next hole is unnoticed. **Negative:** a run that reads nothing outside the closure must pass without exemptions, or the row is untestable in the ordinary case |
| **M2** | **Every run input reaches the assessment's carrier identity** | Take an assessment; for each input of its run, mutate that input's bytes and assert the assessment identity **moves**. **Sabotage:** attach an input to the run that no declared role partition covers, and assert the attempt is **refused** — not silently ignored. §4.3 finding (a) established that the current path is three hops (the recipe's role-partitioned `inputs` → R2 → assessment identity) and is a **binding** path, not a proven semantic one; this row pins the binding so the fragility is tested rather than argued |
| **M3** | **`standing` terminates on every input** | Evaluate `standing` over retraction chains of increasing depth, including counter-retractions and multiple standing retractions of one target, and assert termination and a stable value. **Sabotage:** attempt to construct a retraction whose target's content identity contains its own — assert it is **unconstructible**, since a retraction's identity covers its target's identity, and separately that a hand-written cyclic pair is **refused at the boundary** and an **audit finding** when raw-written. Correction §4 argues well-foundedness; no banked row tests it |
| **M4** | **Every argument and restriction is a resolvable referent, or the decode refused** | Decode a claim whose argument term **is** in the sort's bound vocabulary with that vocabulary readable → accepted, check recorded **performed**. **Sabotage:** decode one whose term is **not** in a readable vocabulary → **refused**, nothing minted. **Negative — availability is not membership:** make the vocabulary unreadable and decode the same bad term → **accepted** with the check recorded **not performed**, and assert the two receipts are distinguishable. **Static:** assert a bare string cannot occupy an argument slot at all |
| **M5** | **Qualification participates in claim identity** | Two claims differing **only** in a restriction identifier → different `I_claim`; differing **only** in quantifier tag → different; one carrying a dimension the other omits → different. Then the founding case end to end: mint kernel §4.1's *"in adults"* claim, assess it, "edit" to *"in all humans"*, and assert a **new** identity, the prior assessment still bound to the old one, and a `supersedes` link. **Sabotage:** drop the qualifier map from `π_claim` and assert the founding case **collapses to one identity** — the row's whole point. **Negative:** re-serialize the qualifier map with keys in a different order and assert the identity is **unchanged** |
| **M6** | **Operators are issued, retired, and never redefined** | A successor contract changing `arity`, `arg_sorts`, `sign_apt`, `layers` or `dimensions` under an existing identifier → **refused at contract load**. A successor **dropping** a retired declaration → refused. A successor adding a new operator → accepted, no existing claim affected. **Retirement, both paths:** assert the authoring constructor **cannot select** a retired identifier (statically), and that decode/restore of a historical claim at that identifier **succeeds** against the frozen declaration. **Sabotage:** flip `sign_apt` on a live operator and assert load fails; remove the declared predecessor link and assert the redefinition check is **unable to run** rather than silently passing. **Negative:** a purely editorial change is accepted, moves the contract identity, and needs no new identifier |
| **M7** | **No second authored operator artifact exists** | Assert operator, dimension and sort declarations exist **only** in profile contracts, and every runtime form is compiled from `ProfileSpec`. **Sabotage:** add a hand-authored operator roster beside the contracts and assert it is **refused or unreachable** — never consulted as a parallel source. **Negative:** a grep for operator names is **not** the test and would fail against a conforming tree; the test is that mutating a contract changes the compiled schema with no code change. D4 does not cover this — it governs per-kind sources, and a claim schema is not a per-kind artifact |
| **M8** | **Claim identity is independent of contract release and of compilation** | Bump a consulted contract editorially and assert `I_claim` is **unchanged** while `belief_input_digest` **moves** (§7.4 row 1). Recompile `ProfileSpec` — different merge order, different compiler build — and assert `I_claim` is unchanged and `ProfileSpec`'s identity appears in **neither** `π_claim` nor the consulted set. **Sabotage:** fold the contract release into `π_claim` and assert an ontology release now forks every claim, which is the failure this row forbids. **Negative:** bump an **activated but unconsulted** contract and assert both `I_claim` and the digest are unchanged (§7.4 row 3) |
| **M9** | **`π_claim`'s shape depends on the claim, never on a contract field** | Project a claim at a **sign-inapt** operator; assert the polarity position is **present**, carrying `sign_inapt_tag`, and that `inapt` and `unsigned` produce **different** digests. **Sabotage:** omit the position for sign-inapt operators and assert the digest changes — the defect §7.5 corrects, in which a `sign_apt` edit would re-project stored claims. **Negative:** an operator's contract may not be edited in a way that changes any stored claim's projection; combined with **M6** this must be unreachable rather than merely untried |
| **M10** | **Two implementations hash a typed claim identically** | One shared fixture: a claim exercising every position — multi-slot args, several qualifier dimensions, a sign-inapt operator, a non-ASCII referent identifier — projected and hashed in **both** Python and TypeScript, asserted byte-identical at the projection and equal at the digest. **Sabotage:** change one implementation's map-key sort, slot order, or tag bytes and assert the fixture **fails**. This follows D §6's precedent of exactly one parity fixture per shared encoding; a typed claim has strictly more ways to disagree than a facet key |
| **M11** | **`decodeClaim` is a function of its arguments, and refuses rather than repairs** | Same `⟨WireClaim, ProfileSpec, ResolutionSnapshot⟩` decoded twice, in different processes and different checkouts → **identical** result. Then each ill-formed input in turn — a sign on a sign-inapt operator, wrong arity, an undeclared dimension, an inadmissible layer, a missing required contract — → **`Refused`**, with **nothing minted** in every case. **Sabotage:** make availability ambient rather than a parameter and assert two holders now decode the same bytes differently. **Negative:** a raw-written malformed claim is an **audit finding**, not a silent accept and not a decode failure — the boundary was bypassed, not defeated |
| **M12** | **An untypeable span mints nothing** | Present a span no operator fits → assert **no** proposition, **no** source-assertion, and a project-scoped typing-work item. **Static:** assert a source-assertion naming a non-existent proposition identity is **unconstructible**, since world §4.2 puts the proposition identity in its basis. **Sabotage:** add a fallback that mints a proposition with a placeholder operator and assert the check fails. **Negative:** the work item must **not** appear in kernel limitation 1's unassessed queue — different membership condition, different owner (§6.6) |
| **M13** | **Invalid claims are unspellable, tested statically** | Type-level, not by attempting a call: assert the typed constructor offers **no** polarity argument at a sign-inapt operator, no slot for an argument of the wrong sort, and no inhabitant for an inadmissible layer. **Sabotage:** reintroduce a `SIGN_MEANINGFUL_PREDICATES`-style roster with a runtime validator and assert the static check **no longer holds** — the roster is exactly what §6.3 retires, and this row is what stops it returning. **Negative:** the check must not be a passing unit test that merely never constructs the bad value |
| **M14** | **The five term-resolution outcomes stay distinct** | Reach each of `member`, `not-member`, `not-consulted`, `not-present`, `not-available` and assert none collapses into another — extending D3's existing method to the two new members. **Sabotage:** report a `not-consulted` term as `not-member` and assert the check fails; the two have **opposite evidential force**, one being a finding and the other the absence of one. **Scope:** this row tests the **diagnostic** outcome and its recording at decode. It asserts **nothing** about persistence, discovery, succession, or epistemic effect — those are ρO1 and have no row |

### 9.1 What M does not cover

| not covered | why |
|---|---|
| binding-check persistence, discovery, succession, and the correction path for a claim later found `not-member` | ρO1. M14 covers the outcome only, and deliberately stops there |
| whether an unchecked claim may be assessed | ρO1 |
| the recording mechanism for destruction of a last held copy | ρO2. M has no row, because ρA8 decides the *answer* and not the mechanism |
| entailment, subsumption, and estimand match | ρO3. §6.7 preserves the encoding's capacity to express them and defines no relation, so there is nothing to test |
| that a population-qualified claim can be typed at all | ρO4. No population vocabulary is bound, so the case is currently untypeable by construction |
| that an operator's declared schema faithfully describes the relation it names | authored, not checked — the same class as D limitation 4 and kernel limitation 8's acquisition boundary. M6 tests that a declaration cannot **change**; nothing tests that it was right |

**Two rows are load-bearing beyond their own statement.** M1 is the only row
that attacks the method rather than a property: every other row here, and in the
nine banked tables, tests something a person thought to test. And M13 is the
only static row — if it decays into a runtime check, §6.3's entire argument
reduces to a validator with better manners.

## 10. Limitations

*Not yet drafted.*

## 11. Open questions

*Not yet drafted.*
