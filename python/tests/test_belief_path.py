"""The success criterion over the fixture world: claim -> dataset -> spec ->
run -> assess -> verify -> belief, every step a record, through one
dispatcher. Two hosts, two answers: under the minimal boundary policy a
replay cannot qualify as clean-environment, so the verification does not
admit and the belief stays NoBelief; under confinement it admits."""
import pytest

from beliefs.confinement import host_prerequisites
from science.report import KeyVals
from helpers.snapshot import snapshot
from helpers.world import BELIEF_PATH_COMMANDS, open_rig, walk_belief_path

CONFINED = host_prerequisites() is None


def _walked(work_base, monkeypatch, *, confined: bool):
    import science.commands.run as run_module
    from beliefs.recipe import MINIMAL_POLICY
    name = "walked-confined" if confined else "walked-portable"
    snap = snapshot(work_base, name, lambda work: walk_belief_path(work, confined=confined))
    snap.restore()
    if not confined:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
        monkeypatch.setattr(run_module, "host_prerequisites", lambda: None)
    cfg, prop = snap.value
    return cfg, prop


@pytest.fixture
def walked_portable(certified_worker_work, monkeypatch):
    cfg, prop = _walked(certified_worker_work, monkeypatch, confined=False)
    with open_rig(cfg, BELIEF_PATH_COMMANDS) as (d, ctx):
        yield d, ctx, prop, cfg


@pytest.fixture
def walked_confined(certified_worker_work, monkeypatch):
    if not CONFINED:
        pytest.skip(f"confinement unavailable: {host_prerequisites()}")
    cfg, prop = _walked(certified_worker_work, monkeypatch, confined=True)
    with open_rig(cfg, BELIEF_PATH_COMMANDS) as (d, ctx):
        yield d, ctx, prop, cfg


def _answer(ctx, prop):
    from science.commands.belief import handle as belief
    return dict(next(b for b in belief(ctx, proposition=prop) if isinstance(b, KeyVals)).pairs)


def test_every_step_left_exactly_its_record(walked_portable):
    _, ctx, _, _ = walked_portable
    view = ctx.write_view()
    kinds = sorted(n.kind for n in view.iter_stored())
    # The contract world holds the concept and level lists; the walk holds the data.
    assert kinds.count("proposition") == 1 and kinds.count("dataset") == 3
    assert kinds.count("analysis-spec") == 1 and kinds.count("run") == 2
    assert kinds.count("assessment") == 1 and kinds.count("verification") == 1


def test_without_confinement_the_verification_does_not_admit(walked_portable):
    """same-environment, passed — a real verification, not an admitting one."""
    from science.commands.next import classify
    _, ctx, prop, _ = walked_portable
    view = ctx.write_view()
    facet = next(n for n in view.iter_stored() if n.kind == "verification").facets["verification"]
    assert facet["verdict"] == "passed" and facet["scope"] == "same-environment"
    pairs = _answer(ctx, prop)
    assert pairs["kind"] == "NoBelief" and pairs["reason"] == "no-eligible-assessment"
    assert classify(ctx, prop) == "assessed-not-admitted"


def test_under_confinement_the_path_ends_in_an_admitted_belief(walked_confined):
    from science.commands.next import classify
    _, ctx, prop, _ = walked_confined
    view = ctx.write_view()
    facet = next(n for n in view.iter_stored() if n.kind == "verification").facets["verification"]
    assert facet["scope"] == "clean-environment" and facet["verdict"] == "passed"
    pairs = _answer(ctx, prop)
    assert pairs["kind"] == "Belief", pairs
    assert pairs["value"] and pairs["belief_input_digest"] and pairs["policy_binding"]
    assert classify(ctx, prop) == "admitted"
