"""The sharing registry: pins (adopted corpora), provider bindings and adopted roots."""
from __future__ import annotations

import json
import os
import re
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from beliefs.session.ledger import (
    LedgerEmpty,
    LedgerMissing,
    LedgerReader,
    LedgerUnreadable,
    SharingLine,
    read_ledger_evidence,
)

_VERSION = 1
_ID_RE = re.compile(r"[0-9a-f]{32}")
STATE_ORDER = ("fetched", "admitted", "mounted", "retired")
_SOURCE_KINDS = ("provider", "catalog")


@dataclass(frozen=True)
class PinSource:
    kind: Literal["provider", "catalog"]
    # The bound location URL, or the catalog artifact identity.
    reference: str

    @classmethod
    def parse(cls, text: str) -> PinSource | None:
        if text == "":
            return None
        kind, sep, reference = text.partition(":")
        if not sep or kind not in _SOURCE_KINDS or not reference:
            raise ValueError(f"not a pin source: {text!r}")
        return cls(kind, reference)  # type: ignore[arg-type]

    def render(self) -> str:
        return f"{self.kind}:{self.reference}"


@dataclass(frozen=True)
class FetchRecord:
    location: str
    at: str
    # restore's LogReport.outcome
    verdict: str


@dataclass(frozen=True)
class ProviderBinding:
    world: str
    locations: tuple[str, ...]
    bound_since: str
    confirmed: bool
    via: tuple[str, ...] = ()


@dataclass(frozen=True)
class Pin:
    corpus_id: str
    marker: str
    artifact: str
    world: str
    view: str
    source: PinSource | None
    fetch: FetchRecord
    state: Literal["fetched", "admitted", "mounted", "retired"]
    keep: bool = False

    def origin_confirmed(self, bindings: Mapping[str, ProviderBinding]) -> bool:
        if self.source is None or self.source.kind != "provider":
            return False
        binding = bindings.get(self.world)
        return binding is not None and binding.confirmed and self.source.reference in binding.locations


class SharingRegistryMalformed(Exception):
    def __init__(self, entry: str, reason: str) -> None:
        super().__init__(f"{entry}: {reason}")
        self.entry = entry
        self.reason = reason


class SharingLedgerUnreadable(Exception):
    """A session ledger replay cannot read: its sharing lines may be lost, so the
    registry is not rebuilt without them."""

    def __init__(self, session_id: str, error: str) -> None:
        super().__init__(f"session {session_id}: ledger unreadable: {error}")
        self.session_id = session_id
        self.error = error


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def _text(data: dict, key: str) -> str:
    value = data.get(key)
    _require(isinstance(value, str), f"{key} must be a string")
    return value


def _texts(data: dict, key: str) -> tuple[str, ...]:
    value = data.get(key)
    _require(isinstance(value, list) and all(isinstance(v, str) for v in value),
             f"{key} must be a list of strings")
    return tuple(value)


def _bool(data: dict, key: str) -> bool:
    value = data.get(key)
    _require(isinstance(value, bool), f"{key} must be a boolean")
    return value


def _pin_from(data: object) -> Pin:
    _require(isinstance(data, dict), "not a JSON object")
    _require(data.get("version") == _VERSION, f"unsupported version {data.get('version')!r}")
    corpus_id, world = _text(data, "corpus_id"), _text(data, "world")
    _require(_ID_RE.fullmatch(corpus_id) is not None, "corpus_id must be 32 lowercase hex digits")
    _require(_ID_RE.fullmatch(world) is not None, "world must be 32 lowercase hex digits")
    state = _text(data, "state")
    _require(state in STATE_ORDER, f"unknown state {state!r}")
    fetch = data.get("fetch")
    _require(isinstance(fetch, dict), "fetch must be an object")
    return Pin(
        corpus_id, _text(data, "marker"), _text(data, "artifact"), world, _text(data, "view"),
        PinSource.parse(_text(data, "source")),
        FetchRecord(_text(fetch, "location"), _text(fetch, "at"), _text(fetch, "verdict")),
        state, _bool(data, "keep"),  # type: ignore[arg-type]
    )


def _pin_to(pin: Pin) -> dict:
    return {
        "version": _VERSION, "corpus_id": pin.corpus_id, "marker": pin.marker,
        "artifact": pin.artifact, "world": pin.world, "view": pin.view,
        "source": pin.source.render() if pin.source else "",
        "fetch": {"location": pin.fetch.location, "at": pin.fetch.at, "verdict": pin.fetch.verdict},
        "state": pin.state, "keep": pin.keep,
    }


def _binding_from(data: object) -> ProviderBinding:
    _require(isinstance(data, dict), "not a JSON object")
    _require(data.get("version") == _VERSION, f"unsupported version {data.get('version')!r}")
    world = _text(data, "world")
    _require(_ID_RE.fullmatch(world) is not None, "world must be 32 lowercase hex digits")
    return ProviderBinding(world, _texts(data, "locations"), _text(data, "bound_since"),
                           _bool(data, "confirmed"), _texts(data, "via"))


def _binding_to(binding: ProviderBinding) -> dict:
    return {
        "version": _VERSION, "world": binding.world, "locations": list(binding.locations),
        "bound_since": binding.bound_since, "confirmed": binding.confirmed,
        "via": list(binding.via),
    }


def _write_json(path: Path, data: dict) -> None:
    """Atomic: temp file in the target directory, fsync, os.replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(data, handle, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    except BaseException:
        Path(temp).unlink(missing_ok=True)
        raise


class SharingRegistry:
    """`pins/`, `providers/`, `roots/` and `scratch/` under one sharing root; `follows/` is reserved."""

    def __init__(self, root: Path) -> None:
        self._root = root

    def _read_all(self, directory: str, parse) -> list:
        folder = self._root / directory
        if not folder.is_dir():
            return []
        found = []
        for path in sorted(folder.glob("*.json")):
            entry = f"{directory}/{path.name}"
            try:
                found.append(parse(json.loads(path.read_text())))
            except (ValueError, KeyError) as error:  # JSONDecodeError is a ValueError
                raise SharingRegistryMalformed(entry, str(error)) from error
        return found

    def pins(self) -> tuple[Pin, ...]:
        return tuple(sorted(self._read_all("pins", _pin_from), key=lambda p: p.corpus_id))

    def pin(self, corpus_id: str) -> Pin | None:
        return next((p for p in self.pins() if p.corpus_id == corpus_id), None)

    def write_pin(self, pin: Pin) -> None:
        _write_json(self._root / "pins" / f"{pin.corpus_id}.json", _pin_to(pin))

    def bindings(self) -> dict[str, ProviderBinding]:
        return {b.world: b for b in self._read_all("providers", _binding_from)}

    def binding_for_location(self, location: str) -> ProviderBinding | None:
        return next((b for b in self.bindings().values() if location in b.locations), None)

    def write_binding(self, binding: ProviderBinding) -> None:
        existing = self.bindings().get(binding.world)
        if existing is not None:
            binding = ProviderBinding(
                binding.world,
                existing.locations + tuple(l for l in binding.locations if l not in existing.locations),
                existing.bound_since,
                existing.confirmed or binding.confirmed,
                existing.via + tuple(v for v in binding.via if v not in existing.via),
            )
        _write_json(self._root / "providers" / f"{binding.world}.json", _binding_to(binding))

    def root_for(self, corpus_id: str) -> Path:
        return self._root / "roots" / corpus_id

    def scratch(self, token: str) -> Path:
        return self._root / "scratch" / token

    def mounted_roots(self) -> tuple[Path, ...]:
        return tuple(self.root_for(p.corpus_id) for p in self.pins() if p.state == "mounted")


def apply_line(registry: SharingRegistry, line: SharingLine) -> bool:
    """Fold one ledger sharing line into the registry; idempotent. True when it wrote."""
    if line.transition == "bound":
        existing = registry.bindings().get(line.world)
        if existing is not None and existing.confirmed and line.location in existing.locations:
            return False
        registry.write_binding(ProviderBinding(line.world, (line.location,), line.at, True))
        return True
    if line.transition not in STATE_ORDER:
        raise ValueError(f"unknown sharing transition {line.transition!r}")
    source = PinSource.parse(line.source)
    pin = registry.pin(line.corpus)
    if pin is None:
        registry.write_pin(Pin(
            line.corpus, line.marker, line.artifact, line.world, line.view, source,
            FetchRecord(line.location, line.at, line.verdict), line.transition,  # type: ignore[arg-type]
        ))
        return True
    state = pin.state
    if STATE_ORDER.index(line.transition) > STATE_ORDER.index(state):
        state = line.transition  # type: ignore[assignment]
    new_source = pin.source if pin.source is not None else source
    if state == pin.state and new_source == pin.source:
        return False
    registry.write_pin(Pin(
        pin.corpus_id, pin.marker, pin.artifact, pin.world, pin.view, new_source,
        pin.fetch, state, pin.keep,
    ))
    return True


def replay(registry: SharingRegistry, operations_root: Path) -> tuple[SharingLine, ...]:
    """Rebuild the registry from every session ledger's sharing lines (spec §7.4):
    every line under `<operations_root>/sessions`, in (at, session id, ledger
    position) order, folded through `apply_line`. Returns the lines that wrote.

    A session whose creation was interrupted (no ledger, or an empty one) holds no
    line by construction and is skipped, as the kernel's reconciliation treats it;
    an unreadable ledger refuses, since its lines would be lost."""
    sessions = Path(operations_root) / "sessions"
    ordered: list[tuple[str, str, int, SharingLine]] = []
    if sessions.is_dir():
        for directory in sorted(entry for entry in sessions.iterdir() if entry.is_dir()):
            evidence = read_ledger_evidence(operations_root, directory.name)
            if isinstance(evidence, (LedgerMissing, LedgerEmpty)):
                continue
            if isinstance(evidence, LedgerUnreadable):
                raise SharingLedgerUnreadable(evidence.session_id, evidence.error)
            if not isinstance(evidence, LedgerReader):  # fail closed on a new evidence shape
                raise TypeError(f"unknown ledger evidence from the kernel: {evidence!r}")
            ordered.extend((line.at, directory.name, position, line)
                           for position, line in enumerate(evidence.sharing()))
    ordered.sort(key=lambda each: each[:3])
    return tuple(line for *_, line in ordered if apply_line(registry, line))
