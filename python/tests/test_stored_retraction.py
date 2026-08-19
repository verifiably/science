from __future__ import annotations

import dataclasses

import pytest

from science import stored
from science.errors import MalformedRecord

TARGET = stored.NodeTarget(
    ref="assessment:a1",
    resolved="assessment:a1",
    content_identity="sha256:" + "ab" * 32,
)


def retraction(**changes: object):
    arguments = {
        "title": "r",
        "target": TARGET,
        "reason": "defective-code",
        "rationale": "why",
        "grounds": ("verification:v1",),
        "actor": "keith",
        "event_token": "tok",
    }
    arguments.update(changes)
    return stored.retraction_node(**arguments)  # type: ignore[arg-type]


def test_retraction_node_derives_relations_from_one_argument():
    node = retraction()

    assert [(relation.source, relation.predicate, relation.target) for relation in node.relations] == [
        (node.id, "retracts", "assessment:a1"),
        (node.id, "grounded-in", "verification:v1"),
    ]
    assert node.facets[stored.RETRACTION_FACET] == {
        "target": {
            "arm": "node",
            "ref": "assessment:a1",
            "resolved": "assessment:a1",
            "content_identity": "sha256:" + "ab" * 32,
        },
        "reason": "defective-code",
        "rationale": "why",
        "grounds": ["verification:v1"],
        "actor": "keith",
        "event_token": "tok",
    }
    assert not stored.semantic_hash_missing(node)


def test_retraction_id_is_the_full_content_digest():
    first = retraction()
    repeated = retraction()

    assert first.id == repeated.id
    assert first.id == "retraction:47005267cbc432bec897fee210624a90e24e4744d7f9dca3482f6d6a268e5a02"


@pytest.mark.parametrize(
    "change",
    [
        {"target": dataclasses.replace(TARGET, content_identity="sha256:" + "cd" * 32)},
        {"reason": "authored-error"},
        {"rationale": "different"},
        {"grounds": ("verification:v2",)},
        {"actor": "other"},
        {"event_token": "tok-2"},
        {"successor": "assessment:a2"},
    ],
)
def test_each_retraction_identity_field_moves_the_id(change):
    assert retraction(**change).id != retraction().id


def test_retraction_reason_outside_closed_vocabulary_refuses():
    with pytest.raises(MalformedRecord):
        retraction(reason="vibes")


@pytest.mark.parametrize("change", [{"actor": ""}, {"event_token": ""}])
def test_retraction_missing_attribution_refuses(change):
    with pytest.raises(MalformedRecord):
        retraction(**change)


def test_retraction_empty_grounds_refuses():
    with pytest.raises(MalformedRecord):
        retraction(grounds=())


def test_retraction_non_string_rationale_refuses():
    with pytest.raises(MalformedRecord):
        retraction(rationale=1)


def test_retraction_non_string_ground_refuses():
    with pytest.raises(MalformedRecord):
        retraction(grounds=("verification:v1", 1))


def test_retraction_unknown_target_arm_refuses():
    with pytest.raises(MalformedRecord):
        retraction(target={"arm": "future"})


def test_route_target_carries_route_identity():
    node = retraction(
        target=stored.RouteTarget(
            dataset="dataset:d1",
            resolved="dataset:d1",
            content_identity="sha256:" + "cd" * 32,
            route_identity="route-identity",
        )
    )

    assert node.facets[stored.RETRACTION_FACET]["target"] == {
        "arm": "route",
        "dataset": "dataset:d1",
        "resolved": "dataset:d1",
        "content_identity": "sha256:" + "cd" * 32,
        "route_identity": "route-identity",
    }


def test_successor_derives_succeeded_by_relation():
    node = retraction(grounds=("verification:v1", "source:s1"), successor="assessment:a2")

    assert [(relation.predicate, relation.target) for relation in node.relations] == [
        ("retracts", "assessment:a1"),
        ("grounded-in", "verification:v1"),
        ("grounded-in", "source:s1"),
        ("succeeded-by", "assessment:a2"),
    ]
    assert node.facets[stored.RETRACTION_FACET]["successor"] == "assessment:a2"


def test_retraction_facet_is_wholly_covered():
    node = retraction()

    assert stored.COVERED_FACETS["retraction"] == (stored.RETRACTION_FACET,)
    node.facets[stored.RETRACTION_FACET]["rationale"] = "changed"
    assert stored.semantic_hash_disagrees(node)


def test_retraction_target_values_are_frozen_and_exact():
    assert [field.name for field in dataclasses.fields(stored.NodeTarget)] == [
        "ref",
        "resolved",
        "content_identity",
    ]
    assert [field.name for field in dataclasses.fields(stored.RouteTarget)] == [
        "dataset",
        "resolved",
        "content_identity",
        "route_identity",
    ]
    assert stored.NodeTarget.__dataclass_params__.frozen
    assert stored.RouteTarget.__dataclass_params__.frozen


def test_retraction_vocabulary_is_frozen_exactly():
    assert stored.RETRACTION_REASONS == (
        "authored-error",
        "corrupt-input",
        "defective-code",
        "environment-miscapture",
        "false-certification",
        "upstream-retraction",
        "wrong-route",
    )
