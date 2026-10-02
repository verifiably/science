"""Mount citations consumer spec, decisions 1–3: a write cites a record any
session corpus holds; a mutation target stays in the write root."""
import dataclasses

import pytest

from beliefs import stored
from beliefs.root import open_corpus
from helpers.world import (
    FIXTURE_AUTHORITY, add_mounted_evidence, build_shared_contract_world, mount_config,
)
from science.config import ReadContext
from science.refusal import Refused


@pytest.fixture
def shared(certified_work, monkeypatch):
    import science.commands.run as run_module
    from beliefs.confinement import host_prerequisites
    from beliefs.recipe import MINIMAL_POLICY
    if host_prerequisites() is not None:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
    cfg = build_shared_contract_world(certified_work)
    return cfg, add_mounted_evidence(cfg, certified_work)


def _ids(cfg) -> dict[str, str]:
    return {mount.root.name: mount.corpus_id for mount in ReadContext.open(cfg).mounts()}


def test_a_mounted_record_is_cited_from_its_holder(shared):
    cfg, mounted = shared
    ctx = ReadContext.open(cfg)
    assert [m.root.name for m in ctx.session_mounts()] == sorted(
        ("corpus", "shared"), key=lambda name: _ids(cfg)[name])
    assert ctx.has_read_mounts() and ctx.session_ids() == frozenset(_ids(cfg).values())
    for ref in (mounted["data"], mounted["assessment"], "proposition:shared"):
        assert ctx.cited(ref).root.name == "shared"


def test_with_coordination_off_a_mounted_ref_refuses_naming_the_mount(shared):
    cfg, mounted = shared
    ctx = ReadContext.open(dataclasses.replace(cfg, coordination=None))
    assert [m.root.name for m in ctx.session_mounts()] == ["corpus"] and not ctx.has_read_mounts()
    with pytest.raises(Refused) as caught:
        ctx.cited(mounted["data"])
    assert caught.value.refusal.code == "invalid-input"
    assert _ids(cfg)["shared"] in caught.value.refusal.message
    assert "coordination" in caught.value.refusal.message


def test_a_ref_two_session_corpora_hold_refuses_naming_both(shared):
    cfg, _ = shared
    node = stored.proposition_node("twice", title="twice", claim={"operator": "affects"})
    for each in (cfg, mount_config(cfg)):
        open_corpus(each.write_root, authority=FIXTURE_AUTHORITY, profile=each.profile).add(node)
    with pytest.raises(Refused) as caught:
        ReadContext.open(cfg).cited("proposition:twice")
    assert caught.value.refusal.code == "invalid-input"
    assert all(corpus_id in caught.value.refusal.message for corpus_id in _ids(cfg).values())


def test_own_refuses_a_mounted_record_naming_the_mount(shared):
    cfg, mounted = shared
    with pytest.raises(Refused) as caught:
        ReadContext.open(cfg).own(mounted["spec"])
    assert caught.value.refusal.code == "invalid-input"
    assert _ids(cfg)["shared"] in caught.value.refusal.message
    assert "write root" in caught.value.refusal.message


def test_an_unheld_ref_refuses_without_a_hint(shared):
    cfg, _ = shared
    with pytest.raises(Refused) as caught:
        ReadContext.open(cfg).cited("proposition:nowhere")
    assert caught.value.refusal.message == "'proposition:nowhere' is not in the session's corpora"
