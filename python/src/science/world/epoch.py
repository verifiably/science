"""The epoch carrier: its frozen member inventory and the receipts inside it.

A world publishes an **epoch** — a content-addressed directory holding four
derived maps, the producer snapshot, four derivation receipts, and the two
declarations that bound them — at ``epochs/<packaging_identity>/``. Slice 2's
specification §6.1 fixes that layout exactly, and `EPOCH_MEMBERS` below is that
inventory. Nothing else writes beneath ``epochs/`` except the one-line
``current`` pointer, which is a member of the *directory* ``epochs/`` and never
of an epoch.

What this module holds today is the part the rules store needs: **which
receipts a retained epoch carries, and which exact rule binding each one
names.** A receipt is what makes a derived map re-checkable, so it records the
exact ``(rule_identity, implementation_identity)`` that produced its subject
(§7.5). That makes the epochs directory the place — the only place — where a
world can answer "what evidence would I strand if I stopped holding this
pair?", which is what `science.world.rules.remove_rule_binding` must report.

A receipt identity is the digest under `RECEIPT_DOMAIN` of the canonical
projection ``(receipt kind, subject projection identity, sorted corpus-state
pairs, rule identity, implementation identity)``. The kind discriminant is what
keeps the four receipt subjects disjoint under one domain, and it is carried
*inside* the document as well as implied by the member name — a document whose
discriminant disagrees with the member holding it is malformed, because two
readings of the same receipt would then disagree about which subject it
attests.

**Deliberately not here yet.** Building, publishing, opening, selecting and
deleting epochs are later acts. This module recomputes no member digest and no
packaging identity: the scanner locates carriers and reads receipts, and full
carrier validation belongs to the open act. The receipt shape parsed here is
the identity-bearing part of §7.5, not the whole receipt — the retraction and
certification receipts additionally carry their own subject projections, which
arrive with the code that writes them.

**Layering.** Nothing here knows the rules *store*: a receipt names a binding
as two digests, and reading a receipt does not require holding what it names.
That keeps the removal act, which does need both, the only place the two meet.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

import yaml

from science.errors import EpochMalformed
from science.identity import v1
from science.world.registry import _ManifestLoader

__all__ = [
    "CURRENT_POINTER",
    "EPOCH_MEMBERS",
    "RECEIPT_DOMAIN",
    "RECEIPT_KINDS",
    "receipt_identity",
]

EPOCH_MEMBERS: tuple[str, ...] = (
    "address-map.yaml",
    "producers-map.yaml",
    "retraction-discovery-map.yaml",
    "coreference-map.yaml",
    "producer-snapshot.yaml",
    "producer-receipt.yaml",
    "retraction-receipt.yaml",
    "certification-receipt.yaml",
    "coreference-receipt.yaml",
    "anchors.yaml",
    "coverage.yaml",
)
"""Specification §6.1's closed layout, in the order it is written there.

An epoch directory contains exactly these eleven members: a missing one and an
extra one are the same failure, `EpochMalformed`. This is the module's one
declaration of the inventory; every act over epochs reads it from here.
"""

CURRENT_POINTER = "current"
"""The one-line operational pointer beside the epoch directories.

It is a member of ``epochs/``, not of an epoch, and it is a regular file rather
than a symlink. Named here so every walk of ``epochs/`` agrees about the one
entry that is not a carrier.
"""

RECEIPT_KINDS: Mapping[str, str] = MappingProxyType(
    {
        "producer-receipt.yaml": "producer",
        "retraction-receipt.yaml": "retraction-enumeration",
        "certification-receipt.yaml": "certification-enumeration",
        "coreference-receipt.yaml": "coreference-reduction",
    }
)
"""The four receipt members and the kind discriminant each one must carry."""

RECEIPT_DOMAIN = "science.derivation-receipt.v1"
"""One domain for the receipt family; §7.5's kind member keeps them disjoint."""

_RECEIPT_KEYS = frozenset({"kind", "subject", "corpus_states", "rule_identity", "implementation_identity"})
_STATE_KEYS = frozenset({"corpus_id", "corpus_state"})
_PACKAGING_IDENTITY = re.compile(r"[0-9a-f]{64}")
_LOWER_HEX = re.compile(r"[0-9a-f]+")


def receipt_identity(
    kind: str,
    subject_identity: str,
    corpus_states: tuple[tuple[str, str], ...],
    rule_identity: str,
    implementation_identity: str,
) -> str:
    """§7.5's receipt identity, over the five members that fix what ran.

    Each corpus-state pair encodes as a two-member list, the same shape the
    fixture-set pairs use, so one reading of "a pair" serves the whole slice.
    """
    return v1.digest(
        RECEIPT_DOMAIN,
        [
            kind,
            subject_identity,
            [[corpus_id, corpus_state] for corpus_id, corpus_state in corpus_states],
            rule_identity,
            implementation_identity,
        ],
    )


@dataclass(frozen=True)
class _ReceiptCarrier:
    """One receipt member of one retained epoch, reduced to what names it.

    The subject itself is not here: the identity digests the subject's
    projection identity, and severing evidence is decided by the binding, so
    the sever report never needs to reconstruct a map.
    """

    packaging_identity: str
    member: str
    kind: str
    subject_identity: str
    corpus_states: tuple[tuple[str, str], ...]
    rule_identity: str
    implementation_identity: str

    @property
    def binding(self) -> tuple[str, str]:
        """The exact pair this receipt names, as ``(rule, implementation)``.

        Two digests, compared as two digests: a receipt naming a *sibling*
        implementation of the same rule shares the first member and differs in
        the second, which is exactly the distinction removal turns on.
        """
        return (self.rule_identity, self.implementation_identity)

    @property
    def identity(self) -> str:
        return receipt_identity(
            self.kind,
            self.subject_identity,
            self.corpus_states,
            self.rule_identity,
            self.implementation_identity,
        )


def _retained_receipt_bindings_locked(world_root: Path) -> tuple[_ReceiptCarrier, ...]:
    """Every receipt carried by every retained epoch of this world.

    The caller holds the world lock; this must not take it, and the lock is not
    reentrant. Ordering is deterministic — by packaging identity, then by the
    §6.1 member order — so a report derived from this scan does not depend on
    directory iteration order.

    A world that has published nothing, or whose ``epochs/`` directory is
    empty, carries no receipt. Anything else that cannot be read as the closed
    layout is `EpochMalformed`: a caller asking what evidence it is about to
    strand is owed an answer or a refusal, never a short scan.
    """
    base = Path(world_root) / "epochs"
    if base.is_symlink():
        raise EpochMalformed(f"{base}: the epochs directory is a symbolic link")
    if not base.exists():
        return ()
    if not base.is_dir():
        raise EpochMalformed(f"{base}: the epochs directory is not a directory")
    carriers: list[_ReceiptCarrier] = []
    for entry in sorted(base.iterdir()):
        if entry.name == CURRENT_POINTER:
            if entry.is_symlink() or not entry.is_file():
                raise EpochMalformed(f"{entry}: the current pointer is not a regular file")
            continue
        if entry.is_symlink() or not entry.is_dir() or not _PACKAGING_IDENTITY.fullmatch(entry.name):
            raise EpochMalformed(f"{entry}: nothing but epoch carriers and {CURRENT_POINTER!r} lives here")
        carriers.extend(_receipts_of(entry))
    return tuple(carriers)


def _receipts_of(directory: Path) -> tuple[_ReceiptCarrier, ...]:
    """The four receipts of one closed carrier, in §6.1's member order."""
    members: dict[str, Path] = {}
    for path in directory.iterdir():
        if path.is_symlink() or not path.is_file():
            raise EpochMalformed(f"{path}: an epoch member is a regular file")
        members[path.name] = path
    if set(members) != set(EPOCH_MEMBERS):
        raise EpochMalformed(
            f"{directory}: the member set is not the closed epoch layout; "
            f"missing {sorted(set(EPOCH_MEMBERS) - set(members))}, "
            f"unexpected {sorted(set(members) - set(EPOCH_MEMBERS))}"
        )
    return tuple(
        _parse_receipt(directory.name, member, members[member].read_bytes())
        for member in EPOCH_MEMBERS
        if member in RECEIPT_KINDS
    )


def _parse_receipt(packaging_identity: str, member: str, content: bytes) -> _ReceiptCarrier:
    """One receipt document, closed over §7.5's five identity-bearing members."""
    try:
        document = yaml.load(content.decode("utf-8"), Loader=_ManifestLoader)
        if type(document) is not dict or set(document) != _RECEIPT_KEYS:
            raise ValueError(f"a receipt must have exactly {sorted(_RECEIPT_KEYS)}")
        if document["kind"] != RECEIPT_KINDS[member]:
            raise ValueError(f"kind {document['kind']!r} does not discriminate this member")
        return _ReceiptCarrier(
            packaging_identity,
            member,
            RECEIPT_KINDS[member],
            _require_digest(document["subject"], 64, "subject"),
            _corpus_states(document["corpus_states"]),
            _require_digest(document["rule_identity"], 64, "rule_identity"),
            _require_digest(document["implementation_identity"], 64, "implementation_identity"),
        )
    except Exception as caught:
        raise EpochMalformed(f"{packaging_identity}/{member}: {caught}") from caught


def _corpus_states(value: object) -> tuple[tuple[str, str], ...]:
    """The captured corpus-state identity for every covered corpus.

    Stored sorted and distinct, and read back the same way: the receipt
    identity digests this sequence, so a document free to spell one covered set
    two ways would be free to name one receipt two identities.
    """
    if type(value) is not list:
        raise ValueError("corpus_states must be a list")
    states: list[tuple[str, str]] = []
    for entry in value:
        if type(entry) is not dict or set(entry) != _STATE_KEYS:
            raise ValueError(f"a corpus state must have exactly {sorted(_STATE_KEYS)}")
        states.append(
            (
                _require_digest(entry["corpus_id"], 32, "corpus_id"),
                _require_digest(entry["corpus_state"], 64, "corpus_state"),
            )
        )
    if states != sorted(states) or len({corpus_id for corpus_id, _state in states}) != len(states):
        raise ValueError("corpus_states must be sorted and name each corpus once")
    return tuple(states)


def _require_digest(value: object, length: int, location: str) -> str:
    if type(value) is not str or len(value) != length or not _LOWER_HEX.fullmatch(value):
        raise ValueError(f"{location} must be {length} lowercase hexadecimal characters")
    return value
