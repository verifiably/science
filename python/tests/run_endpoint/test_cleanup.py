"""Private capture cleanup uses the retained directory identity."""
import os
from pathlib import Path
import select
import shutil
import subprocess
import sys
import threading

import pytest

from science.run_endpoint.paths import Scratch


def test_replaced_capture_survives_cleanup(tmp_path):
    source = tmp_path / "input"
    source.write_bytes(b"x")
    scratch = Scratch(tmp_path, tmp_path, threading.Event())
    with pytest.raises(OSError, match="identity changed"):
        with scratch, scratch.prepare("fetch", "owned", {"source": str(source)}):
            directory = tmp_path / "capture/owned"
            directory.rename(tmp_path / "original")
            directory.mkdir()
            sentinel = directory / "sentinel"
            sentinel.write_bytes(b"keep")
    assert sentinel.read_bytes() == b"keep"


def test_orphan_reclaimed_only_after_root_is_idle(tmp_path):
    from science.refusal import Refused
    source = tmp_path / "input"
    source.write_bytes(b"new")
    orphan = tmp_path / "capture/one"
    worker = """
import sys, threading
from pathlib import Path
from science.run_endpoint.paths import Scratch
root = Path(sys.argv[1])
with Scratch(root, root, threading.Event()) as capture:
    with capture.prepare("fetch", "one", {"source": str(root / "input")}):
        print("capture owned", flush=True)
        sys.stdin.buffer.read(1)
"""
    with subprocess.Popen([sys.executable, "-I", "-c", worker, str(tmp_path)], stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env={"HOME": str(tmp_path), "PATH": os.defpath}) as original:
        try:
            assert select.select([original.stdout], [], [], 5)[0]
            assert original.stdout.readline() == b"capture owned\n"
        finally:
            original.kill()
            original.wait(timeout=5)
    with Scratch(tmp_path, tmp_path, threading.Event()) as fresh:
        with pytest.raises(Refused, match="capture-exists"), fresh.prepare("fetch", "one", {"source": str(source)}):
            pass
    assert (orphan / "input").read_bytes() == b"new"
    # Operator has excluded new launches and confirmed the fixture root is idle.
    shutil.rmtree(orphan)
    with Scratch(tmp_path, tmp_path, threading.Event()) as fresh:
        with fresh.prepare("fetch", "one", {"source": str(source)}) as captured:
            assert Path(captured["source"]).read_bytes() == b"new"
    assert not orphan.exists()


def test_pid_recheck_preserves_an_unrelated_process(monkeypatch):
    from science.run_endpoint import drain
    read_fd, write_fd = os.pipe()
    signals = []
    try:
        monkeypatch.setattr(drain, "open_pidfd", lambda pid: os.dup(read_fd))
        monkeypatch.setattr(Path, "read_bytes", lambda path: b"PPid:\t0\n")
        monkeypatch.setattr(drain, "signal_pidfd", signals.append)
        assert not drain.kill_child(1)
        assert not signals
    finally:
        os.close(read_fd)
        os.close(write_fd)


def test_sweep_includes_a_child_started_on_a_worker_thread(tmp_path):
    from science.run_endpoint import drain
    import signal

    ready = threading.Event()
    children = []
    errors = []

    def serve():
        try:
            with subprocess.Popen([sys.executable, "-I", "-S", "-c", "import sys; sys.stdin.buffer.read(1)"],
                                  stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                  env={"HOME": str(tmp_path), "PATH": os.defpath}) as child:
                children.append(child)
                ready.set()
                try:
                    child.wait(timeout=5)
                finally:
                    child.stdin.close()
        except Exception as error:
            errors.append(error)

    worker = threading.Thread(target=serve)
    worker.start()
    try:
        assert ready.wait(5)
        assert children[0].pid in drain.children()
        assert drain.kill_child(children[0].pid)
    finally:
        worker.join(8)
    assert not errors
    assert children[0].returncode == -signal.SIGKILL


@pytest.mark.parametrize("when", ["before-pin", "during-check"])
def test_exited_child_cannot_receive_a_signal(monkeypatch, when):
    from science.run_endpoint import drain

    signals = []
    monkeypatch.setattr(drain, "signal_pidfd", signals.append)
    if when == "before-pin":
        def gone(pid):
            raise ProcessLookupError(pid)
        monkeypatch.setattr(drain, "open_pidfd", gone)
        assert not drain.kill_child(123)
    else:
        read_fd, write_fd = os.pipe()
        os.close(write_fd)
        try:
            monkeypatch.setattr(drain, "open_pidfd", lambda pid: os.dup(read_fd))
            monkeypatch.setattr(Path, "read_bytes", lambda path: f"PPid:\t{os.getpid()}\n".encode())
            assert not drain.kill_child(123)
        finally:
            os.close(read_fd)
    assert not signals
