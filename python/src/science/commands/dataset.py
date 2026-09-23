"""dataset: hold a local file and mint the dataset record (belief-path §4.2)."""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path

from beliefs import stored
from beliefs.acquisition import bearer_refusal, validity_refusal
from beliefs.dataset import ByteObservation, DatasetDeclaration, Held, ResourceDeclaration, admission_state, dataset_address
from beliefs.errors import FacetPayloadRefused, MalformedRecord
from beliefs.facets import validate_payload
from beliefs.holdings.boundary import write
from beliefs.holdings.records import Found, StoreLocator

from science.refusal import Refusal, Refused
from science.report import Report, record_block

INSTRUMENT = "science/dataset.v1"


def _refuse(message: str):
    raise Refused(Refusal("invalid-input", message))


def _parse_facets(entries) -> dict[str, dict[str, str]]:
    facets: dict[str, dict[str, str]] = {}
    for entry in entries or ():
        name, sep, body = entry.partition("=")
        if not sep or not name:
            _refuse(f"facet {entry!r} is not name=key:value,...")
        pairs = {}
        for pair in body.split(","):
            key, colon, value = pair.partition(":")
            if not colon or not key:
                _refuse(f"facet {entry!r}: {pair!r} is not key:value")
            pairs[key] = value
        facets[name] = pairs
    return facets


def handle(ctx, writer, *, path, title, locator=None, facets=None) -> Report:
    source = Path(path)
    if not source.is_file():
        _refuse(f"{path} is not a regular file")
    domain_facets = _parse_facets(facets)
    content = source.read_bytes()
    digest = "sha256:" + sha256(content).hexdigest()
    declaration = DatasetDeclaration(resources=(ResourceDeclaration(name=source.name, digest=digest),))
    address = dataset_address(declaration)
    _, view = ctx.single_view()
    for node in view.iter_stored():
        if node.kind == "dataset" and dataset_address(stored.dataset_declaration(node)) == address:
            _refuse(f"these bytes are already held as {node.id}")
    relative = f"{digest.removeprefix('sha256:')}/{source.name}"
    standing = tuple(
        stored.holdings_observation_value(node)
        for node in view.iter_stored()
        if node.kind == "holdings-observation"
        and stored.holdings_observation_value(node).location.relative_path == relative
    )
    # The record is built and validated BEFORE the first act: a facet the
    # profile does not know, or a payload it refuses, must leave no bytes in
    # the store and no observation behind (design §6.3, validate before act).
    empirical = None
    if locator is not None:
        empirical = {"locator": locator, "attested_by": writer.actor}
    try:
        proposed = stored.dataset_node(
            title=title,
            resources=[{"name": source.name, "digest": digest}],
            empirical_observation=empirical, domain_facets=domain_facets or None,
        )
    except MalformedRecord as caught:
        _refuse(f"dataset record refused: {caught}")
    profile = ctx.config.profile
    # Kind registered, facet keys declared: the findings form of the check the
    # writer raises on, so nothing of `nodes`' own exception types reaches here.
    violations = profile.document_violations(proposed)
    if violations:
        _refuse("dataset record refused: " + "; ".join(v.message for v in violations))
    # Every facet payload the profile compiles a shape for — the domain facets
    # AND the empirical-observation facet — exactly as the writer's own
    # `_refuse_facets` will check them, so the writer can refuse nothing here
    # that this did not refuse first.
    for key, payload in proposed.facets.items():
        facet = profile.facets.get(key)
        if facet is not None:
            try:
                validate_payload(facet, payload, where=proposed.id)
            except FacetPayloadRefused as caught:
                _refuse(f"facet {key!r} refused: {caught}")
    for name in domain_facets:
        if name not in profile.facets:
            _refuse(f"facet {name!r} is not declared by this profile")
    reason = bearer_refusal(view, proposed)
    if reason is not None:
        _refuse(f"dataset record refused: {reason}")
    if empirical is not None:
        reason = validity_refusal(view, proposed, profile)
        if reason is not None:
            _refuse(f"locator refused: {reason}")
    # --- first act: the holdings write ---------------------------------------
    holdings = writer.holdings_context(instrument=INSTRUMENT)
    published = write(holdings, StoreLocator(writer.store_id, relative), content, expected=digest,
                      standing=standing)
    node = writer.add(proposed)
    outcome = published.record.outcome
    assert isinstance(outcome, Found)
    verdict = admission_state(stored.dataset_declaration(node),
                              (ByteObservation(digest=outcome.digest, location=published.record.location.canonical()),))
    if not isinstance(verdict, Held):
        raise RuntimeError(f"held bytes with a matching digest did not read Held: {verdict!r}")
    return (record_block(node),)
