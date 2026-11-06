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
    assert prepared["held_inputs"][ref].is_relative_to(inherited)
    assert prepared["held_inputs"][ref].read_bytes() == b"x\n"


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


def test_run_refuses_multi_resource_dataset_or_multi_dataset_spec_before_any_act(rig, certified_work):
    from hashlib import sha256
    from beliefs import stored
    from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
    from beliefs.root import open_corpus
    from beliefs.rules import REFERENCE_RULES
    from beliefs.spec import Deterministic, SpecDraft, SpecInput, freeze
    from helpers.world import FIXTURE_AUTHORITY

    d, ctx, spec_ref, ref = rig
    code, entrypoint, targets = fixture_bundle(certified_work)
    writer = open_corpus(ctx.config.write_root, authority=FIXTURE_AUTHORITY, profile=ctx.config.profile)
    existing_spec = stored.analysis_spec_value(ctx.write_view().get(spec_ref), profile=ctx.config.profile)
    act_reports_before = sum(1 for n in ctx.write_view().iter_stored() if n.kind == "act-report")

    d1 = "sha256:" + sha256(b"a\n").hexdigest()
    d2 = "sha256:" + sha256(b"b\n").hexdigest()
    multi_decl = DatasetDeclaration(resources=(
        ResourceDeclaration(name="a.txt", digest=d1),
        ResourceDeclaration(name="b.txt", digest=d2),
    ))
    multi_addr = dataset_address(multi_decl)
    assert multi_addr is not None
    writer.add(stored.dataset_node(
        title="two-files",
        resources=[{"name": "a.txt", "digest": d1}, {"name": "b.txt", "digest": d2}],
    ))
    multi_res_spec = freeze(
        SpecDraft(
            target=existing_spec.target,
            estimand=existing_spec.estimand,
            method=existing_spec.method,
            assumptions=existing_spec.assumptions,
            falsification=existing_spec.falsification,
            input_roles=(SpecInput(role="observes", dataset=multi_addr),),
            applicability=existing_spec.applicability,
            interpretation_rule=existing_spec.interpretation_rule,
            equivalence_rule=existing_spec.equivalence_rule,
            parameters=existing_spec.parameters,
            nondeterminism=Deterministic(),
        ),
        held_rules=REFERENCE_RULES,
    )
    multi_res_spec_ref = writer.add(stored.analysis_spec_node(multi_res_spec)).id

    with pytest.raises(Refused) as caught_res:
        d.invoke("run", {"spec": multi_res_spec_ref, "dataset": multi_addr, "code": str(code),
                         "entrypoint": entrypoint, "targets": list(targets)})
    assert caught_res.value.refusal.code == "invalid-input"
    assert "declares 2 resources; single-file staging requires 1" in caught_res.value.refusal.message
    assert sum(1 for n in ctx.write_view().iter_stored() if n.kind == "act-report") == act_reports_before

    other_ref = hold_fixture_dataset(ctx.config, "aux.txt", b"aux\n", "auxiliary")
    two_dataset_spec = freeze(
        SpecDraft(
            target=existing_spec.target,
            estimand=existing_spec.estimand,
            method=existing_spec.method,
            assumptions=existing_spec.assumptions,
            falsification=existing_spec.falsification,
            input_roles=(
                SpecInput(role="observes", dataset=ref),
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
    two_dataset_spec_ref = writer.add(stored.analysis_spec_node(two_dataset_spec)).id

    with pytest.raises(Refused) as caught_spec:
        d.invoke("run", {"spec": two_dataset_spec_ref, "dataset": ref, "code": str(code),
                         "entrypoint": entrypoint, "targets": list(targets)})
    assert caught_spec.value.refusal.code == "invalid-input"
    assert "observes datasets other than" in caught_spec.value.refusal.message
    assert sum(1 for n in ctx.write_view().iter_stored() if n.kind == "act-report") == act_reports_before

