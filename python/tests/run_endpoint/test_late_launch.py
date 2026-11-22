"""Shutdown discovers a child started by a worker after its first sweep."""
import json
import os
import signal
import subprocess
import sys

import pytest

from science.run_endpoint.drain import drain_workers


def test_real_drain_waits_for_the_late_child_and_worker(tmp_path):
    # Exercise process-wide child enumeration inside its own fixture process.
    # The worker closes only after it has reaped its one disposable child.
    program = """
import json, os, subprocess, sys, threading, time
from science.run_endpoint.drain import children, drain_workers, sweep_children

start, running, closed = threading.Event(), threading.Event(), threading.Event()
result, sweeps = [], []
def work():
    if not start.wait(4):
        return
    with subprocess.Popen([sys.executable, "-I", "-c", "import sys; sys.stdin.buffer.read(1)"],
                          stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          env={"PATH": os.defpath, "HOME": sys.argv[1]}) as child:
        running.set()
        try:
            result.append(child.wait(timeout=8))
        finally:
            child.stdin.close()
    closed.set()
def sweep():
    sweeps.append(len(children()))
    sweep_children()
    if len(sweeps) == 1:
        start.set()
        assert running.wait(4)
worker = threading.Thread(target=work)
worker.start()
try:
    drained = drain_workers(closed.is_set, sweep, time.monotonic()+5, clock=time.monotonic, wait=closed.wait)
finally:
    start.set()
    worker.join(10)
print(json.dumps([drained, sweeps, result, worker.is_alive()]))
"""
    completed = subprocess.run([sys.executable, "-I", "-c", program, str(tmp_path)], input=b"",
                               env={"PATH": os.defpath, "HOME": str(tmp_path)}, capture_output=True, timeout=20)
    assert completed.returncode == 0, completed.stderr.decode()
    drained, sweeps, result, alive = json.loads(completed.stdout)
    assert drained and not alive
    assert sweeps[0] == 0 and any(count == 1 for count in sweeps[1:])
    assert result == [-signal.SIGKILL]


@pytest.mark.parametrize("repeat", [True, False])
def test_late_launch_model_controls_for_the_first_empty_sweep(repeat):
    now = 0.0
    launched, closed = False, False
    sweeps = []

    def sweep():
        nonlocal closed
        if repeat or not sweeps:
            closed = launched
        sweeps.append(now)

    def advance(duration):
        nonlocal now, launched
        now += duration
        launched = True

    assert drain_workers(lambda: closed, sweep, 0.2, clock=lambda: now, wait=advance) == repeat
    assert now == pytest.approx(0.05 if repeat else 0.2)
