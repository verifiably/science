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
