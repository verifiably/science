import pytest

from science.refusal import Refused
from helpers.world import OBSERVED, SPEC_FIELDS, build_belief_world, fixture_bundle, hold_fixture_dataset, mint_fixture_run, open_rig


@pytest.fixture
def rig(certified_work, monkeypatch):
    import science.commands.run as run_module
    from beliefs.confinement import host_prerequisites
    from beliefs.recipe import MINIMAL_POLICY
    if host_prerequisites() is not None:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression", **OBSERVED)
    bundle = fixture_bundle(certified_work, "supported")
    with open_rig(cfg, ("spec", "assess", "verify")) as (d, ctx):
        spec_ref = next(t for t in d.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=ref)).text.split()
                        if t.startswith("analysis-spec:"))
        run_ref = mint_fixture_run(cfg, spec_ref, ref, bundle)
        assessment_ref = next(t for t in d.invoke("assess", {"run": run_ref}).text.split() if t.startswith("assessment:"))
        yield d, ctx, assessment_ref, bundle


def test_verify_mints_a_verification_naming_the_assessment_and_both_runs(rig):
    d, ctx, assessment_ref, (code, entrypoint, _) = rig
    out = d.invoke("verify", {"assessment": assessment_ref, "code": str(code), "entrypoint": entrypoint})
    assert "[verification] verification:" in out.text
    _, view = ctx.single_view()
    node = next(n for n in view.iter_stored() if n.kind == "verification")
    facet = node.facets["verification"]
    assert facet["verdict"] == "passed"
    assert facet["derivation"]["original"] != facet["derivation"]["replayed"]
    assert sum(1 for n in view.iter_stored() if n.kind == "run") == 2
    assert any(r.target == assessment_ref for r in node.relations)


def test_verify_refuses_an_unknown_assessment(rig):
    d, _, _, (code, entrypoint, _) = rig
    with pytest.raises(Refused) as caught:
        d.invoke("verify", {"assessment": "assessment:0000000000000000", "code": str(code), "entrypoint": entrypoint})
    assert caught.value.refusal.code == "invalid-input"


def test_a_disagreeing_replay_yields_failed_and_still_mints(rig, certified_work):
    """The bundle's outcome file is rewritten between run and replay; the
    equivalence rule says failed; the verification is a record either way."""
    d, ctx, assessment_ref, (code, entrypoint, _) = rig
    (code / "workflow" / "Snakefile").write_text((code / "workflow" / "Snakefile").read_text().replace("supported", "refuted"))
    with pytest.raises(Refused) as caught:
        d.invoke("verify", {"assessment": assessment_ref, "code": str(code), "entrypoint": entrypoint})
    # A changed bundle changes the recipe identity: the boundary refuses the
    # replay as a different recipe, never a silently different result.
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data["kind"] == "RunRefused"
