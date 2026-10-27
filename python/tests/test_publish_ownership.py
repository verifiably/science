"""Science supplies the same Own declaration to preview and each new publication."""
from dataclasses import replace
import shutil
from types import SimpleNamespace

import pytest

from beliefs.publish_request import decode_snapshot
from beliefs.root import (admit_arrival, export_head_artifact, metadata_root_for, open_corpus, open_world,
                         replicate_root, restore_root)
from beliefs.world import ReplicaOf, load_manifest
from beliefs.world.anchors import CorpusSubject
from beliefs.world.verify import ArtifactCarrier, ObserverSet
from helpers.commons import a_identity, binding_ref, read_rig, refused
from helpers.world import (FIXTURE_AUTHORITY, QUERY, build_fixture_world,
                           build_world_without_coordination, fixture_proposition_node, open_rig)

from science.publication import binding_fields, marker_fields, marker_of
from science.config import ReadContext
from science.sharing import FetchRecord, Pin, SharingRegistry
from science.world_belief import publish_session_epoch


@pytest.fixture(params=[2, 3], ids=["v2", "v3"])
def own_replica(certified_work, request):
    source = build_world_without_coordination(certified_work / "source")
    open_corpus(source.write_root, authority=FIXTURE_AUTHORITY, profile=source.profile).add(
        fixture_proposition_node("restored"))
    cid = load_manifest(source.write_root).corpus_id
    artifact = export_head_artifact(open_world(source.world, authority=FIXTURE_AUTHORITY), CorpusSubject(cid))
    cfg = build_fixture_world(certified_work / "reader", coordination=request.param)
    cfg = replace(cfg, sharing_root=certified_work / "sharing")
    # A registry path is hand-listed too: the pin below decides whether it counts as Own.
    root = SharingRegistry(cfg.sharing_root).root_for(cid).resolve()
    root.parent.mkdir(parents=True)
    cfg = replace(cfg, world=replace(cfg.world, corpus_roots=(*cfg.world.corpus_roots, root)))
    replicate_root(source.write_root, root, authority=FIXTURE_AUTHORITY)
    observers = ObserverSet((ArtifactCarrier.from_bytes(artifact),))
    assert restore_root(root, CorpusSubject(cid), observers, authority=FIXTURE_AUTHORITY).outcome == "validated"
    world = open_world(cfg.world, authority=FIXTURE_AUTHORITY)
    admit_arrival(world, root, ReplicaOf(cid), observers)
    with open_rig(cfg, ("project",)) as (d, _):
        d.invoke("project", {"name": "findings", "query": QUERY})
    publish_session_epoch(cfg)
    destination = certified_work / "destination"
    destination.mkdir()
    return cfg, cid, root, destination


def test_configured_markerless_replica_preview_matches_publication(own_replica):
    cfg, cid, root, destination = own_replica
    params = {"target": "findings", "to": str(destination)}
    text = read_rig(cfg, "publish-preview").invoke("publish-preview", params).text
    selected = {line.strip().removeprefix("record: ") for line in text.splitlines()
                if line.strip().startswith("record: ")}
    assert selected == {"proposition:p1", "proposition:restored"}
    assert "attribution: every selected record is this world's own" in text
    before = open_world(cfg.world, authority=FIXTURE_AUTHORITY).registry()
    with open_rig(cfg, ("publish",)) as (d, ctx):
        report = d.invoke("publish", params).text
        binding = binding_fields(ctx.write_view().get(binding_ref(report)))
    fields = marker_fields(marker_of(destination / binding.corpus_id))
    assert fields.selection == selected and fields.attributions == {}
    (snapshot_path,) = (cfg.operations_root / "publish").glob("*/selection.v1")
    snapshot = decode_snapshot(snapshot_path.read_bytes())
    assert {address for address, _ in snapshot.records} == selected
    assert snapshot.attributions == (None if cfg.coordination == 2 else ())
    assert open_world(cfg.world, authority=FIXTURE_AUTHORITY).registry() == before
    assert load_manifest(root).corpus_id == cid


def test_hand_listed_markerless_registry_root_is_never_declared_own(own_replica):
    cfg, cid, _, destination = own_replica
    SharingRegistry(cfg.sharing_root).write_pin(Pin(
        cid, "a" * 32, "b" * 64, cfg.world.world_id, "coord:findings", None,
        FetchRecord("https://remote.test/source", "2026-10-27T00:00:00Z", "validated"), "retired"))
    params = {"target": "findings", "to": str(destination)}
    expected = "attribution-contract-unpinned" if cfg.coordination == 2 else "attribution-source-invalid"
    preview = refused(lambda: read_rig(cfg, "publish-preview").invoke("publish-preview", params))
    with open_rig(cfg, ("publish",)) as (d, ctx):
        publication = refused(lambda: d.invoke("publish", params))
        assert not any(node.kind == "publication-binding" for node in ctx.write_view().iter_stored())
    for refusal in (preview, publication):
        assert refusal.code == "kernel-refused" and refusal.data["reason"] == expected
        assert cid in refusal.message
    assert list(destination.iterdir()) == []


def test_hand_listed_publication_keeps_its_origins(reopened):
    cfg = replace(reopened.b, sharing_root=None)
    source = a_identity(reopened.a)
    destination = cfg.world.world_root.parent / "publication"
    destination.mkdir()
    params = {"target": "b", "to": str(destination)}
    text = read_rig(cfg, "publish-preview").invoke("publish-preview", params).text
    assert f"{source['proposition']}: {source['corpus_id']} {source['marker']}" in text
    with open_rig(cfg, ("publish",)) as (d, ctx):
        report = d.invoke("publish", params).text
        binding = binding_fields(ctx.write_view().get(binding_ref(report)))
    fields = marker_fields(marker_of(destination / binding.corpus_id))
    assert fields.attributions == {ref: (source["corpus_id"], source["marker"]) for ref in fields.selection}


def test_preview_refuses_duplicate_claimed_carriers(reopened):
    cfg = reopened.b
    cid = a_identity(reopened.a)["corpus_id"]
    source = SharingRegistry(cfg.sharing_root).root_for(cid).resolve()
    twin = cfg.world.world_root.parent / "twin"
    shutil.copytree(source, twin)
    shutil.copytree(metadata_root_for(source), metadata_root_for(twin))
    cfg = replace(cfg, world=replace(cfg.world, corpus_roots=(*cfg.world.corpus_roots, twin)))
    refusal = refused(lambda: read_rig(cfg, "publish-preview").invoke(
        "publish-preview", {"target": "b", "to": str(twin.parent / "destination")}))
    assert refusal.code == "invalid-input"
    assert cid in refusal.message and "more than one configured root" in refusal.message


@pytest.mark.parametrize("command", ["publish-preview", "publish"])
@pytest.mark.parametrize("count", [0, 2], ids=["missing-write-mount", "duplicate-write-mount"])
def test_publication_requires_exactly_one_write_mount(fresh, monkeypatch, command, count):
    mounts = ReadContext.open(fresh.a).mounts()
    monkeypatch.setattr(ReadContext, "mounts", lambda self: mounts * count)
    message = "not enough values to unpack" if count == 0 else "too many values to unpack"
    with pytest.raises(ValueError, match=message):
        if command == "publish":
            with open_rig(fresh.a, (command,)) as (d, _):
                d.invoke(command, {"target": "a", "to": str(fresh.remotes)})
        else:
            read_rig(fresh.a, command).invoke(command, {"target": "a", "to": str(fresh.remotes)})


@pytest.mark.parametrize("command", ["publish-preview", "publish"])
def test_publication_propagates_an_unselected_mount_read_error(fresh, monkeypatch, command):
    mounts = ReadContext.open(fresh.a).mounts()

    def unreadable():
        raise OSError("unselected mount is unreadable")

    unread = replace(mounts[0], corpus_id="f" * 32, root=fresh.remotes / "unreadable",
                     view=SimpleNamespace(iter_stored=unreadable, holds=lambda ref: False))
    monkeypatch.setattr(ReadContext, "mounts", lambda self: (*mounts, unread))
    with pytest.raises(OSError, match="unselected mount is unreadable"):
        if command == "publish":
            with open_rig(fresh.a, (command,)) as (d, _):
                d.invoke(command, {"target": "a", "to": str(fresh.remotes)})
        else:
            read_rig(fresh.a, command).invoke(command, {"target": "a", "to": str(fresh.remotes)})
