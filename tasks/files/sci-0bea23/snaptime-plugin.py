import json, os, time
_out = os.environ["SNAP_OUT"]
def pytest_sessionstart(session):
    import helpers.snapshot as m
    orig = m.snapshot
    def timed(work_base, name, build):
        fresh = name not in m._SNAPSHOTS
        t = time.monotonic(); snap = orig(work_base, name, build); dt = time.monotonic() - t
        if fresh:
            with open(_out, "a") as f:
                f.write(json.dumps({"w": os.environ.get("PYTEST_XDIST_WORKER"), "name": name, "s": round(dt, 2)}) + "\n")
        return snap
    m.snapshot = timed
