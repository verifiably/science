"""A frozen enrichment universe is retained by its observed content digest."""
from dataclasses import replace
import json
from pathlib import Path

from beliefs import stored
from beliefs.claim import Member, Referent, build_claim
from beliefs.projection import project_claim
from beliefs.root import open_corpus
from helpers.analysis import spec_inputs
from helpers.world import FIXTURE_AUTHORITY, build_belief_world, hold_fixture_dataset, open_rig
from science.config import ReadContext
from science.retention import dependency_closure, required
from test_retention import held, holder


def test_enrichment_universe_keeps_its_carrier_and_accepts_an_identical_survivor(certified_work, monkeypatch):
    import yaml
    import helpers.world as world
    document = yaml.safe_load(world.TEST_CONTRACT)
    body = document["contract"]
    body["instantiations"]["enrich-pair"] = {"template": "general/covaries-with", "roles": {"parties": ["concept", "protein"]}}
    body["estimands"]["instantiation:enrich-pair"] = {"forms": ["enrichment"], "conditioning_sorts": ["concept"]}
    body["functionals"] = {"enrichment-score": {
        "definition": "Synthetic enrichment score over an explicit held universe.", "form": "enrichment",
        "arity": "not-applicable", "response_transformation": "fixed", "reversal": "not-applicable",
        "response_reversal": "not-applicable", "exchange": "not-applicable", "ties": "not-applicable",
        "output": "dimensionless", "domain": "real", "null": "zero", "increment": "not-applicable",
        "uncertainty": "exact", "parameters": "not-applicable"}}
    monkeypatch.setattr(world, "TEST_CONTRACT", yaml.safe_dump(document))
    cfg = build_belief_world(certified_work)
    claim = build_claim(cfg.profile, operator="general/covaries-with", roles={"parties": (
        Member(Referent("testing/concept", "concept:disease-stage")), Member(Referent("testing/protein", "protein:PHF19")))},
        layer="statistical", polarity="positive")
    writer = open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile)
    target = writer.add(stored.proposition_node("enrichment", title="enrichment", claim=project_claim(claim))).id
    data = hold_fixture_dataset(cfg, "data.txt", b"observations\n", "observations")
    universe = hold_fixture_dataset(cfg, "universe.txt", b"explicit universe\n", "universe")
    digest = stored.dataset_declaration(ReadContext.open(cfg).write_view().get(universe)).resources[0].digest
    inputs = spec_inputs(cfg, target=target, dataset=data)
    path = Path(inputs["estimand"])
    authored = json.loads(path.read_text())
    authored.update(form="enrichment", functional="testing/enrichment-score", bindings={
        "membership": {"role": "parties"}, "reference_set": {"role": "parties", "member": {
            "sort": "testing/concept", "term": "concept:disease-stage"}}, "universe": {"digest": digest}},
        outputs={"estimate": {"typing": "dimensionless", "domain": "real"}}, reference={"kind": "value", "value": 0})
    authored["control"]["identification"] = "general/observational"
    path.write_text(json.dumps(authored))
    with open_rig(cfg, ("spec",)) as (d, _):
        d.invoke("spec", inputs)
    ctx = ReadContext.open(cfg)
    nodes = {n.id: n for n in ctx.write_view().iter_stored()}
    universe_node = nodes.pop(universe)
    write = holder(certified_work / "write", *nodes.values(), profile=cfg.profile)
    predecessor = holder(certified_work / "predecessor", universe_node, profile=cfg.profile)
    observations = ctx.observations()
    closure = dependency_closure(write, (predecessor,), observations=observations)
    assert universe in closure.addresses and closure.unresolved == ()
    pin = replace(held(1), corpus_id=predecessor[0])
    args = dict(keep=(), group_chain=(pin,), tip=("p2", "m2"), mounted=(pin,), write_root=write)
    assert required(pin, live=(predecessor,), observations=observations, **args)
    equal = holder(certified_work / "equal", universe_node, profile=cfg.profile)
    assert required(pin, live=(predecessor, equal), observations=observations, **args) == ()
    differing = holder(certified_work / "differing", stored.stamp_semantic_identity(universe_node.model_copy(update={"title": "different universe copy"}, deep=True)), profile=cfg.profile)
    assert "unresolved-copy" in " ".join(dependency_closure(write, (predecessor, differing), observations=observations).unresolved)
    without = {address: found for address, found in observations.items() if address != universe}
    assert digest in " ".join(dependency_closure(write, (predecessor,), observations=without).unresolved)
    assert required(pin, live=(predecessor, equal), observations=without, **args)
