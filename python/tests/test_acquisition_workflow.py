"""Static acquisition across a killed downloader, service acceptance and offline replay."""

import hashlib
import io
import json
import os
import select
import signal
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from beliefs import stored
from beliefs.holdings.acquisition_log import Attempt, parse_acquisition_log, render_acquisition_log
from beliefs.holdings.transport import UrlSeam
from beliefs.runrecord import decode_run_closure
from helpers.analysis import spec_inputs
from helpers.world import build_belief_world, fixture_bundle, open_rig, write_config_for
from science.acquisition.journal import Journal
from science.acquisition.retrieve import retrieve_set
from science.cli import main
from science.config import ReadContext
from science.serve import serve

PLAN = Path(__file__).parent / "fixtures" / "acquisition" / "quarry-geo.json"
SOURCE = json.loads(PLAN.read_bytes())
NAMES = [row["name"] for row in SOURCE["resources"]]
STAMP = "2026-11-23T12:00:00Z"


class Response(io.BytesIO):
    status = 200

    def getheader(self, name):
        return None


class Connection:
    def request(self, method, target, headers):
        assert method == "GET"
        self.content = target.rsplit("/", 1)[-1].encode()

    def getresponse(self):
        return Response(self.content)

    def close(self):
        pass


def offline(journal):
    seam = UrlSeam(lambda *_: ["1.1.1.1"], lambda *_: Connection())
    retrieve_set(journal, seam=seam, stamp=lambda: STAMP)


def worker(config, cut):
    from science.acquisition import operator
    operator.retrieve_set = offline
    append = Journal.append

    def gate(self, event, **payload):
        if event == "attempt-open" and payload["seq"] == 2:
            if cut == "after-open":
                append(self, event, **payload)
            print("at cut", flush=True)
            signal.pause()
        append(self, event, **payload)

    Journal.append = gate
    return main(["acquire", "start", "--plan", str(PLAN), "--config", config, "--min-interval-ms", "0"])


def line_from(stream):
    assert select.select([stream], [], [], 40)[0], "downloader did not reach its checkpoint"
    return stream.readline().decode().strip()


@pytest.mark.parametrize("cut", ["before-open", "after-open"])
@pytest.mark.parametrize("resume", [False, True])
def test_cut_and_continue(certified_work, short_tmp, monkeypatch, capsys, cut, resume):
    from science.acquisition import operator

    cfg = build_belief_world(certified_work)
    initial = {n.id for n in ReadContext.open(cfg).write_view().iter_stored() if n.kind == "holdings-observation"}
    config = str(write_config_for(cfg, short_tmp / "service.sock"))
    home = certified_work / "empty-home"
    home.mkdir()
    env = {"PATH": os.defpath, "HOME": str(home), "XDG_CONFIG_HOME": str(home)}
    with subprocess.Popen([sys.executable, __file__, config, cut], env=env, stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0) as child:
        try:
            token = line_from(child.stdout)
            assert len(token) == 32, child.stderr.read() if child.poll() is not None else token
            assert line_from(child.stdout) == "at cut"
            server = serve(cfg, short_tmp / "service.sock")
            thread = threading.Thread(target=server.serve_forever)
            thread.start()
            try:
                def call(verb, *args):
                    return main(["acquire", verb, "--config", config, "--set", token, *args])

                assert main(["acquire", "start", "--config", config, "--plan", str(PLAN)]) == 3
                assert "retrieval-busy" in capsys.readouterr().err
                assert [p.name for p in (cfg.operations_root / "acquisitions").iterdir()] == [token]
                for flag in ([], ["--accept-partial"]):
                    assert call("seal", *flag) == 3
                    assert "set-busy" in capsys.readouterr().err
                assert call("status") == 0
                assert json.loads(capsys.readouterr().out)["active"] == int(cut == "after-open")
                child.kill()
                child.wait(timeout=10)
                for _ in range(2):
                    assert call("status") == 0
                    assert json.loads(capsys.readouterr().out)["pending"] == 1
                from science.acquisition.journal import locked_directory
                with locked_directory(cfg.operations_root / "acquisitions" / token, "set-busy"):
                    assert call("resume") == 3
                    assert "set-busy" in capsys.readouterr().err
                assert call("seal") == 3
                assert "partial" in capsys.readouterr().err
                monkeypatch.setattr(operator, "retrieve_set", offline)
                if resume:
                    assert call("resume") == 0
                assert call("seal", *([] if resume else ["--accept-partial"])) == 0
                capsys.readouterr()
                assert call("status") == 0
                final = json.loads(capsys.readouterr().out)
            finally:
                server.shutdown()
                thread.join(timeout=10)
                server.server_close()
        finally:
            if child.poll() is None:
                child.kill()
                child.wait(timeout=10)
    j = Journal.open(cfg.operations_root, token)
    raw = (j.path / "acquisition-log.jsonl").read_bytes()
    log = parse_acquisition_log(raw)
    assert log.header.plan == SOURCE and json.loads((j.path / "plan.json").read_bytes()) == SOURCE
    assert render_acquisition_log(log) == raw
    completed = Attempt(STAMP, STAMP, "fetched", 200, (), None)
    assert log.lines[0].attempts == (completed,)
    interrupted = (Attempt(STAMP, None, "interrupted", None, (), None),) if cut == "after-open" else ()
    assert log.lines[1].attempts == interrupted + ((completed,) if resume else ())
    assert [r.member for r in log.lines if r.result == "fetched"] == NAMES[:1 + int(resume)]
    with open_rig(cfg, ("derive", "spec", "run", "verify")) as (d, ctx):
        view = ctx.write_view()
        report = stored.act_report_facet(view.get(final["report"]))
        summary = next(e["outcome"] for e in report["entries"] if e["kind"] == "acquisition-set")
        assert summary["log"] == "sha256:" + hashlib.sha256(raw).hexdigest()
        assert (summary["fetched"], summary["abandoned"], summary["failed"]) == (1 + int(resume), int(not resume), 0)
        assert view.holds(final["dataset"])
        assert len({n.id for n in view.iter_stored() if n.kind == "holdings-observation"} - initial) == 2
        if resume and cut == "after-open":
            check_offline_runs(d, ctx, cfg, final["dataset"], summary["tree"], certified_work)


def check_offline_runs(d, ctx, cfg, dataset, digest, work):
    code, entrypoint, targets = fixture_bundle(work)
    rule = code / "workflow" / "Snakefile"
    rule.write_text(rule.read_text().replace("inputs/data.txt", "inputs/data/" + NAMES[0]))
    shared = {"code": str(code), "entrypoint": entrypoint}

    def invoke(command, inputs, kind):
        out = d.invoke(command, inputs).text
        return next(word for word in out.split() if word.startswith(kind + ":"))

    derived = invoke("derive", dict(shared, targets=list(targets), dataset=dataset, title="from tree"), "run")
    verified = invoke("verify", dict(shared, run=derived), "verification")
    assert ctx.write_view().get(verified).facets["verification"]["verdict"] == "passed"
    spec = invoke("spec", spec_inputs(cfg, target="proposition:p1", dataset=dataset), "analysis-spec")
    assessed = invoke("run", dict(shared, targets=list(targets), dataset=dataset, spec=spec), "run")
    for run in (derived, assessed):
        (item,) = decode_run_closure(ctx.write_view().get(run)).recipe.inputs
        assert item.content == digest


if __name__ == "__main__":
    sys.exit(worker(*sys.argv[1:]))
