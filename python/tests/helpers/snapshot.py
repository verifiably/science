"""Build a test world once per process and restore it per test (spec
docs/specs/2026-10-02-world-fixture-snapshots-design.md). A world records its
absolute path in atoms' metadata and in run records, so it is restored to the
directory it was built in, never moved."""
import shutil
import stat
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from science.config import ScienceConfig

_LEAVES = (ScienceConfig, Path, str, int, bool, type(None))


@dataclass
class WorldSnapshot:
    work: Path
    image: Path
    value: object

    def restore(self) -> None:
        from beliefs.corpus import _forget_roots_under
        from beliefs.world.registry import _forget_worlds_under
        sockets = [p for p in self.work.rglob("*") if stat.S_ISSOCK(p.lstat().st_mode)]
        if sockets:
            raise RuntimeError(f"a live socket under the world blocks the restore: {sockets}")
        _forget_roots_under(self.work)
        _forget_worlds_under(self.work)
        shutil.rmtree(self.work)
        shutil.copytree(self.image, self.work, symlinks=True)


_SNAPSHOTS: dict[str, WorldSnapshot] = {}


def check_value(value: object, where: str = "value") -> None:
    """Data only: a snapshot outlives the files under it, so it must not hold a
    session, dispatcher or context (spec §2.4a). `ScienceConfig` is trusted
    whole; around it only containers of plain leaves pass."""
    if isinstance(value, _LEAVES):
        return
    if isinstance(value, (tuple, list)):
        for i, item in enumerate(value):
            check_value(item, f"{where}[{i}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{where} has a {type(key).__name__} key; a snapshot holds str-keyed dicts")
            check_value(item, f"{where}[{key!r}]")
        return
    raise TypeError(f"{where} is a {type(value).__name__}; a snapshot holds a config, refs and plain data")


def snapshot(work_base: Path, name: str, build: Callable[[Path], object]) -> WorldSnapshot:
    """The world `build` makes in `work_base / name`, built on this process's
    first call for `name`. The caller restores it before use."""
    snap = _SNAPSHOTS.get(name)
    if snap is None:
        work, image = work_base / name, work_base / f"{name}.image"
        work.mkdir()
        value = build(work)
        check_value(value)
        shutil.copytree(work, image, symlinks=True)
        snap = _SNAPSHOTS[name] = WorldSnapshot(work, image, value)
    return snap
