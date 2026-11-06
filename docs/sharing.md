# Sharing publications

Type: protocol, data model; document types 1. This describes the implemented
publication/provider/pin flow, sharing-registry version 1 and acceptance policy
`science.accept.v1`. Kernel publication markers, bindings, restore and lifecycle
rules belong to [beliefs](https://github.com/verifiably/beliefs/blob/main/docs/writes.md#publication).
[Configuration](configuration.md) supplies the roots and reader policy;
[sessions](sessions.md) supplies invocation and replay ordering.

## Participants and identities

A producer publishes a saved project's view. A provider hosts the resulting
corpus and head artifact; a recipient inspects, explicitly binds the provider's
location to its claimed world, adopts the publication, and separately decides
whether to accept that world's evidence. Availability, origin confirmation,
acceptance and assessment independence are separate questions. A URL is a location,
not an identity. A marker's world claim alone authenticates nothing.

A publication is an immutable selected set of records with a marker. The corpus
id, marker uid, artifact identity, originating world and view identify the pin.
Record content identity permits equal copies in different carriers to resolve;
it does not make every copy an independent assessment. Attribution entries name
an originating publication `(corpus_id, marker)` for carried records, rather than
crediting an intermediary as the source. Scientific addresses do not become local
copies merely because the recipient hosts them.

## Publish, inspect, bind and adopt

1. Use `science epoch` to publish an epoch after writes. `publish-preview` evaluates
   the named project through the kernel's publication selection and closure checks.
   It shows selected records, attribution and dataset bytes the destination does
   not carry. Incomplete/empty selection and missing closure refuse; preview writes
   nothing. `publish` uses the same Own classification for a new attempt.
2. `publish --target <project> --to <absolute-directory-or-https-git-remote>` freezes
   its selection, stages a new corpus, transports it and records a publication
   binding. An unfinished attempt names its event token; `--resume` uses the frozen
   request and ownership/attributions, not a new classification. Local and remote
   transport do not change publication semantics. Authorization and redistribution
   permission remain the operator's decisions.
3. `provider-inspect --location <location> --corpus-id <id>` verifies the offered
   corpus in disposable scratch and reports its claimed world/marker. It records
   no binding and grants no acceptance.
4. `provider-bind --location <location> --corpus-id <id> --world <expected-world>`
   checks the expected world against the publication and records `bound` evidence
   before writing the provider projection. Binding one's own world as a provider
   refuses. Use an explicit expected id rather than trusting a URL or prose title.
5. `adopt --location <location> --corpus-id <id>` rebuilds registry projections,
   reconciles prior transitions, fetches and verifies the publication and sources
   it from a binding of that publication's claimed world. An unsourced pin refuses.
   A refusal before `fetched` removes the downloaded copy and writes no pin/line.
   After fetched, layout/overlap/lifecycle refusals may leave a pin for recovery.
6. Admission checks the publication against live corpora, then the kernel records
   admitted/mounted evidence. Mounts are fixed at session open: reopen after adoption
   or retirement and run `science epoch` before epoch-bound evaluation. `show
   --corpus-id <id>` distinguishes mounted state, live/present kernel state, source,
   origin confirmation, acceptance and verification. It does not expose a new
   independence verdict the kernel's belief inputs do not supply.

Adopt's admission checklist allows equal copies. Different content at the same
canonical id refuses `content`; conflicting deprecated keys refuse `deprecated-key`;
one uid claiming different ids refuses `uid-corruption` (highest priority).
Within the first conflicting live corpus, detail lists all conflicting addresses.
Publication layout and pins must still be valid even when content copies agree.

## Acceptance and belief

The verifier set is this installation's world plus configured `accept` world ids.
The policy filters assessments, verifications and retractions before their effects.
The first applicable branch decides whether a particular carrier's record counts:

- Own: the write corpus and explicitly configured markerless roots count, including
  restored replicas. Registry roots are excluded from implicit ownership even if
  hand-listed. A configured marker-bearing root remains a publication carrier.
- Carried: an attributed record needs its named origin publication mounted at the
  attributed marker, origin-confirmed and from an accepted world. That origin must
  select the record as its own, and the carried copy's content must equal it.
- A carrier's own record must be in its pinned marker's selection. It counts when
  it is this installation's own publication adopted back (matching the write
  corpus's binding), or when its world is accepted and its origin is confirmed.
- A hand-listed publication without a confirming pin does not acquire acceptance
  merely from being readable.

Two claimed publication/adopted roots with the same corpus id refuse because the
policy cannot distinguish their standing. The policy statement, verifier set and
selection/exclusion explanation contribute to belief provenance. Acceptance does
not admit an unreproduced assessment; the kernel's held-input, verification and
independence rules still apply. Removing an origin can exclude carried evidence
without deleting its carrier. No hosting vote or popularity score enters belief.

## Supersession and retirement

Publications group by originating world, unpinned view and destination. Successors name predecessor
corpus/marker pairs. A complete resolved chain has one current tip; sibling tips
refuse `divergent-publication`. A chain passing through a retired intermediate
refuses `chain-retired`; never infer missing lineage from dates or filenames.
Equal content may overlap across publications; in-place divergent content does not.
An unresolved group reports missing pairs and folds historical mounted lines to
choose its displayed current publication, using only markers seen so far. This is
not a new ancestry link. Same-second adoptions in different sessions can affect
that display order. Publishing one view to two destinations creates two groups;
an unlinked attributed origin can still make publication attribution ambiguous.

Adoption reevaluates mounted predecessors. Retirement is blocked by explicit
`keep`, a needed intermediate chain, attribution from mounted publications, or a
live dependency with no equal-content alternative holder. The dependency closure
includes assessment/spec/run/proposition inputs, verification derivations,
retractions and kernel closure. Retention reasons are reported individually.
A changed captured configuration refuses `config-stale` before retirement; an
already completed adoption stands. Restart with the current config and rerun adopt.
Terminal/departed corpus reconciliation records or reports the actual state rather
than reviving it. `keep` protects a pin; it does not edit its scientific records. Retirement does not preserve vocabulary
declarations reachable only through profile bindings; those may need explicit
re-declaration. Reads can still see the old session mounts until reopen, while
citing writes and publication refuse retired corpora. Running epoch alone does not
refresh a stale session's mounts.

## Registry and replay

Under `sharing_root`, science owns `pins/`, `providers/`, `scratch/` and adopted
`roots/`; `follows/` is reserved. Adopted corpora are kernel-restored roots, not
science-owned record formats. Each root's head artifact is retained beside it as
`roots/<corpus-id>.head-artifact.v1` for verification of a reused fetched copy.

Pin JSON has fields `version:1`, `corpus_id`, `marker`, `artifact`, `world`, `view`,
`source`, `fetch:{location,at,verdict}`, `state`. Corpus and world ids are 32 lower
hex; states advance `fetched → admitted → mounted → retired`. Source is empty or
`provider:<location>` / `catalog:<artifact>`; current adoption writes provider sources.
Provider JSON has `version:1`, `world`, `locations` (string list), `bound_since`,
`confirmed` (boolean), `via` (string list). Writes merge new locations/via entries,
retain the original bound time and never unconfirm a confirmed binding. Malformed
registry values refuse rather than silently disappear.

Every registry change follows its kernel ledger sharing line. Replay reads all
session sharing lines ordered by `(time, session id, position)`, folds transitions
idempotently, never regresses a pin, and only fills a source when absent. Missing
or empty interrupted ledgers carry no evidence and are skipped; unreadable ledgers
refuse reconstruction. The ledger is authority, the JSON registry a projection.

Historical sharing reports also retain presentation tails at
`operations_root/tails/<session-id>/<invocation-id>.json`. The dispatcher rebuilds
pin blocks from ledger evidence and appends that saved commentary. A missing file
means an empty tail. Losing a nonempty tail loses commentary and can stale a cursor,
while effects remain recoverable. The tail is neither kernel evidence, an invocation
close outcome, nor a cache recomputed from current state; exact replay requires it.

## Holding external bytes and current limits

`fetch` requires policy `fetch`, a dataset resolved through the session mounts declaring exactly one resource
and a pinned digest. Its source is an absolute local file or HTTPS URL. It checks
retrieved bytes against the declaration and optional byte bound before the one
holdings write to `store_root`. URLs use a 60-second timeout and at most five
redirects. A mismatch refuses without publishing a holding; prior URL observations
or another store's same relative path are not superseded as this store's location.
It does not redeclare the dataset. Multi-resource fetch is currently refused.

Catalog discovery, provider-list import, automatic follow/subscription, mirror
selection, signing and preservation workflows remain intended directions beyond
the current command surface. Their recorded designs remain historical intent;
their absence here neither supplies those commands nor abandons the goal. Current
use is explicit publish, provider binding, pin adoption and policy-controlled fetch.

## Failure and recovery

Read structured refusals and the ledger before retrying an uncertain effect.
An unfinished invocation is not proof of no effect. Restore/admission and permit
failures require the named kernel/operator remedy; registry replay cannot repair
scientific roots. Never edit pins or ledger lines to force progress. Reopen after
mount changes; resolve stale epochs before treating an evaluation as current.
