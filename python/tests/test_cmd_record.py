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


def _attestation(cfg, left, right, token, *, stance=1, actor="fixture", grounds="Same edition.", root=None):
    event = stored.coreference_attestation_node(
        title="Signed source comparison", endpoints=(left, right), stance=stance,
        actor=actor, grounds=grounds, event_token=token,
    )
    raw_write_node(cfg.write_root if root is None else root, event)
    return event


def _build_coreference_world(work):
    cfg = build_two_corpus_world(work)
    a = add_source(cfg, "corpus", "Publisher", doi="10.1234/article")
    b = add_source(cfg, "archive", "Index", pmid="123")
    c = add_source(cfg, "corpus", "Repository", accession="ARTICLE_1")
    return cfg, a.id, b.id, c.id


@pytest.fixture
def coreference_world(certified_worker_work):
    from helpers.snapshot import snapshot

    saved = snapshot(certified_worker_work, "source-coreference-read", _build_coreference_world)
    saved.restore()
    return saved.value


def test_coreference_is_direct_and_counts_each_distinct_unit(coreference_world, monkeypatch):
    from science.commands import record

    cfg, a, b, c = coreference_world
    first = _attestation(cfg, b, a, "first")
    raw_write_node(cfg.write_root.parent / "archive", first)
    later = _attestation(cfg, a, b, "repeat")
    next_pair = _attestation(cfg, b, c, "second-pair")

    with research_rig(cfg, NAMES) as (dispatch, _):
        for args in ({"address": a}, {"doi": "10.1234/article"}):
            text = dispatch.invoke("record", args).text
            assert "source coreference" in text
            assert "state: positive" in text
            assert "balance: 1" in text and "distinct_key_count: 1" in text
            evidence = sorted((first.id, later.id))
            assert f"attestations: {', '.join(evidence)}" in text
            assert c not in text and next_pair.id not in text
        event_text = dispatch.invoke("record", {"address": first.id}).text
        assert "Same edition." in event_text and a in event_text and b in event_text

        scans = []
        original = record.source_coreference

        def scan(ctx):
            scans.append(ctx)
            return original(ctx)

        monkeypatch.setattr(record, "source_coreference", scan)
        text = dispatch.invoke("record", {"doi": "10.1234/article", "accession": "ARTICLE_1"}).text
        assert len(scans) == 1
        assert text.count("source:\n") == 2
        assert text.count("state: positive") == 2
        assert "state: unassessed" in text and "may be one work" in text
        assert b in text and next_pair.id in text

    _attestation(cfg, a, b, "second-actor", actor="other")
    _attestation(cfg, a, b, "further-grounds", grounds="Independent catalog cross-check.")
    for count in range(1, 5):
        _attestation(cfg, a, b, f"counter-{count}", stance=-1, grounds=f"Contrary evidence {count}.")
        if count in (3, 4):
            with research_rig(cfg, NAMES) as (dispatch, _):
                text = dispatch.invoke("record", {"address": a}).text
                assert f"state: {'contested' if count == 3 else 'negative'}" in text
                assert f"balance: {3 - count}" in text
                assert f"distinct_key_count: {3 + count}" in text


def test_historical_redirect_leaves_exact_pair_unassessed_and_marks_missing_peer(coreference_world):
    from beliefs.root import open_world
    from helpers.world import FIXTURE_AUTHORITY

    cfg, a, b, _ = coreference_world
    event = _attestation(cfg, a, b, "before-correction")
    corrected = correct_source(cfg, a, doi="10.1234/corrected")
    with research_rig(cfg, NAMES) as (dispatch, _):
        text = dispatch.invoke("record", {"doi": "10.1234/corrected", "pmid": "123"}).text
        assert "state: historical-redirect" in text and "state: unassessed" in text
        assert "state: positive" not in text
        assert f"{a} (redirected to {corrected.id})" in text and event.id in text

    archive = cfg.write_root.parent / "archive"
    open_world(cfg.world, authority=FIXTURE_AUTHORITY).retire(corpus_id_at(archive))
    with research_rig(cfg, NAMES) as (dispatch, _):
        text = dispatch.invoke("record", {"address": corrected.id}).text
        assert "state: historical-redirect" in text and f"{b} (unavailable)" in text
        direct = dispatch.invoke("record", {"address": event.id}).text
        assert "Same edition." in direct and b in direct


def test_missing_peer_is_unavailable_and_retired_event_holder_is_ignored(coreference_world):
    from beliefs.root import open_world
    from helpers.world import FIXTURE_AUTHORITY

    cfg, a, b, c = coreference_world
    archive = cfg.write_root.parent / "archive"
    held = _attestation(cfg, a, b, "held")
    retired = _attestation(cfg, a, c, "retired", root=archive)
    open_world(cfg.world, authority=FIXTURE_AUTHORITY).retire(corpus_id_at(archive))
    with research_rig(cfg, NAMES) as (dispatch, _):
        text = dispatch.invoke("record", {"address": a}).text
        assert "state: unavailable" in text and f"{b} (unavailable)" in text
        assert held.id in text and retired.id not in text
        assert f"{a} (exact)" in text


@pytest.mark.parametrize("problem", ["mixed", "inadmissible", "untyped", "empty-local", "actor",
                                     "id", "facets", "coord-facet", "relations", "wrong-kind", "unstamped", "stale"])
def test_coreference_corruption_refuses_both_read_paths(coreference_world, problem):
    cfg, a, b, _ = coreference_world
    endpoints = {
        "mixed": ("source:unmounted", "proposition:unmounted"),
        "inadmissible": ("policy:first", "policy:second"),
        "untyped": ("source", "source:second"),
        "empty-local": ("source:", "source:second"),
        "wrong-kind": (a, "source:redirected"),
    }.get(problem, (a, b))
    event = stored.coreference_attestation_node(
        title="Signed", endpoints=endpoints, stance=1, actor="fixture", grounds="Grounds", event_token="bad",
    )
    if problem == "actor":
        event.facets[stored.COREFERENCE_ATTESTATION_FACET]["actor"] = ""
    elif problem == "id":
        event = event.model_copy(update={"id": "coreference-attestation:" + "a" * 64})
    elif problem == "facets":
        event.facets["invented"] = {"value": True}
    elif problem == "coord-facet":
        event.facets[stored.COORDINATION_FACET] = {"project": "a" * 32}
    elif problem == "relations":
        event.relations.append(Relation(source=event.id, predicate="assesses", target=a))
    elif problem == "wrong-kind":
        node = stored.proposition_node("redirected", title="Wrong kind", claim={}, display_statement="Wrong kind")
        raw_write_node(cfg.write_root, node.model_copy(update={"deprecated_ids": ["source:redirected"]}))
    if problem == "unstamped":
        event.facets.pop(stored.SEMANTIC_IDENTITY_FACET)
    elif problem == "stale":
        event.facets[stored.COREFERENCE_ATTESTATION_FACET]["grounds"] = "Tampered"
    else:
        stored.stamp_semantic_identity(event)
    raw_write_node(cfg.write_root, event)
    with research_rig(cfg, NAMES) as (dispatch, _):
        paths = ({"address": event.id}, {"address": a}, {"doi": "10.1234/article"})
        for args in paths:
            with pytest.raises(Refused) as caught:
                dispatch.invoke("record", args)
            refusal = caught.value.refusal
            assert refusal.code == "kernel-refused"
            assert refusal.data == {
                "kind": {"unstamped": "SemanticHashMissing", "stale": "SemanticHashStale"}.get(
                    problem, "MalformedRecord"),
            }
            assert event.id in refusal.message


def test_valid_other_kind_attestation_is_inspectable_and_omitted_from_source_report(coreference_world):
    cfg, a, _, _ = coreference_world
    event = _attestation(cfg, "proposition:absent", "proposition:archived", "other-kind")
    with research_rig(cfg, NAMES) as (dispatch, _):
        text = dispatch.invoke("record", {"address": event.id}).text
        assert "proposition:archived" in text and "Same edition." in text
        text = dispatch.invoke("record", {"address": a}).text
        assert "source coreference" not in text and event.id not in text


def test_differing_attestation_replicas_refuse_both_read_paths(coreference_world):
    cfg, a, b, _ = coreference_world
    event = _attestation(cfg, a, b, "replicated")
    archive = cfg.write_root.parent / "archive"
    raw_write_node(archive, event.model_copy(update={"title": "Different title"}))
    with research_rig(cfg, NAMES) as (dispatch, _):
        for address in (a, event.id):
            refusal = refused(dispatch, {"address": address})
            assert "copies differ" in refusal.message
            assert all(corpus_id_at(root) in refusal.message for root in (archive, cfg.write_root))


def test_coreference_pages_reassemble_the_full_ordered_report(coreference_world):
    from science.cursor import MIN_OUTPUT_BUDGET

    cfg, a, b, c = coreference_world
    for count in range(17):
        _attestation(cfg, a, b, f"one-{count}")
        _attestation(cfg, a, c, f"two-{count}")
    args = {"doi": "10.1234/article", "pmid": "123"}
    with research_rig(cfg, NAMES) as (dispatch, _):
        full = dispatch.invoke("record", args).text
        assert full.count("state: positive") == 3
        dispatch._decls["record"] = replace(dispatch._decls["record"], output_budget=MIN_OUTPUT_BUDGET + 300)
        page = dispatch.invoke("record", args).text
        pieces = []
        while match := re.search(r"\n… truncated at \d+ bytes; continue with cursor (\S+)\n$", page):
            pieces.append(page[:match.start()])
            assert len(pieces) < 30
            page = dispatch.invoke("record", args, cursor=match[1]).text
        assert pieces and "".join([*pieces, page]) == full


def test_coreference_endpoint_read_fault_is_a_refusal_on_both_paths(coreference_world, monkeypatch):
    from nodes.core.errors import RefError
    from science import lookup

    cfg, a, b, _ = coreference_world
    event = _attestation(cfg, a, b, "read-fault")
    resolve = lookup.world_record

    def read(ctx, ref):
        if ref == b:
            raise RefError("held peer could not be read")
        return resolve(ctx, ref)

    monkeypatch.setattr(lookup, "world_record", read)
    with research_rig(cfg, NAMES) as (dispatch, _):
        for args in ({"address": event.id}, {"address": a}, {"doi": "10.1234/article"}):
            with pytest.raises(Refused) as caught:
                dispatch.invoke("record", args)
            assert caught.value.refusal.code == "kernel-refused"
            assert caught.value.refusal.data == {"kind": "RefError"}
            assert "held peer could not be read" in caught.value.refusal.message


def test_coreference_keeps_each_projects_notes_and_each_sources_assertions(coreference_world):
    cfg, a, b, _ = coreference_world
    _attestation(cfg, a, b, "linked")
    left = add_source_assertion(cfg, "corpus", source=a, proposition="proposition:archived",
                                quote="A distinct passage from the publisher.")
    right = add_source_assertion(cfg, "archive", source=b, proposition="proposition:archived",
                                 quote="A distinct passage from the index.")
    with research_rig(cfg, NAMES, extra=EXTRA) as (dispatch, _):
        for name, address in (("publisher-project", a), ("index-project", b)):
            mint_project(dispatch, name)
            dispatch.invoke("project-select", {"target": name})
            dispatch.invoke("mint-coordination", {
                "kind": "note", "name": f"Reading for {name}", "body": "Read", "about": [address],
            })
        for name, chosen in (("publisher-project", a), ("index-project", b)):
            dispatch.invoke("project-select", {"target": name})
            for address, assertion, other in ((a, left, right), (b, right, left)):
                text = dispatch.invoke("record", {"address": address}).text
                assert "state: positive" in text
                assert assertion.id in text and other.id not in text
                assert (f"Reading for {name}" in text) == (address == chosen)
        text = dispatch.invoke("record", {"doi": "10.1234/article", "pmid": "123"}).text
        assert text.count("source:\n") == 2
        assert text.count("state: positive") == 2
        assert "state: unassessed" not in text
        assert left.id in text and right.id in text


RESERVATION_NAMES = ("record", "exposure-event", "reservation-assignment")


def _reservation_chain(cfg):
    """A read event, a root that considers it and a successor that suspends a reserved group, all in the write root."""
    from helpers.reservation import assignment_facet, assignment_node, event_facet, event_node, group, hold_record

    source = hold_record(cfg.write_root, cfg.profile, stored.source_node(title="GSE24080", identifiers={"accession": "GSE24080"}))
    event = hold_record(cfg.write_root, cfg.profile, event_node(event_facet(
        channel="read", subjects=[source.id], bound={"freeze": "sha256:" + "3" * 64}, evidence=["atoms-event:3d426b17"],
        account="First line.\nSecond line."), actor="fixture"))
    root = hold_record(cfg.write_root, cfg.profile, assignment_node(
        assignment_facet(events=[event.id], groups=[group("a", role="reserved"), group("b")]), actor="fixture"))
    successor = hold_record(cfg.write_root, cfg.profile, assignment_node(assignment_facet(
        events=[event.id], groups=[group("a"), group("b")], predecessor=root.id, evidence=[event.id], flagged=[]),
        actor="fixture"))
    return event, root, successor


def _facets_of(text):
    import yaml
    return yaml.safe_load(text.split("  facets: ", 1)[1].split("\nchanges from", 1)[0])


def test_exposure_and_reservation_records_render_their_whole_facet_and_changes(certified_work):
    cfg = build_two_corpus_world(certified_work)
    event, root, successor = _reservation_chain(cfg)
    with research_rig(cfg, RESERVATION_NAMES) as (d, _):
        text = d.invoke("record", {"address": event.id}).text
        assert f"address: {event.id}\n" in text and "changes from the predecessor" not in text
        assert _facets_of(text)[stored.EXPOSURE_EVENT_FACET] == event.facets[stored.EXPOSURE_EVENT_FACET]
        text = d.invoke("record", {"address": root.id}).text
        assert "changes from the predecessor:\n  count: 0\n" in text
        # the successor is the head; the root is a historical assignment and reads the same way
        text = d.invoke("record", {"address": successor.id}).text
        assert _facets_of(text)[stored.RESERVATION_ASSIGNMENT_FACET] == (
            successor.facets[stored.RESERVATION_ASSIGNMENT_FACET])
        assert ('changes from the predecessor:\n  count: 1\n'
                '  changed: testing/cohort "a"; was reserved; suspended\n') in text


def test_a_historical_assignment_keeps_its_own_changes_after_it_is_superseded(certified_work):
    from helpers.reservation import assignment_facet, assignment_node, digest, group, hold_record

    cfg = build_two_corpus_world(certified_work)
    event, _, successor = _reservation_chain(cfg)
    hold_record(cfg.write_root, cfg.profile, assignment_node(assignment_facet(
        events=[event.id], groups=[group("a"), group("b")], predecessor=successor.id, inputs={"roster.yaml": digest("next")}),
        actor="fixture"))
    with research_rig(cfg, RESERVATION_NAMES) as (d, _):
        assert 'changed: testing/cohort "a"; was reserved; suspended' in d.invoke("record", {"address": successor.id}).text


@pytest.mark.parametrize("damage,kind", [("stale-stamp", "SemanticHashStale"), ("malformed-facet", "MalformedRecord")])
@pytest.mark.parametrize("which", ["event", "assignment"])
def test_a_damaged_exposure_or_reservation_record_refuses_structurally(certified_work, which, damage, kind):
    from helpers.reservation import assignment_facet, assignment_node, event_facet, event_node

    cfg = build_two_corpus_world(certified_work)
    node, facet, field = ((event_node(event_facet(), actor="fixture"), stored.EXPOSURE_EVENT_FACET, "account")
                          if which == "event" else
                          (assignment_node(assignment_facet(), actor="fixture"), stored.RESERVATION_ASSIGNMENT_FACET, "rule"))
    del node.facets[facet][field]
    if damage == "malformed-facet":
        stored.stamp_semantic_identity(node)
    raw_write_node(cfg.write_root, node)
    with research_rig(cfg, RESERVATION_NAMES) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("record", {"address": node.id})
    assert caught.value.refusal.code == "kernel-refused" and caught.value.refusal.data == {"kind": kind}


@pytest.mark.parametrize("predecessor", ["missing", "divergent", "malformed"])
def test_an_assignment_whose_predecessor_cannot_be_read_refuses_structurally(certified_work, predecessor):
    from helpers.research import archive_config
    from helpers.reservation import assignment_facet, assignment_node, digest, hold_record

    cfg = build_two_corpus_world(certified_work)
    archive = archive_config(cfg)
    root = assignment_node(assignment_facet(groups=[{"units": [{"start": "open", "end": "2026-01-01T00:00:00Z"}],
                                                     "role": "open"}]), actor="fixture")
    if predecessor == "divergent":
        for index, target in enumerate((cfg, archive)):
            hold_record(target.write_root, target.profile, root.model_copy(update={"title": f"copy {index}"}))
    elif predecessor == "malformed":
        damaged = root.model_copy(deep=True)
        del damaged.facets[stored.RESERVATION_ASSIGNMENT_FACET]["rule"]
        stored.stamp_semantic_identity(damaged)
        raw_write_node(archive.write_root, damaged)
    successor = assignment_node(assignment_facet(
        groups=[{"units": [{"start": "open", "end": "2026-01-01T00:00:00Z"}], "role": "open"}],
        inputs={"roster.yaml": digest("next")}, predecessor=root.id), actor="fixture")
    raw_write_node(cfg.write_root, successor)
    with research_rig(cfg, RESERVATION_NAMES) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("record", {"address": successor.id})
    refusal = caught.value.refusal
    if predecessor == "divergent":
        assert refusal.code == "invalid-input" and "copies differ" in refusal.message
        assert all(corpus_id_at(target.write_root) in refusal.message for target in (cfg, archive))
    else:
        assert refusal.code == "kernel-refused"
        assert refusal.data == {"kind": {"missing": "RefError", "malformed": "MalformedRecord"}[predecessor]}


def test_an_absent_exposure_or_reservation_address_is_an_ordinary_miss(certified_work):
    with research_rig(build_two_corpus_world(certified_work), RESERVATION_NAMES) as (d, _):
        for kind in ("exposure-event", "reservation-assignment"):
            refused(d, {"address": f"{kind}:" + "0" * 64})
