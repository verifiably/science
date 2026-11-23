from dataclasses import replace

import pytest

from science.acquisition.bounds import AcquisitionBounds
from science.acquisition.staging import stage_tree
from science.refusal import Refused


def test_tree_staging_keeps_bytes_and_honors_selection(tmp_path):
    root = tmp_path / "source"
    root.mkdir()
    (root / "b").write_bytes(b"b")
    (root / "dir").mkdir()
    (root / "dir" / "a").write_bytes(b"aa")
    stage = tmp_path / "private"
    stage.mkdir()
    tree, members = stage_tree(root, stage, AcquisitionBounds(), selected=["dir/a"])
    (root / "dir" / "a").write_bytes(b"bad")
    assert [m.path for m in tree.members] == ["dir/a"]
    assert members["dir/a"].read_bytes() == b"aa"


@pytest.mark.parametrize("kind", ["extra-bytes", "symlink", "fifo", "empty", "duplicate", "escape"])
def test_unsealable_trees_refuse_without_reading_special_files(tmp_path, kind):
    root = tmp_path / "source"
    root.mkdir()
    stage = tmp_path / "private"
    stage.mkdir()
    bounds = replace(AcquisitionBounds(), max_response_bytes=1)
    if kind == "extra-bytes":
        (root / "a").write_bytes(b"ab")
    if kind == "symlink":
        (root / "a").symlink_to(stage, target_is_directory=True)
    if kind == "fifo":
        import os
        os.mkfifo(root / "a")
    selected = ["a", "a"] if kind == "duplicate" else ["../escape"] if kind == "escape" else None
    with pytest.raises(Refused):
        stage_tree(root, stage, bounds, selected=selected)


def test_evidence_copy_refuses_growth_at_limit(tmp_path):
    from io import BytesIO
    from science.acquisition.staging import copy_regular

    source = tmp_path / "original"
    source.write_bytes(b"initial")

    class GrowingCopy(BytesIO):
        def write(self, chunk):
            with source.open("ab") as handle:
                handle.write(b"growth")
            return super().write(chunk)

    output = GrowingCopy()
    with pytest.raises(Refused, match="grew"):
        copy_regular(source, output, max_bytes=7)
    assert output.getvalue() == b"initial"
