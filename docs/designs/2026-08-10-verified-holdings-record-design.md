# Verified holdings record — design

**Date:** 2026-08-10
**Status:** design, approved in session. The amendment set of §8 applies in the
banking commit; nothing here is implemented, and no conformance arm is claimed —
the G9 independence arm and the record's code stay owed to the cut that draws
the persistence seam (§7).
**Inherits:** the admission ramp (`2026-08-09-admission-ramp-design.md`) §6.1
(state derived from declaration plus the system's record of verified holdings),
§6.2 (the dataset basis projection), §6.3 (`G9` and its arms), §6.7 and §8
item 2 (the record undesigned: where it lives, how it is re-checked, what makes
an entry stale); kernel §2.2 (held is possession and addressability, location-
and mechanism-independent); computation `R5` (belief does not depend on
availability in this checkout), `R10` (a URL-valued input routes to
acquisition), and the act-bound validation ruling (validation at explicit
import and audit, "mounting a volume is not an epistemic event", admission
changes because a node was recorded); world §5's producer snapshot (enumeration
bounded by a coverage declaration naming corpora by stable identity, because
enumeration against whatever is checked out is the R5 violation); the
correction lifecycle (revision by superseding record, never by edit); the
tamper-evident log design (its own table `L`; guarantees stated at the strength
they have until `atoms` A7–A8 land); conformance cut 2
(`2026-08-09-conformance-cut-2.md`) §2.1 item 1 — the slice consumes byte
observations as supplied arguments and settles nothing about their store, "an
argument's type is not a storage design."
**Constraints:** the frozen tables stay frozen under their identifiers; this
design adds its own table (**H**, §6), taking the corpus from eleven frozen
tables and 139 rows to **twelve and 143**. The cut-2 document is frozen: it is
amended by Status append only. No timestamps enter any derivation; no new
attester class is privileged (`meta/` measures reliability, nothing assumes
it).

## 1. The gap, and the box already drawn around it

The admission ramp closed F2 by deriving a dataset's state — curation note,
`declared`, `held` — from the declaration and *the system's record of verified
holdings*, and then said plainly that no such record exists: where it lives,
how it is re-checked, and what makes an entry stale are undesigned (ramp §6.7,
§8 item 2). The cost is concrete and measured: 24 of the 47 surveyed records —
62 resources, 11.83 GB — are in a state no measurement can currently determine,
because answering for them is a search when it should be a lookup.

The bounds are already frozen, from three sides:

- **`R5`** — belief does not depend on availability in this checkout. The
  record cannot be a property of a checkout, and a derivation over "whatever
  happens to be here" is the violation whatever store it reads.
- **`G9`** — no API accepts an authored `held`. The record cannot be an
  assertion; it can only be the output of an act that hashed bytes.
- **Act-bound validation** — admission may change *only because a record was
  recorded*: at explicit import, or because an audit minted a superseding node.
  A filesystem changing shape is not an epistemic event. Any staleness
  semantics lives inside this ruling or contradicts it.

Cut 2 sharpened the consumer side without designing the supply side: the
evaluator's availability context takes byte observations *as arguments*,
matched by digest, location never read. This design is the supply side — what
produces those observations, where they persist, and how a caller comes to
hold a current set of them.

Two of the ramp's residues are decided here: the record itself (§8 item 2) and
the staleness of its entries, which is §8 item 1 — how long a probe's evidence
lasts — asked about the remote half. The third residue, the partly-pinned
rule's empirical corroboration, is evidence, not design, and stays open.

## 2. The record

A **holdings observation** is a world record: content-addressed, attributable,
append-only, revised only by supersession. One record spans **one location
claim** — what one act found at one locator — and nothing wider.

Canonical facet:

| field | content |
|---|---|
| `kind` | `holdings-observation` |
| `location` | a byte locator — a path in a store, a URL, any string another party with access could dereference. Non-empty. What grammar locators take beyond that is open (§7); the field is opaque to every derivation |
| `outcome` | `found` with an algorithm-qualified digest `sha256:<64 hex>`, or `absent`. The algorithm must be in the accepted set (`sha256`); a digest that is not algorithm-qualified is **refused at construction** — the survey instrument's rule, made a record invariant |
| `observer` | the attester's identity — human or agent, equally weighted; reliability is `meta/`'s to measure, never this record's to assert |
| `instrument` | the identity of the tool that hashed or dereferenced — the survey instrument's commit-pinning discipline, generalized |
| `observed_at` | when the act ran. **Recorded as data, never read by a derivation** (§4) |
| `supersedes` | optional: the identity of the prior holdings observation **for the same location**. Constructing a record whose `supersedes` names a record with a different location is refused — chains are per-location by construction, not by convention |

Identity is the content identity of this facet under a new domain,
**`science.holdings-observation.v1`**, through `science.identity.v1`'s
`v1.digest`. Every field participates: two acts that found the same bytes at
the same location at different times are two records, which is correct — each
is a distinct piece of evidence, and §4 says what "current" means.

**Observations are declaration-independent.** A record says *bytes at L hash
to D* (or *L holds nothing*); it names no dataset. The join to datasets
happens at derivation time, by digest — exactly how cut 2's `admission_state`
already matches, location never read. One observation therefore serves every
dataset whose declaration names that digest, and an observation of unclaimed
bytes is recordable but promotes nothing: no declaration names its digest, and
the fabricated-basis rule is untouched — ramp §6.6's line stands, hashing
bytes a record never declared must never seed a declaration.

**A mismatch is not a record kind.** An act that found bytes hashing to `D′`
where a declaration says `D` records `found(D′)` — the truth about the bytes.
The mismatch is *computed* at derivation, against each declaration that names
`D`, and reported as the ramp's `G9` arm requires: not promoted, and not
reported as a failure to retrieve. The record layer does not know which
declaration the observer had in mind, and does not need to.

## 3. Creation acts

Exactly three acts mint a holdings observation:

1. **An acquisition ending.** `R10` routes URL-valued inputs to acquisition
   and ramp §6.6 rules that an acquisition *ends by recording the digest of
   what it retrieved*. That recording now has an address: the terminal act of
   every acquisition is minting the `found` observation for each resource it
   retrieved. An acquisition that has not minted its observations has not
   ended — the "unfinished acquisition" of §6.6, now visible as the absence of
   its records.
2. **An audit, or any explicit re-check.** The admission-ramp survey is the
   existing example: an instrument dereferenced locations, hashed bytes, and
   reported. Under this design such a run mints observations — `found` with
   whatever digest the bytes have, or `absent` — each superseding the prior
   record for its location, if one exists.
3. **A boundary-mediated deletion.** Destroying bytes through the execution
   boundary mints `absent` superseding the `found` it invalidates. This is
   `R5`'s negative (a) — destroy the last held copy, heldness ends — enacted
   the only way the act-bound ruling permits: because a record was recorded.

Nothing else mints one. Not a declaration, not a directory listing, not an
import of somebody's claim that bytes exist. `G9`'s "no API accepts an
authored `held`" extends naturally: no API accepts an authored *observation* —
construction is reserved to acts that dereferenced and hashed, and **H1** (§6)
is what makes that reservation independently checkable.

**The forgery bound, stated at the strength it has.** A hand-forged
observation — a record written to look like an act's output — stands until an
audit reaches its location, exactly as a hand-forged verification stands until
audited. This is the act-bound ruling's own bound ("tamper detection at import
and under audit, and nothing in between") and it is inherited here, not
improved. What improves it is what improves it there: the tamper-evident log's
pre-mutation registration and detectable removal, landing with `atoms` A7–A8,
under which a record with no registered provenance is itself detectable. Until
then, saying otherwise would be claiming a guarantee the substrate does not
carry.

## 4. Supersession and staleness

**Active** means: not named by any later record's `supersedes` within its
location chain. Ordering is by explicit reference only — a chain is walked,
never sorted. `observed_at` orders nothing, decides nothing, and expires
nothing (**H2**).

The derived facts, over a set of active observations:

- a digest `D` is **held** iff some active observation attests `found(D)` —
  at any location, inside or outside the repository (kernel §2.2, `G9`'s
  location arm).
- a dataset's state is cut 2's `admission_state` over those observations,
  unchanged: `held` only when **every** declared resource digest has a
  matching active observation; the quantifier is `G9`'s and stays whole.

**Age alone never changes the derived state.** There is no TTL, no validity
window, no clock read anywhere in the derivation — a TTL would make admission
a function of the wall clock, which is ambient invalidation with a timer, the
exact thing the act-bound ruling refused. An observation stands until a later
act supersedes it: a re-check that found matching bytes refreshes the chain, a
re-check that found different bytes or nothing demotes through it, a
boundary-mediated deletion closes it.

**This closes ramp §8 item 1 at the record layer, and hands the remainder to
the policy layer, typed.** "What may admission do with a six-month-old
probe" splits: the record layer answers *the observation stands until
superseded* — six months old and active is active. Whether a **belief policy**
discounts old evidence is a policy parameter: `observed_at` is in the facet
precisely so a future policy *can* read it as data and weigh it, the way
`science.belief.v1` weighs directions today. No current policy does, and this
design mints none; the question is now a well-typed parameter on a seam that
exists rather than a floating doubt about a record that didn't.

**The out-of-band bound, restated rather than hidden.** Bytes destroyed
without the boundary — a raw `rm` in a store — leave a stale `found` active
until an audit observes the absence. That is the same sentence the act-bound
ruling wrote about raw `cp`, with the arrow reversed, and it has the same
repair (audit) and the same eventual strengthening (the log's detectable
removal). A reader who needs current heldness *now* runs the re-check act; the
derivation will not pretend to know what no act observed.

## 5. The coverage projection

How a caller comes to hold a current set of observations — the "undesigned
middle" — is a **projection over a declared coverage**:

1. The caller names a **coverage**: the corpora whose observation records the
   derivation may enumerate, each by stable identity. Holdings observations
   live in **the observer's corpus** — whoever performed the act records it in
   their own corpus, like any attestation; observing needs no write access to
   the dataset's home, and the commons store the recreate-not-migrate ruling
   retires is never written to.
2. The projection enumerates every holdings observation across the coverage,
   resolves supersession chains (a chain may span corpora: an audit in corpus
   B may supersede an acquisition record in corpus A — the ref is an identity,
   and identities do not care where they resolve), and yields the **active
   set**. Two consequences are stated rather than discovered: a record
   superseded only in a corpus *outside* the coverage reads active *within*
   it — the coverage declaration is what makes that a bounded, stated claim
   instead of a silent error; and a declared corpus that cannot be enumerated
   **refuses the whole projection** — a partial enumeration reported as a
   result would be the silent shrink the declaration exists to prevent.
3. The active set is precisely the `observations` argument cut 2's seam
   already consumes — `admission_state`, the admission gate, the evaluator's
   availability context. Nothing downstream changes shape.
4. The projection also yields a **derivation receipt**: the coverage
   declaration plus the content identity of the active set it produced.

**A derivation with no declared coverage is refused** (**H3**). This is world
§5's producer-snapshot argument applied to its second population: enumerated
against whatever happened to be checked out, the projection silently shrinks,
a held dataset reads `declared` because its observing corpus was not mounted,
and admission moves with the checkout — `R5`'s exact prohibition. The ramp's
"held **in this coverage**" stops being a caveat on one survey and becomes the
type of every heldness answer.

**The receipt makes the observation set pinnable; it does not pin it.** Whether
the receipt becomes a member of the belief-input closure — alongside the
producer snapshot it is patterned on — is a decision for the conformance cut
that draws the persistence seam, which will hold the closure's frozen
projection in one hand and this receipt in the other. The precedent leans yes
(the producer snapshot was published exactly so kernel §5.1 could digest it),
and this design's obligation is only to make the yes *possible*: the receipt
is a value with a content identity, ready to be a closure member the day a cut
selects it.

## 6. The H table

On the tamper-evident log's precedent, this design adds its own table rather
than appending to `G`. The ramp's pre-commitment governs: a row exists only
for a property that is **independently sabotage-able** — breakable while every
banked row still passes. Four candidates were tested; four survive.

> **H1 — creation is reserved to acts.** A holdings observation exists only as
> the recorded outcome of an act that dereferenced its location: an
> acquisition ending, an audit, a boundary-mediated deletion. Nothing mints
> one from a declaration, a directory listing, or any state the act did not
> hash.

*Sabotage:* back-fill `found` records from a directory listing, copying each
declared digest into a record without hashing anything. Every banked arm,
exercised at the derivation seam, passes — the derivation *does* read records,
so `G9`'s path-exists arm is satisfied — and the content-addressing guarantee
is void one layer up: the path-exists predicate has been laundered through the
record store. Creation is the unowned half of the record's lifecycle exactly
as promotion was the unowned transition before `G9`, and H1 owns it.

> **H2 — supersession is by explicit reference, per location.** Active-ness is
> resolved by walking `supersedes` chains, each chain confined to one
> location. No derivation orders records by `observed_at`; no record
> supersedes across locations.

*Sabotage:* resolve "current" by latest timestamp. Every banked row passes —
none speaks to ordering — and active-ness now moves with clock skew between
observers: two records, neither superseding the other, flip precedence with
no node recorded, which is admission changing because of a clock, the
act-bound violation in its subtlest form.

> **H3 — the derivation refuses an undeclared coverage.** Every heldness
> answer names the corpora it enumerated, by stable identity. "Whatever is
> checked out" is not a coverage.

*Sabotage:* default the coverage to the corpora currently present. `G9`
passes (records are consulted), and `R5`'s banked arms pass — they test copy
loss, not enumeration scope — while unmounting an observing corpus silently
demotes every dataset it vouched for: belief depending on the checkout, the
producer-snapshot defect on the holdings side, with no banked arm positioned
to see it.

> **H4 — no silent act.** An act records its outcome whatever it is: `found`,
> `found` with an unexpected digest, `absent`. An act that cannot record its
> outcome **fails**; it does not report transiently and drop the record.

*Sabotage:* an audit that finds a mismatch prints it and mints nothing. The
stale `found` stays active, the dataset stays held, and every banked arm
passes — `G9`'s mismatch arm, exercised over *supplied* observations, never
sees an observation that was never recorded. H4 is computation §7.1's "a
failure to look is not a finding of absence" — the framing the ramp holds its
own drafts to — made an obligation on the acts themselves: a look that
happened must become a finding.

`H1`–`H4` take the frozen corpus from **139 rows across eleven tables to 143
across twelve**. Their arms are acceptance criteria for the conformance cut
that builds the persistence seam; none is claimed exercised by this document.

## 7. What this unblocks, and what stays open

**Unblocked:**

- **The run boundary.** Cut 2 §2's stop-rule failure dissolves: acquisition
  now has a designed place to record what it retrieved, so a run-capture
  slice no longer chooses between designing this record implicitly and
  building a boundary that can admit nothing.
- **The `G9` independence arm.** Its sabotage — install the path-exists
  predicate, assert `G9` fails alone — needs a persisted promotion predicate
  to corrupt. The record is that predicate's substrate; the arm stays owed to
  the cut that builds it, and is now buildable.
- **The ramp's 24 undetermined records.** Their determination is now a
  procedure, not a mystery: an observing act over a coverage that can see
  their bytes — where any exist — after which their state is a lookup. The 10
  with no authority fields remain reachable only this way, which the ramp
  already said; the design changes what kind of thing the answer is, not the
  work of looking.

**Open, deliberately:**

1. **Recency as a policy parameter.** Whether any belief policy discounts old
   observations, and by what curve — now a typed question on `observed_at`
   (§4), owned by the belief-policy layer.
2. **The partly-pinned rule's empirical corroboration** — ramp §8 item 3,
   evidence not design, untouched here.
3. **Whether the derivation receipt joins the belief-input closure** — owed
   to the persistence cut (§5).
4. **The locator grammar.** `location` is an opaque non-empty string to every
   derivation; whether locators deserve a grammar or a registry is deferred
   until an act needs to dereference one it did not author.
5. **Observer reliability weighting.** Observations are equally weighted at
   derivation; `meta/` measures reliability, and whether any consumer reads
   that measurement is that consumer's design, not this record's.
6. **The engine.** Persistence, the tamper-evident log's strengthening, and
   every operational duty (who runs audits, on what cadence) wait on `atoms`
   A7–A8 and the composition root, as everything durable does.

## 8. What this changes elsewhere

Applied in the same change as this document, on the world address ruling's
precedent: a ruling that leaves its amendments untabled leaves the corpus
disagreeing with itself.

| site | change |
|---|---|
| admission ramp §8 item 2 | gains the closure annotation: *designed 2026-08-10 (`2026-08-10-verified-holdings-record-design.md`); the record is a world record in the observer's corpus, per-location, act-minted, superseded never expired, projected under a declared coverage* |
| admission ramp §8 item 1 | gains: *closed at the record layer 2026-08-10 — an observation stands until superseded; recency moves to the belief-policy layer as a typed parameter on `observed_at` (its §4)* |
| admission ramp §6.7 | gains a one-line pointer to this design |
| conformance cut 2 | **Status append only:** one sentence recording that the design its §10 item 1 named as the most consequential open question landed 2026-08-10 |
| guide `open-questions.md` | the *where verified holdings are recorded* entry is replaced by its residue: recency as a policy parameter and the partly-pinned corroboration; the *third conformance cut* entry's run-capture arm gains *unblocked by the holdings design, 2026-08-10* |
| guide `glossary.md` | **Holdings observation** added; **Held** and **Declared** cite it |
| guide `foundations.md` | the `held` section gains the record: heldness is derived from active holdings observations under a declared coverage; this design joins `sources` |
| guide `contracts-and-adoption.md` | frozen-row count **139 → 143**, tables **eleven → twelve**; the open-edges pointer moves the holdings question to its residue |
| formal model §2.1 | gains the **holdings observation** player row: content identity over the §2 facet under `science.holdings-observation.v1`; minted by the three acts; revised by supersession only; read by the coverage projection |
| formal model, tables | reproduces the **H** table, as it reproduces every other |
| normative contract §4 | the exact current inventory extends to twelve tables and 143 rows; the count guard moves in the same change |
| adoption ledger, artifact 7 | the oracle inventory extends to the **H** table |
| README | row count **→ 143**, tables **→ twelve**; the design table gains this document's row; the spelled-out design count and date range move per the existing corpus guard |
| `python/tests/test_designs_corpus.py` | `TABLE_OWNERS` gains `H → 2026-08-10-verified-holdings-record-design.md`; the "eleven frozen tables" README assertion becomes twelve via the guard's own machinery |

**Not amended, deliberately:** `G9` — every arm stands, and this design is its
instantiation, not its revision; `R5` and `R10`, leaned on and unmoved; cut 2's
selection, frozen and untouched beyond the Status append; the belief policy —
recency arrives there as an open question, not a change.
