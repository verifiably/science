"""Portable guards for the cut-5 acceptance launcher."""

import importlib.util
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "cut5_acceptance", Path(__file__).parents[1] / "tools" / "cut5_acceptance.py"
)
assert _SPEC is not None and _SPEC.loader is not None
cut5_acceptance = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(cut5_acceptance)


def test_missing_n2_module_refuses_before_certification_probe(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setattr(cut5_acceptance, "ACCEPTANCE", tmp_path)
    monkeypatch.setattr(cut5_acceptance, "work_directory", lambda: tmp_path)

    def unexpected_probe(_run: Path) -> str | None:
        raise AssertionError("certification probe ran without the required N2 module")

    monkeypatch.setattr(cut5_acceptance, "probe", unexpected_probe)

    assert cut5_acceptance.main([]) == 1
    assert "required acceptance module is missing" in capsys.readouterr().err
