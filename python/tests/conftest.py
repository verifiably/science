import os
import shutil
import subprocess
import tempfile
import threading
import uuid
from contextlib import contextmanager
from pathlib import Path

import pytest

from helpers.world import short_socket

REPO_ROOT = Path(__file__).resolve().parents[2]
# The main checkout, which a worktree's own root is not: a worktree under .worktrees/
# resolves onto a volume whose mount options fail atoms' durability allowlist, so the
# certified test root always lives beside the main checkout's .git.
MAIN_ROOT = Path(subprocess.run(
    ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
    cwd=REPO_ROOT, check=True, capture_output=True, text=True,
).stdout.strip()).parent


@pytest.fixture(autouse=True)
def _no_thread_left_running():
    """A thread a test starts ends with it. A `serve_forever` left polling a closed
    socket (`server_close()` without `shutdown()`) slowed every later test on its
    worker about fivefold."""
    before = set(threading.enumerate())
    yield
    started = [thread for thread in threading.enumerate() if thread not in before]
    for thread in started:
        thread.join(timeout=1)
    alive = [thread.name for thread in started if thread.is_alive()]
    assert not alive, f"threads still running after the test: {alive}"


@contextmanager
def _certified_dir():
    base = Path(os.environ.get("SCIENCE_TEST_ROOT", MAIN_ROOT / ".framework-test"))
    work = base / uuid.uuid4().hex
    work.mkdir(parents=True)
    try:
        yield work
    finally:
        shutil.rmtree(work, ignore_errors=True)  # metadata siblings live inside work
        short_socket(work).unlink(missing_ok=True)  # left only by a launcher that never closed


@pytest.fixture()
def certified_work():
    with _certified_dir() as work:
        yield work


@pytest.fixture(scope="session")
def certified_worker_work():
    """One certified directory per worker process, holding the worlds
    `helpers.snapshot` builds once and restores per test."""
    with _certified_dir() as work:
        yield work


@pytest.fixture
def short_tmp():
    """A short directory for sockets. AF_UNIX caps the socket path at 107 bytes, and
    pytest's `tmp_path` grows with the test name and, under xdist, a worker segment."""
    root = Path(tempfile.mkdtemp(prefix="sci-", dir="/tmp"))
    try:
        yield root
    finally:
        shutil.rmtree(root)


# The commons 1a fixture chain (plan Task 5 onward): each builder's dict is snapshot-cached per worker and
# restored per test; `fresh_value` is the raw dict, the others wrap it with `Installations.of`. Later tasks add
# their snapshots (`published`, `bound`, ...) beside these.
@pytest.fixture
def fresh_value(certified_worker_work):
    from helpers.commons import build_fresh
    from helpers.snapshot import snapshot
    snap = snapshot(certified_worker_work, "commons-1a-fresh", build_fresh)
    snap.restore()
    return snap.value


@pytest.fixture
def fresh(fresh_value):
    from helpers.commons import Installations
    return Installations.of(fresh_value)


@pytest.fixture
def fresh_no_epoch(certified_worker_work):
    from helpers.commons import Installations, build_fresh_no_epoch
    from helpers.snapshot import snapshot
    snap = snapshot(certified_worker_work, "commons-1a-fresh-no-epoch", build_fresh_no_epoch)
    snap.restore()
    return Installations.of(snap.value)


@pytest.fixture
def published(certified_worker_work):
    from helpers.commons import Installations, build_published
    from helpers.snapshot import snapshot
    snap = snapshot(certified_worker_work, "commons-1a-published", build_published)
    snap.restore()
    return Installations.of(snap.value)


@pytest.fixture
def bound(certified_worker_work):
    from helpers.commons import Installations, build_bound
    from helpers.snapshot import snapshot
    snap = snapshot(certified_worker_work, "commons-1a-bound", build_bound)
    snap.restore()
    return Installations.of(snap.value)


@pytest.fixture
def adopted(certified_worker_work):
    from helpers.commons import Installations, build_adopted
    from helpers.snapshot import snapshot
    snap = snapshot(certified_worker_work, "commons-1a-adopted", build_adopted)
    snap.restore()
    return Installations.of(snap.value)


@pytest.fixture
def reopened(certified_worker_work):
    from helpers.commons import Installations, build_reopened
    from helpers.snapshot import snapshot
    snap = snapshot(certified_worker_work, "commons-1a-reopened", build_reopened)
    snap.restore()
    return Installations.of(snap.value)


@pytest.fixture
def verified(certified_worker_work):
    """`reopened`, once B has fetched A's dataset and both vocabulary lists and verified A's assessment."""
    from helpers.commons import Installations, build_verified
    from helpers.snapshot import snapshot
    snap = snapshot(certified_worker_work, "commons-1a-verified", build_verified)
    snap.restore()
    return Installations.of(snap.value)


@pytest.fixture
def derived(certified_worker_work):
    """`verified`, once B has derived its changed analysis over A's mounted records: a spec, run and assessment
    of its own (`helpers.commons.b_derivation` reads them)."""
    from helpers.commons import Installations, build_derived
    from helpers.snapshot import snapshot
    snap = snapshot(certified_worker_work, "commons-1a-derived", build_derived)
    snap.restore()
    return Installations.of(snap.value)


@pytest.fixture
def conflicting_publication(certified_worker_work):
    """`(installations, corpus_id)`: the bound installations once A has published a second time to `LOC_A2` and
    B has bound it, and that second publication's corpus id. Its own snapshot, so it carries its installations
    rather than sharing `bound`'s."""
    from helpers.commons import Installations, build_conflicting
    from helpers.snapshot import snapshot
    snap = snapshot(certified_worker_work, "commons-1a-conflicting", build_conflicting)
    snap.restore()
    return Installations.of(snap.value["installations"]), snap.value["corpus_id"]
