from hashlib import sha256

import pytest

from beliefs import stored
from beliefs.audit import check_lineage_basis
from beliefs.runrecord import decode_run_closure
from helpers.world import build_belief_world, open_rig
from science.refusal import Refused


@pytest.fixture
def rig(certified_work, monkeypatch):
    from beliefs.confinement import host_prerequisites
    from beliefs.recipe import MINIMAL_POLICY

    cfg = build_belief_world(certified_work)
    with open_rig(cfg, ("dataset", "derive")) as (d, ctx):
        if host_prerequisites() is not None:
            import science.commands.derive as derive_module

            monkeypatch.setattr(derive_module, "POLICY", MINIMAL_POLICY)
            monkeypatch.setattr(derive_module, "host_prerequisites", lambda: None)
        yield d, ctx


def _minted_ref(text: str, prefix: str) -> str:
    return next(t for t in text.split() if t.startswith(prefix))


def test_derive_produces_multi_resource_package_and_mints_run_and_dataset(rig, certified_work, tmp_path):
    d, ctx = rig
    raw_dir = tmp_path / "raw_pkg"
    (raw_dir / "raw").mkdir(parents=True)
    (raw_dir / "raw" / "series_matrix.txt").write_bytes(b"probe_1\t4.2\n")
    (raw_dir / "raw" / "probe_map.tsv").write_bytes(b"probe_1\tPHF19\n")

    raw_out = d.invoke(
        "dataset",
        {"path": str(raw_dir), "title": "GSE24080 raw", "locator": "accession:GSE24080"},
    )
    raw_id = _minted_ref(raw_out.text, "dataset:")

    code = certified_work / "derive_pkg"
    (code / "workflow").mkdir(parents=True, exist_ok=True)
    (code / "workflow" / "Snakefile").write_text(
        'rule curate:\n'
        '    input: "inputs/raw/series_matrix.txt", "inputs/raw/probe_map.tsv"\n'
        '    output: "tables/expression.tsv", "tables/clinical.tsv", "datapackage.json"\n'
        '    run:\n'
        '        import pathlib\n'
        '        matrix = pathlib.Path(input[0]).read_text().strip()\n'
        '        probes = pathlib.Path(input[1]).read_text().strip()\n'
        '        cohort = config.get("cohort", "UNKNOWN")\n'
        '        pathlib.Path(output[0]).parent.mkdir(parents=True, exist_ok=True)\n'
        '        pathlib.Path(output[0]).write_text(f"gene\\tval\\n{probes}\\t{matrix}\\n")\n'
        '        pathlib.Path(output[1]).write_text(f"patient\\tcohort\\nP1\\t{cohort}\\n")\n'
        '        pathlib.Path(output[2]).write_text(\'{"name": "gse24080-curated"}\\n\')\n'
    )

    targets = ["tables/expression.tsv", "tables/clinical.tsv", "datapackage.json"]
    out = d.invoke(
        "derive",
        {
            "dataset": raw_id,
            "code": str(code),
            "entrypoint": "derive_pkg/workflow/Snakefile",
            "targets": targets,
            "title": "GSE24080 curated package",
            "parameters": ["cohort=UAMS"],
        },
    )
    assert "[run] run:" in out.text
    run_id = _minted_ref(out.text, "run:")

    view = ctx.write_view()
    assert view.holds(run_id)
    dataset_node = next(
        n for n in view.iter_stored() if n.kind == "dataset" and n.title == "GSE24080 curated package"
    )
    assert dataset_node.id.startswith("dataset:sha256:")
    assert ctx.is_held(dataset_node)
    resolved = ctx.held_resources(dataset_node.id)
    assert set(resolved) == set(targets)
    assert b"UAMS" in resolved["tables/clinical.tsv"].read_bytes()
    assert stored.lineage_basis(dataset_node) == {
        "tag": "single",
        "routes": [{"run": run_id, "ancestor": raw_id, "transforms": [raw_id]}],
    }


def test_derive_preserves_nested_member_path_for_single_resource_input(rig, certified_work, tmp_path):
    d, ctx = rig
    raw_dir = tmp_path / "single_nested"
    (raw_dir / "tables").mkdir(parents=True)
    raw_bytes = b"patient\tage\nP1\t62\n"
    (raw_dir / "tables" / "raw_clinical.tsv").write_bytes(raw_bytes)

    raw_out = d.invoke(
        "dataset",
        {"path": str(raw_dir), "title": "nested single", "locator": "accession:GSE24080"},
    )
    raw_id = _minted_ref(raw_out.text, "dataset:")

    code = certified_work / "derive_nested"
    (code / "workflow").mkdir(parents=True, exist_ok=True)
    (code / "workflow" / "Snakefile").write_text(
        'rule clean:\n'
        '    input: "inputs/tables/raw_clinical.tsv"\n'
        '    output: "tables/clinical.tsv"\n'
        '    run:\n'
        '        import pathlib\n'
        '        text = pathlib.Path(input[0]).read_text()\n'
        '        pathlib.Path(output[0]).parent.mkdir(parents=True, exist_ok=True)\n'
        '        pathlib.Path(output[0]).write_text(text + "P2\\t55\\n")\n'
    )

    out = d.invoke(
        "derive",
        {
            "dataset": raw_id,
            "code": str(code),
            "entrypoint": "derive_nested/workflow/Snakefile",
            "targets": ["tables/clinical.tsv"],
            "title": "cleaned single",
        },
    )
    run_id = _minted_ref(out.text, "run:")
    closure = decode_run_closure(ctx.write_view().get(run_id))
    (recipe_input,) = closure.recipe.inputs
    assert recipe_input.role == "transforms"
    assert recipe_input.dataset == raw_id
    assert recipe_input.content == "sha256:" + sha256(raw_bytes).hexdigest()


def test_derive_supports_reads_aux_datasets_and_r23_rebuild_passes_audit(rig, certified_work, tmp_path):
    d, ctx = rig
    raw_file = tmp_path / "raw_matrix.tsv"
    raw_file.write_bytes(b"gene\tval\nPHF19\t1\n")
    aux_file = tmp_path / "aux_panel.tsv"
    aux_file.write_bytes(b"gene\nPHF19\n")

    raw_id = _minted_ref(
        d.invoke("dataset", {"path": str(raw_file), "title": "raw matrix", "locator": "accession:GSE1"}).text,
        "dataset:",
    )
    aux_id = _minted_ref(
        d.invoke("dataset", {"path": str(aux_file), "title": "aux panel"}).text,
        "dataset:",
    )

    code = certified_work / "derive_aux"
    (code / "workflow").mkdir(parents=True, exist_ok=True)
    (code / "workflow" / "Snakefile").write_text(
        'rule filter_genes:\n'
        '    input: "inputs/raw_matrix.tsv", "inputs/aux_panel.tsv"\n'
        '    output: "tables/filtered.tsv"\n'
        '    run:\n'
        '        import pathlib\n'
        '        raw_text = pathlib.Path(input[0]).read_text()\n'
        '        aux_text = pathlib.Path(input[1]).read_text()\n'
        '        cohort = config.get("cohort", "")\n'
        '        pathlib.Path(output[0]).parent.mkdir(parents=True, exist_ok=True)\n'
        '        pathlib.Path(output[0]).write_text(raw_text + aux_text + cohort + "\\n")\n'
    )

    payload = {
        "dataset": raw_id,
        "reads": [aux_id],
        "code": str(code),
        "entrypoint": "derive_aux/workflow/Snakefile",
        "targets": ["tables/filtered.tsv"],
        "title": "filtered matrix",
        "parameters": ["cohort=UAMS"],
    }
    first_out = d.invoke("derive", payload)
    first_run_id = _minted_ref(first_out.text, "run:")

    second_out = d.invoke("derive", payload)
    second_run_id = _minted_ref(second_out.text, "run:")
    assert first_run_id != second_run_id

    view = ctx.write_view()
    assert view.holds(first_run_id)
    assert view.holds(second_run_id)
    (dataset_node,) = [n for n in view.iter_stored() if n.kind == "dataset" and n.title == "filtered matrix"]
    assert stored.lineage_basis(dataset_node) == {
        "tag": "single",
        "routes": [{"run": first_run_id, "ancestor": raw_id, "transforms": [raw_id]}],
    }
    result = check_lineage_basis(view, dataset_node)
    assert result.contradiction is None


def test_derive_refuses_duplicate_staged_paths_and_malformed_parameters_before_acting(
    rig, certified_work, tmp_path
):
    d, ctx = rig
    dir1 = tmp_path / "d1"
    dir2 = tmp_path / "d2"
    (dir1 / "shared").mkdir(parents=True)
    (dir2 / "shared").mkdir(parents=True)
    (dir1 / "shared" / "table.tsv").write_bytes(b"a\n")
    (dir2 / "shared" / "table.tsv").write_bytes(b"b\n")

    ds1 = _minted_ref(d.invoke("dataset", {"path": str(dir1), "title": "ds1"}).text, "dataset:")
    ds2 = _minted_ref(d.invoke("dataset", {"path": str(dir2), "title": "ds2"}).text, "dataset:")

    code = certified_work / "derive_refuse"
    (code / "workflow").mkdir(parents=True, exist_ok=True)
    (code / "workflow" / "Snakefile").write_text(
        'rule noop:\n'
        '    output: "out.tsv"\n'
        '    run:\n'
        '        import pathlib\n'
        '        pathlib.Path(output[0]).write_text("ok\\n")\n'
    )

    before_nodes = {n.id for n in ctx.write_view().iter_stored()}
    base_args = {
        "dataset": ds1,
        "code": str(code),
        "entrypoint": "derive_refuse/workflow/Snakefile",
        "targets": ["out.tsv"],
        "title": "should refuse",
    }

    # 1. Duplicate relative resource names across transforms and reads
    with pytest.raises(Refused) as caught:
        d.invoke("derive", {**base_args, "reads": [ds2]})
    assert caught.value.refusal.code == "invalid-input"

    # 2. Duplicate dataset ref across --dataset and --reads
    with pytest.raises(Refused) as caught:
        d.invoke("derive", {**base_args, "reads": [ds1]})
    assert caught.value.refusal.code == "invalid-input"

    # 3. Malformed --parameters (no_equals, =val, duplicate key, reserved key)
    for bad_params in (["no_equals"], ["=val"], ["k=1", "k=2"], ["seed_roots=x"]):
        with pytest.raises(Refused) as caught:
            d.invoke("derive", {**base_args, "parameters": bad_params})
        assert caught.value.refusal.code == "invalid-input"

    # 4. Invalid --targets
    for bad_targets in (["../escape.tsv"], ["out.tsv", "out.tsv"]):
        with pytest.raises(Refused) as caught:
            d.invoke("derive", {**base_args, "targets": bad_targets})
        assert caught.value.refusal.code == "invalid-input"

    assert {n.id for n in ctx.write_view().iter_stored()} == before_nodes


def test_derive_propagates_kernel_refusal_after_execution_begins_without_contract_violation(
    rig, certified_work, tmp_path
):
    d, ctx = rig
    raw_file = tmp_path / "raw.tsv"
    raw_file.write_bytes(b"x\n")
    raw_id = _minted_ref(d.invoke("dataset", {"path": str(raw_file), "title": "raw"}).text, "dataset:")

    code = certified_work / "derive_fail"
    (code / "workflow").mkdir(parents=True, exist_ok=True)
    (code / "workflow" / "Snakefile").write_text(
        'rule fail_exec:\n'
        '    input: "inputs/raw.tsv"\n'
        '    output: "out.tsv"\n'
        '    run:\n'
        '        import sys\n'
        '        sys.exit(1)\n'
    )

    payload = {
        "dataset": raw_id,
        "code": str(code),
        "entrypoint": "derive_fail/workflow/Snakefile",
        "targets": ["out.tsv"],
        "title": "failing derive",
    }
    with pytest.raises(Refused) as caught:
        d.invoke("derive", payload, invocation_id="F" * 8)
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data["kind"] == "RunRefused"
    assert caught.value.refusal.data["reason"] == "execution-failed"

    view = ctx.write_view()
    assert not any(n.kind == "dataset" and n.title == "failing derive" for n in view.iter_stored())
    assert sum(1 for n in view.iter_stored() if n.kind == "act-report") >= 1
