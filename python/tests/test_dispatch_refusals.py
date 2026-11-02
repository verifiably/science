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
KERNEL_REFUSED_AFTER_ACT = Declaration(
    "kernel-refused-after-act", "fixture",
    WriteClass("mints", ("proposition",), {"proposition": "corpus-write"}),
    MIN_OUTPUT_BUDGET, (InputSpec("slug", "string", True, "d"),), (), Path("."))


def refusing_handler(ctx, writer, *, slug):
    raise Refused(Refusal("invalid-input", f"no plan row for {slug}"))


def half_acted_handler(ctx, writer, *, slug):
    writer.add(fixture_proposition_node(slug))
    raise Refused(Refusal("invalid-input", "refused after acting"))


def kernel_refused_after_act_handler(ctx, writer, *, slug):
    """Two acts, the second refused by the kernel: the same proposition twice."""
    writer.add(fixture_proposition_node(slug))
    writer.add(fixture_proposition_node(slug))


@pytest.fixture
def rig(certified_work):
    from science.session import open_session
    from science.config import ReadContext
    cfg = build_fixture_world(certified_work)
    session = open_session(cfg)
    dispatcher = Dispatcher((REFUSING, HALF_ACTED, KERNEL_REFUSED_AFTER_ACT),
                            {"refusing": refusing_handler, "half-acted": half_acted_handler,
                             "kernel-refused-after-act": kernel_refused_after_act_handler},
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


def test_a_kernel_refusal_after_an_act_closes_done_and_is_an_internal_error(rig):
    """The kernel refusing a later act does not unmake the earlier one: the
    invocation closes done with the committed act, as a surface refusal after
    an act does, and a retry replays that act rather than a refusal."""
    d, session = rig
    from science.dispatch import HandlerContractViolation
    with pytest.raises(HandlerContractViolation, match="kernel-refused"):
        d.invoke("kernel-refused-after-act", {"slug": "twice"}, invocation_id="K" * 8)
    assert len(session.invocation_acts("K" * 8)) == 1
    out = d.invoke("kernel-refused-after-act", {"slug": "twice"}, invocation_id="K" * 8)
    assert "proposition:twice" in out.text


def _refusing_boundary_call(writer, scratch_base: Path):
    from beliefs.boundary import execute_production_run
    from beliefs.recipe import CONFINED_POLICY
    return execute_production_run(
        inputs=(),
        port=writer.operation_port(),
        boundary_policy=CONFINED_POLICY,
        parameters={},
        nondeterminism=None,  # type: ignore[arg-type] — refuses on missing code root before nondeterminism
        definition=None,  # type: ignore[arg-type]
        code_roots=(scratch_base / "missing-bundle",),
        held_inputs={},
        entrypoint="workflow/Snakefile",
        targets=(),
        declared_outputs=(),
        observer=writer.actor,
        started_at="2026-09-09T00:00:00Z",
        host_realization="linux-x86_64",
        scratch_base=scratch_base / "scratch",
    )


def test_a_boundary_refusal_recording_only_an_act_report_closes_refused_and_replays(certified_work):
    """A boundary operation (run, replay, publish) records its refusal as an
    act-report through the ledgered operation port before returning RunRefused
    or PublishRefused. That act-report is the refusal's own durable evidence,
    not a prior act: the invocation closes refused and replays the refusal."""
    from beliefs.session import KernelRefusalValue, reconcile_sessions
    from science.config import ReadContext
    from science.session import open_session

    boundary_refusing = Declaration(
        "boundary-refusing", "fixture",
        WriteClass("mints", ("run", "act-report"), {"run": "run", "act-report": "run"}),
        MIN_OUTPUT_BUDGET, (), (), Path("."))

    def handler(ctx, writer):
        outcome = _refusing_boundary_call(writer, certified_work)
        raise KernelRefusalValue(outcome)

    cfg = build_fixture_world(certified_work)
    session = open_session(cfg)
    try:
        d = Dispatcher((boundary_refusing,), {"boundary-refusing": handler},
                       ReadContext.open(cfg), session=session)
        with pytest.raises(Refused) as first:
            d.invoke("boundary-refusing", {}, invocation_id="B" * 8)
        assert first.value.refusal.code == "kernel-refused"
        assert first.value.refusal.data["kind"] == "RunRefused"
        acts = session.invocation_acts("B" * 8)
        assert len(acts) == 1
        assert all(rid.startswith("act-report:") for _, rid in acts[0].record_ids)
        with pytest.raises(Refused) as again:
            d.invoke("boundary-refusing", {}, invocation_id="B" * 8)
        assert again.value.refusal == first.value.refusal
    finally:
        session.close()
    assert reconcile_sessions(cfg.world, cfg.operations_root) == ()


def test_a_boundary_refusal_after_a_committed_act_closes_done_and_is_an_internal_error(certified_work):
    """When an earlier act already minted a record before a later boundary act
    refuses and records its act-report, the earlier act still committed: the
    invocation closes done and raises HandlerContractViolation."""
    from beliefs.session import KernelRefusalValue, reconcile_sessions
    from science.config import ReadContext
    from science.dispatch import HandlerContractViolation
    from science.session import open_session

    mixed = Declaration(
        "mixed", "fixture",
        WriteClass("mints", ("proposition", "run", "act-report"),
                   {"proposition": "corpus-write", "run": "run", "act-report": "run"}),
        MIN_OUTPUT_BUDGET, (InputSpec("slug", "string", True, "d"),), (), Path("."))

    def handler(ctx, writer, *, slug):
        writer.add(fixture_proposition_node(slug))
        outcome = _refusing_boundary_call(writer, certified_work)
        raise KernelRefusalValue(outcome)

    cfg = build_fixture_world(certified_work)
    session = open_session(cfg)
    try:
        d = Dispatcher((mixed,), {"mixed": handler}, ReadContext.open(cfg), session=session)
        with pytest.raises(HandlerContractViolation, match="kernel-refused"):
            d.invoke("mixed", {"slug": "kept"}, invocation_id="M" * 8)
        assert len(session.invocation_acts("M" * 8)) == 2
        out = d.invoke("mixed", {"slug": "kept"}, invocation_id="M" * 8)
        assert "proposition:kept" in out.text
    finally:
        session.close()
    assert reconcile_sessions(cfg.world, cfg.operations_root) == ()


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


def _normalization_cases():
    from beliefs.errors import PermitExceeded, PermitFact, PermitSummary, ProjectNotResolvable
    from beliefs.session import KernelRefusalValue
    class RunRefused:
        reason = "closure-unsupported"
        detail = "missing input"
    return [
        (PermissionError("denied"), "kernel-refused", "denied", {"kind": "PermissionError"}),
        (ProjectNotResolvable("diverged", tips=("b" * 32, "a" * 32)), "kernel-refused", "diverged",
         {"kind": "ProjectNotResolvable", "tips": ["a" * 32, "b" * 32]}),
        (KernelRefusalValue(RunRefused()), "kernel-refused", "closure-unsupported: missing input",
         {"kind": "RunRefused", "reason": "closure-unsupported", "detail": "missing input"}),
        (PermitExceeded(PermitFact("family", "run"), PermitSummary((), (), False)),
         "permit-exceeded", "permit exceeded: family run is not permitted",
         {"requirement": "PermitFact(dimension='family', name='run')",
          "capability": "PermitSummary(kinds=(), act_families=(), ungoverned=False)"}),
    ]


@pytest.mark.parametrize("error,code,message,data", _normalization_cases())
def test_kernel_refusal_preserves_existing_shapes(error, code, message, data):
    from science.refusal import kernel_refusal
    assert kernel_refusal(error) == Refusal(code, message, data)


@pytest.mark.parametrize("error,code,message,data", _normalization_cases())
def test_kernel_refusal_adds_root_context(error, code, message, data):
    from science.refusal import kernel_refusal
    refusal = kernel_refusal(error, root="/store")
    assert refusal.code == code
    assert refusal.message == f"/store: {message}"
    assert refusal.data == {**data, "root": "/store"}
