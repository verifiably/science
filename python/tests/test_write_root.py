"""Spec §5.5 (part 3 amendment): the write commands read the write root, and
share the one store's holdings and vocabularies with every mount."""
import pytest

from beliefs.corpus import ReadView
from helpers.world import OBSERVED, SPEC_FIELDS, archive_config, build_two_corpus_world, hold_fixture_dataset, open_rig
from science.config import ReadContext
from science.refusal import Refused

CLAIM = {"subject": "concept:disease-stage", "predicate": "affects", "object": "protein:PHF19",
         "layer": "causal", "polarity": "positive", "slug": "claimed"}


@pytest.fixture
def two(certified_work):
    return build_two_corpus_world(certified_work)


def test_claim_types_through_a_vocabulary_held_in_the_read_mount(two):
    with open_rig(two, ("claim",)) as (d, ctx):
        d.invoke("claim", CLAIM)
        assert ctx.write_view().holds("proposition:claimed")
    assert not ReadView.opened_at(two.world.world_root.parent / "archive").holds("proposition:claimed")


def test_a_spec_in_the_write_root_reads_its_dataset_there(two):
    data = hold_fixture_dataset(two, "data.txt", b"y\n", "expression", **OBSERVED)
    with open_rig(two, ("claim", "spec")) as (d, _):
        d.invoke("claim", CLAIM)
        out = d.invoke("spec", dict(SPEC_FIELDS, target="proposition:claimed", dataset=data))
        assert "analysis-spec:" in out.text


def test_a_spec_over_a_read_mount_dataset_is_minted(two):
    """Consumer spec decision 1 lifts part 3's refusal: the kernel now judges
    an assessment's observed dataset over the session's corpora."""
    data = hold_fixture_dataset(archive_config(two), "data.txt", b"y\n", "expression", **OBSERVED)
    with open_rig(two, ("claim", "spec")) as (d, ctx):
        d.invoke("claim", CLAIM)
        out = d.invoke("spec", dict(SPEC_FIELDS, target="proposition:claimed", dataset=data))
        assert "analysis-spec:" in out.text
        assert not ctx.write_view().holds(data)


def test_a_spec_on_a_proposition_only_the_mount_can_decode_refuses(two):
    """Consumer spec decision 2: proposition:archived uses the archive's
    corpus-local contract, which the writer does not pin, so the writer's own
    decode refuses, the mm30 case the second-project corpus must pin around."""
    data = hold_fixture_dataset(archive_config(two), "data.txt", b"y\n", "expression", **OBSERVED)
    with open_rig(two, ("spec",)) as (d, ctx):
        with pytest.raises(Refused) as caught:
            d.invoke("spec", dict(SPEC_FIELDS, target="proposition:archived", dataset=data))
        assert not any(n.kind == "analysis-spec" for n in ctx.write_view().iter_stored())
    assert caught.value.refusal.code == "invalid-input"


def test_holding_bytes_a_read_mount_declares_refuses_naming_its_record(two, certified_work):
    """Review round 1, P1: a second record would put one content-derived
    address in two corpora, and every selected `next` would refuse
    duplicate-location. The refusal names the record to use instead."""
    data = hold_fixture_dataset(archive_config(two), "data.txt", b"z\n", "expression", **OBSERVED)
    archive_id = next(m.corpus_id for m in ReadContext.open(two).mounts() if m.root.name == "archive")
    source = certified_work / "data.txt"
    source.write_bytes(b"z\n")
    with open_rig(two, ("dataset",)) as (d, ctx):
        with pytest.raises(Refused) as caught:
            d.invoke("dataset", {"path": str(source), "title": "expression again"})
        assert not any(n.kind == "dataset" for n in ctx.write_view().iter_stored())
    assert caught.value.refusal.code == "invalid-input"
    assert data in caught.value.refusal.message and archive_id in caught.value.refusal.message


def test_run_given_a_mounted_dataset_the_spec_does_not_observe_refuses_before_any_act(two, monkeypatch, certified_work):
    """Final review: `run` reads the dataset it is given in the write root, so
    the archive's dataset refuses by the archive's corpus id before the
    boundary runs anything."""
    import science.commands.run as run_module
    from helpers.world import _minted_ref, fixture_bundle

    monkeypatch.setattr(run_module, "host_prerequisites", lambda: None)
    monkeypatch.setattr(run_module, "execute_assessment_run",
                        lambda **_: pytest.fail("run reached the boundary"))
    data = hold_fixture_dataset(two, "data.txt", b"y\n", "expression", **OBSERVED)
    archived = hold_fixture_dataset(archive_config(two), "archived.txt", b"z\n", "expression", **OBSERVED)
    code, entrypoint, targets = fixture_bundle(certified_work)
    with open_rig(two, ("claim", "spec", "run")) as (d, ctx):
        d.invoke("claim", CLAIM)
        out = d.invoke("spec", dict(SPEC_FIELDS, target="proposition:claimed", dataset=data))
        spec = _minted_ref(out.text, "analysis-spec")
        with pytest.raises(Refused) as caught:
            d.invoke("run", {"spec": spec, "dataset": archived, "code": str(code),
                             "entrypoint": entrypoint, "targets": list(targets)})
        assert not any(n.kind == "run" for n in ctx.write_view().iter_stored())
    assert caught.value.refusal.code == "invalid-input"
    assert "is not the dataset the spec observes" in caught.value.refusal.message
