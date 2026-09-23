"""Store reads for the belief path (design §5.4), through the kernel's
holdings reduction: the reduced answer per dataset address, the held path
for an address, and the admission check."""
from __future__ import annotations

from pathlib import Path

from beliefs import stored
from beliefs.corpus import ReadView
from beliefs.dataset import ByteObservation, Held, admission_state, dataset_address
from beliefs.holdings.adapter import DatasetAnswer, DatasetBlocked, dataset_observations
from beliefs.holdings.receipt import derive_holdings
from beliefs.holdings.reduce import holdings_rule_bundle
from beliefs.root import log_seam
from beliefs.world.rules import binding_for

from science.refusal import Refusal, Refused


def reduced_heads(world, corpus_id: str):
    """(active, blocked) from the world's held reducer over this corpus.

    Detached inspection, deliberately: the registered inspection reaches the
    engine's recovering `inspect_chain`, which may reclaim debris and append
    registrations or settlements. A read context holds no authority to write,
    and a read that repaired the chain on the way past would be a write the
    ledger never saw. Pending evidence is read as pending."""
    seam = log_seam()
    active, blocked, _ = derive_holdings(
        world, frozenset({corpus_id}), binding_for(holdings_rule_bundle()),
        chain_view=seam.inspect_detached, state_facts=seam.state_facts,
    )
    return active, blocked


def reduced_observations(view: ReadView, world, corpus_id: str) -> dict[str, DatasetAnswer | DatasetBlocked]:
    """The reduction's answer for every dataset record that has an address."""
    active, blocked = reduced_heads(world, corpus_id)
    answers: dict[str, DatasetAnswer | DatasetBlocked] = {}
    for node in view.iter_stored():
        if node.kind != "dataset":
            continue
        declaration = stored.dataset_declaration(node)
        address = dataset_address(declaration)
        if address is not None:
            answers[address] = dataset_observations(declaration, active, blocked)
    return answers


def found_observations(view: ReadView, world, corpus_id: str) -> dict[str, tuple[ByteObservation, ...]]:
    """Address -> the reduced Found observations; blocked and empty answers
    are absent from the mapping, which is what `Availability` wants."""
    return {
        address: answer.observations
        for address, answer in reduced_observations(view, world, corpus_id).items()
        if isinstance(answer, DatasetAnswer) and answer.observations
    }


def held_path_for(store_root: Path, store_id: str, observations: tuple[ByteObservation, ...]) -> Path:
    """The reducer renders a location as `store:<store id>:<relative path>`.
    Only an observation recorded for the configured store's own identity
    resolves here: evidence for another store names bytes this root never
    held, however the relative paths happen to coincide."""
    for observation in observations:
        parts = observation.location.split(":", 2)
        if len(parts) == 3 and parts[0] == "store" and parts[1] == store_id and parts[2]:
            return Path(store_root) / parts[2]
    raise Refused(Refusal("invalid-input",
                          f"no observation resolves in store {store_id}: "
                          f"{sorted(o.location for o in observations)}"))


def held_path(view: ReadView, world, corpus_id: str, store_root: Path, store_id: str, address: str) -> Path:
    answer = reduced_observations(view, world, corpus_id).get(address)
    if isinstance(answer, DatasetBlocked):
        raise Refused(Refusal("invalid-input",
                              f"{address} is blocked at {answer.locations}: {answer.reasons}"))
    if not isinstance(answer, DatasetAnswer) or not answer.observations:
        raise Refused(Refusal("invalid-input", f"{address} is not held in this store"))
    return held_path_for(store_root, store_id, answer.observations)


def is_held(view: ReadView, world, corpus_id: str, node) -> bool:
    declaration = stored.dataset_declaration(node)
    address = dataset_address(declaration)
    if address is None:
        return False
    answer = reduced_observations(view, world, corpus_id).get(address)
    if not isinstance(answer, DatasetAnswer):
        return False
    return isinstance(admission_state(declaration, answer.observations), Held)
