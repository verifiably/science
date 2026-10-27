"""The walk (milestone design §5.6): one `science mcp serve` process, one attended
session, every command a JSON-RPC `tools/call` frame; `science epoch` runs between
batches in a fresh process; the frozen schedule and nothing else.

    walk.py <state> [--new-run] [--stop-after KEY] [--crash-before-record KEY]
    walk.py <state> --reconcile KEY=IDENTITY|none

Without `--new-run` the walk resumes the latest run directory whose journal is not
complete, else starts a new one. Live-run contract: every mint is journaled
`attempt` before its frame and `record` after its reply; a fail-before-write check
precedes each `attempt`; a restart verifies each recorded mint by content, stops on
an uncertain one (exit 3) until it is reconciled, and re-issues the last selection
before its first unjournaled step. `--stop-after` and `--crash-before-record` are the
drills' hooks.
"""
from __future__ import annotations

import argparse
import json
import queue
import shutil
import subprocess
import sys
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import yaml

import selections
from common import DriverStop, Journal, State, environment, now, read_json, run_cli_full, science_bin, stop, write_json
from terms import EZH2, PHF19, PLACEHOLDER

META = {
    "io.modelcontextprotocol/protocolVersion": "2026-07-28",
    "io.modelcontextprotocol/clientInfo": {"name": "sci-0d00d2-walk", "version": "0"},
    "io.modelcontextprotocol/clientCapabilities": {},
}
READ_TIMEOUT = 120
PROJECTS = ("multiple-myeloma", "cancer", "health", "multiple-myeloma-findings")
VIEWS = ("multiple-myeloma", "cancer", "health")
HEALTH_QUESTION = "Does disease stage drive the PRC2 catalytic core (EZH2) where it drives PHF19?"
EVIDENCE_BOUND = "evidence-bound terms"
MM30_OPERATOR = "mm30/affects-concept-molecular-entity"
W3_EXPECTED = {  # key -> (the project it is minted under, its name)
    "W3.question.health": ("health", HEALTH_QUESTION),
    "W3.reuse": ("cancer", HEALTH_QUESTION),
    "W3.question.evidence-bound-terms": ("multiple-myeloma", EVIDENCE_BOUND),
}
PROJECT_BODIES = {
    "multiple-myeloma": "The multiple-myeloma program's view of the world (projects design §6.2).",
    "cancer": "Cancer: the myeloma view verbatim until a disease vocabulary is bound (projects design §6.2, §6.3).",
    "health": "Health: the cancer view plus what the health program introduces (projects design §6.2).",
    "multiple-myeloma-findings": "The findings level of multiple-myeloma (projects design §8.1), "
                                 "minted as a project so that it can be previewed (milestone design C7).",
}


class Server:
    """`science mcp serve` with bounded reads and an unconditional close."""

    def __init__(self, config: Path, cwd: Path, stderr_path: Path):
        self.config, self.cwd, self.stderr_path = config, cwd, stderr_path
        self.counter = 0

    def __enter__(self) -> Server:
        self.stderr = self.stderr_path.open("a")
        self.process = subprocess.Popen(
            [str(science_bin()), "mcp", "serve", "--config", str(self.config)],
            cwd=self.cwd, env=environment(self.config), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=self.stderr, text=True,
        )
        self.lines: queue.Queue = queue.Queue()
        threading.Thread(target=self._pump, daemon=True).start()
        try:
            # The session is open once the server answers; no attempt row precedes this.
            self.send({"jsonrpc": "2.0", "id": 0, "method": "server/discover", "params": {"_meta": META}},
                      "server/discover")
        except BaseException:
            self.__exit__(None, None, None)
            raise
        return self

    def _pump(self) -> None:
        for line in self.process.stdout:
            self.lines.put(line)
        self.lines.put(None)

    def request(self, name: str, arguments: dict, step: str) -> dict:
        self.counter += 1
        return self.send({"jsonrpc": "2.0", "id": self.counter, "method": "tools/call",
                          "params": {"name": name, "arguments": arguments, "_meta": META}}, step)

    def send(self, frame: dict, step: str) -> dict:
        self.process.stdin.write(json.dumps(frame) + "\n")
        self.process.stdin.flush()
        try:
            line = self.lines.get(timeout=READ_TIMEOUT)
        except queue.Empty:
            stop(f"{step}: no reply from the server within {READ_TIMEOUT}s")
        if line is None:
            stop(f"{step}: the server exited (status {self.process.poll()}); see {self.stderr_path}")
        reply = json.loads(line)
        if reply.get("id") != frame["id"]:
            stop(f"{step}: reply id {reply.get('id')} for request {frame['id']}")
        if frame["method"] == "server/discover" and "result" not in reply:
            stop(f"{step}: {reply}")
        return reply

    def __exit__(self, *exc) -> None:
        try:
            self.process.stdin.close()
        except OSError:
            pass
        try:
            self.process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
        self.stderr.close()


def record_identity(text: str) -> tuple[str, str, str]:
    """(kind, record id, uid) of the reply's one record block."""
    blocks = [line for line in text.splitlines() if line.startswith("[") and " uid=" in line]
    if len(blocks) != 1:
        stop(f"expected one record block, found {len(blocks)}:\n{text}")
    head, uid = blocks[0].rsplit(" uid=", 1)
    kind, record_id = head[1:].split("] ", 1)
    return kind, record_id, uid


def coordination_address(record_id: str) -> str:
    kind, rest = record_id.split(":", 1)
    parts = rest.split(".")
    return f"coord:{parts[0]}" if len(parts) == 2 else f"coord:{parts[0]}/{parts[1]}"


class Walk:
    def __init__(self, state: State, run_dir: Path, *, stop_after=None, crash_before_record=None):
        self.state, self.run_dir = state, run_dir
        self.cfg = state.load_config()
        self.declared = state.declared
        if self.declared is None:
            stop(f"{state.path} has no declared.json")
        self.journal = Journal(run_dir / "progress.json", world_id=state.world["world_id"], config=state.config)
        self.stop_after, self.crash_before_record = stop_after, crash_before_record
        self.resolved = run_dir / "queries-resolved"
        self.server: Server | None = None
        self.reselected = False

    # -- outputs ---------------------------------------------------------------
    def log(self, key, call, arguments, result, seconds) -> None:
        with (self.run_dir / "walk.jsonl").open("a") as handle:
            handle.write(json.dumps({"key": key, "call": call, "arguments": arguments, "result": result,
                                     "seconds": round(seconds, 3), "at": now()}) + "\n")

    def append_json(self, name: str, row: dict) -> None:
        # Keyed: a step re-run after a crash replaces its row rather than adding one.
        path = self.run_dir / name
        rows = [r for r in (read_json(path) if path.exists() else []) if r["key"] != row["key"]]
        rows.append(row)
        write_json(path, rows)

    def save(self, name: str, text: str) -> None:
        (self.run_dir / name).write_text(text)

    # -- the server --------------------------------------------------------------
    def call(self, key: str, name: str, arguments: dict) -> tuple[dict, float]:
        started = time.monotonic()
        reply = self.server.request(name, arguments, key)
        seconds = time.monotonic() - started
        if "error" in reply:
            self.log(key, name, arguments, reply, seconds)
            self.journal.stopped(key, json.dumps(reply["error"]))
            stop(f"{key}: `{name}` answered JSON-RPC error {reply['error']}")
        result = reply["result"]
        status = "REFUSED" if result["isError"] else "ok"
        print(f"--- {key} {name} [{status}] {seconds:.2f}s invocation {result['structuredContent'].get('invocation_id')}")
        return result, seconds

    def text(self, result: dict) -> str:
        return result["content"][0]["text"]

    def ensure_selection(self) -> None:
        """Before the first unjournaled step of a resumed run, the last journaled
        selection is re-issued on this server (live-run contract)."""
        if self.reselected:
            return
        self.reselected = True
        last = self.journal.last_selection()
        if last is None:
            return
        arguments = {"clear": True} if last == "--clear" else {"target": last}
        result, seconds = self.call("resume.select", "project-select", arguments)
        self.log("resume.select", "project-select", arguments, result, seconds)
        if result["isError"]:
            stop(f"resume: re-issuing the selection {last} refused: {self.text(result)}")
        self.journal.select("resume.select", None if last == "--clear" else last,
                            invocation_id=result["structuredContent"].get("invocation_id"), seconds=seconds)

    def hook(self, key: str) -> None:
        if self.stop_after == key:
            self.journal.stopped(key, "stop-after")
            print(f"stop-after {key}: stopping with the server closed")
            raise SystemExit(0)

    # -- steps -------------------------------------------------------------------
    def done(self, key: str) -> bool:
        return self.journal.status(key) in {"recorded", "reconciled"}

    def read(self, key: str, name: str, arguments: dict, *, output: str | None = None,
             expect_refusal: bool = False) -> str:
        if self.done(key):
            return ""
        self.ensure_selection()
        result, seconds = self.call(key, name, arguments)
        self.log(key, name, arguments, result, seconds)
        text = self.text(result)
        refusal = result["structuredContent"].get("refusal")
        if result["isError"] and not expect_refusal:
            self.journal.stopped(key, text)
            stop(f"{key}: `{name}` refused: {text}")
        if output:
            self.save(output, text + "\n" if not text.endswith("\n") else text)
        self.journal.record(key, invocation_id=result["structuredContent"].get("invocation_id"),
                            seconds=round(seconds, 3), refusal=refusal)
        self.hook(key)
        return text

    def select(self, key: str, target: str | None) -> None:
        if self.journal.selected(key):
            return
        self.ensure_selection()
        arguments = {"clear": True} if target is None else {"target": target}
        result, seconds = self.call(key, "project-select", arguments)
        self.log(key, "project-select", arguments, result, seconds)
        if result["isError"]:
            self.journal.stopped(key, self.text(result))
            stop(f"{key}: project-select refused: {self.text(result)}")
        self.journal.select(key, target, invocation_id=result["structuredContent"].get("invocation_id"),
                            seconds=round(seconds, 3))
        self.hook(key)

    def mint(self, key: str, name: str, arguments: dict, check) -> str:
        if self.done(key):
            return self.journal.identity(key)
        self.ensure_selection()
        try:
            check()
        except DriverStop as caught:
            self.journal.stopped(key, f"fail-before-write: {caught.message}")
            raise
        self.journal.attempt(key)
        result, seconds = self.call(key, name, arguments)
        self.log(key, name, arguments, result, seconds)
        if self.crash_before_record == key:
            print(f"crash-before-record {key}: reply read, nothing journaled")
            raise SystemExit(1)
        if result["isError"]:
            self.journal.refused(key, result["structuredContent"].get("refusal"))
            stop(f"{key}: `{name}` refused: {self.text(result)}")
        kind, record_id, uid = record_identity(self.text(result))
        identity = record_id if kind in {"proposition", "analysis-spec"} else coordination_address(record_id)
        self.journal.record(key, identity=identity, invocation_id=result["structuredContent"].get("invocation_id"),
                            seconds=round(seconds, 3), record_id=record_id, revision=uid)
        print(f"    {identity}")
        if key == "W1.claim" and identity != EZH2:
            stop(f"W1.claim minted {identity}; the frozen queries and the spec name {EZH2}")
        self.hook(key)
        return identity

    def epoch(self, key: str, trigger: str, writes: list[str]) -> None:
        if self.done(key):
            return
        interrupted = self.journal.status(key) == "attempted"
        self.journal.attempt(key)
        started = time.monotonic()
        done = run_cli_full(self.state.config, ["epoch"], cwd=self.state.path, timeout=1800)
        seconds = time.monotonic() - started
        self.log(key, "science epoch", {}, {"returncode": done.returncode, "stdout": done.stdout,
                                            "stderr": done.stderr}, seconds)
        if done.returncode != 0:
            self.journal.stopped(key, done.stdout + done.stderr)
            stop(f"{key}: `science epoch` exited {done.returncode}: {done.stdout}{done.stderr}")
        outcome, packaging = done.stdout.splitlines()[0].split(": ", 1)
        print(f"--- {key} epoch [{outcome}] {seconds:.2f}s {packaging}")
        self.append_json("epochs.json", {"key": key, "trigger": trigger, "outcome": outcome,
                                         "packaging_identity": packaging, "seconds": round(seconds, 3),
                                         "writes_since_previous": writes,
                                         "after_interrupted_attempt": interrupted})
        self.journal.record(key, identity=packaging, seconds=round(seconds, 3), outcome=outcome,
                            after_interrupted_attempt=interrupted)
        self.hook(key)

    def view(self, key: str, address: str, query_file: str) -> None:
        if self.done(key):
            return
        row = selections.read_view(self.cfg, key, address, self.resolved / query_file)
        self.append_json("selections.json", row)
        self.journal.record(key, identity=address, equivalent=row["equivalent"], complete=row["complete"])
        print(f"--- {key} view {address}: {len(row['selected'])} selected, equivalent {row['equivalent']}, "
              f"complete {row['complete']}")
        self.hook(key)

    # -- fail-before-write checks --------------------------------------------------
    def context(self):
        from science.config import ReadContext
        return ReadContext.open(self.cfg)

    def stored(self):
        for corpus_id, view in self.context().read_views():
            yield from view.iter_stored()

    def check_claim(self) -> None:
        if any(node.id == EZH2 for node in self.stored()):
            stop(f"W1.claim: {EZH2} already exists in this world")

    def spec_targets(self) -> list[tuple[str, dict]]:
        found = []
        for node in self.stored():
            if node.kind == "analysis-spec":
                projection = json.loads(node.facets["analysis-spec"]["projection"])
                found.append((node.id, projection))
        return found

    def check_spec(self) -> None:
        existing = [spec for spec, projection in self.spec_targets() if projection["target"] == EZH2]
        if existing:
            stop(f"W1.spec: {existing} already target {EZH2}")

    def check_project(self, name: str):
        def check() -> None:
            from science.coordination import resolve_project_ref
            from science.refusal import Refused
            try:
                address = resolve_project_ref(self.context(), name)
            except Refused as caught:
                if caught.refusal.code == "unknown-project":
                    return
                raise
            stop(f"W2.project.{name}: a project named {name!r} already stands at {address}")
        return check

    def check_question(self, key: str, project: str, name: str):
        def check() -> None:
            from science.coordination import parse_unpinned, tip_nodes
            resolver = self.context().coordination()
            address = parse_unpinned(self.journal.identity(f"W2.project.{project}"))
            for kind in ("question",):
                for found, resolved in resolver.standing(kind, project=address).items():
                    if any(tip.title == name for tip in tip_nodes(resolver, resolved)):
                        stop(f"{key}: {project} already holds {kind} {found} named {name!r}")
        return check

    def checks(self) -> dict:
        """The fail-before-write check of every minting key."""
        return {"W1.claim": self.check_claim, "W1.spec": self.check_spec,
                **{f"W2.project.{name}": self.check_project(name) for name in PROJECTS},
                **{key: self.check_question(key, project, name) for key, (project, name) in W3_EXPECTED.items()}}

    def existing(self, key: str) -> list[str]:
        """What `--check KEY` prints: every record that key's mint would have made."""
        if key == "W1.claim":
            return [node.id for node in self.stored() if node.id == EZH2]
        if key == "W1.spec":
            return [spec for spec, projection in self.spec_targets() if projection["target"] == EZH2]
        if key.startswith("W2.project."):
            from science.coordination import resolve_project_ref
            from science.refusal import Refused
            try:
                return [str(resolve_project_ref(self.context(), key.removeprefix("W2.project.")))]
            except Refused as caught:
                if caught.refusal.code == "unknown-project":
                    return []
                raise
        from science.coordination import parse_unpinned, tip_nodes
        project, name = W3_EXPECTED[key]
        resolver = self.context().coordination()
        address = parse_unpinned(self.journal.identity(f"W2.project.{project}"))
        return [str(found) for found, resolved in resolver.standing("question", project=address).items()
                if any(tip.title == name for tip in tip_nodes(resolver, resolved))]

    def verify_identity(self, key: str, identity: str) -> None:
        """Content verification of one minted identity; stops on any mismatch."""
        if key == "W1.claim":
            nodes = [n for n in self.stored() if n.id == identity]
            if identity != EZH2 or len(nodes) != 1:
                stop(f"{key}: {identity} is not the one {EZH2} record")
            claim = nodes[0].facets["proposition"]
            if claim["operator"] != MM30_OPERATOR or claim["args"] != ["concept:disease-stage", "protein:EZH2"]:
                stop(f"{key}: {identity} does not hold the claim journaled: {claim}")
            return
        if key == "W1.spec":
            found = [p for spec, p in self.spec_targets() if spec == identity]
            if len(found) != 1:
                stop(f"{key}: {identity} is not one analysis-spec in this world")
            observes = [r["dataset"] for r in found[0]["input_roles"] if r["role"] == "observes"]
            if found[0]["target"] != EZH2 or observes != [self.declared["cohort"]]:
                stop(f"{key}: {identity} targets {found[0]['target']}, observes {observes}")
            return
        from science.coordination import parse_unpinned
        try:
            address = parse_unpinned(identity)
        except Exception as caught:  # noqa: BLE001 -- a person's typed value, refused by name
            stop(f"{key}: {identity!r} is not an unpinned coord: address ({caught})")
        tip = selections.resolved_tip(self.cfg, identity)
        row = selections.equivalence(self.cfg, identity, self.resolved / self.query_file(key))
        if key.startswith("W2.project."):
            expected = ("project", key.removeprefix("W2.project."), None)
        else:
            project, name = W3_EXPECTED[key]
            owner = parse_unpinned(self.journal.identity(f"W2.project.{project}")).project
            expected = ("question", name, owner)
            if key == "W3.reuse" and identity == self.journal.identity("W3.question.health"):
                stop(f"{key}: {identity} is the reuse's source, not its copy")
        actual = (tip.kind, tip.title, None if address.local is None else address.project)
        if actual != expected or not row["equivalent"]:
            stop(f"{key}: {identity} is {actual} with equivalent {row['equivalent']}; expected {expected}")

    # -- resume ------------------------------------------------------------------
    def verify_recorded(self) -> None:
        keys = sorted({row["key"] for row in self.journal.rows if row["key"].startswith("W")
                       and not row["key"].startswith("W3.select")})
        for key in keys:
            status = self.journal.status(key)
            if status == "attempted":
                self.journal.stopped(key, "uncertain write")
                print(f"uncertain write {key}: run `{sys.executable} {Path(__file__).resolve()} "
                      f"{self.state.path} --check {key}` and rerun with --reconcile {key}=<identity|none>",
                      flush=True)
                raise SystemExit(3)
            if status in {"recorded", "reconciled"}:
                self.verify_identity(key, self.journal.identity(key))
                print(f"resume: {key} {self.journal.identity(key)} verified")

    def reconcile(self, key: str, value: str) -> None:
        if self.journal.status(key) not in {"attempted", "reconciled"}:
            stop(f"{key} is {self.journal.status(key)}, not an uncertain or reconciled write")
        if value == "none":
            found = self.existing(key)
            if found:
                stop(f"{key}: `none` given, but {found} exists; reconcile with its identity")
        else:
            self.verify_identity(key, value)
        self.journal.reconcile(key, None if value == "none" else value)
        print(f"reconciled {key}={value} in {self.run_dir}")

    def query_file(self, key: str) -> str:
        if key.startswith("W2.project."):
            return key.removeprefix("W2.project.") + ".yaml"
        return {"W3.question.health": "health-question.yaml", "W3.reuse": "health-question.yaml",
                "W3.question.evidence-bound-terms": "evidence-bound-terms.yaml"}[key]

    # -- the substitution ----------------------------------------------------------
    def check_templates(self) -> None:
        manifest = (self.state.queries / "MANIFEST").read_text().split()
        expected = dict(zip(manifest[1::2], manifest[0::2], strict=True))
        actual = {p.name: selections._sha256(p.read_bytes()) for p in self.state.queries.glob("*.yaml")}
        if actual != expected:
            stop(f"{self.state.queries} differs from its MANIFEST: {actual} != {expected}")

    def check_resolved(self) -> None:
        manifest = (self.resolved / "MANIFEST").read_text().split()
        expected = dict(zip(manifest[1::2], manifest[0::2], strict=True))
        actual = {p.name: selections._sha256(p.read_bytes()) for p in self.resolved.glob("*.yaml")}
        if actual != expected:
            stop(f"{self.resolved} differs from its MANIFEST: {actual} != {expected}")
        (row,) = [r for r in self.journal.rows if r["key"] == "Q1" and r["phase"] == "record"]
        for name, hashes in row["hashes"].items():
            if selections._sha256((self.resolved / name).read_bytes()) != hashes["raw_sha256"]:
                stop(f"{self.resolved / name} differs from the substitution journaled in Q1")

    def resolve_queries(self, spec: str) -> None:
        if self.done("Q1"):
            self.check_resolved()
            return
        self.check_templates()
        if self.resolved.exists():
            shutil.rmtree(self.resolved)  # an unjournaled copy is rewritten from the templates
        shutil.copytree(self.state.queries, self.resolved)
        hashes = {}
        for name in ("health.yaml", "health-question.yaml"):
            path = self.resolved / name
            text = path.read_text()
            if text.count(PLACEHOLDER) != 1:
                stop(f"{path}: {text.count(PLACEHOLDER)} placeholders")
            path.write_text(text.replace(PLACEHOLDER, spec))
            hashes[name] = {"raw_sha256": selections._sha256(path.read_bytes()),
                            "projection_sha256": selections.projection_sha256(yaml.safe_load(path.read_text()))}
        manifest = [f"{selections._sha256(p.read_bytes())}  {p.name}"
                    for p in sorted(self.resolved.glob("*.yaml"))]
        (self.resolved / "MANIFEST").write_text("\n".join(manifest) + "\n")
        self.journal.record("Q1", identity=spec, hashes=hashes)

    # -- the schedule ----------------------------------------------------------------
    def run(self) -> None:
        resumed = any(row["phase"] in {"attempt", "record", "select"} for row in self.journal.rows)
        if self.done("Q1"):
            self.check_resolved()
        self.verify_recorded()
        if not resumed:
            self.reselected = True
        if self.journal.status("W1.claim") is None:
            # A journal that has not minted the claim, against a world that already
            # holds it, stops here, before a server opens or an epoch is published.
            try:
                self.check_claim()
            except DriverStop as caught:
                self.journal.stopped("W1.claim", f"fail-before-write: {caught.message}")
                raise
        declared = self.declared
        with Server(self.state.config, self.state.path, self.run_dir / "serve.stderr") as self.server:
            self.read("S0", "status", {}, output="status-initial.txt")
            self.epoch("E1", "initial", ["declarations"])
            self.mint("W1.claim", "claim", {
                "subject": "concept:disease-stage", "predicate": "affects", "object": "protein:EZH2",
                "layer": "causal_effect", "polarity": "positive"}, self.check_claim)
            spec = self.mint("W1.spec", "spec", spec_arguments(declared), self.check_spec)
            self.resolve_queries(spec)
            self.epoch("E2", "evidence", ["W1.claim", "W1.spec"])
            for name in PROJECTS:
                self.mint(f"W2.project.{name}", "project", {
                    "name": name, "query": (self.resolved / f"{name}.yaml").read_text(),
                    "body": PROJECT_BODIES[name]}, self.check_project(name))
            self.read("R0.next-stale", "next", {}, output="next-stale.txt", expect_refusal=True)
            self.epoch("E3", "coordination-only", [f"W2.project.{name}" for name in PROJECTS])
            for name in PROJECTS:
                self.view(f"R1.{name}", self.journal.identity(f"W2.project.{name}"), f"{name}.yaml")
            self.select("W3.select.health", "health")
            question = self.mint("W3.question.health", "question", {
                "name": HEALTH_QUESTION, "query": (self.resolved / "health-question.yaml").read_text(),
                "body": "A narrower sub-claim of the health program's PRC2 line (milestone design §4.1): "
                        "the stage levels are myeloma's, so the cross-disease half is not representable yet."},
                self.checks()["W3.question.health"])
            self.select("W3.select.cancer", "cancer")
            reuse = self.mint("W3.reuse", "reuse", {"source": question}, self.checks()["W3.reuse"])
            self.select("W3.select.multiple-myeloma", "multiple-myeloma")
            bound = self.mint("W3.question.evidence-bound-terms", "question", {
                "name": EVIDENCE_BOUND, "query": (self.resolved / "evidence-bound-terms.yaml").read_text(),
                "body": "Measurement only (milestone design §5.4, M2): the term clauses its own evidence binds."},
                self.checks()["W3.question.evidence-bound-terms"])
            self.epoch("E4", "coordination-only", ["W3.question.health", "W3.reuse",
                                                   "W3.question.evidence-bound-terms"])
            self.epoch("E5", "none", [])
            for name in VIEWS:
                self.select(f"R2.{name}.select", name)
                self.read(f"R2.{name}", "next", {}, output=f"next-{name}.txt")
            self.select("R2.unselected.select", None)
            self.read("R2.unselected", "next", {}, output="next-unselected.txt")
            self.view("R3.question.health", question, "health-question.yaml")
            self.view("R3.reuse", reuse, "health-question.yaml")
            self.view("R3.question.evidence-bound-terms", bound, "evidence-bound-terms.yaml")
            self.read("R4", "publish-preview", {"target": "multiple-myeloma-findings",
                                                "to": str(self.run_dir / "publish")},
                      output="publish-preview.txt", expect_refusal=True)
            self.read("R5", "belief", {"proposition": PHF19}, output="belief.txt")
            self.read("S1", "status", {}, output="status-final.txt")
        print(f"walk complete: {self.run_dir}")


def spec_arguments(declared: dict) -> dict:
    annotation = declared["annotation"]
    ndmm, pd = declared["condition_values"]["ndmm"], declared["condition_values"]["pd"]
    return {
        "target": EZH2, "dataset": declared["cohort"],
        "contrast": "levels", "slot": 0, "baseline": "level:ndmm", "comparison": "level:pd",
        "measure": "measure:rna-seq-tpm", "scale": "additive", "reference": "0",
        "identification": "identification:observational",
        "method": (
            "TPM per gene from the counts' `unstranded` column by the GDC's own rule: the count divided by the "
            "gene's length in kilobases, the length being the sum of the gene's non-overlapping exon bases in "
            f"the GENCODE release 36 primary annotation ({annotation}), normalised to a million per sample; "
            "protein:EZH2 is the row whose Ensembl gene id without its version suffix is ENSG00000106462; "
            f"level:ndmm is every sample whose metadata `condition` is {ndmm!r} and level:pd every sample whose "
            f"`condition` is {pd!r}, one sample per patient as the source states; then a two-group rank "
            "comparison (Mann-Whitney U, normal approximation) at alpha 0.05, as the mm30 spec's"),
        "assumptions": ("independent samples, one per patient; the stage is the two-level factor the metadata's "
                        "`condition` column carries; the counts were produced against GENCODE release 36"),
        "falsification": "no difference at alpha 0.05, or a difference opposite the proposition's polarity",
        "interpretation_rule": "beliefs/outcome-file/v1",
        "equivalence_rule": "beliefs/content-identity-equality/v1",
        "parameters": ["alpha=0.05"],
    }


def latest_run(state: State) -> Path | None:
    runs = sorted(state.runs.glob("*/progress.json")) if state.runs.exists() else []
    return runs[-1].parent if runs else None


def complete(run_dir: Path) -> bool:
    progress = run_dir / "progress.json"
    return progress.exists() and any(
        json.loads(line).get("key") == "S1" and json.loads(line).get("phase") == "record"
        for line in progress.read_text().splitlines() if line.strip())


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("state", type=Path)
    parser.add_argument("--new-run", action="store_true")
    parser.add_argument("--stop-after")
    parser.add_argument("--crash-before-record")
    parser.add_argument("--reconcile", help="KEY=IDENTITY or KEY=none")
    parser.add_argument("--check", help="KEY: print what that key's mint would have made")
    parser.add_argument("--run", type=Path, help="the run directory to resume, check or reconcile")
    args = parser.parse_args(argv[1:])
    state = State(args.state)
    latest = latest_run(state)
    if args.run is not None:
        latest = args.run.resolve()
        if latest.parent != state.runs or not (latest / "progress.json").is_file():
            stop(f"{latest} is not a run of {state.path}")
    if args.reconcile or args.check:
        if latest is None or complete(latest):
            stop("--reconcile and --check need an incomplete run")
        walk = Walk(state, latest)
        if args.check:
            found = walk.existing(args.check)
            print(f"{args.check}: {found if found else 'nothing minted'}")
            return 0
        key, _, value = args.reconcile.partition("=")
        walk.reconcile(key, value)
        return 0
    if latest is not None and not complete(latest) and not args.new_run:
        run_dir = latest
        print(f"resuming {run_dir}")
    else:
        run_dir = state.runs / datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        run_dir.mkdir(parents=True)
        print(f"new run {run_dir}")
    Walk(state, run_dir, stop_after=args.stop_after, crash_before_record=args.crash_before_record).run()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
