import pytest

from science.refusal import Refused
from helpers.world import SPEC_FIELDS, build_belief_world, fixture_bundle, hold_fixture_dataset, open_rig


@pytest.fixture
def rig(certified_work, monkeypatch):
    import science.commands.run as run_module
    from beliefs.recipe import MINIMAL_POLICY
    from beliefs.confinement import host_prerequisites
    if host_prerequisites() is not None:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
        monkeypatch.setattr(run_module, "host_prerequisites", lambda: None)
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression")
    with open_rig(cfg, ("spec", "run")) as (d, ctx):
        spec_out = d.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=ref))
        spec_ref = next(t for t in spec_out.text.split() if t.startswith("analysis-spec:"))
        yield d, ctx, spec_ref, ref


def test_run_mints_one_run_record(rig, certified_work):
    d, ctx, spec_ref, ref = rig
    code, entrypoint, targets = fixture_bundle(certified_work)
    out = d.invoke("run", {"spec": spec_ref, "dataset": ref, "code": str(code),
                           "entrypoint": entrypoint, "targets": list(targets)})
    assert "[run] run:" in out.text
    view = ctx.write_view()
    assert sum(1 for n in view.iter_stored() if n.kind == "run") == 1


def test_run_refuses_without_bubblewrap_before_any_act(certified_work, monkeypatch):
    import science.commands.run as run_module
    monkeypatch.setattr(run_module, "host_prerequisites", lambda: "bubblewrap (bwrap) is not on PATH")
    cfg = build_belief_world(certified_work)
    with open_rig(cfg, ("run",)) as (d, ctx):
        with pytest.raises(Refused) as caught:
            d.invoke("run", {"spec": "analysis-spec:" + "0" * 64, "dataset": "dataset:x", "code": "/nowhere",
                             "entrypoint": "e", "targets": ["t"]})
        assert "bubblewrap" in caught.value.refusal.message
        view = ctx.write_view()
        assert not any(n.kind == "run" for n in view.iter_stored())


def test_run_refuses_a_missing_code_directory(rig):
    d, _, spec_ref, ref = rig
    with pytest.raises(Refused) as caught:
        d.invoke("run", {"spec": spec_ref, "dataset": ref, "code": "/does/not/exist",
                         "entrypoint": "analysis/workflow/Snakefile", "targets": ["outputs/outcome.txt"]})
    assert caught.value.refusal.code == "invalid-input"


def test_kernel_run_refusal_is_the_refusal_envelope(rig, certified_work):
    """A wrong entrypoint reaches the boundary, which refuses with its reason;
    the invocation closes with that envelope."""
    d, _, spec_ref, ref = rig
    code, _, targets = fixture_bundle(certified_work)
    with pytest.raises(Refused) as caught:
        d.invoke("run", {"spec": spec_ref, "dataset": ref, "code": str(code),
                         "entrypoint": "analysis/workflow/Missing", "targets": list(targets)})
    assert caught.value.refusal.code == "invalid-input"  # prepare() refuses before the boundary


def test_boundary_refusal_is_kernel_refused_and_closes_the_invocation(rig, certified_work):
    """A definition the entrypoint does not embody reaches the boundary, which
    refuses; the dispatcher's kernel path renders it and closes the ledger."""
    d, _, spec_ref, ref = rig
    code, entrypoint, targets = fixture_bundle(certified_work)
    (code / "workflow" / "Snakefile").write_text("rule nothing:\n    output: 'outputs/other.txt'\n    shell: 'touch {output}'\n")
    with pytest.raises(Refused) as caught:
        d.invoke("run", {"spec": spec_ref, "dataset": ref, "code": str(code),
                         "entrypoint": entrypoint, "targets": list(targets)}, invocation_id="K" * 8)
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data["kind"] == "RunRefused"
    with pytest.raises(Refused) as again:  # the refusal replays from the ledger
        d.invoke("run", {"spec": spec_ref, "dataset": ref, "code": str(code),
                         "entrypoint": entrypoint, "targets": list(targets)}, invocation_id="K" * 8)
    assert again.value.refusal.code == "kernel-refused"


def test_run_preparation_consumes_inherited_inputs(rig, certified_work):
    from dataclasses import replace
    from beliefs.root import init_store_root
    from helpers.world import FIXTURE_AUTHORITY
    from science.config import ReadContext
    from science.commands.run import prepare
    _, ctx, spec_ref, ref = rig
    inherited = ctx.config.store_root
    fresh = certified_work / "fresh"
    init_store_root(fresh, authority=FIXTURE_AUTHORITY)
    cfg = replace(ctx.config, store_root=fresh, read_store_roots=(inherited,))
    code, entrypoint, targets = fixture_bundle(certified_work)
    prepared = prepare(ReadContext.open(cfg), spec_ref, ref, str(code), entrypoint, targets)
    assert prepared["held_inputs"][ref]["data.txt"].is_relative_to(inherited)
    assert prepared["held_inputs"][ref]["data.txt"].read_bytes() == b"x\n"


def _forbid_engines(monkeypatch):
    from beliefs import boundary as boundary_module

    def _never_engine(*args, **kwargs):
        raise AssertionError("engine must not launch when staged input digest check refuses")

    monkeypatch.setattr(boundary_module, "run_engine", _never_engine)
    monkeypatch.setattr(boundary_module, "launch_confined", _never_engine)


def test_run_refuses_corrupted_store_bytes_before_execution_and_closes_invocation(rig, certified_work, monkeypatch):
    d, ctx, spec_ref, ref = rig
    code, entrypoint, targets = fixture_bundle(certified_work)
    ctx.held_path(ref).write_bytes(b"corrupted\n")
    _forbid_engines(monkeypatch)

    with pytest.raises(Refused) as caught:
        d.invoke("run", {"spec": spec_ref, "dataset": ref, "code": str(code),
                         "entrypoint": entrypoint, "targets": list(targets)}, invocation_id="C" * 8)
    assert caught.value.refusal.code == "kernel-refused"
    assert "does not match expected" in caught.value.refusal.data["reason"]
    view = ctx.write_view()
    assert not any(n.kind == "run" for n in view.iter_stored())
    assert sum(1 for n in view.iter_stored() if n.kind == "act-report") >= 1

    with pytest.raises(Refused) as again:
        d.invoke("run", {"spec": spec_ref, "dataset": ref, "code": str(code),
                         "entrypoint": entrypoint, "targets": list(targets)}, invocation_id="C" * 8)
    assert again.value.refusal == caught.value.refusal


def test_run_checks_staged_bytes_when_source_mutates_during_copy(rig, certified_work, monkeypatch):
    import shutil as _shutil
    from pathlib import Path
    from beliefs import boundary as boundary_module

    d, ctx, spec_ref, ref = rig
    code, entrypoint, targets = fixture_bundle(certified_work)
    held_source = ctx.held_path(ref)
    real_copy2 = _shutil.copy2

    def corrupt_during_copy(src, dst, *args, **kwargs):
        result = real_copy2(src, dst, *args, **kwargs)
        if Path(src) == held_source:
            Path(dst).write_bytes(b"corrupted-in-flight\n")
        return result

    monkeypatch.setattr(boundary_module.shutil, "copy2", corrupt_during_copy)
    _forbid_engines(monkeypatch)
    with pytest.raises(Refused) as caught:
        d.invoke("run", {"spec": spec_ref, "dataset": ref, "code": str(code),
                         "entrypoint": entrypoint, "targets": list(targets)})
    assert held_source.read_bytes() == b"x\n"
    assert caught.value.refusal.code == "kernel-refused"
    assert "does not match expected" in caught.value.refusal.data["reason"]


def test_run_refuses_mismatched_observes_or_staged_path_collision_before_any_act(rig, certified_work):
    from beliefs import stored
    from beliefs.root import open_corpus
    from beliefs.rules import REFERENCE_RULES
    from beliefs.spec import Deterministic, SpecDraft, SpecInput, freeze
    from helpers.world import FIXTURE_AUTHORITY

    d, ctx, spec_ref, ref = rig
    code, entrypoint, targets = fixture_bundle(certified_work)
    writer = open_corpus(ctx.config.write_root, authority=FIXTURE_AUTHORITY, profile=ctx.config.profile)
    existing_spec = stored.analysis_spec_value(ctx.write_view().get(spec_ref), profile=ctx.config.profile)
    act_reports_before = sum(1 for n in ctx.write_view().iter_stored() if n.kind == "act-report")

    other_ref = hold_fixture_dataset(ctx.config, "aux.txt", b"aux\n", "auxiliary")
    with pytest.raises(Refused) as caught_mismatch:
        d.invoke("run", {"spec": spec_ref, "dataset": other_ref, "code": str(code),
                         "entrypoint": entrypoint, "targets": list(targets)})
    assert caught_mismatch.value.refusal.code == "invalid-input"
    assert sum(1 for n in ctx.write_view().iter_stored() if n.kind == "act-report") == act_reports_before

    colliding_ref = hold_fixture_dataset(ctx.config, "data.txt", b"colliding\n", "colliding")
    colliding_spec = freeze(
        SpecDraft(
            target=existing_spec.target,
            estimand=existing_spec.estimand,
            method=existing_spec.method,
            assumptions=existing_spec.assumptions,
            falsification=existing_spec.falsification,
            input_roles=(
                SpecInput(role="observes", dataset=ref),
                SpecInput(role="reads", dataset=colliding_ref),
            ),
            applicability=existing_spec.applicability,
            interpretation_rule=existing_spec.interpretation_rule,
            equivalence_rule=existing_spec.equivalence_rule,
            parameters=existing_spec.parameters,
            nondeterminism=Deterministic(),
        ),
        held_rules=REFERENCE_RULES,
    )
    colliding_spec_ref = writer.add(stored.analysis_spec_node(colliding_spec)).id

    with pytest.raises(Refused) as caught_col:
        d.invoke("run", {"spec": colliding_spec_ref, "dataset": ref, "code": str(code),
                         "entrypoint": entrypoint, "targets": list(targets)})
    assert caught_col.value.refusal.code == "invalid-input"
    assert "collision" in caught_col.value.refusal.message
    assert sum(1 for n in ctx.write_view().iter_stored() if n.kind == "act-report") == act_reports_before


def test_run_executes_spec_over_multi_resource_package(certified_work, tmp_path, monkeypatch):
    import science.commands.run as run_module
    from beliefs.confinement import host_prerequisites
    from beliefs.recipe import MINIMAL_POLICY

    if host_prerequisites() is not None:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
        monkeypatch.setattr(run_module, "host_prerequisites", lambda: None)

    cfg = build_belief_world(certified_work)
    pkg_dir = tmp_path / "pkg"
    (pkg_dir / "tables").mkdir(parents=True)
    (pkg_dir / "tables" / "expression.tsv").write_bytes(b"gene\tval\nPHF19\t4.2\n")
    (pkg_dir / "tables" / "clinical.tsv").write_bytes(b"patient\tage\nP1\t62\n")
    (pkg_dir / "datapackage.json").write_bytes(b'{"name": "gse24080"}\n')

    code = certified_work / "pkg_analysis"
    (code / "workflow").mkdir(parents=True, exist_ok=True)
    (code / "workflow" / "Snakefile").write_text(
        'rule analyze:\n'
        '    input: "inputs/tables/expression.tsv", "inputs/tables/clinical.tsv"\n'
        '    output: "outputs/stats.tsv", "outputs/outcome.txt"\n'
        '    run:\n'
        '        import pathlib\n'
        '        expr = pathlib.Path(input[0]).read_text()\n'
        '        clin = pathlib.Path(input[1]).read_text()\n'
        '        assert "PHF19" in expr and "P1" in clin\n'
        '        pathlib.Path(output[0]).parent.mkdir(parents=True, exist_ok=True)\n'
        '        pathlib.Path(output[0]).write_text("n\\t1\\n")\n'
        '        pathlib.Path(output[1]).write_text("supported\\n")\n'
    )

    with open_rig(cfg, ("dataset", "spec", "run", "assess", "verify")) as (d, ctx):
        ds_out = d.invoke(
            "dataset",
            {"path": str(pkg_dir), "title": "GSE24080 package", "locator": "accession:GSE24080"},
        )
        ds_ref = next(t for t in ds_out.text.split() if t.startswith("dataset:"))
        spec_out = d.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=ds_ref))
        spec_ref = next(t for t in spec_out.text.split() if t.startswith("analysis-spec:"))

        run_out = d.invoke(
            "run",
            {
                "spec": spec_ref,
                "dataset": ds_ref,
                "code": str(code),
                "entrypoint": "pkg_analysis/workflow/Snakefile",
                "targets": ["outputs/stats.tsv", "outputs/outcome.txt"],
            },
        )
        assert "[run] run:" in run_out.text
        run_ref = next(t for t in run_out.text.split() if t.startswith("run:"))

        assess_out = d.invoke("assess", {"run": run_ref})
        assessment_ref = next(t for t in assess_out.text.split() if t.startswith("assessment:"))

        verify_out = d.invoke(
            "verify",
            {
                "assessment": assessment_ref,
                "code": str(code),
                "entrypoint": "pkg_analysis/workflow/Snakefile",
            },
        )
        assert "[verification] verification:" in verify_out.text


def test_run_preserves_nested_member_path_for_single_resource_package(certified_work, tmp_path, monkeypatch):
    from hashlib import sha256
    import science.commands.run as run_module
    from beliefs.confinement import host_prerequisites
    from beliefs.recipe import MINIMAL_POLICY
    from beliefs.runrecord import decode_run_closure

    if host_prerequisites() is not None:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
        monkeypatch.setattr(run_module, "host_prerequisites", lambda: None)

    cfg = build_belief_world(certified_work)
    pkg_dir = tmp_path / "single_pkg"
    (pkg_dir / "tables").mkdir(parents=True)
    clin_bytes = b"patient\tage\nP1\t62\n"
    (pkg_dir / "tables" / "clinical.tsv").write_bytes(clin_bytes)

    code = certified_work / "single_nested_analysis"
    (code / "workflow").mkdir(parents=True, exist_ok=True)
    (code / "workflow" / "Snakefile").write_text(
        'rule analyze:\n'
        '    input: "inputs/tables/clinical.tsv"\n'
        '    output: "outputs/stats.tsv", "outputs/outcome.txt"\n'
        '    run:\n'
        '        import pathlib\n'
        '        clin = pathlib.Path(input[0]).read_text()\n'
        '        assert "P1" in clin\n'
        '        pathlib.Path(output[0]).parent.mkdir(parents=True, exist_ok=True)\n'
        '        pathlib.Path(output[0]).write_text("n\\t1\\n")\n'
        '        pathlib.Path(output[1]).write_text("supported\\n")\n'
    )

    with open_rig(cfg, ("dataset", "spec", "run")) as (d, ctx):
        ds_out = d.invoke(
            "dataset",
            {"path": str(pkg_dir), "title": "nested single", "locator": "accession:GSE24080"},
        )
        ds_ref = next(t for t in ds_out.text.split() if t.startswith("dataset:"))
        spec_out = d.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=ds_ref))
        spec_ref = next(t for t in spec_out.text.split() if t.startswith("analysis-spec:"))

        run_out = d.invoke(
            "run",
            {
                "spec": spec_ref,
                "dataset": ds_ref,
                "code": str(code),
                "entrypoint": "single_nested_analysis/workflow/Snakefile",
                "targets": ["outputs/stats.tsv", "outputs/outcome.txt"],
            },
        )
        run_ref = next(t for t in run_out.text.split() if t.startswith("run:"))
        closure = decode_run_closure(ctx.write_view().get(run_ref))
        (recipe_input,) = closure.recipe.inputs
        assert recipe_input.dataset == ds_ref
        assert recipe_input.content == "sha256:" + sha256(clin_bytes).hexdigest()


def test_run_stages_reads_roles_on_multi_role_spec(certified_work, monkeypatch):
    import science.commands.run as run_module
    from beliefs import stored
    from beliefs.confinement import host_prerequisites
    from beliefs.recipe import MINIMAL_POLICY
    from beliefs.root import open_corpus
    from beliefs.rules import REFERENCE_RULES
    from beliefs.spec import Deterministic, SpecDraft, SpecInput, freeze
    from helpers.world import FIXTURE_AUTHORITY, OBSERVED

    if host_prerequisites() is not None:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
        monkeypatch.setattr(run_module, "host_prerequisites", lambda: None)

    cfg = build_belief_world(certified_work)
    obs_ref = hold_fixture_dataset(cfg, "obs.tsv", b"gene\tval\nPHF19\t1\n", "observed", **OBSERVED)
    aux_ref = hold_fixture_dataset(cfg, "aux.tsv", b"gene\nPHF19\n", "aux")

    code = certified_work / "multi_role_analysis"
    (code / "workflow").mkdir(parents=True, exist_ok=True)
    (code / "workflow" / "Snakefile").write_text(
        'rule analyze_both:\n'
        '    input: "inputs/obs.tsv", "inputs/aux.tsv"\n'
        '    output: "outputs/stats.tsv", "outputs/outcome.txt"\n'
        '    run:\n'
        '        import pathlib\n'
        '        obs_text = pathlib.Path(input[0]).read_text()\n'
        '        aux_text = pathlib.Path(input[1]).read_text()\n'
        '        assert "PHF19" in obs_text and "PHF19" in aux_text\n'
        '        pathlib.Path(output[0]).parent.mkdir(parents=True, exist_ok=True)\n'
        '        pathlib.Path(output[0]).write_text("n\\t1\\n")\n'
        '        pathlib.Path(output[1]).write_text("supported\\n")\n'
    )

    with open_rig(cfg, ("spec", "run", "assess", "verify")) as (d, ctx):
        base_spec_out = d.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=obs_ref))
        base_spec_ref = next(t for t in base_spec_out.text.split() if t.startswith("analysis-spec:"))
        existing_spec = stored.analysis_spec_value(ctx.write_view().get(base_spec_ref), profile=cfg.profile)
        multi_role_spec = freeze(
            SpecDraft(
                target=existing_spec.target,
                estimand=existing_spec.estimand,
                method=existing_spec.method,
                assumptions=existing_spec.assumptions,
                falsification=existing_spec.falsification,
                input_roles=(
                    SpecInput(role="observes", dataset=obs_ref),
                    SpecInput(role="reads", dataset=aux_ref),
                ),
                applicability=existing_spec.applicability,
                interpretation_rule=existing_spec.interpretation_rule,
                equivalence_rule=existing_spec.equivalence_rule,
                parameters=existing_spec.parameters,
                nondeterminism=Deterministic(),
            ),
            held_rules=REFERENCE_RULES,
        )
        writer = open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile)
        spec_ref = writer.add(stored.analysis_spec_node(multi_role_spec)).id

        run_out = d.invoke(
            "run",
            {
                "spec": spec_ref,
                "dataset": obs_ref,
                "code": str(code),
                "entrypoint": "multi_role_analysis/workflow/Snakefile",
                "targets": ["outputs/stats.tsv", "outputs/outcome.txt"],
            },
        )
        run_ref = next(t for t in run_out.text.split() if t.startswith("run:"))
        assess_out = d.invoke("assess", {"run": run_ref})
        assessment_ref = next(t for t in assess_out.text.split() if t.startswith("assessment:"))
        verify_out = d.invoke(
            "verify",
            {
                "assessment": assessment_ref,
                "code": str(code),
                "entrypoint": "multi_role_analysis/workflow/Snakefile",
            },
        )
        assert "[verification] verification:" in verify_out.text


