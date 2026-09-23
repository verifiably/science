import pytest

from science.refusal import Refused
from helpers.world import OBSERVED, SPEC_FIELDS, build_belief_world, fixture_bundle, hold_fixture_dataset, mint_fixture_run, open_rig


@pytest.fixture
def rig(certified_work):
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression", **OBSERVED)
    with open_rig(cfg, ("spec",)) as (d, _):
        spec_ref = next(t for t in d.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=ref)).text.split()
                        if t.startswith("analysis-spec:"))
    # The fixture run is minted outside any session, so no attended session
    # may be open across it: a session's writer is the corpus's one writer.
    run_ref = mint_fixture_run(cfg, spec_ref, ref, fixture_bundle(certified_work, "supported"))
    with open_rig(cfg, ("assess",)) as (d, ctx):
        yield d, ctx, run_ref


def test_assess_mints_the_assessment_the_outcome_file_fixes(rig):
    d, ctx, run_ref = rig
    out = d.invoke("assess", {"run": run_ref})
    assert "[assessment] assessment:" in out.text
    _, view = ctx.single_view()
    from beliefs import stored
    node = next(n for n in view.iter_stored() if n.kind == "assessment")
    value = stored.assessment_value(node, profile=ctx.config.profile)
    assert value.outcome == "supported"
    assert value.proposition == "proposition:p1"
    assert node.id == f"assessment:{value.identity()[:16]}"


def test_assess_refuses_an_unknown_run(rig):
    d, _, _ = rig
    with pytest.raises(Refused) as caught:
        d.invoke("assess", {"run": "run:" + "0" * 64})
    assert caught.value.refusal.code == "invalid-input"
