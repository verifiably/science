"""Prepare and open immutable locked uv workflow environments in operations storage."""
from __future__ import annotations

import errno
import fcntl
import hashlib
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import tomllib
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import NoReturn

from science.refusal import Refusal, Refused

WORKFLOW_ENVIRONMENT_KEY_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_PINNED_REV_RE = re.compile(r"#[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

KEY_FORMAT_VERSION = 1
READY_FORMAT_VERSION = 1
WORKFLOW_ENVIRONMENTS_DIR = "workflow-environments"
LOCKS_DIR = ".locks"
READY_FILENAME = "ready.json"
INSTALL_FLAGS = (
    "--no-config",
    "--locked",
    "--no-default-groups",
    "--no-install-project",
    "--no-install-workspace",
    "--no-python-downloads",
)
_PASSTHROUGH_ENV_KEYS = (
    "PATH",
    "HOME",
    "UV_CACHE_DIR",
    "XDG_CACHE_HOME",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
    "REQUESTS_CA_BUNDLE",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "no_proxy",
    "LANG",
    "LC_ALL",
)


def _invalid(message: str) -> NoReturn:
    raise Refused(Refusal("invalid-input", message))


def validate_key(key: object) -> str:
    if type(key) is not str or WORKFLOW_ENVIRONMENT_KEY_RE.fullmatch(key) is None:
        _invalid("workflow_environment must be 64 lowercase hexadecimal digits")
    return key


def _base_python() -> Path:
    resolved = Path(os.path.realpath(sys.executable))
    if not resolved.is_file():
        _invalid(f"base Python executable is missing: {resolved}")
    return resolved


def _base_interpreter_identity(base_python: Path) -> dict[str, object]:
    try:
        binary_digest = hashlib.sha256(base_python.read_bytes()).hexdigest()
    except OSError as exc:
        _invalid(f"cannot read base Python executable {base_python}: {exc}")
    return {
        "base_prefix": os.path.realpath(sys.base_prefix),
        "executable": str(base_python),
        "executable_sha256": binary_digest,
        "version": sys.version,
    }


def _compute_key(pyproject_bytes: bytes, lock_bytes: bytes, base_identity: Mapping[str, object]) -> str:
    payload = {
        "base_interpreter": dict(base_identity),
        "format_version": KEY_FORMAT_VERSION,
        "install_flags": list(INSTALL_FLAGS),
        "lock_sha256": hashlib.sha256(lock_bytes).hexdigest(),
        "pyproject_sha256": hashlib.sha256(pyproject_bytes).hexdigest(),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _read_regular_file(path: Path, label: str) -> bytes:
    try:
        st = path.stat()
    except OSError as exc:
        _invalid(f"workflow project {label} is missing or unreadable ({path}): {exc}")
    if not stat.S_ISREG(st.st_mode):
        _invalid(f"workflow project {label} is not a regular file: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        _invalid(f"cannot read workflow project {label} ({path}): {exc}")


def _has_sha256_artifact(pkg: Mapping[str, object]) -> bool:
    sdist = pkg.get("sdist")
    if isinstance(sdist, Mapping):
        digest = sdist.get("hash")
        if isinstance(digest, str) and _SHA256_RE.fullmatch(digest):
            return True
    wheels = pkg.get("wheels")
    if isinstance(wheels, list):
        for wheel in wheels:
            if isinstance(wheel, Mapping):
                digest = wheel.get("hash")
                if isinstance(digest, str) and _SHA256_RE.fullmatch(digest):
                    return True
    return False


def _is_root_source(source: object) -> bool:
    if not isinstance(source, Mapping) or len(source) != 1:
        return False
    (kind, target), = source.items()
    return kind in ("editable", "virtual", "directory") and target == "."


def _is_omitted_workspace_member(pkg: Mapping[str, object], workspace_members: set[str]) -> bool:
    name = pkg.get("name")
    source = pkg.get("source")
    if not isinstance(name, str) or name not in workspace_members:
        return False
    if not isinstance(source, Mapping) or len(source) != 1:
        return False
    (kind,) = source.keys()
    return kind in ("editable", "virtual", "directory")


def _validate_installed_source(pkg: Mapping[str, object], project: Path) -> None:
    name = pkg.get("name", "<unknown>")
    source = pkg.get("source")
    if not isinstance(source, Mapping) or len(source) != 1:
        _invalid(f"workflow dependency {name!r} has malformed source in uv.lock")
    (kind, target), = source.items()
    if kind == "registry":
        if not isinstance(target, str) or not target:
            _invalid(f"workflow dependency {name!r} has empty registry source")
        return
    if kind == "git":
        if not isinstance(target, str) or _GIT_PINNED_REV_RE.search(target) is None:
            _invalid(f"workflow dependency {name!r} uses an unpinned git source: {target!r}")
        return
    if kind == "url":
        if not isinstance(target, str) or not target or not _has_sha256_artifact(pkg):
            _invalid(f"workflow dependency {name!r} uses an unhashed URL source: {target!r}")
        return
    if kind == "path":
        if not isinstance(target, str) or not target or not _has_sha256_artifact(pkg):
            _invalid(f"workflow dependency {name!r} uses an unhashed or mutable local path source: {target!r}")
        candidate = Path(target)
        if not candidate.is_absolute():
            candidate = project / candidate
        if candidate.is_dir():
            _invalid(f"workflow dependency {name!r} points to a mutable local directory: {target!r}")
        return
    if kind in ("directory", "editable", "virtual"):
        _invalid(f"workflow dependency {name!r} requires a mutable local directory ({kind}={target!r})")
    _invalid(f"workflow dependency {name!r} uses unsupported source class {kind!r}")


def _validate_project_inputs(project: Path) -> tuple[bytes, bytes]:
    if not isinstance(project, Path):
        _invalid("workflow project must be a filesystem path")
    if not project.exists() or not project.is_dir():
        _invalid(f"workflow project is not an existing directory: {project}")
    pyproject_bytes = _read_regular_file(project / "pyproject.toml", "pyproject.toml")
    lock_bytes = _read_regular_file(project / "uv.lock", "uv.lock")
    try:
        tomllib.loads(pyproject_bytes.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        _invalid(f"workflow project pyproject.toml is invalid: {exc}")
    try:
        lock_data = tomllib.loads(lock_bytes.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        _invalid(f"workflow project uv.lock is invalid: {exc}")

    packages = lock_data.get("package")
    if not isinstance(packages, list) or not all(isinstance(p, dict) for p in packages):
        _invalid("workflow project uv.lock has malformed package entries")

    manifest = lock_data.get("manifest")
    workspace_members: set[str] = set()
    if isinstance(manifest, dict):
        members = manifest.get("members")
        if isinstance(members, list):
            workspace_members = {m for m in members if isinstance(m, str)}

    by_name: dict[str, list[dict[str, object]]] = {}
    roots: list[dict[str, object]] = []
    for pkg in packages:
        name = pkg.get("name")
        if isinstance(name, str):
            by_name.setdefault(name, []).append(pkg)
        if _is_root_source(pkg.get("source")):
            roots.append(pkg)

    if not roots:
        _invalid("workflow project uv.lock has no root project entry")

    # Walk only runtime dependencies (excluding dev-dependencies and optional-dependencies).
    visited: set[int] = set()
    queue: list[dict[str, object]] = list(roots)
    while queue:
        current = queue.pop()
        obj_id = id(current)
        if obj_id in visited:
            continue
        visited.add(obj_id)

        omitted = _is_root_source(current.get("source")) or _is_omitted_workspace_member(current, workspace_members)
        if not omitted:
            _validate_installed_source(current, project)

        deps = current.get("dependencies")
        if not isinstance(deps, list):
            continue
        for dep in deps:
            if not isinstance(dep, dict):
                continue
            dep_name = dep.get("name")
            if not isinstance(dep_name, str):
                continue
            dep_version = dep.get("version")
            dep_source = dep.get("source")
            candidates = by_name.get(dep_name, [])
            for candidate in candidates:
                if dep_version is not None and candidate.get("version") != dep_version:
                    continue
                if dep_source is not None and candidate.get("source") != dep_source:
                    continue
                queue.append(candidate)

    return pyproject_bytes, lock_bytes


def _open_dir_nofollow(path: str | Path, *, dir_fd: int | None = None, label: str) -> int:
    try:
        if dir_fd is None:
            return os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        return os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=dir_fd)
    except FileNotFoundError:
        raise
    except OSError as exc:
        if exc.errno in (errno.ELOOP, errno.ENOTDIR):
            _invalid(f"workflow environment {label} redirects through a symlink or is not a directory")
        _invalid(f"cannot open workflow environment {label}: {exc}")


def _ensure_dir_nofollow(parent_fd: int, name: str, *, mode: int = 0o700, label: str) -> int:
    try:
        os.mkdir(name, mode, dir_fd=parent_fd)
    except FileExistsError:
        pass
    except OSError as exc:
        _invalid(f"cannot create workflow environment {label}: {exc}")
    try:
        return _open_dir_nofollow(name, dir_fd=parent_fd, label=label)
    except FileNotFoundError as exc:
        _invalid(f"workflow environment {label} disappeared during creation: {exc}")


def _parse_pyvenv_cfg(raw: bytes) -> dict[str, str]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        _invalid(f"pyvenv.cfg is not valid UTF-8: {exc}")
    cfg: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        k, _, v = stripped.partition("=")
        cfg[k.strip().lower()] = v.strip()
    return cfg


def _validate_ready_entry(entry_fd: int, entry_dir: Path, key: str, base_python: Path) -> Path:
    try:
        ready_fd = os.open(READY_FILENAME, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=entry_fd)
    except FileNotFoundError:
        _invalid(f"workflow environment {key} is incomplete (missing readiness marker)")
    except OSError as exc:
        _invalid(f"workflow environment {key} readiness marker is invalid: {exc}")
    try:
        st = os.fstat(ready_fd)
        if not stat.S_ISREG(st.st_mode):
            _invalid(f"workflow environment {key} readiness marker is not a regular file")
        with os.fdopen(ready_fd, "rb") as handle:
            ready_fd = -1
            raw_ready = handle.read()
    finally:
        if ready_fd >= 0:
            os.close(ready_fd)

    try:
        ready = json.loads(raw_ready.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        _invalid(f"workflow environment {key} readiness marker is malformed: {exc}")
    if (
        not isinstance(ready, dict)
        or ready.get("format_version") != READY_FORMAT_VERSION
        or ready.get("key") != key
        or ready.get("base_executable") != str(base_python)
    ):
        _invalid(f"workflow environment {key} readiness marker does not match this runtime")
    expected_prefix = os.path.realpath(sys.base_prefix)
    if "base_prefix" in ready and ready.get("base_prefix") != expected_prefix:
        _invalid(f"workflow environment {key} readiness marker base prefix mismatch")

    return _validate_venv_layout(entry_fd, entry_dir, key, base_python)


def _validate_venv_layout(entry_fd: int, entry_dir: Path, key: str, base_python: Path) -> Path:
    try:
        venv_fd = _open_dir_nofollow("venv", dir_fd=entry_fd, label=f"{key}/venv")
    except FileNotFoundError:
        _invalid(f"workflow environment {key} is missing its venv directory")
    try:
        try:
            cfg_fd = os.open("pyvenv.cfg", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=venv_fd)
        except OSError as exc:
            _invalid(f"workflow environment {key} is missing pyvenv.cfg: {exc}")
        try:
            if not stat.S_ISREG(os.fstat(cfg_fd).st_mode):
                _invalid(f"workflow environment {key} pyvenv.cfg is not a regular file")
            with os.fdopen(cfg_fd, "rb") as handle:
                cfg_fd = -1
                cfg = _parse_pyvenv_cfg(handle.read())
        finally:
            if cfg_fd >= 0:
                os.close(cfg_fd)

        if cfg.get("include-system-site-packages", "false").lower() != "false":
            _invalid(f"workflow environment {key} enables system site-packages")
        home = cfg.get("home")
        if not home or Path(os.path.realpath(home)) != base_python.parent:
            _invalid(f"workflow environment {key} base home does not match {base_python.parent}")

        try:
            bin_fd = _open_dir_nofollow("bin", dir_fd=venv_fd, label=f"{key}/venv/bin")
        except FileNotFoundError:
            _invalid(f"workflow environment {key} is missing venv/bin")
        try:
            try:
                os.lstat("python", dir_fd=bin_fd)
            except OSError as exc:
                _invalid(f"workflow environment {key} is missing venv/bin/python: {exc}")
        finally:
            os.close(bin_fd)
    finally:
        os.close(venv_fd)

    venv_dir = entry_dir / "venv"
    if Path(os.path.realpath(venv_dir / "bin" / "python")) != base_python:
        _invalid(f"workflow environment {key} interpreter does not resolve to {base_python}")
    return venv_dir


def _write_ready_marker(entry_fd: int, key: str, base_python: Path) -> None:
    payload = (
        json.dumps(
            {
                "base_executable": str(base_python),
                "base_prefix": os.path.realpath(sys.base_prefix),
                "format_version": READY_FORMAT_VERSION,
                "key": key,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    tmp_name = f".ready.{os.getpid()}.{secrets.token_hex(8)}.tmp"
    fd = os.open(tmp_name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=entry_fd)
    try:
        with os.fdopen(fd, "wb") as handle:
            fd = -1
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, READY_FILENAME, src_dir_fd=entry_fd, dst_dir_fd=entry_fd)
        os.fsync(entry_fd)
    except BaseException:
        if fd >= 0:
            os.close(fd)
        try:
            os.unlink(tmp_name, dir_fd=entry_fd)
        except OSError:
            pass
        raise


def _uv_command() -> tuple[str, ...]:
    uv_bin = shutil.which("uv")
    if uv_bin is None:
        _invalid("uv executable is not available on PATH")
    return (uv_bin,)


def _controlled_uv_env(venv_dir: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    for key in _PASSTHROUGH_ENV_KEYS:
        val = os.environ.get(key)
        if val is not None:
            env[key] = val
    env.setdefault("PATH", "/usr/bin:/bin")
    env["UV_PROJECT_ENVIRONMENT"] = str(venv_dir)
    env["UV_NO_CONFIG"] = "1"
    env["UV_PYTHON_DOWNLOADS"] = "never"
    env["UV_NO_SYNC"] = "0"
    return env


def _run_uv_sync(project: Path, venv_dir: Path, base_python: Path) -> None:
    argv = [
        *_uv_command(),
        "sync",
        *INSTALL_FLAGS,
        "--python",
        str(base_python),
    ]
    env = _controlled_uv_env(venv_dir)
    try:
        result = subprocess.run(argv, cwd=project, env=env, capture_output=True, text=True)
    except OSError as exc:
        _invalid(f"failed to invoke uv sync: {exc}")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip().splitlines()
        summary = " | ".join(detail[-4:]) if detail else f"exit code {result.returncode}"
        _invalid(f"uv sync failed for workflow project {project}: {summary}")


def prepare_environment(project: Path, operations_root: Path) -> str:
    """Prepare an immutable locked workflow venv under operations storage and return its key."""
    project = Path(project)
    operations_root = Path(operations_root)
    pyproject_bytes, lock_bytes = _validate_project_inputs(project)
    base_python = _base_python()
    base_identity = _base_interpreter_identity(base_python)
    key = _compute_key(pyproject_bytes, lock_bytes, base_identity)

    if operations_root.is_symlink():
        _invalid(f"operations_root redirects through a symlink: {operations_root}")
    operations_root.mkdir(parents=True, exist_ok=True)

    ops_fd = _open_dir_nofollow(operations_root, label="operations_root")
    try:
        envs_fd = _ensure_dir_nofollow(ops_fd, WORKFLOW_ENVIRONMENTS_DIR, label=WORKFLOW_ENVIRONMENTS_DIR)
        try:
            locks_fd = _ensure_dir_nofollow(envs_fd, LOCKS_DIR, label=LOCKS_DIR)
            try:
                try:
                    lock_fd = os.open(
                        f"{key}.lock",
                        os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW,
                        0o600,
                        dir_fd=locks_fd,
                    )
                except OSError as exc:
                    _invalid(f"cannot open workflow environment lock for {key}: {exc}")
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_EX)
                    entry_dir = operations_root / WORKFLOW_ENVIRONMENTS_DIR / key

                    # Check for existing entry under exclusive lock.
                    existing_stat = None
                    try:
                        existing_stat = os.lstat(key, dir_fd=envs_fd)
                    except FileNotFoundError:
                        existing_stat = None
                    if existing_stat is not None:
                        if stat.S_ISLNK(existing_stat.st_mode):
                            _invalid(f"workflow environment entry {key} redirects through a symlink")
                        if stat.S_ISDIR(existing_stat.st_mode):
                            try:
                                existing_fd = _open_dir_nofollow(key, dir_fd=envs_fd, label=key)
                            except FileNotFoundError:
                                existing_fd = -1
                            if existing_fd >= 0:
                                try:
                                    _validate_ready_entry(existing_fd, entry_dir, key, base_python)
                                    return key
                                except Refused:
                                    pass
                                finally:
                                    os.close(existing_fd)
                            shutil.rmtree(entry_dir)
                        else:
                            os.unlink(key, dir_fd=envs_fd)

                    os.mkdir(key, 0o700, dir_fd=envs_fd)
                    entry_fd = _open_dir_nofollow(key, dir_fd=envs_fd, label=key)
                    succeeded = False
                    try:
                        venv_dir = entry_dir / "venv"
                        _run_uv_sync(project, venv_dir, base_python)

                        # Re-read frozen inputs and confirm they still match the computed key.
                        after_pyproject = _read_regular_file(project / "pyproject.toml", "pyproject.toml")
                        after_lock = _read_regular_file(project / "uv.lock", "uv.lock")
                        if after_pyproject != pyproject_bytes or after_lock != lock_bytes:
                            _invalid("workflow project pyproject.toml or uv.lock changed during preparation")

                        _validate_venv_layout(entry_fd, entry_dir, key, base_python)
                        _write_ready_marker(entry_fd, key, base_python)
                        succeeded = True
                    finally:
                        os.close(entry_fd)
                        if not succeeded:
                            shutil.rmtree(entry_dir, ignore_errors=True)
                    return key
                finally:
                    try:
                        fcntl.flock(lock_fd, fcntl.LOCK_UN)
                    finally:
                        os.close(lock_fd)
            finally:
                os.close(locks_fd)
        finally:
            os.close(envs_fd)
    finally:
        os.close(ops_fd)


@contextmanager
def open_environment(key: str, operations_root: Path) -> Iterator[Path]:
    """Hold a shared lock on a ready prepared workflow environment and yield its venv path."""
    validated_key = validate_key(key)
    operations_root = Path(operations_root)
    base_python = _base_python()

    try:
        ops_fd = _open_dir_nofollow(operations_root, label="operations_root")
    except FileNotFoundError:
        _invalid(f"workflow environment {validated_key} is not prepared")
    try:
        try:
            envs_fd = _open_dir_nofollow(WORKFLOW_ENVIRONMENTS_DIR, dir_fd=ops_fd, label=WORKFLOW_ENVIRONMENTS_DIR)
        except FileNotFoundError:
            _invalid(f"workflow environment {validated_key} is not prepared")
        try:
            lock_fd = _open_shared_lock(envs_fd, validated_key)
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_SH)
                try:
                    entry_fd = _open_dir_nofollow(validated_key, dir_fd=envs_fd, label=validated_key)
                except FileNotFoundError:
                    _invalid(f"workflow environment {validated_key} is not prepared")
                try:
                    entry_dir = operations_root / WORKFLOW_ENVIRONMENTS_DIR / validated_key
                    venv_dir = _validate_ready_entry(entry_fd, entry_dir, validated_key, base_python)
                finally:
                    os.close(entry_fd)
                yield venv_dir
            finally:
                try:
                    fcntl.flock(lock_fd, fcntl.LOCK_UN)
                finally:
                    os.close(lock_fd)
        finally:
            os.close(envs_fd)
    finally:
        os.close(ops_fd)


def _open_shared_lock(envs_fd: int, key: str) -> int:
    try:
        locks_fd = _open_dir_nofollow(LOCKS_DIR, dir_fd=envs_fd, label=LOCKS_DIR)
    except FileNotFoundError:
        locks_fd = -1

    if locks_fd >= 0:
        try:
            try:
                return os.open(f"{key}.lock", os.O_RDONLY | os.O_NOFOLLOW, dir_fd=locks_fd)
            except FileNotFoundError:
                pass
            except OSError as exc:
                _invalid(f"workflow environment lock for {key} is invalid: {exc}")
        finally:
            os.close(locks_fd)

    # No existing lock file: check whether the entry itself exists before creating a lock.
    try:
        st = os.lstat(key, dir_fd=envs_fd)
    except FileNotFoundError:
        _invalid(f"workflow environment {key} is not prepared")
    if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode):
        _invalid(f"workflow environment {key} redirects through a symlink or is not a directory")

    locks_fd = _ensure_dir_nofollow(envs_fd, LOCKS_DIR, label=LOCKS_DIR)
    try:
        try:
            return os.open(f"{key}.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600, dir_fd=locks_fd)
        except OSError as exc:
            _invalid(f"cannot open workflow environment lock for {key}: {exc}")
    finally:
        os.close(locks_fd)
