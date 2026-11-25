"""The payloads in the command reference mint, and the guide's walk runs as printed."""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from beliefs import stored
from beliefs.reservation import assignment_changes_of, assignment_head
from helpers.reservation import COMMANDS, write_payload
from helpers.research import research_rig
from helpers.world import build_fixture_world, build_fixture_world_with_contract, write_config_for
from science.config import ReadContext

DOCS = Path(__file__).resolve().parents[2] / "docs"


def _section(document: str, heading: str) -> str:
    text = (DOCS / document).read_text()
    level = heading.split(" ", 1)[0]
    body = text.split(f"\n{heading}\n", 1)[1]
    return re.split(rf"\n{level} ", body, maxsplit=1)[0]


def _blocks(section: str, language: str) -> list[str]:
    return re.findall(rf"^```{language}\n(.*?)^```$", section, re.MULTILINE | re.DOTALL)


def test_the_reference_payloads_mint_in_a_world_with_no_prerequisites(certified_work, tmp_path):
    event, assignment = (json.loads(block) for block in _blocks(
        _section("commands.md", "### Exposure and reservation payloads"), "json"))
    with research_rig(build_fixture_world(certified_work), COMMANDS) as (d, ctx):
        for command, document in (("exposure-event", event), ("reservation-assignment", assignment)):
            payload = write_payload(tmp_path, document["facet"], title=document["title"])
            assert json.loads(Path(payload).read_text()) == document
            assert f"[{command}] {command}:" in d.invoke(command, {"payload": payload}).text


def test_the_guides_walk_runs_as_printed(certified_work, short_tmp, tmp_path):
    from science.config import load_config
    from science.serve import serve

    (script,) = _blocks(_section("guide.md", "## Recording what was seen and what is held back"), "sh")
    cfg = build_fixture_world_with_contract(certified_work)
    config = write_config_for(cfg, service_socket=short_tmp / "service.sock")
    loaded = load_config(config)
    tools, home, cwd = (tmp_path / name for name in ("bin", "home", "cwd"))
    for directory in (tools, home, cwd):
        directory.mkdir()
    shim = tools / "science"
    shim.write_text(f"#!/bin/sh\nexec {shlex.quote(sys.executable)} -m science.cli \"$@\"\n")
    shim.chmod(0o755)
    environment = {"PATH": f"{tools}:{os.environ['PATH']}", "HOME": str(home), "PYTHONDONTWRITEBYTECODE": "1",
                   "SCIENCE_CONFIG": str(config)}
    server = serve(loaded, loaded.service_socket)
    runner = threading.Thread(target=server.serve_forever)
    runner.start()
    try:
        walked = subprocess.run(["bash", "-euo", "pipefail", "-c", script], cwd=cwd, env=environment, text=True,
                                capture_output=True, timeout=120)
    finally:
        server.shutdown()
        runner.join()
        server.server_close()
    assert walked.returncode == 0, walked.stderr
    view = ReadContext.open(cfg).write_view()
    events = [n for n in view.iter_stored() if n.kind == "exposure-event"]
    head = assignment_head(view, "epochs")
    assert len(events) == 3 and head.predecessor is not None
    (change,) = assignment_changes_of(view, head.id)
    assert change.suspended and head.flagged == ()
    (unconsidered,) = {n.id for n in events} - set(head.events)
    # The walk ends with the statement's check, whose last block is the second look, in an epoch now open.
    assert walked.stdout.rstrip().splitlines()[-10:-7] == [f"{unconsidered}:", "  whose: program", "  falls: open"]
    assert sorted(path.name for path in (cwd / "reservation").iterdir()) == ["epochs.json", "epochs.md"]
    assert stored.exposure_event_value(view.get(unconsidered)).channel == "read"
