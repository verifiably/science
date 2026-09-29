# Front door for tests. Focused loop: `just test-one <pytest args>`.
# Inner loop: `just test-fast` (affected-only via pytest-testmon).
# Full suite: `just test`. Gates: `just check` at pre-commit, `just gate` at pre-push.
# The git hooks in .githooks/ call `hook-pre-commit` and `hook-pre-push`, which run the
# very same commands under their own target names so the report can price the hooks.
# Every recipe runs through the vendored timing wrapper tools/tt (source of truth: ops
# bin/tt) so the run is recorded. Design: ops docs/specs/2026-09-04-test-ci-audit-design.md.

set quiet
set positional-arguments

tt := "python3 tools/tt"

# The three commands, each written once. Recipes and hooks all run these, so a hook can
# never drift from the gate it is supposed to be. Avoid single quotes inside them.
# The package lives under python/; `uv run` syncs the dev group (pytest, pytest-testmon,
# pytest-xdist). Each test builds its own certified world, and atoms certifies the volume
# on every open by spawning children, so tests wait on I/O and subprocesses rather than
# CPU: 8 workers with work-stealing took the suite from 626 s to 79 s on 2026-09-23,
# and 16 workers bought nothing more. The worker count is the host's budget: test runs go
# through `host-budget run` (ops), which sets PYTEST_XDIST_AUTO_NUM_WORKERS for `-n auto`
# (design: ops docs/specs/2026-09-24-host-budget-design.md). Worktree runs need no
# SCIENCE_TEST_ROOT: conftest resolves the certified test root through the main checkout.
xdist := "-n auto --dist worksteal"
fast_cmd := "cd python && uv run pytest --testmon " + xdist
test_cmd := "cd python && uv run pytest " + xdist
one_cmd := "cd python && uv run pytest"
# No formatter, linter, or typechecker is configured for this repository yet, so the
# seconds-long gate is the task-record check alone.
check_cmd := "python3 tools/ops-check && tasks check"

# Only passive docs and task records: python/tests/fixtures/*.md are command inputs.
docs_paths := "README.md AGENTS.md docs/*.md tasks/*.md"
docs_check_cmd := check_cmd

# No CI workflow runs the full suite on push, so every push keeps the full local gate.
ci_suite_refs := ""
ci_remote := "origin"
# testmon selects from its dependency data, independent of a git push base (form 2).
push_fast_cmd := fast_cmd

# One path, path::test, or -k expression, with each argument forwarded unchanged.
test-one +args:
    {{tt}} test-one -- host-budget run -- sh -c '{{one_cmd}} "$@" 2>&1' test-one "$@"

# Affected-only: the inner loop. An empty selection is a result, not a failure.
test-fast:
    {{tt}} test-fast -- host-budget run -- sh -c '{{fast_cmd}}'

# The full suite.
test:
    {{tt}} test -- host-budget run -- sh -c '{{test_cmd}}'

# Seconds, not minutes.
check:
    {{tt}} check -- sh -c '{{check_cmd}}'

gate: check test

# What the pre-commit hook runs: `check`'s command under its own hook target.
hook-pre-commit:
    {{tt}} hook-pre-commit -- sh -c '{{check_cmd}}'

# Every staged path is a passive document or task record.
hook-pre-commit-docs:
    {{tt}} hook-pre-commit-docs -- sh -c '{{docs_check_cmd}}'

# What the pre-push hook runs: the same commands as `gate`, under one hook target.
hook-pre-push:
    {{tt}} hook-pre-push -- host-budget run -- sh -c '{{check_cmd}} && {{test_cmd}}'

# Available for CI-covered pushes when ci_suite_refs is configured; currently unused.
hook-pre-push-fast:
    {{tt}} hook-pre-push-fast -- host-budget run -- sh -c '{{check_cmd}} && {{push_fast_cmd}}'
