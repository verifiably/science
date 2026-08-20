"""Closed corpus manifests, independent of the corpus engine."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, NoReturn, cast

import yaml

from science.consulted import CorpusPins
from science.errors import ManifestMalformed, ManifestMissing

__all__ = ["CorpusManifest", "ForkedFrom", "load_manifest", "manifest_bytes", "manifest_projection"]

_NAMESPACE = re.compile(r"^[a-z][a-z0-9-]*$")
_LOWER_HEX = frozenset("0123456789abcdef")


@dataclass(frozen=True)
class ForkedFrom:
    corpus_id: str
    corpus_state: str


@dataclass(frozen=True)
class CorpusManifest:
    manifest_version: Literal[2]
    corpus_id: str
    profile: CorpusPins
    forked_from: ForkedFrom | None = None


class _ManifestLoader(yaml.SafeLoader):
    pass


def _construct_mapping(loader: _ManifestLoader, node: yaml.MappingNode, deep: bool = False) -> dict[object, object]:
    mapping: dict[object, object] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise yaml.constructor.ConstructorError(None, None, f"duplicate key {key!r}", key_node.start_mark)
        mapping[key] = (
            value_node.value
            if key in {"corpus_id", "corpus_state"}
            and isinstance(value_node, yaml.ScalarNode)
            and value_node.tag == "tag:yaml.org,2002:int"
            else loader.construct_object(value_node, deep=deep)
        )
    return mapping


_ManifestLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def _malformed(message: str) -> NoReturn:
    raise ManifestMalformed(message)


def _closed_mapping(value: object, expected: set[str], location: str) -> dict[str, object]:
    if type(value) is not dict or set(value) != expected or any(type(key) is not str for key in value):
        _malformed(f"{location} must have exactly {sorted(expected)}")
    return cast(dict[str, object], value)


def _lower_hex(value: object, length: int, location: str) -> str:
    if type(value) is not str or len(value) != length or any(character not in _LOWER_HEX for character in value):
        _malformed(f"{location} must be {length} lowercase hexadecimal characters")
    return value


def _identity(value: object, namespace: str, location: str) -> str:
    if type(value) is not str:
        _malformed(f"{location} must be an identity string")
    prefix, separator, digest = value.partition(":")
    if separator != ":" or prefix != namespace or not _NAMESPACE.fullmatch(prefix):
        _malformed(f"{location} must be a {namespace!r} identity")
    _lower_hex(digest, 64, location)
    return value


def _profile(value: object) -> CorpusPins:
    profile = _closed_mapping(value, {"science_contract", "domains"}, "manifest profile")
    science_contract = _identity(profile["science_contract"], "science", "manifest profile science_contract")
    domains = profile["domains"]
    if type(domains) is not dict:
        _malformed("manifest profile domains must be a mapping")
    checked_domains: dict[str, str] = {}
    for namespace, identity in cast(dict[object, object], domains).items():
        if type(namespace) is not str or not _NAMESPACE.fullmatch(namespace) or namespace == "science":
            _malformed("manifest profile domain namespaces must be non-science namespaces")
        checked_domains[namespace] = _identity(identity, namespace, f"manifest profile domain {namespace!r}")
    try:
        return CorpusPins(science_contract=science_contract, domains=checked_domains)
    except Exception as caught:
        raise ManifestMalformed(f"manifest profile is invalid: {caught}") from caught


def _parse_manifest(value: object) -> CorpusManifest:
    fields = {"manifest_version", "corpus_id", "profile"}
    if type(value) is dict and "forked_from" in value:
        fields.add("forked_from")
    document = _closed_mapping(value, fields, "manifest")
    if type(document["manifest_version"]) is not int or document["manifest_version"] != 2:
        _malformed("manifest_version must be the exact integer 2")
    corpus_id = _lower_hex(document["corpus_id"], 32, "corpus_id")
    profile = _profile(document["profile"])
    forked_from = None
    if "forked_from" in document:
        fork = _closed_mapping(document["forked_from"], {"corpus_id", "corpus_state"}, "manifest forked_from")
        forked_from = ForkedFrom(
            corpus_id=_lower_hex(fork["corpus_id"], 32, "forked_from corpus_id"),
            corpus_state=_lower_hex(fork["corpus_state"], 64, "forked_from corpus_state"),
        )
    return CorpusManifest(manifest_version=2, corpus_id=corpus_id, profile=profile, forked_from=forked_from)


def load_manifest(root: Path) -> CorpusManifest:
    """Load the exact closed manifest at a corpus root."""
    path = Path(root) / "corpus.yaml"
    try:
        document = yaml.load(path.read_text(encoding="utf-8"), Loader=_ManifestLoader)
        return _parse_manifest(document)
    except FileNotFoundError as caught:
        raise ManifestMissing(f"{path}: manifest is missing") from caught
    except ManifestMalformed:
        raise
    except Exception as caught:
        raise ManifestMalformed(f"{path}: malformed manifest: {caught}") from caught


def manifest_projection(manifest: CorpusManifest) -> dict[str, object]:
    projection: dict[str, object] = {
        "manifest_version": manifest.manifest_version,
        "corpus_id": manifest.corpus_id,
        "profile": {
            "science_contract": manifest.profile.science_contract,
            "domains": dict(sorted(manifest.profile.domains.items())),
        },
    }
    if manifest.forked_from is not None:
        projection["forked_from"] = {
            "corpus_id": manifest.forked_from.corpus_id,
            "corpus_state": manifest.forked_from.corpus_state,
        }
    return projection


def manifest_bytes(manifest: CorpusManifest) -> bytes:
    return yaml.safe_dump(manifest_projection(manifest), sort_keys=True, allow_unicode=True).encode("utf-8")
