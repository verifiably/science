"""Attended source attestations keep both endpoints and invocation evidence intact."""
import json
from contextlib import contextmanager
from dataclasses import replace

import pytest
from beliefs import errors, stored
from beliefs.consulted import CorpusPins
from beliefs.permit import WritePermit
from beliefs.root import init_corpus_root, open_corpus, open_world
from beliefs.session import ScopedWriter, open_run_session
from beliefs.world import Fresh
from beliefs.world.view import WorldReadView
from helpers.research import add_shared_source, add_source, correct_source, raw_write_node, research_rig
from helpers.snapshot import snapshot
from helpers.world import FIXTURE_AUTHORITY, build_two_corpus_world
from nodes.core.corpus import Corpus
from nodes.core.errors import RefError
from science.config import ReadContext, corpus_id_at
from science.dispatch import Dispatcher
from science.loader import production_tree, resolve_handlers
from science.refusal import Refusal, Refused, envelope
from science import world_belief
from test_serve import _ask, _running

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


@contextmanager
def _attended(cfg, short_tmp):
    sock = short_tmp / "coreference.sock"
    server = _running(cfg, sock)
    try:
        yield sock
    finally:
        server.shutdown()
        server.server_close()


def _wire_refusal(sock, args, iid):
    reply = _ask(sock, {"command": COMMAND, "inputs": args, "invocation_id": iid})
    assert set(reply) == {"ok", "invocation_id", "refusal"}
    assert reply["ok"] is False and reply["invocation_id"] == iid
    return Refusal(**reply["refusal"])


def _check_wire_replay(cfg, sock, args, iid, refusal):
    assert _wire_refusal(sock, args, iid) == refusal
    assert _events(ReadContext.open(cfg)) == []
    (ledger,) = (cfg.operations_root / "sessions").glob("*/ledger.v1")
    lines = [json.loads(line) for line in ledger.read_text().splitlines()]
    attempt = [line for line in lines if line.get("invocation") == iid]
    assert [line["line"] for line in attempt] == ["invocation-open", "invocation-close"]
    assert attempt[-1]["outcome"] == {"refusal": envelope(refusal)}


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
    ("surrogate-left", "left", "unresolved"),
    ("surrogate-right", "right", "unresolved"),
])
def test_input_refusal_closes_without_minting_and_replays(local_pair, short_tmp, case, field, reason):
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
    elif case.startswith("surrogate-"):
        args[field] = "source:\ud800"
    else:
        args["grounds"] = {"blank": " \t", "non-nfc": "cafe\u0301", "surrogate": "\ud800"}[case]

    with _attended(cfg, short_tmp) as sock:
        refusal = _wire_refusal(sock, args, "preflight")
        assert refusal.code == "invalid-input"
        assert refusal.data["field"] == field and refusal.data["reason"] == reason
        if field != "grounds":
            assert refusal.data["address"] == args[field].encode("utf-8", "backslashreplace").decode("utf-8")
        if case == "redirect":
            assert refusal.data["current_address"] == corrected.id
        _check_wire_replay(cfg, sock, args, "preflight", refusal)


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
def test_holder_faults_refuse_before_act(local_pair, short_tmp, case):
    cfg, left, right = local_pair
    archive = cfg.write_root.parent / "archive"
    if case == "differing-copy":
        Corpus(archive).add(stored.source_node(title="Different title", identifiers={"pmid": "123"}))
    elif case == "retired-source":
        right = add_source(cfg, "archive", "Retiring source", pmid="456").id

    with _attended(cfg, short_tmp) as sock:
        if case != "differing-copy":
            root = cfg.write_root if case == "retired-root" else archive
            open_world(cfg.world, authority=FIXTURE_AUTHORITY).retire(corpus_id_at(root))
        args = _inputs(left, right)
        refusal = _wire_refusal(sock, args, "holders")
        if case == "differing-copy":
            assert refusal.code == "invalid-input" and "copies differ" in refusal.message
            raw_write_node(archive, ReadContext.open(cfg).write_view().get(right))
        elif case == "retired-source":
            assert refusal.data == {"field": "right", "address": right, "reason": "unresolved"}
        else:
            assert refusal.code == "corpus-retired"
            assert refusal.data == {"corpus": corpus_id_at(cfg.write_root)}
        _check_wire_replay(cfg, sock, args, "holders", refusal)


def _build_mounted_pair(work):
    cfg = build_two_corpus_world(work)
    left = add_source(cfg, "corpus", "Publisher record", doi="10.1000/example")
    right = add_source(cfg, "archive", "Index record", pmid="123")
    extra = work / "third"
    init_corpus_root(extra, authority=FIXTURE_AUTHORITY)
    open_corpus(extra, authority=FIXTURE_AUTHORITY, profile=cfg.profile).adopt_manifest(profile=CorpusPins(
        science_contract="science:" + cfg.profile.base_contract_identity,
        domains={ns: f"{ns}:{identity}" for ns, identity in cfg.profile.activated_contracts.items()},
    ))
    cfg = replace(cfg, world=replace(cfg.world, corpus_roots=cfg.world.corpus_roots + (extra,)))
    open_world(cfg.world, authority=FIXTURE_AUTHORITY).admit(extra, provenance=Fresh())
    return cfg, left.id, right.id, extra


@pytest.fixture
def mounted_pair(certified_worker_work):
    saved = snapshot(certified_worker_work, "source-coreference-mounted", _build_mounted_pair)
    saved.restore()
    return saved.value


def _call_refused(dispatch, args, iid):
    with pytest.raises(Refused) as caught:
        dispatch.invoke(COMMAND, args, invocation_id=iid)
    return caught.value.refusal


def _check_replay(dispatch, ctx, args, iid, refusal):
    assert _call_refused(dispatch, args, iid) == refusal
    assert dispatch._session.invocation_acts(iid) == ()
    assert _events(ctx) == []
    ledger = ctx.config.operations_root / "sessions" / dispatch._session.session_id / "ledger.v1"
    lines = [json.loads(line) for line in ledger.read_text().splitlines()]
    attempt = [line for line in lines if line.get("invocation") == iid]
    assert [line["line"] for line in attempt] == ["invocation-open", "invocation-close"]
    assert attempt[-1]["outcome"] == {"refusal": envelope(refusal)}


@pytest.mark.parametrize("retired", [False, True])
def test_mounted_write_reuses_one_view_opened_before_the_act(mounted_pair, monkeypatch, retired):
    cfg, left, right, extra = mounted_pair
    ctx = ReadContext.open(cfg)
    live_ids = ctx.session_ids()
    if retired:
        extra_id = corpus_id_at(extra)
        open_world(cfg.world, authority=FIXTURE_AUTHORITY).retire(extra_id)
        live_ids -= {extra_id}
    built = world_belief.build_over(cfg, live_ids)
    seen = []
    open_view = world_belief.open_world_view
    attest = ScopedWriter.attest_coreference

    def capture(world, epoch):
        view = open_view(world, epoch)
        seen.append(("captured", view))
        return view

    def write(writer, node, *, view):
        assert seen == [("captured", view)]
        seen.append(("act", view))
        return attest(writer, node, view=view)

    monkeypatch.setattr(world_belief, "open_world_view", capture)
    monkeypatch.setattr(ScopedWriter, "attest_coreference", write)
    with research_rig(cfg, (COMMAND, "record")) as (dispatch, ctx):
        reply = dispatch.invoke(COMMAND, _inputs(left, right), invocation_id="mounted")
        assert [step for step, _ in seen] == ["captured", "act"]
        assert seen[0][1] is seen[1][1]
        (event,) = _events(ctx)
        assert event.id in reply.text
        assert left in dispatch.invoke("record", {"address": left}).text
        assert right in dispatch.invoke("record", {"address": right}).text
        assert world_belief.current_epoch(ctx.world).packaging_identity == built.packaging_identity


@pytest.mark.parametrize("condition", ["no-epoch", "coverage", "drift", "scope-no-epoch",
                                      "scope-coverage", "scope-drift", "absent-before-drift"])
def test_mounted_preflight_reports_first_failure_and_replays(mounted_pair, monkeypatch, condition):
    cfg, left, right, extra = mounted_pair
    ctx = ReadContext.open(cfg)
    extra_id = corpus_id_at(extra)
    left_id = corpus_id_at(cfg.write_root)
    live_ids = ctx.session_ids()
    if condition.startswith("scope-"):
        open_world(cfg.world, authority=FIXTURE_AUTHORITY).retire(extra_id)
        live_ids -= {extra_id}
    if condition.endswith("coverage"):
        world_belief.build_over(cfg, live_ids - {left_id})
    elif not condition.endswith("no-epoch"):
        world_belief.build_over(cfg, live_ids)
        add_source(cfg, "corpus", "Later source", pmid="456")

    with research_rig(cfg, (COMMAND,)) as (dispatch, ctx):
        args = _inputs(left, right)
        if condition == "absent-before-drift":
            capture = world_belief.open_world_view

            def absent(world, epoch):
                displaced = extra.with_name("displaced")
                extra.rename(displaced)
                try:
                    return capture(world, epoch)
                finally:
                    displaced.rename(extra)

            with monkeypatch.context() as inject:
                inject.setattr(world_belief, "open_world_view", absent)
                refusal = _call_refused(dispatch, args, "currency")
            assert (refusal.code, refusal.data) == ("kernel-refused", {
                "kind": "AbsentCarrier", "absent": [extra_id],
            })
            assert "restore" in refusal.message.lower() and "science epoch" not in refusal.message
        else:
            refusal = _call_refused(dispatch, args, "currency")
            if condition.startswith("scope-"):
                assert (refusal.code, refusal.data) == (
                    "config-stale", {"session_only": [extra_id], "live_only": []},
                )
                assert "reopen" in refusal.message
            else:
                assert "science epoch" in refusal.message and "fresh invocation" in refusal.message
                if condition == "no-epoch":
                    assert (refusal.code, refusal.data) == ("no-epoch", {})
                else:
                    assert (refusal.code, refusal.data) == ("epoch-stale", {
                        "missing": [left_id] if condition == "coverage" else [],
                        "extra": [],
                        "drifted": [left_id] if condition == "drift" else [],
                    })
        _check_replay(dispatch, ctx, args, "currency", refusal)


@pytest.mark.parametrize("change", ["missing", "address", "uid", "kind"])
def test_mounted_capture_rechecks_exact_identity(mounted_pair, monkeypatch, change):
    cfg, left, right, _ = mounted_pair
    world_belief.publish_session_epoch(cfg)
    resolve = WorldReadView.resolve
    get = WorldReadView.get
    new_uid = "f" * 32

    def resolve_left(view, ref):
        if ref == left and change in {"missing", "address"}:
            return None if change == "missing" else "source:changed"
        return resolve(view, ref)

    def get_left(view, ref):
        node = get(view, ref)
        if ref != left:
            return node
        if change == "kind":
            return node.model_copy(update={"kind": "proposition"})
        return node.model_copy(update={"uid": new_uid}) if change == "uid" else node

    with research_rig(cfg, (COMMAND,)) as (dispatch, ctx):
        expected_uid = ctx.write_view().get(left).uid
        args = _inputs(left, right)
        with monkeypatch.context() as inject:
            inject.setattr(WorldReadView, "resolve", resolve_left)
            inject.setattr(WorldReadView, "get", get_left)
            refusal = _call_refused(dispatch, args, "moved")
        if change == "kind":
            assert (refusal.code, refusal.data) == ("kernel-refused", {"kind": "MalformedRecord"})
        else:
            assert (refusal.code, refusal.data) == ("epoch-stale", {
                "field": "left", "address": left, "expected_uid": expected_uid,
                "resolved_address": {"missing": None, "address": "source:changed"}.get(change, left),
                "resolved_uid": {"missing": None, "uid": new_uid}.get(change, expected_uid),
            })
            assert "reread" in refusal.message.lower()
        _check_replay(dispatch, ctx, args, "moved", refusal)


@pytest.mark.parametrize(("site", "failure"), [
    ("discovery", errors.CorpusStateMalformed),
    ("discovery", errors.ContractMismatch),
    ("discovery", RefError),
    ("discovery", OSError),
    ("epoch", errors.EpochMalformed),
    ("capture", errors.CaptureDrift),
    ("capture", errors.BuildContended),
    ("capture", errors.ResolutionRefused),
    ("resolve", errors.SemanticHashMissing),
    ("get", errors.SemanticHashStale),
    ("get", errors.CorpusDamaged),
    ("get", errors.RecordNotPresent),
    ("act", errors.BuildHold),
])
def test_mounted_faults_close_with_original_kernel_type(mounted_pair, monkeypatch, site, failure):
    cfg, left, right, _ = mounted_pair
    world_belief.publish_session_epoch(cfg)
    owner, method = {
        "discovery": (ReadContext, "mounts"),
        "epoch": (world_belief, "current_epoch"),
        "capture": (world_belief, "open_world_view"),
        "resolve": (WorldReadView, "resolve"),
        "get": (WorldReadView, "get"),
        "act": (ScopedWriter, "attest_coreference"),
    }[site]

    def fail(*args, **kwargs):
        if failure in (errors.CorpusDamaged, errors.RecordNotPresent):
            raise failure(args[1], corpus_id_at(cfg.write_root), args[0].stamp)
        raise failure("injected read or hold failure")

    with research_rig(cfg, (COMMAND,)) as (dispatch, ctx):
        args = _inputs(left, right)
        with monkeypatch.context() as inject:
            inject.setattr(owner, method, fail)
            refusal = _call_refused(dispatch, args, "fault")
        assert refusal.code == "kernel-refused" and refusal.data == {"kind": failure.__name__}
        assert "science epoch" not in refusal.message
        _check_replay(dispatch, ctx, args, "fault", refusal)


def test_storage_error_after_commit_does_not_close_as_a_refusal(local_pair, monkeypatch):
    cfg, left, right = local_pair
    original = ScopedWriter.attest_coreference

    def succeed_then_fail(writer, node):
        original(writer, node)
        raise OSError("storage error after commit")

    with research_rig(cfg, (COMMAND,)) as (dispatch, ctx):
        args = _inputs(left, right)
        with monkeypatch.context() as inject:
            inject.setattr(ScopedWriter, "attest_coreference", succeed_then_fail)
            with pytest.raises(OSError, match="after commit"):
                dispatch.invoke(COMMAND, args, invocation_id="post-act")
        assert len(_events(ctx)) == len(dispatch._session.invocation_acts("post-act")) == 1
        assert _call_refused(dispatch, args, "post-act").code == "outcome-unknown"
