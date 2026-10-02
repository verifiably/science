"""Belief over a session's corpora at an epoch (consumer spec decisions 7-8).

A mounted session's belief is a world read at the current epoch, and only at
one that is current for the session: coverage equal to the session corpora's
ids, and no drift in any of them, whatever moved. `science epoch` is the operator verb that
makes one current; it reuses an epoch already current rather than rebuilding,
because a rebuild anchors a moved world chain head and mints a new identity."""
from __future__ import annotations

from dataclasses import dataclass

from beliefs.errors import BuildContended, EpochUnknown
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


def _contended(caught: BuildContended) -> Refused:
    """A covered corpus mid-write: retryable, named like every kernel refusal
    (consumer spec decisions 5 and 7)."""
    return Refused(Refusal("kernel-refused", str(caught), {"kind": "BuildContended"}))


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
        raise _contended(caught) from None
    # Strict: any drift, coordination writes included. The view checks mapped
    # addresses and uids, not content, so no drift can be proved inert today
    # (plan review round 1, P1; spec limitation 2).
    drifted = sorted(report.corpus_id for report in view.drift())
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
    except BuildContended as caught:
        raise _contended(caught) from None


def publish_session_epoch(config) -> Published:
    """`science epoch`: reuse the current epoch when it is current for the
    session; otherwise build one over exactly the session's corpora."""
    from science.config import ReadContext

    ctx = ReadContext.open(config)
    session_ids = ctx.session_ids()
    try:
        current = epoch_currency(ctx.world, session_ids)
    except Refused as caught:
        if caught.refusal.code not in EPOCH_CODES:
            raise
    else:
        return Published("current", current.epoch.packaging_identity, current.epoch.coverage)
    built = build_over(config, session_ids)
    return Published("built", built.packaging_identity, built.coverage)
