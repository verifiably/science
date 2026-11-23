"""Publish private acquisition sets and recover their committed journal prefixes."""

from __future__ import annotations

import fcntl
import hashlib
import os
import re
import secrets
import shutil
import stat
import tempfile
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path

from atoms.fs.volume import read_mountinfo, resolve_mount_entry
from beliefs.durable import ensure_directory
from beliefs.errors import IdentityError, MalformedRecord
from beliefs.holdings.acquisition_log import AcquisitionLog, LogHeader
from beliefs.identity import v1
from science.acquisition.bounds import AcquisitionBounds
from science.acquisition.plan import StaticPlan, parse_plan
from science.acquisition.request import RequestState
from science.refusal import Refusal, Refused

__all__ = ["Journal", "locked_directory", "prepare_root", "sync_dir"]

_TOKEN = re.compile("[0-9a-f]{32}")
INSTRUMENT = "science/acquire.v1 (beliefs transport)"


def _invalid(message):
    return Refused(Refusal("invalid-input", message))


def _safe(path: Path) -> Path:
    if path.resolve() != path.absolute():
        raise _invalid(f"acquisition path redirects through a link: {path}")
    return path


@contextmanager
def _directory(path):
    fd = os.open(_safe(path), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        yield fd
    finally:
        os.close(fd)


def sync_dir(path):
    with _directory(path) as fd:
        os.fsync(fd)


@contextmanager
def locked_directory(path: Path, busy: str):
    with _directory(path) as fd:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise Refused(Refusal(busy, f"acquisition lock held at {path}")) from None
        yield


def prepare_root(operations: Path, protected: tuple[Path, ...]) -> Path:
    _safe(operations)
    for root in protected:
        root = root.resolve()
        if operations.is_relative_to(root) or root.is_relative_to(operations):
            raise _invalid(f"operations root overlaps protected root {root}")
    existing = operations
    while not existing.exists():
        existing = existing.parent
    with _directory(existing) as fd:
        fs = resolve_mount_entry(fd, read_mountinfo()).filesystem_type
        if fs in ("tmpfs", "ramfs"):
            raise _invalid(f"acquisition work area requires persistent storage, found {fs}")
    ensure_directory(operations)
    root = _safe(operations / "acquisitions")
    root.mkdir(mode=0o700, exist_ok=True)
    sync_dir(operations)
    return root


def _digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _write_file(path, data):
    with path.open("xb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def _planned(seq, seed):
    row = {"event": "planned", "seq": seq, "url": seed.url.url, "member": seed.name}
    if seed.expected is not None:
        row["expected"] = seed.expected
    return row


class Journal:
    def __init__(self, path: Path, plan: StaticPlan, bounds: AcquisitionBounds):
        self.path, self.plan, self.bounds = path, plan, bounds
        self.requests = [RequestState(seed) for seed in plan.seeds]
        self.position = 1 + len(plan.seeds)

    @classmethod
    def create(cls, operations, raw, bounds, *, protected):
        plan = parse_plan(raw, max_requests=bounds.max_requests)
        root = prepare_root(operations, protected)
        token = secrets.token_hex(16)
        final = root / token
        path = Path(tempfile.mkdtemp(prefix=".creating-", dir=root))
        try:
            policy = v1.encode(asdict(bounds))
            _write_file(path / "plan.json", raw)
            _write_file(path / "bounds.json", policy)
            for name in ("objects", "scratch"):
                (path / name).mkdir(mode=0o700)
            header = {"event": "initialized", "set": token, "plan": _digest(raw), "bounds": _digest(policy)}
            rows = [header, *(_planned(i, seed) for i, seed in enumerate(plan.seeds, 1))]
            _write_file(path / "journal.v1", b"".join(v1.encode(r) + b"\n" for r in rows))
            sync_dir(path)
            path.rename(final)
            sync_dir(root)
        finally:
            if path.exists():
                shutil.rmtree(path)
        return cls(final, plan, bounds)

    @classmethod
    def open(cls, operations, token, *, repair=False):
        if not isinstance(token, str) or not _TOKEN.fullmatch(token):
            raise _invalid("invalid acquisition set token")
        path = _safe(operations / "acquisitions" / token)
        if not path.is_dir():
            raise _invalid(f"unknown acquisition set {token}")
        for name in ("objects", "scratch", "plan.json", "bounds.json", "journal.v1"):
            item = _safe(path / name)
            mode = item.stat().st_mode
            if not (stat.S_ISDIR(mode) if name in ("objects", "scratch") else stat.S_ISREG(mode)):
                raise _invalid(f"invalid acquisition set entry {name}")
        raw = (path / "plan.json").read_bytes()
        policy = (path / "bounds.json").read_bytes()
        header = {"event": "initialized", "set": token, "plan": _digest(raw), "bounds": _digest(policy)}
        with (path / "journal.v1").open("r+b" if repair else "rb") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX if repair else fcntl.LOCK_SH)
            if handle.readline() != v1.encode(header) + b"\n":
                raise _invalid("journal line 1: input digest or set token differs")
            bounds = AcquisitionBounds.from_mapping(v1.decode(policy))
            result = cls(path, parse_plan(raw, max_requests=bounds.max_requests), bounds)
            for i, seed in enumerate(result.plan.seeds, 1):
                if handle.readline() != v1.encode(_planned(i, seed)) + b"\n":
                    raise _invalid(f"journal line {i + 1}: planned row differs")
            while True:
                start = handle.tell()
                line = handle.readline()
                if not line.endswith(b"\n"):
                    if line and repair:
                        handle.truncate(start)
                        os.fsync(handle.fileno())
                    break
                try:
                    row = v1.decode(line[:-1])
                    if not isinstance(row, dict):
                        raise ValueError("event is not an object")
                    index, next_request = result._next(row)
                except (ValueError, KeyError, TypeError, IdentityError, MalformedRecord) as exc:
                    raise _invalid(f"journal line {result.position + 1}: {exc}") from exc
                result.requests[index] = next_request
                result.position += 1
        return result

    def _next(self, row):
        event, seq = row["event"], row["seq"]
        if type(seq) is not int or not 1 <= seq <= len(self.requests):
            raise ValueError(f"invalid sequence {seq}")
        payload = {key: value for key, value in row.items() if key not in ("event", "seq")}
        return seq - 1, self.requests[seq - 1].transition(event, payload, self.bounds.attempts)

    def append(self, event, *, seq, **payload):
        """The caller owns the per-set directory lock through all mutation."""
        row = {"event": event, "seq": seq, **payload}
        try:
            index, next_request = self._next(row)
        except (ValueError, TypeError, KeyError, MalformedRecord) as exc:
            raise _invalid(f"journal line {self.position + 1}: {exc}") from exc
        with (self.path / "journal.v1").open("ab") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            handle.write(v1.encode(row) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.requests[index] = next_request
        self.position += 1

    def acquisition_log(self):
        header = LogHeader(self.path.name, "fetched", INSTRUMENT, self.plan.source, ())
        lines = tuple(request.line(seq) for seq, request in enumerate(self.requests, 1))
        return AcquisitionLog(header, lines)
