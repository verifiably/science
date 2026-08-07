# The multi-corpus typing exercise — measurement

**Date:** 2026-08-07
**Status:** Run 2026-08-07. Ledger item 11, discharged. The commit carries the
instrument (`python/tools/type_corpus_claims.py`), four authored claim
vocabularies (`python/tools/vocabularies/`), and its regression suite
(`python/tests/test_typing_exercise.py`, 20 tests).
**Scope:** the first measurement of the claim calculus against corpora it was
not fitted to. Reports four runs, checks three predictions recorded before the
run, rules one vocabulary admission, and **corrects one over-claim in the
ledger's own description of this item**. Mints no guarantee table — §7 says why.

## 1. What was run

Ledger item 11, and the obligation is older than the ledger. The review
disposition record's §2.1 scope rule bound its own hand-typed figures:

> The vertical slice must **replace judgment with an executable constructor**
> before any coverage number here is treated as a property of the system rather
> than of the exercise.

Cut 1 built that constructor. This is the run.

Four runs, each `build_claim` over every `kind: proposition` record in a corpus,
against a claim vocabulary authored for it:

    uv run python tools/type_corpus_claims.py tools/vocabularies/<plan>.yaml <corpus-dir>

| plan | corpus | propositions | typed |
|---|---|---|---|
| `mm30-unsorted` | mm30 | 334 | **307** |
| `mm30-modal-sorted` | mm30 | 334 | **282** |
| `post-acute-infection` | post-acute-infection | 45 | **0** |
| `natural-systems` | natural-systems | 5 | **0** |

The corpora live outside this repository and are not vendored into it, so
nothing here runs in CI and nothing here is a conformance oracle (§7).

## 2. What is fitted, and what is tested

**A contract authored from a corpus types that corpus by construction.** A
number produced that way measures the author. This section is what separates the
result from that failure, and it is the section to attack first.

**Fitted, and therefore not evidence.** Operator names, `sign_apt` flags and
admitted layer sets are read off mm30's own `predicate`, `polarity` and
`claim_layer` fields. No record can refuse on any of them. Arity is fitted
twice over: a subject/predicate/object corpus has only arity 2 to offer.

**Fitted upstream, which is worse and was missed on the first pass.** The
predecessor system *enforces* the polarity/predicate partition on construction,
in a corpus check, and by auto-writing the sign-less value (§3.4). A violating
record could never have reached disk, so measuring the partition measures a
validator. An earlier draft listed it below as tested; it is listed here instead.

**Tested, because the corpus had no say in it.**

1. **Sorts.** `ArgSort(op) : Fin(arity(op)) → Sort` is one sort per slot. mm30's
   terms carry a `<kind>:` prefix, but nothing in the corpus constrains which
   kinds an operator may relate — `affects` is written across **all four**
   combinations of its two. §3.2 is what that costs.
2. **The layer vocabulary.** A domain *selects* from the base contract's four
   layers and may not extend them (§7.1). A `claim_layer` value with no base
   counterpart has nowhere to go, and no contract edit reachable from a domain
   gives it one. §5.2.
3. **Whether a claim was recorded at all.** A constructor reads front matter. §4
   is where that parts company with a reader holding the same records.
4. **Whether a qualifier is ever recorded.** §6.4's restriction apparatus is
   reachable by no corpus, and nothing in the plans could make it so. §3.5.

**Two sortings, both reported.** `mm30-unsorted` declares one sort covering every
term, making the sort discipline vacuous, and measures whether the rest of the
calculus fits. `mm30-modal-sorted` gives each operator the per-slot sorts it most
often relates — a rule computed from the data and **stated before the run**, so
it cannot be tuned operator-by-operator until the yield improves. The gap between
the two is the measurement; either alone hides the other.

**A plan never defaults.** A corpus value the plan cannot map is reported as an
unmapped value against its field, never coerced. *The vocabulary is incomplete*
and *the calculus refused* are the two findings a typing exercise must never
merge, and a default converts the first into the second's absence. The suite
tests exactly this separation.

## 3. Results

### 3.1 mm30 — every structured proposition types

**307 of 307**, under the unsorted plan. The remaining 27 records carry no
subject, predicate or object; they are §4's subject.

| operator | typed |
|---|---|
| `affects` | 224 |
| `associates-with` | 50 |
| `induces-state` | 12 |
| `regulates` | 9 |
| `is-proxy-for` | 5 |
| `part-of` | 4 |
| `subtype-of` | 2 |
| `binds` | 1 |

Read against §2 this figure is close to fitted, and the honest statement of what
it adds is narrow but real: **every structured mm30 proposition is flat-fragment
shaped** — arity 2, one operator, one layer, one polarity, no qualifiers. Nothing
in the structured population needs a grammar extension.

That is worth stating precisely, because it relocates every grammar gap the
disposition record found. Adjustment sets, magnitudes, superlatives, modality and
disjunction — the whole Γ column, 16 records — live **entirely** in the 27
records mm30 never structured. Closing every one of those gaps would type **zero**
additional structured records.

Two readings survive this measurement and it does not distinguish them: the
author structured only what fitted, or the schema's three fields could hold
nothing else. The consequence for the order of work is the same either way.

### 3.2 The sort discipline costs 25 records

**282 of 307** under the modal-sorted plan: **25 records refuse**, all
`ArgumentSortMismatch`, **8.1%** of the structured population.

| operator | refusals | what mm30 wrote |
|---|---|---|
| `affects` | 16 | a `protein:` term in a slot the modal rule made `concept` |
| `associates-with` | 4 | protein–protein pairs under a concept–concept declaration |
| `regulates` | 4 | a `concept:` object under a `protein` declaration |
| `part-of` | 1 | a `concept:` subject under a `protein` declaration |

This is the calculus meeting a corpus that recorded kind prefixes without ever
constraining which kinds an operator relates. It is the one number in the mm30
run the contract was not written to produce.

`binds` is the case that shows the modal rule's own limits. mm30 records protein
binding between two `concept:` terms — its single instance — so the modal rule
declares it `concept, concept` and the record types. The operator's meaning
objects; the measurement cannot, and a rule that could would be a reader's
judgment again.

### 3.3 post-acute-infection and natural-systems — zero, as predicted

**0 of 45** and **0 of 5**. Every record: `no-claim-recorded`.

post-acute-infection records the full epistemic apparatus of claims it never
wrote down structurally — `claim_layer`, `identification_strength`,
`proxy_directness` and `supports_scope` on **all 45** — with no subject,
predicate or object anywhere. **The labels are there and the claim is not.**

Those four fields are **claim-adjacent labels, not qualifiers** in §6.4's sense,
and an earlier draft called them qualifiers — which contradicted §3.5 two
sections later. A qualifier is a `d ↦ ⟨quantifier, restriction⟩` entry
restricting a claim along a declared dimension. None of these four is one, and
§3.5's finding that **no corpus records a qualifier** stands unqualified,
including for this corpus.

A vocabulary could have been extracted from the 45 titles and 18
`measurement_model` prose blocks. Doing so would be the extraction step kernel
limitation 3 names, performed by one reader with the answer in view — the exact
error §2.1 of the disposition record says this exercise exists to stop
committing. No operators were authored, and the zero is the finding.

natural-systems: 5 propositions, none with a predicate, and its three recorded
subject/object values are prose — `KPZ`, `guide morphism vocabulary`,
`idempotent dequantization` — carrying no `<kind>:` prefix to sort them by.

### 3.4 The polarity partition is a legacy constraint reproduced exactly

Across all 307 structured mm30 propositions, **polarity values partition exactly
by predicate**. No predicate carries both `not_applicable` and a signed value:

    affects, associates-with, regulates      positive / negative / unsigned   283 records
    induces-state, is-proxy-for, subtype-of,
    part-of, binds                           not_applicable                    24 records

**This is not evidence, and an earlier draft of this section claimed it was.**
That draft called the partition a property the corpus respected *"with zero
exceptions"* in a distinction *"nobody arranged."* It was arranged. The
predecessor system enforces exactly this partition in three places:

- `science_model.propositions.PropositionEntity` validates it on construction —
  a sign-meaningful predicate **must** carry `positive`/`negative`/`unsigned`, a
  sign-less one **must** carry `not_applicable`;
- `science_tool.validate.checks.propositions` repeats it as a corpus check, at
  ERROR;
- `science_tool.annotation.synthesize` **auto-writes** `not_applicable` when a
  sign-less predicate's polarity is omitted.

And `SIGN_MEANINGFUL_PREDICATES` is `{affects, regulates, associates_with}` —
the same three, named in the predecessor's source.

So mm30 **could not have contained a counterexample**: a violating record fails
validation before it reaches disk. The zero-exception count measures the
validator, not the authors, and reporting it as corroboration would be the survey
§4.1 failure — a rule checked against the data that produced it — committed one
level down. What the measurement actually shows is that §7.5's `unsigned`/`inapt`
split **reproduces a distinction the predecessor already drew**, which is a
reason to think the distinction is workable and no evidence at all that it is
true. The `sign_apt` flags in the plan are fitted from it, and so is the
partition.

### 3.5 No corpus exercises a qualifier

Across all eight surveyed corpora, **no proposition records a qualifier of any
kind** — no population, no setting, no restriction. §6.4's flat fragment, the
quantifier set, `Dims(op)`, `RestrictionSort(op)` and the whole
`Qualifier`/restriction-sort apparatus have **zero authored instances anywhere**.

The four plans declare `dimensions: {}` for this reason. This is a measured
absence, not an omission in the plan files.

## 4. What this does *not* measure — and one ledger claim to withdraw

The ledger's item 11 says this exercise is *"what makes the 6-of-16
expressiveness figure and the 6-of-27 reproduction yield **measured** rather than
hand-computed."*

**It does not, and no constructor can.** That claim is withdrawn.

The 27 records those figures are computed over carry no subject, predicate or
object. They state their claim in a `title`. `build_claim` reads front matter, so
it reaches **0 of 27** — and the gap between 0 and 6 is not a disagreement about
the calculus. It is the extraction step: the distance between a span of prose and
the claim a reader takes from it. That is kernel limitation 3 and formal-model
limitation 3, it is unautomated, and this exercise does not close it.

So both hand-figures **stay hand-computed**, and both stay non-quotable on the
grounds the disposition record already gave — pending the §2.4 re-homing
adjudication and open question 4.

What this exercise measured instead is a **different population** with a
different denominator: the 307 structured records the hand-exercise never
touched. The two measurements do not overlap, and neither substitutes for the
other.

The ledger's error was not the figure but the arithmetic of coverage: it assumed
an executable constructor would reach the same records a reader did. §5.3 amends
it.

## 5. The admission pass

Every candidate field this exercise surfaced, run against domain-extension
**2.6** — agreement and exercise over all **eight** surveyed corpora, then the
reader clause, which is what actually admits. Corpus counts are corpora clearing
the survey's 20-occurrence floor, the same convention §3.2 of the survey uses.

| field | corpora | agreement | exercise | reader | disposition |
|---|---|---|---|---|---|
| `claim_layer` | 3 | nested, 2 of 4 | 3 of 3 | claim identity | **already admitted** |
| `polarity` | 2 | nested, 1 of 4 | 1 of 2 | claim identity | **already admitted** |
| `predicate` | 2 | nested, 1 of 8 | 1 of 2 | operator resolution | **not a base-profile question** — §5.1 |
| `identification_strength` | 4 | **divergent**, 2 of 6 | 4 of 4 | none | out of the base profile |
| `proxy_directness` | 3 | nested, 2 of 3 | 3 of 3 | none | **waits** |
| `supports_scope` | 2 | nested, 2 of 4 | 1 of 2 | none | **waits** |

**Two of these rows agree only because a corpus is too poor to disagree.**
`polarity` and `predicate` are nested because cbioportal's 24 claims carry one
value each — `positive` and `affects` — so the agreement is with a corpus that
drew no distinction at all. Survey limitation 5 names this exact shape, and
neither row's disposition rests on it: both are already settled on other grounds.

No relation kind was minted, and none was proposed. §2.7's single navigation-only
`see-also` edge stands untouched — a typing pass is exactly where a plausible
relation gets invented for one record, and none was.

### 5.1 `predicate` is not a base-profile admission question

It looks like the exercise's biggest vocabulary finding and it is not a finding
of this kind at all. **Operators are domain-issued without exception** (§7.1),
and the base contract may not issue one. So mm30's eight predicates are a domain
contract's business, admitted or not by whoever owns that domain. 2.6 governs
what enters the **base profile**, and an operator vocabulary never can.

### 5.2 `mechanistic_narrative` is not admitted as a base layer

The exercise's one genuine admission question, and it is a **value**, not a
field. `claim_layer` is already admitted; `mechanistic_narrative` is a fourth
value with no counterpart in the base contract's closed layer set
`[causal, structural, statistical, methodological]`.

It clears the clauses that would matter if 2.6 governed values: **13 records
across two corpora** with separately evolved histories — 8 in
post-acute-infection, 5 in mm30 — nested within `claim_layer`'s agreeing family,
and discriminating in both.

**Not admitted: no structured instance justifies it.** All 13 records carrying
it — 8 in post-acute-infection, 5 in mm30 — are **unstructured**. Not one has a
subject, predicate and object, so not one would become a typed claim if the layer
existed. A layer with no claim to admit is a declaration, and 2.6(c)'s reasoning
applies to a value as readily as to a field: what admits is a reader, and there
is nothing here to read.

**What it costs is smaller than an earlier draft of this section claimed, and
the correction matters.** That draft cited §7.4 **row 5** and said admitting the
value *"re-identifies every claim in every corpus."* **That is wrong.** Row 5
covers a **kernel tag's byte encoding changing** — an existing symbol's bytes
moving under it. Appending a *new* symbol to the layer list touches no existing
tag, so no `π_claim` position moves and **every existing claim identity is
unchanged**. The applicable row is **row 1**: the base contract's content
identity moves, and D6 puts that in `belief_input_digest`, so every derivation
consulting it re-derives. That is a real cost and a bounded one — beliefs are
re-derivable and known to be affected; claims do not fork. The refusal does not
rest on it.

**What the mm30 records add, and what they do not.** The 5 mm30 instances are
the only ones ever adjudicated, and every one was ruled **R**:

| record | disposition record verdict | destination |
|---|---|---|
| 0003 | R — Γ, K | re-home as a **decision** |
| 0007 | R — K | re-home as an **interpretation** |
| 0011 | R — A, K | re-home as a **verification result** |
| 0014 | R — Γ | grammar: modality |
| 0015 | R — A, Γ | decompose; grammar: modality |

Three are **K**, wrong epistemic kind — not claims at all. Two are blocked on
modality. That adjudication was made per record, months earlier, without
reference to this field, which is what makes it worth citing.

**It covers 5 of the 13, and the other 8 were never adjudicated.**
post-acute-infection's records are unstructured and nothing more is known about
them; reading them as *also* needing re-homing would be this exercise inferring a
verdict it did not reach. So the mm30 five are **suggestive of** what the value
marks, not a finding about all 13.

**The condition for revisiting is stated, so this is a ruling and not a
postponement:** a corpus records a **structured** proposition — subject,
predicate and object — whose `claim_layer` is `mechanistic_narrative`. None of
the 13 is one.

### 5.3 Amendments this measurement forces

- **Ledger item 11** — withdraw the claim that this exercise makes the 6-of-16
  and 6-of-27 figures measured (§4); record what it measured instead; mark the
  item discharged.
- **Survey design §6** — record the three predictions as checked, including the
  one confirmed for the wrong reason (§6.1).

## 6. The predictions, checked

Recorded in the survey design §6 **before** the run, on the discipline that froze
cut 1 prospectively.

**mm30 — "most propositions type."** Confirmed, 307 of 307 structured, and §2
says how much of that is fitted. The rest of the prediction — that the two
hand-figures become measured — is **withdrawn** (§4). The predicted dominant
failure mode, the adjustment/covariate-set grammar gap, did **not** appear: it
cannot, because it lives entirely in the unstructured 27 (§3.1).

**post-acute-infection — "belief output empty by G1, and empty is a pass."**
Empty confirmed; **the mechanism was not tested**, and the difference matters.

The prediction expected an empty belief output because the corpus's evidence is
100% literature with no eligibility field, so G1 would admit nothing. The
measured reason is upstream of that and stronger: there are **no claims at all**,
so the belief output is empty *a fortiori* and G1's eligibility gate was never
reached. No belief was computed here — the stop rule forbids it (§8) — so G1's
behaviour on this corpus remains **untested**, and the prediction is confirmed in
outcome while its mechanism stands unexamined.

**natural-systems — "a constraint on the base profile, not a defect in the
corpus."** Confirmed: 0 of 5, and the corpus must be able to conform without a
claim calculus. Survey §9.2 already ruled it — the base profile requires claim
**capability**, not claim **instances**, and zero claims with zero activated
operator contracts is conforming, with no profile variant and no activation flag.
This run is that ruling's **instance, not its evidence**; it was ruled before the
measurement and the measurement did not move it.

## 7. Guarantees

**No guarantee table, for the survey's reason (§7) and one of its own.** Every
figure above is over corpora outside this repository that change under their own
authors, so N2's requirement — that every oracle row can be made to fail by a
source mutation — cannot be met by an assertion about someone else's tree.

What *is* guarded is the part that decides an outcome.
`python/tests/test_typing_exercise.py` covers the classifier: that a record with
no triple reports `no-claim-recorded` and never a refusal, that an unmapped layer
reports as vocabulary work, that a sort mismatch reports as a refusal by the
calculus, that a signed polarity on a sign-inapt operator refuses, and that the
two mm30 plans differ **only** in their sorts — without which §3.2's gap stops
being attributable to sorting.

One row is load-bearing beyond regression: a tool that reported *"the vocabulary
is incomplete"* as *"the calculus refused"* would produce a coverage figure
indistinguishable from a real one, wrong in the direction that flatters the
design.

**The `mechanistic_narrative` row is not that, and an earlier draft said it
was.** It claimed a plan mapping the value onto `causal` would produce *"eight
more typed records."* It would produce **zero** — measured, by running both mm30
and post-acute-infection with the mapping added: 307 and 0, unchanged. Every
record carrying the value lacks a triple, and the triple is checked first, so
none reaches the layer lookup at all.

The row is kept as a **forward** guard, which is what it always was in substance.
Today the ruling and the mapping are indistinguishable in every count. If a
structured record carrying the value ever appears — §5.2's stated revisit
condition — a mapped plan would silently type it as `causal` instead of surfacing
it, and the one record that could reopen the ruling would be the one record the
instrument hid.

## 8. Limitations

1. **The mm30 contract is fitted and its 307 is close to a tautology.** §2 says
   which parts. The figures that survive the objection are the 25 sort refusals,
   the 27 and 45 and 5 unreachable records, and the qualifier absence — not the
   yield, and **not** the polarity partition, which review found to be enforced
   by the predecessor system and therefore unmeasurable here (§3.4).
2. **The modal sorting rule is arbitrary.** It is *computed* rather than chosen
   per operator, which is the only property claimed for it. A different rule
   gives a different 25, and `binds` (§3.2) shows the rule assigning a sort the
   operator's meaning contradicts.
3. **Two corpora contributed no typed claim, so the calculus was exercised
   against exactly one corpus.** This is item 11's stated purpose only half
   achieved: the exercise established that two corpora *cannot* exercise it, which
   is a real finding and is not the same as validating it against a second corpus.
   The disposition record's limitation 3 — figures bound to *"the mm30 authored
   set and for nothing else"* — is **not lifted**, and this measurement does not
   lift it.
4. **The vocabulary bindings are placeholders and were never read.** No surveyed
   corpus records a binding of any kind. Referent membership is **M4**, arrives
   with `decodeClaim`, and is not implemented — so every plan's binding is inert
   here. Nothing in these results is evidence that any term exists in any
   vocabulary. This is the disposition record's §2.1 protocol step 3 with the
   as-if moved into the artifact.
5. **Only the flat fragment was reachable to test**, because no corpus records a
   qualifier (§3.5). The qualifier half of §6.4 is untested by data and cannot be
   tested by data that does not exist.
6. **Prose was deliberately not read.** Titles and `measurement_model` blocks
   hold claims this exercise scores as absent. That is the intended discipline
   (§3.3) and it makes every yield here a **floor** on what the corpora say, not
   on what they record.
7. **The exercise is hand-run and is no oracle.** Same standing as the survey.
   A corpus edited tomorrow moves these numbers and nothing reports it.

## 9. What stays open

**Nothing new.** This measurement raised no question it did not also rule, and
the two it inherited are unchanged:

- **Open question 4** (adjustment sets default to the `analysis-spec` or to the
  claim) and the **§2.4 re-homing adjudication** still gate the 6-of-16 and
  6-of-27 figures. §4 removes this exercise from the list of things that could
  settle them.
- **ρO3** still gates `strength`, and this exercise surfaced no candidate that
  changes its standing.

The one thing it adds to the order of work is a **prerequisite, not a question**:
a second corpus exercising the calculus does not exist and cannot be measured
into existence. It has to be authored — which is what limitation 3 said, and what
the survey said when it ruled that the bound *"cannot be lifted by finding a
second corpus, because no second corpus has a claim vocabulary to measure."*
This run is the confirmation, with counts attached.
