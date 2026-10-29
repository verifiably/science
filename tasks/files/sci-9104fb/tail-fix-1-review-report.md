# Retirement-tail fix round 1 scoped re-review

Reviewer: claude-code/claude-sonnet-5-5; range 6779b0c..1339976.

### Finding Verdicts
- **No gate covers the sequential sweep's equal-holder rule (hoisting `live_mounts` out of the loop in `adopt.py` goes undetected)** — ADDRESSED.
  - The new test is `test_the_sweep_judges_each_predecessor_against_the_holders_the_last_retirement_left` (`python/tests/test_commons_1b.py`, after the late-link test). It follows the prescribed scenario.
    - The fixture builds on `build_verified`. P2 comes from `publish_again` and keeps the assessment. P3 comes from `_publish_update` with the default keys, so it drops the assessment.
    - B adopts P3, and nothing is retired.
    - B adopts P2. Pin states are exactly `{P1: retired, P2: mounted, P3: mounted}`, and there is exactly one retired line, for P1.
    - The adopt report holds `retention P2: kept: dependency (<assessment>)`. `show P2` holds the same.
    - After `reopen` and a session epoch, `cited(assessment)` resolves to P2.
    - B's `verify` succeeds with a `[verification]` block. It uses the same code, entrypoint and `_confine` pattern as the existing verify test.
  - The mutation log (`tail-tail-fix-1-mutation.log`, in the `.superpowers/sdd/2026-10-28-science-commons-1b/` folder) hoists `mounts = live_mounts(...)` to the top of `_reevaluate`. It shows 1 failed in 23.72s. P2 comes out `retired` where `mounted` is expected, which is the double retirement the finding describes.
  - `tail-fix-1-green.log` shows 1 passed in 26.05s after the restore. The report says `git diff -- python/src` was empty before the GREEN run. I did not check that independently.
  - The focused log shows 21 passed and the fast log shows 1070 passed, as the fix agent reported. I did not re-run any suite.

### New Breakage in the Fix Diff
None. The builder follows the snapshot-cached pattern (`commons-1b-equal-holders`) with a matching conftest fixture shaped like `late_chain`. It only composes existing helpers (`build_verified`, `publish_again`, `_publish_update`), so it adds no duplicated logic. The test drives the real `adopt` and `verify` commands and monkeypatches nothing but the existing `_confine`. I did not look at how the subprocess env is built for this test.

### Out-of-Scope Observations
- The fix commit also adds the task-record file `tasks/sci-4b5ec4.md`, which is outside the code under review. It is a follow-up about retirement report wording, and I ignored it.

### Verdict
**Fix round:** All findings addressed, no new Critical/Important breakage

reviewer: claude-code/claude-sonnet-5-5
