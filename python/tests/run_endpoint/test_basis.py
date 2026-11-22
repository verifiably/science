"""Derivation context is measured at open and again at seal."""
from dataclasses import replace

import pytest

from helpers.world import build_fixture_world


def test_open_requires_every_member_and_seal_retains_an_absence_marker(certified_work, tmp_path, monkeypatch):
    from science.run_endpoint import basis
    from science.refusal import Refused

    config = build_fixture_world(certified_work)
    module = tmp_path / "rule.py"
    monkeypatch.setattr(basis, "_installed_files", lambda: (("verifiably-beliefs", "rule.py", module),))
    with pytest.raises(Refused, match="basis"):
        basis.open_basis(config)
    module.write_bytes(b"original")
    opened = basis.open_basis(config)
    assert basis.seal_basis(opened, config) == opened.digest
    module.write_bytes(b"changed!")
    changed = basis.seal_basis(opened, config)
    module.unlink()
    missing = basis.seal_basis(opened, config)
    assert None not in (opened.digest, changed, missing)
    assert len({opened.digest, changed, missing}) == 3
    module.mkdir()
    assert basis.seal_basis(opened, config) is None


def test_installed_closure_is_stable_across_lazy_imports(certified_work):
    from science.run_endpoint.basis import open_basis, seal_basis
    cfg = build_fixture_world(certified_work)
    opened = open_basis(cfg)
    assert {dist for dist, _, _ in opened.files} == {
        "verifiably-science", "verifiably-beliefs", "verifiably-atoms", "verifiably-nodes",
    }
    import science.mcp
    assert science.mcp.__file__
    assert seal_basis(opened, cfg) == opened.digest


def test_remeasures_a_changed_profile_at_seal(certified_work):
    from helpers.world import PROFILE_V3, PROFILE
    from science.run_endpoint.basis import open_basis, seal_basis
    cfg = build_fixture_world(certified_work)
    opened = open_basis(cfg)
    changed = PROFILE if cfg.profile == PROFILE_V3 else PROFILE_V3
    assert seal_basis(opened, replace(cfg, profile=changed)) not in (None, opened.digest)


def test_wheel_members_follow_record_and_editable_members_follow_package_trees(tmp_path):
    import csv
    from importlib.metadata import PathDistribution
    from science.run_endpoint.basis import _members

    root = tmp_path / "wheel"
    info = root / "example-1.dist-info"
    info.mkdir(parents=True)
    (info / "METADATA").write_text("Name: example\nVersion: 1\n")
    pkg = root / "example"
    pkg.mkdir()
    (pkg / "rules.json").write_text("{}")
    with (info / "RECORD").open("w", newline="") as stream:
        writer = csv.writer(stream)
        for name in ("example/rules.json", "example/__pycache__/a.pyc", "example-1.dist-info/RECORD"):
            writer.writerow((name, "", ""))
    dist = PathDistribution(info)
    assert {n for n, _ in _members(dist)} == {"example/rules.json", "example-1.dist-info/RECORD"}
    import json
    (info / "direct_url.json").write_text(json.dumps({"url": root.as_uri(), "dir_info": {"editable": True}}))
    (root / "pyproject.toml").write_text('[tool.hatch.build.targets.wheel]\npackages = ["example"]')
    (pkg / "__pycache__").mkdir()
    (pkg / "__pycache__/a.pyc").write_bytes(b"cache")
    assert list(_members(dist)) == [("example/rules.json", pkg / "rules.json")]


def test_basis_tracks_provider_confirmation_and_verifiers_across_an_ordinary_mint(certified_work):
    from helpers.world import add_one_more_record
    from science.run_endpoint.basis import open_basis, seal_basis
    from science.sharing import FetchRecord, Pin, PinSource, ProviderBinding, SharingRegistry

    config = replace(build_fixture_world(certified_work), sharing_root=certified_work / "sharing")
    registry = SharingRegistry(config.sharing_root)
    world, corpus, location = "d" * 32, "c" * 32, "https://example.test/pin"
    binding = ProviderBinding(world, (location,), "2026-11-22T00:00:00Z", False)
    registry.write_pin(Pin(corpus, "marker", "artifact", world, "view:x", PinSource("provider", location),
                           FetchRecord(location, binding.bound_since, "validated"), "mounted"))
    registry.write_binding(binding)
    opened = open_basis(config)
    add_one_more_record(config)
    assert seal_basis(opened, config) == opened.digest
    assert seal_basis(opened, replace(config, accept=(world,))) not in (None, opened.digest)
    registry.write_binding(replace(binding, confirmed=True))
    assert seal_basis(opened, config) not in (None, opened.digest)
    (config.sharing_root / "providers" / f"{world}.json").write_text("{")
    assert seal_basis(opened, config) is None


def test_registry_enumeration_failure_refuses_open_and_preserves_null_seal(certified_work, monkeypatch):
    import os
    from science.refusal import Refused
    from science.run_endpoint.basis import open_basis, seal_basis

    cfg = replace(build_fixture_world(certified_work), sharing_root=certified_work / "sharing")
    folder = cfg.sharing_root / "providers"
    opened = open_basis(cfg)  # No optional registry directories yet.
    folder.mkdir(parents=True)
    scan = os.scandir

    def denied(path):
        if path == folder or path == str(folder):
            raise PermissionError("cannot enumerate providers")
        return scan(path)

    monkeypatch.setattr(os, "scandir", denied)
    assert seal_basis(opened, cfg) is None
    with pytest.raises(Refused, match="enumerate providers"):
        open_basis(cfg)
