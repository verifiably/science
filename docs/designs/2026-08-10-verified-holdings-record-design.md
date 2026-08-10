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
its `intent`/`fulfills` discipline, reused by the two mutating acts, §3;
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
| `location` | a **typed, canonical** byte locator: `store(store identity, relative path)` for bytes in a managed store, or `url(canonical absolute URL)` for remote bytes. Each type carries its canonicalization rule, applied **at construction**. For `store`: path normalization. For `url`, the **exact profile**: scheme and host lowercased, default port elided, dot-segments resolved, percent-encoding normalized to uppercase hex with unreserved characters decoded, query preserved byte-exact, and **no fragment, no userinfo — both refused at construction**. A fragment never participates in an HTTP request, so spellings differing only there would name one retrieval as two locations; userinfo is a credential, and a credential must never enter immutable world content. The obligation reaches past what a parser can check, so it is stated on the acts: a signed or otherwise authenticated URL names an **access grant**, not a location — the location is the credential-free form, and authentication material (a signed query, a token) is supplied **out of band** by the acting boundary, never persisted in a record — equality is field equality of the canonical form, and everything keyed "per location" (§4) keys on it. An opaque string cannot do this job: the same path spelling names different bytes in different stores, and one URL has many spellings, which would break dereferencing, the same-location refusal, and `H2` at once. The two types are the two every §3 act already dereferences; adding a locator type is an amendment (§7) |
| `outcome` | `found` with an **algorithm-qualified** digest `<algorithm>:<hex>`, or `absent`. Both are **established findings**: `found` means the act hashed the bytes it dereferenced; `absent` means the dereference completed and answered that the location holds nothing — today establishable **for a `store` locator only**: the identified root enumerated, the path missing. A `url` locator cannot currently mint `absent`: the inherited boundary classifies every transport and status failure — a 404 included — as `retrieval-failed`, and no qualifying authoritative negative is defined; defining one would be a ramp-boundary amendment, not a record change (§3). An attempt that established neither mints no observation (§3). **Qualification is the invariant, not the algorithm — and qualification is canonical**: the ramp's basis projection already normalizes every digest to `<algorithm>:<lowercase hex>`, and the record adopts that form at construction — lowercase canonical algorithm identifier, lowercase hex, the algorithm's exact width (64 for `sha256`) — refusing an unqualified digest (the survey instrument's rule, made a record invariant, because losing the algorithm is what broke the first freeze) and refusing a non-canonical spelling, since `sha256:AB` and `sha256:ab` would otherwise mint two records of one fact and miss every whole-digest join (§5). None of this freezes the accepted set — canonical form is per-algorithm, and the record stays **algorithm-generic**. Which algorithms may pin bytes is the profile's open residue (ramp §6.2), and the ramp is explicit that the instrument's own sha256-only bound "is its own rather than the profile's" — a capability limit of one tool. Freezing that limit here would make a future accepted declaration unobservable by construction: a basis it could carry, an observation it could never have |
| `expected` | optional: the algorithm-qualified digest the act *expected* at this location — an acquisition retrieving against a declaration records what it was retrieving *for*. This is the explicit expectation link that lets a first-contact mismatch surface at derivation (§5): `found(D′)` with `expected = D` joins to every declaration naming `D`. Promotion never reads it — held is decided by `outcome` alone, so the field adds an association, never an assertion. **With a `found` outcome, `expected` must share the found digest's algorithm — refused at construction otherwise**: an act whose instrument cannot hash in its expectation's algorithm established nothing about that expectation, so it omits the field and reports the unchecked expectation through its own channel — the ramp's rule, a refusal names the tool's limit where a `mismatch` would blame the corpus for it. The constraint is what makes every derivation-time mismatch a same-algorithm comparison (§5) |
| `observer` | the attester's identity — human or agent, equally weighted; reliability is `meta/`'s to measure, never this record's to assert |
| `instrument` | the identity of the tool that hashed or dereferenced — the survey instrument's commit-pinning discipline, generalized |
| `event_token` | minted by the act, one per act — the `retraction` / `coreference-attestation` / `run` precedent, whose token is what "keeps two genuinely distinct … events distinct". Without it, two identical findings by one observer at one location in one clock tick collapse into one identity — a piece of corroborating evidence silently lost — and `observed_at` cannot carry the guarantee: a timestamp has resolution, a mint does not. For every intent-bearing act (§3 — the two mutating acts, and any store-dereferencing re-check) this token is the **same one its intent carries** — reused, never a second attempt id, the tamper log's own rule — and, together with the boundary-built `fulfills`, it is what qualifies an observation as its intent's fulfillment (§3) |
| `observed_at` | when the act ran, in **one canonical encoding**: exactly `YYYY-MM-DDTHH:MM:SSZ` — RFC 3339 UTC, whole seconds, **no fractional digits, no offset form** — so one instant has one byte form under the facet hash, and two conforming implementations cannot mint different identities for one act. **Recorded as data, never read by a derivation** (§4). It carries no uniqueness: distinctness of acts is `event_token`'s job, never the clock's |
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
location**, which is precisely the contested state §4 blocks. A fork
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
   what it retrieved*. That recording is **two outputs at two layers, never
   one record doing both jobs**. *Declaration authoring, where needed:* for a
   resource declared with a locator and no digest — the ramp's eleven — the
   acquirer **pins the declaration** with the retrieved digest. This is
   §6.6's authoring act at the declaration layer, and it is not the
   fabricated basis §2 refuses: the record declared the resource, and what
   was missing was the pin. The authorship flows from the act — retrieval
   against a declared locator — never from an observation record, so §2's
   line stands whole: no observation seeds a declaration, and the eleven
   acquire their basis by an acquirer's authorship, not a record store's side
   effect. *The holdings observation:* the act's evidence, at a **named
   location**. The mutating observation names the **destination store
   location** the bytes were written to — that is the mutation the intent
   (below) covers. The dereference of the source URL was also a look that
   happened and established `found` there, so H4 gives it the same duty: the
   acquisition also mints the `found` observation at the source `url`
   locator — a pure look, no intent, exactly an audit's observation of a
   remote location. An acquisition has **ended** when every retrieval it
   attempted has reached its recorded terminus: a fulfilled intent and its
   observations for each resource retrieved, a reported inconclusive attempt
   (below) for each it failed to retrieve — a resource at neither terminus
   leaves the "unfinished acquisition" of §6.6, now visible as an unfulfilled
   intent or an unreported attempt.
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
reserved for a completed dereference that answered — which today only a
`store` dereference can do (§2). Under the inherited boundary a remote look
never answers *nothing is there*, only `retrieval-failed`, so the cost is
stated rather than hidden: remote disappearance is observable today only as
repeated inconclusive attempts, and a stale remote `found` stands until
either a ramp-boundary amendment defines a qualifying negative response or
the recency successor (§4) discounts it. Stating that cost beats laundering a
status code into absence. **H4** (§6) is what makes the reservation
sabotage-able in both directions.

**Dereferencing is the ramp's boundary, reused — not a second one.** Every act
above consumes an untrusted locator, and §2's canonical form is an equality
contract, not a safety contract. A `store` locator dereferences by resolving
its store identity to a supplied root **whose genesis record must carry that
identity** — verified before any read, a mismatch refusing exactly as the
`world_id` contract refuses a re-mint — and then resolving the relative path
under the ramp's local preflight: an absolute path, an upward traversal, or a
symlink escape from the root is refused, **resolved and compared against the
root before any read**. Path safety is not read consistency, so the contract
has a second half: a store dereference-and-hash runs under the **store's
consistent-read boundary** — the root's existing `atoms` lease, the one its
mutations already serialize through — held from dereference start through
hash completion, so an observation is of **a stable store state**: never a
mixed stream hashed while a replacement was mid-flight, never a transient
absence caught between a remove and a write. A read that cannot obtain the
boundary is an **inconclusive attempt** — reported, minting nothing — not a
torn `found` and not a false `absent`. A `url` locator inherits the ramp's network boundary
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
it. So the ordering is pinned, and it uses the log's machinery **as built** —
intent, registered transaction, `fulfills`, the §6 qualification reduction —
never a token-matching shortcut beside it. In the log's vocabulary an
observation is not a "settlement" (that word is reserved for a registered
transaction's completion); it is a published record whose publishing
transaction *fulfills* an intent:

- **One act, one location, one intent, one token.** A holdings act is per
  canonical location. An acquisition retrieving several resources runs
  several holdings acts, each with its own intent and its own minted
  `event_token` — the log permits exactly one fulfilling registration per
  intent, and one intent cannot name many locations. Ramp §6.6's "ends by
  recording the digest" now reads at this grain: the acquisition has ended
  when the **last** of its acts' intents is fulfilled, and one unfulfilled
  act leaves the whole acquisition the unfinished acquisition §6.6 already
  names.
- **The intent.** Before mutating, the boundary durably appends a **holdings
  intent** in the observer's corpus root — the root the observation will be
  published through, so the log's same-root rule holds — with payload: the
  canonical location, the act kind, the boundary-minted `event_token`, and
  the actor (the assessment-run intent's shape, with the location standing
  where its spec identity stands).
- **The fulfillment.** After the mutation, the observation is published by a
  **registered, committed transaction** in that same root, and the boundary
  constructs `fulfills` **from its own intent** — no caller-selected
  `fulfills` exists, the log's rule restated, not relaxed. A **qualifying
  fulfillment** is a committed registration whose published record is a
  holdings observation for the intent's canonical location carrying the
  intent's `event_token`. Pointer ancestry alone proves nothing — any
  committed transaction could carry `fulfills` — so matching runs only
  through the log §6's reduction: a non-qualifying pointer never matches,
  and an unreadable one leaves qualification **unresolved**, which proves
  nothing and leaves the location unsettled rather than quietly settled.
- **Unmatched or unresolved, and the repair.** An intent is **unmatched**
  exactly as the log defines it — no pointers at all, or every pointer fully
  resolved and non-qualifying — and proves *a boundary-mediated attempt with
  no recorded outcome*, crash and cancellation indistinguishable. An intent
  whose qualification is **unresolved** — an unreadable pointer — proves
  nothing either way, and blocks exactly as an unmatched one does, **as
  itself, never reinterpreted as unmatched**: collapsing unresolved into
  either resolved state would settle a location no evidence settled. A
  **mutating** intent in either condition leaves its location **unsettled**
  (§4). The repair is a later **re-check of that location through the same
  root**, and its ordering covers the *read*, not merely the publication: a
  store-dereferencing re-check appends its **own holdings intent before
  reading** (below), so the chain — never a clock — orders its dereference
  start after the damaged act's intent, and the store's consistent-read
  boundary keeps the read from interleaving with the attempt itself. A
  **fulfilled** re-check intent later in the chain than the damaged intent
  **lifts the unsettled state**. The damaged intent stays unmatched forever,
  which is the truth: that attempt's outcome was never recorded. What the
  repair establishes is the location's current state, which is all the
  projection asked.

A phantom attestation cannot arise (the observation is published only after
the mutation completed), and a stale `found` cannot silently survive a crash
(the unmatched intent marks it until a later fulfilled re-check answers).
**Every store-dereferencing act appends an intent before it reads** — the
mutating acts because they mutate; re-checks because intent-before-read is
what makes chain position mean *looked after*, not merely *published after*.
Without it, a re-check could read a store, a deletion could then announce
itself and mutate, and the stale reading could publish later and lift a
refusal it never re-examined. The intent's **act kind** keeps the failure
modes distinct: an unmatched *mutating* intent is unsettled state; an
unmatched *re-check* intent is a look that never became a finding — no
mutation behind it, nothing unsettled, the act's failure (H4), not the
record's. A `url` re-check needs no intent: no boundary-mediated act mutates
a URL, so no URL location is ever unsettled, and remote evidence is
time-stamped data, not a race. The log amendments this requires — the intent
union, the §6 qualification reduction, `fulfills` construction, `L7`, and the
§9 ownership split — are tabled in §8.

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
  location **contested**, and a contested location is **blocked** (below) —
  the existential held-rule must never silently let `found` outvote
  `absent`. The repair is an act: a re-check that supersedes *every* standing
  head (the set-valued `supersedes` of §2) and records what is actually
  there.
- **A dangling predecessor is not an error.** A head whose `supersedes` names
  a record outside the enumerated coverage is still a head; the unseen tail
  is the §5 coverage bound doing its job.
- **An unsettled location is blocked, like a contested one.** A location is
  **unsettled** when a **mutating** holdings intent naming it is unmatched —
  or its qualification is **unresolved**, blocking as itself (§3) — under the
  log's reduction, and no **fulfilled** re-check intent for that location
  sits later in that root's chain: some boundary-mediated mutation has no
  recorded outcome, and nothing has demonstrably looked since. The intent's
  chain position — never a clock, and never mere publication order — is what
  puts the repair's *look* after the attempt (§3). Unsettled is contested's
  sibling — both name evidence in a state only an act can repair, and both
  make it the caller's problem instead of a silent guess.

**Blocking is scoped to what depends on it; corruption is not.** A contested
or unsettled location is **blocked**: its records leave the active set, and
the location enters the projection's **blocked set** — an output reported,
and receipt-committed (§5), beside the active set. The **dataset-scoped
adapter** (§5 step 3) then decides dependency: a dataset answer **refuses**
iff any record at a blocked location would enter its tuple by a §5 join —
the joins run over the blocked records exactly to answer that question —
and every other dataset proceeds. One crashed act at an unclaimed
locator therefore blocks nothing but itself — refusing the whole coverage
for it would hand any single stray conflict a denial of every dataset the
coverage serves. Contested and unsettled are **honest operation** —
concurrent audits fork, processes crash — and honest operation scopes. A
presented **cycle** is not: no act constructs a record naming a successor's
identity, so a cycle is corruption of the record set itself, and it keeps
refusing the **whole projection** (the checked invariant above).

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
   set** beside the **blocked set** (§4). Two consequences are stated rather
   than discovered: a record
   superseded only in a corpus *outside* the coverage reads active *within*
   it — the coverage declaration is what makes that a bounded, stated claim
   instead of a silent error; and a declared corpus that cannot be enumerated
   **refuses the whole projection** — a partial enumeration reported as a
   result would be the silent shrink the declaration exists to prevent. The
   enumeration also carries each covered corpus's **holdings intents with
   their qualification states** — matched, unmatched, and **unresolved as
   itself, never collapsed** (§3): the blocked set derives from them (§4).
   An intent outside the coverage is invisible exactly as its would-be
   fulfillment is — the same bounded claim, stated once.
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
   algorithm, same hex, or no join — with §2's construction constraint
   (`expected` shares its `found`'s algorithm) closing the one route around
   it: a head admitted by expectation carries a found digest commensurable
   with the declaration it joined, so every mismatch the seam reports
   compares digests under **one** algorithm. The false cross-algorithm
   mismatch — the bytes said to contradict a record nothing checked them
   against, the survey's own coverage error — is **unconstructible**, not
   merely avoided. The same commensurability gates the history join: a head
   enters through its superseded past only where its own found digest shares
   the declared digest's algorithm — a re-check under a different algorithm
   than its predecessor's contributes nothing there, and the resource reads
   `no-matching-observation-in-coverage`: true, in the checkable sense — no
   observation exists that can answer for it. The adapter also owns the
   blocked set's reach (§4): before answering a dataset, it runs the same
   three joins over each blocked location's records, and a hit **refuses
   that dataset's answer** — blocked evidence never enters a tuple, and
   never silently vanishes from one either.
4. The projection also yields a **derivation receipt**, on the contract world
   §5 and `W8a` already set for enumerations that feed belief — adopted
   whole, not paraphrased. The receipt names the **exact corpus-state
   identities** enumerated (a receipt naming corpora rather than states is
   **`malformed`**) — and, because the reducer now reads each corpus's log
   for unmatched holdings intents (§4), **the log chain head under which each
   corpus was enumerated, captured coherently with its state**. The state
   identity is over node content, not the log — world addressing's own
   boundary — so two corpora in identical states can carry different chain
   heads and therefore different unsettled sets; a receipt silent on the
   heads names inputs that do not determine its output. It also names the
   **exact rule binding**: the fixture-bound
   identity of the **active-set reducer** — steps 1 and 2 whole: enumeration,
   the supersession walk, coalescing, the contested- and unsettled-blocking,
   and the cycle-refusal; the rule a recency-bearing successor would replace
   (§4) — *together with* the content identity of the implementation
   that ran, resolved from the held store — a bare identity or version
   string is `malformed`, and an implementation that fails its fixtures **is
   not that rule**. Validating a receipt is re-running: resolve the binding,
   re-reduce the named states under the named heads, and land in the
   vocabulary the corpus already has — **`validated`** (the named active and blocked sets reproduce), **`refuted`**
   (it does not), **`unresolvable`** (a named corpus state, a named
   chain head, or the implementation is not resolvable here — a
   computability state, never an epistemic one, and never reported as
   refutation), **`malformed`** (the
   receipt could never be checked by anyone). A receipt naming coverage and
   output alone would validate nothing — a wrong or incomplete reduction
   could sign a perfectly consistent one — which is `H3`'s second arm (§6).

**The receipt's claim ends at the reducer's output — the active set and the
blocked set.** The dataset-scoped adapter
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

*Sabotage, first arm:* back-fill `found` records from a directory listing,
copying each declared digest into a record without hashing anything. Every
banked arm, exercised at the derivation seam, passes — the derivation *does*
read records, so `G9`'s path-exists arm is satisfied — and the
content-addressing guarantee is void one layer up: the path-exists predicate
has been laundered through the record store. Creation is the unowned half of
the record's lifecycle exactly as promotion was the unowned transition before
`G9`, and H1 owns it. *Sabotage, second arm:* hash a store path outside the
consistent-read boundary, mid-replacement. The mixed stream mints `found`
with a digest **no stable store state ever held** — or the transient gap
between a remove and a write mints a false `absent` — and every banked row
passes: a real act really dereferenced, and no other row speaks to what a
look must hold still. H1 reaches it because an observation of no stable
state established nothing; the boundary (§3) is what makes "established" a
checkable word.

> **H2 — supersession is by explicit reference, per location, over a checked
> DAG, and a contested or unsettled location is blocked.** Active-ness is
> resolved by walking each canonical location's `supersedes` graph from its
> heads, with acyclicity validated as an **admissibility invariant** on every
> walk (ρA9's discipline). No derivation orders records by `observed_at`; no
> record supersedes across locations; agreeing heads coalesce; **disagreeing
> heads block the location** rather than letting any outcome win; a mutating
> intent left unmatched — or **qualification-unresolved, blocking as
> itself** — leaves its location unsettled and blocked until a later
> fulfilled re-check intent answers (§4); and a blocked location refuses
> exactly the dataset answers that depend on it, never fewer.

*Sabotage, first arm:* resolve "current" by latest timestamp. Every banked
row passes — none speaks to ordering — and active-ness now moves with clock
skew between observers: two records, neither superseding the other, flip
precedence with no node recorded, which is admission changing because of a
clock, the act-bound violation in its subtlest form. *Sabotage, second arm:*
on disagreeing heads — an active `found` beside an active `absent` — let the
existential held-rule quietly count the `found`. Every banked row passes, and
a location whose own evidence is in open conflict promotes a dataset as if it
were not; H2's blocking is what makes the conflict the problem of exactly the
answers that depend on it, instead of a silent vote. *Sabotage, third arm:* skip the acyclicity check on the
strength of the hash-fixpoint argument — the argument ρA9 already found
invalid once. A crafted record set presenting a cycle now hangs the walk or
silently drops the location, whichever the traversal happens to do; every
banked row passes either way, and H2 alone demands the check that refuses it.
*Sabotage, fourth arm:* enumerate the intents faithfully and **ignore them in
the walk**. Every act creates its intent, so H4's third arm passes; the DAG
is clean and no heads disagree, so H2's other arms pass; and H3 cannot see it
either — a receipt faithfully naming a reducer that ignores intents validates
that reducer's every run. The crash window H4 closes from the act's side
reopens from the reducer's: a mutation with no recorded outcome blocks
nothing, and the stale `found` it may have orphaned promotes as if the
attempt never happened. The same arm covers the softer collapse: resolve an
**unreadable** fulfillment pointer to either resolved state — read as
qualifying, it settles a location no evidence settled; read as unmatched, it
misstates what is known — where the log's reduction says unresolved proves
nothing and must block as itself. The blocking is a guarantee only because
this arm owns it.

> **H3 — the derivation refuses an undeclared coverage, and its receipt is
> checkable.** Every heldness answer names the corpus states **and log chain
> heads** it enumerated and the rule that reduced them; "whatever is checked
> out" is not a coverage, and a receipt the named rule over the named inputs
> does not reproduce is a defect, not a disagreement.

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
**`malformed`**, refused rather than trusted. *Sabotage, third arm:* name the
corpus states exactly and read the log heads **ambiently** — re-reduce under
whatever chains are present at re-run. The state identities match (the state
identity is over node content, not the log), the reduction reproduces on
every day the chains happen to agree, and on the day a chain gained an
unmatched intent the same receipt flips verdict with no named input changed —
a receipt whose named inputs do not determine its output. Committing each
coherently captured head is what makes the unsettled set part of the claim
instead of ambient state.

> **H4 — no silent act, and no laundered non-answer.** An act records every
> outcome it **established** — `found`, `found` with an unexpected digest,
> `absent` — and an act that established an outcome but cannot record it
> **fails**; it does not report transiently and drop the record. An
> inconclusive attempt records **no observation**: it reports through the
> act's own channel (`byte-locator-untested`, `retrieval-failed`) and never
> mints `absent`. A mutating act runs inside its intent–fulfillment ordering
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
| tamper-evident log design | five sites, one amendment. **§3's `intent` union**: "the one consumer named today is the assessment-run intent" gains the **holdings intent**, appended by every store-dereferencing act — mutating or re-check — before it acts (§3 here); payload: canonical location, act kind, boundary-minted `event_token` (reused per the log's not-a-second-attempt-id rule), actor. **§6's qualification reduction**: a qualifying fulfillment of a holdings intent is a committed registration publishing a holdings observation for the intent's location carrying its `event_token`, under the same reduction — a non-qualifying pointer never matches, an unresolved one proves nothing. **`fulfills` construction**: the boundary constructs the link from its own holdings intent; no caller-supplied path — the rule restated, not relaxed. **`L7`**: "intent claims are exactly as wide as stated" now quantifies over both intent kinds, its arms instantiated for the holdings shape — a wrong-location observation, a wrong token, or a publication creating no observation each **fails qualification**; a kill between intent append and mutation reads attempt-without-recorded-outcome, exactly as stated. **§9's ownership split**: the science-side obligations gain the boundary writing holdings intents and constructing their `fulfills`, on the `atoms` intent API as built — `atoms` itself changes nothing |
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
