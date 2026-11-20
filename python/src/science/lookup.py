"""Identifier lookup across configured corpora and session citation resolution."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from functools import cache

from beliefs import stored
from beliefs.errors import IdentifierMalformed, MalformedRecord, ScienceError, SourceAssertionRefused
from beliefs.reservation import UNREAD
from beliefs.source import normalized_identifiers
from beliefs.source_assertion import SourceAssertion, source_assertion_refusal
from beliefs.stored import SOURCE_FACET, source_assertion_value
from beliefs.world.rules_v1.coreference import reduce_coreference
from nodes.core.node import Node

from science.config import _retired
from science.refusal import Refusal, Refused, kernel_refusal

__all__ = [
    "CoreferencePair",
    "Located",
    "coreference_attestation_shape",
    "decode_source_assertion",
    "identifiers",
    "require_identifiers",
    "session_record",
    "shared_with",
    "source_assertions",
    "source_coreference",
    "sources_carrying",
    "unresolved_citations",
    "validate_coreference_attestation",
    "world_record",
    "write_root_only",
]


def identifiers(*, doi=None, pmid=None, isbn=None, accession=None) -> dict[str, str]:
    given = {scheme: value for scheme, value in
             (("doi", doi), ("pmid", pmid), ("isbn", isbn), ("accession", accession))
             if value is not None}
    try:
        return normalized_identifiers(given)
    except IdentifierMalformed as caught:
        raise Refused(Refusal("invalid-input", str(caught), {
            "kind": "IdentifierMalformed", "scheme": caught.scheme,
            "value": caught.value, "reason": caught.reason,
        })) from caught


def require_identifiers(given: Mapping[str, str]) -> None:
    if not given:
        raise Refused(Refusal("invalid-input", "give at least one identifier", {"kind": "BasisMissing"}))


@dataclass(frozen=True)
class Located:
    node: Node
    corpora: tuple[str, ...]

    @property
    def address(self) -> str:
        return self.node.id

    def entry(self, *, asked: str | None = None) -> dict:
        result = {"address": self.address, "title": self.node.title,
                  "identifiers": dict(self.node.facets.get(SOURCE_FACET, {}).get("identifiers", {})),
                  "corpora": list(self.corpora)}
        if asked is not None and asked != self.address:
            result["redirect"] = True
        return result


def _live(ctx, mounts):
    return tuple(mount for mount in mounts if not _retired(ctx.world.status(mount.corpus_id)))


def _located(ctx, holders, ref):
    if not holders:
        return None
    try:
        preferred = ctx._holder_among(holders, ref)
        node = preferred.view.get(ref)
    except ScienceError as caught:
        raise Refused(kernel_refusal(caught)) from caught
    return Located(node, tuple(sorted({mount.corpus_id for mount in holders})))


def world_record(ctx, ref: str) -> Located | None:
    return _located(ctx, [mount for mount in _live(ctx, ctx.mounts()) if mount.view.holds(ref)], ref)


def session_record(ctx, ref: str) -> Located | None:
    """The record `ref` resolves to, live or through a redirect, across
    session-mounted non-retired corpora (`_live(ctx, ctx.session_mounts())`).
    Differing copies refuse `invalid-input` as `world_record` does; corrupt
    stored nodes (`ScienceError` from `ReadView.get`) refuse `kernel-refused`."""
    return _located(ctx, [mount for mount in _live(ctx, ctx.session_mounts()) if mount.view.holds(ref)], ref)


def decode_source_assertion(node: Node) -> SourceAssertion:
    """Validate `node` with `stored.source_assertion_value(node)` followed by
    `source_assertion_refusal(value, node.relations, kind_of=lambda _ref: UNREAD)`,
    raising `SourceAssertionRefused(refusal.code, f"{node.id}: {refusal.detail}")`
    when `refusal is not None`, and catching `(MalformedRecord,
    SourceAssertionRefused) as caught` to raise `Refused(kernel_refusal(caught))
    from caught` (`code == "kernel-refused"`)."""
    try:
        value = source_assertion_value(node)
        refusal = source_assertion_refusal(value, node.relations, kind_of=lambda _ref: UNREAD)
        if refusal is not None:
            raise SourceAssertionRefused(refusal.code, f"{node.id}: {refusal.detail}")
        return value
    except (MalformedRecord, SourceAssertionRefused) as caught:
        raise Refused(kernel_refusal(caught)) from caught


def source_assertions(ctx) -> tuple[tuple[Located, SourceAssertion], ...]:
    """Every stored `source-assertion` across configured non-retired corpora
    (`_live(ctx, ctx.mounts())`), deduplicated by canonical address via
    `_located` (so differing replicas refuse `invalid-input` and stale/missing
    stamps refuse `kernel-refused` as `world_record` does), sorted by `address`,
    each decoded with `decode_source_assertion`."""
    mounts = _live(ctx, ctx.mounts())
    addresses = {
        node.id
        for mount in mounts
        for node in mount.view.iter_stored()
        if node.kind == "source-assertion"
    }
    by_address: dict[str, tuple[Located, SourceAssertion]] = {}
    for ref in sorted(addresses):
        located = _located(ctx, [mount for mount in mounts if mount.view.holds(ref)], ref)
        if located is not None and located.address not in by_address:
            by_address[located.address] = (located, decode_source_assertion(located.node))
    return tuple(by_address[address] for address in sorted(by_address))


def sources_carrying(ctx, given: Mapping[str, str]) -> tuple[Located, ...]:
    mounts = _live(ctx, ctx.mounts())
    addresses = set()
    for mount in mounts:
        for node in mount.view.iter_stored():
            if node.kind == "source" and any(
                given.get(scheme) == value
                for scheme, value in node.facets[SOURCE_FACET]["identifiers"].items()
            ):
                addresses.add(node.id)
    return tuple(_located(ctx, [mount for mount in mounts if mount.view.holds(ref)], ref)
                 for ref in sorted(addresses))


def shared_with(ctx, node) -> tuple[str, ...]:
    return tuple(sorted({mount.corpus_id for mount in _live(ctx, ctx.mounts())
                         if mount.root != ctx.config.write_root and
                         (mount.view.holds(node.id) or any(
                             candidate.uid == node.uid for candidate in mount.view.iter_stored()))}))


def write_root_only(ctx, located: Located) -> bool:
    return any(mount.root == ctx.config.write_root and mount.view.holds(located.address)
               for mount in _live(ctx, ctx.mounts())) and not shared_with(ctx, located.node)


def unresolved_citations(ctx, addresses: Iterable[str]) -> list[str]:
    mounts = _live(ctx, ctx.session_mounts())
    unresolved = []
    for ref in dict.fromkeys(addresses):
        if _located(ctx, [mount for mount in mounts if mount.view.holds(ref)], ref) is None:
            unresolved.append(ref)
    return unresolved


@dataclass(frozen=True)
class CoreferencePair:
    addresses: tuple[str, str]
    resolved: tuple[Located | None, Located | None]
    balance: int
    distinct_key_count: int
    attestations: tuple[str, ...]

    @property
    def state(self) -> str:
        if any(item is not None and item.address != address
               for address, item in zip(self.addresses, self.resolved, strict=True)):
            return "historical-redirect"
        if None in self.resolved:
            return "unavailable"
        if not self.distinct_key_count:
            return "unassessed"
        if self.balance > 0:
            return "positive"
        return "contested" if self.balance == 0 else "negative"

    def other_address(self, uid: str) -> str | None:
        """Current peer address for sorting, or its stored address if absent."""
        for index, item in enumerate(self.resolved):
            if item is not None and item.node.uid == uid:
                peer = self.resolved[1 - index]
                return self.addresses[1 - index] if peer is None else peer.address
        return None


def coreference_attestation_shape(node: Node) -> stored.CoreferenceAttestation:
    """Validate the controlled event independently of its endpoint holdings."""
    if node.kind != "coreference-attestation":
        raise MalformedRecord(f"{node.id}: expected a coreference-attestation, found {node.kind}")
    try:
        value = stored.coreference_attestation_value(node)
        expected = stored.coreference_attestation_node(
            title=node.title, endpoints=value.endpoints, stance=value.stance, actor=value.actor,
            grounds=value.grounds, event_token=value.event_token,
        )
    except (MalformedRecord, ValueError, TypeError) as caught:
        raise MalformedRecord(f"{node.id}: invalid coreference attestation: {caught}") from caught
    if (node.id, node.facets, node.relations) != (expected.id, expected.facets, expected.relations):
        raise MalformedRecord(f"{node.id}: coreference attestation does not match the controlled stored shape")

    kinds = []
    for address in value.endpoints:
        kind, separator, local = address.partition(":")
        if not separator or not local or kind not in stored.COREFERENCE_ENDPOINT_KINDS:
            raise MalformedRecord(f"{node.id}: inadmissible coreference endpoint {address!r}")
        kinds.append(kind)
    if kinds[0] != kinds[1]:
        raise MalformedRecord(f"{node.id}: coreference endpoints have different kinds")
    return value


def _validated_coreference(node, resolve_source):
    value = coreference_attestation_shape(node)
    if not value.endpoints[0].startswith("source:"):
        return value, None

    left, right = (resolve_source(address) for address in value.endpoints)
    for address, item in zip(value.endpoints, (left, right), strict=True):
        if item is not None and item.node.kind != "source":
            raise MalformedRecord(f"{node.id}: endpoint {address!r} resolves to a {item.node.kind}")
    return value, (left, right)


def validate_coreference_attestation(ctx, node: Node) -> None:
    """Check a direct event read against the same rules as a source scan."""
    _validated_coreference(node, lambda ref: world_record(ctx, ref))


def source_coreference(ctx) -> tuple[CoreferencePair, ...]:
    """Reduce directly held source events over configured live mounts."""
    mounts = _live(ctx, ctx.mounts())
    addresses = {
        node.id for mount in mounts for node in mount.view.iter_stored()
        if node.kind == "coreference-attestation"
    }

    @cache
    def endpoint(ref):
        return world_record(ctx, ref)

    projections = []
    resolved = {}
    evidence = {}
    for address in sorted(addresses):
        event = _located(ctx, [mount for mount in mounts if mount.view.holds(address)], address)
        if event is None:
            raise MalformedRecord(f"{address}: an enumerated coreference attestation no longer resolves")
        value, endpoints = _validated_coreference(event.node, endpoint)
        if endpoints is None:
            continue
        resolved[value.endpoints] = endpoints
        evidence.setdefault(value.endpoints, []).append(event.address)
        projections.append({"coreference": {
            "endpoints": value.endpoints, "stance": value.stance, "actor": value.actor, "grounds": value.grounds,
        }})

    pairs = []
    for result in reduce_coreference({"records": projections})["pairs"]:
        left, right = result["endpoints"]
        key = (left, right)
        pairs.append(CoreferencePair(key, resolved[key], result["balance"],
                                    result["distinct_key_count"], tuple(evidence[key])))
    return tuple(pairs)
