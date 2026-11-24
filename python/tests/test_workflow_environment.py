"""Tests for preparing and opening immutable locked workflow environments."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import threading
import time
import zipfile
from pathlib import Path

import pytest

from science.refusal import Refused
from science.workflow_environment import (
    WORKFLOW_ENVIRONMENT_KEY_RE,
    open_environment,
    prepare_environment,
)


def _build_wheel(wheel_dir: Path, name: str, version: str, files: dict[str, str]) -> Path:
    wheel_dir.mkdir(parents=True, exist_ok=True)
    dist = name.replace("-", "_")
    wheel_path = wheel_dir / f"{dist}-{version}-py3-none-any.whl"
    dist_info = f"{dist}-{version}.dist-info"
    metadata = f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"
    wheel_meta = (
        "Wheel-Version: 1.0\n"
        "Generator: test-fixture\n"
        "Root-Is-Purelib: true\n"
        "Tag: py3-none-any\n"
    )
    entries = {
        **files,
        f"{dist_info}/METADATA": metadata,
        f"{dist_info}/WHEEL": wheel_meta,
    }
    record_lines: list[str] = []
    with zipfile.ZipFile(wheel_path, "w") as zf:
        for rel, content in sorted(entries.items()):
            raw = content.encode("utf-8")
            zf.writestr(rel, raw)
            record_lines.append(f"{rel},sha256={hashlib.sha256(raw).hexdigest()},{len(raw)}")
        record_lines.append(f"{dist_info}/RECORD,,")
        zf.writestr(f"{dist_info}/RECORD", "\n".join(record_lines) + "\n")
    return wheel_path


def _make_locked_fixture(
    root: Path,
    *,
    include_dev_group: bool = True,
    extra_pyproject: str = "",
    uv_cmd: list[str] | None = None,
) -> tuple[Path, Path]:
    """Create a real small locked project with local wheels requiring Python >=3.11."""
    wheels = root / "wheels"
    runtime_whl = _build_wheel(
        wheels,
        "wf-runtime-pkg",
        "0.1.0",
        {"wf_runtime_pkg/__init__.py": "TOKEN = 'runtime-v1'\n"},
    )
    dev_whl = _build_wheel(
        wheels,
        "wf-dev-only",
        "0.1.0",
        {"wf_dev_only/__init__.py": "DEV = True\n"},
    )
    extra_group_whl = _build_wheel(
        wheels,
        "wf-default-group-pkg",
        "0.1.0",
        {"wf_default_group_pkg/__init__.py": "GROUP = True\n"},
    )
    project = root / "project"
    project.mkdir(parents=True, exist_ok=True)
    (project / "src" / "wf_root").mkdir(parents=True, exist_ok=True)
    (project / "src" / "wf_root" / "__init__.py").write_text("ROOT_REV = 1\n")

    lines = [
        "[project]",
        'name = "wf-fixture"',
        'version = "0.1.0"',
        'requires-python = ">=3.11"',
        'dependencies = ["wf-runtime-pkg==0.1.0"]',
        "",
        "[build-system]",
        'requires = ["hatchling"]',
        'build-backend = "hatchling.build"',
        "",
        "[tool.hatch.build.targets.wheel]",
        'packages = ["src/wf_root"]',
        "",
        "[tool.uv.sources]",
        f'wf-runtime-pkg = {{ path = "{runtime_whl}" }}',
    ]
    if include_dev_group:
        lines.extend([
            f'wf-dev-only = {{ path = "{dev_whl}" }}',
            f'wf-default-group-pkg = {{ path = "{extra_group_whl}" }}',
            "",
            "[dependency-groups]",
            'dev = ["wf-dev-only==0.1.0"]',
            'extras = ["wf-default-group-pkg==0.1.0"]',
            "",
            "[tool.uv]",
            'default-groups = ["dev", "extras"]',
        ])
    if extra_pyproject:
        lines.append("")
        lines.append(extra_pyproject)
    (project / "pyproject.toml").write_text("\n".join(lines) + "\n")

    lock_cmd = [*(uv_cmd or ["uv"]), "lock", "--no-config", "--offline"]
    lock_cache = root / "lock-cache"
    lock_env = {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(root / "lock-home"),
        "UV_CACHE_DIR": str(lock_cache),
    }
    res = subprocess.run(lock_cmd, cwd=project, env=lock_env, capture_output=True, text=True)
    assert res.returncode == 0, f"uv lock failed: {res.stderr}"
    return project, wheels


def _make_fake_venv(venv_dir: Path, base_python: Path) -> None:
    venv_dir.mkdir(parents=True, exist_ok=True)
    bin_dir = venv_dir / "bin"
    bin_dir.mkdir(exist_ok=True)
    py = bin_dir / "python"
    if not py.exists():
        os.symlink(base_python, py)
    (venv_dir / "pyvenv.cfg").write_text(
        f"home = {base_python.parent}\n"
        "include-system-site-packages = false\n"
        f"version_info = {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}\n"
    )


def _write_minimal_project(project: Path, *, lock_text: str, pyproject_text: str | None = None) -> None:
    project.mkdir(parents=True, exist_ok=True)
    (project / "pyproject.toml").write_text(
        pyproject_text
        or (
            "[project]\n"
            'name = "demo"\n'
            'version = "0.1.0"\n'
            'requires-python = ">=3.11"\n'
            'dependencies = ["alpha==1.0.0"]\n'
        )
    )
    (project / "uv.lock").write_text(lock_text)


def test_real_locked_fixture_syncs_offline_excludes_default_groups_and_root_source_edits_preserve_key(
    tmp_path, monkeypatch
):
    project, _ = _make_locked_fixture(tmp_path)
    ops_root = tmp_path / "ops"
    ops_root.mkdir()
    empty_cache = tmp_path / "empty-uv-cache"
    fixture_home = tmp_path / "fixture-home"
    fixture_home.mkdir()
    monkeypatch.setenv("HOME", str(fixture_home))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("UV_CACHE_DIR", str(empty_cache))
    # Ambient redirection/group variables must not affect preparation.
    monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", str(tmp_path / "wrong-venv"))
    monkeypatch.setenv("UV_DEFAULT_GROUPS", "all")
    monkeypatch.setenv("VIRTUAL_ENV", str(tmp_path / "ambient-venv"))

    # Hostile project uv.toml must be ignored (--no-config + UV_NO_CONFIG=1).
    (project / "uv.toml").write_text('default-groups = ["dev", "extras"]\n')

    key = prepare_environment(project, ops_root)
    assert WORKFLOW_ENVIRONMENT_KEY_RE.fullmatch(key)
    assert not (tmp_path / "wrong-venv").exists()

    with open_environment(key, ops_root) as venv_path:
        assert venv_path == ops_root / "workflow-environments" / key / "venv"
        py = venv_path / "bin" / "python"
        py_home = tmp_path / "py-check-home"
        py_home.mkdir()
        check = subprocess.run(
            [
                str(py),
                "-c",
                (
                    "import importlib.util, wf_runtime_pkg; "
                    "assert wf_runtime_pkg.TOKEN == 'runtime-v1'; "
                    "assert importlib.util.find_spec('wf_dev_only') is None; "
                    "assert importlib.util.find_spec('wf_default_group_pkg') is None; "
                    "assert importlib.util.find_spec('wf_root') is None; "
                    "print('OK')"
                ),
            ],
            env={
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "HOME": str(py_home),
                "PYTHONDONTWRITEBYTECODE": "1",
            },
            capture_output=True,
            text=True,
            check=True,
        )
        assert check.stdout.strip() == "OK"

    # Root-project source edits alone must preserve the key and hit the ready cache without syncing.
    (project / "src" / "wf_root" / "__init__.py").write_text("ROOT_REV = 2\n")
    from science import workflow_environment as mod

    called: list[object] = []
    monkeypatch.setattr(mod, "_run_uv_sync", lambda *a, **kw: called.append((a, kw)))
    key2 = prepare_environment(project, ops_root)
    assert key2 == key
    assert called == []


def test_stale_lock_refuses_preparation_and_leaves_no_ready_entry(tmp_path, monkeypatch):
    project, _ = _make_locked_fixture(tmp_path)
    ops_root = tmp_path / "ops"
    ops_root.mkdir()
    fixture_home = tmp_path / "fixture-home"
    fixture_home.mkdir()
    monkeypatch.setenv("HOME", str(fixture_home))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")
    monkeypatch.setenv("UV_CACHE_DIR", str(tmp_path / "empty-cache"))

    # Edit pyproject.toml to add a dependency without updating uv.lock -> stale lock.
    text = (project / "pyproject.toml").read_text()
    (project / "pyproject.toml").write_text(
        text.replace(
            'dependencies = ["wf-runtime-pkg==0.1.0"]',
            'dependencies = ["wf-runtime-pkg==0.1.0", "wf-unlocked-extra==0.1.0"]',
        )
    )

    with pytest.raises(Refused) as caught:
        prepare_environment(project, ops_root)
    assert caught.value.refusal.code == "invalid-input"
    envs_dir = ops_root / "workflow-environments"
    if envs_dir.exists():
        entries = [p for p in envs_dir.iterdir() if p.name != ".locks"]
        assert entries == []


def test_uv_invocation_argv_and_controlled_env(tmp_path, monkeypatch):
    from science import workflow_environment as mod

    project = tmp_path / "proj"
    _write_minimal_project(
        project,
        lock_text=(
            "version = 1\n"
            'requires-python = ">=3.11"\n\n'
            "[[package]]\n"
            'name = "demo"\n'
            'version = "0.1.0"\n'
            'source = { editable = "." }\n'
            'dependencies = [{ name = "alpha" }]\n\n'
            "[[package]]\n"
            'name = "alpha"\n'
            'version = "1.0.0"\n'
            'source = { registry = "https://pypi.org/simple" }\n'
            'wheels = [{ url = "https://example.invalid/alpha-1.0.0-py3-none-any.whl", hash = "sha256:' + "a" * 64 + '" }]\n'
        ),
    )
    ops_root = tmp_path / "ops"
    ops_root.mkdir()

    monkeypatch.setenv("UV_PROJECT_ENVIRONMENT", "/should/not/leak")
    monkeypatch.setenv("UV_DEFAULT_GROUPS", "all")
    monkeypatch.setenv("UV_CONFIG_FILE", "/tmp/evil-uv.toml")
    monkeypatch.setenv("VIRTUAL_ENV", "/tmp/ambient-venv")
    monkeypatch.setenv("PYTHONPATH", "/tmp/evil-pythonpath")

    recorded: dict[str, object] = {}

    def fake_run(argv, *, cwd, env, capture_output, text):
        recorded["argv"] = list(argv)
        recorded["cwd"] = cwd
        recorded["env"] = dict(env)
        venv_dir = Path(env["UV_PROJECT_ENVIRONMENT"])
        _make_fake_venv(venv_dir, Path(os.path.realpath(sys.executable)))
        return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")

    monkeypatch.setattr(mod.subprocess, "run", fake_run)
    # Hostile project uv.toml must be ignored (--no-config + UV_NO_CONFIG=1).
    (project / "uv.toml").write_text('default-groups = ["dev", "extras"]\n')

    key = prepare_environment(project, ops_root)

    argv = recorded["argv"]
    assert isinstance(argv, list)
    assert argv[1:9] == [
        "sync",
        "--no-config",
        "--locked",
        "--no-default-groups",
        "--no-install-project",
        "--no-install-workspace",
        "--no-python-downloads",
        "--link-mode=copy",
    ]
    assert "--python" in argv
    py_arg = argv[argv.index("--python") + 1]
    assert py_arg == os.path.realpath(sys.executable)

    env = recorded["env"]
    assert isinstance(env, dict)
    assert env["UV_PROJECT_ENVIRONMENT"] == str(ops_root / "workflow-environments" / key / "venv")
    assert env["UV_NO_CONFIG"] == "1"
    assert env["UV_LINK_MODE"] == "copy"
    for forbidden in ("UV_DEFAULT_GROUPS", "UV_CONFIG_FILE", "VIRTUAL_ENV", "PYTHONPATH"):
        assert forbidden not in env


def test_source_classes_admit_locked_git_and_omitted_workspace_and_reject_mutable_dir(tmp_path, monkeypatch):
    from science import workflow_environment as mod

    def fake_sync(project_dir, venv_dir, base_python):
        _make_fake_venv(venv_dir, base_python)

    monkeypatch.setattr(mod, "_run_uv_sync", fake_sync)
    ops_root = tmp_path / "ops"
    ops_root.mkdir()

    # 1. Locked Git source + omitted root + omitted workspace member -> ALLOWED.
    ok_proj = tmp_path / "ok-git-ws"
    _write_minimal_project(
        ok_proj,
        lock_text=(
            "version = 1\n"
            'requires-python = ">=3.11"\n\n'
            "[manifest]\n"
            'members = ["demo", "ws-helper"]\n\n'
            "[[package]]\n"
            'name = "demo"\n'
            'version = "0.1.0"\n'
            'source = { editable = "." }\n'
            'dependencies = [{ name = "ws-helper" }, { name = "verifiably-atoms" }]\n\n'
            "[[package]]\n"
            'name = "ws-helper"\n'
            'version = "0.1.0"\n'
            'source = { editable = "packages/ws-helper" }\n'
            'dependencies = [{ name = "alpha" }]\n\n'
            "[[package]]\n"
            'name = "verifiably-atoms"\n'
            'version = "0.1.0"\n'
            'source = { git = "https://github.com/verifiably/atoms?subdirectory=python&rev=2329cc1773bf4479e369c02e34160e824ae2b541#2329cc1773bf4479e369c02e34160e824ae2b541" }\n\n'
            "[[package]]\n"
            'name = "alpha"\n'
            'version = "1.0.0"\n'
            'source = { registry = "https://pypi.org/simple" }\n'
            'wheels = [{ url = "https://example.invalid/alpha.whl", hash = "sha256:' + "b" * 64 + '" }]\n'
        ),
    )
    key = prepare_environment(ok_proj, ops_root)
    assert WORKFLOW_ENVIRONMENT_KEY_RE.fullmatch(key)

    # 2. Required non-workspace mutable directory dependency -> REFUSED before sync.
    calls: list[object] = []
    monkeypatch.setattr(mod, "_run_uv_sync", lambda *a, **kw: calls.append(a))
    for bad_name, bad_source in [
        ("local-dir", '{ directory = "../local-pkg" }'),
        ("local-editable", '{ editable = "../local-pkg" }'),
        ("unpinned-git", '{ git = "https://github.com/example/repo?branch=main" }'),
    ]:
        bad_proj = tmp_path / f"bad-{bad_name}"
        _write_minimal_project(
            bad_proj,
            lock_text=(
                "version = 1\n"
                'requires-python = ">=3.11"\n\n'
                "[[package]]\n"
                'name = "demo"\n'
                'version = "0.1.0"\n'
                'source = { editable = "." }\n'
                'dependencies = [{ name = "local-dep" }]\n\n'
                "[[package]]\n"
                'name = "local-dep"\n'
                'version = "0.1.0"\n'
                f"source = {bad_source}\n"
            ),
        )
        with pytest.raises(Refused) as caught:
            prepare_environment(bad_proj, ops_root)
        assert caught.value.refusal.code == "invalid-input"
    assert calls == []


def test_open_environment_rejects_malformed_missing_incomplete_and_redirected_entries(tmp_path):
    ops_root = tmp_path / "ops"
    ops_root.mkdir()

    for bad_key in ("", "abc", "A" * 64, "0" * 63, "0" * 65, "../" + "0" * 61, "0" * 32 + "/" + "0" * 31):
        with pytest.raises(Refused) as caught:
            with open_environment(bad_key, ops_root):
                pass
        assert caught.value.refusal.code == "invalid-input"

    # Missing entry
    missing_key = "a" * 64
    with pytest.raises(Refused) as caught:
        with open_environment(missing_key, ops_root):
            pass
    assert caught.value.refusal.code == "invalid-input"
    assert not (ops_root / "workflow-environments").exists()

    # Incomplete entry (dir exists without ready.json)
    envs = ops_root / "workflow-environments"
    envs.mkdir()
    incomplete_key = "b" * 64
    (envs / incomplete_key / "venv").mkdir(parents=True)
    with pytest.raises(Refused) as caught:
        with open_environment(incomplete_key, ops_root):
            pass
    assert caught.value.refusal.code == "invalid-input"

    # Redirected entry (symlink to another valid entry)
    real_key = "c" * 64
    real_dir = envs / real_key
    real_dir.mkdir()
    base_py = Path(os.path.realpath(sys.executable))
    _make_fake_venv(real_dir / "venv", base_py)
    (real_dir / "ready.json").write_text(
        json.dumps({"format_version": 1, "key": real_key, "base_executable": str(base_py)}) + "\n"
    )
    redirected_key = "d" * 64
    os.symlink(real_dir, envs / redirected_key)
    with pytest.raises(Refused) as caught:
        with open_environment(redirected_key, ops_root):
            pass
    assert caught.value.refusal.code == "invalid-input"


def test_failed_install_cleans_up_and_retry_succeeds(tmp_path, monkeypatch):
    from science import workflow_environment as mod

    project = tmp_path / "proj"
    _write_minimal_project(
        project,
        lock_text=(
            "version = 1\n"
            'requires-python = ">=3.11"\n\n'
            "[[package]]\n"
            'name = "demo"\n'
            'version = "0.1.0"\n'
            'source = { editable = "." }\n'
            'dependencies = [{ name = "alpha" }]\n\n'
            "[[package]]\n"
            'name = "alpha"\n'
            'version = "1.0.0"\n'
            'source = { registry = "https://pypi.org/simple" }\n'
            'wheels = [{ url = "https://example.invalid/alpha.whl", hash = "sha256:' + "c" * 64 + '" }]\n'
        ),
    )
    ops_root = tmp_path / "ops"
    ops_root.mkdir()

    attempts = 0

    def flaky_sync(project_dir, venv_dir, base_python):
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            venv_dir.mkdir(parents=True, exist_ok=True)
            (venv_dir / "partial.txt").write_text("broken\n")
            raise Refused(Refusal_invalid("simulated uv sync failure"))
        _make_fake_venv(venv_dir, base_python)

    from science.refusal import Refusal

    def Refusal_invalid(msg: str) -> Refusal:
        return Refusal("invalid-input", msg)

    monkeypatch.setattr(mod, "_run_uv_sync", flaky_sync)

    with pytest.raises(Refused) as caught:
        prepare_environment(project, ops_root)
    assert caught.value.refusal.code == "invalid-input"
    entries = [p for p in (ops_root / "workflow-environments").iterdir() if p.name != ".locks"]
    assert entries == []

    # Hostile project uv.toml must be ignored (--no-config + UV_NO_CONFIG=1).
    (project / "uv.toml").write_text('default-groups = ["dev", "extras"]\n')

    key = prepare_environment(project, ops_root)
    assert attempts == 2
    with open_environment(key, ops_root) as venv_path:
        assert (venv_path / "bin" / "python").exists()


def test_concurrent_prepare_and_open_serialize_and_sync_once(tmp_path, monkeypatch):
    from science import workflow_environment as mod

    project = tmp_path / "proj"
    _write_minimal_project(
        project,
        lock_text=(
            "version = 1\n"
            'requires-python = ">=3.11"\n\n'
            "[[package]]\n"
            'name = "demo"\n'
            'version = "0.1.0"\n'
            'source = { editable = "." }\n'
            'dependencies = [{ name = "alpha" }]\n\n'
            "[[package]]\n"
            'name = "alpha"\n'
            'version = "1.0.0"\n'
            'source = { registry = "https://pypi.org/simple" }\n'
            'wheels = [{ url = "https://example.invalid/alpha.whl", hash = "sha256:' + "d" * 64 + '" }]\n'
        ),
    )
    ops_root = tmp_path / "ops"
    ops_root.mkdir()

    entered = threading.Event()
    release = threading.Event()
    sync_calls = 0

    def slow_sync(project_dir, venv_dir, base_python):
        nonlocal sync_calls
        sync_calls += 1
        entered.set()
        assert release.wait(timeout=5.0)
        _make_fake_venv(venv_dir, base_python)

    monkeypatch.setattr(mod, "_run_uv_sync", slow_sync)

    results: dict[str, object] = {}

    def run_prep(slot: str) -> None:
        try:
            results[slot] = prepare_environment(project, ops_root)
        except BaseException as exc:  # noqa: BLE001
            results[slot] = exc

    t1 = threading.Thread(target=run_prep, args=("p1",))
    t1.start()
    assert entered.wait(timeout=5.0)

    # Start second preparer and a reader while p1 holds exclusive lock.
    t2 = threading.Thread(target=run_prep, args=("p2",))
    t2.start()

    # Determine the key from the created lock file so the reader targets the in-flight key.
    lock_files = list((ops_root / "workflow-environments" / ".locks").glob("*.lock"))
    assert len(lock_files) == 1
    in_flight_key = lock_files[0].stem

    reader_done = threading.Event()

    def run_reader() -> None:
        try:
            with open_environment(in_flight_key, ops_root) as venv:
                results["reader"] = venv
                reader_done.set()
        except BaseException as exc:  # noqa: BLE001
            results["reader"] = exc
            reader_done.set()

    t3 = threading.Thread(target=run_reader)
    t3.start()
    time.sleep(0.15)
    assert not reader_done.is_set(), "reader must wait for exclusive build lock"

    release.set()
    t1.join(timeout=5.0)
    t2.join(timeout=5.0)
    t3.join(timeout=5.0)

    assert sync_calls == 1
    assert results["p1"] == in_flight_key
    assert results["p2"] == in_flight_key
    assert results["reader"] == ops_root / "workflow-environments" / in_flight_key / "venv"


def test_frozen_inputs_modified_during_sync_refuse_before_readiness(tmp_path, monkeypatch):
    from science import workflow_environment as mod

    project = tmp_path / "proj"
    _write_minimal_project(
        project,
        lock_text=(
            "version = 1\n"
            'requires-python = ">=3.11"\n\n'
            "[[package]]\n"
            'name = "demo"\n'
            'version = "0.1.0"\n'
            'source = { editable = "." }\n'
            'dependencies = [{ name = "alpha" }]\n\n'
            "[[package]]\n"
            'name = "alpha"\n'
            'version = "1.0.0"\n'
            'source = { registry = "https://pypi.org/simple" }\n'
            'wheels = [{ url = "https://example.invalid/alpha.whl", hash = "sha256:' + "e" * 64 + '" }]\n'
        ),
    )
    ops_root = tmp_path / "ops"
    ops_root.mkdir()

    def mutating_sync(project_dir, venv_dir, base_python):
        _make_fake_venv(venv_dir, base_python)
        (project_dir / "pyproject.toml").write_text((project_dir / "pyproject.toml").read_text() + "# mutated\n")

    monkeypatch.setattr(mod, "_run_uv_sync", mutating_sync)
    with pytest.raises(Refused) as caught:
        prepare_environment(project, ops_root)
    assert caught.value.refusal.code == "invalid-input"
    entries = [p for p in (ops_root / "workflow-environments").iterdir() if p.name != ".locks"]
    assert entries == []


def test_workspace_member_extra_mutable_dependency_is_refused(tmp_path, monkeypatch):
    from science import workflow_environment as mod

    calls: list[object] = []
    monkeypatch.setattr(mod, "_run_uv_sync", lambda *a, **kw: calls.append(a))
    ops_root = tmp_path / "ops"
    ops_root.mkdir()
    proj = tmp_path / "ws-extra-bad"
    _write_minimal_project(
        proj,
        lock_text=(
            "version = 1\n"
            'requires-python = ">=3.11"\n\n'
            "[manifest]\n"
            'members = ["demo", "ws-helper"]\n\n'
            "[[package]]\n"
            'name = "demo"\n'
            'version = "0.1.0"\n'
            'source = { editable = "." }\n'
            'dependencies = [{ name = "ws-helper", extra = ["extras"] }]\n\n'
            "[[package]]\n"
            'name = "ws-helper"\n'
            'version = "0.1.0"\n'
            'source = { editable = "packages/ws-helper" }\n\n'
            "[package.optional-dependencies]\n"
            'extras = [{ name = "local-dep" }]\n\n'
            "[[package]]\n"
            'name = "local-dep"\n'
            'version = "0.1.0"\n'
            'source = { directory = "../local-dep" }\n'
        ),
    )
    with pytest.raises(Refused) as caught:
        prepare_environment(proj, ops_root)
    assert caught.value.refusal.code == "invalid-input"
    assert calls == []


def test_prepared_environments_use_copy_mode_and_isolate_cache_across_keys(tmp_path, monkeypatch):
    wheels = tmp_path / "wheels"
    shared_whl = _build_wheel(
        wheels,
        "wf-shared-copy",
        "0.1.0",
        {"wf_shared_copy/__init__.py": "VALUE = 'original'\n"},
    )
    private_cache = tmp_path / "private-uv-cache"
    fixture_home = tmp_path / "fixture-home"
    fixture_home.mkdir()
    monkeypatch.setenv("UV_CACHE_DIR", str(private_cache))
    monkeypatch.setenv("HOME", str(fixture_home))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")

    def _make_proj(name: str, version: str) -> Path:
        proj = tmp_path / name
        proj.mkdir()
        (proj / "pyproject.toml").write_text(
            f'[project]\nname = "{name}"\nversion = "{version}"\n'
            'requires-python = ">=3.11"\n'
            'dependencies = ["wf-shared-copy==0.1.0"]\n\n'
            "[tool.uv.sources]\n"
            f'wf-shared-copy = {{ path = "{shared_whl}" }}\n'
        )
        lock_res = subprocess.run(
            ["uv", "lock", "--no-config", "--offline"],
            cwd=proj,
            env={
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "HOME": str(fixture_home),
                "UV_CACHE_DIR": str(private_cache),
            },
            capture_output=True,
            text=True,
        )
        assert lock_res.returncode == 0, lock_res.stderr
        return proj

    proj1 = _make_proj("copy-proj-one", "0.1.0")
    proj2 = _make_proj("copy-proj-two", "0.2.0")
    ops_root = tmp_path / "ops"
    ops_root.mkdir()

    key1 = prepare_environment(proj1, ops_root)
    with open_environment(key1, ops_root) as venv1:
        installed1 = list(venv1.rglob("wf_shared_copy/__init__.py"))
        assert len(installed1) == 1
        assert installed1[0].stat().st_nlink == 1, "prepared module must not be hard-linked to uv cache"
        # In-place edit on key1 must not mutate the private uv cache.
        installed1[0].write_text("VALUE = 'mutated-in-key1'\n")

    key2 = prepare_environment(proj2, ops_root)
    assert key2 != key1
    with open_environment(key2, ops_root) as venv2:
        installed2 = list(venv2.rglob("wf_shared_copy/__init__.py"))
        assert len(installed2) == 1
        assert installed2[0].stat().st_nlink == 1
        assert installed2[0].read_text() == "VALUE = 'original'\n"


def test_workspace_stale_lock_refuses_even_after_warm_cache_and_direct_open_still_works(tmp_path, monkeypatch):
    from science import workflow_environment as mod

    wheels = tmp_path / "wheels"
    runtime_whl = _build_wheel(
        wheels,
        "wf-ws-runtime",
        "0.1.0",
        {"wf_ws_runtime/__init__.py": "WS_TOKEN = 'v1'\n"},
    )
    private_cache = tmp_path / "ws-uv-cache"
    fixture_home = tmp_path / "ws-home"
    fixture_home.mkdir()
    monkeypatch.setenv("UV_CACHE_DIR", str(private_cache))
    monkeypatch.setenv("HOME", str(fixture_home))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")
    monkeypatch.setenv("GIT_CONFIG_NOSYSTEM", "1")

    project = tmp_path / "ws-root"
    member_dir = project / "packages" / "ws-member"
    (member_dir / "src" / "ws_member").mkdir(parents=True)
    (member_dir / "src" / "ws_member" / "__init__.py").write_text("MEMBER_REV = 1\n")
    (member_dir / "pyproject.toml").write_text(
        "[project]\n"
        'name = "ws-member"\n'
        'version = "0.1.0"\n'
        'requires-python = ">=3.11"\n'
        'dependencies = ["wf-ws-runtime==0.1.0"]\n\n'
        "[build-system]\n"
        'requires = ["hatchling"]\n'
        'build-backend = "hatchling.build"\n\n'
        "[tool.hatch.build.targets.wheel]\n"
        'packages = ["src/ws_member"]\n'
    )
    (project / "pyproject.toml").write_text(
        "[project]\n"
        'name = "ws-root"\n'
        'version = "0.1.0"\n'
        'requires-python = ">=3.11"\n'
        'dependencies = ["ws-member"]\n\n'
        "[tool.uv.workspace]\n"
        'members = ["packages/*"]\n\n'
        "[tool.uv.sources]\n"
        'ws-member = { workspace = true }\n'
        f'wf-ws-runtime = {{ path = "{runtime_whl}" }}\n'
    )
    lock_res = subprocess.run(
        ["uv", "lock", "--no-config", "--offline"],
        cwd=project,
        env={
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(fixture_home),
            "UV_CACHE_DIR": str(private_cache),
        },
        capture_output=True,
        text=True,
    )
    assert lock_res.returncode == 0, lock_res.stderr

    ops_root = tmp_path / "ops"
    ops_root.mkdir()
    key1 = prepare_environment(project, ops_root)
    assert WORKFLOW_ENVIRONMENT_KEY_RE.fullmatch(key1)

    # Editing member Python source preserves key and hits warm cache with zero syncs.
    (member_dir / "src" / "ws_member" / "__init__.py").write_text("MEMBER_REV = 2\n")
    sync_calls: list[object] = []
    real_sync = mod._run_uv_sync
    monkeypatch.setattr(mod, "_run_uv_sync", lambda *a, **kw: sync_calls.append(a))
    assert prepare_environment(project, ops_root) == key1
    assert sync_calls == []
    monkeypatch.setattr(mod, "_run_uv_sync", real_sync)

    # Bumping member version in pyproject.toml without re-locking makes the lock stale;
    # warm cache must NOT mask it, while direct open_environment(key1, ops_root) still works.
    member_toml = member_dir / "pyproject.toml"
    member_toml.write_text(member_toml.read_text().replace('version = "0.1.0"', 'version = "0.2.0"'))
    with pytest.raises(Refused) as stale:
        prepare_environment(project, ops_root)
    assert stale.value.refusal.code == "invalid-input"

    with open_environment(key1, ops_root) as venv_path:
        assert (venv_path / "bin" / "python").exists()


@pytest.mark.parametrize("setting", [None, "true"])
def test_open_environment_rejects_omitted_or_true_system_site_packages(tmp_path, setting):
    ops_root = tmp_path / "ops"
    key = "e" * 64
    entry_dir = ops_root / "workflow-environments" / key
    venv_dir = entry_dir / "venv"
    base_py = Path(os.path.realpath(sys.executable))
    _make_fake_venv(venv_dir, base_py)
    cfg_lines = [
        f"home = {base_py.parent}",
        f"version_info = {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    ]
    if setting is not None:
        cfg_lines.append(f"include-system-site-packages = {setting}")
    (venv_dir / "pyvenv.cfg").write_text("\n".join(cfg_lines) + "\n")
    (entry_dir / "ready.json").write_text(
        json.dumps(
            {
                "base_executable": str(base_py),
                "base_prefix": os.path.realpath(sys.base_prefix),
                "format_version": 1,
                "key": key,
            }
        )
        + "\n"
    )
    with pytest.raises(Refused) as caught:
        with open_environment(key, ops_root):
            pass
    assert caught.value.refusal.code == "invalid-input"
