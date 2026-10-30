"""Store reads for the belief path (design §5.4), through the kernel's
holdings reduction: the reduced answer per dataset address, the held path
for an address, and the admission check."""
from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from beliefs import stored
from beliefs.dataset import ByteObservation, Held, admission_state, dataset_address
from beliefs.errors import MalformedRecord
from beliefs.holdings.records import StoreLocator
from beliefs.holdings.adapter import DatasetAnswer, DatasetBlocked, dataset_observations
from beliefs.holdings.receipt import derive_holdings
from beliefs.holdings.reduce import holdings_rule_bundle
from beliefs.root import log_seam
from beliefs.world.rules import binding_for

from science.refusal import Refusal, Refused


def reduced_heads(world, corpus_ids: frozenset[str]):
    """(active, blocked) from the world's held reducer over these corpora.

    Detached inspection, deliberately: the registered inspection reaches the
    engine's recovering `inspect_chain`, which may reclaim debris and append
    registrations or settlements. A read context holds no authority to write,
    and a read that repaired the chain on the way past would be a write the
    ledger never saw. Pending evidence is read as pending."""
    seam = log_seam()
    active, blocked, _ = derive_holdings(
        world, corpus_ids, binding_for(holdings_rule_bundle()),
        chain_view=seam.inspect_detached, state_facts=seam.state_facts,
    )
    return active, blocked


def reduced_observations(views, world) -> dict[str, DatasetAnswer | DatasetBlocked]:
    """The reduction's answer for every dataset record any mount holds: one
    dataset, whichever corpus declared it."""
    active, blocked = reduced_heads(world, frozenset(corpus_id for corpus_id, _ in views))
    answers: dict[str, DatasetAnswer | DatasetBlocked] = {}
    for _, view in views:
        for node in view.iter_stored():
            if node.kind != "dataset":
                continue
            declaration = stored.dataset_declaration(node)
            address = dataset_address(declaration)
            if address is not None:
                answers[address] = dataset_observations(declaration, active, blocked)
    return answers


def dataset_at(views, address: str):
    """(corpus id, dataset record) declaring `address` in any mount, or None.
    A dataset's id derives from its content, so one address has one record
    world-wide; `dataset` refuses to mint a second."""
    for corpus_id, view in views:
        for node in view.iter_stored():
            if node.kind == "dataset" and dataset_address(stored.dataset_declaration(node)) == address:
                return corpus_id, node
    return None


def found_observations(views, world) -> dict[str, tuple[ByteObservation, ...]]:
    """Address -> the reduced Found observations; blocked and empty answers
    are absent from the mapping, which is what `Availability` wants."""
    return {
        address: answer.observations
        for address, answer in reduced_observations(views, world).items()
        if isinstance(answer, DatasetAnswer) and answer.observations
    }


def held_path_for(stores: Mapping[str, Path], observations: tuple[ByteObservation, ...]) -> Path:
    """First configured identity in reducer order; never retry a selected copy."""
    for observation in observations:
        parts = observation.location.split(":", 2)
        if len(parts) != 3 or parts[0] != "store" or parts[1] not in stores:
            continue
        try:
            locator = StoreLocator(parts[1], parts[2])
        except MalformedRecord as caught:
            raise Refused(Refusal("invalid-input", str(caught))) from caught
        root = stores[locator.store_id]
        candidate = root / locator.relative_path
        if not candidate.resolve().is_relative_to(root.resolve()):
            raise Refused(Refusal("invalid-input", f"{observation.location} escapes store {root}"))
        return candidate
    raise Refused(Refusal("invalid-input",
                          f"no observation resolves in stores {sorted(stores)}: "
                          f"{sorted(o.location for o in observations)}"))


def held_path(views, world, stores: Mapping[str, Path], address: str) -> Path:
    answer = reduced_observations(views, world).get(address)
    if isinstance(answer, DatasetBlocked):
        raise Refused(Refusal("invalid-input",
                              f"{address} is blocked at {answer.locations}: {answer.reasons}"))
    if not isinstance(answer, DatasetAnswer) or not answer.observations:
        raise Refused(Refusal("invalid-input", f"{address} is not held in the configured stores"))
    return held_path_for(stores, answer.observations)


def is_held(views, world, node) -> bool:
    declaration = stored.dataset_declaration(node)
    address = dataset_address(declaration)
    if address is None:
        return False
    answer = reduced_observations(views, world).get(address)
    if not isinstance(answer, DatasetAnswer):
        return False
    return isinstance(admission_state(declaration, answer.observations), Held)
