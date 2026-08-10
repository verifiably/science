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
ramp's §4 retrieval boundary (preflight refusals, retrieval bounds, and the
`byte-locator-untested` / `retrieval-failed` vocabulary, reused as the acts'
dereference contract, §3); the tamper-evident log design (its own table `L`;
its `intent`/settlement discipline, reused by the two mutating acts, §3;
guarantees stated at the strength they have until `atoms` A7–A8 land);
conformance cut 2
(`2026-08-09-conformance-cut-2.md`) §2.1 item 1 — the slice consumes byte
observations as supplied arguments and settles nothing about their store, "an
argument's type is not a storage design."
**Constraints:** the frozen tables stay frozen under their identifiers; this
design adds its own table (**H**, §6), taking the corpus from eleven frozen
tables and 139 rows to **twelve and 143**. The cut-2 document is frozen: it is
amended by Status append only. No timestamp enters any derivation **under the
current projection rule** — the one sanctioned successor (§4) would read
`observed_at` and an explicit reference instant only as pinned,
receipt-committed derivation inputs, and lands by amending this constraint,
never by an ambient clock. No new attester class is privileged (`meta/`
measures reliability, nothing assumes it).

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
| `location` | a **typed, canonical** byte locator: `store(store identity, relative path)` for bytes in a managed store, or `url(canonical absolute URL)` for remote bytes. Each type carries its canonicalization rule (path normalization for `store`; scheme-and-host lowering, default-port and dot-segment removal for `url`), applied **at construction** — equality is field equality of the canonical form, and everything keyed "per location" (§4) keys on it. An opaque string cannot do this job: the same path spelling names different bytes in different stores, and one URL has many spellings, which would break dereferencing, the same-location refusal, and `H2` at once. The two types are the two every §3 act already dereferences; adding a locator type is an amendment (§7) |
| `outcome` | `found` with an **algorithm-qualified** digest `<algorithm>:<hex>`, or `absent`. Both are **established findings**: `found` means the act hashed the bytes it dereferenced; `absent` means the dereference completed and answered that the location holds nothing — a store root enumerated with the path missing, an authoritative negative from a URL's origin. An attempt that established neither mints no observation (§3). **Qualification is the invariant, not the algorithm**: a digest that is not algorithm-qualified is refused at construction — the survey instrument's rule, made a record invariant, because losing the algorithm is what broke the first freeze — but the record is **algorithm-generic**. Which algorithms may pin bytes is the profile's open residue (ramp §6.2), and the ramp is explicit that the instrument's own sha256-only bound "is its own rather than the profile's" — a capability limit of one tool. Freezing that limit here would make a future accepted declaration unobservable by construction: a basis it could carry, an observation it could never have |
| `expected` | optional: the algorithm-qualified digest the act *expected* at this location — an acquisition retrieving against a declaration records what it was retrieving *for*. This is the explicit expectation link that lets a first-contact mismatch surface at derivation (§5): `found(D′)` with `expected = D` joins to every declaration naming `D`. Promotion never reads it — held is decided by `outcome` alone, so the field adds an association, never an assertion |
| `observer` | the attester's identity — human or agent, equally weighted; reliability is `meta/`'s to measure, never this record's to assert |
| `instrument` | the identity of the tool that hashed or dereferenced — the survey instrument's commit-pinning discipline, generalized |
| `event_token` | minted by the act, one per act — the `retraction` / `coreference-attestation` / `run` precedent, whose token is what "keeps two genuinely distinct … events distinct". Without it, two identical findings by one observer at one location in one clock tick collapse into one identity — a piece of corroborating evidence silently lost — and `observed_at` cannot carry the guarantee: a timestamp has resolution, a mint does not. For the two mutating acts (§3) this token is the **same one their intent carries** — reused, never a second attempt id, the tamper log's own rule — which is what correlates an observation to the intent it settles |
| `observed_at` | when the act ran, in **one canonical encoding** — an RFC 3339 UTC instant, `Z`-suffixed, fixed precision — so one instant has one byte form under the facet hash. **Recorded as data, never read by a derivation** (§4). It carries no uniqueness: distinctness of acts is `event_token`'s job, never the clock's |
| `supersedes` | zero or more identities of prior holdings observations, **every one for the same canonical location**. Constructing a record naming a predecessor at a different location is refused — the per-location discipline is by construction, not convention. The plural form is what lets a later act resolve a fork: concurrent observers cannot name each other, so one location can grow parallel heads, and the resolving re-check supersedes every head it replaces (§4). **Canonical representation, because `science.identity.v1` refuses sets:** the facet encodes `supersedes` as a **deduplicated sequence sorted by canonical reference bytes** before hashing — one predecessor set, one identity; anything else would mint one fork-resolution under several addresses, or none |

**The `store identity` a `store` locator names is not left undesigned — it
reuses the one lifecycle contract the corpus already has for exactly this.**
The tamper-evident log design gave the world root a `world_id`: minted once
at fresh initialization, preserved verbatim by replica, restore and cold
bootstrap, and a configuration/genesis mismatch **refuses** rather than
silently re-minting. A store's identity is that contract applied to a store:
minted at store initialization, carried in the store's genesis record,
surviving every move and replica *because it is data, not a path*. The
failure mode the contract cannot prevent — two replicas of one genesis
diverging into different bytes at one relative path — needs no new machinery:
the diverging observations are **disagreeing heads at one canonical
location**, which is precisely the contested state §4 refuses. A fork
surfaces as the conflict it is, instead of hiding in an ambiguous locator.

Identity is the content identity of this facet under a new domain,
**`science.holdings-observation.v1`**, through `science.identity.v1`'s
`v1.digest`. Every field participates: two acts that found the same bytes at
the same location are two records **because each bears its own minted
`event_token`** — distinct evidence stays distinct however the clock reads,
including two acts in one clock tick — and §4 says what "current" means.

**Observations are declaration-independent.** A record says *bytes at L hash
to D* (or *L holds nothing*); it names no dataset. The join to datasets
happens at derivation time, by digest — exactly how cut 2's `admission_state`
already matches, location never read. One observation therefore serves every
dataset whose declaration names that digest, and an observation of unclaimed
bytes is recordable but promotes nothing: no declaration names its digest, and
the fabricated-basis rule is untouched — ramp §6.6's line stands, hashing
bytes a record never declared must never seed a declaration.

**A mismatch is not a record kind.** An act that found bytes hashing to `D′`
where it expected `D` records `found(D′)` with `expected = D` — the truth
about the bytes, plus the association that makes the disagreement reportable.
The mismatch itself is *computed* at derivation (§5), against each declaration
naming `D`, and reported as the ramp's `G9` arm requires: not promoted, and
not reported as a failure to retrieve. The record layer never decides which
declarations are affected; the join does.

## 3. Creation acts

Exactly three acts mint a holdings observation:

1. **An acquisition ending.** `R10` routes URL-valued inputs to acquisition
   and ramp §6.6 rules that an acquisition *ends by recording the digest of
   what it retrieved*. That recording now has an address: the terminal act of
   every acquisition is minting the `found` observation for each resource it
   retrieved. An acquisition that has not minted its observations has not
   ended — the "unfinished acquisition" of §6.6, now visible as the absence of
   its records. A resource the acquisition *failed* to retrieve is an
   inconclusive attempt (below), not an `absent` — it mints nothing.
2. **An audit, or any explicit re-check.** The admission-ramp survey is the
   existing example: an instrument dereferenced locations, hashed bytes, and
   reported. Under this design such a run mints observations — `found` with
   whatever digest the bytes have, or `absent` where the look completed and
   established nothing is there — each superseding the prior record for its
   location, if one exists; a look that established neither reports and mints
   nothing (below).
3. **A boundary-mediated deletion.** Destroying bytes through the execution
   boundary mints `absent` superseding the `found` it invalidates. This is
   `R5`'s negative (a) — destroy the last held copy, heldness ends — enacted
   the only way the act-bound ruling permits: because a record was recorded.

Nothing else mints one. Not a declaration, not a directory listing, not an
import of somebody's claim that bytes exist. `G9`'s "no API accepts an
authored `held`" extends naturally: no API accepts an authored *observation* —
construction is reserved to acts that dereferenced and hashed, and **H1** (§6)
is what makes that reservation independently checkable.

**An inconclusive attempt is not a finding.** A retrieval refusal, a timeout,
a transport failure, unreadable bytes — each proves neither `found` nor
`absent`, and computation §7.1's line — *a failure to look is not a finding of
absence* — binds the acts themselves, not just the drafts the ramp held to it.
Such an attempt mints **no observation**. It lands in the act's own report
under the ramp's existing vocabulary, reused rather than reinvented: a locator
refused before any request was made is **`byte-locator-untested`** with the
refusal reason, a request that was made and did not yield the bytes is
**`retrieval-failed`**. The record layer is untouched: the prior observation,
if any, stays active, because no act established otherwise. `absent` is
reserved for a completed dereference that answered — and **H4** (§6) is what
makes the reservation sabotage-able in both directions.

**Dereferencing is the ramp's boundary, reused — not a second one.** Every act
above consumes an untrusted locator, and §2's canonical form is an equality
contract, not a safety contract. A `store` locator dereferences by resolving
its store identity to a supplied root **whose genesis record must carry that
identity** — verified before any read, a mismatch refusing exactly as the
`world_id` contract refuses a re-mint — and then resolving the relative path
under the ramp's local preflight: an absolute path, an upward traversal, or a
symlink escape from the root is refused, **resolved and compared against the
root before any read**. A `url` locator inherits the ramp's network boundary
whole, not paraphrased: the `https`-only scheme set, the non-public-address
refusal, per-hop redirect revalidation, the timeout and the streaming byte
ceiling, and the pin-the-validated-resolution rule with hostname and TLS
validation preserved — *"if it cannot do both, it issues no request."* The
classification above comes with the boundary: every one of these refusals and
failures is an inconclusive attempt, never an `absent`.

**The two mutating acts run under the tamper log's intent discipline, because
they span roots.** An acquisition ending and a boundary-mediated deletion each
mutate a store while their observation lands in the observer's corpus — two
roots — and the inherited log is per-root, its registration never publishing
across roots. Record-first could attest a mutation that never happened;
mutate-first could crash and leave a stale `found` active with nothing marking
it. So the ordering is pinned, reusing the log's existing `intent` consumer
shape rather than inventing a protocol: **(1)** the boundary durably appends a
**holdings intent** in the observer's corpus root — the root the settlement
will land in, so intent and settlement share one chain and the log's own
same-root rule is satisfied — naming the canonical location, the act kind, and
the act's minted `event_token`; **(2)** the store mutation runs; **(3)** the
observation is minted as that intent's **settlement**, correlated by the
token. An intent with no settlement proves exactly what the log says an
unmatched intent proves — *a boundary-mediated attempt with no recorded
outcome*, crash and cancellation indistinguishable — and its consequence is
§4's: the named location is **unsettled**, refusing the projection until a
re-check act observes what is actually there and supersedes through it. A
phantom attestation cannot arise (the observation is minted only after the
mutation completed), and a stale `found` cannot silently survive a crash (the
unmatched intent marks it). A pure re-check mutates nothing and needs no
intent: a crashed audit is a look that never became a finding, which **H4**
makes the act's failure, not the record's. Adding the holdings intent to the
log's named consumer list is an amendment, tabled in §8.

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

**Active** means: not named by any enumerated record's `supersedes`. Ordering
is by explicit reference only — the records for one canonical location form a
DAG walked from its heads, never a list sorted by time. `observed_at` orders
nothing, decides nothing, and expires nothing (**H2**).

The structure is stated, not assumed:

- **Acyclicity is an invariant, checked — never an impossibility, assumed.**
  The tempting argument — a record's identity covers its predecessors', so a
  cycle would need a hash fixpoint — is the exact argument the formal model's
  **ρA9** found invalid for `retraction` and replaced with the retraction
  graph's acyclicity *invariant*, validated where records are admitted. The
  same ruling governs here: each location's `supersedes` graph **must be a
  DAG as a condition of admissibility**, the projection checks it on every
  walk, and a record set presenting a cycle **refuses the projection**.
  Traversal never trusts termination it has not checked.
- **Forks happen and are legal.** Two concurrent audits of one location
  cannot name each other, so both are heads. Heads whose outcomes **agree** —
  the same `found` digest, or both `absent` — coalesce into one claim: two
  auditors agreeing is corroboration, not conflict, and refusing it would
  make concurrent audit an error. Heads whose outcomes **disagree** make the
  location **contested**, and a contested location **refuses the projection**
  — the existential held-rule must never silently let `found` outvote
  `absent`. The repair is an act: a re-check that supersedes *every* standing
  head (the set-valued `supersedes` of §2) and records what is actually
  there.
- **A dangling predecessor is not an error.** A head whose `supersedes` names
  a record outside the enumerated coverage is still a head; the unseen tail
  is the §5 coverage bound doing its job.
- **An unsettled location refuses, like a contested one.** A holdings intent
  (§3) enumerable in the coverage with no settling observation marks its
  canonical location **unsettled**: some boundary-mediated mutation has no
  recorded outcome, so the location's active records may describe a world
  that no longer exists. The projection refuses the location until a re-check
  act settles what is there. Unsettled is contested's sibling — both name
  evidence in a state only an act can repair, and both make it the caller's
  problem instead of a silent guess.

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

**This closes ramp §8 item 1 at the record layer, and names the seam that
owns the remainder — which is not the belief policy.** "What may admission do
with a six-month-old probe" splits: the record layer answers *the observation
stands until superseded* — six months old and active is active. Whether
anything ever discounts old evidence is a question about **heldness**, and
heldness is decided before admission, which is decided before the belief
policy ever runs — `science.belief.v1` aggregates already-admitted
directional inputs and receives neither observations nor `observed_at`, so
recency can never be its parameter without amending the closure itself. The
seam that *can* own it is the **projection rule** (§5): the derivation
receipt pins the rule's exact binding, so a future recency-bearing projection
rule is a successor rule, pinned and visible in every receipt it signs —
never an ambient reinterpretation of the same records. And such a successor
carries one more obligation, stated now so it cannot be forgotten then: a
rule that discounts by age must take its **reference instant as an explicit
derivation input, committed into the receipt** — otherwise the same rule over
the same corpus states validates today and refutes tomorrow, which breaks the
receipt's re-run contract (§5) with an ambient clock, the exact thing this
section refuses. `observed_at` is in the facet so that successor *can* read
it as data. No current rule does, and this design mints none.

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
   result would be the silent shrink the declaration exists to prevent. The
   enumeration also carries the coverage's **unmatched holdings intents**
   (§3): a location one names is unsettled and refuses (§4). An intent outside
   the coverage is invisible exactly as its would-be settlement is — the same
   bounded claim, stated once.
3. A **dataset-scoped adapter** turns the active set into cut 2's argument.
   The seam is already dataset-keyed — the evaluator's availability context
   maps each dataset address to its own `ByteObservation` tuple, and
   `admission_state` reports a supplied observation matching no declared
   digest as a `mismatch` — so the adapter's whole job is deciding **which
   heads enter a dataset's tuple**. Three joins, each explicit:
   - **by outcome** — a head whose `found` digest matches a declared resource
     digest enters. This is promotion, and it is the only join `held` reads.
   - **by expectation** — a `found` head whose `expected` digest matches a
     declared resource digest enters, whatever digest it actually found. A
     first-contact acquisition that retrieved wrong bytes surfaces here, and
     the existing seam reports it as the `mismatch` it is. (An `absent` head
     never enters a tuple — it has no digest to enter with; what it
     contributes is the absence of anything, and the resource reads
     `no-matching-observation-in-coverage`.)
   - **by history** — a head enters if any record it transitively supersedes
     would have entered by outcome or expectation. Bytes that drifted since a
     matching observation surface here: the head's differing digest arrives
     as a `mismatch`, an `absent` head contributes nothing and the resource
     reads `no-matching-observation-in-coverage` — the ramp's distinction
     between *different bytes* and *no bytes*, preserved by construction.
   A head none of the three joins reaches belongs to no dataset in question
   and enters nothing — declaration-independence at work, not a gap. And
   every join compares **algorithm-qualified digests as wholes** — same
   algorithm, same hex, or no join. A `found` under one algorithm neither
   matches nor mismatches a declaration pinned under another: nothing
   compared them, and reporting `mismatch` would be the survey's own coverage
   error — the bytes said to contradict the record when in fact nothing
   checked them — recurring at the seam. An incommensurable head enters
   nothing, and the resource reads `no-matching-observation-in-coverage`:
   true, in the checkable sense — no observation exists that can answer for
   it.
4. The projection also yields a **derivation receipt**, on the contract world
   §5 and `W8a` already set for enumerations that feed belief — adopted
   whole, not paraphrased. The receipt names the **exact corpus-state
   identities** enumerated (a receipt naming corpora rather than states is
   **`malformed`**), and the **exact rule binding**: the fixture-bound
   identity of the **active-set reducer** — steps 1 and 2 whole: enumeration,
   the supersession walk, coalescing, and the contested-, cycle- and
   unsettled-refusals; the rule a recency-bearing successor would replace
   (§4) — *together with* the content identity of the implementation
   that ran, resolved from the held store — a bare identity or version
   string is `malformed`, and an implementation that fails its fixtures **is
   not that rule**. Validating a receipt is re-running: resolve the binding,
   re-reduce the named states, and land in the vocabulary the corpus already
   has — **`validated`** (the named active set reproduces), **`refuted`**
   (it does not), **`unresolvable`** (a named corpus state or the
   implementation is not held here — a computability state, never an
   epistemic one, and never reported as refutation), **`malformed`** (the
   receipt could never be checked by anyone). A receipt naming coverage and
   output alone would validate nothing — a wrong or incomplete reduction
   could sign a perfectly consistent one — which is `H3`'s second arm (§6).

**The receipt's claim ends at the active set.** The dataset-scoped adapter
(step 3) is deliberately outside the binding: its other input is the dataset
declarations, and a receipt that claimed the dataset-keyed tuples without
naming those declarations as inputs would let a wrong adapter reproduce the
active set and still validate — a receipt certifying what it never checked.
The adapter answers instead at the seam it feeds: its output *is* cut 2's
argument, and a mis-join is `G9`'s arms' business at the admission seam,
where the declarations are first-class. One receipt, one claim, checkable in
full — widening it to the tuples is a decision for the cut that would also
put declarations into the receipt's input set, not a default.

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

> **H1 — creation is reserved to acts, and to established outcomes.** A
> holdings observation exists only as the recorded outcome of an act that
> dereferenced its location and **established** what it records — `found` by
> hashing the bytes, `absent` by a completed dereference that answered
> nothing is there: an acquisition ending, an audit, a boundary-mediated
> deletion. Nothing mints one from a declaration, a directory listing, or an
> attempt that established neither.

*Sabotage:* back-fill `found` records from a directory listing, copying each
declared digest into a record without hashing anything. Every banked arm,
exercised at the derivation seam, passes — the derivation *does* read records,
so `G9`'s path-exists arm is satisfied — and the content-addressing guarantee
is void one layer up: the path-exists predicate has been laundered through the
record store. Creation is the unowned half of the record's lifecycle exactly
as promotion was the unowned transition before `G9`, and H1 owns it.

> **H2 — supersession is by explicit reference, per location, over a checked
> DAG, and a contested location refuses.** Active-ness is resolved by walking
> each canonical location's `supersedes` graph from its heads, with
> acyclicity validated as an **admissibility invariant** on every walk (ρA9's
> discipline). No derivation orders records by `observed_at`; no record
> supersedes across locations; agreeing heads coalesce; **disagreeing heads
> refuse the projection** rather than letting any outcome win.

*Sabotage, first arm:* resolve "current" by latest timestamp. Every banked
row passes — none speaks to ordering — and active-ness now moves with clock
skew between observers: two records, neither superseding the other, flip
precedence with no node recorded, which is admission changing because of a
clock, the act-bound violation in its subtlest form. *Sabotage, second arm:*
on disagreeing heads — an active `found` beside an active `absent` — let the
existential held-rule quietly count the `found`. Every banked row passes, and
a location whose own evidence is in open conflict promotes a dataset as if it
were not; H2's refusal is what makes the conflict a caller's problem instead
of a silent vote. *Sabotage, third arm:* skip the acyclicity check on the
strength of the hash-fixpoint argument — the argument ρA9 already found
invalid once. A crafted record set presenting a cycle now hangs the walk or
silently drops the location, whichever the traversal happens to do; every
banked row passes either way, and H2 alone demands the check that refuses it.

> **H3 — the derivation refuses an undeclared coverage, and its receipt is
> checkable.** Every heldness answer names the corpus states it enumerated
> and the rule that reduced them; "whatever is checked out" is not a
> coverage, and a receipt the named rule over the named states does not
> reproduce is a defect, not a disagreement.

*Sabotage, first arm:* default the coverage to the corpora currently present.
`G9` passes (records are consulted), and `R5`'s banked arms pass — they test
copy loss, not enumeration scope — while unmounting an observing corpus
silently demotes every dataset it vouched for: belief depending on the
checkout, the producer-snapshot defect on the holdings side, with no banked
arm positioned to see it. *Sabotage, second arm:* enumerate half the declared
coverage — or reduce with an implementation other than the bound one — and
sign the receipt anyway. The receipt stays internally consistent, every
banked row passes, and the completeness claim is void; H3's second arm is
what makes "resolve the binding, re-reduce the named states" a test instead
of a hope. The arm inherits §5's outcome vocabulary whole: a reproduced set
is `validated`, a wrong reduction is **`refuted`**, an absent corpus state or
unheld implementation is **`unresolvable`** — never reported as refutation —
and a receipt naming corpora-not-states or a bare version string is
**`malformed`**, refused rather than trusted.

> **H4 — no silent act, and no laundered non-answer.** An act records every
> outcome it **established** — `found`, `found` with an unexpected digest,
> `absent` — and an act that established an outcome but cannot record it
> **fails**; it does not report transiently and drop the record. An
> inconclusive attempt records **no observation**: it reports through the
> act's own channel (`byte-locator-untested`, `retrieval-failed`) and never
> mints `absent`. A mutating act runs inside its intent–settlement ordering
> (§3) or fails; it never mutates outside it.

*Sabotage, first arm:* an audit that finds a mismatch prints it and mints
nothing. The stale `found` stays active, the dataset stays held, and every
banked arm passes — `G9`'s mismatch arm, exercised over *supplied*
observations, never sees an observation that was never recorded. *Sabotage,
second arm:* a timed-out retrieval recorded as `absent` — the non-answer
laundered into established absence. The fresh `absent` supersedes the
standing `found`, a held dataset demotes on evidence of nothing, and every
banked row passes; computation §7.1's *a failure to look is not a finding of
absence* is banked as prose, and H4 is its only enforcement at this seam.
*Sabotage, third arm:* a deletion that mutates first and skips the intent. A
crash before minting leaves the stale `found` active with nothing marking the
location unsettled; the log's banked rows are per-root and never knew a
holdings act existed; every banked row passes, and H4 alone demands the
ordering that makes the window visible. H4 is computation §7.1 — the framing
the ramp holds its own drafts to — made an obligation on the acts themselves:
a look that established something must become a finding, and a look that
established nothing never may.

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

1. **Recency as a successor projection rule.** Whether anything ever
   discounts old observations, and by what curve — now a typed question on
   `observed_at`, owned by the projection-rule seam whose exact binding every
   derivation receipt pins (§4, §5), and bound by the stated obligation: the
   reference instant is an explicit derivation input in the receipt, never an
   ambient clock. Explicitly **not** a belief-policy parameter: the belief
   policy runs after admission and never sees an observation.
2. **The partly-pinned rule's empirical corroboration** — ramp §8 item 3,
   evidence not design, untouched here.
3. **Whether the derivation receipt joins the belief-input closure** — owed
   to the persistence cut (§5).
4. **Further locator types.** §2 fixes two — `store(store identity, relative
   path)` and `url(canonical absolute URL)` — because those are the two the
   creation acts dereference today. A third scheme (an object store's native
   addressing, say) arrives by amendment, with its canonicalization rule, or
   not at all.
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
| admission ramp §8 item 1 | gains: *closed at the record layer 2026-08-10 — an observation stands until superseded; what remains is a possible recency-bearing **successor projection rule**, pinned in every derivation receipt with an explicit reference instant, and it is **not** a belief-policy parameter (the holdings design §4)* |
| admission ramp §6.7 | gains a one-line pointer to this design |
| conformance cut 2 | **Status append only:** one sentence recording that the design its §10 item 1 named as the most consequential open question landed 2026-08-10 |
| guide `open-questions.md` | the *where verified holdings are recorded* entry is replaced by its residue: recency as a possible successor **projection rule** (never a belief-policy parameter) and the partly-pinned corroboration; the *third conformance cut* entry's run-capture arm gains *unblocked by the holdings design, 2026-08-10* |
| guide `glossary.md` | **Holdings observation** added; **Held** and **Declared** cite it |
| guide `foundations.md` | the `held` section gains the record: heldness is derived from active holdings observations under a declared coverage; the kind inventory gains `holdings-observation`; this design joins `sources` |
| guide `contracts-and-adoption.md` | frozen-row count **139 → 143**, tables **eleven → twelve**; the open-edges pointer moves the holdings question to its residue |
| epistemic kernel, kind inventory | a world record is a kernel kind, and the counts move with it: the kernel is **eleven kinds today** — eight as designed, then `retraction` (correction lifecycle), `instrument-certification` (5b), `coreference-attestation` (world address ruling, 2026-08-08) — and **`holdings-observation` joins as the twelfth**, on the same appending precedent, the sequence preserved; the §4.4 accounting discipline extends to it. The count sites are amended as an **exact inventory, not a sweep**: the domain extension design's two "eleven kernel kinds — ten until 2026-08-08" clauses (its §1 inherits line and its §5 ownership line); the adoption ledger's docket note ("the kernel is **eleven kinds**, not ten"); the admission ramp §2.2's "binds all eleven kinds"; the world address ruling §3's "now bind all eleven kinds"; the formal model §2.1 heading "(the eleven kernel kinds)" with its "All eleven" lead — `foundations.md`'s anchor link to that heading moves with it; and `foundations.md`'s "the formal inventory contains eleven kernel kinds". The world address ruling's *historical* statements — "an eleventh kernel kind", "taking the kernel to eleven kinds" — record what that ruling did, remain true, and are deliberately untouched |
| tamper-evident log design, the `intent` consumer list | "the one consumer named today is the assessment-run intent" gains its second: the **holdings intent** (§3) — the two mutating acts register pre-mutation in the observer's corpus root and settle by observation, correlated by the act's `event_token`, reused per the log's own not-a-second-attempt-id rule |
| world addressing §4.2, the identity-basis table | gains the **`holdings-observation`** row: basis is the content identity of the §2 canonical facet under `science.holdings-observation.v1` — every field participating, the minted `event_token` among them on the `retraction` shape's precedent, `supersedes` hashing as its sorted ref sequence — so the kind has a banked address basis rather than an implied one |
| formal model §2.1 | gains the **holdings observation** player row: content identity over the §2 facet under `science.holdings-observation.v1`, event token included; minted by the three acts; revised by supersession only; read by the coverage projection |
| formal model, tables | reproduces the **H** table, as it reproduces every other |
| normative contract §4 | the exact current inventory extends to twelve tables and 143 rows; the count guard moves in the same change |
| adoption ledger, artifact 7 | the oracle inventory extends to the **H** table |
| README | row count **→ 143**, tables **→ twelve**; the design table gains this document's row; the spelled-out design count and date range move per the existing corpus guard |
| `python/tests/test_designs_corpus.py` | `TABLE_OWNERS` gains `H → 2026-08-10-verified-holdings-record-design.md`; the "eleven frozen tables" README assertion becomes twelve via the guard's own machinery |

**Not amended, deliberately:** `G9` — every arm stands, and this design is its
instantiation, not its revision; `R5` and `R10`, leaned on and unmoved; cut 2's
selection, frozen and untouched beyond the Status append; the belief policy —
confirmed a **non-owner** of recency (§4), so nothing arrives there, not even a
question; the domain extension boundary design's *governance* — it rules
domain contracts, not core digest namespaces, so no namespace registration is
owed there and `science.holdings-observation.v1` is accounted for where
identity is accounted (world §4.2 and the formal model); its two kind-count
quotes move with every other count site, per the kernel row above.
