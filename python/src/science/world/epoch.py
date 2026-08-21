"""The epoch carrier: its frozen member inventory and the receipts inside it.

A world publishes an **epoch** — a content-addressed directory holding four
derived maps, the producer snapshot, four derivation receipts, and the two
declarations that bound them — at ``epochs/<packaging_identity>/``. Slice 2's
specification §6.1 fixes that layout exactly, and `EPOCH_MEMBERS` below is that
inventory. Nothing else writes beneath ``epochs/`` except the one-line
``current`` pointer, which is a member of the *directory* ``epochs/`` and never
of an epoch.

**Two things live here, and they meet only at the draft.** The first is the
part the rules store needs: **which receipts a retained epoch carries, and
which exact rule binding each one names.** A receipt is what makes a derived
map re-checkable, so it records the exact
``(rule_identity, implementation_identity)`` that produced its subject (§7.5).
That makes the epochs directory the place — the only place — where a world can
answer "what evidence would I strand if I stopped holding this pair?", which is
what `science.world.rules.remove_rule_binding` must report.

The second is a build's **coherent preflight and capture** (§5.2, §5.3), at the
bottom of this module: the two acts that read live state, and the frozen
`_BuildDraft` that separates them from everything pure. They are here rather
than beside the derivations because an epoch is what they are gathering the
inputs for, and because the draft's shape — anchors, coverage, captured states,
the build-start world head — is §6.1's layout read backwards.

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
unreadability*: bytes that are not a YAML mapping, a duplicate key, or a value
that is present and is not the text the identity formula digests. Everything a
reader can still lift *something* out of is handed on intact — a discriminant
disagreeing with its member, a value that is not an identity, an unsorted or
repeated corpus state, a key outside the kind's declared set, and an identity
member the document simply omits. Those are receipt-contract violations, and
§8.2's carrier list is closed and names none of them: it is "invalid YAML, a
missing or extra epoch **member**, a bad member content name, or a
packaging-identity mismatch", where a member is one of the eleven files. A
missing receipt *key* is §7.5's own closing sentence instead — "An unsound
receipt contract is ``malformed``" — and turning one into a carrier failure
would close the path §8.2 exists to keep open, where a malformed coreference
receipt opens, evaluates as ``malformed``, and leaves its edges
``indeterminate``.

An omitted identity member is therefore read as *absent*, not as a refusal:
`_ReceiptCarrier` holds each of the five as optional and `missing` names the
ones the document did not carry, which is exactly the finding the validator
has to report. Such a receipt has no identity — there is nothing to digest —
and it names no binding, which is the honest answer rather than a convenient
one: §7.5 puts an unsound contract at ``malformed`` before resolvability is
ever asked, so no act that changes what a store *holds* can move its outcome.

`RECEIPT_KEYS` therefore *declares* the closed per-kind contract without
enforcing it: the receipt validator is what enforces it. The two
projection-bearing kinds carry more than the identity members — §7.5 puts the
retraction enumeration projection inside the retraction receipt and the
certification inventory inside the certification receipt — so one closed set
across all four kinds would be wrong in both directions at once.

**Deliberately not here yet.** Publishing, opening, selecting and deleting
epochs are later acts, and so is the pure derivation between capture and
publication. This module recomputes no member digest and no packaging identity:
the scanner locates carriers and reads receipts, full carrier validation
belongs to the open act, and a build stops at its draft.

**Layering.** The *carrier* half knows nothing of the rules store: a receipt
names a binding as two digests, and reading a receipt does not require holding
what it names. The build half does need the store — preflight resolves four
exact pairs and runs their fixtures — and reaches it through
`science.world.rules` at call time, which is also what keeps the import cycle
between the two modules resolvable in every order.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import cast

import yaml

from science import stored
from science.corpus import ReadView, _acyclic_postorder, _root_state_for, _validated_retraction_facet
from science.errors import (
    CaptureDrift,
    CoverageNotLive,
    CoverageUnknown,
    CoverageUnresolvable,
    EnumeratedKindUngoverned,
    EpochMalformed,
)
from science.identity import v1

# Module form, and every use below is at call time. `derive` and `rules` both
# import this module back, and only the module form survives every import
# order: a name-form import of either would bind at *this* module's import
# time, which is exactly the moment the partially-initialised cycle cannot
# satisfy. Nothing here may touch `derive.<name>` or `rules.<name>` at module
# level for the same reason.
from science.world import derive, registry, rules

__all__ = [
    "CURRENT_POINTER",
    "DERIVATION_KINDS",
    "ENUMERATED_SOURCE_KINDS",
    "EPOCH_MEMBERS",
    "RECEIPT_DOMAIN",
    "RECEIPT_IDENTITY_KEYS",
    "RECEIPT_KEYS",
    "RECEIPT_KINDS",
    "RETRACTION_RESOLUTIONS",
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

    Each of the five identity members is optional, because a document may
    simply omit one and that is a receipt-contract fault rather than an
    unreadable carrier (§7.5, §8.2). `missing` names what was omitted; a
    receipt missing anything has no `identity` and names no `binding`.
    """

    packaging_identity: str
    member: str
    kind: str | None
    """The discriminant the *document* carries, which is what the identity
    digests. `RECEIPT_KINDS[member]` is what it should be; whether the two
    agree is the validator's question, not this layer's."""
    subject_identity: str | None
    corpus_states: tuple[tuple[str, str], ...] | None
    """As the document orders them; `receipt_identity` sorts. `None` is the
    member being absent, which an empty coverage is not."""
    rule_identity: str | None
    implementation_identity: str | None

    @property
    def missing(self) -> tuple[str, ...]:
        """The identity members this document did not carry, by document key.

        Empty for a receipt whose contract is sound this far. Non-empty is the
        validator's ``malformed`` finding, ready to report.
        """
        return tuple(
            key
            for key, value in (
                ("corpus_states", self.corpus_states),
                ("implementation_identity", self.implementation_identity),
                ("kind", self.kind),
                ("rule_identity", self.rule_identity),
                ("subject", self.subject_identity),
            )
            if value is None
        )

    @property
    def binding(self) -> tuple[str, str] | None:
        """The exact pair this receipt names, as ``(rule, implementation)``,
        or `None` where it named no pair.

        Two digests, compared as two digests: a receipt naming a *sibling*
        implementation of the same rule shares the first member and differs in
        the second, which is exactly the distinction removal turns on.
        """
        if self.rule_identity is None or self.implementation_identity is None:
            return None
        return (self.rule_identity, self.implementation_identity)

    @property
    def identity(self) -> str | None:
        """This receipt's identity, or `None` where the document carried too
        little to have one. An identity over invented members would be an
        identity for a receipt nobody wrote."""
        binding = self.binding
        if self.kind is None or self.subject_identity is None or self.corpus_states is None or binding is None:
            return None
        return receipt_identity(self.kind, self.subject_identity, self.corpus_states, *binding)


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
    duplicate key, or a member that is present and is not the shape the
    identity formula digests. An *absent* identity member is lifted as `None`
    rather than refused — the document still parsed, and §7.5 assigns an
    unsound receipt contract to outcome ``malformed``.

    What this does **not** check is the receipt *contract* — that every
    identity member is there, that the discriminant matches the member, that
    the keys are exactly `RECEIPT_KEYS[member]`, that each digest is an
    identity, that the corpus states are sorted and distinct. Those are §8.2's
    receipt outcome ``malformed``, and the validator that decides them extends
    this extraction without inheriting a refusal policy that would hide them.
    Recovering any of it by catching `EpochMalformed` would put the policy back
    in the layer this split exists to take it out of.
    """
    try:
        document = yaml.load(content.decode("utf-8"), Loader=registry._ManifestLoader)
        if type(document) is not dict:
            raise ValueError("a receipt is a mapping")
        states = document.get("corpus_states")
        return _ReceiptCarrier(
            packaging_identity,
            member,
            _lift_text(document, "kind"),
            _lift_text(document, "subject"),
            None if states is None else _corpus_states(states),
            _lift_text(document, "rule_identity"),
            _lift_text(document, "implementation_identity"),
        )
    except Exception as caught:
        raise EpochMalformed(f"{packaging_identity}/{member}: {caught}") from caught


def _lift_text(document: dict[object, object], key: str) -> str | None:
    """One identity member as written, or `None` where it was not written.

    A YAML ``null`` and an omitted key are the same absence here: neither is
    the text the identity digests, and neither is a carrier failure.
    """
    value = document.get(key)
    return None if value is None else _require_text(value, key)


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


# --- coherent preflight and capture (§5.2, §5.3) ------------------------------
#
# The two halves of an epoch build that touch live state, and the frozen draft
# that separates them from everything pure. Preflight answers "may this build
# run, over exactly these corpora, with exactly these four rules" while holding
# the world lock. Capture then takes each covered corpus's operation lock in
# turn and, under that one exclusion, reads its chain head, its corpus-state
# identity, its stored nodes, and its corpus-state identity again.
#
# Publication is not here. What leaves is `_BuildDraft`, and the discipline it
# encodes is that nothing downstream can re-read a corpus: the draft carries no
# carrier path, no view and no handle, so a derivation that wanted to peek at
# live state would have to be handed one by its caller.

DERIVATION_KINDS: tuple[str, ...] = tuple(
    RECEIPT_KINDS[member] for member in EPOCH_MEMBERS if member in RECEIPT_KINDS
)
"""§5.2's four derivations, keyed as §7.5 keys their receipts, in §6.1's order.

Derived from the member inventory rather than written out again: a build input
that named three kinds, or a fifth, has not described an epoch, and the one
place that says which four there are is `RECEIPT_KINDS`.
"""

ENUMERATED_SOURCE_KINDS: tuple[str, ...] = (
    "coreference-attestation",
    "instrument-certification",
    "retraction",
    "run",
)
"""The stored kinds the four epoch derivations read a record *as*.

A `run` contributes its `produces` edges to the producer snapshot, a
`retraction` its target and resolution to the enumeration and the discovery
map, and the remaining two would contribute a certification and a coreference
attestation. Membership here is what makes a kind's governance a build's
business: every other stored kind contributes only its address and `uid`, which
the address map reads without any contract for the record's fields.

This is deliberately not a blocklist of the two deferred kinds. The refusal is
computed against `stored.SEMANTIC_DOMAINS`, so the day either kind gains its
charter and a governed stored-kind definition, the refusal stops firing without
an edit here — and a *new* enumerated kind that arrives ungoverned starts
refusing without one either.
"""

RETRACTION_OVERTURNED = "overturned"
RETRACTION_UPHELD = "upheld"
RETRACTION_RESOLUTIONS: tuple[str, ...] = (RETRACTION_OVERTURNED, RETRACTION_UPHELD)
"""The closed resolution vocabulary a capture attaches to a found retraction.

`derive.CapturedRetraction` takes the resolution as opaque non-empty text
because a pure derivation has no way to decide one; capture does, and closing
the vocabulary here is what stops two builds of one corpus from spelling the
same corpus-local judgement differently and minting two enumeration identities
for it. A retraction is `upheld` when nothing in its own corpus retracts it and
`overturned` when something standing does — exactly
`corpus.standing_in_local_view`'s judgement, which is corpus-local and
non-authoritative by design.
"""


@dataclass(frozen=True)
class _Anchor:
    """One `(subject, genesis_digest, head_digest)` triple, as §6.1 stores it.

    The subject is a covered `corpus_id` for a corpus anchor and the world id
    for the build-start world anchor. The two digests are exactly what the
    injected callback returned: this layer never learns what an entry is.
    """

    subject: str
    genesis_digest: str
    head_digest: str


@dataclass(frozen=True)
class _Preflight:
    """What §5.2 retains for the rest of one build.

    `carriers` is the pinned `corpus_id -> carrier root` mapping, in sorted id
    order, and it is pinned rather than re-derived: a build that resolved a
    carrier twice could capture one corpus and anchor another.
    """

    coverage: tuple[str, ...]
    carriers: Mapping[str, Path]
    world_anchor: _Anchor
    held: Mapping[str, rules._HeldRule]

    def __post_init__(self) -> None:
        object.__setattr__(self, "carriers", MappingProxyType(dict(self.carriers)))
        object.__setattr__(self, "held", MappingProxyType(dict(self.held)))


@dataclass(frozen=True)
class _BuildDraft:
    """Everything one build carries out of its holds, and nothing else.

    Captured values, the per-corpus anchors, the declared coverage and its
    captured states, the build-start world head, and the four exact rules as
    resolved — their bytes and the entry point loaded from those bytes.

    There is no carrier path here, and that absence is the point. §5.3's "only
    captured values leave the hold" is not a convention a publisher has to
    remember if the draft simply has nowhere to put a root: derivation and
    publication cannot re-read a corpus because they are not told where one is.
    """

    coverage: tuple[str, ...]
    capture: derive.Capture
    anchors: tuple[_Anchor, ...]
    world_anchor: _Anchor
    held: Mapping[str, rules._HeldRule]

    def __post_init__(self) -> None:
        object.__setattr__(self, "held", MappingProxyType(dict(self.held)))

    @property
    def corpus_states(self) -> tuple[tuple[str, str], ...]:
        """The one sorted `(corpus_id, corpus_state)` sequence every receipt of
        this epoch carries. One value, not four: §7.5 requires the four
        receipts to agree, and there is nowhere here for a per-kind state."""
        return self.capture.corpus_states

    @property
    def bindings(self) -> Mapping[str, tuple[str, str]]:
        """Each derivation's exact `(rule_identity, implementation_identity)`,
        ready for `derive.derivation_receipts`."""
        return MappingProxyType(
            {
                kind: (held.binding.rule_identity, held.binding.implementation_identity)
                for kind, held in self.held.items()
            }
        )

    def run(self, kind: str) -> object:
        """Run one resolved derivation over the one captured projection.

        Every kind is handed the same `rule_input()` value, which is what makes
        "enumerated once, fed to all four" a property of the draft rather than
        of whoever remembers to reuse the argument.
        """
        return self.held[kind].invoke(self.capture.rule_input())


def _declared_coverage(coverage: frozenset[str]) -> tuple[str, ...]:
    """The declared covered ids, sorted. Never the registry's live set.

    §5.2's closing sentence is a rule about what a build may *substitute*, and
    the only way to keep it is to have no path that reads liveness as a
    default. The caller declares; this checks the shape and orders it.
    """
    if not isinstance(coverage, (frozenset, set)):
        raise TypeError("a build's coverage is a set of stable corpus ids")
    return tuple(sorted(registry._require_lower_hex(corpus_id, 32, "corpus_id") for corpus_id in coverage))


def _declared_bindings(bindings: Mapping[str, rules.RuleBinding]) -> Mapping[str, rules.RuleBinding]:
    """Exactly one exact pair per receipt kind. Three is not an epoch."""
    if set(bindings) != set(DERIVATION_KINDS):
        raise ValueError(
            f"a build names one exact rule binding per receipt kind {sorted(DERIVATION_KINDS)}; "
            f"got {sorted(bindings)}"
        )
    for kind, binding in bindings.items():
        if type(binding) is not rules.RuleBinding:
            raise TypeError(f"the {kind!r} binding must be an exact RuleBinding")
    return MappingProxyType(dict(bindings))


def _preflight(
    world: registry.World,
    *,
    coverage: frozenset[str],
    bindings: Mapping[str, rules.RuleBinding],
) -> _Preflight:
    """§5.2, in the order §5.2 writes it, under `_WorldState.lock` throughout.

    The chain read comes first and completes recovery, so every world file
    inspected below is inspected after recovery rather than beside it. The
    registry rescan follows; then, for each covered id in sorted order,
    admission, liveness and carrier uniqueness — in that order, so that a
    world with two faults reports the one that is decided first rather than the
    one that happens to be cheapest to find. The four exact bindings resolve
    last, with their fixtures run, because a build whose coverage is
    inadmissible has no business executing rule content at all.

    The world lock is plain and blocking. Holding it across a registry rescan
    and four fixture runs is short and serializes against registry appends and
    rule removal; §5.1's no-queueing rule is about corpus capture and does not
    reach here.
    """
    covered = _declared_coverage(coverage)
    declared = _declared_bindings(bindings)
    config = world.config
    with world._state.lock:
        genesis_digest, head_digest = world._chain_head(config.world_root)
        world._state.registry = registry._scan_registry(config.world_root)
        view = world._state.registry
        carriers: dict[str, Path] = {}
        for corpus_id in covered:
            if not any(record.corpus_id == corpus_id for record in view.admissions):
                raise CoverageUnknown(
                    f"{corpus_id}: declared coverage names a corpus this world has not admitted"
                )
            if any(record.corpus_id == corpus_id for record in view.statuses):
                raise CoverageNotLive(f"{corpus_id}: declared coverage names a corpus with terminal status")
            roots = registry._carrier_roots(config, corpus_id)
            if len(roots) != 1:
                detail = ",".join(sorted(str(root) for root in roots)) or "none"
                raise CoverageUnresolvable(
                    f"{corpus_id}: exactly one configured carrier root is required; carriers={detail}"
                )
            carriers[corpus_id] = roots[0]
        held = rules._locked_resolve_rule_bindings(config.world_root, declared)
    return _Preflight(covered, carriers, _Anchor(config.world_id, genesis_digest, head_digest), held)


def _capture(world: registry.World, preflight: _Preflight) -> _BuildDraft:
    """§5.3: sorted, serial, and one hold per corpus.

    The whole of a corpus's coherent capture — chain head, state, enumeration,
    state again — happens inside `capture()`, which never waits: a build that
    queued behind a corpus operation could park the writer queue behind itself.
    Serial rather than concurrent, because holding several corpora's operation
    locks at once is a lock order this layer would then have to own, and the
    coherence guarantee is per corpus and gains nothing from overlap.

    The drift comparison is inside the hold so the refusal is attributable to
    it, and it discards by simply not returning: no partial draft exists to be
    salvaged, and there is no retry. Silently trying again would convert an
    operator editing a corpus underneath a running build into a build that
    quietly succeeded on the second look.
    """
    captured: list[derive.CapturedCorpus] = []
    anchors: list[_Anchor] = []
    for corpus_id in preflight.coverage:
        carrier = preflight.carriers[corpus_id]
        state = _root_state_for(carrier, world._corpus_executor_factory)
        with state.lock.capture():
            genesis_digest, head_digest = world._chain_head(carrier)
            before = registry.corpus_state_identity(carrier)
            records = _captured_records(carrier)
            after = registry.corpus_state_identity(carrier)
            if before != after:
                raise CaptureDrift(
                    f"{corpus_id}: {carrier}: the corpus state moved inside the capture hold "
                    f"({before} -> {after}); the whole capture is discarded and nothing is published"
                )
        captured.append(derive.CapturedCorpus(corpus_id, before, records))
        anchors.append(_Anchor(corpus_id, genesis_digest, head_digest))
    return _BuildDraft(
        preflight.coverage,
        derive.Capture(tuple(captured)),
        tuple(anchors),
        preflight.world_anchor,
        preflight.held,
    )


def _capture_build_inputs(
    world: registry.World,
    *,
    coverage: frozenset[str],
    bindings: Mapping[str, rules.RuleBinding],
) -> _BuildDraft:
    """Preflight, then coherent capture: everything a build reads from live
    state, in one act with one frozen result."""
    return _capture(world, _preflight(world, coverage=coverage, bindings=bindings))


def _captured_records(corpus_root: Path) -> tuple[derive.CapturedRecord, ...]:
    """One corpus's stored nodes, enumerated **once**, as captured records.

    The enumeration is `ReadView.iter_stored`, the same unvalidated read
    `registry.corpus_state_identity` takes. That is deliberate: the two state
    computations and this pass have to agree about what the corpus holds, and a
    validating read would refuse records the captured state identity counted,
    leaving the two halves of one coherent capture describing different
    corpora. Record validity is the read side's question (`ReadView.get`), not
    the capture's.

    Governance is this pass's question, and it is asked before any record is
    built. `EnumeratedKindUngoverned` refuses the whole capture: a record whose
    kind one of the four maps enumerates but which has no governed stored-kind
    definition can be neither derived from nor silently omitted.
    """
    view = ReadView.opened_at(corpus_root)
    nodes = tuple(view.iter_stored())
    for node in nodes:
        if node.kind in ENUMERATED_SOURCE_KINDS and node.kind not in stored.SEMANTIC_DOMAINS:
            raise EnumeratedKindUngoverned(
                f"{corpus_root}: {node.id}: kind {node.kind!r} is enumerated by an epoch derivation "
                "but has no governed stored-kind definition; the capture is discarded rather than "
                "derived from or silently narrowed"
            )
    facets = {node.id: _validated_retraction_facet(node) for node in nodes if node.kind == "retraction"}
    standing = _standing_retractions(view, facets)
    return tuple(
        derive.CapturedRecord(
            address=node.id,
            uid=node.uid,
            kind=node.kind,
            deprecated_ids=tuple(node.deprecated_ids),
            produces=tuple(
                relation.target
                for relation in node.relations
                if relation.predicate == stored.PRODUCES and relation.source == node.id
            ),
            retraction=(
                None
                if node.id not in facets
                else derive.CapturedRetraction(
                    _retraction_target(facets[node.id]),
                    RETRACTION_UPHELD if standing.get(node.id, True) else RETRACTION_OVERTURNED,
                )
            ),
        )
        for node in nodes
    )


def _retraction_target(facet: Mapping[str, object]) -> str:
    """The target identity §7.4's discovery map groups on.

    A node-arm retraction names its target by the ref the author wrote, and
    that ref is what travels: turning it into a live address here would make
    the map's keys depend on a resolution the epoch already publishes an
    address map for. A route-arm retraction names an embedded route rather than
    a record, and its route identity keeps it disjoint from a node-arm
    retraction of the same dataset — two genuinely different claims that a
    shared dataset key would silently merge.
    """
    target = cast(Mapping[str, str], facet["target"])
    return target["ref"] if target["arm"] == "node" else target["route_identity"]


def _standing_retractions(view: ReadView, facets: Mapping[str, Mapping[str, object]]) -> Mapping[str, bool]:
    """Which of this corpus's retractions still stand, in one fold.

    `corpus.standing_in_local_view`'s **graph** half, computed for every
    retraction at once instead of one at a time, because the capture pass may
    enumerate the corpus only once. Only node-arm retractions subtract standing
    — a route-arm target names an embedded route, not a record — and the target
    ref is resolved through the corpus index here, exactly as the corpus-local
    judgement resolves it, so a retraction naming another by a deprecated id
    still overturns it. `_acyclic_postorder` is the corpus's own traversal,
    reused rather than reimplemented: a retraction cycle is
    `RetractionCycleMalformed` here for the same reason it is there.

    **What this deliberately does not do, and the divergence it creates.**
    `standing_in_local_view` first puts every retraction through
    `CorpusWriter._resolve_retraction_target`, which enforces target
    eligibility, exact resolution and a matching target content identity, and
    raises `RetractionTargetIneligible` / `RetractionTargetUnresolvable` when
    any of it fails. This does none of that. So on a corpus whose retraction
    target has drifted, the corpus *declines to judge* while capture records
    `upheld` or `overturned` — and that resolution reaches the retraction
    enumeration projection and its published identity.

    That is a choice, not an oversight. Those two refusals are `WriteRefused`
    subclasses: they are the admission gate's verdict on an *act*, not a
    finding about stored content, and re-running them here would make an epoch
    build a second, later admission gate over records the corpus already holds
    — one raw-imported retraction anywhere in any covered corpus would then
    make the whole world unbuildable. §5.3 closes capture's refusal surface at
    `EnumeratedKindUngoverned` and `CaptureDrift` and names no target-validity
    requirement, and the resolution a capture publishes is a claim about the
    retraction graph ("nothing standing in this corpus retracts this
    retraction"), never a claim that the retraction's own target still
    resolves. A reader checks that through the epoch's address map and the
    retraction-discovery map, which is what they are for. Pinned by
    `test_world_build.py::TestSerialCapture`'s drifted-target arm.
    """
    targets: dict[str, list[str]] = {}
    for address, facet in facets.items():
        target = cast(Mapping[str, str], facet["target"])
        if target["arm"] != "node":
            continue
        resolved = view.resolve(target["ref"])
        if resolved is not None:
            targets.setdefault(resolved, []).append(address)
    graph = {target: tuple(sorted(retractions)) for target, retractions in targets.items()}
    standing: dict[str, bool] = {}
    for target in _acyclic_postorder(graph):
        standing[target] = not any(standing[retraction] for retraction in graph.get(target, ()))
    return standing


def _recheck_rule_bindings(world: registry.World, draft: _BuildDraft) -> Mapping[str, rules._HeldRule]:
    """§5.4's pre-publication recheck: the same four exact pairs, still held.

    It reacquires the world lock — the same lock removal takes — which is what
    gives binding removal and epoch publication a determined order without
    holding the world lock across corpus enumeration. If removal won the race,
    this raises `RuleNotHeld` and the caller publishes nothing.

    It reads no corpus. Every value publication needs from live corpus state
    was captured under the corpus's own hold, and a second look here would be a
    freshness claim the staleness contract explicitly does not make: covered
    corpora may move between capture and publication, and receipts name the
    exact captured states rather than the present ones.
    """
    declared = {kind: held.binding for kind, held in draft.held.items()}
    with world._state.lock:
        return rules._locked_resolve_rule_bindings(world.config.world_root, declared)
