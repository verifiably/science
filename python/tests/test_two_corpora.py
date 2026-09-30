"""Spec §9, the two-corpus check: each proposition's evidence in its own
corpus, each corpus decoded under its own manifest's profile."""
import dataclasses
import json

import pytest

from beliefs.errors import ContractMismatch
from beliefs.profile import compile_profile, shipped_base_contract, shipped_coordination, shipped_domain_contract
from beliefs.world import WorldConfig
from helpers.world import (
    COORDINATION, DOMAINS, OBSERVED, SPEC_FIELDS, FIXTURE_AUTHORITY, add_archived_assessment,
    _minted_ref, build_two_corpus_world, fixture_bundle, hold_fixture_dataset, mint_fixture_run,
    open_rig, write_two_corpus_config,
)
from science.commands.next import handle
from science.config import ReadContext
from science.refusal import Refused
from science.session import open_session

NAMES = ("claim", "spec", "project", "project-select", "next", "belief")
VERSION = "science.view-query.v1"
CLAIM = {"subject": "concept:disease-stage", "predicate": "affects", "object": "protein:PHF19",
         "layer": "causal", "polarity": "positive", "slug": "claimed"}
QUEUED = dict(CLAIM, object="protein:EZH2", slug="queued")


def _query(clause):
    return json.dumps({"version": VERSION, "clauses": [{"all": [clause]}]})


def _rows(text):
    return text.split("propositions:\n", 1)[1]


@pytest.fixture
def world(certified_work, monkeypatch):
    """The archive's proposition assessed. In the write root, alongside the
    mounted archive: proposition:claimed walked run → assess → verify, and
    proposition:queued with a spec only (review round 2: the acceptance check
    runs the whole write path with a read mount present). Both working specs
    observe a dataset the write root holds."""
    import science.commands.run as run_module
    from beliefs.confinement import host_prerequisites
    from beliefs.recipe import MINIMAL_POLICY
    if host_prerequisites() is not None:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
    cfg = build_two_corpus_world(certified_work)
    add_archived_assessment(cfg, certified_work)
    data = hold_fixture_dataset(cfg, "data.txt", b"y\n", "expression", **OBSERVED)
    bundle = fixture_bundle(certified_work)
    with open_rig(cfg, ("claim", "spec")) as (d, _):
        d.invoke("claim", CLAIM)
        d.invoke("claim", QUEUED)
        spec = _minted_ref(d.invoke("spec", dict(SPEC_FIELDS, target="proposition:claimed", dataset=data)).text,
                           "analysis-spec")
        d.invoke("spec", dict(SPEC_FIELDS, target="proposition:queued", dataset=data))
    run = mint_fixture_run(cfg, spec, data, bundle)
    code, entrypoint, _ = bundle
    with open_rig(cfg, ("assess", "verify")) as (d, _):
        assessment = _minted_ref(d.invoke("assess", {"run": run}).text, "assessment")
        d.invoke("verify", {"assessment": assessment, "code": str(code), "entrypoint": entrypoint})
    return cfg


def test_next_under_a_project_selecting_both_classifies_each_from_its_own_corpus(world):
    """The mutation that enumerates the write root only drops the archived row;
    the mutation that decodes the read mount under the writer's profile fails
    on the corpus-local `archive` operator. Rows sort by class, then id."""
    with open_rig(world, NAMES) as (d, _):
        d.invoke("project", {"name": "all three", "query": _query({"addresses": [
            "proposition:archived", "proposition:claimed", "proposition:queued"]})})
        d.invoke("project-select", {"target": "all three"})
        text = d.invoke("next", {}).text
    assert _rows(text) == (
        "  proposition:queued: ready: concept:disease-stage affects protein:EZH2\n"
        "  proposition:archived: assessed-not-admitted: concept:disease-stage affects protein:PHF19 (archived)\n"
        "  proposition:claimed: assessed-not-admitted: concept:disease-stage affects protein:PHF19\n"
    )


def test_the_unselected_session_reads_both_corpora_as_a_project_of_every_kind_does(world):
    """P5 across two corpora."""
    with open_rig(world, NAMES) as (d, _):
        unselected = _rows(d.invoke("next", {}).text)
        d.invoke("project", {"name": "all", "query": _query({"kinds": ["proposition"]})})
        d.invoke("project-select", {"target": "all"})
        selected = _rows(d.invoke("next", {}).text)
    assert unselected == selected and "proposition:archived" in unselected


def test_belief_answers_for_each_corpus_proposition_whatever_is_selected(world):
    """The archive's under its own profile; the write root's over its verified
    assessment, with the archive mounted beside it."""
    from science.commands.belief import handle as belief
    ctx = ReadContext.open(world)
    for proposition in ("proposition:archived", "proposition:claimed"):
        report = belief(ctx, proposition=proposition)
        assert report[0].text == f"Belief: {proposition}"
        assert dict(report[1].pairs)["kind"] in ("Belief", "NoBelief")


def test_the_walked_write_path_minted_every_record_in_the_write_root(world):
    view = ReadContext.open(world).write_view()
    kinds = [node.kind for node in view.iter_stored()]
    assert kinds.count("run") == 2  # the original and verify's replay
    assert kinds.count("assessment") == 1 and kinds.count("verification") == 1


def test_a_sessionless_cli_read_mounts_both_corpora_each_under_its_own_profile(world, capsys):
    from science.cli import main
    assert main(["next", "--config", str(write_two_corpus_config(world))]) == 0
    out = capsys.readouterr().out
    assert "proposition:archived: assessed-not-admitted" in out and "proposition:queued: ready" in out


def test_activating_read_contracts_in_the_writer_is_refused_by_the_write_root_pins(world):
    from science.contracts import load_contract_document
    base = shipped_base_contract()
    loaded = [load_contract_document(world.world.world_root.parent / name, base)[0]
              for name in ("testing.yaml", "archive.yaml")]
    widened = compile_profile(base, [shipped_domain_contract(ns) for ns in DOMAINS] + loaded,
                              coordination=shipped_coordination(COORDINATION))
    with pytest.raises(ContractMismatch):
        open_session(dataclasses.replace(world, profile=widened))


def test_a_selected_record_no_configured_corpus_holds_refuses_naming_it(world):
    """The world admits the archive; a configuration mounting only the write
    root cannot read the row, and says so. The live capture reads the world
    through the configured roots, so the kernel refuses the address before
    `next`'s own unmounted check (which test_cmd_next_selection reaches with a
    capture that names a record no mount holds)."""
    with open_rig(world, ("project",)) as (d, _):
        d.invoke("project", {"name": "archived", "query": _query({"addresses": ["proposition:archived"]})})
    narrowed = dataclasses.replace(world, world=WorldConfig(
        world.world.world_root, world.world.world_id, (world.write_root,)))
    with open_rig(narrowed, NAMES) as (d, _):
        d.invoke("project-select", {"target": "archived"})
        with pytest.raises(Refused) as caught:
            d.invoke("next", {})
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data == {"kind": "SelectionRefused", "reason": "address-unknown",
                                         "refs": ["proposition:archived"]}


def _twice(world):
    from beliefs import stored
    from beliefs.root import open_corpus
    from helpers.world import archive_config
    node = stored.proposition_node("twice", title="twice", claim={"operator": "affects"})
    for cfg in (world, archive_config(world)):
        open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile).add(node)


def test_one_id_in_two_corpora_refuses_naming_both_in_belief_and_unselected_next(world):
    from science.commands.belief import handle as belief
    _twice(world)
    ctx = ReadContext.open(world)
    ids = [mount.corpus_id for mount in ctx.mounts()]
    for call in (lambda: belief(ctx, proposition="proposition:twice"), lambda: handle(ctx, limit=None)):
        with pytest.raises(Refused) as caught:
            call()
        assert caught.value.refusal.code == "invalid-input"
        assert all(corpus_id in caught.value.refusal.message for corpus_id in ids)


def test_one_id_in_two_corpora_refuses_selected_next_as_the_kernel_duplicate_location(world):
    """Review round 1, P2: the live capture refuses the duplicate before the
    project's query applies, whatever the project selects."""
    _twice(world)
    with open_rig(world, NAMES) as (d, _):
        d.invoke("project", {"name": "claimed", "query": _query({"addresses": ["proposition:claimed"]})})
        d.invoke("project-select", {"target": "claimed"})
        with pytest.raises(Refused) as caught:
            d.invoke("next", {})
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data["kind"] == "AddressMapConflict"


def test_a_read_mount_without_a_manifest_refuses_at_the_read_entry_points(world):
    """Review round 1, P2: sessionless `belief` and unselected `next` name the
    root, never an internal error."""
    from science.commands.belief import handle as belief
    empty = world.world.world_root.parent / "empty"
    empty.mkdir()
    ctx = ReadContext.open(dataclasses.replace(world, world=WorldConfig(
        world.world.world_root, world.world.world_id, world.world.corpus_roots + (empty,))))
    for call in (lambda: belief(ctx, proposition="proposition:archived"), lambda: handle(ctx, limit=None)):
        with pytest.raises(Refused) as caught:
            call()
        assert caught.value.refusal.code == "invalid-input" and str(empty) in caught.value.refusal.message
