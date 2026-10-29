"""adopt: fetch a publication from a provider's bound location, verify it, source it, check its layout and
conflicts, then admit and mount it (commons spec §4.3 step 3, §10). Every registry write follows the sharing line
that is its evidence, and nothing survives a refusal before `fetched` (plan Deviation 9): the copy is deleted and
no pin is written."""
from __future__ import annotations

import shutil
from hashlib import sha256

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

from science import publication, supersession
from science.config import live_mounts
from science.refusal import Refusal, Refused
from science.report import Finding, KeyVals, Report
from science.overlap import conflicts
from science.retention import required
from science.sharing import Pin, PinSource, SharingRegistry, apply_line, replay, sharing_lines

RETIREMENT_PENDING = "retirement pending: the kernel's retire door (beliefs-a989fb) has not landed"


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
        """Track writes for recovery, then project the ledger evidence into the registry."""
        lines.append(line)
        apply_line(registry, line)

    tail = []
    _reconcile(ctx, writer, registry, record, tail)
    pin = registry.pin(corpus_id)
    already_mounted = pin is not None and pin.state == "mounted"
    if pin is not None and pin.state == "retired":
        raise _already_adopted(pin)
    if not already_mounted:
        root = registry.root_for(corpus_id)
        if pin is not None and pin.fetch.location != destination.locator:
            raise Refused(Refusal(
                "invalid-input", f"corpus {corpus_id} was fetched from {pin.fetch.location}, not {destination.locator}; "
                f"adopt it from {pin.fetch.location}", {"location": pin.fetch.location}))
        if pin is not None and root.is_dir() and registry.head_artifact_for(corpus_id).is_file():
            evidence = _evidence(pin)
            observers = _observers(registry.head_artifact_for(corpus_id).read_bytes())
        else:
            evidence, observers = _fetch(writer, transport, destination, registry, corpus_id, record)
        candidate = supersession.Held(corpus_id, root, publication.marker_fields(publication.marker_of(root)), "mounted")
        history = sharing_lines(config.operations_root)
        groups = supersession.groups(registry, history)
        held = groups.get(supersession.group_of(candidate.marker), ())
        mounts = live_mounts(config, ctx.world, registry)
        conflict = conflicts(ReadView.opened_at(root), [(mount.corpus_id, mount.view) for mount in mounts])
        if conflict is not None:
            message = (f"corpus {corpus_id} conflicts with live corpus {conflict.corpus}: "
                       f"{conflict.rule} at {', '.join(conflict.addresses)}")
            predecessor = next((item for item in held if item.corpus_id == conflict.corpus), None)
            if predecessor is not None:
                path = supersession.chain(_pair(predecessor), _pair(candidate), (*held, candidate))
                if path is not None:
                    reasons = _required(ctx, predecessor, (*held, candidate), _pair(candidate), groups, mounts)
                    if reasons:
                        message += "; required predecessor: " + ", ".join(map(_reason, reasons))
            raise Refused(Refusal("adopt-conflict", message,
                                  {"rule": conflict.rule, "addresses": list(conflict.addresses), "corpus": conflict.corpus}))
        _preflight(held, candidate, history)
        try:
            admitted = writer.admit_publication(root, observers, evidence=evidence)
        except WriteRefused as caught:
            raise _kernel_refused(caught) from None
        record(admitted)
        _mark_mounted(writer, registry.pin(corpus_id), record)
    tail.extend(_reevaluate(ctx, registry))
    if already_mounted and not lines:
        raise _already_adopted(pin)
    return tuple(tail)


def _already_adopted(pin):
    return Refused(Refusal("invalid-input", f"corpus {pin.corpus_id} is already adopted: its pin is {pin.state}",
                          {"corpus_id": pin.corpus_id, "state": pin.state}))


def _reconcile(ctx, writer, registry: SharingRegistry, record, tail) -> None:
    state = ctx.world.registry()
    admitted = {admission.corpus_id for admission in state.admissions}
    terminal = {item.corpus_id: item.status for item in state.statuses}
    for pin in registry.pins():
        if pin.state in ("fetched", "admitted") and pin.corpus_id in admitted:
            _mark_mounted(writer, pin, record)
        elif pin.state == "mounted":
            status = ctx.world.status(pin.corpus_id)
            if status.known and not status.live:
                if terminal.get(pin.corpus_id) == "retired":
                    tail.append(Finding(f"{pin.corpus_id}: {RETIREMENT_PENDING}"))
                elif terminal.get(pin.corpus_id) == "departed":
                    tail.append(Finding(f"corpus {pin.corpus_id} departed"))


def _pair(item):
    return item.corpus_id, item.marker.uid


def _preflight(held, candidate, history):
    outcome = supersession.classify(held, candidate)
    if outcome.kind == "divergent":
        tips = [list(pair) for pair in outcome.tips]
        raise Refused(Refusal("divergent-publication", f"divergent publication sibling tips: {tips}", {"tips": tips}))
    items = (*held, candidate)
    targets = {_pair(item) for item in held if item.state == "mounted"}
    current = supersession.current(history, held)
    if current is not None:
        targets.add(current)
    for target in sorted(targets):
        path = (supersession.chain(_pair(candidate), target, items)
                or supersession.chain(target, _pair(candidate), items))
        if path is not None:
            retired = next((item for item in held if item.state == "retired" and _pair(item) in path[1:-1]), None)
            if retired is not None:
                raise Refused(Refusal("adopt-conflict", f"chain-retired: the chain passes through retired corpus {retired.corpus_id}",
                                      {"rule": "chain-retired", "addresses": [], "corpus": retired.corpus_id}))


def _reason(reason):
    if reason.kind == "configuration":
        return "configuration"
    if reason.kind == "chain":
        return f"chain (for {reason.detail[0]})"
    if reason.kind == "attribution":
        return f"attribution (named by {reason.detail[0]})"
    return f"dependency ({', '.join(reason.detail)})"


def _required(ctx, predecessor, held, tip, groups, mounts):
    write = next(mount for mount in mounts if mount.root == ctx.config.write_root)
    holders = [(mount.corpus_id, mount.view, mount.profile) for mount in mounts if mount != write]
    live_ids = {mount.corpus_id for mount in mounts}
    return required(predecessor, keep=ctx.config.keep, group_chain=held, tip=tip,
                    mounted=tuple(item for group in groups.values() for item in group
                                  if item.state == "mounted" and item.corpus_id in live_ids),
                    write_root=(write.corpus_id, write.view, write.profile), live=holders)


def _reevaluate(ctx, registry):
    config = ctx.config
    groups = supersession.groups(registry, sharing_lines(config.operations_root))
    mounts = live_mounts(config, ctx.world, registry)
    tail = [Finding(f"keep entry {corpus}: no pin records this corpus") for corpus in config.keep
            if registry.pin(corpus) is None]
    for held in groups.values():
        outcome = supersession.classify(held)
        if outcome.kind != "resolved":
            continue
        paths = {_pair(item): supersession.chain(_pair(item), outcome.tip, held) for item in held}
        predecessors = sorted((item for item in held if item.state == "mounted" and _pair(item) != outcome.tip
                               and paths[_pair(item)] is not None), key=lambda item: (-len(paths[_pair(item)]), item.corpus_id))
        for predecessor in predecessors:
            if not ctx.world.status(predecessor.corpus_id).live:
                continue  # Reconcile already reported this completed terminal effect.
            reasons = _required(ctx, predecessor, held, outcome.tip, groups, mounts)
            if reasons:
                tail.append(KeyVals(f"retention {predecessor.corpus_id}", tuple(("kept", _reason(reason)) for reason in reasons)))
            else:
                _require_current_config(config)
                tail.append(Finding(f"{predecessor.corpus_id}: {RETIREMENT_PENDING}"))
    return tail


def _require_current_config(config):
    if config.source is None:
        return
    path, digest = config.source
    if sha256(path.read_bytes()).hexdigest() != digest:
        raise Refused(Refusal("config-stale", f"configuration {path} changed; evaluated keep {list(config.keep)}; "
                              "the adoption stands; restart the service and rerun adopt",
                              {"path": str(path), "keep": list(config.keep)}))


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
    """The bytes came from `locator` in this invocation, so a binding of the world the marker claims that holds
    `locator` earns the pin its source. A location may be bound to several worlds: only the claimed world's binding
    is consulted, and the others name the refusal when it holds no such binding."""
    bindings = registry.bindings()
    binding = bindings.get(world)
    if binding is not None and locator in binding.locations:
        return PinSource("provider", locator)
    bound = sorted(b.world for b in bindings.values() if locator in b.locations)
    if not bound:
        raise Refused(Refusal(
            "pin-unsourced",
            f"the publication at {locator} claims world {world}, and nothing sources it: bind the location to that "
            "world with `provider-bind`, or `follow` a catalog that names the corpus",
            {"world": world}))
    raise Refused(Refusal(
        "world-mismatch",
        f"the publication at {locator} claims world {world}; the location is bound to world(s) {', '.join(bound)}",
        {"claimed": world, "bound": bound}))


def _discard(registry: SharingRegistry, corpus_id: str) -> None:
    """Delete a copy: its root, the engine's metadata sibling and the head artifact kept beside it."""
    root = registry.root_for(corpus_id)
    for directory in (root, metadata_root_for(root)):
        if directory.exists():
            shutil.rmtree(directory)
    registry.head_artifact_for(corpus_id).unlink(missing_ok=True)


def _kernel_refused(caught: WriteRefused) -> Refused:
    """A sharing door's refusal before its line, with the kind and what the kernel says refused it."""
    data = {"kind": type(caught).__name__}
    if isinstance(caught, SharingEvidenceDisagrees):
        data["field"] = caught.field
    elif isinstance(caught, (PublicationArrivalRefused, PublicationReadingRefused)):
        data["reason"] = caught.reason
    return Refused(Refusal("kernel-refused", str(caught), data))
