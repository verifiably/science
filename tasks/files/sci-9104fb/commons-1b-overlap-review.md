Reviewer: /root/final_review — codex/gpt-6-astra

The overlap phase of sci-9104fb needs two corrections before merging: `show` double-counts overlapping verification copies, and an unavailable fetched-only corpus can block unrelated adoption. The controller owns the correction round. Retirement remains intentionally blocked under Tasks 13–15.

Reviewed range: `7d86976488160fcf2c4724aa75bd4cd63d7e396a..894d169a3fccd8aa739cd00300284577b5d38bec`, against accepted plan `8937235`, design `99eabaa`, current amendments, task/source records, and the execution ledger.

Reviewer identity: **codex/gpt-6-astra**, freshly verified by `timeout 2 relay model --harness codex --pretty`.

**Strengths**

- Admission, holder resolution, and Carried acceptance consistently use the kernel’s parsed content identity.
- Supersession uses exact corpus/marker pairs, preserves named missing ancestry, and rejects sibling branches before admission. Tests cover siblings without a held predecessor and a sibling pair beside a disconnected tip.
- Retention follows the extra stored references needed for verification and analysis replay, using each holder’s profile. The real update fixture proves that the dropped assessment remains readable.
- Sharing reports preserve every ledger pin block and persist historical commentary separately. Fault tests cover serialization, replacement, directory-sync failures, missing sidecars, replay, and continuation through a fresh dispatcher.
- Documentation distinguishes implemented overlap from intended retirement. No alternate retirement route was introduced.

**Critical findings**

None.

**Important findings**

1. **`show` reports duplicate copies as additional counting verifications.**

   Files: `.worktrees/commons-1b/python/src/science/commands/show.py:44`, especially lines 54 and 64–66.

   `_verifications` appends one entry per holder. `_evidence` then counts those entries, including accepted entries, without deduplicating the verification record. If two accepted publication revisions contain the same verification, `show` reports two verifications and says both count under the policy. The kernel’s overlap semantics count that record once.

   A completed read-only reproduction passed the same real `stored.verification_node` through two in-memory publication mounts with accepted pins. The existing helper returned:

   ```text
   verifications 2 from worlds bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb, 2 count under the policy
   ```

   This overstates the evidence supporting an assessment precisely when the user adopts overlapping revisions. The existing sci-cf4d58 follow-up covers other `show` issues, not duplicate verification totals.

   **Fix:** Aggregate equal copies by verification record identity, retaining their holders for policy decisions. Count the record once when any holder qualifies. Add a regression covering two equal accepted copies and a case where only one copy qualifies.

2. **A missing fetched-only root blocks unrelated adoption and retention reporting.**

   File: `.worktrees/commons-1b/python/src/science/config.py:371`.

   `live_mounts` adds every registry pin’s root, reads every manifest at line 373, and only then filters for kernel admission and liveness. A rejected candidate may remain `fetched`; if its copy subsequently disappears or becomes unreadable, another valid adoption now refuses while inspecting that unrelated, unadmitted root. `show` also reaches this helper when reporting a superseded pin’s retention.

   A completed read-only reproduction supplied one fetched pin with an absent root and an empty kernel admissions set. Instead of returning no live mounts, the helper raised `invalid-input` for that root’s missing manifest. The previous adoption checklist excluded fetched-only pins.

   **Fix:** Use the registry pin’s known corpus ID to filter registry roots by kernel admission and liveness before opening their manifests. Preserve validation of admitted live roots, including pins whose files still say `fetched` after an admission crash. Extend the existing regression at `.worktrees/commons-1b/python/tests/test_cmd_show.py:261` with an unavailable, unadmitted fetched root and an unrelated successful adoption.

**Minor findings**

3. **`show` omits the planned warning for unpinned `keep` entries.**

   File: `.worktrees/commons-1b/python/src/science/commands/show.py:135`.

   The accepted plan’s **Review Focus 1** requires both `adopt` and `show` to report a configured `keep` ID with no pin. `adopt` implements this at `.worktrees/commons-1b/python/src/science/commands/adopt.py:168`; `show` only renders whether its requested pin is kept.

   A user inspecting retention after editing configuration receives no warning about a mistyped entry elsewhere in `keep`. This is a small, explicit plan omission; actual retirement is absent in this phase.

   **Fix:** Append the same unknown-entry Finding during `show`, with a focused regression. Keep accepting unpinned IDs in configuration because predeclaring a future adoption is supported.

The existing Task 1 testmon survey-banner minor remains **minor and deferred**. It affects test-log noise, with no demonstrated consequence for runtime behavior or verification validity; no regrade is warranted.

**Checks and limits**

- Reviewed the production delta, connected callers, graph/retention/report tests, overlap integration fixtures, documentation amendments, and recorded task evidence.
- Verified the recorded normal `just gate`: exit **0**, **1,048 collected; 1,047 passed and 1 expected xfail**, **177.22 seconds**, twelve workers. The remaining strict xfail concerns Task 13’s actual retirements.
- Ran the two small read-only reproductions described above. They confirm helper behavior; they are not full command integration tests.
- `git diff --check` passed. The worktree remained clean.
- Assumed the documented local installation workload. No large-corpus performance benchmark was run.

**Declined to judge**

- Actual retirement, idempotent retirement recovery, and full post-retirement integration: explicitly reserved for Tasks 13–15 after beliefs-a989fb supplies the scoped door.
- The accepted same-second cross-session ordering limitation, unlinked-destination publication restriction, and omission of vocabulary bindings from dependency edges: documented design decisions, not claimed solved by this phase.
- Existing acceptance snapshot consistency, first-assessment summary, and reconciliation-predicate cleanup: separately tracked in sci-cf4d58. The new duplicate-verification finding above is distinct.
- Existing re-fetch identity and immutable ledger-evidence validation: separately tracked in sci-347a36 and explicitly sequenced after this phase.
- Own-publication adoption through a future sourcing route and migration of retained v1 epochs: outside this phase’s approved routes; this review does not certify those scenarios.

**Ready to merge the overlap phase? No—fix Important findings 1 and 2 first.** The principal overlap implementation and recovery tests are strong, but the evidence report must not exaggerate verification counts, and an unadmitted failed candidate must not obstruct unrelated live work.

No files, task notes, branch state, or reports were changed; nothing was pushed or merged, and no checks remain running. The branch remains in `.worktrees/commons-1b` for controller correction, scoped re-review, and subsequent local integration.

Skipped rerunning the already-proven full suite. Actual retirement remains unimplemented and blocked as planned.
