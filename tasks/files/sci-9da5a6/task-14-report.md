# Task 14 report: the retirement gates (sci-9da5a6)

Status: DONE. Commit 320f9e3 `test(commons): the retirement gates` on branch commons-1b (base 0ca4934; a8c6df8 is
the `tasks start` record). Tests only: no source defect found, no change under `python/src`, docs or prompts.

## Gate map (brief gate -> test)

Paths relative to `python/`. Line numbers are at 320f9e3.

| Gate (design §5.9 item 6 / §5.7) | Test | New / existing |
|---|---|---|
| spec-drop: P3 keeps assessment and run, drops the spec; B's verification keeps P1 `kept: dependency (<spec>)` | `tests/test_commons_1b.py:215` `test_a_successor_dropping_the_spec_keeps_p1_for_bs_verification` (fixture `spec_drop`) | new |
| spec-only: B's spec over A's proposition, no assessment; P3 keeps the dataset, drops the proposition and everything relating to it; P1 `kept: dependency (<proposition>)` | `tests/test_commons_1b.py:230` `test_a_successor_dropping_the_proposition_keeps_p1_for_bs_spec` (fixture `spec_only`) | new |
| late-link, both arrival orders: unresolved, current = first-mounted end, nothing retired; then P2′ adopted: P1 and P2′ both retired by that adopt | `tests/test_commons_1b.py:245` `test_the_late_link_resolves_the_chain_and_retires_both_non_tips[oldest-first, newest-first]` | new |
| (late-link report detail: two `[pin] … retired` blocks before the tail) | `tests/test_cmd_adopt.py:522` `test_two_retirements_in_one_invocation_render_both_pins_before_tail` | existing, supporting |
| retry after a crash between mount and retirement: adopt of P3 again retires P1 and reports it rather than refusing | `tests/test_cmd_show.py:210` `test_show_reports_pending_retirement_read_only_until_adopt_retries` (crash seam `science.commands.adopt._reevaluate`; second adopt reports `[pin] P1 retired`, pin `retired`) | existing, cited |
| post-retirement sibling: P1 retired, sibling P3′ arrives: preflight reads P1's retired copy, `divergent-publication`, P3′ `fetched` | `tests/test_commons_1b.py:271` `test_a_sibling_arriving_after_retirement_is_divergent_against_the_retired_copy` (fixture `sibling_publications_unkept`) | new |
| late-kept predecessor: P2 retired, P3 mounted, P1 adopted under `keep`: `adopt-conflict` rule `chain-retired` naming P2, P1 `fetched` | `tests/test_commons_1b.py:287` `test_a_late_kept_predecessor_refuses_chain_retired_naming_the_retired_intermediate` | new (the existing `test_cmd_adopt.py:468` is a monkeypatched unit test and does not count) |
| requirement-before-sweep: P1 pending retirement when Q (attributions naming P1) is adopted: Q mounts, P1 `kept: attribution (named by Q)` | `tests/test_commons_1b.py:303` `test_a_publication_naming_a_pending_predecessor_keeps_it_by_attribution` | new |
| chain retention by `keep`: P2 `kept: chain (for P1)`, nothing retired; requirement released, one adopt retires both | `tests/test_cmd_adopt.py:369` `test_chain_retention_keeps_the_intermediate_for_a_kept_predecessor_until_released` | new |
| chain retention by B's verification | `tests/test_commons_1b.py:334` `test_a_chain_kept_for_bs_verification_keeps_the_intermediate_and_retires_nothing` (fixture `b_updated`) | new |
| configured keep: P1 in `keep` before the session that adopts P3: `kept: configuration`; without the entry, retired | `tests/test_cmd_adopt.py:348` `test_a_keep_entry_loaded_at_open_keeps_the_predecessor_and_its_absence_retires_it[True, False]` (keep read through `load_config` of the written file) | new; complements existing `test_cmd_show.py:154` and `test_cmd_adopt.py` `test_a_successor_reports_configuration_retention` |
| stale configuration: file edited after open: adoption stands, `config-stale`, nothing retired | `tests/test_cmd_adopt.py:390` `test_changed_configuration_refuses_before_retirement_and_keeps_the_adoption` | existing, extended: it did not assert "nothing retired"; added P1 pin `mounted`, P1 live, no `retired` line |
| write guards: in one session, adopt retires P1, then `verify` of A's assessment, `publish-preview` and `publish` refuse `corpus-retired` naming P1, writing nothing | `tests/test_commons_1b.py:347` `test_writes_after_an_in_session_retirement_refuse_corpus_retired` (fixture `updated_unkept`) | new (existing `test_cmd_publish.py:156` and `test_mount_citations.py:91` retire through `open_world(...).retire`, not an in-session adopt) |
| `build_b_updated_unkept` retirement assertions: P1 retired, its line in the ledger, its pin `retired`, next open mounts P3 only | `tests/test_commons_1b.py:160` `test_the_unkept_branch_retires_the_predecessor_and_reports_it` | existing, extended: the "next open mounts P3 only" half was asserted only over registry pin states; added that B's next-open configuration (`b_updated_unkept.b`, the `reopen` after the adopt) holds P3's root and not P1's |

## What was implemented

- `tests/helpers/commons.py`: `_publish_update(installations, keys=...)` takes the A record keys its successor
  keeps (default unchanged); `_fetch_a_datasets` extracted from `build_verified` (behaviour unchanged);
  `build_sibling_publications` split into `_build_sibling_publications(work, *, base)` with
  `build_sibling_publications` (base `build_overlapping`, unchanged) and new `build_sibling_publications_unkept`
  (base `build_overlapping_unkept`); new `build_spec_drop` (`build_verified`, then a successor without the spec)
  and `build_spec_only` (`build_reopened`, B fetches A's datasets and specs over A's proposition, then a successor
  carrying only the dataset and vocabulary lists).
- `tests/conftest.py`: snapshot fixtures `sibling_publications_unkept`, `spec_drop`, `spec_only` under
  `commons-1b-<name>`.
- `tests/test_commons_1b.py`: eight new tests (nine cases), one extended; local `_show` and `_retired_lines`
  helpers; `_adopt`, `_bind`, `_states` imported from `test_cmd_adopt` (as `test_cmd_show` does).
- `tests/test_cmd_adopt.py`: two new tests (three cases), one extended.

Every new test drives the real commands (adopt, show, verify, publish-preview, publish, provider-bind) over
fixture builders. Monkeypatching: only the requirement-before-sweep test, which injects a crash at
`science.commands.adopt._reevaluate` (the crash seam between mount and retirement, as the existing retry test
uses) to put P1 in the pending state; the decision under test (step 3 during Q's adopt) runs unpatched.

Requirement-before-sweep uses a third reader built inline (`build_installation(..., "c")`, precedent
`test_siblings_under_a_never_held_predecessor_refuse_the_same_way`): Q is B's publication P2 from the unkept
chain, whose marker attributes A's records to P1. The test asserts that precondition from Q's marker.

Late-link adopts both ends in one session so the fold orders them by ledger position, deterministic whatever the
clock (two sessions within one second would fold by session id).

## TDD / fail demonstration

Every new test passed on its first run (gates on already-implemented behaviour). Each retirement-deciding gate was
shown to fail under a one-line source mutation, run, then `git checkout` of the source file (tree verified clean
after each). Full output: `task-14-mutations.log`.

| Mutation (source restored after) | Failing tests |
|---|---|
| `retention.dependency_closure`: stop following an assessment's and a run's spec | spec-drop (`kept: dependency (analysis-spec:…)` absent; P1 retired) |
| `retention.dependency_closure`: stop following a spec's `target` | spec-only (`kept: dependency (proposition:p1)` absent) |
| `retention.required`: never record chain retention | both chain-retention tests |
| `retention.required`: ignore `keep` | configured keep `[True]`, chain retention by keep (`[False]` still passes, as it should) |
| `adopt._require_current_config`: never refuse | stale configuration (`DID NOT RAISE`) |
| `adopt._reevaluate`: retire before the configuration check | stale configuration (P1 `retired`, new assertion) |
| `retention.required`: drop attribution reasons | requirement-before-sweep (P1 retired at Q's adopt) |
| `adopt._preflight`: skip the chain-retired refusal | late-kept predecessor (`DID NOT RAISE`) |

## Runs

- New tests, first run: `just test-one tests/test_commons_1b.py -k "…" -v`: 9 passed (134.5 s); spec-drop alone 1 passed
  (19.6 s); `just test-one tests/test_cmd_adopt.py -k "changed_configuration or keep_entry_loaded or chain_retention" -v`:
  4 passed (27.7 s).
- Focused (plan Step 2, plus `test_cmd_show.py` because the helper refactor touches builders it uses):
  `just test-one tests/test_commons_1b.py tests/test_cmd_adopt.py tests/test_cmd_show.py -v`: 94 passed in 460.86 s.
  Log `task-14-focused.log`.
- `just test-fast`: 1069 passed in 305.05 s (testmon selected the whole suite), exit 0. Log `task-14-fast.log`.
- Commit hooks passed (`task-14-commit.log`).

## Files changed

- `python/tests/helpers/commons.py`
- `python/tests/conftest.py`
- `python/tests/test_commons_1b.py`
- `python/tests/test_cmd_adopt.py`

## Self-review

- Completeness: every gate in the brief maps to a test above; two are existing tests cited (retry) or extended
  (stale configuration, unkept retirement assertions) where they had a gap.
- Design reading: chain retention "by `keep` or by B's verification" is tested both ways; the "released" half only
  for `keep`, since a verification cannot be released by configuration. The verification variant's chain is
  P1 → P3 → P4 (A republishes the update query once more), not the late chain, because the late chain carries A's
  assessment in every link (design: "on the main branch B's verification keeps P1 by rule 4" refers to P1 alone).
- The post-retirement sibling test asserts P1's retired copy is in the group the preflight reads; divergence would
  also follow from named ancestry without it (design §5.9 "a reader that never held P1, refused the same way"), so
  the test proves the outcome with P1 retired, not that the retired copy is necessary.
- Late-link "current is the first-mounted end" is asserted through `supersession.current` over the real ledger
  lines; `show` renders an unresolved group as `unresolved: adopt …`, which the existing
  `test_show_an_unresolved_group_names_the_link_to_adopt` covers.

## Concerns

None blocking. `build_spec_only` and `build_spec_drop` add two snapshot builds per xdist worker that runs them
(about 15–20 s each on this host).
