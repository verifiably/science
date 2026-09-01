from pathlib import Path

import pytest

from science.config import load_config, resolve_config_path
from science.refusal import Refused


WORLD_ID = "deadbeef" * 4


def write_config(tmp_path: Path, world_id: str = WORLD_ID, extra: str = "") -> Path:
    world_root = tmp_path / "world"
    ops = tmp_path / "ops"
    corpus = tmp_path / "corpora" / "one"
    cfg = tmp_path / "science.toml"
    cfg.write_text(f'''\
world_root = "{world_root}"
world_id = "{world_id}"
corpus_roots = ["{corpus}"]
operations_root = "{ops}"
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


def test_missing_or_unknown_fields_are_refused(tmp_path):
    missing = tmp_path / "missing.toml"
    missing.write_text('world_root = "/x"\n')
    assert_invalid_config(missing)
    assert_invalid_config(write_config(tmp_path, extra="stray = 1\n"))
    assert_invalid_config(write_config(tmp_path, extra="[untrusted]\nvalue = 1\n"))


@pytest.mark.parametrize("contents", [
    f'world_root = 3\nworld_id = "{WORLD_ID}"\ncorpus_roots = ["/x"]\noperations_root = "/x"\n',
    f'world_root = "/x"\nworld_id = "{WORLD_ID}"\ncorpus_roots = "not-a-list"\noperations_root = "/x"\n',
    f'world_root = "/x"\nworld_id = "{WORLD_ID}"\ncorpus_roots = ["/x", 3]\noperations_root = "/x"\n',
    f'world_root = "/x"\nworld_id = "{WORLD_ID}"\ncorpus_roots = ["/x"]\noperations_root = false\n',
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
