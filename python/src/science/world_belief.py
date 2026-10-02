"""Belief over a session's corpora at an epoch (consumer spec decisions 7-8).

A mounted session's belief is a world read at the current epoch, and only at
one that is current for the session: coverage equal to the session corpora's
ids, and no drift in any of them, whatever moved. `science epoch` is the operator verb that
makes one current; it reuses an epoch already current rather than rebuilding,
because a rebuild anchors a moved world chain head and mints a new identity."""
from __future__ import annotations

from dataclasses import dataclass

from beliefs.errors import AddressMapConflict, BuildContended, EpochUnknown, ResolutionRefused
from beliefs.permit import Authority, WritePermit
from beliefs.root import install_shipped_world_rules, open_world
from beliefs.world.epoch import DerivationBindings, build_epoch
from beliefs.world.read import current_epoch
from beliefs.world.rules import shipped_rule_bundles
from beliefs.world.view import WorldReadView, open_world_view

from science.refusal import Refusal, Refused

EPOCH_CODES = frozenset({"no-epoch", "epoch-stale"})
REMEDY = "run `science epoch` to publish one over the session's corpora"

# Which derivation each shipped rule's symbol fills. The rules store is keyed by
# identity and knows nothing of kinds, so the join is the caller's (beliefs
# epoch design §7.5); a symbol missing here is a KeyError, never a guess.
SYMBOL_FIELDS = {
    "derive_producer_snapshot": "producer",
    "enumerate_retractions": "retraction",
    "enumerate_certifications": "certification",
    "reduce_coreference": "coreference",
}
EPOCH_AUTHORITY = Authority(WritePermit(frozenset(), frozenset({"epoch"})), "science-epoch")


@dataclass(frozen=True)
class Current:
    epoch: object  # beliefs.world.epoch.Epoch
    view: WorldReadView


@dataclass(frozen=True)
class Published:
    state: str  # "current" | "built"
    packaging_identity: str
    coverage: tuple[tuple[str, str], ...]


def _stale(message: str, *, missing=(), extra=(), drifted=()) -> Refused:
    return Refused(Refusal("epoch-stale", f"{message}; {REMEDY}",
                           {"missing": sorted(missing), "extra": sorted(extra), "drifted": sorted(drifted)}))


def _kernel_refused(caught: Exception, *, remedy: bool = False) -> Refused:
    """A kernel refusal named like every other (consumer spec decisions 5 and
    7). `BuildContended` is a covered corpus mid-write: retryable, so no remedy
    is named; a read's `ResolutionRefused` names `science epoch`, which
    rebuilds over the present carriers."""
    message = f"{caught}; {REMEDY}" if remedy else str(caught)
    return Refused(Refusal("kernel-refused", message, {"kind": type(caught).__name__}))


def epoch_currency(world, session_ids: frozenset[str]) -> Current:
    """The current epoch and its view, when that epoch is current for the
    session; otherwise `no-epoch` or `epoch-stale`, naming the corpora."""
    try:
        published = current_epoch(world)
    except EpochUnknown:
        raise Refused(Refusal("no-epoch", f"this world has published no epoch; {REMEDY}")) from None
    covered = frozenset(corpus_id for corpus_id, _ in published.coverage)
    missing, extra = session_ids - covered, covered - session_ids
    if missing or extra:
        raise _stale(f"epoch {published.packaging_identity} covers {', '.join(sorted(covered))}, not exactly the "
                     f"session's {', '.join(sorted(session_ids))}", missing=missing, extra=extra)
    try:
        view = open_world_view(world, published)
    except BuildContended as caught:
        raise _kernel_refused(caught) from None
    except ResolutionRefused as caught:
        # A uid held by two corpora (W8b), or a mapped record its carrier no
        # longer holds at the mapped address: the kernel judges both, and
        # science names them rather than re-scanning for them.
        raise _kernel_refused(caught, remedy=True) from None
    # Strict on any move: every write after the epoch, coordination writes
    # included, changes the corpus state identity, so no drift is presumed inert
    # (plan review round 1, P1). Records the epoch left unmapped at an unchanged
    # state are kinds it excludes by design (only world kinds are mapped), not drift.
    drifted = sorted(report.corpus_id for report in view.drift()
                     if report.published_state != report.captured_state)
    if drifted:
        raise _stale(f"corpora {', '.join(drifted)} have moved since epoch {published.packaging_identity}",
                     drifted=drifted)
    return Current(published, view)


def build_over(config, coverage: frozenset[str]):
    """Install the shipped rules (idempotent: identical bytes submit nothing)
    and publish one epoch over exactly `coverage`."""
    world = open_world(config.world, authority=EPOCH_AUTHORITY)
    bindings = dict(zip((bundle.symbol for bundle in shipped_rule_bundles()),
                        install_shipped_world_rules(world), strict=True))
    fields = {field: bindings[symbol] for symbol, field in SYMBOL_FIELDS.items()}
    try:
        return build_epoch(world, coverage=coverage, bindings=DerivationBindings(**fields))
    except (BuildContended, ResolutionRefused, AddressMapConflict) as caught:
        raise _kernel_refused(caught) from None


def publish_session_epoch(config) -> Published:
    """`science epoch`: reuse the current epoch when it is current for the
    session; otherwise build one over exactly the session's corpora."""
    from science.config import ReadContext

    ctx = ReadContext.open(config)
    session_ids = ctx.session_ids()
    try:
        current = epoch_currency(ctx.world, session_ids)
    except Refused as caught:
        # The old epoch's view refusing to resolve over the present carriers
        # (a mapped record deleted or moved) is grounds to rebuild: the build
        # captures the present corpora and judges them itself. Contention is
        # retryable and a rebuild cannot help it.
        rebuildable = caught.refusal.code in EPOCH_CODES or (
            caught.refusal.code == "kernel-refused" and caught.refusal.data.get("kind") == "ResolutionRefused")
        if not rebuildable:
            raise
    else:
        return Published("current", current.epoch.packaging_identity, current.epoch.coverage)
    built = build_over(config, session_ids)
    return Published("built", built.packaging_identity, built.coverage)


def world_context(current: Current, observations, pins):
    """The supplied context of a world read (beliefs J20's recipe): lineage
    rooted at every observed dataset the epoch maps, the epoch's producer
    snapshot, and each covered corpus's pins. `gather` fills node_corpus."""
    from beliefs.belief import SuppliedContext
    from beliefs.corpus import lineage_snapshot

    view = current.view
    return SuppliedContext(
        snapshot=lineage_snapshot(view, sorted(address for address in observations if view.holds(address))),
        producer_snapshot_identity=view.producer_snapshot_identity(),
        node_corpus={},
        pins=pins,
    )
