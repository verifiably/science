"""Public entry points select the actor transport before consulting host state."""
import json
from pathlib import Path

import pytest

from science import cli
from science.dispatch import Outcome
from science.run_endpoint.handle import Handle


@pytest.mark.parametrize(("env", "args", "reason"), [
    ({"VERIFIABLY_ENDPOINT": "/socket"}, ["status"], "handle-incomplete"),
    ({"VERIFIABLY_TOKEN_FILE": "/token"}, ["status"], "handle-incomplete"),
    ({"VERIFIABLY_ENDPOINT": "", "VERIFIABLY_TOKEN_FILE": ""}, ["status"], "handle-incomplete"),
    ({"VERIFIABLY_ENDPOINT": "/socket", "VERIFIABLY_TOKEN_FILE": "/token", "SCIENCE_CONFIG": ""},
     ["status"], "handle-incomplete"),
    ({"VERIFIABLY_ENDPOINT": "/socket", "VERIFIABLY_TOKEN_FILE": "/token"},
     ["heads", "--config", "/absent"], "handle-incomplete"),
    ({}, ["mcp", "bridge"], "handle-incomplete"),
])
def test_incomplete_handle_refuses_before_config(monkeypatch, capsys, env, args, reason):
    for key in ("SCIENCE_CONFIG", "VERIFIABLY_ENDPOINT", "VERIFIABLY_TOKEN_FILE"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(cli, "load_config", lambda *_: pytest.fail("read host config"))
    assert cli.main(args) == cli.EXIT_REFUSED
    assert json.loads(capsys.readouterr().err)["refusal"]["code"] == reason


@pytest.mark.parametrize("args", [["build"], ["serve"], ["mcp", "serve"], ["epoch"], ["adapters", "build"]])
def test_handle_refuses_framework_operations(monkeypatch, capsys, args):
    monkeypatch.delenv("SCIENCE_CONFIG", raising=False)
    monkeypatch.setenv("VERIFIABLY_ENDPOINT", "/socket")
    monkeypatch.setenv("VERIFIABLY_TOKEN_FILE", "/token")
    assert cli.main(args) == cli.EXIT_REFUSED
    assert json.loads(capsys.readouterr().err)["refusal"]["code"] == "handle-mode"


def test_handle_forwards_selected_continuation_before_config(monkeypatch, capsys):
    monkeypatch.delenv("SCIENCE_CONFIG", raising=False)
    monkeypatch.setenv("VERIFIABLY_ENDPOINT", "/socket")
    monkeypatch.setenv("VERIFIABLY_TOKEN_FILE", "/token")
    seen = []

    def invoke(self, name, inputs, **fields):
        seen.append((self, name, inputs, fields))
        return Outcome("continued\n", fields["invocation_id"])

    monkeypatch.setattr(Handle, "invoke", invoke)
    monkeypatch.setattr(cli, "load_config", lambda *_: pytest.fail("read host config"))
    assert cli.main(["project-show", "--project", "selected", "--continue", "cursor", "--invocation-id", "same"]) == 0
    assert seen == [(Handle(Path("/socket"), Path("/token")), "project-show", {},
                     {"project": "selected", "cursor": "cursor", "invocation_id": "same"})]
    assert capsys.readouterr().out == "continued\n"
