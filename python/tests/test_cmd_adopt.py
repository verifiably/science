"""`adopt` (commons 1a, Task 8): B fetches A's publication from a bound location, verifies it, sources it, checks
its layout and conflicts, then admits and mounts it. Every registry write follows the sharing line that is its
evidence, and nothing survives a refusal before `fetched`."""
import pytest
from beliefs.session.ledger import LedgerReader, read_ledger_evidence
from beliefs.session.writer import ScopedWriter
from helpers.commons import (
    LOC_A,
    LOC_A2,
    LOC_B,
    Installations,
    a_identity,
    build_bound,
    publish_again,
    refused,
    reopen,
    with_remotes,
)
from helpers.snapshot import snapshot
from helpers.world import hold_fixture_dataset, open_rig

from science.config import ReadContext
from science.sharing import PinSource, SharingRegistry, replay
from science.world_belief import publish_session_epoch

LOC_OTHER = "https://remote.test/other"
NOT_A_CORPUS = "0" * 32


def _adopt(installations, location: str, corpus_id: str):
    with with_remotes(installations), open_rig(installations.b, ("adopt",)) as (d, _):
        return d.invoke("adopt", {"location": location, "corpus_id": corpus_id})


def _bind(installations, location: str, corpus_id: str, world: str) -> None:
    with with_remotes(installations), open_rig(installations.b, ("provider-bind",)) as (d, _):
        d.invoke("provider-bind", {"location": location, "corpus_id": corpus_id, "world": world})


def _states(text: str) -> list[str]:
    return [line.split()[2] for line in text.splitlines() if line.startswith("[pin]")]


def _sharing_lines(cfg) -> list:
    """Every sharing line in `cfg`'s session ledgers, in time order."""
    lines = []
    for directory in sorted((cfg.operations_root / "sessions").iterdir()):
        evidence = read_ledger_evidence(cfg.operations_root, directory.name)
        if isinstance(evidence, LedgerReader):
            lines.extend(evidence.sharing())
    return sorted(lines, key=lambda line: line.at)


def _known(cfg, corpus_id: str) -> bool:
    return ReadContext.open(cfg).world.status(corpus_id).known


def _no_copy(registry: SharingRegistry, corpus_id: str) -> bool:
    root = registry.root_for(corpus_id)
    return not root.exists() and not registry.head_artifact_for(corpus_id).exists() and \
        not root.with_name(root.name + ".metadata").exists()


def build_bound_fetched_only(work):
    """`build_bound`, then an adopt that crashes as it reaches admission: B holds a `fetched` pin of A's corpus
    at LOC_A, with its copy, and the kernel has not admitted it."""
    value = build_bound(work)
    installations = Installations.of(value)

    def crash(*args, **kwargs):
        raise RuntimeError("injected crash before admission")

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(ScopedWriter, "admit_publication", crash)
        with pytest.raises(RuntimeError, match="injected crash"):
            _adopt(installations, LOC_A, a_identity(installations.a)["corpus_id"])
    return value


@pytest.fixture
def bound_fetched_only(certified_worker_work):
    snap = snapshot(certified_worker_work, "commons-1a-bound-fetched-only", build_bound_fetched_only)
    snap.restore()
    return Installations.of(snap.value)


def test_adopt_unsourced_discards_the_copy_writes_no_pin_and_names_the_remedies(published):
    ids = a_identity(published.a)
    refusal = refused(lambda: _adopt(published, LOC_A, ids["corpus_id"]))
    assert refusal.code == "pin-unsourced" and refusal.data == {"world": ids["world"]}
    assert ids["world"] in refusal.message and "provider-bind" in refusal.message and "follow" in refusal.message
    registry = SharingRegistry(published.b.sharing_root)
    assert registry.pin(ids["corpus_id"]) is None and _no_copy(registry, ids["corpus_id"])
    assert not _known(published.b, ids["corpus_id"])
    assert _sharing_lines(published.b) == []


def test_adopt_after_bind_admits_and_marks_mounted(bound):
    ids = a_identity(bound.a)
    cid = ids["corpus_id"]
    text = _adopt(bound, LOC_A, cid).text
    assert _states(text) == ["fetched", "admitted", "mounted"]
    source = f"provider:{LOC_A}"
    lines = [line for line in _sharing_lines(bound.b) if line.transition != "bound"]
    assert [line.transition for line in lines] == ["fetched", "admitted", "mounted"]
    assert all(line.source == source and line.location == LOC_A and line.corpus == cid for line in lines)
    assert all(line.marker == ids["marker"] and line.artifact == ids["artifact"] for line in lines)
    pin = SharingRegistry(bound.b.sharing_root).pin(cid)
    assert pin.state == "mounted" and pin.source == PinSource("provider", LOC_A) and pin.fetch.location == LOC_A
    status = ReadContext.open(bound.b).world.status(cid)
    assert status.known and status.live


def test_adopt_at_a_non_canonical_spelling_records_the_canonical_location(bound):
    cid = a_identity(bound.a)["corpus_id"]
    assert _states(_adopt(bound, "https://REMOTE.test:443/a", cid).text) == ["fetched", "admitted", "mounted"]
    pin = SharingRegistry(bound.b.sharing_root).pin(cid)
    assert pin.source == PinSource("provider", LOC_A) and pin.fetch.location == LOC_A


def test_adopt_from_a_local_path_refuses_before_any_line(bound):
    location = str(bound.remotes / "a.git")
    r = refused(lambda: _adopt(bound, location, a_identity(bound.a)["corpus_id"]))
    assert r.code == "invalid-input" and location in r.message and "https://" in r.message
    assert [line.transition for line in _sharing_lines(bound.b)] == ["bound"]


def test_a_retry_at_a_bound_location_that_does_not_hold_the_candidate_refuses_naming_it(published):
    ids = a_identity(published.a)
    cid = ids["corpus_id"]
    # A also publishes at LOC_B, and B binds LOC_B to A's world on that publication: LOC_B never holds `cid`.
    _bind(published, LOC_B, publish_again(published, LOC_B), ids["world"])
    assert refused(lambda: _adopt(published, LOC_A, cid)).code == "pin-unsourced"
    refusal = refused(lambda: _adopt(published, LOC_B, cid))
    assert refusal.code == "invalid-input" and LOC_B in refusal.message
    registry = SharingRegistry(published.b.sharing_root)
    assert registry.pin(cid) is None and _no_copy(registry, cid) and not _known(published.b, cid)


def test_a_fetched_pin_is_reused_only_at_its_own_location(bound_fetched_only):
    cid = a_identity(bound_fetched_only.a)["corpus_id"]
    registry = SharingRegistry(bound_fetched_only.b.sharing_root)
    assert registry.pin(cid).state == "fetched" and not _known(bound_fetched_only.b, cid)
    r = refused(lambda: _adopt(bound_fetched_only, LOC_OTHER, cid))
    assert r.code == "invalid-input" and LOC_A in r.message
    assert registry.pin(cid).state == "fetched"
    assert _states(_adopt(bound_fetched_only, LOC_A, cid).text) == ["admitted", "mounted"]
    assert registry.pin(cid).state == "mounted" and _known(bound_fetched_only.b, cid)


def test_a_registry_rebuilt_from_the_ledger_alone_matches_the_live_one(adopted, tmp_path):
    cid = a_identity(adopted.a)["corpus_id"]
    registry = SharingRegistry(adopted.b.sharing_root)
    rebuilt = SharingRegistry(tmp_path / "rebuilt")
    replay(rebuilt, adopted.b.operations_root)
    assert rebuilt.pin(cid) == registry.pin(cid) and rebuilt.bindings() == registry.bindings()


def test_the_adopted_root_is_a_corpus_root_at_the_next_open(adopted):
    ids = a_identity(adopted.a)
    cfg = reopen(adopted.b)
    assert SharingRegistry(adopted.b.sharing_root).root_for(ids["corpus_id"]) in cfg.world.corpus_roots
    assert ReadContext.open(cfg).cited(ids["proposition"]).corpus_id == ids["corpus_id"]


@pytest.mark.xfail(strict=True, reason=(
    "the kernel's selection-incomplete names covered corpora without a carrier; an epoch built before reopen "
    "covers only the mounted corpora, so the adopted corpus is uncovered and publish succeeds"))
def test_publish_before_reopen_refuses_selection_incomplete_naming_the_adopted_corpus(adopted):
    cid = a_identity(adopted.a)["corpus_id"]
    hold_fixture_dataset(adopted.b, "b.txt", b"gene\tvalue\n", "expression")  # B's selection is not empty
    publish_session_epoch(adopted.b)  # over the corpora B's session mounts, which do not include the adopted one
    with with_remotes(adopted), open_rig(adopted.b, ("publish",)) as (d, _):
        r = refused(lambda: d.invoke("publish", {"target": "b", "to": LOC_B}))
    assert r.code == "kernel-refused" and r.data["reason"] == "selection-incomplete" and cid in r.message


def test_adopt_a_second_time_refuses_already_adopted(adopted):
    cid = a_identity(adopted.a)["corpus_id"]
    before = _sharing_lines(adopted.b)
    r = refused(lambda: _adopt(adopted, LOC_A, cid))
    assert r.code == "invalid-input" and "already adopted" in r.message
    assert _sharing_lines(adopted.b) == before


def test_adopt_of_a_conflicting_candidate_refuses_before_admission(conflicting_publication):
    installations, cid2 = conflicting_publication
    ids = a_identity(installations.a, binding_destination=LOC_A)
    _adopt(installations, LOC_A, ids["corpus_id"])
    r = refused(lambda: _adopt(installations, LOC_A2, cid2))
    assert r.code == "adopt-conflict" and r.data["corpus"] == ids["corpus_id"]
    assert r.data["reason"] == "overlap is milestone 1b (beliefs-81367e)"
    assert {ids[key] for key in ("proposition", "dataset", "spec", "run", "assessment")} <= set(r.data["addresses"])
    registry = SharingRegistry(installations.b.sharing_root)
    assert registry.pin(cid2).state == "fetched" and registry.root_for(cid2).is_dir()
    assert not _known(installations.b, cid2)


def test_adopt_of_an_absent_corpus_writes_nothing(bound):
    before = _sharing_lines(bound.b)
    r = refused(lambda: _adopt(bound, LOC_A, NOT_A_CORPUS))
    assert r.code == "invalid-input" and LOC_A in r.message and "absent" in r.message
    registry = SharingRegistry(bound.b.sharing_root)
    assert registry.pins() == () and _no_copy(registry, NOT_A_CORPUS)
    assert _sharing_lines(bound.b) == before


def _crash_on_write_pin(monkeypatch, state: str) -> None:
    write_pin = SharingRegistry.write_pin

    def crash(self, pin):
        if pin.state == state:
            raise RuntimeError(f"injected crash before the {state} pin write")
        write_pin(self, pin)

    monkeypatch.setattr(SharingRegistry, "write_pin", crash)


def test_a_crash_after_admission_before_the_pin_write_recovers_with_its_source(bound, monkeypatch):
    cid = a_identity(bound.a)["corpus_id"]
    registry = SharingRegistry(bound.b.sharing_root)
    _crash_on_write_pin(monkeypatch, "admitted")
    with pytest.raises(RuntimeError, match="injected crash"):
        _adopt(bound, LOC_A, cid)
    monkeypatch.undo()
    assert _known(bound.b, cid)
    assert registry.pin(cid).state == "fetched" and registry.pin(cid).source == PinSource("provider", LOC_A)
    text = _adopt(bound, LOC_A, cid).text
    assert _states(text) == ["mounted"]
    assert registry.pin(cid).state == "mounted" and registry.pin(cid).source == PinSource("provider", LOC_A)
    assert refused(lambda: _adopt(bound, LOC_A, cid)).code == "invalid-input"


def test_a_crash_between_the_mounted_line_and_the_pin_write_is_repaired_by_replay(bound, monkeypatch):
    cid = a_identity(bound.a)["corpus_id"]
    registry = SharingRegistry(bound.b.sharing_root)
    _crash_on_write_pin(monkeypatch, "mounted")
    with pytest.raises(RuntimeError, match="injected crash"):
        _adopt(bound, LOC_A, cid)
    monkeypatch.undo()
    assert registry.pin(cid).state == "admitted"
    (line,) = replay(registry, bound.b.operations_root)
    assert line.transition == "mounted" and line.source == f"provider:{LOC_A}"
    assert registry.pin(cid).state == "mounted" and registry.pin(cid).source == PinSource("provider", LOC_A)


def test_the_reopened_fixture_mounts_the_adopted_corpus_under_an_epoch_covering_it(reopened):
    from beliefs.world.read import current_epoch
    cid = a_identity(reopened.a)["corpus_id"]
    assert SharingRegistry(reopened.b.sharing_root).root_for(cid) in reopened.b.world.corpus_roots
    assert cid in dict(current_epoch(ReadContext.open(reopened.b).world).coverage)
