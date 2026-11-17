"""Membership uses the native underlying dataset and an explicit node inventory."""
from dataclasses import replace
from hashlib import sha256

import pytest
from beliefs import stored
from beliefs.contract.domain import parse_domain_contract
from beliefs.dataset import ByteObservation
from beliefs.profile import compile_profile, shipped_base_contract
from beliefs.resolution import TermOutcome, build_snapshot
from science.refusal import Refused


def profile_for(binding):
    base = shipped_base_contract()
    sort = {"binding": binding}
    if binding["kind"] != "world-kind":
        sort["identifier_class"] = {"prefix": "EX", "pattern": "EX:.+"}
    contract = parse_domain_contract({"contract": "vocab", "version": 1, "lineage": "genesis",
        "sorts": {"item": sort}, "dimensions": {}}, source="<test>", base=base, predecessor=None)
    return compile_profile(base, [contract])


@pytest.fixture
def vocabulary(tmp_path):
    content = b"EX:a\nEX:b\n"
    digest = "sha256:" + sha256(content).hexdigest()
    node = stored.dataset_node(title="vocabulary", resources=[{"name": "terms.txt", "digest": digest}])
    (tmp_path / "terms.txt").write_bytes(content)
    observations = {node.id: (ByteObservation(digest, "store:" + "1" * 32 + ":terms.txt"),)}
    return node, {"1" * 32: tmp_path}, observations


@pytest.mark.parametrize("arm", ["dataset", "selection", "run-output"])
def test_dataset_backed_arms_use_the_underlying_dataset(vocabulary, arm):
    from science.vocabulary import snapshot, dataset_bound_sorts
    node, stores, observations = vocabulary
    binding = {"kind": arm, "dataset": node.id}
    if arm == "selection":
        binding.update(dataset="dataset:sha256:" + "a" * 64, selected=node.id,
                       rule="classification-rule:" + "b" * 64, annotator="fixture")
    if arm == "run-output":
        binding["run"] = "run:" + "c" * 64
    profile = profile_for(binding)
    assert dataset_bound_sorts(profile)["vocab/item"].dataset == node.id
    found = snapshot(profile, iter((node,)), stores, observations)
    assert found.resolve(profile.sorts["vocab/item"], "EX:a") is TermOutcome.MEMBER
    assert found.resolve(profile.sorts["vocab/item"], "EX:missing") is TermOutcome.NOT_MEMBER
    assert snapshot(profile, (), stores, observations).resolve(profile.sorts["vocab/item"], "EX:a") is TermOutcome.NOT_AVAILABLE


@pytest.mark.parametrize("outcome", ["not-consulted", "not-present", "not-available"])
def test_unperformed_dataset_membership_cannot_author(vocabulary, outcome):
    from science.vocabulary import require_performed
    from beliefs.claim import Referent
    from types import SimpleNamespace
    node, _, _ = vocabulary
    profile = profile_for({"kind": "dataset", "dataset": node.id})
    # The boundary consumes receipt outcomes; all three public kernel states
    # must have the same heldness consequence, irrespective of their source.
    receipt = SimpleNamespace(outcomes={"role:x": TermOutcome(outcome)})
    with pytest.raises(Refused, match=node.id):
        require_performed(profile, receipt, {"role:x": Referent("vocab/item", "EX:a")})


@pytest.mark.parametrize("resources", [[], [{"name": "a"}, {"name": "b"}]])
def test_vocabulary_requires_exactly_one_resource(vocabulary, resources):
    from science.vocabulary import snapshot
    node, stores, observations = vocabulary
    # Preserve the declared address as the sort's vocabulary key; malformed
    # resource count must refuse before attempting bytes, even without holdings.
    node = node.model_copy(deep=True)
    node.facets["dataset"]["resources"] = resources
    profile = profile_for({"kind": "dataset", "dataset": node.id})
    with pytest.raises(Refused, match="one resource"):
        snapshot(profile, (node,), stores, observations)


@pytest.mark.parametrize("damage", ["digest", "utf8", "io"])
def test_selected_vocabulary_failure_never_retries_another_copy(vocabulary, tmp_path, damage):
    from science.vocabulary import snapshot
    node, stores, observations = vocabulary
    profile = profile_for({"kind": "dataset", "dataset": node.id})
    good = tmp_path / "good"
    good.mkdir()
    (good / "terms.txt").write_bytes((tmp_path / "terms.txt").read_bytes())
    digest = observations[node.id][0].digest
    observations[node.id] += (ByteObservation(digest, "store:" + "2" * 32 + ":terms.txt"),)
    stores["2" * 32] = good
    if damage == "io":
        (tmp_path / "terms.txt").unlink()
    else:
        content = b"corrupt" if damage == "digest" else b"\xff"
        (tmp_path / "terms.txt").write_bytes(content)
        if damage == "utf8":
            digest = "sha256:" + sha256(content).hexdigest()
            # Keep a real matching digest to reach the encoding boundary.
            node = stored.dataset_node(title="utf8", resources=[{"name": "terms.txt", "digest": digest}])
            profile = profile_for({"kind": "dataset", "dataset": node.id})
            observations = {node.id: (ByteObservation(digest, "store:" + "1" * 32 + ":terms.txt"),)}
    if damage == "digest":
        assert snapshot(profile, (node,), stores, observations).resolve(profile.sorts["vocab/item"], "EX:a") is TermOutcome.NOT_AVAILABLE
    else:
        with pytest.raises(Refused):
            snapshot(profile, (node,), stores, observations)


def test_world_kind_inventory_ignores_slugs_and_unbound_kinds():
    from science.vocabulary import snapshot
    from nodes.core.node import Node
    profile = profile_for({"kind": "world-kind", "world_kind": "proposition"})
    empty = snapshot(profile, (), {}, {})
    slug = Node(id="proposition:p1", kind="proposition", title="slug")
    unrelated = Node(id="source:" + "a" * 64, kind="source", title="other kind")
    omitted = snapshot(profile, (slug, unrelated), {}, {})
    assert empty.identity == omitted.identity
    assert set(omitted.kinds) == {"proposition"}
    canonical = "proposition:" + "b" * 64
    assert omitted.resolve(profile.sorts["vocab/item"], canonical) is TermOutcome.NOT_MEMBER
    found = snapshot(profile, (slug, unrelated, Node(id=canonical, kind="proposition", title="member")), {}, {})
    assert found.resolve(profile.sorts["vocab/item"], canonical) is TermOutcome.MEMBER
