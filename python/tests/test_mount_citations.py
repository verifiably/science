"""Mount citations consumer spec, decisions 1–3: a write cites a record any
session corpus holds; a mutation target stays in the write root."""
import dataclasses

import pytest

from beliefs import stored
from beliefs.root import open_corpus
from helpers.world import (
    FIXTURE_AUTHORITY, SPEC_FIELDS, WORKING_FIELDS, _minted_ref, add_mounted_evidence,
    build_shared_contract_world, fixture_bundle, mint_fixture_run, mount_config, open_rig,
)
from science.commands.next import classify, handle as next_handle
from science.config import ReadContext
from science.refusal import Refused
from science.world_belief import publish_session_epoch

LOCAL = {"subject": "concept:remission", "predicate": "affects", "object": "protein:PHF19",
         "layer": "causal", "polarity": "positive", "slug": "local"}


def _confine(monkeypatch) -> None:
    import science.commands.run as run_module
    from beliefs.confinement import host_prerequisites
    from beliefs.recipe import MINIMAL_POLICY
    if host_prerequisites() is not None:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)


@pytest.fixture
def shared(certified_work, monkeypatch):
    _confine(monkeypatch)
    cfg = build_shared_contract_world(certified_work)
    return cfg, add_mounted_evidence(cfg, certified_work)


@pytest.fixture(scope="module")
def shared_read(certified_module_work):
    """`shared`, built once for the module's read-only resolver tests (final
    review I5). A test that writes, or publishes an epoch, takes `shared`."""
    with pytest.MonkeyPatch.context() as monkeypatch:
        _confine(monkeypatch)
        cfg = build_shared_contract_world(certified_module_work)
        return cfg, add_mounted_evidence(cfg, certified_module_work)


def _ids(cfg) -> dict[str, str]:
    return {mount.root.name: mount.corpus_id for mount in ReadContext.open(cfg).mounts()}


def test_a_mounted_record_is_cited_from_its_holder(shared_read):
    cfg, mounted = shared_read
    ctx = ReadContext.open(cfg)
    assert [m.root.name for m in ctx.session_mounts()] == sorted(
        ("corpus", "shared"), key=lambda name: _ids(cfg)[name])
    assert ctx.has_read_mounts() and ctx.session_ids() == frozenset(_ids(cfg).values())
    for ref in (mounted["data"], mounted["assessment"], "proposition:shared"):
        assert ctx.cited(ref).root.name == "shared"


def test_with_coordination_off_a_mounted_ref_refuses_naming_the_mount(shared_read):
    cfg, mounted = shared_read
    ctx = ReadContext.open(dataclasses.replace(cfg, coordination=None))
    assert [m.root.name for m in ctx.session_mounts()] == ["corpus"] and not ctx.has_read_mounts()
    with pytest.raises(Refused) as caught:
        ctx.cited(mounted["data"])
    assert caught.value.refusal.code == "invalid-input"
    assert _ids(cfg)["shared"] in caught.value.refusal.message
    assert "coordination" in caught.value.refusal.message


def test_has_read_mounts_opens_no_corpus(shared_read, monkeypatch):
    """Final review M5: the question is the configuration's, answered without
    opening a view or reading a manifest."""
    cfg, _ = shared_read

    def opened(*_, **__):
        pytest.fail("has_read_mounts opened the corpora")

    monkeypatch.setattr(ReadContext, "mounts", opened)
    assert ReadContext.open(cfg).has_read_mounts()
    assert not ReadContext.open(dataclasses.replace(cfg, coordination=None)).has_read_mounts()


def test_a_ref_two_session_corpora_hold_refuses_naming_both(shared):
    cfg, _ = shared
    node = stored.proposition_node("twice", title="twice", claim={"operator": "affects"})
    for each in (cfg, mount_config(cfg)):
        open_corpus(each.write_root, authority=FIXTURE_AUTHORITY, profile=each.profile).add(node)
    with pytest.raises(Refused) as caught:
        ReadContext.open(cfg).cited("proposition:twice")
    assert caught.value.refusal.code == "invalid-input"
    assert all(corpus_id in caught.value.refusal.message for corpus_id in _ids(cfg).values())


def test_own_refuses_a_mounted_record_naming_the_mount(shared_read):
    cfg, mounted = shared_read
    with pytest.raises(Refused) as caught:
        ReadContext.open(cfg).own(mounted["spec"])
    assert caught.value.refusal.code == "invalid-input"
    assert _ids(cfg)["shared"] in caught.value.refusal.message
    assert "write root" in caught.value.refusal.message


def test_an_unheld_ref_refuses_without_a_hint(shared_read):
    cfg, _ = shared_read
    with pytest.raises(Refused) as caught:
        ReadContext.open(cfg).cited("proposition:nowhere")
    assert caught.value.refusal.message == "'proposition:nowhere' is not in the session's corpora"


def test_spec_run_and_assess_in_the_write_root_cite_the_mount(shared, certified_work):
    """Decision 1: the second-project shape. Every new record lands in the
    write root, and every record it cites stays in the mount."""
    cfg, mounted = shared
    with open_rig(cfg, ("spec",)) as (d, _):
        spec = _minted_ref(d.invoke("spec", dict(WORKING_FIELDS, target="proposition:shared",
                                                 dataset=mounted["data"])).text, "analysis-spec")
    assert spec != mounted["spec"]
    run = mint_fixture_run(cfg, spec, mounted["data"], fixture_bundle(certified_work))
    with open_rig(cfg, ("assess",)) as (d, _):
        assessment = _minted_ref(d.invoke("assess", {"run": run}).text, "assessment")
    own = ReadContext.open(cfg).write_view()
    assert own.holds(spec) and own.holds(run) and own.holds(assessment)
    assert not own.holds("proposition:shared") and not own.holds(mounted["data"])


def test_run_prepares_a_mounted_spec_and_dataset(shared, certified_work):
    from science.commands.run import prepare
    cfg, mounted = shared
    code, entrypoint, targets = fixture_bundle(certified_work)
    prepared = prepare(ReadContext.open(cfg), mounted["spec"], mounted["data"], str(code), entrypoint, targets)
    assert list(prepared["held_inputs"]) == [prepared["spec"].input_roles[0].dataset]


def test_verify_of_a_mounted_assessment_lands_in_the_write_root(shared, certified_work):
    cfg, mounted = shared
    code, entrypoint, _ = fixture_bundle(certified_work)
    with open_rig(cfg, ("verify",)) as (d, _):
        out = d.invoke("verify", {"assessment": mounted["assessment"], "code": str(code),
                                  "entrypoint": entrypoint})
    verification = _minted_ref(out.text, "verification")
    assert ReadContext.open(cfg).write_view().holds(verification)


def test_supersedes_names_a_write_root_spec_only(shared):
    cfg, mounted = shared
    with open_rig(cfg, ("spec",)) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("spec", dict(SPEC_FIELDS, target="proposition:shared", dataset=mounted["data"],
                                  supersedes=mounted["spec"]))
    assert caught.value.refusal.code == "invalid-input"
    assert _ids(cfg)["shared"] in caught.value.refusal.message
    assert "write root" in caught.value.refusal.message


def _walk(cfg, mounted, work) -> str:
    """spec → run → assess in the write root over the mount's proposition and
    data; returns the assessment ref."""
    with open_rig(cfg, ("spec",)) as (d, _):
        spec = _minted_ref(d.invoke("spec", dict(WORKING_FIELDS, target="proposition:shared",
                                                 dataset=mounted["data"])).text, "analysis-spec")
    run = mint_fixture_run(cfg, spec, mounted["data"], fixture_bundle(work))
    with open_rig(cfg, ("assess",)) as (d, _):
        return _minted_ref(d.invoke("assess", {"run": run}).text, "assessment")


def test_mounted_belief_needs_an_epoch(shared, certified_work):
    from science.commands.belief import handle as belief
    cfg, mounted = shared
    _walk(cfg, mounted, certified_work)
    with pytest.raises(Refused) as caught:
        belief(ReadContext.open(cfg), proposition="proposition:shared")
    assert caught.value.refusal.code == "no-epoch"


def test_at_a_current_epoch_belief_counts_the_write_roots_assessment_of_a_mounted_proposition(
        shared, certified_work):
    from science.commands.belief import handle as belief
    from science.world_belief import publish_session_epoch
    cfg, mounted = shared
    assessment = _walk(cfg, mounted, certified_work)
    publish_session_epoch(cfg)
    ctx = ReadContext.open(cfg)
    inputs = ctx.gather_inputs("proposition:shared")
    local = stored.assessment_value(ctx.write_view().get(assessment), profile=cfg.profile).identity()
    held = stored.assessment_value(ctx.cited(mounted["assessment"]).view.get(mounted["assessment"]),
                                   profile=cfg.profile).identity()
    assert {local, held} <= {a.identity() for a in inputs.assessments}
    report = belief(ctx, proposition="proposition:shared")
    assert dict(report[1].pairs)["kind"] in ("Belief", "NoBelief")


def test_a_world_read_finds_the_observations_once_per_context(shared, monkeypatch):
    """Final review M5: the world context, its observations and the snapshot's
    are one computation per context, however many propositions it evaluates."""
    cfg, _ = shared
    publish_session_epoch(cfg)
    found = ReadContext.observations
    calls = []

    def counted(self):
        calls.append(None)
        return found(self)

    monkeypatch.setattr(ReadContext, "observations", counted)
    ctx = ReadContext.open(cfg)
    for proposition in ("proposition:shared", "proposition:fresh"):
        ctx.evaluate(proposition)
        ctx.gather_inputs(proposition)
    assert len(calls) == 1


def test_a_read_mount_write_after_the_epoch_is_stale_naming_the_mount(shared, certified_work):
    from science.commands.belief import handle as belief
    from science.world_belief import publish_session_epoch
    cfg, mounted = shared
    publish_session_epoch(cfg)
    mounted_cfg = mount_config(cfg)
    open_corpus(mounted_cfg.write_root, authority=FIXTURE_AUTHORITY, profile=mounted_cfg.profile).add(
        stored.proposition_node("late", title="late", claim={"operator": "affects"}))
    with pytest.raises(Refused) as caught:
        belief(ReadContext.open(cfg), proposition="proposition:shared")
    assert caught.value.refusal.code == "epoch-stale"
    assert caught.value.refusal.data["drifted"] == [_ids(cfg)["shared"]]


def test_with_coordination_off_belief_stays_corpus_local_without_an_epoch(shared):
    """Review focus 1: no read mounts, no epoch needed."""
    from science.commands.belief import handle as belief
    cfg, _ = shared
    local = dataclasses.replace(cfg, coordination=None)
    report = belief(ReadContext.open(local), proposition="proposition:shared")
    assert dict(report[1].pairs)["kind"] in ("Belief", "NoBelief")


def _local_walk(cfg, mounted, work) -> str:
    """claim → spec → run → assess, all in the write root, on a write-root
    proposition over the mount's dataset; returns the assessment ref."""
    with open_rig(cfg, ("claim", "spec")) as (d, _):
        d.invoke("claim", LOCAL)
        spec = _minted_ref(d.invoke("spec", dict(WORKING_FIELDS, target="proposition:local",
                                                 dataset=mounted["data"])).text, "analysis-spec")
    run = mint_fixture_run(cfg, spec, mounted["data"], fixture_bundle(work))
    with open_rig(cfg, ("assess",)) as (d, _):
        return _minted_ref(d.invoke("assess", {"run": run}).text, "assessment")


def test_cross_corpus_evidence_read_without_mounts_is_the_kernels_input_outside_corpus(shared, certified_work):
    from science.commands.belief import handle as belief
    cfg, mounted = shared
    _local_walk(cfg, mounted, certified_work)
    report = belief(ReadContext.open(dataclasses.replace(cfg, coordination=None)), proposition="proposition:local")
    answer = dict(report[1].pairs)
    assert answer["kind"] == "Refused" and answer["reason"].startswith("input-outside-corpus")
    assert mounted["data"] in answer["reason"]


def test_a_write_root_spec_on_a_mounted_proposition_makes_it_ready(shared, certified_work):
    """Review round 1, P2 1: readiness reads specs in every session corpus.
    proposition:fresh is mounted with no evidence anywhere until the write root
    writes a spec on it."""
    cfg, mounted = shared
    assert classify(ReadContext.open(cfg), "proposition:fresh") == "not-ready"
    with open_rig(cfg, ("spec",)) as (d, _):
        d.invoke("spec", dict(WORKING_FIELDS, target="proposition:fresh", dataset=mounted["data"]))
    assert classify(ReadContext.open(cfg), "proposition:fresh") == "ready"


def test_next_marks_mounted_evidence_unevaluated_without_an_epoch_and_judges_it_with_one(
        shared, certified_work):
    cfg, mounted = shared
    _walk(cfg, mounted, certified_work)
    assert classify(ReadContext.open(cfg), "proposition:shared") == "assessed-unevaluated"
    rows = dict(next_handle(ReadContext.open(cfg), limit=None)[-1].pairs)
    assert rows["proposition:shared"].startswith("assessed-unevaluated (no-epoch): ")
    assert rows["proposition:fresh"].startswith("not-ready: ")
    publish_session_epoch(cfg)
    assert classify(ReadContext.open(cfg), "proposition:shared") == "assessed-not-admitted"


def test_with_coordination_off_next_classifies_from_the_holders_own_corpus(shared, certified_work):
    """Plan review round 1, P2 4: no read mounts means today's holder-local
    rule. The mount's proposition keeps the spec and assessment its own corpus
    holds, and no epoch is asked for."""
    cfg, _ = shared
    off = ReadContext.open(dataclasses.replace(cfg, coordination=None))
    assert classify(off, "proposition:shared") == "assessed-not-admitted"
    assert classify(off, "proposition:fresh") == "not-ready"


def test_cross_corpus_evidence_read_without_mounts_is_an_unevaluated_row(shared, certified_work):
    """Plan review round 1, P2 5: authored normally, then read with
    coordination off, the corpus-local gather raises InputOutsideCorpus. The
    row says so; next neither fails internally nor blanks every row."""
    cfg, mounted = shared
    _local_walk(cfg, mounted, certified_work)
    off = dataclasses.replace(cfg, coordination=None)
    assert classify(ReadContext.open(off), "proposition:local") == "assessed-unevaluated"
    rows = dict(next_handle(ReadContext.open(off), limit=None)[-1].pairs)
    assert rows["proposition:local"].startswith("assessed-unevaluated (input-outside-corpus): ")
    assert rows["proposition:shared"].startswith("assessed-not-admitted: ")


def test_verify_with_coordination_off_names_the_corpus_declaring_the_dataset(shared, certified_work):
    """Final review M1: a spec whose dataset only a read mount declares refuses
    with `cited`'s hint, naming that corpus, not a bare "not in the session"."""
    from science.commands.verify import handle as verify
    cfg, mounted = shared
    assessment = _local_walk(cfg, mounted, certified_work)
    code, entrypoint, _ = fixture_bundle(certified_work)
    off = ReadContext.open(dataclasses.replace(cfg, coordination=None))
    with pytest.raises(Refused) as caught:
        verify(off, None, assessment=assessment, code=str(code), entrypoint=entrypoint)
    assert caught.value.refusal.code == "invalid-input"
    assert _ids(cfg)["shared"] in caught.value.refusal.message
    assert "coordination" in caught.value.refusal.message
