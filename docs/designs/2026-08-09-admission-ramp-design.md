# The admission ramp — design

**Date:** 2026-08-09
**Status:** **Specified 2026-08-09. Nothing has been run and nothing is ruled.**
Gate 1 (§5) is not started. **Every figure in this document is reconnaissance**
from throwaway shell and Python one-liners — in §2, §2.1 and §8 — is labelled as
such at each site, and is **superseded wholesale** by the frozen run at Gate 2.
No figure here is a measurement. §6 names the obligations
the ruling is expected to touch; it does not say what the ruling will be.
**Scope:** closes F2 and conformance cut 1's open question 2 — how a corpus with
zero content-addressed inputs reaches a usable admitted set — narrowed to the
part that survives the recreate-not-migrate ruling: **externally sourced input**.

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

**What survives is what cannot be re-authored.** Published datasets, papers and
third-party reference resources are external. No authoring discipline makes them
held. That is the whole of the remaining question, and it is what this design
measures and rules.

## 2. The population, and its denominators

The measured corpus is the predecessor's shared store — a record root holding
`dataset` and `paper` records, and a sibling payload root holding materialized
bytes under the same relative layout. **Both roots are required arguments to the
instrument** (§4); no path on any particular machine appears in the code or in
this document.

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

**Papers — 274 records, measured for authority identifiers, not for bytes.** No
paper record declares a byte resource; each is a single document with front
matter. Reconnaissance finds **52** carrying an external authority identifier
(`doi`, with `pmid` and `pmcid` appearing only on records that also carry a
`doi`) and **222** carrying only a bibliographic key.

A DOI, a PMID and a PMCID are **external authority identifiers**. They identify a
work. They do not retrieve that work's exact bytes, and this document never
treats them as byte locators.

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
3. **The frozen artifact holds every unit-level observation**, one row per
   declared resource and per paper record, each carrying its three axis values,
   plus every parse failure. The human-readable report **renders from that
   artifact** rather than being computed alongside it, so the prose and the data
   cannot drift and every figure in the document is re-derivable from one file.
4. **Probing is opt-in and destroys nothing.** Retrieval runs only behind an
   explicit flag. Bytes are written to the scratch root, hashed, and the
   instrument's own temporary files are deleted — only its own. The scratch root
   **refuses either corpus root, and any descendant of either, as its location.**
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

## 5. Two gates, and the condition that pauses between them

**Gate 1 — bank the instrument.** The instrument and its tests are committed and
passing, and every discrepancy between readings is reconciled with the
reconciliation written into §2.1. No measured figure is published at this gate.

**Gate 2 — run, freeze, then rule.** One run. The frozen record carries the
unit-level artifact, the counts rendered from it, the run date, the instrument's
commit, and the identity of both roots. **Root identities and relative paths
only — never a machine-specific absolute path**, in the artifact or in this
document. The normative section is written only afterwards, downstream of figures
already fixed.

**The pause condition.** If the measured distribution overturns the state model
the ruling is expected to rest on, the normative section is **not** written and
the finding comes back for a decision first. This remains one document either
way; a second document would add ceremony, not evidence.

## 6. What the ruling is expected to touch — and what it must not assume

The direction settled before measurement, and recorded here so the measurement
cannot be read as having discovered it: **`held` is not weakened.** The ramp
names the gap instead — an external input may be *declared*, carrying its
identity and its authority identifiers without its bytes, and a declared input is
authorable but never belief-eligible. This is the move the coreference ruling made
with `indeterminate`: name the unestablished state rather than let it read as
absence.

Two existing rows already own most of this ground, and the ruling is expected to
**amend rather than append**:

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
3. **Whether an authority identifier resolves.** The paper axis measures presence,
   not resolution. Resolving 52 DOIs is a network measurement of registries, not
   of this corpus.
4. **Anything about the successor's own corpora.** None exist yet. Every figure
   here describes the predecessor's shared store.

## 8. Open at the time of writing

1. **How long a probe's evidence of retrievability lasts.** A timestamp is
   recorded; what admission may do with a six-month-old successful probe is the
   ruling's to decide.
2. **Whether bytes-without-a-recorded-hash is its own admission state.** The
   resource is holdable and unpinned. Reconnaissance found one; the run will say
   whether the case is rare enough to fold in.
3. **Whether papers are inputs at all.** A paper supports a claim; an input is
   consumed by a run. The two may need different admission paths, and 222 records
   carrying no authority identifier is the figure that makes the question urgent
   rather than academic.
