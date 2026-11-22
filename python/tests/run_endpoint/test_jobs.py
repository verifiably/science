"""Scratch-local workflows use the run session's private kernel staging."""
import threading

import pytest
from beliefs.confinement import host_prerequisites
from beliefs.permit import WritePermit
from beliefs.session import open_run_session

from helpers.analysis import spec_inputs
from helpers.world import build_belief_world, fixture_bundle, hold_fixture_dataset, open_rig
from science.config import ReadContext
from science.dispatch import Dispatcher
from science.loader import production_tree, resolve_handlers
from science.run_endpoint.paths import Scratch


@pytest.mark.parametrize("command", ["run", "derive"])
def test_captured_job_uses_kernel_staging(certified_work, command):
    reason = host_prerequisites()
    if reason:
        pytest.skip(f"bwrap confinement is unavailable: {reason}")
    cfg = build_belief_world(certified_work)
    dataset = hold_fixture_dataset(cfg, "data.txt", b"x\n", "input")
    scratch = certified_work / "actor"
    code, entry, targets = fixture_bundle(scratch)
    inputs = dict(code=str(code), entrypoint=entry, targets=list(targets), dataset=dataset)
    if command == "run":
        with open_rig(cfg, ("spec",)) as (attended, _):
            spec = attended.invoke("spec", spec_inputs(cfg, target="proposition:p1", dataset=dataset))
            inputs["spec"] = next(word for word in spec.text.split() if word.startswith("analysis-spec:"))
    else:
        inputs["title"] = "derived fixture"
    decls = tuple(d for d in production_tree() if d.name == command)
    kinds = frozenset(decls[0].write_class.kinds)
    permit = WritePermit(kinds, frozenset(decls[0].write_class.routes.values()))
    session = open_run_session(cfg.world, cfg.operations_root, write_root=cfg.write_root, profile=cfg.profile,
                               ceiling=permit, store_root=cfg.store_root if command == "derive" else None)
    try:
        with Scratch(scratch, cfg.operations_root, threading.Event()) as capture:
            dispatcher = Dispatcher(decls, resolve_handlers(decls), ReadContext.open(cfg), session=session, run_inputs=capture)
            outcome = dispatcher.invoke(command, inputs, invocation_id="kernel-stages")
            assert "[run] run:" in outcome.text
            assert not (cfg.operations_root / "capture" / "kernel-stages").exists()
            assert (cfg.operations_root / "scratch" / session.session_id / "kernel-stages").is_dir()
    finally:
        session.close()
