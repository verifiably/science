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
keeps the four receipt subjects disjoint under one domain. It is carried
*inside* the document as well as implied by the member name, and the identity
digests the document's own value: a document whose discriminant disagrees with
the member holding it still has one identity, and which of the two readings is
wrong is the validator's finding to make.

**Two layers, and this module is the lower one** (§8.2). Reading a receipt out
of a carrier and judging whether that receipt honours its contract are separate
questions with separate outcomes. What refuses here is *structural
unreadability*: bytes that are not a YAML mapping, a duplicate key, or a
document from which the five identity-bearing members of §7.5 cannot be lifted
as strings. Everything a reader can still lift a binding out of is handed on
intact — a discriminant disagreeing with its member, a value that is not an
identity, an unsorted or repeated corpus state, a key outside the kind's
declared set. Those are receipt-contract violations, and §8.2 assigns them
receipt outcome ``malformed``, not `EpochMalformed`. Turning one into a carrier
failure would close the path §8.2 exists to keep open, where a malformed
coreference receipt opens, evaluates as ``malformed``, and leaves its edges
``indeterminate``.

`RECEIPT_KEYS` therefore *declares* the closed per-kind contract without
enforcing it: the receipt validator is what enforces it. The two
projection-bearing kinds carry more than the identity members — §7.5 puts the
retraction enumeration projection inside the retraction receipt and the
certification inventory inside the certification receipt — so one closed set
across all four kinds would be wrong in both directions at once.

**Deliberately not here yet.** Building, publishing, opening, selecting and
deleting epochs are later acts. This module recomputes no member digest and no
packaging identity: the scanner locates carriers and reads receipts, and full
carrier validation belongs to the open act.

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
    "RECEIPT_IDENTITY_KEYS",
    "RECEIPT_KEYS",
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

RECEIPT_IDENTITY_KEYS: frozenset[str] = frozenset(
    {"kind", "subject", "corpus_states", "rule_identity", "implementation_identity"}
)
"""The five members every receipt carries, and the only ones its identity
digests. They are what this layer must be able to lift out of a document; a
document it cannot lift them from is unreadable rather than merely wrong."""

RECEIPT_KEYS: Mapping[str, frozenset[str]] = MappingProxyType(
    {
        "producer-receipt.yaml": RECEIPT_IDENTITY_KEYS,
        "retraction-receipt.yaml": RECEIPT_IDENTITY_KEYS | {"enumeration"},
        "certification-receipt.yaml": RECEIPT_IDENTITY_KEYS | {"inventory"},
        "coreference-receipt.yaml": RECEIPT_IDENTITY_KEYS,
    }
)
"""The closed key set each receipt kind's document carries — §7.5's contract.

The two projection-bearing kinds carry one member more than the identity
members: the retraction receipt holds its retraction enumeration projection
(``enumeration``) and the certification receipt its location-free,
resolution-free inventory (``inventory``), neither of which is a further epoch
member. Their subject *projections* are read and checked by the receipt
validator, which is also what enforces this closure as outcome ``malformed``
(§8.2). The carrier layer below declares the contract and does not police it.
"""

_STATE_KEYS = ("corpus_id", "corpus_state")
_PACKAGING_IDENTITY = re.compile(r"[0-9a-f]{64}")


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
    The formula names *sorted* pairs, so the sort belongs here rather than to
    whoever assembled the sequence — `rules.fixture_set_identity` orders its
    members for the same reason.
    """
    return v1.digest(
        RECEIPT_DOMAIN,
        [
            kind,
            subject_identity,
            [[corpus_id, corpus_state] for corpus_id, corpus_state in sorted(corpus_states)],
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
    """The discriminant the *document* carries, which is what the identity
    digests. `RECEIPT_KINDS[member]` is what it should be; whether the two
    agree is the validator's question, not this layer's."""
    subject_identity: str
    corpus_states: tuple[tuple[str, str], ...]
    """As the document orders them. `receipt_identity` sorts."""
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
    """Lift §7.5's five identity-bearing members out of one receipt document.

    This is the structural floor and nothing above it. It refuses only what
    leaves no receipt to hand on: bytes that are not a YAML mapping, a
    duplicate key, an absent identity member, or one whose value is not the
    string the identity formula digests. What it does **not** check is the
    receipt *contract* — that the discriminant matches the member, that the
    keys are exactly `RECEIPT_KEYS[member]`, that each digest is an identity,
    that the corpus states are sorted and distinct. Those are §8.2's receipt
    outcome ``malformed``, and the validator that decides them reuses this
    extraction without inheriting a refusal policy that would hide them.
    """
    try:
        document = yaml.load(content.decode("utf-8"), Loader=_ManifestLoader)
        if type(document) is not dict:
            raise ValueError("a receipt is a mapping")
        missing = sorted(RECEIPT_IDENTITY_KEYS - set(document))
        if missing:
            raise ValueError(f"a receipt carries {sorted(RECEIPT_IDENTITY_KEYS)}; missing {missing}")
        return _ReceiptCarrier(
            packaging_identity,
            member,
            _require_text(document["kind"], "kind"),
            _require_text(document["subject"], "subject"),
            _corpus_states(document["corpus_states"]),
            _require_text(document["rule_identity"], "rule_identity"),
            _require_text(document["implementation_identity"], "implementation_identity"),
        )
    except Exception as caught:
        raise EpochMalformed(f"{packaging_identity}/{member}: {caught}") from caught


def _corpus_states(value: object) -> tuple[tuple[str, str], ...]:
    """The captured corpus-state pair for every covered corpus, as written.

    Sortedness and distinctness are contract, not structure: an unsorted or
    repeated sequence is still a sequence of pairs, and `receipt_identity`
    sorts what it digests. Only a shape with no pair in it refuses.
    """
    if type(value) is not list:
        raise ValueError("corpus_states is a list")
    states: list[tuple[str, str]] = []
    for entry in value:
        if type(entry) is not dict or any(key not in entry for key in _STATE_KEYS):
            raise ValueError(f"a corpus state carries {list(_STATE_KEYS)}")
        states.append(
            (
                _require_text(entry["corpus_id"], "corpus_id"),
                _require_text(entry["corpus_state"], "corpus_state"),
            )
        )
    return tuple(states)


def _require_text(value: object, location: str) -> str:
    """An identity-bearing member is a string. *Which* string — an identity, a
    known discriminant — is the validator's question; that it is text at all is
    this layer's, because the digest is over text."""
    if type(value) is not str:
        raise ValueError(f"{location} is text, not {type(value).__name__}")
    return value
