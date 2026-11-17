"""Lookup includes configured live holders and resolves cited redirects."""
import json
from dataclasses import replace

import pytest
from nodes.core.corpus import Corpus
from helpers.world import build_two_corpus_world
from science.config import ReadContext, corpus_id_at
from science.lookup import (identifiers, require_identifiers, sources_carrying,
                            world_record, shared_with, write_root_only, unresolved_citations)
from science.refusal import Refused
from helpers.research import add_source, add_shared_source, correct_source


def test_identifiers_normalise_and_refuse():
    assert identifiers(doi="https://doi.org/10.1234/ABC") == {"doi": "10.1234/abc"}
    assert identifiers() == {}
    with pytest.raises(Refused) as caught:
        identifiers(doi="")
    assert caught.value.refusal.code == "invalid-input"
    assert caught.value.refusal.data == {"kind": "IdentifierMalformed", "scheme": "doi", "value": "", "reason": "empty"}
    with pytest.raises(Refused) as caught:
        require_identifiers({})
    assert caught.value.refusal.data == {"kind": "BasisMissing"}


@pytest.mark.parametrize("coordination", [2, None])
def test_carrying_finds_a_non_basis_identifier_in_a_read_mount(certified_work, coordination):
    cfg = replace(build_two_corpus_world(certified_work), coordination=coordination)
    node = add_source(cfg, "archive", "Paper", doi="10.1234/abc", pmid="123")
    found, = sources_carrying(ReadContext.open(cfg), {"pmid": "123"})
    assert found.node == node
    assert found.corpora == (corpus_id_at(certified_work / "archive"),)


def test_equal_copies_are_one_match(certified_work):
    cfg = build_two_corpus_world(certified_work)
    node = add_shared_source(cfg, "Paper", pmid="123")
    found, = sources_carrying(ReadContext.open(cfg), {"pmid": "123"})
    assert found.node == node
    assert found.corpora == tuple(sorted(corpus_id_at(root) for root in cfg.world.corpus_roots))


def test_differing_copies_refuse(certified_work):
    cfg = build_two_corpus_world(certified_work)
    node = add_source(cfg, "corpus", "Paper", pmid="123")
    Corpus(certified_work / "archive").add(node.model_copy(update={"title": "Different"}))
    for read in (lambda: sources_carrying(ReadContext.open(cfg), {"pmid": "123"}),
                 lambda: world_record(ReadContext.open(cfg), node.id),
                 lambda: unresolved_citations(ReadContext.open(cfg), [node.id])):
        with pytest.raises(Refused, match="copies differ") as caught:
            read()
        assert caught.value.refusal.code == "invalid-input"


def test_world_record_follows_a_redirect(certified_work):
    cfg = build_two_corpus_world(certified_work)
    old = add_source(cfg, "corpus", "Paper", pmid="123")
    new = correct_source(cfg, old.id, doi="10.1234/abc", pmid="123")
    found = world_record(ReadContext.open(cfg), old.id)
    assert found.node == new
    assert found.address == new.id != old.id
    assert found.entry(asked=old.id)["redirect"] is True
    assert json.loads(json.dumps(found.entry())) == {"address": new.id, "title": "Paper", "identifiers": {"doi": "10.1234/abc", "pmid": "123"}, "corpora": list(found.corpora)}


@pytest.mark.parametrize("coordination", [2, None])
def test_shared_with_names_the_other_holder(certified_work, coordination):
    cfg = replace(build_two_corpus_world(certified_work), coordination=coordination)
    node = add_shared_source(cfg, "Paper", pmid="123")
    ctx = ReadContext.open(cfg)
    assert shared_with(ctx, node) == (corpus_id_at(certified_work / "archive"),)
    assert not write_root_only(ctx, world_record(ctx, node.id))


def test_write_root_only(certified_work):
    cfg = build_two_corpus_world(certified_work)
    own = add_source(cfg, "corpus", "Own", pmid="123")
    other = add_source(cfg, "archive", "Other", pmid="456")
    ctx = ReadContext.open(cfg)
    assert shared_with(ctx, own) == ()
    assert write_root_only(ctx, world_record(ctx, own.id))
    assert not write_root_only(ctx, world_record(ctx, other.id))


def test_unresolved_citations_lists_every_miss_once(certified_work):
    cfg = build_two_corpus_world(certified_work)
    held = add_source(cfg, "archive", "Paper", pmid="123")
    assert unresolved_citations(ReadContext.open(cfg), ["source:missing", held.id, "source:other", "source:missing"]) == ["source:missing", "source:other"]
    assert unresolved_citations(ReadContext.open(replace(cfg, coordination=None)), [held.id]) == [held.id]


def test_retired_differing_holder_is_ignored(certified_work):
    from beliefs.root import open_world
    from helpers.world import FIXTURE_AUTHORITY
    cfg = build_two_corpus_world(certified_work)
    own = add_source(cfg, "corpus", "Paper", pmid="123")
    archive = certified_work / "archive"
    Corpus(archive).add(own.model_copy(update={"title": "Different"}))
    open_world(cfg.world, authority=FIXTURE_AUTHORITY).retire(corpus_id_at(archive))
    ctx = ReadContext.open(cfg)
    assert world_record(ctx, own.id).node == own
    assert sources_carrying(ctx, {"pmid": "123"}) == (world_record(ctx, own.id),)
    assert shared_with(ctx, own) == ()
    assert unresolved_citations(ctx, [own.id]) == []


def test_shared_with_finds_uid_after_address_moves(certified_work):
    cfg = build_two_corpus_world(certified_work)
    old = add_shared_source(cfg, "Paper", pmid="123")
    new = correct_source(cfg, old.id, doi="10.1234/abc", pmid="123")
    ctx = ReadContext.open(cfg)
    assert shared_with(ctx, new) == (corpus_id_at(certified_work / "archive"),)
    assert not write_root_only(ctx, world_record(ctx, new.id))


def test_research_rig_mints_coordination_with_selected_project(certified_work):
    from helpers.research import MINT_COORDINATION, mint_coordination_handler, research_rig
    from helpers.world import mint_project
    cfg = build_two_corpus_world(certified_work)
    with research_rig(cfg, ("project",), extra=((MINT_COORDINATION, mint_coordination_handler),)) as (d, _):
        d._selection = mint_project(d)
        result = d.invoke("mint-coordination", {"kind": "note", "name": "Reading", "body": "Read", "about": ["source:missing"]})
        assert "[note]" in result.text
