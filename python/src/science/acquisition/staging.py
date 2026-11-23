"""Copy local members to bounded private staging through no-follow directory handles."""

from __future__ import annotations

import hashlib
import io
import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path

from beliefs.errors import MalformedRecord
from beliefs.holdings.records import require_store_relative_path
from beliefs.tree import TreeMember, make_tree
from science.refusal import Refusal, Refused

__all__ = ["copy_regular", "read_regular", "stage_tree"]

_READ = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK


@contextmanager
def _under(directory, part, flags):
    fd = os.open(part, flags, dir_fd=directory)
    try:
        yield fd
    finally:
        os.close(fd)


@contextmanager
def _root(path: Path):
    path = path.absolute()
    fd = os.open(path.anchor, _READ | os.O_DIRECTORY)
    try:
        for part in path.parts[1:]:
            child = os.open(part, _READ | os.O_DIRECTORY, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def _enumerate(fd, prefix=""):
    for name in sorted(os.listdir(fd)):
        path = prefix + name
        mode = os.stat(name, dir_fd=fd, follow_symlinks=False).st_mode
        if stat.S_ISDIR(mode):
            with _under(fd, name, _READ | os.O_DIRECTORY) as sub:
                yield from _enumerate(sub, path + "/")
        elif stat.S_ISREG(mode):
            yield path
        else:
            raise ValueError(f"{path} is a symlink or nonregular entry")


@contextmanager
def _regular(fd, relative):
    require_store_relative_path(relative)
    parent, _, name = relative.rpartition("/")
    current = os.dup(fd)
    try:
        for part in parent.split("/") if parent else ():
            child = os.open(part, _READ | os.O_DIRECTORY, dir_fd=current)
            os.close(current)
            current = child
        with os.fdopen(os.open(name, _READ, dir_fd=current), "rb") as inp:
            if not stat.S_ISREG(os.fstat(inp.fileno()).st_mode):
                raise ValueError(f"{relative} is not a regular file")
            yield inp
    finally:
        os.close(current)


def copy_regular(path: Path, out) -> str:
    """Copy precisely the observed file size without following links or a growing tail."""
    try:
        with _root(path.parent) as fd, _regular(fd, path.name) as inp:
            size = os.fstat(inp.fileno()).st_size
            remaining = size
            digest = hashlib.sha256()
            while remaining:
                chunk = inp.read(min(1024**2, remaining))
                if not chunk:
                    raise ValueError("source shortened during copy")
                digest.update(chunk)
                out.write(chunk)
                remaining -= len(chunk)
            if inp.read(1):
                raise ValueError("source grew during copy")
            return "sha256:" + digest.hexdigest()
    except (OSError, ValueError, MalformedRecord) as exc:
        raise Refused(Refusal("invalid-input", f"Cannot stage {path}: {exc}")) from exc


def read_regular(path: Path) -> bytes:
    with io.BytesIO() as buffer:
        copy_regular(path, buffer)
        return buffer.getvalue()


def stage_tree(root, destination, bounds, *, selected=None):
    """The caller owns the private destination and cleans it up on every exit."""
    try:
        if destination.resolve().is_relative_to(root.resolve()):
            raise ValueError("staging directory overlaps input")
        with _root(root) as fd:
            if selected is not None and len(set(selected)) != len(selected):
                raise ValueError("duplicate selected member")
            names = _enumerate(fd) if selected is None else selected
            members = []
            paths = {}
            total = 0
            for name in names:
                if len(members) >= bounds.max_requests:
                    raise ValueError("tree exceeds max_requests")
                limit = min(bounds.max_total_bytes - total, bounds.max_response_bytes)
                size = 0
                digest = hashlib.sha256()
                with _regular(fd, name) as inp, tempfile.NamedTemporaryFile(dir=destination, delete=False) as out:
                    while chunk := inp.read(min(1024**2, limit - size + 1)):
                        size += len(chunk)
                        if size > limit:
                            raise ValueError(f"{name!r} exceeds the member or total byte limit")
                        digest.update(chunk)
                        out.write(chunk)
                members.append(TreeMember(name, "sha256:" + digest.hexdigest(), size))
                paths[name] = Path(out.name)
                total += size
        return make_tree(members), paths
    except (ValueError, OSError, MalformedRecord) as exc:
        raise Refused(Refusal("invalid-input", f"Cannot stage tree {root}: {exc}")) from exc
