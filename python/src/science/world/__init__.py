"""The world layer: closed corpus manifests and the fixture-bound rules store.

Slice 1's registry lives in `science.world.registry` and slice 2's rules store
in `science.world.rules`; this module is the package's import surface and
re-exports both unchanged. The private names below are the seams
`science.root`, `science.corpus`, and the suite already reach for through
`science.world`, kept importable so the promotion moves no caller. Anything
that *replaces* one of them — a monkeypatched global — must patch the module
where the binding the implementation reads lives.
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
from science.world.rules import (
    FIXTURE_SET_DOMAIN,
    RULE_DOMAIN,
    RuleBinding,
    RuleBundle,
    binding_for,
    fixture_set_identity,
    implementation_identity,
    install_rule_binding,
    member_content_digest,
    parse_rule_document,
    rule_document_bytes,
    rule_identity,
    shipped_rule_bundles,
)
from science.world.rules import _HeldRule as _HeldRule
from science.world.rules import _resolve_rule_binding as _resolve_rule_binding

__all__ = [
    "FIXTURE_SET_DOMAIN",
    "RULE_DOMAIN",
    "AdmissionProvenance",
    "AdmissionRecord",
    "CorpusManifest",
    "CorpusStatus",
    "ForkOf",
    "ForkedFrom",
    "Fresh",
    "RegistryView",
    "ReplicaOf",
    "RuleBinding",
    "RuleBundle",
    "StatusRecord",
    "World",
    "WorldConfig",
    "admission_digest",
    "admission_projection",
    "binding_for",
    "corpus_state_identity",
    "fixture_set_identity",
    "implementation_identity",
    "install_rule_binding",
    "load_manifest",
    "manifest_bytes",
    "manifest_projection",
    "member_content_digest",
    "parse_rule_document",
    "provenance_projection",
    "rule_document_bytes",
    "rule_identity",
    "shipped_rule_bundles",
    "status_digest",
    "status_projection",
]
