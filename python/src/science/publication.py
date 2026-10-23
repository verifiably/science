"""Publishing a view to a destination: destination parsing, the transport choice, and the fields of the two
publication records (the marker a publication corpus carries, the binding the publishing write root holds).

`REMOTE_FOR` maps a destination to the git remote its transport pushes to, and `GIT_ENV` is the environment that
transport's git runs under (`None`: the production one). Both are module seams: `transport_for` reads them at
call time, so a test that reassigns them reaches every transport built after."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from beliefs import stored
from beliefs.corpus import ReadView
from beliefs.errors import MalformedRecord, SelectionRefused
from beliefs.intents.publish import Destination
from beliefs.publication import BINDING_KIND, MARKER_KIND
from beliefs.publication_arrival import require_publication_layout
from beliefs.transport import Transport
from nodes.core.node import Node

from science.refusal import Refusal, Refused
from science.transport_git import GitTransport, identity_remote
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
