"""The resolution snapshot over held vocabularies (belief-path design §5.3)."""
from __future__ import annotations

from hashlib import sha256

from beliefs import stored
from beliefs.contract.domain import VocabularyBinding
from beliefs.corpus import ReadView
from beliefs.dataset import dataset_address
from beliefs.profile import ProfileSpec
from beliefs.resolution import ResolutionSnapshot, build_snapshot

from science.holdings import held_path_for


def dataset_bound_sorts(profile: ProfileSpec) -> dict[str, VocabularyBinding]:
    """Sort term -> binding, for every sort bound by dataset identity."""
    return {
        term: compiled.vocabulary
        for term, compiled in profile.sorts.items()
        if compiled.vocabulary.dataset_identity is not None
    }


def snapshot(profile: ProfileSpec, view: ReadView, store_root, store_id: str, observations) -> ResolutionSnapshot:
    """Read each dataset-bound vocabulary from the store by the address the
    contract names. `observations` is the read context's reduced mapping
    (address -> Found observations). A binding whose dataset is not in the
    corpus or not held is listed unreadable, so a referent under it resolves
    not-available."""
    readable: dict[VocabularyBinding, list[str]] = {}
    unreadable: list[VocabularyBinding] = []
    for binding in dataset_bound_sorts(profile).values():
        address = f"dataset:{binding.dataset_identity}"
        node = _dataset_at(view, address)
        if node is None or address not in observations:
            unreadable.append(binding)
            continue
        path = held_path_for(store_root, store_id, observations[address])
        content = path.read_bytes()
        (resource,) = stored.dataset_declaration(node).resources
        if "sha256:" + sha256(content).hexdigest() != resource.digest:
            unreadable.append(binding)  # an edited copy is not the held vocabulary
            continue
        readable[binding] = content.decode("utf-8").splitlines()
    return build_snapshot(readable=readable, unreadable=tuple(unreadable))


def _dataset_at(view: ReadView, address: str):
    for node in view.iter_stored():
        if node.kind == "dataset" and dataset_address(stored.dataset_declaration(node)) == address:
            return node
    return None
