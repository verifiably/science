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
def test_captured_job_uses_kernel_staging(certified_work, command, monkeypatch):
    reason = host_prerequisites()
    if reason:
        pytest.skip(f"confinement unavailable: {reason}")
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
        from science.commands import derive

        execute = derive.execute_production_run

        def check_export(**kwargs):
            expected = cfg.operations_root / "scratch" / session.session_id / "kernel-stages"
            assert kwargs["output_dir"].parent == expected
            return execute(**kwargs)

        monkeypatch.setattr(derive, "execute_production_run", check_export)
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


def test_prepared_action_uses_two_slots_and_keyed_read(certified_work, autonomy_source):
    import json
    import runpy
    from pathlib import Path

    from autonomy.allowance import Campaign
    from autonomy.allowance.protocol import HostPeer
    from science.config import load_config
    from science.refusal import Refused
    from science.run_endpoint.allowance import JobAdmission
    from science.run_endpoint.research import ResearchAction

    gold = json.loads((autonomy_source / "python/tests/fixtures/allowance/research-launch.json").read_bytes())
    permit = WritePermit.from_json(gold["permit"])
    example = runpy.run_path(str(Path(__file__).parents[1] / "fixtures/analysis/demo.py"))
    world = example["create"](certified_work / "prepared")
    target = example["prepare"](world)
    config = load_config(world.config)
    action = ResearchAction(gold["research_action"] | {k: target[k] for k in ("workflow","spec","dataset","proposition")}, permit)
    from contextlib import closing
    from shutil import copytree
    scratch = certified_work / "actor-scratch"
    code = copytree(world.code, scratch / world.code.name)
    budget = {"attempts": 1, "input_tokens": 10, "output_tokens": 5, "micro_usd": 30, "job_starts": 2}
    name = "action"
    route = "f" * 64
    member = {"limits": budget, "caller": "band", "route_digest": route, "target": target}
    rates = dict.fromkeys(("input", "output", "cache_read", "cache_write_5m", "cache_write_1h"), 1000000)
    storage = certified_work / "authority"
    storage.mkdir(mode=0o700)
    import time
    pool = Campaign.issue(storage, {"campaign_id": "pool", "source": "offline synthetic test",
        "expires": int(time.time())+600, "members": {name: member}, "limits": budget,
        "tariff": {"model": "fixture", "billing_mode": "standard", "context": 10, "output_cap": 5,
            "max_input_micro_usd_per_mtok": 1000000, "output_micro_usd_per_mtok": 1000000,
            "rates_micro_usd_per_mtok": rates}})
    envelope = "e"*32
    pool.open(name, envelope, caller="band", target=target, route_digest=route, conversation_id=action.action["conversation_id"])
    ctx = ReadContext.open_detached(config)
    action.check_preparation(ctx)
    with supervisor_signals(), closing(open_run_session(config.world, config.operations_root, write_root=config.write_root,
            profile=config.profile, ceiling=permit)) as session, Scratch(scratch, config.operations_root, threading.Event()) as paths:
        pool.register_actor(name, envelope, session.session_id)
        with HostPeer(pool, name, envelope, "job") as host, host.take_socket() as peer:
            decls = production_tree()
            actor = Dispatcher(decls, resolve_handlers(decls), ctx, session=session, run_inputs=paths,
                               research=action, jobs=JobAdmission(peer))
            original = world.authoring_inputs()["run"] | {"code": str(code), "spec": target["spec"], "dataset": target["dataset"]}
            assert "ready" in actor.invoke("next", {}).text
            actor.invoke("run", original, invocation_id="A")
            with pytest.raises(Refused, match="already completed"):
                actor.invoke("run", original, invocation_id="duplicate")
            actor.invoke("assess", {"run": action.records["run"]}, invocation_id="B")
            actor.invoke("verify", world.authoring_inputs()["verify"] | {"code": str(code), "assessment": action.records["assessment"]}, invocation_id="C")
            with pytest.raises(Refused) as refused:
                actor.invoke("belief", {"proposition": target["proposition"], "key": "wrong"})
            assert refused.value.refusal.code == "allowance-scope"
            assert "Belief" in actor.invoke("belief", {"proposition": target["proposition"]}).text
            assert action.records["verification"].startswith("verification:")
            session.begin_close("stop", 10)
            session.seal(10)
    report = pool.snapshot(name)
    assert report["remaining"]["job_starts"] == 0
    assert [row["settlement"]["status"] for row in report["reservations"]] == ["completed", "completed"]


def test_member_queue_uses_bound_proposition_and_checks_readiness_before_original(certified_work, autonomy_source):
    import json
    import runpy
    from pathlib import Path
    from science.config import load_config
    from science.refusal import Refused
    from science.run_endpoint.research import ResearchAction
    gold = json.loads((autonomy_source / "python/tests/fixtures/allowance/research-launch.json").read_bytes())
    example = runpy.run_path(str(Path(__file__).parents[1] / "fixtures/analysis/demo.py"))
    world = example["create"](certified_work / "prepared")
    target = example["prepare"](world)
    ctx = ReadContext.open_detached(load_config(world.config))
    action = ResearchAction(gold["research_action"] | {k: target[k] for k in ("workflow","spec","dataset","proposition")},
                            WritePermit.from_json(gold["permit"]))
    with pytest.raises(Refused, match="ready"):
        action.require_selected(ctx)
    report = action.queue(ctx)
    assert report[-1].pairs == ((target["proposition"], "ready"),)
    action.require_selected(ctx)
    with pytest.raises(Refused, match="already"):
        action.queue(ctx)
