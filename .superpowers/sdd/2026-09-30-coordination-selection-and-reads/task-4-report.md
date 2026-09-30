# Task 4 report: `projects` and `project-show`

Implemented the two read-only coordination commands from the approved brief. `projects` enumerates every standing project, orders by name then address, marks the selected address, and displays every divergent tip. `project-show` uses the selected or invocation-bound project, renders the canonical query and records in the specified sections, and treats divergent tasks as open. Added `mint_projects` for session-backed setup in CLI/MCP tests.

## Changed files

- `commands/projects/command.toml`, `commands/projects/prompt.md`
- `commands/project-show/command.toml`, `commands/project-show/prompt.md`
- `python/src/science/commands/projects.py`, `python/src/science/commands/project_show.py`
- `python/tests/helpers/world.py`, `python/tests/test_cmd_projects.py`
- `tools/cli.toml`
- `adapters/claude-code/skills/projects/SKILL.md`, `adapters/claude-code/skills/project-show/SKILL.md`
- `tasks/sci-b0b8cf.md` (completion), `tasks/sci-a66ca4.md` (existing Task 3 review note), `tasks/sci-103ec2.md` (controller ruling for Task 8)

## TDD and verification

- RED: `just test-one tests/test_cmd_projects.py` — 11 failed as expected. The direct invocations reported `unknown-command` for `projects`; the CLI transport rejected `projects` as an invalid command choice because the declarations did not exist yet.
- GREEN: `just test-one tests/test_cmd_projects.py` — 11 passed in 17.55s.
- Focused surface and adapter checks: `just test-one tests/test_cmd_projects.py tests/test_cli_surface.py tests/test_adapters.py` — 53 passed in 69.63s.
- Inner loop: `just test-fast` — 231 passed in 96.85s.
- Adapter generation: from `python/`, `uv run science adapters build` — exit 0.
- Diff whitespace check: `git diff --check` — clean.

## Self-review and concerns

The handler implementations reuse `tip_nodes`, `selected_project`, `stored_query`, and the existing typed report blocks. Tests cover sorting, empty worlds, divergent projects and tasks, project binding without changing selection, renamed tips, absent coordination, and byte-identical CLI/MCP output.

The generated adapter carries the existing common preamble claiming no project can be selected yet. This was preserved as directed; Task 8 owns the correction. No other concerns.
