"""Attended source attestations keep both endpoints and invocation evidence intact."""
import json
from dataclasses import replace

import pytest
from beliefs import stored
from beliefs.permit import WritePermit
from beliefs.root import open_world
from beliefs.session import open_run_session
from helpers.research import add_shared_source, add_source, correct_source, research_rig
from helpers.snapshot import snapshot
from helpers.world import FIXTURE_AUTHORITY, build_two_corpus_world
from nodes.core.corpus import Corpus
from science.config import ReadContext, corpus_id_at
from science.dispatch import Dispatcher
from science.loader import production_tree, resolve_handlers
from science.refusal import Refused

COMMAND = "source-coreference"


def _build_pair(work):
    cfg = build_two_corpus_world(work)
    left = add_shared_source(cfg, "Publisher record", doi="10.1000/example")
    right = add_source(cfg, "corpus", "Index record", pmid="123")
    return cfg, left.id, right.id


@pytest.fixture
def local_pair(certified_worker_work):
    saved = snapshot(certified_worker_work, "source-coreference-local", _build_pair)
    saved.restore()
    return saved.value


def _inputs(left, right, *, stance="same", grounds="Both records name the published version."):
    return dict(left=left, right=right, stance=stance, grounds=grounds)


def _events(ctx):
    return [node for node in ctx.write_view().iter_stored() if node.kind == "coreference-attestation"]


def test_mints_one_local_attestation_with_equal_replica_and_no_epoch(local_pair):
    cfg, left, right = local_pair
    with research_rig(cfg, (COMMAND,)) as (dispatch, ctx):
        assert dispatch.selection is None
        original = [ctx.write_view().get(ref) for ref in (left, right)]
        args = _inputs(right, left)
        first = dispatch.invoke(COMMAND, args, invocation_id="same-version")
        (event,) = _events(ctx)
        assert event.id in first.text and event.uid in first.text
        value = stored.coreference_attestation_value(event)
        assert value.endpoints == tuple(sorted((left, right)))
        assert value.stance == 1
        assert value.actor == dispatch._session.actor
        assert value.grounds == args["grounds"]
        assert value.event_token == "same-version"
        assert not event.relations
        assert [ctx.write_view().get(ref) for ref in (left, right)] == original
        (act,) = dispatch._session.invocation_acts("same-version")
        assert [address for _, address in act.record_ids] == [event.id]
        assert dispatch.invoke(COMMAND, args, invocation_id="same-version") == first
        assert [node.id for node in _events(ctx)] == [event.id]

        dispatch.invoke(COMMAND, args, invocation_id="new-event")
        dispatch.invoke(COMMAND, _inputs(left, right, stance="distinct", grounds="Different issue."),
                        invocation_id="counter")
        values = {value.event_token: value for value in map(stored.coreference_attestation_value, _events(ctx))}
        assert {key: value.stance for key, value in values.items()} == {
            "same-version": 1, "new-event": 1, "counter": -1,
        }
        assert values["counter"].grounds == "Different issue."


@pytest.mark.parametrize(("case", "field", "reason"), [
    ("unresolved", "left", "unresolved"),
    ("wrong-kind", "right", "wrong-kind"),
    ("redirect", "right", "redirect"),
    ("outside-session", "left", "outside-session"),
    ("self-pair", "right", "self-pair"),
    ("blank", "grounds", "invalid-text"),
    ("non-nfc", "grounds", "invalid-text"),
    ("surrogate", "grounds", "invalid-text"),
])
def test_input_refusal_closes_without_minting_and_replays(local_pair, case, field, reason):
    cfg, left, right = local_pair
    args = _inputs(left, right)
    if case == "unresolved":
        args["left"] = "source:missing"
        args["right"] = "proposition:archived"
    elif case == "wrong-kind":
        args["right"] = "proposition:archived"
    elif case == "redirect":
        corrected = correct_source(cfg, right, pmid="456")
    elif case == "outside-session":
        args["left"] = add_source(cfg, "archive", "Read mount only", pmid="456").id
        cfg = replace(cfg, coordination=None)
    elif case == "self-pair":
        args["right"] = left
    else:
        args["grounds"] = {"blank": " \t", "non-nfc": "cafe\u0301", "surrogate": "\ud800"}[case]

    with research_rig(cfg, (COMMAND,)) as (dispatch, ctx):
        with pytest.raises(Refused) as first:
            dispatch.invoke(COMMAND, args, invocation_id="preflight")
        refusal = first.value.refusal
        assert refusal.code == "invalid-input"
        assert refusal.data["field"] == field and refusal.data["reason"] == reason
        if field != "grounds":
            assert refusal.data["address"] == args[field]
        if case == "redirect":
            assert refusal.data["current_address"] == corrected.id
        assert dispatch._session.invocation_acts("preflight") == ()
        assert _events(ctx) == []
        with pytest.raises(Refused) as replay:
            dispatch.invoke(COMMAND, args, invocation_id="preflight")
        assert replay.value.refusal == refusal
        ledger = cfg.operations_root / "sessions" / dispatch._session.session_id / "ledger.v1"
        lines = [json.loads(line) for line in ledger.read_text().splitlines()]
        lines = [line for line in lines if line.get("invocation") == "preflight"]
        assert [line["line"] for line in lines] == ["invocation-open", "invocation-close"]
        assert lines[-1]["outcome"] == {"refusal": {
            "code": refusal.code, "message": refusal.message, "data": refusal.data,
        }}


def test_permit_denial_rechecks_capability_before_claiming(local_pair, monkeypatch):
    cfg, left, right = local_pair
    decls = tuple(decl for decl in production_tree() if decl.name == COMMAND)
    session = open_run_session(cfg.world, cfg.operations_root, write_root=cfg.write_root,
                               profile=cfg.profile, ceiling=WritePermit(frozenset(), frozenset()))
    ctx = ReadContext.open(cfg)
    dispatch = Dispatcher(decls, resolve_handlers(decls), ctx, session=session)
    original = session.scoped
    checks = []

    def scoped(required, invocation_id):
        checks.append(invocation_id)
        return original(required, invocation_id)

    monkeypatch.setattr(session, "scoped", scoped)
    try:
        for _ in range(2):
            with pytest.raises(Refused) as caught:
                dispatch.invoke(COMMAND, _inputs(left, right), invocation_id="no-permit")
            assert caught.value.refusal.code == "permit-exceeded"
        assert checks == ["no-permit", "no-permit"]
        assert _events(ctx) == []
    finally:
        session.close()
    ledger = cfg.operations_root / "sessions" / session.session_id / "ledger.v1"
    assert [json.loads(line)["line"] for line in ledger.read_text().splitlines()] == [
        "session-open", "session-close",
    ]


@pytest.mark.parametrize("case", ["differing-copy", "retired-source", "retired-root"])
def test_holder_faults_refuse_before_act(local_pair, case):
    cfg, left, right = local_pair
    archive = cfg.write_root.parent / "archive"
    if case == "differing-copy":
        Corpus(archive).add(stored.source_node(title="Different title", identifiers={"pmid": "123"}))
    elif case == "retired-source":
        right = add_source(cfg, "archive", "Retiring source", pmid="456").id

    with research_rig(cfg, (COMMAND,)) as (dispatch, ctx):
        if case != "differing-copy":
            root = cfg.write_root if case == "retired-root" else archive
            open_world(cfg.world, authority=FIXTURE_AUTHORITY).retire(corpus_id_at(root))
        with pytest.raises(Refused) as caught:
            dispatch.invoke(COMMAND, _inputs(left, right), invocation_id="holders")
        refusal = caught.value.refusal
        if case == "differing-copy":
            assert refusal.code == "invalid-input" and "copies differ" in refusal.message
        elif case == "retired-source":
            assert refusal.data == {"field": "right", "address": right, "reason": "unresolved"}
        else:
            assert refusal.code == "corpus-retired"
            assert refusal.data == {"corpus": corpus_id_at(cfg.write_root)}
        assert dispatch._session.invocation_acts("holders") == ()
        assert _events(ctx) == []
