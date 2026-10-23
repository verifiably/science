from pathlib import Path

from science.config import FetchPolicy, load_config
from science.sharing import FetchRecord, Pin, SharingRegistry
from helpers.commons import refused, write_minimal_config

CID = "a" * 32
W = "c" * 32


def make_pin(state: str, corpus_id: str = CID) -> Pin:
    return Pin(corpus_id, "m1", "art1", W, "view1", None,
               FetchRecord("https://example.org/one", "2026-10-22T10:00:00Z", "ok"), state)


def registry_with(tmp_path: Path, state: str, *, corpus: bool = True) -> SharingRegistry:
    registry = SharingRegistry(tmp_path / "sharing")
    registry.write_pin(make_pin(state))
    if corpus:
        root = registry.root_for(CID)
        root.mkdir(parents=True)
        (root / "corpus.yaml").write_text(f"manifest_version: 2\ncorpus_id: {CID}\n")
    return registry


def test_sharing_keys_load_with_defaults(tmp_path):
    cfg = load_config(write_minimal_config(tmp_path))
    assert cfg.sharing_root is None
    assert cfg.accept == ()
    assert cfg.fetch == FetchPolicy("records-only", 0)
    cfg = load_config(write_minimal_config(
        tmp_path, sharing_root="sharing", accept=[W], fetch={"policy": "fetch", "max_bytes": 5}))
    assert cfg.sharing_root == (tmp_path / "sharing").resolve()
    assert cfg.accept == (W,)
    assert cfg.fetch == FetchPolicy("fetch", 5)


def test_accept_must_be_world_ids(tmp_path):
    refusal = refused(lambda: load_config(write_minimal_config(tmp_path, accept=["abc"])))
    assert refusal.code == "invalid-input" and "accept" in refusal.message


def test_fetch_table_validates_policy_and_bound(tmp_path):
    for bad in ({"policy": "maybe"}, {"policy": "fetch", "max_bytes": -1},
                {"policy": "fetch", "extra": 1}, {"max_bytes": 1}):
        refusal = refused(lambda: load_config(write_minimal_config(tmp_path, fetch=bad)))
        assert refusal.code == "invalid-input" and "fetch" in refusal.message


def test_mounted_registry_roots_join_corpus_roots(tmp_path):
    registry = registry_with(tmp_path, "mounted")
    cfg = load_config(write_minimal_config(tmp_path, sharing_root="sharing"))
    assert registry.root_for(CID).resolve() in cfg.world.corpus_roots


def test_a_fetched_pin_is_not_mounted(tmp_path):
    registry = registry_with(tmp_path, "fetched")
    cfg = load_config(write_minimal_config(tmp_path, sharing_root="sharing"))
    assert registry.root_for(CID).resolve() not in cfg.world.corpus_roots


def test_a_single_configured_root_stays_the_write_root_after_a_mount_joins(tmp_path):
    registry_with(tmp_path, "mounted")
    cfg = load_config(write_minimal_config(tmp_path, sharing_root="sharing"))
    assert cfg.write_root == (tmp_path / "corpora" / "one").resolve()
    assert len(cfg.world.corpus_roots) == 2


def test_a_mounted_root_missing_on_disk_refuses_naming_the_pin(tmp_path):
    registry = registry_with(tmp_path, "mounted", corpus=False)
    refusal = refused(lambda: load_config(write_minimal_config(tmp_path, sharing_root="sharing")))
    assert refusal.code == "invalid-input"
    assert CID in refusal.message and str(registry.root_for(CID)) in refusal.message


def test_a_malformed_registry_refuses_naming_the_entry(tmp_path):
    registry = registry_with(tmp_path, "mounted")
    (tmp_path / "sharing" / "pins" / "x.json").write_text("{not json")
    refusal = refused(lambda: load_config(write_minimal_config(tmp_path, sharing_root="sharing")))
    assert refusal.code == "invalid-input" and "pins/x.json" in refusal.message
