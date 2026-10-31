# `recheck`: settle an unmatched holdings intent — design

Status: proposed; requires human review before implementation planning.
Task: sci-409235.

## Intent and evidence

A holdings write appends its intent to the write corpus before it touches the
store. When the store then refuses (observed: a read-only-serviceable store
root), no observation follows, and the kernel's holdings reducer
(`rules_v1/holdings.py::_unsettled`) blocks that location as `unsettled`. A
blocked location for a declared digest blocks the whole dataset, even beside a
healthy copy of the same bytes (`docs/stores.md`, step 4). The block clears only
when a later `re-check` intent at the same location, in the same corpus chain,
is matched by its observation. The block shows in the holdings reduction's
blocked list; it reaches a dataset's answer only when the location also has an
observation matching a declared digest (`beliefs/holdings/adapter.py`). Beliefs supplies that operation; no science
command reaches it, so today the block can only be cleared by writing around
science.

Whose ask: the user authorized filing this task in session
`claude-code:a2943a1d-dd3d-4577-a43b-8347da7f11bf` after an agent proposed "a
re-check command" as one of three science follow-ups to the mm-62e2da incident.
The 2026-10-30 scope pass (codex) narrowed it to a reviewed command contract.
Every design choice below is the author's recommendation, not prior human
approval.

Instance: the mm30 world's working corpus holds chain entry
`553be3ce…` (event token `956c6da0…`) for
`store:05b6c1225e710bb1559f36e8333f3f29:2061b373…/mask-key.json`, left by
invocation `6cf80d36…` on 2026-10-30. Settling it is a live world write owned by
mm-62e2da under separate authorization; this task ships the command and does not
run it against mm30.

Tree inspection on 2026-10-31 (science `ee509ca`, beliefs `d135eb3`; the beliefs
holdings and session modules are unchanged since the scoped `405f249`):

- `ScopedWriter.recheck(locations, *, instrument, standing)`
  (`beliefs/session/writer.py`) wraps `holdings/recheck.py::recheck_locations`
  with this invocation's ledgered holdings seam, ledgered operation port and
  closing hold. Before any effect it requires `holdings` for
  `holdings-observation` and `corpus-write` for `act-report`, checks observer and
  instrument text, the writer/observer root agreement, the bound port, and that
  every location names the bound store. It then appends one `re-check` operation
  intent, runs `boundary.recheck` per location (its own holdings intent, a read,
  then a published `Found`/`Absent` observation or an `InconclusiveAttempt` that
  publishes nothing), and closes with one `act-report` carrying one locator entry
  per location.
- `writer.holdings_context()` binds `session.corpus_root` (the configured
  `write_root`) and `session.store_root` (the configured `store_root`). `dataset`
  and `fetch` both append their write intents through it, so their unmatched
  intents live in the write corpus, and a re-check through the same route lands
  in the same chain.
- The session binds exactly one store. `read_store_roots` (sci-300dab, landed)
  serve science's reads only; the kernel session never sees them, and
  `recheck_locations` refuses a location whose store id is not the bound
  store's.
- mm30's active config (sci-e5d803's inventory, 2026-10-30) still binds store
  `05b6c…` as `store_root`, read-only-serviceable. The relocation runbook
  (`docs/stores.md`) moves that store to `read_store_roots` behind a fresh
  writable store.
- The dispatcher renders a write's report from the ledger's minted identities
  (`dispatch.py::_minted_report`), each through `report.record_block(node)`,
  which shows kind, id, uid and title. A holdings observation's title is
  `Holdings observation <12 hex>` and an act-report's is `re-check report`:
  neither says Found, Absent or inconclusive.

## Goals

1. One science command re-checks one requested store location through
   `ScopedWriter.recheck` and publishes the kernel's result in the write corpus,
   settling an unmatched mutating intent at that location.
2. Its report states the kernel's actual result: Found with its digest, Absent,
   or inconclusive with the kernel's reason.
3. It refuses before any effect on malformed, URL, unconfigured or unbound
   locators and on an insufficient permit.
4. It works against a read-only-serviceable `store_root`: a re-check only reads
   the store.

## Non-goals

- Bulk recovery, retries, scanning for blocked locations, or automatic
  re-checks after a refused write.
- URL locations (the kernel's URL look is a different operation).
- Re-checking a store bound only as a read store without a configuration change
  (see Approaches).
- Closing sci-eccb43's original invocation, clearing the pilot retry guard, or
  running the mm30 repair (mm-62e2da).
- Store lifecycle changes of any kind.

## Anti-goals

- A second recovery protocol around `boundary.recheck`, or any reach into
  beliefs' private members (`ScopedWriter._writer`, the session's seams).
- Labelling the command read-only: it reads the store but writes governed
  corpus and ledger evidence.
- Assuming the incident's expected Absent: the report carries whatever the
  kernel observed.
- Recovery side effects folded into `dataset` or `verify` (`verify` already
  means assessment replay).

## Approaches

The open question is which store a re-check may read.

1. **Bound store only, with a recovery configuration for read stores
   (recommended).** The command re-checks locations in the session's bound
   `store_root` only. A location in a configured read store refuses with the
   route: open a session whose `store_root` is that read store, with the same
   `write_root` and the former write store moved to `read_store_roots`. The
   re-check never writes the store, so binding a read-only-serviceable store is
   valid (mm30 runs that way today). Science-only, uses the public session route
   unchanged, and covers mm30 now, before relocation, with no extra step.
2. **Session-level read stores in beliefs.** Teach the attended session about
   read stores and let `ScopedWriter.recheck` pick the root by the locator's
   store id. Cleanest for the operator, but it is new kernel surface (session
   open, the ledgered seam's store binding, the act context) in another
   project, with its own design and review, and it gates this task on that
   work. Worth filing if read-store re-checks become routine; one incident
   does not justify it now.
3. **Science builds its own act context for a read store.** Rejected: it needs
   `ScopedWriter._writer` and the session's private seams, which the anti-goals
   exclude.

Recommendation: approach 1. It is the author's call, made under the
decision-rule default; the reviewer can redirect to approach 2.

## Design

### Command surface

- Name `recheck` (kernel term `re-check`; science names carry no verb field,
  and the grammar of framework §3.1 admits it). Module
  `science.commands.recheck`, directory `commands/recheck/`.
- One required input, `--location`: the canonical store locator spelling
  `store:<32 lowercase hex>:<store-relative path>`, exactly what
  `StoreLocator.canonical()` produces and what a blocked reduction row and the
  incident report name. Not repeatable.
- Declaration:

  ```toml
  schema_version = 1
  name = "recheck"
  purpose = "Re-check one store location and record what the store holds there, settling an unmatched holdings intent."
  write_class = "mints:holdings-observation,act-report"
  output_budget = 2048

  [write.routes]
  holdings-observation = "holdings"
  act-report = "corpus-write"

  [inputs.location]
  type = "string"
  required = true
  doc = "A store locator, store:<store id>:<relative path>, in this session's store_root."

  [reads]
  families = ["corpus-stored", "holdings"]
  ```

  `act-report` must be mapped because `KIND_ACTS` admits it through both
  `corpus-write` and `run` (framework §3.3); `recheck_locations` requires
  `corpus-write`. The compiled requirement is then exactly the two families the
  kernel route checks.
- The CLI row in `tools/cli.toml` follows the other science write commands
  (`--config`, `--invocation-id`, `--continue`, plus `--location` required).
  `tools/cli.toml` is vendored from ops, and `bin/vendored adopt` copies only
  commits already on ops' default branch. The plan's first step therefore adds
  the row in an ops worktree and integrates it into ops `main` (a local merge
  in a repository the user maintains, no push); then science adopts the file
  and commits it with the implementation. The adopt also brings other tools'
  rows that landed in ops since science last adopted; science's own section is
  unchanged by them.

### Handler

`handle(ctx, writer, *, location) -> Report`, validating before the first act:

1. Parse `location`. Split on the first two `:`; the first field must be
   `store`, else refuse `invalid-input` (a `url:` locator names the URL look, out
   of scope). Construct `StoreLocator(store_id, relative_path)`; a
   `MalformedRecord` (bad identity, unsafe or escaping relative path) refuses
   `invalid-input` with the kernel's message.
2. Bind the store. Compare the locator's store id with `writer.store_id`.
   Unequal: if `configured_stores(ctx.config)` maps the id to a read store,
   refuse `invalid-input` naming that root and the recovery-configuration route;
   otherwise refuse `invalid-input` naming the configured identities.
3. Standing observations: every `holdings-observation` record at this canonical
   location in every view of `ctx.read_views()` (the write corpus and every
   mount), as `HoldingsObservation` values, deduplicated by identity. The new
   observation supersedes them all, so an inherited head in a read corpus does
   not stay beside it and turn the location `contested`. The record layer
   admits cross-corpus supersession (supersedes are canonical references,
   checked only for location agreement). This differs on purpose from
   `dataset` and `fetch`, which take standing from the write view alone; that
   difference is noted here and not changed by this task.
4. `writer.recheck((locator,), instrument="science/recheck.v1", standing=...)`.
   The kernel's checks (`RecheckRefused` is a `WriteRefused`; `PermitExceeded`)
   run before any intent and reach the dispatcher's existing
   `KERNEL_REFUSALS` mapping, closing the invocation refused with no act.
   Two kernel errors can arise after the intent: `RecheckRefused` at the close
   (a report naming an observation no act published) and `StoreIdMismatch`
   inside `boundary.recheck` (the store's genesis changed between the
   pre-check and the read). The handler's own store binding and the kernel's
   pre-intent check make both practically unreachable. The dispatcher's
   `KERNEL_REFUSALS` path closes refused without consulting recorded acts, so
   a late `RecheckRefused` would close refused beside committed acts. That is
   the dispatcher's existing behaviour for every write command (sci-eccb43
   chose it for `StoreWriteRefused`); this task records it and does not change
   it.
5. Return record blocks for what was minted: the published observation, if
   any, and the act-report. An inconclusive read publishes no observation;
   the invocation still closes `done` with the act-report, and the location
   stays blocked. That is the kernel's honest result, not a refusal.

Errors after the operation intent other than kernel refusals (an I/O fault
the seam does not turn into an inconclusive view) propagate under the
dispatcher's existing contract; this task does not widen it.

### Report: show the kernel's result

Amend `report.record_block(node)` so that a block for these two kinds carries
a detail line derived from the record itself:

- `holdings-observation`: `found <digest> at <location>` or
  `absent at <location>`.
- `act-report` whose operation is `re-check`: one line per entry,
  `<locator>: observed <ref>` or
  `<locator>: <byte-locator-untested|retrieval-failed> <reason>`. Act-reports
  of other operations (`run`, `verify`, `publish`) keep today's block
  unchanged (author's call: their entry shapes differ and no acceptance asks
  for them).

The stored entry keeps only the kernel's reason code (for example
`lifecycle-state`), not the attempt's detail string, which
`recheck_locations` drops when it builds the entry. The report therefore names
the reason code and no more; carrying the detail would be a kernel change and
is not needed to tell the three results apart (author's call).

The detail is derived by the renderer from the stored record on first response,
replay and continuation alike, exactly as the title is; no handler authors it,
so the write-audit rule (framework §7.4) keeps its purpose. Amend §7.4 with a
dated note recording this. The change also adds the detail to `dataset` and
`fetch` reports, which mint holdings observations; their fixtures change
accordingly; `run`, `verify` and `publish` reports
are unchanged. Without it the person cannot tell Found from Absent from the
report, and the task's acceptance requires that.

### Which corpus settles

The re-check lands in the session's `write_root`. It settles an intent only if
that intent is in the same corpus chain, which holds when the configuration's
`write_root` is the one the failed write used. The command does not check for
a blocked location before acting: a re-check is a valid observation at any
location, and refusing on reduction state would add a precondition the kernel
does not have. The prompt and the runbook state the same-corpus requirement.

### Documentation

- `commands/recheck/prompt.md`: when to use it (a location blocked
  `unsettled` after a refused or interrupted holdings write), the locator
  spelling, the same-`write_root` requirement, that a live world write needs
  the person's authorization, and how to read the three results.
- `docs/stores.md`: replace step 4's "sci-409235 owns any unsettled-intent
  work" with a short procedure: re-check before relocating when the blocked
  location is in the current `store_root`; after relocation, use the recovery
  configuration (read store as `store_root`, same `write_root`, writable store
  in `read_store_roots`), stop any running `science serve` first, re-check,
  then restore the working configuration.
- `docs/specs/2026-08-31-command-framework-design.md`: the §7.4 amendment
  above.
- Generated adapters and any command listing the build or `just docs`
  regenerates.

## Verification

Focused tests through `just test-one`, under the checkout's validated test
policy for gates. No live repair is an acceptance test.

- Settlement: a synthetic unmatched write (a `dataset` invocation whose store
  write is refused because `store_root` is a read-only-serviceable replica, as
  in the incident) blocks its location `unsettled`; `recheck` at that location
  publishes Absent and the reduction's blocked list no longer holds it; a second, separately
  held location is unaffected throughout.
- Found: a re-check at a held location publishes Found with the stored digest
  and supersedes the standing observation.
- Inherited standing: a head at the location in a mounted read corpus is
  superseded, and the location is not `contested` afterwards.
- Inconclusive: an unestablished or not-attempted read (seam injection)
  publishes no observation, mints the act-report with the kernel's reason, and
  leaves the location blocked.
- Refusals before effect, each with no ledger act and no chain entry:
  malformed locator, `url:` locator, unconfigured store id, configured read
  store id (message names the recovery route), and an insufficient permit at
  declaration time (a session whose permit lacks `holdings` or `corpus-write`).
  Through the dispatcher the scoped authority equals the compiled declaration,
  which is exactly what the kernel checks, so the act-time permit check is
  beliefs' own test, not this task's.
- Recovery configuration: a location in a read store refuses under the
  working configuration and settles under the recovery configuration sharing
  the same `write_root` and operations root; the working configuration then
  reads it unblocked.
- Report and replay: the rendered report shows the detail line for each
  result; a replay by `--invocation-id` renders the same report from the
  ledger; continuation keeps the detail.
- Conformance: `test_cli_surface`/`test_contracts` see the new row and
  declaration; adapters regenerate.

## Left to the builder

Checked by the builder review: the act-report's identity reaches
`invocation_acts` through `LedgeredPort.execute_fulfilling`, so the
dispatcher's canonical report includes it.

- Fixture construction (the existing relocated-store and replicated-store
  helpers in `test_stores.py` and `helpers/world.py` are the starting point).
- Exact detail-line wording, within the content listed above.
- Where the locator parse lives (handler or `science.holdings`).
