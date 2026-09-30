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


def test_a_spec_over_a_read_mount_dataset_refuses_naming_the_mount(two):
    """Review round 2: the kernel checks an assessment's observed dataset in the
    writer's own corpus, so a spec over the archive's dataset could reach `run`
    and never be assessed. It refuses at the first step instead."""
    data = hold_fixture_dataset(archive_config(two), "data.txt", b"y\n", "expression", **OBSERVED)
    archive_id = next(m.corpus_id for m in ReadContext.open(two).mounts() if m.root.name == "archive")
    with open_rig(two, ("claim", "spec")) as (d, _):
        d.invoke("claim", CLAIM)
        with pytest.raises(Refused) as caught:
            d.invoke("spec", dict(SPEC_FIELDS, target="proposition:claimed", dataset=data))
    assert caught.value.refusal.code == "invalid-input"
    assert archive_id in caught.value.refusal.message and "write root" in caught.value.refusal.message


def test_a_write_command_given_a_read_mount_record_names_the_mount(two):
    data = hold_fixture_dataset(archive_config(two), "data.txt", b"y\n", "expression", **OBSERVED)
    archive_id = next(m.corpus_id for m in ReadContext.open(two).mounts() if m.root.name == "archive")
    with open_rig(two, ("spec",)) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("spec", dict(SPEC_FIELDS, target="proposition:archived", dataset=data))
    assert caught.value.refusal.code == "invalid-input"
    assert archive_id in caught.value.refusal.message and "write root" in caught.value.refusal.message


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
