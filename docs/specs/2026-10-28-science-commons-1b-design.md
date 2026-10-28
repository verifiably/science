# Science commons milestone 1b — design

**Date:** 2026-10-28
**Status:** draft for review, revision 3. Revision 2 (`3a6fcf8`) followed the builder
check (§5.7's pending-door behaviour, §5.9's query by address and comparison assertion,
§7's two merges). Revision 3 answers review round 1 (reviewer `codex/gpt-6-astra`, verdict
revise: P1 2, P2 3): the supersession preflight runs before admission and a divergent
sibling stays `fetched` (§5.7); the dependency walk follows the facet references the
relations miss, with the spec-drop case as a gate (§5.7 rule 4); retirement is re-evaluated
on every `adopt`, with a retry on a mounted tip (§5.7); `current` under an unresolved chain
is the earliest mounted tip, from the `mounted` line's stamp (§5.6); P3's selection is P1's
minus the assessment, vocabulary datasets included (§5.9). The round's rulings on the
proposed choices (two merges, configuration-owned `keep`, derived current publication)
stand as ruled. Task sci-9104fb (`planned`), child sci-73c80e (science's side of the
kernel's cut 48), idea sci-4a3543 (absorbed, §5.4).
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
reports `keep` from the configuration.

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
| **chain** | for a mounted publication *P*, the publications science holds whose markers connect *P* to the current tip of its `(view, destination)` by authorized supersession links (§5.6). |
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
untouched, as today. When the live corpus is a required predecessor of the candidate's own
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

For a mounted pin *P*, science reads its marker's `(view, destination)` address from the
copy it holds (the marker's coordination address) and computes the **current publication**
for that address with the kernel's `publication_tip` over the **authorized roots**: the
mounted registry roots whose marker names the same `(view, destination)` and whose pin is
origin-confirmed to the world *P*'s marker names (commons §10.2: a transition uses only
links from markers confirmed to the same world as *P*'s). A root whose pin is unsourced,
recommended, or confirmed to another world is held but supplies no link; a marker from any
other world claiming *P*'s address is a different publisher's publication.

The outcome is one of: *resolved* (one tip; *P* is the tip or is superseded by it through
held links), *divergent* (two or more tips of which at least one names, in its
`supersedes_markers`, a marker science holds, so they are siblings under the same
predecessor; `DivergentPublication`), or *unresolved* (two or more tips none of which names
a held marker that connects them: the chain needs a link that is missing, recommended or
confirmed to another world, and science names, from each tip's `supersedes_markers`, the
marker uids it holds no corpus for).

**The current publication under an unresolved outcome.** `publication_tip` sees the
unconnected ends as two tips, and the held marker set alone cannot say which was current
before the gap arrived: P1 then P3, and P3 then P1, leave the same set. The rule is the
**earliest mounted tip**: each pin records `mounted_at`, the `at` of its `mounted` sharing
line, which `apply_line` copies onto the pin as a projection of that line (no new
transition, no new write; `replay` rebuilds it). Among unconnected tips the current
publication is the one with the least `mounted_at`, the least corpus id on an equal stamp.
This keeps `current` unmoved whichever end arrives second, and the arrival-order test of
§5.9 asserts it both ways. When the gap closes, the chain resolves and the tip is current.
No `current` is stored (§3.3): it is a function of held markers, bindings and the ledger's
order.

### 5.7 Supersession preflight and retirement

**Preflight, before admission.** `publication_tip` reads the roots it is given and needs no
admission, so `adopt` computes §5.6 over the `fetched` candidate's root plus the authorized
held roots of its `(view, destination)` after the admission checklist (§5.1) and before the
admission door. A *divergent* outcome refuses `divergent-publication`, naming the sibling
tips; the candidate stays `fetched` and nothing is admitted, which is commons §10.2's letter
("a divergent sibling among authorized links leaves the update unresolved and the candidate
`fetched`"). Without this, two authorized siblings with equal shared content would pass the
checklist, both mount, and nothing could remove either. A *resolved* or *unresolved*
outcome admits and mounts the candidate; *unresolved* leaves `current` where §5.6 puts it
and `show` names the missing link.

**Retirement re-evaluation, on every `adopt`.** Retirement is not tied to the candidate
being the tip. After reconciliation (step 2) and again after any admission in the
invocation, `adopt` re-evaluates every mounted address group: for each `(view, destination)`
with a *resolved* outcome, every mounted publication on the chain other than the tip, in
chain order from the oldest, is retired unless it is **required** (below). This covers the
cases where the arriving corpus is not the tip: adopting the missing P2 after P1 and P3
resolves their chain, and P1 is retired then; a crash after P3 was mounted and before P1 was
retired is recovered by the next `adopt`, whichever corpus it names; and the pending
retirements of the interval before the kernel door (§7) are made by the first `adopt` after
the retirement tail lands. An `adopt` naming an already-mounted corpus runs the
re-evaluation first and refuses `already adopted` only when it wrote nothing; when it retired
something, the invocation is that recovery and reports the `retired` blocks, as the
reconcile-and-return path already does for `mounted`.

A predecessor is **required** when any of these holds:

1. **`keep`**: its corpus id is in the configuration's `keep` list;
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
   its dataset roles in its facet. A successor that keeps an assessment and its run and drops
   their spec passes the publish act's closure check, and `verify.handle` needs that spec
   (`ctx.cited(spec_ref)`) to replay. The walk therefore follows, beside `WORLD_RELATIONS`:
   an assessment's `spec`, `run` and `proposition`; a run's `spec`; a verification's two run
   refs; a spec's dataset roles; a correction's target. The plan tests exactly that case: *B*
   holds an unpublished verification of *A*'s assessment, *A*'s successor keeps the assessment
   and run and drops the spec, and P1 stays mounted as `kept: dependency (<spec address>)`.
   This test is a gate on the retirement tail: no retirement ships before it passes.

A predecessor that is required stays `mounted`; `adopt`'s report names it with its reason,
and `show` reports the same (§5.8). An unrequired predecessor is retired through the kernel
door (`ScopedWriter.retire`, `beliefs-c0d952` → `beliefs-a989fb`), which ledgers `retired`;
`apply_line` folds the line to the pin's `retired` state, and the loader stops mounting it
(`mounted_roots` already selects `mounted` only). Reconciliation covers the crash between the
door and the pin write: `_reconcile` marks `retired` every pin whose corpus the kernel's
status records list retired, as it marks `mounted` from admissions today.

An *unresolved* address group retires nothing; `show` names the missing link and `current`
stays the earliest mounted tip (§5.6).

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
`<origin corpus>:<marker>` pairs and says that adopting the publication whose marker both
claims descend from, from the world those markers name, would order them; it cannot name the
intermediate marker, since the recipient never held it. `show` of either claimed pin reports
the same gap in its `supersession` block (its *unresolved* outcome names the marker uid the
tip's `supersedes_markers` lists and science holds no corpus for).

### 5.9 The fixture and the decisive cases

The 1b fixture extends `helpers/commons.py` from `build_derived`:

1. `build_published_b`: *B* publishes its project to `LOC_B`, P2 (carrying *A*'s
   proposition, dataset, spec, run and assessment, attributed to P1).
2. `build_a_bound_b`: *A* binds `LOC_B` to *B*'s world.
3. `build_overlapping`: *A* adopts P2 and reopens; `science epoch` captures an epoch over
   *A*'s write root and P2. **Overlap, first half:** the epoch's address map holds each of
   *A*'s shared records once with two holders; `belief` over *A*'s proposition gathers *A*'s
   assessment once; with `accept = []`, the context lists P2's copies of *A*'s records as
   excluded copies that counted through *A*'s write root; with `accept = [B]`, *A*'s own
   assessment counts through the write root, P2's copy is listed excluded, and *B*'s derived
   assessment counts.
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
6. Once the door lands: `build_b_updated_unkept`, the same with *B*'s verification absent
   (the fixture branches before `build_verified`), where P1 is retired, its line is in the
   ledger, its pin is `retired`, and the next open mounts P3 only. Beside it, the three
   retirement gates of §5.7: the **spec-drop case** (P3 keeps *A*'s assessment and run and
   drops the spec; *B*'s verification keeps P1 as `kept: dependency (<spec>)`), the
   **late-link case** (*B* adopts P1 and P3 of a chain P1 → P2 → P3 with P2 absent, in both
   arrival orders: the outcome is *unresolved*, `current` is the earliest mounted tip either
   way, nothing is retired; *B* then adopts P2, the chain resolves, and P1 is retired by that
   `adopt` although P2 is not the tip), and the **retry case** (a crash after P3 mounts and
   before P1 retires; `adopt` of P3 again retires P1 and reports it rather than refusing).
   The preflight is tested on the overlap fixture before the door: two sibling
   republications of P1 to the same destination, the second refused
   `divergent-publication` and left `fetched`.

Belief on both sides is compared over the same pins and the same policy, read as commons §9
item 5 means it: each side evaluates under its own policy, and the comparison is of what both
sides gathered. The test asserts that the shared records' gathered identities (their content
identities and assessment identities) are equal on both sides, that each side's context
names the shared addresses it read from more than one holder, and that each side's policy
statement is the deterministic statement of its own inputs. The two statements are not
asserted equal: `own_roots`, `pins`, `carriers` and `accept` differ between *A* and *B* by
construction.

The admission checklist is tested on the conflict fixture already built
(`build_conflicting`: a republication holding the same addresses with equal content now
passes) and on two hand-made conflicts: a copy whose one record differs in body, and a copy
whose record carries the live address of a write-root record as a deprecated id.

## 6. Amendments to the commons design

Made in place, dated, by the plan's final task, as 1a's Deviations were:

- §3 (pin): `keep` is a configuration list, not a pin flag (§3.2).
- §7.4: the configuration gains `keep = ["<corpus_id>", ...]`; the registry's pins carry no
  `keep`.
- §10: the conflict rule is the kernel's §8 checklist (§5.1), retiring Deviation 3; the
  supersession preflight runs before admission and §10.2's `fetched` stands (§5.7); the
  current publication under an unresolved chain is the earliest mounted tip (§5.6); the
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
§5.2, §5.4, §5.5, §5.6, §5.7 up to the retirement call with the pending-door Finding, §5.8,
the fixture through step 5, and the §6 amendments that do not describe retirement) is
executed and merged to `main` without waiting on the kernel; the **retirement tail** (the
retirement call through the door, `_reconcile`'s `retired` mark, fixture step 6, the §6
amendments to §10 and §12 that describe retirement) is one plan task blocked on
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
