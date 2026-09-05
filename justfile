# Front door for tests. Inner loop: `just test-fast` (affected-only via pytest-testmon).
# Full suite: `just test`. Gates: `just check` at pre-commit, `just gate` at pre-push.
# The git hooks in .githooks/ call `hook-pre-commit` and `hook-pre-push`, which run the
# very same commands under their own target names so the report can price the hooks.
# Every recipe runs through the vendored timing wrapper tools/tt (source of truth: ops
# bin/tt) so the run is recorded. Design: ops docs/specs/2026-09-04-test-ci-audit-design.md.

tt := "python3 tools/tt"

# The three commands, each written once. Recipes and hooks all run these, so a hook can
# never drift from the gate it is supposed to be. Avoid single quotes inside them.
# The package lives under python/; `uv run` syncs the dev group (pytest, pytest-testmon).
fast_cmd := "cd python && uv run pytest --testmon"
test_cmd := "cd python && uv run pytest"
# No formatter, linter, or typechecker is configured for this repository yet, so the
# seconds-long gate is the task-record check alone.
check_cmd := "tasks check"

# Affected-only: the inner loop. An empty selection is a result, not a failure.
test-fast:
    {{tt}} test-fast -- sh -c '{{fast_cmd}}'

# The full suite.
test:
    {{tt}} test -- sh -c '{{test_cmd}}'

# Seconds, not minutes.
check:
    {{tt}} check -- sh -c '{{check_cmd}}'

gate: check test

# What the pre-commit hook runs: `check`'s command under its own hook target.
hook-pre-commit:
    {{tt}} hook-pre-commit -- sh -c '{{check_cmd}}'

# What the pre-push hook runs: the same commands as `gate`, under one hook target.
hook-pre-push:
    {{tt}} hook-pre-push -- sh -c '{{check_cmd}} && {{test_cmd}}'
