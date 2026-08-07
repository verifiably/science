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

**One earlier reading is withdrawn.** A regex pass over the same corpora appeared
to show `evidence_type` written both as `literature` and as `"literature"` in
post-acute-infection, and that was reported as encoding drift inside one corpus.
It is not: YAML resolves both spellings to the same string, and the instrument
reports **no** encoding drift in any corpus. The regex was the defect, and
preserve/require/normalize gains no support from it.

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
| `identification_strength` | 4 | nested, 2 of 6 | 4 of 4 |
| `independence` | 4 | nested, 2 of 3 | 3 of 4 — evolution adds `circular` |
| `evidence_type` | 5 | nested, 1 of 4 | 4 of 5 |
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

Sixty-seven distinct link-bearing frontmatter fields exist across the eight
corpora; **five** appear in all of them.

| corpus | distinct link fields | via `related` | via every other field | `related` share |
|---|---|---|---|---|
| mm30 | 43 | 7,221 | 3,893 | 65% |
| natural-systems | 34 | 6,664 | 1,351 | **83%** |
| protein-landscape | 28 | 1,435 | 514 | 74% |
| cycles | 19 | 2,563 | 1,084 | 70% |
| post-acute-infection | 27 | 3,372 | 1,930 | 64% |
| cbioportal | 19 | 1,592 | 877 | 64% |
| health/meta | 8 | 1,453 | 906 | 62% |
| evolution | 22 | 1,473 | 944 | 61% |

One untyped catch-all carries **61–83%** of all links in every corpus without
exception. The two facts together are the finding: authors did not use the typed
relations — *and the projects went on minting more of them* (`focus_ref`,
`focal`, `derivation`, `rival_model_packet`, `identity_context`). Adding a typed
relation did not reduce use of `related`, and nothing measured whether anyone
adopted it.

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

> **2.6 A base-profile vocabulary is admitted on cross-corpus agreement and
> demonstrated exercise, never on plausibility.** Across at least **two**
> independent corpora carrying at least 20 records each:
>
> - **(a) agreement** — the corpora's value sets must be **identical or nested**.
>   A **divergent** pair, where each contributes a term the other lacks, is
>   refused: it is two vocabularies sharing a name.
> - **(b) exercise** — at least **two** of the declared values must actually
>   occur in each corpus. A value occurring in no corpus is dropped before
>   admission.
>
> A field failing (a) starts in a **domain pack** and is promoted only when
> corpora agree. A field failing (b) is not admitted at all: it declares a
> distinction nobody drew.

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
`stance` admitted, `status` and `priority` to domain packs, `scope`/`provisional`/
`pre_registered` refused outright, `strength` and `claim_layer` admitted. That is
the intended answer in every case, and none of it was reachable from three
corpora.

The general lesson, which outlives this rule: **a threshold tuned on the corpora
that suggested it will pass on those corpora.** The check that matters is the one
run against data the rule was not drawn from.

### 4.2 What the rule does not claim

**It is weaker than "this field is meaningful."** Agreement and exercise are
necessary, not sufficient. Two corpora can agree on a vocabulary and both use it
wrongly; `independence` (§3.4) is very likely exactly that.

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

1. **Domain-extension §2** gains ruling 2.6.
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
5. **Relation-signature work** inherits §3.5: a typed relation nobody adopts is
   worse than absent, because it competes with `related` while claiming coverage.
   Whatever admits a relation signature should answer the adoption question the
   way 2.6 answers the vocabulary question.

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
against 2.6 — against all eight corpora, not the three being typed, since §4.1 is
what happens when a rule is checked only against the data that suggested it.

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

One testable consequence exists, and it belongs to 5b's contract cut rather than
here: given a **frozen** survey artifact — dated, reviewed and committed the way
M10's parity fixture is — a check could assert that every vocabulary the base
contract declares is recorded in that artifact as agreeing and exercised across
two corpora. That converts 2.6 into an oracle at the cost of carrying a survey
snapshot. It is worth doing when the base contract has enough vocabulary to be
worth guarding; it is not worth it for `stance` and `claim_layer` alone.

## 8. Limitations

1. **Eight corpora are not a sample.** They share one author and one predecessor
   system, so agreement among them is weaker evidence than it looks — a shared
   habit is not a shared truth. Disagreement is the stronger signal, which is why
   §3 leans on it. Roughly seven smaller corpora remain unmeasured; all are below
   400 records, and the instrument runs over them in minutes.
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
   values are a subset of another's, this rule admits the field. It could equally
   be read as the smaller corpus not having encountered the distinction yet, or
   as the larger one having invented terms alone — `identification_strength`
   (2 shared of 6) is close to that line.
6. **Nothing here measures whether authors understood a vocabulary.** A field can
   agree and be exercised because two authors used it two different ways.

## 9. Open questions

- **What replaces `related`?** §3.5 shows one untyped edge carrying 61–83% of
  links in every corpus while typed relations went unadopted and kept
  multiplying. Whether the answer is fewer relation signatures, a different
  authoring affordance, or accepting an untyped edge as legitimate and typing it
  later is undecided. It should be settled before relation signatures are
  implemented.
- **Does the base profile require a claim at all?** §3.6 and §6's
  natural-systems prediction point at a base profile under which a corpus may be
  almost entirely process narrative and still conform. Whether that is a profile
  variant, a separate contract, or simply what "optional" already means is not
  ruled here.
- **What happens to a base-profile vocabulary that later diverges or collapses?**
  §4.2 says it is a finding; it does not say whether the field is retired,
  demoted to a domain pack, or kept with the finding recorded. Retirement
  interacts with the tombstone rules in domain-extension §12's bound, since
  historical claims are typed against retired declarations.
- **Is `affects` a vocabulary or a default?** It is 73% of mm30's predicates and
  the *only* predicate in the two other corpora that have any. A single operator
  carrying nearly every claim is the same shape as `related` carrying nearly
  every link (§3.5), and it may have the same cause.
