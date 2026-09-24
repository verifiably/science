# The coordination command set — design

**Date:** 2026-09-24
**Status:** draft for review. Task `sci-c5528e`.
**Scope:** the second half of sub-project 4 of the user/autonomy layer design
(`beliefs` `docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md`
§5.1, §8 item 4): the commands that mint and revise `project`, `question`,
`hypothesis`, `task` and `decision` records; the selection of a current project
within a session; how a read finds that selection; the same-query mint; and the
launcher configuration those need. It folds in `sci-17851d` (the coordination
profile at session open) and designs the `write_root` key whose implementation
waits on `beliefs-fe7149`. It designs no view query extension, no publish act, no
priority function and no ledger line shape — the last is `beliefs`', requested
here (§8).

**Inherits:** the projects design (`docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md`)
§5 and §7 in full, and carries its guarantees P1, P2, P4, P5 and P8 (§10 there);
the command framework design (`docs/specs/2026-08-31-command-framework-design.md`)
§3–§9; the belief path design (`docs/specs/2026-09-09-belief-path-commands-design.md`)
§4.8 and §6.3; the coordination and view kinds design (`beliefs`
`docs/designs/2026-08-31-coordination-and-view-kinds-design.md`) §3, §4 and §6.2;
the layer design §4.1–§4.2. Terms used without definition — view, coordination
record, standing tip, `divergent-view`, write class, scoped writer, session ledger,
epoch, `Refused(reason)` — are those documents'.

## 1. Problem

The belief path gave the world its facts. Nothing yet gives a person a place to
put a question. The kernel has had the kinds since cut 14: eight ordinary
coordination kinds under a shipped coordination contract (`contracts/coordination/v2`),
a writer door for them (`mint_coordination`, `revise_coordination` on the scoped
writer), a resolver that finds an address's one standing tip, and a query language
whose `evaluate_query` denotes a view. The surface uses none of it:

- every launcher opens its session with `coordination=None` (`serve.py`, `mcp.py`),
  so a coordination write would reach its act and refuse `CoordinationUnavailable`;
- no command mints a coordination kind, and the only `coordination`-class
  declaration is the synthetic `coord-note` fixture;
- no current project exists in code; `next`'s purpose says "from the current view"
  and scans every stored proposition;
- relative paths inside `SCIENCE_CONFIG` resolve against the process's working
  directory (`config.py`, pinned by two tests), so one file names different worlds
  from different directories — the gap P1 leaves open (projects design §11);
- the preamble still says no project can be selected.

The projects design settled what selection *is*. This document settles how the
surface does it with what the kernel has, and names the three things the kernel
must add.

## 2. Decisions

Rulings from the 2026-09-24 session, recorded so they are not re-derived.

1. **One declaration, one write class, so a verb that differs in class is its own
   command.** The name grammar is one hyphenated word and the CLI is flat
   (framework §3.1). Minting a project is a coordination write, selecting one
   changes session state, and listing them is a read; they are three commands —
   `project`, `project-select`, `projects` — not one command with an action input,
   which would need three write classes on one declaration.
2. **Selection is a new write class, `session`.** It mints nothing and performs no
   kernel act, so it is neither `read-only` nor `coordination`; it changes the
   session and must be ledgered, so it needs a live session and the write path's
   routing. §4.1 adds the class to framework §3.3's closed set.
3. **A project's query is evaluated live, by a `beliefs` seam; publish stays
   epoch-bound.** The kernel evaluates a query only over a published epoch and
   refuses `corpus-drifted` once any corpus moves past it (coordination §6.2;
   `evaluate_query`), and no command may publish an epoch (framework §4.4). Read
   through that rule, a project's `next` would refuse after the first write until
   an operator republished. The queue is attention, not belief input; the argument
   coordination §6.2 gives for live coordination resolution — "no packaging step
   mediates seeing your own task edit" — holds for seeing your own new proposition
   in your project's queue. So the surface requests a live, unpublished selection
   evaluation from `beliefs` (§8, S1), stamped so it can never be mistaken for an
   epoch's; publish keeps the epoch. Chosen by the person over two alternatives
   (§11).
4. **Selection scopes enumeration, never lookup by identity.** A command that
   enumerates world records (`next`) reads through the selection. A command given
   an identity (`belief <proposition>`, `status`) answers for that identity whatever
   is selected. So P5 holds for `belief` by construction, and a person can ask about
   a proposition outside their project without switching.
5. **Writes bind to the session's selection only.** An explicit `--project` binds a
   read invocation (projects design §5.1a step 1); no write takes one. A question is
   minted under the selection standing when it ran, which is what makes the ledger's
   selection lines sufficient attribution (P3).
6. **Both launchers serve the whole service protocol on the socket.** The projects
   design requires `science mcp serve` to bind `service_socket` for the selection
   query. It binds it for writes too: one world has one live session (projects
   design §5.1a), so a CLI write made while an MCP session is live has nowhere else
   to go, and starting `science serve` beside it would be the second writer the
   single-writer obligation forbids. `serve`'s existing refusal on an existing
   socket then enforces the one-session rule for both launchers.
7. **The same-query mint is one act, and the source is named in the new record's
   body.** Projects design §7 asks for "a view of the same kind under the current
   project carrying the same query and a `note` naming the source address. One
   command, one act." A separate `note` record would be a second act, and a
   `note`'s `about` accepts world addresses only (`corpus.py`
   `_validated_coordination_content`), so it cannot carry a `coord:` address. The
   new view's `body` opens with the source's pinned address instead.
8. **Relative paths in the configuration resolve against the configuration file's
   directory.** Refusing them would be stricter and would break every existing
   configuration for no gain in determinism; resolving them against the file makes
   one file name one world from anywhere (P1).
9. **The three `beliefs` seams are requests, filed before the plan** — the live
   selection evaluation (S1), the selection ledger lines (S2), and a public
   enumeration of standing tips by kind (S3). §8 states each requirement; none is
   designed here.

## 3. The commands

Declarations follow framework §3.2. Every coordination record's content is the
kernel's full field set (`contracts/coordination/v2/CONTRACT.yaml`): `name`, `body`,
`author` and `at` on every kind, `query` on view kinds, `status` and `depends` on
`task`, `about` on `note`. The surface fills `author` with the session's actor and
`at` with the act's time; neither is an input.

| command | write class | kind | needs a selection |
|---|---|---|---|
| `project` | `coordination` | `project` genesis | no — the root of its own address space |
| `question` | `coordination` | `question` genesis | yes |
| `hypothesis` | `coordination` | `hypothesis` genesis | yes |
| `task` | `coordination` | `task` genesis | yes |
| `decide` | `coordination` | `decision` genesis | yes |
| `revise` | `coordination` | a revision of any of the above | no — it names its own address |
| `reuse` | `coordination` | the same-query mint | yes |
| `project-select` | `session` | none | no |
| `projects` | `read-only` | none | no |
| `project-show` | `read-only` | none | reads the selection, or `--project` |

`topic`, `theme` and `note` get no command: the layer design's list names none of
them, and each is one declaration away when a measurement wants it.

### 3.1 `project`

```toml
schema_version = 1
name = "project"
purpose = "Start a project: a name and a query over the world."
write_class = "coordination"
output_budget = 4096

[inputs.name]
type = "string"
required = true

[inputs.query]
type = "string"
required = true
doc = "The view query, as YAML or JSON text (science.view-query.v1)."

[inputs.body]
type = "string"
required = false

[reads]
families = ["coordination"]
```

`mint_coordination("project", project=None, content=…)`. The query text is parsed
as YAML (JSON is a subset) before any act, refusing `invalid-input` when it does
not parse to a mapping; the kernel validates it against the query language and the
profile's world kinds at the act. A query is required: a project with no query
would select nothing and read as an empty project, and the whole world is already
what an unselected session reads (projects design §5.3). A fresh world's first act
after opening a session is this command (P2's genesis arm). `body` absent is the
empty string.

### 3.2 `question`, `hypothesis`

The inputs of `project`, minting the kind under the current project:
`mint_coordination(kind, project=<selection>, content=…)`. With no selection each
refuses `no-current-project` before any act (§5.4), and the refusal names
`project-select` and `reuse`.

### 3.3 `task`

Inputs `name` (required), `body` and `depends` (`list-of-string`, each a
`coord:<project>/<local>` address). `status` is `open` at genesis; changing it is a
revision (§3.6). The kernel refuses a malformed or repeated dependency.

### 3.4 `decide`

Mints a `decision`. Inputs `name` and `body`, both required: a decision without its
reasoning is the attributed act minus the part a later reader needs. The layer
design's persisted choice — "a coordination record saying which candidate was taken
and why" (§4.4) — is this command's record.

### 3.5 `reuse` — the same-query mint

Inputs `source` (required, a `coord:<project>/<local>` address of a `question` or
`hypothesis`) and `name` (optional, default the source's name). Resolves the source
to its one standing tip — `divergent-view` refuses — and mints a record of the
source's kind under the current project whose `query` is the source's query
verbatim and whose `body` is `Same query as <source address>@<revision>.` followed
by a blank line and the source's body. One act; the source is untouched (P4). A
`project` source refuses `invalid-input`: a project has no parent to mint under,
and copying one's query is `project --query` with the text.

### 3.6 `revise`

Abbreviated; each input's type is given in its comment.

```toml
name = "revise"
purpose = "Revise a project, question, hypothesis, task or decision."
write_class = "coordination"

[inputs.address]    # coord:<project> or coord:<project>/<local>; required
[inputs.name]       # optional
[inputs.body]       # optional
[inputs.query]      # optional; view kinds only
[inputs.status]     # optional enum: open | done | dropped; task only
[inputs.depends]    # optional list-of-string; task only
[inputs.repair]     # optional bool, default false
```

The kernel's revision is a whole new record naming its predecessors
(`revise_coordination(kind, address, predecessors, content)`); a patch is the
surface's convenience. The handler resolves the address's standing tips, takes the
tip's content, replaces the fields given, refreshes `author` and `at`, and names the
tip as the one predecessor. A field given for a kind that lacks it refuses
`invalid-input` naming the field and the kind, before any act.

**Divergence is repaired only on request.** Two or more tips refuse
`kernel-refused` with `{kind: "divergent-view", tips: […]}` unless `repair` is
true; with `repair`, the revision names every tip as a predecessor and takes its
unspecified fields from none of them — every content field except `author` and `at`
must then be given, since there is no one tip to carry over from. This is
coordination §4.4's repair, made explicit so that no revision silently resolves a
divergence.

### 3.7 `project-select`

```toml
name = "project-select"
purpose = "Select the current project for this session, or clear it."
write_class = "session"
output_budget = 2048

[inputs.target]     # a project name or coord:<project> address; optional
[inputs.clear]      # bool, default false
```

The input is `target`, not `project`: `project` is the reserved read protocol field
(§4.2), and a declaration naming it is a build refusal. Exactly one of `target` and
`clear=true` is given, or the command refuses `invalid-input`. A `coord:` address resolves through the resolver and must be a
`project` with one standing tip. A name resolves by enumerating the standing
`project` tips (S3) and matching `name` exactly: none refuses `unknown-project`,
two or more refuse `ambiguous-project` with each candidate's address and query
digest in `data`. The session's selection becomes the address — never the name, so
a later rename leaves the selection standing — and the session appends the
selection ledger line (S2). The report is §4.1's selection block: the project's
address, the revision it resolved to, and that revision's name; `clear` renders the
block with no project.

### 3.8 `projects` and `project-show`

`projects` lists every standing `project` tip — address, name, revision, and a mark
on the selected one — ordered by name then address, under the budget. A project
whose address has two tips renders once with `divergent` and every tip, rather than
being dropped.

`project-show` renders one project: the selection, or the invocation's `--project`
(§5.2). Its address, name, revision and canonical query, then its subordinate
records by kind — open tasks first, then questions, hypotheses, decisions, and
closed tasks — each with its address, name and, for tasks, status. Both read
coordination records through the resolver, which is live (coordination §6.2); they
need no epoch and do not wait on S1.

## 4. Framework amendments

### 4.1 The `session` write class

Framework §3.3's table gains one row:

| write class | required record kinds | required act families |
|---|---|---|
| `session` | none | none |

Its requirement is `RequiredCapabilities.none()`, but unlike `read-only` it requires
a session: the dispatcher refuses it `permit-exceeded` "no writer session on this
surface" exactly as it refuses a write without one, and the CLI routes it through
the service (§5.3). It follows the write invocation protocol (framework §6.1):
claim, `invocation-open`, the handler, `invocation-close` recording `done` with an
empty identity list or the refusal envelope; a retry under the same invocation id
replays the recorded outcome.

**Its report is not a write report.** Framework §7.4's audit admits record blocks
for minted identities only, and a write's canonical report is rebuilt from those
identities (§6.1), so a class that mints nothing would render empty or fail the
audit. A `session` invocation's canonical report is instead exactly one
**selection block**, rebuilt — on the first response, on replay and on
continuation alike — from the S2 selection line the invocation appended, found in
the ledger by invocation id: `selected: <address>@<revision>` and the name that
pinned revision carries, or `selected: none` for `clear`. The name is read from the
pinned revision, which is immutable, so a replay after a rename renders what the
selection was, not what the project is now called. The `session` audit admits
exactly one selection block whose address and revision equal the ledger line's, and
nothing else; the handler's own blocks are discarded as a write's are. A `done`
close with no selection line for its invocation is an internal error, since the
session port appends the line before the handler returns. The handler receives a **session port** instead of a
scoped writer — one method, `select(address | None)`, which sets the dispatcher's
selection and appends S2's line — and no kernel writer at all, so a `session`
handler cannot act on a corpus. The production write gate admits the class.

### 4.2 The `selects` key and the `project` protocol field

A declaration gains one optional top-level key, `selects` (bool, default false): the
command enumerates through the current project. Only a `read-only` declaration may
set it — a write binds to the session's selection alone (decision 5) — and a
`selects` write is a build refusal. `next` and `project-show` set it; `status`,
`belief` and `projects` do not (decision 4).

`project` joins framework §3.2's reserved input names beside `cursor`,
`invocation_id`, `view`, `session` and `config`. It is a protocol field offered
exactly on `selects` commands: the CLI's `--project <name or address>` on their
subcommands, and an optional `project` property in their MCP tool schemas. Any other
command's request carrying it refuses `invalid-input`, so the field is never
silently ignored. The dispatcher resolves it before the handler runs (§5.2) and
hands the handler the resolved selection; handlers never see the raw value.

The documented `reads` families (framework §3.2, belief path §5.4) gain
`coordination`, for commands that read coordination records through the resolver.

### 4.3 Refusal codes

`refusal.py`'s closed set gains three surface codes:

- `no-current-project` — a subordinate mint with no selection; `data` is empty and
  the message names `project-select` and `reuse`;
- `unknown-project` — a name or address resolving to no standing project;
- `ambiguous-project` — a name matching two or more standing projects; `data.candidates`
  lists each address and query digest.

`divergent-view`, `ProjectNotResolvable` and every other kernel refusal keep
arriving as `kernel-refused`, with the kernel's kind and detail (`sci-23e773`) in
`data`.

### 4.4 The preamble

`commands/PREAMBLE.md`'s sentence "no project can be selected yet, so every command
reads the whole world" is replaced by the rule itself: the current project is
chosen with `project-select`; enumerations read through its query and see the whole
world when none is selected; a command given an identity answers for it whatever is
selected; and "a question or task needs a selected project" widens to "a question or
any coordination record needs a selected project, except a project itself". Framework
§8's 2026-09-23 amendment is closed by a dated line pointing here, and
`test_preamble_states_the_selected_project_rule` asserts the new sentences.

## 5. The current project in the surface

### 5.1 Where the selection lives

The dispatcher of a session-bearing endpoint (`science serve`, `science mcp serve`)
holds the selection: a project address or none. It is set at open from the initial
selection (projects design §5.1: an explicit `--project` to the launcher, else the
configuration's `default_project`, else none), and changed only by `project-select`.
Both the initial value and every change are ledgered (S2). Nothing else stores it: a
selection is not a record, and the surface owns no file (layer §5.2).

An initial selection that resolves to no standing project refuses the launcher's
start with `unknown-project`, before the session opens, so a stale `default_project`
is found at startup rather than at the first question.

### 5.2 How a read resolves its selection

A read in a session-bearing endpoint uses the invocation's `project` field when
given, else the endpoint's selection. A CLI read, which runs in its own process with
no session (framework §9.2), resolves in the projects design §5.1a's order:

1. the invocation's `--project`, binding that invocation only;
2. otherwise the live session's selection, asked over `service_socket` with the
   request `{"query": "selection"}`, answered from the endpoint's state with
   `{"project": <address> | null}` — no ledger scan, no write, no invocation id. A
   live session's `null` is the answer: the read is unselected and does not go on to
   step 3, since the session's selection, not the configuration's default, is what
   the person is working under;
3. otherwise, when no session is live — the socket does not exist, or connecting to
   it is refused because nothing listens — the configuration's `default_project`;
4. otherwise none.

Any other socket failure — a timeout, a malformed answer, a permission error — is an
`internal-error`, never a silent step to 3: a live session the read could not ask is
not an absent one. An explicit `--project` naming no standing project refuses
`unknown-project` before anything is read.

### 5.3 The service protocol on both launchers

`serve.py`'s one-JSON-line protocol gains the selection query beside command
requests; the two are told apart by their key sets (`{"query"}` against the existing
`{command, inputs, invocation_id, cursor}`), and any other shape refuses as today.
`science mcp serve` binds `service_socket` at start with the same server `serve`
builds, sharing its dispatcher — which already serializes invocations under one lock
— between the stdio loop and the socket's threads, and closes the socket in the same
`finally` that closes the session. Its existing-socket refusal applies, so whichever
launcher starts second refuses to start. CLI `session`-class and write-class
invocations route to whichever launcher bound the socket.

### 5.4 Subordinate mints need a selection

`question`, `hypothesis`, `task`, `decide` and `reuse` read the selection through
the context and refuse `no-current-project` before any act when there is none, so
the invocation closes with the refusal and replays it (belief path §6.3). The kernel
then enforces the rest at the act: the selected project must resolve to one standing
tip (`ProjectNotResolvable` otherwise), which catches a selection whose project
diverged after it was selected.

### 5.5 `next` reads through the selection

`next` classifies the propositions the selection's query selects instead of every
stored proposition; under no selection it classifies every stored proposition, as
today. The selection is evaluated live through S1 over the configured corpora; the
propositions in it are classified by the existing four-class rule, and a selected
record that is not a proposition is not a row. The belief path design's §4.8
("from the current view") takes this section by reference in a dated amendment.

**Classification across mounted corpora.** S1 selects across corpora, but the
classifier does not read across them: `classify` and `ReadContext.gather_inputs`,
`observations`, `snapshot` and `pins` all go through `single_view()`, which refuses
more than one root, and each assumes one corpus and one profile. With two mounted
corpora the classifier must enumerate the selected propositions from **every** mounted
corpus and classify each from the evidence in **its own** corpus — the specs
targeting it, the assessments naming it and the verifications naming those — decoded
under that corpus's profile, with holdings read from the one configured store and a
spec input's dataset declaration found in whichever mounted corpus holds its content
address.

**A proposition's evidence lives in its corpus.** The kernel refuses a spec whose
target is not held in the spec's own corpus (`CorpusWriter._refuse_estimand_target_mismatch`,
`estimand-target-unresolvable`: "a cross-corpus target is world-resolution's read",
estimand-typing §13), so a spec in the working corpus cannot target an mm30
proposition. The milestone does not need one: its health question mints its own
proposition in the working corpus and the spec targeting it beside it (projects
design §9.2 criterion 3). That proposition is typed under the working corpus's
profile, so if it uses an operator or sort the `mm30` contract declares, the working
corpus must pin that contract and the configuration must activate it for the writer
(§6's `contracts`); otherwise the claim is typed under `biology`'s operators. A
cross-corpus spec target is not requested here: it is the kernel's world-resolution
read, and the milestone's finding is what would motivate it. The enumeration and the per-corpus classification are surface scope, owned here and neither S1's nor
`beliefs-fe7149`'s: a child task after both, carrying a two-corpus check (§9). Every
other `single_view()` caller — `claim`, `dataset`, `spec`, `run`, `assess`,
`verify`, `belief` — is decided in the same task as either write-root-only (it mints
into the write root and reads its own evidence there) or read-set-wide, and until
then refuses `invalid-input` with more than one root, as it does today.

Until S1 lands, `next` under a selection refuses `invalid-input` naming S1's task,
and `next` under no selection is unchanged. It never falls back to the whole world
silently: a person who selected `health` and saw the whole world's queue would read
the wrong project without being told.

## 6. Configuration

Framework §9.1's file gains two keys now and designs two more:

```toml
coordination = 2                 # required: the shipped coordination contract version, or false
default_project = "coord:…"      # optional: a project address
# write_root = "…"               # with beliefs-fe7149: one of corpus_roots
# read_contracts = ["…"]         # with beliefs-fe7149: documents available to read mounts only
```

**Activation and availability are separate.** `domains`, `contracts` and
`coordination` state the **writer's** profile, and nothing else enters it: the
framework's rule that the launcher states the profile and never infers it from a
manifest (framework §5.1, 2026-09-09 amendment) holds for the writer unchanged.
`read_contracts` lists corpus-local contract documents a **read mount** may need and
the writer must not activate — the `mm30` document, when the working corpus does not
type under it. A document listed in both keys refuses `invalid-input`: it is either
activated for the writer or available to mounts only.

**`coordination`** is required, for `domains`' reason: a configuration written
before this design refuses rather than silently opening a session that cannot mint
a question. An integer names the shipped coordination contract
(`shipped_coordination(version)`), compiled into the one profile the session binds:
`compile_profile(base, domains + contracts, coordination=shipped_coordination(v))`,
passed to `open_attended_session` as both `profile` and `coordination` — the kernel
requires the two to agree in compiled identity (`require_profile_compatible`), so
they are the same `ProfileSpec`. The corpus must pin it: a corpus adopted without
the coordination contract refuses at session open under `require_pins_agree`, and
the loader's refusal says the configuration asks for coordination the corpus does
not pin. `false` opens a session without coordination, for a corpus adopted before
it; every coordination-class command then refuses `kernel-refused`
(`CoordinationUnavailable`) at its act, as today, and `project-select`, `projects`,
`project-show`, a `--project` on any read, and a `default_project` key each refuse
`invalid-input` naming the `coordination = false` setting, since there is no
resolver to ask. The read context builds a
`CoordinationResolver` when coordination is on. With one configured root — the only
shape the kernel's session opens today — that root is mounted under the session's
profile.

**Every mount under its own manifest's profile.** The resolver checks each mount's
manifest pins against the profile it is given (`CoordinationResolver.__init__`), and
the corpora the milestone mounts pin different contracts: the working corpus pins
base, `biology` and coordination; the mm30 corpus pins its corpus-local `mm30`
contract. So no configuration ever mounts two corpora under one profile. When
`beliefs-fe7149` lands, each mount — in the session's resolver and in the
sessionless read context a CLI read builds alike — is mounted under the profile its
own manifest pins, compiled by the mechanism that task gives the kernel (projects
design §3.1: "the kernel owns how a mounted corpus's profile is compiled"). The rule
selecting documents for each profile is explicit:

- **The writer's profile** — and so the write root's mount — is
  `compile_profile(base, [shipped_domain_contract(ns) for ns in domains] + contracts,
  coordination=…)`, exactly the configuration's statement, and must equal the write
  root's manifest pins (`require_pins_agree`).
- **Each other mount's profile** activates exactly the contracts that mount's
  manifest pins. Each pinned identity is resolved, by contract identity, against the
  shipped packs and the union of `contracts` and `read_contracts`; a pin no available
  document or pack carries refuses at open naming the mount and the pin, and nothing
  available but unpinned is activated. Availability never becomes activation.

So supplying the `mm30` document through `read_contracts` lets the mm30 mount decode
its own records without changing the writer's profile or the working corpus's pins.

**`default_project`** is an address, not a name: names are content and may collide
or change (coordination §3.3), and a configuration that followed a name would move
to another project on a rename. It is checked at launcher start (§5.1) and consulted
by a CLI read only when no session is live (§5.2).

**`write_root`** and **`read_contracts`**, designed here and implemented with
`beliefs-fe7149`. `write_root` is the one entry
of `corpus_roots` the session writes into, required when `corpus_roots` has more
than one entry and refused when it names a root outside the list. Until the kernel's
session takes a write root and a read set, `open_attended_session` refuses more than
one root, and neither key is accepted.

**Relative paths** — `operations_root`, `store_root`, `service_socket`, each
`contracts` entry, `world_root` and each `corpus_roots` entry — resolve against the
directory of the configuration file, not the process's working directory (decision
8). `test_load_config_resolves_relative_operations_root` and
`test_service_socket_is_configurable_and_resolved` change to assert that, from a
working directory other than the file's.

## 7. Errors and edge cases

- **A selected project is revised.** The selection is an address; the next read
  resolves its new tip. Nothing re-selects.
- **A selected project diverges.** Reads through it refuse `kernel-refused`
  (`divergent-view`, every tip), subordinate mints refuse `ProjectNotResolvable`;
  `revise --repair` on the project, or `project-select --clear`, is the way out.
- **A launcher crashes and leaves its socket.** A CLI read's connect is refused, so
  it reads as no live session (§5.2 step 3); the next launcher refuses to start on
  the existing socket, as today, and removing a stale socket stays the operator's
  act (`serve.py`'s refusal message).
- **A query text that is not a mapping, or not YAML.** `invalid-input` before any
  act. A query that parses but the kernel rejects — an unknown world kind, a
  `coord:` address in `addresses` — is `kernel-refused` at the act, with no act
  recorded, and replays.
- **A same-query mint of a source in the current project.** Allowed: it is a second
  view with the same query, which is what the source's owner asked for.

## 8. What the kernel must add

Three `beliefs` requests, each filed as a task and depended on by the plan task that
needs it. The requirement is stated; the design is `beliefs`'.

**S1 — live, unpublished query evaluation.** Denote a `ViewQuery` over the mounted
corpora's current captured state without building or publishing an epoch, returning
a selection whose stamp names the capture rather than any epoch identity, so that no
consumer can mistake it for an epoch-bound answer; publish and every epoch-bound
read are unchanged. Needed by `next` under a selection (§5.5). This reverses nothing
in coordination §6.2 for publication; it adds the attention read that §6.2's own
argument for live coordination resolution covers. Whether it is a new function or a
view type is the kernel's.

**S2 — selection ledger lines (P3).** The session ledger records the initial
selection at `session-open` and every change, attributable to the invocation that
made it: a `project` value on `session-open` (an address or null) and a new line
kind carrying the invocation id, the new value (an address or null) and the
revision the address resolved to, appended with the ledger's append-then-fsync
discipline before the invocation closes. Exposed as one `WriterSession` method the
surface's session port calls, and readable back by invocation id through the ledger
reader, which is the replay source of §4.1's selection block. Needed by `project-select` and by launcher start with an initial
selection. `LINE_KINDS` is closed today (`session/ledger.py`), so this is a ledger
amendment.

**S3 — enumerate standing tips by kind.** A public `CoordinationResolver` method
returning every address of a given kind — optionally within one project — with its
resolution (the tip's node, or `divergent-view` with its tips), over exactly the
resolver's mounts. Needed by `project-select` by name, `projects` and
`project-show`. Names stay content the kernel never consults (coordination §3.3):
the surface matches names over the enumeration. The resolver's mount set is the
authority on what is visible — and becomes multi-corpus with `beliefs-fe7149` — so a
surface-side scan of stored records would have to track that set itself.

## 9. Guarantees and testing

Framework §11's harness shape: the assertion, the mutation that falsifies it, the
test that catches it. The fixture world gains the coordination contract in its
profile and manifest pins.

| # | guarantee | check |
|---|---|---|
| P1 | No configuration is discovered from the working directory, and relative paths inside it resolve against the file | a launcher test opens a session — through `serve`, `mcp serve` and a CLI read — from a directory holding a predecessor `science.yaml`, a workspace `science.toml` and a stray `corpus.yaml`, and asserts the world, corpus roots, operations root and selection equal the configuration's; the two relative-path tests run from a directory other than the file's |
| P2 | A subordinate mint with no selection refuses `no-current-project`; `project` genesis and world-kind writes do not | three dispatcher arms under a session with no selection: `question` refuses before any act and replays the refusal, `project` mints, `claim` mints; the mutation that drops the selection check makes `question` reach the kernel |
| P4 | `reuse` mints a record of the source's kind under the current project with the source's query, and the source is unchanged | the new record's query equals the source's canonical query; the source's tip uid is asserted equal before and after |
| P5 | The unselected session reads the whole world | `next` under no selection equals `next` under a project whose query is `kinds` over every world kind; `belief` is selection-independent by decision 4 and asserted equal under both |
| P8 | A read in a new process resolves the live session's selection whichever launcher opened it; `--project` binds that invocation only | two arms, `serve` and `mcp serve`: `project-select` through the endpoint, then `project-show` in a fresh CLI process observes it; `project-show --project <other>` observes the other, and the endpoint's selection is unchanged afterwards |

Beyond the guarantees:

- **Configuration.** `coordination` absent refuses; `false` opens and a `project`
  mint refuses `CoordinationUnavailable`; an integer against a corpus that does not
  pin coordination refuses at open; `default_project` naming no project refuses
  launcher start.
- **The `session` class.** A `project-select` without a session refuses
  `permit-exceeded`; its handler is given no kernel writer (the mutation that passes
  one is caught by a type assertion in the handler test); a replay returns the
  recorded outcome and does not append a second selection line.
- **Names.** Two projects sharing a name make `project-select <name>` refuse
  `ambiguous-project` listing both; selecting by address still works; a rename
  leaves the selection standing.
- **`revise`.** Carries over unspecified fields; refuses a field the kind lacks;
  refuses a divergent address without `repair` and repairs it with; after a
  `status: done` revision the task renders under closed tasks in `project-show`.
- **`next` under a selection** classifies exactly the selected propositions (with
  S1); before S1 it refuses naming the dependency (the mutation that falls back to
  the whole world is caught).
- **Two corpora** (after `beliefs-fe7149` and S1), in the shape the kernel admits —
  each proposition's evidence in its own corpus: a read-only corpus pinning a
  corpus-local test contract, holding a proposition typed under that contract's
  operator with its spec, run and assessment; and a working corpus pinning base,
  `biology` and coordination, whose session mints a proposition under a `biology`
  operator and a spec targeting it with its input held. The test contract reaches
  the read mount through `read_contracts`. Under a project selecting both
  propositions, `next` classifies the read-only corpus's proposition **assessed,
  not admitted** and the working corpus's **ready**. The mutation that enumerates
  the write root only drops the first row; the mutation that decodes the read
  mount's records under the writer's profile fails on the corpus-local operator;
  the mutation that activates `read_contracts` in the writer is refused by the write
  root's pin check; and a sessionless CLI read mounts both corpora each under its
  own manifest's profile.
- **Profile selection.** A document listed in both `contracts` and
  `read_contracts` refuses at load; a read mount pinning a contract no available
  document carries refuses at open naming the pin.
- **The selection block.** `project-select` then a replay under the same invocation
  id render identical blocks after the project is renamed in between; `clear`
  renders `selected: none`; a report carrying any record block fails the `session`
  audit.
- **The socket.** The selection query answers without an invocation id and leaves no
  ledger line; `science serve` refuses to start while an MCP endpoint holds the
  socket, and the reverse.
- **Transports** (framework §9.4). Each new read renders byte-identically through
  the CLI and MCP; each new write is driven through at least one transport with
  replay and the refusal envelope exercised.

The second-project milestone (`sci-0d00d2`, projects design §9.2) is the integration
measurement and is not a suite test.

## 10. What this changes elsewhere

- **Framework design:** §3.2 (reserved `project`), §3.3 (the `session` class), §8 (the
  preamble amendment closed), §9.1 (`coordination`, `default_project`, relative
  paths), §9.2 and §9.3 (both launchers on the socket; the selection query) take dated
  amendments in the implementing commits.
- **Belief path design:** §4.8 takes §5.5 by reference.
- **Projects design:** §7's "a `note` naming the source address" is read as decision
  7; a dated note there points here.
- **`tools/cli.toml`:** one row per new command and a `--project` option on every read
  row, edited in the ops repository first and re-vendored. Its shared `--project`
  vocabulary entry means a tasks project prefix, so science's rows carry their own
  option rather than the shared one.
- **`coord-note`:** the synthetic fixture's `unreachable` handler becomes a real one
  now that the class can act, or the fixture is dropped in favour of the production
  commands' tests; the plan chooses.
- **Fixture worlds and existing configurations** gain `coordination`; the mm30
  measurement world under `.work/` was adopted without it and takes `coordination =
  false`.
- **`beliefs`:** S1, S2 and S3 filed as tasks (§8).
- **The second-project milestone** (`sci-0d00d2`): its health question's proposition
  and spec are minted in the working corpus (§5.5); if the proposition uses an `mm30`
  operator or sort, the working corpus is adopted pinning the `mm30` contract and the
  configuration lists it under `contracts`, otherwise under `read_contracts`.

## 11. Alternatives rejected

- **The launcher publishes an epoch after every write.** Framework §4.4 permits
  launcher-time epoch acts and it needs no kernel change, but every write would
  publish a world package nobody asked for, epochs would accumulate, and write latency
  would carry an epoch build. Rejected by the person in favour of S1.
- **Selected reads refuse when the epoch is stale.** No kernel change and no hidden
  act, but the daily loop stops at every write until an operator republishes.
  Rejected by the person.
- **One `project` command with an action input.** Needs three write classes on one
  declaration; the schema has one.
- **Selection as a dispatcher operation, like `continue`.** It needs an input, a skill,
  a CLI subcommand and an MCP tool, which a declaration gives it and a dispatcher
  operation would have to rebuild by hand.
- **The MCP launcher binds the socket for the selection query only.** A CLI write
  while an MCP session is live would then refuse "no writer service", and the remedy
  that message names — `science serve` — would be the forbidden second writer.
- **`--project` on writes.** Would let a question land under a project the session
  never selected, so the ledger's selection lines would no longer attribute it.
- **`default_project` by name.** A rename would silently move a person's default to
  whichever project next carries the name.
- **A surface-side scan for name resolution.** The kernel functions it would compose
  are public, but the resolver's mount set decides what is visible and becomes
  multi-corpus with `beliefs-fe7149`; a second scanner would have to follow it.
- **A separate `note` record for the same-query mint.** Two acts where the projects
  design asks for one, and `note.about` cannot hold a `coord:` address.
- **Commands for `topic`, `theme` and `note` now.** No measurement asks for them.

## 12. Task mapping

The goal is `sci-c5528e`. The plan decomposes it; the dependencies it must carry:

- the coordination profile at session open and the `coordination` key — absorbs
  `sci-17851d`, which closes with it;
- relative paths against the configuration file (P1) — independent;
- the `session` class, the `project` protocol field and the refusal codes — before
  any command;
- `project`, `question`, `hypothesis`, `task`, `decide`, `revise`, `reuse` — after the
  profile;
- `project-select`, the selection block and its audit, launcher initial selection,
  `default_project` — after S2;
- `projects`, `project-show`, name resolution — after S3;
- both launchers on the socket and the CLI's selection resolution (P8);
- `next` through the selection (§5.5) — after S1;

- the preamble and the dated amendments;
- **multi-corpus**, one child after `beliefs-fe7149` and S1: `write_root`,
  `read_contracts` and the per-mount profile rule in both resolvers (§6), classification across mounted corpora and the
  `single_view()` callers' decision (§5.5), with the two-corpus check. It does not
  hold the goal's other work, and milestone criterion 4 (`sci-0d00d2`) depends on it.

`sci-0d00d2`, the second-project milestone, depends on this goal and on
`beliefs-fe7149` and `beliefs-c08725`, as it already does.
