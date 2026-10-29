# Task 15 report: documents for the retirement tail (sci-50d0c2)

Status: DONE. Docs and generated adapter skills only; no code change.

## Amendments (each dated `Amended 2026-10-29 (milestone 1b plan, Task 15)`)
- `docs/specs/2026-09-30-science-commons-design.md`
  - 10: the interim "adds no retirement call" paragraph is replaced by an amendment describing shipped behaviour: `ScopedWriter.retire(root, observers, *, evidence)` (root from registry, observers from retained head artifact, transition always `retired`); idempotent any-actor recovery (`already-retired`, no second status record); reconcile calls the door for every mounted pin with known, non-live, non-departed status; departed -> Finding, never the door; refusals StatusTerminal/StatusTargetUnknown; `config-stale` before retirement; `show` `retention: pending: rerun adopt`; write guards; the gates (Task 14 map); one stated limit (reconcile retiring the requested target persists the line then refuses invalid-input). Rests on adopt.py `_retire`/reconcile and task-13/14 reports. A closing note after the "Retirement is therefore a 1b obligation" sentence.
  - 11: door row now "landed (beliefs `f274822`)", plus an amendment after the Task 12 one stating the door's shape.
  - 12: 1b paragraph states both halves are implemented on `commons-1b` (`bb1fad5`, `320f9e3`), integration pending, strict xfail gone.
- `docs/specs/2026-08-31-command-framework-design.md`: an amendment after Task 12's paragraph (4.x, ~line 385): door landed; `adopt` reaches it via `ScopedWriter.retire`; science still does not call `World.retire` directly.
- `docs/specs/2026-10-28-science-commons-1b-design.md`: status amendment only (tail landed on `commons-1b` at `bb1fad5`/`320f9e3`, review and integration pending); 5.7/5.9/7 interim prose untouched.
- `docs/plans/2026-10-28-science-commons-1b.md`: Execution status paragraph: Tasks 13-15 with commit ids, xfail gone, whole-tail review and local merge to come. Task 15's own commit id is described as "follows in history" (it cannot name itself).
- `commands/adopt/prompt.md`, `commands/show/prompt.md`: pending-door wording replaced by shipped behaviour. Regenerated `adapters/claude-code/skills/{adopt,show}/SKILL.md` with `science adapters build` (test_adapters requires it; the first gate run failed on exactly this).

## Grep hits (a989fb | no door | retirement pending | has not landed)
- commons 1b design (lines ~94,151,597,616-619,738-739,789-809): left; decision record, interim prose per ruling.
- plan 2026-10-28 lines 19, 72, 680-681, 941: left; dated plan text / approval status / the Task 13 heading, a record of what was true at writing; Execution status carries the current state.
- plan 2026-10-22 1a:107, commons design:210, plan 2026-08-31:3437: false positives ("needs no door", "beliefs has not landed").
- commons design 901 (quoted in my amendment as the superseded interim state), 1020 (row, now "landed"), 1049 (new amendment): intended.
- framework design 372: Task 12's dated amendment, left as history; superseded by the new amendment directly after it.
- adopt/show prompts, python/src: no hits remain.

## Gate
`just gate` rc 0: 1069 collected, 1069 passed, 0 failed, 0 xfailed (the strict xfail is gone); suite 279.84s (4:42 wall). Log: `.superpowers/sdd/2026-10-28-science-commons-1b/task-15-gate.log`. Two earlier runs failed only on the stale generated adapter skills (1 failed, 1068 passed); fixed by regeneration.

## Self-review / concerns
- Wording checked against adopt.py (`_retire`, reconcile lines ~110-120, `config-stale` ~198) and show.py (line 129 row). "Even of the already-mounted target" rests on the task-13 report and test_cmd_show retry test, not re-read in code.
- The 10 amendment is long; it is a single paragraph to match the style of the section.
- Plan Execution status says "its commit follows"; the controller may wish to add the id at merge.
