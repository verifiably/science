"""Exposure events: one strict payload, the session's recorder, and every refusal before the act."""
from __future__ import annotations

import json
import re
from dataclasses import replace
from pathlib import Path

import pytest
from beliefs import stored
from beliefs.reservation import ExposureEvent, IntervalUnit, TermUnit
from helpers.reservation import (
    COHORT, COMMANDS, OMIT, add_foreign_mount, event_facet, event_node, hold_record, no_writer_act, stored_of,
    write_payload,
)
from helpers.research import raw_write_node, research_rig
from helpers.snapshot import snapshot
from helpers.world import build_fixture_world, build_shared_world_with_evidence, mount_config
from nodes.core.relations import Relation
from science.config import corpus_id_at
from science.refusal import Refused

COMMAND = "exposure-event"


@pytest.fixture
def shared(certified_worker_work):
    snap = snapshot(certified_worker_work, "shared-with-evidence", build_shared_world_with_evidence)
    snap.restore()
    return snap.value


def _refusal(dispatch, payload, iid):
    with no_writer_act(), pytest.raises(Refused) as caught:
        dispatch.invoke(COMMAND, {"payload": payload}, invocation_id=iid)
    assert dispatch._session.invocation_acts(iid) == ()
    return caught.value.refusal


def _minted(text: str) -> str:
    return re.search(r"exposure-event:[0-9a-f]{64}", text)[0]


def test_the_mm_unmask_event_is_minted_under_the_sessions_recorder(shared, tmp_path):
    cfg, _ = shared
    source = hold_record(cfg.write_root, cfg.profile,
                         stored.source_node(title="GSE24080", identifiers={"accession": "GSE24080"}))
    account = ("phase-2 unmask completed (release gse24080-pilot-v2r2-2026-11-06, attempt d3e989d0fadb422f) — "
               "exploratory description (design 2026-10-18)")
    freeze = "sha256:3f3a832745fd2919" + "0" * 48
    observer = "session:b71d3a9e40c2f6851e9a7d03c4b62f18"
    evidence = "atoms-event:3d426b17308814dd4a97e7c44e8b6a300325506715a22b5d5af438cb0ece41a8"
    payload = write_payload(tmp_path, event_facet(
        channel="read", subjects=[source.id], **{"class": "unmask"}, bound={"freeze": freeze}, account=account,
        observer=observer, observed_at="2026-11-06T09:15:00Z", propositions=["proposition:shared"],
        evidence=[evidence]), title="GSE24080 cohort uams-tt2-tt3: phase-2 unmask completed")

    with research_rig(cfg, COMMANDS) as (d, ctx):
        reply = d.invoke(COMMAND, {"payload": payload}, invocation_id="MM-UNMASK")
        expected = ExposureEvent(
            channel="read", subjects=(source.id,), units=(TermUnit(COHORT, "uams-tt2-tt3"),), effect="exposing",
            read_class="unmask", bound=(("freeze", freeze),), account=account, observer=observer,
            recorded_by=d._session.actor, observed_at="2026-11-06T09:15:00Z", propositions=("proposition:shared",),
            evidence=(evidence,))
        node = ctx.write_view().get(expected.id)
        assert reply.text == (f"[exposure-event] {expected.id} uid={node.uid}\n"
                              "GSE24080 cohort uams-tt2-tt3: phase-2 unmask completed\n")
        assert stored.exposure_event_value(node) == expected
        assert node.relations == [
            Relation(source=expected.id, predicate="exposes", target=source.id),
            Relation(source=expected.id, predicate="concerns", target="proposition:shared"),
        ]
        assert node.body == ""
        assert len(d._session.invocation_acts("MM-UNMASK")) == 1
        assert d.invoke(COMMAND, {"payload": payload}, invocation_id="MM-UNMASK").text == reply.text
        assert stored_of(ctx, COMMAND) == [expected.id]


def test_interval_and_kernel_evidence_survive_with_their_edges(shared, tmp_path):
    """A Sun date-of-use event: interval units, no subject, and kernel evidence held by a read mount."""
    cfg, mounted = shared
    view = mount_config(cfg)
    with research_rig(cfg, COMMANDS) as (d, ctx):
        mount = next(m for m in ctx.mounts() if m.root == view.write_root)
        refs = sorted([mounted["run"], next(
            n.id for n in mount.view.iter_stored() if n.kind == "holdings-observation")])
        payload = write_payload(tmp_path, event_facet(
            units=[{"start": "open", "end": "2026-11-07T14:40:51Z"}], observed_at="2026-11-07T14:40:51Z",
            evidence=sorted([*refs, "task:sun-7bfa16"])))
        address = _minted(d.invoke(COMMAND, {"payload": payload}).text)
        node = ctx.write_view().get(address)
        value = stored.exposure_event_value(node)
        assert value.units == (IntervalUnit("open", "2026-11-07T14:40:51Z"),)
        assert value.evidence == tuple(sorted([*refs, "task:sun-7bfa16"]))
        assert [(r.predicate, r.target) for r in node.relations] == [("attested-by", ref) for ref in refs]


def test_required_empty_arrays_keep_their_kernel_meaning(certified_work, tmp_path):
    cfg = build_fixture_world(certified_work)
    payload = write_payload(tmp_path, event_facet(units=[], propositions=[]))
    with research_rig(cfg, COMMANDS) as (d, ctx):
        address = _minted(d.invoke(COMMAND, {"payload": payload}).text)
        node = ctx.write_view().get(address)
        facet = node.facets[stored.EXPOSURE_EVENT_FACET]
        assert facet == {**event_facet(units=[]), "recorded_by": d._session.actor}


VALID = {"schema_version": 1, "title": "t", "facet": event_facet(units=[])}


def _text(**changes) -> bytes:
    return json.dumps({k: v for k, v in {**VALID, **changes}.items() if v is not OMIT}).encode()


def _facet(**changes) -> bytes:
    return _text(facet=event_facet(**{"units": [], **changes}))


DOCUMENTS = {
    "not-utf8": b"\xff\xfe",
    "not-json": b"{",
    "byte-order-mark": b"\xef\xbb\xbf" + _text(),
    "not-an-object": b"[]",
    "deeply-nested": b"[" * 200_000,
    "extra-envelope-key": _text(body="prose"),
    "no-title": _text(title=OMIT),
    "no-facet": _text(facet=OMIT),
    "no-version": _text(schema_version=OMIT),
    "version-2": _text(schema_version=2),
    "version-true": _text(schema_version=True),
    "version-float": _text().replace(b'"schema_version": 1', b'"schema_version": 1.0'),
    "version-string": _text(schema_version="1"),
    "facet-not-an-object": _text(facet=[]),
    "facet-null": _text(facet=None),
    "title-null": _text(title=None),
    "title-empty": _text(title=""),
    "title-blank": _text(title="  "),
    "title-multiline": _text(title="one\ntwo"),
    "title-surrogate": _text(title="\ud800"),
    "duplicate-envelope-key": _text().replace(b'"title": "t"', b'"title": "t", "title": "u"'),
    "duplicate-facet-key": _text().replace(b'"effect": "exposing"', b'"effect": "exposing", "effect": "non-exposing"'),
    "duplicate-nested-key": _facet(bound={"freeze": "sha256:" + "0" * 64}).replace(
        b'"bound": {', b'"bound": {"freeze": "sha256:' + b"1" * 64 + b'", '),
    "non-finite": _text().replace(b'"schema_version": 1', b'"schema_version": NaN'),
    "supplied-recorder": _facet(recorded_by="codex"),
    "unknown-facet-key": _facet(note="extra"),
    "missing-propositions": _facet(propositions=OMIT),
    "missing-units": _facet(units=OMIT),
    "null-bound": _facet(bound=None),
    "null-evidence": _facet(evidence=None),
    "empty-bound": _facet(bound={}),
    "empty-evidence": _facet(evidence=[]),
    "unsorted-evidence": _facet(evidence=["task:b", "task:a"]),
    "wrong-kind-evidence": _facet(evidence=["assessment:" + "0" * 64]),
    "surrogate-account": _facet(account="\ud800"),
    "read-without-subjects": _facet(channel="read"),
    "bad-timestamp": _facet(observed_at="2026-11-06"),
    "numeric-account": _facet(account=3),
}


@pytest.mark.parametrize("document", DOCUMENTS.values(), ids=DOCUMENTS)
def test_a_malformed_or_noncanonical_payload_refuses_before_acting(certified_work, tmp_path, document):
    cfg = build_fixture_world(certified_work)
    path = tmp_path / "payload.json"
    path.write_bytes(document)
    with research_rig(cfg, COMMANDS) as (d, ctx):
        refusal = _refusal(d, str(path), "BAD")
        assert refusal.code == "invalid-input"
        assert "payload.json" in refusal.message and str(tmp_path) not in refusal.message
        assert stored_of(ctx, COMMAND) == []


@pytest.mark.parametrize("kind", ["missing", "directory"])
def test_an_unreadable_payload_path_refuses(certified_work, tmp_path, kind):
    cfg = build_fixture_world(certified_work)
    path = tmp_path / "payload"
    if kind == "directory":
        path.mkdir()
    with research_rig(cfg, COMMANDS) as (d, _):
        assert _refusal(d, str(path), "UNREADABLE").code == "invalid-input"


def test_the_caller_is_told_which_rule_a_payload_broke(certified_work, tmp_path):
    cfg = build_fixture_world(certified_work)
    cases = {
        "recorder": (event_facet(units=[], recorded_by="codex"), {"field": "facet.recorded_by"}),
        "noncanonical": (event_facet(units=[], bound={}, evidence=None), {"field": "facet", "noncanonical": ["bound", "evidence"]}),
        "malformed": (event_facet(units=[], channel="read"), {"kind": "MalformedRecord"}),
    }
    with research_rig(cfg, COMMANDS) as (d, _):
        for name, (facet, data) in cases.items():
            if name == "noncanonical":
                facet["evidence"] = []
            assert _refusal(d, write_payload(tmp_path, facet), name).data == data, name
        assert _refusal(d, write_payload(tmp_path, event_facet(), title="a\nb"), "title").data == {"field": "title"}


@pytest.mark.parametrize("coordination", [True, False])
@pytest.mark.parametrize("where", ["corpus", "shared", "both"])
def test_an_event_already_held_by_a_live_mount_is_not_minted_again(shared, tmp_path, where, coordination):
    cfg, _ = shared
    if not coordination:
        cfg = replace(cfg, coordination=None)
    facet = event_facet()
    mounted = mount_config(cfg)
    targets = [target for name, target in (("corpus", cfg), ("shared", mounted)) if where in (name, "both")]
    with research_rig(cfg, COMMANDS) as (d, ctx):
        node = event_node(facet, actor=d._session.actor)
        for target in targets:
            hold_record(target.write_root, target.profile, node, actor=d._session.actor)
        before = stored_of(ctx, COMMAND)
        refusal = _refusal(d, write_payload(tmp_path, facet, title="Another title"), "DUPLICATE")
        assert refusal.code == "invalid-input"
        assert refusal.data == {"existing": [{
            "address": node.id, "uid": node.uid,
            "corpora": sorted(corpus_id_at(target.write_root) for target in targets)}]}
        assert stored_of(ctx, COMMAND) == before


def test_a_duplicate_of_the_sessions_own_event_refuses_in_a_new_invocation(certified_work, tmp_path):
    cfg = build_fixture_world(certified_work)
    payload = write_payload(tmp_path, event_facet(units=[]))
    with research_rig(cfg, COMMANDS) as (d, ctx):
        address = _minted(d.invoke(COMMAND, {"payload": payload}, invocation_id="FIRST").text)
        refusal = _refusal(d, payload, "SECOND")
        assert refusal.data["existing"][0]["address"] == address
        assert stored_of(ctx, COMMAND) == [address]


@pytest.mark.parametrize("where", ["corpus", "shared"])
def test_an_address_another_kind_occupies_refuses(shared, tmp_path, where):
    cfg, _ = shared
    root = {"corpus": cfg.write_root, "shared": mount_config(cfg).write_root}[where]
    with research_rig(cfg, COMMANDS) as (d, ctx):
        address = event_node(event_facet(), actor=d._session.actor).id
        occupying = stored.dataset_node(
            title="Occupying", resources=[{"name": "x", "digest": "sha256:" + "0" * 64}],
        ).model_copy(update={"deprecated_ids": [address]})
        raw_write_node(root, occupying)
        refusal = _refusal(d, write_payload(tmp_path, event_facet()), "OCCUPIED")
        assert refusal.code == "invalid-input"
        assert refusal.data == {"occupied": {"address": occupying.id, "uid": occupying.uid, "kind": "dataset",
                                             "corpora": [corpus_id_at(root)], "redirect": True}}
        assert stored_of(ctx, COMMAND) == []


def test_divergent_copies_of_the_address_keep_the_lookups_refusal(shared, tmp_path):
    cfg, _ = shared
    mounted = mount_config(cfg)
    with research_rig(cfg, COMMANDS) as (d, _):
        for index, target in enumerate((cfg, mounted)):
            hold_record(target.write_root, target.profile,
                        event_node(event_facet(), actor=d._session.actor, title=f"copy {index}"), actor=d._session.actor)
        refusal = _refusal(d, write_payload(tmp_path, event_facet()), "DIVERGENT")
        assert refusal.code == "invalid-input" and "copies differ" in refusal.message
        assert all(corpus_id_at(target.write_root) in refusal.message for target in (cfg, mounted))


def test_unresolved_citations_are_reported_together_with_their_unmounted_holders(shared, tmp_path):
    cfg, mounted = shared
    missing_source = "source:" + "0" * 64
    missing_run = "run:" + "0" * 64
    payload = write_payload(tmp_path, event_facet(
        channel="read", subjects=sorted([mounted["data"], missing_source]), propositions=["proposition:shared"],
        evidence=sorted([missing_run, "task:external"])))
    held = [mounted["data"], "proposition:shared"]
    with research_rig(cfg, COMMANDS) as (d, ctx):
        refusal = _refusal(d, payload, "MISSING")
        assert refusal.code == "invalid-input"
        assert refusal.data == {"unresolved": [missing_source, missing_run]}
    with research_rig(replace(cfg, coordination=None), COMMANDS) as (d, ctx):
        refusal = _refusal(d, payload, "UNMOUNTED")
        shared_id = corpus_id_at(mount_config(cfg).write_root)
        assert refusal.data == {
            "unresolved": [mounted["data"], missing_source, "proposition:shared", missing_run],
            "unmounted": {ref: [shared_id] for ref in held}}
        assert "coordination = false" in refusal.message
        assert stored_of(ctx, COMMAND) == []


@pytest.mark.parametrize("slot", ["subjects", "propositions", "evidence"])
def test_a_reference_of_the_wrong_kind_refuses(shared, tmp_path, slot):
    cfg, _ = shared
    prefix = {"subjects": "source:", "propositions": "proposition:", "evidence": "run:"}[slot]
    alias = prefix + "aliased"
    raw_write_node(cfg.write_root, stored.procedure_node(_fixture_procedure()).model_copy(
        update={"deprecated_ids": [alias]}))
    changes = {"subjects": {"channel": "read", "subjects": [alias]}, "propositions": {"propositions": [alias]},
               "evidence": {"evidence": [alias]}}[slot]
    with research_rig(cfg, COMMANDS) as (d, ctx):
        refusal = _refusal(d, write_payload(tmp_path, event_facet(**changes)), "WRONG-KIND")
        assert refusal.code == "invalid-input"
        assert refusal.data == {"kind": "ReservationRefused", "check": "exposure-ref-unresolved"}
        assert alias in refusal.message and "procedure" in refusal.message
        assert stored_of(ctx, COMMAND) == []


def _fixture_procedure():
    from beliefs.procedure import Procedure
    return Procedure("general/estimator", "Aliased", "Fixture.", (), None, {}, (), (), None, None, {}, None)


def test_an_undeclared_term_sort_refuses(shared, tmp_path):
    cfg, _ = shared
    payload = write_payload(tmp_path, event_facet(units=[{"sort": "mm/cohort", "term": "uams-tt2-tt3"}]))
    with research_rig(cfg, COMMANDS) as (d, ctx):
        refusal = _refusal(d, payload, "SORT")
        assert refusal.code == "invalid-input"
        assert refusal.data == {"kind": "ReservationRefused", "check": "exposure-unit-sort-undeclared"}
        assert "mm/cohort" in refusal.message and stored_of(ctx, COMMAND) == []


@pytest.mark.parametrize("copies", [("foreign",), ("shared", "foreign"), ("corpus", "shared", "foreign")],
                         ids=["only", "agreeing-mount", "agreeing-write-root"])
def test_a_holder_pinning_another_contract_refuses_even_beside_an_acceptable_copy(shared, tmp_path, copies):
    cfg, _ = shared
    mounted = mount_config(cfg)
    cfg, foreign, foreign_profile = add_foreign_mount(cfg)
    node = stored.source_node(title="Cited paper", identifiers={"doi": "10.1234/cited"})
    for name, (root, profile) in {"corpus": (cfg.write_root, cfg.profile), "shared": (mounted.write_root, mounted.profile),
                                  "foreign": (foreign, foreign_profile)}.items():
        if name in copies:
            hold_record(root, profile, node)
    payload = write_payload(tmp_path, event_facet(channel="read", subjects=[node.id]))
    with research_rig(cfg, COMMANDS) as (d, ctx):
        refusal = _refusal(d, payload, "PINS")
        assert refusal.code == "kernel-refused"
        assert refusal.data == {"kind": "CitationContractMismatch"}
        assert str(foreign) in refusal.message and stored_of(ctx, COMMAND) == []
    if "corpus" in copies:
        with research_rig(replace(cfg, coordination=None), COMMANDS) as (d, ctx):
            assert _minted(d.invoke(COMMAND, {"payload": payload}).text) in stored_of(ctx, COMMAND)


def test_a_retired_mount_supplies_no_citation_and_occupies_no_address(shared, tmp_path):
    from beliefs.root import open_world
    from helpers.world import FIXTURE_AUTHORITY
    cfg, mounted = shared
    mount = mount_config(cfg)
    open_world(cfg.world, authority=FIXTURE_AUTHORITY).retire(corpus_id_at(mount.write_root))
    with research_rig(replace(cfg, coordination=None), COMMANDS) as (d, ctx):
        refusal = _refusal(d, write_payload(tmp_path, event_facet(propositions=["proposition:shared"])), "RETIRED")
        assert refusal.data == {"unresolved": ["proposition:shared"]}


@pytest.mark.parametrize("where", ["corpus", "shared"])
def test_a_damaged_cited_record_refuses_structurally_and_replays(shared, tmp_path, where):
    cfg, _ = shared
    root = {"corpus": cfg.write_root, "shared": mount_config(cfg).write_root}[where]
    node = stored.proposition_node("damaged", title="damaged", claim={"operator": "affects"})
    node.facets[stored.SEMANTIC_IDENTITY_FACET] = {"digest": "0" * 64}
    raw_write_node(root, node)
    payload = write_payload(tmp_path, event_facet(propositions=["proposition:damaged"]))
    with research_rig(cfg, COMMANDS) as (d, _):
        first = _refusal(d, payload, "DAMAGED")
        assert first.code == "kernel-refused"
        assert _refusal(d, payload, "DAMAGED") == first
