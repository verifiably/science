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

## Task 13 resumption (2026-10-29)
Retained overlap manifest and all 137 files verified before use. Existing branch fast-forwarded to main 7a49152; task claimed and trial-arm reports not enrolled. Human source session f666f956-1928-4c06-8bf1-80cd5a586d90 turn 1814 confirms approved plan and sequential execution.
Task 13 preflight: shipped root/observers/evidence API agrees with evidence binding; any-actor recovery returns already-retired and folds by transition. Plan interface amended at 08efbbf. Task 13/show/commons tests share the unkept builder and must change together; Task 14 owns additional safety gates, Task 15 the document amendments.
Ruling: execute only requested Task 13 and retain its branch for Tasks 14–15 before phase integration — the user selected sci-9c0bba, and design section 5.7 explicitly forbids shipping retirement before the spec-drop and spec-only gates — Cost: Task 13 is complete only on the retained branch until the remaining tail is verified and reviewed. Revision: user request 2026-10-29; plan 08efbbf Tasks 13–15; design 99eabaa section 5.7.
Ruling: use the shipped root/observers/evidence signature and any-actor recovery instead of the provisional corpus-ID-only signature — the approved plan requires this substitution against the merged kernel design — Cost: retirement requires the retained root and head artifact to remain readable. Revision: plan 08efbbf; beliefs f274822, retirement-door design section 6.

Task 13: BASE 02f784e5eba56194b22cc166d9f5c69d74928ee4; implementer /root/task13 (gpt-6.1-sol high), reads only until controller confirms baseline.

Task 13 Setup baseline: just test exit 0, 1053 passed and 1 expected xfailed (1054 collected), 261.07s. Log task-13-baseline.log. Implementer notified to proceed.

Task 13 Ruling: change show's obsolete pending/no-door result to pending/rerun-adopt and test the lagging mounted state — after this implementation the door exists, while read-only show can still encounter pre-tail pending retirement — Cost: the pending report text changes; callers must use the new actionable remedy. Revision: plan 08efbbf Task 13 connected show expectation; design 99eabaa sections 5.7–5.8.

Task 13 Ruling: drain the real cursor pages and exclude all registry-managed pin roots in fixture configuration — active retirement exposed a first-page-only assertion and promotion of retired automatic mounts to explicit configuration — Cost: the report assertion spans pages, and fixture serialization recognizes retired as well as mounted pins. Revision: bb1fad5; task-13-green.log initial 81-test run; controller scope confirmation.
Task 13: complete (commits 02f784e..bb1fad5, independent review clean; focused GREEN 7 passed, final affected suite 87 passed). Reviewer /root/review13, codex/gpt-6.1-sol; full returned text task-13-review-report.md. Self-review impl round1 and independent impl round2 both accept with no findings. No new deferred minors. Existing parent minors remain tracked under sci-7315fb and the historical overlap ledger.
Task 13 final state: branch commons-1b remains unmerged. Next agent resumes Task14 sci-9da5a6 in this worktree, then Task15 sci-50d0c2 and whole-tail review before local integration. Current user request is complete; no remaining check or child is running. Retirement-target refusal after recovery is retained per existing target-state contract; recovered evidence can persist before that refusal, as independently reviewed.

## Task 14 resumption (2026-10-29, claude-code/claude-opus-5-5 controller)
task-13-evidence-manifest.json sha256 83d2bd4f… matches the retained note; all 151 files verified. Controller claim on sci-9104fb; trial-arm not enrolled. No .tt.toml: suite policy enabled. Branch commons-1b = main 7a49152 + 27 commits.
Ruling: user asked for sci-9c0bba, already done and reviewed at bb1fad5; proceed to the parent's recorded next step (Task 14 sci-9da5a6, then Task 15, then whole-tail review) instead of repeating Task 13 — the park's next step names it and the tail cannot merge without it — Cost: if the user meant something else, one correction and no code lost.
Ruling: global-constraints.md predates the door; hand reviewers the plan's current Global Constraints (door landed at f274822) — Cost: none beyond a stale scratch file.
Ruling: Task 14 gates run through real commands over fixture builders; a monkeypatched unit test of the same decision does not satisfy a gate, while an existing fixture-level test that already asserts a gate counts and is cited rather than duplicated. A gate that exposes a source defect is fixed minimally in source with RED→GREEN and flagged; a design question stops the implementer with NEEDS_CONTEXT — Cost: a source fix widens Task 14 beyond tests; review checks it against the design.
Task 14: BASE 0ca4934c6af1e0ee5be00f9b93680f6c0f038ccd; implementer dispatched (claude-code opus).
Task 14 implementer: claude-code opus (agent a9fcd46982c49db66), background.
Task 14 implementer report: DONE, 320f9e3 test-only (11 new tests/13 cases, 3 extended); focused 94 passed 461s; just test-fast 1069 passed 305s; mutation evidence task-14-mutations.log. Self-flagged concerns: post-retirement sibling does not isolate P1's retired copy as necessary; chain retention by verification uses P1→P3→P4, not the late chain. Task review dispatched (claude-code opus, agent a82f5b1080e0aa4c3) over review-0ca4934..320f9e3.diff.
Task 14 review round 1: accept, Critical 0, Important 0, Minor 5; reviewer claude-code/claude-opus-5-5; task-14-review-report.md.
Task 14: minor (deferred): duplicate `_show` helper in test_commons_1b.py:35 (same as test_cmd_show.py:25), and inline show invocation at :164.
Task 14: minor (deferred): two ledger readers for retired lines (`_retired_lines` vs `_sharing_lines` filter).
Task 14: minor (deferred): post-retirement sibling gate cannot isolate that P1's retired copy (not named ancestry alone) drives divergence; would need a hand-built marker.
Task 14: minor (deferred): requirement-before-sweep builds reader C inline every run (not snapshot-cached).
Task 14: minor (deferred): write-guard, late-link and sibling gates lack a mutation fail-demonstration (assertions are exact).
Task 14: complete (commits 0ca4934..320f9e3, review clean; 5 minors deferred).

Task 15: BASE 839e42d37d585ec3679ec1007acea50a933185a5.
Ruling: Task 15 also amends the other documents that still state the retirement tail is pending — commons §11's door row (design §6 lists §11) and the framework design's §4.4 sentence Task 12 wrote — and show's prompt, whose `pending: no door` text Task 13 already replaced in code with `pending: rerun adopt` — leaving them would ship documents contradicting the merged behaviour — Cost: a slightly wider docs diff than the plan's step names. The 1b design's own §5.7/§5.9/§7 interim prose stays as decision record; only its status changes.
Task 15 implementer dispatched (claude-code sonnet).
Task 15 implementer report: DONE, 240907e; just gate exit 0, 1069 collected/passed, 0 xfail, 279.84s (first two runs failed only test_adapters until generated skills rebuilt with science adapters build). Review dispatched (claude-code sonnet) over review-839e42d..240907e.diff.
Task 15 review round 1: accept, Critical 0, Important 0, Minor 6; reviewer claude-code/claude-sonnet-5-5; task-15-review-report.md.
Task 15: minor (deferred): framework design 371-374 and commons Task 12 §11 sentences still read "pending" in isolation, superseded only by the adjacent dated amendment.
Task 15: minor (deferred): stray hard line break after "by another route." in framework design 371-374.
Task 15: minor (deferred): adopt prompt (and generated SKILL.md) overlong/uneven lines around the config-stale sentence.
Task 15: minor (deferred): show prompt (and generated SKILL.md) overlong line "retiring it); `adopt` retires it…".
Task 15: minor (deferred): commons §12 amendment inserted mid-paragraph before "A binds B…".
Task 15: minor (deferred): commons §10 amendment is one very long paragraph.
Task 15: complete (commits 839e42d..240907e, review clean; 6 minors deferred).
Tail whole-branch review: BASE 7a49152 (main), HEAD 6779b0c; dispatched claude-code opus.
Tail whole-branch review round 1: With fixes — Critical 0, Important 1 (no gate for the sequential sweep's per-iteration live_mounts: hoisting it would retire both equal holders of a depended-on record, irreversibly), Minor 5. Reviewer claude-code/claude-opus-5-5; tail-final-review-report.md. Deferred-minor triage: none of Tasks 13–15's minors re-graded.
Tail final review: minor (deferred): lag state (mounted pin over kernel-retired corpus) — corpus-retired remedy "reopen the session" loops; only adopt reconciles; show gives no remedy. Rare, recoverable. Follow-up task to be filed.
Tail final review: minor (deferred): reconcile retiring the requested target refuses with "already adopted: its pin is retired" (reads as success) and the refused invocation drops every reconciled retirement block. Follow-up task to be filed (with the lag-state remedy).
Tail final review: minor (deferred): show judges each pending predecessor alone while adopt sweeps sequentially; two equal holders both show pending: rerun adopt.
Tail final review: minor (deferred → integration bookkeeping): docs say "on branch commons-1b … pending local integration"; rewritten in the integration commit per the docs-when-work-lands rule, together with Task 15's isolated "pending" sentences.
Tail final review: minor (deferred): reconcile's retirement block prints the current keep list though nothing was evaluated.
Tail corrective round 1/5: one fix agent reopens sci-9da5a6 and adds the equal-holder sequential-sweep gate with the hoist mutation as RED; FIX_BASE 6779b0c. Minors do not enter the round.
Tail final review minors 1–2 (lag-state remedy; target-retired refusal dropping reconciled blocks) filed as sci-4b5ec4 (P3, s, mid, direct). Minors 3 and 5 stay deferred in this ledger; minor 4 is integration bookkeeping.
Tail fix round 1: fix agent DONE 1339976 (test-only gate; hoist mutation RED 1 failed, GREEN 1 passed; test_commons_1b 21 passed; just test-fast 1070 passed 405s); tail-fix-1-report.md. Scoped re-review dispatched (claude-code sonnet).
Tail corrective round 1/5: 1 addressed, 0 open (equal-holder sweep gate 1339976); scoped re-review claude-code/claude-sonnet-5-5 accept, no new breakage; tail-fix-1-review-report.md. Tail ready for integration bookkeeping and local merge.
Integration bookkeeping 81bf98f (status wording: commons §10/§11/§12, 1b design status, plan status; framework stray line break from Task 15 minor 2 folded in). main had advanced by df38eab (vendored tt v8, tools/tt only); merged into commons-1b at 775ec0f. Merge gate just gate running (log tail-merge-gate.log).
