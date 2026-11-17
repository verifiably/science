"""Real publication transitions exercise current custody observations and replay."""
from dataclasses import replace
from hashlib import sha256
import json

import pytest
from beliefs import stored
from beliefs.corpus import ReadView
from beliefs.holdings.boundary import ActContext, write
from beliefs.holdings.records import StoreLocator
from beliefs.procedure import ModelInputs, SameAs, procedure_from_stored
from beliefs.root import holdings_seam, open_corpus
from helpers.analysis import analysis_nodes
from helpers.commons import LOC_A, _publish_update, a_identity, publish_again, refused, with_remotes
from helpers.world import FIXTURE_AUTHORITY, concept_list_address, level_list_address, hold_fixture_dataset, open_rig
from nodes.core.corpus import Corpus
from science.config import ReadContext
from science.sharing import SharingRegistry
from test_cmd_adopt import _adopt
from test_cmd_show import _show


def hold_digest_without_declaration(cfg, content):
    digest = "sha256:" + sha256(content).hexdigest()
    context = ActContext(cfg.write_root, cfg.store_root, "fixture", "fixture/hold.v1", FIXTURE_AUTHORITY,
                         holdings_seam(), profile=cfg.profile)
    write(context, StoreLocator(ReadContext.open(cfg).store_id(), digest[7:] + "/data.txt"), content, expected=digest)
    base = procedure_from_stored(analysis_nodes(cfg.profile)[2])
    node = stored.procedure_node(replace(base, kind="testing/model", name="Digest-dependent model",
                                         inputs=ModelInputs((digest,), ())))
    Corpus(cfg.write_root).add(node)  # custody does not assert eligibility
    return digest


def publish_addresses(installations, addresses):
    from science.coordination import resolve_project_ref
    with open_rig(installations.a, ("revise",)) as (d, ctx):
        d.invoke("revise", {"address": str(resolve_project_ref(ctx, "a")), "query": json.dumps({
            "version": "science.view-query.v1", "clauses": [{"all": [{"addresses": addresses}]}]})})
    return publish_again(installations, LOC_A)


@pytest.mark.parametrize("known", [True, False])
def test_adopt_and_show_keep_native_dependencies_and_replay_committed_admission(adopted, known):
    first = a_identity(adopted.a)["corpus_id"]
    nodes = analysis_nodes(adopted.a.profile)
    dependency = nodes[0].id if known else "procedure:" + "f" * 64
    dependent = stored.procedure_node(replace(procedure_from_stored(nodes[0]), name="Uses frozen authority", scale=SameAs(dependency)))
    Corpus(adopted.b.write_root).add(dependent)
    ids = a_identity(adopted.a)
    successor = publish_addresses(adopted, [ids["dataset"], concept_list_address(), level_list_address(), nodes[1].id, nodes[2].id])
    with with_remotes(adopted), open_rig(adopted.b, ("adopt",)) as (d, _):
        inputs = {"location": LOC_A, "corpus_id": successor}
        text = d.invoke("adopt", inputs, invocation_id="native-retention").text
        assert d.invoke("adopt", inputs, invocation_id="native-retention").text == text
    assert f"retention {first}:" in text and dependency in text
    registry = SharingRegistry(adopted.b.sharing_root)
    assert registry.pin(first).state == registry.pin(successor).state == "mounted"
    shown = _show(adopted.b, first)
    assert "kept: dependency" in shown and dependency in shown


def test_newly_admitted_declaration_supplies_a_digest_outside_configured_roots(adopted):
    first = a_identity(adopted.a)["corpus_id"]
    content = b"successor-only bytes\n"
    dataset = hold_fixture_dataset(adopted.a, "new.txt", content, "new declaration")
    digest = hold_digest_without_declaration(adopted.b, content)
    assert digest not in {o.digest for values in ReadContext.open(adopted.b).observations().values() for o in values}
    successor = publish_again(adopted, LOC_A)
    text = _adopt(adopted, LOC_A, successor).text
    registry = SharingRegistry(adopted.b.sharing_root)
    assert registry.pin(first).state == "retired", text
    assert registry.pin(successor).state == "mounted"
    assert ReadView.opened_at(registry.root_for(successor)).holds(dataset)
    assert "state: retired" in _show(adopted.b, first)


def test_retention_uses_fresh_live_observations_after_each_transition(adopted, monkeypatch):
    import science.retention as module
    first = a_identity(adopted.a)["corpus_id"]
    ids = a_identity(adopted.a)
    data = stored.dataset_declaration(ReadContext.open(adopted.a).write_view().get(ids["dataset"]))
    content = adopted.data_a_path().read_bytes()
    assert hold_digest_without_declaration(adopted.b, content) == data.resources[0].digest
    second = publish_again(adopted, LOC_A)
    _adopt(replace(adopted, b=replace(adopted.b, keep=(first,))), LOC_A, second)
    third = _publish_update(adopted, keys=())
    observed = []
    found = module.found_observations
    def capture(views, world):
        ids = frozenset(cid for cid, _ in views)
        assert all(world.status(cid).live for cid in ids)
        observed.append(ids)
        return found(views, world)
    monkeypatch.setattr(module, "found_observations", capture)
    text = _adopt(adopted, LOC_A, third).text
    registry = SharingRegistry(adopted.b.sharing_root)
    assert registry.pin(first).state == "retired", text
    assert registry.pin(second).state == registry.pin(third).state == "mounted"
    assert any(first in ids for ids in observed) and first not in observed[-1]
    assert second in observed[-1] and third in observed[-1]
    assert ids["dataset"] in text and ids["dataset"] in _show(adopted.b, second)


def test_pre_admission_conflict_cannot_use_the_candidates_identical_copy(adopted):
    ids = a_identity(adopted.a)
    hold_digest_without_declaration(adopted.b, adopted.data_a_path().read_bytes())
    writer = open_corpus(adopted.a.write_root, authority=FIXTURE_AUTHORITY, profile=adopted.a.profile)
    writer.revise(writer.read_view.get(ids["proposition"]).model_copy(update={"title": "Changed proposition"}))
    successor = publish_again(adopted, LOC_A)
    failure = refused(lambda: _adopt(adopted, LOC_A, successor))
    assert failure.code == "adopt-conflict"
    assert "required predecessor: dependency" in failure.message and ids["dataset"] in failure.message
    assert not ReadContext.open(adopted.b).world.status(successor).known
