"""A program's statement from author to reader: published, adopted and checked against the clone."""
from __future__ import annotations

import dataclasses
import re

import pytest
import yaml
from helpers.commons import (
    LOC_A, Installations, a_identity, read_rig, step_adopted, step_bound, step_published,
    step_reopened,
)
from helpers.reservation import assignment_facet, assignment_node, digest, event_facet, event_node, group, hold_record
from helpers.world import open_rig
from science.commands.reservation_statement import write
from science.config import ReadContext, corpus_id_at
from science.refusal import Refused
from science.world_belief import publish_session_epoch

CHAIN, COMMAND = "mm-roster", "reservation-statement"
GROUPS = [group("held-cohort", role="reserved"), group("open-cohort")]
RULE = {"block_on": ["reserved", "withheld", "unscoped", "unattributed"]}


def _hold(cfg, node):
    return hold_record(cfg.write_root, cfg.profile, node).id


def _event(cfg, term, **changes):
    units = [{"sort": "testing/cohort", "term": term}]
    return _hold(cfg, event_node(event_facet(units=units, **changes), actor="fixture"))


def _claim(cfg, *clauses):
    """Revise A's project: the fixture's own clauses, then one clause of predicates per argument."""
    ctx = ReadContext.open(cfg)
    ((address, node),) = ctx.coordination().standing("project").items()
    from science.coordination import content_of
    query = yaml.safe_load(yaml.safe_dump(content_of(node)["query"]))
    query["clauses"] = [*query["clauses"], *({"all": list(clause)} for clause in clauses)]
    with open_rig(cfg, ("revise",)) as (d, _):
        d.invoke("revise", {"address": str(address), "query": yaml.safe_dump(query)})


def _section(text, title):
    lines = text.splitlines()
    start = lines.index(f"{title}:") + 1
    end = next((i for i in range(start, len(lines)) if not lines[i].startswith("  ")), len(lines))
    return [line.strip() for line in lines[start:end]]


def _check(cfg, out, *, project=None, **inputs):
    return read_rig(cfg, COMMAND).invoke(COMMAND, {"chain": CHAIN, "check": str(out), **inputs}, project=project).text


def _preview(cfg):
    publish_session_epoch(cfg)
    return read_rig(cfg, "publish-preview").invoke("publish-preview", {"target": "a", "to": LOC_A}).text


def _adopt(installations, work) -> Installations:
    value = {field.name: getattr(installations, field.name) for field in dataclasses.fields(installations)}
    for step in (step_published, step_bound, step_adopted, step_reopened):
        value = step(work, value)
    return Installations.of(value)


def _authored(cfg, out, term, **changes):
    """A head with one considered event, then an unconsidered event over `term`; both claimed; files written."""
    considered = _event(cfg, "open-cohort", observer="earlier")
    head = _hold(cfg, assignment_node(assignment_facet(groups=GROUPS, events=[considered]), actor="fixture"))
    later = _event(cfg, term, **changes)
    _claim(cfg, [{"addresses": sorted([head, considered, later])}])
    write(ReadContext.open(cfg), chain=CHAIN, directory=out)
    return head, later


def test_author_and_reader_pass_on_the_same_event(fresh, tmp_path):
    out = tmp_path / "reservation"
    head, later = _authored(fresh.a, out, "open-cohort")
    author = _check(fresh.a, out, project="a", **RULE)
    preview = _preview(fresh.a)
    assert f"record: {later}" in _section(preview, "selection")
    assert _section(preview, "exposure claims") == ["status: equal to the selected events", "events: 2"]
    reader = _adopt(fresh, tmp_path.parent)
    text = _check(reader.b, out, **RULE)
    assert _section(text, later) == _section(author, later)
    assert _section(text, later)[:2] == ["whose: program", "falls: open"]
    ids = a_identity(fresh.a)
    assert f"corpus {ids['corpus_id']}: publication marker {ids['marker']}; holds the head" in _section(text, "examined")
    own = corpus_id_at(fresh.a.write_root)
    assert f"corpus {own}: no publication marker; holds the head" in _section(author, "examined")
    # The author's printed revision is the one the preview froze.
    (revision,) = re.findall(r"project: (coord:[0-9a-f]{32}@[0-9a-f]{32})", author)
    assert f"publish {revision} to" in preview
    assert _section(text, "reservation statement") == _section(author, "reservation statement")

    successor = _hold(fresh.a, assignment_node(assignment_facet(
        groups=GROUPS, events=[], predecessor=head, inputs={"roster.yaml": digest("new")}), actor="fixture"))
    with pytest.raises(Refused) as stale:
        _check(fresh.a, out)
    assert stale.value.refusal.code == "statement-stale" and stale.value.refusal.data["head"] == successor
    older = _check(reader.b, out, **RULE)  # yesterday's publication, today's producer
    assert f"head: {head}" in _section(older, "reservation statement")
    assert any(ids["marker"] in line for line in _section(older, "examined"))


def test_author_and_reader_refuse_identically(fresh, tmp_path):
    """Constructed: the procedure publishes only when the author's own gate passes."""
    out = tmp_path / "reservation"
    _, later = _authored(fresh.a, out, "held-cohort")

    def refusal(cfg, **inputs):
        with pytest.raises(Refused) as caught:
            _check(cfg, out, **RULE, **inputs)
        return caught.value.refusal
    author = refusal(fresh.a, project="a")
    assert author.code == "events-unconsidered" and [item["address"] for item in author.data["events"]] == [later]
    publish_session_epoch(fresh.a)
    assert refusal(_adopt(fresh, tmp_path.parent).b) == author


def test_the_preview_reports_an_event_selected_and_not_claimed(fresh, tmp_path):
    """Two `addresses` predicates of one clause intersect on the event: published, and claimed by no clause."""
    one, two, three = (_event(fresh.a, "open-cohort", observer=name) for name in ("one", "two", "three"))
    _claim(fresh.a, [{"addresses": sorted([one, two])}, {"addresses": sorted([one, three])}], [{"addresses": [two]}])
    preview = _preview(fresh.a)
    assert f"record: {one}" in _section(preview, "selection") and f"record: {three}" not in _section(preview, "selection")
    assert _section(preview, "exposure claims") == ["status: differ from the selected events",
                                                    f"selected and not claimed: {one}"]


def test_an_event_named_beside_another_predicate_is_neither_claimed_nor_selected(fresh, tmp_path):
    event = _event(fresh.a, "open-cohort")
    _claim(fresh.a, [{"addresses": [event]}, {"kinds": ["dataset"]}])
    preview = _preview(fresh.a)
    assert f"record: {event}" not in _section(preview, "selection")
    assert _section(preview, "exposure claims") == ["status: equal to the selected events", "events: 0"]
