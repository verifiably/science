"""The documented source-checkout example must finish through production confinement."""
from pathlib import Path
import runpy

import pytest
from beliefs.confinement import host_prerequisites
from beliefs.belief import Belief
from science.commands.next import classify
from science.config import ReadContext

ASSETS = Path(__file__).parent / "fixtures" / "analysis"


def test_documented_example_reaches_a_verified_keyed_belief(certified_work):
    reason = host_prerequisites()
    if reason is not None:
        pytest.skip(f"confinement unavailable: {reason}")
    example = runpy.run_path(str(ASSETS / "demo.py"))
    cfg, proposition = example["run_demo"](certified_work / "demo")
    ctx = ReadContext.open(cfg)
    (key,) = ctx.claim_view(proposition).beliefs
    assert isinstance(ctx.evaluate(proposition, key=key), Belief)
    assert classify(ctx, proposition) == "admitted"
    verification, = [n for n in ctx.write_view().iter_stored() if n.kind == "verification"]
    assert verification.facets["verification"]["verdict"] == "passed"
    assert verification.facets["verification"]["scope"] == "clean-environment"
