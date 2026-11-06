# Sessions and invocation

Type: protocol; document types 1. Participants are the caller, CLI/MCP launcher,
science dispatcher, kernel attended session, scoped writer and append-only ledger.
The Unix service protocol is unversioned; MCP advertises `2026-07-28`; JSON-RPC is
`2.0`; ledger files are `ledger.v1`; command schema 1 and `scur1` cursors have their
own versions. There is no umbrella science wire version.

## Open, invoke and close

1. Resolve an explicit [configuration](configuration.md). Validate configured
   stores and writer manifest pins before opening the attended session. Resolve
   the launcher's initial project selection before session creation.
2. Open one kernel session with the configured write root/profile and all read
   mounts under their own pinned profiles. The kernel binds actor and permit
   ceiling, records session-open and reconciles older session evidence.
3. Build a dispatcher with production declarations, resolved handlers and a read
   context. Corpus writes, selection and sharing calls require this live session;
   a sessionless read gets no write authority.
4. Validate command/protocol fields and canonicalize declared inputs. Read calls
   evaluate directly. Writes serialize through the dispatcher lock, claim an
   invocation id and digest, scope the kernel requirement, invoke, audit the
   resulting evidence/report and close the invocation with its outcome.
5. Close the session after all calls have drained. A failed ledger append makes
   the session terminal. Do not keep writing after a terminal failure.

`science.session.open_session` is the library launcher; callers must close it
in `finally`. The [guide](guide.md) demonstrates `Dispatcher.invoke`. Scientific
writes produce governed corpus records. Selection and sharing produce ledger
lines instead. The ledger lives at `operations_root/sessions/<session-id>/ledger.v1`;
it is not an editable application cache. See the kernel's
[write protocol](https://github.com/verifiably/beliefs/blob/main/docs/writes.md#writer-sessions).

## Replay, partial effects and paging

Claiming a new write id runs it. A completed matching id replays its recorded
outcome without invoking the handler. An id with different command/inputs refuses
`input-mismatch`; an invocation still open refuses `outcome-unknown`. IDs are
session-scoped, so retry in that same session. A fresh id after an uncertain write
can duplicate intent: inspect the ledger and governed records first.

Validate before the first act. A surface refusal before any act closes refused.
If a handler refuses after committing acts, those acts remain true: the dispatcher
closes done with their records and reports a handler-contract defect. Kernel
boundary refusals preserve their evidence, including any refusal act-report; a
refusal does not erase earlier successful acts. There is no automatic retry or
rollback of already committed scientific evidence.

Continuation is a dispatcher operation. Reads are recomputed and their report
hash must agree; writes rebuild only their saved outcome. Page positions are
validated against the serialized report. Do not replay a scientific command to
obtain a missing page. See [cursor fields](commands.md#paging-and-cursor-format).
Historical sharing commentary is retained separately as described in
[sharing](sharing.md#registry-and-replay).

## Project selection

A project is a coordination view, not a corpus. The launcher chooses an explicit
`--project` ahead of `default_project`, or no selection. `project-select` records
one pinned selection or clears it. Endpoint state holds the current unpinned
project address; the ledger records the revision resolved at selection time.
Writes bind to this session selection and reject a per-call `project` override.
Subordinate coordination mints require a current project.

A read command with `selects = true` accepts an invocation-only `project` name or
address; it does not change the endpoint. Names resolve exactly against standing
project tips; ambiguity, absence and divergence refuse with structured tips.
Without an override a CLI read first asks the live service's selection, then uses
its configured default if no service exists. An existing but unreadable/unresponsive
service is an error, never permission to substitute the default. Selection
queries create no invocation or ledger line. `next` evaluates project queries
live and refuses incomplete/unmounted record access rather than dropping rows.

## Unix service and CLI

`science serve --config <file>` binds one Unix socket and owns an attended session.
The MCP launcher also exposes this service, so CLI writes and MCP calls for that
world share one session. A pre-existing socket refuses before session creation;
remove a stale socket only after establishing its owner is gone. Paths over 107
UTF-8 bytes refuse explicitly. Closing removes only the socket inode the service
created, preserving a file someone else put there.

Requests/replies are newline-delimited JSON. Invocation request keys are exactly
`command`, `inputs`, `invocation_id`, `cursor`, `project`. Command is a string;
inputs is an object or null/omitted (empty mapping); the remaining fields are
strings or null/omitted. Unknown keys and malformed shapes refuse. Success is
`{ok:true, text, invocation_id}`; failure is `{ok:false, refusal}` with an
invocation id when available. `{query:"selection"}` returns `{project:address-or-null}`.
This socket is a local attended authority boundary, not a network authentication
service. Callers sharing access to it share that session's capability ceiling.

CLI declared input names become hyphenated flags. List inputs repeat according to
CLI help; booleans use the generated boolean flags. Reads execute without opening
a writer session; writes and write cursors route to the configured service. The
CLI prints report text on stdout and invocation/refusal metadata on stderr.
Exit 0 means success; refusal uses exit 3. `build` validates declarations without
opening a world; `adapters build` generates harness artifacts without one.

## MCP stdio

`science mcp serve --config <file>` reads newline-delimited JSON-RPC requests.
This implementation uses `server/discover`; `initialize` is unsupported and returns
`-32601`. Each request with an id is independent and carries `params._meta` with
required `io.modelcontextprotocol/protocolVersion` (`2026-07-28`) and
`io.modelcontextprotocol/clientCapabilities` (an object, `{}` is valid). For example:

```json
{"jsonrpc":"2.0","id":1,"method":"server/discover","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}}}}
```

Repeat that metadata on `tools/list` and `tools/call`; discovery does not establish
a protocol session or supply metadata for later requests. Optional
`io.modelcontextprotocol/clientInfo` is validated as an Implementation: string
`name` and `version`, optional string `title`/`description`, URI `websiteUrl`, and
validated `icons`. Known capability fields are shape-checked when present: `roots`
is an object; `sampling` and `elicitation` contain object-shaped known features;
`experimental`/`extensions` map to objects, with namespaced extension keys.

`server/discover` takes only `_meta` and returns `supportedVersions`, `capabilities`
(`tools:{}`), `_meta["io.modelcontextprotocol/serverInfo"]`, `ttlMs:300000` and
`cacheScope:"public"`. `tools/list` returns declaration-derived schemas with the
same cache fields and no `nextCursor`; every supplied listing cursor refuses.
Result trees are fresh allocations; callers cannot mutate later results. The
launcher-owned attended writer session is process state shared by these independent
requests, distinct from protocol request state.

`tools/call` takes `_meta`, `name`, and optional object `arguments`. Schemas forbid
unknown tool arguments and add optional `invocation_id` and `cursor`, plus `project`
only on selecting reads. A cursor continues that command's report rather than
invoking a separate tool. Optional `inputResponses` (object) and `requestState`
(string) are type-checked but then refused as unsolicited multi-round state:
science never returns `input_required`. Every successful RPC result has
`resultType:"complete"`; tool results contain rendered text, structured invocation
metadata and `isError`. A scientific refusal is a complete tool result with
`isError:true` and structured refusal detail, not a JSON-RPC protocol error.

Malformed JSON, duplicate keys and invalid UTF-8 produce `-32700`; an invalid
closed envelope (`jsonrpc:"2.0"`, string method, non-null string/integer id)
produces `-32600`. Malformed params or metadata and unknown tools use `-32602`;
unsupported protocol versions use `-32022` with supported/requested versions;
unknown methods (including initialize) use `-32601`. Notifications omit `id` and
receive no response. Frames are bounded to 1,048,576 bytes; oversized or malformed
frames are drained through their newline and do not end or desynchronize the loop.
Shutdown drains active work and closes the attended session and companion socket.

## Failure and recovery

Read structured refusals and the ledger before retrying an uncertain effect.
An unfinished invocation is not proof of no effect. Restore/admission and permit
failures require the named kernel/operator remedy; registry replay cannot repair
scientific roots. Never edit pins or ledger lines to force progress. Reopen after
mount changes; resolve stale epochs before treating an evaluation as current.

Multi-corpus belief evaluation is epoch-bound: coverage must equal the session's
corpora and every captured state must match the published state, including after
coordination writes. `science epoch` performs one fresh build in the CLI process;
it does not mutate the session's mounts. Corpus-local belief retains its kernel
path without introducing an epoch requirement. `next` keeps its attention read
live and names a row's unevaluated admission reason separately.

Launchers emit session-reconciliation findings as structured stderr lines at
startup. These are distinct from command refusal metadata; an unfinished intent
or unverified act needs investigation, not deletion of its ledger. A stop signal
during open/bind is held until session/socket cleanup owns the new resources.
