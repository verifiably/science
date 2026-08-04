# Retraction and the correction lifecycle — design (sub-problem 5a)

**Status:** Banked 2026-08-03. First of the two sub-problem 5 clusters (adoption
ledger §2); the kernel document's §3.3, G8 row, and §8.7 consequences table were
amended in the banking commit.
**Inherits:** comp §5.2's fixed form and §12's two open halves; world §4.3 (conflict
routes) and limitation 11 (refuted snapshots); comp §11.13 (nothing retires a run) and
the coverage-accountability question (comp §11, world limitation 11's coda).
**Constraints (ledger §2):** the guarantee tables G/S/W/R stay frozen — this design
extends and, where a banked rule must change (G8, §7a), amends in place under the same
identifier, never renumbering; and nothing here is tamper evidence (§8).

## 1. Why

Every correction mechanism the banked designs have is a *minting* mechanism — a
successor spec, a superseding verification, a corrected re-execution, a corrected
snapshot — and each adds a record beside the wrong one rather than removing the wrong
one's contribution. That is correct for provenance and insufficient for belief. Four
banked limitations say so from four directions: a run later found defective keeps its
assessment contributing at its original address (comp §11.13); a false exclusion
certification on a `dataset-production` run stays epistemically active (comp §5.2); a
conflicted lineage basis is permanent because no operation retires a route shown to be
wrong (world §4.3); a refuted snapshot remains a well-formed record that a computation
can still name and compute the false value from (world limitation 11).

The form is already fixed (comp §5.2): additive — a new node, never an edit; attributed
and rationale-bearing — a claim, not a computation; a belief input, so kernel §5.1's
digest covers it or a retracted and an unretracted corpus would hash alike;
structurally subtractive — its only effect is that a named input is no longer read,
with belief recomputed by the ordinary policy; and itself eligibility-bearing. What was
handed here open: **what carries it** and **what makes one eligible**.

## 2. The opening ruling — one form, three instantiations

Verification-and-assessment retraction, conflict-route retirement, and
coverage-declaration narrowing are **one lifecycle form**:

> An authored, attributed, immutable record that subtracts a named input's **standing**
> without touching the input, optionally naming a successor record, with the affected
> computations rereading their inputs through the ordinary policy.

Comp §12 asked whether a false exclusion certification, a defective implementation, and
a corrupt input are the same shape but different records. Ruled: **one record, reasons
as data.** The computation's response is identical regardless of reason — stop reading
the named input and recompute — so the reason belongs in the record's content (a typed
code plus prose rationale), not in the record's kind. Splitting the mechanism per
reason would constrain the operation by its motivation, which is the same
wrong-noun slip comp §5.2 caught twice ("constraining the output of an operation that
should be constrained in its form").

This completes the correction lifecycle as a three-member set, each authored, each
additive, each digest-visible:

| operation | exists | corrects | by |
|---|---|---|---|
| `supersedes` | kernel §4.1 | a proposition's semantic content | minting a successor |
| merge | world §4.3 | two records of one identity | recording a claim, unioning routes |
| **retraction** | **this design** | a record's **standing** as a read input | subtracting it from the read set |

## 3. What carries it — the `retraction` kind

One new immutable kernel kind, **`retraction`**, the ninth. Its content:

- **target** — a **discriminated union**, because the readable inputs are not all
  nodes. The `node` arm names a world-kind record the way the kernel names
  everything: stored ref **and** its resolution at authoring time, recorded
  separately, plus the record's content identity — this arm covers assessments,
  verifications, semantic snapshots, and — since 2026-08-03 (normative-contract
  §7.2) — `instrument-certification` records, whose standing scope derivation
  reads. The `route` arm names a component embedded
  in a record: a `node`-shaped reference to the dataset carrying the stamped lineage
  basis, plus the route's own identity within that basis — the `science.identity.v1`
  digest of the route tuple as the basis records it. Comp §5.2's correction is
  normative across both arms: the target is whatever the computation *reads*, never
  "the run" whose defect motivated the act. A `dataset-production` run has no
  assessment; what its false certification corrupts is the lineage closure, and the
  retraction's `route` arm names exactly that.
- **reason** — a typed code from a closed initial vocabulary (`defective-code`,
  `environment-miscapture`, `corrupt-input`, `false-certification`, `wrong-route`,
  `upstream-retraction`, `authored-error`) plus prose rationale. The vocabulary is
  data, extensible by minor amendment; the mechanism never branches on it.
- **grounds** — refs to the recorded evidence the retraction rests on (§5).
- **successor** (optional, informational) — the replacement record, when one exists (a
  narrowing retraction names the narrowed successor snapshot, §4; a plain retraction
  names none). It is a pointer for reviewers and diagnostics, **never an implicit
  redirect**: computations select their snapshot explicitly (world §5.1), and nothing
  resolves through a retraction to its successor.
- **actor** and a minted **event token**. The token is in the identity basis (the run
  occurrence precedent): two retractions of one target by one actor for two reasons are
  two records, and repetition never collides an address.

`retraction` is a **world kind** — its `node`-arm targets are world kinds that need not
share its corpus, and its `route`-arm targets are identified components embedded in
one — with a content-derived address over the basis above. It is immutable with no
revision path: a wrongful retraction is corrected by retracting *it* (§6, chain not
toggle). It is admitted at the write boundary and validated at import/audit exactly as
verifications are; a raw-written retraction is the standard raw-write case — undetected
until audit, then reported.

## 4. Standing — what "no longer read" means per target

Standing is **computed, never stored on the target**. The target is byte-unchanged; a
reader joins the retraction records at read time. Two definitions make that
well-founded and discoverable:

**Standing, defined.** An input's standing is subtracted iff **at least one standing
retraction targets it**, and a retraction is itself standing unless a standing
retraction targets *it*. The recursion is well-founded: a retraction's identity covers
its target's identity, so a cycle would require two records each containing the
other's digest — unconstructible. A counter-retraction therefore restores nothing by
itself; it removes one retraction from standing, and the target's standing returns
**iff no sibling standing retraction remains** (event tokens permit several
retractions of one target; C5 pins the sibling case).

**Discovery, bounded.** Retractions are joined through the world index, which gains a
**fourth derived map** — the retraction map, target identity → retraction addresses —
beside address, alias, and producers (world §5; a new consumer requirement for the
index packaging design, recorded in the adoption ledger). A computation enumerates it
over the **same declared coverage and recorded corpus states as its producer
enumeration**, and the enumeration — the found refs, their resolutions, and the
coverage declaration — enters the closure (§6). The exact corpus states the
enumeration ran at are **receipt material, never digest members**: world §5's
semantic-snapshot/receipt split holds here as it holds for the producer snapshot,
so a corpus move changes what the receipt records and nothing about belief. "None
exist" is therefore always a statement *relative to declared coverage at recorded
states*, never an absolute: a standing retraction in an uncovered corpus — or one
minted after the index state the enumeration read — does not reach the computation,
and the declaration's presence in the digest is what makes that bound visible rather
than silent (§8).

Per instantiation:

- **Assessment.** A retracted assessment leaves belief aggregation's read set. Support
  and dispute both: retracting a refuting assessment legitimately raises support (comp
  §5.2's monotone-downward correction is preserved as a guarantee, C4).
- **Verification.** A retracted verification leaves admission's read set, and the
  fail-closed lifecycle recomputes: retracting a false *failing* verification restores
  the assessment's admission iff a standing passing verification remains; retracting a
  false *passing* one de-admits. This **amends banked G8** rather than leaving it
  untouched — G8's "active" currently admits exactly one clearing path for a recorded
  failure (a resolution: a superseding verification explicitly naming it) — and the
  amendment is stated precisely in §7a, identifier retained. The recomputation itself
  is the one the G8 deletion negative performs illegitimately; retraction is its
  attributed, digest-visible legitimate twin, which is what finally licenses the
  profile rule that deleting a verification is *never* the sanctioned path (kernel
  §3.3's hygiene guard).
- **Production route.** Retirement (the `route` target arm, §3) removes a route from
  the lineage closure's read set.
  The stored basis facet is untouched — §5.2 route-preservation holds through this path
  as it holds through merge — and the **effective** tag is computed over unretired
  routes: exactly one survivor → certifiable over that route; several → still
  `conflict`; zero → `not-certified`, never silently single. Merge-widening then
  retirement composes: union the routes, then subtract standing.
- **Semantic snapshot.** A retracted snapshot is refused at import and reported by the
  evaluator's outcomes (`retracted` joins `malformed`/`validated`/`refuted`/
  `unresolvable`) at the three call sites that already recompute — import, audit,
  diagnostic query. Mounting a corpus still performs nothing (world's mount rule); a
  raw computation that ignores retraction records can still read the bytes. "Unusable"
  is therefore bounded the way every enforcement claim here is bounded: enforced at
  boundaries, detected at audit (§8).
- **Coverage narrowing.** Coverage is part of a snapshot's identity, and computations
  select a snapshot explicitly with no implicit successor (world §5) — so nothing here
  recomputes an "effective coverage" behind a standing identity. Narrowing is
  **snapshot succession plus retraction**: derive the narrowed successor snapshot
  under the new declaration through the ordinary machinery, then retract the old
  snapshot with `successor` naming the new one (informational, §3). Computations that
  named the old snapshot hit C8's refusal at the boundaries; receipts naming it
  remain valid records *of the old enumeration*; narrowing is visible because the
  retraction is a record and a §5.1 digest member. "Who may narrow" is answered the
  only way this system answers authority questions: anyone who can write,
  attributably, visibly, reviewably (§5) — accountability by exposure, not by
  permission. A coverage declaration is therefore **not a separate target class**;
  the eligible-target set stays two arms.

**Eligible targets are exactly the readable inputs.** A record is retraction-eligible
iff a computed view reads its standing: assessments, verifications, semantic
snapshots, and instrument certifications (the `node` arm — the last added at
5b's banking, normative-contract §7.2, by exactly this test), and production
routes (the `route` arm). Propositions are
not (their lifecycle is `supersedes`); runs are not (a run happened; its readable
products are the targets); notes and coordination kinds are not (outside every
closure). A retraction naming an ineligible or ill-formed target is malformed —
refused at the boundary, an audit finding when raw-written.

## 5. Eligibility — the harder half, answered procedurally

Nothing about a subtractive form stops "remove the evidence against my claim": a
retraction can raise belief, so its eligibility contract is the design's real content.
The contract is **procedural, not epistemic** — no one certifies a retraction true; the
system makes it *expensive to issue invisibly* and *cheap to review and reverse*:

1. **Named input** (§4): the target must be an eligible, resolvable input, named by
   content identity. No wildcard, no "everything from this author", no target-by-path.
2. **Attribution and typed rationale**: actor, reason code, prose. Refused at the write
   boundary if absent.
3. **Grounding**: the retraction names at least one recorded ground — a failing or
   superseding verification, a divergent replay, an audit finding, an upstream
   retraction recorded as a source-assertion, or an authored note recording the
   discovery. A ground is itself authorable, so this is a paper-trail requirement, not
   a truth gate — stated plainly rather than dressed as one (§8). Its force is that a
   bare, groundless subtraction is unspellable, and every retraction arrives pointing
   at *something* a reviewer can independently weigh.
4. **Symmetry**: retractions are themselves eligible targets (`node` arm). A
   counter-retraction removes one retraction from standing; the original target's
   standing returns **iff no sibling standing retraction remains** (§4's definition —
   event tokens permit several retractions of one target, and one counter-retraction
   answers one of them). The chain is additive and every link is digest-covered. There
   is no toggle and no erasure — a corpus that went wrong and was corrected is forever
   distinguishable from one that was never wrong (C5).
5. **Exposure**: a retraction that moves belief is precisely what the divergence view
   surfaces and ranks as review work. This is not 5a machinery — it is the standing
   kernel machinery receiving a new input kind — but it is the ecosystem's actual
   answer to "against what standard is a retraction reviewed."

**Exogenous retractions are not this kind.** A journal retracting a paper, a repository
withdrawing an accession — those are observed facts about sources, recorded as
source-assertions (typed as measurements of what someone wrote, kernel §2). They do not
subtract anything by themselves; they are the natural *grounds* for endogenous
retractions of the assessments and routes that depended on the withdrawn thing. The
boundary matters: collapsing the two would let a discourse observation mutate belief
standing without an attributed act, which is the literature→belief edge the kernel
spent its first invariant removing.

## 6. The digest — history is not erased

Kernel §5.1's closure gains the rule: **for every input in a computation's closure, the
retraction enumeration over that input is in the closure** — the found retraction refs
and their resolutions, *and* the coverage declaration the enumeration ran under (§4's
discovery bound), exactly as the producer snapshot enters with its coverage rather
than as a bare member set. The exact corpus states the enumeration ran at go to the
derivation receipt, **not** the digest — world §5 split those deliberately, and this
rule inherits the split: a corpus move changes state identities and therefore
receipts, and a digest that moved with it would make relocation a belief event.
Consequences, pinned by C3/C5:

- a standing retraction inside the declared coverage moves the belief input digest of
  every computation whose closure contains its target, and no other computation's;
- a retraction *outside* the declared coverage moves nothing — and the declaration's
  presence in the digest is what keeps that a visible bound instead of a silent gap;
- an in-coverage **corpus move** — records relocated, state identities changed,
  content identities unchanged — moves receipts and nothing else; the digest is
  invariant under relocation, exactly as world §5 rules for every other closure
  member;
- retract-then-counter-retract restores admission and belief while producing a third
  distinct digest — state A (never wrong) and state C (wrong, corrected) agree in what
  they admit and differ in what they hash. The digest is the memory; the records are
  the audit trail; nothing recomputes to a state indistinguishable from innocence.

## 7. Guarantees

### 7a. Amendment to banked G8 (identifier retained)

G8's lifecycle (kernel §3.3) defines "active" as *not superseded by a later
verification that explicitly references it*, and rules that a recorded failing
verification is cleared **only** by a resolution — never by adding a passing sibling.
This design adds a second explicit path and amends the definition in place, under the
same identifier:

> **"Active" (amended):** not superseded by a later verification that explicitly
> references it, **and not targeted by a standing retraction (§4)**. While it is
> recorded, a failing verification is cleared only by a **resolution** — a subsequent
> verification naming the failure it supersedes — **or by a standing retraction**,
> both addressed, attributed acts; and never by adding a passing sibling. Precedence
> remains explicit supersession, now joined by explicit subtraction.

G8's mutation test gains the retraction path (C6 exercises it); its deletion negative
is untouched — raw deletion still restores admission undetectably (kernel §8.7). The
kernel document's §3.3 wording, its G8 row, and its §8.7 consequences table (four
undetectable actions become five, limitation 1) were amended in the banking commit.
The ledger's frozen-id rule is satisfied: G8 is extended and re-defined under its own
id; nothing is renumbered.

### 7b. New guarantees

New table, new prefix; beyond the §7a amendment, G/S/W/R are untouched. Each row is
certified by mutation, per the estimator doctrine — every check must be able to fail.

| # | guarantee | mutation test |
|---|---|---|
| C1 | Retraction is additive: the target is byte-identical and still resolvable after | retract; assert target bytes, address, and resolution unchanged; assert no API edits or deletes a target |
| C2 | Attribution, reason, and ground are required at the boundary | submit a retraction missing each in turn; assert refusal with no file written |
| C3 | The digest covers the retraction enumeration — refs, resolutions, and coverage declaration; never exact corpus states | retract an in-closure, in-coverage input → digest moves; input outside the closure → unchanged; **standing retraction in an uncovered corpus → digest unchanged, and the coverage declaration is itself a digest member — the bound is visible, not silent**; **in-coverage corpus move (content identities unchanged) → digest unchanged, receipt records the new states** |
| C4 | Subtraction is direction-free | retract a supporting assessment → support falls; retract a refuting one → support rises; assert both apply identically |
| C5 | Chain, not toggle — and standing is sibling-aware | retract, then counter-retract → admission equals the initial state while all three digests are pairwise distinct; **two sibling retractions of one target, counter-retract one → standing stays subtracted until the second is also counter-retracted** |
| C6 | Verification retraction recomputes admission fail-closed under amended G8 (§7a) | retract a false failing verification → admitted iff a standing passing one remains; retract the passing one → unadmitted; a passing *sibling* still clears nothing. **Negative (unchanged):** raw deletion of a verification still restores admission undetectably — kernel §8.7's bound stands, §8 |
| C7 | Route retirement never selects silently | conflict of two routes: retire one → certifiable over the survivor; retire both → `not-certified`; assert stored basis facet unchanged throughout (route preservation) |
| C8 | A retracted snapshot is refused where recomputation already happens | import naming it refuses before any write; audit and diagnostic query report `retracted`; **negative:** mounting the corpus writes nothing and validates nothing |
| C9 | Narrowing is snapshot succession plus retraction, never mutation behind an identity | derive the narrowed successor snapshot, retract the old naming it as `successor`; assert the old snapshot's identity and its receipts are byte-unchanged, a computation naming the old hits C8's refusal, one naming the new proceeds, and the digest moves. **Negative:** nothing resolves through the retraction to the successor implicitly |
| C10 | Ineligible or ill-formed targets are unspellable through the boundary | retraction naming a note, a proposition, a run → refused; **a `route` arm naming a route absent from the named dataset's stamped basis → malformed**; a retraction naming an `instrument-certification` → **eligible** (added 2026-08-03, normative-contract §7.2 — its standing is read by scope derivation); raw-write each refused case and assert the audit reports it |

## 8. Limitations

1. **Not tamper evidence — the fifth §8.7 consequence, stated on arrival.** Deleting a
   retraction record silently restores the target's standing, exactly as deleting a
   failing verification silently restores admission. The four undetectable actions of
   kernel §8.7 become five, and §9's mutation log ("the deletion, as a mutation")
   already generalizes over the fifth. Nothing in this design closes any of them; the
   ledger's constraint stands — this is the verification constructor's "hygiene, not
   tamper evidence" line, redrawn around a new kind.
2. **Attribution is recorded, not authenticated.** There is no identity system; "who
   may issue one" is answered by exposure and symmetry (§5), not by permission. An
   attributed false retraction is reviewable and reversible; an unattributed one is
   unspellable through the boundary and an audit finding outside it. That is the whole
   claim.
3. **Grounding is procedural.** A ground can itself be authored; the requirement
   produces a reviewable trail, not a certified truth. Dressing it as more would
   rebuild authored belief one relation upstream (the comp §11 limitation-12 shape).
4. **"Unusable" is boundary-bounded.** A raw reader can compute from a retracted
   snapshot's bytes; enforcement lives at import, audit, and query, like every other
   enforcement claim in the banked designs.
5. **Reason vocabulary is initial.** The closed set in §3 will grow by amendment; the
   mechanism is invariant under it by construction (§2's ruling).
6. **Discovery is enumeration-bounded.** A standing retraction reaches a computation
   only through the enumeration it ran, which is bounded twice: **spatially** — a
   retraction in a corpus outside the declared coverage does not reach it, the same
   bound the producers map lives with; and **temporally** — a retraction minted after
   the index state the enumeration read is invisible until a later enumeration, so a
   fresh retraction's reach inherits whatever staleness semantics the world index's
   packaging design settles. Both bounds are visible the same way: the coverage
   declaration is in the digest, and the states the enumeration ran at are in the
   receipt. Widening coverage and re-enumerating are the remedies; nothing here
   discovers what no enumeration was asked, or able, to see.

## 9. Open questions

- **The `source`/`dataset` instantiation.** An upstream withdrawal grounds retractions
  of dependent assessments and routes, but should a *dataset's* own
  empirical-observation standing be retractable directly (the acquisition boundary is
  authored — kernel limitation 8)? Deferred until a concrete case forces it; the
  eligible-target test (§4) admits it without a new mechanism if so.
- **Relation names.** ~~`retracts`, `grounded-in`, `succeeded-by` are provisional
  pending sub-problem 5b's contract, which owns the normative vocabulary.~~
  **Closed 2026-08-03:** adopted as-is into the contract's normative relation
  vocabulary at the first cut (normative-contract §7.7).
- **Review surface.** How retraction-driven divergence is ranked and presented is
  sub-problem 6's daily-surface question, not answered here.
