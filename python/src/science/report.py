"""Typed report blocks: what handlers return instead of prose (spec §7.1)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Heading:
    text: str


@dataclass(frozen=True)
class KeyVals:
    title: str
    pairs: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class RecordBlock:
    uid: str
    record_id: str
    kind: str
    title: str


def record_block(node) -> RecordBlock:
    """Derive a record block from a kernel record; handlers never author one."""
    return RecordBlock(node.uid, node.id, node.kind, node.title)


@dataclass(frozen=True)
class Finding:
    text: str


@dataclass(frozen=True)
class Text:
    text: str


@dataclass(frozen=True)
class SelectionBlock:
    """What a `session` invocation reports (coordination design §4.1): the
    selection it recorded, as the project's address pinned to the revision it
    resolved to and the name that revision carries, or nothing selected."""
    address: str | None
    name: str | None


@dataclass(frozen=True)
class PinBlock:
    """What a `sharing` invocation reports: one ledger sharing line of it, with
    the facts the line attests and the transition it records."""
    corpus_id: str
    marker: str
    artifact: str
    world: str
    view: str
    source: str
    location: str
    verdict: str
    transition: str


def pin_block(line) -> PinBlock:
    """Derive a pin block from a kernel `SharingLine`; handlers never author one."""
    return PinBlock(line.corpus, line.marker, line.artifact, line.world, line.view,
                    line.source, line.location, line.verdict, line.transition)


Block = Heading | KeyVals | RecordBlock | Finding | Text | SelectionBlock | PinBlock
Report = tuple[Block, ...]


def serialize_block(block: Block) -> str:
    match block:
        case Heading(text):
            return f"## {text}\n"
        case KeyVals(title, pairs):
            lines = [f"{title}:"] + [f"  {k}: {v}" for k, v in pairs]
            return "\n".join(lines) + "\n"
        case RecordBlock(uid, record_id, kind, title):
            return f"[{kind}] {record_id} uid={uid}\n{title}\n"
        case Finding(text):
            return f"! {text}\n"
        case Text(text):
            return text + "\n"
        case SelectionBlock(None, _):
            return "selected: none\n"
        case SelectionBlock(address, name):
            return f"selected: {address}\nname: {name}\n"
        case PinBlock(corpus_id, marker, artifact, world, view, source, location, verdict, transition):
            facts = (("marker", marker), ("artifact", artifact), ("world", world), ("view", view),
                     ("source", source), ("location", location), ("verdict", verdict))
            lines = [f"[pin] {corpus_id} {transition}"] + [f"{k}: {v}" for k, v in facts]
            if transition == "mounted":
                # A session's mounts are fixed at open (commons spec §5).
                lines.append("takes effect at the next session open")
            return "\n".join(lines) + "\n"
    raise TypeError(f"not a block: {block!r}")
