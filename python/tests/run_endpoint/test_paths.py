"""Capture pins private bytes and only removes the invocation it owns."""
from pathlib import Path
import threading

import pytest

from science.refusal import Refused


def test_private_capture_stable_and_cleanup(tmp_path):
    from science.run_endpoint.paths import Scratch
    scratch = tmp_path / "scratch"
    code = scratch / "code"
    code.mkdir(parents=True)
    entry = code / "Snakefile"
    entry.write_text("original")
    ops = tmp_path / "ops"
    ops.mkdir()
    with Scratch(scratch, ops, threading.Event()) as confined:
        with confined.prepare("run", "job", {"code": str(code), "entrypoint": "code/Snakefile", "targets": ["out"]}) as prepared:
            entry.write_text("changed")
            captured = Path(prepared["code"])
            assert captured == ops / "capture/job/code"
            assert (captured / "Snakefile").read_text() == "original"
        assert not captured.parent.exists()


def test_existing_capture_keeps_its_bytes(tmp_path):
    from science.run_endpoint.paths import Scratch
    scratch = tmp_path / "scratch"
    code = scratch / "code"
    code.mkdir(parents=True)
    owned = tmp_path / "ops/capture/job"
    owned.mkdir(parents=True)
    marker = owned / "sentinel"
    marker.write_text("previous")
    with Scratch(scratch, tmp_path / "ops", threading.Event()) as confined:
        with pytest.raises(Refused) as caught, confined.prepare("run", "job", {"code": str(code)}):
            pass
    assert caught.value.refusal.code == "capture-exists"
    assert marker.read_text() == "previous"


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo", "relative", "outside", "prefix"])
def test_invalid_source_refuses_and_cleans_only_its_capture(tmp_path, kind):
    import os
    from science.run_endpoint.paths import Scratch

    root = tmp_path / "scratch"
    ops = tmp_path / "ops"
    root.mkdir()
    ops.mkdir()
    sentinel = tmp_path / "sentinel"
    sentinel.write_bytes(b"untouched")
    item = root / "input"
    if kind == "symlink":
        item.symlink_to(sentinel)
    elif kind == "hardlink":
        os.link(sentinel, item)
    elif kind == "fifo":
        os.mkfifo(item)
    elif kind == "relative":
        item = Path("input")
    elif kind == "outside":
        item = sentinel
    else:
        item = tmp_path / "scratch-extra/input"
    with Scratch(root, ops, threading.Event()) as confined:
        with pytest.raises(Refused) as caught, confined.prepare("fetch", "job", {"source": str(item)}):
            pass
        assert caught.value.refusal.code == "path-outside-run"
        assert not (ops / "capture/job").exists()
    assert sentinel.read_bytes() == b"untouched"


def test_unavailable_openat2_blocks_only_commands_taking_a_path(tmp_path, monkeypatch):
    import errno
    from science.run_endpoint import paths

    def unavailable(*args):
        raise OSError(errno.ENOSYS, "unavailable")

    monkeypatch.setattr(paths.linux, "openat2", unavailable)
    with paths.Scratch(tmp_path, tmp_path, threading.Event()) as confined:
        with pytest.raises(Refused) as caught, confined.prepare("fetch", "job", {"source": str(tmp_path / "file")}):
            pass
        assert caught.value.refusal.code == "path-confinement-unavailable"
        with confined.prepare("status", "read", {}) as values:
            assert values == {}


def test_cancelled_copy_leaves_no_partial_capture(tmp_path, monkeypatch):
    from science.run_endpoint import paths
    root = tmp_path / "scratch"
    root.mkdir()
    source = root / "data"
    source.write_bytes(b"x" * 100000)
    cancelled = threading.Event()
    with paths.Scratch(root, tmp_path, cancelled) as confined:
        read = paths.os.read
        def stop_after_first_chunk(fd, size):
            result = read(fd, size)
            cancelled.set()
            return result
        monkeypatch.setattr(paths.os, "read", stop_after_first_chunk)
        with pytest.raises(Refused, match="run-sealed"), confined.prepare("fetch", "job", {"source": str(source)}):
            pass
        assert not (tmp_path / "capture/job").exists()
