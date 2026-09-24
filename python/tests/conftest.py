import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
# The main checkout, which a worktree's own root is not: a worktree under .worktrees/
# resolves onto a volume whose mount options fail atoms' durability allowlist, so the
# certified test root always lives beside the main checkout's .git.
MAIN_ROOT = Path(subprocess.run(
    ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
    cwd=REPO_ROOT, check=True, capture_output=True, text=True,
).stdout.strip()).parent


@pytest.fixture()
def certified_work():
    base = Path(os.environ.get("SCIENCE_TEST_ROOT", MAIN_ROOT / ".framework-test"))
    work = base / uuid.uuid4().hex
    work.mkdir(parents=True)
    try:
        yield work
    finally:
        shutil.rmtree(work, ignore_errors=True)  # metadata siblings live inside work
