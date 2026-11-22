"""The documented source-checkout example must finish through production confinement,
and its probe world must build and read back against current code."""
from pathlib import Path
import runpy
import subprocess
import sys

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
    world = example["create"](certified_work / "demo")
    cfg, proposition = example["walk"](world)
    ctx = ReadContext.open(cfg)
    (key,) = ctx.claim_view(proposition).beliefs
    assert isinstance(ctx.evaluate(proposition, key=key), Belief)
    assert classify(ctx, proposition) == "admitted"
    verification, = [n for n in ctx.write_view().iter_stored() if n.kind == "verification"]
    assert verification.facets["verification"]["verdict"] == "passed"
    assert verification.facets["verification"]["scope"] == "clean-environment"

    found = example["readback"](world.config)
    (claim,) = found["propositions"]
    (spec,) = found["specs"]
    (assessment,) = found["assessments"]
    (checked,) = found["verifications"]
    assert claim["id"] == proposition and spec["target"] == proposition
    assert spec["id"] == "analysis-spec:" + spec["identity"] and '"form":"contrast"' in spec["estimand"]
    assert len(found["runs"]) == 2
    for run in found["runs"]:
        assert run["spec_identity"] == spec["identity"]
        assert run["policy"] == "boundary-policy/confined-v1"
        assert "network-denied" in run["capabilities"]
        assert [name for name, _ in run["outputs"]] == ["outputs/outcome.txt", "outputs/stats.tsv"]
    assert assessment["run"] in {run["id"].removeprefix("run:") for run in found["runs"]}
    assert assessment["outcome"] == "supported"
    assert checked["assessment"] == assessment["id"].removeprefix("assessment:")
    assert (checked["scope"], checked["verdict"]) == ("clean-environment", "passed")
    counts = found["records"]["by_kind"]
    assert {kind: counts[kind] for kind in ("proposition", "analysis-spec", "run", "assessment", "verification")} \
        == {"proposition": 1, "analysis-spec": 1, "run": 2, "assessment": 1, "verification": 1}
    assert found["records"]["total"] == sum(counts.values())
    printed = example["render"](found).splitlines()
    assert f"assessment {assessment['id']} run {assessment['run']} outcome supported" in printed
    assert sum(line.startswith("run run:") for line in printed) == 2


def test_created_probe_world_holds_only_its_prerequisites(certified_work, tmp_path):
    example = runpy.run_path(str(ASSETS / "demo.py"))
    root = certified_work / "probe"
    world = example["create"](root)
    for path in (world.config, world.estimand, world.data, world.code / "workflow" / "Snakefile"):
        assert path.is_file()
    assert world.rule_procedure.startswith("beliefs/outcome-file/v1=procedure:")
    with pytest.raises(FileExistsError):
        example["create"](root)

    home = tmp_path / "home"
    home.mkdir()
    environment = {"PATH": "/usr/bin:/bin", "HOME": str(home), "PYTHONPATH": "tests"}
    completed = subprocess.run(
        [sys.executable, str(ASSETS / "demo.py"), "readback", str(world.config)],
        cwd=ASSETS.parents[2], env=environment, capture_output=True, text=True, timeout=300,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.splitlines() == [
        "records 7: classification-rule 1, dataset 2, holdings-observation 2, procedure 2"
    ]
