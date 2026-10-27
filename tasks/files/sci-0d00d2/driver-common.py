"""Shared pieces of the second-project milestone drivers (sci-0d00d2).

Nothing here is mutable: every attempt's journals, declarations, frozen queries
and outputs live in its own state directory, bound by `world.json` to one world
and one config. Drivers run under the worktree's interpreter
(`<wt>/python/.venv/bin/python`) and run that same environment's `science` by
explicit path; nothing is read from the working directory.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from beliefs.permit import Authority, WritePermit

AUTHORITY = Authority(WritePermit.full(), "sci-0d00d2-driver")
DRIVER = Path(__file__).resolve().parent
TASK_DIR = DRIVER.parent


class DriverStop(SystemExit):
    """A refusal by the driver itself, before any effect it names."""

    def __init__(self, code: int, message: str):
        super().__init__(code)
        self.message = message


def stop(message: str, code: int = 2):
    # stdout as well as stderr, so a drill's captured output carries the deciding line.
    print(f"stop: {message}", flush=True)
    print(f"stop: {message}", file=sys.stderr, flush=True)
    raise DriverStop(code, message)


def now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def read_json(path: Path):
    return json.loads(path.read_text())


def wt() -> Path:
    # <wt>/python/.venv/bin/python: the worktree the interpreter belongs to.
    return Path(sys.executable).parents[3]


def science_bin(worktree: Path | None = None) -> Path:
    return (wt() if worktree is None else worktree) / "python" / ".venv" / "bin" / "science"


def environment(config: Path) -> dict[str, str]:
    # Built key by key: the CLI and the server read their config from here and nothing else.
    return {"PATH": os.environ["PATH"], "HOME": os.environ["HOME"], "SCIENCE_CONFIG": str(config)}


def run_cli(config: Path, args: list[str], *, cwd: Path, timeout: float = 120, check: bool = True) -> str:
    started = time.monotonic()
    done = subprocess.run(
        [str(science_bin()), *args], cwd=cwd, env=environment(config), stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=timeout,
    )
    if check and done.returncode != 0:
        stop(f"`science {' '.join(args)}` exited {done.returncode} after {time.monotonic() - started:.1f}s:\n"
             f"{done.stdout}{done.stderr}")
    return done.stdout


def run_cli_full(config: Path, args: list[str], *, cwd: Path, timeout: float = 120) -> subprocess.CompletedProcess:
    return subprocess.run(
        [str(science_bin()), *args], cwd=cwd, env=environment(config), stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=timeout,
    )


class State:
    """One attempt's state directory: `world.json` binds it to a world and config."""

    def __init__(self, path: Path):
        self.path = Path(path).resolve()
        marker = self.path / "world.json"
        if not marker.is_file():
            stop(f"{self.path} has no world.json; genesis creates it")
        self.world = read_json(marker)
        self.config = Path(self.world["config"])
        self.data_root = Path(self.world["data_root"])
        self.queries = self.path / "queries"
        self.runs = self.path / "runs"

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def declared(self) -> dict | None:
        path = self.path / "declared.json"
        return read_json(path) if path.is_file() else None

    @classmethod
    def create(cls, path: Path, *, world_id: str, data_root: Path, config: Path) -> State:
        path = Path(path).resolve()
        if (path / "world.json").exists():
            stop(f"{path}/world.json exists; a state is created once")
        path.mkdir(parents=True, exist_ok=True)
        write_json(path / "world.json", {
            "world_id": world_id, "config": str(Path(config).resolve()),
            "data_root": str(Path(data_root).resolve()), "created_at": now(),
        })
        return cls(path)

    def load_config(self):
        """The config, refused unless it names the world this state is bound to."""
        from science.config import load_config

        if not self.config.is_file():
            stop(f"{self.config} does not exist")
        cfg = load_config(self.config)
        if cfg.world.world_id != self.world["world_id"]:
            stop(f"{self.config} names world {cfg.world.world_id}; {self.path} is bound to {self.world['world_id']}")
        return cfg


class Journal:
    """Two-phase journal, one JSON row per line, each fsynced. The first row binds it
    to one world and config; a journal bound elsewhere is refused."""

    def __init__(self, path: Path, *, world_id: str, config: Path):
        self.path = Path(path)
        header = {"journal": "sci-0d00d2", "world_id": world_id, "config": str(Path(config).resolve())}
        if self.path.exists():
            rows = self._read()
            if not rows or {k: rows[0].get(k) for k in header} != header:
                stop(f"{self.path} is bound to {rows[0] if rows else 'nothing'}, not {header}")
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._append({**header, "at": now()})

    def _read(self) -> list[dict]:
        return [json.loads(line) for line in self.path.read_text().splitlines() if line.strip()]

    def _append(self, row: dict) -> None:
        with self.path.open("a") as handle:
            handle.write(json.dumps(row, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())

    @property
    def rows(self) -> list[dict]:
        return [row for row in self._read() if "key" in row]

    def attempt(self, key: str) -> None:
        self._append({"key": key, "phase": "attempt", "at": now()})

    def record(self, key: str, *, identity: str | None = None, invocation_id: str | None = None,
               seconds: float | None = None, **extra) -> None:
        self._append({"key": key, "phase": "record", "at": now(), "identity": identity,
                      "invocation_id": invocation_id, "seconds": seconds, **extra})

    def reconcile(self, key: str, identity: str | None) -> None:
        self._append({"key": key, "phase": "reconcile", "at": now(), "identity": identity})

    def select(self, key: str, target: str | None, *, invocation_id: str | None = None,
               seconds: float | None = None) -> None:
        self._append({"key": key, "phase": "select", "at": now(), "target": target,
                      "invocation_id": invocation_id, "seconds": seconds})

    def stopped(self, key: str, reason: str) -> None:
        self._append({"key": key, "phase": "stop", "at": now(), "reason": reason})

    def refused(self, key: str, refusal: dict) -> None:
        # A refusal reply is certain: nothing was minted, so the key is unjournaled again.
        self._append({"key": key, "phase": "refused", "at": now(), "refusal": refusal})

    def _last(self, key: str) -> dict | None:
        rows = [row for row in self.rows
                if row["key"] == key and row["phase"] in {"attempt", "record", "reconcile", "refused"}]
        return rows[-1] if rows else None

    def status(self, key: str) -> str | None:
        """`recorded`, `reconciled` (a person found the identity), `attempted` (uncertain),
        or None: never tried, refused, or reconciled as `none` (nothing was minted)."""
        last = self._last(key)
        if last is None or last["phase"] == "refused":
            return None
        if last["phase"] == "reconcile":
            return None if last["identity"] is None else "reconciled"
        return {"attempt": "attempted", "record": "recorded"}[last["phase"]]

    def selected(self, key: str) -> bool:
        return any(row["key"] == key and row["phase"] == "select" for row in self.rows)

    def identity(self, key: str) -> str | None:
        last = self._last(key)
        return None if last is None else last.get("identity")

    def last_selection(self) -> str | None:
        """The most recent selection's target, `--clear` for a cleared one, None for none."""
        rows = [row for row in self.rows if row["phase"] == "select"]
        if not rows:
            return None
        return rows[-1]["target"] or "--clear"
