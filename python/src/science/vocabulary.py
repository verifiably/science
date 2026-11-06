"""The resolution snapshot over held vocabularies."""
from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
from pathlib import Path

from beliefs import stored
from beliefs.contract.domain import VocabularyBinding
from beliefs.profile import ProfileSpec
from beliefs.resolution import ResolutionSnapshot, build_snapshot

from science.holdings import dataset_at, held_path_for


def dataset_bound_sorts(profile: ProfileSpec) -> dict[str, VocabularyBinding]:
    """Sort term -> binding, for every sort bound by dataset identity."""
    return {
        term: compiled.vocabulary
        for term, compiled in profile.sorts.items()
        if compiled.vocabulary.dataset_identity is not None
    }


def snapshot(profile: ProfileSpec, views, stores: Mapping[str, Path], observations) -> ResolutionSnapshot:
    """Read dataset-bound vocabularies in reducer order across admitted stores.

    Missing declarations or found observations, and selected bytes with a wrong
    digest, are unreadable. Found observations with no configured carrier
    refuse; I/O errors propagate. Neither failure retries another copy.
    """
    readable: dict[VocabularyBinding, list[str]] = {}
    unreadable: list[VocabularyBinding] = []
    for binding in dataset_bound_sorts(profile).values():
        address = f"dataset:{binding.dataset_identity}"
        node = _dataset_at(views, address)
        if node is None or address not in observations:
            unreadable.append(binding)
            continue
        path = held_path_for(stores, observations[address])
        content = path.read_bytes()
        (resource,) = stored.dataset_declaration(node).resources
        if "sha256:" + sha256(content).hexdigest() != resource.digest:
            unreadable.append(binding)  # an edited copy is not the held vocabulary
            continue
        readable[binding] = content.decode("utf-8").splitlines()
    return build_snapshot(readable=readable, unreadable=tuple(unreadable))


def _dataset_at(views, address: str):
    found = dataset_at(views, address)
    return None if found is None else found[1]
