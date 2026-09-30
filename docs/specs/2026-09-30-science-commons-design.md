# Science commons — design

**Date:** 2026-09-30
**Status:** draft for user review. Task `sci-fe8522`.
**Scope:** how published science is shared, found, trusted, reproduced,
changed and preserved across installations of verifiably, and what a
*commons* is in that model. The kernel has ruled that publishing mints an
immutable corpus and that a commons is a world whose operator adopts many
publications (layer §6). This document settles what the kernel left to the
surface: the roles a participant can play; the three separate decisions a
reader makes about other people's work; the identity boundary below which
nothing is authenticated; how mirrors and provider lists distribute without a
central registry; how overlapping publications, retirement and pinned
dependencies coexist; how a fork is attributed without a second lineage; how
a commons catalogs, explains and preserves; how a corpus is laid out at a git
remote and a Zenodo deposit; and the milestones, the first of which is one
complete collaboration between two installations. It designs no command
declaration in detail, no query-language change and no kernel change; kernel
preconditions are named in §11 and filed to `beliefs`.

**Inherits:** the user/autonomy layer design (`beliefs`
`docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md`) §2
decision 5 and §6 in full; the publication records design
(`2026-09-22-publication-records-design.md`) decisions 9 and 10; the publish
act remote design (`2026-09-26-publish-act-remote-design.md`) §2 decision 1
and §13; the session mounts design (`2026-09-27-session-mounts-design.md`);
the projects, corpora and workspaces design
(`docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md`) §3 and
§8; the coordination command set design
(`docs/specs/2026-09-24-coordination-command-set-design.md`) §6; and the
command framework design (`docs/specs/2026-08-31-command-framework-design.md`)
§3.3, §4.4 and §9.1. Terms used without definition — world, corpus, view,
epoch, closure, publication marker, publication binding, head artifact,
`ReplicaOf`, holdings observation, coreference attestation, `Refused(reason)`
— are those documents'.

**Predecessor:** the `science-commons` prototype store (datasets with
recipes, 274 papers, topics, themes; promotion, overlays, peers and registry
sync). The world-addressing design retired that model: "three mechanisms did
not produce one world; they produced overlays beside local copies". This
design keeps what the prototype was *for* — curated, citable, reusable
science that more than one project can build on — and none of its mechanism.
Its content is input to what a commons must be able to hold, not a migration
target (§13).

## 1. Problem

One installation can publish a view to a private directory or a remote and
adopt a published corpus whole, read-only (layer §6.1–6.3). Nothing yet says
how a second installation finds that publication, decides whether to trust
it, fetches it when the origin is down, reads it beside an update that
shares half its records, builds on it without losing attribution, or returns
a reproduction to the publisher. And nothing says what a *commons* does
beyond adopting: whether it republishes, what it promises to preserve, how it
explains why something is in its collection, and how a reader tells the
commons's recommendation from the original author's evidence.

The prototype answered these with canonical owners, promotion and overlays,
and failed. The kernel answers the storage half — identity is content, a
publication is immutable, a recipient verifies the traveled chain — and
leaves the sharing half open with a list of gaps: who may write, retiring a
superseded corpus, overlapping publications, observer distribution, and the
reciprocal return of a recipient's verification (layer §6.5; remote §13).

This document is the sharing half.

## 2. Success criteria

Two perspectives, carried verbatim into every milestone's acceptance:

- **User:** find useful work, understand why I trust it, reproduce or change
  it, and share my contribution.
- **Commons:** curate a collection, explain inclusion decisions, preserve
  what I promise to preserve, and help others discover it.

## 3. Vocabulary and roles

**A commons is an ordinary participant.** Every participant runs one
installation: a world with one write root and N read mounts, exactly as the
session mounts design opens it. The roles below differ only in what a
participant chooses to publish and hold; no role has a capability another
lacks.

| term | meaning |
|---|---|
| **publication** | an immutable corpus minted by `publish(view, destination)`, identified by its `corpus_id` and head artifact, carrying one `publication` marker (layer §6.1). Its revisions chain by `supersedes`. |
| **location** | a remote destination URL under the holdings `url` canonicalization (publication records decision 9), or a local path. A publication may be held at several locations; its identity is its verified contents, never a location. |
| **provider** | a world id bound, in a reader's configuration, to the locations the reader accepts *new* publications of that world from (§4.4). |
| **mirror** | any location holding a publication the reader has already pinned. A mirror is not a provider: it serves bytes whose identity is known. |
| **pin** | `(corpus_id, marker identity, head artifact content identity)`: what a reader holds or intends to hold, and where the pin came from (§4.5). |
| **catalog** | an epoch artifact a commons publishes: the publications it holds, with locations, observed holdings and inclusion reasons (§7.2). |
| **inclusion record** | a record the commons authors in its own write root: why a publication is in its collection, and the relations the commons curates between publications (§7.3). |
| **provider list** | an epoch artifact a participant publishes: the providers it binds, for others to import at a pinned revision (§7.4). |
| **user** | a participant who publishes their own views and adopts others' publications. |
| **host** | a participant whose collection is offered to others: they publish a catalog, and may preserve copies. The predecessor's "commons" is a host. |
| **aggregator** | a host who follows other hosts' catalogs and publishes a merged catalog. Not a third kind of thing. |

## 4. Decisions

### 4.1 Federated pull over hosted corpora

Every publisher hosts their published corpora at locations they control. A
reader pulls. There is no service between them: discovery is reading a
catalog, which is itself a publication; trust is the reader's configuration;
aggregation is a host following other hosts.

**Rejected:** a central registry service that publishers push to and readers
query. It recreates the predecessor's canonical owner, is a single point of
failure, and contradicts the kernel's "nothing promotes, overlays or
rewrites". **Rejected for now:** peer-to-peer discovery over a DHT with
signed entries, and any ledger. A ledger adds consensus machinery before
there is a requirement that everyone agree on one global catalog, and a DHT
needs signing the kernel lacks. The useful idea in both — locating identical
content across many holders — is §4.5's mirrors. Locations are already
locators and a catalog is already data, so a peer transport plugs into the
kernel's transport seam later without changing this design.

### 4.2 A commons catalogs; it does not republish

A host's catalog names other people's publications by origin world,
`corpus_id` and marker. A reader who wants one adopts the *origin corpus*,
from any location that holds it. The host publishes, from its own write root,
only records it authored: inclusion records, coreference attestations,
datasets and sources it originates, and its own assessments.

Consequence: original evidence stays in the author's corpus; a verification
stays in the verifier's corpus; the host's endorsement is its inclusion
record. Three artifacts, three authors, and a reader's three decisions (§4.3)
land on three different things.

The one legitimate carry is closure. An author whose assessment names an
adopted dataset must select that dataset into their publication or be
`Refused(closure-incomplete)` (layer §6.1). Datasets, sources and specs are
content-addressed, so a record carried this way is the same record wherever
it appears; §4.7 says how two corpora holding it coexist, and §4.8 says how
its origin stays resolvable.

**Rejected:** a host republishing adopted records under its own marker. The
marker's `published_from` would then name the host, and a reader's accept
policy (§4.3) could not tell the author's evidence from the host's
endorsement without a second attribution mechanism.

### 4.3 Three local decisions: follow, hold, accept

A reader makes three separate decisions about other people's work, each its
own configuration list, none implying another:

| decision | question | affects | where |
|---|---|---|---|
| **follow** | which catalogs and provider lists do I read? | what I can find | `[[follow]]` |
| **hold** | which publications do I adopt, and which data bytes do I fetch? | what I can read and run | `corpus_roots` (adopted corpora are read mounts) and `[holdings]` |
| **accept** | whose verification evidence does my belief policy count? | belief | `accept` |

Trusting a host to recommend interesting work says nothing about its
verification results, and trusting it to preserve bytes says nothing about
its scientific judgment. A shortcut that sets several at once (a "trust this
host" command that follows, holds and accepts) is permitted as a surface
convenience only if it writes the three lists visibly; no stored grade
collapses them.

Adopted corpora enter the reader's world index like any other mount, so
without `accept` an adopted assessment would reach belief as the reader's own
do. `accept` is therefore not a preference: it is the rule that keeps
"believe nothing until we have re-analyzed the data ourselves" true after
adoption. §9 specifies where it applies.

### 4.4 The identity boundary

Five layers, from what is verified to what is merely claimed:

1. **Integrity.** The corpus's chain and head artifact, verified at
   `admit_arrival`. Establishes that these bytes are the corpus the head
   names, unchanged since it was sealed. Nothing more.
2. **World identity.** The marker's `published_from.world_id`. A claim the
   publisher's kernel wrote. A self-consistent chain does not prove who
   controls the world it names.
3. **Provider binding.** The reader's configuration binds a world id to
   approved locations: hosting accounts the reader has decided speak for
   that world. A **new** publication for world *A* is accepted into the
   reader's pins only when fetched from a location bound to *A*. This is the
   authentication the design has today, and it is explicitly the host's
   account controls standing in for a key.
4. **Pinned content.** A publication the reader has already pinned may be
   fetched from any location (§4.5). Identity is the verified contents.
5. **Attribution and description.** The world of the containing publication
   and the per-record origin (§4.8) are the publisher's provenance claims. A
   catalog's descriptions and inclusion reasons are the cataloguer's claims.
   None of these is verified by admission; admission catches integrity
   failures only, so "a catalog that lies is caught at adoption" is true for
   bytes and false for attributions.

**A catalog pin authenticates the catalog's recommendation, not the claimed
origin.** When followed host *C*'s catalog names publication *P* from world
*A*, the reader learns that *C* recommends these exact bytes. It does not
learn that *A* published them. Fetching *P* from a mirror on the strength of
*C*'s pin is fine (§4.5). Counting *P*'s verification evidence under
`accept(A)` is not: that needs a pin of *P* obtained from a location bound to
*A* (§9). Delegated authentication — *C* vouching for *A* — is deferred to
signing.

**Signing** replaces layer 3 with key binding: a world's key signs its head
artifacts, and a provider binding becomes a key rather than a location.
This design fixes only that the head artifact is the signed object and that
a pin's source records whether it was location-bound or key-bound. The
signature format is chosen when it is implemented, not reserved as an empty
field now.

### 4.5 Mirrors, and identity by contents

A publication may be held at several locations. A catalog entry lists every
location the cataloguer has observed to hold it, including the host's own
storage when it preserves a copy. A reader fetching a pinned publication
tries locations in its own order; whichever answers, `restore_root` verifies
the chain against the pinned head artifact identity, so a mirror cannot
substitute content.

Provenance survives the mirror: the holdings observation records the
location fetched from and when; the registry's `ReplicaOf` provenance
records the origin marker; the pin records where the pin came from (a bound
provider, or a followed catalog or list, by artifact identity). Reading any
adopted corpus, the reader can answer "who published this, who told me
about it, and where did the bytes come from" from three separate records.

### 4.6 Provider lists are versioned publications, imported explicitly

A participant's provider bindings are exportable as a provider-list artifact
(§7.4), an ordinary epoch artifact in an ordinary publication. A reader
imports one by pinning a revision: the entries are copied into the reader's
`[[provider]]` table with `via` naming the list's publication marker.

- An imported binding is a *candidate* for layer 3. It binds nothing until
  the reader confirms it, because a location-bound identity that arrived
  through another party is exactly the delegation §4.4 defers.
- `via` is a set, not a value. A binding recommended by several lists keeps
  every path, so a reader sees that two independent hosts name the same
  location for *A*, or that only one does.
- Imports are pinned revisions. Subscriptions — following a list's
  `supersedes` chain automatically — and bounded transitive traversal come
  after milestone 2 and reuse the same pinned import as their unit.

### 4.7 Overlapping publications

Every republication of one view shares records with its predecessor, and
any publication carrying closure (§4.2) shares content-addressed records
with its sources. The kernel's world index refuses one address held in two
corpora (`duplicate-location`; remote §13 item 3), which today prevents a
recipient from building an epoch after a second publication arrives. This
is milestone 1's blocker, not a later concern.

The rules this design requires of the kernel's resolution, which is
`beliefs-81367e`'s to make:

1. **Identical records contribute once.** One address held in several
   corpora with the same content identity is one record in the world index,
   with every holding corpus listed. Belief already does this at its own
   level: identity-equal assessments collapse to one vertex.
2. **Conflicting content under one address refuses explicitly.** Two corpora
   holding one address with different content is a contradiction the index
   names, never resolved by corpus order. Belief already refuses an
   identity-equal, facet-disagreeing pair.
3. **Competing assessments stay distinct.** Two analyses of one proposition
   have different `(spec, run, proposition)` identities and are two vertices.
   Nothing in deduplication merges them.

Deduplication by `corpus_id` alone is insufficient — two different corpora
legitimately hold the same records — and is rejected as the aggregator's
rule; an aggregator dedupes catalog *entries* by `corpus_id` and world
*records* by content identity.

### 4.8 Forking preserves a dependency graph the kernel already derives

A derived analysis pins, through its run, the original's dataset
identities, `analysis-spec`, code identity, environment digest and output
digests. Ancestry is the kernel's lineage — `derived_from` as a view over
`produces ∘ transforms`, "stored nowhere, and no API accepts an authored
ancestry list" — and this design adds no second source of scientific
dependency.

What the publication level adds is **attribution**, and it must be
resolvable per record. The `publication` marker gains `carries`: for every
selected record the publisher's world holds in an *adopted* corpus rather
than in a corpus it wrote, one entry `(record address, origin corpus_id,
origin marker identity)`. Recovery is mechanical at publish: the publisher's
registry knows which corpus holds each selected record; if that corpus was
admitted `ReplicaOf`, its marker is the origin, **unless that corpus's own
marker already carries the record**, in which case the earlier entry is
copied forward. So a record that travels *A1 → B → C* is attributed to *A1*
in *C*'s marker, not to *B*. A flat list of upstream publications is
rejected: it says which publications were drawn on, not which record came
from which. `carries` is a provenance claim by the publisher (§4.4 layer 5);
naming an origin is not proof of authorship.

Two acts that look alike are different:

- **Revising my publication** supersedes it: same view, same destination,
  a new corpus whose marker names the predecessor.
- **Deriving from yours** mints a new view in my world whose publication
  carries your records where closure requires and names them in `carries`.
  Your publication is never superseded by mine.

Two analyses of one proposition are found together by the proposition's
identity. Related but different propositions need an explicit relation,
which a host curates in an inclusion record with a reason (§7.3). No new
kernel edge is proposed.

### 4.9 No votes

The Stack Overflow shape — a proposition is the question, assessments are
alternative answers — is kept for discovery. "Verifications are votes" is
rejected. In the kernel, verification is an admission gate, and independence
between assessments is certified pairwise over the data roots their runs
observed, so ten reproductions over one dataset are one line of evidence,
not ten. A catalog shows, for an assessment, its reproducibility (which
verifications name it and from which worlds), its assumptions (the spec it
ran) and the conflicting evidence (directional assessments of the same
proposition with the opposite sign), as separate facts. A host may
recommend an analysis as its best current guess; nothing in the model is a
globally accepted answer.

### 4.10 Hosting does not define publication semantics

GitHub is the first destination and Zenodo the archival one (§8), and
neither's behavior is the model's:

- Git history can be rewritten and a repository deleted. Continued
  availability is a **preservation promise** made by whoever holds a copy,
  stated in a catalog entry, never a property of the origin.
- Zenodo's version-per-publication mapping is this design's convention.
  Zenodo permits some file corrections under one DOI, so the head artifact
  and content digests remain the truth and a DOI is a location.
- Whether a Zenodo deposit carries the corpus as individual files or as one
  archive preserving the internal layout is the transport's choice, decided
  against Zenodo's file limits at implementation. Either must satisfy the
  seam's `listing` contract — names mapped to SHA-256 of remote bytes — so
  an archive transport lists the archive's members.
- A `commit` step on the transport seam (draft, then publish, after the
  kernel's completeness check) is a hypothesis, not a decision. Milestone 3
  first tests whether a resumable adapter reconciles draft creation,
  publication and uncertain responses inside `push` and `listing` as they
  are.

### 4.11 Availability and redistribution are separate

A dataset in a catalog entry carries two independent facts: **observed
locations**, each with the observation's time and outcome (`found
<digest>` or `absent`), and **redistribution status** (`redistributable`,
`not-redistributable`, `unknown`), taken from the dataset record's declared
terms when it declares any and otherwise the cataloguer's claim, marked as
such. Bytes may be held locally and not redistributable; the two never
collapse into one state.

A preservation promise names what it covers, separately: the **publication
records**, the **data** (holdings of selected datasets) and the **execution
dependencies** (the workspace commit and environment the reproducible level
names). A host may promise any subset and the catalog says which.

Holdings policy is the holder's, independent of provider: `records-only`,
`fetch` up to a size bound, or `fetch` everything redistributable. A
publish's dry run reports the inputs the chosen destination will not carry,
and the catalog entry repeats each dataset's facts.

## 5. The user's path

Success is: find useful work, understand why I trust it, reproduce or change
it, share my contribution. Each step names the surface command it needs;
declarations follow the framework's write classes and are the plan's.

1. **Find.** `follow <location>` pins a catalog or provider list at its
   current revision. `find` reads followed catalogs: by proposition, term,
   dataset identity or world. Without any catalog (milestone 1), a user
   adopts by explicit location.
2. **Understand why I trust it.** `show <pin>` answers the three questions
   of §4.5 — who published, who recommended, where the bytes came from — and
   whether the world is a bound provider, whether it is accepted, and what
   the verification and independence picture is under the user's accept
   policy.
3. **Hold.** `adopt <location or pin>` fetches, verifies and admits a
   publication as a read mount (`restore_root`, then `admit_arrival`), records
   the pin's source, and applies the holdings policy to its datasets. `adopt`
   of a successor also runs §10's retirement. A new publication of an unbound
   world refuses `provider-unbound` naming the world and the location, and
   `provider bind` is the remedy.
4. **Reproduce or change.** Reproduction is the existing `verify` path over
   an adopted assessment; the verification lands in the user's write root.
   Changing is: fork the workspace at the commit the reproducible publication
   names, author a spec whose inputs name the adopted datasets by identity,
   run, assess. The kernel's cross-corpus dataset input work
   (`beliefs-9ce6e4`) is what lets an assessment in the write root name a
   dataset a mount declares.
5. **Share.** `publish <view> --to <destination>` with a dry run that shows
   the selection, the closure, `carries` (§4.8), and the inputs the
   destination will not carry. Returning a reproduction to its publisher is
   the publisher adopting the user's publication (layer §6.5); nothing here
   shortcuts that.

## 6. The commons's path

Success is: curate a collection, explain inclusion decisions, preserve what I
promise to preserve, help others discover it.

1. **Curate.** The host adopts what it chooses to hold, exactly as a user
   does. Its collection *is* its set of pins.
2. **Explain.** For each held publication the host mints an inclusion record
   (§7.3) in its write root: the reason, the curated relations, and the
   preservation promise it makes for that entry.
3. **Preserve.** Under its holdings policy the host fetches the bytes it
   promised and, for records, keeps its own copy of each corpus at a location
   it controls. The catalog entry lists that location.
4. **Help others discover.** `catalog` builds the catalog artifact (§7.2) from
   pins, inclusion records and holdings observations, and publishes it as an
   epoch artifact of the host's world. `providers export` publishes the
   provider list (§7.4). An aggregator follows other hosts' catalogs and its
   `catalog` merges them: entries keep their origin world, marker and
   observed locations, dedupe by `corpus_id`, and record which followed
   catalog contributed each entry.

## 7. Records and artifacts

### 7.1 Publication marker: `carries`

A kernel addition (§11): `carries`, a list of `[record address, origin
corpus_id, origin marker uid]`, strictly ascending by address, possibly
empty, computed at publish as §4.8 states and part of the marker's identity.

### 7.2 Catalog artifact

An epoch artifact, `catalog.v1`, published by a host's world. One entry per
held publication:

| field | content |
|---|---|
| `world` | the marker's `published_from.world_id` |
| `corpus_id`, `marker`, `artifact` | the pin |
| `view` | the marker's view address |
| `supersedes` | the marker's `supersedes_markers` |
| `superseded_by` | markers the host holds that name this one, or empty |
| `locations` | every location observed to hold the corpus, each with observation time and outcome; the host's own copy included when it holds one |
| `pin_source` | how the host obtained the pin: `provider` (with the bound location) or `catalog` (with the artifact identity) |
| `kinds` | record kinds and counts in the corpus |
| `propositions` | the proposition identities the corpus's assessments assess |
| `datasets` | per selected dataset: identity, observed locations with times and outcomes, redistribution status and its basis (§4.11) |
| `inclusion` | the host's inclusion record address (§7.3) |
| `preserves` | the subset of {records, data, execution} the host promises for this entry |
| `contributed_by` | for an aggregator, the followed catalog artifact identity the entry came from; empty for the host's own pins |

Entries for retired publications remain, with `superseded_by` set, so a
reader can find a version an explicit pin or dependency needs (§10).

The catalog is not a world record and no view selects it. Science pushes it
to the host's container beside the corpora, at `catalog.v1/<artifact
identity>`, outside the kernel's publish act and outside the names the
kernel's `listing` check reads; `follow` fetches it by location and verifies
the artifact identity. The provider list (§7.4) travels the same way.

### 7.3 Inclusion record

A coordination record kind in the science coordination contract, addressed
to the host's project, belief-inert like every coordination kind:

- `includes`: the pin.
- `reason`: prose.
- `relates`: zero or more `(pin, relation, reason)` where `relation` is a
  closed small set — `alternative-analysis-of` (same proposition, different
  spec), `addresses-related-question`, `supersedes-in-our-view` — curated
  claims of the host, never a kernel edge.
- `preserves`: the promise, as §7.2.
- Revisable like any coordination record; the catalog reads the tip.

### 7.4 Provider list artifact

An epoch artifact, `providers.v1`: one entry per binding — `world`,
`locations`, `bound_since`, and `via` (the set of list markers it was
imported from, empty for the host's direct bindings). It carries no accept
policy: a host's scientific acceptances are its own and are not offered for
import.

### 7.5 Configuration

Framework §9.1's file gains keys, all optional, with the loader's exact key
set rule:

```toml
[[provider]]                     # §4.4 layer 3
world = "<32-hex world id>"
locations = ["https://github.com/<org>/<repo>", "..."]
via = []                         # list markers that recommended it; empty when direct
confirmed = true                 # false for an imported candidate (§4.6)

[[follow]]                       # §4.3
artifact = "<64-hex artifact identity>"
kind = "catalog"                 # or "providers"
location = "..."

accept = ["<32-hex world id>", "..."]   # §9; empty means own world only

[holdings]                       # §4.11
policy = "records-only"          # or "fetch"
max_bytes = 0                    # with "fetch": 0 means no bound
```

Adopted corpora are `corpus_roots` entries as today. A pin's provenance
(§4.5) is registry state written by `adopt`, not configuration.

## 8. Hosting layouts and transports

The kernel lays a remote out as a container: `<corpus_id>/` holding the
corpus files and `<corpus_id>.head-artifact.v1` beside it
(`transport_files`). Both layouts keep that shape unchanged, so the kernel's
completeness check over `listing` applies as it is.

**Git remote.** One repository is one container and may hold every
publication a publisher sends there, from any view. A publish is one commit
adding a corpus directory and its head artifact. A superseded corpus may be
removed from the tree by a later commit; the history keeps it, and a reader
needing a retired revision fetches it by the commit the catalog or the
container's history names. Records are markdown, so a publication is
browsable on GitHub without an installation. The git transport implements
`push` as add, commit and push to the bound branch, idempotent because a
retry that finds the files present with matching digests commits nothing;
`listing` reads the remote tree. A missing intermediate (remote §13 item 2)
is fetched from the same container: it holds the whole chain unless the
publisher pruned it, in which case the catalog's other locations are tried.

**Zenodo deposit.** One deposit per publication, holding the corpus, its head
artifact and the holdings of every selected redistributable dataset. A
revision is a new version of the deposit, so the concept DOI stands for the
view at that destination and each version DOI is one corpus. The transport's
layout choice (files or archive) and the draft-to-publish reconciliation are
§4.10's milestone 3 questions.

**Any other container.** A plain directory served over HTTPS, an S3 bucket or
a peer transport is a transport implementing the same two methods. Nothing
above §8 changes per transport.

## 9. Belief under an accept policy

`accept` is applied **before** the kernel's verification lifecycle is
evaluated, and to every kind that lifecycle reads:

1. The verifier set is the reader's own world plus `accept`.
2. A record — assessment, verification, or a verification that supersedes
   another — counts toward belief only when the corpus holding it is
   **accepted**: its marker names a world in the verifier set **and** the
   reader's pin of that corpus came from a location bound to that world
   (§4.4). A corpus pinned through a followed catalog and fetched from a
   mirror is held, readable and citable, and not accepted until a pin from
   the origin's bound location confirms the same head artifact identity.
3. Applying the rule uniformly is what keeps it safe: an unaccepted
   publisher's failed verification cannot invalidate an accepted assessment,
   and an unaccepted superseding verification cannot suppress an accepted
   failure.
4. The reproducibility context that belief returns records the effective
   policy: the verifier set, each accepted corpus's pin source, and every
   record the policy excluded with its world. A belief answer therefore
   explains both the evidence considered and how it was selected.
5. Belief comparisons across installations (milestone 1) are made over the
   same pinned evidence and the same policy. Different selections can
   legitimately give different results, and the context is what shows why.

The kernel change is a verifier-set parameter on belief evaluation and the
policy in the context (§11). Science computes the set from configuration and
pin provenance.

## 10. Retirement, supersession and pinned dependencies

When `adopt` admits a successor:

1. The predecessor stays held and addressable. What was shared cannot be
   unshared, and the reader's own runs or other held publications may depend
   on it.
2. The **current** publication for `(view, destination)` advances only after
   admission succeeds and supersession resolves to one tip; a divergent
   sibling (`divergent-publication`) leaves the update unresolved, as does a
   missing intermediate.
3. The predecessor leaves the **default world index** only when nothing
   requires it: no explicit pin, no run in the reader's write root observing
   a dataset only it declares, no held publication whose `carries` names it.
   While something does, it stays indexed, which §4.7's rule 1 makes legal
   for the records it shares with its successor; the records the successor
   dropped remain readable from it.
4. A dependency-required predecessor is reported by `show`, so the reader
   knows why a retired revision is still in their index.

## 11. What `beliefs` must add, and what `science` builds

Kernel preconditions, each filed as a `beliefs` task after this spec's
review, with the milestone that needs it:

| precondition | milestone |
|---|---|
| overlapping publications in the world index under §4.7's three rules (`beliefs-81367e`) | 1 |
| recipient retirement with §10's index rule (remote §13 item 1) | 1 |
| `carries` on the publication marker (§7.1) | 1 |
| cross-corpus dataset inputs at assessment (`beliefs-9ce6e4`) | 1 |
| verifier-set parameter and policy in the reproducibility context (§9) | 2 |
| an `inclusion` coordination kind (§7.3), or a contract extension point for a surface-defined coordination kind | 2 |
| key-bound provider identity: signed head artifacts (§4.4) | 4 |
| view publication, so topics and themes can be shared (projects design §8.1 defers it) | 4 |

Science builds: the `publish` command with dry run; `adopt`, `show`,
`provider bind`, `follow`, `find`; the git transport; the catalog, inclusion
record and provider list; `catalog` and `providers export`; the holdings
policy; the accept-policy computation; the Zenodo transport.

## 12. Milestones

**1. One complete collaboration between two installations, over git.** Two
worlds — two hosts, or two installations on one machine — and one bound git
remote each; explicit locations, no catalog. *A* publishes a findings view;
*B* binds *A* as a provider, adopts, reproduces one assessment, forks the
workspace, changes one input, runs, assesses, publishes; *A* binds *B*,
adopts *B*'s publication; *A* publishes an update that drops one record; *B*
adopts the update. Three decisive cases, each a test:

- **overlap:** after *B* adopts *A*'s update, the records the two revisions
  share appear once in *B*'s index and contribute once to belief;
- **lineage:** *B*'s changed analysis is a distinct assessment with its own
  identity, its lineage reaches *A*'s dataset by identity, and *B*'s marker
  `carries` attributes the carried records to *A*'s first publication;
- **pinned derivation:** adopting *A*'s update does not make *B*'s derived
  analysis unreadable: the dropped record *B* depends on stays indexed from
  the retired revision, and `show` says why.

Belief on both sides is compared over the same pins and the same policy.

**2. A commons.** A host world with a catalog, inclusion records and a
provider list; a reader who follows it, adopts through it from a mirror,
imports its provider list as candidates, and sees the accept policy in a
belief context. Aggregation of two catalogs.

**3. Preservation.** The Zenodo transport, holdings policy, host copies of
records and bytes, and the preservation promise in catalog entries. The
`commit`-seam hypothesis is tested here.

**4. Hardening.** Signing, list subscriptions and bounded traversal, view
publication, and curated relations in `find`.

Milestone 1 is a `planned` task with its own implementation plan once the
four kernel preconditions in §11 land; milestones 2–4 are filed as goals
with `idea` children and scoped when milestone 1 closes.

## 13. Non-goals

No web application: GitHub renders the records. No migration of the
prototype's papers, topics, themes or dataset recipes; papers become
`source` records and source assertions when a project needs them, recipes
become workspaces with an `analysis-spec`, and topics and themes are views.
No promotion, overlay or canonical owner. No central service. No access
control beyond the host's account controls. No authored ancestry list. No
global reputation, vote or accepted answer.

## 14. Open questions

1. Whether a catalog should carry the cataloguer's *own* assessments'
   reproducibility summary or leave that entirely to `find` over held
   corpora. Deferred to milestone 2's plan.
2. The closed relation set of §7.3: whether three relations suffice or
   whether "same data, different proposition" needs one. Decided by
   milestone 2's first real catalog.
3. Whether a provider binding should expire or require re-confirmation when
   a location's account changes hands. Deferred to signing.
