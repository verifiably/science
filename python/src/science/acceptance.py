"""The accept policy (commons spec §9): which mounted records count toward the reader's belief.

The kernel consults `counts(corpus_id, address)` for every assessment, verification and retraction before any of
their effects; this module computes that predicate from the reader's own roots, its `accept` configuration, the
sharing registry's mounted pins and provider bindings, the write root's publication bindings and the mounted
publications' markers, and states it as the policy statement the belief input digest incorporates."""
from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from functools import partial

from beliefs.belief import AcceptanceContext, AcceptancePolicy
from beliefs.errors import PublicationArrivalRefused
from beliefs.publication import BINDING_KIND, MARKER_KIND
from beliefs.publication_arrival import require_publication_layout
from beliefs.world.registry import content_identity

from science.publication import binding_fields, marker_fields
from science.refusal import Refusal, Refused
from science.sharing import Pin, ProviderBinding, SharingRegistry

POLICY = "science.accept.v1"


@dataclass(frozen=True)
class Carrier:
    """A session mount that is a publication: its marker's claims, unauthenticated until a pin confirms them."""
    corpus_id: str
    world: str
    marker: str
    selection: frozenset[str]
    attributions: Mapping[str, tuple[str, str]]  # address -> (origin corpus, origin marker)
    content: Mapping[str, str]  # address -> content identity of this copy


@dataclass(frozen=True)
class AcceptanceInputs:
    own_corpus: str
    own_roots: frozenset[str]  # the write root and every configured (hand-listed) root that holds no marker
    verifiers: frozenset[str]  # own world ∪ config.accept
    pins: Mapping[str, Pin]  # mounted pins by corpus id
    bindings: Mapping[str, ProviderBinding]
    own_bindings: frozenset[tuple[str, str, str]]  # (corpus_id, marker, artifact) from the write root
    carriers: Mapping[str, Carrier]  # every configured mount holding a marker, by corpus id


def _carrier(mount) -> Carrier | None:
    """The mount as a publication, or None when it holds no marker. A marker outside the kernel's publication
    layout refuses: the mount claims to be a publication and its claims cannot be read."""
    records = tuple(mount.view.iter_stored())
    if not any(node.kind == MARKER_KIND for node in records):
        return None
    try:
        require_publication_layout(records)
    except PublicationArrivalRefused as caught:
        raise Refused(Refusal("invalid-input", f"corpus {mount.corpus_id} at {mount.root} carries a publication "
                                               f"marker but is not a publication: {caught}")) from None
    (marker,) = (node for node in records if node.kind == MARKER_KIND)
    fields = marker_fields(marker)
    return Carrier(mount.corpus_id, fields.world, fields.uid, fields.selection, dict(fields.attributions),
                   {node.id: content_identity(node) for node in records})


def _refuse_claimed_duplicates(found, registry_roots: set) -> None:
    """Two configured roots with one corpus id are a duplicate carrier, which a read context keeps so `status`
    can report it. The kernel names a record by `(corpus_id, address)` alone, so the policy cannot tell which
    root it came from: when either root holds a marker or is a pinned registry root, one could take the other's
    standing, and the read refuses. Two markerless, unpinned roots are both Own whichever holds the record."""
    by_id: dict[str, list] = {}
    for mount, carrier in found:
        by_id.setdefault(mount.corpus_id, []).append((mount, carrier))
    for corpus_id, held in sorted(by_id.items()):
        if len(held) > 1 and any(carrier is not None or mount.root in registry_roots for mount, carrier in held):
            roots = ", ".join(str(mount.root) for mount, _ in held)
            raise Refused(Refusal("invalid-input",
                                  f"corpus {corpus_id} is carried by more than one configured root ({roots}) and "
                                  "one of them is a publication or an adopted root; the accept policy cannot tell "
                                  "which root a record came from, so remove the duplicate from corpus_roots"))


def acceptance_inputs(ctx) -> AcceptanceInputs:
    """The policy's inputs for a read context. Every configured mount is read: with coordination on that is the
    session, and with it off a corpus-local read of a non-write root is still decided here. A root under the
    sharing registry (any pin's, whatever its state) is never the reader's own; a hand-listed root is its own
    only while it holds no marker (plan Deviation 6)."""
    config = ctx.config
    registry = None if config.sharing_root is None else SharingRegistry(config.sharing_root)
    pins = {} if registry is None else {pin.corpus_id: pin for pin in registry.pins() if pin.state == "mounted"}
    registry_roots = (set() if registry is None
                      else {registry.root_for(pin.corpus_id).resolve() for pin in registry.pins()})
    mounts = ctx.mounts()
    found = [(mount, _carrier(mount)) for mount in mounts]
    _refuse_claimed_duplicates(found, registry_roots)
    carriers = {carrier.corpus_id: carrier for _, carrier in found if carrier is not None}
    (write,) = (mount for mount in mounts if mount.root == config.write_root)
    own_roots = {write.corpus_id} | {mount.corpus_id for mount in mounts
                                     if mount.root not in registry_roots and mount.corpus_id not in carriers}
    own_bindings = frozenset((fields.corpus_id, fields.marker, fields.artifact)
                             for node in write.view.iter_stored() if node.kind == BINDING_KIND
                             for fields in (binding_fields(node),))
    return AcceptanceInputs(
        own_corpus=write.corpus_id,
        own_roots=frozenset(own_roots),
        verifiers=frozenset({config.world.world_id, *config.accept}),
        pins=pins,
        bindings={} if registry is None else registry.bindings(),
        own_bindings=own_bindings,
        carriers=carriers,
    )


def _origin_holds(inputs: AcceptanceInputs, origin: str, origin_marker: str, address: str) -> bool:
    """The Carried branch: the origin publication is pinned at the attributed marker, origin-confirmed, of an
    accepted world, mounted, and its own marker selects the record as its own: an origin that itself carries the
    record is an intermediary, and an honest marker names the first origin (spec §4.8)."""
    pin = inputs.pins.get(origin)
    carrier = inputs.carriers.get(origin)
    return (pin is not None and pin.marker == origin_marker and pin.origin_confirmed(inputs.bindings)
            and pin.world in inputs.verifiers and carrier is not None and address in carrier.selection
            and address not in carrier.attributions)


def counts(inputs: AcceptanceInputs, corpus_id: str, address: str) -> bool:
    """Whether the record at `address` in `corpus_id` counts toward belief: the first applicable branch decides."""
    if corpus_id in inputs.own_roots:
        return True  # Own: the write root, or a hand-listed root holding no marker
    carrier = inputs.carriers.get(corpus_id)
    if carrier is None:
        return False  # neither ours nor a publication
    if address in carrier.attributions:
        origin, origin_marker = carrier.attributions[address]
        return (_origin_holds(inputs, origin, origin_marker, address)
                and inputs.carriers[origin].content.get(address) == carrier.content[address])  # Carried
    pin = inputs.pins.get(corpus_id)
    if pin is None:
        return False  # a hand-listed publication: its own records need a pin
    if address not in carrier.selection or carrier.marker != pin.marker:
        return False  # not the pinned publication's record: the pin vouches for its marker's selection only
    if (corpus_id, carrier.marker, pin.artifact) in inputs.own_bindings:
        return True  # Own: our publication adopted back
    return carrier.world in inputs.verifiers and pin.origin_confirmed(inputs.bindings)  # Carrier's own


def statement(inputs: AcceptanceInputs) -> str:
    """The policy's identity statement: canonical JSON of what `counts` reads, each carrier's selection and
    attributions stated by size. Deterministic for a context: every collection is sorted."""
    document = {
        "policy": POLICY,
        "verifiers": sorted(inputs.verifiers),
        "own_roots": sorted(inputs.own_roots),
        "pins": [{"corpus": pin.corpus_id, "world": pin.world, "marker": pin.marker,
                  "source": "" if pin.source is None else pin.source.render(),
                  "confirmed": pin.origin_confirmed(inputs.bindings), "state": pin.state}
                 for _, pin in sorted(inputs.pins.items())],
        "own_bindings": sorted(list(entry) for entry in inputs.own_bindings),
        "carriers": [{"corpus": carrier.corpus_id, "world": carrier.world, "marker": carrier.marker,
                      "selected": len(carrier.selection), "attributed": len(carrier.attributions)}
                     for _, carrier in sorted(inputs.carriers.items())],
    }
    return json.dumps(document, sort_keys=True, separators=(",", ":"))


def policy(ctx) -> AcceptancePolicy:
    inputs = acceptance_inputs(ctx)
    return AcceptancePolicy(counts=partial(counts, inputs), statement=statement(inputs))


def _world_of(inputs: AcceptanceInputs, corpus_id: str, address: str) -> str:
    """The provenance world a record claims, as its holder's marker states it."""
    carrier = inputs.carriers.get(corpus_id)
    if carrier is None:
        return "unknown: the corpus is not a publication"
    if address not in carrier.attributions:
        return carrier.world
    origin, _ = carrier.attributions[address]
    if origin in inputs.carriers:
        return f"{inputs.carriers[origin].world} (carried from corpus {origin})"
    return f"unknown: carried from corpus {origin}, which is not mounted"


def explain(context: AcceptanceContext, inputs: AcceptanceInputs,
            holders_of: Callable[[str], tuple[str, ...]]) -> tuple[tuple[str, str], ...]:
    """What belief selected by (spec §9 item 4): the verifier set, each mounted pin's source and standing, and
    every excluded copy with a counting session holder or its provenance world."""
    pairs = [("policy", POLICY), ("verifiers", ", ".join(sorted(inputs.verifiers)))]
    for corpus_id, pin in sorted(inputs.pins.items()):
        source = "none" if pin.source is None else pin.source.render()
        confirmed = "origin-confirmed" if pin.origin_confirmed(inputs.bindings) else "not origin-confirmed"
        pairs.append((f"pin {corpus_id}", f"world {pin.world}; source {source}; {confirmed}; {pin.state}"))
    if not context.complete:
        pairs.append(("excluded", "unknown: the evaluation stopped before the selection completed"))
    elif not context.excluded:
        pairs.append(("excluded", "none"))
    for corpus_id, address in context.excluded:
        holder = next((other for other in holders_of(address)
                       if other != corpus_id and counts(inputs, other, address)), None)
        detail = (f"copy of a record that counts through corpus {holder}" if holder is not None
                  else f"world {_world_of(inputs, corpus_id, address)}")
        pairs.append((f"excluded {address} ({corpus_id})", f"corpus {corpus_id}; {detail}"))
    return tuple(pairs)
