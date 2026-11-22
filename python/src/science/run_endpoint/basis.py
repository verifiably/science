"""Measure the fixed installed file set and the current belief bindings."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import stat
import tomllib
from urllib.parse import unquote, urlsplit

from beliefs.errors import ScienceError
from beliefs.root import AtomsError
from beliefs.world.registry import load_manifest
from nodes.core.errors import NodesError
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from science import acceptance, closure
from science.config import ReadContext, ScienceConfig, load_config, mount_profiles
from science.refusal import Refusal, Refused
from science.sharing import SharingRegistryMalformed

_File = tuple[str, str, Path]


@dataclass(frozen=True)
class BasisInventory:
    files: tuple[_File, ...]
    digest: str


def _raise(error):
    raise error


def _editable_members(root):
    metadata_path = root / "pyproject.toml"
    with metadata_path.open("rb") as stream:
        projects = tomllib.load(stream)["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"]
    for package in sorted(projects):
        base = root / package
        if not base.is_dir():
            raise ValueError(f"missing editable package {package}")
        for directory, dirs, names in os.walk(base, onerror=_raise):
            dirs[:] = sorted(d for d in dirs if d != "__pycache__")
            for dirname in dirs:
                if (Path(directory) / dirname).is_symlink():
                    raise ValueError(f"linked editable package directory {dirname}")
            for name in sorted(names):
                if name.endswith((".pyc", ".pyo")):
                    continue
                path = Path(directory) / name
                yield path.relative_to(base.parent).as_posix(), path


def _members(distribution):
    direct = json.loads(distribution.read_text("direct_url.json") or "{}")
    if direct.get("dir_info", {}).get("editable") is True:
        location = urlsplit(direct["url"])
        if location.scheme != "file" or location.netloc not in ("", "localhost"):
            raise ValueError("editable source must be a local install")
        yield from _editable_members(Path(unquote(location.path)))
        return
    if not distribution.read_text("RECORD") or not distribution.files:
        raise ValueError(f"missing installed RECORD for {distribution.metadata['Name']}")
    for member in distribution.files:
        if "__pycache__" not in member.parts and member.suffix not in (".pyc", ".pyo"):
            yield str(member), Path(distribution.locate_file(member))


def _installed_files():
    remaining = {"verifiably-science", "verifiably-beliefs"}
    seen = set()
    members = {}
    while remaining:
        name = remaining.pop()
        if name in seen:
            continue
        seen.add(name)
        dist = metadata.distribution(name)
        for raw in dist.requires or ():
            requirement = Requirement(raw)
            dependency = canonicalize_name(requirement.name)
            if dependency.startswith("verifiably-") and (requirement.marker is None or requirement.marker.evaluate()):
                remaining.add(dependency)
        for logical, path in _members(dist):
            members[name, logical] = path
    return tuple((name, logical, path) for (name, logical), path in sorted(members.items()))


def _bindings(config):
    if config.source is not None:
        config = load_config(config.source[0])
    mounts = []
    for root, profile in mount_profiles(config).items():
        manifest = load_manifest(root)
        mounts.append((manifest.corpus_id, manifest.profile.science_contract, sorted(manifest.profile.domains.items()),
                       profile.compiled_identity, sorted(profile.activated_contracts.items())))
    inputs = acceptance.acceptance_inputs(ReadContext(world=None, config=config))
    return {
        "policy": [closure.BINDING.rule, closure.BINDING.implementation],
        "acceptance": acceptance.statement(inputs),
        "artifacts": sorted((key, pin.artifact) for key, pin in inputs.pins.items()),
        "mounts": sorted(mounts),
    }


def _digest(files, config, *, opening):
    rows = []
    for distribution, name, path in files:
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NONBLOCK)
            with os.fdopen(fd, "rb") as stream:
                if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                    raise ValueError(f"basis member is not a regular file: {path}")
                value = ("present", hashlib.file_digest(stream, "sha256").hexdigest())
        except (FileNotFoundError, NotADirectoryError):
            if opening:
                raise
            value = ("absent",)
        rows.append((distribution, name, *value))
    data = {"version": "basis.v1", "files": rows, "bindings": _bindings(config)}
    encoded = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


_UNMEASURABLE = (OSError, ValueError, KeyError, TypeError, metadata.PackageNotFoundError,
                 AtomsError, NodesError, ScienceError, SharingRegistryMalformed, Refused)


def open_basis(config: ScienceConfig) -> BasisInventory:
    try:
        files = _installed_files()
        return BasisInventory(files, _digest(files, config, opening=True))
    except _UNMEASURABLE as error:
        raise Refused(Refusal("read-unavailable", f"Cannot measure the opening basis: {error}")) from error


def seal_basis(inventory: BasisInventory, config: ScienceConfig) -> str | None:
    try:
        return _digest(inventory.files, config, opening=False)
    except _UNMEASURABLE:
        return None
