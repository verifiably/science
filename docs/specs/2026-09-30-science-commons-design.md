# Science commons — design

**Date:** 2026-09-30
**Status:** draft for user review, revised after review rounds 1 to 6. Task
`sci-fe8522`.
**Scope:** how published science is shared, found, trusted, reproduced,
changed and preserved across installations of verifiably, and what a
*commons* is in that model. The kernel has ruled that publishing mints an
immutable corpus and that a commons is a world whose operator adopts many
publications (layer §6). This document settles what the kernel left to the
surface: the roles a participant can play; the three separate decisions a
reader makes about other people's work; the identity boundary below which
nothing is authenticated; how mirrors and provider lists distribute without a
central registry; what the surface requires of the kernel for overlapping
publications, retirement and pinned dependencies; how a fork is attributed
without a second lineage; how a commons catalogs, explains and preserves;
how a corpus is laid out at a git remote; and the milestones, the first of
which is one complete collaboration between two installations. It designs
no command declaration in detail, no query-language change and no kernel
change; kernel preconditions are requirements named in §11 and filed to
`beliefs`, and the framework amendment the sharing commands need is named
in §11 and made in the framework document.

**Inherits:** the user/autonomy layer design (`beliefs`
`docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md`) §2
decision 5 and §6 in full; the publication records design
(`2026-09-22-publication-records-design.md`) §3, §4 and decisions 3, 9 and
10; the publish act remote design (`2026-09-26-publish-act-remote-design.md`)
§2 decisions 1 and 10, §13 and §14; the session mounts design
(`2026-09-27-session-mounts-design.md`); the projects, corpora and
workspaces design (`docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md`)
§3 and §8; the coordination command set design
(`docs/specs/2026-09-24-coordination-command-set-design.md`) §6; and the
command framework design (`docs/specs/2026-08-31-command-framework-design.md`)
§3.3, §4.4 and §9.1. Terms used without definition — world, corpus, view,
epoch, closure, publication marker, publication binding, head artifact,
`ReplicaOf`, coreference attestation, `Refused(reason)` — are those
documents'. Where this document says **marker uid** it means the 32-hex uid
the contract's `supersedes_markers` pairs carry; where it says **artifact
identity** it means a 64-hex SHA-256 of bytes, the head artifact's or a
side artifact's (§7).

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
| **container** | what a location names: a directory-shaped remote holding `<corpus_id>/` roots and their `<corpus_id>.head-artifact.v1` siblings (`transport_files`), plus this design's side artifacts (§7). |
| **side artifact** | a file science places in a container beside the corpora: a catalog or a provider list. Identified by its artifact identity. Not a world record, not a publication, never selected by a view, invisible to the kernel's `listing` check (§7). |
| **pin** | `(corpus_id, marker uid, head artifact identity)` plus its **source** (where the reader learned it), its **fetch record** (§4.5), and a `keep` flag the reader sets, **before adopting a successor**, to hold that revision when the successor arrives (§10); retirement is irreversible, so a need discovered later cannot be met by re-adoption. A pin is what the reader holds or intends to hold. |
| **provider** | a world id bound, in the reader's sharing registry, to the locations the reader has confirmed speak for that world (§4.4). |
| **mirror** | any location holding a publication the reader has already pinned. A mirror is not a provider: it serves bytes whose identity is known. |
| **catalog** | a side artifact a host publishes: the publications it holds, with locations, observed holdings, and the host's inclusion decisions (§7.2). |
| **provider list** | a side artifact a participant publishes: the providers it binds, for others to import at a pinned artifact (§7.3). |
| **sharing registry** | science-owned state beside the operations root holding pins, provider bindings and follows, written only by the sharing commands (§7.4). |
| **user** | a participant who publishes their own views and adopts others' publications. |
| **host** | a participant whose collection is offered to others: they publish a catalog, and may preserve copies. The predecessor's "commons" is a host. |
| **aggregator** | a host who follows other hosts' catalogs and publishes a merged catalog. Not a third kind of thing. |

## 4. Decisions

### 4.1 Federated pull over hosted corpora

Every publisher hosts their published corpora at locations they control. A
reader pulls. There is no service between them: discovery is reading a
catalog a host placed in its container; trust is the reader's own registry;
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
`corpus_id` and marker uid. A reader who wants one adopts the *origin
corpus*, from any location that holds it. The host publishes, from its own
write root, only records it authored: coreference attestations, datasets
and sources it originates, and its own assessments. Its inclusion decisions
are content of its catalog (§7.2), because coordination records cannot be
selected into a publication (projects §8.1) and the endorsement must travel.

Consequence: original evidence stays in the author's corpus; a verification
stays in the verifier's corpus; the host's endorsement is its catalog entry.
Three artifacts, three authors, and a reader's three decisions (§4.3) land
on three different things.

The one legitimate carry is closure. An author whose assessment names an
adopted dataset must select that dataset into their publication or be
`Refused(closure-incomplete)` (layer §6.1). Datasets, sources and specs are
content-addressed, so a record carried this way is the same record wherever
it appears; §4.7 states what the surface requires of two corpora holding
it, and §4.8 says how its origin stays resolvable.

**Rejected:** a host republishing adopted records under its own marker. The
marker's `published_from` would then name the host, and a reader's accept
policy (§4.3) could not tell the author's evidence from the host's
endorsement without a second attribution mechanism.

### 4.3 Three local decisions: follow, hold, accept

A reader makes three separate decisions about other people's work, each its
own list, none implying another:

| decision | question | affects | where |
|---|---|---|---|
| **follow** | which catalogs and provider lists do I read? | what I can find | sharing registry, `follow` |
| **hold** | which publications do I adopt, and which data bytes do I fetch? | what I can read and run | sharing registry, `adopt`; configuration `[fetch]` |
| **accept** | whose verification evidence does my belief policy count? | belief | configuration `accept` |

Trusting a host to recommend interesting work says nothing about its
verification results, and trusting it to preserve bytes says nothing about
its scientific judgment. A shortcut that sets several at once (a "trust this
host" command that follows, holds and accepts) is permitted as a surface
convenience only if it writes the three places visibly; no stored grade
collapses them.

Adopted corpora enter the reader's world like any other mount, so without
`accept` an adopted assessment would reach belief as the reader's own do.
`accept` is therefore not a preference: it is the rule that keeps "believe
nothing until we have re-analyzed the data ourselves" true after adoption.
§9 specifies where it applies, and it is a milestone 1 precondition.

### 4.4 The identity boundary

Five layers, from what is verified to what is merely claimed:

1. **Integrity.** The corpus's chain and head artifact, verified at
   `restore_root`, then the marker layout at `admit_publication`.
   Establishes that these bytes are the corpus the head names, unchanged
   since it was sealed, and that it is a publication. Nothing more.
2. **World identity.** The marker's `published_from.world_id`. A claim the
   publisher's kernel wrote. A self-consistent chain does not prove who
   controls the world it names.
3. **Provider binding.** The reader's sharing registry binds a world id to
   locations the reader has confirmed speak for that world. Binding starts
   from one publication at a location: `provider bind <location>
   <corpus_id>` fetches and verifies that corpus (`restore_root` on a
   scratch copy, no admission), reports the world id its marker claims, and
   records nothing; `provider bind <location> <corpus_id> --world <id>`
   records the binding when the id the reader passes is the one the marker
   claims, and refuses `world-mismatch` otherwise. The confirmation is the
   argument, since the surface has no prompt. This is the authentication
   the design has today, and it is explicitly the host's account controls
   standing in for a key.
4. **Pinned content.** A publication the reader has pinned may be fetched
   from any location (§4.5). Identity is the verified contents. A pin is
   **origin-confirmed** when its source is a location bound to the marker's
   world, and **recommended** when its source is a followed catalog or
   list. Both may be held; only origin-confirmed pins are accepted (§9).
5. **Attribution and description.** The world of the containing publication
   and the per-record origin (§4.8) are the publisher's provenance claims. A
   catalog's descriptions and inclusion reasons are the cataloguer's claims.
   None of these is verified by admission; admission catches integrity
   failures only, so "a catalog that lies is caught at adoption" is true for
   bytes and false for attributions.

**A catalog pin authenticates the catalog's recommendation, not the claimed
origin.** When followed host *C*'s catalog names publication *P* from world
*A*, the reader learns that *C* recommends these exact bytes, and may hold
them from any location. It does not learn that *A* published them. Counting
*P*'s verification evidence under `accept(A)` needs an origin-confirmed pin
of *P* — the same `(corpus_id, marker uid, artifact identity)` learned from
a location bound to *A*. Delegated authentication — *C* vouching for *A* —
is deferred to signing.

**Signing** (milestone 4) replaces layer 3 with key binding. The constraint
milestone 1 must not break: a pin's source records whether it was
location-bound, so key-bound sources can be added beside it; and the head
artifact is the object a signature will cover, so nothing below it is
signed separately.

### 4.5 Mirrors, and identity by contents

A publication may be held at several locations. A catalog entry lists every
location the cataloguer has observed to hold it, including the host's own
storage when it preserves a copy. A reader fetching a pinned publication
tries locations in its own order; whichever answers, `restore_root` verifies
the chain against the pinned head artifact identity, so a mirror cannot
substitute content.

Provenance survives the mirror because three records answer three
questions: the corpus's own marker says who published it; the pin's source
says who told the reader about it; the pin's **fetch record** in the sharing
registry says which location the bytes came from, when, and that the
artifact identity verified. The kernel's registry adds `ReplicaOf` with the
parent `corpus_id`; the origin marker is read from the adopted corpus
itself, which holds it.

### 4.6 Provider lists are side artifacts, imported explicitly

A participant's provider bindings are exportable as a provider-list artifact
(§7.3) placed in its container. A reader imports one by pinning its artifact
identity: the entries are copied into the reader's sharing registry as
**candidate** bindings with `via` naming the list's artifact identity.

- A candidate binds nothing until the reader confirms it, because a
  location-bound identity that arrived through another party is exactly the
  delegation §4.4 defers.
- `via` is a set. A binding recommended by several lists keeps every path,
  so a reader sees that two independent hosts name the same location for
  *A*, or that only one does.
- Imports are pinned artifacts. A list names its predecessor's artifact
  identity, so revisions chain like publications do; following that chain
  automatically (subscription) and bounded transitive import come after
  milestone 2 and reuse the pinned import as their unit.

### 4.7 Overlapping publications: the requirement

Every republication of one view shares records with its predecessor, and
any publication carrying closure (§4.2) shares content-addressed records
with its sources. The kernel's world index refuses one address held in two
corpora (`duplicate-location`; remote §13 item 3), which today prevents a
recipient from building an epoch once two overlapping corpora are mounted.
This is a milestone 1 blocker (§12, part b), not a later concern.

What the surface requires, stated as outcomes and left to `beliefs-81367e`
to resolve in the index:

1. **Identical records contribute once.** One address held in several
   mounted corpora with the same content identity reads as one record.
   Belief already does this at its own level: identity-equal assessments
   collapse to one vertex.
2. **Conflicting content under one address refuses explicitly**, never
   resolved by corpus order. Belief already refuses an identity-equal,
   facet-disagreeing pair.
3. **Competing assessments stay distinct.** Two analyses of one proposition
   have different `(spec, run, proposition)` identities and are two
   vertices. Nothing in deduplication merges them.

Deduplication by `corpus_id` alone is insufficient — two different corpora
legitimately hold the same records. An aggregator dedupes catalog *entries*
by `corpus_id`; the kernel dedupes *records* by content identity.

### 4.8 Forking preserves a dependency graph the kernel already derives

A derived analysis pins, through its run, the original's dataset
identities, `analysis-spec`, code identity, environment digest and output
digests. Ancestry is the kernel's lineage — `derived_from` as a view over
`produces ∘ transforms`, "stored nowhere, and no API accepts an authored
ancestry list" — and this design adds no second source of scientific
dependency.

What the publication level adds is **attribution**, and it must be
resolvable per record. Requirement on the marker (§7.1): for every selected
record the publisher's world holds in an *adopted* corpus rather than in a
corpus it wrote, the marker carries `(record address, origin corpus_id,
origin marker uid)`. The origin is the adopted corpus's own marker, unless
that marker already carries the record, in which case the earlier entry is
copied forward. So a record that travels *A1 → B → C* is attributed to *A1*
in *C*'s marker, not to *B*. A flat list of upstream publications is
rejected: it says which publications were drawn on, not which record came
from which. The entries are a provenance claim by the publisher (§4.4 layer
5); naming an origin is not proof of authorship.

Two acts that look alike are different:

- **Revising my publication** supersedes it: same view, same destination,
  a new corpus whose marker names the predecessor.
- **Deriving from yours** mints a new view in my world whose publication
  carries your records where closure requires and attributes them to you.
  Your publication is never superseded by mine.

Two analyses of one proposition are found together by the proposition's
identity. Related but different propositions need an explicit relation,
which a host curates in its catalog entry with a reason (§7.2). No new
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
neither's behavior is the model's. The constraints milestone 1 must not
break:

- Continued availability is a **preservation promise** made by whoever
  holds a copy, stated in a catalog entry, never a property of the origin.
- A location is a canonical URL and the kernel's `listing` takes a location
  and a `corpus_id`: the seam enumerates one corpus, never a container. So
  every sharing command that reads a remote names a `corpus_id`, and the
  list of what a container holds is its catalog (§7.2), not a transport
  method. Milestone 1 passes corpus ids by hand. A container is **never
  pruned** in this design: a
  retired revision is fetched from the same container. A host that wants to
  shed old revisions moves them to another container it lists as a location.
- Content digests are the truth at every destination; a DOI is a location.

Zenodo's layout, its draft-to-publish reconciliation, and whether the
transport seam needs a `commit` step are milestone 3's questions, decided by
an experiment there, not here.

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

Fetch policy is the holder's, independent of provider: `records-only`, or
`fetch` with an optional byte bound over redistributable datasets. A
publish's dry run reports the inputs the chosen destination will not carry;
a catalog entry repeats each dataset's facts. Milestone 1 needs `fetch`:
a collaborator cannot run or verify over a mount's dataset without its
bytes (§5 step 4). `records-only` is a host's choice, not a collaborator's.

## 5. The user's path

Success is: find useful work, understand why I trust it, reproduce or change
it, share my contribution. Each step names the surface command it needs;
declarations follow the framework's write classes, extended as §11 says.

1. **Find.** `follow <location>` pins the catalog or provider list at that
   location by artifact identity. `find` reads followed catalogs: by
   proposition, term, dataset identity or world. Without any catalog
   (milestone 1), a user adopts by explicit location.
2. **Understand why I trust it.** `show <pin>` answers §4.5's three
   questions, says whether the pin is origin-confirmed or recommended,
   whether the world is accepted, and what the verification and
   independence picture is under the user's accept policy.
3. **Hold.** `adopt <location> <corpus_id>` fetches, verifies and admits a
   publication (`restore_root`, then `admit_publication`), records the pin
   with its source and fetch record, and marks it **mounted** in the sharing
   registry. A session's mounts are fixed at open (session mounts design
   decision 3), so the mount takes effect at the next session open, and
   `adopt` says so; the epoch that covers the new corpus is captured at that
   open. Until then the corpus is live and uncovered, so `publish` refuses
   `selection-incomplete` naming it; `adopt`'s report says this too, and the
   remedy is to reopen. A pin needs a source: a bound provider for that location, or a
   followed catalog naming the corpus. Neither present, `adopt` refuses
   `pin-unsourced` naming the world the marker claims and the two remedies,
   `provider bind` and `follow`. `adopt` of a successor also runs §10's
   retirement.
4. **Reproduce or change.** Reproduction is the existing `verify` path over
   an adopted assessment; the verification lands in the user's write root.
   Changing is: obtain the workspace at the revision the publisher ran,
   author a spec whose inputs name the adopted datasets by identity, run,
   assess. **The workspace revision has no carrier in the kernel today.** A
   marker names no repository or commit; a run's recipe carries the code
   identity and the environment identity, which is what a reproduction is
   checked against. So in milestone 1 the execution inputs — repository
   location, commit, and the environment bundle's location — are supplied
   beside the publication, out of band. They are only how the reader
   obtains the materials; the check is the kernel's existing recipe
   validation on the replay run, which compares the materials against the
   recipe's own identities — the code identity of the bundle built from
   the workspace and the environment identity of the bundle used — and
   refuses as it does today. This design adds no comparison of its own: a
   digest of the rendered workflow is not the code identity, and inventing
   a parallel check would let the two disagree. From
   milestone 2 the catalog entry carries `execution` locators per run
   (§7.2), the cataloguer's claim, checked the same way. Whether the marker
   itself should carry a workspace locator is filed to `beliefs` as an open
   question, not required here. Three science changes and one kernel change make
   this possible and are in §11: `fetch <dataset>` acquires the bytes of a
   dataset a mount declares into the user's store and records the holdings
   observation there, composed from the holdings boundary's `look` and the
   store write, **never** from the kernel's `acquire` act, which mints a
   dataset node and would redeclare the mount's content-addressed dataset
   (observing needs no write access to the dataset's home, and nothing is
   redeclared); `verify`, `run` and `assess` resolve
   datasets, and the assessment, run, spec and proposition they name, over
   the session's mounts, not the write root alone; and the kernel admits an
   assessment whose run observed a mount's dataset (`beliefs-9ce6e4`).
5. **Share.** `publish <view> --to <destination>` with a dry run that shows
   the selection, the closure, the attribution entries (§4.8), and the
   inputs the destination will not carry. Returning a reproduction to its
   publisher is the publisher adopting the user's publication (layer §6.5);
   nothing here shortcuts that.

## 6. The commons's path

Success is: curate a collection, explain inclusion decisions, preserve what I
promise to preserve, help others discover it.

1. **Curate.** The host adopts what it chooses to hold, exactly as a user
   does. Its collection *is* its set of pins.
2. **Explain.** For each held publication the host writes an inclusion
   statement into its catalog: the reason, the curated relations, and the
   preservation promise it makes for that entry (§7.2). A statement is
   attributed to the host's world; an aggregator that copies it attaches
   the source catalog's identity, and the statement survives aggregation
   unchanged.
3. **Preserve.** Under its fetch policy the host fetches the bytes it
   promised and, for records, keeps its own copy of each corpus in a
   container it controls. The catalog entry lists that location.
4. **Help others discover.** `catalog` builds the catalog artifact from
   pins, inclusion statements and fetch records and pushes it to the host's
   container. `providers export` does the same for the provider list. An
   aggregator follows other hosts' catalogs and its `catalog` merges them:
   entries keep their origin world, marker uid and observed locations,
   dedupe by `corpus_id` when every field of the pin agrees, refuse the
   merge naming both catalogs when two entries share a `corpus_id` with
   different marker uids or artifact identities, concatenate the inclusion
   statements of every contributing catalog each under its own author, and
   add the aggregator's own statement beside them, if it makes one. A
   preservation promise is owned by the world whose statement carries it;
   an aggregator never inherits one, and an entry with no statement of the
   aggregator's own promises nothing on the aggregator's behalf.

## 7. Records and artifacts

### 7.1 Publication marker: attribution entries

A kernel requirement (§11): the marker carries the per-record attribution
entries §4.8 defines as content, frozen with the selection snapshot so a
retry re-reads nothing. Their inputs are three things the publisher's
world already holds: the epoch's address map (which corpus holds each
selected address), the registry's provenance (which of those corpora were
admitted `ReplicaOf`), and each such corpus's own marker facet (its uid,
and any entry it already carries for the record, which is copied forward).
They are content, not identity: a marker's uid remains
`digest(domain, event_token)[:32]` and `marker_consistent` is unchanged.
The field's name, its encoding and where in the act the inputs are read are
the kernel's to choose.

### 7.2 Catalog artifact

A side artifact, `catalog.v1/<artifact identity>` in the host's container,
pushed by science outside the kernel's publish act and outside the names
`listing` reads. It names its predecessor's artifact identity, so revisions
chain. `follow` fetches it by location and verifies the artifact identity.

One entry per held publication:

| field | content |
|---|---|
| `world` | the marker's `published_from.world_id` |
| `corpus_id`, `marker`, `artifact` | the pin: 32-hex, 32-hex marker uid, 64-hex head artifact identity |
| `view` | the marker's view address |
| `supersedes` | the marker's `supersedes_markers` |
| `superseded_by` | marker uids the host holds that name this one, or empty |
| `locations` | every location observed to hold the corpus, each with observation time and outcome; the host's own copy included when it holds one |
| `pin_source` | `provider` (with the bound location) or `catalog` (with the artifact identity) |
| `kinds` | record kinds and counts in the corpus |
| `propositions` | the proposition identities the corpus's assessments assess |
| `datasets` | per selected dataset: identity, observed locations with times and outcomes, redistribution status and its basis (§4.11) |
| `execution` | per run in the corpus: the locators `(repository location, commit, environment bundle location)` from which the cataloguer's own replay passed the kernel's recipe validation, with the observation time; the cataloguer's claim (§5 step 4). A `preserves: execution` promise covers both locators. |
| `inclusions` | one or more statements, each `{by: world id, reason, relates, preserves}` plus, **only when copied by an aggregator**, `from: <the source catalog's artifact identity>`. A cataloguer's own statement names no source: its source is the catalog it is in, whose identity cannot appear inside its own bytes. `relates` is zero or more `(pin, relation, reason)` with `relation` from the closed set `alternative-analysis-of`, `addresses-related-question`, `supersedes-in-our-view`; `preserves` is the subset of {records, data, execution} that world promises. A statement is never edited or merged by another cataloguer. |
| `contributed_by` | for an aggregator, the set of followed catalog artifact identities the entry came from; empty for the host's own pins |

Entries for retired publications remain, with `superseded_by` set, so a
reader who still holds that revision, or who never adopted it, can find
it; a reader who retired it cannot re-adopt it (§10).

### 7.3 Provider list artifact

A side artifact, `providers.v1/<artifact identity>`, naming its predecessor
like a catalog. One entry per binding — `world`, `locations`,
`bound_since`, and `via` (the set of list artifact identities it was
imported from, empty for direct bindings). It carries no accept policy: a
host's scientific acceptances are its own and are not offered for import.

### 7.4 Sharing registry and configuration

Framework §9.1's file is launcher-owned, read at session open and written
by nothing in the framework. Sharing state changes by acts, so it does not
live there. It lives in a **sharing registry** under one new configuration
key, and the loader derives the session's mounts from it:

```toml
sharing_root = "..."             # one directory; resolved like operations_root
accept = ["<32-hex world id>"]   # §9; empty means the reader's own world only
[fetch]                          # §4.11
policy = "records-only"          # or "fetch"
max_bytes = 0                    # with "fetch": 0 means no bound
```

The sharing registry under `sharing_root` holds pins (with source and fetch
record and `keep`), provider bindings (with `confirmed` and `via`),
follows (artifact identity, kind, location) and the adopted corpora's
roots. At session open the loader **unions** the roots the registry marks
**mounted** (§10) into `WorldConfig.corpus_roots`, so the kernel's rule that
mounts equal `corpus_roots` exactly holds; `write_root` and
`read_contracts` apply unchanged. `accept` and `[fetch]` are policy the
person authors, so they stay in the configuration file.

Every registry write is the durable effect of a ledger-recorded act of the
`sharing` write class (§11), and the registry is rebuildable from those
ledger entries; the framework's write-audit rule counts it. The act's
ledger evidence is the pin it wrote or changed: corpus id, marker uid,
artifact identity, source, location, the verification verdict, and the
mounted or retired transition.

This is a framework §9.1 amendment: one key, and mounts derived from
registry state rather than listed by hand. Its rationale is the framework's
own: configuration is untrusted input validated at session open, and the
registry is validated the same way.

## 8. Hosting layouts and transports

The kernel lays a remote out as a container (§3). Every layout keeps that
shape unchanged, so the kernel's completeness check over `listing` applies
as it is, and side artifacts sit beside the corpora under names the check
never reads.

**Git remote.** One repository is one container and may hold every
publication a publisher sends there, from any view, and its side artifacts.
A publish is one commit adding a corpus root and its head artifact; the
container is never pruned (§4.10). Records are markdown, so a publication is
browsable on GitHub without an installation. The git transport implements
`push` by clone-or-fetch, add, commit and push to the container's one
branch, idempotent because a retry that finds every named file present with
matching digests commits nothing; `listing` reads the tree at the branch
head. Credentials are git's own; the transport adds none. A missing
intermediate (remote §13 item 2) is fetched from the same container, or
from the catalog's other locations.

**Zenodo deposit.** One deposit per publication, holding the corpus, its head
artifact and the holdings of every selected redistributable dataset; a
revision is a new version. Everything further is milestone 3's (§4.10).

**Any other container.** A plain directory served over HTTPS, an S3 bucket or
a peer transport is a transport implementing the same two methods; none
enumerates a container (§4.10). The git transport's idempotent retry is a
milestone 1a test, not a promise.

## 9. Belief under an accept policy

`accept` is applied **before** the kernel's verification lifecycle is
evaluated, and to every kind that lifecycle reads:

1. The verifier set is the reader's own world plus `accept`.
2. Acceptance is decided **per record, by its provenance world**, never by
   the corpus that happens to carry it. For each corpus holding the record
   one branch applies, in this order, and the record counts if any holding
   corpus's branch says so:
   - **Carried.** The corpus's marker attributes the record to an origin
     (§4.8). This branch is tested first for *every* carrier, the reader's
     own re-adopted publication included: foreign attribution survives
     publication and re-adoption. Counts only when the origin world is in
     the verifier set and the reader holds an origin-confirmed pin of the
     origin publication that holds the record. So accepted *B* carrying
     unaccepted *A*'s assessment through closure never makes it count
     under `accept(B)`, *B* adopting its own verification back never
     makes *A*'s assessment count under `accept = []`, and a carrier's
     attribution of a record to *A* is not taken on the carrier's word.
   - **Own.** The record is in the reader's write root, or is an
     unattributed record of a corpus whose `(corpus_id, marker uid,
     artifact identity)` a `publication-binding` in the reader's own world
     bound — the reader's own authored records, adopted back. Counts, with
     nothing further. A marker that merely *claims* the reader's world id
     proves nothing (§4.4 layer 2) and never takes this branch.
   - **Carrier's own.** Otherwise the carrier's `published_from` world.
     Counts only when that world is in the verifier set and the reader's
     pin of the carrier is origin-confirmed (§4.4).
   A corpus pinned through a followed catalog only is held, readable and
   citable; its carrier's-own records do not count until an
   origin-confirmed pin names the same head artifact identity, and its
   carried records count exactly when the Carried branch independently
   authenticates their origin.
3. The rule applies to every record kind that can change what belief reads:
   assessments, verifications, superseding verifications, and the
   correction records — retractions and their successors — whose standing
   the kernel folds before it gathers evidence. Applying it uniformly and
   first is what keeps it safe: an unaccepted publisher's failed
   verification cannot invalidate an accepted assessment, an unaccepted
   superseding verification cannot suppress an accepted failure, and an
   unaccepted retraction cannot remove accepted evidence before the filter
   sees it.
4. The reproducibility context that belief returns records the effective
   policy: the verifier set, each accepted corpus's pin source, and every
   record the policy excluded with its world. A belief answer therefore
   explains both the evidence considered and how it was selected.
5. Belief comparisons across installations are made over the same pins and
   the same policy. Different selections can legitimately give different
   results, and the context is what shows why.

Two outcomes are required: the filter applies to assessments,
verifications and correction records alike **before any of their effects
and before any pool-level rule** — retraction standing and the identity
collapse included — so an unaccepted retraction cannot remove accepted
evidence and an unaccepted corpus's facet-disagreeing twin cannot refuse an
accepted assessment; and the context states the policy. Science cannot meet
the first from outside: it hands a view, not records, to evaluation, and
the kernel's gather takes the retraction enumeration from the view, folds
standing and subtracts retracted targets before any assessment is decoded.
So the requirement on `beliefs` (§11) is a **kernel-side predicate**
supplied to gather, `counts(corpus_id, address)`, consulted before standing
is folded, and the policy statement carried into the context. The kernel
already attributes every node to a corpus (`node_corpus`); what it lacks is
the world and the pin state, which the predicate encapsulates. Science
computes the predicate from `accept`, the pins' confirmation state, the
reader's own publication bindings, and the carriers' attribution entries.
It is a milestone 1a precondition: without it, *B*'s belief after adopting
*A* simply contains *A*'s assessments.

## 10. Retirement, supersession and pinned dependencies

`adopt` moves a pin through recoverable states, and every check that can
refuse runs **before** the kernel's world is touched:

| state | meaning |
|---|---|
| `fetched` | the copy is on disk and `restore_root` has verified its chain; the root is readable and **not** in the reader's world |
| `admitted` | `admit_publication` succeeded; the corpus is live in the kernel's registry |
| `mounted` | the loader will mount it at the next session open |
| `retired` | the kernel's `World.retire` has written its terminal status under registry authority; it has left the live span. Irreversible: a retired `corpus_id` is never re-admitted to that world. |

On a `fetched` candidate `adopt` checks, by reading the restored root
directly: the marker layout; supersession (the tip rule over held markers);
and the conflict rule below, comparing the candidate's addresses and
content identities against **every corpus the kernel's registry lists
live, plus every candidate this session has already admitted or marked
`mounted`** — not the session's fixed `corpus_roots` alone, which miss an
adoption made moments ago — each opened by its root (`ReadView.opened_at`):
the write root and the configured roots from the configuration, adopted
roots from the sharing registry, since the kernel's admission record
carries no path. The read needs no epoch and so cannot itself refuse
`duplicate-location`. A
refusal at this stage leaves the candidate `fetched` and the world exactly
as it was, usable. Only a clean candidate is admitted, then marked
`mounted`. A crash between admission and the mark is reconciled at the next
`adopt` or `show` from the kernel's registry, which is the truth about
admission; the sharing registry never claims a state the kernel does not
show.

When the candidate is a successor:

1. The predecessor stays held and addressable. What was shared cannot be
   unshared, and the reader's own runs or other held publications may depend
   on it.
2. The **current** publication for `(view, destination)` advances only after
   admission succeeds, supersession resolves to one tip, **and the
   successor's pin is at least as confirmed as the predecessor's**: an
   origin-confirmed predecessor is never superseded, and never retired, on
   a recommended successor's word, since a followed catalog can serve a
   chain-valid corpus whose marker merely claims the predecessor's world
   and names it in `supersedes` (§4.4 layer 2). A recommended successor of
   an origin-confirmed predecessor is held — admitted and mounted — with
   `current` unmoved and nothing retired, and `show` says what confirmation
   would advance it. A divergent sibling (`divergent-publication`) leaves
   the update unresolved and the candidate `fetched`, as does a missing
   intermediate.
3. The predecessor is **retired** — the kernel's existing `World.retire`,
   reached by the `sharing` write class, after which it leaves the mounts
   and the live span — only when nothing requires it: no pin flagged
   `keep` (set before this adoption; §3); no held publication whose
   attribution entries name it; and no record in the reader's write root,
   published or not, whose **required dependency closure** reaches a record
   only the predecessor holds. That closure is exactly what the publish act
   computes for `closure-incomplete`: the walk over every world relation
   the contract declares — which includes `composes`, so a composite keeps
   its members, and `grounded-in`, so a retraction keeps its grounds — plus
   a spec's projection-held `addresses`, extended by what the act leaves
   inward: a verification's target assessment and the runs it compares,
   and a correction's target. A verification of *A1*'s assessment that *B*
   has not yet published, or a composite of *B*'s over *A1*'s proposition,
   therefore keeps *A1* when *A2* drops that record. An
   admitted corpus that is merely absent from the mounts is not an option:
   the kernel counts it live, and every later publish would refuse
   `selection-incomplete` naming it. While something requires it, it stays
   mounted, which §4.7's requirement 1 makes legal for the records it
   shares with its successor; the records the successor dropped remain
   readable from it.
4. A dependency-required predecessor is reported by `show`, so the reader
   knows why a retired-in-intent revision is still mounted.
5. **Exit rule for a conflict.** When a `fetched` successor holds an
   address a required predecessor also holds with different content (§4.7
   requirement 2 refuses such a pair once both are live), `adopt` refuses
   before admission: the successor stays `fetched`, nothing is live that
   was not live before, and `show` names the conflicting addresses and the
   dependency. The reader either releases the dependency (drops the `keep`,
   republishes without the derived record) and adopts again, or keeps the
   predecessor and leaves the successor `fetched`. Nothing picks for them.

Retirement is therefore a milestone 1b obligation of the surface — the
kernel has the act, and "nothing acts on it" (remote §13 item 1) is the
`sharing` write class's gap (§11) — not an option.

## 11. What `beliefs` must add, what the framework must amend, what `science` builds

Kernel requirements, each filed as a `beliefs` task after this spec's
review, with the milestone part that needs it:

| requirement | needed by |
|---|---|
| cross-corpus dataset inputs at assessment and admission (`beliefs-9ce6e4`) | 1a |
| attribution entries on the marker, as a frozen facet (§7.1) | 1a |
| an acceptance predicate `counts(corpus_id, address)` on gather, consulted before retraction standing is folded, and the policy statement in the context (§9) | 1a |
| overlapping publications in the world index under §4.7's three outcomes (`beliefs-81367e`) | 1b |
| whether `beliefs-9ce6e4` covers an `assesses` edge and a `verification` whose targets live in a mount, or a sibling task does | 1a |
| whether the marker should carry a workspace locator, or the catalog's `execution` claim suffices (§5 step 4) | open, asked at 1a |
| key-bound provider identity: signed head artifacts (§4.4) | 4 |
| view publication, so topics and themes can be shared (projects §8.1 defers it) | 4 |

Framework amendments, made in the framework document before milestone 1a's
plan:

- §4.4: a `sharing` write class reaching the `lifecycle` (`restore_root`)
  and `registry` (`admit_publication`, `World.retire`) act families for
  `adopt`, with the ledger evidence §7.4 names; today "no write class maps
  to any of them". Reaching `World.retire` is milestone 1b's whole
  retirement requirement. The framework document defines the evidence's
  shape.
- §9.1: the `sharing_root` key and mounts derived from the sharing registry
  (§7.4).

Science builds: the `publish` command with dry run; `adopt`, `show`,
`provider bind`, `follow`, `find`, `fetch`; `spec`, `verify`, `run` and
`assess` resolving datasets, propositions and the records they name over
mounts (today each checks through the write view alone), and `belief`
evaluating over a world read rather than the one mount holding the
proposition, since after adoption the assessment and the proposition it
assesses live in different corpora; the git
transport; the catalog and provider list artifacts; `catalog` and
`providers export`; the fetch policy; the accept-policy computation; later,
the Zenodo transport. Science's own precondition for 1a is the session
mounts landing in the coordination command set (`sci-923d3a`).

## 12. Milestones

**1. One complete collaboration between two installations, over git.** Two
worlds — two hosts, or two installations on one machine — and one bound git
remote each; explicit locations, no catalog. It has two parts because
overlap arrives at a known step: *A*'s first adoption of *B*'s derivation
mounts *A*'s own records a second time, from *B*'s corpus — the datasets,
and through the reproducible closure the assessment, run, spec and
proposition *B* reproduced. *B* adopting *A*'s single publication beside a
fresh write root collides with nothing, provided *B* redeclares nothing.

*1a, no overlap.* *A* publishes a **reproducible** view; *B* runs `provider
bind` on *A*'s location, confirms the world id it reports, adopts, is
handed *A*'s workspace location and commit out of band, reproduces one
assessment, authors a `spec` against *A*'s mounted proposition and datasets
without redeclaring any of them, changes one input, runs, assesses, and
publishes a reproducible view to its own remote. Decisive cases:

- **lineage:** *B*'s changed analysis is a distinct assessment with its own
  identity, its lineage reaches *A*'s dataset by identity, and *B*'s marker
  attributes the carried records to *A*'s publication; *B*'s belief with
  `accept = []` excludes *A*'s assessments and says so in its context, and
  with `accept = [A]` includes them;
- **transport:** a `publish` retried after a partial push converges on the
  same remote content and commits nothing new when the files are present.

*1b, overlap and retirement.* *A* binds *B*, adopts *B*'s publication; *A*
publishes an update that drops one record; *B* adopts the update. Decisive
cases:

- **overlap:** after *A* adopts *B*'s publication, *A*'s records held in
  both corpora read once and contribute once to belief, and with
  `accept = [B]` only, *A*'s own assessment counts through its write-root
  copy under the own branch, while the copy carried in *B*'s corpus
  contributes nothing and never counts as *B*'s evidence; after *B* adopts
  *A*'s update, the records the two revisions share read once;
- **pinned derivation:** adopting *A*'s update does not make *B*'s derived
  analysis unreadable: the dropped record *B* depends on stays mounted from
  the retired revision, and `show` says why.

Belief on both sides is compared over the same pins and the same policy.

**2. A commons.** A host world with a catalog and a provider list; a reader
who follows it, adopts through it from a mirror, imports its provider list
as candidates, and sees a recommended pin stay unaccepted until an
origin-confirmed one arrives. Aggregation of two catalogs.

**3. Preservation.** The Zenodo transport, fetch policy beyond
`records-only`, host copies of records and bytes, and the preservation
promise in catalog entries. The transport-seam `commit` hypothesis is tested
here.

**4. Hardening.** Signing, list subscriptions and bounded traversal, view
publication, and curated relations in `find`.

Milestone 1a is a `planned` task with its own implementation plan once its
four kernel requirements, the framework amendments and `sci-923d3a` land;
1b follows its two; milestones 2–4 are filed as goals with `idea` children and scoped when
milestone 1 closes.

## 13. Non-goals

No web application: GitHub renders the records. No migration of the
prototype's papers, topics, themes or dataset recipes; papers become
`source` records and source assertions when a project needs them, recipes
become workspaces with an `analysis-spec`, and topics and themes are views.
No promotion, overlay or canonical owner. No central service. No access
control beyond the host's account controls. No authored ancestry list. No
global reputation, vote or accepted answer. No container pruning.

## 14. Open questions

1. Whether a host's inclusion decisions should also be governed
   coordination records in its own world, for its audit trail, beside the
   catalog block that travels. Deferred to milestone 2's plan.
2. The closed relation set of §7.2: whether three relations suffice or
   whether "same data, different proposition" needs one. Decided by
   milestone 2's first real catalog.
3. Whether a provider binding should expire or require re-confirmation when
   a location's account changes hands. Deferred to signing.
4. Whether a catalog should carry the cataloguer's own reproducibility
   summary of held assessments or leave that entirely to `find` over held
   corpora. Deferred to milestone 2's plan.
