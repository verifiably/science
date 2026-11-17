"""Source writes deduplicate shared identifiers before any governed act."""
import re
from dataclasses import replace

import pytest
from beliefs.source import source_address
from helpers.research import add_source, correct_source, research_rig
from helpers.world import build_two_corpus_world, mint_project
from science.config import corpus_id_at
from science.refusal import Refused

NAMES = ("source", "record", "project", "project-select")


def refused(d, args, iid="SOURCE01"):
    with pytest.raises(Refused) as caught:
        d.invoke("source", {"title": "Paper", **args}, invocation_id=iid)
    assert caught.value.refusal.code == "invalid-input"
    assert not d._session.invocation_acts(iid)
    return caught.value.refusal


def test_a_source_is_minted_without_a_selection(certified_work):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, _):
        text = d.invoke("source", {"title": "Paper", "doi": "https://doi.org/10.1234/ABC"}).text
        assert text.startswith("[source] source:")
        assert re.search(r"source:[a-f0-9]+", text)[0] == source_address({"doi": "10.1234/abc"})


def test_no_identifier_refuses(certified_work):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, _):
        assert refused(d, {}).data == {"kind": "BasisMissing"}


def test_a_malformed_identifier_refuses(certified_work):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, _):
        assert refused(d, {"doi": "broken"}).data["kind"] == "IdentifierMalformed"


def test_a_blank_title_refuses(certified_work):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, _):
        refused(d, {"title": " \n", "pmid": "123"})


@pytest.mark.parametrize("where,held,given,message", [
    ("corpus", {"pmid": "123"}, {"pmid": "123"}, "already recorded"),
    ("corpus", {"pmid": "123"}, {"doi": "10.1234/abc", "pmid": "123"}, "source-correct"),
    ("corpus", {"doi": "10.1234/abc", "pmid": "123"}, {"pmid": "123"}, "already recorded"),
    ("archive", {"pmid": "123"}, {"doi": "10.1234/abc", "pmid": "123"}, "cannot be changed here"),
    ("corpus", {"doi": "10.1234/abc"}, {"doi": "https://doi.org/10.1234/ABC"}, "already recorded"),
])
def test_duplicates_refuse_before_any_act(certified_work, where, held, given, message):
    cfg = build_two_corpus_world(certified_work)
    node = add_source(cfg, where, "Existing paper", **held)
    with research_rig(cfg, NAMES) as (d, _):
        first = refused(d, given)
        assert message in first.message
        assert first.data["existing"][0]["address"] == node.id
        root = cfg.write_root if where == "corpus" else next(r for r in cfg.world.corpus_roots if r != cfg.write_root)
        assert first.data["existing"][0]["corpora"] == [corpus_id_at(root)]
        assert refused(d, given) == first


def test_a_read_mount_source_refuses_without_coordination(certified_work):
    cfg = replace(build_two_corpus_world(certified_work), coordination=None)
    node = add_source(cfg, "archive", "Read-mounted", pmid="123")
    with research_rig(cfg, NAMES) as (d, _):
        assert refused(d, {"pmid": "123"}).data["existing"][0]["address"] == node.id


def test_a_redirect_address_refuses(certified_work):
    cfg = build_two_corpus_world(certified_work)
    old = add_source(cfg, "corpus", "Paper", doi="10.1234/wrong", pmid="123")
    new = correct_source(cfg, old.id, doi="10.1234/right", pmid="123")
    with research_rig(cfg, NAMES) as (d, _):
        entry = refused(d, {"doi": "10.1234/wrong"}).data["existing"][0]
        assert entry["address"] == new.id and entry["redirect"] is True


def test_disjoint_identifiers_mint_a_second_record_KNOWN_LIMIT(certified_work):
    """§6 Disjoint identifiers: minting pins a stated limit and should fail on
    purpose if the limit is ever closed.
    """
    cfg = build_two_corpus_world(certified_work)
    old = add_source(cfg, "archive", "Paper", pmid="123")
    with research_rig(cfg, NAMES) as (d, _):
        first = mint_project(d, name="A")
        d.invoke("project-select", {"target": str(first)})
        given = {"doi": "10.1234/abc", "pmid": "123"}
        assert old.id in d.invoke("record", given).text
        second = mint_project(d, name="B")
        d.invoke("project-select", {"target": str(second)})
        assert old.id in d.invoke("record", given).text
        assert refused(d, given).data["existing"][0]["address"] == old.id
        text = d.invoke("source", {"title": "Paper", "doi": "10.1234/abc"}).text
        assert text.startswith("[source] source:") and old.id not in text
