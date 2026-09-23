import pytest

from science.commands.belief import handle
from science.config import ReadContext
from science.report import KeyVals
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
