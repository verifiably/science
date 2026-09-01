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


Block = Heading | KeyVals | RecordBlock | Finding | Text
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
    raise TypeError(f"not a block: {block!r}")
