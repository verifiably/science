Reviewer: claude-code/claude-opus-5-5 (fresh subagent), fix 8b36d2c..301dda3

I recommend **revise**. Both findings are fixed in their main part, but the new runbook text in step 1 contains one inexact instruction about the dataset-read refusal's tuple form. Followed literally, it re-checks the wrong path.

## Findings

**1. The `isprintable()` clause blocked valid kernel locations: Resolved.**
- `python/src/science/commands/recheck.py:25` now refuses only `text != text.strip()`. The refusal message no longer mentions control characters.
- After the "surrounding whitespace" check, the parser only refuses URLs, refuses anything not shaped `store:<id>:<path>`, and passes `StoreLocator`'s `MalformedRecord`. That last check is the kernel's `require_store_relative_path`, which refuses NUL, empty paths, absolute paths, a trailing `/`, empty components, `.` and `..` components, and the `.#~` prefix. So the kernel now has the final say on interior characters.
- No stale text remains. `git grep -i "control char|isprintable|unprintable"` finds only the new test name and an unrelated line in `tools/tt`. Neither `commands/recheck/prompt.md`, `adapters/claude-code/skills/recheck/SKILL.md`, `commands/recheck/command.toml`, the `tools/cli.toml` row nor `docs/stores.md` mentions a control-character refusal.

**2. Runbook step 1 pointed to a refusal that a first refused write never produces: Resolved for the main point; the tuple-repr part is only partly addressed (see the new issue below).**
- The step now names the refused write's own message. I checked each claim:
  - The message is `"{location}: the store refused the write: {detail}"` (beliefs `errors.py:1682`).
  - It is raised with `location.canonical()` (beliefs `holdings/boundary.py:275`).
  - `kernel_refusal` uses `str(error)`, so the location appears raw, not as a repr (`science/refusal.py:55`).
  - `StoreWriteRefused` is in `KERNEL_REFUSALS` and is closed through `_close_refused`, which stores the envelope in the ledger. `_replay_outcome` raises the same refusal on a replay with that id (`dispatch.py:240-243, 418-422, 448-452`). So "replaying that invocation by its id returns the same refusal" holds.
- The claim that the dataset read names the location "only once the location also has an observation matching the dataset's declared digest" matches `dataset_observations` and `_joined` (beliefs `holdings/adapter.py:63-77`). One nuance is glossed: a `found` head whose digest differs still joins if its history once matched. That is acceptable.
- The claim that the read otherwise "reports the dataset not held" matches `held_path` (`science/holdings.py:100-101`) when no other copy holds the dataset. If another copy does, the read succeeds from that copy instead. That is a small overgeneralisation.

## Test checks (b)
- `just test-one tests/test_cmd_recheck.py` in the worktree: **26 passed**. That includes the three new cases (`\u00a0`, `\t`, `\u200d`) and `test_padded_location_refuses` (a leading space and a trailing `\n`).
- I did not run the RED half; it is inferred. I could not revert the code without writing to the tree. All three names return `isprintable() == False` (checked in a Python shell). So before 301dda3, `parse_store_location` would have refused `invalid-input`, `d.invoke` would have raised `Refused`, and all three new cases would fail.
- The padded-location refusal still holds: `str.strip()` removes the leading space and the trailing newline, and the test passes.

## New issues

**Important: `docs/stores.md:115-120`. Followed literally, the tuple instruction gives the wrong path.**
- The dataset read renders `f"{address} is blocked at {answer.locations}: {answer.reasons}"` (`python/src/science/holdings.py:99`), where `locations` is a `tuple[str, ...]`. Two consequences:
  1. **The common case of one location renders with a trailing comma:** `('store:<id>:<path>',)`. The doc writes the pattern as `(<locations>)` and says to drop "the tuple's quotes and parentheses and with nothing else added or trimmed". Read literally, that leaves `store:<id>:<path>,`, and `<path>,` is a valid kernel path.
  2. **repr escapes the very characters this fix now admits.** A tab shows as `\t`, NBSP as `\xa0`, ZWJ as `\u200d`. A path containing a `'` is quoted with `"`.
- **Why it matters:** copying from that refusal would re-check a different, non-existent path. That publishes a spurious `absent` observation and leaves the real block in place. This is the outcome the padded-locator refusal exists to prevent, and the step is meant to give the exact spelling.
- **Smallest fix:** render the locations plainly in `holdings.py:99`, e.g. `", ".join(answer.locations)` (one per line would be better, since paths may contain `, `). Then simplify the doc. Alternatively, keep the repr and document the trailing comma and escapes, but fixing the rendering is cleaner.
- This could be graded Minor, because the refused-write route is now listed first and is exact. I graded it Important because it is the step's own literal instruction, it applies in the most common case, and the fix is one line.

**Minor: `commands/recheck/prompt.md` (and the generated `SKILL.md`) plus `recheck.py:27`.** Both still tell the caller to give the location "exactly as the blocked row names it". By the doc's own statement, no science command lists blocked rows. An agent will normally have the `StoreWriteRefused` message instead. This was there before the fix and is not a regression, but it is out of step with the corrected step 1.

**Minor, by design: `recheck.py:25`.** `str.strip()` also strips Unicode whitespace, so a path ending in NBSP (or starting with it, if it were the first character) is refused, although the kernel admits it. This follows the requested behaviour ("keep the surrounding-whitespace refusal") and is noted only so the limit is on record.

## Verdict
**revise.** The only remaining item is the Important tuple-rendering instruction in `docs/stores.md` step 1. Fixing `holdings.py:99` to render the locations plainly, then simplifying the doc, resolves it.

Reviewer identity: claude-code/claude-opus-5-5