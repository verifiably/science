# Task 3: `project-select`

Implemented the production `project-select` session command, including name/address resolution, clearing, replay behavior, ambiguous and unknown project refusals, divergent project handling, and the selection block. Session handlers now bind with `ctx, port`; subordinate and revise command tests select through the public command.

## TDD and verification

- RED — `just test-one tests/test_cmd_project_select.py`, 2026-09-30 12:17:14Z: 15 failed as expected because `project-select` was not registered (`unknown-command`). The MCP path also had no production command to call.
- GREEN — `just test-one tests/test_cmd_project_select.py`: 15 passed in 20.13s.
- GREEN — `just test-one tests/test_cmd_project_select.py tests/test_cmd_subordinate.py tests/test_cmd_revise.py tests/test_cli_surface.py tests/test_adapters.py`: 75 passed, exit 0, 97.924s. The run record is `2026-09-30T12:18:56Z`; its initial terminal output was not retained, so the completed `tools/tt` run record supplied the exit and test count.
- `just test-fast`: 188 passed in 87.70s.
- `uv run science adapters build`: passed.
- `git diff --check` and `tasks check`: passed.

## Changed files

- `commands/project-select/command.toml`, `commands/project-select/prompt.md`
- `python/src/science/commands/project_select.py`, `python/src/science/loader.py`
- `python/tests/test_cmd_project_select.py`, `python/tests/test_cmd_subordinate.py`, `python/tests/test_cmd_revise.py`
- `tools/cli.toml`, `adapters/claude-code/skills/project-select/`
- `tasks/sci-a66ca4.md` (started and completed in this commit)
- `tasks/sci-108756.md` (included Task 2's accepted implementation review note)

## Self-review

The command checks coordination availability and validates the target before calling the session port. The real command tests load it from `production_tree()` and cover both successful selection and refusal through MCP; the loader test rejects a session handler whose lead parameters are not `ctx, port`. No unrelated changes or unresolved concerns.

Commit: `feat(commands): project-select`.
