"""The `sharing` write class: ledger sharing lines through kernel doors, and a pin
report rebuilt from them (commons 1a, Task 4)."""
import dataclasses
import json

import pytest

from helpers.commons import refused
from helpers.synthetic import PROBE_LOCATION, PROBE_WORLD, probe_evidence, synthetic_decls_and_handlers
from helpers.world import build_fixture_world, fixture_proposition_node
from science.cursor import MIN_OUTPUT_BUDGET
from science.dispatch import Dispatcher, HandlerContractViolation
from science.refusal import CODES, Refusal, Refused
from science.render import AuditViolation
from science.report import Text, pin_block, serialize_block

CID = "a" * 32


@pytest.fixture
def rig(certified_work):
    from science.config import ReadContext
    from science.session import open_session

    cfg = build_fixture_world(certified_work)
    decls, handlers = synthetic_decls_and_handlers()
    session = open_session(cfg)
    dispatcher = Dispatcher(decls, handlers, ReadContext.open(cfg), session=session)
    try:
        yield dispatcher, session, cfg
    finally:
        session.close()


def _lines(cfg, session, kind):
    from beliefs.session import ledger_path
    text = ledger_path(cfg.operations_root, session.session_id).read_text()
    return [line for line in map(json.loads, text.splitlines()) if line["line"] == kind]


def _close(cfg, session, iid):
    (close,) = [line for line in _lines(cfg, session, "invocation-close") if line["invocation"] == iid]
    return close["outcome"]


def test_required_for_sharing_is_the_kernel_sharing_requirement():
    from pathlib import Path

    from beliefs.permit import RequiredCapabilities
    from science.schema import Declaration, WriteClass

    share = Declaration("share", "p", WriteClass("sharing"), MIN_OUTPUT_BUDGET, (), (), Path("."))
    dispatcher = Dispatcher((share,), {"share": lambda ctx, writer: ()}, read_context=None, session=object())
    assert dispatcher._required(share) == RequiredCapabilities.sharing()


def test_a_sharing_invocation_reports_exactly_its_ledgered_lines(rig):
    d, session, cfg = rig
    out = d.invoke("share-probe", {"corpus_id": CID}, invocation_id="P" * 8)
    (line,) = session.invocation_sharing("P" * 8)
    assert line.transition == "bound" and line.corpus == CID and line.world == PROBE_WORLD
    assert out.text == serialize_block(pin_block(line))
    assert out.text.startswith(f"[pin] {CID} bound\n")
    assert _close(cfg, session, "P" * 8) == {"done": []}


@pytest.mark.parametrize("forge", [
    lambda block: (dataclasses.replace(block, verdict="forged"),),
    lambda block: (block, block),
    lambda block: (Text("not a pin"),),
])
def test_a_block_the_ledger_does_not_show_is_an_audit_violation(rig, forge):
    d, session, cfg = rig

    def forging(ctx, writer, *, corpus_id):
        line = writer.record_sharing(probe_evidence(corpus_id), transition="bound", verdict="validated")
        return forge(pin_block(line))

    d._handlers["share-probe"] = forging
    with pytest.raises(AuditViolation):
        d.invoke("share-probe", {"corpus_id": CID}, invocation_id="F" * 8)
    # The line is truth: the invocation closed done with it before the audit failed.
    assert _close(cfg, session, "F" * 8) == {"done": []}
    assert len(session.invocation_sharing("F" * 8)) == 1


def test_a_refusal_after_a_sharing_line_closes_refused_and_keeps_the_line(rig):
    from beliefs.session import open_ledger_reader

    d, session, cfg = rig

    def late(ctx, writer, *, corpus_id):
        writer.record_sharing(probe_evidence(corpus_id), transition="bound", verdict="validated")
        raise Refused(Refusal("world-mismatch", "the candidate claims another world"))

    d._handlers["share-probe"] = late
    refusal = refused(lambda: d.invoke("share-probe", {"corpus_id": CID}, invocation_id="r1"))
    assert refusal.code == "world-mismatch"
    reader = open_ledger_reader(cfg.operations_root, session.session_id)
    assert [line.transition for line in reader.invocation("r1").sharing] == ["bound"]
    assert _close(cfg, session, "r1")["refusal"]["code"] == "world-mismatch"
    d._handlers["share-probe"] = lambda *a, **k: pytest.fail("a replay must not run the handler")
    assert refused(lambda: d.invoke("share-probe", {"corpus_id": CID}, invocation_id="r1")).code == "world-mismatch"


def test_a_kernel_refusal_closes_refused(rig):
    d, session, cfg = rig

    def overreaching(ctx, writer, *, corpus_id):
        writer.add(fixture_proposition_node("sneaky"))  # a sharing writer holds no kinds

    d._handlers["share-probe"] = overreaching
    assert refused(lambda: d.invoke("share-probe", {"corpus_id": CID}, invocation_id="K" * 8)).code == "permit-exceeded"
    assert _close(cfg, session, "K" * 8)["refusal"]["code"] == "permit-exceeded"


@pytest.mark.parametrize("then_refuse", [False, True])
def test_an_act_in_a_sharing_invocation_is_a_handler_defect(rig, then_refuse):
    from beliefs.permit import RequiredCapabilities

    d, session, cfg = rig
    iid = "A" * 8

    def acting(ctx, writer, *, corpus_id):
        # The handler reaches past its writer for one that mints, inside its own invocation.
        session.scoped(RequiredCapabilities.for_kinds(("proposition",), {"proposition": "corpus-write"}), iid).add(
            fixture_proposition_node("stray"))
        if then_refuse:
            raise Refused(Refusal("adopt-conflict", "refused after acting"))
        return ()

    d._handlers["share-probe"] = acting
    with pytest.raises(HandlerContractViolation):
        d.invoke("share-probe", {"corpus_id": CID}, invocation_id=iid)
    # The act is truth: the invocation closed done with its pair.
    assert _close(cfg, session, iid)["done"] == [list(pair) for act in session.invocation_acts(iid)
                                                 for pair in act.record_ids]


def test_replay_of_a_sharing_invocation_re_renders_from_the_ledger(rig):
    d, session, cfg = rig
    first = d.invoke("share-probe", {"corpus_id": CID}, invocation_id="R" * 8)
    d._handlers["share-probe"] = lambda *a, **k: pytest.fail("a replay must not run the handler")
    again = d.invoke("share-probe", {"corpus_id": CID}, invocation_id="R" * 8)
    assert again.text == first.text
    assert len(_lines(cfg, session, "sharing")) == 1


def test_a_long_pin_report_continues_from_the_ledger_without_the_handler(rig):
    d, session, cfg = rig
    probe = dataclasses.replace(d._decls["share-probe"], output_budget=MIN_OUTPUT_BUDGET)
    d._decls["share-probe"] = probe

    def several(ctx, writer, *, corpus_id):
        return tuple(pin_block(writer.record_sharing(probe_evidence(corpus_id), transition=transition,
                                                     verdict="validated"))
                     for transition in ("bound", "mounted", "bound", "mounted"))

    d._handlers["share-probe"] = several
    pages = [d.invoke("share-probe", {"corpus_id": CID}, invocation_id="C" * 8).text]
    d._handlers["share-probe"] = lambda *a, **k: pytest.fail("a continuation must not run the handler")
    while "continue with cursor " in pages[-1]:
        cursor = pages[-1].rsplit("cursor ", 1)[1].strip()
        pages.append(d.invoke("share-probe", {}, cursor=cursor).text)
    assert len(pages) > 1
    body = "".join(page.split("\n… truncated at")[0] for page in pages)
    assert body == "".join(serialize_block(pin_block(line)) for line in session.invocation_sharing("C" * 8))


def test_without_a_session_refuses_permit_exceeded(certified_work):
    from science.config import ReadContext

    decls, handlers = synthetic_decls_and_handlers()
    d = Dispatcher(decls, handlers, ReadContext.open(build_fixture_world(certified_work)))
    refusal = refused(lambda: d.invoke("share-probe", {"corpus_id": CID}))
    assert refusal.code == "permit-exceeded" and refusal.message == "no writer session on this surface"


def test_new_refusal_codes_construct():
    for code in ("pin-unsourced", "world-mismatch", "adopt-conflict"):
        assert code in CODES and Refusal(code, "m").code == code


def test_sharing_replay_reads_the_lines_the_door_wrote(rig):
    from science.sharing import SharingRegistry, replay

    d, session, cfg = rig
    d.invoke("share-probe", {"corpus_id": CID}, invocation_id="B" * 8)
    registry = SharingRegistry(cfg.operations_root.parent / "sharing")
    (written,) = replay(registry, cfg.operations_root)
    assert written == session.invocation_sharing("B" * 8)[0]
    binding = registry.bindings()[PROBE_WORLD]
    assert binding.locations == (PROBE_LOCATION,) and binding.confirmed and binding.bound_since == written.at
    assert replay(registry, cfg.operations_root) == ()
