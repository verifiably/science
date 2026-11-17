"""Source correction preserves identity through the audited act and replay."""
import re
from dataclasses import replace

import pytest
from beliefs.root import open_corpus

from beliefs.source import source_address
from helpers.research import add_source, add_shared_source, correct_source, research_rig
from helpers.world import (FIXTURE_AUTHORITY, archive_config, build_two_corpus_world,
                           fixture_proposition_node, mint_project)
from science.config import corpus_id_at
from science.coordination import live_selection, resolve_one
from science.refusal import Refused

NAMES = ("source", "source-correct", "record", "note", "project", "project-select")


def test_a_correction_is_recorded_and_audited(certified_work):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, ctx):
        original = d.invoke("source", {"title": "Paper", "pmid": "123"}).text
        address = source_address({"pmid": "123"})
        uid = re.search(r"uid=(\S+)", original)[1]
        args = {"address": address, "doi": "10.1234/abc", "grounds": "index record"}
        reply = d.invoke("source-correct", args, invocation_id="CORRECT01")
        expected = source_address({"doi": "10.1234/abc", "pmid": "123"})
        assert reply.text.startswith(f"[source] {expected} uid={uid}\n")
        assert reply.text.count("[source]") == 1
        assert ctx.write_view().get(expected).uid == uid
        assert d._session.invocation_acts("CORRECT01")
        assert d.invoke("source-correct", args, invocation_id="CORRECT01").text == reply.text


def refused(d, address, **given):
    with pytest.raises(Refused) as caught:
        d.invoke("source-correct", {"address": address, "grounds": "index", **given}, invocation_id="REFUSE01")
    assert caught.value.refusal.code == "invalid-input"
    assert not d._session.invocation_acts("REFUSE01")
    return caught.value.refusal


@pytest.mark.parametrize("initial,doi", [({"pmid": "123"}, "10.1234/abc"),
                                         ({"doi": "10.1234/wrong", "pmid": "123"}, "10.1234/right")])
def test_a_later_identifier_keeps_earlier_notes(certified_work, initial, doi):
    cfg = build_two_corpus_world(certified_work)
    old = add_source(cfg, "corpus", "Paper", **initial)
    with research_rig(cfg, NAMES) as (d, _):
        d._selection = mint_project(d)
        d.invoke("note", {"name": "Earlier reading", "body": "Earlier note body", "about": [old.id]})
        d.invoke("source-correct", {"address": old.id, "doi": doi, "grounds": "index"})
        new = source_address({**initial, "doi": doi})
        for args in ({"address": old.id}, {"address": new}, {"doi": doi}, {"pmid": "123"}):
            text = d.invoke("record", args).text
            assert text.count("source:\n") == 1 and text.count("Earlier reading") == 1
        if "doi" in initial:
            with pytest.raises(Refused) as caught:
                d.invoke("source", {"title": "Other", "doi": initial["doi"]})
            assert caught.value.refusal.data["existing"][0]["redirect"] is True


def test_a_shared_source_is_refused(certified_work):
    cfg = build_two_corpus_world(certified_work)
    node = add_shared_source(cfg, "Paper", pmid="123")
    with research_rig(cfg, NAMES) as (d, ctx):
        project = resolve_one(ctx, mint_project(d))
        assert refused(d, node.id, doi="10.1234/abc").data["corpora"] == [
            corpus_id_at(root) for root in cfg.world.corpus_roots if root != cfg.write_root]
        assert ctx.write_view().get(node.id) == node
        live_selection(ctx, project)


def test_the_refusal_is_needed(certified_work):
    cfg = build_two_corpus_world(certified_work)
    node = add_shared_source(cfg, "Paper", pmid="123")
    with research_rig(cfg, NAMES) as (d, ctx):
        project = resolve_one(ctx, mint_project(d))
        correct_source(cfg, node.id, doi="10.1234/abc", pmid="123")
        with pytest.raises(Refused) as caught:
            live_selection(ctx, project)
        assert caught.value.refusal.code == "kernel-refused"


def test_a_shared_source_is_refused_without_coordination(certified_work):
    cfg = replace(build_two_corpus_world(certified_work), coordination=None)
    node = add_shared_source(cfg, "Paper", pmid="123")
    with research_rig(cfg, NAMES) as (d, _):
        assert refused(d, node.id, doi="10.1234/abc").data["corpora"]


@pytest.mark.parametrize("case", ["read", "non-source", "none", "unchanged", "canonical", "identifier", "redirect"])
def test_refusals(certified_work, case):
    cfg = build_two_corpus_world(certified_work)
    node = add_source(cfg, "archive" if case == "read" else "corpus", "Paper", doi="10.1234/abc", pmid="123")
    args = {"doi": "10.1234/new"}
    address = node.id
    if case == "non-source":
        address = "proposition:p1"
        open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile).add(
            fixture_proposition_node("p1"))
    if case == "none":
        args = {}
    if case in ("unchanged", "canonical"):
        args = {"doi": "https://doi.org/10.1234/ABC" if case == "canonical" else "10.1234/abc"}
    if case in ("identifier", "redirect"):
        other = add_source(cfg, "archive", "Other", doi="10.1234/new")
        if case == "redirect":
            # A retired basis is still taken even though no current identifier matches.
            archive = archive_config(cfg)
            open_corpus(archive.write_root, authority=FIXTURE_AUTHORITY, profile=archive.profile).correct_identifier(
                other.id, {"doi": "10.1234/retired"}, grounds="fixture")
    with research_rig(cfg, NAMES) as (d, _):
        data = refused(d, address, **args).data
        if case == "read":
            assert data["corpus"]
        elif case == "non-source":
            assert data["address"] == address
        elif case == "none":
            assert data == {"kind": "BasisMissing"}
        elif case in ("identifier", "redirect"):
            assert data["existing"]
            if case == "redirect":
                assert data["existing"][0]["redirect"] is True


def test_an_older_duplicate_does_not_block_an_unrelated_correction(certified_work):
    cfg = build_two_corpus_world(certified_work)
    node = add_source(cfg, "corpus", "Paper", doi="10.1234/abc", pmid="123")
    add_source(cfg, "archive", "Older duplicate", pmid="123")
    with research_rig(cfg, NAMES) as (d, _):
        assert "[source]" in d.invoke("source-correct", {
            "address": node.id, "accession": "NEW_1", "grounds": "index"}).text
