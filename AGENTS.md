# science — agent guide

The daily surface of Science: commands and skills over the `beliefs` kernel. The Python
package lives under `python/`; tasks live in `tasks/` and the `tasks` skill applies. The
governing design is `docs/specs/2026-08-31-command-framework-design.md`.

## Setup

```sh
git config core.hooksPath .githooks
```

The hooks in `.githooks/` run the `just` recipes below. `uv run` under `python/` creates
the environment on first use, with `beliefs` as an editable path dependency.

## Session protocol

- `tasks prime`, then `tasks start <id>` before changing anything; `tasks done <id>` in the
  same commit; `tasks check` before every commit.
- Tests: `just test-one <pytest args>` runs the test at hand: a path relative to `python/`,
  `tests/test_file.py::test_name`, or `-k "a and b"`; at least one argument is required.
  `just test-fast` is the inner loop (pytest-testmon selects affected tests from its
  dependency data); run it before committing. `just test` runs the suite, about 80
  seconds on 8 workers. All test recipes run under ops' `host-budget run`, which sizes
  `-n auto` to the host's budget. `just check` runs the seconds-long gate;
  `just gate` runs both. All test recipes run in a worktree as they are. Every recipe
  records its run through `tools/tt`, the timing wrapper vendored from the ops
  repository; do not call `pytest` directly.
- The pre-commit hook classifies every staged path against `docs_paths` in the justfile:
  only `README.md`, `AGENTS.md`, `docs/*.md` and `tasks/*.md` take `hook-pre-commit-docs`.
  Markdown command fixtures are excluded; renames count on both sides and failed
  classification runs the full check. Both checks currently run ops-check and tasks check.
- There is no CI workflow, so `ci_suite_refs` is empty and the pre-push hook always
  carries the full suite through `just hook-pre-push`. `hook-pre-push-fast` is available
  for future CI-covered push refs and uses testmon's dependency selection. Run `just test`
  yourself only when hooks are not installed, the fast target does not cover the affected
  behavior, or you are asked to.
- Before removing a worktree, run `tt-report` (in the ops repository) so its fallback
  test-timing log is harvested.
