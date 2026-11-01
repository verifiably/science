Reviewer: claude-code/claude-opus-5-5 (fresh subagent), fix 7e53742..9c93dac

**Resolved, in part.** The Python refusal now carries each location verbatim, one per line. But the doc's new instruction to copy "exactly as either message prints it" is wrong for the CLI, which prints refusals as escaped JSON. So the finding's failure mode survives on the CLI for some paths.

**(a) Is the finding resolved?**
- `python/src/science/holdings.py:98-100` builds the message as `f"{address} is blocked ({', '.join(answer.reasons)}) at:\n" + "\n".join(answer.locations)`. `answer.locations` is a sorted tuple of plain strings (beliefs `holdings/adapter.py:77`). The repr, trailing comma and quotes are gone. In the Python message, tab, NBSP, `, ` and quotes now appear as themselves.
- **Newline.** beliefs' `require_store_relative_path` (`records.py:54-75`) rejects only NUL, an empty path, a leading or trailing `/`, empty components, `.` and `..`, and the `.#~` prefix. A newline is allowed. Science really produces such paths: `commands/dataset.py:56` and `commands/fetch.py:64` use `f"{digest}/{source.name}"`, and a Linux filename can contain `\n`. Such a location splits across two lines, and the second line does not start with `store:`. Copying the first line re-checks a shorter, nonexistent path, and the effect is the same as the original finding. This is rare, so I grade it Minor (below).
- `science recheck` would accept the full multi-line location, because `parse_store_location` only refuses whitespace at either end.

**(b) Does the test fail without the fix and pass with it?**
- With the fix, `just test-one tests/test_stores.py tests/test_cmd_recheck.py` passed 68 of 68.
- Without the fix, the old message was one line. The test's `inherited_location` is plain ASCII with no newline, so `splitlines()[1:]` would be `[]`, not `[inherited_location]`, and the assertion fails. I worked this out from the code and did not run it, since this review was read-only.
- A repr-per-line format would also fail it, because repr adds quotes. The fixture has no special characters, so tab, NBSP and quote spellings are not tested.

**(c) Do the doc's claims match the code?**
- `<address> is blocked (<reasons>) at:` matches line 99. `<reasons>` is the sorted union of reasons across all blocked locations.
- "Only once the location also has an observation matching the declared digest" matches `dataset_observations` (`adapter.py:70-77`, the `_joined(head, declared)` check). Otherwise the result is a `DatasetAnswer` with no observations, which gives the "not held" refusal.
- The `StoreWriteRefused` message `<location>: the store refused the write: …` matches beliefs `errors.py:1682`, which is passed `location.canonical()` (`boundary.py:275`).
- **Mismatch:** "one location per line" and "exactly as either message prints it". See the Important finding.

**(d) Does anything depend on the old format?**
- Searching `python/`, `docs/`, `commands/`, `adapters/`, `tools/` and `README.md` finds no parser of this refusal and no other test asserting on it.
- The only copy of the old f-string is `docs/plans/2026-09-09-belief-path-commands.md:1112`, a historical plan, which is fine to leave.
- The `commands/recheck/prompt.md` and recheck `SKILL.md` text ("exactly as the blocked row names it") is unaffected.

## New issues

**Important: `docs/stores.md:113-120`. The CLI does not print the message as the doc describes.**
- The CLI writes a refusal as one JSON line on stderr (`python/src/science/cli.py:98-99, 202-207`). `json.dumps` there uses the default `ensure_ascii=True`.
- So the dataset-read refusal does not show one location per line: the lines are joined by a literal `\n`.
- Any non-ASCII character in a location becomes `\uXXXX`, a tab becomes `\t`, and `"` and `\` gain a backslash. Example output: `"…at:\nstore:aaaa…:dead/caf\u00e9\tx \"q\".csv"`. The `StoreWriteRefused` message goes through the same JSON path.
- An operator following "copy exactly as either message prints it, nothing added or trimmed" would pass the escaped spelling to `science recheck --location`. The kernel accepts it as a different path.
- `recheck.handle` (`recheck.py:74-84`) does not require an intent or observation at the location. It re-checks the wrong path, publishes a governed Absent there, and leaves the real block. That is the original finding's effect.
- This is realistic: the relative path ends in the user's source filename, so non-ASCII names are ordinary.
- The MCP surface is not affected: its content text `refused [code] message` (`mcp.py:303-304`) is JSON-decoded by the client.
- Suggested fix: tell the operator to take the location from the decoded message (for example `… 2>&1 >/dev/null | jq -r .refusal.message` on the CLI, or the MCP text), one line per location. Ideally add a test with a non-ASCII or tab location that round-trips the decoded line into `parse_store_location`.
- Part of this predates the commit, since the write refusal was always JSON-escaped. But the "exactly as printed" claim is new in this change.

**Minor: `python/src/science/holdings.py:99-100`. A location containing a newline is ambiguous in the one-per-line format.**
- As described in (a), such a location splits across two lines, and copying the first line re-checks a different path.
- It is rare and somewhat recognisable (the extra line lacks `store:`), but nothing documents or guards it.
- Options: refuse or flag a location containing a newline in this message, or document that a line not starting with `store:` belongs to the line before.

**Minor, outside this diff: `python/src/science/commands/recheck.py:25-27`.**
- `parse_store_location` refuses any location for which `text != text.strip()`. Python's `strip()` removes Unicode whitespace, NBSP included. The kernel accepts a relative path ending in a space or NBSP, and a filename can end that way.
- Such a location cannot be re-checked at all, yet the doc says to give it "with nothing added or trimmed".
- It fails safe (a refusal, no publication), but that block has no settling route.

**Minor: `python/tests/test_stores.py:335-336`.** The strengthened assertion uses an ASCII hex/filename location only. Nothing pins the verbatim spelling for tab, NBSP or quote characters, so the behaviour the finding was about is untested.

## Verdict
**Revise.** Correct the step-1 instruction so it matches what the CLI actually prints (decode the JSON `message` first), and preferably add a test with special characters. The code change itself is correct.

Reviewer: claude-opus-5-5