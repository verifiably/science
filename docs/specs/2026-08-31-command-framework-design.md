# Command framework — design

**Date:** 2026-08-31
**Status:** implemented 2026-09-09 (Tasks 1–13). The beliefs permit and
writer-session deliverables this design is the companion contract for landed
first (`beliefs-96a24a`, `beliefs-afbbff`). Two amendments were taken during
implementation and are marked in place: §5.1 and §9.1 for the required session
`profile` and the `domains` configuration key, and §4.4's consequence that a
`publishes` command refuses at declaration time until sub-project 5 supplies
the publish act family.
**Scope:** sub-project 2 of the user/autonomy layer design (`beliefs`
`docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md`, §5 and
§8 item 2): the command declaration schema, write classes, the budgeted
renderer, the shared preamble, the adapter generator with the Claude Code
target, and the CLI and MCP surfaces over `beliefs` reads — all in this
repository — and, as the contract the `beliefs` repository implements
alongside (`beliefs-96a24a` and a successor task for the session), the write
permit on every `beliefs` write entry point and the writer session with its
bound permit, endpoint-set actor and session ledger. It ships one real
command, `status`. It designs no view query language (sub-project 1's), no
dogfood command semantics (sub-project 4's), no publish act (sub-project 5's),
and no actor sandbox or private endpoint handle (sub-project 6's).

**Inherits:** the user/autonomy layer design's §2 decisions 4–6, §4 (the
knowledge model at the user layer), §5 (the daily surface), §7.1's tier
ordering, and §9 (verification posture). Terms used without definition —
write class, permit, launcher, session ledger, `Refused(reason)` — are that
document's.

## 1. Problem

The `science` repository is empty and `beliefs` exposes no permit type, no
CLI, and no endpoint: every write entry point takes a caller-supplied `actor`
string and nothing gates what a caller may mint. The predecessor shows what
grows in that vacuum — 253 leaf commands re-deciding format, write discipline
and budget each for themselves, a 21 MB read, audit echo on every write.
Sub-project 2 is the framework contract that prevents the recurrence: one
declaration schema every command must fit, one permit mechanism every write
must pass, one renderer every result must go through, one generated adapter
per harness — built now, against today's kernel reads, so that sub-project 4
can add commands without adding decisions.

## 2. Decisions

Rulings from the 2026-08-31 session, recorded so they are not re-derived.

1. **One shipped read exemplar; synthetic write exemplars only.** `status`
   ships, limited to today's kernel state. Test-only fixture commands
   exercise `coordination`, `mints:<kinds>`, `publishes`, declaration-time
   and act-time permit refusal, and audit and paging rendering. Real write
   commands arrive when sub-project 4 defines their acts.
2. **Commands are the tools.** Each command is one declaration, one
   deterministic server-side handler, and one harness-neutral prompt teaching
   an agent when and how to invoke it — the prompt is the agent-side
   workflow, not sugar. CLI and MCP expose handlers 1:1. Kernel primitives
   are never exposed publicly: the endpoint receives a command name, its
   inputs and the protocol fields of §6 — nothing else — selects the
   handler, binds actor and effective permit, and performs the kernel calls
   internally. A unit that only
   orchestrates other commands and owns no deterministic endpoint is a
   skill, not a command.
3. **A command's source is a directory**: `commands/<name>/command.toml`
   (the declaration, pure data, validated against one schema) plus
   `prompt.md` (the body). The handler is bound by convention at
   `science.commands.<module>:handle` and checked against the declaration at
   build time.
4. **One session API, three frontings.** `beliefs` owns the writer session —
   permit, fresh session identity, ledger — as the single write choke point.
   The MCP server fronts it for a harness; the CLI fronts it for a person
   (writes through the service process, reads in-process); library use is
   in-process and attended by construction. Sub-project 6 adds the process
   boundary around the same API without changing it.
5. **`science` is Python-only.** Handlers call the `beliefs` kernel API
   in-process, which is Python; the layer design's distribution table gives
   `science` no TypeScript distribution.

## 3. The declaration schema

### 3.1 Source layout and name grammar

`commands/<name>/` holds exactly `command.toml` and `prompt.md`. The
directory name must equal the declared `name`. The name grammar is
`^[a-z][a-z0-9]*(-[a-z0-9]+)*$`, at most 32 bytes. The handler module is the
name with every `-` replaced by `_` — injective under this grammar, since `_`
cannot appear in a name — so `science.commands.<module>:handle` is
unambiguous. **Reserved names**, refused at build: `continue`, `serve`,
`mcp`, `adapters`, `build`, and any future dispatcher operation.
The command root, each command directory, both files, and `PREAMBLE.md`
must be real filesystem directories or regular files as appropriate:
symlinks and special files are build refusals. Build validation proves each
command source is contained by the command root before reading it.

### 3.2 The declaration

```toml
schema_version = 1
name = "status"
purpose = "One line, shown as the CLI help line and the MCP tool description."
write_class = "read-only"
output_budget = 16384

[inputs.corpus]
type = "string"          # string | int | bool | enum | list-of-string
required = false
doc = "One line."
# default = "..."        # optional inputs only
# choices = ["a", "b"]   # enum only: required, non-empty, unique strings

[reads]
families = ["registry", "epoch", "corpus-stored"]
```

- `schema_version` is required; the framework refuses a version it does not
  implement.
- **Inputs.** The type set is closed. `required = true` forbids `default`.
  An `enum` requires `choices`; every non-enum forbids the `choices` key even
  when its value is an empty list. Runtime input keys must be exact strings
  before any set operation or sorting. An optional input without a `default` is,
  when absent, absent: it does not appear in the canonical inputs mapping,
  and the handler's keyword parameter receives `None`. Canonicalization —
  the form every digest and every schema is computed over — is: apply
  declared defaults, drop absent optionals, sort keys, encode as canonical
  JSON. **Reserved input names**, refused at build: `cursor`,
  `invocation_id`, `view`, `session`, `config`. They are protocol fields
  (§6), never command inputs, and reserving them lets the wire schemas carry
  them without collision.
- **`reads` is documentation and a test contract, not runtime enforcement.**
  The reader test for a command asserts it performs the declared read
  families and no others; nothing at runtime scopes what a handler may read.
  A runtime read facade is a possible later hardening and is not claimed
  here. Write classes, by contrast, *are* runtime-enforced (§4).
- **`output_budget`** is required, in bytes, with no default, and must be
  at least **`MIN_OUTPUT_BUDGET`** — a framework constant derived from the
  fixed protocol overhead: the truncation marker, `MAX_CURSOR_BYTES` (a
  real maximum, because every cursor field has a fixed grammar or width —
  §6.2, §7.3), and one complete UTF-8 character. Both constants are
  published by the framework and asserted by its own test, so §7.2's
  progress guarantee is satisfiable at every legal budget. A declaration
  below the minimum is a build refusal. There is deliberately **no
  framework maximum**; §5.3 of the layer design makes the declared number
  the contract, and the renderer (§7) makes it a test.

### 3.3 Write classes

The closed set, and what each requires of the session (both permit
dimensions — see §4.2 for the capability model):

| write class | required record kinds | required act families |
|---|---|---|
| `read-only` | none | none |
| `coordination` | the coordination contract's kinds (sub-project 1) | `corpus-write` |
| `mints:<k1,…>` | the named kinds | exactly the declared routes (below) |
| `publishes` | the publication kinds (sub-project 5) | `publish` |

A `mints` class must name kinds that exist in the governing contract the
build validates against; an unknown kind is a build refusal. Until
sub-project 1 lands there is no coordination contract, so a
`coordination`-class command cannot ship — which is exactly decision 1's
scope: it exists only in test fixtures until then. Likewise `publishes`
until sub-project 5.

**The declaration selects the minting route; nothing is inferred by
union.** A kind can be mintable through more than one entry point — a `run`
record enters through the run boundary or through ordinary corpus writing —
so deriving act families as the union of every route capable of minting a
kind would over-require, and a session permitting only one valid route
would wrongly refuse the command: a union is not least privilege. The one
schema form is a kind-to-route map:

```toml
[write.routes]
run = "run"              # <declared kind> = <act family>
dataset = "run"
```

A kind with a single admissible route in `KIND_ACTS` (§4.1) **may be
omitted** from the map, and the build derives its route; a route-ambiguous
kind **must** appear, and its omission is a build refusal. Also build
refusals: a map key that is not one of the class's declared kinds, and a
route `KIND_ACTS` does not admit for its kind. The required act families
are then exactly the mapped (or uniquely derived) routes — no more.

### 3.4 Build refusals

`science build` (invoked by the adapter generator, the CLI's self-check and
the test suite) validates every declaration against the schema and refuses
the tree — not the command — on: schema violation, name grammar or reserved
name violation, directory/name mismatch, handler missing or its keyword
signature disagreeing with the declared inputs, unknown kind in a write
class, unsafe or uncontained source nodes, or a generated/authored skill-name
collision. The shared production preflight reads every TOML, prompt, preamble,
and authored-skill file before adapter output is removed or rewritten. A
command that does not fit the schema does not ship, as a refusal with the file
and field named. A single filesystem root cannot contain duplicate directory
names, so this loader claims no duplicate-command check; a future multi-root
loader must add collision validation when it introduces that second source.

Until Task 12 imports the beliefs capability contract, the production loader
also refuses every declaration whose write class is not `read-only`. Generic
injected trees continue to accept all four write classes for schema tests.

## 4. Write permits in `beliefs`

This section and §5 are the contract `beliefs` implements; the permit half
is tracked there as `beliefs-96a24a`.

### 4.1 The permit value

`WritePermit` is a frozen value with two closed dimensions:

- **`kinds`** — a frozenset of record kinds the holder may mint through
  `CorpusWriter.add` and the family adapters (`retract`, `supersede`,
  `revise`, `import_bundle` judged member-by-member).
- **`act_families`** — a frozenset over a closed enumeration owned by
  `beliefs`: `corpus-write`, `run`, `holdings`, `registry`, `epoch`,
  `lifecycle`, and, when sub-project 5 lands, `publish`.

`beliefs` also owns **`KIND_ACTS`**, a closed mapping from each mintable
kind to the set of act families **admissible as its minting route** (for
example `holdings-observation` to `{holdings}`; a `run` record to
`{run, corpus-write}`; most ordinary records to `{corpus-write}` alone).
It is **validation data, not a requirement derivation**: the declaration
selects its route (§3.3), and `KIND_ACTS` is what the build checks the
selection against — and what lets a single-route kind's declaration omit
the selection. Its full contents are settled with `beliefs-96a24a`'s plan;
the mapping is exported read-only.

**Amended 2026-09-04 (`beliefs` write-permits design §13.7).** The kernel
mints kinds outside `KIND_ACTS` — ungoverned records carrying no
semantic-identity facet — through `CorpusWriter.add` alone. `WritePermit`
therefore carries a third, boolean dimension, `ungoverned`, admitting such
kinds through `corpus-write` only. `KIND_ACTS` is complete over the
**governed** kinds. Nothing here changes for `science`: no
`RequiredCapabilities` constructor sets the flag, a `mints` class naming an
unknown kind remains a build refusal (§3.3), and the names the plan's Task
12 consumes are unchanged.

### 4.2 Requirements, not permits, cross the layer boundary

§5.2 of the layer design is literal: `science` never sees, threads, or
constructs a permit. `beliefs` exports a **`RequiredCapabilities`** value
with constructors — `RequiredCapabilities.none()`, `.coordination()`,
`.for_kinds(kinds, routes)`, `.publishes()` — and the session exposes
**`WriterSession.scoped(required)`**, which either returns an
**invocation-scoped writer** or a structured refusal (§6.3).

**Amended 2026-09-05 (`beliefs` writer-session design §5).** `scoped` takes
the invocation id as its second argument — `scoped(required, invocation_id)`
— and the writer it returns acts only while that invocation is the session's
current one. A writer scoped before the claim and outside the dispatcher's
lock cannot otherwise be told from another invocation's, and a writer
retained across invocations would carry its own permit into a later one.

The scoped writer is a facade whose **effective permit is exactly the requirement**:
`scoped` checks the requirement against the session's permit (the
declaration-time refusal) and binds the invocation's kernel entry points to
the requirement, not to the session's ceiling — so a handler that exceeds
its declaration is refused **at the act** even under an attended session's
full permit. The session's own permit is only ever a ceiling; no act runs
under it directly. `science` compiles a declaration's write class to a
requirement through the constructors and asks; it never holds either
frozenset, and a handler never receives the `WriterSession` — a `read-only`
command receives no writer at all (§6.1). `WritePermit.full()` exists in
`beliefs` for its own launcher constructors (§5.1) and is not importable
policy for `science` code.

**Amended 2026-09-05 (`beliefs` write-permits design §16).** Every `beliefs`
construction seam binds an authority, `open_world` included, so the read
context of §9.2 — which holds no permit and may not construct one — opens its
world through `beliefs.root.open_world_read(config)`, a door `beliefs` binds to
its own `permit.READ_ONLY`: the empty permit, under which every act refuses on
its family before any effect. `science` still sees no permit; it sees a `World`
that can only be read.

### 4.3 Enforcement at every entry point

Every write entry point takes the permit — bound once at the construction
seams (`open_corpus`, `open_world`, the `OperationPort`, the holdings
`ActContext`, the root lifecycle acts) rather than per call — and checks the
kind or act actually being emitted **before any effect**. There is no
default value: in-`beliefs` callers state their permit explicitly. A
violation raises `PermitExceeded`, a new `WriteRefused` subclass carrying
structured fields (§6.3), and on the run boundary surfaces as the existing
`RunRefused` value with the same structured reason. The check is exercised
on the interactive path daily because the attended session holds a full
permit through the same mechanism, not around it.

### 4.4 Acts without corpus-chain evidence are not command-reachable

Three act families write without corpus-chain evidence: `lifecycle`
(`adopt_manifest` writes the manifest through a direct `CreateOp` with no
operation intent; `init_*`, `replicate_root`, `restore_root`, `fork_*`
write outside any chain), `registry` (`World.admit`/`retire`/`depart`
commit through the world registry, not a corpus log), and `epoch`
(`build_epoch`, `delete_epoch`, `install_rule_binding` likewise). All
three remain permit-gated, but **no write class maps to any of them**: the
command-reachable act families are exactly `corpus-write`, `run`,
`holdings`, and — with sub-project 5 — `publish`.

**Amended 2026-09-09.** Until sub-project 5 lands, `publish` is not merely
uncovered by any permit — it is not an act family at all, and
`beliefs.permit.RequiredCapabilities.publishes()` refuses to construct a
requirement naming it. A `publishes`-class command is therefore declarable and
loadable, but the dispatcher refuses it `permit-exceeded` at declaration time,
before the session is consulted and before its handler runs. The refusal names
sub-project 5 as what it waits on. `coordination` is not in this position: its
requirement constructs and an attended session's permit covers it, so a
coordination command reaches its act and refuses there —
`CoordinationUnavailable` — when the launcher supplied no coordination profile. Lifecycle, registry and
epoch acts are launcher- and operator-time library operations. A future
command that wants one is a spec amendment whose first obligation is to
define the ledger evidence for that family — what the session can claim
and §7.1's comparison can check — not merely to map a class to it. The
session ledger (§5.2) therefore only ever claims acts that have
corpus-chain evidence, and the ledger-versus-chain comparison never meets
an act that could not appear in a chain.

## 5. Writer sessions in `beliefs`

### 5.1 Opening a session

`beliefs` exports launcher constructors, not a raw session:

- `open_attended_session(world_config, operations_root, *, profile, coordination=None)`
  — full permit by
  construction; the interactive constructor. The MCP server and the CLI's
  service process open one; a CLI read invocation opens none (§9.2) — a
  session exists to bind writes, and a `read-only` requirement needs no
  session to be judged.
  **Amended 2026-09-05 (`beliefs` writer-session design §3.1).** The
  constructor takes an optional keyword `coordination`, the compiled
  `ProfileSpec` for the corpus; without it coordination-class commands refuse
  `CoordinationUnavailable` at the act. The launcher's configuration therefore
  names the contract documents the profile compiles from.
  **Amended 2026-09-09 (`beliefs` writer-session design, integration amendment
  of 2026-09-07).** `profile` — the compiled `ProfileSpec` the session's writer
  and durable operation port bind — is a **required** keyword, and
  `open_corpus` requires it alike. No profile is inferred from a manifest or
  from `coordination`: the launcher states it, and `require_pins_agree` then
  refuses a corpus whose manifest pins disagree. `require_profile_compatible`
  additionally refuses a `coordination` profile that differs from `profile` in
  base identity, activated contracts, or compiled identity.

  §9.1's launcher configuration therefore carries `domains`, the list of
  namespaces the profile activates; `science` compiles
  `compile_profile(shipped_base_contract(), [shipped_domain_contract(ns) …])`
  at config load, so an unrecognized namespace refuses at startup rather than
  at the first write. `coordination` stays unset until a coordination-class
  command exists: the shipped base declares no coordination kinds, so passing
  a resolver would arm nothing.
- A run-session constructor with a tier parameter arrives with sub-project 6
  and is out of scope here beyond the seam existing.

Opening mints a **fresh session identity** — a 32-lowercase-hex token
(§6.2's identifier bound) — and
fixes the **actor** as `session:<session-id>`. The session sets every
intent's `actor` itself; no caller of the session supplies one, which is
where `actor` stops being a caller-supplied string. The returned
`WriterSession` is the **trusted server-side object**: it lives in the
endpoint process, wraps the permit-bound entry points and the ledger, and
is touched only by the dispatcher — handlers receive at most the
invocation-scoped writer of §4.2. Closing the session
(`WriterSession.close()`, idempotent) appends the ledger's `session-close`
line; every endpoint closes its session in a `finally`, on the error path
as much as on clean shutdown. It
is distinct from the **session handle** — the transport address and
per-session token an actor process will hold — which does not exist until
sub-project 6 builds the sandbox; naming the distinction now is what lets 6
add the boundary without changing this API.

### 5.2 The session ledger, and the intent every session write carries

**Every session-mediated write is intent-fulfilling, the ordinary corpus
route included.** The run and holdings routes already append actor-bearing
intents, but the ordinary corpus-write route (`CorpusWriter.add`,
`retract`, `supersede`, `revise`) publishes records that fulfill no
intent — so a crashed session's corpus writes would be unattributable and
§5.3's reconciliation, like §7.1's interval-membership test, could never
name them. The session therefore performs every ordinary corpus write as
intent plus fulfillment: it appends
`OperationIntent(kind = corpus-write, event_token, actor = session actor)`
and publishes the record through the existing fulfilling execution path.
`corpus-write` is not in the kernel's closed operation-kind set, so this
is a **versioned act-report amendment** adding the operation kind — the
same amendment discipline the layer design's §6.1 uses for `publish` —
banked in `beliefs` with the writer-session task before any session
ships. Direct library use of `CorpusWriter` outside a session is
unchanged, bounded as ever by the single-writer deployment obligation.

The ledger itself is an append-only JSONL file at
`<operations root>/sessions/<session-id>/ledger.v1`, outside every corpus,
written with append-then-fsync before any result is reported. Typed lines:

- `session-open` — session id, actor, world id, permit summary, timestamp.
- `invocation-open` — invocation id, command name, **input digest** (§6.2),
  timestamp — the digest only, not the canonical inputs: deduplication
  compares digests and write continuation re-renders from minted
  identities, so the inputs themselves would be durable data nothing
  needs. Written for **write-class invocations only**: the ledger is write
  evidence, not a query store. Reads leave no ledger trace, and read
  continuation is stateless (§7.3).
- `act` — invocation id, corpus id, **chain entry digest**, and the
  **minted record identities** (uid and id). The pair is deliberate: the
  entry digest ties the line to the chain, the record identities are what
  the write-audit rule (§7.4) and continuation (§7.3) verify against;
  neither substitutes for the other.
- `invocation-close` — invocation id, and the outcome: `done` with the
  minted record identities in total, or the **full structured refusal
  envelope** `{code, message, data}` (§6.3) — persisted whole because
  deduplication promises to re-render the recorded outcome (§6.2), and a
  bare code could not reconstruct it.
- `session-close`.

§7.1 of the layer design compares chain intervals against this ledger
**`act` lines only**; the other line kinds are session evidence and paging
state, not write claims.

### 5.3 The crash window, honestly

An act can commit and the process die before its `act` line is written. The
contract: **chains are truth, the ledger is evidence.** Reconciliation — run
when a later endpoint opens over the same operations root, and by the audit
surface — scans for chain entries whose intent `actor` matches a ledgered
session and that no `act` line covers. An actor-matching uncovered entry
under an `invocation-open` without `invocation-close` is classified
**`outcome-unknown`**: surfaced as an audit finding naming the invocation
and the entry, never silently adopted as covered and never treated as
foreign. (Under sub-project 6's closing check the same state quarantines
the run; interactively it is a finding for the person.) An uncovered entry
matching no open invocation is foreign, exactly as §7.1 already rules.

## 6. The invocation protocol

### 6.1 Dispatch order

A request names a command and its inputs, plus the protocol fields
`invocation_id` and `cursor` (both optional). The dispatcher, in order:
(1) resolve the command or refuse `unknown-command`; (2) validate and
canonicalize inputs against the declaration or refuse `invalid-input`;
(3) compile the write class to a `RequiredCapabilities`; a `read-only`
command's requirement is `none`, satisfied with or without a session
(§9.2's sessionless CLI reads included), and yields no writer; otherwise
call `session.scoped(required)` — the declaration-time permit refusal,
before the handler runs — for the invocation-scoped writer; (4) for a write-class invocation, claim the
invocation id and append `invocation-open` (§6.2); (5) invoke the handler
with the read context and, for writes, the scoped writer — never the
session — so a body exceeding its declaration is refused at the act;
(6) for a read, render under the budget (§7) and return; for a write,
collect the minted identities, apply the write audit (§7.4), append
`invocation-close` **recording act truth** — `done` with the minted
identities, or the refusal envelope — and only then render. The close
precedes rendering because the ledger records what was done, never whether
a report survived rendering: an audit violation still closes `done` (the
acts committed) and surfaces as an internal error whose recovery is a
dedup replay from the ledger, and what a successful write renders — first
response and replay alike — is the canonical report rebuilt from the
ledger's identities, not the handler's blocks. A request carrying `cursor`
is a continuation (§7.3), handled by the dispatcher before this pipeline;
it never reaches a write handler.

**Amended 2026-09-09 (belief-path design §6.3).** A surface `Refused` raised by
a write handler is caught at step 5. With no act recorded for the invocation,
the dispatcher closes it with the refusal envelope exactly as a kernel refusal
closes, and a retry replays that refusal from the ledger. With an act
recorded, the handler broke the validate-before-act rule: the dispatcher closes
`done` with the minted identities and raises `HandlerContractViolation`, an
internal error, because a half-acted write is a defect and not a refusal.

### 6.2 Invocation identity and retry

The caller may supply an **`invocation_id`** (protocol field, exposed on
every wire surface — §9) with the fixed grammar
`^[A-Za-z0-9_-]{1,64}$` — opaque in meaning, bounded in form, refused
`invalid-input` outside the grammar; absent one, the dispatcher mints a
32-lowercase-hex token and returns it with the result. Session identities
share the 32-hex form (§5.1). These bounds, with the digest fields' fixed
widths and the fixed-width `u64` cursor positions, are what make
`MAX_CURSOR_BYTES` (§3.2) a real number. For a write-class invocation the
dispatcher deduplicates within the session against the ledger before
step 5, and the claim is **atomic**: one session dispatch lock serializes
steps 4–7 for write-class invocations, so two concurrent requests bearing
the same id cannot both find "no match" and both execute. Under the lock:
a matching `invocation-open` with `invocation-close` and the **same
command and input digest** returns the recorded outcome re-rendered (no
re-execution); a matching open (either state) whose command or input
digest **differs** refuses `input-mismatch` — an invocation id names one
invocation, and reuse with a different payload is a caller error, never a
second execution; a matching open without close refuses
**`outcome-unknown`** — the write may
or may not have committed, and the framework never re-executes into that
uncertainty; no match claims the id and proceeds. The honest limit is stated rather than
papered over: deduplication is **session-scoped**. A retry against a new
session is not deduplicated; the durable ledger of the crashed session is
the operator's diagnostic, and the `outcome-unknown` finding of §5.3 is what
tells them to look. With record `uid`s random by default, "replay identical
inputs" is *never* a safe idempotency story, and this protocol does not
claim one.

### 6.3 The refusal envelope

Refusals cross the endpoint as structured data, not strings clients parse:
`{code, message, data}` with a **closed framework code set** —
`unknown-command`, `invalid-input`, `permit-exceeded`, `outcome-unknown`,
`unknown-cursor`, `stale-cursor`, `input-mismatch`, `kernel-refused` —
extended only by spec amendment. `permit-exceeded` carries the requirement
and the exceeded capability as fields. `kernel-refused` carries the kernel's
own prefix-stable reason verbatim in `message` and its structured refusal
kind (the `WriteRefused` subclass name or value-refusal type) in `data`;
the renderer presents it verbatim, and nothing upstream repairs, retries
with altered inputs, or writes around it. The kernel's two refusal
conventions reach the endpoint through **one normalization path**:
exception-style refusals (`WriteRefused` and its subclasses) propagate as
raised, and value-style refusals (`RunRefused`, `AdmissionRefused`, …)
are raised by the invocation-scoped writer wrapped in
**`KernelRefusalValue`** — a scoped writer never *returns* a refusal
value, so the dispatcher has exactly one place to translate either shape
into this envelope, and a write-path refusal always carries the
invocation id it was bound to.

### 6.4 The threat boundary

Command inputs, model output, cursors, and configuration files are
**untrusted**: validated, canonicalized, refused on violation, and never a
source of identity or capability. Actor, permit, session identity, resolved
roots, and the ledger are **endpoint-owned**: bound at session open from the
launcher's own state, never accepted from a request. In this sub-project the
interactive endpoint and the actor share a trust domain (the person's own
process tree); the statement is normative now so that sub-project 6's
sandbox changes where the boundary is enforced, not what it is.

## 7. The budgeted renderer

### 7.1 Reports, not prose

A handler returns a **`Report`**: an ordered sequence of typed blocks from a
closed set — `heading`, `keyvals`, `record`, `finding`, `text`. One renderer
serializes a report deterministically (stable ordering, stable formatting,
no timestamps it did not receive) and enforces the declared budget in UTF-8
bytes over the full emitted payload, marker included.

### 7.2 Truncation with guaranteed progress

Truncation happens at block boundaries, appending a visible marker naming
the byte cap and the continuation cursor. If the next block alone exceeds
the remaining budget and nothing has been emitted for it, the renderer
splits **inside** the block at a UTF-8 character boundary — so a single
oversized block cannot stall paging — and the cursor addresses
`(block index, intra-block byte offset)`. Every page emits at least one
byte of report content; progress is a renderer test, not a hope.

### 7.3 Continuation is a dispatcher operation

A continuation is a request carrying the `cursor` protocol field, handled
by the dispatcher before command dispatch; it is never a general
re-execution handle, and cursors carry no inputs. Every cursor field is
bounded — command names by §3.1's grammar, identifiers by §6.2's,
digests at their fixed hex width, positions as fixed-width `u64`
`(block index, intra-block byte offset)` pairs — and the versioned
encoding over them therefore has a computable maximum, published as
`MAX_CURSOR_BYTES` and asserted by test. A cursor that does not parse
under the encoding's grammar refuses `unknown-cursor`. The two cursor
forms match the two invocation classes:

- **Read cursors are stateless.** A read cursor encodes `(command name,
  input digest, report digest, position)` and references nothing durable —
  reads leave no ledger trace (§5.2). Continuation is the same command
  invoked again with the same inputs plus the cursor: the dispatcher
  verifies the canonical input digest against the cursor's or refuses
  `input-mismatch`, re-executes the read handler, re-renders in full, and
  compares the fresh report's digest to the cursor's — equal emits the
  next window; different refuses `stale-cursor`: the world moved, and the
  caller re-runs the command rather than receiving a spliced view. Nothing
  is cached; the handle leads back into the world, and it works across
  processes because it depends on nothing but the world.
- **Write cursors are ledger references, and write continuation never
  calls the write handler.** A write cursor encodes `(session id,
  invocation id, position, report digest)`; the dispatcher resolves the
  session ledger under the operations root — any endpoint over the same
  operations root can continue — or refuses `unknown-cursor`, then
  re-renders only what the ledger proves: the invocation's minted record
  identities, loaded back through ordinary reads. A write is executed at
  most once per invocation, and no cursor changes that.

### 7.4 The write-audit rule

For a write-class invocation the report may contain **only** `record`
blocks, and the renderer — receiving the invocation's `act` lines —
refuses to serialize one whose identity is not among the minted record
identities. Handler-authored `heading`, `keyvals`, `finding` and `text`
blocks are refused outright for writes: any of them is a channel for the
predecessor's audit echo, which checking record blocks alone would not
close. What a write invocation emits is its minted records, the
dispatcher-rendered refusal envelope if there was one, and the renderer's
own framing — nothing else. The rule is a renderer test with mutations
that fail it, per block kind (§11).

## 8. The preamble

One `commands/PREAMBLE.md`, prepended by the adapter generator to every
emitted prompt body and versioned with the commands. Content, kept short
enough to be read every time: there is one world, read through the current
view — with the exception stated in the preamble itself that until
sub-project 1 lands no view exists and commands read world state directly,
as `status` does; every write is a kernel act that returns a record or a refusal; report
refusals verbatim and never write around them; results are budgeted, and the
cursor is how you continue; a command's inputs are the whole interface —
there is nothing to reach around.

> **Amended 2026-09-23** (`docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md`
> §5, §11). Sub-project 1 landed at cut 14, so the exception above is
> retired. The preamble now states the rule: the world is read through the
> selected project's query when one is selected and whole when none is; a
> question or task needs a selected project, a fact does not. Selection
> itself arrives with the coordination command set (`sci-c5528e`), and until
> then the preamble says no project can be selected yet.

## 9. Surfaces

### 9.1 Configuration

One launcher-owned TOML file, located by `--config PATH` or
`SCIENCE_CONFIG`: the fields of `beliefs.WorldConfig` (world root, world id,
corpus roots) plus `operations_root`, `domains`, `contracts`, and `store_root`.
The loader constructs
`beliefs.WorldConfig` directly — no parallel world model, no drift.
Configuration is untrusted input (§6.4): paths are resolved and validated at
session open.

`domains` (**added 2026-09-09** with §5.1's required `profile`) is the list of
domain-contract namespaces the world's profile activates — `["biology"]` for a
corpus pinning the shipped biology pack, `[]` for the shipped base alone. The
loader compiles the `ProfileSpec` at load time from
`beliefs.profile.shipped_base_contract()` and one
`shipped_domain_contract(namespace)` per entry, and carries it on
`ScienceConfig`; a namespace the package does not ship raises `ProfileError`,
which the loader reports as `invalid-input` like every other configuration
fault. The key is **required and may be empty**: the loader accepts exactly the
declared key set, so a configuration written before this amendment refuses
rather than silently compiling a base-only profile against a corpus that pins
domains.

`service_socket` (**added 2026-09-09**: `sci-fd792c`) is the one optional key:
the path of the service socket `science serve` binds and write-class CLI
invocations connect to, resolved like `operations_root`. Absent, it is
`service.sock` beside the operations root. It exists because AF_UNIX caps a
socket path at 107 bytes and a worktree checkout's operations root already
exceeds that; the loader is the single place both ends read the path, which
is what keeps them agreeing.

`contracts` and `store_root` (**added 2026-09-09**: belief-path design §5.1).
`contracts` lists corpus-local domain-contract documents by path, parsed
against the shipped base and compiled into the profile with the shipped
domains; a document may carry an operator `plan` the `claim` command reads.
It is required and may be empty, for `domains`'s reason. `store_root` is the
holdings store the session and the `dataset` command bind, resolved like
`operations_root`; required. Both are superseded whenever the kernel gives
contracts a home (belief-path ruling 5).

### 9.2 CLI

`science`, stdlib `argparse`, zero dependencies. One subcommand per shipped
command, options compiled from the declaration. Command subcommands consume
`--config`, `--invocation-id` and `--continue <cursor>` (the wire form of §6's
protocol fields — continuation is the same subcommand re-run with its inputs
and the cursor). `science mcp serve` consumes only `--config`; `science build`
and `science adapters build` consume none of those protocol options. The
`science serve` parser entry is deliberately absent until Task 13 implements
the service process. Exit
codes: `0` success, `1` internal error, `2` invalid invocation (argparse's
own convention), `3` refused.

For every command invocation, stdout contains rendered output only. Stderr
contains exactly one compact, key-sorted JSON line. Success emits
`{"invocation_id":"<id>"}`. Refusal emits
`{"invocation_id":"<id>","refusal":{"code":"…","data":{},"message":"…"}}`,
preserving the complete §6.3 envelope; a missing caller id is minted before
configuration loading so even an early refusal is bound. Unexpected failures
emit only the generic `internal-error` shape (and the id when already bound),
never exception text.

**2026-09-09 amendment — startup findings.** `science serve` writes one
compact, key-sorted JSON line per session-reconciliation finding to stderr
at startup, and nothing when there are none. Reporting runs once, without
polling or blocking startup on findings. `session-unclosed` means the
referenced session's ledger has no close line; a healthy live peer over the
same operations root also produces it, so it is not proof of a crash.
Findings may be followed by a CLI refusal or internal-error line if startup
fails. Existing top-level keys distinguish the lines:

| key present | line shape |
|---|---|
| `severity` | session-reconciliation finding |
| `refusal` | CLI refusal envelope |
| `error` | CLI internal error |

**Read-only commands run in-process with
only the read context** — no `WriterSession` is opened and no ledger is
touched (§4.2, §5.2); read cursors are stateless (§7.3), so paging needs
nothing a process could leave behind. Once Task 13 lands, **write-class
commands go through the service process** — `science serve`, the CLI's
service of §5.2 of the layer design, same
endpoint core as the MCP server over a local socket — never an in-process
writer opened per invocation around the endpoint architecture. Until then the
production write gate makes this path unreachable; no shipped command writes.

### 9.3 MCP server

**2026-09-09 amendment — startup findings.** `science mcp serve` writes one
compact, key-sorted JSON line per session-reconciliation finding to stderr
at startup, and nothing when there are none; stdout remains JSON-RPC only.
The §9.2 discrimination table applies: top-level `severity` marks a finding,
`refusal` or `error` marks a CLI failure, which may follow the findings.
Reporting runs once, without polling or blocking startup on findings.
`session-unclosed` means the referenced session's ledger has no close line;
a healthy live peer over the same operations root also produces it.

`science mcp serve`, stdio transport, one attended session per server
lifetime; the harness configuration that starts it is the person's launcher.
The server pins **MCP protocol revision `2026-07-28`** — the revision that
retired the `initialize` handshake in favor of a **mandatory
`server/discover`** method — whose result carries `supportedVersions`,
`capabilities`, and the server's `Implementation` under
`_meta["io.modelcontextprotocol/serverInfo"]`, plus the required
`CacheableResult` fields `ttlMs` and `cacheScope` — requires every request to
carry `_meta` with the namespaced `io.modelcontextprotocol/` keys
(protocol version and client capabilities required; client info optional
when absent, validated as an `Implementation` when present), and
**removed protocol sessions entirely**: requests are independent.
Protocol errors stay in the protocol's vocabulary, distinct from
framework refusals: malformed JSON is `-32700` and never ends the stdio
loop, an invalid envelope (`jsonrpc`, non-null string/integer `id`,
string `method`) is `-32600`, a malformed params object, missing required
`_meta` fields, and unknown tool names are `-32602`, and an unsupported
protocol version is `-32022` carrying the supported and requested
versions. The attended
**writer** session is not an MCP concept at all — it is launcher-owned
process state, bound to the server process from spawn to exit, that those
independent requests share: one person, one full permit, one ledger.
JSON-RPC notifications omit `id` and receive no response. `tools/list` is a
cacheable paginated result; this implementation returns its complete list
without `nextCursor`, and therefore refuses every supplied cursor as invalid
or expired instead of ignoring it. `tools/call` recognizes the standard
optional `inputResponses` object and `requestState` string. Because science
never returns `input_required`, either field is unsolicited state and is
refused `-32602` after its outer type is validated. Every result tree is newly
allocated, so one caller cannot mutate later discovery, list, or schema
responses.

Stdio is newline-delimited strict UTF-8 over a binary reader, bounded by the
published `MAX_REQUEST_BYTES = 1_048_576`. The reader allocates only a bounded
prefix, drains an oversized frame through its newline, emits a protocol error,
and then serves the next frame; invalid UTF-8 is a parse error and likewise
does not terminate or desynchronize the loop.

The tool list is generated 1:1 from the declarations — name, `purpose` as
description, input JSON Schema from the canonical inputs **plus the
optional protocol properties `invocation_id` and `cursor`**, which the
reserved input names of §3.2 guarantee can never collide with a command's
own inputs. There is no separate continuation tool; a call carrying
`cursor` is a continuation. Tool calls enter the same dispatcher.

### 9.4 Equivalence

The three frontings share one dispatcher and one renderer; a transport-level
test (§11) invokes `status` through the CLI and through the MCP server
against the same fixture world and asserts byte-identical rendered payloads,
not merely equivalent dispatcher calls.

## 10. The adapter generator

`science adapters build` emits `adapters/claude-code/`, a committed,
never-edited tree, diffed against a fresh build by a test:

- `.claude-plugin/plugin.json` — the plugin manifest.
- `skills/<name>/SKILL.md` per command — the **skills form, not the legacy
  flat `commands/` files**, per the current Claude Code plugin reference:
  frontmatter (name, description from `purpose`) and body = preamble +
  prompt body. Authored skills under `science/skills/` are carried through
  beside the generated ones; a name collision between the two is a build
  refusal.
- `.mcp.json` — registers `science mcp serve` by command name and
  `${CLAUDE_PLUGIN_ROOT}`-relative or PATH-resolved invocation only; no
  machine paths in the generated tree. World selection stays in the user's
  environment (`SCIENCE_CONFIG`), never baked into the plugin.

Other harnesses are further targets of the same generator, added when a
second harness is actually used.

`science build` and `science adapters build` call the same preflight. Before
any adapter output mutation it validates handler signatures and skill-name
collisions; rejects symlink, special-file, or uncontained command directories,
TOMLs, prompts, preamble, and authored-skill sources; and snapshots every
source's text or bytes. Generation reads only that snapshot.

## 11. Shipped surface and testing

**`status`** — write class `read-only`; reads: registry, epoch, corpus
stored records; budget 16384 bytes. Renders: the world's corpora with
lifecycle status, followed by one `Finding` block per finding the registry's
status reduction carries for a corpus (**added 2026-09-09**: `sci-097534`;
`duplicate-carrier` is the one such finding today, and a read context over
two roots carrying one corpus id opens both rather than refusing, so the
finding can be shown); the current epoch's packaging identity or its stated
absence; per-corpus record counts by kind. Nothing else — `status` is the
framework's proof, not a dashboard.

Synthetic test-only commands (fixtures, not shipped) exercise: a
`coordination` declaration (schema and dispatch only, until sub-project 1
provides the contract), a `mints:<kinds>` command that stays within its
declaration, one that exceeds it (act-time refusal), a command whose
declared class exceeds the session permit (declaration-time refusal), and a
`publishes` declaration — which proves schema, dispatch and permit shape
only; nothing can prove the real publish act until sub-project 5 lands, and
this spec does not claim otherwise.

Every check in N2's harness shape — the assertion, the source mutation that
falsifies it, the test that catches the mutation:

- **`beliefs`:** per-entry-point permit refusal before any effect; the
  invocation-scoped writer refusing an act inside the session's ceiling
  but outside the requirement; endpoint-set actor (a caller-supplied actor
  has nowhere to enter); every session corpus write leaving an
  actor-bearing `corpus-write` intent (a mutation dropping the intent is
  caught by reconciliation's attribution test); ledger
  append-before-report; refusal-envelope persistence round-tripping
  through `invocation-close`; reconciliation classifying a covered, an
  `outcome-unknown`, and a foreign entry distinctly.
- **`science`:** declaration build refusals (each §3.4 case, the
  route-ambiguity and below-minimum-budget refusals included); budget
  enforcement, oversized-block progress, deterministic serialization;
  write-audit refusal per block kind — a foreign record block and each
  handler-authored non-record block; read continuation's stale-cursor on a
  mutated world and input-mismatch on altered inputs, and write
  continuation's never-calls-the-handler; retry dedup, the concurrent
  same-id race resolving to one execution under the dispatch lock,
  id-reuse `input-mismatch`, and `outcome-unknown`; the `status` reader
  test on a fixture world; source-safety mutations for command-directory,
  TOML, prompt, and preamble symlinks; the adapter tree diff; bounded MCP
  framing recovery; notification silence; and the CLI/MCP byte-equivalence
  test.

## 12. The knowledge-model pressure points, carried in

1. **No kind is minted here (§4.1 of the layer design).** The schema can
   only *name* kinds that a `beliefs` contract declares; there is no
   registration surface, and a kind a command wants is a request to
   `beliefs`.
2. **Context binds a world; the view slot is reserved (§4.2).** The
   dispatcher's context carries the world and a not-yet-populated current
   view; the view query language and selection are sub-project 1's, and no
   command in this sub-project takes a project or view input.
   *Amended 2026-09-23:* the selection rule is the projects design's §5 —
   a session fact, never derived from the working directory, whole-world
   when unselected — and the slot is populated by the coordination command
   set (`sci-c5528e`).
3. **No suppression surface (§4.3).** The schema has no deny-list, ignore
   or severity field; a finding a command surfaces is rendered, and the
   renderer has no channel for hiding one.
4. **Nothing persists a ranking, and the budget is the contract (§4.4,
   §5.3).** No command writes derived state; `output_budget` is declared
   per command, enforced by the one renderer, and tested.

## 13. Repository layout and task mapping

```
science/
  commands/               # source: <name>/command.toml + prompt.md; PREAMBLE.md
  skills/                 # authored skills, carried into the plugin
  adapters/claude-code/   # generated, committed, never edited
  python/src/science/     # schema, dispatch, render, cli, mcp, serve;
                          #   handlers under science/commands/
  docs/specs/             # this document
```

Deliverables split by repository: §§4–5 are `beliefs`' (`beliefs-96a24a`
for permits; a new `beliefs` task for the writer session and ledger, on
which this repository's endpoint work depends); everything else lands here,
as tasks under `--spec command-framework` once this spec is approved.

## 14. Alternatives rejected

- **Exposing kernel primitives as public CLI/MCP tools.** Violates §5.2 and
  §7.4 of the layer design, turns the union of declarations into an
  expanding capability surface, and makes prompt parsing an enforcement
  mechanism.
- **A `prompt`/`tool` hybrid command ontology.** Two ontologies, neither
  implementation path removed; the orchestration-only case is a skill.
- **Python-first declarations.** "Fits the schema or does not ship" becomes
  a runtime property of imported modules instead of data validation.
- **Frontmatter-markdown declarations.** Structured typed inputs live
  awkwardly in frontmatter, and the declaration/prompt split disappears.
- **A daemon from day one.** Transport and lifecycle plumbing before the
  sandbox that makes it meaningful exists; the session API is the stable
  seam instead.
- **An in-process full-permit writer inside the CLI for writes.** Bypasses
  the endpoint architecture the moment it exists; reads are the only
  in-process path.
- **Cursors carrying canonical inputs.** An opaque blob that re-executes
  whatever it says is a confused-deputy handle; a read cursor that only
  *verifies* caller-supplied inputs by digest, and a write cursor that is a
  ledger-validated reference, are not.
- **Ledgering every read for continuation.** Persisting each read's
  canonical inputs would grow the governing write ledger into a durable
  query store, a data boundary this design declines to cross without
  retention rules it does not need; stateless read cursors cost a
  recomputation instead.
- **Deriving act families as the union of a kind's routes.** Over-requires
  every route capable of minting the kind and wrongly refuses a session
  permitting one valid route; the declaration selects, `KIND_ACTS`
  validates.
- **String-prefix refusal parsing at the endpoint.** Clients matching on
  message prefixes is the predecessor's habit; codes are data.
- **A per-command budget default.** A default is where the 21 MB read
  hides; every declaration states its number.
