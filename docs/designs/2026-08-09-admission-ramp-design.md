# The admission ramp — design

**Date:** 2026-08-09
**Status:** **Specified 2026-08-09. Nothing has been run and nothing is ruled.**
Gate 1 (§5) is not started. **Every figure in this document is reconnaissance**
from throwaway shell and Python one-liners — in §2, §2.1 and §8 — is labelled as
such at each site, and is **superseded wholesale** by the frozen run at Gate 2.
No figure here is a measurement. §6 names the obligations
the ruling is expected to touch; it does not say what the ruling will be.
**Scope:** **will close F2 and conformance cut 1's open question 2 at Gate 2** —
how a corpus with zero content-addressed inputs reaches a usable admitted set —
narrowed to the part that survives the recreate-not-migrate ruling: **externally
sourced input**. Neither is closed by this document.

## 1. What this owes, and what was already cut away

The review disposition record (`2026-08-05-review-disposition-and-conformance-cut-1.md`)
accepted F2 and left the obligation unowned. Its finding column reads
*"content-addressability is empty on day one and no ramp is designed"*, and its
disposition:

> 0 of 259 mm30 datasets carry a content hash, so kernel §2.2's *held* predicate
> and the eligibility gate admit nothing. New obligation: **the admission ramp** —
> how a corpus goes from zero held inputs to a usable admitted set. No banked
> document owns it

The gate it names is kernel §2.2: an input is **held** when we can produce its
exact bytes on demand and identify them by content hash. `G2b` refuses an
assessment over an unheld or unhashed input, and eligibility (kernel §3) needs
the held inputs *and* the processing closure above them.

**Most of F2's evidence no longer carries weight.** F2 was argued from *0 of 259
mm30 datasets carry a content hash*. The predecessor's content is to be
re-authored under the redesigned system rather than migrated — the clean-start
ruling, `2026-08-03-redesign-adoption-ledger.md` §0 — and a corpus authored
correctly content-addresses what it writes. That figure measures the
predecessor.

**What survives is what cannot be re-authored.** Published datasets and
third-party reference resources are external, and no authoring discipline makes
them held. That is the remaining question, and it is what this design measures
and rules.

Papers are external too, and are nonetheless **not** part of it: computation
§4.7's run-input rule puts them on the other side of the boundary (§2, §7 item
3). F2 is a question about run inputs, and every run input is a held dataset.

## 2. The population, and its denominators

The measured corpus is the predecessor's shared store — a record root, and a
sibling payload root holding materialized bytes under the same relative layout.
**Both roots are required arguments to the instrument** (§4); no path on any
particular machine appears in the code or in this document.

**Dataset records only.** The store also holds 274 `paper` records, and they are
**out of scope for this measurement**, on a rule rather than on convenience:
computation §4.7 states that *"every input to a run is a **held dataset**"*, and
a computation whose input is not held is acquisition, never a run. An individual
paper is a `source`; a literature corpus, if one is built, is a `dataset` and
would be measured as one. A paper census therefore measures **W3 addressability**
— whether a record has an accepted external identifier at all — and can bear on
F2 not at all. §7 records it as a separate measurement rather than dropping the
observation.

It is chosen over the eight project corpora for one reason: it is the artifact
most likely to be carried forward rather than re-authored, so a measurement of
it is not heritage.

**Datasets — the denominator is stated in three parts, because the third part is
the hard one.**

| part | count *(reconnaissance)* |
|---|---|
| dataset records | **47** |
| …declaring resources in a data package | **34**, declaring **113** resources between them |
| …declaring **no** resources at all | **13** |

Every one of the 34 declares at least one resource; the 13 carry no data package
whatsoever. Reporting per-dataset rather than per-resource would hide partial
datasets — one record has 1 of its 4 resources present — and dropping the 13
would delete the hardest cases from the denominator. **Every access-restricted or
embargoed record in the corpus is among those 13**: the sole `controlled` record,
the sole `registration` record and both `embargoed` records declare no resources
at all. One of the 13 also has bytes materialized in the payload root while
declaring nothing, which is the mirror image of the failure this design exists to
name. A denominator of 34 would report the corpus as better characterized than it
is, by excluding precisely the records that characterize it worst.

**A DOI, a PMID and a PMCID are external authority identifiers.** They identify a
work; they do not retrieve that work's exact bytes. This document never treats
one as a byte locator, in either measurement.

### 2.1 The reconnaissance figures, and why they are not the measurement

Two throwaway readings of the same 113 resources disagreed on how many carry a
recorded hash — **85 against 90** — on regex block-scoping alone. Neither is
reported as fact. Reconciling that disagreement against a real parse is Gate 1's
first obligation, and the reconciliation is published rather than quietly
applied: the corpus survey found four instrument defects, three of them in
review, and each changed a reported number
(`2026-08-07-corpus-survey-and-vocabulary-admission-design.md` §2.1).

The rest of the reconnaissance, on the same footing: across both roots, **28** of
the 113 declared resources resolved to bytes; **27** of those carried a recorded
hash and **all 27 matched**, with **zero mismatches**; the remaining one had
bytes and no hash to check. **8** of the 34 data-packaged datasets had at least
one resource present.

The shape those numbers suggest — records rich in recorded hashes, thin in
retrievable bytes — is the motivation for this design. It is not evidence for its
ruling.

### 2.2 Two boundaries, and the basis boundary comes first

An earlier draft of §6 put the whole question at the holding layer. That was
wrong, and it mattered: a record can fail to be a world entity **before** the
question of whether its bytes are in hand is reachable.

The world address ruling's generalized basis rule
(`2026-08-08-world-address-ruling.md` §3) binds all eleven kinds: every
addressable entity carries the basis declared for its kind — intrinsic, or an
identifier from an accepted authority — and *"if that basis is missing, the
record is a project-scoped **curation note** — not a weakened world entity."*
`W3` is the refusal that enforces it, and it names both cases this measurement
meets: a `source` with no accepted external identifier, and **a `dataset`
holding no content**. Its new clause is what makes the ordering bite — a curation
note **cannot be the target of a semantic reference**, so an unbased record is
not merely weaker, it is unreachable.

So there are two boundaries, and they compose in one direction only:

| boundary | question | owner | outcome if it fails |
|---|---|---|---|
| **basis** | does the record have a content identity at all? | `W3` | curation note, unreferenceable — an explicit second act, never a coercion |
| **holding** | are the exact bytes obtainable and pinned? | `G2b`, `R5` | declared and unheld — a world entity, authorable, not belief-eligible |

**A dataset with a recorded content identity and unavailable bytes clears the
first and fails the second.** That is the state the ramp exists to name. **A
dataset with no content basis fails the first**, and no amount of retrieval
rescues it, because nothing pins what would be retrieved.

This is why the 13 cannot be dropped from the denominator: they are not a
smaller version of the 34's problem, they are a **different** problem, sitting at
the other boundary. Whether each of the 13 carries a content basis outside its
absent data package is a question for the run, not an assumption of this design.

## 3. What is observed: three independent axes

Byte availability and record integrity are different questions, and one resource
can be interesting on either axis alone. They are therefore reported as
**independent axes**, so that no combination is unrepresentable — in particular
*bytes obtained but never pinned by a recorded hash*, and *bytes present locally
that disagree with the record*.

| axis | values |
|---|---|
| **byte observation** | `local` · `retrieved` · `retrieval-failed` · `byte-locator-untested` · `no-byte-locator` |
| **hash result** | `match` · `mismatch` · `absent` · `unchecked` |
| **byte-count result** | `match` · `mismatch` · `absent` · `unchecked` |

**A byte locator is defined narrowly: a locator that retrieves that declared
resource's exact bytes.** A study landing page does not qualify. An accession
does not qualify. A DOI does not qualify. The definition is what makes
`no-byte-locator` an honest bucket rather than an empty one, and it is the single
place where a generous reading would flatter the result most.

**`mismatch` is never folded into `retrieval-failed`.** A retrieval that succeeds
and disagrees with the record is not a network problem — it is a successful
observation that contradicts the record, and the recorded digest is the only
thing standing between *held* and *believed to be held*. Against 27 of 27 local
matches, a mismatch would be the most informative single result the run can
produce, and it must not be reported as a failure to look.

`unchecked` and `absent` are likewise distinct: one is a question not asked, the
other an answer the record cannot give.

## 4. The instrument

`python/tools/survey_admission.py`, on the pattern of its two predecessors
(`2026-08-07-corpus-survey-and-vocabulary-admission-design.md` §2 and
`2026-08-07-multi-corpus-typing-exercise.md` §1): **run by hand, against roots
outside this repository, never in CI, minting no conformance oracle.** The record
root, the payload root and the scratch root are all required arguments.

Five properties are load-bearing.

1. **A real parse, not a pattern match.** The 85-against-90 disagreement in §2.1
   came from regex block-scoping. Data packages are parsed as YAML, and the
   parsed reading is what the document reports.
2. **Every parse failure is counted and named, never skipped.** Every share is a
   fraction of a stated denominator, and dropping an unreadable record shrinks
   the denominator silently.
3. **The frozen artifact holds every unit-level observation, in three
   collections plus a failure list.** One row per resource is not enough: the 13
   records declaring nothing would contribute no rows at all and vanish from the
   artifact — the same deletion §2 refuses in the denominator. The collections
   are:

   | collection | one row per | fields |
   |---|---|---|
   | **dataset records** | dataset record, all of them | data package `present` · `absent` · `unparseable`; declared-resource count; **payload files present under the record's payload directory that no declared resource claims** |
   | **declared resources** | declared resource | the three axes of §3 |
   | **parse failures** | unreadable file | path relative to its root, and the reason |

   Unmatched payload files are what make the mirror-image case visible: a record
   with **no data package and bytes on disk anyway** produces a dataset row with
   `absent`, a count of zero, and a non-empty unmatched list — while contributing
   nothing to the resource collection. That combination is a required test case
   (§4, tests).

   The human-readable report **renders from that artifact** rather than being
   computed alongside it, so the prose and the data cannot drift and every figure
   in the document is re-derivable from one file.
4. **Probing is opt-in, bounded on both sides, and destroys nothing.** Retrieval
   runs only behind an explicit flag. *Local side:* bytes are written to the
   scratch root, hashed, and the instrument's own temporary files are deleted —
   only its own; the scratch root **refuses either corpus root, and any
   descendant of either, as its location.** *Network side*, because scratch
   safety bounds none of it:

   - only **approved schemes** are fetched, and the approved set is `https` —
     anything else is `retrieval-failed` with the scheme named, never attempted;
   - **every redirect hop is revalidated** against the same rules, since the
     first URL's approval says nothing about where it lands;
   - destinations resolving to **loopback, link-local, private or otherwise
     non-public addresses are rejected** before any request is issued;
   - a **timeout** and a **maximum byte count** bound every fetch, and exceeding
     either is `retrieval-failed` with the bound named, never a truncated body
     silently hashed.
5. **Every probe outcome is stamped with the time it ran.** Retrievability varies
   over time. An undated probe result asserted as a standing property is the same
   error the coreference ruling refused when it kept edge state out of an
   immutable epoch (`2026-08-08-world-address-ruling.md` §5.5).

**What discarding the bytes does and does not buy.** It means the run **does not
materialize either corpus root**. It does not keep a resource from being held:
kernel §2.2 is explicit that data outside the repository is held if
content-addressed and retrievable, so location is not the discriminator. A
matching probe is time-stamped evidence of retrievability. **How long that
evidence supports admission is a question for the ruling**, not a property the
instrument may assume.

**Tests.** `python/tests/test_admission_survey.py`, constructing synthetic record,
payload and scratch roots under `tmp_path`, following the lighter fixture pattern
of the existing suites. Committed fixture files are used only where they
materially improve readability. Every axis value is exercised — including
`mismatch` on both the hash and byte-count axes, and bytes-without-a-recorded-hash
— because those are the arms the real corpus may never produce, and an
unexercised arm is an unmeasured one.

Three cases are required rather than optional, because each is a shape the real
corpus may hold and no axis value alone expresses:

- **no data package, and undeclared payload bytes present** — the dataset row
  reads `absent` with a zero count and a non-empty unmatched list, and the
  resource collection gains nothing;
- **an unparseable data package** — a dataset row reading `unparseable` *and* a
  parse-failure row, never a silent skip that shrinks the denominator;
- **a declared resource whose bytes are present and whose recorded hash is
  absent** — obtained and unpinned, distinct from both `match` and `mismatch`.

## 5. Two gates, and the condition that pauses between them

**Gate 1 — bank the instrument.** The instrument and its tests are committed and
passing, and every discrepancy between readings — the 85-against-90 among them —
is reconciled, with the reconciliation written into §2.1.

**Gate 1 permits exploratory runs against the real roots, and requires them.**
A disagreement between two readings of real data cannot be reconciled against
fixtures; only the corpus that produced it can settle it. What Gate 1 forbids is
not running the instrument but **publishing any figure from it as a
measurement**. Exploratory output is diagnostic, may be discarded, and is never
frozen.

**Gate 2 — one run, frozen, then rule.** A single authoritative run. The frozen
record carries the unit-level artifact, the counts rendered from it, the run
date, the instrument's commit, and the identity of both roots. **Root identities
and relative paths only — never a machine-specific absolute path**, in the
artifact or in this document. The normative section is written only afterwards,
downstream of figures already fixed.

**Root identity, for a root that is not a repository.** The record root may be
under version control; the payload root is not, and has no commit to name. Its
identity is therefore **a digest over the sorted relative-path observations the
run actually used** — each relative path with the size and content digest
observed for it — so that two runs over the same payload state carry the same
identity, a changed or added payload file changes it, and nothing about where the
root sits on any machine enters it. The same construction is applied to the
record root, so the two are named the same way and neither depends on version
control being present.

**The pause condition.** If the measured distribution overturns the state model
the ruling is expected to rest on, the normative section is **not** written and
the finding comes back for a decision first. This remains one document either
way; a second document would add ceremony, not evidence.

## 6. What the ruling is expected to touch — and what it must not assume

The direction settled before measurement, and recorded here so the measurement
cannot be read as having discovered it: **`held` is not weakened.** The ramp
names the gap instead — a dataset may be *declared*, carrying its **content
identity** without its bytes, and a declared input is authorable but never
belief-eligible. This is the move the coreference ruling made with
`indeterminate`: name the unestablished state rather than let it read as absence.

**`declared` presupposes a basis and never substitutes for one.** Per §2.2, `W3`
decides first. A record with no content identity is a curation note and is
already unreferenceable; calling it *declared* would re-admit through the ramp
exactly what the basis rule refuses, and would make `declared` the fallback basis
the ruling forbids deriving. So the ramp's new state is available **only** to a
record that has already cleared `W3` — which is why the ordering is fixed here,
before the measurement, and not left to be inferred from the distribution.

Three existing rows own this ground, in order, and the ruling is expected to
**amend rather than append**:

- **`W3`** — *creating a world entity without its basis is refused* — already
  names the `dataset` holding no content, and already routes it to an explicit
  curation note rather than a weakened entity. Nothing about `declared` changes
  that boundary; the ruling must confirm it is untouched.

- **`G2b`** — *an assessment requires held, content-hashed inputs* — is the
  refusal a declared input must run into.
- **`R5`** — *belief does not depend on artifact availability in this checkout* —
  already separates reach from holding, and its negative (a) already asserts that
  destroying the last held copy makes the input unheld and changes admission.

**No new guarantee row is committed to here.** A successor contract identity is
certain if `held` semantics change at all, since amending a row's meaning mints
one under the retained id (`2026-08-03-normative-contract-design.md` §4). A new
row is added only for a property that is **independently sabotage-able** — one an
implementation could break while leaving `G2b` and `R5` intact. Whether the ramp
has such a property is decided at Gate 2, not now, and the frozen row count moves
only if the answer is yes.

## 7. What this will not measure

1. **Closure completeness.** Most data-packaged datasets carry a recipe
   directory, which is a processing closure in all but name. Checking one against
   kernel §3.1's seven-part closure — spec hash, code, environment, parameters,
   held-input hashes, nondeterminism contract, output manifest — is a second
   measurement with its own instrument. Eligibility needs both; this design
   measures the input half only, and says so rather than implying the gate is
   closed.
2. **The eight project corpora.** Their external references are largely reachable
   through the commons, and measuring their records directly re-measures material
   the recreate-not-migrate ruling says will be re-authored.
3. **The paper census — a separate measurement, with no bearing on F2.** The 274
   `paper` records are a **W3 addressability** question: does a record carry an
   accepted external identifier, and is it therefore a `source` entity or a
   curation note? Reconnaissance finds **52** carrying one (all via `doi`, with
   `pmid` and `pmcid` appearing only alongside it) and **222** carrying only a
   bibliographic key — which would make the large majority curation notes,
   unreferenceable under §3 of the world address ruling. That is a real and
   probably uncomfortable finding, and it is **not this measurement's**:
   computation §4.7 makes every run input a held dataset, so no paper result can
   move F2 either way. It is named here so the observation is banked rather than
   lost, and so the instrument's schema is not bent to carry a population it
   should not report on.
4. **Whether an authority identifier resolves.** Presence is not resolution, in
   either measurement. Resolving DOIs measures registries, not this corpus.
5. **Anything about the successor's own corpora.** None exist yet. Every figure
   here describes the predecessor's shared store.

## 8. Open at the time of writing

1. **How long a probe's evidence of retrievability lasts.** A timestamp is
   recorded; what admission may do with a six-month-old successful probe is the
   ruling's to decide.
2. **Whether bytes-without-a-recorded-hash is its own admission state.** The
   resource is obtained and unpinned — nothing in the record says which bytes are
   the right ones, so possession alone does not make it held. **Frequency does not
   decide this**: a state exists because its semantics differ from every other
   state, not because the corpus happens to contain many of it. One instance and
   ten thousand argue equally. What the run contributes is whether the case is
   *reachable* in practice, not whether it is common.

**Closed rather than left open.** An earlier draft asked whether papers are
inputs at all. Computation §4.7 answers it: every input to a run is a held
dataset, an individual paper is a `source`, and a literature corpus would be a
`dataset` measured as one. The question was already ruled; §7 item 3 records what
follows for the paper census.
