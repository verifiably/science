"""Resolution snapshots over an explicitly scoped inventory and held bytes."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from hashlib import sha256
from pathlib import Path
import re

from nodes.core.node import Node
from beliefs import stored
from beliefs.claim import Referent
from beliefs.contract.domain import DatasetBinding, SelectionBinding, RunOutputBinding, WorldKindBinding
from beliefs.profile import ProfileSpec
from beliefs.resolution import BindingCheckReceipt, ResolutionSnapshot, build_snapshot
from science.holdings import held_path_for
from science.refusal import Refusal, Refused

__all__ = ["dataset_bound_sorts", "snapshot", "require_performed"]


def dataset_bound_sorts(profile: ProfileSpec) -> dict[str, DatasetBinding]:
    result = {}
    for term, compiled in profile.sorts.items():
        binding = compiled.binding
        if isinstance(binding, DatasetBinding):
            result[term] = binding
        elif isinstance(binding, SelectionBinding):
            result[term] = DatasetBinding(dataset=binding.selected)
        elif isinstance(binding, RunOutputBinding):
            result[term] = DatasetBinding(dataset=binding.dataset)
    return result


def snapshot(profile: ProfileSpec, nodes: Iterable[Node], stores: Mapping[str, Path], observations) -> ResolutionSnapshot:
    inventory = tuple(nodes)
    datasets = {node.id: node for node in inventory if node.kind == "dataset"}
    readable, unreadable = {}, []
    for binding in sorted(set(dataset_bound_sorts(profile).values()), key=lambda b: b.dataset):
        address = binding.dataset
        node = datasets.get(address)
        if node is None:
            unreadable.append(binding)
            continue
        resources = stored.dataset_declaration(node).resources
        if len(resources) != 1:
            raise Refused(Refusal("invalid-input", f"vocabulary {address} requires exactly one resource"))
        if address not in observations:
            unreadable.append(binding)
            continue
        try:
            content = held_path_for(stores, observations[address]).read_bytes()
            if "sha256:" + sha256(content).hexdigest() != resources[0].digest:
                unreadable.append(binding)
                continue
            readable[binding] = content.decode("utf-8").splitlines()
        except (OSError, UnicodeError) as caught:
            raise Refused(Refusal("invalid-input", f"vocabulary {address} cannot be read: {caught}",
                                  {"kind": type(caught).__name__, "dataset": address})) from caught
    bound_kinds = {s.binding.world_kind for s in profile.sorts.values() if isinstance(s.binding, WorldKindBinding)}
    kinds = {kind: tuple(node.id for node in inventory
                        if node.kind == kind and re.fullmatch(re.escape(kind) + r":[0-9a-f]{64}", node.id))
             for kind in sorted(bound_kinds)}
    return build_snapshot(readable=readable, unreadable=unreadable, kinds=kinds)


def require_performed(profile: ProfileSpec, receipt: BindingCheckReceipt, referents: Mapping[str, Referent]) -> None:
    bound = dataset_bound_sorts(profile)
    for label, outcome in receipt.outcomes.items():
        ref = referents[label]
        binding = profile.sorts[ref.sort].binding
        if ref.sort in bound and not outcome.performed:
            address = bound[ref.sort].dataset
            raise Refused(Refusal("invalid-input", f"sort {ref.sort} binds vocabulary {address}, which is not "
                                  "held here; hold it with `dataset` before authoring under it",
                                  {"sort": ref.sort, "dataset": address, "outcome": outcome.value}))
        if isinstance(binding, WorldKindBinding) and not outcome.performed:
            raise Refused(Refusal("invalid-input", f"sort {ref.sort} requires held {binding.world_kind} records",
                                  {"sort": ref.sort, "outcome": outcome.value}))
