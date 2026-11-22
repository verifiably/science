"""Exercise the shipped CLI and stdio bridge through a namespace-bound endpoint."""
import array
from contextlib import ExitStack, contextmanager
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import pytest

from helpers.world import build_fixture_world_with_contract, write_config_for
from science.config import corpus_id_at
from science.loader import COMMANDS_ROOT
from science.run_endpoint.control import wire


# A fixture supervisor releases this actor only after the endpoint acknowledges
# its PID namespace. Each CLI and bridge invocation is a new ordinary client.
_ACTOR = """
import json, os, subprocess, sys
assert sys.stdin.buffer.readline() == b"go\\n"
env = {name: os.environ[name] for name in ("VERIFIABLY_ENDPOINT", "VERIFIABLY_TOKEN_FILE", "PATH", "HOME")}
cli = [sys.executable, "-I", "-m", "science.cli"]
def call(args, stdin=""):
    response = subprocess.run(cli + args, input=stdin, capture_output=True, env=env, text=True, timeout=30)
    return [response.returncode, response.stdout, response.stderr]
fields = ["--subject","concept:disease-stage","--predicate","affects","--object","protein:PHF19",
          "--layer","causal","--polarity","positive"]
meta = {"io.modelcontextprotocol/protocolVersion": "2026-07-28",
        "io.modelcontextprotocol/clientInfo": {"name": "fixture", "version": "1"},
        "io.modelcontextprotocol/clientCapabilities": {}}
def rpc(i, method, **params):
    return json.dumps({"jsonrpc": "2.0", "id": i, "method": method, "params": {"_meta":meta, **params}})+"\\n"
frames = (rpc(1, "tools/list") + rpc(2, "tools/call", name="status", arguments={}) +
          rpc(3, "tools/call", name="publish", arguments={"target":"fixture","to":"/tmp/result"}))
print(json.dumps([call(["status"]), call(["claim", *fields], "yes\\n"), call(["mcp", "bridge"], frames)]))
"""


def _runtime_paths():
    from atoms import coordinator
    from beliefs import root
    from nodes import core
    import science

    env = Path(sys.prefix)
    runtime = Path(sys.base_prefix)
    sources = [Path(module.__file__).resolve().parent for module in (coordinator, root, core, science)]
    roots = [next(p for p in (path, *path.parents) if p.name == "src") for path in sources]
    # uv's interpreter symlink often names its minor-version alias.
    interpreter_target = Path(os.readlink(env / "bin/python")) if (env / "bin/python").is_symlink() else None
    links = ()
    if interpreter_target is not None and interpreter_target.is_absolute():
        alias = interpreter_target.parent.parent
        if alias != runtime and alias.resolve() == runtime.resolve():
            links = ((runtime, alias),)
    return tuple(dict.fromkeys([env, runtime, COMMANDS_ROOT, *roots])), links


@contextmanager
def sandbox_actor(source, doc, tmp_path, program, *arguments):
    from autonomy.sandbox.bwrap import build_argv, read_info
    from autonomy.sandbox.spec import SandboxSpec

    control_path = Path(doc["control_socket"])
    control_path.unlink()
    paths, links = _runtime_paths()
    spec = SandboxSpec(scratch=Path(doc["scratch_dir"]), ro_binds=paths, symlinks=links, disable_nested_userns=True,
                       socket=Path(doc["socket"]), token=Path(doc["token_file"]),
                       env={"HOME": "/tmp", "VERIFIABLY_ENDPOINT": "/run/va/endpoint.sock",
                            "VERIFIABLY_TOKEN_FILE": "/run/va/token"})
    env = {"HOME": str(tmp_path), "PATH": os.defpath}
    with ExitStack() as stack:
        listener = stack.enter_context(socket.socket(socket.AF_UNIX))
        listener.bind(str(control_path))
        listener.listen(1)
        listener.settimeout(20)
        log = stack.enter_context((source.parent / "endpoint.log").open("wb"))
        endpoint = stack.enter_context(subprocess.Popen(
            [sys.executable, "-I", "-m", "science.cli", "serve", "--run", str(source)],
            stdin=subprocess.DEVNULL, stdout=log, stderr=log, env=env, start_new_session=True))
        stack.callback(endpoint.kill)
        conn, _ = listener.accept()
        stack.enter_context(conn)
        conn.settimeout(20)
        control = stack.enter_context(conn.makefile("rb"))
        opened = json.loads(control.readline())
        assert opened["type"] == "open"
        r, w = os.pipe()
        with os.fdopen(r, "rb") as info:
            with os.fdopen(w, "wb") as output:
                command = build_argv(spec, [sys.executable, "-I", "-c", program, *arguments], info_fd=w)
                actor = stack.enter_context(subprocess.Popen(command, pass_fds=(w,), stdin=subprocess.PIPE,
                                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env))
                stack.callback(actor.kill)
            spawned = read_info(info.fileno(), actor)
        if spawned is None:
            _, err = actor.communicate(timeout=10)
            detail = err.decode()
            if "Operation not permitted" in detail and os.environ.get("VERIFIABLY_UNCERTIFIED_HOST") == "1":
                pytest.skip(f"certified tuple unavailable on this host: {detail.strip()}")
            pytest.fail(f"sandbox did not start: {detail}")
        with open(f"/proc/{spawned['child-pid']}/ns/pid", "rb", buffering=0) as ns:
            conn.sendmsg([wire({"type": "bind-actor", "version": "control.v1"})],
                         [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", [ns.fileno()]))])
        assert json.loads(control.readline())["type"] == "bound"
        yield endpoint, actor, conn, control


@pytest.mark.parametrize("level", ["coordination", "mints"])
def test_sandbox_cli_and_bridge(autonomy_source, launch_file, certified_work, tmp_path, level):
    from autonomy.tiers import tier

    source, doc = launch_file
    work = certified_work / "with-contract"
    work.mkdir()
    cfg = build_fixture_world_with_contract(work)
    doc["config"] = str(write_config_for(cfg))
    doc["permit"] = tier(level, {"proposition": "corpus-write"} if level == "mints" else None).permit.to_json()
    doc["written_chains"] = [{"role": "corpus", "id": corpus_id_at(cfg.write_root), "root": str(cfg.write_root)}]
    doc["lease_seconds"] = 120
    source.write_text(json.dumps(doc))
    with sandbox_actor(source, doc, tmp_path, _ACTOR) as (endpoint, actor, conn, control):
        out, err = actor.communicate(b"go\n", timeout=90)
        assert actor.returncode == 0, err.decode()
        status, claim, bridge = json.loads(out)
        assert status[0] == 0 and "World status" in status[1], status
        if level == "coordination":
            assert claim[0] == 3 and json.loads(claim[2])["refusal"]["code"] == "permit-exceeded", claim
        else:
            assert claim[0] == 0 and "proposition:" in claim[1], claim
        assert bridge[0] == 0, bridge
        discovery, read, denied = [json.loads(line)["result"] for line in bridge[1].splitlines()]
        assert "status" in {tool["name"] for tool in discovery["tools"]}
        assert "World status" in read["content"][0]["text"]
        assert denied["isError"] and "permit-exceeded" in denied["content"][0]["text"]
        conn.sendall(wire({"type": "seal", "version": "control.v1"}))
        assert json.loads(control.readline())["type"] == "sealed"
        assert endpoint.wait(timeout=20) == 0


def _descendants(pid):
    """Walk only the fixture endpoint's process tree, including thread-owned children."""
    for children in Path(f"/proc/{pid}/task").glob("*/children"):
        try:
            pids = children.read_text().split()
        except (FileNotFoundError, ProcessLookupError):
            continue
        for child in map(int, pids):
            yield child, pid
            yield from _descendants(child)


def test_confined_workload_and_descendant_exit_with_endpoint(autonomy_source, launch_file, certified_work, tmp_path):
    import select
    import time
    from beliefs.confinement import host_prerequisites
    from helpers.world import build_belief_world, fixture_bundle, hold_fixture_dataset
    from science.config import configured_stores
    from science.loader import production_tree
    from science.run_endpoint.drain import open_pidfd, signal_pidfd

    reason = host_prerequisites()
    if reason:
        pytest.skip(f"confinement unavailable: {reason}")
    source, doc = launch_file
    work = certified_work / "workload"
    work.mkdir()
    cfg = build_belief_world(work)
    dataset = hold_fixture_dataset(cfg, "data.txt", b"x\n", "input")
    code, entry, targets = fixture_bundle(Path(doc["scratch_dir"]))
    # The rule waits for this idle child. The unique final argument distinguishes
    # the child from the workflow runner while observing only this endpoint's tree.
    marker = b"science-fixture-idle-child"
    snakefile = code.parent / entry
    snakefile.write_text(snakefile.read_text().replace("        pathlib.Path(input[0]).read_text()",
        "        import subprocess, sys\n"
        "        subprocess.run([sys.executable, '-I', '-c', 'import time; time.sleep(40)', "
        f"{marker.decode()!r}], check=True, env={{'HOME': os.getcwd(), 'PATH': os.defpath, "
        "'LD_LIBRARY_PATH': os.environ['LD_LIBRARY_PATH']})"))
    decl = next(d for d in production_tree() if d.name == "derive")
    doc["permit"] = {"kinds": sorted(set(decl.write_class.kinds)),
                     "act_families": sorted(set(decl.write_class.routes.values())), "ungoverned": False}
    store_id = next(k for k, v in configured_stores(cfg).items() if v == cfg.store_root)
    doc["written_chains"] = [{"role": "corpus", "id": corpus_id_at(cfg.write_root), "root": str(cfg.write_root)},
                             {"role": "store", "id": store_id, "root": str(cfg.store_root)}]
    doc.update(config=str(write_config_for(cfg)), lease_seconds=180)
    source.write_text(json.dumps(doc))
    inputs = dict(dataset=dataset, code=str(code), entrypoint=entry, targets=list(targets), title="idle fixture")
    program = """
import json, os, sys
from science.run_endpoint.handle import Handle
assert sys.stdin.buffer.readline() == b"go\\n"
Handle.from_env(os.environ).invoke("derive", json.loads(sys.argv[1]), invocation_id="idle-job")
"""
    with sandbox_actor(source, doc, tmp_path, program, json.dumps(inputs)) as (endpoint, actor, _, _):
        actor.stdin.write(b"go\n")
        actor.stdin.flush()
        deadline = time.monotonic() + 60
        while time.monotonic() < deadline:
            if actor.poll() is not None:
                pytest.fail(f"actor exited before idle job started: {actor.stderr.read().decode()}")
            for pid, parent in _descendants(endpoint.pid):
                try:
                    args = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
                except (FileNotFoundError, ProcessLookupError):
                    continue
                if marker in args:
                    break
            else:
                time.sleep(0.05)
                continue
            break
        else:
            pytest.fail("confined workload did not start its idle child")
        with ExitStack() as observers:
            fds = {}
            for observed in (parent, pid):
                fd = open_pidfd(observed)
                observers.callback(os.close, fd)
                fds[fd] = observed
            poll = select.poll()
            for fd in fds:
                poll.register(fd, select.POLLIN)
            try:
                assert not poll.poll(0)
                endpoint.kill()
                endpoint.wait(timeout=5)
                deadline = time.monotonic() + 5
                while fds and time.monotonic() < deadline:
                    for fd, _ in poll.poll(max(1, int(1000 * (deadline - time.monotonic())))):
                        poll.unregister(fd)
                        fds.pop(fd)
                assert not fds, f"confined processes survived endpoint death: {list(fds.values())}"
            finally:
                for fd in fds:
                    try:
                        signal_pidfd(fd)
                    except ProcessLookupError:
                        pass
