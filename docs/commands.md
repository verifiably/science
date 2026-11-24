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
never repeats effects. For `derive`, `run` and `verify`, an empty input object
performs cursor-only paging, while any non-empty input object is treated as a full
resubmission: it runs ordinary canonicalization (refusing partial payloads missing
required fields as `invalid-input`) and compares `input_digest` against the
historical invocation digest (refusing changes, including a changed or removed
`workflow_environment`, as `input-mismatch`); neither paging route opens or
prepares a workflow environment. Other write continuations retain their existing
ledger-bound paging behavior. A write cursor stays bound to its original session and
invocation ledger, but any endpoint over the same `operations_root` can continue
it while the ledger and referenced records remain available; the library reader
needs no active writer session or handler. This durable lookup is distinct from
new-write deduplication, which remains scoped to the original attended session.
Sharing replay also needs its saved presentation tail; changing or losing
commentary can stale the cursor.

## Scientific command contracts

Exact current inputs, defaults and prompts are the public files under
[`commands/`](../commands/); CLI help and MCP schemas derive from them.

- `record` reads a world address, a coordination address (optionally pinned), or
  the stored coordination id printed by a write reply. Alternatively, give one
  or more source identifiers. No match is a finding, and every direct match
  prints its own fields, body, holders and whether correction is possible here.
  Source reads show incident coreference pairs from configured live corpora.
  Each row retains the stored pair, signed balance, count of distinct
  (stance, actor, grounds) units, and addresses of the held attestations.
  Open an attestation by address to read its actor and grounds. Endpoint
  availability is shown independently. Two exact endpoints can be `positive`,
  `contested` or `negative`; missing peers are `unavailable`, and any redirect
  gives `historical-redirect`. An exact pair of identifier hits without current
  evidence is `unassessed` and produces a possible-duplicate finding. These
  are direct live links and carry no published epoch receipt. On a `source` or
  `proposition` it lists stored `source assertions` across configured live
  corpora (following source redirects; attributed readings inert in `belief`).
  With a selected project it lists notes about the world record, following
  source redirects.
- `project-show` shows the selected or explicitly named project's query, open
  tasks, questions, hypotheses, decisions, topics, notes and closed tasks.
- `source` mints a world source without a project selection, with a publisher
  title and at least one DOI, PMID, ISBN or accession. Identifiers are normalised
  before lookup across all configured live corpora. Any shared identifier refuses
  before an act, with `data.existing` naming the matching records and their holders;
  an exclusive write-root record can gain an identifier through `source-correct`.
  A source held elsewhere is used as it stands. Retired redirect addresses also
  refuse. Look up every confirmed identifier together with `record` first; never
  retry a refusal with fewer identifiers. Disjoint identifier sets can still mint
  two sources for one work: this is deduplication by shared identifier.
- `source-correct` adds or replaces identifiers on a write-root source, with
  `--address` and `--grounds`. Supplied schemes replace those schemes; other
  identifiers remain. A source held by another live corpus refuses, as do
  unchanged identifiers and collisions with another record. When its basis
  changes, the reply shows its new address and the old address keeps resolving,
  including earlier notes. Identifiers cannot be removed without a replacement;
  retired addresses remain taken.
- `source-coreference` attests whether two current source addresses describe the
  same citable version. Supply `--left`, `--right`, `--stance same|distinct`, and
  nonblank NFC `--grounds`. For example:

  ```sh
  science source-coreference --left "$doi_record" --right "$pmid_record" \
    --stance same --grounds "The publisher and PubMed identify the same journal version."
  ```

  The attended session signs the statement. No project selection is required.
  Two exact sources held in the write root can be attested before the first
  epoch, including when a live mount holds an equal copy. The write leaves the
  source records and their citations intact. A pair spanning mounts requires a
  current publication over all configured live corpora. For `no-epoch` or
  coverage/state drift, run `science epoch` and use a fresh invocation. With
  `config-stale`, correct the listed roots/read mounts and reopen before
  publishing. Restore absent carriers or correct the configuration. A captured
  endpoint disagreement calls for rereading the source and checking its address.
  Post-claim refusals replay with the same invocation ID and payload.
- `source-assertion` mints a world `source-assertion` without a project selection,
  anchoring an extracted span (`asserts`, `denies` or `hypothesizes`) from a
  `source` representation (`sha256`, `media_type`, `extent`, NFC `quote` and
  `locator`, `extracted_by`, optional `attributed_to`, single-line `title` and
  optional `body`) onto a `proposition`, with `recorded_by` bound to the session
  actor. Text inputs are never silently NFC-normalised. Before acting, it checks
  all configured live corpora at the derived address: same-source matches
  (including across `source-correct` redirects) refuse with `data.existing`,
  distinct-source collisions refuse with `data.anchor_conflict`, and non-assertion
  occupants refuse with `data.occupied`. Both `source` and `proposition` must
  resolve by kind in the session's live corpora (`data.unresolved`, plus
  `data.unmounted` when `coordination = false`, or `data.wrong_kind`). Source
  assertions are attributed readings and are inert in `belief`.

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
  refusal evidence is retained. Its minted run block renders the result manifest
  (declared output names and SHA-256 digests).
- `run-output` reads one declared output of a `run` record from local operations
  scratch (`--run`, `--output`), confined under `operations_root/scratch` without
  following symlinks. Before rendering, it hashes the file bytes and requires exact
  agreement with the run's result manifest digest. The reply prints the run ref,
  output path, verified digest and byte count ahead of the UTF-8 content, paged
  within its output budget; missing or reclaimed scratch copies, paths outside
  operations scratch, and digest mismatches refuse `read-unavailable`, while unknown
  outputs and non-UTF-8 content refuse `invalid-input`.
- `assess` restores the run's frozen spec and interpretation rule; the caller cannot
  choose a new outcome or target after seeing the result. It persists the exact
  derived target, named estimates, uncertainty and curves, with a full native
  assessment identity address, and its minted assessment block renders the derived
  outcome. The run's observed
  dataset needs empirical standing: an acquired dataset carries it directly, and a
  `derive` package inherits it through a complete, undiverged `lineage-basis`
  chain to an acquired ancestor (the kernel's rule is in beliefs'
  `docs/records.md`); without standing, `assess` refuses. `verify` accepts
  exactly one of `--assessment` (replaying an assessment's run) or `--run`
  (replaying a dataset-production run), resolves the original equivalence
  implementation (`REFERENCE_RULES` or `DATASET_CONTENT_EQUALITY`) before replay,
  uses the original targets, rereads stored run closures, derives scope and mints
  comparison evidence; its reply renders the replayed run's result manifest and
  the verification's scope and verdict. Supplied code/environment must match the captured recipe;
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

### Workflow environments (`derive`, `run`, `verify`)

`derive`, `run` and `verify` accept an optional `workflow_environment` input (64
lowercase hex digits identifying a ready prepared venv under
`<operations_root>/workflow-environments/<key>/`, outside job scratch and the
kernel snapshot cache). Omitting it keeps the executing Science interpreter's
capture and preserves existing canonical digests. Attended CLI invocations also
accept the mutually exclusive CLI-only `--workflow-project <dir>` option, which
runs `uv sync --locked --no-default-groups --no-install-project --no-install-workspace`
against the project's `pyproject.toml` and `uv.lock` with the shared base CPython
interpreter, rejects mutable local directory dependencies and stale locks, reports
`"workflow_environment": "<key>"` in the single stderr JSON metadata line once
preparation succeeds, and forwards only the key to the service. Direct MCP and
socket callers pass `workflow_environment` directly (raw `workflow_project` paths
refuse), and restricted run handles reject both `--workflow-project` (`handle-mode`
before preparation) and `workflow_environment` (`permit-exceeded` at endpoint
admission). `--continue` refuses `--workflow-project`, and retries wanting to
reproduce the original payload directly should pass the reported
`--workflow-environment <key>`.

Prepared environments hold Snakemake 8.11.4 and the workflow's locked runtime
Python dependencies; confined sandboxes still expose no ambient host shell
binaries beyond the confined mount plan, so workflows using `shell:` rules that
depend on host executables can refuse until adapted to Python rules. Retaining
replayability requires keeping both the prepared workflow environment entry and
the verified kernel snapshot under `operations_root` (or restoring an identical
candidate).

## Coordination command contracts

`project` mints a project with a YAML/JSON query, without needing an existing
selection. `question` and `hypothesis` mint views under the current project; `task`
mints an open task with optional dependencies; `decide` records a decision and
its reasoning. Subordinate addresses are scoped by project identity. A query is
parsed and validated before effects; it selects world records, not coordination
records. Publication closure and query graph traversal are separate operations:
a query must explicitly include every required closure record.

`note` records a dated statement in the selected project, with a required name
and non-empty body. Optional repeated `about` values name world records held by
live session corpora, including read mounts and redirects. Every citation is
checked before the first act; unresolved ones refuse `invalid-input` with
`data.unresolved`, and a blank body refuses with `data.field = "body"`. Exact
duplicates are removed while preserving order and the supplied address spelling.
Citing is not believing: acceptance and retraction do not filter citations. Notes
cannot be revised; a correction is a new note naming the old one's pinned address
in its text. A citation may stop resolving if its only holder later leaves the world.

`topic` records a complete background synthesis in the selected project: a name,
non-empty body and YAML/JSON query. The query must have an `addresses` predicate
(`invalid-input`, `data.reason = "no-addresses"` otherwise). Every addresses value
and closure anchor must resolve in live session corpora; all misses appear in
`data.unresolved`. A non-mapping query refuses `invalid-input`; malformed query
language is left to the kernel (`kernel-refused`). A topic is never an empty stub
or a vocabulary referent. Its citations can outlive their holders, as notes can.

`revise` edits topics' name, body and query, taking an unpinned address. The
resulting body must remain non-empty; query references are checked only when a
new query is supplied. A rename carries the query without rechecking references
that may have stopped resolving.

`reuse` copies a question/hypothesis query into the selected project as one new
mint, preserving a pinned source pointer in prose; it does not bridge address
spaces. `revise` writes a whole new revision naming its predecessors, carries over
unchanged fields from one tip, and rejects fields not owned by that kind. Divergent
tips require explicit `repair`, which supplies every field even if only one tip
currently stands. `clear_depends` conflicts with explicit `depends`. Project
selection reports its resolved pinned revision; later reads resolve the current
tip rather than silently reselecting an obsolete revision.

## Run handles and chain evidence

A supervisor gives an actor `VERIFIABLY_ENDPOINT` and `VERIFIABLY_TOKEN_FILE`.
With both set, the CLI sends each declared command, including reads and
continuations, to that endpoint. Supply the same invocation ID, project and
cursor you would use for an attended call. The token file is private.
Either path missing or empty, or a handle combined with `--config` or
`SCIENCE_CONFIG`, returns `handle-incomplete`. Framework commands return
`handle-mode`, apart from help, version and `science mcp bridge`. The bridge
serves the same MCP discovery and tool-call protocol over stdio and forwards
calls through the handle. The supervisor owns the session and its selection.

`science heads` prints a `heads.v1` JSON object with the configured world's
genesis, head and pending registrations, and each mounted corpus or store's
identity, root, genesis, tip and pending registrations. The default read
preserves pending transactions. An operator can request recovery with
`--resolve`. An actor cannot request recovery.

`science log --chain <corpus-id-or-store> --after <digest> --through <digest>`
prints a `log.v1` JSON Lines header followed by entries after the first
digest up to and including the last. Equal bounds produce only a header.
Use the same explicit end digest on every page. Rejoin the output fragments
after stripping the continuation trailer. Discard partial output on
`stale-cursor`. An unknown chain, unknown tip, or unavailable evidence gives
a structured refusal.

## Static acquisitions

Run `science acquire start --plan FILE` with Quarry's acquisition JSON or a
static seed plan. Use `-` for standard input. Start validates the plan and
prints the set token before contacting its first HTTPS host. The six settings
in [configuration](configuration.md#acquisition-limits) have dashed creation
flags such as `--max-total-bytes`. A completed retrieval is ready for explicit
acceptance.

`science acquire status --set TOKEN` reports counts and logical bytes.
`science acquire resume --set TOKEN` rechecks previously fetched bytes and gives
each failed request one new budget, including requests whose last attempt met a
deterministic redirect refusal. One downloader may run per operations root.
Start and resume refuse immediately if either the root lock or the set lock is busy.
Within one downloader, redirects obey per-host pacing and retry deadlines.

Use `science acquire seal --set TOKEN` through the attended service. Add
`--accept-partial` to accept verified members alongside recorded failures and
abandon the remaining pending requests. At least one member must be held. A
finished set's status includes its dataset address and acquisition report.
To accept an external program's converted log, use `science acquire import
--log FILE --members DIR --journals DIR --title TITLE --locator LOCATOR`.
Member files and the original journals must match the canonical log.
The service records the original fetching instrument. The log and all declared
original journals together may occupy up to 64 MiB by default. Configure
`[acquire].max_import_evidence_bytes` to change that limit. A fresh import
over the limit is refused before the set is published. Recovery of a committed
report uses its binding without recopying original journals.

`science dataset --tree --path DIR --title TITLE` holds a local directory as a
single resource named `data`. A declared tree can also be held using
`science fetch --dataset REF --source DIR` with an absolute directory and the
fetch policy enabled. Runs and derivations stage trees under the declared
resource name and verify each member against its stored digest.
