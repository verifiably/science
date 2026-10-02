"""Mount citations consumer spec, decisions 1–3: a write cites a record any
session corpus holds; a mutation target stays in the write root."""
import dataclasses

import pytest

from beliefs import stored
from beliefs.root import open_corpus
from helpers.world import (
    FIXTURE_AUTHORITY, SPEC_FIELDS, WORKING_FIELDS, _minted_ref, add_mounted_evidence,
    build_shared_contract_world, fixture_bundle, mint_fixture_run, mount_config, open_rig,
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


def test_spec_run_and_assess_in_the_write_root_cite_the_mount(shared, certified_work):
    """Decision 1: the second-project shape. Every new record lands in the
    write root, and every record it cites stays in the mount."""
    cfg, mounted = shared
    with open_rig(cfg, ("spec",)) as (d, _):
        spec = _minted_ref(d.invoke("spec", dict(WORKING_FIELDS, target="proposition:shared",
                                                 dataset=mounted["data"])).text, "analysis-spec")
    assert spec != mounted["spec"]
    run = mint_fixture_run(cfg, spec, mounted["data"], fixture_bundle(certified_work))
    with open_rig(cfg, ("assess",)) as (d, _):
        assessment = _minted_ref(d.invoke("assess", {"run": run}).text, "assessment")
    own = ReadContext.open(cfg).write_view()
    assert own.holds(spec) and own.holds(run) and own.holds(assessment)
    assert not own.holds("proposition:shared") and not own.holds(mounted["data"])


def test_run_prepares_a_mounted_spec_and_dataset(shared, certified_work):
    from science.commands.run import prepare
    cfg, mounted = shared
    code, entrypoint, targets = fixture_bundle(certified_work)
    prepared = prepare(ReadContext.open(cfg), mounted["spec"], mounted["data"], str(code), entrypoint, targets)
    assert list(prepared["held_inputs"]) == [prepared["spec"].input_roles[0].dataset]


def test_verify_of_a_mounted_assessment_lands_in_the_write_root(shared, certified_work):
    cfg, mounted = shared
    code, entrypoint, _ = fixture_bundle(certified_work)
    with open_rig(cfg, ("verify",)) as (d, _):
        out = d.invoke("verify", {"assessment": mounted["assessment"], "code": str(code),
                                  "entrypoint": entrypoint})
    verification = _minted_ref(out.text, "verification")
    assert ReadContext.open(cfg).write_view().holds(verification)


def test_supersedes_names_a_write_root_spec_only(shared):
    cfg, mounted = shared
    with open_rig(cfg, ("spec",)) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("spec", dict(SPEC_FIELDS, target="proposition:shared", dataset=mounted["data"],
                                  supersedes=mounted["spec"]))
    assert caught.value.refusal.code == "invalid-input"
    assert _ids(cfg)["shared"] in caught.value.refusal.message
    assert "write root" in caught.value.refusal.message
