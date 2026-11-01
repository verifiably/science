Reviewer: claude-code/claude-opus-5-5 (fresh subagent), range ee509ca..a0e38ea

### Strengths

- The handler is small and stays on the public route. `parse_store_location` → `_bind` → `standing_at` → `writer.recheck`, and every handler refusal is raised before the kernel call. Product code reads no private beliefs members (`ScopedWriter._writer`, seams). The command is not labelled read-only, and it assumes no outcome: it renders whatever the kernel published.
- It fits the dispatcher's write contract cleanly. The handler's blocks only need to pass `audit_write_report`'s identity-pair check. The detail lines come from `record_block` over stored records, so the rendered report is the same on first response, replay and continuation. `test_replay_renders_the_same_detail` proves this, including a forced multi-page continuation.
- `standing_at` gathers observations from every read view, as spec §Design step 3 asks. `test_inherited_head_is_superseded` would fail if standing came from the write view only: the archive head would survive and `(head,) = active_heads(...)` would break.
- I checked the kernel contract against the beliefs source:
  - `recheck_locations` checks permits, observer and instrument, the root, the port and the store id before `_append_operation_intent`.
  - `re-check` is not in `MUTATING_KINDS`, so an inconclusive re-check adds no new block.
  - `_unsettled` repairs only with a later matched `re-check` intent in the same chain. That is the "same `write_root`" rule that prompt.md and stores.md state.
- The tests exercise real behaviour end to end: the incident replica (`READ_ONLY_SERVICEABLE` store as `store_root`, `StoreWriteRefused`), an untouched second location, before-effect refusals checked by an unchanged write-root tree snapshot, and the full recovery configuration round trip including `held_path` on the fresh store.
- §7.4's amendment matches the implementation word for word.
- The `cli.toml` adopt adds only the `recheck` hunk to science's section. The row matches the plan.
- `just test-one tests/test_cmd_recheck.py tests/test_report.py`: 35 passed (my run).

### Issues

#### Critical (Must Fix)

None.

#### Important (Should Fix)

1. **`python/src/science/commands/recheck.py:25`: `not text.isprintable()` refuses valid kernel locations that science's own writers produce.**
   - **What's wrong:** `require_store_relative_path` admits every character except NUL. `dataset` builds `<hex>/<source.name>` from any file name, and `ResourceDeclaration.name` has no character rule. Python's `isprintable()` is False for tab, NBSP (U+00A0), ZWNJ/ZWJ (U+200C/U+200D), soft hyphen (U+00AD) and every other Zs/Cf/Cc character.
   - **Effect:** a file named with any of these can leave an `unsettled` location after a refused write, and `recheck` can never settle it. The refusal message ("carries surrounding whitespace or control characters; give it exactly as the blocked row names it") is a dead end, because the operator did give it exactly as named. That defeats the command's one purpose for that person.
   - **Ruling cost understated:** the Task 2 ruling records the cost as "a store path with a control character cannot be re-checked", but the class is wider than control characters.
   - **Fix:** drop the `isprintable()` clause. `text != text.strip()` alone covers Review Focus 1, both the padded space and the trailing newline. Interior characters can be left to `StoreLocator`.
   - **Test:** add a case that re-checks a never-written path containing `\u00a0` or a tab and expects Absent.

#### Minor (Nice to Have)

1. **Trailing whitespace in a path is ambiguous with padding** (`recheck.py:25`).
   - A dataset file name ending in a space yields a locator that ends in a space, and the strip check refuses it. This is inherent to Review Focus 1, and I would keep the refusal.
   - The message should say that a location whose path really ends in whitespace cannot be given to `recheck`, so the operator knows it is a limitation and not their mistake. Alternatively, record it as a known limitation in prompt.md.
2. **`docs/stores.md` step 1 omits the most direct source of the location.**
   - **What's wrong:** the refused write's own refusal names it. `StoreWriteRefused`'s message is `"<canonical location>: the store refused the write: …"`, and a replay by the refused invocation's id returns it.
   - **Why it matters:** the dataset-read route the step does name (`held_path`'s "is blocked at") fires only when a head at the blocked location joins a declared digest (`beliefs/holdings/adapter.py::dataset_observations`). After a first write refused with no observation, a dataset read says "not held", not "blocked at".
   - **Also:** that refusal renders `answer.locations` as a Python tuple repr (`('store:…',)`), so "give it to `recheck` unchanged" needs the quotes and parentheses taken off.
   - **Fix:** name the write refusal first, state when a dataset read shows the block, and note the tuple spelling. The Task 4 ruling's premise ("a dataset read's refusal names the location") holds only in that narrower case.
3. **`test_malformed_location_refuses` `uppercase-id` checks only the refusal code** (`test_cmd_recheck.py`). Review Focus 2 expects the message to name the identity rule. The behaviour holds, since the kernel message is "not 32 lowercase hexadecimal characters", but the test would not catch a regression. Assert `"lowercase hexadecimal" in refusal.message` for that case.
4. **`docs/stores.md` step 3, "restart the writer".** "The writer" is undefined in this doc. Say "restart `science serve`", matching the stop instruction earlier in the step.
5. **`python/src/science/report.py:_detail` now validates every act-report on every write render.** It calls `stored.act_report_facet`, including for `run`, `verify` and `publish` reports and their replays. If the kernel's validator ever tightens, a historical replay of an unrelated command would raise `MalformedRecord` where it used to render title only. This is low risk with append-only corpora. A cheap guard is to check `node.facets.get("act-report", {}).get("operation") == "re-check"` before validating, though that reads a raw facet. Alternatively, leave it as is and note it.
6. **`python/tests/test_report.py:1`:** `import pytest` sits above the stdlib `from types import …`. This is cosmetic.
7. **Handler block order is discarded.** The plan's "observation first" is overridden because `_minted_report` sorts the pairs by `(uid, record_id)`, so the act-report may render first. This is harmless, and the tests match by substring. A comment in `handle` would stop a future reader from relying on the order.

### Rulings

- **Task 1, ops focused tests only under ops' `automatic_broad = false`:** agree. Ops' own policy governs ops checkouts, per the global Tests rule.
- **Task 1, added `test_science_recheck_surface` for RED→GREEN:** agree.
- **Task 2, inherited head tested with `build_two_corpus_world` rather than relocated store plus recovery config:** agree. It is the direct "head in a mounted read corpus" case, and Task 4 covers the recovery path.
- **Task 2, permit test narrows the declaration's routes; the invocation opens and closes refused:** agree. An attended session is full-permit, so this is the only reachable form. The plan's "no `invocation-open`" was unachievable.
- **Task 2, patching `beliefs.session.holdings_seam`:** agree. It is test-only coupling that the plan anticipated.
- **Task 2, refusing surrounding whitespace and any non-printable character:** partly disagree. Keep the strip check. The `isprintable()` half blocks legitimate locations that `dataset` can create, and the recorded cost is too narrow (Important 1).
- **Task 2, importing `replicate_store` and `tree_snapshot` from `test_stores`; "no chain entry" as an unchanged file tree:** agree. The tree snapshot is a stronger check than a chain-length count.
- **Task 3, `run-attempt` operation and test-only use of `beliefs.report._mint_report`:** agree. The private use stays in tests.
- **Task 3, `test_detail_lines_follow_the_title` added; no dataset/fetch expected outputs needed changing:** agree. I found no exact-text golden files for those reports.
- **Task 4, runbook step 1 keeps "find it in the reduction" and states that no science command lists blocked rows:** agree that this is the honest limitation. Disagree with the stated discovery premise (Minor 2).

### Declined to judge

- **Late `RecheckRefused` closing refused beside committed acts:** the dispatcher's existing behaviour. The spec explicitly records it and leaves it unchanged.
- **`RuntimeError` from `_load` leaving the invocation open (`outcome-unknown` on retry):** the existing contract for non-refusal errors. The spec says this task does not widen it.
- **Cross-corpus supersession of a head in a retired or foreign corpus:** kernel semantics. The spec relies on the record layer admitting it. Beliefs owns the question, not this command.
- **`--location` required at CLI parse even with `--continue`:** the same pattern as `fetch --source`. It is outside this task.
- **Outstanding continuation cursors for `dataset`/`fetch` reports issued before this change:** they now refuse `stale-cursor` because the report digest gained detail lines. The cursors are ephemeral and the refusal tells the user to re-run.
- **The Task 4 xdist "different tests collected" flake under testmon selection:** gate tooling (ops' `tt`/testmon), not this diff. It is worth a `tasks feedback --project ops` gap report if it recurs.
- **Whether the operations root must be shared in the recovery configuration (stores.md says to share it; the handler message names only `write_root`):** the conservative doc instruction is harmless, and the recovery test shares it.

### Recommendations

- Remove the `isprintable()` clause and add a re-check test on a path containing NBSP or a tab.
- Tighten stores.md step 1 (the write refusal names the location; the tuple repr spelling) and the "restart" wording in step 3.
- Assert the identity-rule message in the `uppercase-id` case.

### Assessment

**Ready to merge?** With fixes.

**Reasoning:** The command, the report detail and the recovery path are correct against the beliefs contract, and the tests fail when the behaviour they name breaks. The one Important finding is a one-line over-strict input check: it stops `recheck` settling valid locations that science's own `dataset` can produce, with a misleading message.

**Reviewer:** claude-code/claude-opus-5-5