# A health contract: estimands beyond myeloma's stages and a disease vocabulary — brief

Scope pass, 2026-10-29. Frames sci-036920 (idea, filed as finding F9 of the
second-project milestone record) for the decisions that remain before it can be
scoped.

## Problem

The health program's first real question cannot be represented today. The milestone
asked its one health question as a myeloma-typed sub-claim because the only
estimand-bearing operator in the world is mm30's, whose levels are myeloma's stages,
and no disease vocabulary is bound. The half that makes it a health question (does the
PRC2 coupling generalise beyond myeloma) is unrepresentable. A health program needs a
contract whose estimands are its own (tissue levels, a TPM measure) and a disease
vocabulary that lets a claim say what disease it is about.

## Current behaviour and evidence

- The milestone (sci-0d00d2, done 2026-10-27) chose option 1 of its design §4.1: the
  literal sub-claim `concept:disease-stage affects protein:EZH2` under mm30's operator,
  labelled a narrower sub-claim. Option 3, a `health` corpus-local contract with tissue
  levels, a TPM measure and a GTEx-anchored co-expression claim
  (`protein:PHF19 associates-with protein:EZH2`), was named the right shape and rejected
  for the milestone only because it is contract design and vocabulary holding, outside
  a measurement of the project surface. See
  `docs/specs/2026-10-26-second-project-milestone-design.md` §4.1 and §8.
- The record, `docs/records/2026-10-26-second-project-milestone.md` §5 F9 and §7,
  files the need as this idea and adds that the declared cohort is the mm program's
  (mm-a32d58) to hold or supersede under its own protocol.
- Projects design §6.3 (`docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md`):
  until a disease vocabulary is bound, health and cancer views lean on `closure` from
  anchor datasets and on `kinds`, which is coarse and honest. Binding a disease
  vocabulary is the biology pack's measurement to take when a project needs it; the
  projects design does not request it.
- In beliefs, the biology pack binds one namespace (HGNC) and its design lists GO, HP,
  EFO and MONDO as unmeasured limitations
  (`beliefs:docs/designs/2026-09-08-biology-pack-design.md` §9 item 1). The admission
  ramp's frozen run observed a `mondo` record held in full
  (`beliefs:docs/designs/2026-08-09-admission-ramp-design.md` §5.1), so the ontology
  is already a held dataset; what is missing is the pack's binding and its measurement.
- mm30's contract is corpus-local: its sort vocabularies (`stage-level`, `measure`,
  `identification`) are written as lists whose dataset addresses the contract binds
  (`beliefs:docs/superpowers/specs/2026-09-05-mm30-reproduction-design.md` §1c). A
  health contract would follow the same shape with its own lists.
- Projects design §9.3: after the milestone, the remaining health and cancer programs
  are recreated one question at a time; which comes first is the person's priority.
  sci-861d8f (briefed 2026-10-24, waits on sci-1fd5e5) offers breast cancer as another
  candidate, and its brief (`docs/notes/2026-10-24-exposure-reservation-reuse-brief.md`)
  defers the next program slot to the user after health's milestone, which has now
  landed.

## Constraints

- Science keeps no record storage: a contract and a vocabulary binding are beliefs
  artifacts (a corpus-local contract compiled by `adopt`; a biology pack binding). The
  science side is the project views and the first question.
- The §6.2 term-clause rule is under a proposed amendment (sci-538142, F7): under the
  prescribed rule the contract's vocabulary is the project boundary, so a health
  contract's term clauses decide what `health` selects. The amendment is the user's
  call and interacts with this design.
- The declared cohort (Zenodo 22399365) belongs to the mm program's protocol; a health
  question over GTEx needs its own holding route, which no science command supplies
  today (sci-20aee0: no command declares a dataset without holding it; sci-326015: no
  command creates a corpus).
- Open milestone follow-ups that shape any new question: sci-c5872f (closure clauses
  never select their anchor), sci-2a3f0a (only a project can be published),
  sci-8e2cd7 (no command renders a view's selection).

## Alternatives

1. **Build the health contract now** (option 3 in full): a `health` corpus-local
   contract with tissue levels and a TPM measure, a MONDO (or EFO) binding measured
   by the biology pack, and the GTEx co-expression claim as the first question. Two
   beliefs pieces and one science piece; the largest option, and the only one that
   makes a cross-disease question representable.
2. **An interim contract without a vocabulary**: a health contract with its own
   estimands, disease still distinguished by `closure` and `kinds` as §6.3 allows. It
   lets the tissue question be asked but leaves "beyond myeloma" unrepresentable, so
   the health view stays coarse.
3. **Defer until the next program is chosen** (current lean): the disease vocabulary
   is shared infrastructure for health, cancer and a breast-cancer program alike, so
   its binding is justified by whichever program comes next, and the contract's
   estimands depend on that program's first question. A bounded research task sizes
   the beliefs-side cost now so the user's choice of program is informed.

## Unanswered questions

- Which program is next after the milestone: health (post-acute infection, the
  predecessor's largest health program), cancer mechanisms, or the breast-cancer
  candidate (sci-861d8f)? The user; projects design §9.3 leaves it to them.
- Does the first health question stay option 3's GTEx co-expression claim, or does the
  chosen program bring a different first question? The user, once the program is chosen.
- Can a corpus-local contract declare tissue levels and a TPM measure as its estimand,
  and what does a MONDO or EFO binding cost in the biology pack? Research: sci-ad7335
  (filed by this pass; see Proposed decomposition).
- Where would a GTEx-anchored dataset be held: under a new workspace project like the
  mm program, or by a science command once sci-20aee0 lands? Follows from the program
  choice and sci-20aee0's outcome.
- Does the term-clause amendment (sci-538142) land before the health contract is
  designed? Its ruling decides what a health contract's vocabulary selects.

## Proposed decomposition

- Goal: sci-c4d587 "Health program: the first real question and its contract"
  (todo, P2, source this brief). Children:
  - sci-036920 (this idea; stays `briefed` until the research below and the user's
    program choice).
  - sci-ad7335 (research): what a health contract needs from beliefs, the estimand
    shape and the disease-vocabulary admission route. Wakes sci-036920.
- Not filed: a design task. One sizing question does not need a design task; a
  `Design the health contract from the brief` task is filed only after the user
  chooses the program and the research reports.
