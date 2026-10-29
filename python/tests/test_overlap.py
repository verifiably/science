"""Admission compares every key and uid against real corpus records."""

import pytest

from beliefs import stored
from beliefs.root import init_corpus_root, open_corpus
from helpers.world import FIXTURE_AUTHORITY, PINS, PROFILE
from science.overlap import Conflict, conflicts


@pytest.fixture
def two_corpora(certified_work):
    return writer_at(certified_work / "candidate"), writer_at(certified_work / "live")


def writer_at(root):
    init_corpus_root(root, authority=FIXTURE_AUTHORITY)
    writer = open_corpus(root, authority=FIXTURE_AUTHORITY, profile=PROFILE)
    writer.adopt_manifest(profile=PINS)
    return writer


def proposition(slug, **changes):
    return stored.proposition_node(slug, title=slug, claim={"operator": "affects"}).model_copy(update=changes)


def test_equal_copies_share_live_and_deprecated_addresses_without_conflict(two_corpora):
    candidate, live = two_corpora
    node = proposition("p", deprecated_ids=["proposition:old"])
    candidate.add(node)
    live.add(node)
    assert conflicts(candidate.read_view, [("live", live.read_view)]) is None


def test_differing_content_at_a_shared_live_address_is_content(two_corpora):
    candidate, live = two_corpora
    node = proposition("p")
    candidate.add(node)
    live.add(node.model_copy(update={"title": "changed"}))
    assert conflicts(candidate.read_view, [("live", live.read_view)]) == Conflict(
        "content", ("proposition:p",), "live",
    )


@pytest.mark.parametrize("candidate_deprecated", [False, True])
def test_a_live_address_meeting_another_records_deprecated_id_is_deprecated_key(two_corpora, candidate_deprecated):
    candidate, live = two_corpora
    canonical = proposition("old")
    redirected = proposition("new", deprecated_ids=["proposition:old"])
    candidate.add(redirected if candidate_deprecated else canonical)
    live.add(canonical if candidate_deprecated else redirected)
    assert conflicts(candidate.read_view, [("live", live.read_view)]) == Conflict(
        "deprecated-key", ("proposition:old",), "live",
    )


def test_two_differing_records_sharing_a_deprecated_id_is_deprecated_key(two_corpora):
    candidate, live = two_corpora
    candidate.add(proposition("new", deprecated_ids=["proposition:old"]))
    live.add(proposition("other", deprecated_ids=["proposition:old"]))
    assert conflicts(candidate.read_view, [("live", live.read_view)]) == Conflict(
        "deprecated-key", ("proposition:old",), "live",
    )


def test_a_uid_held_live_under_another_address_is_uid_corruption_before_any_key_rule(two_corpora):
    candidate, live = two_corpora
    original = proposition("old")
    live.add(original)
    candidate.add(proposition("new", uid=original.uid, deprecated_ids=[original.id]))
    assert conflicts(candidate.read_view, [("live", live.read_view)]) == Conflict(
        "uid-corruption", ("proposition:new", "proposition:old"), "live",
    )


def test_the_first_conflicting_live_corpus_is_named_with_all_its_addresses(two_corpora):
    candidate, live = two_corpora
    for slug in ("z", "a"):
        node = proposition(slug)
        candidate.add(node)
        live.add(node.model_copy(update={"title": "changed"}))
    assert conflicts(candidate.read_view, [
        ("equal", candidate.read_view), ("first", live.read_view), ("later", live.read_view),
    ]) == Conflict("content", ("proposition:a", "proposition:z"), "first")


def test_mixed_rules_choose_precedence_and_report_every_conflicting_address(two_corpora):
    candidate, live = two_corpora
    node = proposition("p", deprecated_ids=["proposition:former"])
    candidate.add(node)
    live.add(node.model_copy(update={"title": "changed"}))
    expected = ("proposition:former", "proposition:p")
    assert conflicts(candidate.read_view, [("live", live.read_view)]) == Conflict("content", expected, "live")

    original = proposition("old")
    live.add(original)
    candidate.add(proposition("new", uid=original.uid))
    assert conflicts(candidate.read_view, [("live", live.read_view)]) == Conflict(
        "uid-corruption", ("proposition:former", "proposition:new", "proposition:old", "proposition:p"), "live",
    )


def test_disjoint_records_and_empty_live_set_do_not_conflict(two_corpora):
    candidate, live = two_corpora
    candidate.add(proposition("p"))
    live.add(proposition("other"))
    assert conflicts(candidate.read_view, [("live", live.read_view)]) is None
    assert conflicts(candidate.read_view, []) is None


def test_an_earlier_key_conflict_precedes_a_later_uid_conflict(two_corpora, certified_work):
    candidate, live = two_corpora
    node = proposition("p")
    candidate.add(node)
    live.add(node.model_copy(update={"title": "changed"}))
    later = writer_at(certified_work / "later")
    original = proposition("old")
    later.add(original)
    candidate.add(proposition("new", uid=original.uid))
    assert conflicts(candidate.read_view, [
        ("first", live.read_view), ("later", later.read_view),
    ]) == Conflict("content", ("proposition:p",), "first")
