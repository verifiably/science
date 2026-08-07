# Corpus survey and vocabulary admission — design

**Date:** 2026-08-07
**Status:** design, approved in session
**Scope:** evidence for, and one ruling over, what may enter the `science` base
profile. Amends domain-extension §2 in place and adds item 11 to the ledger's
order of work. Mints no guarantee table — §7 says why.

## 1. Why

Every empirical claim in this redesign so far rests on **one** corpus. The
kernel's §1 argument is built from `proto-science`'s code and a 62-item feedback
log. The disposition record's §2.3 figures — **expressiveness 6 of 16**, and a
**reproduction yield of 6 of 27 with 11 undetermined** — were computed by hand
against 27 mm30 records and nothing else.

That record does not hide it: its **limitation 3** says outright that §2 *"sizes
limitation 4 for the mm30 authored set and for nothing else,"* and its limitation
2 forbids quoting either figure until two adjudications settle. So the obligation
this document discharges is one the corpus already **stated** and left open — not
one it concealed.

One corpus cannot distinguish a property of science from a property of a project.
That is not hypothetical: mm30 is the most elaborated corpus we have and the one
every banked design was written while looking at. Measuring it again would
confirm.

So this document measures **eight** corpora that grew under proto-science, with
different subject matter, scale and working style — 6,860 records in total:

| corpus | what it is | records | kinds |
|---|---|---|---|
| **mm30** | empirical analysis across 30 myeloma transcriptomic datasets | 2,737 | 37 |
| **natural-systems** | a curated catalog of mathematical models of natural systems | 1,059 | 25 |
| **post-acute-infection** | literature synthesis of post-acute infection syndromes | 729 | 22 |
| **cycles** | health processes — biological rhythms | 539 | 19 |
| **cbioportal** | a cancer data source | 491 | 20 |
| **protein-landscape** | protein structure/function landscape | 460 | 21 |
| **health/meta** | cross-cutting health methodology | 451 | 11 |
| **evolution** | cancer mechanisms — somatic evolution | 394 | 19 |

They are not a sample. They are the eight largest bodies of work the predecessor
system produced, they share one author, and they grew under one system. The
argument below is therefore built on **disagreement among them** wherever
possible, which needs no representativeness — where it rests on agreement, §8
says so.

**This document was drafted against three corpora and its central ruling was
wrong.** Running the other five inverted it (§4.1). The rewrite is the finding as
much as the ruling is.

## 2. The instrument

`python/tools/survey_corpora.py`, run by hand against corpus directories that
live outside this repository and are not vendored into it. Nothing in it runs in
CI and nothing in it is a conformance oracle (§7).

Two of its properties are load-bearing for what §3 concludes.

**It discovers vocabulary-shaped fields rather than being handed a list.** Every
scalar field clearing a floor of 20 occurrences is classified by two computed
ratios — `free-text` when distinct values exceed half the occurrences,
`collapsed` when the top value covers 90% or more, `discriminating` otherwise.
Passing it the fields we already suspected would have confirmed the suspicion and
found nothing else. Several findings below are fields nobody thought to name.

**A parse failure is counted and named, never skipped.** Every share reported is
a fraction of a denominator, and silently dropping records shrinks denominators.
All 6,860 records parsed; the unparsed count is zero in all eight corpora.

### 2.1 Four instrument defects, found and corrected

An instrument that decides a ruling has to be read as adversarially as the ruling.
Four defects were found — one before banking, three in review — and each changed a
reported number. Two changed a ruling. The link measurement was corrected **twice**,
which is the point of the section: the first correction was checked against the
cases that motivated it and passed, and a second reading found cases it still let
through.

The predicates are now covered by `python/tests/test_survey_instrument.py`, with a
case per defect below. The survey itself is still not run by any test — a test
asserting a *finding* would assert something CI cannot see — but nothing stops the
predicates that decide the findings from being tested, and nothing should have.

**Encoding drift does not exist; the regex did.** A regex pass appeared to show
`evidence_type` written both as `literature` and as `"literature"` in
post-acute-infection, reported as encoding drift inside one corpus. YAML resolves
both spellings to the same string. The instrument reports **no** encoding drift in
any corpus, and preserve/require/normalize gains no support from it.

**`nested` was not testing nestedness.** The agreement verdict asked whether *some*
corpus's value set equalled the union. That is not a chain: `{a,b,c}`, `{a,b}`,
`{a,c}` has a set equal to the union while `{a,b}` and `{a,c}` each carry a term
the other lacks. Nestedness requires **every pair comparable by inclusion**.
`evidence_type` is exactly that shape — mm30 has `expert_judgment`, cycles has
`simulation`, neither contains the other — and so is
`identification_strength`, where cycles adds `longitudinal` and cbioportal adds
`none`. **Both were reported nested and are divergent**, which moves both out of
the base profile under §4.

**Reference *shape* is not a relation edge (first correction).** The link
measurement accepted any `head:tail` with an alphanumeric head, which admitted
every ISO timestamp (`2026-08-07T10:49:59` partitions to a perfectly alphanumeric
head) and every URL; it counted `id`, which is a record naming itself rather than
an edge; and for a list it added the list's **full length** when a single element
matched. The correction required a lowercase kind-shaped head that is not a URI
scheme, excluded self-reference, and counted only the elements that are actually
references. The field tally fell from 67 to 61 and the universal set from 5 to 3.

**Reference shape is still not a relation edge (second correction).** The first
correction constrained the *head* and left the tail unconstrained, so any prose
containing a colon still counted — which is exactly what a title is. `title` was
counted as a link field **314 times** in mm30. `sha256:` passed too, because a
content address has a kind-shaped head; `content_hash` was counted three times in
natural-systems. The measurement now requires the **whole value** to be a
whitespace-free `<kind>:<id>` token whose head is neither a URI scheme, an
identifier authority (`doi`, `pmid`, `orcid`, …) nor a digest algorithm, and it
excludes by name the fields that name or display a record rather than pointing at
one — `id`, `title`, `name`, `slug`, `content_hash` and their neighbours. Those
are excluded by name deliberately: no shape rule separates `mm30:0001` used as an
id from the same string used as a target. The field tally falls again, 61 to
**56**, and the universal set holds at **3** — now named in the output, so the
tally can be objected to rather than only counted: `related`, `datasets`,
`source_refs`.

§3.5's conclusion survives both corrections — `related`'s share moves 61–83% →
61–84% → **62–84%** — but it survives as a measurement rather than as luck.

## 3. What the corpora show

### 3.1 A small shared spine, and one corpus's invented tail

**Eight** entity kinds appear in all eight corpora: `dataset`, `hypothesis`,
`paper`, `plan`, `proposition`, `question`, `report`, `topic`. That is the
universal core — and it is much smaller than any single corpus's kind list, which
runs from 11 to 37.

Kinds unique to one corpus:

| corpus | unique kinds | records they carry |
|---|---|---|
| **mm30** | **10** — `audit`, `commentary`, `critique`, `decision`, `design`, `latent`, `mechanism`, `note`, `paper-synthesis`, `review` | 104 |
| cbioportal | 2 | 2 |
| cycles | 1 | 21 |
| protein-landscape | 1 | 7 |
| natural-systems | 1 | 3 |
| post-acute-infection | 1 | 3 |
| health/meta | 0 | 0 |
| evolution | 0 | 0 |

mm30 minted five times as many kinds as any other corpus, and several are
near-synonyms of each other and of spine kinds: `review`/`critique`/`commentary`,
and `plan`/`design`. Its unique kinds carry 3.8% of its records while occupying
27% of its kind list. That asymmetry is the signature of a system where minting a
kind was cheaper than finding the existing one — and the fact that two corpora
minted **nothing** shows it was a choice, not a necessity.

### 3.2 Agreement and exercise are different axes, and they come apart

For each field, two independent questions: do the corpora that use it **agree**
on its values, and does it **discriminate** within a corpus?

| field | corpora | agreement | discriminates in |
|---|---|---|---|
| `stance` | 5 | **identical**, 2 of 2 | **1 of 5** — collapsed at 90–94% `supports` elsewhere |
| `status` | 8 | **divergent**, 4 of 20 | **8 of 8** |
| `strength` | 4 | nested, 2 of 3 | 3 of 4 — only mm30 collapsed (97% `weak`) |
| `claim_layer` | 3 | nested, 2 of 4 | 3 of 3 |
| `identification_strength` | 4 | **divergent**, 2 of 6 | 4 of 4 |
| `independence` | 4 | nested, 2 of 3 | 3 of 4 — evolution adds `circular` |
| `evidence_type` | 5 | **divergent**, 1 of 4 | 4 of 5 |
| `evidence_role` | 4 | **divergent**, 2 of 5 | 2 of 4 |
| `source_class` | 6 | nested, 2 of 3 | 4 of 6 |
| `proxy_directness` | 3 | nested, 2 of 3 | 3 of 3 |
| `priority` | 2 | **divergent**, **0 of 6** | 2 of 2 |
| `mode` | 3 | **divergent**, 2 of 24 | 3 of 3 |
| `focus_type` | 2 | **divergent**, 7 of 30 | 2 of 2 |
| `scope` | 2 | identical, 1 of **1** | **0 of 2** |
| `provisional` | 2 | identical, 1 of **1** | **0 of 2** |
| `pre_registered` | 2 | identical, 1 of **1** | **0 of 2** |

The two columns disagree constantly, and each catches a failure the other misses.

**`priority` is the pure agreement failure**: two corpora, the same concept,
`high`/`medium`/`low` against `P1`/`P2`/`P3`, **zero** shared values, each corpus
entirely reasonable alone. `status`, `mode` and `focus_type` are the same failure
at larger scale — and `focus_type` shows it *inside* one corpus, natural-systems
carrying both `architectural` and `architecture` among its 17 values.

**`scope`, `provisional` and `pre_registered` are the pure exercise failure**:
perfect agreement across two corpora, on **one value each**, across 307–317
records. They are not vocabularies. They are constants costing a schema field, a
validator and a line in every record.

### 3.3 `verdict` is free text in a slot named like an enum

mm30's `verdict` carries **43 distinct values across 51 records**. Among them:
`decoupled__no_axis__gutierrez_cascade_refuted`,
`step_a_soft_pass_step_b_infeasible_close_with_collab_followup`, and — in a field
that gates whether a hypothesis stands — the literal string
`"<copy from summary.json:headline_verdict_myc_r_sv>"`, an **unfilled template
placeholder** that no check rejected.

This is the sharpest instance of the failure the kernel's §1 names: the stance is
written as prose and enforced as after-the-fact checks over a schema that permits
the violation. Here there was not even a schema to permit it.

A second instance, same corpus: `pmid`'s most common value is `[UNVERIFIED]`, on
19 of 119 records carrying the field. The kernel's §1 cites `fb-2026-07-28-002` —
a fabricated citation backing a `Strong / literature_evidence` finding for four
months. This is that hazard with a count attached.

### 3.4 Two rulings corroborated, one cost revised upward

**Independence is computed, not authored** — corroborated. Kernel §4.2.1 already
rules that *"an independence tag is an assertion about the world wearing the
costume of metadata,"* and §7's closure derives it from dataset lineage. The
corpora show exactly what an authored tag looks like: mm30 is 92% `shared-source`
while post-acute-infection is 87% `independent`, inverted defaults on the same
two-value vocabulary. A fourth corpus, evolution, invents a third value
(`circular`) that no design anticipated. The kernel's own vocabulary is wider
still — its `not-certified` state, *"a computed state, never authored,"* has no
counterpart in any corpus, which is the collapse §4.2.1 was written to prevent.

**Literature cannot enter belief by type** — corroborated, and sharply.
post-acute-infection's evidence is **100% literature**, 95 of 95 evidence-lines,
and it carries no eligibility field at all. Under **G1** that corpus has *zero*
belief-eligible evidence. That is the guarantee working, and §6 requires it be
predicted in writing before item 11 runs, so an empty result reads as a correct
answer rather than a broken tool.

**Strength: the cost of unit weighting is larger than mm30 suggested — a
correction.** Belief policy §3.2 weights every directional eligible assessment at
1, and an earlier draft of this document offered mm30's 97%-`weak` `strength`
field as evidence that there had been nothing to weight by. That was an mm30
artifact. Three other corpora use `strength` and **discriminate** on it —
post-acute-infection 56% top value, cycles 55%, evolution 67% — and all three
carry a `strong` value that mm30 never used. So authors in most corpora *were*
drawing the distinction v1 declines to read.

This overturns no ruling. Belief policy is explicit that weighting by study
design or precision is **blocked on ρO3**, not deferred by preference, and
limitation 1 already states the cost plainly. What changes is its size: the cost
is not theoretical and not confined to a field nobody used. That belongs in the
record backing limitation 1, and it is the strongest available argument for
prioritizing ρO3's estimand typing.

### 3.5 The typed relation vocabulary was abandoned, and kept growing anyway

**Fifty-six** distinct link-bearing frontmatter fields exist across the eight
corpora; **three** appear in all of them — `related`, `datasets` and
`source_refs`. (These are the twice-corrected figures — see §2.1.)

| corpus | distinct link fields | via `related` | via every other field | `related` share |
|---|---|---|---|---|
| natural-systems | 28 | 6,664 | 1,248 | **84%** |
| protein-landscape | 22 | 1,435 | 496 | 74% |
| cycles | 14 | 2,562 | 958 | 73% |
| mm30 | 37 | 7,220 | 3,603 | 67% |
| cbioportal | 13 | 1,592 | 805 | 66% |
| post-acute-infection | 20 | 3,342 | 1,810 | 65% |
| health/meta | 5 | 1,450 | 897 | 62% |
| evolution | 18 | 1,466 | 913 | 62% |

One untyped catch-all carries **62–84%** of all links in every corpus without
exception. The two facts together are the finding: authors did not use the typed
relations — *and the projects went on minting more of them*. The measured tail
includes `focus_ref`, `focal`, `inquiry_target`, `plan_target`, `commits_to`,
`absorbs`, `resynthesized_into`, `inquiries_touched` and `orphan_ids`. Adding a
typed relation did not reduce use of `related`, and nothing measured whether
anyone adopted it.

### 3.6 Typed claims exist in three corpora, and one holds 91% of them

| corpus | propositions | with subject+predicate+object | distinct predicates | claim-bearing share |
|---|---|---|---|---|
| mm30 | 334 | **307** | 8 | 957/2,737 (35%) |
| cbioportal | 24 | 24 | **1** | 129/491 (26%) |
| protein-landscape | 6 | 6 | **1** | 85/460 (18%) |
| post-acute-infection | 45 | 0 | 0 | 204/729 (28%) |
| cycles | 13 | 0 | 0 | 54/539 (10%) |
| natural-systems | 5 | 0 | 0 | 275/1,059 (26%) |
| health/meta | 6 | 0 | 0 | 12/451 (3%) |
| evolution | 5 | 0 | 0 | 48/394 (12%) |

Of 337 structured propositions across all eight corpora, **307 are mm30's** — and
the two corpora that do carry the triple use exactly **one** predicate, `affects`,
which is also 73% of mm30's own 8-term vocabulary (224 of 307).

The claim-bearing share counts `proposition`, `evidence-line`, `hypothesis`,
`finding` and `interpretation` — deliberately over-inclusive, since most
interpretations carry no claim. Even at that ceiling, **65% to 97% of every
corpus is process narrative**.

This is the survey's most important result for the order of work, and it cuts
both ways. It is the strongest evidence yet that typed claims are the right
foundation — five corpora cannot answer *"do these two records say the same
thing?"* at all, so `same_as`, deduplication and aggregation are structurally
unavailable to them. It is *also* why the calculus cannot be validated against
mm30: mm30 is the corpus it was fitted to, and the second and third corpora
exercise one operator between them.

## 4. Ruling: admission by agreement and exercise

Domain-extension §2.2 rules *defer-and-promote* for facets entering `nodes`, and
§2.3 gives the promotion trigger for facets becoming nodes. Neither governs the
question this survey raises: **what earns a vocabulary field a place in the
`science` base profile, as against a domain pack or nothing at all.**

The rule, added to domain-extension §2 as **2.6**:

> **2.6 Cross-corpus agreement and demonstrated exercise are *necessary* for a
> base-profile vocabulary. They are never sufficient.** Across at least **two**
> corpora with **separately evolved histories** carrying at least 20 records each:
>
> - **(a) agreement** — the corpora's value sets must be **identical or nested**,
>   where nested means every pair is comparable by inclusion. A **divergent**
>   family, where two corpora each carry a term the other lacks, is refused: it is
>   two vocabularies sharing a name.
> - **(b) exercise** — at least **two** distinct values must occur across those
>   corpora, and every value the contract declares must occur in at least one. A
>   field carrying one value everywhere declares a distinction nobody drew; a
>   declared value occurring nowhere is dropped before admission.
> - **(c) a reader** — some rule, projection, invariant or computation in this
>   system must consume the field. This is the **final** test, and it is the one
>   that actually admits: (a) and (b) only establish that the field could be
>   carrying information, never that anything reads it.
>
> A field failing (a) is **out of the base profile**; it enters a domain pack only
> if a domain reader wants it, and otherwise waits. A field failing (b) is not
> admitted at all. A field passing both and failing (c) **waits**, named, until its
> reader exists.

**"Separately evolved," not "independent."** The first draft said *independent
corpora*, which the survey cannot supply and limitation 1 says so outright: all
eight share one author and one predecessor system. A rule whose own evidence
cannot satisfy it is not a rule. What the survey can attest, and what 2.6 now
requires, is that the corpora have **separately evolved histories** — the
vocabulary choices were made in separate project directories, at separate times,
with neither corpus's frontmatter copied from the other's. That is materially
weaker than independence: a shared habit still crosses it, which is exactly
limitation 1's warning. It is not vacuous, because it is what makes disagreement
informative — `priority`'s `high`/`medium`/`low` against `p1`/`p2`/`p3` is two
separately evolved answers to one question, and the same author produced both.
Agreement under this criterion is therefore weak evidence and **disagreement is
strong**, which is why (a) is stated as a refusal rather than an admission.

**Why (c) is the operative clause, not a formality.** `strength` passes agreement
and exercise: nested across four corpora, three of them discriminating, with a
`strong` value mm30 never used (§3.4). It still stays out of the base profile,
because belief policy v1 weights every assessment at 1 and nothing else reads it —
and weighting is blocked on **ρO3**, not on this ruling. Admitting it would put a
field in the base contract whose only function is to be carried. When ρO3 makes
precision computable, `strength` is a candidate again and (a) and (b) are already
measured for it.

**The two-corpus exercise floor, not a per-corpus one.** An earlier form of (b)
required two values *in each corpus*, which rejects `polarity`: cbioportal's 24
claims are all one polarity, and a corpus that happens to hold no negative claims
is not evidence that polarity is unreal. Taking exercise across the corpora still
refuses `scope`, `provisional` and `pre_registered`, which carry one value in
every corpus that has them.

### 4.1 The rule this replaced, and why the measurement forced it

The first draft of 2.6 admitted a field on **discrimination** — top value below
90% in at least two corpora. Drafted against three corpora, it looked sound.
Against eight it inverts:

- It **rejects `stance`**, which is `supports`/`disputes` identically across five
  corpora but runs 90–94% `supports` in four of them — the one vocabulary in the
  entire survey that never drifted.
- It **admits `status`**, which discriminates in all eight corpora and shares
  **4 values of 20** — seventeen values in mm30, eleven in natural-systems, six
  in post-acute-infection, and a truncated prose sentence as a value in
  natural-systems' `entities/meta/0013-…-t462.md`.

Two mistakes, both instructive. **Rarity is not uninformativeness**: a disputing
evidence line is rare precisely because it is consequential, and a signed balance
reads the minority class. **Variety is not agreement**: a field can vary
beautifully in every corpus and still mean something different in each.

The replacement separates the axes and is checked against the same eight corpora:

| field | (a) agreement | (b) exercise | (c) reader | outcome |
|---|---|---|---|---|
| `stance` | identical | ✓ | eligibility, aggregation | **base profile** |
| `claim_layer` | nested | ✓ | claim identity | **base profile** |
| `polarity` | nested | ✓ | claim identity | **base profile** |
| `strength` | nested | ✓ | **none** — blocked on ρO3 | **waits** |
| `proxy_directness` | nested | ✓ | none | **waits** |
| `evidence_type` | **divergent** | ✓ | G1 reads *kind*, not this | out of base |
| `identification_strength` | **divergent** | ✓ | none | out of base |
| `evidence_role` | **divergent** | ✓ | none | out of base |
| `status`, `priority`, `mode`, `focus_type` | **divergent** | ✓ | none | out of base |
| `scope`, `provisional`, `pre_registered` | identical | **✗** one value | none | **refused** |

**"Out of base" is not "into a domain pack."** Every divergent row above has no
reader either, and a domain contract is not free: it costs ownership, succession
and a schema (§3 of the domain-extension design). Divergence establishes exactly
one thing — the field cannot be in the base profile. Routing it automatically to
a domain would replace a base-profile vocabulary nobody reads with a domain
vocabulary nobody reads, and would do it while charging for a contract. A
divergent field enters a domain **when a domain reader wants it**, and until then
it waits, in the same state as `strength`. (c) is the admitting clause at every
level, not just the base.

None of this was reachable from three corpora, and two rows moved again when the
nestedness defect was fixed (§2.1). The general lesson outlives the rule: **a
threshold tuned on the corpora that suggested it will pass on those corpora**, and
**an instrument trusted because it produced the expected answer is not evidence**.

### 4.2 What the rule does not claim

**It is weaker than "this field is meaningful."** Even all three clauses are a
floor. Two corpora can agree on a vocabulary, exercise it, have a reader, and both
use it wrongly; `independence` (§3.4) is very likely exactly that, which is why
the kernel computes it rather than reading it.

**Its unit is the corpus, not the record count.** Two corpora at 20 records beat
one corpus at 2,000, because the failure guarded against is a project inventing
its own term — and that failure is invisible inside any single project.

**It is a review rule, not a guarantee** (§7).

**Admission is a check on a state, not a permanent verdict.** No field was added
in order to be constant or to mean two things, so `evidence_role`'s divergence
and mm30's 97%-`weak` `strength` are states that arose after admission — whether
gradually or from the first record, this survey cannot say, since it measures one
snapshot and not a history. Either way the state must be re-measured rather than
assumed, and a field found divergent or collapsed reports either that its
distinctions were never real or that authorship stopped making them. Both deserve
an answer rather than a default.

## 5. Consequences for banked designs

Recorded here, amended in place where they belong. None reopens a ruling.

1. **Domain-extension §2** gains **2.6** (vocabulary admission) and **2.7** (the
   single navigation-only edge, §9.1).
2. **The ledger's §3** gains item 11 (§6).
3. **The disposition record's §2.3 figures** stand as recorded, under the bound
   its own limitations 2 and 3 already place on them. What §3.6 adds is *why*
   that bound is tighter than it reads: mm30 is not merely one domain, it holds
   **91%** of all structured propositions in eight corpora, and the two others
   that have any use a single operator. The measurement cannot be widened by
   finding a second corpus — a second corpus must be **given** a vocabulary
   first. Item 11 is that work.
4. **Belief policy limitation 1** is corroborated at a larger cost than the
   record carries (§3.4): three corpora discriminate on `strength`. This changes
   no ruling and is the strongest available argument for prioritizing **ρO3**.
5. **Relation-signature work** is ruled rather than merely constrained: §9.1 and
   domain-extension **2.7**. A typed relation nobody adopts is worse than absent,
   because it competes with `related` while claiming coverage, so relations are
   added one reader at a time and everything else is `see-also`.

## 6. Item 11 — the multi-corpus typing exercise

**Scope.** Compile a claim vocabulary for each of three corpora, then run
`build_claim` over every proposition in all three, and report what types, what
does not, and why.

**Which three, and why.** **mm30** (307 structured propositions, 8 predicates) as
the confirmation case. **post-acute-infection** (45 propositions, no predicates,
100% literature evidence) and **natural-systems** (5 propositions, no predicates,
26% claim-bearing) as the tests. cbioportal and protein-landscape are held in
reserve: they have the triple but one operator each, so they measure the
projection without testing the grammar.

**Predicted results, recorded before the run**, on the discipline that froze cut
1 prospectively — a prediction recorded afterwards is a redefinition:

- **mm30** — most propositions type. The 6-of-16 expressiveness figure, the
  6-of-27 reproduction yield and the 11 undetermined records become measured
  rather than hand-computed. The adjustment/covariate-set grammar gap is expected
  to dominate the failures; open question 4's adjudication is what bounds the
  figure between 6/16 and 9/16 today.
- **post-acute-infection** — propositions type only after a predicate vocabulary
  is authored, since none is recorded. Belief output is expected to be **empty**
  by G1 (§3.4), and an empty result there is a **pass**.
- **natural-systems** — 5 propositions is too few to measure expressiveness. The
  expected finding is a constraint on the base profile rather than a defect in
  the corpus: at 26% claim-bearing and 83% of links untyped, it must be able to
  conform **without** a claim calculus.

**Admission pass.** Every candidate vocabulary field the exercise surfaces is run
against 2.6 — agreement and exercise against all eight corpora, not the three
being typed, since §4.1 is what happens when a rule is checked only against the
data that suggested it, and then the reader clause, which is the one that admits.
Satisfying it means **naming** the check that consumes the field and exhibiting a
value perturbation that flips that check's verdict (§7) — not showing that the
field's removal breaks something. A field that types beautifully and is read by
nothing waits, whether the destination proposed for it is the base profile or a
domain pack.

**What item 11 must *not* do.** It must not mint a relation kind for anything it
finds. §9.1 rules one navigation-only edge, and a typing exercise is exactly the
context in which a plausible-sounding relation gets invented for a single record.

**Stop rule, inherited unchanged from the disposition record's §5.5.** No belief
computed, no persistence boundary crossed. A typing that would require either is
recorded as *blocked on A6–A8*, not worked around.

## 7. Guarantees

**This design mints no guarantee table, and the omission is the point.** Every
measurement above is over corpora that live outside this repository, are not
vendored into it, and change under their own authors. A conformance oracle built
on them would fail for reasons having nothing to do with this system, and N2's
requirement — that every oracle row can be made to fail by a source mutation —
cannot be met by an assertion about someone else's tree.

Ruling 2.6 is therefore a **review rule**: it binds the authors of the base
contract and is checked when a contract change is reviewed, not when the suite
runs. That is a real weakening, stated rather than disguised.

One testable consequence exists today and one is owed; both belong to 5b's
contract cut rather than here.

**2.6(a) and (b) can become an oracle** given a **frozen** survey artifact —
dated, reviewed and committed the way M10's parity fixture is — against which a
check asserts that every vocabulary the base contract declares is recorded as
agreeing and exercised. That costs carrying a survey snapshot, and is worth doing
when the base contract has enough vocabulary to guard; not for `stance`,
`claim_layer` and `polarity` alone.

**2.6(c) is a property of this tree and can become an oracle — but not the obvious
one.** The obvious oracle is *remove the field from the base contract and require
some test to fail*, and it is **insufficient**. Three ways it passes with no reader
in existence:

- **schema completeness** — a round-trip or schema test enumerates every declared
  field, so deleting any field breaks it whether or not anything reads the value;
- **fixture coverage** — a golden fixture contains the field, so removal breaks
  byte equality for the same reason;
- **contract identity** — the contract's own digest is pinned, so *any* edit to
  the contract fails a test by construction.

All three fail on **declaration**, and a reader consumes a **value**. N2's actual
requirement is sharper than "something fails": every oracle row must name the
check it is a row of, and that check's *result, identity or refusal* must change
under a source mutation. Applied here, admission under (c) owes a **named**
check `C_F` for each declared field `F`, together with a fixture perturbation that
changes `F`'s **value** and flips `C_F`'s verdict — a different belief, a different
claim identity, or a refusal where there was none. `stance` has such a check
(eligibility, then the signed balance); `claim_layer` and `polarity` have one
(claim identity); `strength` has none, which is the whole reason it waits. A field
that survives value perturbation with every check's verdict unchanged is carried,
not read, whatever the schema says.

That check is owed by 5b's contract cut, and it is a stronger row than 2.6(a) and
(b) because it needs no corpus and no snapshot.

**§9.1's oracle is owed, not available.** `see-also` has no implementation in this
tree yet, so *no epistemic effect* cannot be sabotaged today — there is nothing to
sabotage. When the edge surface lands, it lands with two rows: give `see-also` a
belief-moving path and assert refusal, and assert that no `see-also` edge appears
in a G3 closure. Recording the rule now and the oracle later is the ordinary case;
recording it as "testable today" was wrong.

## 8. Limitations

1. **Eight corpora are not a sample.** They share one author and one predecessor
   system, so agreement among them is weaker evidence than it looks — a shared
   habit is not a shared truth. Disagreement is the stronger signal, which is why
   §3 leans on it, and why 2.6's criterion is **separately evolved histories**
   rather than independence (§4): a rule requiring independent corpora could not
   be satisfied by the corpora that produced it. Roughly seven smaller corpora
   remain unmeasured; all are below 400 records, and the instrument runs over them
   in minutes.
2. **The instrument reads frontmatter only.** Prose bodies, sidecar files and
   `science.yaml` configuration are outside it. A vocabulary enforced in prose
   and never written to frontmatter is invisible here.
3. **Agreement and exercise are not meaningfulness** (§4.2), and 2.6 will be
   read as a quality bar it is not.
4. **The 20-record floor and the two-corpus minimum are chosen, not derived.**
   §4.1 shows what a badly chosen threshold costs, and nothing guarantees these
   two are better — only that they were checked against data they were not drawn
   from.
5. **Nested is treated as agreement, and that is a judgment.** When one corpus's
   values are a subset of another's, the field passes (a). That could equally be
   read as the smaller corpus not having met the distinction yet, or as the larger
   one having invented terms alone. `predicate` is the sharp case: nested only
   because the two corpora beside mm30 use a single operator, `affects`, which is
   a subset of mm30's eight by having barely any content at all.
6. **Nothing here measures whether authors understood a vocabulary.** A field can
   agree, be exercised, and have a reader, while two authors mean different things
   by it.
7. **A snapshot cannot see a rule's own effect.** 2.6 and 2.7 will change what
   future corpora contain, so re-running this instrument later measures a
   population the rulings shaped. That is not a reason to skip re-running it, but
   agreement observed after the fact is weaker evidence than agreement observed
   here.
8. **The link measurement is a shape rule plus a hand-maintained exclusion list.**
   It counts a whole value matching `<kind>:<id>`, minus URI schemes, identifier
   authorities, digest algorithms, and nine field names that name or display a
   record. Both lists are judgments, and a corpus using an unlisted identity field
   or an unlisted authority prefix would still be counted. §2.1 is the record of
   what two rounds of getting this wrong cost — the direction of the error was
   over-counting both times, so **56 is an upper bound** on the relation-field
   tally and §3.5's argument only gets stronger if it falls again.

## 9. Two rulings, and what stays open

Both questions this survey raised were **decided in session on 2026-08-07**, and
neither answer is "a better taxonomy."

**9.1 `related` is not replaced. It is narrowed to one navigation-only edge.**
Nothing replaces it with a second relation taxonomy — that is what produced 56
link fields and 3 universal ones. There is **one** explicitly navigation-only
edge, named **`see-also`**, carrying no inference, no closure traversal, no
symmetry, and **no epistemic effect**. It cannot move belief, cannot enlarge or
contract an independent set, and cannot participate in a G3 closure. Precise
relations are added **only** when a reader or an invariant uses them — the same
consumer test as 2.6(c), applied to edges.

The clause is a **rule without an oracle until the edge surface exists** (§7).
Nothing in this tree implements `see-also`, so *no epistemic effect* cannot be
sabotaged yet; the two rows are owed by whichever cut lands the surface.

The attributed source→claim connection is **not** a new primitive. It is the
existing **`source-assertion`** record projected as an edge: it already carries
the source, the anchored span, the stance, and the claim identity, and G1 already
rules that it cannot enter belief aggregation by type. Minting an edge kind beside
it would duplicate a record that exists and re-open the firewall G1 closes.

**9.2 The base profile requires claim *capability*, never claim *instances*.**
The base contract still owns the claim grammar and the kernel tag bytes. A corpus
with **zero claims and zero activated operator contracts is conforming** — and
this needs no profile variant and no activation flag, which are two mechanisms for
a state that is simply the empty one. What the profile requires is that **if a
claim exists, it must type**; a proposition that will not type is typing work, not
a licensed exception.

This is what makes §6's post-acute-infection prediction a *pass* rather than a
special case: an empty belief output is the correct result for a corpus with no
belief-eligible evidence, and an empty claim set is the correct result for a
corpus that has authored no claims.

**Still open:**

- **What happens to a base-profile vocabulary that later diverges or collapses?**
  §4.2 says it is a finding; it does not say whether the field is retired,
  demoted to a domain pack, or kept with the finding recorded. Retirement
  interacts with the tombstone rules in domain-extension §12's bound, since
  historical claims are typed against retired declarations.
- **Is `affects` a vocabulary or a default?** It is 73% of mm30's predicates and
  the *only* predicate in the two other corpora that have any. A single operator
  carrying nearly every claim is the same shape as `related` carrying nearly
  every link (§3.5), and it may have the same cause.
