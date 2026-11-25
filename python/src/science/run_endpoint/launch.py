"""Validate supervisor-owned launch data before acquiring a kernel writer."""
from __future__ import annotations

import json
import math
import os
import re
import stat
import threading
from dataclasses import dataclass, field
from pathlib import Path

from beliefs.errors import ChainClaimed, ScienceError
from beliefs.permit import WritePermit
from beliefs.session import open_run_session
from beliefs.session.ledger import ledger_path

from science.config import ScienceConfig, configured_stores, corpus_id_at, load_config, mount_profiles, require_write_root_pins
from science.refusal import Refusal, Refused
from science.serve import MAX_SOCKET_PATH_BYTES
from science.run_endpoint.basis import BasisInventory, open_basis

_PATHS = ("config", "run_dir", "scratch_dir", "socket", "control_socket", "token_file")
_REQUIRED = {"version", "permit", "written_chains", *_PATHS}


def _bad(message):
    raise Refused(Refusal("invalid-input", message))


def _private_dir(path):
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        _bad(f"Expected a private owned directory at {path}")


def _private_bytes(path, limit):
    _private_dir(path.parent)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_nlink != 1
                or stat.S_IMODE(info.st_mode) != 0o600):
            _bad(f"Expected an owned mode-0600 file at {path}")
        data = stream.read(limit + 1)
        if len(data) > limit:
            _bad(f"File exceeds its size limit at {path}")
        return data


def _path(raw):
    if not isinstance(raw, str) or not Path(raw).is_absolute() or "\x00" in raw:
        _bad("Launch paths must be absolute")
    path = Path(raw)
    if str(path) != raw or path.resolve() != path:
        _bad(f"Launch path uses an alias: {path}")
    return path


def _limit(doc, key, default, minimum):
    value = doc.get(key, default)
    if type(value) not in (int, float) or not minimum <= value <= threading.TIMEOUT_MAX or not math.isfinite(value):
        _bad(f"Invalid {key}")
    return float(value)


def _closed(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _bad(f"Duplicate launch field {key}")
        result[key] = value
    return result


def _overlap(a, b):
    if a.is_relative_to(b) or b.is_relative_to(a):
        return True
    for path, other in ((a, b), (b, a)):
        if path.exists() and any(p.exists() and path.samefile(p) for p in (other, *other.parents)):
            return True
    return False


@dataclass(frozen=True)
class RunLaunch:
    config: ScienceConfig
    run_dir: Path
    scratch_dir: Path
    socket: Path
    control_socket: Path
    token: bytes = field(repr=False)
    permit: WritePermit
    store_root: Path | None
    lease_seconds: float
    seal_timeout_seconds: float
    research: object = None
    allowance_fd: int | None = None
    resume_handoff: dict | None = None


@dataclass(frozen=True)
class OpenedRun:
    session: object
    basis: BasisInventory

    research_digest: str | None = None

    def open_report(self):
        session = self.session
        return {"version": "control.v1", "type": "open", "session_id": session.session_id,
                "ledger_path": str(ledger_path(session.operations_root, session.session_id)),
                "basis_open": self.basis.digest, **({"research_action_digest": self.research_digest} if self.research_digest else {})}


def read_launch(source: Path) -> RunLaunch:
    try:
        return _read_launch(_path(str(source)))
    except (OSError, ValueError, TypeError, RecursionError, ScienceError) as error:
        raise Refused(Refusal("invalid-input", f"Invalid launch: {error}")) from error


def _read_launch(source):
    doc = json.loads(_private_bytes(source, 1 << 20), object_pairs_hook=_closed)
    governed = {"research_action", "allowance_fd", "resume_handoff"}
    has_research = type(doc) is dict and bool(governed.intersection(doc))
    if (type(doc) is not dict or not _REQUIRED <= doc.keys() or doc.keys() - _REQUIRED - {"lease_seconds", "seal_timeout_seconds"} - governed
            or (has_research and not governed <= doc.keys())
            or doc["version"] != "launch.v1"):
        _bad("Invalid launch.v1 fields or version")
    config_path, run, scratch, actor, control, token_path = (_path(doc[k]) for k in _PATHS)
    if len({source, config_path, actor, control, token_path}) != 5:
        _bad("Launch files and socket paths must be distinct")
    for directory in (run, control.parent, actor.parent, token_path.parent):
        _private_dir(directory)
    if source.parent != run or actor.parent != token_path.parent or _overlap(run, actor.parent):
        _bad("The launch file belongs in the private run directory and actor credentials in a separate runtime directory")
    if not scratch.is_dir():
        _bad("Missing scratch directory")
    if any(len(os.fsencode(p)) > MAX_SOCKET_PATH_BYTES for p in (actor, control)):
        _bad("Unix socket path too long")
    if os.path.lexists(actor) or not stat.S_ISSOCK(control.lstat().st_mode):
        _bad("Actor socket is occupied or control socket is missing")
    token = _private_bytes(token_path, 64)
    if not re.fullmatch(b"[0-9a-f]{64}", token):
        _bad("Invalid token file")
    cfg = load_config(config_path)
    protected = [source, config_path, run, control.parent, actor.parent, token_path.parent,
                 cfg.operations_root, cfg.world.world_root, *cfg.world.corpus_roots, cfg.store_root, *cfg.read_store_roots]
    if cfg.sharing_root is not None:
        protected.append(cfg.sharing_root)
    if any(_overlap(scratch, p) for p in protected):
        _bad("Scratch overlaps a protected root")
    permit = WritePermit.from_json(doc["permit"])
    if permit.ungoverned or permit.act_families - {"holdings", "corpus-write", "run"}:
        _bad("Inadmissible run permit")
    stores = configured_stores(cfg)
    require_write_root_pins(cfg)
    writable = cfg.store_root if "holdings" in permit.act_families and "holdings-observation" in permit.kinds else None
    expected = {("corpus", corpus_id_at(cfg.write_root), cfg.write_root)}
    if writable is not None:
        expected.add(("store", next(k for k, v in stores.items() if v == writable), writable))
    rows = doc["written_chains"]
    if type(rows) is not list or any(type(r) is not dict or set(r) != {"id","role","root"} for r in rows):
        _bad("Invalid written_chains rows")
    actual = {(r["role"], r["id"], _path(r["root"])) for r in rows}
    if len(rows) != len(actual) or actual != expected:
        _bad("Written chains do not match this configuration and permit")
    research = None
    if has_research:
        from science.run_endpoint.research import ResearchAction
        research = ResearchAction(doc["research_action"], permit)
        if type(doc["allowance_fd"]) is not int or doc["allowance_fd"] < 3:
            _bad("Invalid allowance descriptor")
        handoff = doc["resume_handoff"]
        if type(handoff) is not dict or set(handoff) != {"sessions"} or type(handoff["sessions"]) is not list:
            _bad("Invalid resume handoff")
    return RunLaunch(cfg, run, scratch, actor, control, token, permit, writable,
                     _limit(doc, "lease_seconds", 60, 10), _limit(doc, "seal_timeout_seconds", 30, 0),
                     research, doc.get("allowance_fd"), doc.get("resume_handoff"))


def open_run(launch: RunLaunch) -> OpenedRun:
    cfg = launch.config
    basis = open_basis(cfg)
    try:
        session = open_run_session(cfg.world, cfg.operations_root, write_root=cfg.write_root, profile=cfg.profile,
                                   ceiling=launch.permit, mounts=mount_profiles(cfg) if cfg.coordination is not None else None,
                                   store_root=launch.store_root, project=cfg.default_project)
    except ChainClaimed as error:
        raise Refused(Refusal("corpus-claimed", str(error))) from error
    except ScienceError as error:
        raise Refused(Refusal("kernel-refused", str(error))) from error
    return OpenedRun(session, basis, launch.research.digest if launch.research else None)
