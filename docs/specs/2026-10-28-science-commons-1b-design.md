# Science commons milestone 1b — design

**Date:** 2026-10-28
**Status:** draft for review, revision 8. Revision 7 (`e4f7160`) answered review round 5;
revision 8 answers a scoped review round 6 of that revision's delta (a fresh `claude-code`
reviewer, verdict revise: Important 5, Minor 6): the `corpus-retired` guard sits on
`cited` alone, since `mount_holding` serves reads only; `publish` and `publish-preview`
refuse `corpus-retired` when a session corpus is not live, the one route that creates a
dependency on a retired origin without a citation; the `science epoch` claim is replaced by
its observed behaviour (a CLI-process build over the live set, then `epoch-stale` in the
stale session); the gate is `verify` of the record P1 alone holds, not a `spec`; the unkept
branch is built in the overlap half; and the `dataset` recovery, the vocabulary route, the
coordination-kinds invariant and the clock seam are stated (§5.7, §5.9, §7).
Revision 6 (`202a298`) answered review round 4;
revision 7 answers review round 5 (reviewer `codex/gpt-6-astra`, verdict revise: P1 1, P2
1, P3 2): a citation of a retired corpus refuses `corpus-retired` in `cited` and
`mount_holding` until the session reopens, with a two-command gate (§5.7); the
`duplicate-publication` refusal is withdrawn under the round's ruling, one view at two
destinations is admitted and reported, the kernel's `attribution-ambiguous` stands, and
the conflict fixture's expectation follows (§5.6, §5.9); the cross-session same-second
order is kept as a stated limitation of an unresolved group's displayed `current` and
tested (§5.6, §5.9); the pending-door report gate runs on the unkept branch (§5.9).
Revision 5 (`a699ac1`) answered review round 3;
revision 6 answers review round 4 (a fresh `claude-code` reviewer, verdict revise:
Important 4, Minor 11): divergence is decided by named ancestry, so siblings under a
never-held predecessor are refused, not mounted (§5.6); two publications of one view to two
destinations refuse `duplicate-publication` at preflight, this document's call for the user
to confirm (§5.6, §5.9); `keep` is read at session open, retirement refuses `config-stale`
when the file changed since, and the report prints the list it used (§5.7 rule 1); the
chain-retention, configured-keep and stale-configuration gates are added, with the
never-held sibling, the checklist's three hand-made candidates and the report gates (§5.9);
the fold states its predecessor case and reads links from the established authorized roots
seen so far, the established set is folded in memory for `show`, `departed` is its own
Finding, step (3) reads by root, the checklist's live set is the kernel's, and the
`supersedes` fields are named as not followed (§5.1, §5.6, §5.7). Revision 4 (`8439319`)
answered review round 2;
revision 5 answers review round 3 (reviewer `codex/gpt-6-astra`, verdict revise: P1 4,
P2 2, P3 1): only `mounted` and `retired` pins form the established state, so a refused
`fetched` sibling never becomes current or triggers a retirement (§5.6); a spec's `target`
joins the dependency walk with the spec-only case as a second gate (§5.7 rule 4); an
`adopt` reconciles completed effects, adopts, then re-evaluates retirement with the
candidate mounted, so an incoming publication's requirements are known before anything is
retired (§5.7); the pin shape keeps version 1, dropping `keep` without a migration (§3.2);
the current publication is a fold over the ledger's lines in replay order, replacing the
earliest-mounted rule that a disconnected earlier adoption or a same-second pair defeated
(§5.6); a chain through a retired marker is refused at preflight as `chain-retired`, since
the kernel's attribution fold reads mounted replicas only (§5.6, §5.7); the empty-accept
fixture asserts both excluded lines (§5.9). Revision 2 (`3a6fcf8`) followed the builder
check (§5.7's pending-door behaviour, §5.9's query by address and comparison assertion,
§7's two merges). Revision 3 (`a8f7a85`) answered review round 1 (reviewer
`codex/gpt-6-astra`, verdict revise: P1 2, P2 3): the supersession preflight runs before
admission and a divergent sibling stays `fetched` (§5.7); the dependency walk follows the
facet references the relations miss, with the spec-drop case as a gate (§5.7 rule 4);
retirement is re-evaluated on every `adopt`, with a retry on a mounted tip (§5.7); `current`
under an unresolved chain is the earliest mounted tip, from the `mounted` line's stamp
(§5.6); P3's selection is P1's minus the assessment, vocabulary datasets included (§5.9).
The round's rulings on the proposed choices (two merges, configuration-owned `keep`,
derived current publication) stand as ruled. Revision 4 answers review round 2 (a fresh
`claude-code` reviewer, verdict revise: Important 2, Minor 7): the authorized roots include
retired pins' copies and divergence is a common known ancestor, so a post-retirement sibling
is refused rather than mounted (§5.6, §5.9); the reconcile path for `retired` is a stated
requirement on the kernel door, idempotent re-ledgering, since science cannot ledger that
transition (§5.7); the address group is keyed by world (§5.6); the missing link is named as
the `(corpus_id, marker)` pair the tip carries (§5.6, §5.8); P2 is retired with P1 in the
late-link case, `keep` precedes a late predecessor's adoption, and every retirement reports
the reopen remedy (§5.7, §5.9); the registry version is bumped and rebuilt from the ledger
(§3.2); the first-half `excluded` wording is one line, and the Carried content check gets
its own unit test (§5.9). Task sci-9104fb (`planned`), child sci-73c80e (science's side of
the kernel's cut 48), idea sci-4a3543 (absorbed, §5.4).
**Scope:** how `science` meets milestone 1b of the commons design
(`2026-09-30-science-commons-design.md` §12: update, overlap and retirement) now that the
kernel reads one address held in several live corpora (`beliefs`
`docs/superpowers/specs/2026-10-28-overlapping-publications-design.md`, cut 48, merged on
`beliefs` main at `316c202`). The commons design stays the authority for *what* 1b is; this
document settles what it left to the surface, adopts the amendment list the kernel's §8 hands
to science, and records where this milestone departs from the commons design's letter. It
designs no command declaration in detail and no kernel change; the one kernel precondition
is already filed (§7).
**Baseline:** science main `a509cb8`; beliefs main `316c202`.
**Workspace:** `.worktrees/commons-1b`, branch `commons-1b`.

**Inherits:** the commons design §4.4, §4.7, §4.8, §9, §10 and §12 in full, with its 1a
amendments (Deviations 1–12 of `docs/plans/2026-10-22-science-commons-1a.md`); the kernel's
overlapping-publications design §4.1, §5.4, §6, §7, §8 and §10; the writer-session design's
sharing and publish doors amendment of 2026-10-23. Terms used without definition are those
documents'.

## 1. Intent and evidence

Milestone 1b, in the commons design's words: *A* binds *B*, adopts *B*'s publication; *A*
publishes an update that drops one record; *B* adopts the update. Two decisive cases:

- **overlap:** after *A* adopts *B*'s publication, *A*'s records held in both corpora read
  once and contribute once to belief; with `accept = [B]` only, *A*'s own assessment counts
  through its write-root copy under the Own branch while the copy carried in *B*'s corpus
  contributes nothing and never counts as *B*'s evidence; after *B* adopts *A*'s update, the
  records the two revisions share read once;
- **pinned derivation:** adopting *A*'s update does not make *B*'s derived analysis
  unreadable: the dropped record *B* depends on stays mounted from the retired revision, and
  `show` says why.

The intent is the user's: the commons design was reviewed and approved on 2026-10-01 and its
§10 and §12 were written for this milestone. The kernel's design was accepted by the user at
revision 10 on 2026-10-28 and names, in its §8, exactly what science must change. No human
turn in this task's record chooses a mechanism beyond those two documents; every ruling below
is this author's proposal from them and from the tree, for the user to confirm or correct.

What the tree does today, read at the baseline:

- `commands/adopt.py` `_require_no_overlap` refuses `adopt-conflict` on any shared address,
  content aside, with the reason "overlap is milestone 1b" (commons §10 Deviation 3). It
  compares live record ids only: no deprecated ids, no uids, no content.
- `acceptance.py` decides `counts(corpus_id, address)` per holder as commons §9 says. The
  Carried branch (`_origin_holds`) checks that the origin's marker selects the address as its
  own, but compares no content: a carrier could hold different content under an accepted
  origin's address and count (sci-4a3543; reachable only in corpus-local reads, since world
  reads refused the pair). `explain` prints `excluded <address>` per rejected
  `(corpus_id, address)` with no word for a copy whose record counted elsewhere.
- `config.py` `ReadContext.mount_holding` and `cited` refuse any address two mounts hold,
  content aside, before the kernel is consulted. `_world_inputs` builds `pins` for every
  session mount, which is every captured holder, so the kernel's §5.4 pin requirement already
  holds for world reads.
- `world_belief.py` `SYMBOL_FIELDS` binds `enumerate_retractions` (v1) to the retraction
  derivation; the kernel now ships `enumerate_retractions_v2` beside it (five bundles;
  `build_over` zips bundles to installed rules and selects by symbol, so the fifth bundle
  changes nothing until the dict names it).
- `sharing.py` `Pin` carries `keep: bool = False`; nothing sets it, no command reads it
  except `show`'s pin block. The registry knows pins, bindings and roots; it has no notion
  of the *current* publication for a `(view, destination)` and no retirement path:
  `apply_line` folds a `retired` line, but no science command can produce one.
- The kernel's `ScopedWriter` has `restore_root`, `admit_publication`, `record_sharing`
  (which admits only `bound` and `mounted` and says `retired` waits for "World.retire's"
  door), `publish` and `resume_publish`. `World.retire(corpus_id)` exists under `registry`
  authority and writes a terminal status record; no session door reaches it, so no
  `sharing`-class invocation can retire a corpus and ledger it. `beliefs-c0d952` (design
  ledgered publication retirement, `planned`) and its implementation idea `beliefs-a989fb`
  are the kernel's filed answer.
- The publisher's own supersession needs nothing from science: the publish door's
  `marker_tips_at` reads the publisher's `publication-binding` tips, so a republication of
  the same view to the same destination names its predecessor in `supersedes_markers`.
  `publication_arrival.publication_tip(roots, view, destination)` folds the markers of
  exactly the roots it is given and returns one tip, sibling tips, or none.
- The 1a fixture (`python/tests/helpers/commons.py`) ends at `build_derived`: *B* has
  bound *A*, adopted P1, verified *A*'s assessment (the verification sits unpublished in
  *B*'s write root) and derived a changed analysis over *A*'s proposition and dataset.
  `build_conflicting` already has *A* republish project `a` to a second location. The
  kernel's 1b fixture, `python/tests/acceptance/test_overlapping_publications_acceptance.py`
  in the `beliefs` repository, builds the overlap and the chain gap at the kernel level.

## 2. Goals, non-goals and anti-goals

Goals:

1. The two decisive cases of §1, shown end to end between two installations over git, as
   1a's cases were, over the same pins and the same policy on both sides.
2. Every amendment the kernel's §8 names is made, with `registry.content_identity` as the
   one equality contract wherever science compares two copies of a record.
3. Retirement reaches `World.retire` only through the `sharing` write class and its ledger
   line, never through a world handle (commons §11).
4. Nothing that 1a shipped changes its meaning for a world with no overlap: a single-holder
   read, a single-publication adoption and the accept policy over disjoint corpora behave as
   today.

Non-goals: a commons catalog, `follow`, `find` and recommended pins (milestone 2); the Zenodo
transport and fetch policy (milestone 3); adopting one's own publication back (`provider-bind`
refuses the own world, 1a Final M7; the Own-adopted-back branch stays implemented and
untested until milestone 2's catalog source gives it a route); the supersession-aware map for
a renamed record (`beliefs-49afc2`); a marker carrying transitive ancestry (the kernel's §10
item 3 alternative); the 1a follow-ups already scoped as their own direct tasks (sci-6d4286,
sci-347a36, sci-cf4d58, sci-b979ce, sci-eb808f), which touch the same files and are
sequenced after this branch merges (§9).

Anti-goals: picking a holder by registration or sort order for any answer that depends on
content; retiring anything the reader, a held publication or a write-root record still needs;
a second equality contract beside the kernel's; a science-side copy of the kernel's address
map or closure walk; retiring a corpus without its ledger line.

## 3. Approaches

The commons design fixes the shape of this milestone, so the alternatives below are about the
pieces it left open. Each is ruled in §5; this section records what was weighed.

**3.1 Where retirement runs.** (a) `adopt` of a successor runs the retirement policy after
admission, as commons §5 step 3 and §10 say ("`adopt` of a successor also runs §10's
retirement"). (b) A separate `retire` command the user runs after adopting. **Chosen: (a).**
Retirement is a consequence of supersession resolving, and nothing else in the design acts
on it; a separate command would let the registry hold a resolved successor beside an
unretired, unrequired predecessor indefinitely, which the design's "while something requires
it" rule does not contemplate. (b) is not needed for recovery either: a retirement the door
commits but the pin does not record is reconciled by the next `adopt` from the kernel's
status records, as admission is today.

**3.2 Where `keep` lives.** (a) On the pin in the sharing registry (commons §7.4's letter),
written by a `sharing`-class `keep` command. (b) In the configuration file as a `keep` list of
corpus ids beside `accept`, read at session open. **Chosen: (b), a dated amendment to
commons §7.4 (§6).** Every registry write must follow a ledger line of the `sharing` write
class (commons §7.4), and the kernel's sharing transitions are `bound`, `fetched`,
`admitted`, `mounted` and `retired`: a `keep` write has no transition to ledger under, and
inventing one is a kernel change for a flag that is the reader's policy, not a fact about the
corpus. `accept` is the precedent: "policy the person authors stays in the configuration
file". The retention the surface itself sets (chain retention, §5.7) is computed at
retirement time, not stored, so it needs no write either. `Pin.keep` is removed; `show`
reports `keep` from the configuration. The pin's JSON shape does not otherwise change and
the registry version stays at 1: `Pin` loses `keep`, `_pin_to` stops writing it, and
`_pin_from` stops reading it (the parser reads named keys and ignores others today), so a
1a pin file parses unchanged at the next `load_config` and its next write drops the key.
Provider bindings are untouched. No `mounted_at` is added: the current publication is folded
from the ledger (§5.6), not from a pin field. There is therefore no migration and no entry
point to reach: an existing installation opens as before.

**3.3 The current publication.** (a) Stored in the registry as a `current` entry per
`(view, destination)`, advanced by `adopt`. (b) Derived whenever it is needed, from the
markers of the pins science holds, through the kernel's `publication_tip` over the roots
science authorizes. **Chosen: (b).** It is a pure function of held markers and bindings, and
storing it would need a ledger line (3.2's argument) and could lag the markers.

**3.4 The dependency closure for retirement.** (a) Reuse the kernel's publish-act walk by
calling `closure_missing` to a fixed point from the write root's records, extended inward by
the relations commons §10.3 names. (b) A science-side walk over `stored.WORLD_RELATIONS`.
**Chosen: (a).** Commons §10.3 defines the closure as "exactly what the publish act computes
for `closure-incomplete`"; two walks would disagree the first time the kernel's relation set
moves.

**3.5 The admission checklist's refusal shape.** (a) One refusal code `adopt-conflict`, as
1a, with data saying which rule refused. (b) Three codes. **Chosen: (a).** Callers already
handle `adopt-conflict`; the rule is data, and the message names it.

## 4. Vocabulary added

| term | meaning |
|---|---|
| **content identity** | `beliefs.world.registry.content_identity(node)`: the kernel's digest of a record's canonical projection. Two copies of an address are the same record iff their content identities are equal (kernel §4.1). |
| **live corpus** | a corpus the kernel's registry lists admitted with no terminal status: the configured roots, the registry's `admitted` and `mounted` roots, and every candidate this `adopt` already admitted. |
| **established state** | the registry's `mounted` and `retired` pins: what supersession, the current publication and retirement are computed over. A `fetched` or `admitted` pin is not in it (§5.6). |
| **chain** | for a mounted publication *P*, the publications science holds whose markers connect *P* to the current tip of its `(world, view, destination)` by authorized supersession links (§5.6). |
| **required predecessor** | a superseded publication something still needs: a `keep` entry, chain retention, an attribution entry in a held publication, or a write-root record's dependency closure (§5.7). |
| **`keep`** | the configuration list of corpus ids the reader holds through supersession (§3.2). |

## 5. Decisions

### 5.1 The admission checklist replaces the 1a conflict rule

`adopt` step 8 (`_require_no_overlap`) becomes the kernel's §8 checklist, run on a `fetched`
candidate before admission, against every live corpus and every candidate this invocation
already admitted, each opened by its root (commons §10's "every corpus the kernel's registry
lists live"; 1a's `_require_no_overlap` already assembles that set and keeps doing so). A
candidate is admissible iff:

1. every key, live or deprecated, that it shares with a live record belongs to a record of
   equal content identity (kernel §4.2 rules 2 and 3: content includes the id, so a live
   address meeting another record's deprecated id, or two differing records sharing a
   deprecated id, refuses; differing content at a shared live address is commons §10.5's
   case);
2. no candidate uid is held live under a different canonical address (`uid-corruption`,
   kernel §4.2 rule 1; an identifier correction published as a successor produces this
   against the predecessor, and live ids alone do not reveal it).

A refusal is `adopt-conflict` with data `{"rule": "content" | "deprecated-key" |
"uid-corruption", "addresses": [...], "corpus": <live corpus id>}` and a message naming the
rule, the addresses and the live corpus; the candidate stays `fetched` and the world is
untouched, as today. The preflight (§5.7) adds one rule under the same code,
`chain-retired` (§5.6), whose data names the retired publication instead of addresses. The
live set the checklist compares against is the kernel's: every
corpus the registry lists admitted with no terminal status, read by root (the configured
roots and the sharing registry's roots), plus the candidates this invocation admitted. It
is not `ctx.read_views()`, which is fixed at session open and still holds a corpus retired
earlier in the session. When the live corpus is a required predecessor of the candidate's own
chain, the message and data also name why it is required (§5.7's reasons), which is commons
§10.5's exit rule: the reader releases the dependency or keeps the predecessor and leaves the
candidate `fetched`; nothing picks. The 1a reason string "overlap is milestone 1b" goes.

An address shared with equal content passes: that is the 1b case, and the kernel reads it
once.

### 5.2 Session-holder resolution admits equal copies

`ReadContext.mount_holding(ref)` and `cited(ref)` collect every mount holding `ref`. One
holder: as today. Several: compute each holder's `content_identity`; all equal, the answer is
the write root's mount when it holds the record, else the least corpus id's mount (the
kernel's §8 J17 rule; a representative, since the bytes are equal); unequal, refuse
`invalid-input` naming every holder and that the copies differ, as today's duplicate-location
wording does. `own(ref)` is unchanged: a record a command changes is the write root's.

### 5.3 The in-place content rule

No science command rewrites a scientific record in place: `revise` mints a coordination
revision at a new address, and no command calls the kernel's `revise`, `correct_identifier`,
`supersede` or `delete` on a record. The kernel's §8 rule, that no in-place content change
is made on an address a mounted carrier holds, is therefore recorded as a constraint on any
future write route (commons §10's amendment, §6) and guarded nowhere yet. The plan adds no
code for it; a route that arrives later carries the guard with it.

### 5.4 Acceptance over content identity (absorbs sci-4a3543)

`Carrier` gains `content: Mapping[str, str]`, the content identity of every record the
carrier holds by address, computed once in `_carrier` from the records `acceptance_inputs`
already reads. The branches of `counts` change in one place:

- **Carried.** `_origin_holds` additionally requires that the origin's copy of the address
  has the same content identity as the carrier's copy. A carrier's attribution claim is
  authenticated by the origin's own pinned bytes, so a copy that differs from the origin's
  counts under nothing; the kernel refuses such a pair in a world read, and this makes the
  corpus-local read agree.
- **Own** (the write root, a hand-listed markerless root) and **Own adopted back** and
  **Carrier's own** need no content check beyond what they have: the pin vouches for the
  carrier's exact bytes through its head artifact, and the Own branches read the reader's
  own records.

The policy `statement` adds nothing: content identities are a property of the records the
epoch already captures, not of the policy.

`explain` keeps one line per rejected `(corpus_id, address)` (kernel §6: every holder's
decision is reported), and words a rejected copy of a record that counted through another
holder as a copy, not a record: `excluded copy <address> in corpus <c>` with `the record
counts through corpus <h>` when any other session mount holding the address counts under
the same inputs, and `excluded <address>` with the world otherwise. Keys are qualified by
corpus as well as address (the 1a M3 collision; sci-cf4d58 keeps its other items).

Pins (kernel §5.4): `_world_inputs` already builds a pin for every session mount, and every
captured holder is a session mount. The plan asserts it with a test over the overlapping
fixture rather than changing it.

### 5.5 The retraction-enumeration rebinding

`SYMBOL_FIELDS["enumerate_retractions_v2"] = "retraction"` **replaces** the v1 entry (the
kernel's §8: adding beside it would rebind silently by dict order). Every epoch science
builds from then on carries v2's fold; v1 stays installed by `install_shipped_world_rules`
for the epochs that name it, so retained epochs still open and validate. `epoch_currency`
reuses a current epoch rather than rebuilding, so a world whose current epoch is v1-bound
keeps it until something moves; `science epoch` after a mount change builds the v2 one. The
1b fixture's worlds are built after the rebinding and never hold a v1 epoch, so no test
exercises a mixed world; the kernel's W19 arms cover that.

### 5.6 Supersession and the current publication

For a pin *P*, science reads its marker's `(view, destination)` address from the copy it
holds (the marker's coordination address) and the world its marker names; the **address
group** is keyed by `(world, view, destination)`: a marker from another world claiming the
same view and destination is a different publisher's publication and forms its own group,
so one `publication_tip` call never mixes two worlds' roots. Science computes the **current
publication** for the group with the kernel's `publication_tip` over the **authorized
roots**: the registry roots whose marker names that `(world, view, destination)`, whose pin
is origin-confirmed to that world (commons §10.2: a transition uses only links from markers
confirmed to the same world as *P*'s), and whose pin is in the **established state**:
`mounted`, or `retired`. A `fetched` pin is a candidate that was refused or never reached
admission and an `admitted` pin is a crash the reconcile step resolves first; neither feeds
the established state, so a refused sibling cannot become the tip, make a later evaluation
divergent, or trigger a retirement. A candidate joins the fold only in its own preflight
(§5.7), as the one extra root beside the established ones. A retired pin's copy stays on
disk under the registry (commons §10.1: what was shared cannot be unshared, and the order of
a chain is readable only through held markers, kernel §7); it is read for links in this
classification and is never mounted. A root whose pin is unsourced, recommended, or confirmed
to another world is held but supplies no link.

The outcome is one of: *resolved* (one tip; *P* is the tip or is superseded by it through
held links), *divergent*, or *unresolved*. The last two are told apart by **named
ancestry**: for each tip, its ancestry is the set of `(corpus_id, marker uid)` pairs
reachable from its own pair through `supersedes_markers`, followed through the markers of
the established authorized roots where a named pair is held and keeping an unheld named
pair as a member of the set. Two tips are *divergent* iff their ancestries intersect
(siblings under one predecessor, held or not; the kernel returns `DivergentPublication` for
any two tips, so the distinction is science's), and *unresolved* otherwise (some tip names a
pair no authorized pin records, and the chain needs that publication). So P3 and P3′ both
naming `(P1, m1)` are divergent at a reader that never adopted P1, as they are at one that
retired it; and with P1 and P3 held, a P5 naming an unheld P4 is unresolved, not a fork.
Retired roots' copies still supply the links of longer chains. Science names a missing link
as the pair the tip's `supersedes_markers` carries: the corpus id and marker uid of the
publication whose adoption, from a location bound to that world, would connect the chain.

**One view, two destinations.** A publisher may publish one view to two destinations; the
marker address digests the destination, so the two publications are two chains with no
supersession link between them. Such a pair is **admitted and reported**, not refused
(review round 5's ruling, rejecting this document's earlier `duplicate-publication`
refusal): two revisions published to different destinations can select disjoint records,
and shared records may carry the same origin attribution, which the kernel's rule 3.2
resolves without any supersession; a refusal keyed on view and destination alone would
narrow the overlap the approved design permits. What the kernel refuses stays refused: a
record the two carry under *different* claims is `attribution-ambiguous` at `publish`, and
since neither `supersedes_markers` names the other there is no link to adopt and no
retirement route (each chain is resolved at its own tip). `show` reports, for a pin whose
group has another mounted group of the same world and unpinned view, that the two chains
are unlinked and that a record they attribute differently cannot be published while that
holds; `publish`'s `attribution-ambiguous` detail says the same when a claimed marker's
`supersedes_markers` is empty (§5.8). That limitation is accepted with the ruling, and is
the cost of not refusing legitimate overlap.

**The current publication under an unresolved outcome.** `publication_tip` sees the
unconnected ends as two tips, and the held marker set alone cannot say which was current
before the gap arrived: P1 then P3, and P3 then P1, leave the same set. Nor does the order
of mounting alone: with P1 mounted, then an unconnected P4, then P2 superseding P1 while P3
is still missing, the tips are P2 and P4, and "the earliest mounted tip" would move current
to P4. The rule is a **fold over the ledger's sharing lines in replay order** (`(at, session
id, ledger position)`, a total order, so two adoptions within one second are still
ordered; across two sessions a same-second pair is ordered by the random session id, not by
arrival, a narrow limitation this document keeps rather than adding an ordering mechanism:
it can change the displayed `current` of an *unresolved* group, which authorizes no
retirement, and §5.9 tests it instead of avoiding it), read
through the kernel's ledger reader without writing anything, for the `mounted` lines of
the group's established authorized pins, in that order: current starts empty; a line whose
publication supersedes the current one, transitively through the markers of the
established authorized roots **seen so far**, advances current to it; a line for a
predecessor of current (superseded by it) leaves current where it is; a line for a
publication connected to current in neither direction leaves current where it is (when
nothing is current yet, it becomes current); and after each line, current advances again
while some publication seen so far supersedes it. `retired` lines are not consumed, and
current never lands on a retired publication, since retirement runs only on a resolved
group whose fold ends at its tip. So in the example current goes P1, stays P1 at P4, moves
to P2, and reaches P3 and P4 only once P3 arrives and connects them. `current` is unmoved
whichever end of a gap arrives second (§5.9's arrival-order test asserts both orders), with
the one qualification above: two sessions mounting the two ends within one second are
ordered by session id, and the displayed `current` of that unresolved group follows that
order. The **established set itself** is derived the same way, by folding the same lines in memory
under `apply_line`'s state rule rather than by reading the registry's pin files, so that
`show`'s answer does not lag a pin write that crashed after its line; `adopt` has replayed
before it folds and reads the same. No `current` is stored (§3.3): it is a function of held
markers, bindings and the ledger's order.

**An unrecoverable gap.** The kernel's attribution fold (its §7 rule 3.3) reads the markers
of captured, mounted replicas only; a retired copy science reads for classification is
invisible to it. A chain whose only connection between two mounted publications runs through
a retired one is therefore resolved for science and ambiguous for `publish`, and retirement
is irreversible, so nothing can repair it. The preflight (§5.7) refuses a candidate whose
chain to current, or to any mounted publication of the group, passes through a retired
marker: `adopt-conflict` with rule `chain-retired`, naming the retired intermediate; the
candidate stays `fetched`. This is the late-kept-predecessor case: with P1 → P2 → P3 held as
P2 retired and P3 mounted, adopting P1 under `keep` is refused rather than mounted into a
pair `publish` would refuse `attribution-ambiguous` on every shared record.

### 5.7 Supersession preflight and retirement

**Order of an `adopt` invocation.** (1) Reconcile **completed effects only**: pins the
kernel lists admitted are marked `mounted`, and pins whose kernel status is `retired` are
marked `retired` through the door's idempotent re-ledger (below); a corpus whose status is
`departed` is reported as its own Finding and never sent to the door. Nothing new is retired
here. (2) The candidate: target state, fetch, the admission checklist (§5.1), the preflight,
admission and the `mounted` mark. (3) Retirement re-evaluation over the established state
**with the candidate mounted**, so that the candidate's own requirements (its attribution
entries, its chain) count before anything is retired: a candidate Q whose attributions name
P1 keeps P1, and a sweep before Q's admission would have retired P1 irreversibly and left
Q's carried records unable to count under the Carried branch. When the target is already
mounted, step (2) is a no-op and step (3) still runs: that is the recovery path for a crash
after a mount and before a retirement. Every read in step (3) is by root from the sharing
registry, as the checklist's are (§5.1): the session's mounts are fixed at open and do not
hold the candidate, so a mounted publication's attribution entries (rule 3) and "no other
live mounted corpus holds it" (rule 4) are read from the registry's roots, not from
`ctx.mounts()`.

**Preflight, before admission.** `publication_tip` reads the roots it is given and needs no
admission, so `adopt` computes §5.6 over the `fetched` candidate's root plus the group's
established authorized roots after the admission checklist (§5.1) and before the admission
door. A *divergent* outcome refuses `divergent-publication`, naming the sibling tips; the
candidate stays `fetched` and nothing is admitted, which is commons §10.2's letter ("a
divergent sibling among authorized links leaves the update unresolved and the candidate
`fetched`"). Without this, two authorized siblings with equal shared content would pass the
checklist, both mount, and nothing could remove either. A chain through a retired marker
refuses `adopt-conflict` rule `chain-retired` (§5.6). A *resolved* or *unresolved* outcome
admits and mounts the candidate; *unresolved* leaves `current` where §5.6's fold puts it and
`show` names the missing link.

**Retirement re-evaluation, on every `adopt`.** Retirement is not tied to the candidate
being the tip. In step (3), `adopt` re-evaluates every address group of the established
state: for each `(world, view, destination)` with a *resolved* outcome, every mounted
publication on the chain other than the tip, in chain order from the oldest, is retired
unless it is **required** (below). This covers the
cases where the arriving corpus is not the tip: adopting the missing P2 after P1 and P3
resolves their chain, and **both P1 and P2** are retired by that invocation unless required
(P2 is on the chain and not the tip; the rule retires every non-tip publication, not only
those mounted before); a crash after P3 was mounted and before P1 was retired is recovered
by the next `adopt`, whichever corpus it names; and the pending retirements of the interval
before the kernel door (§7) are made by the first `adopt` after the retirement tail lands.
An `adopt` naming an already-mounted corpus runs the re-evaluation first and refuses
`already adopted` only when it wrote nothing; when it retired something, the invocation is
that recovery and reports the `retired` blocks, as the reconcile-and-return path already
does for `mounted`. A reader who adopts a predecessor after its successor to read a record
the successor dropped must list it in `keep` **before that `adopt`**, exactly as commons §3
says for adopting a successor: the same invocation retires it otherwise. Every `adopt` that
retires reports, with each `retired` block, that the session's mounts are fixed at open and
the remedy is to reopen and run `science epoch`, as the `mounted` block does today.

**Writes over a retired corpus refuse until the session reopens.** The session's mounts
are fixed at open, so after an in-session retirement the read views still hold the retired
corpus, and a later write in the same service session could depend on a record only it
holds: the dependency would vanish at the next open and P1 cannot be readmitted. A remedy
printed in a report does not prevent that, so the enforcement is on the two write routes
that reach records outside the write root:

- **Citing writes** (`spec`, `run`, `assess`, `verify`, `fetch`) resolve every cited record
  through `ReadContext.cited`, which gains the check: the holding corpus's kernel status
  must be live, else `corpus-retired`, naming the corpus, the record and the remedy (reopen
  the session). The kernel's `MountCitations` reads the fixed roots and checks no status,
  so science's check is the one that stands. `mount_holding` is a read route (`belief`,
  `next`, `publish-preview`'s dataset rows) and gets no guard.
- **`publish` and `publish-preview`** cite nothing through `ReadContext`: the kernel's
  `publication_preview` selects over the current epoch, whose coverage in the retiring
  session still names P1, captures P1 by presence alone, and attributes a record it alone
  holds to `(P1, m1)`, an origin the reader has retired; the kernel checks admission, not
  liveness, and the registry's own docstring calls a retired corpus's continued presence in
  a wider epoch intended. Science therefore refuses `corpus-retired` before
  `writer.publish` and before the preview when any corpus in the session's ids is not live
  by kernel status.

Reads stay as they are until reopen: a belief, `next` or `show` over the stale mounts
answers from records that are still readable, and the reopen remedy is in their reports.
Two read-side consequences are stated rather than guarded: `dataset_at`, the duplicate
check `dataset` runs over the read views, excludes holders that are not live, so a dataset
only P1 declared can be declared again in the retiring session (its address is content-
derived and equal), which is the recovery a retirement makes necessary; and the vocabulary
route (`claim` and `spec` resolve terms through the profile's dataset-bound lists over the
read views) resolves against a retired holder until reopen and mints no record dependency,
while rule 4's walk follows relations and facet references only and never a profile's
vocabulary binding, so a successor that dropped a vocabulary dataset would retire its
holder and the reader re-declares the bytes with `dataset` afterwards; the fixture keeps
the vocabulary datasets in P3 and the gap is recorded here, not closed.

`science epoch` is not a session command: it runs in the CLI process over a fresh
`load_config`, which mounts only `mounted` pins, so after the retirement it builds over the
live set and succeeds, and the service session's belief reads then refuse `epoch-stale`
until reopen, since its session ids still hold P1. The kernel's `CoverageNotLive` is
reachable only when a retired corpus is still configured, which the loader never does for
a registry pin, so `build_over` does not normalize it.

The coordination commands (`project`, `question`, `hypothesis`, `task`, `decide`, `reuse`,
`revise`, `project-select`) resolve through the coordination resolver over every configured
root, not `cited`; they cannot reach a retired publication today only because a
publication carries world kinds, the marker and act reports, never coordination kinds. That
invariant is what closes the route, and a publication that carried coordination kinds
would reopen it.

The guard ships in the overlap half (§7), where it is inert since nothing can retire, and
its gate runs on the unkept branch once the door lands: in one session, an `adopt` that
retires P1, then `verify` of *A*'s assessment, the one record P1 alone holds there; the
second refuses `corpus-retired` before writing anything. A `spec` cannot serve as the gate:
its target and dataset are carried by P3 and resolve there.

A predecessor is **required** when any of these holds:

1. **`keep`**: its corpus id is in the configuration's `keep` list **as loaded at session
   open**. Configuration is read once per process (each CLI command's session, and once for
   the service process that runs the writes), so an entry added to the file is seen only by
   a session opened after the edit; commons §3's "set before adopting a successor" means
   before that session opens. Because retirement is irreversible, step (3) refuses to retire
   anything, with `config-stale` naming the file and the remedy (restart the service, rerun
   `adopt`), when the configuration file's bytes differ from those the session loaded; the
   adoption itself stands. Every retirement report prints the `keep` list it was evaluated
   under;
2. **chain retention** (the kernel's §7 and §8): some older publication on the same chain is
   required by rule 1, 3 or 4, so every publication between it and the tip stays mounted,
   because the attribution order of their shared records is readable only through held
   markers and retirement is irreversible;
3. **attribution**: a mounted publication's attribution entries name it (its `corpus_id` as
   an origin);
4. **dependency**: a record in the reader's write root, published or not, has a required
   dependency closure reaching a record that no other live mounted corpus holds with equal
   content identity. The closure is the kernel's publish-act walk (`closure_missing`, iterated
   to a fixed point over the write root's records and what it reaches) **plus the stored
   facet references the walk does not follow**. Those are real dependencies that are not
   relations on the record: the base contract declares `executes` (run → analysis-spec) as a
   world relation, but `stored.run_node` and `assessment_node` emit no such relation, and the
   spec is named only in the run facet (`spec`) and the assessment facet (`spec`, `run`,
   `proposition`); a verification names the two runs it compares in its facet; a spec names
   its dataset roles and its `target` proposition in its facet, and `analysis_spec_node`
   emits no relation at all (the contract's `targets` relation, spec → proposition, is
   declared and never emitted, like `executes`). A successor that keeps an assessment and its
   run and drops their spec passes the publish act's closure check, and `verify.handle` needs
   that spec (`ctx.cited(spec_ref)`) to replay; a successor that keeps a dataset and drops
   the proposition a reader's standalone spec targets passes it too. The walk therefore
   follows, beside `WORLD_RELATIONS`: an assessment's `spec`, `run` and `proposition`; a
   run's `spec`; a verification's two run refs; a spec's dataset roles **and its `target`**;
   a correction's target. A verification's optional `supersedes` and a spec's `supersedes`
   (a predecessor's identity) are **not** followed: `verify.handle` reads neither to replay,
   and a predecessor spec is history, not an input. The plan tests two cases, both gates on
   the retirement tail (no
   retirement ships before they pass): the **spec-drop case** (*B* holds an unpublished
   verification of *A*'s assessment, *A*'s successor keeps the assessment and run and drops
   the spec, and P1 stays mounted as `kept: dependency (<spec address>)`) and the
   **spec-only case** (*B* has authored a spec over *A*'s proposition and no assessment,
   *A*'s successor keeps the dataset and drops the proposition with everything that relates
   to it, and P1 stays mounted as `kept: dependency (<proposition address>)`).

A predecessor that is required stays `mounted`; `adopt`'s report names it with its reason,
and `show` reports the same (§5.8). An unrequired predecessor is retired through the kernel
door (`ScopedWriter.retire`, `beliefs-c0d952` → `beliefs-a989fb`), which ledgers `retired`;
`apply_line` folds the line to the pin's `retired` state, and the loader stops mounting it
(`mounted_roots` already selects `mounted` only). The crash between the line and the pin
write is `replay`'s to repair, as for every other transition. The crash between the kernel's
status write and the line is the door's: science cannot ledger `retired` itself
(`record_sharing` admits `bound` and `mounted` only, and `World._terminal` refuses a second
status for the corpus), so this document states the requirement on the door
(`beliefs-c0d952`) rather than a mechanism: the door is **idempotent**, ledgering `retired`
without a second act when the corpus already carries a `retired` status, and `_reconcile`
calls it for every `mounted` pin whose kernel status is known and not live, as it ledgers
`mounted` from admissions today. Whether a different actor's retry is accepted is the
kernel design's call; science's reconcile runs under the session's actor and accepts the
door's refusal as a Finding naming the corpus.

An *unresolved* address group retires nothing; `show` names the missing link and `current`
stays where §5.6's fold puts it.

Until the kernel door lands, this rule is implemented up to the retirement call: the
preflight, the chain, the required set, the re-evaluation and the reports are computed and
tested, and the plan's retirement step is blocked on `beliefs-a989fb` (§7). Nothing ships a
retirement by another route. In that state a re-evaluation that finds an unrequired
predecessor leaves it `mounted` and reports a Finding, `retirement pending: the kernel's
retire door (beliefs-a989fb) has not landed`, and `show` reports `retention: pending (no
door)` for it; the adoption itself has succeeded and is not misreported as a refusal. This
behaviour is on `main` between the overlap half's merge and the retirement tail's (§7), and
the first `adopt` after the tail lands retires what was pending.

### 5.8 `show`

`show --corpus-id` gains:

- a `supersession` block: the pin's `(view, destination)`; the current publication for it
  (corpus id and marker, or `divergent` with the sibling tips, or `unresolved` naming the
  marker uid whose publication would connect the chain); whether this pin is the tip, is
  superseded (by which), or is a sibling;
- a `retention` row when the pin is superseded and still mounted: `kept: configuration` |
  `kept: chain (for <corpus>)` | `kept: attribution (named by <corpus>)` | `kept: dependency
  (<addresses>)`, every reason that applies; and `retired` when the kernel's status says so;
- the pin block's `keep` row reads the configuration.

The kernel's `attribution-ambiguous` refusal (its §7 rule 3.4) reaches science through
`publish` and `publish-preview` as a `PublicationRefused` carrying the distinct claims in
`field` and the holders in `corpus_ids`. Science's refusal detail renders the claims as
`<origin corpus>:<marker>` pairs and names the link to adopt: `supersedes_markers` entries
are `(corpus_id, marker uid)` pairs, so the held tip's marker already names the corpus id
and marker of the publication whose adoption, from a location bound to that world, would
connect the claims. `show` of either claimed pin reports the same pair in its `supersession`
block (its *unresolved* outcome, §5.6). When a claimed marker's `supersedes_markers` is
empty, the detail says so instead of naming a link: no held marker orders the claims, and
the record cannot be published while both carriers are mounted (§5.6, one view at two
destinations).

### 5.9 The fixture and the decisive cases

The 1b fixture extends `helpers/commons.py` from `build_derived`:

1. `build_published_b`: *B* publishes its project to `LOC_B`, P2 (carrying *A*'s
   proposition, dataset, spec, run and assessment, attributed to P1).
2. `build_a_bound_b`: *A* binds `LOC_B` to *B*'s world.
3. `build_overlapping`: *A* adopts P2 and reopens; `science epoch` captures an epoch over
   *A*'s write root and P2. **Overlap, first half:** the epoch's address map holds each of
   *A*'s shared records once with two holders; `belief` over *A*'s proposition gathers *A*'s
   assessment once; with `accept = []`, the context's excluded lines are exactly two: P2's
   copy of *A*'s assessment, worded as a copy that counted through *A*'s write root, and
   *B*'s own derived assessment, a record excluded with world *B* (`excluded` lists the
   selection domain only: assessments, verifications and retractions, kernel §6, so the
   proposition, datasets, spec and run produce no line); with `accept = [B]`, *A*'s own
   assessment counts through the write root, P2's copy of it is the one excluded line, and
   *B*'s derived assessment counts.
4. `build_updated`: *A* revises project `a`'s query from `kinds` to an `addresses` clause
   naming **P1's selection minus *A*'s assessment**: *A*'s proposition, observed dataset,
   the two vocabulary datasets (`concepts.txt`, `levels.txt`, which P1 carries and *B*'s
   mounted vocabulary declarations rely on), spec and run. *A* republishes to `LOC_A`, P3,
   whose marker supersedes P1 (the revision keeps the unpinned view address, and the publish
   door names P1 from *A*'s binding tips) and no longer carries *A*'s assessment. **This is
   the update that drops exactly one record.** The dropped record is the one *B*'s
   unpublished verification targets, so *B* depends on it. The query names addresses rather
   than kinds because, with P2 mounted at *A*, a kinds query would also select *B*'s spec and
   run from P2 and P3 would carry them back to *B* attributed to P2: a second scenario (own
   records returned in another publisher's carrier) that the milestone does not set out to
   show and that would muddy the second-half assertions.
5. `build_b_updated`: *B* adopts P3. **Pinned derivation:** P1 stays `mounted`, `adopt`'s
   report and `show --corpus-id P1` say `kept: dependency (<A's assessment address>)`, and
   P3 is current; *B* reopens and captures an epoch over its write root, P1 and P3.
   **Overlap, second half:** the records P1 and P3 share read once (one address-map entry,
   holders P1 and P3), and *B*'s belief and verification over *A*'s assessment still read it
   from P1.
6. `build_b_updated_unkept`, the same with *B*'s verification absent (the fixture
   branches before `build_verified`), is built in the overlap half: before the door it
   carries the pending-door report gates, and once the door lands its retirement assertions
   run there: P1 is retired, its line is in the ledger, its pin is `retired`, and the next
   open mounts P3 only. Beside it, the three
   retirement gates of §5.7: the **spec-drop case** (P3 keeps *A*'s assessment and run and
   drops the spec; *B*'s verification keeps P1 as `kept: dependency (<spec>)`), the
   **late-link case** (*B* adopts P1 and P3 of a chain P1 → P2 → P3 with P2 absent, in both
   arrival orders: the outcome is *unresolved*, `current` is the first-mounted end either
   way by §5.6's fold, nothing is retired; *B* then adopts P2, the chain resolves, and P1
   and P2 are both retired by that `adopt` although P2 is not the tip), the **retry case**
   (a crash after P3 mounts and before P1 retires; `adopt` of P3 again retires P1 and
   reports it rather than refusing), the **post-retirement sibling** (after P1 is retired, a
   sibling P3′ of P3 arrives: the preflight reads P1's retired copy, classifies the pair
   *divergent*, refuses `divergent-publication` and leaves P3′ `fetched`), the
   **late-kept predecessor** (P2 retired, P3 mounted, P1 adopted under `keep`: refused
   `adopt-conflict` rule `chain-retired` naming P2, P1 left `fetched`), the
   **requirement-before-sweep case** (P1 pending retirement when Q, whose attributions name
   P1, is adopted: Q mounts, P1 stays `kept: attribution (named by Q)`), the **chain
   retention case** (P1 → P2 → P3 with P1 required by `keep` or by *B*'s verification: the
   re-evaluation keeps P2 as `kept: chain (for P1)` and retires nothing; the requirement
   released, one `adopt` retires both), the **configured keep case** (P1 listed in `keep`
   before the session that adopts P3: `kept: configuration`; the same adoption without the
   entry retires it) and the **stale configuration case** (the file edited after the
   session opened: the adoption stands, retirement refuses `config-stale`, nothing is
   retired). The late-link and chain cases need a three-link chain, which the base fixture
   lacks (step 4's P3 supersedes P1 directly): *A* publishes twice more to `LOC_A` on the
   unkept branch, and "both retired" holds there; on the main branch *B*'s verification
   keeps P1 by rule 4. Two fold cases run before the door: the
   **disconnected-then-connected order** (P1, then an unconnected P4, then P2 superseding
   P1 with P3 absent: current is P2, not P4), **two adoptions in one second** in one
   session (current follows ledger position, not corpus-id order), and **two sessions
   mounting the two ends of a gap within one second** (the test seams the ledger's clock
   so both `mounted` lines carry one stamp; current follows the session-id order, the group
   is unresolved, nothing is retired). The preflight is also tested before
   the door: two sibling republications of P1 to the same destination while P1 is mounted,
   the second refused `divergent-publication` and left `fetched`; the same pair at a reader
   that never held P1, refused the same way (named ancestry); and a refused sibling left
   `fetched` neither changes `show`'s current nor makes a later evaluation divergent. The
   1a conflict fixture (`build_conflicting`: *A*'s second publication of project `a` to
   `LOC_A2`, equal content; *B* adopts P1 from `LOC_A` and then P1′ from `LOC_A2`) now
   **passes** the checklist and mounts; `show` of either pin
   reports the unlinked chain; and *B*'s `publish` of a view reaching a record both carry
   under different claims refuses `attribution-ambiguous` with the detail that no held
   marker orders them (§5.6). An equal-content republication passing the checklist is also
   shown by the main fixture's P3. The checklist's
   other rules get one hand-made candidate each: a copy whose record differs in body
   (`content`), a copy carrying a write-root record's live address as a deprecated id
   (`deprecated-key`), and a redirect published as a successor, new live address with the
   old in `deprecated_ids` under the same uid (`uid-corruption`, the case kernel §10 item 2
   says a live-id comparison misses).

   Two reports get gates of their own: `publish` at *B* in the late-link state (P1 and P3
   mounted, P2 absent) refuses `attribution-ambiguous` with the rendered claims and the
   named `(P2 corpus, marker)` pair; and, before the door, the `retirement pending` Finding
   and `show`'s `retention: pending (no door)` row on the **unkept branch** (on the main
   fixture *B*'s verification requires P1, so its row is `kept: dependency` and nothing
   awaits the door), plus one assertion that `SYMBOL_FIELDS` names
   `enumerate_retractions_v2` and not `enumerate_retractions`. The write-guard gates of
   §5.7 run once the door lands, on the unkept branch: retire P1, then `verify` of *A*'s
   assessment refused `corpus-retired`; and `publish-preview` and `publish` in that session
   refused `corpus-retired` naming P1.

   The Carried content check (§5.4) runs under none of the fixture's cases: at *A*, origin
   P1 is not pinned; at *B*, neither P1 nor P3 carries attributions. It gets its own unit
   test in `test_acceptance.py`: a hand-made carrier whose copy of an attributed address
   differs from the mounted, pinned origin's copy does not count, and an equal copy does.

Belief on both sides is compared over the same pins and the same policy, read as commons §9
item 5 means it: each side evaluates under its own policy, and the comparison is of what both
sides gathered. The test asserts that the shared records' gathered identities (their content
identities and assessment identities) are equal on both sides, that each side's context
names the shared addresses it read from more than one holder, and that each side's policy
statement is the deterministic statement of its own inputs. The two statements are not
asserted equal: `own_roots`, `pins`, `carriers` and `accept` differ between *A* and *B* by
construction.

The window between the kernel's status write and the door's `retired` line is the door's
to keep atomic (§7): in it `load_config` would still mount a kernel-retired corpus at the
next open, and what the kernel does with an epoch coverage naming a retired corpus is not
verified here; the kernel design states both.

## 6. Amendments to the commons design

Made in place, dated, by the plan's final task, as 1a's Deviations were:

- §3 (pin): `keep` is a configuration list, not a pin flag (§3.2).
- §7.4: the configuration gains `keep = ["<corpus_id>", ...]`; the registry's pins carry no
  `keep`; a retired pin's copy stays under the registry, read for supersession links and
  never mounted; the current publication is folded from the ledger's lines (§5.6).
- §10: the conflict rule is the kernel's §8 checklist (§5.1), retiring Deviation 3; the
  supersession preflight runs before admission and §10.2's `fetched` stands, a chain
  through a retired marker refuses `chain-retired`, and one view published to two
  destinations is admitted and reported as unlinked (§5.6, §5.7); `keep` takes effect at
  the next session open and a changed configuration file refuses retirement `config-stale`
  (§5.7 rule 1); a citing write or a publish over a retired corpus refuses `corpus-retired`
  until the session reopens (§5.7); the current publication
  under an unresolved chain is the ledger fold of §5.6; an `adopt` reconciles completed
  effects, adopts, then re-evaluates retirement with the candidate mounted (§5.7); the
  in-place content rule (§5.3); chain retention as a fourth reason a predecessor is
  required, and the facet references the dependency walk follows beside the relations (§5.7);
  retirement re-evaluated on every `adopt`, not only at the tip's arrival (§5.7).
- §9: the Carried branch compares content identities (§5.4); Deviation 12's "tying a
  carrier's copy to the origin's content identity per address is deferred to milestone 1b" is
  closed.
- §11: the retirement door row, `beliefs-c0d952` / `beliefs-a989fb`; the Deviation 3
  sentence under §10.
- §12: the 1b amendment paragraph recording what the fixture shows and what waited on the
  door.

## 7. Kernel dependency

Retirement needs `ScopedWriter.retire(corpus_id, *, evidence)` ledgering `retired`
(`beliefs-a989fb`, waiting on the design `beliefs-c0d952`, which nothing has started).
sci-9104fb takes a dependency on `beliefs-a989fb`.

**The milestone lands in two merges.** One plan with two phases: the **overlap half** (§5.1,
§5.2, §5.4, §5.5, §5.6, §5.7 up to the retirement call with the pending-door Finding and
the write guards, inert until the door, §5.8, the fixture through step 5 and the
construction of step 6's unkept branch with its pending-door report gates, and the §6
amendments that do not describe retirement) is executed and merged to `main` without
waiting on the kernel; the **retirement tail** (the retirement call through the door,
`_reconcile`'s `retired` mark, step 6's retirement assertions and the retirement and
write-guard gates, the §6 amendments to §10 and §12 that describe retirement) is one plan
task blocked on
`beliefs-a989fb`, revised against the merged kernel design before it starts rather than
guessed now, and merged second. The goal sci-9104fb closes after the second merge. Rejected:
one branch held open until the door lands, which would hold the 1a follow-ups (§9) behind a
kernel design no one has started and leave the overlap half, which is useful alone,
unmerged. The cost of the chosen shape is §5.7's pending-door behaviour on `main` for the
interval, which `show` and `adopt` name rather than hide.

## 8. What is left to the builder

- The exact placement of the content-identity cache (`Carrier.content` vs. a per-context map
  on `ReadContext`), as long as each holder's records are read once per context.
- How the dependency walk (§5.7 rule 4) is composed: `closure_missing` iterated by science
  with the facet references read through `stored`'s decoders, or a kernel idea asking the
  publish act to follow the same references (the gap between the declared `executes`
  relation and the emitted records is a kernel observation worth filing either way).
- Report block shapes (`KeyVals` rows and their labels), within §5.8's content.
- The fixture's snapshot names and the split of `test_commons_1b.py` into cases.
- Refusal message wording, within the codes and data fields fixed above.

## 9. Sequencing with the 1a follow-ups

sci-6d4286, sci-347a36 and sci-cf4d58 edit `adopt`, `show`, `acceptance` and `sharing` and
are scoped as direct tasks. They stay separate and run after the overlap half merges, so that each
lands against the 1b shapes rather than being redone; this document notes where 1b touches
their items (§5.4 takes M3's key collision because the `explain` wording changes anyway; the
rest of sci-cf4d58, and all of the other two, are untouched). sci-b979ce (a clean-environment
verification fixture) is independent and may land either side.

## 10. Open questions

1. Whether a required predecessor's `keep` should expire or be re-evaluated when the
   dependency is published (the write-root record leaves for a publication that carries it):
   the closure then reaches the record through the publication, so the predecessor is no
   longer required by rule 4 and the next supersession retires it. This document treats that
   as intended; nothing in commons §10 says otherwise.
2. Whether `show` should also list, for a current tip, the predecessors it retired, from the
   kernel's status records. Deferred: the pin's `retired` state is visible by corpus id.
