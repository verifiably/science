"""The admission checklist over parsed candidate and live corpus records."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from beliefs.corpus import ReadView
from beliefs.world.registry import content_identity


@dataclass(frozen=True)
class Conflict:
    rule: Literal["content", "deprecated-key", "uid-corruption"]
    addresses: tuple[str, ...]
    corpus: str


def conflicts(candidate: ReadView, live: Sequence[tuple[str, ReadView]]) -> Conflict | None:
    """Report the first conflicting corpus, with rule priority and all its addresses."""
    indexes = []
    for corpus, view in live:
        keys: dict[str, tuple[str, str]] = {}
        uids: dict[str, str] = {}
        for node in view.iter_stored():
            content = content_identity(node)
            for key in (node.id, *node.deprecated_ids):
                keys[key] = (node.id, content)
            uids[node.uid] = node.id
        indexes.append((corpus, keys, uids, set(), set(), set()))

    for node in candidate.iter_stored():
        content = content_identity(node)
        for _, keys, uids, corrupt, canonical, deprecated in indexes:
            held_id = uids.get(node.uid)
            if held_id is not None and held_id != node.id:
                corrupt.update((node.id, held_id))
            for key in (node.id, *node.deprecated_ids):
                held = keys.get(key)
                if held is not None and held[1] != content:
                    if key == node.id == held[0]:
                        canonical.add(key)
                    else:
                        deprecated.add(key)

    for corpus, _, _, corrupt, canonical, deprecated in indexes:
        addresses = tuple(sorted(corrupt | canonical | deprecated))
        if corrupt:
            return Conflict("uid-corruption", addresses, corpus)
        if canonical:
            return Conflict("content", addresses, corpus)
        if deprecated:
            return Conflict("deprecated-key", addresses, corpus)
    return None
