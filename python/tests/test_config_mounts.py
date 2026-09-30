"""Spec §6: `write_root` and `read_contracts` (coordination part 3)."""
import shutil
from pathlib import Path

import pytest

from helpers.world import DOMAINS, archive_contract_document, build_fixture_world_with_contract
from science.config import load_config
from science.refusal import Refused


def _config(work: Path, *, corpus_roots=("corpus",), extra: str = "") -> Path:
    """The contract world's launcher TOML, every path relative to the file."""
    cfg = build_fixture_world_with_contract(work)
    path = work / "science.toml"
    path.write_text(
        'world_root = "world"\n'
        f'world_id = "{cfg.world.world_id}"\n'
        f"corpus_roots = {list(corpus_roots)!r}\n"
        'operations_root = "ops"\n'
        f"domains = {list(DOMAINS)!r}\n"
        'contracts = ["testing.yaml"]\n'
        'store_root = "store"\n'
        "coordination = 2\n" + extra
    )
    return path


def _refused(path: Path) -> str:
    with pytest.raises(Refused) as caught:
        load_config(path)
    assert caught.value.refusal.code == "invalid-input"
    return caught.value.refusal.message


def test_one_root_is_the_write_root_without_the_key(certified_work):
    assert load_config(_config(certified_work)).write_root == (certified_work / "corpus").resolve()


def test_two_roots_need_a_write_root(certified_work):
    message = _refused(_config(certified_work, corpus_roots=("corpus", "archive")))
    assert "write_root" in message and "2 corpus_roots" in message


def test_a_write_root_outside_corpus_roots_refuses(certified_work):
    assert "not one of corpus_roots" in _refused(_config(certified_work, extra='write_root = "elsewhere"\n'))


def test_write_root_must_be_a_string(certified_work):
    assert "write_root must be a string" in _refused(_config(certified_work, extra="write_root = 3\n"))


def test_a_relative_write_root_resolves_against_the_file(certified_work, tmp_path, monkeypatch):
    path = _config(certified_work, corpus_roots=("corpus", "archive"), extra='write_root = "corpus"\n')
    monkeypatch.chdir(tmp_path)
    assert load_config(path).write_root == (certified_work / "corpus").resolve()


def test_read_contracts_are_available_and_never_activated(certified_work):
    path = _config(certified_work, extra='read_contracts = ["archive.yaml"]\n')
    archive_contract_document(certified_work)
    cfg = load_config(path)
    assert "archive" not in cfg.profile.activated_contracts
    assert [contract.namespace for contract in cfg.available_contracts] == ["testing", "archive"]
    assert [plan.namespace for plan in cfg.plans] == ["testing"]


def test_read_contracts_must_be_a_list_of_strings(certified_work):
    message = _refused(_config(certified_work, extra='read_contracts = "archive.yaml"\n'))
    assert "read_contracts must be a list of strings" in message


def test_a_document_in_both_lists_refuses(certified_work):
    message = _refused(_config(certified_work, extra='read_contracts = ["testing.yaml"]\n'))
    assert "both contracts and read_contracts" in message and "testing" in message


def test_one_document_under_two_paths_is_still_in_both_lists(certified_work):
    path = _config(certified_work, extra='read_contracts = ["copy.yaml"]\n')
    shutil.copy(certified_work / "testing.yaml", certified_work / "copy.yaml")
    assert "both contracts and read_contracts" in _refused(path)
