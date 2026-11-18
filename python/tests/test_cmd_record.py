"""Full record reads preserve identity and work without a selection."""
import re
from dataclasses import replace

import pytest
from beliefs import stored
from beliefs.coordination import CoordinationAddress, CoordinationRefused
from beliefs.corpus import CoordinationResolver
from beliefs.source_assertion import Bearing, Reading, Representation, SourceAssertion, Span
from helpers.research import (MINT_COORDINATION, add_shared_source, add_source,
                              add_source_assertion, correct_source,
                              mint_coordination_handler, raw_write_node, research_rig)
from helpers.world import (QUERY, build_two_corpus_world, build_world_without_coordination,
                           mint_project)
from nodes.core.relations import Relation
from science.config import corpus_id_at
from science.refusal import Refused
from test_cmd_projects import _twin

NAMES = ("record", "project", "project-select", "question", "task")
EXTRA = ((MINT_COORDINATION, mint_coordination_handler),)


def refused(d, arguments):
    with pytest.raises(Refused) as caught:
        d.invoke("record", arguments)
    assert caught.value.refusal.code == "invalid-input"
    return caught.value.refusal


def test_exactly_one_way_of_naming(certified_work):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, _):
        assert refused(d, {}).data == {"kind": "BasisMissing"}
        refused(d, {"address": "source:missing", "pmid": "123"})


def test_a_source_by_each_identifier_and_by_address(certified_work):
    cfg = build_two_corpus_world(certified_work)
    node = add_source(cfg, "corpus", "Paper", doi="10.1234/abc", pmid="123", isbn="9780306406157", accession="DATA_1")
    with research_rig(cfg, NAMES) as (d, _):
        for args in ({"doi": "https://doi.org/10.1234/ABC"}, {"pmid": "123"},
                     {"isbn": "9780306406157"}, {"accession": "DATA_1"},
                     {"doi": "10.1234/abc", "pmid": "123"}, {"address": node.id}):
            text = d.invoke("record", args).text
            assert "source:\n" in text and f"address: {node.id}" in text
            assert "doi: 10.1234/abc" in text and "pmid: 123" in text
            assert "correctable here: yes" in text


def test_no_match_is_a_finding_not_a_refusal(certified_work):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, _):
        text = d.invoke("record", {"pmid": "123"}).text
    assert text.startswith("! ") and "source:\n" not in text


def test_two_sources_print_both_with_a_finding(certified_work):
    cfg = build_two_corpus_world(certified_work)
    first = add_source(cfg, "corpus", "First", doi="10.1234/abc")
    second = add_source(cfg, "archive", "Second", pmid="123")
    with research_rig(cfg, NAMES) as (d, _):
        text = d.invoke("record", {"doi": "10.1234/abc", "pmid": "123"}).text
    assert first.id in text and second.id in text and "may be one work" in text
    assert text.count("\nsource:\n") + text.startswith("source:\n") == 2


def test_equal_copies_print_once(certified_work):
    cfg = build_two_corpus_world(certified_work)
    add_shared_source(cfg, "Paper", pmid="123")
    with research_rig(cfg, NAMES) as (d, _):
        text = d.invoke("record", {"pmid": "123"}).text
    assert text.count("source:\n") == 1 and "correctable here: no" in text
    assert all(corpus_id_at(root) in text for root in cfg.world.corpus_roots)


def test_a_missing_address_refuses(certified_work):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, _):
        refused(d, {"address": "source:missing"})
        refused(d, {"address": "coord:" + "f" * 32})


def test_a_proposition_prints_its_claim(certified_work):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, _):
        text = d.invoke("record", {"address": "proposition:archived"}).text
    assert "operator:" in text


def test_a_coordination_record_by_coord_address_and_by_stored_id(certified_work):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, ctx):
        d._selection = mint_project(d)
        out = d.invoke("question", {"name": "Question", "body": "Full body", "query": QUERY}).text
        stored_id = re.search(r"question:[a-f0-9.]+", out)[0]
        _, project, local, uid = re.split(r"[:.]", stored_id)
        address = f"coord:{project}/{local}"
        for ref in (address, f"{address}@{uid}", stored_id):
            text = d.invoke("record", {"address": ref}).text
            assert f"address: {address}\n" in text
            assert f"pinned: {address}@{uid}" in text and "Full body" in text and "query:" in text


def test_a_divergent_address_prints_every_tip(certified_work, monkeypatch):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, ctx):
        project = mint_project(d)
        real = ctx.coordination().resolve(project)
        twin = _twin(real, "Other title")
        resolve, revision = CoordinationResolver.resolve, CoordinationResolver.revision
        monkeypatch.setattr(CoordinationResolver, "resolve", lambda self, address:
                            CoordinationRefused("divergent-view", (real.uid, twin.uid))
                            if address == project else resolve(self, address))
        monkeypatch.setattr(CoordinationResolver, "revision", lambda self, uid:
                            twin if uid == twin.uid else revision(self, uid))
        text = d.invoke("record", {"address": str(project)}).text
        assert real.uid in text and twin.uid in text and "Other title" in text


def test_notes_about_a_world_record(certified_work):
    cfg = build_two_corpus_world(certified_work)
    old = add_source(cfg, "corpus", "Paper", pmid="123")
    with research_rig(cfg, NAMES, extra=EXTRA) as (d, _):
        d._selection = mint_project(d)
        d.invoke("mint-coordination", {"kind": "note", "name": "Reading", "body": "Read", "about": [old.id]})
        text = d.invoke("record", {"address": old.id}).text
        assert "notes about this record:" in text and text.count(": Reading\n") == 1
        d._selection = None
        assert "notes about this record:" not in d.invoke("record", {"address": old.id}).text
    new = correct_source(cfg, old.id, doi="10.1234/abc", pmid="123")
    with research_rig(cfg, NAMES) as (d, _):
        # Select the persisted project by name in a fresh session after correction.
        d.invoke("project-select", {"target": "health"})
        for ref in (old.id, new.id):
            text = d.invoke("record", {"address": ref}).text
            assert text.count(": Reading\n") == 1 and f"formerly: {old.id}" in text


@pytest.mark.parametrize("diverged", [False, True])
def test_an_unresolvable_selection_is_a_finding(certified_work, monkeypatch, diverged):
    cfg = build_two_corpus_world(certified_work)
    node = add_source(cfg, "corpus", "Paper", pmid="123")
    with research_rig(cfg, NAMES) as (d, ctx):
        project = mint_project(d)
        d._selection = project
        real = ctx.coordination().resolve(project)
        monkeypatch.setattr(CoordinationResolver, "resolve", lambda self, address:
                            CoordinationRefused("divergent-view", (real.uid, "e" * 32)) if diverged else None)
        text = d.invoke("record", {"address": node.id}).text
        assert "source:\n" in text and "\n! " in text


def test_without_coordination_a_world_record_still_prints(certified_work):
    cfg = build_world_without_coordination(certified_work)
    from beliefs import stored
    from beliefs.root import open_corpus
    from helpers.world import FIXTURE_AUTHORITY
    node = stored.source_node(title="Paper", identifiers={"pmid": "123"})
    open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile).add(node)
    with research_rig(cfg, NAMES) as (d, _):
        for args in ({"address": node.id}, {"pmid": "123"}):
            assert "source:\n" in d.invoke("record", args).text
        refused(d, {"address": "coord:" + "f" * 32})


def test_without_coordination_an_identifier_finds_a_configured_read_corpus(certified_work):
    cfg = replace(build_two_corpus_world(certified_work), coordination=None)
    node = add_source(cfg, "archive", "Read-mounted paper", pmid="456")
    with research_rig(cfg, NAMES) as (d, _):
        for args in ({"address": node.id}, {"pmid": "456"}):
            text = d.invoke("record", args).text
            assert f"address: {node.id}" in text and "source:\n" in text
            assert "correctable here: no" in text
        refused(d, {"address": "coord:" + "f" * 32})


def test_a_source_assertion_prints_relations_and_facets_without_representer_error(certified_work):
    cfg = build_two_corpus_world(certified_work)
    corpus_src = add_source(cfg, "corpus", "Corpus paper", pmid="123")
    archive_src = add_source(cfg, "archive", "Archive paper", pmid="456")
    in_corpus = add_source_assertion(
        cfg, "corpus", source=corpus_src.id, proposition="proposition:archived", body="Corpus assertion context."
    )
    in_archive = add_source_assertion(
        cfg, "archive", source=archive_src.id, proposition="proposition:archived",
        locator="Discussion, [2]", body="Archive assertion context.",
    )
    with research_rig(cfg, NAMES) as (d, _):
        text = d.invoke("record", {"address": in_corpus.id}).text
        assert "source-assertion:\n" in text
        assert "predicate: anchored_in" in text
        assert "sha256:" in text
        assert "bears_on:" in text
        assert "Corpus assertion context." in text
    with research_rig(replace(cfg, coordination=None), NAMES) as (d, _):
        text = d.invoke("record", {"address": in_archive.id}).text
        assert "source-assertion:\n" in text
        assert "predicate: anchored_in" in text
        assert "sha256:" in text
        assert "bears_on:" in text
        assert "Archive assertion context." in text


def test_source_lists_assertions_across_mounts_and_redirects(certified_work):
    cfg = build_two_corpus_world(certified_work)
    old = add_source(cfg, "corpus", "Paper", pmid="123")
    other = add_source(cfg, "corpus", "Unasserted paper", pmid="999")
    assertion = add_source_assertion(cfg, "corpus", source=old.id, proposition="proposition:archived")
    raw_write_node(certified_work / "archive", assertion)
    new = correct_source(cfg, old.id, doi="10.1234/abc", pmid="123")
    expected = f"  {assertion.id}: asserts proposition:archived (extracted by agent:reader) — Paraphrase."

    with research_rig(cfg, NAMES) as (d, _):
        d._selection = mint_project(d)
        for args in ({"address": old.id}, {"address": new.id}, {"doi": "10.1234/abc"}, {"pmid": "123"}):
            text = d.invoke("record", args).text
            assert "source assertions:\n" in text
            assert text.count(expected) == 1
            assert text.index("source assertions:\n") < text.index("notes about this record:\n")
        assert "source assertions:" not in d.invoke("record", {"address": other.id}).text

    with research_rig(replace(cfg, coordination=None), NAMES) as (d, _):
        for args in ({"address": old.id}, {"address": new.id}, {"doi": "10.1234/abc"}, {"pmid": "123"}):
            text = d.invoke("record", args).text
            assert "source assertions:\n" in text
            assert text.count(expected) == 1
        assert "source assertions:" not in d.invoke("record", {"address": other.id}).text


def test_proposition_lists_source_assertions(certified_work):
    cfg = build_two_corpus_world(certified_work)
    with research_rig(cfg, NAMES) as (d, _):
        assert "source assertions:" not in d.invoke("record", {"address": "proposition:archived"}).text
    src = add_source(cfg, "corpus", "Paper", pmid="123")
    assertion = add_source_assertion(cfg, "corpus", source=src.id, proposition="proposition:archived")
    expected = f"  {assertion.id}: asserts in {src.id} (extracted by agent:reader) — Paraphrase."
    with research_rig(cfg, NAMES) as (d, _):
        d._selection = mint_project(d)
        text = d.invoke("record", {"address": "proposition:archived"}).text
        assert "source assertions:\n" in text
        assert text.count(expected) == 1
        assert text.index("source assertions:\n") < text.index("notes about this record:\n")
    with research_rig(replace(cfg, coordination=None), NAMES) as (d, _):
        text = d.invoke("record", {"address": "proposition:archived"}).text
        assert "source assertions:\n" in text
        assert text.count(expected) == 1


@pytest.mark.parametrize(
    ("damage", "expected_kind"),
    [
        ("stale_stamp", "SemanticHashStale"),
        ("malformed_facet_restamped", "MalformedRecord"),
        ("extra_assesses_edge", "SourceAssertionRefused"),
    ],
)
def test_damaged_source_assertion_refuses_kernel_refused(certified_work, damage, expected_kind):
    cfg = build_two_corpus_world(certified_work)
    src = add_source(cfg, "corpus", "Paper", pmid="123")
    val = SourceAssertion(
        source=src.id,
        read=Reading(
            representation=Representation(sha256="a" * 64, media_type="text/markdown", extent="full"),
            span=Span(quote="Quoted span.", locator="Results, [1]"),
            extracted_by="agent:reader",
        ),
        bears_on=Bearing(sign="asserts", proposition="proposition:archived"),
        recorded_by="fixture",
    )
    damaged = stored.source_assertion_node(val, title="Paraphrase.")
    if damage == "stale_stamp":
        del damaged.facets[stored.SOURCE_ASSERTION_FACET]["recorded_by"]
    elif damage == "malformed_facet_restamped":
        del damaged.facets[stored.SOURCE_ASSERTION_FACET]["recorded_by"]
        stored.stamp_semantic_identity(damaged)
    elif damage == "extra_assesses_edge":
        damaged.relations.append(Relation(source=damaged.id, predicate="assesses", target="proposition:archived"))
        stored.stamp_semantic_identity(damaged)
    raw_write_node(cfg.write_root, damaged)
    with research_rig(cfg, NAMES) as (d, _):
        for target in (damaged.id, src.id, "proposition:archived"):
            with pytest.raises(Refused) as caught:
                d.invoke("record", {"address": target})
            assert caught.value.refusal.code == "kernel-refused"
            assert caught.value.refusal.data == {"kind": expected_kind}
