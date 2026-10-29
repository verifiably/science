# SDD ledger — plan: docs/plans/2026-10-28-science-commons-1b.md

Execution: approved plan at faad6f6 (plan revision 7, 8937235); sequential implementers and fresh task reviewers. Phase 1: Tasks 1–12. Phase 2: Tasks 13–15 blocked on beliefs-a989fb. Parent sci-9104fb remains open through both phases.

## Pre-flight task checks
| Task | Internal agreement |
|---|---|
| 1 | Pin loses keep; config keep/source supply show and retirement; parser version stays 1. |
| 2 | Conflict rules and deterministic corpus/rule order align with checklist tests. |
| 3 | Equal-holder selection shared by reads/citations; only citations and dataset duplicate checks inspect liveness. |
| 4 | Carrier content and three-argument explain updated together at belief/next callers. |
| 5 | Replace v1 dict entry rather than adding a duplicate binding. |
| 6 | Group includes world/view/destination; classify uses kernel roots and named ancestry; established is ledger-derived. |
| 7 | Per-holder profiles and facet dependencies extend closure_missing; supersedes is excluded. |
| 8 | Complete pin prefix composed by dispatch; durable historical tail; preflight before admission; retention after mount. |
| 9 | Read-only ledger fold supplies supersession/retention; command declaration unchanged. |
| 10 | Guard both publication routes; ambiguous details distinguish missing links from unlinked chains. |
| 11 | Snapshot callables stable; sibling fork restores publisher before republishing; fixtures discharge temporary xfails. |
| 12 | Overlap documentation includes sharing-tail exception and historical replay limits; full gate required. |
| 13 | Kernel door interface explicitly provisional; blocked until dependency lands. |
| 14 | Retirement/guard gates depend on Task 13; retain dependency block. |
| 15 | Retirement documentation follows actual door and gates, not overlap merge. |

## Pre-flight shared interfaces
| Tasks | Shared files/interfaces | Finding |
|---|---|---|
| 1, 3 | ScienceConfig, commons-fixtures | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 1, 6 | Pin | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 1, 8 | ScienceConfig, commons-fixtures | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 1, 9 | ScienceConfig, show | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 1, 11 | commons-fixtures | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 1, 13 | Pin | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 1, 14 | commons-fixtures | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 1, 15 | show | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 2, 8 | Conflict | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 3, 8 | ScienceConfig, commons-fixtures, refusal-codes | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 3, 9 | ScienceConfig | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 3, 10 | context-live-guard | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 3, 11 | commons-fixtures | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 3, 14 | commons-fixtures, context-live-guard | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 4, 11 | acceptance-content, commons-tests | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 4, 14 | commons-tests | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 5, 11 | epoch-v2 | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 6, 7 | supersession | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 6, 8 | supersession | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 6, 9 | supersession | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 6, 11 | supersession | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 6, 13 | Pin | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 7, 8 | retention, supersession | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 7, 9 | retention, supersession | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 7, 11 | retention, supersession | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 7, 13 | retention | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 7, 14 | retention | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 8, 9 | ScienceConfig, retention, supersession | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 8, 11 | adopt-tests, commons-fixtures, retention, supersession | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 8, 12 | sharing-report | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 8, 13 | adopt, adopt-tests, retention | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 8, 14 | adopt-tests, commons-fixtures, retention | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 8, 15 | adopt | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 9, 11 | retention, show-tests, supersession | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 9, 13 | retention | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 9, 14 | retention | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 9, 15 | show | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 10, 11 | publish-tests | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 10, 14 | context-live-guard, publication-handlers | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 11, 13 | adopt-tests, retention | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 11, 14 | adopt-tests, commons-fixtures, commons-tests, retention | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 12, 15 | overlap-docs | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 13, 14 | adopt-tests, retention | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |
| 13, 15 | adopt | Sequential changes compose; later task consumes the earlier shape. Fixtures deferred explicitly to Task 11; retirement changes deferred to Tasks 13–15. |

Task 8: Ruling: interpret “A fetched pin is never looked at here” as an unadmitted fetched pin, retaining reconcile for fetched pins already admitted by the kernel — the same paragraph explicitly requires fetched/admitted recovery and the existing crash test; design §5.7 requires reconciling completed effects — Cost: a wrong reading would change crash recovery; verify with the existing admission-crash test. Revision: approved plan 8937235 Task 8; design 99eabaa §5.7.

## Progress
Setup: existing clean locked commons-1b worktree, .githooks installed, existing python/.venv; just test baseline running; no implementation started.

Setup baseline: just test → 897 passed, 1 failed, 898 collected, 610.79s. Focused reproduction → 1 failed, 1.34s. Logs baseline.log and baseline-failure.log.
Ruling: continue from the observed red baseline and correct the obsolete selected-next duplicate-location assertion as a Task 1 prerequisite — cut 48 allows identical copies; the actual refusal is address-unknown for proposition:claimed, which the base fixture never minted. The plan already requires equal-holder behavior, so keep the missing-selection assertion and name equal-copy admission in the test — Cost: the wrong expectation could hide a selection regression; assert the exact refusal reason and refs. Revision: baseline ab9bfe8, approved plan 8937235 Tasks 1 and 3.
Task 1: BASE ab9bfe855202caf9611a9ad30b6af31e554abfc8; implementer /root/task1.

Task map: 1 sci-bb102d; 2 sci-a23752; 3 sci-29be32; 4 sci-390998; 5 sci-ba7508; 6 sci-29a07b; 7 sci-b47e33; 8 sci-e3cacf; 9 sci-d5954d; 10 sci-f8a0cf; 11 sci-8f42b9; 12 sci-12c16d; 13 sci-9c0bba; 14 sci-9da5a6; 15 sci-50d0c2.
Branch merge base before execution: 255295dd1b1e8682ee0aaf9c1e97b1e9f55d23c0.

Task 1: minor (deferred): testmon survey banner in task-1-fast.log:4; dependency output noise only, no production defect. Reviewer /root/review1, codex/gpt-6.1-sol; full report task-1-review-report.md.
Task 1: complete (commits ab9bfe8..84db392, review approved; 65 focused and 910 fast-suite passes; 1 minor deferred).
Task 2: BASE 77c2ed0c2c650703e29edb5bde03fe4aef84a025; fresh implementer next.
Task 2: Ruling: select the first conflicting live corpus, report its highest-priority rule (uid-corruption, content, deprecated-key), and include the sorted union of all its conflicting addresses; UID conflicts include both canonical endpoints — the brief specifies first corpus and every conflicting address but leaves mixed-rule aggregation implicit; complete deterministic diagnostics retain that contract — Cost: downstream callers might have expected addresses for only the selected rule; a mixed-rule test pins the decision. Revision: approved plan 8937235 Task 2, design 99eabaa §5.1.
Task 2: Ruling: use invocation-only just xdist="-n 1 --dist worksteal" test-fast for remaining incremental checks, keeping the locked dependency and selection enabled — the standard route failed before execution with divergent worker collection; upstream main fixes that exact initialization race in af5ba5c26d43a4b07b8afecc96ed2bcfc8773e92, not installed 2.2.0. Open/closed issues and PRs, main/development branches and releases searched; PR268 concerns a different nocollect path. Wait for a release containing af5ba5c instead of pinning a dependency during feature work — Cost: affected suites run serially and may be slower; revert the override once the installed release contains the fix. Evidence task-2-fast.log; feedback ops-ab03a7.

Task 2: complete (commits 77c2ed0..1e11efc, review clean; 10 focused + 10 selected fast pass). Reviewer /root/review2, codex/gpt-6.1-sol; full report task-2-review-report.md.
Task 3: BASE 9a88b6788b60cd04eb5c34714a7249f0e79354d7; fresh implementer next.
Task 3: Ruling: deduplicate unselected next proposition addresses before classification, preserving mount_holding validation for each row, and replace obsolete duplicate-refusal assertions with single-row success tests — equal-holder resolution otherwise exposes duplicate queue rows, contradicting commons §4.7 identical records contribute once; smallest complete caller fix belongs with this behavior change — Cost: premature dedup could mask conflicting copies, so keep equality validation and a differing-copy refusal regression. Revision: approved plan 8937235 Task 3; commons §4.7, 1b design 99eabaa §5.2.

Task 3: complete (commits 9a88b67..df4755e, review clean; 52 focused, next mutation RED/GREEN, 627 broad fast passes plus corrected assertion final focused/incremental pass). Reviewer /root/review3 codex/gpt-6.1-sol; task-3-review-report.md.
Task 4: BASE 56a2f7c0ac3bdb19842aa3b6e738f08af0d643de; fresh implementer next.
Task 4: Ruling: update belief.py as the sole production explain caller and leave next.py unchanged for this task — tree inspection finds next uses acceptance_inputs/counts, whose signature is unchanged, despite the brief naming an explain call there — Cost: a missed indirect caller could break at runtime; implementer searches all callers and runs the existing acceptance tests. Revision: approved plan 8937235 Task 4; implementation base 56a2f7c.

Task 4: complete (commits 56a2f7c..d1b2b41, review clean; 32 focused +96 fast pass). Reviewer /root/review4 codex/gpt-6.1-sol; task-4-review-report.md.
Task 5: BASE a2ad3e844a6eb3b64bd9782d0e4756dda67adb72; fresh implementer next.

Task 5: complete (commits a2ad3e8..5332653, review clean; 19 focused +55 fast pass). Reviewer /root/review5 codex/gpt-6.1-sol; task-5-review-report.md.
Task 6: BASE 2beccd7cac9e423059f92c591e3dfdfbc2e1e6c6; fresh implementer next.
Task 6: Ruling: chain(from_pair, to_pair, held) is endpoint-inclusive predecessor→descendant, with singleton self-path and None for a missing held path — consumers need oldest→tip order and intermediate-retirement inspection, while the brief leaves direction implicit — Cost: a reversed consumer could misclassify retention or retired intermediates; explicit path tests and downstream integration must enforce the direction. Revision: approved plan 8937235 Tasks 6–8.
Task 6 clarification: current consumes historical mounted lines for now-retired pins too; a transient fold current may name such a historical publication. Design §5.6 final-current property is not an instruction to omit their history.
Task 6: review round 2 by /root/review6 codex/gpt-6-astra: spec compliant, quality needs fixes; Important 1 duplicated ordered ledger reader. Full report task-6-review-report.md. Fix round 1/5 dispatched to original /root/task6, FIX_BASE 535307781e4f2eb66fdb35f220f9df39e4b92568; share the reader with replay, preserve supersession API.
Task 6: Ruling: consume historical mounted lines even for now-retired pins and allow historical intermediate current values — final-current liveness follows valid post-retirement history, not filtering ledger events; skipping historical events would change ordering — Cost: incomplete history can temporarily name a retired pair; valid histories end at their mounted successor. Revision: design 99eabaa §5.6, approved plan 8937235 Task 6.

Task 6: fix round 1/5 (1 addressed, 0 open — shared ledger reader; commits 5353077..ad6e9eb). Scoped reviewer /root/rereview6 codex/gpt-6.1-sol; task-6-fix-1-review-report.md.
Task 6: complete (commits 2beccd7..ad6e9eb, review clean after correction; 23 original focused +102 fast, fix 45 focused +129 fast pass).
Task 7: BASE eeed8b64923b1a0a27c63b4bcc8381b16ff50239; fresh implementer next.
Task 7: Ruling: explicitly expand stored.RETRACTS relation targets beside closure_missing — real fixture RED showed retracts is absent from WORLD_RELATIONS, despite builder emission; this realizes design §5.7 correction-target requirement without inventing a correction facet schema or using a private decoder — Cost: if kernel target encoding later changes, this surface adapter must follow it; real node/route target tests cover current contract. Revision: approved plan 8937235 Task 7; design 99eabaa §5.7. Earlier assumption that closure_missing already followed retracts was disproven before GREEN.

Task 7: complete (commits eeed8b6..e0272e6, review clean; 14 focused +14 fast pass). Reviewer /root/review7 codex/gpt-6.1-sol; task-7-review-report.md.
Task 8: BASE 422d2dfc00d6d1dd8c0073fb72ba8092fcfcc424; fresh implementer next.

Task 8: Ruling: keep reusable ledger-derived grouping in supersession.py and current live-root/profile collection in config.py — this reuses Mount/profile rules while keeping retention pure and lets show share the same inputs without a new orchestration layer — Cost: later consumers must distinguish live mounts from frozen session read mounts. Revision: approved plan 8937235 Tasks 8–9; Task 8 controller direction and implementation report.

Task 8: complete (commits 422d2df..0a44cc6, review clean; 71 focused +4 xfails, 707 fast +5 xfails). Reviewer /root/review8 codex/gpt-6-astra; task-8-review-report.md. Four integration xfails activate in Task 11; one retirement xfail stays for Task 13.
Task 9: BASE fc952be23d39f33ec4ffc88fa5191eca3a3e0530; fresh implementer /root/task9 next.

Task 9: Ruling: omit supersession when no authorized established group exists; an unresolved group shows its missing-link explanation and no pending-door retention claim, while kernel-retired status still reports retired — there is no authoritative current for a first fetched/unconfirmed pin, and design §5.6–5.7 permits retirement evaluation only for resolved groups — Cost: unresolved groups do not enumerate provisional retention reasons, but naming the link preserves the actionable blocker. Revision: plan 8937235 Task 9; design 99eabaa §5.6–5.8; controller Task 9 direction.

Task 9: Ruling: collect all registry pin roots in live_mounts and let the existing kernel-admission/liveness filter select inputs — a mounted ledger line can precede the pin projection, leaving its file fetched while show already folds it as established; pin-state filtering omits a live holder — Cost: fetched roots are considered before filtering, so the regression must retain exclusion of unadmitted fetched pins. Revision: Task 8 implementation 7f5a2d7; Task 9 integration against fc952be; design 99eabaa ledger-derived show/current and reads-by-root contract.

Task 9: Ruling: regenerate committed adopt/show prompt derivatives with the existing adapter generator, without changing adapter APIs, generator code or declarations — test_adapters.py:19–23 requires generated output to equal the committed tree; the plan’s adapters-untouched constraint conflicts with its required prompt changes if applied to generated content — Cost: generated adapter files change beyond the listed task files; focused equality verification and diff inspection constrain the change. Revision: plan 8937235 Global Constraints and Tasks 8–9; Task 8 prompt 7f5a2d7; Task 9 fast RED 1 failed,44 passed,3 xfailed.

Task 9: Ruling: cross-destination unlinked annotation takes precedence over tip for either pin — each destination can resolve independently while cross-chain attribution remains ambiguous — Cost: the this-pin row foregrounds the limitation over the otherwise true tip designation. Revision: design 99eabaa §5.6; Task 9 report/controller confirmation.
Task 9: Ruling: require explicit retired registry evidence rather than terminal liveness booleans for retired: yes — departed shares known/live booleans but is not retirement — Cost: show reads the existing registry to distinguish them. Revision: design 99eabaa §5.8; existing adopt reconcile contract; Task 9 report.

Task 9: complete (commits fc952be..0d51b71, review clean; 22 focused +3 xfails,11 adapters pass; fast44 passed/1 failed/3 xfails then generated derivative fix and final1 selected pass). Reviewer /root/review9 codex/gpt-6.1-sol; task-9-review-report.md.
Task 10: BASE 5ed330cfec985b63b476e15b8b700d93f0453ee3; fresh implementer /root/task10 next.

Integration preflight: main is clean at 7d86976 and contains an independent baseline correction, 065ae81 (sci-0bc09c), plus its task records, not yet in commons-1b. It edits test_two_corpora.py, overlapping Tasks 1/3’s equal-holder tests. Before Task 11 implementation, merge main into this worktree and preserve all distinct cases: equal-copy belief/queue, unequal unselected refusal, missing selected address, main’s unequal selected refusal and equal selected existing-record success. Use one fixture helper shape and review the resolved delta; the full gate will run on the combined tree. No main changes by this session yet.

Task 10: Ruling: guard every explicitly nonlive session corpus, including departed corpora and resumed publication — Task 10 specifies live is False for every session id, not a retirement-only or selection-only check — Cost: corpus-retired names all such nonlive statuses and reopening is required before token/destination validation. Revision: plan 8937235 Task 10; design 99eabaa §5.7–5.8.
Task 10: Ruling: narrow the resume regression trap to ownership recomputation and add frozen selection snapshot equality — the required liveness check legitimately reads mounts through session_ids, while resume must reuse frozen selection/attribution — Cost: the test no longer forbids unrelated mount reads; ownership recomputation and frozen-state drift remain checked. Revision: Task 10 base 5ed330c and controller confirmation.
Task 10: Ruling: prove the real unlinked-destination case now and defer only missing late-link fixtures — the existing conflicting-publication fixture already mounts both destination chains — Cost: full missing-link kernel-to-surface integration remains under strict xfail until Task 11; parsed ancestry tests cover the formatter meanwhile. Revision: plan 8937235 Tasks 10–11; controller Task 10 assignment.

Task 10: complete (commits 5ed330c..7b29319, review clean; 31 focused +2 xfails,118 fast +2 xfails). Reviewer /root/review10 codex/gpt-6.1-sol; task-10-review-report.md.
Task 11: BASE 291f250512799e153cef950c125646bfa686b869; fresh implementer /root/task11 next; includes main integration preflight above.

Task 11: complete (commits 291f250..3c352c3, review clean; main merge 2f4b5b4; 16 focused+16 fast merge checks,105 focused+1 xfail,2 strengthened,1047 fast+1 xfail). Nine deferred integration gates now active; only Task 13 retirement remains xfail. Reviewer /root/review11 codex/gpt-6-astra; task-11-review-report.md.
Task 12: BASE 65f629f720fd4b78624b2a55ccc30a5f827e6db9; fresh implementer /root/task12 next.

Task 12: Ruling: retain the accepted narrow historical sidecar exception — commentary cannot enter the kernel close outcome, while dispatcher reports must preserve complete ledger pin evidence — Cost: exact historical replay needs the sidecar retained beside the ledger; its loss stales old cursors without losing effects. Revision: plan 8937235 round-5 ruling; Task 8 implementation 7f5a2d7; docs bc7c3ab.
Task 12: Ruling: document implemented overlap separately from intended retirement — implementation a1b0ac8 and active integration gates establish only the first phase — Cost: unrequired predecessors remain mounted until the scoped door lands. Revision: design 99eabaa §7; plan 8937235 Tasks 12–15; docs bc7c3ab.
Task 12: Ruling: use the required normal full just gate instead of a redundant selected testmon run for docs-only work — controller direction and Task 12 Step 2 require the complete suite, which covered all 1048 cases — Cost: no additional incremental testmon timing sample. Revision: plan 8937235 Task 12; full gate 1047 passed,1 expected xfail.

Task 12: complete (commits 65f629f..511838d, review clean; full just gate 1048 collected,1047 passed,1 expected retirement xfail,177.22s; follow-up just check passes). Reviewer /root/review12 codex/gpt-6.1-sol; task-12-review-report.md.

Overlap whole-branch review: BASE current main/merge-base 7d86976488160fcf2c4724aa75bd4cd63d7e396a; HEAD 894d169a3fccd8aa739cd00300284577b5d38bec. Main was integrated by Task 11, so this range reviews the actual remaining local-merge delta. Parent impl review round 1 next; existing parent reviews are spec/plan only.

Overlap whole-branch review round 1: revise, Important 2 (duplicate verification counts in show; unavailable unadmitted fetched root read before live filtering), Minor 1 (show unknown-keep warning absent). Reviewer /root/final_review codex/gpt-6-astra; final-review-report.md.
Final review: minor (deferred): show omits Review Focus 1’s Finding for configured keep IDs with no pin; adopt already warns. Small explicit plan omission, no retirement in this phase. Track under open sci-9104fb; final-review-report.md finding3. Existing testmon survey banner stays minor (deferred), no regrade.
Overlap corrective round 1/5: one fix agent will reopen sci-d5954d and correct both Important findings, with RED→GREEN and green suite; FIX_BASE 894d169a3fccd8aa739cd00300284577b5d38bec. Minor findings do not enter the round.

Final review scope Ruling: keep actual retirement, idempotent retirement recovery and full post-retirement integration in Tasks 13–15 — their scoped kernel door is absent and the approved plan explicitly splits the phases — Cost: unrequired predecessors remain mounted and those paths remain unverified until beliefs-a989fb lands. Revision: plan 8937235 Tasks 13–15; design 99eabaa §7; final-review-report.md declined item1.
Final review scope Ruling: retain the accepted same-second cross-session ordering, unlinked-destination publication and vocabulary-binding limits — these are explicit approved design choices, not promises of this implementation — Cost: unresolved current can follow session-ID order, differently attributed records can be unpublishable while both chains mount, and vocabulary bindings do not retain dependencies. Revision: design 99eabaa §5.6–5.7 and acceptance record; final-review-report.md declined item2.
Final review scope Ruling: leave remaining acceptance snapshot consistency, first-assessment summary and reconcile-predicate work with sci-cf4d58, but fix the distinct duplicate-verification count now — the task body and design §9 explicitly sequence those existing follow-ups after this branch — Cost: those existing snapshot/summary discrepancies persist until that task runs. Revision: sci-cf4d58 scoped record 2026-10-24; design 99eabaa §5.4/§9; final-review-report.md declined item3.
Final review scope Ruling: leave re-fetch identity and immutable ledger-evidence validation with sci-347a36 — the read task record and design §9 explicitly retain and sequence that separate work — Cost: existing replacement-evidence mismatch risk remains until its fix. Revision: sci-347a36 scoped record 2026-10-24; design 99eabaa §3/§9; final-review-report.md declined item4.
Final review scope Ruling: do not certify own-publication adoption or mixed retained-v1/new-v2 epoch migration in this phase — design §3 excludes the own-world sourcing route until milestone2, and §5.5 retains existing v1 epochs without a mixed-world science fixture — Cost: those routes and mixed-world integration remain unverified here; existing epochs remain on v1 until rebuilt. Revision: design 99eabaa §3/§5.5; final-review-report.md declined item5.

Final fix 1 Ruling: group verification copies by address plus kernel content identity and retain every holder — equal records count once when any holder qualifies, without address-only conflation — Cost: conflicting copies present through bypassed admission are reported separately rather than concealed; admission remains the conflict gate. Revision: final review Important1 over 894d169; correction fac6b909.
Final fix 1 Ruling: filter registry roots by pin corpus ID admission/liveness before manifest access, preserving admitted/fetched crash recovery — an unavailable unadmitted candidate cannot obstruct unrelated live operations — Cost: excluded copies are validated when actually adopted, not on unrelated reads; configured/admitted roots still validate. Revision: final review Important2 over 894d169; correction fac6b909. This supersedes Task9’s accepted cost of inspecting every registry root.

Overlap final fix round 1/5: 2 addressed,0 open (verification count aggregation; kernel filter before unadmitted manifest read), correction fac6b909, reviewed commits 894d169..fe37a95. Fresh scoped review /root/final_rereview1 codex/gpt-6.1-sol; final-fix-1-review-report.md. Parent impl round2 accept, no new findings. Full gate 1054 collected,1053 passed,1 expected retirement xfail,175.00s. Both retained minors remain deferred. Overlap is ready for local integration; retirement tail remains pending.

Local integration complete: main fast-forwarded to b07e761635ee5c39a05956059e8a721157172709; main just check passed, and tracked code/docs match verified correction fac6b909 (only later task metadata differs). No push. Worktree and this plan workspace are retained for the open retirement tail owned by sci-9104fb; after beliefs-a989fb lands, agent verifies the retained manifest, revises Tasks 13–15 interfaces against the merged kernel design, and resumes sci-9c0bba here. Both listed minors remain deferred under the parent.
