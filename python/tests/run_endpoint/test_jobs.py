"""Scratch-local workflows use the run session's private kernel staging."""
import signal
import threading
from contextlib import contextmanager

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


@contextmanager
def supervisor_signals():
    from science.run_endpoint.service import _term_wakeup

    previous = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGTERM})
    try:
        with _term_wakeup():
            yield
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous)


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
        snakefile = code.parent / entry
        # The workload starts a private interpreter in its own sandbox and handles TERM there.
        probe = ("import os,signal; seen=[]; "
                 "assert signal.SIGTERM not in signal.pthread_sigmask(signal.SIG_BLOCK, []); "
                 "signal.signal(signal.SIGTERM, lambda signum, frame: seen.append(signum)); "
                 "os.kill(os.getpid(), signal.SIGTERM); assert seen == [signal.SIGTERM]")
        body = snakefile.read_text().replace("        import os, pathlib", "        import os, pathlib, subprocess, sys")
        body = body.replace("        pathlib.Path(input[0]).read_text()", f"        subprocess.run([sys.executable, '-I', '-c', {probe!r}], check=True, env={{'HOME': os.getcwd(), 'PATH': os.defpath, 'LD_LIBRARY_PATH': os.environ['LD_LIBRARY_PATH']}})")
        snakefile.write_text(body)
    decls = tuple(d for d in production_tree() if d.name == command)
    kinds = frozenset(decls[0].write_class.kinds)
    permit = WritePermit(kinds, frozenset(decls[0].write_class.routes.values()))
    session = open_run_session(cfg.world, cfg.operations_root, write_root=cfg.write_root, profile=cfg.profile,
                               ceiling=permit, store_root=cfg.store_root if command == "derive" else None)
    try:
        with supervisor_signals(), Scratch(scratch, cfg.operations_root, threading.Event()) as capture:
            dispatcher = Dispatcher(decls, resolve_handlers(decls), ReadContext.open(cfg), session=session, run_inputs=capture)
            outcome = dispatcher.invoke(command, inputs, invocation_id="kernel-stages")
            assert "[run] run:" in outcome.text
            assert not (cfg.operations_root / "capture" / "kernel-stages").exists()
            assert (cfg.operations_root / "scratch" / session.session_id / "kernel-stages").is_dir()
        assert not (cfg.operations_root / "scratch" / session.session_id).exists()
        assert (cfg.operations_root / "scratch" / "environments").is_dir()
    finally:
        session.close()
