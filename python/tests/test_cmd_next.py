from science.commands.next import classify, handle
from science.config import ReadContext
from science.report import KeyVals
from helpers.world import SPEC_FIELDS, build_belief_world, hold_fixture_dataset, open_rig


def test_a_proposition_no_spec_targets_is_not_ready_however_much_is_held(certified_work):
    cfg = build_belief_world(certified_work)
    hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    assert classify(ReadContext.open(cfg), "proposition:p1") == "not-ready"


def test_a_spec_whose_inputs_are_held_makes_it_ready(certified_work):
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    with open_rig(cfg, ("spec",)) as (d, ctx):
        d.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=ref))
        assert classify(ctx, "proposition:p1") == "ready"


def test_a_later_absent_observation_moves_it_back_to_not_ready(certified_work):
    from helpers.world import unhold_fixture_dataset
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    with open_rig(cfg, ("spec",)) as (d, _):
        d.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=ref))
    assert classify(ReadContext.open(cfg), "proposition:p1") == "ready"
    unhold_fixture_dataset(cfg, ref)
    assert classify(ReadContext.open(cfg), "proposition:p1") == "not-ready"


def test_next_renders_rows_in_class_order(certified_work):
    cfg = build_belief_world(certified_work)
    report = handle(ReadContext.open(cfg), limit=None)
    kv = next(b for b in report if isinstance(b, KeyVals))
    assert kv.pairs[0][0] == "proposition:p1"
    assert kv.pairs[0][1].startswith("not-ready:")
