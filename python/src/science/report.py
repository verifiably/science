"""Typed report blocks: what handlers return instead of prose (spec §7.1)."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
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


def tail_to_json(blocks: Report) -> list[dict]:
    """The sharing tail contains presentation only, never ledger evidence."""
    from science.render import audit_sharing_report
    audit_sharing_report(blocks)
    return [{"kind": "keyvals", "title": block.title, "pairs": [list(pair) for pair in block.pairs]}
            if isinstance(block, KeyVals) else {"kind": "finding", "text": block.text} for block in blocks]


def tail_from_json(raw: object) -> Report:
    if type(raw) is not list:
        raise ValueError("sharing tail must be a list")
    blocks = []
    for item in raw:
        if type(item) is not dict:
            raise ValueError("sharing tail block must be an object")
        if set(item) == {"kind", "text"} and item["kind"] == "finding" and type(item["text"]) is str:
            blocks.append(Finding(item["text"]))
        elif (set(item) == {"kind", "title", "pairs"} and item["kind"] == "keyvals"
              and type(item["title"]) is str and type(item["pairs"]) is list
              and all(type(pair) is list and len(pair) == 2 and all(type(value) is str for value in pair)
                      for pair in item["pairs"])):
            blocks.append(KeyVals(item["title"], tuple(tuple(pair) for pair in item["pairs"])))
        else:
            raise ValueError("invalid sharing tail block")
    return tuple(blocks)


def write_tail(operations_root: Path, session_id: str, invocation_id: str, blocks: Report) -> None:
    payload = json.dumps(tail_to_json(blocks), ensure_ascii=False).encode()
    directory = operations_root / "tails" / session_id
    directory.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=directory, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, directory / f"{invocation_id}.json")
        # Sync parents even after an earlier attempt left their entries behind.
        for parent in (directory, directory.parent, operations_root):
            fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def read_tail(operations_root: Path, session_id: str, invocation_id: str) -> Report:
    """Missing sidecars carry no historical commentary, including invocations before tails existed."""
    path = operations_root / "tails" / session_id / f"{invocation_id}.json"
    try:
        payload = path.read_text()
    except FileNotFoundError:
        return ()
    return tail_from_json(json.loads(payload))
