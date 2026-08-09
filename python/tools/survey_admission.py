"""Measure how far a corpus's externally sourced datasets are from **held**.
**The survey is run by hand.**

    uv run python tools/survey_admission.py \
        --records <record-root> --payloads <payload-root> --scratch <scratch-root>

The gate being measured is kernel §2.2: an input is *held* when we can produce
its exact bytes on demand and identify them by content hash. The design is
`docs/designs/2026-08-09-admission-ramp-design.md`; this file implements §4 and
nothing beyond it.

The roots live outside this repository and are not vendored into it, so nothing
here runs in CI and nothing here is a conformance oracle. `tests/test_admission_survey.py`
covers the predicates that decide the findings, over synthetic roots — the
predecessor survey shipped four defects in exactly those predicates, three found
in review, and each changed a reported number.

Five decisions the reader should not have to reverse-engineer.

**Two collections and a failure list, not one row per resource.** A record
declaring no resources would contribute no rows at all and vanish from the
artifact. Dataset records are their own collection so the denominator survives
contact with the corpus.

**Byte availability and record integrity are independent axes.** A resource can
have bytes and no recorded digest, or a recorded digest and no bytes. Folding
them into one status makes those two states unrepresentable.

**A preflight refusal is not a retrieval failure.** A locator rejected before any
request was never attempted, and reporting it as a failure records a refusal to
look as a finding about the resource.

**Basis evidence is recorded, never resolved.** The instrument reports what a
record states about its own content identity. It never hashes an undeclared file
to manufacture one, and it never folds per-resource digests into a dataset-level
identity — which fold is canonical is a ruling the instrument has no authority to
make.

**The report renders from the artifact.** Every printed figure is read back out
of the same structure that is written to disk, so prose and data cannot drift.
"""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import json
import socket
import ssl
import sys
from collections.abc import Callable, Iterator, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from http.client import HTTPSConnection
from pathlib import Path
from typing import Any, Protocol
from urllib.parse import urljoin, urlsplit

import yaml

FRONTMATTER = "---"

#: The only scheme a probe will fetch. Anything else is refused at preflight.
APPROVED_SCHEMES = frozenset({"https"})

#: Bounds on an attempted fetch. Exceeding either is a retrieval failure, never a
#: truncated body silently hashed.
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_MAX_BYTES = 512 * 1024 * 1024

#: Read size for hashing and for streaming a probe body.
CHUNK = 1024 * 1024

#: Frontmatter fields recording provenance or authority-side identity. **None of
#: them is a content basis**: an accession names a work at a registry, `origin`
#: says where a dataset came from, `source_url` names a page. Only a recorded
#: digest pins bytes, and that is counted separately.
AUTHORITY_FIELDS = ("origin", "accessions", "datapackage", "derivation")

# ---------------------------------------------------------------------------
# Axis values (§3 of the design)
# ---------------------------------------------------------------------------

BYTES_LOCAL = "local"
BYTES_RETRIEVED = "retrieved"
BYTES_RETRIEVAL_FAILED = "retrieval-failed"
BYTES_LOCATOR_UNTESTED = "byte-locator-untested"
BYTES_NO_LOCATOR = "no-byte-locator"

CHECK_MATCH = "match"
CHECK_MISMATCH = "mismatch"
CHECK_ABSENT = "absent"
CHECK_UNCHECKED = "unchecked"

PACKAGE_PRESENT = "present"
PACKAGE_ABSENT = "absent"
PACKAGE_UNPARSEABLE = "unparseable"


# ---------------------------------------------------------------------------
# Observations
# ---------------------------------------------------------------------------


class MalformedRecord(Exception):
    """A record the instrument could read but could not make sense of.

    Distinct from a YAML error: the bytes parsed, and the shape is wrong. Both
    reach the failure list; neither is ever skipped.
    """


@dataclass(frozen=True)
class Failure:
    """A file the instrument could not read. Counted and named, never skipped."""

    root: str
    path: str
    reason: str


@dataclass(frozen=True)
class ResourceObservation:
    """One declared resource, on the three independent axes of §3."""

    dataset: str
    path: str
    byte_observation: str
    hash_result: str
    byte_count_result: str
    recorded_hash: str | None = None
    observed_hash: str | None = None
    recorded_bytes: int | None = None
    observed_bytes: int | None = None
    #: Why a locator was not tested, or why a retrieval failed. Required whenever
    #: the byte observation is one of those two — a value without one is unreportable.
    reason: str | None = None
    #: When a probe ran. Retrievability varies over time; an undated probe result
    #: asserted as a standing property is a stored derived value.
    probed_at: str | None = None


@dataclass(frozen=True)
class BasisEvidence:
    """What the record states about its identity, with the two kinds kept apart.

    **Content basis and authority identity are different things**, and merging
    them makes the report claim more than the corpus says. An accession names a
    *work* at a registry; `origin: external` says where a dataset came from; a
    `source_url` names a page. None of them pins bytes. Only a recorded digest
    does, and only per resource — whether those digests fold into a dataset-level
    identity is a ruling, so this is a count and never a fold.
    """

    #: How many declared resources carry a recorded digest. The only evidence here
    #: that bears on *content* identity.
    declared_resources_with_digest: int
    #: Provenance and authority-side fields the record carries, and what they
    #: hold. Preserved as observations; they are not content basis.
    authority_and_provenance: dict[str, Any]


@dataclass(frozen=True)
class DatasetObservation:
    dataset: str
    package_state: str
    declared_resource_count: int
    basis_evidence: BasisEvidence
    #: Payload files under this record's payload directory that no declared
    #: resource claims. Enumerated, never hashed: hashing one would manufacture an
    #: identity the record does not claim.
    unmatched_payload_files: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Survey:
    datasets: list[DatasetObservation]
    resources: list[ResourceObservation]
    failures: list[Failure]
    record_root_identity: str
    payload_root_identity: str
    probed: bool
    run_at: str


# ---------------------------------------------------------------------------
# Root identity — for a root that is not a repository
# ---------------------------------------------------------------------------


class RootObservations:
    """Accumulates what the run actually read from one root, and digests it.

    A payload root has no commit to name, so its identity is a digest over the
    sorted relative-path observations the run used: each relative path with the
    size and, where the run read the bytes, the content digest.

    **Stated bound.** Unmatched payload files are enumerated and not read, so they
    contribute a path and a size and no digest. A content change to an unmatched
    file that preserves its size does not move the identity.
    """

    def __init__(self) -> None:
        self._lines: set[str] = set()

    def record(self, relative: str, size: int, digest: str | None) -> None:
        self._lines.add(f"{relative}\t{size}\t{digest or '-'}")

    def identity(self) -> str:
        joined = "\n".join(sorted(self._lines))
        return "sha256:" + hashlib.sha256(joined.encode("utf-8")).hexdigest()


def digest_file(path: Path) -> tuple[str, int]:
    """Return the file's sha256 and its size, read in chunks."""
    hasher = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK):
            hasher.update(chunk)
            size += len(chunk)
    return hasher.hexdigest(), size


# ---------------------------------------------------------------------------
# Local declared paths
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PathRefusal:
    reason: str


def resolve_declared_path(root: Path, dataset: str, declared: str) -> Path | PathRefusal:
    """Resolve a declared resource path under one root, refusing every escape.

    Refused before any read: an absolute path, a path traversing upward, and a
    path that leaves its directory through a symlink. The comparison is made
    against the resolved directory so a symlinked root is not itself an escape.
    """
    if declared.startswith("/"):
        return PathRefusal("declared path is absolute")
    if ".." in Path(declared).parts:
        return PathRefusal("declared path traverses upward")

    base = (root / dataset).resolve()
    candidate = (base / declared).resolve()
    if candidate != base and base not in candidate.parents:
        return PathRefusal("declared path escapes its root through a symlink")
    return candidate


# ---------------------------------------------------------------------------
# Probing — preflight, then a pinned fetch
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Approved:
    """A locator that cleared preflight, with the address that was validated."""

    host: str
    port: int
    path: str
    address: str


@dataclass(frozen=True)
class Refused:
    reason: str


Resolver = Callable[[str, int], list[str]]


def system_resolver(host: str, port: int) -> list[str]:
    infos = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
    return [str(info[4][0]) for info in infos]


def preflight(url: str, resolver: Resolver = system_resolver) -> Approved | Refused:
    """Decide whether a locator may be fetched at all, before any request.

    Every refusal here is `byte-locator-untested`: nothing was attempted, so
    nothing was learned about the resource.
    """
    parts = urlsplit(url)
    if parts.scheme not in APPROVED_SCHEMES:
        return Refused(f"scheme {parts.scheme or '(none)'} is not approved")
    if not parts.hostname:
        return Refused("locator names no host")

    port = parts.port or 443
    try:
        addresses = resolver(parts.hostname, port)
    except OSError as exc:
        return Refused(f"host does not resolve: {exc}")
    if not addresses:
        return Refused("host resolves to no address")

    for address in addresses:
        if not ipaddress.ip_address(address).is_global:
            return Refused(f"host resolves to non-public address {address}")

    path = parts.path or "/"
    if parts.query:
        path = f"{path}?{parts.query}"
    # The first validated address is the one pinned. Every address resolved for
    # the host was checked above, so choosing among them cannot smuggle one past
    # the check.
    return Approved(host=parts.hostname, port=port, path=path, address=addresses[0])


@dataclass(frozen=True)
class ProbeOutcome:
    byte_observation: str
    reason: str | None = None
    digest: str | None = None
    size: int | None = None


class Probe(Protocol):
    def fetch(self, url: str) -> ProbeOutcome: ...


#: How a probe obtains a connection to an approved address. Injected so the
#: pinning behaviour is exercised directly and the fail-closed arm is reachable
#: without reaching into the probe's internals.
ConnectionFactory = Callable[["Approved", float], HTTPSConnection]


class PinnedHTTPSConnection(HTTPSConnection):
    """Connects to a validated address while validating the certificate's hostname.

    Resolving a name, checking the result, and then letting the client resolve it
    again leaves the check decorative — the second answer can differ from the
    first, which is the whole of the rebinding attack. This connects to the
    address preflight validated and keeps `self.host` as the name, so SNI and
    certificate verification still run against the name.
    """

    def __init__(self, host: str, address: str, port: int, timeout: float, context: ssl.SSLContext) -> None:
        super().__init__(host, port=port, timeout=timeout, context=context)
        self._address = address
        self._pinned_context = context

    def connect(self) -> None:
        sock = socket.create_connection((self._address, self.port), self.timeout)
        self.sock = self._pinned_context.wrap_socket(sock, server_hostname=self.host)


class NetworkProbe:
    """Fetches to the scratch root, hashes, and deletes only its own files.

    Fails closed: if the validated address cannot be connected to while hostname
    and certificate validation are preserved, no request is issued and the
    locator is reported untested. A disclosed hole is still a hole.
    """

    def __init__(
        self,
        scratch: Path,
        *,
        resolver: Resolver = system_resolver,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        max_bytes: int = DEFAULT_MAX_BYTES,
        max_redirects: int = 5,
        connect: ConnectionFactory | None = None,
    ) -> None:
        self._scratch = scratch
        self._resolver = resolver
        self._timeout = timeout
        self._max_bytes = max_bytes
        self._max_redirects = max_redirects
        self._connect = connect or pinned_connection

    def fetch(self, url: str) -> ProbeOutcome:
        seen = 0
        current = url
        while True:
            decision = preflight(current, self._resolver)
            if isinstance(decision, Refused):
                where = "" if current == url else f" (redirect hop {current})"
                return ProbeOutcome(BYTES_LOCATOR_UNTESTED, reason=decision.reason + where)

            try:
                response, location = self._request(decision)
            except PinningUnavailable as exc:
                return ProbeOutcome(BYTES_LOCATOR_UNTESTED, reason=str(exc))
            except OSError as exc:
                return ProbeOutcome(BYTES_RETRIEVAL_FAILED, reason=f"transport failure: {exc}")

            if location is not None:
                seen += 1
                if seen > self._max_redirects:
                    return ProbeOutcome(BYTES_RETRIEVAL_FAILED, reason="too many redirects")
                # A Location may be relative. Joining it against the URL it came
                # from is what makes the next preflight examine the real target.
                current = urljoin(current, location)
                continue
            return response

    def _request(self, approved: Approved) -> tuple[ProbeOutcome, str | None]:
        connection = self._connect(approved, self._timeout)
        try:
            connection.request("GET", approved.path, headers={"Host": approved.host})
            response = connection.getresponse()
            if response.status in (301, 302, 303, 307, 308):
                location = response.getheader("Location")
                if not location:
                    return ProbeOutcome(BYTES_RETRIEVAL_FAILED, reason="redirect without a location"), None
                return ProbeOutcome(BYTES_RETRIEVAL_FAILED), location
            if response.status != 200:
                return ProbeOutcome(BYTES_RETRIEVAL_FAILED, reason=f"status {response.status}"), None
            return self._stream(response), None
        finally:
            connection.close()

    def _stream(self, response: Any) -> ProbeOutcome:
        self._scratch.mkdir(parents=True, exist_ok=True)
        target = self._scratch / f"probe-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%f')}"
        hasher = hashlib.sha256()
        size = 0
        try:
            with target.open("wb") as handle:
                while chunk := response.read(CHUNK):
                    size += len(chunk)
                    if size > self._max_bytes:
                        return ProbeOutcome(
                            BYTES_RETRIEVAL_FAILED,
                            reason=f"exceeded the {self._max_bytes}-byte streaming ceiling",
                        )
                    hasher.update(chunk)
                    handle.write(chunk)
        finally:
            target.unlink(missing_ok=True)
        return ProbeOutcome(BYTES_RETRIEVED, digest=hasher.hexdigest(), size=size)


class PinningUnavailable(RuntimeError):
    """Raised when the validated address cannot be used with validation intact.

    The caller reports the locator untested and issues no request. Probing while
    announcing the check as unenforced would keep the exposure and merely
    document it.
    """


def pinned_connection(approved: Approved, timeout: float) -> HTTPSConnection:
    """Build a connection to the validated address that still validates the name."""
    context = ssl.create_default_context()
    if not context.check_hostname or context.verify_mode != ssl.CERT_REQUIRED:
        raise PinningUnavailable("cannot pin the validated address with hostname validation intact")
    return PinnedHTTPSConnection(approved.host, approved.address, approved.port, timeout, context)


# ---------------------------------------------------------------------------
# Reading the corpus
# ---------------------------------------------------------------------------


def read_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith(FRONTMATTER):
        raise MalformedRecord("no frontmatter block")
    parts = text.split(FRONTMATTER, 2)
    if len(parts) < 3:
        raise MalformedRecord("unterminated frontmatter block")
    loaded = yaml.safe_load(parts[1])
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise MalformedRecord("frontmatter is not a mapping")
    return loaded


def declared_resources(package: dict[str, Any]) -> Iterator[tuple[dict[str, Any], str]]:
    """Yield each `resources` entry that declares a path, with that path.

    An entry without a path declares no resource: it cannot be resolved, hashed
    or counted, so it is a shape failure rather than a resource with unknown
    values.
    """
    entries = package.get("resources")
    if entries is None:
        return
    if not isinstance(entries, list):
        raise MalformedRecord("`resources` is not a list")
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise MalformedRecord(f"resource {index} is not a mapping")
        path = entry.get("path")
        if path is None:
            raise MalformedRecord(f"resource {index} declares no path")
        yield entry, str(path)


def is_url(value: object) -> bool:
    return isinstance(value, str) and bool(urlsplit(value).scheme) and "://" in value


def byte_locator(resource: dict[str, Any], declared: str) -> str | None:
    """The locator that retrieves *this resource's exact bytes*, or nothing.

    Narrow by design. A dataset landing page, an API base and an accession all
    fail it. Two things pass:

    * **A declared `path` that is itself a URL.** The resource is not stored
      beside the record at all; the path names the exact bytes remotely. Missing
      this was a measurement-changing defect — every remote resource in the
      predecessor's store reads its bytes from such a path, and all of them were
      reported as carrying no locator at all.
    * **A non-local `source.ref` that is a URL.** A `{type: local, ref: ...}`
      source is acquisition provenance for the build, not a way to retrieve the
      published resource, so it does not qualify.
    """
    if is_url(declared):
        return declared
    source = resource.get("source")
    if not isinstance(source, dict) or source.get("type") == "local":
        return None
    ref = source.get("ref")
    return ref if is_url(ref) else None


def recorded_hash(resource: dict[str, Any]) -> str | None:
    value = resource.get("hash")
    if not isinstance(value, str):
        return None
    return value.split(":", 1)[1] if value.startswith("sha256:") else value


def compare(recorded: Any, observed: Any) -> str:
    if observed is None:
        return CHECK_UNCHECKED
    if recorded is None:
        return CHECK_ABSENT
    return CHECK_MATCH if recorded == observed else CHECK_MISMATCH


# ---------------------------------------------------------------------------
# The survey
# ---------------------------------------------------------------------------


def survey(record_root: Path, payload_root: Path, probe: Probe | None = None) -> Survey:
    datasets: list[DatasetObservation] = []
    resources: list[ResourceObservation] = []
    failures: list[Failure] = []
    record_obs = RootObservations()
    payload_obs = RootObservations()

    for directory in sorted(p for p in record_root.iterdir() if p.is_dir() and not p.is_symlink()):
        name = directory.name
        stated: dict[str, Any] = {}
        entity = directory / "entity.md"
        if entity.is_file():
            _observe(record_obs, record_root, entity)
            try:
                frontmatter = read_frontmatter(entity)
            except (MalformedRecord, yaml.YAMLError) as exc:
                failures.append(Failure("records", f"{name}/entity.md", str(exc)))
            else:
                stated = {key: frontmatter[key] for key in AUTHORITY_FIELDS if key in frontmatter}
                access = frontmatter.get("access")
                if isinstance(access, dict) and access.get("source_url"):
                    stated["access.source_url"] = access["source_url"]

        package_path = directory / "datapackage.yaml"
        declared: list[tuple[dict[str, Any], str]] = []
        if not package_path.is_file():
            package_state = PACKAGE_ABSENT
        else:
            _observe(record_obs, record_root, package_path)
            try:
                loaded = yaml.safe_load(package_path.read_text(encoding="utf-8"))
                if loaded is not None and not isinstance(loaded, dict):
                    raise MalformedRecord("data package is not a mapping")
                declared = list(declared_resources(loaded or {}))
            except (MalformedRecord, yaml.YAMLError) as exc:
                package_state = PACKAGE_UNPARSEABLE
                failures.append(Failure("records", f"{name}/datapackage.yaml", str(exc)))
                declared = []
            else:
                package_state = PACKAGE_PRESENT

        # Claims are the *declared* relative paths, normalized. Recording the
        # absolute file that happened to win resolution would report a payload
        # copy as unmatched whenever the record-root copy was found first.
        claimed = {_normalized_claim(path) for _, path in declared}
        for resource, path in declared:
            resources.append(
                _observe_resource(name, resource, path, record_root, payload_root, record_obs, payload_obs, probe)
            )

        unmatched, walk_failure = _unmatched(payload_root, name, claimed, payload_obs)
        if walk_failure is not None:
            failures.append(walk_failure)

        datasets.append(
            DatasetObservation(
                dataset=name,
                package_state=package_state,
                declared_resource_count=len(declared),
                basis_evidence=BasisEvidence(
                    declared_resources_with_digest=sum(1 for r, _ in declared if recorded_hash(r) is not None),
                    authority_and_provenance=stated,
                ),
                unmatched_payload_files=unmatched,
            )
        )

    return Survey(
        datasets=datasets,
        resources=resources,
        failures=failures,
        record_root_identity=record_obs.identity(),
        payload_root_identity=payload_obs.identity(),
        probed=probe is not None,
        run_at=datetime.now(UTC).isoformat(),
    )


def _observe(root_obs: RootObservations, root: Path, path: Path) -> tuple[str, int]:
    digest, size = digest_file(path)
    root_obs.record(str(path.relative_to(root)), size, digest)
    return digest, size


def _observe_resource(
    dataset: str,
    resource: dict[str, Any],
    declared: str,
    record_root: Path,
    payload_root: Path,
    record_obs: RootObservations,
    payload_obs: RootObservations,
    probe: Probe | None,
) -> ResourceObservation:
    recorded = recorded_hash(resource)
    recorded_bytes = resource.get("bytes") if isinstance(resource.get("bytes"), int) else None

    # A declared path that is a URL names no local file. Trying to resolve it as
    # one would report a refusal about a path the record never claimed was local.
    if not is_url(declared):
        refusal: PathRefusal | None = None
        for root, root_obs in ((record_root, record_obs), (payload_root, payload_obs)):
            resolved = resolve_declared_path(root, dataset, declared)
            if isinstance(resolved, PathRefusal):
                refusal = resolved
                continue
            if resolved.is_file():
                digest, size = digest_file(resolved)
                root_obs.record(str(resolved.relative_to(root.resolve())), size, digest)
                return ResourceObservation(
                    dataset=dataset,
                    path=declared,
                    byte_observation=BYTES_LOCAL,
                    hash_result=compare(recorded, digest),
                    byte_count_result=compare(recorded_bytes, size),
                    recorded_hash=recorded,
                    observed_hash=digest,
                    recorded_bytes=recorded_bytes,
                    observed_bytes=size,
                )
        if refusal is not None:
            return _untested(dataset, declared, recorded, recorded_bytes, refusal.reason)

    locator = byte_locator(resource, declared)
    if locator is None:
        return ResourceObservation(
            dataset=dataset,
            path=declared,
            byte_observation=BYTES_NO_LOCATOR,
            hash_result=CHECK_UNCHECKED,
            byte_count_result=CHECK_UNCHECKED,
            recorded_hash=recorded,
            recorded_bytes=recorded_bytes,
        )

    if probe is None:
        return _untested(dataset, declared, recorded, recorded_bytes, "no probe was run")

    outcome = probe.fetch(locator)
    stamped = datetime.now(UTC).isoformat()
    if outcome.byte_observation == BYTES_RETRIEVED:
        return ResourceObservation(
            dataset=dataset,
            path=declared,
            byte_observation=BYTES_RETRIEVED,
            hash_result=compare(recorded, outcome.digest),
            byte_count_result=compare(recorded_bytes, outcome.size),
            recorded_hash=recorded,
            observed_hash=outcome.digest,
            recorded_bytes=recorded_bytes,
            observed_bytes=outcome.size,
            probed_at=stamped,
        )
    return ResourceObservation(
        dataset=dataset,
        path=declared,
        byte_observation=outcome.byte_observation,
        hash_result=CHECK_UNCHECKED,
        byte_count_result=CHECK_UNCHECKED,
        recorded_hash=recorded,
        recorded_bytes=recorded_bytes,
        reason=outcome.reason,
        probed_at=stamped,
    )


def _untested(
    dataset: str, declared: str, recorded: str | None, recorded_bytes: int | None, reason: str
) -> ResourceObservation:
    return ResourceObservation(
        dataset=dataset,
        path=declared,
        byte_observation=BYTES_LOCATOR_UNTESTED,
        hash_result=CHECK_UNCHECKED,
        byte_count_result=CHECK_UNCHECKED,
        recorded_hash=recorded,
        recorded_bytes=recorded_bytes,
        reason=reason,
    )


def _unmatched(
    payload_root: Path, dataset: str, claimed: set[str], payload_obs: RootObservations
) -> tuple[list[str], Failure | None]:
    """Payload files no declared resource claims. Enumerated, never read.

    Refuses a symlinked payload directory rather than walking it. Guarding only
    the children leaves the door itself open: if the dataset's directory *is* the
    link, every file behind it is enumerated as though it sat inside the payload
    root. The refusal is reported, not skipped — a silent skip would read as a
    dataset with no undeclared bytes, which is a finding rather than a gap.
    """
    directory = payload_root / dataset
    if directory.is_symlink():
        return [], Failure("payloads", dataset, "payload directory is a symlink; not walked")
    if not directory.is_dir():
        return [], None
    found: list[str] = []
    for path in sorted(_walk_without_symlinks(directory)):
        relative = path.relative_to(directory)
        if _normalized_claim(str(relative)) in claimed:
            continue
        recorded = str(path.relative_to(payload_root))
        payload_obs.record(recorded, path.stat().st_size, None)
        found.append(recorded)
    return found, None


def _walk_without_symlinks(directory: Path) -> Iterator[Path]:
    """Yield regular files under `directory`, never following a symlink.

    A symlinked directory can point anywhere, so descending into one would let a
    file outside the payload root be reported as inside it — the same escape the
    declared-path rules refuse, arriving by a different door.
    """
    for entry in sorted(directory.iterdir()):
        if entry.is_symlink():
            continue
        if entry.is_dir():
            yield from _walk_without_symlinks(entry)
        elif entry.is_file():
            yield entry


def _normalized_claim(declared: str) -> str:
    """A declared path in the one spelling both sides of the comparison use."""
    return str(Path(declared)) if not is_url(declared) else declared


# ---------------------------------------------------------------------------
# Artifact and report
# ---------------------------------------------------------------------------


def to_artifact(result: Survey) -> dict[str, Any]:
    return {
        "run_at": result.run_at,
        "probed": result.probed,
        "record_root_identity": result.record_root_identity,
        "payload_root_identity": result.payload_root_identity,
        "datasets": [asdict(d) for d in result.datasets],
        "resources": [asdict(r) for r in result.resources],
        "failures": [asdict(f) for f in result.failures],
    }


def render_report(artifact: dict[str, Any]) -> str:
    """Render the human report *from the artifact*, so the two cannot drift."""
    datasets = artifact["datasets"]
    resources = artifact["resources"]
    lines = [
        "Admission ramp survey",
        "=====================",
        f"run at              {artifact['run_at']}",
        f"probing             {'enabled' if artifact['probed'] else 'not run'}",
        f"record root         {artifact['record_root_identity']}",
        f"payload root        {artifact['payload_root_identity']}",
        "",
        f"Dataset records: {len(datasets)}",
    ]
    for state in (PACKAGE_PRESENT, PACKAGE_ABSENT, PACKAGE_UNPARSEABLE):
        count = sum(1 for d in datasets if d["package_state"] == state)
        lines.append(f"  data package {state:<12} {count}")
    with_unmatched = sum(1 for d in datasets if d["unmatched_payload_files"])
    unmatched_total = sum(len(d["unmatched_payload_files"]) for d in datasets)
    pinned = sum(1 for d in datasets if d["basis_evidence"]["declared_resources_with_digest"])
    authority_only = sum(
        1
        for d in datasets
        if not d["basis_evidence"]["declared_resources_with_digest"] and d["basis_evidence"]["authority_and_provenance"]
    )
    lines += [
        f"  with unmatched payload files  {with_unmatched} ({unmatched_total} files)",
        f"  declaring at least one pinned resource  {pinned}",
        f"  stating authority or provenance only    {authority_only}",
        "",
        f"Declared resources: {len(resources)}",
        "  byte observation",
    ]
    for value in (BYTES_LOCAL, BYTES_RETRIEVED, BYTES_RETRIEVAL_FAILED, BYTES_LOCATOR_UNTESTED, BYTES_NO_LOCATOR):
        lines.append(f"    {value:<24} {sum(1 for r in resources if r['byte_observation'] == value)}")
    for axis in ("hash_result", "byte_count_result"):
        lines.append(f"  {axis.replace('_', ' ')}")
        for value in (CHECK_MATCH, CHECK_MISMATCH, CHECK_ABSENT, CHECK_UNCHECKED):
            lines.append(f"    {value:<24} {sum(1 for r in resources if r[axis] == value)}")

    mismatches = [r for r in resources if CHECK_MISMATCH in (r["hash_result"], r["byte_count_result"])]
    lines.append("")
    lines.append(f"Mismatches: {len(mismatches)}")
    for r in mismatches:
        lines.append(f"  {r['dataset']}/{r['path']}  hash={r['hash_result']} bytes={r['byte_count_result']}")

    lines.append("")
    lines.append(f"Parse failures: {len(artifact['failures'])}")
    for f in artifact["failures"]:
        lines.append(f"  [{f['root']}] {f['path']}: {f['reason']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def validate_scratch(scratch: Path, record_root: Path, payload_root: Path) -> None:
    """The scratch root may not be, or sit inside, either corpus root."""
    resolved = scratch.resolve()
    for name, root in (("record", record_root), ("payload", payload_root)):
        base = root.resolve()
        if resolved == base or base in resolved.parents:
            raise SystemExit(f"scratch root is inside the {name} root; choose one outside both")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--records", type=Path, required=True, help="root holding dataset records")
    parser.add_argument("--payloads", type=Path, required=True, help="root holding materialized bytes")
    parser.add_argument("--scratch", type=Path, required=True, help="scratch root, outside both corpus roots")
    parser.add_argument("--artifact", type=Path, help="write the unit-level artifact here as JSON")
    parser.add_argument("--probe", action="store_true", help="attempt retrieval for resources naming a byte locator")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--max-bytes", type=int, default=DEFAULT_MAX_BYTES)
    args = parser.parse_args(argv)

    validate_scratch(args.scratch, args.records, args.payloads)
    probe = NetworkProbe(args.scratch, timeout=args.timeout, max_bytes=args.max_bytes) if args.probe else None
    artifact = to_artifact(survey(args.records, args.payloads, probe))
    if args.artifact:
        args.artifact.write_text(json.dumps(artifact, indent=2, sort_keys=True, default=str), encoding="utf-8")
    print(render_report(artifact))
    return 0


if __name__ == "__main__":
    sys.exit(main())
