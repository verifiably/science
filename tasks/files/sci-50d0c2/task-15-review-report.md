# Task 15 review (impl round 1)

Reviewer: claude-code/claude-sonnet-5-5 (fresh subagent, read-only). Range 839e42d..240907e, package review-839e42d..240907e.diff.

### Spec Compliance
- ✅ Spec compliant. All five scoped amendment groups are present and dated in Task 12's style. The behavioural claims I checked match `adopt.py` and `show.py`.
- ⚠️ Cannot verify from the diff or the two files I read:
  - The `[pin] <corpus> retired` block text, which comes from the ledger line projection, not `adopt.py`.
  - "Even the already-mounted target" is retired. The code shape supports it: `_reevaluate` runs on the `already_mounted` path before the `not lines` refusal. I did not read the retry test.
  - The gate log and its 1069-passed result, which I took as given.

### Strengths
- The prompts describe the shipped behaviour:
  - Retirement goes through the door, and the report names the corpus.
  - Mounts stay as opened until reopen and `science epoch`.
  - `config-stale` is raised before retirement, in `_require_current_config` just before `_retire`.
  - `show`'s `pending: rerun adopt` is at `show.py:129`.
- The §10 amendment matches the code:
  - `_retire` takes the root from the registry, the observers from the retained head artifact, and `evidence=_evidence(pin)`.
  - Reconcile calls the door only when `status.known and not status.live`.
  - `departed` gives a Finding and never reaches the door.
  - Reconcile turns door refusals into a Finding, as the text says.
  - The stated limit is real. If reconcile retires the requested target, the pin is `retired` and `_already_adopted` raises `invalid-input` after the line persists.
- The interim prose in the 1b design §5.7, §5.9 and §7 is left as decision record, as the ruling required.
- The remaining grep hits are dispositioned correctly. Everything in `python/src`, `commands` and `adapters` is clean. The surviving hits are dated plan text, the 1b design's interim sections, the Task 12 amendments and false positives.
- The adapter `SKILL.md` files are regenerated and match their prompts.
- The report is candid: it says the first gate runs failed on stale adapter skills and that the plan commit id is deferred.

### Issues
#### Critical (Must Fix)
None.

#### Important (Should Fix)
None.

#### Minor (Nice to Have)
- `docs/specs/2026-08-31-command-framework-design.md:371-374` and `docs/specs/2026-09-30-science-commons-design.md` (Task 12 §11 paragraph, "remains a separate pending door… revise their provisional interfaces… before implementation"):
  - The ruling said to amend the sentence saying the door remains pending. Both sentences still read as current-state pending and are superseded only by the next dated paragraph.
  - It is in keeping with dated-record style and the superseding paragraph is adjacent. A reader of the single sentence could still be misled.
  - Fix: add "(superseded below)" or reword the sentence in place.
- `docs/specs/2026-08-31-command-framework-design.md:371-374`: the edit splits one paragraph by inserting a hard newline after "by another route." and shifts the following text. This is cosmetic; remove the stray break.
- `commands/adopt/prompt.md` (and the generated `SKILL.md`): the changed lines are uneven. One is about 100 characters, and the "Before retirement, a changed configuration file refuses `config-stale`: the adoption stands;" line is overlong against the file's wrapping. Rewrap.
- `commands/show/prompt.md` and its generated `SKILL.md`: the "retiring it); `adopt` retires it. An unresolved group…" line is overlong. Rewrap the same way.
- `docs/specs/2026-09-30-science-commons-design.md` §12 (about line 1118): the "A binds B…" sentence now follows the inserted amendment mid-paragraph, which reads oddly. Move the amendment after the paragraph.
- `docs/specs/2026-09-30-science-commons-design.md` §10 amendment: it is a single very long paragraph. The report already flags this.

### Assessment
**Task quality:** Approved
**Reasoning:** Every required amendment is present, dated, and no stronger than `adopt.py` and `show.py` establish. No stale pending statement remains in a current-behaviour document. Only wording and layout nits are left.

reviewer: claude-code/claude-sonnet-5-5
