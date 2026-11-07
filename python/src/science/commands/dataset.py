"""dataset: hold a local file or directory and mint the dataset record."""
from __future__ import annotations

import os
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


def _validate_locator_name(store_id: str, rel: str) -> None:
    try:
        StoreLocator(store_id, f"{'0' * 64}/{rel}")
    except MalformedRecord as caught:
        _refuse(str(caught))


def _read_entries(source: Path, store_id: str, path: str, resources) -> list[tuple[str, bytes, str]]:
    if source.is_symlink() or not (source.is_file() or source.is_dir()):
        _refuse(f"{path} is not a regular file or directory")
    if source.is_file():
        if resources is not None:
            _refuse("--resources requires --path to be a directory")
        _validate_locator_name(store_id, source.name)
        content = source.read_bytes()
        digest = "sha256:" + sha256(content).hexdigest()
        return [(source.name, content, digest)]

    root_resolved = source.resolve()
    if resources is not None:
        if len(resources) == 0:
            _refuse("--resources must not be empty")
        if len(set(resources)) != len(resources):
            _refuse("--resources must not contain duplicates")
        for rel in resources:
            _validate_locator_name(store_id, rel)
            current = source
            for part in Path(rel).parts:
                current = current / part
                if current.is_symlink():
                    _refuse(f"resource {rel!r} traverses a symlink at {current}")
            candidate = source / rel
            if (
                candidate.is_symlink()
                or not candidate.resolve().is_relative_to(root_resolved)
                or not candidate.is_file()
            ):
                _refuse(f"resource {rel!r} is not a regular file inside {path}")
        rel_names = sorted(resources)
    else:
        collected: list[str] = []
        for dirpath, dirnames, filenames in os.walk(source, followlinks=False):
            for dirname in dirnames:
                entry = Path(dirpath, dirname)
                if entry.is_symlink() or not entry.is_dir():
                    _refuse(f"{entry} is a symlink or non-directory")
            for filename in filenames:
                entry = Path(dirpath, filename)
                if entry.is_symlink() or not entry.is_file():
                    _refuse(f"{entry} is a symlink or non-regular file")
                collected.append(entry.relative_to(source).as_posix())
        if not collected:
            _refuse(f"{path} contains no regular files")
        for rel in collected:
            _validate_locator_name(store_id, rel)
        rel_names = sorted(collected)

    entries: list[tuple[str, bytes, str]] = []
    for rel in rel_names:
        content = (source / rel).read_bytes()
        digest = "sha256:" + sha256(content).hexdigest()
        entries.append((rel, content, digest))
    return entries


def handle(ctx, writer, *, path, title, locator=None, facets=None, resources=None) -> Report:
    holdings = writer.holdings_context(instrument=INSTRUMENT)
    source = Path(path)
    entries = _read_entries(source, writer.store_id, path, resources)
    domain_facets = _parse_facets(facets)
    declaration = DatasetDeclaration(
        resources=tuple(ResourceDeclaration(name=name, digest=digest) for name, _, digest in entries)
    )
    address = dataset_address(declaration)
    found = ctx.dataset_at(address)
    if found is not None:
        corpus_id, node = found
        _refuse(
            f"these bytes are already declared as {node.id} in corpus {corpus_id}; a dataset is one "
            "world record, and a second would be a duplicate location"
        )
    view = ctx.write_view()
    planned_writes = []
    for name, content, digest in entries:
        relative = f"{digest.removeprefix('sha256:')}/{name}"
        try:
            location = StoreLocator(writer.store_id, relative)
        except MalformedRecord as caught:
            _refuse(str(caught))
        standing = tuple(
            stored.holdings_observation_value(node)
            for node in view.iter_stored()
            if node.kind == "holdings-observation"
            and stored.holdings_observation_value(node).location == location
        )
        planned_writes.append((location, standing, content, digest))
    # The record is built and validated BEFORE the first act: a facet the
    # profile does not know, or a payload it refuses, must leave no bytes in
    # the store and no observation behind.
    empirical = None
    if locator is not None:
        empirical = {"locator": locator, "attested_by": writer.actor}
    try:
        proposed = stored.dataset_node(
            title=title,
            resources=[{"name": name, "digest": digest} for name, _, digest in entries],
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
    # --- first act: the holdings writes --------------------------------------
    observations: list[ByteObservation] = []
    seen_locations: set[StoreLocator] = set()
    for location, standing, content, digest in planned_writes:
        if location in seen_locations:
            continue
        seen_locations.add(location)
        published = write(holdings, location, content, expected=digest, standing=standing)
        outcome = published.record.outcome
        assert isinstance(outcome, Found)
        observations.append(
            ByteObservation(digest=outcome.digest, location=published.record.location.canonical())
        )
    node = writer.add(proposed)
    verdict = admission_state(stored.dataset_declaration(node), tuple(observations))
    if not isinstance(verdict, Held):
        raise RuntimeError(f"held bytes with a matching digest did not read Held: {verdict!r}")
    return (record_block(node),)
