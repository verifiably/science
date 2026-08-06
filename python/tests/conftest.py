"""Shared fixtures.

The repository-relative paths below are the *only* place a test resolves one.
Nothing in `science` locates a contract for itself: the belief policy's §2.3
refuses an implicit selector on the ground that it would make belief follow the
checkout, and a contract loader that guessed its own path would have the same
defect one layer down.
"""

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def base_contract_path() -> Path:
    return REPO_ROOT / "contracts" / "science" / "CONTRACT.yaml"


@pytest.fixture(scope="session")
def fixtures_dir() -> Path:
    return REPO_ROOT / "fixtures"


@pytest.fixture(scope="session")
def testing_contract_path() -> Path:
    return REPO_ROOT / "fixtures" / "contracts" / "testing.yaml"


@pytest.fixture(scope="session")
def parity_fixture_path() -> Path:
    return REPO_ROOT / "fixtures" / "claim-identity-v1.json"


@pytest.fixture(scope="session")
def base_contract(base_contract_path):
    from science.contract import load_base_contract

    return load_base_contract(base_contract_path)


@pytest.fixture()
def testing_document(testing_contract_path) -> dict:
    import yaml

    return yaml.safe_load(testing_contract_path.read_text(encoding="utf-8"))
