"""fetch: hold a mounted dataset's bytes from a path or URL after checking the declared digest (commons spec §7.4)."""
from __future__ import annotations

import sys
from hashlib import sha256
from pathlib import Path

from beliefs import stored
from beliefs.holdings.boundary import write
from beliefs.holdings.records import StoreLocator, url_locator
from beliefs.holdings.transport import Failed, NotAttempted, RetrievalBounds, retrieve, url_seam

from science.refusal import Refusal, Refused
from science.report import Report, record_block

INSTRUMENT = "science/fetch.v1"
URL_TIMEOUT_SECONDS = 60
URL_MAX_REDIRECTS = 5


def _refuse(message: str, data: dict | None = None):
    raise Refused(Refusal("invalid-input", message, data or {}))


def _bytes_of(ctx, writer, source: str, max_bytes: int) -> bytes:
    if source.startswith("https://"):
        scratch = ctx.config.operations_root / "scratch" / "fetch" / writer.invocation_id
        scratch.mkdir(parents=True, exist_ok=True)
        bounds = RetrievalBounds(timeout_seconds=URL_TIMEOUT_SECONDS, max_bytes=max_bytes or sys.maxsize,
                                 max_redirects=URL_MAX_REDIRECTS)
        retrieved = retrieve(url_locator(source), bounds, url_seam(), scratch)
        if isinstance(retrieved, (NotAttempted, Failed)):
            _refuse(f"{source} was not retrieved: {retrieved.reason}")
        try:
            return retrieved.path.read_bytes()
        finally:
            retrieved.path.unlink(missing_ok=True)
    path = Path(source)
    if not path.is_absolute():
        _refuse(f"source {source!r} is neither an absolute path nor an https:// URL")
    if not path.is_file():
        _refuse(f"{source} is not a regular file")
    return path.read_bytes()


def handle(ctx, writer, *, dataset, source) -> Report:
    policy = ctx.config.fetch
    if policy.policy == "records-only":
        _refuse("fetch is refused: [fetch] policy is \"records-only\"", {"key": "[fetch] policy"})
    mount = ctx.cited(dataset)
    resources = stored.dataset_declaration(mount.view.get(dataset)).resources
    if len(resources) != 1:
        _refuse(f"{dataset} declares {len(resources)} resources; fetch holds one (sci-d1e874)")
    (resource,) = resources
    digest, name = resource.digest, resource.name
    if digest is None:
        _refuse(f"{dataset} declares no digest to check the bytes against")
    content = _bytes_of(ctx, writer, source, policy.max_bytes)
    actual = "sha256:" + sha256(content).hexdigest()
    if actual != digest:
        _refuse(f"the bytes from {source} are {actual}, not the declared {digest}")
    if policy.max_bytes and len(content) > policy.max_bytes:
        _refuse(f"the bytes from {source} are {len(content)} bytes, over [fetch] max_bytes {policy.max_bytes}")
    relative = f"{digest.removeprefix('sha256:')}/{name}"
    view = ctx.write_view()
    standing = tuple(
        stored.holdings_observation_value(node)
        for node in view.iter_stored()
        if node.kind == "holdings-observation"
        and stored.holdings_observation_value(node).location.relative_path == relative
    )
    # --- the one act: the holdings write -------------------------------------
    holdings = writer.holdings_context(instrument=INSTRUMENT)
    published = write(holdings, StoreLocator(writer.store_id, relative), content, expected=digest,
                      standing=standing)
    (node,) = [n for n in ctx.write_view().iter_stored()
               if n.kind == "holdings-observation" and stored.holdings_observation_value(n) == published.record]
    return (record_block(node),)
