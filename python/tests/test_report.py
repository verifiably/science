import pytest
from types import SimpleNamespace

from science.report import (
    Finding, Heading, KeyVals, RecordBlock, Text, record_block, serialize_block,
)


def test_record_block_is_derived_from_the_record():
    node = SimpleNamespace(uid="u" * 32, id="proposition:x", kind="proposition", title="claim")
    block = record_block(node)
    assert block == RecordBlock("u" * 32, "proposition:x", "proposition", "claim")


def test_serialization_is_deterministic_and_distinct():
    blocks = (
        Heading("World"),
        KeyVals("epoch", (("packaging", "abc"), ("coverage", "2"))),
        RecordBlock("u" * 32, "proposition:x", "proposition", "claim"),
        Finding("chain head moved"),
        Text("plain"),
    )
    outs = [serialize_block(b) for b in blocks]
    assert outs == [serialize_block(b) for b in blocks]
    assert all(o.endswith("\n") for o in outs)
    assert len(set(outs)) == len(outs)
    assert "## World" in outs[0]
    assert "packaging: abc" in outs[1]
    assert "[proposition] proposition:x" in outs[2] and "u" * 32 in outs[2]
    assert outs[3].startswith("! ")


def test_a_selection_block_serializes_the_selection_or_none():
    from science.report import SelectionBlock

    address = "coord:" + "a" * 32 + "@" + "b" * 32
    assert serialize_block(SelectionBlock(address, "health")) == f"selected: {address}\nname: health\n"
    assert serialize_block(SelectionBlock(None, None)) == "selected: none\n"


def _sharing_line(transition):
    from beliefs.session.ledger import SharingLine

    return SharingLine("i1", "a" * 32, "5" * 32, "6" * 64, "7" * 32, f"coord:{'1' * 32}@{'2' * 32}",
                       "provider:https://remote.test/a", "https://remote.test/a", "validated", transition,
                       "2026-10-23T10:00:00Z")


def test_a_pin_block_is_derived_from_its_ledger_line():
    from science.report import PinBlock, pin_block

    assert pin_block(_sharing_line("bound")) == PinBlock(
        "a" * 32, "5" * 32, "6" * 64, "7" * 32, f"coord:{'1' * 32}@{'2' * 32}",
        "provider:https://remote.test/a", "https://remote.test/a", "validated", "bound",
    )


def test_a_pin_block_serializes_its_facts_and_a_mount_says_when_it_takes_effect():
    from science.report import pin_block

    bound = serialize_block(pin_block(_sharing_line("bound")))
    assert bound == (
        f"[pin] {'a' * 32} bound\n"
        f"marker: {'5' * 32}\n"
        f"artifact: {'6' * 64}\n"
        f"world: {'7' * 32}\n"
        f"view: coord:{'1' * 32}@{'2' * 32}\n"
        "source: provider:https://remote.test/a\n"
        "location: https://remote.test/a\n"
        "verdict: validated\n"
    )
    mounted = serialize_block(pin_block(_sharing_line("mounted")))
    assert mounted.startswith(f"[pin] {'a' * 32} mounted\n")
    assert mounted.endswith("verdict: validated\ntakes effect at the next session open\n")


# --- holdings detail lines  -------------------------------------

STORE = "c" * 32
LOCATION = f"store:{STORE}:{'d' * 64}/x.txt"


def _observation_node(outcome):
    from beliefs import stored
    from beliefs.holdings.records import StoreLocator, holdings_observation
    return stored.holdings_observation_node(holdings_observation(
        location=StoreLocator(STORE, f"{'d' * 64}/x.txt"), outcome=outcome, observer="fixture",
        instrument="fixture/report.v1", event_token="e" * 32, observed_at="2026-10-31T00:00:00Z"))


def _report_node(operation, entries):
    """A kernel act-report node; tests reach the boundary's minting directly."""
    from beliefs import stored
    from beliefs.report import _mint_report
    return stored.act_report_node(_mint_report(
        operation=operation, event_token="f" * 32, actor="fixture", observer="fixture",
        instrument="fixture/report.v1", opened_at="2026-10-31T00:00:00Z",
        closed_at="2026-10-31T00:00:01Z", entries=entries))


def test_observation_block_states_the_outcome():
    from beliefs.holdings.records import Absent, Found
    digest = "sha256:" + "d" * 64
    assert record_block(_observation_node(Found(digest))).detail == (f"found {digest} at {LOCATION}",)
    assert record_block(_observation_node(Absent())).detail == (f"absent at {LOCATION}",)


def test_recheck_report_block_lists_a_published_entry():
    from beliefs.report import LocatorEntry, PublishedObservation
    ref = "holdings-observation:" + "a" * 64
    node = _report_node("re-check", (LocatorEntry(LOCATION, PublishedObservation(ref)),))
    assert record_block(node).detail == (f"{LOCATION}: observed {ref}",)


@pytest.mark.parametrize("outcome_type", ["retrieval-failed", "byte-locator-untested"])
def test_recheck_report_block_lists_an_inconclusive_entry(outcome_type):
    from beliefs.report import ByteLocatorUntested, LocatorEntry, RetrievalFailed
    value = {"retrieval-failed": RetrievalFailed, "byte-locator-untested": ByteLocatorUntested}[outcome_type]
    node = _report_node("re-check", (LocatorEntry(LOCATION, value("io-error")),))
    assert record_block(node).detail == (f"{LOCATION}: {outcome_type} io-error",)


def test_other_act_reports_carry_no_detail():
    from beliefs.report import RunAttemptEntry, RunRefusal
    node = _report_node("run-attempt", (RunAttemptEntry("run:" + "a" * 64, RunRefusal("inputs")),))
    block = record_block(node)
    assert block.detail == ()
    assert serialize_block(block) == f"[act-report] {node.id} uid={node.uid}\n{node.title}\n"


def test_four_argument_record_block_still_constructs():
    assert RecordBlock("u", "i", "k", "t").detail == ()


def test_detail_lines_follow_the_title():
    block = RecordBlock("u", "i", "k", "t", ("one", "two"))
    assert serialize_block(block) == "[k] i uid=u\nt\none\ntwo\n"


def test_assessment_verification_and_run_record_blocks_carry_their_minted_details(certified_work):
    from beliefs import stored
    from beliefs.errors import MalformedRecord
    from beliefs.runrecord import decode_run_closure
    from helpers.analysis import spec_inputs
    from helpers.world import OBSERVED, build_belief_world, fixture_bundle, hold_fixture_dataset, mint_fixture_run, open_rig

    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression", **OBSERVED)
    bundle = fixture_bundle(certified_work, "inconclusive")
    code, entrypoint, _ = bundle
    with open_rig(cfg, ("spec",)) as (d, _):
        spec_ref = next(
            t for t in d.invoke("spec", spec_inputs(cfg, target="proposition:p1", dataset=ref)).text.split()
            if t.startswith("analysis-spec:")
        )
    run_ref = mint_fixture_run(cfg, spec_ref, ref, bundle)
    with open_rig(cfg, ("assess", "verify")) as (d, ctx):
        assess_out = d.invoke("assess", {"run": run_ref})
        assessment_ref = next(t for t in assess_out.text.split() if t.startswith("assessment:"))
        verify_out = d.invoke("verify", {"assessment": assessment_ref, "code": str(code), "entrypoint": entrypoint})
        verification_ref = next(t for t in verify_out.text.split() if t.startswith("verification:"))
        view = ctx.write_view()

        run_node = view.get(run_ref)
        closure = decode_run_closure(run_node)
        expected_outputs = tuple(f"output: {name} {digest}" for name, digest in closure.result.outputs)
        assert record_block(run_node).detail == expected_outputs
        assert expected_outputs

        assessment_node = view.get(assessment_ref)
        assert record_block(assessment_node).detail == ("outcome: inconclusive",)
        assert "outcome: inconclusive\n" in assess_out.text

        verification_node = view.get(verification_ref)
        facet = verification_node.facets["verification"]
        assert record_block(verification_node).detail == (
            f"scope: {facet['scope']}",
            f"verdict: {facet['verdict']}",
        )
        assert f"scope: {facet['scope']}\n" in verify_out.text
        assert f"verdict: {facet['verdict']}\n" in verify_out.text

        # Non-closure run node carries no manifest detail.
        bare_run = SimpleNamespace(uid="u" * 32, id="run:bare", kind="run", title="bare", facets={})
        assert record_block(bare_run).detail == ()

        # Malformed assessment node fails early.
        bad_assessment = SimpleNamespace(
            uid="u" * 32, id="assessment:bad", kind="assessment", title="bad", facets={stored.ASSESSMENT_FACET: {}}
        )
        with pytest.raises(MalformedRecord):
            record_block(bad_assessment)
