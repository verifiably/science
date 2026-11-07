import pytest

from science.refusal import Refused
from helpers.snapshot import snapshot
from helpers.world import (
    OBSERVED, SPEC_FIELDS, build_belief_world, build_verify_rig_world, fixture_bundle, hold_fixture_dataset,
    mint_fixture_run, open_rig,
)


@pytest.fixture
def rig(certified_worker_work, monkeypatch):
    import science.commands.run as run_module
    from beliefs.confinement import host_prerequisites
    from beliefs.recipe import MINIMAL_POLICY
    snap = snapshot(certified_worker_work, "verify-rig", build_verify_rig_world)
    snap.restore()
    if host_prerequisites() is not None:
        monkeypatch.setattr(run_module, "POLICY", MINIMAL_POLICY)
    cfg, assessment_ref, bundle = snap.value
    with open_rig(cfg, ("spec", "assess", "verify")) as (d, ctx):
        yield d, ctx, assessment_ref, bundle


def test_verify_mints_a_verification_naming_the_assessment_and_both_runs(rig):
    d, ctx, assessment_ref, (code, entrypoint, _) = rig
    out = d.invoke("verify", {"assessment": assessment_ref, "code": str(code), "entrypoint": entrypoint})
    assert "[verification] verification:" in out.text
    view = ctx.write_view()
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


def test_a_recipe_changed_between_run_and_replay_is_refused(rig, certified_work):
    """The bundle's outcome file is rewritten between run and replay: a changed
    bundle changes the recipe identity, so the boundary refuses the replay as a
    different recipe, never a silently different result."""
    d, ctx, assessment_ref, (code, entrypoint, _) = rig
    (code / "workflow" / "Snakefile").write_text((code / "workflow" / "Snakefile").read_text().replace("supported", "refuted"))
    with pytest.raises(Refused) as caught:
        d.invoke("verify", {"assessment": assessment_ref, "code": str(code), "entrypoint": entrypoint})
    # A changed bundle changes the recipe identity: the boundary refuses the
    # replay as a different recipe, never a silently different result.
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data["kind"] == "RunRefused"


def test_a_disagreeing_replay_under_one_recipe_yields_failed_and_still_mints(certified_work):
    """One recipe whose stats.tsv differs on every execution: the replay
    disagrees, the equivalence rule answers failed, and the verification is a
    record either way."""
    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"x\n", "expression", **OBSERVED)
    bundle = fixture_bundle(certified_work, "supported", varying=True)
    with open_rig(cfg, ("spec", "assess", "verify")) as (d, ctx):
        spec_ref = next(t for t in d.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=ref)).text.split()
                        if t.startswith("analysis-spec:"))
        run_ref = mint_fixture_run(cfg, spec_ref, ref, bundle)
        assessment_ref = next(t for t in d.invoke("assess", {"run": run_ref}).text.split() if t.startswith("assessment:"))
        code, entrypoint, _ = bundle
        out = d.invoke("verify", {"assessment": assessment_ref, "code": str(code), "entrypoint": entrypoint})
        assert "[verification] verification:" in out.text
        view = ctx.write_view()
        (node,) = [n for n in view.iter_stored() if n.kind == "verification"]
        assert node.facets["verification"]["verdict"] == "failed"
        assert sum(1 for n in view.iter_stored() if n.kind == "run") == 2


def test_verify_refuses_before_the_replay_when_the_equivalence_implementation_changed(rig, monkeypatch):
    """The original run bound the equivalence rule to one implementation; if the
    rule now resolves to another, build_verification would raise RuleUnbound
    after the replay act. The handler refuses before it."""
    import science.commands.verify as verify_module
    from beliefs.replay import EquivalenceImplementation
    from beliefs.rules import CONTENT_IDENTITY_RULE, REFERENCE_RULES
    d, ctx, assessment_ref, (code, entrypoint, _) = rig
    current = REFERENCE_RULES[CONTENT_IDENTITY_RULE]
    swapped = dict(REFERENCE_RULES)
    swapped[CONTENT_IDENTITY_RULE] = EquivalenceImplementation("impl-eq-other", current.evaluate, current.fixtures)
    monkeypatch.setattr(verify_module, "REFERENCE_RULES", swapped)
    with pytest.raises(Refused) as first:
        d.invoke("verify", {"assessment": assessment_ref, "code": str(code), "entrypoint": entrypoint},
                 invocation_id="V" * 8)
    with pytest.raises(Refused) as again:
        d.invoke("verify", {"assessment": assessment_ref, "code": str(code), "entrypoint": entrypoint},
                 invocation_id="V" * 8)
    assert first.value.refusal.code == "invalid-input"
    assert "impl-eq-other" in first.value.refusal.message
    assert again.value.refusal == first.value.refusal
    view = ctx.write_view()
    assert sum(1 for n in view.iter_stored() if n.kind == "run") == 1  # no replay was minted


def test_verify_preparation_consumes_inherited_inputs(rig, monkeypatch):
    from dataclasses import replace
    from beliefs.root import init_store_root
    from helpers.world import FIXTURE_AUTHORITY
    from science.config import ReadContext
    import science.commands.verify as verify_module
    _, ctx, assessment_ref, (code, entrypoint, _) = rig
    inherited = ctx.config.store_root
    fresh = inherited.with_name("fresh")
    init_store_root(fresh, authority=FIXTURE_AUTHORITY)
    cfg = replace(ctx.config, store_root=fresh, read_store_roots=(inherited,))
    real_prepare = verify_module.prepare
    class Prepared(Exception):
        pass
    def stop_after_prepare(*args, **kwargs):
        prepared = real_prepare(*args, **kwargs)
        assert prepared["held_inputs"]
        assert all(
            path.is_relative_to(inherited)
            for mapping in prepared["held_inputs"].values()
            for path in mapping.values()
        )
        raise Prepared
    monkeypatch.setattr(verify_module, "prepare", stop_after_prepare)
    with pytest.raises(Prepared):
        verify_module.handle(ReadContext.open(cfg), None, assessment=assessment_ref,
                             code=str(code), entrypoint=entrypoint)


def _forbid_engines(monkeypatch):
    from beliefs import boundary as boundary_module

    def _never_engine(*args, **kwargs):
        raise AssertionError("engine must not launch when staged input digest check refuses")

    monkeypatch.setattr(boundary_module, "run_engine", _never_engine)
    monkeypatch.setattr(boundary_module, "launch_confined", _never_engine)


def test_verify_refuses_corrupted_store_bytes_before_execution_and_closes_invocation(rig, monkeypatch):
    from beliefs import stored

    d, ctx, assessment_ref, (code, entrypoint, _) = rig
    assessment = stored.assessment_value(ctx.write_view().get(assessment_ref), profile=ctx.config.profile)
    spec_ref = stored.typed_ref("analysis-spec", assessment.spec)
    (role,) = stored.analysis_spec_value(ctx.write_view().get(spec_ref), profile=ctx.config.profile).input_roles
    ctx.held_path(role.dataset).write_bytes(b"corrupted-after-run\n")
    _forbid_engines(monkeypatch)

    with pytest.raises(Refused) as caught:
        d.invoke("verify", {"assessment": assessment_ref, "code": str(code), "entrypoint": entrypoint},
                 invocation_id="D" * 8)
    assert caught.value.refusal.code == "kernel-refused"
    assert "does not match expected" in caught.value.refusal.data["reason"]
    view = ctx.write_view()
    assert sum(1 for n in view.iter_stored() if n.kind == "run") == 1
    assert not any(n.kind == "verification" for n in view.iter_stored())

    with pytest.raises(Refused) as again:
        d.invoke("verify", {"assessment": assessment_ref, "code": str(code), "entrypoint": entrypoint},
                 invocation_id="D" * 8)
    assert again.value.refusal == caught.value.refusal


def test_verify_refuses_when_run_closure_recorded_corrupted_digest_and_holding_is_restored(
    certified_work, monkeypatch
):
    from science.config import ReadContext

    cfg = build_belief_world(certified_work)
    ref = hold_fixture_dataset(cfg, "data.txt", b"declared\n", "expression", **OBSERVED)
    bundle = fixture_bundle(certified_work, "supported")
    held_file = ReadContext.open(cfg).held_path(ref)

    with open_rig(cfg, ("spec", "assess", "verify")) as (d, ctx):
        spec_ref = next(
            t for t in d.invoke("spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=ref)).text.split()
            if t.startswith("analysis-spec:")
        )
        held_file.write_bytes(b"corrupted\n")
        run_ref = mint_fixture_run(cfg, spec_ref, ref, bundle, expected_inputs=None)
        assessment_ref = next(
            t for t in d.invoke("assess", {"run": run_ref}).text.split()
            if t.startswith("assessment:")
        )
        held_file.write_bytes(b"declared\n")

        _forbid_engines(monkeypatch)
        code, entrypoint, _ = bundle
        with pytest.raises(Refused) as caught:
            d.invoke("verify", {"assessment": assessment_ref, "code": str(code), "entrypoint": entrypoint})
        assert caught.value.refusal.code == "kernel-refused"
        assert "does not match recipe input" in caught.value.refusal.data["reason"]
        view = ctx.write_view()
        assert sum(1 for n in view.iter_stored() if n.kind == "run") == 1
        assert not any(n.kind == "verification" for n in view.iter_stored())


def test_verify_refuses_colliding_multi_input_spec_cleanly_as_invalid_input(rig):
    from beliefs import stored
    from beliefs.root import open_corpus
    from beliefs.rules import REFERENCE_RULES
    from beliefs.spec import Deterministic, SpecDraft, SpecInput, freeze
    from helpers.world import FIXTURE_AUTHORITY

    d, ctx, assessment_ref, (code, entrypoint, _) = rig
    view = ctx.write_view()
    existing_assessment = stored.assessment_value(view.get(assessment_ref), profile=ctx.config.profile)
    existing_spec = stored.analysis_spec_value(
        view.get(stored.typed_ref("analysis-spec", existing_assessment.spec)),
        profile=ctx.config.profile,
    )
    other_ref = hold_fixture_dataset(ctx.config, "data.txt", b"colliding\n", "colliding")
    two_role_spec = freeze(
        SpecDraft(
            target=existing_spec.target,
            estimand=existing_spec.estimand,
            method=existing_spec.method,
            assumptions=existing_spec.assumptions,
            falsification=existing_spec.falsification,
            input_roles=(
                existing_spec.input_roles[0],
                SpecInput(role="reads", dataset=other_ref),
            ),
            applicability=existing_spec.applicability,
            interpretation_rule=existing_spec.interpretation_rule,
            equivalence_rule=existing_spec.equivalence_rule,
            parameters=existing_spec.parameters,
            nondeterminism=Deterministic(),
        ),
        held_rules=REFERENCE_RULES,
    )
    writer = open_corpus(ctx.config.write_root, authority=FIXTURE_AUTHORITY, profile=ctx.config.profile)
    writer.add(stored.analysis_spec_node(two_role_spec))
    synthetic_assessment = writer.add(stored.assessment_node(
        "multiinput000001",
        title="synthetic multi-input assessment",
        spec=two_role_spec.identity,
        run=stored.typed_ref("run", existing_assessment.run),
        proposition=existing_assessment.proposition,
        outcome=existing_assessment.outcome,
        interpretation_rule=existing_assessment.interpretation_rule,
        estimand=existing_assessment.estimand,
        applicability=existing_assessment.applicability,
    )).id

    with pytest.raises(Refused) as caught:
        d.invoke("verify", {"assessment": synthetic_assessment, "code": str(code), "entrypoint": entrypoint})
    assert caught.value.refusal.code == "invalid-input"
    assert "collision" in caught.value.refusal.message


def test_verify_run_replays_production_run_and_mints_verification(certified_work, tmp_path):
    from beliefs import stored

    cfg = build_belief_world(certified_work)
    with open_rig(cfg, ("dataset", "derive", "verify")) as (d, ctx):
        # 1. Multi-resource derive run
        raw_dir = tmp_path / "raw_multi"
        (raw_dir / "raw").mkdir(parents=True)
        (raw_dir / "raw" / "series_matrix.txt").write_bytes(b"PHF19\t4.2\n")
        (raw_dir / "raw" / "probe_map.tsv").write_bytes(b"p1\tPHF19\n")
        raw_id = next(
            t for t in d.invoke("dataset", {"path": str(raw_dir), "title": "raw multi"}).text.split()
            if t.startswith("dataset:")
        )

        code_multi = certified_work / "derive_multi_verify"
        (code_multi / "workflow").mkdir(parents=True, exist_ok=True)
        (code_multi / "workflow" / "Snakefile").write_text(
            'rule build_pkg:\n'
            '    input: "inputs/raw/series_matrix.txt", "inputs/raw/probe_map.tsv"\n'
            '    output: "tables/expression.tsv", "tables/clinical.tsv"\n'
            '    run:\n'
            '        import pathlib\n'
            '        m = pathlib.Path(input[0]).read_text()\n'
            '        p = pathlib.Path(input[1]).read_text()\n'
            '        pathlib.Path(output[0]).parent.mkdir(parents=True, exist_ok=True)\n'
            '        pathlib.Path(output[0]).write_text(m)\n'
            '        pathlib.Path(output[1]).write_text(p)\n'
        )
        derive_out = d.invoke(
            "derive",
            {
                "dataset": raw_id,
                "code": str(code_multi),
                "entrypoint": "derive_multi_verify/workflow/Snakefile",
                "targets": ["tables/expression.tsv", "tables/clinical.tsv"],
                "title": "curated multi",
            },
        )
        derive_run_id = next(t for t in derive_out.text.split() if t.startswith("run:"))

        verify_out = d.invoke(
            "verify",
            {
                "run": derive_run_id,
                "code": str(code_multi),
                "entrypoint": "derive_multi_verify/workflow/Snakefile",
            },
        )
        assert "[verification] verification:" in verify_out.text
        verify_ref = next(t for t in verify_out.text.split() if t.startswith("verification:"))
        view = ctx.write_view()
        node = view.get(verify_ref)
        facet = node.facets["verification"]
        assert facet["verdict"] == "passed"
        assert facet["scope"] == "clean-environment"
        orig_ref, replayed_ref = stored.verification_derivation(node)
        assert orig_ref == derive_run_id
        assert replayed_ref != derive_run_id
        assert view.holds(replayed_ref)

        # 2. Single-resource nested-member derive run
        nested_dir = tmp_path / "raw_nested"
        (nested_dir / "tables").mkdir(parents=True)
        (nested_dir / "tables" / "raw_clinical.tsv").write_bytes(b"patient\tage\nP1\t62\n")
        nested_id = next(
            t for t in d.invoke("dataset", {"path": str(nested_dir), "title": "raw nested"}).text.split()
            if t.startswith("dataset:")
        )

        code_nested = certified_work / "derive_nested_verify"
        (code_nested / "workflow").mkdir(parents=True, exist_ok=True)
        (code_nested / "workflow" / "Snakefile").write_text(
            'rule clean_nested:\n'
            '    input: "inputs/tables/raw_clinical.tsv"\n'
            '    output: "tables/clinical.tsv"\n'
            '    run:\n'
            '        import pathlib\n'
            '        t = pathlib.Path(input[0]).read_text()\n'
            '        pathlib.Path(output[0]).parent.mkdir(parents=True, exist_ok=True)\n'
            '        pathlib.Path(output[0]).write_text(t)\n'
        )
        derive_nested_out = d.invoke(
            "derive",
            {
                "dataset": nested_id,
                "code": str(code_nested),
                "entrypoint": "derive_nested_verify/workflow/Snakefile",
                "targets": ["tables/clinical.tsv"],
                "title": "curated nested",
            },
        )
        derive_nested_run_id = next(t for t in derive_nested_out.text.split() if t.startswith("run:"))

        verify_nested_out = d.invoke(
            "verify",
            {
                "run": derive_nested_run_id,
                "code": str(code_nested),
                "entrypoint": "derive_nested_verify/workflow/Snakefile",
            },
        )
        verify_nested_ref = next(t for t in verify_nested_out.text.split() if t.startswith("verification:"))
        view = ctx.write_view()
        nested_node = view.get(verify_nested_ref)
        assert nested_node.facets["verification"]["verdict"] == "passed"
        assert nested_node.facets["verification"]["scope"] == "clean-environment"
        orig_nested, replayed_nested = stored.verification_derivation(nested_node)
        assert orig_nested == derive_nested_run_id
        assert replayed_nested != derive_nested_run_id


def test_verify_refuses_when_both_or_neither_assessment_and_run_are_given(rig):
    from beliefs import stored

    d, ctx, assessment_ref, (code, entrypoint, _) = rig
    view = ctx.write_view()
    existing_assessment = stored.assessment_value(view.get(assessment_ref), profile=ctx.config.profile)
    assessment_run_ref = stored.typed_ref("run", existing_assessment.run)
    runs_before = sum(1 for n in view.iter_stored() if n.kind == "run")

    # 1. Neither --assessment nor --run
    with pytest.raises(Refused) as caught_neither:
        d.invoke("verify", {"code": str(code), "entrypoint": entrypoint})
    assert caught_neither.value.refusal.code == "invalid-input"

    # 2. Both --assessment and --run
    with pytest.raises(Refused) as caught_both:
        d.invoke(
            "verify",
            {"assessment": assessment_ref, "run": assessment_run_ref, "code": str(code), "entrypoint": entrypoint},
        )
    assert caught_both.value.refusal.code == "invalid-input"

    # 3. Assessment run passed to --run
    with pytest.raises(Refused) as caught_shape:
        d.invoke("verify", {"run": assessment_run_ref, "code": str(code), "entrypoint": entrypoint})
    assert caught_shape.value.refusal.code == "invalid-input"
    assert "dataset-production" in caught_shape.value.refusal.message

    assert sum(1 for n in ctx.write_view().iter_stored() if n.kind == "run") == runs_before


def test_produced_package_assessment_remains_gated_until_beliefs_8ecbb5(certified_work, tmp_path):
    cfg = build_belief_world(certified_work)
    raw_file = tmp_path / "raw.tsv"
    raw_file.write_bytes(b"gene\tval\nPHF19\t1\n")

    derive_code = certified_work / "derive_for_assess"
    (derive_code / "workflow").mkdir(parents=True, exist_ok=True)
    (derive_code / "workflow" / "Snakefile").write_text(
        'rule produce:\n'
        '    input: "inputs/raw.tsv"\n'
        '    output: "data.txt"\n'
        '    run:\n'
        '        import pathlib\n'
        '        pathlib.Path(output[0]).write_text(pathlib.Path(input[0]).read_text() + "derived\\n")\n'
    )
    bundle = fixture_bundle(certified_work, "supported")
    code, entrypoint, targets = bundle

    with open_rig(cfg, ("dataset", "derive", "spec", "run", "assess")) as (d, ctx):
        raw_id = next(
            t for t in d.invoke(
                "dataset", {"path": str(raw_file), "title": "raw", "locator": "accession:GSE1"}
            ).text.split()
            if t.startswith("dataset:")
        )
        d.invoke(
            "derive",
            {
                "dataset": raw_id,
                "code": str(derive_code),
                "entrypoint": "derive_for_assess/workflow/Snakefile",
                "targets": ["data.txt"],
                "title": "derived package",
            },
        )
        derived_node = next(
            n for n in ctx.write_view().iter_stored() if n.kind == "dataset" and n.title == "derived package"
        )
        spec_ref = next(
            t for t in d.invoke(
                "spec", dict(SPEC_FIELDS, target="proposition:p1", dataset=derived_node.id)
            ).text.split()
            if t.startswith("analysis-spec:")
        )
        run_ref = next(
            t for t in d.invoke(
                "run",
                {
                    "spec": spec_ref,
                    "dataset": derived_node.id,
                    "code": str(code),
                    "entrypoint": entrypoint,
                    "targets": list(targets),
                },
            ).text.split()
            if t.startswith("run:")
        )
        with pytest.raises(Refused) as caught:
            d.invoke("assess", {"run": run_ref})
        assert caught.value.refusal.code == "kernel-refused"
        assert caught.value.refusal.data["kind"] == "EligibilityUnmet"
        assert "no-empirical-observation-facet" in caught.value.refusal.message


