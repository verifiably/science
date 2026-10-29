# Tail fix round 1: equal-holder sequential-sweep gate (Important 1)

Status: DONE. Commit 1339976 on `commons-1b` (tests only; no source change). Task sci-9da5a6 reopened, fixed, closed.

## Scenario as built

- Builder `build_equal_holders(work)` (`python/tests/helpers/commons.py`), snapshot `commons-1b-equal-holders`, fixture `equal_holders` (`python/tests/conftest.py`), shaped like `late_chain` (value plus refs).
  - Base: `build_verified` (B holds P1 mounted, has fetched A's datasets and holds an unpublished verification of A's assessment).
  - P2: `publish_again(installations, LOC_A)`, an equal-content successor of P1 that keeps the assessment.
  - P3: `_publish_update(installations)` with the default keys `("proposition","dataset","spec","run")`, a successor of P2 that drops the assessment.
  - Returns `(value, first, equal, last)` = P1, P2, P3 corpus ids. No new logic blocks: only existing helpers are composed.
- Test `test_the_sweep_judges_each_predecessor_against_the_holders_the_last_retirement_left` (`python/tests/test_commons_1b.py`, after the late-link test):
  1. B adopts P3: the chain is unresolved (P2 missing), so nothing is retired (`_retired_lines == []`).
  2. B adopts P2: the chain P1 -> P2 -> P3 resolves. Asserts pin states `{P1: retired, P2: mounted, P3: mounted}`; exactly one `retired` sharing line, for P1; adopt's report holds `retirement P1:` and `retention P2:\n  kept: dependency (<assessment>)`; `show P2` holds `retention:\n  kept: dependency (<assessment>)`.
  3. B reopened with an epoch: `cited(assessment)` resolves to P2, and B's `verify` of A's assessment (confined as `_confine` sets it) succeeds with a `[verification]` block.

## Design clauses it rests on (docs/specs/2026-10-28-science-commons-1b-design.md §5.7)

- Retirement re-evaluation: for a resolved group, "every mounted publication on the chain other than the tip, in chain order from the oldest, is retired unless it is required". So P1 is judged before P2.
- Rule 4 (dependency): a predecessor is required when a write-root record's closure reaches "a record that no other live mounted corpus holds with equal content identity". When P1 is judged, P2 is live and holds the assessment, so P1 is not required and is retired. When P2 is judged, P1 is no longer live, so P2 is the sole holder and is kept by dependency.
- Rule 2 (chain retention) does not apply to P2: the older publication P1 was not required by rules 1, 3 or 4; it was retired.
- The late-link clause ("adopting the missing P2 after P1 and P3 resolves their chain, and both P1 and P2 are retired by that invocation unless required") is the case this test pins with P2 required.

The expectations match the reviewer's; no NEEDS_CONTEXT question arose.

## RED (mutation) and GREEN evidence

Mutation (logged in `tail-fix-1-mutation.log`): hoist `mounts = live_mounts(config, ctx.world, registry)` out of the predecessor loop to the top of `_reevaluate` (its pre-Task-13 position, 7f5a2d7). Command:

```
just test-one tests/test_commons_1b.py::test_the_sweep_judges_each_predecessor_against_the_holders_the_last_retirement_left
```

RED output (full run in `tail-fix-1-red-full.log`):

```
E       AssertionError: assert {'c5adfb355ca...6': 'mounted'} == {'c5adfb355ca...6': 'mounted'}
E         Differing items:
E         {'c865e7a4bbcf299384f339ee86cb90da': 'retired'} != {'c865e7a4bbcf299384f339ee86cb90da': 'mounted'}
FAILED tests/test_commons_1b.py::test_the_sweep_judges_each_predecessor_against_the_holders_the_last_retirement_left
============================== 1 failed in 23.72s ==============================
```

The differing corpus is P2 (expected `mounted`; P3, the other expected `mounted` pin, is among the identical items): with mounts hoisted, P2 is judged against the stale holder set that still lists P1, so both equal holders are retired in one `adopt`, the irreversible loss the finding names.

Restore: source copied back from a saved original; `git diff -- python/src` empty (checked before the GREEN run and recorded in the log).

GREEN after restore: same command, `1 passed in 26.05s` (`tail-fix-1-green.log`). Before the mutation the test also passed first time (29.00s).

Focused file run: `just test-one tests/test_commons_1b.py`, 21 passed in 263.10s (`tail-fix-1-focused.log`).

`just test-fast`: 1070 passed in 405.32s (6m47s wall) (`tail-fix-1-fast.log`); Task 14's run was 1069, the difference is this test.

## Files changed (commit 1339976)

- `python/tests/helpers/commons.py`: `build_equal_holders`.
- `python/tests/conftest.py`: `equal_holders` fixture.
- `python/tests/test_commons_1b.py`: the gate; `reopen` added to the `helpers.commons` import.

## Concerns

None. The gate exposed no defect: the current source keeps P2 as the reviewer traced. The full suite (`just test`) was not run here; the pre-push hook carries it.
