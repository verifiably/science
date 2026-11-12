"""The live inputs and publication history that prevent retirement."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Literal

from beliefs import stored
from beliefs.corpus import ReadView
from beliefs.dataset import ByteObservation, dataset_address
from beliefs.dependencies import record_references
from beliefs.errors import ScienceError
from beliefs.estimand import DatasetBinding
from beliefs.procedure import Procedure, procedure_from_stored
from beliefs.referent_mapping import mapping_from_stored
from beliefs.proxy_model import proxy_from_stored
from beliefs.classification_rule import rule_from_stored
from beliefs.register import register_from_stored
from beliefs.profile import ProfileSpec
from beliefs.publish_request import closure_missing
from beliefs.world.registry import content_identity
from beliefs.root import open_world_read

from science.supersession import Held, chain
from science.holdings import found_observations


@dataclass(frozen=True)
class Reason:
    kind: Literal["configuration", "chain", "attribution", "dependency"]
    detail: tuple[str, ...]


Holder = tuple[str, ReadView, ProfileSpec]


@dataclass(frozen=True)
class DependencyClosure:
    addresses: frozenset[str]
    unresolved: tuple[str, ...]


def live_observations(world_config, mounts):
    """Reduce the supplied live carriers, including publications admitted this invocation."""
    current = open_world_read(replace(world_config, corpus_roots=tuple(m.root for m in mounts)))
    return found_observations([(m.corpus_id, m.view) for m in mounts], current)


_RECORD_READERS = {
    "procedure": procedure_from_stored,
    "referent-mapping": mapping_from_stored,
    "proxy-model": proxy_from_stored,
    "classification-rule": rule_from_stored,
    "assumptions-register": register_from_stored,
}


def _references(node, profile):
    references, digests = set(), set()
    target = None
    if node.kind == "assessment":
        assessment = stored.assessment_value(node, profile=profile)
        references.update((stored.typed_ref("analysis-spec", assessment.spec),
                           stored.typed_ref("run", assessment.run), assessment.proposition))
        target = assessment.target
    elif node.kind == "analysis-spec":
        spec = stored.analysis_spec_value(node, profile=profile)
        references.add(spec.target)
        references.update(role.dataset for role in spec.input_roles)
        references.update(spec.registers)
        references.update(binding.procedure for binding in spec.rule_bindings if binding.procedure is not None)
        target = spec.assessed_target
    elif node.kind == "run":
        if spec := stored.run_spec(node):
            references.add(stored.typed_ref("analysis-spec", spec))
    elif node.kind == "verification":
        references.update(stored.verification_derivation(node) or ())
    elif node.kind == "retraction":
        references.update(r.target for r in node.relations if r.predicate == stored.RETRACTS)
    elif node.kind in _RECORD_READERS:
        value = _RECORD_READERS[node.kind](node)
        references.update(record_references(value, profile))
        if isinstance(value, Procedure) and value.inputs is not None:
            digests.update((*value.inputs.datasets, *value.inputs.code))
    if target is not None:
        references.update(d.id for d in target.dependencies)
        if target.model is not None:
            references.add(target.model)
        digests.update(b.digest for b in target.estimand.bindings.values() if isinstance(b, DatasetBinding))
    return references, digests


def dependency_closure(write_root: Holder, holders: Sequence[Holder], *,
                       observations: Mapping[str, tuple[ByteObservation, ...]]) -> DependencyClosure:
    # Custody keeps frozen provenance even when a reader rejects or retracts it.
    available = (write_root, *holders)
    pending = [node.id for node in write_root[1].iter_stored()]
    reached, unresolved, digest_reads = set(), set(), set()

    def include_digest(digest):
        if digest in digest_reads:
            return
        digest_reads.add(digest)
        observed = {address for address, values in observations.items() if any(o.digest == digest for o in values)}
        matches = set()
        for _, view, _ in available:
            for node in view.iter_stored():
                if node.kind != "dataset":
                    continue
                try:
                    if dataset_address(stored.dataset_declaration(node)) in observed:
                        matches.add(node.id)
                except ScienceError as error:
                    unresolved.add(f"unresolved-reference {node.id} ({type(error).__name__}: {error})")
        pending.extend(matches)
        if not matches:
            unresolved.add(f"unresolved-digest {digest}")

    while pending:
        address = pending.pop()
        if address in reached:
            continue
        reached.add(address)
        copies = []
        for cid, view, profile in available:
            if not view.holds(address):
                continue
            try:
                copies.append((cid, view, profile, view.get(address)))
            except (ScienceError, OSError) as error:
                unresolved.add(f"unresolved-reference {address} holder {cid} ({type(error).__name__}: {error})")
        if not copies:
            unresolved.add(f"unresolved-reference {address}")
            continue
        if len({(node.id, content_identity(node)) for _, _, _, node in copies}) > 1:
            unresolved.add(f"unresolved-copy {address} holders: {', '.join(sorted({cid for cid, _, _, _ in copies}))}")
            continue
        _, view, profile, node = min(copies, key=lambda copy: copy[0])
        reached.add(node.id)
        try:
            pending.extend(closure_missing(view, (node.id,)))
            references, digests = _references(node, profile)
            pending.extend(references)
            for digest in sorted(digests):
                include_digest(digest)
        except (ScienceError, ValueError, KeyError, OSError) as error:
            unresolved.add(f"unresolved-reference {address} ({type(error).__name__}: {error})")
    return DependencyClosure(frozenset(reached), tuple(sorted(unresolved)))


def required(predecessor: Held, *, keep: Sequence[str], group_chain: Sequence[Held], tip: tuple[str, str],
             mounted: Sequence[Held], write_root: Holder, live: Sequence[Holder],
             observations: Mapping[str, tuple[ByteObservation, ...]]) -> tuple[Reason, ...]:
    closure = dependency_closure(write_root, live, observations=observations)
    holders = {corpus: view for corpus, view, _ in (write_root, *live)}

    def direct(item: Held) -> tuple[Reason, ...]:
        reasons = []
        if item.corpus_id in keep:
            reasons.append(Reason("configuration", ()))
        naming = {other.corpus_id for other in mounted if other.state == "mounted"
                  and any(origin == item.corpus_id for origin, _ in other.marker.attributions.values())}
        reasons.extend(Reason("attribution", (corpus,)) for corpus in sorted(naming))
        if closure.unresolved:
            reasons.append(Reason("dependency", closure.unresolved))
            return tuple(reasons)
        dependencies = []
        view = holders.get(item.corpus_id)
        if view is not None:
            for address in sorted(closure.addresses):
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
