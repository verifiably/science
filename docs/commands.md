# Commands and reports

Type: data model; document types 1. Command declarations use schema version 1;
cursors use `scur1`. Configuration and the library handler interface are currently
unversioned. [Sessions](sessions.md) specifies ordering; [sharing](sharing.md)
specifies sharing state and acceptance. Kernel records are defined in
[beliefs](https://github.com/verifiably/beliefs/blob/main/docs/records.md).

## Declaration schema 1

A production command is a real directory `commands/<name>/` containing exactly
regular files `command.toml` and `prompt.md`; symlinks and extra entries refuse.
The command-tree root is real too and may additionally contain `PREAMBLE.md`.
The name matches `[a-z][a-z0-9]*(-[a-z0-9]+)*`, at most 32 UTF-8 bytes, and must
match its directory. `continue`, `serve`, `mcp`, `adapters`, `build` and `epoch`
are reserved built-in names. An unknown declaration key refuses the build.

| Field | Contract |
| --- | --- |
| `schema_version` | Required integer `1` |
| `name` | Required command name |
| `purpose` | Required nonempty single-line string |
| `write_class` | Required class below |
| `output_budget` | Required positive integer, at least `science.cursor.MIN_OUTPUT_BUDGET` |
| `selects` | Optional boolean, default false; only read-only commands may set it |
| `inputs` | Optional mapping of input names to input declarations |
| `reads.families` | Optional list of nonempty strings, default `[]` |
| `write.routes` | Optional mapping from declared minted kinds to admissible kernel routes |

Input names match `[a-z][a-z0-9]*(_[a-z0-9]+)*`, at most 32 bytes. Reserved names
are `cursor`, `invocation_id`, `view`, `session`, `config` and `project`. Each input
has required `type`, `required` (boolean), and nonempty string `doc`. Types are
`string`, `int`, `bool`, `enum` and `list-of-string`. Only enum permits `choices`,
a nonempty list of unique strings. Optional `default` must match the type and any
enum choices; required inputs forbid a non-null default. No other input keys exist.

At invocation, unknown inputs, explicit null, wrong types and missing required
values refuse. Omit an optional input to use its default; without a default it
is omitted from the canonical mapping. Booleans do not satisfy integer inputs.
Canonical inputs are sorted by name, with defaults applied; the input digest is
SHA-256 of compact sorted JSON. CLI and MCP use this same dispatcher canonicalizer.

## Write classes and handlers

| Class | Effect boundary |
| --- | --- |
| `read-only` | Receives `ctx`; no writer session required |
| `mints:<kind>,…` | Receives `ctx, writer`; requirement derives from listed kinds/routes |
| `coordination` | Receives `ctx, writer`; coordination mint/revision acts |
| `publishes` | Receives `ctx, writer`; publication capability |
| `session` | Receives `ctx, port`; records exactly one selection, never a corpus act |
| `sharing` | Receives `ctx, writer`; records sharing lines, never a corpus act |

Non-minting classes take no `write.routes`. Minted kinds must be in the contract
inventory. A route must be admissible for its kind; ambiguous kinds require an
explicit route, and routes for undeclared kinds refuse. Science passes capability
requirements to the kernel; it does not construct an unrestricted permit.

Handlers resolve by convention to `science.commands.<name_with_underscores>.handle`.
They lead with the positional parameters above, followed by keyword-only inputs.
No variadic or positional-only parameters are permitted. Handler inputs exactly
match declaration inputs: required inputs have no default, optional ones default
to `None` (the dispatcher applies declared defaults before the call).

A handler returns a tuple of typed report blocks. Read reports can use `Heading`,
`KeyVals`, `Finding`, `Text` and record detail. Corpus-write reports contain only
`RecordBlock`s for records minted by that invocation. The audit rejects non-record
blocks and identities not minted by the invocation; it does not require the handler
to include every minted record. The dispatcher rebuilds the full canonical report
from all ledger-bound `(uid, record_id)` pairs, sorted by that pair, regardless of
the subset supplied by the handler.
Session reports contain exactly one `SelectionBlock` matching the selection line.
Sharing handlers return only `KeyVals`/`Finding` commentary; the dispatcher prepends
all `PinBlock`s derived from that invocation's sharing lines.

## Refusals and identities

The refusal wire value is exactly `{code, message, data}`: a known string code,
human-readable message and object of structured detail. `Refused` can also carry
the invocation id; transport envelopes keep it separate from the refusal value.
Invocation IDs match `[A-Za-z0-9_-]{1,64}`; an omitted id becomes 32 random hex.
Record addresses, corpus identities, invocation IDs and page cursors are distinct.

Codes: `unknown-command`, `invalid-input`, `permit-exceeded`, `outcome-unknown`,
`unknown-cursor`, `stale-cursor`, `input-mismatch`, `kernel-refused`,
`no-current-project`, `unknown-project`, `ambiguous-project`, `no-epoch`,
`epoch-stale`, `multiple-assessed-propositions`, `pin-unsourced`, `world-mismatch`, `adopt-conflict`, `corpus-retired`,
`divergent-publication`, `config-stale`. Kernel normalization preserves the named
kind/reason or permit requirement/capability in `data`; callers should use codes
and detail instead of parsing prose. These are refusals, not evidence of a run.

## Paging and cursor format

Budgets count UTF-8 bytes, including the truncation marker. Paging advances by
block and byte offset, never splits a code point, and reserves enough space for
its own cursor plus progress. The report digest hashes each serialized block,
prefixed by its eight-byte big-endian length, in report order.

A cursor is `scur1.` followed by unpadded URL-safe base64 JSON. The closed forms:

- Read: `{f:"r", c:command, i:input_digest, r:report_digest, b:block, o:offset}`.
- Write: `{f:"w", s:session_id, n:invocation_id, r:report_digest, b:block, o:offset}`.

Digests are 64 lowercase hex; session ids are 32 lowercase hex. Positions are
integers in `[0, 2**64-1]`. Unknown/duplicate keys, wrong forms, invalid base64,
non-ASCII tokens, bad identifiers or an oversized token refuse `unknown-cursor`.
The size bound derives from maximum encodable field lengths, not an unbounded
JSON parse. Cursors are not authority or signatures: the dispatcher rechecks their
bindings, report digest and valid UTF-8 position. Read continuation reruns the
read with the same canonical inputs and current selection; changed report content
refuses `stale-cursor`. Write continuation rebuilds the ledger-bound outcome,
never repeats effects. A write cursor stays bound to its original session and
invocation ledger, but any endpoint over the same `operations_root` can continue
it while the ledger and referenced records remain available; the library reader
needs no active writer session or handler. This durable lookup is distinct from
new-write deduplication, which remains scoped to the original attended session.
Sharing replay also needs its saved presentation tail; changing or losing
commentary can stale the cursor.

## Scientific command contracts

Exact current inputs, defaults and prompts are the public files under
[`commands/`](../commands/); CLI help and MCP schemas derive from them.

- `claim` uses the first activated operator plan, mapping subject/object into
  named roles. Two one roles or two canonical many-role members are supported.
  Dataset, selection and run-output vocabulary bindings must resolve against held
  text vocabulary; world-kind bindings consult accepted live canonical records.
  Not-member and unperformed held-vocabulary checks refuse authoring. Release
  bindings retain the kernel's permissive reading when not consulted.
- `dataset` accepts a regular local file or a directory package (auto-discovering
  every regular file under the directory, or admitting the explicit relative
  member paths named by `--resources`), fingerprints and holds each resource's
  bytes before minting the declaration/observation evidence. A declaration
  already held in a configured mount refuses rather than redeclaring it locally.
  Identical titles or basenames do not define a dataset's identity or storage
  directory.
- `derive` executes a dataset-production workflow under confinement over a primary
  `--dataset` (`transforms` role) and optional `--reads` auxiliary datasets (`reads`
  role), with optional `KEY=VALUE` `--parameters`. It stages each input dataset's
  resources under `inputs/<resource.name>`, exports and holds every declared
  `--targets` output in the store, and mints the production `run` and derived
  `dataset` records (with its stamped `lineage-basis`).
- `spec` reads a strict UTF-8 schema-version-1 estimand JSON document, required
  standing/evidence mode and explicit rule-procedure bindings. Native named
  measures, outputs, control, references, assumptions and calibration are checked
  against the target claim and held prerequisites before freezing. Numeric JSON
  literals become exact finite Decimals; booleans/NaN/Infinity, duplicate/unknown
  keys and frozen-only fields refuse. Applicability flags support term restrictions
  on applicability-placed dimensions only. Authoring reads accepted live session
  records and cross-mount retractions without requiring an epoch. One observes
  dataset and deterministic nondeterminism remain the command's authoring scope;
  supersedes must resolve in the write root before effects. See the complete
  [example and field rules](guide.md#author-a-native-estimand).
- `run` requires the spec's declared observed dataset (and stages any `reads` role
  datasets declared on the spec), a code directory, an existing entrypoint relative
  to its parent, and at least one output target. Both single-resource and
  multi-resource dataset packages stage under `inputs/<resource.name>`. Host
  confinement prerequisites and staged-path collisions are checked before the run
  act. The kernel captures the recipe, environment, inputs, outputs and closure;
  refusal evidence is retained.
- `assess` restores the run's frozen spec and interpretation rule; the caller cannot
  choose a new outcome or target after seeing the result. It persists the exact
  derived target, named estimates, uncertainty and curves, with a full native
  assessment identity address. The run's observed
  dataset needs empirical standing: an acquired dataset carries it directly, and a
  `derive` package inherits it through a complete, undiverged `lineage-basis`
  chain to an acquired ancestor (the kernel's rule is in beliefs'
  `docs/records.md`); without standing, `assess` refuses. `verify` accepts
  exactly one of `--assessment` (replaying an assessment's run) or `--run`
  (replaying a dataset-production run), resolves the original equivalence
  implementation (`REFERENCE_RULES` or `DATASET_CONTENT_EQUALITY`) before replay,
  uses the original targets, rereads stored run closures, derives scope and mints
  comparison evidence. Supplied code/environment must match the captured recipe;
  no publication marker supplies the workspace checkout for you. Execution
  materials are obtained separately.
- `belief` evaluates one accepted, unretracted assessed target key. `--key` is
  optional for exactly one key, which the report includes. No assessments yields
  NoBelief without an invented key. An unmatched key refuses `invalid-input`;
  several keys without a selection refuse `multiple-assessed-propositions` with
  sorted available keys and an explicit-key remedy. Keys never pool evidence.
  Reads are corpus-local without read mounts and epoch-bound across session
  mounts; coverage must match and no corpus may have moved. Missing/stale epochs
  refuse `no-epoch`/`epoch-stale`; publish a fresh epoch with `science epoch`.
- `next` reads attention live and keeps one row per proposition. Unassessed rows
  retain ready/not-ready input-heldness rules. An assessed row with several keys
  is assessed-unevaluated (`multiple-assessed-propositions`), listing sorted keys
  and a `science belief --proposition <id> --key <key>` remedy, even when individual
  keys admit. A single key is admitted only when a matching assessment passes the
  native dependency-aware admission gate. Missing/stale epochs or unavailable
  inputs remain row-level unevaluated reasons; one row never hides the others.
- `recheck` observes the named store location without writing its bytes and publishes
  governed observation/act-report evidence; a failed or inconclusive retrieval does
  not assume absence or clear an unsettled block. See [stores](stores.md).

## Coordination command contracts

`project` mints a project with a YAML/JSON query, without needing an existing
selection. `question` and `hypothesis` mint views under the current project; `task`
mints an open task with optional dependencies; `decide` records a decision and
its reasoning. Subordinate addresses are scoped by project identity. A query is
parsed and validated before effects; it selects world records, not coordination
records. Publication closure and query graph traversal are separate operations:
a query must explicitly include every required closure record.

`reuse` copies a question/hypothesis query into the selected project as one new
mint, preserving a pinned source pointer in prose; it does not bridge address
spaces. `revise` writes a whole new revision naming its predecessors, carries over
unchanged fields from one tip, and rejects fields not owned by that kind. Divergent
tips require explicit `repair`, which supplies every field even if only one tip
currently stands. `clear_depends` conflicts with explicit `depends`. Project
selection reports its resolved pinned revision; later reads resolve the current
tip rather than silently reselecting an obsolete revision.
