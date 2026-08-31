# Command framework — design

**Date:** 2026-08-31
**Status:** draft — design approved in session 2026-08-31 with the interface
and security revisions incorporated; spec review pending
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
   are never exposed publicly: the endpoint receives a command name and
   inputs and nothing else, selects the handler, binds actor and effective
   permit, and performs the kernel calls internally. A unit that only
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
  An `enum` requires `choices`. An optional input without a `default` is,
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
- **`output_budget`** is required, in bytes, with no default and no
  framework maximum in this sub-project; §5.3 of the layer design makes it
  the contract, and the renderer (§7) makes it a test.

### 3.3 Write classes

The closed set, and what each requires of the session (both permit
dimensions — see §4.2 for the capability model):

| write class | required record kinds | required act families |
|---|---|---|
| `read-only` | none | none |
| `coordination` | the coordination contract's kinds (sub-project 1) | `corpus-write` |
| `mints:<k1,…>` | the named kinds | `corpus-write` ∪ ⋃ `KIND_ACTS[kᵢ]` |
| `publishes` | the publication kinds (sub-project 5) | `publish` |

A `mints` class must name kinds that exist in the governing contract the
build validates against; an unknown kind is a build refusal. Until
sub-project 1 lands there is no coordination contract, so a
`coordination`-class command cannot ship — which is exactly decision 1's
scope: it exists only in test fixtures until then. Likewise `publishes`
until sub-project 5.

### 3.4 Build refusals

`science build` (invoked by the adapter generator, the CLI's self-check and
the test suite) validates every declaration against the schema and refuses
the tree — not the command — on: schema violation, name grammar or reserved
name violation, directory/name mismatch, handler missing or its keyword
signature disagreeing with the declared inputs, unknown kind in a write
class, duplicate command or skill name. A command that does not fit the
schema does not ship, as a refusal with the file and field named.

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
kind to the act families whose operations mint it (for example `dataset` and
`run` to `run`; `holdings-observation` to `holdings`; ordinary records to
`corpus-write` alone). Its full contents are settled with `beliefs-96a24a`'s
plan; the mapping is data, exported read-only, and is what lets a
declaration's write class be translated into a capability requirement
without `science` knowing act families exist.

### 4.2 Requirements, not permits, cross the layer boundary

§5.2 of the layer design is literal: `science` never sees, threads, or
constructs a permit. `beliefs` exports a **`RequiredCapabilities`** value
with constructors — `RequiredCapabilities.none()`, `.coordination()`,
`.for_kinds(kinds)`, `.publishes()` — and the session exposes
`WriterSession.check(required)`, which returns nothing or a structured
refusal (§6.3). `science` compiles a declaration's write class to a
requirement through those constructors and asks; it never holds either
frozenset. `WritePermit.full()` exists in `beliefs` for its own launcher
constructors (§5.1) and is not importable policy for `science` code.

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

### 4.4 Acts without log evidence are not command-reachable

`adopt_manifest` writes the manifest through a direct `CreateOp` with no
operation intent, and the root lifecycle acts (`init_*`, `replicate_root`,
`restore_root`, `fork_*`) write outside any chain. They remain permit-gated
(family `lifecycle`), but **no write class maps to `lifecycle`**, so no
command — shipped or synthetic — can reach them: they are launcher- and
operator-time library operations. The session ledger (§5.2) therefore only
ever claims acts that have chain evidence, and §7.1's ledger-versus-chain
comparison never meets an act that could not appear in a chain.

## 5. Writer sessions in `beliefs`

### 5.1 Opening a session

`beliefs` exports launcher constructors, not a raw session:

- `open_attended_session(world_config, operations_root)` — full permit by
  construction; the interactive constructor every §2 fronting uses.
- A run-session constructor with a tier parameter arrives with sub-project 6
  and is out of scope here beyond the seam existing.

Opening mints a **fresh session identity** — a digest-shaped token — and
fixes the **actor** as `session:<session-id>`. The session sets every
intent's `actor` itself; no caller of the session supplies one, which is
where `actor` stops being a caller-supplied string. The returned
`WriterSession` is the **trusted server-side object**: it lives in the
endpoint process and wraps the permit-bound entry points and the ledger. It
is distinct from the **session handle** — the transport address and
per-session token an actor process will hold — which does not exist until
sub-project 6 builds the sandbox; naming the distinction now is what lets 6
add the boundary without changing this API.

### 5.2 The session ledger

An append-only JSONL file at
`<operations root>/sessions/<session-id>/ledger.v1`, outside every corpus,
written with append-then-fsync before any result is reported. Typed lines:

- `session-open` — session id, actor, world id, permit summary, timestamp.
- `invocation-open` — invocation id, command name, canonical inputs, input
  digest (§6.2), timestamp. Written for **every** invocation, reads
  included: the ledger doubles as the paging basis (§7.3).
- `act` — invocation id, corpus id, **chain entry digest**, and the
  **minted record identities** (uid and id). The pair is deliberate: the
  entry digest ties the line to the chain, the record identities are what
  the write-audit rule (§7.4) and continuation (§7.3) verify against;
  neither substitutes for the other.
- `invocation-close` — invocation id, outcome (`done` or a refusal code),
  minted record identities in total.
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

A request names a command and its inputs, plus optional protocol fields.
The dispatcher, in order: (1) resolve the command or refuse
`unknown-command`; (2) validate and canonicalize inputs against the
declaration or refuse `invalid-input`; (3) compile the write class to a
`RequiredCapabilities` and `session.check` it — the declaration-time permit
refusal, before the handler runs; (4) append `invocation-open`; (5) invoke
the handler, whose kernel writes pass through the session and may still
refuse at the act if the body exceeds its declaration; (6) render under the
budget (§7); (7) append `invocation-close`. Continuation requests (§7.3)
are a dispatcher operation handled before this pipeline and never reach a
handler through it.

### 6.2 Invocation identity and retry

The caller may supply an **`invocation_id`** (protocol field, opaque token);
absent one, the dispatcher mints one and returns it with the result. For a
write-class invocation the dispatcher deduplicates within the session
against the ledger before step 5: a matching `invocation-open` with
`invocation-close` returns the recorded outcome re-rendered (no re-execution);
a matching open without close refuses **`outcome-unknown`** — the write may
or may not have committed, and the framework never re-executes into that
uncertainty; no match proceeds. The honest limit is stated rather than
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
with altered inputs, or writes around it.

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

A cursor is an opaque token encoding `(session id, invocation id, position,
report digest)` — a **validated reference into the durable session
ledgers**, never a carrier of inputs and never a general re-execution
handle. `continue(cursor)` — the CLI's `science continue <cursor>`, the MCP
tool `science-continue` — is handled by the dispatcher before command
dispatch:

- It resolves the cursor's session ledger under the operations root (any
  endpoint over the same operations root can continue, so CLI paging works
  across process-per-invocation sessions) and the `invocation-open` line, or
  refuses `unknown-cursor`.
- **Read continuation** re-executes the read handler with the ledgered
  canonical inputs, re-renders in full, and compares the fresh report's
  digest to the cursor's: equal emits the next window; different refuses
  `stale-cursor` — the world moved, and the caller re-runs the command
  rather than receiving a spliced view. Nothing is cached; the handle leads
  back into the world.
- **Write continuation never calls the write handler.** It re-renders only
  what the ledger proves: the invocation's minted record identities, loaded
  back through ordinary reads. A write is executed at most once per
  invocation, and no cursor changes that.

If a caller supplies inputs alongside a cursor (the stateless CLI form),
their canonical digest must equal the ledgered input digest or the request
refuses `input-mismatch`.

### 7.4 The write-audit rule

For a write-class invocation the renderer receives the invocation's `act`
lines and refuses to serialize any `record` block whose identity is not
among the minted record identities — the write returns its own record and
nothing else, plus the refusal if there was one. The predecessor's audit
echo is thereby unrepresentable, and the rule is a renderer test with a
mutation that fails it (§11).

## 8. The preamble

One `commands/PREAMBLE.md`, prepended by the adapter generator to every
emitted prompt body and versioned with the commands. Content, kept short
enough to be read every time: there is one world, read through the current
view; every write is a kernel act that returns a record or a refusal; report
refusals verbatim and never write around them; results are budgeted, and the
cursor is how you continue; a command's inputs are the whole interface —
there is nothing to reach around.

## 9. Surfaces

### 9.1 Configuration

One launcher-owned TOML file, located by `--config PATH` or
`SCIENCE_CONFIG`: the fields of `beliefs.WorldConfig` (world root, world id,
corpus roots) plus `operations_root`. The loader constructs
`beliefs.WorldConfig` directly — no parallel world model, no drift.
Configuration is untrusted input (§6.4): paths are resolved and validated at
session open.

### 9.2 CLI

`science`, stdlib `argparse`, zero dependencies. One subcommand per shipped
command, options compiled from the declaration, `--config` global, plus the
framework verbs `continue`, `serve`, `mcp`, `adapters`, `build`. Exit
codes: `0` success, `1` internal error, `2` invalid invocation (argparse's
own convention), `3` refused. **Read-only commands run in-process**
(each invocation an ephemeral attended session, so its ledger still exists
for paging). **Write-class commands go through the service process** —
`science serve`, the CLI's service of §5.2 of the layer design, same
endpoint core as the MCP server over a local socket — never an in-process
writer opened per invocation around the endpoint architecture. In this
sub-project no shipped command writes, so the service path is built and
exercised by the synthetic exemplars in tests.

### 9.3 MCP server

`science mcp serve`, stdio transport, one attended session per server
lifetime; the harness configuration that starts it is the person's launcher.
The tool list is generated 1:1 from the declarations — name, `purpose` as
description, input JSON Schema from the canonical inputs — plus
`science-continue`. Tool calls enter the same dispatcher.

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

## 11. Shipped surface and testing

**`status`** — write class `read-only`; reads: registry, epoch, corpus
stored records; budget 16384 bytes. Renders: the world's corpora with
lifecycle status; the current epoch's packaging identity or its stated
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

- **`beliefs`:** per-entry-point permit refusal before any effect;
  endpoint-set actor (a caller-supplied actor has nowhere to enter);
  ledger append-before-report; reconciliation classifying a covered,
  an `outcome-unknown`, and a foreign entry distinctly.
- **`science`:** declaration build refusals (each §3.4 case); budget
  enforcement, oversized-block progress, deterministic serialization;
  write-audit refusal of a foreign record block; read continuation's
  stale-cursor on a mutated world and write continuation's
  never-calls-the-handler; retry dedup and `outcome-unknown`; the
  `status` reader test on a fixture world; the adapter tree diff; the
  CLI/MCP byte-equivalence test.

## 12. The knowledge-model pressure points, carried in

1. **No kind is minted here (§4.1 of the layer design).** The schema can
   only *name* kinds that a `beliefs` contract declares; there is no
   registration surface, and a kind a command wants is a request to
   `beliefs`.
2. **Context binds a world; the view slot is reserved (§4.2).** The
   dispatcher's context carries the world and a not-yet-populated current
   view; the view query language and selection are sub-project 1's, and no
   command in this sub-project takes a project or view input.
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
  whatever it says is a confused-deputy handle; a ledger-validated
  reference is not.
- **String-prefix refusal parsing at the endpoint.** Clients matching on
  message prefixes is the predecessor's habit; codes are data.
- **A per-command budget default.** A default is where the 21 MB read
  hides; every declaration states its number.
