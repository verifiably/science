# Retirement-tail whole-branch review (round 1)

Reviewer: claude-code/claude-opus-5-5; range 7a49152..6779b0c (code and docs, task records excluded).

### Strengths

- The source change is small and does what the plan asks. `_retire` (`python/src/science/commands/adopt.py:207-215`) passes the registry root, observers built from the retained head artifact, and the pin's own evidence, the same way admission does. It records the line only after the kernel returns it, so the registry is written only after its ledger evidence, as AGENTS.md requires. Head artifacts have been kept since 1a's adopt (628b38e), so a pin adopted under 1a can still be retired.
- Moving `live_mounts` into the predecessor loop (`adopt.py:182`) is correct, and it matters. I traced P1→P2→P3 where P1 and P2 both hold a record B depends on. After P1 is retired, P2 becomes the only holder and is kept by dependency. The stale `held` snapshot does no harm: `direct()` of a just-retired corpus finds no view in `holders` and no `keep` entry, so chain retention cannot pick it up.
- Each crash window is closed by the next `adopt`:
  - **Status written, line lost** (door decision 6): reconcile calls the door, which ledgers `already-retired` without writing a second status record. Tested.
  - **Line written, pin file stale:** `replay` at step 1 repairs it. Tested at `test_cmd_adopt.py:322`.
  - **Flushed but unacknowledged `retired` line plus a later `already-retired` line:** `apply_line` folds both to `retired` without error.
- The step order matches §5.7: reconcile, then the candidate, then the sweep. Inside the sweep, the required set is computed first, then `config-stale` is checked, then the door is called. The check runs before every new retirement, and reconcile (which only records completed effects) is correctly not gated.
- The §5.9 gates run through real commands. The keep, stale-config, chain, retired-chain and attribution gates have mutation evidence in `task-14-mutations.log`. The write-guard gate checks exact refusal data and that the write view is unchanged.

### Issues

#### Critical (Must Fix)
None.

#### Important (Should Fix)

1. **No gate covers the sequential sweep's equal-holder rule, which protects against irreversible loss** (`adopt.py:182`; tests missing).
   - **What's wrong:** Task 13 moved `mounts = live_mounts(...)` from before the loop to inside it, and the result is correct. But no test or mutation fails if the call is hoisted back out. The previous code had it hoisted, so the likely refactor is the regression.
   - **Why it matters:** with mounts hoisted, two equal-content holders of a record the reader depends on are both judged unrequired and both retired in one `adopt`. Retirement is irreversible: B's verification loses its holder, and P1 cannot be readmitted.
   - **The scenario is realistic:** it is the late-link arrival with a dependency. B holds P1 and has verified A's assessment. A publishes P2, which keeps the assessment, then P3, which drops it. B adopts P3, then P2.
   - **Fix:** add one gate from the `verified` base. Use `publish_again` for P2 and `_publish_update(..., ("proposition","dataset","spec","run"))` for P3. Adopt P3, then P2. Assert that exactly one of P1/P2 is retired (P1 under the current order), that the other reports `kept: dependency (<assessment>)`, and that B's `verify` still succeeds. Add the hoist to the mutation log.

#### Minor (Nice to Have)

1. **In the lag state, the stated remedy loops and `adopt` is never named** (`config.py:248`, `sharing.py:238`, `config.py:549-555`, `publication.py:88-92`).
   - **The lag state:** a `mounted` pin over a kernel-retired corpus. It exists in two crash windows (status written but line lost; line written but pin file stale), and also after a reconcile door refusal (`adopt.py:119-120`).
   - **What happens:** `load_config` mounts by pin state alone and never replays, so the next open mounts the retired corpus again. Citing writes and publish then refuse `corpus-retired ... reopen the session`, and reopening gives the same refusal. `science epoch` reaches the kernel's `CoverageNotLive`, which science does not normalize. `show` says `retired: yes` with no remedy. Only an `adopt` (of any corpus) repairs it.
   - **Status of the gap:** design §5.9's last paragraph assigned this window to the door to keep atomic. The door design instead chose recovery by the next call. The Task 15 amendments do not carry the consequence forward.
   - **Fix (small):** add "if it persists after reopening, run `adopt` to reconcile" to both `corpus-retired` messages and the `show` prompt. Or file a follow-up for the loader to replay or filter by kernel liveness.
   - **Severity:** rare, recoverable, no data loss.

2. **When reconcile retires the requested target, the user gets a misleading refusal and loses the report** (`adopt.py:55`).
   - **Is it what a reasonable user expects?** Mostly yes. The likely path is a user naming a retired predecessor to keep reading it, and refusing to re-adopt it is right.
   - **Two effects fall short:**
     - The wording "is already adopted: its pin is retired" reads as success.
     - The dispatcher closes a refused sharing invocation without pin blocks, so every retirement reconcile recorded in that invocation, not just the target's, goes unreported. That includes the reopen remedy.
   - **Conflict with the design:** the second effect sits uneasily with §5.7's "refuses `already adopted` only when it wrote nothing".
   - **Fix:** when `lines` is non-empty, return the tail, which carries the retired blocks, plus a Finding that the target is retired and is not re-adopted. Otherwise, at least reword the message ("corpus X is retired; a retired publication is not re-adopted").
   - **Test gap:** the limit is documented in commons §10 but has no test.

3. **`show` judges each predecessor in isolation, but `adopt` sweeps them in sequence** (`show.py:107-129`). In the pending state, two equal holders both show `pending: rerun adopt`, yet rerunning `adopt` keeps the second by dependency. This happens only in the interim and errs toward caution. Possible wording: "pending: rerun adopt (evaluated alone)", or note it in the prompt.

4. **Committed docs will be wrong as soon as the branch merges** (commons §10, §10.3, §12 amendments; 1b design status; plan status paragraph). They say "on branch `commons-1b` … pending local integration" and "the whole-tail review and the local merge are still to come". Fix them in the integration commit, per the global rule to update docs when work lands.

5. **Reconcile's retirement block can print a `keep` list that contradicts it** (`adopt.py:214`). The block prints the current `keep` list as if it had been evaluated, but nothing was evaluated: the kernel had already retired the corpus. It can read `retirement X: keep: ['X']`. Cosmetic.

### Deferred-minor triage

- **Task 14** (duplicate `_show` helper; two ledger readers; requirement-before-sweep fixture built inline; missing mutation demonstrations for the write-guard, late-link and sibling gates): all test hygiene. Keep them deferred. The missing mutation demonstrations become moot for the sweep rule once Important 1 adds a gate.
- **Task 14, sibling gate cannot isolate the retired copy from named ancestry:** keep deferred. Either path gives the user the same `divergent-publication` refusal and leaves the sibling `fetched`.
- **Task 15** (isolated "pending" sentences, a stray line break, overlong prompt lines, a mid-paragraph §12 insertion, a long §10 paragraph): formatting only. Keep deferred. The "pending" sentences overlap Minor 4 and can be folded into that integration-time edit. No re-grade.
- **Final review (overlap): `show` omits the Finding for a `keep` ID with no pin; testmon banner:** keep deferred.

No deferred minor needs fixing before merge.

### Declined to judge

- Refusing `config-stale` partway through a multi-retirement invocation after an earlier retirement committed: a TOCTOU window inherent to checking a file; per-retirement checking is the best available.
- A refusal from the door during the sweep (`StatusTerminal` in a race) aborting the invocation after the candidate was admitted: the kernel's single-writer rule makes the race out of scope.
- An unreadable head artifact or root raising an internal error in reconcile: fail-early by design, and the loader already refuses a mounted pin without a corpus.
- The candidate itself being retired in the invocation that mounted it (late-link P2): §5.7 states this explicitly.
- Python-repr rendering of `keep` (`['id']`): an existing convention shared with `config-stale`.
- The departed-before-door filter: correct by inspection; only two terminal statuses exist in the kernel.
- The fold of `current` over `retired` lines (only `mounted` lines are folded): the overlap half, reviewed earlier.
- The vocabulary-binding, same-second ordering and unlinked-destination limits: approved design rulings from the overlap review.
- Generated adapter skills: covered by `test_adapters` in the gate.
- The kernel door's internals at f274822: reviewed in beliefs; I checked only the interface science relies on.

### Recommendations

- Add the equal-holder sequential-sweep gate (Important 1) before merge. It is one test over existing helpers.
- At integration, rewrite the "pending local integration" statements (Minor 4).
- Fold Minors 1–2 into one small change (remedy text plus reporting recovered retirements), or file it as a follow-up under sci-9104fb.

### Assessment

**Ready to merge?** With fixes

**Reasoning:** The retirement wiring is correct, and every crash window closes at the next `adopt`. But the one invariant that stops a single `adopt` from irreversibly retiring both equal holders of a needed record has no gate, so add that test first. The rest is report and remedy polish plus doc dates to fix at merge.

reviewer: claude-code/claude-opus-5-5
