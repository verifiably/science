from dataclasses import replace

import pytest

from science.commands.belief import handle
from science.config import ReadContext
from science.report import KeyVals
from helpers.commons import a_identity
from helpers.world import build_belief_world


def test_belief_renders_no_belief_with_its_reason_before_assessment(certified_work):
    report = handle(ReadContext.open(build_belief_world(certified_work)), proposition="proposition:p1")
    kv = next(b for b in report if isinstance(b, KeyVals))
    pairs = dict(kv.pairs)
    assert pairs["kind"] == "NoBelief"
    assert pairs["reason"] == "no-eligible-assessment"


def test_belief_refuses_an_unknown_proposition(certified_work):
    from science.refusal import Refused
    with pytest.raises(Refused):
        handle(ReadContext.open(build_belief_world(certified_work)), proposition="proposition:nope")


def test_belief_performs_exactly_its_declared_reads():
    from science.loader import production_tree
    decl = next(d for d in production_tree() if d.name == "belief")
    assert set(decl.reads) == {"corpus-stored", "holdings", "epoch", "registry"}


def _belief(cfg, proposition):
    report = handle(ReadContext.open(cfg), proposition=proposition)
    blocks = {block.title: dict(block.pairs) for block in report if isinstance(block, KeyVals)}
    return blocks["answer"], blocks["acceptance"]


def test_belief_with_empty_accept_excludes_a_and_says_so(reopened):
    ids = a_identity(reopened.a)
    answer, acceptance = _belief(reopened.b, ids["proposition"])
    assert (answer["kind"], answer["reason"]) == ("NoBelief", "no-eligible-assessment")
    assert acceptance["policy"] == "science.accept.v1"
    assert acceptance["verifiers"] == reopened.b.world.world_id
    assert acceptance[f"pin {ids['corpus_id']}"] == (
        f"world {ids['world']}; source provider:https://remote.test/a; origin-confirmed; mounted")
    assert acceptance[f"excluded {ids['assessment']} ({ids['corpus_id']})"] == f"corpus {ids['corpus_id']}; world {ids['world']}"
    assert ReadContext.open(reopened.b).gather_inputs(ids["proposition"]).assessments == ()


def test_belief_with_accept_a_includes_a(reopened):
    """A's assessment is gathered and nothing is excluded. The answer stays `no-eligible-assessment`: A's
    assessment has no verification, so admission finds nothing eligible whatever the policy."""
    ids = a_identity(reopened.a)
    cfg = replace(reopened.b, accept=(ids["world"],))
    _, acceptance = _belief(cfg, ids["proposition"])
    assert acceptance["verifiers"] == ", ".join(sorted({reopened.b.world.world_id, ids["world"]}))
    assert acceptance["excluded"] == "none"
    assert not any(key.startswith("excluded ") for key in acceptance)
    (assessment,) = ReadContext.open(cfg).gather_inputs(ids["proposition"]).assessments
    assert assessment.proposition == ids["proposition"]


def test_belief_without_read_mounts_states_the_policy_too(certified_work):
    _, acceptance = _belief(build_belief_world(certified_work), "proposition:p1")
    assert acceptance["policy"] == "science.accept.v1" and acceptance["excluded"] == "none"
