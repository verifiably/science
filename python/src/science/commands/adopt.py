"""adopt: fetch a publication from a provider's bound location, verify it, source it, check its layout and
conflicts, then admit and mount it (commons spec §4.3 step 3, §10). Every registry write follows the sharing line
that is its evidence, and nothing survives a refusal before `fetched` (plan Deviation 9): the copy is deleted and
no pin is written."""
from __future__ import annotations

import shutil

from beliefs.corpus import ReadView
from beliefs.errors import (
    PublicationArrivalRefused,
    PublicationReadingRefused,
    SharingEvidenceDisagrees,
    WriteRefused,
)
from beliefs.root import metadata_root_for
from beliefs.session.ledger import SharingEvidence
from beliefs.world.anchors import CorpusSubject
from beliefs.world.verify import ArtifactCarrier, ObserverSet

from science import publication
from science.refusal import Refusal, Refused
from science.report import Report, pin_block
from science.sharing import Pin, PinSource, SharingRegistry, apply_line, replay

CONFLICT_REASON = "overlap is milestone 1b (beliefs-81367e)"


def handle(ctx, writer, *, location, corpus_id) -> Report:
    # 1. Inputs, then the registry rebuilt from the ledger.
    config = ctx.config
    publication.require_id(corpus_id, "corpus_id")
    destination = publication.parse_destination(location)
    if config.sharing_root is None:
        raise Refused(Refusal("invalid-input", "adopt records a pin in the sharing registry; configure `sharing_root`",
                              {"key": "sharing_root"}))
    transport = publication.provider_transport(config, destination)
    registry = SharingRegistry(config.sharing_root)
    replay(registry, config.operations_root)
    lines = []

    def record(line):
        """Keep the line for the report, then write the registry state it is the evidence of."""
        lines.append(line)
        apply_line(registry, line)

    # 2. Reconcile, before any duplicate check: the kernel's registry is the truth about admission.
    mounted_now = _reconcile(ctx, writer, registry, record)

    # 3. The target's state.
    pin = registry.pin(corpus_id)
    if pin is not None and pin.state == "mounted" and corpus_id in mounted_now:
        return tuple(pin_block(line) for line in lines)  # this invocation is the recovery
    if pin is not None and pin.state in ("mounted", "retired"):
        raise Refused(Refusal("invalid-input", f"corpus {corpus_id} is already adopted: its pin is {pin.state}",
                              {"corpus_id": corpus_id, "state": pin.state}))
    # A pin `admitted` the kernel does not list cannot arise (the line follows the act): it reads as `fetched`.

    # 4-7. The copy: a `fetched` one reused at its own location, otherwise downloaded, sourced and restored.
    root = registry.root_for(corpus_id)
    if pin is not None and pin.fetch.location != destination.locator:
        raise Refused(Refusal(
            "invalid-input",
            f"corpus {corpus_id} was fetched from {pin.fetch.location}, not {destination.locator}; "
            f"adopt it from {pin.fetch.location}",
            {"location": pin.fetch.location}))
    if pin is not None and root.is_dir() and registry.head_artifact_for(corpus_id).is_file():
        evidence = _evidence(pin)
        observers = _observers(registry.head_artifact_for(corpus_id).read_bytes())
    else:
        evidence, observers = _fetch(writer, transport, destination, registry, corpus_id, record)

    # 8. Conflict: the candidate's addresses against every live root.
    _require_no_overlap(ctx, registry, corpus_id)

    # 9. Admit, then mark mounted.
    try:
        admitted = writer.admit_publication(root, observers, evidence=evidence)
    except WriteRefused as caught:
        raise _kernel_refused(caught) from None
    record(admitted)
    _mark_mounted(writer, registry.pin(corpus_id), record)
    return tuple(pin_block(line) for line in lines)


def _reconcile(ctx, writer, registry: SharingRegistry, record) -> frozenset[str]:
    """Mark `mounted` every `fetched` or `admitted` pin whose corpus the kernel's registry lists admitted (a crash
    fell between the admission and the mark); the corpus ids it mounted."""
    admitted = {admission.corpus_id for admission in ctx.world.registry().admissions}
    mounted = []
    for pin in registry.pins():
        if pin.state in ("fetched", "admitted") and pin.corpus_id in admitted:
            _mark_mounted(writer, pin, record)
            mounted.append(pin.corpus_id)
    return frozenset(mounted)


def _mark_mounted(writer, pin: Pin, record) -> None:
    """Ledger `mounted` for an admitted pin, carrying its source and its fetch record's verification verdict."""
    record(writer.record_sharing(_evidence(pin), transition="mounted", verdict=pin.fetch.verdict))


def _evidence(pin: Pin) -> SharingEvidence:
    """A pin's sharing evidence. Adopt sources every pin before its `fetched` line, so a pin without a source is
    a registry adopt did not write."""
    if pin.source is None:
        raise ValueError(f"pin {pin.corpus_id} is {pin.state} with no source; adopt records one on every line")
    return SharingEvidence(pin.corpus_id, pin.marker, pin.artifact, pin.world, pin.view,
                           source=pin.source.render(), location=pin.fetch.location)


def _observers(sibling: bytes) -> ObserverSet:
    return ObserverSet((ArtifactCarrier.from_bytes(sibling),))


def _fetch(writer, transport, destination, registry: SharingRegistry, corpus_id: str, record):
    """Download the corpus into its registry root, source it from the location's binding, and restore it through
    the kernel's door, which ledgers `fetched`. Any refusal deletes the copy, leaving no pin and no line."""
    root = registry.root_for(corpus_id)
    _discard(registry, corpus_id)  # a stale copy from an earlier attempt
    try:
        found = publication.download(transport, destination, corpus_id, root.parent)
        source = _source(registry, destination.locator, found.fields.world)
        # Kept beside the root, as a container lays them out: a reused `fetched` copy is admitted against it.
        registry.head_artifact_for(corpus_id).write_bytes(found.sibling)
        observers = _observers(found.sibling)
        fields = found.fields
        evidence = SharingEvidence(corpus_id, fields.uid, found.artifact, fields.world, fields.view,
                                   source=source.render(), location=destination.locator)
        try:
            line = writer.restore_root(root, CorpusSubject(corpus_id), observers, evidence=evidence)
        except WriteRefused as caught:
            raise _kernel_refused(caught) from None
    except Refused:
        _discard(registry, corpus_id)
        raise
    record(line)
    return evidence, observers


def _source(registry: SharingRegistry, locator: str, world: str) -> PinSource:
    """The bytes came from `locator` in this invocation, so a binding of `locator` to the world the marker claims
    earns the pin its source."""
    binding = registry.binding_for_location(locator)
    if binding is None:
        raise Refused(Refusal(
            "pin-unsourced",
            f"the publication at {locator} claims world {world}, and nothing sources it: bind the location to that "
            "world with `provider-bind`, or `follow` a catalog that names the corpus",
            {"world": world}))
    if binding.world != world:
        raise Refused(Refusal(
            "world-mismatch",
            f"the publication at {locator} claims world {world}; the location is bound to world {binding.world}",
            {"claimed": world, "bound": binding.world}))
    return PinSource("provider", locator)


def _discard(registry: SharingRegistry, corpus_id: str) -> None:
    """Delete a copy: its root, the engine's metadata sibling and the head artifact kept beside it."""
    root = registry.root_for(corpus_id)
    for directory in (root, metadata_root_for(root)):
        if directory.exists():
            shutil.rmtree(directory)
    registry.head_artifact_for(corpus_id).unlink(missing_ok=True)


def _require_no_overlap(ctx, registry: SharingRegistry, corpus_id: str) -> None:
    """Refuse `adopt-conflict` when the candidate shares an address with a live root: the configured roots (the
    write root among them) and the registry's admitted or mounted roots, which an adoption since this session
    opened adds. The candidate stays `fetched`."""
    candidate = {node.id for node in ReadView.opened_at(registry.root_for(corpus_id)).iter_stored()}
    configured = {root.resolve() for root in ctx.config.world.corpus_roots}
    live = list(ctx.read_views())
    live += [(pin.corpus_id, ReadView.opened_at(registry.root_for(pin.corpus_id))) for pin in registry.pins()
             if pin.state in ("admitted", "mounted") and pin.corpus_id != corpus_id
             and registry.root_for(pin.corpus_id).resolve() not in configured]
    for live_id, view in live:
        shared = sorted(candidate & {node.id for node in view.iter_stored()})
        if shared:
            raise Refused(Refusal(
                "adopt-conflict",
                f"corpus {corpus_id} shares {len(shared)} address(es) with live corpus {live_id}: "
                f"{', '.join(shared)}; {CONFLICT_REASON}",
                {"addresses": shared, "corpus": live_id, "reason": CONFLICT_REASON}))


def _kernel_refused(caught: WriteRefused) -> Refused:
    """A sharing door's refusal before its line, with the kind and what the kernel says refused it."""
    data = {"kind": type(caught).__name__}
    if isinstance(caught, SharingEvidenceDisagrees):
        data["field"] = caught.field
    elif isinstance(caught, (PublicationArrivalRefused, PublicationReadingRefused)):
        data["reason"] = caught.reason
    return Refused(Refusal("kernel-refused", str(caught), data))
