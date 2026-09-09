# Session findings at endpoint startup — design

**Date:** 2026-09-09
**Status:** designed; not yet implemented. Task `sci-296b6d`.
**Scope:** the one missing piece of the command framework's crash story:
making the reconciliation findings that `beliefs` computes on every session
open reach the person who started the endpoint. It covers both endpoints,
`science serve` and `science mcp serve`, and nothing else. It adds no new
classification, changes no exit code, and blocks nothing. The `status`
command's separate discarding of corpus findings is out of scope and filed
as its own task (§7).

**Inherits:** the command framework design
(`docs/specs/2026-08-31-command-framework-design.md`) §5.3 (the crash window),
§6.2 (session-scoped deduplication and the finding that "tells them to look"),
§9.2 (the CLI's stderr convention) and §9.3 (the MCP server's stdio contract).
The finding vocabulary is the writer-session design's §6 in `beliefs`
(`beliefs.session.reconcile`). Terms used without definition — session,
ledger, invocation, act line, operations root — are those documents'.

## 1. Problem

The framework's crash contract rests on one sentence of §5.3: an act can
commit and the process die before its `act` line lands, and the uncovered
chain entry is then "surfaced as an audit finding naming the invocation and
the entry". §6.2 leans on it again: a retry against a new session is not
deduplicated, and "the `outcome-unknown` finding of §5.3 is what tells them
to look" at the crashed session's ledger.

`beliefs` does its half. `open_attended_session` writes the session-open
line and then sets `session.findings` to the result of `reconcile_sessions`
over the operations root, excluding the session it just opened. That tuple
holds every finding the writer-session design's §6 defines: `session-unclosed`,
`session-outcome-unknown`, `session-entry-foreign`, `ledger-torn-tail`, the
ledger-shape findings, and the chain-shape findings.

`science` does not do its half. Nothing in the package reads
`session.findings`. Both endpoints open the session and discard the tuple.
The mechanism the spec relies on to tell an operator to look does not exist.
Tasks 12 and 13 of the implementation plan did not skip it; the plan never
had a step for it.

## 2. Decisions

Rulings from the 2026-09-09 design session, recorded so they are not
re-derived.

1. **Reporting, not blocking.** §5.3 draws the line itself: under
   sub-project 6's closing check the same state quarantines the run;
   "interactively it is a finding for the person." Startup proceeds with
   findings present. No exit code changes. Quarantine is sub-project 6's.
2. **Stderr, at startup, both endpoints, one shape.** Stdout is spoken for
   on the MCP server (JSON-RPC) and unused on the socket service; stderr is
   where MCP servers conventionally log and where the CLI already puts its
   one machine-readable line per invocation (§9.2). The endpoint modules
   write nothing to stderr themselves, but the process does: `cli.main`'s
   last-resort handlers emit a `{"refusal":…}` or `{"error":…}` line there
   when `science serve` or `science mcp serve` fails, including a failure
   after the session has opened. Findings therefore share the stream with
   those lines and must be distinguishable from them (§4).
3. **One compact, key-sorted JSON object per finding**, newline-terminated,
   encoded exactly as the CLI's §9.2 line is (`sort_keys=True`,
   `separators=(",", ":")`). Silent when there are no findings: zero bytes,
   not an empty array and not a "no findings" line.
4. **The finding's own five fields travel under their own names**, so the
   line round-trips to `beliefs.corpus.Finding` without translation, plus
   one key naming the session that did the reporting. §4 gives the shape.
5. **One module, two call sites.** `science/findings.py` owns the emission.
   `serve.py` importing from `mcp.py`, or the reverse, would be a false
   dependency; the MCP server has nothing to do with the socket service.
   Neither imports the CLI module, which imports everything.
6. **The stream is a parameter.** Both `serve` functions take `stderr`,
   defaulting to the process stream, mirroring the MCP server's existing
   `stdin`/`stdout` injection. Tests pass an in-memory buffer.
7. **The honest limit is written down in the code.** Reconciliation is an
   open-time audit. A long-lived endpoint reports once, at startup, and
   never notices a peer that crashes while it runs. §5.3 frames it exactly
   that way — reconciliation runs "when a later endpoint opens over the same
   operations root, and by the audit surface" — so this layer neither polls
   nor pretends to.
8. **An unclosed session is not a crashed one, and the line never says it
   is.** Reconciliation classifies ledger evidence. `session-unclosed` means
   a ledger with no session-close line; it checks nothing about whether the
   process that owns the ledger is alive. Starting `science mcp serve` while
   a healthy `science serve` holds the same operations root reports that
   service as `session-unclosed`, and the reverse. The finding is a pointer
   to a ledger worth reading, not proof of a crash. This document, the
   module docstring and the §7 amendment all use "the referenced session",
   never "the crashed session", and the amendment states the limitation so
   an operator does not read a live peer as a casualty.

## 3. The module

```python
# science/findings.py
def report_findings(findings, *, reported_by: str, stream) -> None
```

- `findings` is the tuple `open_attended_session` left on the session:
  `beliefs.corpus.Finding` values. This is *not* `science.report.Finding`,
  the renderer's one-field text block; the two share a name and nothing
  else, and the module's docstring says so.
- `reported_by` is the opening session's 32-hex id: the session doing the
  reporting. The referenced session's id arrives inside the finding as its
  `ref` (for ledger-level findings) or in its `detail` (for chain-level
  ones). The key name exists so a reader never confuses the two. Nothing
  about the referenced session's liveness is known or implied (§2 item 8).
- `stream` is a text stream with `write`. The function writes one line per
  finding, in the order `reconcile_sessions` returned them (that order is
  already deterministic: corpus id, then position, then code, then ref),
  and flushes once at the end when the stream has `flush`. It returns
  nothing.
- It does not catch anything. A closed or unwritable stderr raises out of
  `report_findings`, and each call site's existing `try` closes the session
  before the exception propagates (§5). Swallowing the error would turn the
  one channel this layer has into a silent one.
- It owns its three-line JSON encoder. The CLI module has an identical
  private helper for invocation lines; that is two wires sharing a
  convention, not one helper wanting a home. Neither imports the other.

## 4. The line

```json
{"code":"session-unclosed","detail":"open_invocations=['a1b2…']","message":"a ledger with no session-close","ref":"<referenced session id>","reported_by":"<opening session id>","severity":"warning"}
```

Six keys, always all six, in sorted order:

| key | value |
|---|---|
| `severity` | the finding's `severity` (`warning` or `error`) |
| `code` | the finding's `code`, from the writer-session design's §6 vocabulary |
| `ref` | the finding's `ref`: a session id, a corpus id, or an entry digest, by code |
| `detail` | the finding's `detail`, verbatim; may be empty |
| `message` | the finding's `message`, verbatim; human-facing, normative for nothing |
| `reported_by` | the opening session's id, 32 lowercase hex |

No wrapper key, no added discriminator, no timestamp. The stream already
carries two other shapes, both from `cli.main` (§9.2 of the governing
design): `{"refusal":{…}}` and `{"error":{…}}`, each optionally with
`invocation_id`. The existing top-level keys tell the three apart, and that
rule is the documented discrimination:

| top-level key present | the line is |
|---|---|
| `severity` | a reconciliation finding (this document) |
| `refusal` | a §6.3 refusal envelope from the CLI |
| `error` | the CLI's generic internal-error shape |

Exactly one of the three is present on any line. The refusal envelope also
carries a `code`, but nested under `refusal`, so a reader keys on `severity`,
not `code`. A sequence such as two finding lines followed by an `error` line
is a legal stream: the endpoint opened its session, reported, and then
failed before serving. The §7 amendment records this table.

## 5. The two call sites

Both endpoints already have the shape this needs: open the session, then
enter a `try` whose failure path closes it.

**`science.serve.serve(config, socket_path, declarations=None, handlers=None, stderr=None)`.**
After `open_attended_session` returns and inside the existing `try`, before
the dispatcher is built:

```python
report_findings(session.findings, reported_by=session.session_id,
                stream=sys.stderr if stderr is None else stderr)
```

The service's `except BaseException` already closes the session and
re-raises, so a failed write leaves no open ledger behind.

**`science.mcp.serve(config_path, stdin=None, stdout=None, stderr=None)`.**
Same call, inside the existing `try`, before the read loop. The `finally`
already writes the session-close line on any exit.

The CLI's `_framework_verb` passes nothing new; both defaults are the
process stream. `science serve` and `science mcp serve` gain no options.

## 6. Testing

One new test file, `python/tests/test_findings.py`, plus one test in each
endpoint's existing file. All use the fixture world helpers that already
exist.

Parsed JSON proves the keys and values and nothing else. Compactness, key
order, the trailing newline, line order and flushing are all invisible to
`json.loads`, so the wire tests compare bytes.

**Unit, the exact wire.** Build two `beliefs.corpus.Finding` values by hand
with distinct codes, one with an empty `detail`, and pass them in a chosen
order to `report_findings` with a recording stream: a `StringIO` subclass
that appends to a log on every `write` and `flush`. Assert the stream's
value equals the exact expected string, two lines, each compact with sorted
keys and terminated by `\n`, in the order given. Assert the log shows both
writes before a single `flush`, and that `flush` was called exactly once.
Assert an empty tuple writes nothing and flushes nothing. Assert a stream
without a `flush` attribute is accepted. This pins the wire independent of
`beliefs` producing a finding.

**Socket service, an unclosed peer.** Open an attended session over the
fixture world's config and operations root the way the endpoints do, claim
an invocation on it with a non-empty command and a 64-hex input digest, and
do not close it: that is an unclosed session as the ledger sees it, and it
is exactly what a live peer looks like (§2 item 8). Then call `serve` over
the same config with a `StringIO` for `stderr`. Assert exactly one line; that
it parses with `code` equal to `session-unclosed`, `ref` equal to the
fabricated session's id, a `detail` naming the claimed invocation id, and a
`reported_by` that is a 32-hex id other than the fabricated one. The byte
shape is the unit test's job. Close the returned server so the test's own
session-close line lands.

**Socket service, a clean root.** Same call over a fresh operations root.
Assert `stderr` holds zero bytes.

**Socket service, a failing stream.** Over the unclosed-peer state, pass a
stream whose `write` raises `OSError`. Assert the error propagates out of
`serve`, that no socket was bound at the given path, and that the ledger of
the session `serve` opened — the one session directory under the operations
root that is not the fabricated peer's — ends with a session-close line.
This is the delivery guarantee of §3: a dead stderr is reported, not
swallowed, and it leaves no open ledger.

**MCP server, all three cases.** The same three tests through
`science.mcp.serve` with `stdin=io.BytesIO()` (immediate EOF),
`stdout=io.StringIO()` and the respective `stderr`. In the failing-stream
case assert additionally that `stdout` holds zero bytes: nothing reached the
JSON-RPC channel.

**What these prove, stated in the test docstrings.** The fabricated state
yields `session-unclosed`, not the spec's headline `session-outcome-unknown`,
which needs a committed chain entry under a session actor that no act line
covers. The surface is agnostic to the code: it prints whatever
`reconcile_sessions` returns. The classification itself is `beliefs`'
contract and is tested there. A test here that manufactured a committed
entry would be re-testing the kernel through the wrong door.

## 7. Documentation and follow-ups

**The governing design.** §9.2 and §9.3 of the command framework design
each gain a short paragraph, marked as a 2026-09-09 amendment in the same
style as the §5.1 and §9.1 amendments: the endpoint writes one compact,
key-sorted JSON line per session-reconciliation finding to stderr at startup
and nothing when there are none; a line with a top-level `severity` key is a
finding, one with `refusal` or `error` is the CLI's (the §4 table); and
`session-unclosed` names a ledger without a close line, which a live peer
over the same operations root also produces (§2 item 8). This document's
status line changes to
"implemented" in the implementing commit, per the repository's rule that
the merge is the moment a status goes stale.

**Filed separately, not done here.** The `status` command calls
`world.status(corpus_id)` and renders `known`, `live` and `present`,
discarding the `findings` tuple the `CorpusStatus` value carries. Different
source, different surface, same smell. It is its own task
(`sci-097534`) and widens nothing here.

## 8. Alternatives rejected

- **A `Finding` block on the first response.** Unrepresentable for writes:
  `audit_write_report` raises `AuditViolation` on any block that is not a
  `RecordBlock` (§7.4), so a finding cannot ride a write response at all.
  "First response" is also arbitrary on a service handling independent
  requests from several clients, and it ties an operator-facing fact to
  whichever caller happens to arrive first.
- **Refusing to start when findings are present.** That is quarantine, and
  §5.3 assigns it to sub-project 6's closing check. Interactively the person
  is in the loop; blocking them from the corpus because another session's
  ledger has no close line — which a live peer also produces (§2 item 8) —
  is the wrong side of the line the spec drew.
- **Python's `logging`.** An unconfigured logger is silent below `WARNING`
  and formats as prose; configuring one adds a second convention next to
  the CLI's JSON line for no reader that exists. Error-severity findings
  would also need a level mapping nobody asked for.
- **A human-readable text line.** The CLI's stderr is machine-readable by
  design (§9.2). A harness wrapping `science mcp serve` can parse a JSON
  line and cannot parse prose. The `message` field is the prose.
- **Re-running reconciliation per request, or on a timer.** Reconciliation
  takes the operation lock of every corpus root and reads every ledger. It
  is an audit, not a heartbeat, and §5.3 scopes it to endpoint open and the
  audit surface. Polling would also surface the same finding repeatedly
  with nothing new to say.
- **A shared JSON-line helper module for the CLI and the findings module.**
  Three lines in two places beats a module whose only job is to hold three
  lines, and it keeps the CLI's wire and the endpoints' wire free to
  diverge if one ever needs to.

## 9. Task mapping

One task, `sci-296b6d`, size `s`, one commit: the module, two call-site
edits with their `stderr` parameters, the tests of §6, the two-sentence
amendment of §7, and `tasks done`. No implementation plan document; the
change is bounded and this spec is its whole design. Implementation follows
test-driven development directly from §6.
