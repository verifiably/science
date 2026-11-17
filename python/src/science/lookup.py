"""Identifier lookup across configured corpora and session citation resolution."""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from beliefs.errors import IdentifierMalformed
from beliefs.source import normalized_identifiers
from beliefs.stored import SOURCE_FACET
from beliefs.world.registry import content_identity
from nodes.core.node import Node

from science.config import _retired
from science.refusal import Refusal, Refused


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
    if len({content_identity(mount.view.get(ref)) for mount in holders}) > 1:
        raise Refused(Refusal("invalid-input",
                             f"{ref!r} is held by corpora {', '.join(m.corpus_id for m in holders)}; "
                             "the copies differ"))
    preferred = min(holders, key=lambda mount: (mount.root != ctx.config.write_root, mount.corpus_id))
    return Located(preferred.view.get(ref), tuple(sorted({mount.corpus_id for mount in holders})))


def world_record(ctx, ref: str) -> Located | None:
    return _located(ctx, [mount for mount in _live(ctx, ctx.mounts()) if mount.view.holds(ref)], ref)


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
