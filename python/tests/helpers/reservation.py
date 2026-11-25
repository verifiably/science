"""Payload documents, direct fixture records and worlds for exposure and reservation command tests."""
from __future__ import annotations

import hashlib
import json
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import pytest
from beliefs import stored
from beliefs.consulted import CorpusPins
from beliefs.permit import Authority, WritePermit
from beliefs.profile import compile_profile, shipped_base_contract, shipped_domain_contract
from beliefs.reservation import exposure_event_from_facet, reservation_assignment_from_facet
from beliefs.root import init_corpus_root, open_corpus, open_world
from beliefs.session.writer import ScopedWriter
from beliefs.world import Fresh
from helpers.world import DOMAINS, FIXTURE_AUTHORITY, TEST_CONTRACT, concept_list_address, level_list_address
from nodes.core.node import Node
from nodes.core.relations import Relation
from science.config import ScienceConfig

__all__ = [
    "COHORT", "COMMANDS", "OMIT", "add_foreign_mount", "assignment_facet", "assignment_node", "digest",
    "event_facet", "event_node", "group", "hold_record", "no_writer_act", "stored_of", "write_payload",
]

COMMANDS = ("exposure-event", "reservation-assignment", "exposure-log", "reservation-head", "record")
COHORT = "testing/cohort"
OMIT = object()


def digest(label: str) -> str:
    """A fixture digest: the sha256 of a label, plausible in form and of no real file."""
    return "sha256:" + hashlib.sha256(label.encode()).hexdigest()


def _changed(base: dict, changes: dict) -> dict:
    return {key: value for key, value in {**base, **changes}.items() if value is not OMIT}


def event_facet(**changes) -> dict:
    """A knowledge event over one cohort, less the writer identity the session supplies."""
    return _changed({
        "channel": "knowledge",
        "subjects": [],
        "units": [{"sort": COHORT, "term": "uams-tt2-tt3"}],
        "effect": "exposing",
        "class": "training-knowledge",
        "account": "Possible training exposure through the date of use.",
        "observer": "agy/gemini-4-argon",
        "observed_at": "2026-11-06T12:00:00Z",
        "propositions": [],
    }, changes)


def group(*terms: str, role: str = "open", **fields) -> dict:
    return {"units": [{"sort": COHORT, "term": term} for term in terms], "role": role, **fields}


def assignment_facet(**changes) -> dict:
    """A chain root over two cohorts, less the writer identity the session supplies."""
    return _changed({
        "chain": "mm-roster",
        "rule": {"name": "mm-phase-1-protocol", "version": "amendment-7"},
        "inputs": {"roster.yaml": digest("roster")},
        "events": [],
        "groups": [group("a20-mm-patients", role="unresolved"), group("uams-tt2-tt3", label="discovery")],
        "assigned_at": "2026-11-06T13:00:00Z",
    }, changes)


def write_payload(directory: Path, facet: object, *, title: object = "Recorded by a test", name: str = "payload.json",
                  **envelope) -> str:
    """The envelope document at `directory/name`; keyword arguments add or (with `OMIT`) drop envelope keys."""
    document = _changed({"schema_version": 1, "title": title, "facet": facet}, envelope)
    path = Path(directory) / name
    path.write_text(json.dumps(document), encoding="utf-8")
    return str(path)


def event_node(facet: dict, *, actor: str, title: str = "Recorded by a test") -> Node:
    value = exposure_event_from_facet({**facet, "recorded_by": actor})
    return stored.exposure_event_node(value, title=title)


def assignment_node(facet: dict, *, actor: str, title: str = "Recorded by a test") -> Node:
    """The record as stored: a successor carries the `supersedes` edge the boundary authors."""
    value = reservation_assignment_from_facet({**facet, "assigned_by": actor})
    node = stored.reservation_assignment_node(value, title=title)
    if value.predecessor is None:
        return node
    edge = Relation(source=node.id, predicate=stored.SUPERSEDES, target=value.predecessor)
    return node.model_copy(update={"relations": [*node.relations, edge]})


def hold_record(root: Path, profile, node: Node, *, actor: str = "fixture") -> Node:
    """Write `node` through the boundary of the corpus at `root`, under full fixture authority for `actor`."""
    writer = open_corpus(root, authority=Authority(WritePermit.full(), actor), profile=profile)
    if node.kind == "reservation-assignment":
        predecessor = stored.reservation_assignment_value(node).predecessor
        if predecessor is not None:
            bare = [edge for edge in node.relations if edge.predicate != stored.SUPERSEDES]
            return writer.supersede(node.model_copy(update={"relations": bare}), of=predecessor)
    return writer.add(node)


@contextmanager
def no_writer_act():
    """Fail if a write reaches its act: several preflight refusals look the same as the kernel's at commit."""
    def reached(*_, **__):
        pytest.fail("a refused payload reached the writer's act")

    with pytest.MonkeyPatch.context() as patch:
        for act in ("add", "supersede"):
            patch.setattr(ScopedWriter, act, reached)
        yield


def stored_of(ctx, kind: str) -> list[str]:
    return sorted(node.id for node in ctx.write_view().iter_stored() if node.kind == kind)


def add_foreign_mount(cfg: ScienceConfig) -> tuple[ScienceConfig, Path, object]:
    """`cfg` with a third admitted root, `foreign`, whose manifest pins another identity of the `testing`
    namespace the writer activates. Returns the config, the root and the profile it pins."""
    from science.contracts import load_contract_document
    work = cfg.world.world_root.parent
    document = work / "testing-foreign.yaml"
    text = TEST_CONTRACT % {"concepts": concept_list_address().removeprefix("dataset:"),
                            "levels": level_list_address().removeprefix("dataset:")}
    document.write_text(text.replace("testing-cohorts", "foreign-cohorts", 1))
    base = shipped_base_contract()
    contract, _ = load_contract_document(document, base)
    profile = compile_profile(base, [*(shipped_domain_contract(ns) for ns in DOMAINS), contract])
    root = work / "foreign"
    init_corpus_root(root, authority=FIXTURE_AUTHORITY)
    open_corpus(root, authority=FIXTURE_AUTHORITY, profile=profile).adopt_manifest(profile=CorpusPins(
        science_contract="science:" + profile.base_contract_identity,
        domains={ns: f"{ns}:{identity}" for ns, identity in profile.activated_contracts.items()},
    ))
    cfg = replace(cfg, world=replace(cfg.world, corpus_roots=(*cfg.world.corpus_roots, root)),
                  available_contracts=(*cfg.available_contracts, contract))
    open_world(cfg.world, authority=FIXTURE_AUTHORITY).admit(root, provenance=Fresh())
    return cfg, root, profile
