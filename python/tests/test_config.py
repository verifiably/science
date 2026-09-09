from pathlib import Path

import pytest

from science.config import load_config, resolve_config_path
from science.refusal import Refused


WORLD_ID = "deadbeef" * 4


def write_config(
    tmp_path: Path,
    world_id: str = WORLD_ID,
    extra: str = "",
    operations_root: str | Path | None = None,
    domains: str = "[]",
) -> Path:
    world_root = tmp_path / "world"
    ops = tmp_path / "ops" if operations_root is None else operations_root
    corpus = tmp_path / "corpora" / "one"
    cfg = tmp_path / "science.toml"
    cfg.write_text(f'''\
world_root = "{world_root}"
world_id = "{world_id}"
corpus_roots = ["{corpus}"]
operations_root = "{ops}"
domains = {domains}
{extra}''')
    return cfg


def assert_invalid_config(path: Path) -> None:
    with pytest.raises(Refused) as caught:
        load_config(path)
    assert caught.value.refusal.code == "invalid-input"


def test_load_config_builds_beliefs_worldconfig(tmp_path):
    cfg = load_config(write_config(tmp_path))
    assert cfg.world.world_id == WORLD_ID
    assert cfg.world.world_root == (tmp_path / "world").resolve()
    assert cfg.operations_root == tmp_path / "ops"
    assert cfg.world.corpus_roots == ((tmp_path / "corpora" / "one").resolve(),)


def test_load_config_resolves_relative_operations_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = load_config(write_config(tmp_path, operations_root="operations"))
    assert cfg.operations_root == tmp_path / "operations"


def test_domains_compile_the_profile_the_session_binds(tmp_path):
    from beliefs.profile import shipped_base_contract

    cfg = load_config(write_config(tmp_path, domains='["biology"]'))
    assert cfg.profile.base_contract_identity == shipped_base_contract().content_identity
    assert set(cfg.profile.activated_contracts) == {"biology"}
    # The operators the pack contributes are what activation is *for*.
    assert any(name.startswith("biology/") for name in cfg.profile.operators)


def test_empty_domains_compile_the_shipped_base_alone(tmp_path):
    cfg = load_config(write_config(tmp_path, domains="[]"))
    assert dict(cfg.profile.activated_contracts) == {}


def test_unshipped_domain_namespace_is_refused_at_load(tmp_path):
    """Not at the first write: a launcher misconfiguration fails at startup."""
    assert_invalid_config(write_config(tmp_path, domains='["no-such-pack"]'))


def test_missing_or_unknown_fields_are_refused(tmp_path):
    missing = tmp_path / "missing.toml"
    missing.write_text('world_root = "/x"\n')
    assert_invalid_config(missing)
    assert_invalid_config(write_config(tmp_path, extra="stray = 1\n"))
    assert_invalid_config(write_config(tmp_path, extra="[untrusted]\nvalue = 1\n"))


_TAIL = 'domains = []\n'


@pytest.mark.parametrize("contents", [
    f'world_root = 3\nworld_id = "{WORLD_ID}"\ncorpus_roots = ["/x"]\noperations_root = "/x"\n' + _TAIL,
    f'world_root = "/x"\nworld_id = "{WORLD_ID}"\ncorpus_roots = "not-a-list"\noperations_root = "/x"\n' + _TAIL,
    f'world_root = "/x"\nworld_id = "{WORLD_ID}"\ncorpus_roots = ["/x", 3]\noperations_root = "/x"\n' + _TAIL,
    f'world_root = "/x"\nworld_id = "{WORLD_ID}"\ncorpus_roots = ["/x"]\noperations_root = false\n' + _TAIL,
    f'world_root = "/x"\nworld_id = "{WORLD_ID}"\ncorpus_roots = ["/x"]\noperations_root = "/x"\ndomains = "biology"\n',
    f'world_root = "/x"\nworld_id = "{WORLD_ID}"\ncorpus_roots = ["/x"]\noperations_root = "/x"\ndomains = ["biology", 3]\n',
    'this = is not [ toml',
])
def test_noncanonical_or_malformed_toml_is_refused(tmp_path, contents):
    path = tmp_path / "bad.toml"
    path.write_text(contents)
    assert_invalid_config(path)


@pytest.mark.parametrize("world_id", ["w-test", WORLD_ID.upper()])
def test_noncanonical_world_id_is_refused(tmp_path, world_id):
    assert_invalid_config(write_config(tmp_path, world_id=world_id))


def test_missing_config_file_is_refused(tmp_path):
    assert_invalid_config(tmp_path / "missing.toml")


def test_resolution_order(tmp_path):
    cfg = write_config(tmp_path)
    assert resolve_config_path(str(cfg), {"SCIENCE_CONFIG": "/ignored"}) == cfg
    assert resolve_config_path(None, {"SCIENCE_CONFIG": str(cfg)}) == cfg
    with pytest.raises(Refused) as caught:
        resolve_config_path(None, {})
    assert caught.value.refusal.code == "invalid-input"
