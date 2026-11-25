"""Where an event falls against an assignment's groups: pure values, no world."""
from __future__ import annotations

import pytest
from beliefs.reservation import exposure_event_from_facet, reservation_assignment_from_facet
from beliefs.view_query import parse_view_query
from helpers.reservation import assignment_facet, event_facet, group
from science.reservation.attribution import claimed_events, differing_events
from science.reservation.gate import gate_of
from science.reservation.placement import places
from science.refusal import Refused

T = "{}-01-01T00:00:00Z".format


def _event(units):
    return exposure_event_from_facet({**event_facet(units=units), "recorded_by": "fixture"})


def _assignment(groups):
    return reservation_assignment_from_facet({**assignment_facet(groups=groups), "assigned_by": "fixture"})


def _intervals(*spans):
    return _assignment([{"units": [{"start": start, "end": end}], "role": role} for start, end, role in spans])


TERMS = _assignment([group("a", "b", role="reserved"), group("c"), group("d", role="unresolved"),
                     group("\u00e9", role="withheld")])
EPOCHS = _intervals(("open", T(2000), "open"), (T(2000), T(2005), "withheld"), (T(2005), T(2010), "reserved"),
                    (T(2012), T(2014), "open"))


def _terms(*names, sort="testing/cohort"):
    return [{"sort": sort, "term": name} for name in names]


@pytest.mark.parametrize("units,expected", [
    (_terms("b"), ("reserved",)),
    (_terms("a", "c", "d"), ("open", "reserved", "unresolved")),
    (_terms("new"), ("outside",)),
    (_terms("b", "new"), ("reserved", "outside")),
    (_terms("a", sort="testing/other"), ()),
    ([*_terms("a"), *_terms("a", sort="testing/other")], ("reserved",)),
    (_terms("e\u0301"), ("withheld",)),
    ([], ("unscoped",)),
    ([{"start": T(2000), "end": T(2001)}], ()),
])
def test_a_term_event_falls_where_its_terms_are(units, expected):
    assert places(_event(units), TERMS) == expected


@pytest.mark.parametrize("start,end,expected", [
    (T(2001), T(2002), ("withheld",)),
    (T(2005), T(2010), ("reserved",)),                          # touches both neighbours, overlaps neither
    (T(2000), T(2005), ("withheld",)),
    (T(2004), T(2006), ("reserved", "withheld")),
    (T(2010), T(2012), ("outside",)),                           # fills the gap exactly
    (T(2009), T(2011), ("reserved", "outside")),                # partly outside
    (T(2009), T(2013), ("open", "reserved", "outside")),        # the gap lies between two groups
    (T(2014), "open", ("outside",)),
    (T(2013), "open", ("open", "outside")),
    ("open", T(1990), ("open",)),
    ("open", T(2000), ("open",)),
    ("open", T(2007), ("open", "reserved", "withheld")),
    (T(2012), T(2014), ("open",)),
])
def test_an_interval_event_falls_where_its_half_open_interval_overlaps(start, end, expected):
    assert places(_event([{"start": start, "end": end}]), EPOCHS) == expected


def test_groups_open_at_both_ends_of_time_leave_nothing_outside():
    whole = _intervals(("open", T(2000), "open"), (T(2000), "open", "reserved"))
    assert places(_event([{"start": "open", "end": T(2030)}]), whole) == ("open", "reserved")
    assert places(_event([{"start": T(1990), "end": "open"}]), whole) == ("open", "reserved")


def test_a_term_event_against_interval_groups_falls_nowhere():
    assert places(_event(_terms("a")), EPOCHS) == ()


def _query(*clauses):
    return parse_view_query({"version": "science.view-query.v1", "clauses": [{"all": list(c)} for c in clauses]})


E, X, Y = (f"exposure-event:{n * 64}" for n in "abc")


@pytest.mark.parametrize("clauses,claimed", [
    ([[{"addresses": [E, "dataset:d"]}]], {E}),
    ([[{"addresses": [E]}, {"kinds": ["dataset"]}]], set()),
    ([[{"addresses": [E, X]}, {"addresses": [E, Y]}]], set()),
    ([[{"addresses": [E, X]}, {"addresses": [E, Y]}], [{"addresses": [Y]}]], {Y}),
    ([[{"kinds": ["dataset"]}]], set()),
])
def test_a_claim_is_an_address_in_an_addresses_only_clause(clauses, claimed):
    assert claimed_events(_query(*clauses)) == claimed


def test_selected_and_claimed_events_are_compared_both_ways():
    intersecting = _query([{"addresses": [E, X]}, {"addresses": [E, Y]}])
    assert differing_events(intersecting, [E, "dataset:d"]) == ((E,), ())
    assert differing_events(_query([{"addresses": [E, X]}]), [E, "dataset:d"]) == ((), (X,))
    assert differing_events(_query([{"addresses": [E]}]), [E, "dataset:d"]) == ((), ())


def test_a_place_no_gate_knows_refuses():
    with pytest.raises(Refused) as caught:
        gate_of(["reserved", "guard"], False)
    assert caught.value.refusal.code == "invalid-input" and caught.value.refusal.data == {"field": "block_on"}
