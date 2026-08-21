"""Closed corpus manifests, independent of the corpus engine.

Slice 1's registry lives in `science.world.registry`; this module is the
package's import surface and re-exports it unchanged. The private names below
are the seams `science.root`, `science.corpus`, and the suite already reach
for through `science.world`, kept importable so the promotion moves no caller.
Anything that *replaces* one of them — a monkeypatched global — must patch
`science.world.registry`, where the binding the implementation reads lives.
"""

from __future__ import annotations

from science.world.registry import (
    AdmissionProvenance,
    AdmissionRecord,
    CorpusManifest,
    CorpusStatus,
    ForkedFrom,
    ForkOf,
    Fresh,
    RegistryView,
    ReplicaOf,
    StatusRecord,
    World,
    WorldConfig,
    admission_digest,
    admission_projection,
    corpus_state_identity,
    load_manifest,
    manifest_bytes,
    manifest_projection,
    provenance_projection,
    status_digest,
    status_projection,
)
from science.world.registry import _lift_json as _lift_json
from science.world.registry import _load_world_mirror as _load_world_mirror
from science.world.registry import _parse_manifest as _parse_manifest
from science.world.registry import _world_mirror_bytes as _world_mirror_bytes

__all__ = [
    "AdmissionProvenance",
    "AdmissionRecord",
    "CorpusManifest",
    "CorpusStatus",
    "ForkOf",
    "ForkedFrom",
    "Fresh",
    "RegistryView",
    "ReplicaOf",
    "StatusRecord",
    "World",
    "WorldConfig",
    "admission_digest",
    "admission_projection",
    "corpus_state_identity",
    "load_manifest",
    "manifest_bytes",
    "manifest_projection",
    "provenance_projection",
    "status_digest",
    "status_projection",
]
