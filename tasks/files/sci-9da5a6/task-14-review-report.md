# Task 14 review (impl round 1)

Reviewer: claude-code/claude-opus-5-5 (fresh subagent, read-only). Range 0ca4934..320f9e3, package review-0ca4934..320f9e3.diff.

### Spec Compliance
- ✅ Spec compliant. Every gate in the brief, as §5.9 item 6 and §5.7 define it, maps to a test. Each test drives the real `adopt`/`show`/`verify`/`publish-preview`/`publish`/`provider-bind` handlers over snapshot fixtures. The only monkeypatch is the named crash seam `science.commands.adopt._reevaluate`. It is never applied to the decision under test, and `python/src` is untouched.
- ⚠️ Cannot verify from diff:
  - The post-retirement sibling case says "the preflight reads P1's retired copy". Nothing the test can observe proves that. Both siblings' markers name P1, so the divergence also follows from named ancestry alone. The test asserts the group held at that point includes P1 as `retired` (`test_commons_1b.py:279-280`), and the refusal outcome. The implementer says so too.
  - I did not re-run the suites. Logs show focused 94 passed and `test-fast` 1069 passed, with no warnings in either log.

### Gate map
| Gate | Test (at 320f9e3) | Check |
|---|---|---|
| spec-drop | `test_commons_1b.py:215` (fixture `spec_drop` = `build_verified` + `_publish_update` without `spec`, `helpers/commons.py:675`) | Precondition asserted: the successor's selection has assessment and run but no spec (`:220`). Adopt report and `show` both give `kept: dependency (<spec>)` with a trailing `\n`, so that is the only reason. Both pins `mounted`, no `retired` line. The mutation that stops the walk following a spec fails it. |
| spec-only | `test_commons_1b.py:230` (`build_spec_only`, `helpers/commons.py:682`) | Selection is exactly the dataset plus the two vocabulary lists. B's write root has a spec and no run, assessment or verification. Report and `show` give `kept: dependency (<proposition>)`; nothing retired. Fails under the "stop following `target`" mutation. |
| late-link, both arrival orders, then P2 | `test_commons_1b.py:246` (parametrised) | The group is `unresolved` with P2 missing. `current` is the first-mounted end, read through the real fold over ledger lines. Nothing retired. Adopting P2 then retires exactly P1 and P2 (verdict `retired`), and the group resolves to tip P3. Fixture base `build_bound` (`helpers/commons.py:658`) gives B nothing that depends on A, matching the design's "unkept branch" condition. |
| retry after crash | cited `test_cmd_show.py:210` | Checked: crash injected at `_reevaluate`, P1 still `mounted` and live, ledger unchanged. Re-adopting P3 returns text containing `[pin] P1 retired` rather than a refusal, and the pin is `retired`. Fully asserts the gate. |
| post-retirement sibling | `test_commons_1b.py:271` (`sibling_publications_unkept`, a base-parametrised split at `helpers/commons.py:627-645`) | P1 is retired by adopting P3. The sibling is refused `divergent-publication`, tips {P3, P3′}. P3′ stays `fetched` and kernel-unknown; P3 and P1 states unchanged. |
| late-kept predecessor | `test_commons_1b.py:287` | P2 retired, P3 mounted. P1 under `keep` is refused with `data == {"rule":"chain-retired","addresses":[],"corpus":P2}`, matching the plan's data shape exactly. P1 stays `fetched` and unknown. Fails under the preflight mutation. |
| requirement-before-sweep | `test_commons_1b.py:303` | Third reader C. The crash seam (scoped by `monkeypatch.context`) leaves P1 at `pending: rerun adopt`. Q = B's P2: the test asserts its attributions name P1 as the only origin. Adopting Q mounts it; report and `show` give `kept: attribution (named by Q)`; P1 live; no `retired` line. The ordering is guarded too: a sweep run before Q mounted would retire P1, which `:329` would catch. |
| chain retention by `keep`, then released | `test_cmd_adopt.py:369` | Gives `kept: configuration` and `kept: chain (for P1)`, all three pins `mounted`, no `retired` line. The released adopt names the already-mounted tip, reports `["retired","retired"]`, and the ledger holds exactly {P1, P2}. |
| chain retention by B's verification | `test_commons_1b.py:334` | P1 stays `kept: dependency (<assessment>)` and the intermediate `kept: chain (for P1)`, in the report and in `show`; nothing retired. |
| configured keep | `test_cmd_adopt.py:348` `[True, False]` | `keep` goes through `write_commons_config` and then `load_config`, i.e. as loaded at open, and the loaded value is asserted. Listed: `kept: configuration`, P1 live, no `retired` lines. Unlisted: P1 `retired` with its ledger line. |
| stale configuration | `test_cmd_adopt.py:390` (extended) | Already asserted `config-stale` and the data. The extension adds the "nothing retired" half: P1 pin `mounted`, kernel live, no `retired` line. Fails under the "retire before the config check" mutation. |
| write guards | `test_commons_1b.py:347` | One session: adopt retires P1, and P1 is still in `ctx.session_ids()`. `verify` of A's assessment is refused `corpus-retired` with `{corpus, record}`. `publish-preview` and `publish` are each refused `corpus-retired` with `{corpus: P1}` and the reopen remedy. The write view is unchanged and the destination was never created. |
| `build_b_updated_unkept` retirement | `test_commons_1b.py:160` (extended) | Asserts the pin is `retired` and the ledger line has verdict `retired`. The extension adds "next open mounts P3 only" over `b_updated_unkept.b`, which `_build_b_updated` sets with `reopen` after the adopt (`helpers/commons.py:610-616`), so this is a genuine loader read. |

### Strengths
- Mutation evidence for eight retirement decisions, each a one-line source change that the targeted gate catches (`task-14-mutations.log`). The `[False]` keep case still passes under the "ignore keep" mutation, as it should.
- Each test asserts its precondition before the gate: the selection membership, Q's attribution origin, and the stale mounts in `session_ids`. A passing test therefore can't come from a mis-built fixture.
- Builders follow the established pattern: `_build_sibling_publications(work, *, base)` with two module-level callables, and snapshot fixtures named `commons-1b-<name>`. `_fetch_a_datasets` is extracted rather than copied, and `build_verified` behaves as before.
- Where existing tests had gaps (stale config, unkept retirement), they were extended rather than duplicated. The monkeypatched unit test at `test_cmd_adopt.py:468` was correctly not counted as the late-kept gate.

### Issues
#### Critical (Must Fix)
None.

#### Important (Should Fix)
None.

#### Minor (Nice to Have)
1. **Duplicate `show` helper.** `test_commons_1b.py:35` adds `_show`, identical to `test_cmd_show.py:25`. The extended test at `test_commons_1b.py:164` still calls `read_rig(...).invoke("show", ...)` inline. The module already imports helpers from `test_cmd_adopt`, so it could import `_show` the same way.
2. **Two ledger readers.** `_retired_lines` (`test_commons_1b.py:39`) uses `sharing_lines(operations_root)`, while `test_cmd_adopt.py` filters `_sharing_lines(cfg)` for the same purpose. Both work.
3. **Sibling gate is weak on mechanism.** As noted under "Cannot verify", it cannot show that the preflight reads P1's retired copy. A case where only the retired copy makes the pair divergent would need a hand-built marker, which is beyond this task.
4. **Unsnapshotted third reader.** `test_commons_1b.py:303` builds reader C inline with `build_installation` on every run. There is precedent for this, but it costs time on each run of the test.
5. **Some gates lack a fail demonstration.** The write-guard, late-link and sibling tests were not shown failing under a mutation. Their assertions are specific (exact refusal codes, exact retired sets), so they would fail if the behaviour regressed.

### Assessment
**Task quality:** Approved
**Reasoning:** Every brief gate is asserted by a real-command test over a fixture builder, or by a cited test that I checked fully asserts it, with preconditions pinned and mutations showing the retirement decisions are what the tests catch. The remaining items are small duplication and one design clause the test cannot observe.

reviewer: claude-code/claude-opus-5-5
