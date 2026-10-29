Reviewer: /root/final_rereview1 — codex/gpt-6.1-sol

- **Important 1 — duplicate verification counts: ADDRESSED.** `.worktrees/commons-1b/python/src/science/commands/show.py:52` groups copies by address and the kernel’s parsed content identity while retaining every holder. Lines 64–68 preserve all provenance worlds, report each equal record once, and count it when any holder qualifies. Differing contents remain separate. Regression cases at `.worktrees/commons-1b/python/tests/test_cmd_show.py:91` cover both holders accepted, only the later holder accepted, neither accepted, and differing content at the same address.

- **Important 2 — unavailable unadmitted roots obstruct unrelated operations: ADDRESSED.** `.worktrees/commons-1b/python/src/science/config.py:372` filters registry roots using the pin’s known corpus ID and authoritative admission/liveness before manifest access. Explicitly configured roots still undergo manifest reads; admitted/live registry roots remain validated regardless of projected pin state. Tests at `.worktrees/commons-1b/python/tests/test_cmd_show.py:303` prove unavailable unadmitted exclusion and admitted/fetched inclusion; line 318 verifies an unreadable admitted root still refuses. `.worktrees/commons-1b/python/tests/test_cmd_adopt.py:103` proves another publication can be successfully adopted while the unavailable candidate remains fetched and unadmitted.

- **New breakage in the fix diff: None identified at Critical, Important, or Minor severity.** The changed aggregation preserves holder-qualified acceptance, and the root filter preserves admission-crash recovery. Existing admission-before-pin-write and mounted-line replay regressions passed in the recorded focused run.

- **Out-of-scope observations: None newly identified.** The previous review’s Minor 3 and previously deferred survey-banner minor remain outside this corrective review; this verdict does not resolve them.

- **Verification:** Read the frozen `894d169..fe37a95` diff once, the original brief/report, global constraints, correction report, connected acceptance logic and kernel identity implementation. Inspected recorded failure output confirming duplicate totals and missing-manifest refusal, followed by **8 targeted passes**, **88 focused passes + 1 xfail**, **78 fast passes + 1 xfail**, and the normal full gate’s **1,053 passes + 1 xfail / 1,054 collected**, **175.00 seconds**, **16 workers**. The focused output identifies the remaining xfail as actual retirement.

- **Reviewer identity:** `codex/gpt-6.1-sol`, freshly verified with `timeout 2 relay model --harness codex --pretty`.

- **Fix round: All findings addressed, no new Critical/Important breakage.** The controller can record acceptance of this corrective round and continue integration under the governing workflow. Review remained read-only; nothing was pushed or merged, and no checks remain running. Branch `commons-1b` remains in `.worktrees/commons-1b` for controller integration.

- **Limits:** Skipped redundant test execution and performance benchmarking; conclusions use code inspection and recorded test evidence. Actual retirement remains blocked as planned and is not certified by this review.
