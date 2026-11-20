"""The live inputs and publication history that prevent retirement."""
from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from typing import Literal

from beliefs import stored
from beliefs.coordination import (
    COORDINATION_KINDS,
    VIEW_KINDS,
    CoordinationAddress,
    CoordinationRevision,
    coordination_revision,
    standing_tips,
)
from beliefs.corpus import ReadView
from beliefs.dataset import ByteObservation, dataset_address
from beliefs.dependencies import record_references
from beliefs.errors import MalformedRecord, ScienceError
from beliefs.estimand import DatasetBinding
from beliefs.procedure import Procedure, procedure_from_stored
from beliefs.referent_mapping import mapping_from_stored
from beliefs.proxy_model import proxy_from_stored
from beliefs.classification_rule import rule_from_stored
from beliefs.register import register_from_stored
from beliefs.profile import ProfileSpec
from beliefs.publish_request import closure_missing
from beliefs.root import open_world_read
from beliefs.view_query import stored_query
from beliefs.world.registry import content_identity
from nodes.core.errors import NodesError
from nodes.core.node import Node

from science.holdings import found_observations
from science.lookup import coreference_attestation_shape
from science.supersession import Held, chain

__all__ = ["DependencyClosure", "Holder", "Reason", "dependency_closure", "live_observations", "required"]

_DEPENDENCY_ERRORS = (ScienceError, NodesError, ValueError, KeyError, TypeError, OSError)


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


def _stored_nodes(view: ReadView, unresolved: set[str], diagnostic: str) -> Iterator[Node]:
    try:
        yield from view.iter_stored()
    except _DEPENDENCY_ERRORS as error:
        unresolved.add(f"{diagnostic} ({type(error).__name__})")


def _note_addresses(revision: CoordinationRevision) -> list[str]:
    node = revision.node
    facet = node.facets[stored.COORDINATION_FACET]
    fields = {"project", "local", "author", "at"}
    if set(facet) not in (fields, fields | {"about"}) or revision.predecessors:
        raise MalformedRecord("invalid immutable note fields or predecessors")
    if not isinstance(node.title, str) or not node.title or not isinstance(node.body, str):
        raise MalformedRecord("invalid note title or body")
    about = facet.get("about", [])
    if not isinstance(about, list) or any(not isinstance(address, str) for address in about):
        raise MalformedRecord("note about must be a list of addresses")
    if len(about) != len(set(about)):
        raise MalformedRecord("note about must contain distinct addresses")
    for address in about:
        kind, separator, spelling = address.partition(":")
        if kind not in stored.WORLD_KINDS or not separator or not spelling:
            raise MalformedRecord("note about must name typed world addresses")
    return about


def _local_citations(write_root: Holder) -> tuple[set[str], set[str]]:
    corpus, view, _ = write_root
    citations: set[str] = set()
    unresolved: set[str] = set()
    histories: dict[CoordinationAddress, list[CoordinationRevision]] = defaultdict(list)
    queries: dict[str, tuple[str, ...]] = {}
    for entry in _stored_nodes(view, unresolved, f"write corpus {corpus} enumerate citations"):
        coordination = entry.kind in COORDINATION_KINDS or stored.COORDINATION_FACET in entry.facets
        coreference = entry.kind == "coreference-attestation" or stored.COREFERENCE_ATTESTATION_FACET in entry.facets
        if not (coordination or coreference):
            continue
        operation = "read citation"
        try:
            node = view.get(entry.id)
            if (node.id, node.uid, node.kind) != (entry.id, entry.uid, entry.kind):
                raise MalformedRecord("enumerated citation identity disagrees with its read")
            if coreference:
                operation = "validate coreference attestation"
                citations.update(coreference_attestation_shape(node).endpoints)
            if coordination:
                operation = "validate coordination revision"
                if node.kind not in COORDINATION_KINDS:
                    raise MalformedRecord("coordination facet on a different kind")
                revision = coordination_revision(node)
                address = revision.address.unpinned()
                if (address.local is None) != (node.kind == "project"):
                    raise MalformedRecord("coordination address has the wrong shape for its kind")
                history = histories[address]
                if history and history[0].node.kind != node.kind:
                    raise MalformedRecord("coordination address has inconsistent kinds")
                if node.kind == "note":
                    operation = "validate note"
                    citations.update(_note_addresses(revision))
                elif node.kind in VIEW_KINDS:
                    operation = "validate view query"
                    queries[node.id] = stored_query(node).addresses()
                history.append(revision)
        except _DEPENDENCY_ERRORS as error:
            unresolved.add(f"write corpus {corpus} {operation} {entry.id} ({type(error).__name__})")
    for history in histories.values():
        if history and history[0].node.kind in VIEW_KINDS:
            for tip in standing_tips(history):
                citations.update(queries[tip.node.id])
    return citations, unresolved


def dependency_closure(write_root: Holder, holders: Sequence[Holder], *,
                       observations: Mapping[str, tuple[ByteObservation, ...]]) -> DependencyClosure:
    # Custody keeps frozen provenance even when a reader rejects or retracts it.
    available = sorted((write_root, *holders), key=lambda holder: holder[0])
    reached: set[str] = set()
    unresolved: set[str] = set()
    digest_reads: set[str] = set()
    pending = [node.id for node in _stored_nodes(
        write_root[1], unresolved, f"write corpus {write_root[0]} enumerate provenance",
    )]

    def include_digest(digest):
        if digest in digest_reads:
            return
        digest_reads.add(digest)
        observed = {address for address, values in observations.items() if any(o.digest == digest for o in values)}
        matches = set()
        for corpus, view, _ in available:
            for node in _stored_nodes(view, unresolved, f"unresolved-digest {digest} holder {corpus} enumerate"):
                if node.kind != "dataset":
                    continue
                try:
                    if dataset_address(stored.dataset_declaration(node)) in observed:
                        matches.add(node.id)
                except _DEPENDENCY_ERRORS as error:
                    unresolved.add(f"unresolved-reference {node.id} ({type(error).__name__}: {error})")
        pending.extend(sorted(matches))
        if not matches:
            unresolved.add(f"unresolved-digest {digest}")

    while pending:
        address = pending.pop()
        if address in reached:
            continue
        reached.add(address)
        copies = []
        for cid, view, profile in available:
            operation = "resolve"
            try:
                if not view.holds(address):
                    continue
                operation = "read"
                node = view.get(address)
                operation = "content identity"
                copies.append((cid, view, profile, node, content_identity(node)))
            except _DEPENDENCY_ERRORS as error:
                holder = f"holder {cid}" if operation == "read" else f"holder {cid} {operation}"
                unresolved.add(f"unresolved-reference {address} {holder} ({type(error).__name__}: {error})")
        if not copies:
            unresolved.add(f"unresolved-reference {address}")
            continue
        if len({(node.id, identity) for _, _, _, node, identity in copies}) > 1:
            unresolved.add(f"unresolved-copy {address} holders: {', '.join(sorted({cid for cid, *_ in copies}))}")
            continue
        _, view, profile, node, _ = copies[0]
        reached.add(node.id)
        try:
            # The publication export may close over attestation endpoints.
            if node.kind != "coreference-attestation":
                pending.extend(closure_missing(view, (node.id,)))
            references, digests = _references(node, profile)
            pending.extend(sorted(references))
            for digest in sorted(digests):
                include_digest(digest)
        except _DEPENDENCY_ERRORS as error:
            unresolved.add(f"unresolved-reference {address} ({type(error).__name__}: {error})")
    return DependencyClosure(frozenset(reached), tuple(sorted(unresolved)))


def _holder_identities(
    address: str, holders: Sequence[Holder], *, context: str,
) -> tuple[dict[str, tuple[str, str] | None], set[str]]:
    """A failed resolution or read leaves a possible holder with unknown identity."""
    copies: dict[str, tuple[str, str] | None] = {}
    unresolved: set[str] = set()
    for corpus, view, _ in holders:
        operation = "resolve"
        try:
            resolved = view.resolve(address)
            if resolved is None:
                continue
            operation = "read"
            node = view.get(address)
            if node.id != resolved:
                raise MalformedRecord("resolved address disagrees with the holder's read")
            operation = "content identity"
            copies[corpus] = (node.id, content_identity(node))
        except _DEPENDENCY_ERRORS as error:
            copies[corpus] = None
            unresolved.add(f"{context} {address} holder {corpus} {operation} ({type(error).__name__})")
    return copies, unresolved


def _dependency_details(
    write_root: Holder, live: Sequence[Holder], observations: Mapping[str, tuple[ByteObservation, ...]],
) -> tuple[dict[str, set[str]], tuple[str, ...]]:
    distinct: dict[str, Holder] = {}
    for holder in (write_root, *live):
        distinct.setdefault(holder[0], holder)
    holders = tuple(distinct.values())
    closure = dependency_closure(write_root, holders[1:], observations=observations)
    citations, unresolved = _local_citations(write_root)
    unresolved.update(closure.unresolved)
    if unresolved:
        return {}, tuple(sorted(unresolved))

    holders = sorted(holders, key=lambda holder: holder[0])
    dependencies: dict[str, set[str]] = defaultdict(set)
    for address in sorted(closure.addresses):
        copies, errors = _holder_identities(address, holders, context="unresolved-reference")
        unresolved.update(errors)
        counts = Counter(copies.values())
        for corpus, identity in copies.items():
            if identity is not None and counts[identity] == 1:
                dependencies[corpus].add(address)
    if unresolved:
        return {}, tuple(sorted(unresolved))

    for address in sorted(citations):
        copies, errors = _holder_identities(address, holders, context="citation")
        read = {corpus: identity for corpus, identity in copies.items() if identity is not None}
        if len(set(read.values())) > 1:
            errors.add(f"citation {address} conflicting holders: {', '.join(sorted(read))}")
        if errors:
            for corpus in copies:
                dependencies[corpus].update(errors)
        elif len(copies) == 1:
            dependencies[next(iter(copies))].add(address)
    return dependencies, ()


def required(predecessor: Held, *, keep: Sequence[str], group_chain: Sequence[Held], tip: tuple[str, str],
             mounted: Sequence[Held], write_root: Holder, live: Sequence[Holder],
             observations: Mapping[str, tuple[ByteObservation, ...]]) -> tuple[Reason, ...]:
    dependencies, unresolved = _dependency_details(write_root, live, observations)

    def direct(item: Held) -> tuple[Reason, ...]:
        reasons = []
        if item.corpus_id in keep:
            reasons.append(Reason("configuration", ()))
        naming = {other.corpus_id for other in mounted if other.state == "mounted"
                  and any(origin == item.corpus_id for origin, _ in other.marker.attributions.values())}
        reasons.extend(Reason("attribution", (corpus,)) for corpus in sorted(naming))
        detail = unresolved or tuple(sorted(dependencies.get(item.corpus_id, ())))
        if detail:
            reasons.append(Reason("dependency", detail))
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
