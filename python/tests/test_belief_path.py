"""The success criterion over the fixture world: claim -> dataset -> spec ->
run -> assess -> verify -> belief, every step a record, through one
dispatcher. Two hosts, two answers: under the minimal boundary policy a
replay cannot qualify as clean-environment, so the verification does not
admit and the belief stays NoBelief; under confinement it admits."""
import pytest

from beliefs.confinement import host_prerequisites
from science.report import KeyVals
from helpers.world import SPEC_FIELDS, build_fixture_world_with_contract, fixture_bundle, open_rig

CONFINED = host_prerequisites() is None


def walk(certified_work, monkeypatch, *, confined: bool):
    import science.commands.run as run_module
    from beliefs.recipe import MINIMAL_POLICY
    if not confined:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
        monkeypatch.setattr(run_module, "host_prerequisites", lambda: None)
    cfg = build_fixture_world_with_contract(certified_work)
    code, entrypoint, targets = fixture_bundle(certified_work, "supported")
    data = certified_work / "data.txt"
    data.write_bytes(b"x\n")
    names = ("claim", "dataset", "spec", "run", "assess", "verify", "belief", "next")
    rig = open_rig(cfg, names)
    d, ctx = rig.__enter__()

    def ref(text, prefix):
        return next(t for t in text.split() if t.startswith(prefix))
    prop = ref(d.invoke("claim", {"subject": "concept:disease-stage", "predicate": "affects",
                                  "object": "protein:PHF19", "layer": "causal", "polarity": "positive"}).text,
               "proposition:")
    dataset = ref(d.invoke("dataset", {"path": str(data), "title": "expression",
                                       "locator": "accession:GSE-FIXTURE"}).text, "dataset:")
    spec = ref(d.invoke("spec", dict(SPEC_FIELDS, target=prop, dataset=dataset)).text, "analysis-spec:")
    run = ref(d.invoke("run", {"spec": spec, "dataset": dataset, "code": str(code),
                               "entrypoint": entrypoint, "targets": list(targets)}).text, "run:")
    assessment = ref(d.invoke("assess", {"run": run}).text, "assessment:")
    d.invoke("verify", {"assessment": assessment, "code": str(code), "entrypoint": entrypoint})
    return rig, d, ctx, prop, cfg


@pytest.fixture
def walked_portable(certified_work, monkeypatch):
    rig, d, ctx, prop, cfg = walk(certified_work, monkeypatch, confined=False)
    try:
        yield d, ctx, prop, cfg
    finally:
        rig.__exit__(None, None, None)


@pytest.fixture
def walked_confined(certified_work, monkeypatch):
    if not CONFINED:
        pytest.skip(f"confinement unavailable: {host_prerequisites()}")
    rig, d, ctx, prop, cfg = walk(certified_work, monkeypatch, confined=True)
    try:
        yield d, ctx, prop, cfg
    finally:
        rig.__exit__(None, None, None)


def _answer(ctx, prop):
    from science.commands.belief import handle as belief
    return dict(next(b for b in belief(ctx, proposition=prop) if isinstance(b, KeyVals)).pairs)


def test_every_step_left_exactly_its_record(walked_portable):
    _, ctx, _, _ = walked_portable
    _, view = ctx.single_view()
    kinds = sorted(n.kind for n in view.iter_stored())
    # The contract world holds the concept and level lists; the walk holds the data.
    assert kinds.count("proposition") == 1 and kinds.count("dataset") == 3
    assert kinds.count("analysis-spec") == 1 and kinds.count("run") == 2
    assert kinds.count("assessment") == 1 and kinds.count("verification") == 1


def test_without_confinement_the_verification_does_not_admit(walked_portable):
    """same-environment, passed — a real verification, not an admitting one."""
    from science.commands.next import classify
    _, ctx, prop, _ = walked_portable
    _, view = ctx.single_view()
    facet = next(n for n in view.iter_stored() if n.kind == "verification").facets["verification"]
    assert facet["verdict"] == "passed" and facet["scope"] == "same-environment"
    pairs = _answer(ctx, prop)
    assert pairs["kind"] == "NoBelief" and pairs["reason"] == "no-eligible-assessment"
    assert classify(ctx, prop) == "assessed-not-admitted"


def test_under_confinement_the_path_ends_in_an_admitted_belief(walked_confined):
    from science.commands.next import classify
    _, ctx, prop, _ = walked_confined
    _, view = ctx.single_view()
    facet = next(n for n in view.iter_stored() if n.kind == "verification").facets["verification"]
    assert facet["scope"] == "clean-environment" and facet["verdict"] == "passed"
    pairs = _answer(ctx, prop)
    assert pairs["kind"] == "Belief", pairs
    assert pairs["value"] and pairs["belief_input_digest"] and pairs["policy_binding"]
    assert classify(ctx, prop) == "admitted"
