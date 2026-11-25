"""Pin actor input descriptors and copy their bytes into an owned private capture."""
from __future__ import annotations

from contextlib import contextmanager
import errno
import os
from pathlib import Path
import shutil
import stat

from atoms.fs.syscalls import linux
from beliefs.errors import ConfinementNotEstablished
from beliefs.session.routes import run_staging_of
from science.refusal import INVOCATION_ID_RE, Refusal, Refused

_RESOLVE = linux.RESOLVE_BENEATH | linux.RESOLVE_NO_XDEV | linux.RESOLVE_NO_MAGICLINKS | linux.RESOLVE_NO_SYMLINKS
_FILES = {"dataset": "path", "fetch": "source", "spec": "estimand", "run": "code", "derive": "code", "verify": "code"}
_DIRECTORY = os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC


def _outside():
    raise Refused(Refusal("path-outside-run", "Input must be a confined regular file or directory"))


def _relative(name):
    if not isinstance(name, str) or "\x00" in name or "\\" in name or any(
        part in ("", ".", "..") for part in name.split("/")
    ):
        _outside()
    return name


@contextmanager
def _opened(parent, name):
    try:
        fd = linux.openat2(parent, os.fsencode(name), os.O_RDONLY | os.O_NONBLOCK | os.O_CLOEXEC, 0, _RESOLVE)
    except (KeyError, OSError) as error:
        if isinstance(error, KeyError) or error.errno in {errno.ENOSYS, errno.EINVAL, errno.EPERM, errno.E2BIG}:
            raise Refused(Refusal("path-confinement-unavailable", "Required openat2 resolution is unavailable")) from error
        _outside()
    try:
        yield fd
    finally:
        os.close(fd)


def _identity(info):
    return info.st_dev, info.st_ino


def _remove_owned(parent, name, directory):
    if _identity(os.fstat(directory)) != _identity(os.stat(name, dir_fd=parent, follow_symlinks=False)):
        raise OSError("Private directory identity changed")
    shutil.rmtree(name, dir_fd=parent)


class Scratch:
    def __init__(self, root: Path, operations: Path, cancelled):
        self.root = root
        self.capture_root = operations / "capture"
        self.cancelled = cancelled
        self.fd = os.open(root, os.O_PATH | _DIRECTORY)
        self.owned = {}
        self.staging = None
        self.quiescent = True

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        if self.quiescent:
            self.cleanup()

    def cleanup(self):
        try:
            for iid in tuple(self.owned):
                self.remove(iid)
            if self.staging is not None:
                path, parent, directory = self.staging
                _remove_owned(parent, path.name, directory)
        finally:
            if self.staging is not None:
                _, parent, directory = self.staging
                os.close(directory)
                os.close(parent)
                self.staging = None
            for parent, directory in self.owned.values():
                os.close(directory)
                os.close(parent)
            self.owned.clear()
            os.close(self.fd)

    def retain_staging(self, writer):
        """Keep the session inode whose exclusive creation the kernel verified."""
        binding = run_staging_of(writer.operation_port())
        if binding is None:
            raise Refused(Refusal("confinement-unavailable", "A captured job requires a run session"))
        staging, iid = binding
        try:
            session_dir = staging.invocation_dir(iid).parent
            if self.staging is None:
                parent = os.open(session_dir.parent, os.O_RDONLY | _DIRECTORY)
                try:
                    directory = os.open(session_dir.name, os.O_RDONLY | _DIRECTORY, dir_fd=parent)
                    try:
                        staging.invocation_dir(iid)  # recheck the kernel anchors after opening our inode
                    except BaseException:
                        os.close(directory)
                        raise
                except BaseException:
                    os.close(parent)
                    raise
                self.staging = session_dir, parent, directory
        except (ConfinementNotEstablished, OSError) as error:
            raise Refused(Refusal("confinement-unavailable", str(error))) from error

    def check(self):
        if self.cancelled.is_set():
            raise Refused(Refusal("run-sealed", "The session is sealing"))

    def _copy(self, parent, name, target):
        self.check()
        with _opened(parent, name) as fd:
            info = os.fstat(fd)
            if stat.S_ISDIR(info.st_mode):
                target.mkdir(mode=0o700)
                for child in os.listdir(fd):
                    self._copy(fd, child, target / child)
            elif stat.S_ISREG(info.st_mode) and info.st_nlink == 1:
                with target.open("xb") as out:
                    while True:
                        self.check()
                        chunk = os.read(fd, 65536)
                        if not chunk:
                            break
                        out.write(chunk)
                    os.fchmod(out.fileno(), 0o700 if info.st_mode & 0o111 else 0o600)
            else:
                _outside()

    def remove(self, iid):
        owner = self.owned.get(iid)
        if owner is None:
            return
        parent, directory = owner
        _remove_owned(parent, iid, directory)
        del self.owned[iid]
        os.close(directory)
        os.close(parent)

    @contextmanager
    def prepare(self, command, iid, inputs):
        self.check()
        key = _FILES.get(command)
        if key is None:
            yield inputs
            return
        path = Path(inputs[key])
        if not path.is_relative_to(self.root) or str(path) != inputs[key] or not path.name:
            _outside()
        relative = "." if path == self.root else _relative(str(path.relative_to(self.root)))
        if not INVOCATION_ID_RE.fullmatch(iid):
            _outside()
        self.capture_root.mkdir(mode=0o700, exist_ok=True)
        parent = os.open(self.capture_root, os.O_RDONLY | _DIRECTORY)
        try:
            os.mkdir(iid, 0o700, dir_fd=parent)
            directory = os.open(iid, os.O_RDONLY | _DIRECTORY, dir_fd=parent)
        except FileExistsError:
            os.close(parent)
            raise Refused(Refusal("capture-exists", "This invocation already has a private capture")) from None
        except BaseException:
            os.close(parent)
            raise
        self.owned[iid] = parent, directory
        target = self.capture_root / iid / path.name
        try:
            self._copy(self.fd, relative, target)
            if command in ("run", "derive", "verify"):
                entry = _relative(inputs["entrypoint"])
                if not entry.startswith(path.name + "/"):
                    _outside()
                with _opened(directory, entry) as fd:
                    if not stat.S_ISREG(os.fstat(fd).st_mode):
                        _outside()
                for output in (() if command == "verify" else inputs["targets"]):
                    _relative(output)
            elif command == "dataset":
                for resource in inputs.get("resources", ()):
                    _relative(resource)
            self.check()
            yield {**inputs, key: str(target)}
        finally:
            self.remove(iid)
