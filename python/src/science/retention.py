"""The live inputs and publication history that prevent retirement."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from beliefs import stored
from beliefs.corpus import ReadView
from beliefs.profile import ProfileSpec
from beliefs.publish_request import closure_missing
from beliefs.world.registry import content_identity

from science.supersession import Held, chain


@dataclass(frozen=True)
class Reason:
    kind: Literal["configuration", "chain", "attribution", "dependency"]
    detail: tuple[str, ...]


Holder = tuple[str, ReadView, ProfileSpec]


def dependency_closure(write_root: Holder, holders: Sequence[Holder]) -> frozenset[str]:
    available = (write_root, *holders)
    pending = [node.id for node in write_root[1].iter_stored()]
    reached: set[str] = set()
    while pending:
        address = pending.pop()
        if address in reached:
            continue
        reached.add(address)
        holding = next((holder for holder in available if holder[1].holds(address)), None)
        if holding is None:
            continue
        _, view, profile = holding
        node = view.get(address)
        pending.extend(closure_missing(view, (address,)))
        if node.kind == "assessment":
            assessment = stored.assessment_value(node, profile=profile)
            pending.extend((stored.typed_ref("analysis-spec", assessment.spec),
                            stored.typed_ref("run", assessment.run), assessment.proposition))
        elif node.kind == "run":
            if spec := stored.run_spec(node):
                pending.append(stored.typed_ref("analysis-spec", spec))
        elif node.kind == "verification":
            pending.extend(stored.verification_derivation(node) or ())
        elif node.kind == "analysis-spec":
            spec = stored.analysis_spec_value(node, profile=profile)
            pending.append(spec.target)
            pending.extend(role.dataset for role in spec.input_roles)
        elif node.kind == "retraction":
            pending.extend(relation.target for relation in node.relations if relation.predicate == stored.RETRACTS)
    return frozenset(reached)


def required(predecessor: Held, *, keep: Sequence[str], group_chain: Sequence[Held], tip: tuple[str, str],
             mounted: Sequence[Held], write_root: Holder, live: Sequence[Holder]) -> tuple[Reason, ...]:
    closure = dependency_closure(write_root, live)
    holders = {corpus: view for corpus, view, _ in (write_root, *live)}

    def direct(item: Held) -> tuple[Reason, ...]:
        reasons = []
        if item.corpus_id in keep:
            reasons.append(Reason("configuration", ()))
        naming = {other.corpus_id for other in mounted if other.state == "mounted"
                  and any(origin == item.corpus_id for origin, _ in other.marker.attributions.values())}
        reasons.extend(Reason("attribution", (corpus,)) for corpus in sorted(naming))
        dependencies = []
        view = holders.get(item.corpus_id)
        if view is not None:
            for address in sorted(closure):
                if not view.holds(address):
                    continue
                identity = content_identity(view.get(address))
                if not any(other.holds(address) and content_identity(other.get(address)) == identity
                           for corpus, other in holders.items() if corpus != item.corpus_id):
                    dependencies.append(address)
        if dependencies:
            reasons.append(Reason("dependency", tuple(dependencies)))
        return tuple(reasons)

    own = direct(predecessor)
    pair = predecessor.corpus_id, predecessor.marker.uid
    retained_for = []
    for older in group_chain:
        if older.state != "mounted" or not direct(older):
            continue
        path = chain((older.corpus_id, older.marker.uid), tip, group_chain)
        if path is not None and pair in path[1:-1]:
            retained_for.append(older.corpus_id)
    return (tuple(reason for reason in own if reason.kind == "configuration")
            + tuple(Reason("chain", (corpus,)) for corpus in sorted(set(retained_for)))
            + tuple(reason for reason in own if reason.kind != "configuration"))
