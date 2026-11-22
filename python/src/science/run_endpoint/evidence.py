"""Versioned chain evidence for the supervisor's closing check."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from beliefs.after import AfterUnavailable, read_after
from beliefs.errors import ScienceError
from beliefs.intents.shapes import Unrecognized, decode_intent
from beliefs.root import AtomsError, log_seam
from beliefs.world.anchors import parse_world_genesis
from beliefs.world.registry import _load_world_mirror
from beliefs.world.logmodel import IntentEntryView, RegisteredEntryView, SettledEntryView, WellFormedView

from science.config import configured_stores, corpus_id_at
from science.refusal import Refusal, Refused
from science.report import Text


@dataclass(frozen=True)
class _Chain:
    role: str
    id: str
    root: Path

    def header(self, genesis: str) -> dict:
        return {"role": self.role, "id": self.id, "root": str(self.root), "genesis": genesis}


def _chains(config):
    corpora = [_Chain("corpus", corpus_id_at(root), root) for root in config.world.corpus_roots]
    stores = [_Chain("store", identity, root) for identity, root in configured_stores(config).items()]
    return sorted(corpora + stores, key=lambda chain: (chain.role, chain.id, chain.root))


def _view(root, resolve):
    seam = log_seam()
    inspect = seam.inspect_registered if resolve else seam.inspect_detached
    view = inspect(root)
    if not isinstance(view, WellFormedView):
        raise Refused(Refusal("read-unavailable", f"Cannot read a well-formed chain at {root}"))
    return view


def _line(row):
    return Text(json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")))


def _world(config, *, resolve=False):
    root = config.world.world_root
    view = _view(root, False)
    try:
        identity = parse_world_genesis(view.genesis.payload)
    except ValueError as error:
        raise Refused(Refusal("read-unavailable", f"{root}: malformed world genesis")) from error
    if identity != config.world.world_id or _load_world_mirror(root) != identity:
        raise Refused(Refusal("read-unavailable", f"{root}: world genesis, mirror and configuration must agree"))
    if resolve:
        recovered = _view(root, True)
        if recovered.genesis != view.genesis:
            raise Refused(Refusal("read-unavailable", f"{root}: world genesis changed during recovery"))
        return recovered
    return view


def heads(config, *, resolve):
    try:
        world = _world(config, resolve=resolve)
        chains = []
        for chain in _chains(config):
            view = _view(chain.root, resolve)
            chains.append(dict(chain.header(view.genesis.digest), tip=view.tip, pending=sorted(view.pending)))
    except (OSError, AtomsError, ScienceError) as error:
        raise Refused(Refusal("read-unavailable", str(error))) from error
    return (_line({"version": "heads.v1", "world_head": world.tip, "world_genesis": world.genesis.digest,
                   "world_pending": sorted(world.pending), "chains": chains}),)


def _intent(entry):
    intent = decode_intent(entry.digest, entry.payload)
    if isinstance(intent, Unrecognized):
        return {"kind": None, "actor": None}
    value = intent.value
    if intent.shape == "holdings":
        locator, rest = value["location"].split(":", 1)
        if locator == "url":
            store_id, location = None, rest
        else:
            store_id, location = rest.split(":", 1)
        return {"kind": "holdings", "actor": value["actor"], "holdings_act": value["kind"],
                "location": location, "store_id": store_id}
    return {"kind": "assessment-run" if intent.shape == "assessment-run" else value.kind, "actor": value.actor}


def _surface(paths):
    return [[path, log_seam().state_facts(state)] for path, state in sorted(paths)]


def _entry(entry):
    if isinstance(entry, IntentEntryView):
        return dict(type="intent", digest=entry.digest, **_intent(entry))
    if isinstance(entry, RegisteredEntryView):
        return {"type": "registration", "digest": entry.digest, "txid": entry.txid, "fulfills": entry.fulfills,
                "consumer_tag": entry.consumer_tag, "initial": _surface(entry.initial), "final": _surface(entry.final)}
    if isinstance(entry, SettledEntryView):
        return {"type": "settlement", "digest": entry.digest, "txid": entry.txid,
                "registration": entry.registration, "committed": entry.committed}
    raise Refused(Refusal("read-unavailable", f"Unexpected log entry {type(entry).__name__}"))


def chain_log(config, *, chain, after, through):
    try:
        _world(config)
        registered = _chains(config)
        if chain == "store":
            matches = [c for c in registered if c.role == "store" and c.root == config.store_root]
        else:
            matches = [c for c in registered if c.role == "corpus" and c.id == chain]
        if not matches:
            raise Refused(Refusal("chain-unknown", f"Unknown chain {chain}"))
        if len(matches) != 1:
            raise Refused(Refusal("read-unavailable", f"Multiple mounted roots claim {chain}"))
        selected, = matches
        genesis = _view(selected.root, False).genesis.digest
        result = read_after(selected.root, genesis=genesis, after=after, through=through)
        if isinstance(result, AfterUnavailable):
            reason = "tip-unknown" if result.reason in {"tip-not-on-chain", "through-not-on-chain"} else "read-unavailable"
            raise Refused(Refusal(reason, result.detail, {"reason": result.reason}))
        header = dict(selected.header(genesis), version="log.v1", after=after, through=result.tip)
        return (_line(header), *(_line(_entry(entry)) for entry in result.entries))
    except (OSError, AtomsError, ScienceError) as error:
        raise Refused(Refusal("read-unavailable", str(error))) from error
