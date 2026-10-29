"""Milestone 1a's decisive cases end to end (commons 1a, Task 12; spec §12 part 1a): B reproduces A's assessment,
derives a changed analysis over A's mounted records without redeclaring any, publishes it with attributions to
A, its belief honours `accept`, and a publish retried after a partial push converges."""
import secrets
import subprocess
from dataclasses import replace

from beliefs import stored
from beliefs.intents.publish import Destination
from beliefs.runrecord import decode_run_closure
from helpers.commons import (
    GIT_ENV,
    LOC_A,
    LOC_B,
    Remotes,
    a_identity,
    b_derivation,
    binding_ref,
    closure_input_addresses,
    commit_count,
    derive_changed_analysis,
    refused,
    transport_with,
    with_remotes,
)
from helpers.world import fixture_bundle, open_rig
import science.publication as publication
from science.commands.belief import handle as belief
from science.config import ReadContext
from science.publication import binding_fields, marker_fields, marker_of
from science.report import KeyVals
from science.world_belief import publish_session_epoch
from test_cmd_publish import _pending
from test_mount_citations import _confine


def _belief(cfg, proposition: str) -> tuple[dict[str, str], dict[str, str]]:
    blocks = {block.title: dict(block.pairs) for block in belief(ReadContext.open(cfg), proposition=proposition)
              if isinstance(block, KeyVals)}
    return blocks["answer"], blocks["acceptance"]


def _identity(cfg, assessment: str) -> str:
    """The kernel identity of the assessment record `assessment`, wherever the session holds it."""
    return stored.assessment_value(ReadContext.open(cfg).cited(assessment).view.get(assessment),
                                   profile=cfg.profile).identity()


def _head(bare) -> tuple[str, str]:
    """The commit `main` names in a bare repository and that commit's tree."""
    rev = subprocess.run(["git", "-C", str(bare), "rev-parse", "main", "main^{tree}"], env=GIT_ENV,
                         capture_output=True, text=True, check=True)
    commit, tree = rev.stdout.split()
    return commit, tree


def test_b_reproduces_one_assessment_after_fetching_the_bytes(reopened, monkeypatch):
    _confine(monkeypatch)
    ids = a_identity(reopened.a)
    code, entrypoint, _ = fixture_bundle(reopened.remotes.parent / "a")   # the bundle A's run was minted from
    with open_rig(reopened.b, ("fetch", "verify")) as (d, _):
        d.invoke("fetch", {"dataset": ids["dataset"], "source": str(reopened.data_a_path())})
        text = d.invoke("verify", {"assessment": ids["assessment"], "code": str(code), "entrypoint": entrypoint}).text
    assert "[verification]" in text
    ctx = ReadContext.open(reopened.b)
    assert ctx.cited(ids["assessment"]).corpus_id == ids["corpus_id"]
    assert not any(node.kind == "dataset" for node in ctx.write_view().iter_stored())


def test_b_derives_without_redeclaring_and_the_lineage_reaches_as_dataset(verified):   # bytes already fetched
    ids = a_identity(verified.a)
    derived = derive_changed_analysis(verified)
    assert derived["assessment"] != ids["assessment"] and derived["spec"] != ids["spec"]
    ctx = ReadContext.open(verified.b)
    for key in ("spec", "run", "assessment"):
        assert ctx.cited(derived[key]).root == verified.b.write_root
    assert ctx.cited(ids["dataset"]).corpus_id == ids["corpus_id"]
    assert ctx.cited(ids["proposition"]).corpus_id == ids["corpus_id"]
    assert not any(node.kind in ("dataset", "proposition") for node in ctx.write_view().iter_stored())
    run = decode_run_closure(ctx.cited(derived["run"]).view.get(derived["run"]))
    assert closure_input_addresses(run) == frozenset({ids["dataset"]})


def test_bs_marker_attributes_the_carried_records_to_a_and_not_its_own(derived):
    ids = a_identity(derived.a)
    own = b_derivation(derived.b)
    publish_session_epoch(derived.b)   # B's derivation moved its write root past the reopened epoch
    with with_remotes(derived), open_rig(derived.b, ("publish",)) as (d, ctx):
        text = d.invoke("publish", {"target": "b", "to": LOC_B}).text
        corpus_b = binding_fields(ctx.write_view().get(binding_ref(text))).corpus_id
    into = derived.remotes.parent / "fetched" / secrets.token_hex(8)
    root, _ = transport_with(derived).fetch_corpus(Destination.remote(LOC_B), corpus_b, into)
    fields = marker_fields(marker_of(root))
    assert fields.world == derived.b.world.world_id
    for key in ("proposition", "dataset", "spec", "run", "assessment"):
        assert fields.attributions[ids[key]] == (ids["corpus_id"], ids["marker"]), key
    for key in ("spec", "run", "assessment"):
        assert own[key] in fields.selection and own[key] not in fields.attributions, key


def test_belief_excludes_a_under_empty_accept_and_includes_it_under_accept_a(derived):
    """Under `accept = []` A's assessment, and B's own verification of it, leave the belief's inputs and the
    acceptance context names the exclusion; under `accept = [A]` both enter. The answer is `no-eligible-assessment`
    either way: A's run was minted under the minimal boundary policy (the fixture is portable to hosts without
    confinement), so B's replay of it can certify only `same-environment`, and the kernel admits only
    `clean-environment` passes. B's own changed analysis is unverified."""
    ids = a_identity(derived.a)
    own = b_derivation(derived.b)
    a_assessment = _identity(derived.b, ids["assessment"])
    publish_session_epoch(derived.b)   # a belief reads over a current epoch; B's derivation moved its write root

    answer, acceptance = _belief(derived.b, ids["proposition"])
    assert acceptance[f"excluded {ids['assessment']} ({ids['corpus_id']})"] == f"corpus {ids['corpus_id']}; world {ids['world']}"
    inputs = ReadContext.open(derived.b).gather_inputs(ids["proposition"])
    assert {value.identity() for value in inputs.assessments} == {_identity(derived.b, own["assessment"])}
    assert not [v for v in inputs.verifications if v.assessment == a_assessment]
    assert (answer["kind"], answer["reason"]) == ("NoBelief", "no-eligible-assessment")

    accepting = replace(derived.b, accept=(ids["world"],))
    answer, acceptance = _belief(accepting, ids["proposition"])
    assert acceptance["excluded"] == "none"
    inputs = ReadContext.open(accepting).gather_inputs(ids["proposition"])
    assert {value.identity() for value in inputs.assessments} == {
        _identity(derived.b, own["assessment"]), a_assessment}
    (verification,) = [v for v in inputs.verifications if v.assessment == a_assessment]
    assert (verification.scope, verification.verdict) == ("same-environment", "passed")
    assert (answer["kind"], answer["reason"]) == ("NoBelief", "no-eligible-assessment")


def test_publish_retried_after_a_partial_push_converges(fresh):
    """Spec §12's transport case over the real git remote: the push lands and the publish then faults; a fresh
    attempt is blocked naming the unfinished one; resuming it finds every file present, commits nothing new and
    leaves the remote's content as the partial push wrote it."""
    bare = Remotes(fresh.remotes).bare("a")
    saved = publication.transport_for
    try:
        with with_remotes(fresh), open_rig(fresh.a, ("publish",)) as (d, ctx):
            fault = transport_with(fresh, fail_after_push=True)
            publication.transport_for = lambda config, destination: fault
            first = refused(lambda: d.invoke("publish", {"target": "a", "to": LOC_A}, invocation_id="p1"))
            assert first.code == "kernel-refused" and first.data["reason"] == "transport-fault"
            pushed = _head(bare)   # the push landed before the fault
            assert commit_count(bare) == 1
            blocked = refused(lambda: d.invoke("publish", {"target": "a", "to": LOC_A}, invocation_id="p2"))
            (token,) = _pending(fresh.a)
            assert blocked.data["reason"] == "publish-unfinished" and token in blocked.message
            fault.fail_after_push = False
            text = d.invoke("publish", {"target": "a", "to": LOC_A, "resume": token}, invocation_id="p3").text
            binding = binding_fields(ctx.write_view().get(binding_ref(text)))
    finally:
        publication.transport_for = saved
    assert _head(bare) == pushed and commit_count(bare) == 1 and _pending(fresh.a) == ()
    into = fresh.remotes.parent / "fetched" / secrets.token_hex(8)
    root, _ = transport_with(fresh).fetch_corpus(Destination.remote(LOC_A), binding.corpus_id, into)
    assert marker_fields(marker_of(root)).uid == binding.marker
