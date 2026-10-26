"""Spec §6.3: a surface refusal raised by a write handler closes the invocation."""
from pathlib import Path

import pytest

from science.cursor import MIN_OUTPUT_BUDGET
from science.dispatch import Dispatcher
from science.refusal import Refusal, Refused
from science.schema import Declaration, InputSpec, WriteClass
from helpers.world import build_fixture_world, fixture_proposition_node

REFUSING = Declaration("refusing", "fixture",
                       WriteClass("mints", ("proposition",), {"proposition": "corpus-write"}),
                       MIN_OUTPUT_BUDGET, (InputSpec("slug", "string", True, "d"),), (), Path("."))
HALF_ACTED = Declaration("half-acted", "fixture",
                         WriteClass("mints", ("proposition",), {"proposition": "corpus-write"}),
                         MIN_OUTPUT_BUDGET, (InputSpec("slug", "string", True, "d"),), (), Path("."))


def refusing_handler(ctx, writer, *, slug):
    raise Refused(Refusal("invalid-input", f"no plan row for {slug}"))


def half_acted_handler(ctx, writer, *, slug):
    writer.add(fixture_proposition_node(slug))
    raise Refused(Refusal("invalid-input", "refused after acting"))


@pytest.fixture
def rig(certified_work):
    from science.session import open_session
    from science.config import ReadContext
    cfg = build_fixture_world(certified_work)
    session = open_session(cfg)
    dispatcher = Dispatcher((REFUSING, HALF_ACTED),
                            {"refusing": refusing_handler, "half-acted": half_acted_handler},
                            ReadContext.open(cfg), session=session)
    try:
        yield dispatcher, session
    finally:
        session.close()


def test_refusal_before_any_act_closes_and_replays(rig):
    d, session = rig
    with pytest.raises(Refused) as first:
        d.invoke("refusing", {"slug": "x"}, invocation_id="R" * 8)
    assert first.value.refusal.code == "invalid-input"
    assert "no plan row" in first.value.refusal.message
    with pytest.raises(Refused) as again:
        d.invoke("refusing", {"slug": "x"}, invocation_id="R" * 8)
    assert again.value.refusal.code == "invalid-input"
    assert again.value.refusal.message == first.value.refusal.message
    assert session.invocation_acts("R" * 8) == ()


def test_refusal_after_an_act_closes_done_and_is_an_internal_error(rig):
    d, session = rig
    from science.dispatch import HandlerContractViolation
    with pytest.raises(HandlerContractViolation):
        d.invoke("half-acted", {"slug": "acted"}, invocation_id="H" * 8)
    assert len(session.invocation_acts("H" * 8)) == 1
    out = d.invoke("half-acted", {"slug": "acted"}, invocation_id="H" * 8)
    assert "proposition:acted" in out.text


@pytest.mark.parametrize("raised", [
    lambda: __import__("beliefs.errors", fromlist=["x"]).CitationContractMismatch(
        Path("/m"), "testing", "testing:aa", "testing:bb"),
    lambda: __import__("beliefs.errors", fromlist=["x"]).BuildContended("read mount /m: build-contended"),
], ids=["CitationContractMismatch", "BuildContended"])
def test_a_citation_error_from_the_writer_is_a_named_kernel_refusal(certified_work, raised):
    """Consumer spec decision 5: these are not WriteRefused, and would
    otherwise escape as internal errors."""
    from science.session import open_session
    from science.config import ReadContext
    error = raised()
    citing = Declaration("citing", "fixture",
                         WriteClass("mints", ("proposition",), {"proposition": "corpus-write"}),
                         MIN_OUTPUT_BUDGET, (), (), Path("."))

    def handler(ctx, writer):
        raise error

    cfg = build_fixture_world(certified_work)
    session = open_session(cfg)
    try:
        d = Dispatcher((citing,), {"citing": handler}, ReadContext.open(cfg), session=session)
        with pytest.raises(Refused) as caught:
            d.invoke("citing", {})
    finally:
        session.close()
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data["kind"] == type(error).__name__
    assert caught.value.refusal.message == str(error)


def test_a_duplicate_citation_from_the_writer_is_a_named_kernel_refusal(certified_work):
    from beliefs.errors import AddressMapConflict
    from beliefs.corpus import Finding
    from science.session import open_session
    from science.config import ReadContext
    error = AddressMapConflict(Finding("error", "duplicate-location", "proposition:twice", "c1, c2",
                                       "proposition:twice: held by corpora c1, c2"))
    citing = Declaration("citing", "fixture",
                         WriteClass("mints", ("proposition",), {"proposition": "corpus-write"}),
                         MIN_OUTPUT_BUDGET, (), (), Path("."))

    def handler(ctx, writer):
        raise error

    cfg = build_fixture_world(certified_work)
    session = open_session(cfg)
    try:
        d = Dispatcher((citing,), {"citing": handler}, ReadContext.open(cfg), session=session)
        with pytest.raises(Refused) as caught:
            d.invoke("citing", {})
    finally:
        session.close()
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data["kind"] == "AddressMapConflict"


@pytest.mark.parametrize("tips", [("b" * 32, "a" * 32), ()], ids=["divergent", "unknown"])
def test_project_not_resolvable_carries_its_tips_in_the_refusal(certified_work, tips):
    """Coordination spec §4.3: a client reconciles a diverged project from the
    tips the kernel named; a project with none carries no `tips` key. A replay
    returns the same data from the closed invocation."""
    from beliefs.errors import ProjectNotResolvable
    from science.session import open_session
    from science.config import ReadContext
    minting = Declaration("minting", "fixture",
                          WriteClass("mints", ("proposition",), {"proposition": "corpus-write"}),
                          MIN_OUTPUT_BUDGET, (), (), Path("."))

    def handler(ctx, writer):
        raise ProjectNotResolvable("the selected project does not resolve", tips=tips)

    cfg = build_fixture_world(certified_work)
    session = open_session(cfg)
    try:
        d = Dispatcher((minting,), {"minting": handler}, ReadContext.open(cfg), session=session)
        refusals = []
        for _ in range(2):
            with pytest.raises(Refused) as caught:
                d.invoke("minting", {}, invocation_id="P" * 8)
            refusals.append(caught.value.refusal)
    finally:
        session.close()
    expected = {"kind": "ProjectNotResolvable", "tips": sorted(tips)} if tips else {"kind": "ProjectNotResolvable"}
    assert [(r.code, r.data) for r in refusals] == [("kernel-refused", expected)] * 2


def test_minting_under_a_diverged_selected_project_refuses_with_its_tips(certified_work, monkeypatch):
    """The same refusal on the real path: the kernel's mint resolves the
    selected project and finds it divergent. Two tips cannot arise in one root
    (coordination §4.3), so the resolver is stubbed to report them for the
    project, as test_cmd_projects.py's `_diverge` does."""
    from beliefs.coordination import CoordinationRefused
    from beliefs.corpus import CoordinationResolver
    from helpers.world import QUERY, coordination_rig, mint_project

    tips = ("b" * 32, "a" * 32)
    with coordination_rig(certified_work, ("project", "question")) as (d, _):
        health = mint_project(d, "health")
        d._selection = health
        resolve = CoordinationResolver.resolve
        monkeypatch.setattr(CoordinationResolver, "resolve", lambda self, address: (
            CoordinationRefused("divergent-view", tips) if address == health else resolve(self, address)))
        with pytest.raises(Refused) as caught:
            d.invoke("question", {"name": "q", "query": QUERY})
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data == {"kind": "ProjectNotResolvable", "tips": sorted(tips)}
