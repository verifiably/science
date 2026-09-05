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
- Tests: `just test` runs the suite. `just check` runs the seconds-long gate; `just gate`
  runs both. Every recipe records its run through `tools/tt`, the timing wrapper vendored
  from the ops repository; do not call `pytest` directly.
- Before removing a worktree, run `tt-report` (in the ops repository) so its fallback
  test-timing log is harvested.
