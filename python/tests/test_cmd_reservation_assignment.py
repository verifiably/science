"""Reservation assignments: linear chains over live mounts, and every refusal before the act."""
from __future__ import annotations

import re
from dataclasses import replace

import pytest
from beliefs import stored
from beliefs.reservation import (
    Group, GroupChange, IntervalUnit, ReservationAssignment, TermUnit, assignment_changes_of, assignment_head,
)
from helpers.reservation import (
    COHORT, COMMANDS, OMIT, add_foreign_mount, assignment_facet, assignment_node, digest, event_facet, event_node, group,
    hold_record, no_writer_act, stored_of, write_payload,
)
from helpers.research import raw_write_node, research_rig
from helpers.snapshot import snapshot
from helpers.world import build_fixture_world, build_shared_world_with_evidence, mount_config
from nodes.core.relations import Relation
from science.config import corpus_id_at
from science.refusal import Refused

COMMAND = "reservation-assignment"
CHAIN = "mm-roster"


@pytest.fixture
def shared(certified_worker_work):
    snap = snapshot(certified_worker_work, "shared-with-evidence", build_shared_world_with_evidence)
    snap.restore()
    return snap.value


def _minted(text: str, kind: str = COMMAND) -> str:
    return re.search(kind + r":[0-9a-f]{64}", text)[0]


def _assign(d, directory, facet, iid=None, **envelope) -> str:
    return _minted(d.invoke(COMMAND, {"payload": write_payload(directory, facet, **envelope)}, invocation_id=iid).text)


def _record_event(d, directory, **changes) -> str:
    return _minted(d.invoke("exposure-event", {"payload": write_payload(directory, event_facet(**changes))}).text,
                   "exposure-event")


def _refusal(d, directory, facet, iid):
    payload = write_payload(directory, facet, name=f"{iid}.json")
    with no_writer_act(), pytest.raises(Refused) as caught:
        d.invoke(COMMAND, {"payload": payload}, invocation_id=iid)
    assert d._session.invocation_acts(iid) == ()
    with pytest.raises(Refused) as replayed:
        d.invoke(COMMAND, {"payload": payload}, invocation_id=iid)
    assert replayed.value.refusal == caught.value.refusal
    return caught.value.refusal


def test_a_root_and_its_successor_are_stored_as_the_kernel_values(shared, tmp_path):
    """The mm 2026-11-06 assignment after its D1 event: unchanged groups, one more considered event."""
    cfg, _ = shared
    inputs = {"amendment-7": digest("amendment-7"), "catchments.yaml": digest("catchments"), "roster.yaml": digest("roster")}
    groups = [
        group("a20-mm-patients-pone2015", role="unresolved", label="unresolved"),
        group("bcd-25-0005-antigen-loss-cohort", "friedrich-2023", "leblay-2024", role="open", label="discovery"),
        group("uams-tt2-tt3", role="reserved", label="reserved (A1)", basis=digest("comparison set")),
    ]
    with research_rig(cfg, COMMANDS) as (d, ctx):
        first = _record_event(d, tmp_path)
        root = _assign(d, tmp_path, assignment_facet(inputs=inputs, groups=groups, events=[first]), "ROOT",
                       title="mm reservation assignment, first section")
        second = _record_event(d, tmp_path, account="phase-2 inspection recorded", observed_at="2026-11-06T12:30:00Z")
        successor = _assign(d, tmp_path, assignment_facet(
            inputs=inputs, groups=groups, events=sorted([first, second]), predecessor=root, evidence=[second],
            account="Roster unchanged after D1.", participants=["codex", "keith"], prior_runs=["job:phase-2"],
            assigned_at="2026-11-06T14:00:00Z"), "SUCCESSOR")

        kernel_groups = (
            Group((TermUnit(COHORT, "a20-mm-patients-pone2015"),), "unresolved", "unresolved", None),
            Group(tuple(TermUnit(COHORT, t) for t in ("bcd-25-0005-antigen-loss-cohort", "friedrich-2023", "leblay-2024")),
                  "open", "discovery", None),
            Group((TermUnit(COHORT, "uams-tt2-tt3"),), "reserved", "reserved (A1)", digest("comparison set")),
        )
        expected_root = ReservationAssignment(
            chain=CHAIN, rule_name="mm-phase-1-protocol", rule_version="amendment-7", inputs=tuple(sorted(inputs.items())),
            events=(first,), scope=None, applies=None, groups=kernel_groups, predecessor=None, evidence=(), flagged=None,
            account=None, participants=(), prior_runs=(), assigned_at="2026-11-06T13:00:00Z", assigned_by=d._session.actor)
        expected = replace(expected_root, events=tuple(sorted([first, second])), predecessor=root, evidence=(second,),
                           account="Roster unchanged after D1.", participants=("codex", "keith"), prior_runs=("job:phase-2",),
                           assigned_at="2026-11-06T14:00:00Z")
        assert (root, successor) == (expected_root.id, expected.id)
        view = ctx.write_view()
        assert view.get(root).title == "mm reservation assignment, first section"
        assert stored.reservation_assignment_value(view.get(root)) == expected_root
        assert stored.reservation_assignment_value(view.get(successor)) == expected
        assert view.get(root).relations == [Relation(source=root, predicate="considers", target=first)]
        assert {(r.predicate, r.target) for r in view.get(successor).relations} == {
            ("considers", first), ("considers", second), ("evidenced-by", second), ("supersedes", root)}
        assert assignment_head(view, CHAIN).id == successor
        assert assignment_changes_of(view, successor) == ()
        assert len(d._session.invocation_acts("SUCCESSOR")) == 1


def test_the_sun_epoch_assignment_17_keeps_its_epochs_and_considers_two_more_events(certified_work, tmp_path):
    cfg = build_fixture_world(certified_work)
    bounds = ["open", "2007-11-01T00:00:00Z", "2008-12-01T00:00:00Z", "2019-12-01T00:00:00Z", "2021-01-01T00:00:00Z",
              "2025-09-29T00:00:00Z", "2026-10-29T00:00:00Z", "open"]
    roles = [("open", "exploration"), ("withheld", "guard"), ("reserved", "reserved (retrospective)"), ("withheld", "guard"),
             ("open", "exploration"), ("withheld", "guard"), ("reserved", "reserved pool")]
    inputs = {
        "boundary-table": "sha256:a4b5b8812c9e966f013c55655176cbd22531e7afd0c304cb93cc38e00e50e4a0",
        "named-series": "sha256:1d1e6f4b9e75fe219327ae93454d9526833fbbf0159976573a4acc8c2de64eca",
        "rule": "sha256:6504868faa3d230913d67b1b2ef7d7b7c3f06ef0e00726af14f327addee8d9ff",
    }
    base = assignment_facet(
        chain="sun-epochs", rule={"name": "epoch-reservation-rule", "version": "3"}, inputs=inputs,
        groups=[{"units": [{"start": start, "end": end}], "role": role, "label": label}
                for start, end, (role, label) in zip(bounds[:-1], bounds[1:], roles, strict=True)])

    def knowledge(observer, until):
        return event_facet(units=[{"start": "open", "end": until}], observer=observer, observed_at=until,
                           account="Possible training exposure through the actual UTC date of use.",
                           evidence=["task:sun-7bfa16"])

    with research_rig(cfg, COMMANDS) as (d, ctx):
        earlier = _minted(d.invoke("exposure-event", {"payload": write_payload(
            tmp_path, knowledge("agent/K1", "2026-10-10T08:00:00Z"))}).text, "exposure-event")
        sixteen = _assign(d, tmp_path, {**base, "events": [earlier], "assigned_at": "2026-11-05T10:00:00Z"})
        k3, k5 = (_minted(d.invoke("exposure-event", {"payload": write_payload(
            tmp_path, knowledge(f"agent/{k}", "2026-11-07T14:40:51Z"))}).text, "exposure-event") for k in ("K3", "K5"))
        seventeen = _assign(d, tmp_path, {
            **base, "events": sorted([earlier, k3, k5]), "predecessor": sixteen, "evidence": sorted([k3, k5]),
            "account": "Inherits bounds, guards, prospective start and named series from assignment 16.",
            "assigned_at": "2026-11-07T14:40:51Z"}, title="sun epoch assignment 17")
        view = ctx.write_view()
        value = stored.reservation_assignment_value(view.get(seventeen))
        assert [g.units for g in value.groups] == [(IntervalUnit(a, b),) for a, b in zip(bounds, bounds[1:])]
        assert [(g.role, g.label) for g in value.groups] == roles
        assert dict(value.inputs) == inputs and value.events == tuple(sorted([earlier, k3, k5]))
        assert assignment_head(view, "sun-epochs").id == seventeen
        assert assignment_changes_of(view, seventeen) == ()
        event = stored.exposure_event_value(view.get(k5))
        assert (event.channel, event.subjects, event.observer) == ("knowledge", (), "agent/K5")


def test_a_second_root_of_a_chain_refuses_and_another_scope_or_chain_does_not(shared, tmp_path):
    cfg, _ = shared
    with research_rig(cfg, COMMANDS) as (d, ctx):
        root = _assign(d, tmp_path, assignment_facet())
        refusal = _refusal(d, tmp_path, assignment_facet(inputs={"roster.yaml": digest("other")}), "SECOND-ROOT")
        assert refusal.code == "invalid-input"
        assert refusal.data == {"chain": CHAIN, "scope": None, "head": root, "predecessor": None}
        scoped = _assign(d, tmp_path, assignment_facet(scope="proposition:shared", applies=root))
        other = _assign(d, tmp_path, assignment_facet(chain="another"))
        assert stored_of(ctx, COMMAND) == sorted([root, scoped, other])
        edges = {(r.predicate, r.target) for r in ctx.write_view().get(scoped).relations}
        assert edges == {("concerns", "proposition:shared"), ("applies", root)}


@pytest.mark.parametrize("coordination", [True, False])
def test_a_chain_held_only_by_a_read_mount_admits_neither_a_root_nor_a_successor(shared, tmp_path, coordination):
    """An ordinary citation of a read-mount record is admitted; superseding one is not."""
    cfg, _ = shared
    mounted = mount_config(cfg)
    if not coordination:
        cfg = replace(cfg, coordination=None)
    shared_id = corpus_id_at(mounted.write_root)
    event = hold_record(mounted.write_root, mounted.profile, event_node(event_facet(), actor="fixture"))
    head = hold_record(mounted.write_root, mounted.profile, assignment_node(assignment_facet(), actor="fixture"))
    with research_rig(cfg, COMMANDS) as (d, ctx):
        refusal = _refusal(d, tmp_path, assignment_facet(inputs={"roster.yaml": digest("new")}), "ROOT")
        assert refusal.code == "invalid-input" and refusal.data["head"] == head.id
        successor = assignment_facet(inputs={"roster.yaml": digest("new")}, predecessor=head.id)
        refusal = _refusal(d, tmp_path, successor, "SUCCESSOR")
        assert refusal.code == "invalid-input"
        assert shared_id in refusal.message and "write root" in refusal.message
        assert stored_of(ctx, COMMAND) == []
        if coordination:
            cited = _assign(d, tmp_path, assignment_facet(chain="another", events=[event.id]))
            assert stored_of(ctx, COMMAND) == [cited]


def test_a_predecessor_a_read_mount_already_extended_is_stale(shared, tmp_path):
    cfg, _ = shared
    mounted = mount_config(cfg)
    a = assignment_node(assignment_facet(), actor="fixture")
    for target in (cfg, mounted):
        hold_record(target.write_root, target.profile, a)
    b = hold_record(mounted.write_root, mounted.profile, assignment_node(
        assignment_facet(inputs={"roster.yaml": digest("b")}, predecessor=a.id), actor="fixture"))
    with research_rig(cfg, COMMANDS) as (d, ctx):
        refusal = _refusal(d, tmp_path, assignment_facet(inputs={"roster.yaml": digest("c")}, predecessor=a.id), "STALE")
        assert refusal.code == "invalid-input"
        assert refusal.data == {"chain": CHAIN, "scope": None, "head": b.id, "predecessor": a.id}
        assert stored_of(ctx, COMMAND) == [a.id]


@pytest.mark.parametrize("fork", ["two-roots", "two-heads"])
@pytest.mark.parametrize("attempt", ["root", "successor"])
def test_an_already_forked_chain_refuses_both_kinds_of_write(shared, tmp_path, fork, attempt):
    cfg, _ = shared
    mounted = mount_config(cfg)
    a = assignment_node(assignment_facet(), actor="fixture")
    hold_record(cfg.write_root, cfg.profile, a)
    if fork == "two-roots":
        other = assignment_node(assignment_facet(inputs={"roster.yaml": digest("z")}), actor="fixture")
        hold_record(mounted.write_root, mounted.profile, other)
        own = a
    else:
        hold_record(mounted.write_root, mounted.profile, a)
        own, _other = (hold_record(target.write_root, target.profile, assignment_node(
            assignment_facet(inputs={"roster.yaml": digest(name)}, predecessor=a.id), actor="fixture"))
            for name, target in (("own", cfg), ("mounted", mounted)))
    with research_rig(cfg, COMMANDS) as (d, ctx):
        before = stored_of(ctx, COMMAND)
        predecessor = {} if attempt == "root" else {"predecessor": own.id}
        refusal = _refusal(d, tmp_path, assignment_facet(inputs={"roster.yaml": digest("new")}, **predecessor), "FORKED")
        assert refusal.code == "kernel-refused" and refusal.data == {"kind": "ChainAmbiguous"}
        assert stored_of(ctx, COMMAND) == before


def test_a_stale_missing_or_foreign_chain_predecessor_refuses(shared, tmp_path):
    cfg, _ = shared
    with research_rig(cfg, COMMANDS) as (d, ctx):
        a = _assign(d, tmp_path, assignment_facet())
        b = _assign(d, tmp_path, assignment_facet(inputs={"roster.yaml": digest("b")}, predecessor=a))
        changed = {"inputs": {"roster.yaml": digest("c")}}
        assert _refusal(d, tmp_path, assignment_facet(**changed, predecessor=a), "STALE").data["head"] == b
        missing = "reservation-assignment:" + "0" * 64
        refusal = _refusal(d, tmp_path, assignment_facet(**changed, predecessor=missing), "MISSING")
        assert refusal.code == "invalid-input" and missing in refusal.message
        refusal = _refusal(d, tmp_path, assignment_facet(**changed, chain="another", predecessor=b), "CHAIN")
        assert refusal.data == {"chain": "another", "scope": None, "head": None, "predecessor": b}
        refusal = _refusal(d, tmp_path, assignment_facet(**changed, scope="proposition:shared", predecessor=b), "SCOPE")
        assert refusal.data == {"chain": CHAIN, "scope": "proposition:shared", "head": None, "predecessor": b}
        assert stored_of(ctx, COMMAND) == sorted([a, b])


RESERVED = [group("a", role="reserved"), group("b", role="open")]


@pytest.mark.parametrize("changes,check", [
    ({"groups": [*RESERVED, group("c", role="open")]}, "assignment-changes-without-evidence"),
    ({"groups": [RESERVED[0], group("b", role="withheld")]}, "assignment-changes-without-evidence"),
    ({"groups": [RESERVED[0]]}, "assignment-changes-without-evidence"),
    ({"groups": [group("a", role="open"), RESERVED[1]], "evidence": ["ledger:entry"]}, "assignment-suspension-unflagged"),
    ({"groups": [RESERVED[1]], "evidence": ["ledger:entry"]}, "assignment-suspension-unflagged"),
    ({"groups": [RESERVED[0], group("b", role="withheld")], "evidence": ["ledger:entry"], "flagged": []},
     "assignment-flagged-without-suspension"),
    ({"assigned_at": "2026-11-07T00:00:00Z"}, "assignment-unchanged"),
    ({"groups": [{"units": [{"start": "open", "end": "2026-01-01T00:00:00Z"}], "role": "reserved"}],
      "evidence": ["ledger:entry"], "flagged": []}, "assignment-scope-mismatch"),
], ids=["added", "changed", "absent", "suspended-by-change", "suspended-by-absence", "flag-without-suspension", "unchanged",
        "unit-shape"])
def test_succession_rules_refuse_before_the_act(shared, tmp_path, changes, check):
    """What mm's `roster check` enforced over its markdown, over stored records."""
    cfg, _ = shared
    with research_rig(cfg, COMMANDS) as (d, ctx):
        root = _assign(d, tmp_path, assignment_facet(groups=RESERVED))
        refusal = _refusal(d, tmp_path, assignment_facet(**{"groups": RESERVED, **changes}, predecessor=root), "SUCCESSION")
        assert refusal.code == "invalid-input"
        assert refusal.data == {"kind": "ReservationRefused", "check": check}
        assert stored_of(ctx, COMMAND) == [root]


def test_a_root_carrying_a_flag_refuses(shared, tmp_path):
    cfg, _ = shared
    with research_rig(cfg, COMMANDS) as (d, _):
        refusal = _refusal(d, tmp_path, assignment_facet(flagged=[]), "ROOT-FLAG")
        assert refusal.data == {"kind": "ReservationRefused", "check": "assignment-flagged-without-suspension"}


def test_an_evidenced_flagged_suspension_and_addition_are_minted(shared, tmp_path):
    cfg, mounted = shared
    with research_rig(cfg, COMMANDS) as (d, ctx):
        root = _assign(d, tmp_path, assignment_facet(groups=RESERVED))
        event = _record_event(d, tmp_path)
        successor = _assign(d, tmp_path, assignment_facet(
            groups=[group("a", role="open"), RESERVED[1], group("c", role="reserved")], events=[event], predecessor=root,
            evidence=[event], flagged=[mounted["assessment"]], prior_runs=[mounted["run"]]))
        view = ctx.write_view()
        assert assignment_changes_of(view, successor) == (
            GroupChange(TermUnit(COHORT, "a"), "changed", "reserved", True),
            GroupChange(TermUnit(COHORT, "c"), "added", None, False))
        assert {(r.predicate, r.target) for r in view.get(successor).relations} == {
            ("considers", event), ("evidenced-by", event), ("flags", mounted["assessment"]), ("reports", mounted["run"]),
            ("supersedes", root)}


def test_unresolved_references_of_every_slot_are_reported_together(shared, tmp_path):
    cfg, mounted = shared
    event, assessment, run, applied = (f"{kind}:" + "0" * 64 for kind in (
        "exposure-event", "assessment", "run", "reservation-assignment"))
    facet = assignment_facet(events=[event], evidence=[event, "ledger:entry"], flagged=sorted([assessment, mounted["assessment"]]),
                             prior_runs=["job:1", run], scope="proposition:nowhere", applies=applied)
    with research_rig(cfg, COMMANDS) as (d, ctx):
        refusal = _refusal(d, tmp_path, facet, "UNRESOLVED")
        assert refusal.code == "invalid-input"
        assert refusal.data == {"unresolved": [event, assessment, run, "proposition:nowhere", applied]}
    with research_rig(replace(cfg, coordination=None), COMMANDS) as (d, _):
        refusal = _refusal(d, tmp_path, facet, "UNMOUNTED")
        assert refusal.data["unmounted"] == {mounted["assessment"]: [corpus_id_at(mount_config(cfg).write_root)]}


def test_applies_names_a_program_level_assignment_and_sorts_are_declared(shared, tmp_path):
    cfg, _ = shared
    with research_rig(cfg, COMMANDS) as (d, ctx):
        scoped = _assign(d, tmp_path, assignment_facet(scope="proposition:shared"))
        refusal = _refusal(d, tmp_path, assignment_facet(scope="proposition:fresh", applies=scoped), "APPLIES")
        assert refusal.data == {"kind": "ReservationRefused", "check": "assignment-applies-scoped"}
        undeclared = {"units": [{"sort": "mm/cohort", "term": "x"}], "role": "open"}
        refusal = _refusal(d, tmp_path, assignment_facet(chain="other", groups=[undeclared]), "SORT")
        assert refusal.data == {"kind": "ReservationRefused", "check": "assignment-unit-sort-undeclared"}
        assert stored_of(ctx, COMMAND) == [scoped]


def test_a_scoped_successor_that_applies_its_own_predecessor_refuses(shared, tmp_path):
    cfg, _ = shared
    with research_rig(cfg, COMMANDS) as (d, ctx):
        scoped = _assign(d, tmp_path, assignment_facet(scope="proposition:shared"))
        refusal = _refusal(d, tmp_path, assignment_facet(
            scope="proposition:shared", applies=scoped, predecessor=scoped, inputs={"roster.yaml": digest("next")}), "SELF")
        assert refusal.code == "invalid-input"
        assert refusal.data == {"kind": "ReservationRefused", "check": "assignment-applies-scoped"}
        assert stored_of(ctx, COMMAND) == [scoped]


@pytest.mark.parametrize("facet", [
    assignment_facet(assigned_by="codex"),
    assignment_facet(scope=None), assignment_facet(predecessor=None), assignment_facet(flagged=None),
    assignment_facet(evidence=[]), assignment_facet(participants=[]), assignment_facet(prior_runs=[]),
    assignment_facet(groups=[]), assignment_facet(inputs={}), assignment_facet(events=OMIT),
    assignment_facet(groups=[{**group("a"), "label": None}]), assignment_facet(chain="MM"),
    assignment_facet(groups=[group("b"), group("a")]), assignment_facet(groups=[group("a"), group("a")]),
    assignment_facet(applies="reservation-assignment:" + "0" * 64),
])
def test_a_malformed_or_noncanonical_facet_refuses(certified_work, tmp_path, facet):
    cfg = build_fixture_world(certified_work)
    with research_rig(cfg, COMMANDS) as (d, ctx):
        assert _refusal(d, tmp_path, facet, "FACET").code == "invalid-input"
        assert stored_of(ctx, COMMAND) == []


def test_flagged_empty_keeps_its_kernel_meaning(shared, tmp_path):
    """A suspension reported with no assessment made: `flagged: []` is stored, not dropped."""
    cfg, _ = shared
    with research_rig(cfg, COMMANDS) as (d, ctx):
        root = _assign(d, tmp_path, assignment_facet(groups=RESERVED))
        successor = _assign(d, tmp_path, assignment_facet(
            groups=[RESERVED[1]], predecessor=root, evidence=["ledger:entry"], flagged=[]))
        assert ctx.write_view().get(successor).facets[stored.RESERVATION_ASSIGNMENT_FACET]["flagged"] == []


def test_an_assignment_already_held_by_a_live_mount_is_not_minted_again(shared, tmp_path):
    cfg, _ = shared
    mounted = mount_config(cfg)
    with research_rig(cfg, COMMANDS) as (d, ctx):
        actor = d._session.actor
        node = hold_record(mounted.write_root, mounted.profile, assignment_node(assignment_facet(), actor=actor), actor=actor)
        refusal = _refusal(d, tmp_path, assignment_facet(), "DUPLICATE")
        assert refusal.data == {"existing": [{"address": node.id, "uid": node.uid,
                                              "corpora": [corpus_id_at(mounted.write_root)]}]}
        assert stored_of(ctx, COMMAND) == []


@pytest.mark.parametrize("where", ["corpus", "shared"])
def test_an_assignment_address_another_kind_occupies_refuses(shared, tmp_path, where):
    cfg, _ = shared
    root = {"corpus": cfg.write_root, "shared": mount_config(cfg).write_root}[where]
    with research_rig(cfg, COMMANDS) as (d, ctx):
        address = assignment_node(assignment_facet(), actor=d._session.actor).id
        occupying = stored.dataset_node(
            title="Occupying", resources=[{"name": "x", "digest": "sha256:" + "0" * 64}],
        ).model_copy(update={"deprecated_ids": [address]})
        raw_write_node(root, occupying)
        refusal = _refusal(d, tmp_path, assignment_facet(), "OCCUPIED")
        assert refusal.code == "invalid-input"
        assert refusal.data == {"occupied": {"address": occupying.id, "uid": occupying.uid, "kind": "dataset",
                                             "corpora": [corpus_id_at(root)], "redirect": True}}
        assert stored_of(ctx, COMMAND) == []


def test_a_failed_successor_leaves_the_recorded_event_and_the_head(shared, tmp_path):
    cfg, _ = shared
    with research_rig(cfg, COMMANDS) as (d, ctx):
        root = _assign(d, tmp_path, assignment_facet(groups=RESERVED))
        event = _record_event(d, tmp_path)
        refusal = _refusal(d, tmp_path, assignment_facet(
            groups=[group("a", role="open"), RESERVED[1]], events=[event], predecessor=root, evidence=[event]), "FAILED")
        assert refusal.data["check"] == "assignment-suspension-unflagged"
        view = ctx.write_view()
        assert stored.exposure_event_value(view.get(event)).id == event
        assert assignment_head(view, CHAIN).id == root
        retried = _assign(d, tmp_path, assignment_facet(
            groups=[group("a", role="open"), RESERVED[1]], events=[event], predecessor=root, evidence=[event], flagged=[]))
        assert assignment_head(ctx.write_view(), CHAIN).id == retried


def test_a_competing_writer_is_refused_by_the_kernel_at_commit(shared, tmp_path, monkeypatch):
    """The preflight reads a snapshot; final admission belongs to the write root."""
    from beliefs.session.writer import ScopedWriter
    cfg, _ = shared
    rival = assignment_node(assignment_facet(inputs={"roster.yaml": digest("rival")}), actor="fixture")
    add = ScopedWriter.add

    def after_a_rival(self, node):
        hold_record(cfg.write_root, cfg.profile, rival)
        return add(self, node)

    with research_rig(cfg, COMMANDS) as (d, ctx):
        monkeypatch.setattr(ScopedWriter, "add", after_a_rival)
        payload = write_payload(tmp_path, assignment_facet())
        with pytest.raises(Refused) as caught:
            d.invoke(COMMAND, {"payload": payload}, invocation_id="RACED")
        assert caught.value.refusal.code == "kernel-refused"
        assert caught.value.refusal.data == {"kind": "ReservationRefused"}
        assert "assignment-root-exists" in caught.value.refusal.message
        assert d._session.invocation_acts("RACED") == ()
        assert stored_of(ctx, COMMAND) == [rival.id]


@pytest.mark.parametrize("where", ["corpus", "shared"])
@pytest.mark.parametrize("damage", ["stale-stamp", "malformed-facet"])
def test_a_malformed_assignment_in_a_live_mount_refuses_structurally(shared, tmp_path, where, damage):
    cfg, _ = shared
    root = {"corpus": cfg.write_root, "shared": mount_config(cfg).write_root}[where]
    node = assignment_node(assignment_facet(chain="damaged"), actor="fixture")
    del node.facets[stored.RESERVATION_ASSIGNMENT_FACET]["rule"]
    if damage == "malformed-facet":
        stored.stamp_semantic_identity(node)
    raw_write_node(root, node)
    with research_rig(cfg, COMMANDS) as (d, ctx):
        refusal = _refusal(d, tmp_path, assignment_facet(), "DAMAGED")
        assert refusal.code == "kernel-refused"
        assert refusal.data == {"kind": {"stale-stamp": "SemanticHashStale", "malformed-facet": "MalformedRecord"}[damage]}


def test_a_predecessor_copied_to_a_mismatched_mount_refuses(shared, tmp_path):
    """The kernel resolves the predecessor as a citation, so its other holders' pins must agree too."""
    cfg, _ = shared
    cfg, foreign, foreign_profile = add_foreign_mount(cfg)
    a = assignment_node(assignment_facet(), actor="fixture")
    for root, profile in ((cfg.write_root, cfg.profile), (foreign, foreign_profile)):
        hold_record(root, profile, a)
    with research_rig(cfg, COMMANDS) as (d, ctx):
        refusal = _refusal(d, tmp_path, assignment_facet(inputs={"roster.yaml": digest("b")}, predecessor=a.id), "PINS")
        assert refusal.code == "kernel-refused" and refusal.data == {"kind": "CitationContractMismatch"}
        assert stored_of(ctx, COMMAND) == [a.id]


@pytest.mark.parametrize("where", ["read-mount", "write-root"])
def test_a_retired_mounts_chain_is_not_visible(shared, tmp_path, where):
    from beliefs.root import open_world
    from helpers.world import FIXTURE_AUTHORITY
    cfg, _ = shared
    mounted = mount_config(cfg)
    hold_record(mounted.write_root, mounted.profile, assignment_node(assignment_facet(), actor="fixture"))
    if where == "read-mount":
        open_world(cfg.world, authority=FIXTURE_AUTHORITY).retire(corpus_id_at(mounted.write_root))
    with research_rig(cfg, COMMANDS) as (d, ctx):
        if where == "read-mount":
            root = _assign(d, tmp_path, assignment_facet())
            assert assignment_head(ctx.write_view(), CHAIN).id == root
        else:
            assert _refusal(d, tmp_path, assignment_facet(), "LIVE").data["head"].startswith("reservation-assignment:")
