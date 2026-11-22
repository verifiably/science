"""Trusted launch inputs fail before a session can acquire claims."""
import json
import os
import socket
from pathlib import Path

import pytest

from helpers.world import write_cli_config
from science.config import corpus_id_at, load_config
from science.refusal import Refused


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


def test_open_report_matches_kernel_session_and_read_only_store(launch_file):
    from science.run_endpoint.launch import read_launch, open_run
    source, _ = launch_file
    launch = read_launch(source)
    opened = open_run(launch)
    try:
        report = opened.open_report()
        first = json.loads(Path(report["ledger_path"]).read_text().splitlines()[0])
        assert report["session_id"] == opened.session.session_id
        assert first["permit"] == json.loads(source.read_text())["permit"]
        assert opened.session.store_id is None
        assert report["basis_open"] == opened.basis.digest
    finally:
        opened.session.close()


@pytest.mark.parametrize("fault", ["lease", "timeout", "chain", "overlap", "mode", "occupied", "permit", "alias"])
def test_malformed_launch_has_no_session_or_listener(launch_file, fault):
    from science.run_endpoint.launch import read_launch
    source, doc = launch_file
    cfg = load_config(Path(doc["config"]))
    if fault == "lease":
        doc["lease_seconds"] = 9.9
    elif fault == "timeout":
        doc["seal_timeout_seconds"] = float("inf")
    elif fault == "chain":
        doc["written_chains"][0]["id"] = "wrong"
    elif fault == "overlap":
        doc["scratch_dir"] = doc["run_dir"]
    elif fault == "mode":
        Path(doc["token_file"]).chmod(0o644)
    elif fault == "occupied":
        Path(doc["socket"]).touch()
    elif fault == "permit":
        doc["permit"]["ungoverned"] = True
    elif fault == "alias":
        doc["control_socket"] = doc["socket"]
    source.write_text(json.dumps(doc))
    with pytest.raises(Refused):
        read_launch(source)
    assert not (cfg.operations_root / "sessions").exists()


def test_launch_and_control_examples_match_open(launch_file):
    from science.run_endpoint.control import wire
    from science.run_endpoint.launch import open_run, read_launch

    fixtures = Path(__file__).parents[1] / "fixtures" / "run_endpoint"
    source, actual = launch_file
    example = json.loads((fixtures / "launch.v1.json").read_bytes())
    assert set(actual) == set(example)
    assert actual["permit"] == example["permit"]
    opened = open_run(read_launch(source))
    try:
        report = opened.open_report()
        sample = json.loads((fixtures / "control.v1.jsonl").read_bytes().splitlines()[0])
        assert set(sample) == set(report)
        assert sample["version"] == report["version"] and sample["type"] == report["type"]
        assert Path(sample["ledger_path"]).name == Path(report["ledger_path"]).name
        assert wire(sample) == (fixtures / "control.v1.jsonl").read_bytes().splitlines(keepends=True)[0]
    finally:
        opened.session.close()
