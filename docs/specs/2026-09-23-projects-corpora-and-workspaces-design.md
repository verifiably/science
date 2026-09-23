# Projects, corpora and workspaces — design

**Date:** 2026-09-23
**Status:** draft for review. Task `sci-388c18`.
**Scope:** how a research project is manifested at the `science` surface,
given that the kernel has already ruled that a user has one world and a
project is a view. This document settles what the kernel left to the surface:
when a user creates a directory and what it is for; how the current project
is selected in a session; how code and data attach to the world; how export
levels map onto views and destinations; how the biology, health and cancer
levels of the predecessor relate in one world; and the first milestone that
exercises more than one project. It is the design the coordination command
set (the second half of sub-project 4, `project`, `question`, `hypothesis`,
`task`, `decide`) inherits, and it designs no command declaration, no view
query extension and no publish transport.

**Inherits:** the user/autonomy layer design (`beliefs`
`docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md`) §2
decisions 4 and 5, §4 in full, §5.2 and §6; the world-addressing design
(`beliefs` `docs/designs/2026-08-02-world-addressing-design.md`) §2, §3, §5
and §6; the coordination and view kinds design (`beliefs`
`docs/designs/2026-08-31-coordination-and-view-kinds-design.md`) §2 and
§6.3; the command framework design (`docs/specs/2026-08-31-command-framework-design.md`)
§5, §6, §8 and §9.1; and the belief path design
(`docs/specs/2026-09-09-belief-path-commands-design.md`, on the
`dogfood-commands` branch) rulings 5 and 8. Terms used without definition —
world, corpus, view, coordination record, epoch, closure, permit, session
ledger, `Refused(reason)` — are those documents'.

## 1. Problem

The kernel answers the physical-versus-logical question. A user's collection
is one world root with N corpora; a project is "a stored world query plus a
label, never a container"; world facts carry no project field and belong to a
project because its query selects them, so one proposition under two projects
is ordinary and a boundary moves by editing a query, not by moving files
(layer §4.1–4.2). Views are governed records over a closed query language
built at cut 14. Publishing resolves a view at an epoch and mints a fresh
corpus at a destination, and private, shared and community differ only in
destination (layer §6). None of that is reopened here.

Three things the kernel deliberately left to the surface are where the
predecessor's friction would return:

- **When a user creates a directory.** The kernel says a corpus is a
  directory root and that several projects share a corpus freely
  (coordination §6.3). It never says what deserves a corpus of its own. The
  predecessor made every topic a directory because a directory was the only
  unit it had.
- **How the current project is selected.** The framework reserves the view
  slot and its preamble still says no view exists (framework §8, §12.2). No
  command takes a project input and nothing says where the selection lives.
- **Where code and data live.** Views select world records. Workflow
  definitions, scripts and raw data are not world records, and nothing says
  how a repository of code relates to a project.

The evidence that the gap matters is already on disk.

**The predecessor.** Under `proto/projects/`, `health` and `cancer` are two
folders of separate git repositories, each with a `meta` umbrella project
standing in for the parent that was never declared. No health project names a
cancer project as a peer, or the reverse. The dataset record for TCGA exists
six times with six different hashes, across both families; GTEx four times,
COSMIC and FinnGen three. The paper id `Bautista2025` names a circadian paper
in one family and an oncogenic-virus paper in the other. The umbrella
`health/meta` holds myeloma-related questions and propositions
(translational capacity, p53–RP–MDM2 surveillance) while `multiple-myeloma`
holds the datasets and evidence they would draw on, with no link between
them. The commons, peers and registry sync — three mechanisms — did not
produce one world; they produced overlays beside local copies.

**The redesign.** The first project recreated on the new stack,
`natural-systems`, is its own repository with no world configuration, no
corpus and no view. Its questions live in a framing spec and its commitments
in a preregistration JSON file under `freezes/`. Nothing there imports the
predecessor, which is right; nothing there is in the world either. That is
the redesign's first partial silo, formed two weeks in, and it formed because
nothing said where a recreated project's records go.

## 2. Decisions

Rulings from the 2026-09-23 session, recorded so they are not re-derived.

1. **Three units where the predecessor had one.** A **corpus** is the
   provenance and lifecycle boundary and is physical. A **view** is the
   attention boundary and is a governed record. A **workspace** is a git
   repository of code, workflow definitions and scratch data, is physical,
   and is not a project. §3.
2. **A user never creates a directory to start a project.** Starting a
   project is minting a `project` view in a session and continuing to write
   into the working corpus. A corpus is created for a provenance reason
   (§3.1), never for a topic.
3. **Project selection is a session property and is never derived from the
   working directory.** No configuration is discovered upward from `cwd`;
   the launcher takes the world from `SCIENCE_CONFIG` or `--config` and the
   project from an explicit input or the launcher's own default. §5.
4. **A claim that is not in the world is not a claim.** The only way to mint
   a question, hypothesis or proposition is a world session. A
   preregistration file or a framing document in a workspace is a note about
   intent; it binds nothing until it is a record. §3.3.
5. **Biology is a contract, not a project.** The biology level is the
   `domains` a corpus pins. Health, cancer and multiple myeloma are `project`
   views over one world whose queries differ in what they select; containment
   between them is a property of their queries, not a declared parent. §6.
6. **Coordination stays single-homed; reuse is a same-query mint.** A
   question belongs to the project it was minted under and does not move.
   Another project that wants it mints its own view with the same query, in
   one command. Whether this fence bites is measured in dogfood before any
   re-homing family is requested from `beliefs`. §7.
7. **Export levels are views; payload transport is a destination
   property.** "Findings only" and "everything needed to reproduce" are two
   views over one project's world facts. Whether dataset payloads travel is
   decided by the destination kind, never by the selection. §8.
8. **Recreate, never migrate, and choose the second project to exercise
   overlap.** The second project is `health`, viewing the reproduced mm30
   corpus and minting one health-level question over myeloma facts. §9.

## 3. The three units

| unit | what it is | physical? | lifetime | how often it is made |
|---|---|---|---|---|
| corpus | a `nodes` root with a manifest: who wrote into it, which contracts it pins, where it came from (fresh, replica, fork, publication) | yes, a directory under or registered with the world root | years; retired, never edited | rarely: one working corpus per person per world, plus one per adopted publication or fork |
| view | `project`, `question`, `hypothesis`, `topic`, `theme`: a label over a world query, addressed by project identity | no, a governed record in a corpus | as long as the question is live; revised, superseded | constantly, in the same breath as asking |
| workspace | a git repository holding workflow definitions, scripts, environment specifications and scratch data for runs | yes, anywhere the user keeps code | per research program or analysis | when there is code to write |

The predecessor's `science.yaml` project bound all three to one directory:
the directory was the corpus (its `entities/`), the project (its manifest's
`id`) and the workspace (its `code/`, `data/`, `workflows/`). Separating
them is the whole design; the rest of this section says what each one owns.

### 3.1 A corpus is a provenance boundary

A corpus is created when one of these is true, and for no other reason:

- **A new writer.** A person or machine that will write records under its
  own authorship into this world and does not already have a working corpus
  here. One person on one host has one working corpus; a second host that
  writes gets a second corpus, because two writers on one corpus root is the
  single-writer obligation's violation (layer §7.1).
- **An adoption.** A published corpus arriving from elsewhere is admitted
  whole, read-only, as its own corpus (layer §6.3). It is never merged into
  the working corpus.
- **A fork.** `fork_corpus` for a lineage that must diverge, which is the
  kernel's operation and stays rare.
- **A contract boundary that must be pinned differently.** A corpus pins
  its contracts in its manifest, and a body of work that must be typed under
  a different corpus-local contract than the working corpus pins is a
  second corpus. This is the one topic-adjacent reason, and it is a typing
  fact, not an organisational one; the mm30 corpus is this case today.

A corpus is **not** created because a new topic, disease, question or
collaborator appears. Those are views. The test is: if the reason for the
new directory could be expressed as a query, it is a view.

Where the world root lives on a host is one place, outside every code
checkout: a user's world is `$XDG_DATA_HOME/science/worlds/<world id>/` or
wherever `SCIENCE_CONFIG` says, and the working corpus and store are under
it. The belief path measurement's world "beside the main checkout,
gitignored" (belief path §8.1) is a measurement fixture and stays one; a
research world is not under a repository. The reproduced mm30 corpus
currently under the `beliefs` checkout's working tree relocates to the
user's world root before the second-project milestone (§9), by
`replicate_root` and `restore_root`, not by copying.

### 3.2 A view is where attention lives

A `project` is a label and a query with an opaque durable identity
(coordination §3). Everything a person would previously have made a folder
for is one of these:

- a **project**, when there are questions and tasks to hang under it;
- a **question** or **hypothesis**, when there is one thing to settle;
- a **topic**, when the purpose is to find things again;
- a **theme**, when several projects share a framing worth naming.

None of them holds anything. A project's world content is whatever its
query selects at the epoch you are reading; its coordination content is the
questions, hypotheses, tasks, decisions and notes addressed to it. Making a
project costs one act and no directory, which is what makes decision 2
livable: the price of starting a project is low enough that a person makes
one when a question deserves company, and never has to decide in advance.

### 3.3 A workspace is where code lives, and it is not a project

A workspace is an ordinary git repository. It holds what the kernel does
not: Snakemake workflows, scripts, environment definitions, notebooks, the
scratch outputs of runs, and the prose a research program writes for
itself. `natural-systems` is a workspace and stays one.

A workspace attaches to the world at exactly two points, both by content
identity:

- **At `spec`.** Freezing an analysis spec binds the workflow's rendered
  content by digest into the spec's identity (the mm30 record's step 4: the
  rendered Snakefile "is committed, since its digest enters the definition
  snapshot"). The spec record is a world fact; the file it was rendered
  from is in the workspace.
- **At `run`.** The run closure comprises the spec, the code, the
  environment and the parameters (kernel design §3.1). A run record names
  what was executed by digest; the workspace is where the bytes came from.

So a workspace is referenced *from* the world and never the reverse. It
holds no records: a `freezes/*.json` file is a note about what a person
intends to freeze, and the frozen thing is the `analysis-spec` record in
the corpus. The workspace may keep a copy of anything for convenience,
including its own preregistration prose, but nothing in `science` reads a
workspace file as a record, and a run whose spec was not minted is a run
the kernel does not know about.

A workspace is also not a project boundary. One workspace may serve several
projects (the mm30 pipeline serves `multiple-myeloma` and, under §9, a
`health` question); one project may draw on several workspaces. The
relation is through the specs and runs the project's query selects, and it
is computed, never declared.

## 4. What this gives the person at a session

The day-to-day shape, stated once so the sections that follow have
something to be true of:

1. A person opens a session on their world. The launcher reads
   `SCIENCE_CONFIG`; the working directory is irrelevant.
2. They select a project, or none. With none selected, reads see the whole
   world; that is a legitimate state, not a refusal, and it is how a person
   asks "what do I know about PHF19" before deciding which project cares.
3. They ask a question. It is minted under the selected project. If no
   project is selected, minting a view kind refuses `no-current-project`,
   because a question needs an address, and the refusal names the
   selection command.
4. They hold a dataset, freeze a spec against code in a workspace, run,
   assess, verify. None of those acts mentions the project; the records
   are world facts and the project's query selects them or does not.
5. They switch project without leaving the session. The world is unchanged;
   `next` ranks differently because the queue is read through a different
   query.
6. At the end they publish a view to a destination, or not. Nothing else is
   needed to "save the project": every act already left a record.

The predecessor's session began with `cd` into a project directory and could
not see out of it. This one begins with the world and narrows by choice.

## 5. The current project

### 5.1 Selection is a session fact

The current project is a property of the session, held by the launcher and
recorded in the session ledger beside the actor and permit at `session-open`
(framework §5.2), and again on every change. It is never stored in a corpus
— a selection is not a record, and the surface owns no store (layer §2
decision 4, §5.2) — and never read back from anything but the ledger. The exact ledger
entry shape is `beliefs`' and is filed with the coordination command set;
this design requires only that the selection is written where the session's
evidence is, so that a trajectory shows which view each act was taken
under.

The launcher accepts the selection three ways, in this order of precedence:

1. an explicit input at session open (`--project <address>` on the CLI, the
   equivalent MCP session parameter);
2. a `project` command during the session, which rewrites the selection and
   appends the ledger entry;
3. the launcher configuration's `default_project`, an optional key beside
   `domains` in `SCIENCE_CONFIG`, for a person who works in one project for
   weeks.

A project is named by its address, which is its opaque identity, and the
surface resolves a **name** to an address through the coordination resolver
at selection time — one standing tip, or `Refused(divergent-view)`
(coordination §4.4) — and refuses `ambiguous-project` listing candidates
when two live projects share a name. Names are content and may collide;
addresses do not.

### 5.2 Never from the working directory

The launcher does not search upward from `cwd` for a configuration, a
manifest or a project file, and no command reads one. This is stated as a
rule rather than left as an absence because it is the mechanism by which the
predecessor's directories became fences: `science.yaml` was discovered from
`cwd`, so being in a directory *was* being in a project, and a question asked
from the wrong directory landed in the wrong project or nowhere. A workspace
may keep a `science.toml` naming the project its code usually serves, for a
person to read; the launcher never opens it.

The world-addressing design's §6 says `science.yaml` "survives" carrying the
view, coordination, storage and availability. Under the layer design's later
ruling that the surface owns no store, only **availability** survives, and it
survives as `SCIENCE_CONFIG`'s `corpus_roots`: which corpora this host can
see. The other three are records or session facts. This design records that
narrowing for the surface; the kernel document is not amended by it.

### 5.3 Unselected means the whole world

A session with no current project reads through the whole world. This is
deliberate, and it is the opposite of the predecessor's default. The layer
design's "every command reads the world through that view's query" holds
with the whole world as the degenerate view; a refusal here would send a
person back to choosing a folder before they may look, which is the habit
this design exists to end. Write acts on world kinds (`claim`, `dataset`,
`spec`, `run`, `assess`, `verify`) need no project and are not refused.
Minting a view or coordination kind is.

## 6. Biology, health, cancer, myeloma

### 6.1 Biology is the contract

The predecessor took a biology parent as implicit and never declared it. In
this world it is already declared and is not a project: it is the `biology`
entry in a corpus's pinned `domains` (framework §9.1), which activates the
HGNC-bound molecular-entity sort, the gene-axis facet and the protein
operators. A proposition is a biology proposition because it types under
that contract, and every belief computed over it is a biology belief for
the same reason. There is nothing a `biology` project view would select
that the domain does not already define, and making one would recreate the
`meta` umbrellas.

### 6.2 Health, cancer and myeloma are views

`health`, `cancer` and `multiple-myeloma` are three `project` records over
the same world. Their queries differ in what they select, in
`science.view-query.v1`'s four predicates:

- `multiple-myeloma`: `closure` from the myeloma datasets and the
  corpus-local `concept` referents the mm30 contract binds, outward through
  the spec, run and assessment relations, plus `references-term` over the
  myeloma concept list.
- `cancer`: the union of every cancer-type project's clauses, plus
  `references-term` over neoplasm terms when a disease vocabulary is
  bound.
- `health`: `kinds` over propositions and assessments, narrowed by
  `references-term` over disease and process terms when bound, and
  otherwise by `closure` from the datasets the health-level questions
  anchor on.

Containment is then a fact about the queries: `multiple-myeloma`'s
selection is inside `cancer`'s because `cancer`'s clauses include it, and
both are inside `health`'s when `health`'s predicates are wider. Nothing
declares a parent, no record carries a level, and a project whose query
happens to sit inside another's is not subordinate to it in any way the
kernel knows. A `theme` view may name the containment for people —
"disease biology across health and cancer" — and selects the union.

### 6.3 The dependency this names

Distinguishing health from cancer by *what a claim is about* needs disease
terms, and MONDO, EFO and HP remain unmeasured in the biology pack (layer
§4.3 as amended). Until a disease vocabulary is bound, the queries above lean
on `closure` from anchor datasets and on `kinds`, which is coarse and honest:
a proposition reached from a myeloma dataset is a myeloma proposition. The
first health-level question in §9 is chosen so that it can be asked and
selected under that coarse form, and the milestone record states which
predicate each query actually used. Binding a disease vocabulary is the
biology pack's measurement to take when a project needs it, and this design
does not request it.

### 6.4 The friction test

The predecessor's cost was having to answer "is this a health question or a
cancer question" before asking it. Under this design the person asks it in
whatever project is selected; the question is minted there. If it later
proves broader, the broader project mints a same-query view (§7) and the
narrower one keeps its record. World facts the question leads to —
datasets, specs, runs, assessments — carry no home at all and are visible
from every project whose query reaches them. The only decision left at
asking time is which project is selected, and §5.3 makes even that
deferrable.

## 7. Reuse across projects, and the fence that remains

World facts float free; views and coordination records do not. A `question`
is `(project identity, local id)` and that address is durable (layer §4.1),
so a question minted under `multiple-myeloma` cannot later become
`health`'s. The kernel's answer is that `health` mints its own view whose
query is the same — "reuse, never co-ownership" — and the two select the
same world facts.

This design accepts that answer and makes it cheap:

- The coordination command set provides a **same-query mint**: given a view
  address in another project, mint a view of the same kind under the
  current project carrying the same query and a `note` naming the source
  address. One command, one act. The new record is its own; nothing links
  the two in the kernel beyond the note, and nothing needs to.
- The refusal for minting a view kind with no current project (§5.3) names
  this command, because the person who hits it is usually about to ask
  which project a question belongs to, and the answer is "the one you are
  in, and any other that wants it".

The fence is named so it can be measured. If dogfood shows a pattern —
same-query mints outnumbering fresh questions, or a repair that needs one
record under two addresses — that is evidence for a `beliefs` request: a
re-homing revision or a multi-address form for view kinds. Until then no
such request is made; the predecessor's lesson is that the bridge built in
anticipation is the one nobody can remove.

## 8. Export levels

### 8.1 A level is a view

Sharing a project is `publish(view, destination)` (layer §6.1). The
different "levels" a person wants — a findings summary for a collaborator,
a reproducible package for a repository, an archival deposit — are three
views over the same project's world facts, and a project keeps as many as it
needs. Three are named here as the conventional set; a project may define
others.

| level | selects | closure pulls in | for |
|---|---|---|---|
| findings | `assessment`, `verification`, `composite`, and the `proposition`s they name | `analysis-spec`, `run`, `dataset` records, by the closure rule | a collaborator, a GitHub repository |
| reproducible | findings plus every `run`, `analysis-spec`, `source` and `dataset` a selected proposition's closure reaches | nothing further | a repository someone will build on |
| archival | reproducible plus the coordination trail: `question`s, `hypothesis`es, `decision`s addressed to the project | nothing further | a Zenodo deposit, a commons world |

The closure rule (`Refused(closure-incomplete)`) is what makes "findings
only" honest: a person cannot publish an assessment without the dataset
record it was computed over, so the findings level always names its data.
What it does not do is carry the data's bytes, which is the next point.

### 8.2 Payload transport is the destination's

A `dataset` record is a world fact: a declaration with resources, digests
and locators. Its **holdings** — the bytes in the store — are not a record
and are not selected by a view. Whether they travel is a property of the
destination kind:

- a **private directory** destination carries records only, and the
  holdings are already on the host;
- a **git remote** destination carries records only, and the dataset
  records' locators are how a recipient acquires the bytes;
- a **Zenodo deposit** carries records and the holdings of every selected
  dataset, because a deposit that named data it did not contain would not
  be an archive;
- a **commons inbox** carries records, and the commons world's own holdings
  policy decides what it fetches.

This is filed to the publish design (sub-project 5, `beliefs-1a5157`) as a
requirement on its destination kinds, not designed here: the publish act
selects records, and the transport for a destination kind states whether it
carries holdings. Code travels the same way. The rendered workflow's digest
is in the spec's identity and the spec record is selected; the bytes are in
the workspace's git history, and a reproducible publication names the
commit, which the recipient fetches as they fetch a dataset's locator.

## 9. Recreating health and cancer

### 9.1 Principles

- **Recreate, never migrate.** The mm30 rule (reproduction design §2)
  holds for every predecessor project: a record exists in the world only
  if this stack produced it. The predecessor's entity files are heritage to
  read, not input to convert. Six TCGA records become one `dataset` record
  the first time a question needs TCGA, minted from the source, and every
  project that needs it selects it.
- **A reading pass is not a migration list.** Before the second project,
  one bounded pass over `health/meta`, `multiple-myeloma` and the overlap
  inventory produces three things: the three project queries of §6.2 in
  their coarse form, the first health-level question, and the list of
  datasets that question needs held. The pass's output is those records
  and the milestone record; it is not a catalogue document.
- **Start where the overlap already is.** The predecessor's `health/meta`
  holds myeloma-related questions; the reproduced mm30 corpus holds the
  facts. That is the cheapest real test of one world seen from two
  projects, and it needs no cancer corpus that does not exist yet.

### 9.2 The second-project milestone

After the belief path measurement (belief path §8) and beside the
coordination command set's implementation, one milestone with these
criteria, all observable:

1. One world root at the user's data location holding the reproduced mm30
   corpus (relocated per §3.1) and one fresh working corpus.
2. Three `project` records — `health`, `cancer`, `multiple-myeloma` — minted
   in the working corpus, with at least one mm30 proposition selected by two
   of them at the same epoch.
3. One `question` minted under `health` whose evidence path reaches mm30
   facts, and a same-query view of it minted under `cancer` through the
   command of §7.
4. `next` rendering a different ranking under each of the three projects
   and under no project.
5. A `publish` dry run of `multiple-myeloma` at the findings level reporting
   its selection and closure without refusal, or refusing
   `closure-incomplete` with the missing identities listed.
6. A session opened from inside the mm30 workspace directory and from an
   unrelated directory reading identically.

The milestone leaves a record in `docs/plans/`, in the reproduction record's
discipline: predictions before, findings classified after, and every
refusal filed to its owning lane. Its findings size the coordination
command set and decide whether §7's fence needs a `beliefs` request.

### 9.3 What follows it

Only after the milestone: the remaining health and cancer programs are
recreated one question at a time, each as views and records in the same
working corpus, with a new corpus only when §3.1 says so. `cancer/mechanisms/evolution`
and `health/processes/post-acute-infection`, the predecessor's two largest
programs after mm30, are candidates for the first workspaces with real
pipelines after mm30's; which comes first is the person's priority and is
not decided here.

## 10. Guarantees

Each can fail, and each names its check.

| # | guarantee | check |
|---|---|---|
| P1 | No configuration is discovered from the working directory | a launcher test opens a session from a directory containing a predecessor `science.yaml`, a workspace `science.toml` and a stray `corpus.yaml`, and asserts the world, corpus roots and selection equal the explicit configuration's |
| P2 | Minting a view or coordination kind without a current project refuses `no-current-project`; minting a world kind does not | dispatcher tests, both arms, under a session with no selection |
| P3 | The current project is in the session ledger at open and at every change, and an act's ledger entry is attributable to the selection standing when it ran | a ledger test that switches project mid-session and reads the trajectory back |
| P4 | A same-query mint produces a record under the current project with the source's query, and the source is unchanged | coordination command test; the source's tip is asserted unchanged |
| P5 | The unselected session reads the whole world | `next` and `belief` under no selection equal their results under a project whose query is the union of every kind |
| P6 | A workspace file is never read as a record | a run whose spec exists only as a workspace preregistration file refuses at `run` because no `analysis-spec` record resolves, under whatever refusal the belief path's `run` already gives an unresolvable spec; nothing in `science` opens `freezes/` |
| P7 | The second-project milestone's six criteria (§9.2) | the milestone record |

P1, P2, P4 and P5 are the coordination command set's tests to carry. P3's
ledger shape is `beliefs`'. P6 is the belief path's existing behaviour,
restated here because it is what decision 4 rests on. P7 is a measurement.

## 11. What this changes elsewhere

- **The framework preamble** (`commands/PREAMBLE.md`, framework §8) says no
  view exists until sub-project 1 lands. Sub-project 1 landed at cut 14. The
  preamble is corrected to §5's rule: one world, read through the current
  project when one is selected and whole when none is; a question needs a
  project, a fact does not. The framework spec's §8 and §12.2 take a dated
  amendment pointing here.
- **The belief path design's `next`** ("from the current view") takes the
  selection rule of §5 by reference when its spec next amends; its
  behaviour under no selection is §5.3's, which is what it already does.
- **`sci-17851d`** (wire a coordination profile into the launcher config)
  is no longer an idea gated on sub-project 1; it is a prerequisite of the
  coordination command set and is scoped with it.
- **The coordination command set spec** (the second half of sub-project 4)
  inherits §5 and §7 and carries P1–P5. It is written after the belief path
  measurement, per that design's ruling 1.
- **`natural-systems`** gets a task in its own project: attach to the
  user's world — a `project` view, its pilot's questions as `question`
  records, and its frozen manifests as the specs they describe — before its
  record count grows further. The repository stays as the workspace it is.
- **The mm30 corpus** relocates from the `beliefs` working tree to the
  user's world root (§3.1), a `beliefs` operator task, before the
  milestone.
- **The publish design** (`beliefs-1a5157`) takes §8.2 as a requirement on
  destination kinds: each states whether it carries holdings.
- **The predecessor tree** is unchanged. Its retirement design already says
  each project is recreated "when its turn comes"; §9 says how the turn is
  taken.

## 12. Alternatives rejected

- **A directory per project over a world index.** The predecessor's shape
  with a better bridge. World-addressing §2.2 already rejected improving
  the bridge; here it would additionally make the directory the unit a
  person reaches for first, which is the habit that produced six TCGA
  records.
- **A project is a corpus.** Tempting because both have durable identity.
  Rejected by coordination §6.3 (several projects share a corpus; a project
  moves between corpora) and because it would make every topic a writer
  boundary.
- **An inbox or `meta` project as the default home for unplaced
  questions.** Recreates `health/meta` and `cancer/meta`, whose contents
  never left. §5.3's unselected-reads-everything plus a refusal on minting
  is the honest version: look freely, and choose when you write.
- **A parent field on `project`.** A declared tree is a fence a query
  cannot cross and a fact the kernel would have to keep true. Containment
  by query is computed and can be wrong without anything breaking.
- **Discovering the project from `cwd` as a convenience.** The convenience
  is the mechanism of the failure. A default in the launcher configuration
  gives the one-project person the same convenience without binding it to
  a directory.
- **Refusing every read when no project is selected.** Sends a person back
  to choosing a folder before they may look.
- **Requesting a re-homing revision family from `beliefs` now.** No
  measurement yet shows the single-home fence bites; a same-query mint is
  one act; the bridge built in anticipation is the one nobody removes.
- **Anchoring the second project on TCGA.** The six diverging copies make
  it the obvious overlap, but a TCGA-anchored question needs a cancer
  corpus and pipeline that do not exist; health over mm30 needs only what
  is built.
- **A catalogue document of the predecessor families as the first
  deliverable.** Reading is needed; a document that indexes files nobody
  will convert is the migration list in disguise. The reading pass's output
  is queries and records.
