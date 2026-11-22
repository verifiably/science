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


@pytest.mark.parametrize("path_kind", ["directory", "file"])
def test_capture_reads_the_opened_inode(tmp_path, monkeypatch, path_kind):
    from contextlib import contextmanager
    from science.run_endpoint import paths

    root = tmp_path / "scratch"
    root.mkdir()
    item = root / "item"
    if path_kind == "directory":
        item.mkdir()
        (item / "content").write_bytes(b"first")
    else:
        item.write_bytes(b"first")
    original = paths._opened

    @contextmanager
    def replace_after_open(parent, name):
        with original(parent, name) as fd:
            if name == "item":
                item.rename(root / "old")
                if path_kind == "directory":
                    item.mkdir()
                    (item / "content").write_bytes(b"second")
                else:
                    item.write_bytes(b"second")
            yield fd

    monkeypatch.setattr(paths, "_opened", replace_after_open)
    with paths.Scratch(root, tmp_path, threading.Event()) as scratch:
        with scratch.prepare("dataset", "capture", {"path": str(item)}) as values:
            captured = Path(values["path"])
            source = captured / "content" if path_kind == "directory" else captured
            assert source.read_bytes() == b"first"


def test_dispatch_claim_precedes_capture_and_replay_preserves_original_input_digest(certified_work, tmp_path):
    from beliefs.permit import WritePermit
    from beliefs.session import open_run_session
    from helpers.world import build_fixture_world, fixture_proposition_node
    from science.canonical import input_digest
    from science.config import ReadContext
    from science.cursor import MIN_OUTPUT_BUDGET
    from science.dispatch import Dispatcher
    from science.report import record_block
    from science.run_endpoint.paths import Scratch
    from science.schema import Declaration, InputSpec, WriteClass

    cfg = build_fixture_world(certified_work)
    ceiling = WritePermit(frozenset({"proposition"}), frozenset({"corpus-write"}))
    session = open_run_session(cfg.world, cfg.operations_root, write_root=cfg.write_root, profile=cfg.profile, ceiling=ceiling)
    decl = Declaration("spec", "Test input capture", WriteClass("mints", ("proposition",), {"proposition": "corpus-write"}),
                       MIN_OUTPUT_BUDGET, (InputSpec("estimand", "string", True, "Path"),), (), Path("."))
    source = tmp_path / "input"
    source.write_text("captured")
    payload = {"estimand": str(source)}

    def handler(ctx, writer, *, estimand):
        assert Path(estimand) != source
        node = fixture_proposition_node(Path(estimand).read_text())
        writer.add(node)
        return (record_block(ctx.write_view().get(node.id)),)

    try:
        with Scratch(tmp_path, cfg.operations_root, threading.Event()) as confined:
            dispatcher = Dispatcher([decl], {"spec": handler}, ReadContext.open(cfg), session=session, run_inputs=confined)
            first = dispatcher.invoke("spec", payload, invocation_id="first")
            source.unlink()
            assert dispatcher.invoke("spec", payload, invocation_id="first") == first
            existing = cfg.operations_root / "capture/collision"
            existing.mkdir()
            marker = existing / "sentinel"
            marker.write_text("owned by another session")
            with pytest.raises(Refused, match="capture-exists"):
                dispatcher.invoke("spec", payload, invocation_id="collision")
            assert marker.read_text() == "owned by another session"
            session.claim_invocation("open", "spec", input_digest(payload))
            with pytest.raises(Refused, match="outcome-unknown"):
                dispatcher.invoke("spec", payload, invocation_id="open")
            assert not (existing.parent / "open").exists()
            session.close_invocation("open", {"done": []})
    finally:
        session.close()


def test_scratch_descriptor_refuses_an_input_on_a_nested_mount(tmp_path):
    import os
    import tempfile
    from science.run_endpoint.paths import Scratch

    device_root = Path("/dev")
    shared_memory = device_root / "shm"
    if not shared_memory.is_mount() or not os.access(shared_memory, os.W_OK):
        pytest.skip("requires a writable shm mount under /dev")
    with tempfile.NamedTemporaryFile(dir=shared_memory) as source:
        with Scratch(device_root, tmp_path, threading.Event()) as confined:
            with pytest.raises(Refused, match="path-outside-run"):
                with confined.prepare("fetch", "mount-check", {"source": source.name}):
                    pytest.fail("cross-mount input admitted")
        assert not (tmp_path / "capture/mount-check").exists()
