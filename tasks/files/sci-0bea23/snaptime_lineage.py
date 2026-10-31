"""Log each snapshot link build (helpers.snapshot._build_link): one JSON line per link with its own seconds.
Run: SNAP_OUT=<file> PYTHONPATH=<this dir> just test-one tests -p snaptime_lineage -n auto --dist worksteal"""
import json, os, time
_out = os.environ["SNAP_OUT"]
def pytest_sessionstart(session):
    import helpers.snapshot as m
    orig = m._build_link
    def timed(work_base, declaration):
        t = time.monotonic(); snap = orig(work_base, declaration); dt = time.monotonic() - t
        with open(_out, "a") as f:
            f.write(json.dumps({"w": os.environ.get("PYTEST_XDIST_WORKER"), "name": declaration.name, "s": round(dt, 2)}) + "\n")
        return snap
    m._build_link = timed
