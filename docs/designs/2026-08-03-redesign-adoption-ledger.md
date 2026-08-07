# System redesign — adoption-order ledger

**Status:** Living record, updated as designs bank and artifacts land.
**Purpose:** The banked designs are each careful about what they do *not* wait on, but no
document names the dependency order between them or the legal partial states in between.
This ledger does, modeled on `atoms`' deferred-obligation ledger: an entry leaves when its
owning design/plan lands *and* its verification covers it. The design commit that names an
entry discharges nothing.

## 0. The clean-start ruling (2026-08-04)

With every design banked, the redesigned system is **built from the ground up on
`nodes` + `atoms` in this repository**, rather than migrated into the existing
codebase. The prior implementation is preserved, public and unchanged, as
**`proto-science`** (`github.com/khughitt/proto-science`); this repository takes
the `science` name and starts its own version line.

Three consequences, recorded so they survive:

- **The git history is deliberately not carried over.** Nine design
  documents seeded the first commit (a tenth, the domain extension boundary,
  banked 2026-08-04; an eleventh, the formal model and claim calculus, banked
  2026-08-05 — §1 and §3 carry the current inventory); the review
  history that produced them —
  including the eleven-round review of the tamper-evident log — stays browsable
  in `proto-science`.
- **Key project elements are *reproduced*, never migrated.** Code may be
  borrowed, but a record only exists here if this system produced it. A migrated
  record would be a provenance-weak assertion — exactly what the kernel's
  guarantees exist to exclude — and nothing in §1's implementation items assumes
  the old codebase.
- **`proto-science` is not a dependency.** No import, no compatibility layer, no
  dual-write. It is heritage and a reference to read, and the two repositories
  share only the design documents' text.

Ownership moves with the restart: the system lives under the **`verifiably`**
organization rather than a personal account, so governance and long-term
stewardship are not tied to one individual. §5 records the namespace and
decomposition rulings that follow from it.

## 1. Unbuilt artifacts and what waits on them

| # | artifact | owner | waits on it | state |
|---|---|---|---|---|
| 1 | **World index** — address/alias/producers maps + producer snapshot, publishable and consumable without the corpora it names | world §5; packaging, write ownership, and staleness are open questions (world §10) | `not-present` resolution, receipt checkability, merge inbound hygiene, `corpus_id` uniqueness refusal, §9 anchor carriage (repro §9 amendment 2026-08-03), and retraction discovery — a fourth derived map, target identity → retraction addresses (5a §4) | **Design banked 2026-08-03** (`2026-08-03-world-index-packaging-design.md`; world §5/W8a/W13/lim. 9/§10 amended in place); build awaits implementation — X1–X12, with X2 gated on `atoms` A6–A8 |
| 2 | **Corpus manifests / `corpus_id` minting** | world §5 | world index build; exact corpus-state identity | Per-corpus explicit adoption act; the one place a duplicate can be created is copying a stamped corpus — refused at index build |
| 3 | **`nodes` contract deltas** — shipped, versioned §11.1 projection; reserved-path contract; recoverable construction; digest-id hazards | `nodes` `2026-08-03-nodes-under-the-system-redesign-design.md` | node content identity and corpus-state identity (world §5, amendment 2026-08-03); manifest safety; audits over damaged corpora | Direction approved; blocks profile *implementation*, not design |
| 4 | **`atoms` A6–A8** — coherent capture, effect/recovery execution, exerciser | `atoms` authority design §14 | durable multi-file commit; retirement of the single-writer/no-durability profile claims (substrate §7) | Nothing in banked designs waits on them; adoption route is science's composition root (`atoms` §12.2) |
| 5 | **Tamper-evident mutation log** (repro §9) | `2026-08-03-tamper-evident-log-design.md` — `atoms` owns registration (the A6–A8 executor path), science owns anchor carriage and verification | closing kernel §8.7's four recorded-mutation consequences and strengthening the fifth — chronology — for boundary-mediated executions (G2a/R12's out-of-band negative remains) | **Design banked 2026-08-03** (per-root chains with settlement lifecycle, epoch-cadence anchors + explicit anchor act, surviving-observer bound; kernel §8.7/G2a, comp §3.3/R12/§9, packaging §3/§4/§5/§5.1/§5.2/X9/§12/lim. 1, and `atoms` §15 amended in the banking commit); consumes artifact 1 as anchor carrier; the four-of-five closure lands at implementation (L1–L13) |
| 6 | **Retraction + correction lifecycle** | sub-problem 5a (§2) | four banked limitations that currently say the wrong answer stays computable (comp §5.2/§11.13/§13, world lim. 11) | **Banked 2026-08-03** (`2026-08-03-correction-lifecycle-design.md`; kernel §3.3/G8/§8.7 amended in the banking commit); C1–C10 await implementation |
| 7 | **Normative contract + conformance oracles + instrument certification** | sub-problem 5b (§2) | disposition of the 63 legacy check modules (principle in 5b §8); homes for G1, G2a–G2c, G3–G8; S1–S8 (S1a); W1–W13 (W5a, W8a–b); R1–R23; C1–C10; X1–X12; N1–N10; L1–L13; D1–D10; M1–M13; P1–P9 (N, L and D added 2026-08-04 — L having been omitted at the §9 banking, and N because 5b §5 puts every oracle table in the suite; **M added 2026-08-05**, on the obligation that design recorded in its own header before drafting, so a third table would not arrive late; **P added 2026-08-05** with the belief policy, under `P` because `B` is the formal model's belief reading) | **Design banked 2026-08-03** (`2026-08-03-normative-contract-design.md`; tenth kind `instrument-certification`, rule-binding recipe member, certification-enumeration receipt — kernel, world §3/§4.2/§5/W8a, comp §4.2/§4.2a/§7.3/§7.3b–c/R18/R19, 5a §3/§4/C10/§9, packaging §5/§5.2/§7/X9/X10/X12 amended in the banking commit); the first contract cut, the executable suite, and N1–N10 await implementation |
| 8 | **Domain extension boundary** — where domain-specific material lives across `nodes`, `science`, and downstream domains | `2026-08-04-domain-extension-boundary-design.md` | consistent organization of domain material; the first domain pack; the predicate-vocabulary design | **Design banked 2026-08-04** (interpretation as facet conjunction with an explicit promotion trigger; exact vocabulary bindings; `ProfileSpec` as the sole compiled profile with a zero `nodes` delta; manifest `profile` block inside corpus-state identity; consulted profile contracts in G3 — world §5/W13/lim. 9, packaging §6, kernel §5.1, substrate §6.1/§12, and this ledger amended in the banking commit); D1–D10 await implementation |
| 9 | **Formal model + typed claim calculus** — a formal model of the banked system (M₀), the smallest system satisfying the intended guarantees (M\*), and the refinement map between them | `2026-08-04-formal-model-and-claim-calculus-design.md` | the claim grammar and canonical tag encoding (`science` base contract); `π_claim` + `tag_claim` in `science.identity.v1`; `ProfileSpec` compilation of claim schemas; the Python/TypeScript claim-identity parity fixture | **Design banked 2026-08-05** (a proposition **is** a typed claim, `Claim = Σ(op:Operator). Args × Qualifiers × Polarity × Layer`, with `statement` demoted out of identity; five-way term resolution; contract succession for claim vocabulary — kernel §4.1/§5/§8/§11 with G3, G7 and limitation 4; comp §7.1; world §4.1/§4.3/W4/§10; substrate §4.2; 5a §3/§4/C10; 5b §4; D §5/§6/§8/§12 with D3, D6 and limitation 2; and this ledger and the README amended in the banking commit); cut 1 implements and tests its selected arms of M4–M11 and M13 (§3 item 10, merged 2026-08-07), M1–M3 and M12 await implementation, and all four **implementation authorities** above are now built or frozen |
| 10 | **Belief policy** — what a belief *value* is, and the identity under which it is pinned | `2026-08-05-belief-policy-design.md` | the four terms kernel §4.2.1 cites as versioned policy members and never defines; `belief policy version` as the last bare rule reference in the G3 digest; the review-disposition record's F3 and its §5.5 stop rule, which place this ahead of the vertical slice | **Design banked 2026-08-05** (exact `PolicyBinding = (rule identity, implementation content identity)` as a required per-computation argument; `science.belief.v1` with `V = ℤ` and unit weight, so a value is a signed evidence balance and never odds; `Belief \| NoBelief(reason) \| Refused(reason)`; `inconclusive` excluded from the graph — kernel §4.2.1/§5/§5.1/lim. 5, formal model §3.3, D §8, substrate S6(h), 5b §4, and this ledger and the README amended in the banking commit); P1–P9 await implementation. Weighting by study design or precision is **blocked on ρO3**, not deferred by choice, and conformance cut 1 is **unchanged** — this discharges its prerequisite without widening it |

## 2. Sub-problem 5 — split and order (ruled 2026-08-03)

Sub-problem 5 is two clusters with a clean seam, taken in the reverse of the charter's
implied order:

- **5a — retraction and the correction lifecycle**, first: retraction (form already fixed:
  additive, attributed, kernel §5.1 digest member, structurally subtractive,
  eligibility-bearing), conflict-route retirement, and coverage-declaration
  accountability — the judgment cluster, all "who may change recorded judgment and how is
  the change visible."
- **5b — the versioned normative contract and its conformance oracles**, second, carrying
  instrument certification with it: equivalence-rule, falsifier, interpretation-rule, and
  scope-derivation-rule certification, plus code-lineage independence.

Rationale, recorded so it survives:

1. The retraction hole is live in banked designs — four separate limitations defer here.
2. Versioning a normative contract before adding a known-pending belief operation
   guarantees a major bump on arrival; the operation set completes before the document
   that describes it freezes.
3. "Prove this can fail" is what an oracle does, so instrument certification travels with
   the oracle work, not the lifecycle work.

Two standing constraints on 5a:

- **5a does not build tamper evidence.** A retraction record is as deletable as the
  record it retracts; the four §8.7 consequences gain a fifth (deleting a correction
  silently restores standing) rather than losing any. 5a's scope section states this
  non-goal explicitly, so the judgment cluster is not read as closing §8.7 by
  adjacency — the same "hygiene, not tamper evidence" line the kernel drew for the
  verification constructor.
- **One form, decided first.** Whether verification retraction, conflict-route
  retirement, and coverage narrowing are one lifecycle form — an authored, attributed
  act that subtracts standing without deleting a record, with an optional
  replacement — is 5a's opening decision. If they share the form, 5a defines it once
  and instantiates it three times, and coverage narrowing's visibility rule falls out
  of the shared form.

Two standing constraints on 5b:

- **The guarantee tables stay frozen under their current ids.** G1, G2a–G2c, G3–G8,
  S1–S8, W1–W13, R1–R23 are conformance oracles in embryo; 5a extends, never renumbers, so 5b inherits
  them unchanged and gives them a version and a conformance meaning.
- **`nodes`' STANDARD transfers as form, not force.** Its three-tier model exists to stop
  two language implementations drifting; science has one implementation. The reusable
  form is the versioned normative doc, frozen oracles, and explicit change policy;
  science's reason for the oracles is its own estimator doctrine — a check must be able
  to fail.

## 3. Order of work

1. **Sub-problem 5a** — retraction + correction lifecycle. **Banked 2026-08-03.**
2. **World-index packaging design** — where it lives, who writes it, staleness and
   consistency semantics, with §9 anchor carriage as a stated consumer (repro §9
   amendment). Everything in artifact 1's "waits on it" column leans here; it should not
   be designed last by default. 5a added two more consumers: the retraction map (its
   fourth derived map) and the temporal half of 5a's limitation 6, which explicitly
   defers a fresh retraction's reach to this design's staleness semantics.
   **Banked 2026-08-03.**
3. **Sub-problem 5b** — normative contract + oracles + instrument certification, after
   5a's operations exist. **Banked 2026-08-03.** Items 4–6 below proceed on
   their own clocks; the design track's next open item is the §9 log design.
4. **`nodes` contract deltas** land on their own clock; required before profile
   implementation, not before design.
5. **`atoms` A6–A8** proceed independently; composition-root adoption follows.
6. **§9 log design** after the world-index packaging design settles the anchor.
   **Banked 2026-08-03** (`2026-08-03-tamper-evident-log-design.md`);
   L1–L13 await implementation with A6–A8.
7. **Domain extension boundary** — where domain-specific material lives, and how
   `science` is organized so a later decomposition into packs is a move rather
   than a rewrite. **Banked 2026-08-04**
   (`2026-08-04-domain-extension-boundary-design.md`); D1–D10 await
   implementation. Its §12 named the **predicate vocabulary** as the next
   focused design; that became item 8.
8. **Formal model and typed claim calculus** — taken instead of a
   predicate-vocabulary design on its own, because the vocabulary question could
   not be answered without saying what a proposition *is*. **Banked 2026-08-05**
   (`2026-08-04-formal-model-and-claim-calculus-design.md`); **M1–M13** await
   implementation. Two consequences for the order of work: its **ρO** rows open
   three questions that belong to other designs — merge versus a retraction's
   immutable exact target (world §10), binding-check persistence and its
   correction path (kernel limitation 4), and a population vocabulary — and its
   **implementation authorities** (the claim grammar and kernel tag bytes, the
   `π_claim` projection under `science.identity.v1`, claim-schema compilation,
   and a cross-language parity fixture) have no home yet and are prerequisites
   for building M\*, not for banking it. **Sited 2026-08-06** at the start of
   item 10 (formal model §8, home column); *sited* is not *built*. Three of the
   four are now built — the base contract, `π_claim`/`tag_claim` under
   `science.identity.v1`, and claim-schema compilation — and the fourth, the
   parity fixture, is **frozen and consumed by both implementations**. A
   *second* fixture is now owed and is outside cut 1: `science.identity.v1`'s
   numeric and escape arms are tested twice and compared never (formal model §8).
9. **Belief policy** — taken next because the review-disposition record's §5.5
   stop rule puts it ahead of the vertical slice: the slice stops at the last
   fully designed seam, and anything computing belief had no seam to stop at.
   **Banked 2026-08-05** (`2026-08-05-belief-policy-design.md`); **P1–P9** await
   implementation. The disposition record's F3 called belief aggregation
   undesigned; that was too broad — kernel §4.2.1 designs the aggregation
   *structure* in depth and substrate S6 already tests eight arms of it. What was
   missing was every scalar it is parameterized by, and the identity pinning
   them. Two consequences for the order of work: weighting by study design or
   precision is **blocked on ρO3** rather than deferred, so no weighted successor
   policy can be written until estimand typing has an owner; and non-empirical
   propositions return an absence reason that deliberately collapses *not
   attempted* with *no applicable route*, which is uncollapsed by whichever
   arrives first — kernel §11's second route, or a route-applicability predicate.
10. **The conformance cut 1 vertical slice** — the first code in this
    repository, and the end of the design-only phase. **Built and merged
    2026-08-07** (`f81d3a3`): 391 Python tests and 101 TypeScript, every one of
    the eleven selected rows carrying executable arms, and the §5.5 stop rule
    held — no belief computed, no persistence boundary crossed. Both gates the
    disposition record put in front of it were open when it started: cut 1 froze
    prospectively (§5, 2026-08-05) and the §5.5 stop rule's belief-policy
    prerequisite was discharged (item 9). Its acceptance criteria were **cut 1's
    eleven rows as frozen** — six fully selected, five part-selected — and it
    adds **no** guarantee table of its own; a slice that minted its own oracles
    would be grading its own homework, which is what freezing the cut in advance
    exists to prevent.

    **N2 is what the slice added to the corpus's practice.** Its trigger is the
    first executable suite, so it landed as a harness rather than a habit: 42
    arms declared as data — the row, what it asserts, a source mutation that
    makes it false, and the exact tests that must fail — applied to a copy of
    the package and audited, with `vacuous`, `uncollected` and `stale` reported
    as malformed contract content rather than as failing tests. Ten of the first
    forty arms were defective on the first audit. The disposition record's §5
    carries what that cost and what it found.

    Three things this item is **not**. It is not the world index, a corpus, a
    run, or a belief — §5.1 puts every persistence boundary outside it, so it
    waits on neither `atoms` A6–A8 nor the `nodes` contract deltas (items 4 and
    5), and it can be built and tested standing alone. It is not `KindSpec`
    compilation — **D4 is fully deferred**, and only the claim-schema half of
    `ProfileSpec` is in scope. And it is not a second implementation in
    TypeScript: formal model limitation 9 records **M10 as the only
    cross-implementation row**, so `ts/` carries the shared encoding and stops.

    One consequence for the order of work. Formal model §8 cited D §6's
    namespaced-facet-key parity fixture as the **existing** precedent for the
    claim parity fixture; measured against the trees it is neither existing nor
    namespaced (§8, corrected 2026-08-06). So M10's fixture is the corpus's
    **first** typed parity fixture and defines the shape rather than inheriting
    one — and D §6's own fixture remains outstanding, unblocked by this item and
    not in cut 1.

11. **The multi-corpus typing exercise** — the first consumer of cut 1's slice,
    and the first measurement in this redesign that is not taken over mm30 alone.
    **Designed 2026-08-07**
    (`2026-08-07-corpus-survey-and-vocabulary-admission-design.md`); awaits
    implementation. It compiles a claim vocabulary for mm30, natural-systems and
    post-acute-infection, then runs `build_claim` over every proposition in all
    three.

    **Why it is not an mm30 exercise.** A survey of **eight** proto-science
    corpora (6,860 records) measured that of 337 structured propositions across
    all of them, **307 are mm30's** — and the only two other corpora carrying
    subject/predicate/object use a single operator, `affects`, between them.
    mm30 is also the corpus every banked design was written while looking at, so
    it can confirm the calculus and cannot test it. The disposition record's
    limitation 3 already bounds its §2.3 figures to *"the mm30 authored set and
    for nothing else"*; what the survey adds is that the bound cannot be lifted
    by finding a second corpus, because no second corpus has a claim vocabulary
    to measure. One has to be authored. This item is that work, and it is what
    makes the 6-of-16 expressiveness figure and the 6-of-27 reproduction yield
    measured rather than hand-computed.

    Two results are **predicted in writing before the run**, on the same
    discipline that froze cut 1 prospectively. post-acute-infection's evidence is
    100% literature (95 of 95) with no eligibility field at all, so under **G1**
    its belief output is expected to be **empty** — and an empty result there is a
    **pass**, not a broken tool. natural-systems is at most 26% claim-bearing and
    largely process narrative, so the expected finding is a constraint on the base
    profile: it must not *require* a claim calculus.

    Every candidate vocabulary field the exercise surfaces is run against
    domain-extension **2.6** — agreement and exercise over all **eight** surveyed
    corpora, not the three being typed, then the **reader** clause, which is what
    actually admits. That widening is not caution: 2.6's own first draft was
    checked against three corpora, passed, and inverted against eight (corpus
    survey §4.1). The exercise **must not mint relation kinds** for what it finds
    — **2.7** rules one navigation-only `see-also` edge, and a typing pass is
    exactly where a plausible relation gets invented for a single record. The
    disposition record's §5.5 stop rule is inherited unchanged: no belief
    computed, no persistence boundary crossed, and a typing that would need either
    is recorded as *blocked on A6–A8* rather than worked around.

    The base profile requires claim **capability**, not claim **instances**
    (corpus survey §9.2): zero claims and zero activated operator contracts is
    conforming, with no profile variant and no activation flag. If a claim exists
    it must type; a proposition that will not type is typing work, not a licensed
    exception.

## 4. Invariants and gates to pin when their layer lands

- **Concurrent-merge interleaving.** Single-writer holds per corpus, but two writers in
  two corpora can each merge across the other's referrers. The redirect makes partial
  application correct; pin it with a stated invariant test when the world layer lands,
  rather than leaving "one world does not add concurrency" (world lim. 5) to carry the
  claim alone.
- **Measurement gates.** Exact maximum-independent-set aggregation and belief-digest
  closure recomputation get measured at mm30 scale before any optimization — the same
  rule substrate §8 applies to `nodes` indexes.
- **Cold arrivals.** A corpus arriving by copy/sync without engine metadata is a normal
  cold bootstrap (`atoms` §7); a corpus arriving *with* another host's metadata is a
  restored-backup classification case. Neither is corruption; both should appear in the
  world-index packaging design's staleness story.

## 5. Repository and package decomposition (ruled 2026-08-04)

The system lives under one GitHub organization, **`verifiably`**, alongside its two
substrates. The organization, not the repository name, is what makes short generic
names (`atoms`, `nodes`, `science`) defensible: they are layer names in one stack.

**Distribution namespaces are flat and the organization does not namespace them.**
The rulings, so they are not re-derived: npm uses the scope — `@verifiably/<name>`;
PyPI has no scopes, so the *distribution* name is `verifiably-<name>` while the
*import* name stays bare (`pip install verifiably-science`, `import science`). The
ugly name is confined to the install line.

**Three boundaries, deliberately not conflated:** what is cloned (repository), what
is installed (distribution), and what imports what (module). Module boundaries are
free and are drawn eagerly. Distribution boundaries are expensive and
hard to reverse — version matrices, release choreography, cross-package
migrations — so they are drawn reluctantly, on the `atoms`/`nodes` test: **split on
an observed second consumer or a genuinely different constraint regime, never on a
projected one.** This is the same discipline computation-reproducibility §9 applies
to the content-addressable store, one level up.

Two splits pass that test now:

- **The normative contract and its conformance oracles**, on doctrinal grounds
  rather than taste. 5b requires **code-lineage independence** for instrument
  certification: an oracle sharing code with the implementation it tests cannot
  independently falsify it, so a suite shipped inside the package it verifies makes
  independence an assertion with no mechanism. Separate distribution makes it
  enforceable and lets a third party run the suite against any implementation —
  the reason `nodes` has a STANDARD.
- **The agent surface** (skills, commands, coding-agent plugin manifests). The
  second consumer is already observed, not projected, and the cadence differs in
  kind: the surface churns while the kernel must not, because belief digests
  depend on kernel semantics. Coupling would also force every library consumer to
  carry agent plumbing it never calls.

Everything else stays in one `science` distribution: the epistemic kernel, world
addressing, computation and reproducibility, the correction lifecycle, world-index
packaging, and the mutation log are **one guarantee surface that co-evolves** — the
2026-08-03 banking commit alone amended five documents across four of them, and as
separate packages each such amendment becomes a multi-repo version dance. The
**CLI** is a consumer of the library and splitting it later is nearly free, so it
stays in-repo behind its own entry point.

Three things are **not** packages:

- **The meta-science arm** is research *about* the system. Under §0 it is
  reproduced as a project and corpus **managed by** the system, not code shipped
  beside it — which makes it the first serious dogfooding consumer.
- **The autonomous arm** is policy over the agent surface (what may run
  unattended, envelope and supervision): a consumer, not a peer.
- **`commons`** keeps its existing repository and its own audience (other
  installations); it consumes the world index.

**Record the seam now, materialize it later.** Empty repositories accumulate stale
scaffolding and imply structure nothing has validated, so the split happens when
the code exists to split, not at organization-creation time.

One dependency is open: the conformance package cannot be scoped until the
**first contract cut** (§1, artifact 7) names what the contract is a contract
*for*. The package boundary and the contract's scope are decided together.
