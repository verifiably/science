"""Build a world once per process and restore it per test; derive each world
from its base image in the same absolute directory. See docs/development.md.
Engine metadata and run records bind that directory, so images never relocate."""
import shutil
import stat
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from science.config import ScienceConfig

_LEAVES = (ScienceConfig, Path, str, int, bool, type(None))


@dataclass(frozen=True, eq=False)
class Root:
    """A world `build(work)` makes from an empty `work_base / name`."""
    name: str
    build: Callable[[Path], object]


@dataclass(frozen=True, eq=False)
class Derived:
    """A world `step(work, value)` makes from its base's restored image, in its root's directory."""
    name: str
    base: "Root | Derived"
    step: Callable[[Path, object], object]


Declaration = Root | Derived


def _clear_tree(target: Path) -> None:
    """Remove `target`, evicting beliefs' per-process registries for it; a live socket under it refuses."""
    from beliefs.corpus import _forget_roots_under
    from beliefs.world.registry import _forget_worlds_under
    from helpers.world import short_socket
    sockets = [p for p in (*target.rglob("*"), short_socket(target))
               if p.exists() and stat.S_ISSOCK(p.lstat().st_mode)]
    if sockets:
        raise RuntimeError(f"a live socket under the world blocks the restore: {sockets}")
    _forget_roots_under(target)
    _forget_worlds_under(target)
    shutil.rmtree(target)


def restore_tree(image: Path, target: Path) -> None:
    """Replace `target` with a copy of `image`, evicting beliefs' per-process registries for it.
    Records nothing: construction, step-internal and live restores all come through here."""
    _clear_tree(target)
    shutil.copytree(image, target, symlinks=True)


@dataclass
class WorldSnapshot:
    work: Path
    image: Path
    value: object
    declaration: Declaration

    def restore(self) -> None:
        """The live restore: the world a test uses, recorded so no other world of its lineage replaces it."""
        _refuse_another_live_world(self.work, self.declaration)
        restore_tree(self.image, self.work)
        _LIVE[self.work] = self.declaration


_SNAPSHOTS: dict[str, WorldSnapshot] = {}
_ROOTS: dict[str, Root] = {}
_LIVE: dict[Path, Declaration] = {}


def clear_live() -> None:
    """Forget the live worlds: each test starts with none."""
    _LIVE.clear()


def _refuse_another_live_world(work: Path, declaration: Declaration) -> None:
    live = _LIVE.get(work)
    if live is not None and live is not declaration:
        raise RuntimeError(f"{live.name!r} is live in {work}; {declaration.name!r} would replace it "
                           "(one snapshot per lineage per test)")


def check_value(value: object, where: str = "value") -> None:
    """Data only: a snapshot outlives the files under it, so it must not hold a
    session, dispatcher or context. `ScienceConfig` is trusted
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


def copy_value(value: object) -> object:
    """A copy whose containers are new and whose immutable leaves are shared: `copy.deepcopy` cannot copy a
    `ScienceConfig`, whose compiled profile holds mapping proxies."""
    if isinstance(value, _LEAVES):
        return value
    kind = type(value)
    if kind is dict and isinstance(value, dict):
        return {key: copy_value(item) for key, item in value.items()}
    if kind is list and isinstance(value, list):
        return [copy_value(item) for item in value]
    if kind is tuple and isinstance(value, tuple):
        return tuple(copy_value(item) for item in value)
    raise TypeError(f"copy_value copies exact dicts, lists and tuples, not a {kind.__name__}")


def _root_of(declaration: Declaration) -> Root:
    while isinstance(declaration, Derived):
        declaration = declaration.base
    return declaration


def lineage_dir(work_base: Path, declaration: Declaration) -> Path:
    return work_base / _root_of(declaration).name


def _build_link(work_base: Path, declaration: Declaration) -> WorldSnapshot:
    """Build one link whose base is already built; record it only once its image is complete. An unrecorded
    link's directory or image is what a failed earlier attempt left, never a world in use, so it is removed and
    the link built again: one failed root build would otherwise fail every later request in its lineage."""
    work = lineage_dir(work_base, declaration)
    image = work_base / f"{declaration.name}.image"
    if image.exists():
        shutil.rmtree(image)
    if isinstance(declaration, Root):
        if work.exists():
            _clear_tree(work)
        work.mkdir()
        value = declaration.build(work)
    else:
        base = _SNAPSHOTS[declaration.base.name]
        restore_tree(base.image, work)
        value = declaration.step(work, copy_value(base.value))
    check_value(value)
    shutil.copytree(work, image, symlinks=True)
    snap = _SNAPSHOTS[declaration.name] = WorldSnapshot(work, image, value, declaration)
    return snap


def materialize(work_base: Path, declaration: Declaration) -> WorldSnapshot:
    """The world `declaration` makes, built on this process's first request along with every ancestor not yet
    built. A name is one declaration, the requested one's and every ancestor's alike. The caller restores it
    before use."""
    chain: list[Declaration] = []
    node: Declaration | None = declaration
    while node is not None:
        built = _SNAPSHOTS.get(node.name)
        if built is not None and built.declaration is not node:
            raise ValueError(f"snapshot {node.name!r} is built from another declaration")
        chain.append(node)
        node = node.base if isinstance(node, Derived) else None
    _refuse_another_live_world(lineage_dir(work_base, declaration), declaration)
    for link in reversed(chain):
        if link.name not in _SNAPSHOTS:
            _build_link(work_base, link)
    return _SNAPSHOTS[declaration.name]


def snapshot(work_base: Path, name: str, build: Callable[[Path], object]) -> WorldSnapshot:
    """The single-level root `build` makes in `work_base / name`. A name is one builder: another builder under it
    is refused. The caller restores it before use."""
    root = _ROOTS.setdefault(name, Root(name, build))
    if root.build is not build:
        raise ValueError(f"snapshot {name!r} is built by {root.build.__qualname__}, not {build.__qualname__}")
    return materialize(work_base, root)
