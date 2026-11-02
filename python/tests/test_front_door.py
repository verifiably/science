"""Exercise the adopted front door in an isolated temporary repository."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]


class FrontDoor:
    def __init__(self, base: Path) -> None:
        self.base = base
        self.repo = base / "repo"
        self.repo.mkdir()
        self.log = base / "timings.jsonl"
        self.marker_log = base / "markers.jsonl"
        self.stdin_log = base / "stdin.txt"
        self.env_log = base / "child_env.json"

        bin_dir = base / "bin"
        bin_dir.mkdir()
        budget = bin_dir / "host-budget"
        budget.write_text(
            "#!/bin/sh\n"
            '[ "$1" = run ] && [ "$2" = -- ] || exit 91\n'
            "shift 2\n"
            'exec "$@"\n'
        )
        budget.chmod(0o755)

        ssh = bin_dir / "ssh"
        ssh.write_text(
            "#!/bin/sh\n"
            'printf "serveraliveinterval %s\\n" "${SSH_INTERVAL:-60}"\n'
        )
        ssh.chmod(0o755)

        self.env = {
            "PATH": f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '/usr/bin:/bin')}",
            "HOME": str(base / "home"),
            "USER": "tester",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_AUTHOR_NAME": "Test",
            "GIT_AUTHOR_EMAIL": "test@example.invalid",
            "GIT_COMMITTER_NAME": "Test",
            "GIT_COMMITTER_EMAIL": "test@example.invalid",
            "TT_LOG": str(self.log),
        }
        (base / "home").mkdir()

        self.git("init", "-q", "-b", "main")
        toplevel = Path(self.git("rev-parse", "--show-toplevel").stdout.strip()).resolve()
        git_dir = Path(self.git("rev-parse", "--absolute-git-dir").stdout.strip()).resolve()
        assert toplevel == self.repo.resolve()
        assert git_dir.is_relative_to(self.repo.resolve())

        for rel in ("justfile", ".githooks/pre-commit", ".githooks/pre-push", "tools/tt"):
            dst = self.repo / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / rel, dst)

        ops_check = self.repo / "tools/ops-check"
        ops_check.write_text("#!/usr/bin/env python3\nimport sys\nsys.exit(0)\n")
        ops_check.chmod(0o755)

        marker = base / "marker.py"
        marker.write_text(
            "import json, os, pathlib, sys\n"
            "log = pathlib.Path(os.environ['MARKER_LOG'])\n"
            "with log.open('a', encoding='utf-8') as fh:\n"
            "    fh.write(json.dumps(sys.argv[1:]) + '\\n')\n"
            "if os.environ.get('RECORD_STDIN') == '1' and not pathlib.Path(os.environ['STDIN_LOG']).exists():\n"
            "    pathlib.Path(os.environ['STDIN_LOG']).write_text(sys.stdin.read(), encoding='utf-8')\n"
            "if os.environ.get('RECORD_ENV') == '1':\n"
            "    pathlib.Path(os.environ['ENV_LOG']).write_text(json.dumps(dict(os.environ)), encoding='utf-8')\n"
            "name = sys.argv[1]\n"
            "if os.environ.get('FAIL_TARGET') == name:\n"
            "    print('1 failed in 0.01s')\n"
            "    sys.exit(7)\n"
            "if name in {'suite', 'fast', 'one', 'ci-py'}:\n"
            "    print('1 passed in 0.01s')\n"
        )
        self.env["MARKER_LOG"] = str(self.marker_log)
        self.env["STDIN_LOG"] = str(self.stdin_log)
        self.env["ENV_LOG"] = str(self.env_log)

        py = shlex.quote(sys.executable)
        mk = shlex.quote(str(marker))
        jf = (self.repo / "justfile").read_text(encoding="utf-8")
        replacements = {
            'check_hygiene_cmd := "python3 tools/ops-check && python3 tools/ops-docs check && tasks check"': (
                f'check_hygiene_cmd := "{py} {mk} hygiene"'
            ),
            'fast_cmd := "cd python && uv run pytest --testmon " + xdist': (
                f'fast_cmd := "{py} {mk} fast"'
            ),
            'test_cmd := "cd python && uv run pytest " + xdist': (
                f'test_cmd := "{py} {mk} suite"'
            ),
            'one_cmd := "cd python && uv run pytest"': (
                f'one_cmd := "{py} {mk} one"'
            ),
            'ci_py_test_cmd := "cd python && uv run --frozen pytest --junitxml=\\"$SCIENCE_CI_EVIDENCE_DIR/pytest.xml\\" " + xdist': (
                f'ci_py_test_cmd := "{py} {mk} ci-py"'
            ),
        }
        for old, new in replacements.items():
            assert old in jf, f"missing expected command declaration in justfile: {old}"
            jf = jf.replace(old, new, 1)
        (self.repo / "justfile").write_text(jf, encoding="utf-8")

        self.git("add", ".")
        self.git("commit", "-q", "-m", "init")

    def git(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args],
            cwd=self.repo,
            env=self.env,
            text=True,
            capture_output=True,
            check=True,
        )

    def write_policy(self, automatic_broad: bool = False) -> None:
        val = "true" if automatic_broad else "false"
        (self.repo / ".tt.toml").write_text(
            f'automatic_broad = {val}\nbroad_targets = ["test", "test-fast", "ci-python"]\n',
            encoding="utf-8",
        )

    def set_ci_suite_refs(self, pattern: str) -> None:
        jf = (self.repo / "justfile").read_text(encoding="utf-8")
        lines = [
            f'ci_suite_refs := "{pattern}"' if line.startswith("ci_suite_refs :=") else line
            for line in jf.splitlines()
        ]
        (self.repo / "justfile").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def clear_logs(self) -> None:
        for path in (self.log, self.marker_log, self.stdin_log, self.env_log):
            path.unlink(missing_ok=True)

    def run_just(self, *args: str, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        self.clear_logs()
        env = {**self.env, **(extra_env or {})}
        return subprocess.run(
            ["just", *args],
            cwd=self.repo,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def run_hook(
        self,
        hook: str,
        *args: str,
        stdin: str = "",
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        self.clear_logs()
        env = {**self.env, **(extra_env or {})}
        return subprocess.run(
            [str(self.repo / ".githooks" / hook), *args],
            cwd=self.repo,
            input=stdin,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def markers(self) -> list[list[str]]:
        if not self.marker_log.exists():
            return []
        return [json.loads(line) for line in self.marker_log.read_text(encoding="utf-8").splitlines()]

    def timings(self) -> list[dict[str, object]]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]


@pytest.fixture
def front_door(tmp_path: Path) -> FrontDoor:
    return FrontDoor(tmp_path)


def test_fixture_environment_is_isolated(front_door: FrontDoor) -> None:
    forbidden = {"TT_FORCE", "GITHUB_ACTIONS", "CI", "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"}
    assert forbidden.isdisjoint(front_door.env)
    assert front_door.env["GIT_CONFIG_GLOBAL"] == "/dev/null"
    assert front_door.env["GIT_CONFIG_NOSYSTEM"] == "1"


def test_recipes_match_shared_contract(front_door: FrontDoor) -> None:
    res = front_door.run_just("--summary")
    assert res.returncode == 0, res.stderr
    assert set(res.stdout.split()) == {
        "test-fast",
        "test-one",
        "test",
        "test-full",
        "ci-python",
        "check-hygiene",
        "check",
        "gate",
        "docs",
        "hook-pre-commit",
        "hook-pre-commit-docs",
        "hook-pre-push",
        "hook-pre-push-fast",
    }


@pytest.mark.parametrize(
    ("path", "expected_target"),
    [
        ("README.md", "hook-pre-commit-docs"),
        ("AGENTS.md", "hook-pre-commit-docs"),
        ("docs/stores.md", "hook-pre-commit-docs"),
        ("tasks/sci-6af05a.md", "hook-pre-commit-docs"),
        ("python/tests/fixtures/doc.md", "hook-pre-commit"),
        ("justfile", "hook-pre-commit"),
    ],
)
def test_pre_commit_routes_docs_paths_only_when_every_staged_file_matches(
    front_door: FrontDoor, path: str, expected_target: str
) -> None:
    target_file = front_door.repo / path
    target_file.parent.mkdir(parents=True, exist_ok=True)
    with target_file.open("a", encoding="utf-8") as fh:
        fh.write("\n# changed\n")
    front_door.git("add", "--", path)

    res = front_door.run_hook("pre-commit")
    assert res.returncode == 0, res.stderr
    assert front_door.markers() == [["hygiene"]]
    rows = front_door.timings()
    assert [(r["target"], r["execution"]) for r in rows] == [(expected_target, "ran")]


@pytest.mark.parametrize(
    ("recipe", "expected_skipped"),
    [
        ("check", []),
        ("gate", ["test"]),
        ("hook-pre-commit", []),
        ("hook-pre-commit-docs", []),
        ("hook-pre-push", ["test"]),
        ("hook-pre-push-fast", ["test-fast"]),
    ],
)
def test_policy_off_keeps_hygiene_and_skips_broad_children(
    front_door: FrontDoor, recipe: str, expected_skipped: list[str]
) -> None:
    front_door.write_policy(automatic_broad=False)
    res = front_door.run_just(recipe)
    assert res.returncode == 0, res.stderr
    assert front_door.markers() == [["hygiene"]]

    rows = front_door.timings()
    skipped = [r for r in rows if r["execution"] == "skipped"]
    assert [r["target"] for r in skipped] == expected_skipped
    for row in skipped:
        assert row["execution_reason"] == "policy-disabled"
        assert row["exit"] is None
        assert row["tests"] is None
        assert row["selection"] is None
        assert row["slowest"] is None


def test_enabled_hooks_run_hygiene_then_suite_and_stop_on_hygiene_failure(
    front_door: FrontDoor,
) -> None:
    front_door.write_policy(automatic_broad=True)

    res = front_door.run_just("hook-pre-push")
    assert res.returncode == 0, res.stderr
    assert front_door.markers() == [["hygiene"], ["suite"]]
    assert [(r["target"], r["execution"]) for r in front_door.timings()] == [
        ("hook-pre-push", "ran"),
        ("test", "ran"),
    ]

    res_fast = front_door.run_just("hook-pre-push-fast")
    assert res_fast.returncode == 0, res_fast.stderr
    assert front_door.markers() == [["hygiene"], ["fast"]]
    assert [(r["target"], r["execution"]) for r in front_door.timings()] == [
        ("hook-pre-push-fast", "ran"),
        ("test-fast", "ran"),
    ]

    fail_hygiene = front_door.run_just("hook-pre-push", extra_env={"FAIL_TARGET": "hygiene"})
    assert fail_hygiene.returncode == 7
    assert front_door.markers() == [["hygiene"]]

    fail_suite = front_door.run_just("hook-pre-push-fast", extra_env={"FAIL_TARGET": "fast"})
    assert fail_suite.returncode == 7
    assert front_door.markers() == [["hygiene"], ["fast"]]


def test_test_full_and_forced_gate_override_policy_off(front_door: FrontDoor) -> None:
    front_door.write_policy(automatic_broad=False)

    res = front_door.run_just("test-full")
    assert res.returncode == 0, res.stderr
    assert front_door.markers() == [["suite"]]
    rows = front_door.timings()
    assert len(rows) == 1
    assert (rows[0]["target"], rows[0]["execution"], rows[0]["execution_reason"]) == (
        "test",
        "ran",
        "forced",
    )

    fail = front_door.run_just("test-full", extra_env={"FAIL_TARGET": "suite"})
    assert fail.returncode == 7
    rows_fail = front_door.timings()
    assert (rows_fail[0]["target"], rows_fail[0]["execution"], rows_fail[0]["exit"]) == (
        "test",
        "ran",
        7,
    )

    gate = front_door.run_just("gate", extra_env={"TT_FORCE": "1"})
    assert gate.returncode == 0, gate.stderr
    assert front_door.markers() == [["hygiene"], ["suite"]]
    assert [(r["target"], r["execution"], r["execution_reason"]) for r in front_door.timings()] == [
        ("check-hygiene", "ran", "forced"),
        ("test", "ran", "forced"),
    ]


def test_test_one_runs_under_policy_off_and_preserves_arguments(front_door: FrontDoor) -> None:
    front_door.write_policy(automatic_broad=False)
    args = ["-k", "a and b", "tests/p q.py", "it's", "$HOME", "renders *"]
    res = front_door.run_just("test-one", *args)
    assert res.returncode == 0, res.stderr
    assert front_door.markers() == [["one", *args]]
    rows = front_door.timings()
    assert [(r["target"], r["execution"], r["tests"]) for r in rows] == [("test-one", "ran", 1)]

    empty = front_door.run_just("test-one")
    assert empty.returncode != 0


def test_ci_python_requires_absolute_evidence_dir_and_runs_when_forced(
    front_door: FrontDoor, tmp_path: Path
) -> None:
    front_door.write_policy(automatic_broad=False)

    missing = front_door.run_just("ci-python", extra_env={"TT_FORCE": "1"})
    assert missing.returncode != 0
    assert "set SCIENCE_CI_EVIDENCE_DIR" in missing.stderr

    relative = front_door.run_just(
        "ci-python",
        extra_env={"TT_FORCE": "1", "SCIENCE_CI_EVIDENCE_DIR": "rel/path"},
    )
    assert relative.returncode == 2
    assert "CI evidence path must be absolute" in relative.stderr

    evidence = tmp_path / "ev"
    evidence.mkdir()
    ok = front_door.run_just(
        "ci-python",
        extra_env={"TT_FORCE": "1", "SCIENCE_CI_EVIDENCE_DIR": str(evidence)},
    )
    assert ok.returncode == 0, ok.stderr
    assert front_door.markers() == [["ci-py"]]
    rows = front_door.timings()
    assert [(r["target"], r["execution"], r["execution_reason"]) for r in rows] == [
        ("ci-python", "ran", "forced")
    ]


@pytest.mark.parametrize("target", ["test", "test-fast", "ci-python", "hook-pre-push-fast"])
def test_hosted_broad_targets_without_force_fail_loudly(
    front_door: FrontDoor, target: str, tmp_path: Path
) -> None:
    front_door.write_policy(automatic_broad=False)
    ev = str(tmp_path / "ev")
    res = front_door.run_just(
        target,
        extra_env={"GITHUB_ACTIONS": "true", "SCIENCE_CI_EVIDENCE_DIR": ev},
    )
    assert res.returncode == 2
    assert "TT_FORCE=1" in res.stderr
    assert not [r for r in front_door.timings() if r["execution"] == "skipped"]

    forced = front_door.run_just(
        target,
        extra_env={"GITHUB_ACTIONS": "true", "TT_FORCE": "1", "SCIENCE_CI_EVIDENCE_DIR": ev},
    )
    assert forced.returncode == 0, forced.stderr


def test_pre_push_routes_refs_and_warns_only_on_uncovered_skipped_push(
    front_door: FrontDoor,
) -> None:
    front_door.write_policy(automatic_broad=False)
    front_door.set_ci_suite_refs("refs/heads/*")

    branch_stdin = f"refs/heads/main {'a' * 40} refs/heads/main {'b' * 40}\n"
    res_branch = front_door.run_hook(
        "pre-push",
        "origin",
        "https://example.invalid/repo.git",
        stdin=branch_stdin,
        extra_env={"RECORD_STDIN": "1"},
    )
    assert res_branch.returncode == 0, res_branch.stderr
    assert "remote full-suite coverage is not declared" not in res_branch.stderr
    assert front_door.stdin_log.read_text(encoding="utf-8") == branch_stdin
    assert [(r["target"], r["execution"]) for r in front_door.timings()] == [
        ("hook-pre-push-fast", "ran"),
        ("test-fast", "skipped"),
    ]

    feat_stdin = f"refs/heads/feat/x {'a' * 40} refs/heads/feat/x {'b' * 40}\n"
    res_feat = front_door.run_hook("pre-push", "origin", "https://example.invalid/repo.git", stdin=feat_stdin)
    assert res_feat.returncode == 0, res_feat.stderr
    assert [(r["target"], r["execution"]) for r in front_door.timings()] == [
        ("hook-pre-push-fast", "ran"),
        ("test-fast", "skipped"),
    ]

    delete_stdin = f"(delete) {'0' * 40} refs/heads/old {'b' * 40}\n"
    res_del = front_door.run_hook("pre-push", "origin", "https://example.invalid/repo.git", stdin=delete_stdin)
    assert res_del.returncode == 0, res_del.stderr
    assert [(r["target"], r["execution"]) for r in front_door.timings()] == [
        ("hook-pre-push-fast", "ran"),
        ("test-fast", "skipped"),
    ]

    tag_stdin = f"refs/tags/v1 {'a' * 40} refs/tags/v1 {'b' * 40}\n"
    res_tag = front_door.run_hook("pre-push", "origin", "https://example.invalid/repo.git", stdin=tag_stdin)
    assert res_tag.returncode == 0, res_tag.stderr
    assert "remote full-suite coverage is not declared for this push" in res_tag.stderr
    assert [(r["target"], r["execution"]) for r in front_door.timings()] == [
        ("hook-pre-push", "ran"),
        ("test", "skipped"),
    ]

    malformed_stdin = "refs/heads/main not-a-sha\n"
    res_malformed = front_door.run_hook("pre-push", "origin", "https://example.invalid/repo.git", stdin=malformed_stdin)
    assert res_malformed.returncode == 0, res_malformed.stderr
    assert "remote full-suite coverage is not declared for this push" in res_malformed.stderr
    assert [(r["target"], r["execution"]) for r in front_door.timings()] == [
        ("hook-pre-push", "ran"),
        ("test", "skipped"),
    ]

    res_backup = front_door.run_hook("pre-push", "backup", "https://example.invalid/repo.git", stdin=branch_stdin)
    assert res_backup.returncode == 0, res_backup.stderr
    assert "remote full-suite coverage is not declared for this push" in res_backup.stderr

    front_door.set_ci_suite_refs("")
    res_empty_refs = front_door.run_hook("pre-push", "origin", "https://example.invalid/repo.git", stdin=branch_stdin)
    assert res_empty_refs.returncode == 0, res_empty_refs.stderr
    assert "remote full-suite coverage is not declared for this push" in res_empty_refs.stderr


def test_unreadable_policy_refuses_push(front_door: FrontDoor) -> None:
    (front_door.repo / ".tt.toml").write_text(
        'automatic_broad = "no"\nbroad_targets = ["test"]\n',
        encoding="utf-8",
    )
    stdin = f"refs/heads/main {'a' * 40} refs/heads/main {'b' * 40}\n"
    res = front_door.run_hook("pre-push", "origin", "https://example.invalid/repo.git", stdin=stdin)
    assert res.returncode == 2
    assert "cannot inspect test execution policy" in res.stderr
    assert front_door.markers() == []


def test_missing_keepalive_refuses_before_gate(front_door: FrontDoor) -> None:
    stdin = f"refs/heads/main {'a' * 40} refs/heads/main {'b' * 40}\n"
    res = front_door.run_hook(
        "pre-push",
        "origin",
        "git@example.invalid:repo.git",
        stdin=stdin,
        extra_env={"SSH_INTERVAL": "0"},
    )
    assert res.returncode == 1
    assert "ServerAliveInterval 60" in res.stderr
    assert front_door.markers() == []


def test_pre_push_clears_git_local_environment(front_door: FrontDoor) -> None:
    front_door.write_policy(automatic_broad=False)
    stdin = f"refs/heads/main {'a' * 40} refs/heads/main {'b' * 40}\n"
    res = front_door.run_hook(
        "pre-push",
        "origin",
        "https://example.invalid/repo.git",
        stdin=stdin,
        extra_env={
            "RECORD_ENV": "1",
            "GIT_DIR": str(front_door.repo / ".git"),
            "GIT_WORK_TREE": str(front_door.repo),
            "GIT_INDEX_FILE": str(front_door.repo / ".git/index"),
        },
    )
    assert res.returncode == 0, res.stderr
    child_env = json.loads(front_door.env_log.read_text(encoding="utf-8"))
    assert "GIT_DIR" not in child_env
    assert "GIT_WORK_TREE" not in child_env
    assert "GIT_INDEX_FILE" not in child_env


def test_ci_workflow_conformance() -> None:
    import re

    workflow = (REPO / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert 'branches: ["**"]' in workflow
    assert "pull_request:" in workflow
    assert "workflow_dispatch:" in workflow
    assert (
        "if: github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name != github.repository"
        in workflow
    )
    assert "group: ${{ github.workflow }}-${{ github.ref }}" in workflow
    assert "cancel-in-progress: true" in workflow
    assert "contents: read" in workflow
    assert "timeout-minutes: 30" in workflow
    assert 'python-version: ["3.11", "3.13"]' in workflow
    assert 'TT_FORCE: "1"' in workflow
    assert 'PYTEST_XDIST_AUTO_NUM_WORKERS: "4"' in workflow
    assert "working-directory: science/python" in workflow

    uses = re.findall(r"^\s*-?\s*uses:\s*(\S+)", workflow, flags=re.MULTILINE)
    assert uses
    for ref in uses:
        assert re.fullmatch(r"[^@]+@[0-9a-f]{40}", ref), f"unpinned action: {ref}"
    assert "actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0" in uses
    assert "astral-sh/setup-uv@11f9893b081a58869d3b5fccaea48c9e9e46f990" in uses
    assert "extractions/setup-just@53165ef7e734c5c07cb06b3c8e7b647c5aa16db3" in uses
    assert "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a" in uses
    assert "setup-python" not in workflow
    assert 'version: "0.11.29"' in workflow
    assert "python-version: ${{ matrix.python-version }}" in workflow

    for repo_line in (
        "path: science",
        "repository: verifiably/beliefs",
        "path: beliefs",
        "repository: verifiably/atoms",
        "path: atoms",
        "repository: verifiably/nodes",
        "path: nodes",
    ):
        assert repo_line in workflow

    ordered = [
        "Prepare coverage evidence",
        "uv sync --frozen",
        "just ci-python",
        "Require coverage evidence",
        "actions/upload-artifact@",
    ]
    positions = [workflow.index(marker) for marker in ordered]
    assert positions == sorted(positions)


def test_live_ops_check_passes_without_tasks_registry(tmp_path: Path) -> None:
    env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(tmp_path),
        "XDG_CONFIG_HOME": str(tmp_path / "xdg"),
    }
    res = subprocess.run(
        [sys.executable, str(REPO / "tools/ops-check")],
        cwd=REPO,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert res.returncode == 0, res.stderr


