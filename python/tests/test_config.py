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
    contracts: str | None = "[]",
    store_root: str | Path | None = "",
) -> Path:
    world_root = tmp_path / "world"
    ops = tmp_path / "ops" if operations_root is None else operations_root
    corpus = tmp_path / "corpora" / "one"
    cfg = tmp_path / "science.toml"
    store = tmp_path / "store" if store_root == "" else store_root
    lines = [
        f'world_root = "{world_root}"',
        f'world_id = "{world_id}"',
        f'corpus_roots = ["{corpus}"]',
        f'operations_root = "{ops}"',
        f"domains = {domains}",
    ]
    if contracts is not None:
        lines.append(f"contracts = {contracts}")
    if store is not None:
        lines.append(f'store_root = "{store}"')
    cfg.write_text("\n".join(lines) + "\n" + extra)
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


def test_relative_paths_resolve_against_the_config_file(tmp_path, monkeypatch):
    """Not the working directory: one file names one world from anywhere (P1)."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    cfg = load_config(write_config(tmp_path, operations_root="operations", store_root="store"))
    assert cfg.operations_root == (tmp_path / "operations").resolve()
    assert cfg.store_root == (tmp_path / "store").resolve()


def test_service_socket_defaults_beside_the_operations_root(tmp_path):
    cfg = load_config(write_config(tmp_path))
    assert cfg.service_socket == tmp_path / "ops" / "service.sock"


def test_service_socket_is_configurable_and_resolved(tmp_path, monkeypatch):
    """The AF_UNIX path limit is 107 bytes and a worktree's operations root
    already exceeds it, so the operator can name a short path; a relative one
    resolves against the configuration file like every other path."""
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    cfg = load_config(write_config(tmp_path, extra='service_socket = "run/s.sock"\n'))
    assert cfg.service_socket == (tmp_path / "run" / "s.sock").resolve()


def test_world_and_corpus_roots_resolve_against_the_config_file(tmp_path, monkeypatch):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    path = tmp_path / "science.toml"
    path.write_text(
        f'world_root = "world"\nworld_id = "{WORLD_ID}"\ncorpus_roots = ["corpora/one"]\n'
        'operations_root = "ops"\ndomains = []\ncontracts = []\nstore_root = "store"\n'
    )
    cfg = load_config(path)
    assert cfg.world.world_root == (tmp_path / "world").resolve()
    assert cfg.world.corpus_roots == ((tmp_path / "corpora" / "one").resolve(),)


def test_service_socket_must_be_a_string(tmp_path):
    assert_invalid_config(write_config(tmp_path, extra="service_socket = 3\n"))


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


_TAIL = 'domains = []\ncontracts = []\nstore_root = "/x"\n'


@pytest.mark.parametrize("contents", [
    f'world_root = 3\nworld_id = "{WORLD_ID}"\ncorpus_roots = ["/x"]\noperations_root = "/x"\n' + _TAIL,
    f'world_root = "/x"\nworld_id = "{WORLD_ID}"\ncorpus_roots = "not-a-list"\noperations_root = "/x"\n' + _TAIL,
    f'world_root = "/x"\nworld_id = "{WORLD_ID}"\ncorpus_roots = ["/x", 3]\noperations_root = "/x"\n' + _TAIL,
    f'world_root = "/x"\nworld_id = "{WORLD_ID}"\ncorpus_roots = ["/x"]\noperations_root = false\n' + _TAIL,
    f'world_root = "/x"\nworld_id = "{WORLD_ID}"\ncorpus_roots = ["/x"]\noperations_root = "/x"\ndomains = "biology"\ncontracts = []\nstore_root = "/x"\n',
    f'world_root = "/x"\nworld_id = "{WORLD_ID}"\ncorpus_roots = ["/x"]\noperations_root = "/x"\ndomains = ["biology", 3]\ncontracts = []\nstore_root = "/x"\n',
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


def test_contracts_and_store_root_are_required_keys(tmp_path):
    assert_invalid_config(write_config(tmp_path, contracts=None, store_root=None))


def test_contracts_compile_into_the_profile(tmp_path):
    from test_contracts import DOCUMENT

    doc = tmp_path / "testing.yaml"
    doc.write_text(DOCUMENT % ("0" * 64))
    cfg = load_config(write_config(tmp_path, contracts=f'["{doc}"]'))
    assert "testing" in cfg.profile.activated_contracts
    assert cfg.store_root == tmp_path / "store"
    (plan,) = cfg.plans
    assert plan.operator_for("affects", "concept", "concept") == "testing/affects-concept-concept"


def test_store_root_resolves_like_operations_root(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    cfg = load_config(write_config(tmp_path, store_root="held"))
    assert cfg.store_root == tmp_path / "held"


def test_unparseable_contract_document_refuses_at_load(tmp_path):
    doc = tmp_path / "bad.yaml"
    doc.write_text("contract: 3\n")
    assert_invalid_config(write_config(tmp_path, contracts=f'["{doc}"]'))


def test_resolution_order(tmp_path):
    cfg = write_config(tmp_path)
    assert resolve_config_path(str(cfg), {"SCIENCE_CONFIG": "/ignored"}) == cfg
    assert resolve_config_path(None, {"SCIENCE_CONFIG": str(cfg)}) == cfg
    with pytest.raises(Refused) as caught:
        resolve_config_path(None, {})
    assert caught.value.refusal.code == "invalid-input"


def test_nothing_is_discovered_from_the_working_directory(tmp_path, monkeypatch):
    """Design 2026-09-23 §5.2, guarantee P1: the launcher takes the world from
    --config or SCIENCE_CONFIG only. A predecessor manifest, a workspace
    config and a stray corpus manifest in cwd change nothing.

    Scope: the configuration here names absolute paths. Relative paths
    *inside* a config file still resolve against the process's cwd
    (test_load_config_resolves_relative_operations_root pins that), so the
    same file can name different worlds from different directories. That
    is a known P1 gap, tracked on sci-c5528e; this test does not cover it."""
    explicit_dir = tmp_path / "explicit"
    explicit_dir.mkdir()
    cfg = write_config(explicit_dir)

    workdir = tmp_path / "workdir"
    workdir.mkdir()
    decoy_corpus = tmp_path / "decoy-corpus"
    decoy_corpus.mkdir()
    (workdir / "science.yaml").write_text(
        f"name: decoy\nid: decoy\nlayout_version: 3\npeers:\n- id: other\n  path: {decoy_corpus}\n"
    )
    (workdir / "science.toml").write_text(
        f'world_root = "{tmp_path / "decoy-world"}"\nworld_id = "{"cafebabe" * 4}"\n'
        f'corpus_roots = ["{decoy_corpus}"]\noperations_root = "{tmp_path / "decoy-ops"}"\ndomains = []\n'
    )
    (workdir / "corpus.yaml").write_text("manifest_version: 2\ncorpus_id: " + "0" * 32 + "\n")
    monkeypatch.chdir(workdir)

    # --config wins and names exactly the explicit world.
    loaded = load_config(resolve_config_path(str(cfg), {}))
    assert loaded.world.world_root == explicit_dir / "world"
    assert loaded.world.corpus_roots == (explicit_dir / "corpora" / "one",)
    assert decoy_corpus not in loaded.world.corpus_roots

    # SCIENCE_CONFIG wins the same way.
    loaded = load_config(resolve_config_path(None, {"SCIENCE_CONFIG": str(cfg)}))
    assert loaded.world.corpus_roots == (explicit_dir / "corpora" / "one",)

    # With neither, cwd's files do not rescue the launcher: it refuses.
    with pytest.raises(Refused) as caught:
        resolve_config_path(None, {})
    assert caught.value.refusal.code == "invalid-input"


def test_relative_science_config_resolves_against_cwd_and_is_not_discovery(tmp_path, monkeypatch):
    """A relative SCIENCE_CONFIG is a path the person gave, resolved where the
    process runs; that is ordinary path resolution, not discovery, and it is
    named here so a wrong-world refusal is not read as one."""
    write_config(tmp_path)  # writes tmp_path / "science.toml"
    monkeypatch.chdir(tmp_path)
    assert resolve_config_path(None, {"SCIENCE_CONFIG": "science.toml"}) == Path("science.toml")
    loaded = load_config(resolve_config_path(None, {"SCIENCE_CONFIG": "science.toml"}))
    assert loaded.world.corpus_roots == (tmp_path / "corpora" / "one",)
