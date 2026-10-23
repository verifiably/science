"""Publishing a view to a destination: destination parsing, the transport choice, and the fields of the two
publication records (the marker a publication corpus carries, the binding the publishing write root holds), and
the inspection of a publication at a provider's location.

`REMOTE_FOR` maps a destination to the git remote its transport pushes to, and `GIT_ENV` is the environment that
transport's git runs under (`None`: the production one). Both are module seams: `transport_for` reads them at
call time, so a test that reassigns them reaches every transport built after."""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from beliefs import stored
from beliefs.corpus import ReadView
from beliefs.errors import MalformedRecord, ObserverCarrierInvalid, PublicationArrivalRefused, SelectionRefused
from beliefs.intents.publish import Destination
from beliefs.publication import BINDING_KIND, MARKER_KIND
from beliefs.publication_arrival import require_publication_layout
from beliefs.root import evaluate_copy
from beliefs.transport import Transport
from beliefs.world.anchors import CorpusSubject
from beliefs.world.verify import ArtifactCarrier, ObserverSet
from nodes.core.node import Node

from science.refusal import Refusal, Refused
from science.transport_git import GitTransport, GitTransportFault, identity_remote
from science.world_belief import REMEDY

REMOTE_FOR = identity_remote
GIT_ENV: Mapping[str, str] | None = None


@dataclass(frozen=True)
class TransportFault:
    """A transport failure the publish handler raises as a kernel refusal value: the kernel's attempt stays
    unfinished with its mark, and `publish --resume` continues it."""
    reason: str
    detail: str


@dataclass(frozen=True)
class PublishRefusedValue:
    """A publish the kernel refused or left unresolved, as a kernel refusal value."""
    reason: str
    detail: str


@dataclass(frozen=True)
class MarkerFields:
    uid: str
    world: str
    view: str  # the view address pinned to the revision the selection was evaluated against
    selection: frozenset[str]
    attributions: dict[str, tuple[str, str]]  # address -> (origin corpus, origin marker)
    supersedes: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class BindingFields:
    corpus_id: str
    marker: str
    artifact: str
    destination: Destination


def parse_destination(text: str) -> Destination:
    """An absolute path is a local destination and an `https://` URL a remote one; anything else refuses."""
    try:
        if text.startswith("/"):
            return Destination.local(text)
        if text.startswith("https://"):
            return Destination.remote(text)
    except MalformedRecord as caught:
        raise Refused(Refusal("invalid-input", f"destination {text!r}: {caught}")) from None
    raise Refused(Refusal("invalid-input",
                          f"destination {text!r} is neither an absolute path nor an https:// URL"))


def selection_detail(refused: SelectionRefused) -> str:
    """A kernel `SelectionRefused`'s message; a drifted corpus also names the remedy, a new epoch."""
    return f"{refused}; {REMEDY}" if refused.reason == "corpus-drifted" else str(refused)


def transport_for(config, destination: Destination) -> Transport | None:
    """None for a local destination; a git transport, cached under the operations root, for a remote one."""
    if destination.type == "local":
        return None
    return GitTransport(config.operations_root / "transport", author=f"science {config.world.world_id}",
                        remote_for=REMOTE_FOR, env=GIT_ENV)


def marker_of(root: Path) -> Node:
    """The publication marker of the corpus at `root`, once the kernel's publication layout holds there (one
    well-formed, self-consistent marker selecting exactly the records held); otherwise the kernel's
    `PublicationArrivalRefused` naming why."""
    records = tuple(ReadView.opened_at(root).iter_stored())
    require_publication_layout(records)
    (marker,) = (node for node in records if node.kind == MARKER_KIND)
    return marker


def marker_fields(node: Node) -> MarkerFields:
    if node.kind != MARKER_KIND:
        raise ValueError(f"{node.id} is a {node.kind} record, not a {MARKER_KIND} marker")
    facet = node.facets[stored.COORDINATION_FACET]
    source = facet["published_from"]
    return MarkerFields(
        uid=node.uid,
        world=source["world_id"],
        view=source["view"],
        selection=frozenset(facet["selection"]),
        attributions={address: (corpus, marker) for address, corpus, marker in source.get("attributions", [])},
        supersedes=tuple(tuple(pair) for pair in facet["supersedes_markers"]),
    )


def artifact_identity(sibling: bytes) -> str:
    """A head artifact's identity: the SHA-256 of its bytes, as a binding and a sharing line name it."""
    return sha256(sibling).hexdigest()


def binding_fields(node: Node) -> BindingFields:
    if node.kind != BINDING_KIND:
        raise ValueError(f"{node.id} is a {node.kind} record, not a {BINDING_KIND}")
    facet = node.facets[stored.COORDINATION_FACET]
    return BindingFields(corpus_id=facet["corpus_id"], marker=facet["marker"], artifact=facet["artifact"],
                         destination=Destination.from_projection(facet["destination"]))


_ID_RE = re.compile(r"[0-9a-f]{32}")


def require_id(text: str, name: str) -> None:
    """A corpus or world id input: 32 lowercase hex digits, or `invalid-input` naming the input."""
    if _ID_RE.fullmatch(text) is None:
        raise Refused(Refusal("invalid-input", f"{name} {text!r} is not 32 lowercase hex digits"))


@dataclass(frozen=True)
class Inspection:
    """A publication fetched from a provider's location and evaluated where it landed, granting nothing."""
    root: Path
    sibling: bytes
    verdict: str
    fields: MarkerFields
    artifact: str


def provider_transport(config, destination: Destination) -> Transport:
    """The transport a provider's location is fetched through. 1a's one provider transport is git, so a local
    directory refuses `invalid-input` naming the location."""
    transport = transport_for(config, destination)
    if transport is None:
        raise Refused(Refusal("invalid-input",
                              f"location {destination.locator!r}: a provider location is an https:// git remote"))
    return transport


def download(transport: Transport, destination: Destination, corpus_id: str, into: Path) -> Inspection:
    """Fetch corpus `corpus_id` from `destination` into `into` (its root is `into/<corpus_id>`), evaluate the copy
    against its own head artifact with `evaluate_copy`, granting nothing, and read its marker. Every way the
    location fails to hold a validated publication of that corpus refuses `invalid-input` naming the location.
    The caller deletes the copy."""
    locator = destination.locator

    def refuse(why: str, **data: str) -> Refused:
        return Refused(Refusal("invalid-input", f"location {locator}: {why}", {"location": locator, **data}))

    try:
        root, sibling = transport.fetch_corpus(destination, corpus_id, into)
    except GitTransportFault as fault:
        raise refuse(str(fault)) from None
    try:
        observers = ObserverSet((ArtifactCarrier.from_bytes(sibling),))
    except ObserverCarrierInvalid as caught:
        raise refuse(f"corpus {corpus_id}: {caught}") from None
    verdict = evaluate_copy(root, CorpusSubject(corpus_id), observers)
    if verdict != "validated":
        raise refuse(f"corpus {corpus_id} evaluates {verdict}, not validated", verdict=verdict)
    try:
        marker = marker_of(root)
    except PublicationArrivalRefused as caught:
        raise refuse(f"corpus {corpus_id} is not a publication: {caught}") from None
    return Inspection(root, sibling, verdict, marker_fields(marker), artifact_identity(sibling))


def inspect(config, destination: Destination, corpus_id: str, scratch: Path) -> Inspection:
    """`download` into `scratch`, which must not exist yet. The caller deletes `scratch`."""
    transport = provider_transport(config, destination)
    scratch.mkdir(parents=True)
    return download(transport, destination, corpus_id, scratch)
