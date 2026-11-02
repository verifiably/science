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
from uncertified_host import capability_unavailable_from, uncertified_host

REPO_ROOT = Path(__file__).resolve().parents[2]
# The main checkout, which a worktree's own root is not: a worktree under .worktrees/
# resolves onto a volume whose mount options fail atoms' durability allowlist, so the
# certified test root always lives beside the main checkout's .git.
MAIN_ROOT = Path(subprocess.run(
    ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
    cwd=REPO_ROOT, check=True, capture_output=True, text=True,
).stdout.strip()).parent


def _report_missing_capability(error: BaseException) -> None:
    cause = capability_unavailable_from(error)
    if cause is not None and uncertified_host(os.environ):
        pytest.skip(f"certified tuple unavailable on this host: {cause}")


@pytest.hookimpl(wrapper=True)
def pytest_runtest_setup(item):
    try:
        return (yield)
    except Exception as error:
        _report_missing_capability(error)
        raise


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    try:
        return (yield)
    except Exception as error:
        _report_missing_capability(error)
        raise


@pytest.hookimpl(wrapper=True)
def pytest_runtest_teardown(item, nextitem):
    try:
        return (yield)
    except Exception as error:
        _report_missing_capability(error)
        raise



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


@pytest.fixture(autouse=True)
def _one_live_world_per_lineage():
    """Each test starts with no live snapshot world (lineages spec §2.3)."""
    yield
    from helpers.snapshot import clear_live
    clear_live()


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


# The commons fixture chain: each declaration in `helpers.commons` is built once per worker from its base's image
# (lineages spec) and restored per test; every fixture hands its test a copy of the snapshot's value, never the
# cached one. `fresh_value` is that dict, the others wrap it with `Installations.of`.
@pytest.fixture
def fresh_value(certified_worker_work):
    from helpers.commons import FRESH
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, FRESH)
    snap.restore()
    return copy_value(snap.value)


@pytest.fixture
def fresh(fresh_value):
    from helpers.commons import Installations
    return Installations.of(fresh_value)


@pytest.fixture
def fresh_no_epoch(certified_worker_work):
    from helpers.commons import Installations, FRESH_NO_EPOCH
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, FRESH_NO_EPOCH)
    snap.restore()
    return Installations.of(copy_value(snap.value))


@pytest.fixture
def published(certified_worker_work):
    from helpers.commons import Installations, PUBLISHED
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, PUBLISHED)
    snap.restore()
    return Installations.of(copy_value(snap.value))


@pytest.fixture
def bound(certified_worker_work):
    from helpers.commons import Installations, BOUND
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, BOUND)
    snap.restore()
    return Installations.of(copy_value(snap.value))


@pytest.fixture
def adopted(certified_worker_work):
    from helpers.commons import Installations, ADOPTED
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, ADOPTED)
    snap.restore()
    return Installations.of(copy_value(snap.value))


@pytest.fixture
def reopened(certified_worker_work):
    from helpers.commons import Installations, REOPENED
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, REOPENED)
    snap.restore()
    return Installations.of(copy_value(snap.value))


@pytest.fixture
def verified(certified_worker_work):
    """`reopened`, once B has fetched A's dataset and both vocabulary lists and verified A's assessment."""
    from helpers.commons import Installations, VERIFIED
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, VERIFIED)
    snap.restore()
    return Installations.of(copy_value(snap.value))


@pytest.fixture
def derived(certified_worker_work):
    """`verified`, once B has derived its changed analysis over A's mounted records: a spec, run and assessment
    of its own (`helpers.commons.b_derivation` reads them)."""
    from helpers.commons import Installations, DERIVED
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, DERIVED)
    snap.restore()
    return Installations.of(copy_value(snap.value))


@pytest.fixture
def conflicting_publication(certified_worker_work):
    """`(installations, corpus_id)`: the bound installations once A has published a second time to `LOC_A2` and
    B has bound it, and that second publication's corpus id. Its own snapshot, so it carries its installations
    rather than sharing `bound`'s."""
    from helpers.commons import Installations, CONFLICTING
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, CONFLICTING)
    snap.restore()
    return Installations.of(copy_value(snap.value)["installations"]), copy_value(snap.value)["corpus_id"]


# Stable module-level builders give each 1b snapshot exactly one identity.


@pytest.fixture
def published_b(certified_worker_work):
    from helpers.commons import Installations, PUBLISHED_B
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, PUBLISHED_B)
    snap.restore()
    return Installations.of(copy_value(snap.value))


@pytest.fixture
def published_b_unkept(certified_worker_work):
    from helpers.commons import Installations, PUBLISHED_B_UNKEPT
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, PUBLISHED_B_UNKEPT)
    snap.restore()
    return Installations.of(copy_value(snap.value))


@pytest.fixture
def a_bound_b(certified_worker_work):
    from helpers.commons import Installations, A_BOUND_B
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, A_BOUND_B)
    snap.restore()
    return Installations.of(copy_value(snap.value))


@pytest.fixture
def a_bound_b_unkept(certified_worker_work):
    from helpers.commons import Installations, A_BOUND_B_UNKEPT
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, A_BOUND_B_UNKEPT)
    snap.restore()
    return Installations.of(copy_value(snap.value))


@pytest.fixture
def overlapping(certified_worker_work):
    from helpers.commons import Installations, OVERLAPPING
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, OVERLAPPING)
    snap.restore()
    return Installations.of(copy_value(snap.value))


@pytest.fixture
def overlapping_unkept(certified_worker_work):
    from helpers.commons import Installations, OVERLAPPING_UNKEPT
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, OVERLAPPING_UNKEPT)
    snap.restore()
    return Installations.of(copy_value(snap.value))


@pytest.fixture
def updated(certified_worker_work):
    from helpers.commons import Installations, UPDATED
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, UPDATED)
    snap.restore()
    return Installations.of(copy_value(snap.value))


@pytest.fixture
def updated_unkept(certified_worker_work):
    from helpers.commons import Installations, UPDATED_UNKEPT
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, UPDATED_UNKEPT)
    snap.restore()
    return Installations.of(copy_value(snap.value))


@pytest.fixture
def b_updated(certified_worker_work):
    from helpers.commons import Installations, B_UPDATED
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, B_UPDATED)
    snap.restore()
    return Installations.of(copy_value(snap.value))


@pytest.fixture
def b_updated_unkept(certified_worker_work):
    from helpers.commons import Installations, B_UPDATED_UNKEPT
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, B_UPDATED_UNKEPT)
    snap.restore()
    return Installations.of(copy_value(snap.value))


@pytest.fixture
def sibling_publications(certified_worker_work):
    from helpers.commons import Installations, SIBLING_PUBLICATIONS
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, SIBLING_PUBLICATIONS)
    snap.restore()
    value, *refs = copy_value(snap.value)
    return Installations.of(value), *refs


@pytest.fixture
def late_chain(certified_worker_work):
    from helpers.commons import Installations, LATE_CHAIN
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, LATE_CHAIN)
    snap.restore()
    value, *refs = copy_value(snap.value)
    return Installations.of(value), *refs


@pytest.fixture
def late_chain_unadopted(certified_worker_work):
    from helpers.commons import Installations, LATE_CHAIN_UNADOPTED
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, LATE_CHAIN_UNADOPTED)
    snap.restore()
    value, *refs = copy_value(snap.value)
    return Installations.of(value), *refs


@pytest.fixture
def late_link(certified_worker_work):
    from helpers.commons import Installations, LATE_LINK
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, LATE_LINK)
    snap.restore()
    value, *refs = copy_value(snap.value)
    return Installations.of(value), *refs


@pytest.fixture
def sibling_publications_unkept(certified_worker_work):
    from helpers.commons import Installations, SIBLING_PUBLICATIONS_UNKEPT
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, SIBLING_PUBLICATIONS_UNKEPT)
    snap.restore()
    value, *refs = copy_value(snap.value)
    return Installations.of(value), *refs


@pytest.fixture
def equal_holders(certified_worker_work):
    from helpers.commons import Installations, EQUAL_HOLDERS
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, EQUAL_HOLDERS)
    snap.restore()
    value, *refs = copy_value(snap.value)
    return Installations.of(value), *refs


@pytest.fixture
def spec_drop(certified_worker_work):
    from helpers.commons import Installations, SPEC_DROP
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, SPEC_DROP)
    snap.restore()
    return Installations.of(copy_value(snap.value))


@pytest.fixture
def spec_only(certified_worker_work):
    from helpers.commons import Installations, SPEC_ONLY
    from helpers.snapshot import copy_value, materialize
    snap = materialize(certified_worker_work, SPEC_ONLY)
    snap.restore()
    return Installations.of(copy_value(snap.value))
