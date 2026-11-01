Reviewer: claude-code/claude-opus-5-5 (fresh subagent), fix 6312229..2504013

**Scoped re-review of 2504013: step 1 of "Settling an unsettled location" in `docs/stores.md`**

## Resolved

The finding is resolved for the characters an operator will realistically meet: non-ASCII, double quotes and backslashes. Tabs and newlines are only partly covered (Minor 1 below).

Read as an operator would, step 1 now does three things. It sends the operator to the decoded refusal message rather than the escaped stderr text. It names the decoder. And it keeps the rule to add or trim nothing. Both ways a location reaches the operator are refusals:
- A failed write fails with `StoreWriteRefused`. Its message comes from beliefs `errors.py:1682` as `f"{location}: the store refused the write: {detail}"` and goes through `kernel_refusal`.
- A blocked dataset read fails with `Refused(Refusal("invalid-input", "... is blocked (...) at:\n" + "\n".join(locations)))` at `holdings.py:97-100`.

So "take it from the decoded refusal message" covers both sources that step 1 lists.

I fed `jq -r .refusal.message` a line built exactly as `_json_line` builds it, using a message containing a tab, `é`, `"`, `\` and a newline. It returned the original bytes.

## The doc's claims checked against the code

| Claim | Evidence | Holds? |
|---|---|---|
| A refusal is one JSON line | `cli.py:98-99` `_json_line` | Yes |
| It goes to stderr | `sys.stderr.write(...)`, used by `main` at `cli.py:203-207` and `_via_service` at `cli.py:286, 289-290, 296-297` | Yes |
| Key path `.refusal.message` | Payload `{"refusal": envelope(...), "invocation_id": ...}`; `envelope` at `refusal.py:43-45` returns `{"code", "message", "data"}`. The service path forwards `reply["refusal"]`, which has the same shape. | Yes |
| Escaping | `json.dumps` with `ensure_ascii` left at its default `True`, so it escapes `\n`, `\t`, `"`, `\`, other control characters (as `\u00XX`) and every non-ASCII character | Yes, but the list is incomplete (Minor 3) |
| MCP delivers the message decoded | `mcp.py:293-310`: the text content is `f"refused [{code}] {message}"`, and `structuredContent.refusal` is the envelope. The JSON-RPC wire (`mcp.py:431`) is ASCII-escaped too, but a client parses it, so the operator sees decoded text. | Yes, with a prefix (Minor 4) |

## Is the jq example usable as written?

The filter itself is correct. The routing is not stated. On a refusal stdout is empty and the JSON is on stderr, so the natural `science <cmd> … | jq -r .refusal.message` sends jq nothing. jq then prints nothing and exits 0 (I checked). The failure is visible as no output, not as a wrong location, so it costs the operator time but not a wrong action. Details in Minor 2.

## New issues

**Critical:** none.

**Important:** none.

**Minor**

1. `docs/stores.md:119-124`: decoding does not give an exact location for tabs and newlines, though the text names both.
   - Store relative paths may contain them. `require_store_relative_path` in beliefs `holdings/records.py` forbids only NUL, and `fetch.py`/`dataset.py` build the path as `<hex>/<source file name>`.
   - Once decoded and shown in a terminal, a tab copies back as spaces in most terminals. The re-check then hits a different path, the same harm as the original finding: a spurious Absent while the real block stays.
   - A decoded newline has to be passed through shell quoting the doc does not describe.
   - In the dataset-read listing (one location per line, `holdings.py:99-100`), a location that contains a newline cannot be told apart from two locations, decoded or not.
   - It is graded Minor because these file names are rare, and the realistic classes are fixed.
   - Fix: say that a location containing a tab or newline must be passed programmatically, not copied from the terminal. Either keep it in a variable taken from `jq -r` and strip the known `": the store refused the write: …"` suffix, or paste the escaped JSON text into bash `$'…'`, whose `\t`, `\n`, `\"`, `\\` and `\uXXXX` match JSON's escapes.
   - Or stop claiming tabs and newlines are covered.

2. `docs/stores.md:121-122`: the jq example does not say that the JSON is on stderr. Spelling it as `science <command> … 2>&1 >/dev/null | jq -r .refusal.message` would make it usable as written.

3. `docs/stores.md:120-121`: the list of escaped characters leaves out backslashes, which the finding itself cited, and other control characters. The instruction "never from escaped text" still covers them, so this is an accuracy gap only. "Escaping quotes, backslashes, control characters such as newlines and tabs, and non-ASCII characters" would be complete.

4. `docs/stores.md:122`: the MCP text content is `refused [<code>] <message>`. An operator reading it has to drop that prefix as well as the `: the store refused the write: …` suffix. `structuredContent.refusal.message` holds the bare message. One clause would cover it.

**Outside this commit's scope, for the controller:** `recheck.py:23-26` (`parse_store_location`) refuses any location with surrounding whitespace. A dataset whose source file name ends in a space gets the location `store:<id>:<hex>/name `, which the writers accept, but `recheck` can never take it. Such a location could never be settled through `science recheck`. This is code on this branch, not this doc commit; it is worth a ruling or a follow-up task.

## Verdict

Accept. The finding is resolved for the characters an operator will realistically meet, and every claim in the changed text matches the code. The four Minors are wording gaps; Minor 1 matters only for file names containing tabs or newlines.

Reviewer: claude-code/claude-opus-5-5