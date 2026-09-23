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
    _, view = ctx.single_view()
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
        _, view = ctx.single_view()
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
