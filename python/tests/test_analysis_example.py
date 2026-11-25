"""The documented source-checkout example must finish through production confinement,
and its probe world must build and read back against current code."""
from pathlib import Path
from hashlib import sha256
import gzip
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


def test_phf19_probe_walks_the_gene_stage_contrast(certified_work):
    example = runpy.run_path(str(ASSETS / "demo.py"))
    sources = certified_work / "sources"
    sources.mkdir()
    matrix = sources / "GSE179929_gene_tpm.txt.gz"
    matrix.write_bytes(gzip.compress(
        b"gene\ta_NDMM\tb_NDMM\tc_NDMM\td_PD\te_PD\tf_PD\n"
        b"ENSG00000119403\t1\t2\t3\t1\t2\t3\n"
    ))
    paths = {"matrix": matrix}
    for name in ("crosswalk", "dataset", "proposition", "hgnc", "ensembl"):
        paths[name] = sources / f"{name}.txt"
        paths[name].write_text(f"Synthetic {name} provenance\n")
    pins = {name: sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}
    root = certified_work / 'PHF19 "probe" \\test\x7f'
    with pytest.raises(ValueError, match="matrix.*digest"):
        example["create_phf19"](root, paths)
    assert not root.exists()
    world = example["create_phf19"](root, paths, input_digests=pins)
    before = example["readback"](world.config)
    assert not before["propositions"] and not before["runs"]
    counts = before["records"]["by_kind"]
    assert counts["procedure"] == 2 and counts["classification-rule"] == 1
    assert counts["referent-mapping"] == 1 and counts["assumptions-register"] == 3
    reason = host_prerequisites()
    if reason is not None:
        pytest.skip(f"confinement unavailable: {reason}")
    cfg, proposition = example["walk"](world)
    assert proposition == "proposition:phf19-rna-pd-vs-ndmm"
    found = example["readback"](world.config)
    assert found["propositions"] == [{
        "id": proposition,
        "claim_identity": "3d6ded48093271ce7985d8debf9bded3aa87a7aa449523c10fe57fa4a7f062ae",
    }]
    (spec,) = found["specs"]
    assert '"functional":"general/probability-of-superiority"' in spec["estimand"]
    assert '"term":"level:ndmm"},{"sort":"mm30/stage-level","term":"level:pd"' in spec["estimand"]
    assert len(found["runs"]) == 2
    (assessment,) = found["assessments"]
    assert assessment["outcome"] == "inconclusive"
    (checked,) = found["verifications"]
    assert (checked["scope"], checked["verdict"]) == ("clean-environment", "passed")
    key, = ReadContext.open(cfg).claim_view(proposition).beliefs
    assert ReadContext.open(cfg).evaluate(proposition, key=key).reason == "no-directional-outcome"


def test_preparation_closes_writer_and_leaves_one_ready_action(certified_work):
    example = runpy.run_path(str(ASSETS / "demo.py"))
    world = example["create"](certified_work / "demo")
    action = example["prepare"](world)
    cfg = example["load_config"](world.config)
    assert classify(ReadContext.open(cfg), action["proposition"]) == "ready"
    assert action["workflow"]["targets"] == list(world.targets)
    assert action["workflow"]["tree_digest"].startswith("sha256-tree:")
    found = example["readback"](world.config)
    assert not found["runs"] and not found["assessments"] and not found["verifications"]
