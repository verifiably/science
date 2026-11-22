"""Private supervisor and actor runtime for endpoint tests."""
import json
import socket

import pytest

from helpers.world import write_cli_config
from science.config import corpus_id_at, load_config


@pytest.fixture
def launch_file(certified_work, tmp_path):
    config = write_cli_config(certified_work)
    cfg = load_config(config)
    run = tmp_path / "run"
    actor = tmp_path / "runtime"
    scratch = tmp_path / "scratch"
    for directory in (run, actor, scratch):
        directory.mkdir(mode=0o700)
    token = actor / "token"
    token.write_text("ab" * 32)
    token.chmod(0o600)
    control = socket.socket(socket.AF_UNIX)
    control.bind(str(run / "control"))
    control.listen(1)
    doc = {"version": "launch.v1", "config": str(config), "run_dir": str(run), "scratch_dir": str(scratch),
           "socket": str(actor / "sock"), "token_file": str(token), "control_socket": str(run / "control"),
           "permit": {"kinds": [], "act_families": [], "ungoverned": False},
           "written_chains": [{"role": "corpus", "id": corpus_id_at(cfg.write_root), "root": str(cfg.write_root)}]}
    source = run / "launch.json"
    source.write_text(json.dumps(doc))
    source.chmod(0o600)
    try:
        yield source, doc
    finally:
        control.close()


@pytest.fixture
def autonomy_source(monkeypatch):
    import os
    from pathlib import Path

    sibling = Path(__file__).resolve().parents[4] / "autonomy"
    root = Path(os.environ.get("SCIENCE_TEST_AUTONOMY_ROOT", sibling))
    package = root / "python/src"
    if not (package / "autonomy/closing.py").is_file():
        pytest.fail("Conformance tests require the pinned autonomy checkout in docs/development.md")
    monkeypatch.syspath_prepend(str(package))
    return root
