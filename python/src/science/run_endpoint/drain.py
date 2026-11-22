"""Discover direct session children and signal only a verified live child."""
from __future__ import annotations

import ctypes
import errno
import os
from pathlib import Path
import select
import signal
import subprocess
import sys


# The certified interpreter can omit its Python pidfd wrappers even when
# libc and the running kernel provide them.
_libc = ctypes.CDLL(None, use_errno=True)


def _pidfd_call(name: str, *args) -> int:
    operation = getattr(_libc, name, None)
    if operation is None:
        raise OSError(errno.ENOSYS, name)
    result = operation(*args)
    if result < 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))
    return result


def open_pidfd(pid: int) -> int:
    return _pidfd_call("pidfd_open", pid, 0)


def signal_pidfd(fd: int) -> None:
    _pidfd_call("pidfd_send_signal", fd, signal.SIGKILL, None, 0)


def children() -> set[int]:
    result = set()
    for task in Path("/proc/self/task").iterdir():
        try:
            contents = (task / "children").read_bytes()
        except FileNotFoundError:
            if task.exists():
                raise
            continue
        result.update(int(pid) for pid in contents.split())
    return result


def kill_child(pid: int) -> bool:
    try:
        fd = open_pidfd(pid)
    except ProcessLookupError:
        return False
    try:
        try:
            status = Path(f"/proc/{pid}/status").read_bytes().splitlines()
        except (FileNotFoundError, ProcessLookupError):
            return False
        parent = next((line.split()[1] for line in status if line.startswith(b"PPid:")), None)
        if parent != str(os.getpid()).encode("ascii"):
            return False
        poll = select.poll()
        poll.register(fd, select.POLLIN)
        if poll.poll(0):
            return False
        try:
            signal_pidfd(fd)
        except ProcessLookupError:
            return False
        return True
    finally:
        os.close(fd)


def can_control_jobs() -> bool:
    """Exercise the required operations on a private child before admitting jobs."""
    try:
        with subprocess.Popen(
            [sys.executable, "-I", "-S", "-c", "import sys; sys.stdin.buffer.read(1)"],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            env={},
        ) as probe:
            try:
                killed = probe.pid in children() and kill_child(probe.pid)
            finally:
                probe.stdin.close()
            return killed and probe.wait() == -signal.SIGKILL
    except OSError:
        return False
