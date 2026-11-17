from helpers.analysis import spec_inputs
from science.commands.next import classify, handle
from science.config import ReadContext
from science.report import KeyVals
from helpers.world import (build_belief_world, hold_fixture_dataset, open_rig)


def test_a_proposition_no_spec_targets_is_not_ready_however_much_is_held(certified_work):
    cfg = build_belief_world(certified_work)
    hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    assert classify(ReadContext.open(cfg), "proposition:p1") == "not-ready"


def test_a_spec_whose_inputs_are_held_makes_it_ready(certified_work):
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    with open_rig(cfg, ("spec",)) as (d, ctx):
        d.invoke("spec", spec_inputs(cfg, target="proposition:p1", dataset=ref))
        assert classify(ctx, "proposition:p1") == "ready"


def test_a_later_absent_observation_moves_it_back_to_not_ready(certified_work):
    from helpers.world import unhold_fixture_dataset
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    with open_rig(cfg, ("spec",)) as (d, _):
        d.invoke("spec", spec_inputs(cfg, target="proposition:p1", dataset=ref))
    assert classify(ReadContext.open(cfg), "proposition:p1") == "ready"
    unhold_fixture_dataset(cfg, ref)
    assert classify(ReadContext.open(cfg), "proposition:p1") == "not-ready"


def test_next_renders_rows_in_class_order(certified_work):
    cfg = build_belief_world(certified_work)
    report = handle(ReadContext.open(cfg), limit=None)
    kv = next(b for b in report if isinstance(b, KeyVals))
    assert kv.pairs[0][0] == "proposition:p1"
    assert kv.pairs[0][1].startswith("not-ready:")


def test_next_keeps_other_rows_when_one_proposition_has_multiple_keys(certified_work):
    from decimal import Decimal
    from helpers.analysis import assess_target
    cfg = build_belief_world(certified_work)
    _, first = assess_target(cfg, certified_work)
    _, second = assess_target(cfg, certified_work, reference=Decimal("0"))
    with open_rig(cfg, ("claim",)) as (d, _):
        d.invoke("claim", {"slug": "p2", "subject": "concept:remission",
                          "predicate": "affects", "object": "protein:PHF19", "layer": "causal", "polarity": "positive"})
    data = hold_fixture_dataset(cfg, "data.txt", b"ready\n", "expression")
    with open_rig(cfg, ("spec",)) as (d, _):
        d.invoke("spec", spec_inputs(cfg, target="proposition:p2", dataset=data))
    ctx = ReadContext.open(cfg)
    assert classify(ctx, "proposition:p1") == "assessed-unevaluated"
    rows = dict(next(b for b in handle(ctx) if isinstance(b, KeyVals)).pairs)
    assert rows["proposition:p2"].startswith("ready:")
    assert rows["proposition:p1"].startswith("assessed-unevaluated (multiple-assessed-propositions)")
    assert rows["proposition:p1"].index(min(first.key(), second.key())) < rows["proposition:p1"].index(max(first.key(), second.key()))
    assert "science belief" in rows["proposition:p1"] and "--key" in rows["proposition:p1"]


def test_next_keeps_other_rows_at_missing_and_stale_epochs(certified_work):
    from beliefs import stored
    from beliefs.root import open_corpus
    from helpers.world import FIXTURE_AUTHORITY, build_shared_world_with_evidence
    from science.world_belief import publish_session_epoch
    cfg, _ = build_shared_world_with_evidence(certified_work)
    def rows():
        return dict(next(b for b in handle(ReadContext.open(cfg)) if isinstance(b, KeyVals)).pairs)
    before = rows()
    assert before["proposition:shared"].startswith("assessed-unevaluated (no-epoch)")
    assert "proposition:fresh" in before
    publish_session_epoch(cfg)
    assert classify(ReadContext.open(cfg), "proposition:shared") == "assessed-not-admitted"
    open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile).add(
        stored.proposition_node("later", title="later", claim={"operator": "affects"}))
    after = rows()
    assert after["proposition:shared"].startswith("assessed-unevaluated (epoch-stale)")
    assert "proposition:fresh" in after and "proposition:later" in after
