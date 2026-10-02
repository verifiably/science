"""Spec §9, the two-corpus check: each proposition's evidence in its own
corpus, each corpus decoded under its own manifest's profile."""
import dataclasses
import json

import pytest

from beliefs.profile import compile_profile, shipped_base_contract, shipped_coordination, shipped_domain_contract
from beliefs.world import WorldConfig
from helpers.snapshot import snapshot
from helpers.world import (
    COORDINATION, DOMAINS, FIXTURE_AUTHORITY, build_two_corpus_walked_world, build_two_corpus_world,
    open_rig, write_two_corpus_config,
)
from science.commands.next import handle
from science.config import ReadContext, corpus_id_at
from science.refusal import Refused
from science.session import open_session

NAMES = ("claim", "spec", "project", "project-select", "next", "belief")
VERSION = "science.view-query.v1"


def _query(clause):
    return json.dumps({"version": VERSION, "clauses": [{"all": [clause]}]})


def _rows(text):
    return text.split("propositions:\n", 1)[1]


@pytest.fixture
def world(certified_worker_work):
    """The walked two-corpus world (`build_two_corpus_walked_world`), restored."""
    snap = snapshot(certified_worker_work, "two-corpus-walked", build_two_corpus_walked_world)
    snap.restore()
    return snap.value


@pytest.fixture
def two_corpora(certified_worker_work):
    """`build_two_corpus_world` alone, for refusals that read nothing the walk mints."""
    snap = snapshot(certified_worker_work, "two-corpus", build_two_corpus_world)
    snap.restore()
    return snap.value


def test_next_under_a_project_selecting_both_classifies_each_from_its_own_corpus(world):
    """The mutation that enumerates the write root only drops the archived row;
    the mutation that decodes the read mount under the writer's profile fails
    on the corpus-local `archive` operator. Rows sort by class, then id."""
    with open_rig(world, NAMES) as (d, _):
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


def test_activating_read_contracts_in_the_writer_is_refused_by_the_write_root_pins(two_corpora):
    world = two_corpora
    from science.contracts import load_contract_document
    base = shipped_base_contract()
    loaded = [load_contract_document(world.world.world_root.parent / name, base)[0]
              for name in ("testing.yaml", "archive.yaml")]
    widened = compile_profile(base, [shipped_domain_contract(ns) for ns in DOMAINS] + loaded,
                              coordination=shipped_coordination(COORDINATION))
    widened_config = dataclasses.replace(world, profile=widened)
    with pytest.raises(Refused) as caught:
        open_session(widened_config)
    assert caught.value.refusal.code == "invalid-input"
    assert "archive" in caught.value.refusal.message
    assert "read_contracts" in caught.value.refusal.message
    # A sessionless read asks the same pins before building its resolver.
    with pytest.raises(Refused) as sessionless:
        ReadContext.open(widened_config).coordination()
    assert sessionless.value.refusal.message == caught.value.refusal.message


def test_a_selected_record_no_configured_corpus_holds_refuses_naming_it(two_corpora):
    """The world admits the archive; a configuration mounting only the write
    root cannot read the row, and says so: the kernel's unknown address is the
    configuration's refusal, naming the address and `corpus_roots`."""
    world = two_corpora
    with open_rig(world, ("project",)) as (d, _):
        d.invoke("project", {"name": "archived", "query": _query({"addresses": ["proposition:archived"]})})
    narrowed = dataclasses.replace(world, world=WorldConfig(
        world.world.world_root, world.world.world_id, (world.write_root,)))
    with open_rig(narrowed, NAMES) as (d, _):
        d.invoke("project-select", {"target": "archived"})
        with pytest.raises(Refused) as caught:
            d.invoke("next", {})
    assert caught.value.refusal.code == "invalid-input"
    assert "proposition:archived" in caught.value.refusal.message
    assert "corpus_roots" in caught.value.refusal.message
    assert corpus_id_at(world.world.world_root.parent / "archive") in caught.value.refusal.message


def _twice(world):
    from beliefs import stored
    from beliefs.root import open_corpus
    from helpers.world import archive_config
    node = stored.proposition_node("twice", title="twice", claim={"operator": "affects"})
    for cfg in (world, archive_config(world)):
        open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile).add(node)


def test_one_id_in_two_corpora_refuses_naming_both_in_belief_and_unselected_next(world):
    """The two halves differ in who judges. `belief` names the proposition, and
    `mount_holding` refuses it as `invalid-input`. The unselected `next` reads the
    world at the epoch first, so the kernel's W8b uid-uniqueness refusal
    (`ResolutionRefused`) is what reaches the reader."""
    from science.commands.belief import handle as belief
    _twice(world)
    ctx = ReadContext.open(world)
    ids = [mount.corpus_id for mount in ctx.mounts()]
    with pytest.raises(Refused) as in_belief:
        belief(ctx, proposition="proposition:twice")
    assert in_belief.value.refusal.code == "invalid-input"
    with pytest.raises(Refused) as in_next:
        handle(ctx, limit=None)
    assert in_next.value.refusal.code == "kernel-refused"
    assert in_next.value.refusal.data["kind"] == "ResolutionRefused"
    for caught in (in_belief, in_next):
        assert all(corpus_id in caught.value.refusal.message for corpus_id in ids)


def test_one_id_in_two_corpora_refuses_selected_next_as_the_kernel_duplicate_location(two_corpora):
    """Review round 1, P2: the live capture refuses the duplicate before the
    project's query applies, whatever the project selects."""
    world = two_corpora
    _twice(world)
    with open_rig(world, NAMES) as (d, _):
        d.invoke("project", {"name": "claimed", "query": _query({"addresses": ["proposition:claimed"]})})
        d.invoke("project-select", {"target": "claimed"})
        with pytest.raises(Refused) as caught:
            d.invoke("next", {})
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data["kind"] == "AddressMapConflict"


def test_a_read_mount_without_a_manifest_refuses_at_the_read_entry_points(two_corpora):
    """Review round 1, P2: sessionless `belief` and unselected `next` name the
    root, never an internal error."""
    world = two_corpora
    from science.commands.belief import handle as belief
    empty = world.world.world_root.parent / "empty"
    empty.mkdir()
    ctx = ReadContext.open(dataclasses.replace(world, world=WorldConfig(
        world.world.world_root, world.world.world_id, world.world.corpus_roots + (empty,))))
    for call in (lambda: belief(ctx, proposition="proposition:archived"), lambda: handle(ctx, limit=None)):
        with pytest.raises(Refused) as caught:
            call()
        assert caught.value.refusal.code == "invalid-input" and str(empty) in caught.value.refusal.message


def test_each_corpus_lineage_reaches_the_evaluator(world):
    """Review fix round 1: the snapshot a mount's evaluation is supplied roots
    every dataset its runs read. The mutation that drops the holding corpus's
    lineage changes the belief input digest and nothing else visible."""
    from beliefs.dataset import dataset_address
    ctx = ReadContext.open(world)
    for proposition in ("proposition:archived", "proposition:claimed"):
        inputs = ctx.gather_inputs(proposition)
        read = {dataset_address(i.dataset) for run in inputs.runs.values() for i in run.inputs}
        assert read and read <= set(inputs.snapshot.roots)
