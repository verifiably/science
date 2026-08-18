"""The composition root — the one module that imports `atoms`.

Science's durable corpus writes flow through the certified `atoms` engine, and
everything the engine needs that is not a plan is decided here: the volume
binding, the explicit root-registration act, the durable executor that compiles
one `nodes` write plan into one `TransactionSpec`, and the root-taking factory
the write API is built with (adapter design §1–§4).

**Why this module and no other.** `atoms` types are engine capability. Confining
their import to the composition root is an architecture rule, checked as one —
distinct from S8's capability boundary, which is about who holds a *mutable
corpus handle* and is checked over `science.corpus`. Two boundaries, two checks,
neither standing in for the other.

**The corpus supplies its own root.** The factory this module hands the write
API is `(root: Path) -> DurableExecutor`, closing over the backend and the
storage profile and deriving the metadata root by §2's sibling rule. A
pre-bound executor would let the corpus write through a root it never verified.
"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from atoms.coordinator.commands import register_root
from atoms.fs.platform import select_backend
from atoms.fs.volume import StorageProfile
from nodes.core.write_plan import CreateOp, DeleteOp, ReplaceOp, WritePlan

from science.errors import CorpusRootRefused
from science.identity import v1

__all__ = [
    "GENESIS_DOMAIN",
    "GENESIS_PAYLOAD",
    "INTENT_DOMAIN",
    "PRODUCTION_STORAGE",
    "init_corpus_root",
    "metadata_root_for",
    "write_intent_digest",
    "write_intent_projection",
]

GENESIS_DOMAIN = "science.corpus-root.v1"
"""The registration chain's genesis domain.

The payload deliberately carries **no corpus identity**: corpus manifests and
`corpus_id` minting are the ledger's second artifact and are unbuilt. When
identity arrives it binds through a later chain entry, never by rewriting
genesis — a genesis rewrite is not a correction, it is a different chain.
"""

GENESIS_PAYLOAD = v1.encode({"domain": GENESIS_DOMAIN})
"""The canonical bytes of the constant payload, under `science.identity.v1`.

`register_root` is idempotent on a matching payload and surface and refuses a
mismatch, so these bytes are permanent for every root ever registered with
them: changing this constant does not migrate a root, it orphans one.
"""

INTENT_DOMAIN = "science.corpus-write-intent.v1"

PRODUCTION_STORAGE = StorageProfile(profile_id="flush-honoring-disk.v1")
"""The engine's production storage profile, passed through unchanged.

A storage profile is a declaration by the trusted composition root, which is
this module. Science holds no tuple data, no allowlist and no override:
admitting a new volume configuration is an `atoms` certification amendment, and
cut 4's *every other tuple fails closed* obligation is exercised as the
engine's own refusal — relied on, never re-implemented.
"""

METADATA_SUFFIX = ".metadata"


def metadata_root_for(corpus_root: Path) -> Path:
    """The engine's caller-supplied metadata root, by one fixed rule: the
    sibling `<corpus-root>.metadata`.

    The rule normally places the store on the corpus's own volume, and the
    engine **proves** same-volume placement and refuses otherwise — the
    guarantee is the engine's probe, not this naming rule. The sibling sits
    outside the corpus root so that the two cold-arrival cases stay legible: a
    corpus copied without its sibling is a normal cold bootstrap, one copied
    with it is the restored-backup classification case.
    """
    root = Path(corpus_root)
    return root.with_name(root.name + METADATA_SUFFIX)


def init_corpus_root(corpus_root: Path) -> None:
    """Make a corpus root durable — the explicit act, never a fallback.

    Every write against an unregistered root refuses (the engine's
    registered-root check, surfaced through the executor's §4 mapping). Lazy
    registration on first write is rejected on purpose: the genesis act is
    attributable and its timing is a recorded decision, not an accident of
    whichever write happened to come first.

    Re-runnable: `register_root` returns the existing genesis digest when the
    payload and surface match, and refuses when they do not.
    """
    root = Path(corpus_root)
    if root.exists() and not root.is_dir():
        raise CorpusRootRefused(f"{str(root)!r} exists and is not a directory, so it cannot be a corpus root")
    root.mkdir(parents=True, exist_ok=True)
    register_root(
        select_backend(),
        str(root),
        str(metadata_root_for(root)),
        PRODUCTION_STORAGE,
        GENESIS_PAYLOAD,
        # No manifest exists to baseline and the corpus-write adapter reserves
        # nothing, so the registered surface is empty.
        (),
    )


def write_intent_projection(plan: WritePlan) -> list[dict[str, str]]:
    """The plan's intent, derivable from the plan alone.

    One discriminated shape per operation kind, in plan order, **omitting the
    fields that do not apply**: a create has no `expected_digest` and a delete
    no `content_sha256`, and the identity encoding refuses `null`, so an
    absent field is spelled by its absence rather than by a placeholder that
    would collide with a present-and-empty one.
    """
    projection: list[dict[str, str]] = []
    for op in plan:
        if isinstance(op, CreateOp):
            projection.append(
                {"op": "create", "path": op.path, "content_sha256": sha256(op.content).hexdigest()}
            )
        elif isinstance(op, ReplaceOp):
            projection.append(
                {
                    "op": "replace",
                    "path": op.path,
                    "expected_digest": op.expected_digest,
                    "content_sha256": sha256(op.content).hexdigest(),
                }
            )
        elif isinstance(op, DeleteOp):
            projection.append({"op": "delete", "path": op.path, "expected_digest": op.expected_digest})
        else:
            # Unreachable through the executor, which validates the plan first;
            # stated rather than silently skipped, because an operation missing
            # from the intent is a transaction whose declared intent is not what
            # it does.
            raise TypeError(f"unknown operation kind: {op!r}")
    return projection


def write_intent_digest(plan: WritePlan) -> str:
    """`sha256:`-prefixed digest of the intent projection. The prefix is
    mandatory: the engine's spec compilation checks the format."""
    return "sha256:" + v1.digest(INTENT_DOMAIN, write_intent_projection(plan))
