# SDD ledger — plan: docs/plans/2026-10-31-snapshot-lineages.md
Pre-flight: Task 1 -> Task 2: Root/Derived/materialize/copy_value produced by T1, consumed by T2 with the same signatures; no conflict.
Pre-flight: Task 1 -> Task 3: _build_link(work_base, declaration) produced by T1 (module global, wrapped by the T3 plugin); no conflict.
Setup: baseline `just test` at 4254cf3+records → 1140 passed, 164.8 s (load 2.4 at start).
Setup: before test-fast cold (fresh TESTMON_DATAFILE) → 1140 passed, 288.4 s pytest / 290.3 s wall (load rose 2.4→13.7 during run).
Setup: before test-fast warm (assert True in test_a_name_reused_with_another_builder_is_refused) → 1 selected, 1 passed, 3.7 s pytest / 5.6 s wall; file restored.
Task 1: Ruling: plan's test_a_failed_step_is_rebuilt_from_its_base root lambda indexed a 2-tuple with [2] (IndexError) — fixed to [1]; the test's intent (base.txt then {}) is unchanged — cost if wrong: none, a typo in test scaffolding
Task 1: Ruling: test-fast before commit failed only test_a_trickling_listener_cannot_extend_the_selection_deadline (load avg peaked 38; passes alone in 1.15 s) — committed anyway; it is the known load-sensitive 0.4 s bound tracked by sci-26ba4d, unrelated to snapshots — cost if wrong: a real regression in selection deadlines would go unnoticed until the full suite
Task 1: complete (commits ea9a67b..c88d9b4, tests: just test-one tests/test_snapshot.py → ============================= 21 passed in 41.21s ==============================)
Task 2: step 4 module runs (serial, reversed, combined worksteal) all pass — see step4-summary.txt: serial 1a 5/37s, 1b 21/121s, adopt 43/131s, show 31/76s, ownership 18/49s; reversed same counts; combined 118 passed 98s.
Task 2: step 5 `just test` → 1155 passed, 136.3 s pytest (user 17m44s vs baseline 24m09s; load 12 at start).
Task 2: Ruling: conftest/test_cmd_adopt step functions are named step_<x> and `build_late_link` became step_late_link(work, chain: tuple) — the plan's table names steps "from" the old builders without fixing parameter names; chain keeps the 4-tuple unpacking explicit — cost if wrong: naming only.
Task 2: complete (commits 2873b30..2fb2d8d, tests: just test-one tests/test_snapshot.py tests/test_commons_1a.py tests/test_commons_1b.py tests/test_cmd_adopt.py tests/test_cmd_show.py tests/test_publish_ownership.py -n auto --dist worksteal → ======================== 140 passed in 98.92s (0:01:38) ========================)
Task 3: measurement run 1 → 1155 passed; build total 1196.1 s over 223 links (16 workers, worst 138.2 s, best 25.5 s); load 11.6 at start, 53.8 at end — another session's parallel suite (kitty-2498922 uv-built python workers) plus obs index and dropbox ran concurrently. Every link built at most once per worker (design holds); the excess is contention plus 16 workers each building shared ancestors (fresh n=16, 167.5 s).
Task 3: Ruling: run 1 exceeds the 1,000 s threshold but was contaminated (load 54 on 32 cpus) — take one re-measurement once the 1-min load is under 8 (bounded 30 min wait) and report both runs; if the quiet run also exceeds 1,000 s, stop and report as the spec says — cost if wrong: a quiet-host number could flatter the routine (loaded) case the latency obligation sees.
Task 3: measurement run 2 (quiet, load 7.2 at start) → 1155 passed in 145.1 s; build total 937.1 s over 234 links, worst worker 110.4 s, best 14.3 s; each link at most once per worker. Threshold (≤1000) met.
Task 3: after test-fast cold → 1155 passed, 223.9 s (before 288.4 s); warm → 1 selected, 3.6 s (before 3.7 s).
Task 3: complete (commits 51afa1f..295d758, tests: just check → (no output))
Final review (fresh reviewer, claude-opus-5-5): Critical 0, Important 0, Minor 4; ready to merge. Saved as final-review-report.md.
Final: Ruling: re-grade Minor 1 (failed root build leaves work_base/<root> and the retry dies with FileExistsError) to Important — every commons declaration shares the FRESH root, so one transient fresh failure turns every later commons test on that worker into a FileExistsError that hides the cause — cost if wrong: one small extra fix and test.
Final: Ruling: re-grade Minor 3 (partial image left by a failed image copytree blocks the retry with FileExistsError) to Important — same cascade for the shared root's image; fixed with the same unrecorded-leftover rule — cost if wrong: one small extra fix and test.
Final: minor (deferred): a name repeated inside one unbuilt chain (Derived("x", base=Derived("x", ...))) is silently reused; no current declaration does this.
Final: minor (deferred): conftest conflicting_publication calls copy_value(snap.value) twice in one return; harmless, inconsistent with test_cmd_adopt's fixtures.
Final: fixed failed root build not retried (Minor 1, re-graded Important) — test_a_failed_root_build_is_retried_from_an_empty_directory RED (FileExistsError) → GREEN, suite 1157/1157
Final: fixed partial image blocks retry (Minor 3, re-graded Important) — test_a_leftover_unrecorded_image_is_replaced RED (FileExistsError on .image) → GREEN, suite 1157/1157
Final: corrective round 1 re-review (fresh reviewer, claude-opus-5-5) on e2a5236: resolved; Critical 0, Important 0, Minor 3. Saved as fix-rereview-report.md.
Final: minor (deferred): a declaration name ending in `.image` would collide with another name's image path, letting _build_link's leftover removal delete a recorded image or lineage directory; no current name does.
Final: minor (deferred): no test pins that the root rebuild goes through _clear_tree (registry eviction, socket refusal) rather than a bare rmtree.
Final: minor (deferred): _clear_tree's socket refusal says "blocks the restore" when it fires on a root rebuild, where no restore is in progress.
