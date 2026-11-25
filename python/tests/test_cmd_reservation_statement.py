"""A chain's checked-in statement: its bytes, its check, and the gate over unconsidered exposure."""
from __future__ import annotations

import dataclasses
import json
import os
import re
from hashlib import sha256

import pytest
import yaml
from beliefs import stored
from beliefs.coordination import CoordinationAddress
from helpers.reservation import (
    COHORT, add_foreign_mount, assignment_facet, assignment_node, digest, event_facet, event_node, group, hold_record,
)
from helpers.research import raw_write_node, research_rig
from helpers.snapshot import snapshot
from helpers.world import build_shared_contract_world, mount_config
from nodes.core.relations import Relation
from science.commands.reservation_statement import write
from science.config import ReadContext, corpus_id_at
from science.dispatch import Dispatcher
from science.loader import production_tree, resolve_handlers
from science.refusal import Refused

CHAIN = "mm-roster"
COMMAND = "reservation-statement"


@pytest.fixture
def shared(certified_worker_work):
    snap = snapshot(certified_worker_work, "shared-contract", build_shared_contract_world)
    snap.restore()
    return snap.value


@pytest.fixture
def out(tmp_path):
    return tmp_path / "reservation"


def _hold(target, node):
    return hold_record(target.write_root, target.profile, node).id


def _event(target, **changes) -> str:
    return _hold(target, event_node(event_facet(**changes), actor="fixture"))


def _assignment(target, **changes) -> str:
    return _hold(target, assignment_node(assignment_facet(**changes), actor="fixture"))


def _write(cfg, out, chain=CHAIN, **inputs):
    return write(ReadContext.open(cfg), chain=chain, directory=out, **inputs)


def _check(cfg, out, *, project=None, chain=CHAIN, **inputs) -> str:
    """The whole report of the production declaration, reassembled from its pages."""
    decls = tuple(decl for decl in production_tree() if decl.name == COMMAND)
    dispatcher = Dispatcher(decls, resolve_handlers(decls), ReadContext.open(cfg))
    given = {"chain": chain, "check": str(out), **inputs}
    page, text = dispatcher.invoke(COMMAND, given, project=project).text, ""
    while match := re.search(r"\n… truncated at \d+ bytes; continue with cursor (\S+)\n$", page):
        text += page[:match.start()]
        page = dispatcher.invoke(COMMAND, given, cursor=match[1], project=project).text
    return text + page


def _refused(call, *args, **kwargs):
    with pytest.raises(Refused) as caught:
        call(*args, **kwargs)
    return caught.value.refusal


def _section(text: str, title: str) -> list[str]:
    lines = text.splitlines()
    start = lines.index(f"{title}:") + 1
    end = next((i for i in range(start, len(lines)) if not lines[i].startswith("  ")), len(lines))
    return [line.strip() for line in lines[start:end]]


def _falls(text: str) -> dict[str, tuple[str, str]]:
    """Each listed event's `whose` and `falls`."""
    return {ref: tuple(line.partition(": ")[2] for line in _section(text, ref)[:2])
            for ref in re.findall(r"^(exposure-event:[0-9a-f]{64}):$", text, re.MULTILINE)}


def _project(cfg, name, *clauses) -> str:
    """A standing project whose query has one clause per argument, each a list of predicates."""
    query = {"version": "science.view-query.v1", "clauses": [{"all": list(clause)} for clause in clauses]}
    with research_rig(cfg, ("project",)) as (d, _):
        text = d.invoke("project", {"name": name, "query": yaml.safe_dump(query)}).text
    return "coord:" + re.search(r"project:([0-9a-f]{32})\.", text)[1]


def _claims(*refs):
    return [{"addresses": list(refs)}]


# --- the statement ------------------------------------------------------------


def test_the_mm_statement_carries_the_head_whole(shared, out):
    """The mm 2026-11-06 assignment: the rule version is opaque text, never a number."""
    first = _event(shared)
    second = _event(shared, observed_at="2026-11-01T00:00:00Z", account="An earlier look, recorded later.")
    inputs = {name: digest(name) for name in ("roster.yaml", "amendment-7", "catchments.yaml")}
    groups = [group("a20-mm-patients-pone2015", role="unresolved"),
              group("uams-tt2-tt3", role="reserved", label="reserved (A1)", basis=digest("comparison"))]
    root = _assignment(shared, events=[first], inputs=inputs, groups=groups)
    head = _assignment(shared, events=sorted([first, second]), inputs={**inputs, "roster.yaml": digest("new")},
                       groups=groups, predecessor=root, account="After D1.", participants=["codex", "keith"])
    _write(shared, out)
    raw = (out / f"{CHAIN}.json").read_bytes()
    content = json.loads(raw)
    assert raw == (json.dumps(content, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    assert set(content) == {"schema_version", "chain", "head", "history", "events"}
    assert (content["schema_version"], content["chain"]) == (1, CHAIN)
    view = ReadContext.open(shared).write_view()
    assert content["head"] == {"address": head, "facet": view.get(head).facets[stored.RESERVATION_ASSIGNMENT_FACET]}
    assert content["head"]["facet"]["rule"] == {"name": "mm-phase-1-protocol", "version": "amendment-7"}
    assert content["events"] == [{"address": ref, "facet": view.get(ref).facets[stored.EXPOSURE_EVENT_FACET]}
                                 for ref in (second, first)]
    lists = {"changes": [], "groups_removed": [], "groups_added": [], "events_dropped": []}
    rule = {"name": "mm-phase-1-protocol", "version": "amendment-7"}
    by = {"assigned_at": "2026-11-06T13:00:00Z", "assigned_by": "fixture", "rule": rule}
    assert content["history"] == [
        {"address": root, **by, **lists, "events_added": [first],
         "inputs_changed": ["amendment-7", "catchments.yaml", "roster.yaml"]},
        {"address": head, **by, **lists, "account": "After D1.", "participants": ["codex", "keith"],
         "events_added": [second], "inputs_changed": ["roster.yaml"]}]


def test_the_sun_statement_after_assignment_17(shared, out):
    bounds = ["open", "2007-11-01T00:00:00Z", "2008-12-01T00:00:00Z", "2026-10-29T00:00:00Z", "open"]
    groups = [{"units": [{"start": a, "end": b}], "role": role, "label": label} for a, b, (role, label) in
              zip(bounds, bounds[1:], [("open", "exploration"), ("withheld", "guard"), ("reserved", "retrospective"),
                                       ("reserved", "pool")], strict=False)]
    base = {"chain": "sun-epochs", "rule": {"name": "epoch-reservation-rule", "version": "3"}, "groups": groups}
    k3, k5 = (_event(shared, units=[{"start": "open", "end": "2026-11-07T14:40:51Z"}], observer=f"agent/{name}",
                     observed_at="2026-11-07T14:40:51Z") for name in ("K3", "K5"))
    sixteen = _assignment(shared, **base)
    seventeen = _assignment(shared, **base, events=sorted([k3, k5]), predecessor=sixteen, evidence=sorted([k3, k5]))
    _write(shared, out, "sun-epochs")
    content = json.loads((out / "sun-epochs.json").read_text())
    assert [entry["address"] for entry in content["history"]] == [sixteen, seventeen]
    assert content["history"][1]["changes"] == [] and content["history"][1]["events_added"] == sorted([k3, k5])
    assert [event["address"] for event in content["events"]] == sorted([k3, k5])
    page = (out / "sun-epochs.md").read_text()
    assert page.splitlines()[0] == "Generated by `science reservation-statement`; do not edit."
    assert "1 open, 2 reserved, 0 unresolved, 1 withheld." in page
    assert f"- Head: `{seventeen}`" in page and "version 3" in page
    assert page.count("| 2007-11-01T00:00:00Z .. 2008-12-01T00:00:00Z |") == 1
    for ref in (sixteen, k3, k5):
        assert f"`{ref}` |" in page
    _check(shared, out, chain="sun-epochs")


def _earlier_groups(content) -> list[list]:
    """Every assignment's groups, oldest first, rebuilt from the head's and the history's group lists."""
    groups = content["head"]["facet"]["groups"]
    found = [groups]
    for entry in reversed(content["history"][1:]):
        groups = [g for g in groups if g not in entry["groups_added"]] + entry["groups_removed"]
        groups = sorted(groups, key=lambda g: g["units"][0]["term"])
        found.append(groups)
    return found[::-1]


def test_history_names_a_unit_the_kernels_changes_hide(shared, out):
    """`b` loses its reservation under a change keyed by `a`; then `d` leaves `c`'s group to form its own, which
    the kernel's changes list under `c` alone."""
    steps = [[group("a", "b", role="reserved"), group("c", "d", role="withheld")],
             [group("a"), group("c", "d", role="withheld")],
             [group("a"), group("c", role="withheld"), group("d", role="reserved")]]
    ref = _assignment(shared, groups=steps[0])
    ref = _assignment(shared, groups=steps[1], predecessor=ref, evidence=["ledger:one"], flagged=[])
    _assignment(shared, groups=steps[2], predecessor=ref, evidence=["ledger:two"])
    _write(shared, out)
    content = json.loads((out / f"{CHAIN}.json").read_text())
    first, second, third = content["history"]
    assert first["groups_removed"] == first["groups_added"] == first["changes"] == []
    assert second["changes"] == [{"kind": "changed", "previous_role": "reserved", "suspended": True,
                                  "unit": {"sort": COHORT, "term": "a"}}]
    assert second["groups_removed"] == [steps[0][0]] and second["groups_added"] == [steps[1][0]]
    assert second["flagged"] == [] and "flagged" not in third
    assert [change["unit"]["term"] for change in third["changes"]] == ["c"]
    assert third["groups_removed"] == [steps[1][1]] and third["groups_added"] == steps[2][1:]
    assert _earlier_groups(content) == steps
    page = (out / f"{CHAIN}.md").read_text()
    assert 'reserved: testing/cohort a; testing/cohort b | open: testing/cohort a |' in page


def test_two_corpora_holding_one_chain_render_the_same_bytes(shared, out, tmp_path):
    """Titles are presentation, and which corpus holds the chain is not in the statement."""
    mounted = mount_config(shared)
    event = event_node(event_facet(), actor="fixture")
    root = assignment_node(assignment_facet(events=[event.id]), actor="fixture")
    for node in (event, root):
        _hold(mounted, node)
    _write(shared, out)
    both = out.with_name("both")
    for node in (event, root):
        _hold(shared, node)
    _write(shared, both)
    alone = out.with_name("alone")
    _write(dataclasses.replace(shared, world=dataclasses.replace(shared.world, corpus_roots=(shared.write_root,))), alone)
    for name in (f"{CHAIN}.json", f"{CHAIN}.md"):
        assert (out / name).read_bytes() == (both / name).read_bytes() == (alone / name).read_bytes()


def test_one_address_spelled_two_ways_renders_one_statement(shared, out):
    """The kernel's address is over NFC text, so a decomposed spelling is the same record."""
    held = {"composed": "caf\u00e9", "decomposed": "cafe\u0301"}
    rendered = []
    for name, account in held.items():
        target = {"composed": shared, "decomposed": mount_config(shared)}[name]
        _assignment(target, chain=CHAIN, account=account)
        only = dataclasses.replace(shared, write_root=target.write_root, profile=target.profile,
                                   coordination=target.coordination,
                                   world=dataclasses.replace(shared.world, corpus_roots=(target.write_root,)))
        _write(only, out / name)
        rendered.append([(out / name / f"{CHAIN}.{kind}").read_bytes() for kind in ("json", "md")])
    assert rendered[0] == rendered[1]
    assert '"account": "caf\u00e9"' in rendered[0][0].decode()  # written directly, not escaped


def test_a_respelled_predecessor_derives_the_same_changes(shared, out):
    """Each corpus holds the same two addresses; only the predecessor's spelling differs."""
    rendered = []
    for target, term in ((shared, "caf\u00e9"), (mount_config(shared), "cafe\u0301")):
        root = _assignment(target, groups=[group("a", role="reserved"), group(term)])
        _assignment(target, groups=[group("a", role="reserved"), group("caf\u00e9")], predecessor=root,
                    inputs={"roster.yaml": digest("new")}, evidence=["ledger:one"])
        only = dataclasses.replace(shared, write_root=target.write_root, profile=target.profile,
                                   coordination=target.coordination,
                                   world=dataclasses.replace(shared.world, corpus_roots=(target.write_root,)))
        _write(only, out / term)
        rendered.append((out / term / f"{CHAIN}.json").read_bytes())
    assert rendered[0] == rendered[1]
    assert json.loads(rendered[0])["history"][1]["changes"] == []


def test_considered_events_are_in_exposure_log_order(shared, out):
    logged = [_event(shared, observed_at=f"2026-11-0{day}T00:00:00Z") for day in range(1, 7)]
    assert logged != sorted(logged)
    _assignment(shared, events=sorted(logged))
    _write(shared, out)
    assert [event["address"] for event in json.loads((out / f"{CHAIN}.json").read_text())["events"]] == logged


def test_record_text_is_shown_on_the_page_and_never_interpreted(shared, out):
    event = _event(shared, account="a | b\n# c [x](y) <b> \u2028", **{"class": "a`b"})
    _assignment(shared, events=[event], groups=[group("x|y", label="*l*\n| a |")])
    _write(shared, out)
    page = (out / f"{CHAIN}.md").read_text()
    assert r"\*l\*<br>\| a \|" in page and r"testing/cohort x\|y" in page and r"a\`b" in page
    assert r"a \| b<br>\# c \[x\](y) \<b\> \\u2028" in page
    assert [line for line in page.splitlines() if line.startswith("#")] == [
        f"# Reservation: {CHAIN}", "## Frozen inputs", "## Groups", "## History", "## Considered exposure"]


# --- writing and checking -----------------------------------------------------


def test_a_written_pair_checks_and_prints_what_was_examined(shared, out):
    head = _assignment(mount_config(shared))
    report = _write(shared, out)
    text = _check(shared, out)
    printed = [f"{name}: sha256:{sha256((out / name).read_bytes()).hexdigest()}" for name in (f"{CHAIN}.json", f"{CHAIN}.md")]
    assert _section(text, "reservation statement") == [f"chain: {CHAIN}", "scope: none", f"head: {head}", *printed]
    examined = ["project: none", *sorted(
        f"corpus {corpus_id_at(target.write_root)}: no publication marker; {holds} the head"
        for target, holds in ((shared, "does not hold"), (mount_config(shared), "holds")))]
    assert _section(text, "examined") == examined
    assert [f"{k}: {v}" for k, v in report[1].pairs] == examined
    assert [f"{k}: {v}" for k, v in report[0].pairs][3:] == printed
    assert _section(text, "visible events not considered by this assignment") == ["count: 0"]
    assert sorted(path.name for path in out.iterdir()) == [f"{CHAIN}.json", f"{CHAIN}.md"]
    assert (out / f"{CHAIN}.json").stat().st_mode & 0o777 == 0o666 & ~_umask()


def _umask() -> int:
    current = os.umask(0)
    os.umask(current)
    return current


@pytest.mark.parametrize("damage,files", [
    ("json edited", [f"{CHAIN}.json"]), ("page edited", [f"{CHAIN}.md"]), ("page missing", [f"{CHAIN}.md"]),
    ("both missing", [f"{CHAIN}.json", f"{CHAIN}.md"]), ("head superseded", [f"{CHAIN}.json", f"{CHAIN}.md"]),
])
def test_a_stale_pair_refuses_naming_the_head_and_the_files(shared, out, damage, files):
    head = _assignment(shared)
    _write(shared, out)
    if "edited" in damage:
        path = out / files[0]
        path.write_text(path.read_text().replace("discovery", "Discovery"))
    elif "missing" in damage:
        for name in files:
            (out / name).unlink()
    else:
        head = _assignment(shared, predecessor=head, inputs={"roster.yaml": digest("new")})
    refusal = _refused(_check, shared, out)
    assert refusal.code == "statement-stale" and refusal.data == {"head": head, "files": files}
    _write(shared, out)
    _check(shared, out)


def test_an_interruption_between_the_replacements_is_stale_and_a_rerun_repairs_it(shared, out, monkeypatch):
    head = _assignment(shared)
    _write(shared, out)
    successor = _assignment(shared, predecessor=head, inputs={"roster.yaml": digest("new")})
    real = os.replace

    def interrupted(source, target):
        if str(target).endswith(".json"):
            raise KeyboardInterrupt
        real(source, target)

    with monkeypatch.context() as patch:
        patch.setattr("science.reservation.statement.os.replace", interrupted)
        with pytest.raises(KeyboardInterrupt):
            _write(shared, out)
    assert sorted(path.name for path in out.iterdir()) == [f"{CHAIN}.json", f"{CHAIN}.md"]
    refusal = _refused(_check, shared, out)
    assert refusal.code == "statement-stale" and refusal.data == {"head": successor, "files": [f"{CHAIN}.json"]}
    _write(shared, out)
    _check(shared, out)


def test_an_absent_chain_refuses_in_both_modes_and_leaves_the_files(shared, out):
    _assignment(shared, chain="other")
    out.mkdir()
    (out / f"{CHAIN}.json").write_text("kept")
    for call in (_check, _write):
        refusal = _refused(call, shared, out)
        assert refusal.code == "chain-absent" and refusal.data == {"chain": CHAIN, "scope": None}
    assert [path.name for path in out.iterdir()] == [f"{CHAIN}.json"] and (out / f"{CHAIN}.json").read_text() == "kept"


def test_a_scoped_chain_is_kept_beside_the_program_level_one(shared, out):
    program, scoped = _assignment(shared), _assignment(mount_config(shared), scope="proposition:shared")
    _write(shared, out)
    _write(shared, out, scope="proposition:shared")
    assert sorted(str(path.relative_to(out)) for path in out.rglob("*.*")) == [
        f"{CHAIN}.json", f"{CHAIN}.md", f"{CHAIN}/shared.json", f"{CHAIN}/shared.md"]
    assert json.loads((out / CHAIN / "shared.json").read_text())["scope"] == "proposition:shared"
    assert f"head: {program}" in _check(shared, out) and f"head: {scoped}" in _check(shared, out, scope="proposition:shared")
    (out / CHAIN / "shared.md").unlink()
    assert _refused(_check, shared, out, scope="proposition:shared").data["files"] == [f"{CHAIN}/shared.md"]


@pytest.mark.parametrize("inputs,field", [
    ({"chain": "MM"}, "chain"), ({"scope": "shared"}, "scope"), ({"scope": "proposition:a/b"}, "scope"),
    ({"scope": "proposition:.."}, "scope"), ({"as_of": "dataset:x"}, "as_of"), ({"block_on": ["guard"]}, "block_on"),
    ({"check": "docs/reservation"}, "check"),
    ({"as_of": f"reservation-assignment:{'a' * 64}", "block_on": ["open"]}, "as_of"),
    ({"as_of": f"reservation-assignment:{'a' * 64}", "all_considered": True}, "as_of"),
])
def test_a_malformed_input_refuses_before_any_record_is_read(shared, out, monkeypatch, inputs, field):
    import science.reservation.records as records
    monkeypatch.setattr(records, "captured_mounts", lambda ctx: pytest.fail("a malformed input reached the corpora"))
    refusal = _refused(_check, shared, out, **inputs)
    assert refusal.code == "invalid-input" and refusal.data == {"field": field}


@pytest.mark.parametrize("fault", ["two-heads", "malformed", "missing-predecessor", "missing-event"])
def test_a_chain_that_cannot_be_resolved_refuses_as_reservation_head_does(shared, out, fault):
    root = assignment_node(assignment_facet(), actor="fixture")
    if fault == "two-heads":
        _hold(shared, root)
        for name in "ab":
            raw_write_node(shared.write_root, assignment_node(
                assignment_facet(predecessor=root.id, inputs={"roster.yaml": digest(name)}), actor="fixture"))
    elif fault == "malformed":
        del root.facets[stored.RESERVATION_ASSIGNMENT_FACET]["rule"]
        stored.stamp_semantic_identity(root)
        raw_write_node(shared.write_root, root)
    elif fault == "missing-predecessor":
        raw_write_node(shared.write_root, assignment_node(
            assignment_facet(predecessor=root.id, inputs={"roster.yaml": digest("b")}), actor="fixture"))
    else:
        raw_write_node(shared.write_root, assignment_node(
            assignment_facet(events=[f"exposure-event:{'a' * 64}"]), actor="fixture"))
    expected = {"two-heads": "ChainAmbiguous", "malformed": "MalformedRecord"}.get(fault, "RefError")
    for call in (_check, _write):
        refusal = _refused(call, shared, out)
        assert refusal.code == "kernel-refused" and refusal.data == {"kind": expected}
    assert not out.exists()


def test_differing_copies_of_a_predecessor_refuse(shared, out):
    root = assignment_node(assignment_facet(), actor="fixture")
    for index, target in enumerate((shared, mount_config(shared))):
        _hold(target, root.model_copy(update={"title": f"copy {index}"}))
    raw_write_node(shared.write_root, assignment_node(
        assignment_facet(predecessor=root.id, inputs={"roster.yaml": digest("b")}), actor="fixture"))
    refusal = _refused(_check, shared, out)
    assert refusal.code == "invalid-input" and "copies differ" in refusal.message


def test_as_of_verifies_an_earlier_statement_even_under_a_later_fork(shared, out):
    event = _event(shared)
    root = _assignment(shared, events=[event])
    _write(shared, out)
    earlier = (out / f"{CHAIN}.json").read_bytes()
    second = _assignment(shared, events=[event], predecessor=root, inputs={"roster.yaml": digest("a")})
    assert _refused(_check, shared, out).code == "statement-stale"
    text = _check(shared, out, as_of=root)
    assert f"as of: {root}" in _section(text, "reservation statement")
    assert "visible events not considered" not in text
    raw_write_node(shared.write_root, assignment_node(
        assignment_facet(events=[event], predecessor=root, inputs={"roster.yaml": digest("b")}), actor="fixture"))
    assert _refused(_check, shared, out).data == {"kind": "ChainAmbiguous"}
    _check(shared, out, as_of=root)
    refusal = _refused(_check, shared, out, as_of=second)
    assert refusal.code == "statement-stale" and refusal.data["head"] == second
    _write(shared, out, as_of=second)
    _check(shared, out, as_of=second)
    _write(shared, out, as_of=root)
    assert (out / f"{CHAIN}.json").read_bytes() == earlier


def test_as_of_outside_the_chain_refuses(shared, out):
    _assignment(shared)
    other, scoped = _assignment(shared, chain="other"), _assignment(mount_config(shared), scope="proposition:shared")
    for as_of, data in ((other, {"field": "as_of", "chain": "other", "scope": None}),
                        (scoped, {"field": "as_of", "chain": CHAIN, "scope": "proposition:shared"}),
                        (f"reservation-assignment:{'a' * 64}", {"field": "as_of"})):
        for call in (_check, _write):
            refusal = _refused(call, shared, out, as_of=as_of)
            assert refusal.code == "invalid-input" and refusal.data == data


# --- the gate -----------------------------------------------------------------

GROUPS = [group("o"), group("r", role="reserved"), group("u", role="unresolved"), group("w", role="withheld")]
WHERE = {"open": ["o"], "reserved": ["r"], "unresolved": ["u"], "withheld": ["w"], "outside": ["new"], "unscoped": []}


def _units(place):
    return [{"sort": COHORT, "term": term} for term in WHERE[place]]


@pytest.mark.parametrize("place", WHERE)
def test_each_place_blocks_an_exposing_event_that_falls_there_and_no_other(shared, out, place):
    head = _assignment(shared, groups=GROUPS)
    _write(shared, out)
    event = _event(shared, units=_units(place))
    assert _falls(_check(shared, out)) == {event: ("program", place)}
    others = [other for other in (*WHERE, "unattributed") if other != place]
    _check(shared, out, block_on=others)
    refusal = _refused(_check, shared, out, block_on=[place])
    assert refusal.code == "events-unconsidered" and refusal.data == {"head": head, "events": [
        {"address": event, "whose": "program", "places": [place], "effect": "exposing"}]}


def test_a_non_exposing_event_blocks_only_when_every_event_must_be_considered(shared, out):
    _assignment(shared, groups=GROUPS)
    _write(shared, out)
    event = _event(shared, units=_units("reserved"), effect="non-exposing")
    _check(shared, out, block_on=list(WHERE))
    refusal = _refused(_check, shared, out, all_considered=True)
    assert [item["address"] for item in refusal.data["events"]] == [event]
    _check(shared, out, all_considered=False)


def test_a_considered_event_never_blocks(shared, out):
    _assignment(shared, groups=GROUPS, events=[_event(shared, units=_units("reserved"))])
    _write(shared, out)
    _check(shared, out, block_on=list(WHERE), all_considered=True)


def test_attribution_under_a_project(shared, out):
    """Another program's event never blocks, whatever its shape; an unclaimed one blocks only `unattributed`."""
    _assignment(shared, groups=GROUPS)
    _write(shared, out)
    own, both = _event(shared, units=_units("reserved")), _event(shared, units=_units("open"), observer="both")
    theirs = [_event(shared, units=_units("reserved"), observer="other"), _event(shared, units=[], observer="other"),
              _event(shared, units=[{"start": "open", "end": "2027-01-01T00:00:00Z"}], observer="other")]
    shadowed = _event(shared, units=_units("reserved"), observer="shadowed")
    loose = _event(shared, units=_units("open"), observer="loose", effect="non-exposing")
    ours = _project(shared, "mm", _claims(own, both), [{"addresses": [shadowed]}, {"kinds": ["dataset"]}])
    _project(shared, "sun", _claims(*theirs, both))
    text = _check(shared, out, project="mm")
    assert _falls(text) == {
        own: ("program", "reserved"), both: ("program", "open"),
        theirs[0]: ("another-program", "reserved"), theirs[1]: ("another-program", "unscoped"),
        theirs[2]: ("another-program", "nowhere"), shadowed: ("unattributed", "reserved"), loose: ("unattributed", "open")}
    (project, *_) = _section(text, "examined")
    assert re.fullmatch(rf"project: {ours}@[0-9a-f]{{32}}", project)
    assert _falls(_check(shared, out, project=ours)) == _falls(text)

    def blocked(**inputs):
        return {item["address"] for item in _refused(_check, shared, out, project="mm", **inputs).data["events"]}
    assert blocked(block_on=["reserved", "unscoped"]) == {own}
    assert blocked(all_considered=True) == {own, both}
    assert blocked(block_on=["unattributed"]) == {shadowed, loose}
    # With no project selected every visible event is the program's.
    assert {whose for whose, _ in _falls(_check(shared, out)).values()} == {"program"}
    assert len(_refused(_check, shared, out, all_considered=True).data["events"]) == 7


def test_another_programs_overlapping_interval_never_blocks(shared, out):
    epochs = [{"units": [{"start": "open", "end": "2020-01-01T00:00:00Z"}], "role": "open"},
              {"units": [{"start": "2020-01-01T00:00:00Z", "end": "open"}], "role": "reserved"}]
    _assignment(shared, groups=epochs)
    _write(shared, out)
    event = _event(shared, units=[{"start": "open", "end": "2026-01-01T00:00:00Z"}])
    _project(shared, "sun", [{"kinds": ["proposition"]}])
    _project(shared, "mm", _claims(event))
    text = _check(shared, out, project="sun", block_on=["open", "reserved", "unattributed"], all_considered=True)
    assert _falls(text) == {event: ("another-program", "open, reserved")}
    assert _refused(_check, shared, out, project="mm", block_on=["reserved"]).code == "events-unconsidered"


def test_an_ambient_selection_decides_whose_events_block_until_project_names_one(shared, out):
    """Why a preflight in a shared world names its project: the session's selection can be another program's."""
    _assignment(shared, groups=GROUPS)
    _write(shared, out)
    event = _event(shared, units=_units("reserved"))
    _project(shared, "mm", _claims(event))
    sun = CoordinationAddress.parse(_project(shared, "sun", [{"kinds": ["proposition"]}]))
    decls = tuple(decl for decl in production_tree() if decl.name == COMMAND)
    dispatcher = Dispatcher(decls, resolve_handlers(decls), ReadContext.open(shared), selection=sun)
    given = {"chain": CHAIN, "check": str(out), "block_on": ["reserved", "unattributed"]}
    assert _falls(dispatcher.invoke(COMMAND, given).text) == {event: ("another-program", "reserved")}
    assert _refused(dispatcher.invoke, COMMAND, given, project="mm").code == "events-unconsidered"


def test_an_event_recorded_and_not_claimed_passes_all_considered_and_blocks_as_unattributed(shared, out):
    """The second of two writes was interrupted: mm's present rule needs both options."""
    _assignment(shared, groups=GROUPS)
    _write(shared, out)
    event = _event(shared, units=_units("reserved"))
    _project(shared, "mm", [{"kinds": ["proposition"]}])
    _check(shared, out, project="mm", all_considered=True)
    refusal = _refused(_check, shared, out, project="mm", all_considered=True, block_on=["unattributed"])
    assert refusal.data["events"] == [{"address": event, "whose": "unattributed", "places": ["reserved"],
                                       "effect": "exposing"}]


def test_another_project_with_divergent_tips_claims_what_any_tip_claims(shared, out):
    _assignment(shared, groups=GROUPS)
    _write(shared, out)
    one, two = _event(shared, units=[], observer="one"), _event(shared, units=[], observer="two")
    _project(shared, "mm", [{"kinds": ["proposition"]}])
    sun = _project(shared, "sun", _claims(one))
    tip = ReadContext.open(shared).coordination().resolve(CoordinationAddress.parse(sun))
    with research_rig(shared, ("revise",)) as (d, _):
        query = {"version": "science.view-query.v1", "clauses": [{"all": _claims(two)}]}
        d.invoke("revise", {"address": sun, "query": yaml.safe_dump(query)})
    # A second successor of the first revision, as an independently written corpus would bring one.
    forked = f"project:{sun.removeprefix('coord:')}.{'f' * 32}"
    raw_write_node(shared.write_root, tip.model_copy(update={"uid": "f" * 32, "id": forked, "relations": [
        Relation(source=forked, predicate=stored.SUPERSEDES, target=tip.id)]}))
    text = _check(shared, out, project="mm")
    assert _falls(text) == {one: ("another-program", "unscoped"), two: ("another-program", "unscoped")}
    refusal = _refused(_check, shared, out, project="sun")
    assert refusal.code == "kernel-refused" and refusal.data["reason"] == "divergent-view"


def test_a_corpus_of_events_alone_is_examined_and_changes_the_verdict(shared, out):
    _assignment(shared, groups=GROUPS)
    _write(shared, out)
    cfg, root, profile = add_foreign_mount(shared)
    event = hold_record(root, profile, event_node(event_facet(units=_units("reserved")), actor="fixture")).id
    _check(shared, out, block_on=["reserved"])
    text = _check(cfg, out)
    corpora = [line for line in _section(text, "examined") if line.startswith("corpus ")]
    assert f"corpus {corpus_id_at(root)}: no publication marker; does not hold the head" in corpora and len(corpora) == 3
    refusal = _refused(_check, cfg, out, block_on=["reserved"])
    assert [item["address"] for item in refusal.data["events"]] == [event]


def test_a_stale_pair_refuses_before_the_gate(shared, out):
    _assignment(shared, groups=GROUPS)
    _event(shared, units=_units("reserved"))
    assert _refused(_check, shared, out, block_on=["reserved"]).code == "statement-stale"
