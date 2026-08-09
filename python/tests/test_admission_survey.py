"""Cover the predicates that decide the admission-ramp survey's findings.

The survey itself is run by hand against roots outside this repository, so no
test here runs it against real data. What is covered is every predicate that
turns a corpus into a reported number — the class of code where the predecessor
survey shipped four defects, three found only in review, each of which changed a
figure.

Synthetic record, payload and scratch roots are built under `tmp_path`. Six cases
are required by the design (§4) rather than merely useful, because each is a
shape the real corpus may never produce, and an unexercised arm is an unmeasured
one:

1. no data package, with undeclared payload bytes present;
2. an unparseable data package;
3. a declared resource with bytes present and no recorded hash;
4. a preflight refusal and a retrieval failure over the same resource;
5. a declared local path that escapes its root;
6. a validated address that cannot be pinned — and *no request issued*.
"""

from __future__ import annotations

import importlib.util
import ssl
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

# `tools/` is not a package and deliberately is not on the import path — nothing
# in `src/` may depend on it. Load it by file instead, registering it in
# `sys.modules` first because `@dataclass` resolves annotations through there,
# and because the fail-closed test patches `survey_admission.socket`.
_SPEC = importlib.util.spec_from_file_location(
    "survey_admission", Path(__file__).parents[1] / "tools" / "survey_admission.py"
)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)

BYTES_LOCAL = _MODULE.BYTES_LOCAL
BYTES_LOCATOR_UNTESTED = _MODULE.BYTES_LOCATOR_UNTESTED
BYTES_NO_LOCATOR = _MODULE.BYTES_NO_LOCATOR
BYTES_RETRIEVAL_FAILED = _MODULE.BYTES_RETRIEVAL_FAILED
BYTES_RETRIEVED = _MODULE.BYTES_RETRIEVED
CHECK_ABSENT = _MODULE.CHECK_ABSENT
CHECK_MATCH = _MODULE.CHECK_MATCH
CHECK_MISMATCH = _MODULE.CHECK_MISMATCH
CHECK_UNCHECKED = _MODULE.CHECK_UNCHECKED
PACKAGE_ABSENT = _MODULE.PACKAGE_ABSENT
PACKAGE_PRESENT = _MODULE.PACKAGE_PRESENT
PACKAGE_UNPARSEABLE = _MODULE.PACKAGE_UNPARSEABLE
Approved = _MODULE.Approved
NetworkProbe = _MODULE.NetworkProbe
PinnedHTTPSConnection = _MODULE.PinnedHTTPSConnection
pinned_connection = _MODULE.pinned_connection
PathRefusal = _MODULE.PathRefusal
ProbeOutcome = _MODULE.ProbeOutcome
Refused = _MODULE.Refused
PinningUnavailable = _MODULE.PinningUnavailable
byte_locator = _MODULE.byte_locator
preflight = _MODULE.preflight
render_report = _MODULE.render_report
resolve_declared_path = _MODULE.resolve_declared_path
survey = _MODULE.survey
to_artifact = _MODULE.to_artifact
validate_scratch = _MODULE.validate_scratch

SHA_OF_ABC = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


# ---------------------------------------------------------------------------
# Building a synthetic corpus
# ---------------------------------------------------------------------------


def write_record(
    records: Path,
    name: str,
    *,
    package: dict[str, Any] | str | None = None,
    frontmatter: dict[str, Any] | None = None,
) -> Path:
    directory = records / name
    directory.mkdir(parents=True)
    if frontmatter is not None:
        directory.joinpath("entity.md").write_text(f"---\n{yaml.safe_dump(frontmatter)}---\n\nbody\n")
    if isinstance(package, str):
        directory.joinpath("datapackage.yaml").write_text(package)
    elif package is not None:
        directory.joinpath("datapackage.yaml").write_text(yaml.safe_dump(package))
    return directory


def write_payload(payloads: Path, dataset: str, relative: str, content: bytes) -> Path:
    target = payloads / dataset / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content)
    return target


@pytest.fixture
def roots(tmp_path: Path) -> tuple[Path, Path, Path]:
    records = tmp_path / "records"
    payloads = tmp_path / "payloads"
    scratch = tmp_path / "scratch"
    for path in (records, payloads, scratch):
        path.mkdir()
    return records, payloads, scratch


# ---------------------------------------------------------------------------
# The three axes
# ---------------------------------------------------------------------------


def test_local_bytes_matching_the_record_report_match_on_both_axes(roots: tuple[Path, Path, Path]) -> None:
    records, payloads, _ = roots
    write_record(
        records,
        "d",
        package={"resources": [{"path": "a.txt", "hash": f"sha256:{SHA_OF_ABC}", "bytes": 3}]},
    )
    write_payload(payloads, "d", "a.txt", b"abc")

    result = survey(records, payloads)

    [resource] = result.resources
    assert resource.byte_observation == BYTES_LOCAL
    assert resource.hash_result == CHECK_MATCH
    assert resource.byte_count_result == CHECK_MATCH


def test_the_two_integrity_axes_are_independent(roots: tuple[Path, Path, Path]) -> None:
    """A digest can disagree while the byte count agrees, and the row must say so."""
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "a.txt", "hash": "sha256:" + "0" * 64, "bytes": 3}]})
    write_payload(payloads, "d", "a.txt", b"abc")

    [resource] = survey(records, payloads).resources

    assert resource.hash_result == CHECK_MISMATCH
    assert resource.byte_count_result == CHECK_MATCH


def test_a_byte_count_can_disagree_while_the_digest_agrees(roots: tuple[Path, Path, Path]) -> None:
    """The mirror of the case above, and the reason the count is its own axis.

    A recorded byte count that contradicts bytes whose digest matches is a defect
    in the record, not in the bytes — and folding the two axes together would
    report it as agreement.
    """
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "a.txt", "hash": f"sha256:{SHA_OF_ABC}", "bytes": 99}]})
    write_payload(payloads, "d", "a.txt", b"abc")

    [resource] = survey(records, payloads).resources

    assert resource.hash_result == CHECK_MATCH
    assert resource.byte_count_result == CHECK_MISMATCH
    assert resource.observed_bytes == 3


def test_a_probe_reports_a_byte_count_mismatch_too(roots: tuple[Path, Path, Path]) -> None:
    records, payloads, _ = roots
    write_record(records, "d", package=_remote_package("https://a.example/x.bin"))
    probe = RecordingProbe({"https://a.example/x.bin": ProbeOutcome(BYTES_RETRIEVED, digest=SHA_OF_ABC, size=99)})

    [resource] = survey(records, payloads, probe).resources

    assert resource.hash_result == CHECK_MATCH
    assert resource.byte_count_result == CHECK_MISMATCH


def test_bytes_present_with_no_recorded_hash_is_absent_not_match(roots: tuple[Path, Path, Path]) -> None:
    """Required case 3. Obtained and unpinned is neither a match nor a mismatch:
    nothing in the record says which bytes are the right ones."""
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "a.txt"}]})
    write_payload(payloads, "d", "a.txt", b"abc")

    [resource] = survey(records, payloads).resources

    assert resource.byte_observation == BYTES_LOCAL
    assert resource.hash_result == CHECK_ABSENT
    assert resource.byte_count_result == CHECK_ABSENT
    assert resource.observed_hash == SHA_OF_ABC


def test_a_resource_with_no_bytes_and_no_locator_is_reported_as_such(roots: tuple[Path, Path, Path]) -> None:
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "gone.txt", "hash": "sha256:" + "0" * 64}]})

    [resource] = survey(records, payloads).resources

    assert resource.byte_observation == BYTES_NO_LOCATOR
    assert resource.hash_result == CHECK_UNCHECKED
    assert resource.byte_count_result == CHECK_UNCHECKED


def test_bytes_resolve_against_the_payload_root_as_well_as_the_record_root(
    roots: tuple[Path, Path, Path],
) -> None:
    """The split root is a property of the corpus and a place the instrument can
    silently under-count, so it is asserted rather than assumed."""
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "nested/a.txt", "hash": f"sha256:{SHA_OF_ABC}"}]})
    write_payload(payloads, "d", "nested/a.txt", b"abc")

    [resource] = survey(records, payloads).resources

    assert resource.byte_observation == BYTES_LOCAL
    assert resource.hash_result == CHECK_MATCH


# ---------------------------------------------------------------------------
# The dataset collection — the denominator that must survive
# ---------------------------------------------------------------------------


def test_no_package_with_undeclared_payload_bytes(roots: tuple[Path, Path, Path]) -> None:
    """Required case 1, and the mirror image of a hash with no bytes.

    The record must still appear, and no basis may be derived from bytes it never
    declared.
    """
    records, payloads, _ = roots
    write_record(records, "d", frontmatter={"kind": "dataset", "origin": "external"})
    write_payload(payloads, "d", "stray.bin", b"abc")

    result = survey(records, payloads)

    [dataset] = result.datasets
    assert dataset.package_state == PACKAGE_ABSENT
    assert dataset.declared_resource_count == 0
    assert dataset.unmatched_payload_files == ["d/stray.bin"]
    assert result.resources == []
    # No basis is derived from the undeclared bytes: the evidence reports only
    # what the record states, and it states no digest.
    assert dataset.basis_evidence.declared_resources_with_digest == 0
    assert dataset.basis_evidence.authority_and_provenance == {"origin": "external"}


def test_an_unparseable_package_yields_a_dataset_row_and_a_failure(roots: tuple[Path, Path, Path]) -> None:
    """Required case 2. A silent skip would shrink the denominator without saying so."""
    records, payloads, _ = roots
    write_record(records, "d", package="resources: [oh: [dear\n")

    result = survey(records, payloads)

    [dataset] = result.datasets
    assert dataset.package_state == PACKAGE_UNPARSEABLE
    assert dataset.declared_resource_count == 0
    [failure] = result.failures
    assert failure.path == "d/datapackage.yaml"
    assert failure.reason


def test_a_resource_entry_without_a_path_is_a_failure_not_a_silent_drop(
    roots: tuple[Path, Path, Path],
) -> None:
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"name": "nameless"}]})

    result = survey(records, payloads)

    [dataset] = result.datasets
    assert dataset.package_state == PACKAGE_UNPARSEABLE
    assert result.resources == []
    assert "declares no path" in result.failures[0].reason


def test_declared_bytes_are_not_reported_as_unmatched(roots: tuple[Path, Path, Path]) -> None:
    """The unmatched list is the evidence for undeclared bytes; a declared
    resource appearing in it would manufacture the very finding it exists to make."""
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "a.txt"}]})
    write_payload(payloads, "d", "a.txt", b"abc")
    write_payload(payloads, "d", "b.txt", b"abc")

    [dataset] = survey(records, payloads).datasets

    assert dataset.unmatched_payload_files == ["d/b.txt"]


def test_a_payload_copy_of_a_declared_resource_is_not_unmatched(
    roots: tuple[Path, Path, Path],
) -> None:
    """Claims are declared relative paths, not the file that won resolution.

    With copies under both roots the record-root copy resolves first; recording
    that absolute path as the claim left the payload copy looking undeclared.
    """
    records, payloads, _ = roots
    directory = write_record(records, "d", package={"resources": [{"path": "crosswalk.csv"}]})
    directory.joinpath("crosswalk.csv").write_bytes(b"abc")
    write_payload(payloads, "d", "crosswalk.csv", b"abc")

    [dataset] = survey(records, payloads).datasets

    assert dataset.unmatched_payload_files == []


def test_a_symlinked_payload_directory_is_refused_not_walked(roots: tuple[Path, Path, Path]) -> None:
    """The door, not just the children.

    Guarding only the entries *inside* the payload directory leaves the case
    where the dataset's directory is itself the link: every file behind it then
    enumerates as though it sat inside the payload root. Here `outside/secret.bin`
    is reachable that way, and must not appear.
    """
    records, payloads, _ = roots
    outside = payloads.parent / "outside"
    outside.mkdir()
    (outside / "secret.bin").write_bytes(b"abc")
    write_record(records, "d", package={"resources": [{"path": "a.txt"}]})
    (payloads / "d").symlink_to(outside, target_is_directory=True)

    result = survey(records, payloads)

    [dataset] = result.datasets
    assert dataset.unmatched_payload_files == [], "a file outside the payload root was enumerated as inside it"
    assert not any("secret.bin" in name for name in dataset.unmatched_payload_files)
    # Refused, and said so: a silent skip reads as a dataset with no undeclared
    # bytes, which is a finding rather than a gap.
    [failure] = result.failures
    assert (failure.root, failure.path) == ("payloads", "d")
    assert "symlink" in failure.reason


def test_a_symlinked_record_directory_is_not_walked_either(roots: tuple[Path, Path, Path]) -> None:
    records, payloads, _ = roots
    outside = records.parent / "outside-record"
    outside.mkdir()
    (outside / "entity.md").write_text("---\nkind: dataset\n---\n")
    (records / "linked").symlink_to(outside, target_is_directory=True)

    assert survey(records, payloads).datasets == []


def test_basis_evidence_records_what_the_record_states(roots: tuple[Path, Path, Path]) -> None:
    records, payloads, _ = roots
    write_record(
        records,
        "d",
        package={"resources": [{"path": "a.txt", "hash": "sha256:" + "0" * 64}, {"path": "b.txt"}]},
        frontmatter={
            "kind": "dataset",
            "origin": "external",
            "accessions": ["GEO: GSE1"],
            "access": {"level": "public", "source_url": "https://example.org/study"},
        },
    )

    [dataset] = survey(records, payloads).datasets

    # An accession and a source URL are authority-side, not content basis: they
    # name a work and a page, and neither pins bytes.
    assert dataset.basis_evidence.authority_and_provenance == {
        "origin": "external",
        "accessions": ["GEO: GSE1"],
        "access.source_url": "https://example.org/study",
    }
    assert dataset.basis_evidence.declared_resources_with_digest == 1


def test_an_unreadable_entity_still_yields_a_dataset_row(roots: tuple[Path, Path, Path]) -> None:
    records, payloads, _ = roots
    directory = write_record(records, "d", package={"resources": []})
    directory.joinpath("entity.md").write_text("no frontmatter here\n")

    result = survey(records, payloads)

    assert len(result.datasets) == 1
    assert result.datasets[0].basis_evidence.authority_and_provenance == {}
    assert result.failures[0].path == "d/entity.md"


# ---------------------------------------------------------------------------
# Local declared paths
# ---------------------------------------------------------------------------


def test_an_absolute_declared_path_is_refused(tmp_path: Path) -> None:
    refusal = resolve_declared_path(tmp_path, "d", "/etc/passwd")
    assert isinstance(refusal, PathRefusal)
    assert "absolute" in refusal.reason


def test_an_upward_traversing_declared_path_is_refused(tmp_path: Path) -> None:
    refusal = resolve_declared_path(tmp_path, "d", "../../etc/passwd")
    assert isinstance(refusal, PathRefusal)
    assert "traverses upward" in refusal.reason


def test_a_symlink_escaping_declared_path_is_refused(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_bytes(b"abc")
    dataset = tmp_path / "root" / "d"
    dataset.mkdir(parents=True)
    (dataset / "link").symlink_to(outside)

    refusal = resolve_declared_path(tmp_path / "root", "d", "link/secret.txt")

    assert isinstance(refusal, PathRefusal)
    assert "symlink" in refusal.reason


def test_an_escaping_path_is_untested_rather_than_read(roots: tuple[Path, Path, Path]) -> None:
    """Required case 5, at the survey level: refused before any read, and the
    refusal is a question not asked rather than a finding about the resource."""
    records, payloads, _ = roots
    outside = records.parent / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_bytes(b"abc")
    directory = write_record(records, "d", package={"resources": [{"path": "link/secret.txt"}]})
    (directory / "link").symlink_to(outside)

    [resource] = survey(records, payloads).resources

    assert resource.byte_observation == BYTES_LOCATOR_UNTESTED
    assert "symlink" in (resource.reason or "")
    assert resource.observed_hash is None


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------


def test_an_unapproved_scheme_is_refused_at_preflight() -> None:
    decision = preflight("http://example.org/a.bin", lambda _h, _p: ["93.184.216.34"])
    assert isinstance(decision, Refused)
    assert "scheme http" in decision.reason


def test_a_private_destination_is_refused_at_preflight() -> None:
    decision = preflight("https://internal.example/a.bin", lambda _h, _p: ["10.0.0.5"])
    assert isinstance(decision, Refused)
    assert "non-public" in decision.reason


def test_loopback_and_link_local_are_refused() -> None:
    for address in ("127.0.0.1", "169.254.1.1", "::1"):
        decision = preflight("https://host.example/a.bin", lambda _h, _p, a=address: [a])
        assert isinstance(decision, Refused), address


def test_one_private_address_among_several_refuses_the_whole_locator() -> None:
    """Checking only the address that happens to be chosen would leave the others
    reachable through ordinary resolution ordering."""
    decision = preflight("https://host.example/a.bin", lambda _h, _p: ["93.184.216.34", "10.0.0.5"])
    assert isinstance(decision, Refused)


def test_an_approved_locator_carries_the_validated_address() -> None:
    decision = preflight("https://host.example/dir/a.bin?v=1", lambda _h, _p: ["93.184.216.34"])
    assert isinstance(decision, Approved)
    assert (decision.host, decision.port, decision.address) == ("host.example", 443, "93.184.216.34")
    assert decision.path == "/dir/a.bin?v=1"


# ---------------------------------------------------------------------------
# Probing: preflight refusal, retrieval failure, and the fail-closed arm
# ---------------------------------------------------------------------------


class RecordingProbe:
    """A probe that records every URL it was asked to fetch."""

    def __init__(self, outcomes: dict[str, ProbeOutcome]) -> None:
        self.outcomes = outcomes
        self.asked: list[str] = []

    def fetch(self, url: str) -> ProbeOutcome:
        self.asked.append(url)
        return self.outcomes[url]


def _remote_package(url: str) -> dict[str, Any]:
    return {
        "resources": [
            {"path": "a.bin", "hash": f"sha256:{SHA_OF_ABC}", "bytes": 3, "source": {"type": "remote", "ref": url}}
        ]
    }


def test_a_preflight_refusal_and_a_retrieval_failure_are_never_collapsed(
    roots: tuple[Path, Path, Path],
) -> None:
    """Required case 4. The same resource shape yields two different axis values,
    because one was never attempted and the other was."""
    records, payloads, _ = roots
    write_record(records, "refused", package=_remote_package("https://a.example/x.bin"))
    write_record(records, "failed", package=_remote_package("https://b.example/x.bin"))
    probe = RecordingProbe(
        {
            "https://a.example/x.bin": ProbeOutcome(BYTES_LOCATOR_UNTESTED, reason="scheme ftp is not approved"),
            "https://b.example/x.bin": ProbeOutcome(BYTES_RETRIEVAL_FAILED, reason="status 503"),
        }
    )

    by_dataset = {r.dataset: r for r in survey(records, payloads, probe).resources}

    assert by_dataset["refused"].byte_observation == BYTES_LOCATOR_UNTESTED
    assert by_dataset["failed"].byte_observation == BYTES_RETRIEVAL_FAILED
    for resource in by_dataset.values():
        assert resource.reason
        assert resource.probed_at
        assert resource.hash_result == CHECK_UNCHECKED


def test_a_successful_probe_is_compared_and_stamped(roots: tuple[Path, Path, Path]) -> None:
    records, payloads, _ = roots
    write_record(records, "d", package=_remote_package("https://a.example/x.bin"))
    probe = RecordingProbe({"https://a.example/x.bin": ProbeOutcome(BYTES_RETRIEVED, digest=SHA_OF_ABC, size=3)})

    [resource] = survey(records, payloads, probe).resources

    assert resource.byte_observation == BYTES_RETRIEVED
    assert resource.hash_result == CHECK_MATCH
    assert resource.byte_count_result == CHECK_MATCH
    assert resource.probed_at


def test_a_retrieved_mismatch_is_not_a_retrieval_failure(roots: tuple[Path, Path, Path]) -> None:
    """A retrieval that succeeds and disagrees with the record is the most
    informative result the run can produce, and must not read as a failure to look."""
    records, payloads, _ = roots
    write_record(records, "d", package=_remote_package("https://a.example/x.bin"))
    probe = RecordingProbe({"https://a.example/x.bin": ProbeOutcome(BYTES_RETRIEVED, digest="0" * 64, size=3)})

    [resource] = survey(records, payloads, probe).resources

    assert resource.byte_observation == BYTES_RETRIEVED
    assert resource.hash_result == CHECK_MISMATCH


def test_without_a_probe_a_remote_locator_is_untested_and_never_fetched(
    roots: tuple[Path, Path, Path],
) -> None:
    records, payloads, _ = roots
    write_record(records, "d", package=_remote_package("https://a.example/x.bin"))

    [resource] = survey(records, payloads, None).resources

    assert resource.byte_observation == BYTES_LOCATOR_UNTESTED
    assert resource.reason == "no probe was run"


def test_a_local_source_ref_is_not_a_byte_locator() -> None:
    """`{type: local, ref: ...}` is acquisition provenance for the build, not a
    way to retrieve the published resource."""
    assert byte_locator({"source": {"type": "local", "ref": "/build/out/a.bin"}}, "a.bin") is None
    assert byte_locator({"source": {"type": "remote", "ref": "not-a-url"}}, "a.bin") is None
    assert byte_locator({"source": {"type": "remote", "ref": "https://a.example/x"}}, "a.bin") == "https://a.example/x"


def test_a_url_valued_declared_path_is_the_resource_s_byte_locator() -> None:
    """The defect this guards cost every remote resource in the predecessor's
    store its locator: they are declared by URL in `path`, not in `source`."""
    url = "https://ftp.example.org/series/GSE1_matrix.txt.gz"
    assert byte_locator({}, url) == url
    # And it wins over a source that says nothing useful.
    assert byte_locator({"source": {"type": "local", "ref": "/build/x"}}, url) == url


def test_the_pinned_connection_dials_the_validated_address_and_validates_the_name(
    monkeypatch: Any,
) -> None:
    """The whole point of pinning, asserted against the real connection code.

    Connecting to the validated address is worthless if the TLS handshake then
    validates against that address instead of the name, and validating the name
    is worthless if the socket dials whatever a second resolution returns. Both
    halves are checked here, on `PinnedHTTPSConnection.connect` itself.
    """
    dialled: list[tuple[str, int]] = []
    wrapped: list[str] = []
    sentinel = object()

    class FakeContext:
        check_hostname = True
        verify_mode = ssl.CERT_REQUIRED

        def wrap_socket(self, sock: Any, *, server_hostname: str) -> Any:
            assert sock is sentinel
            wrapped.append(server_hostname)
            return sentinel

    monkeypatch.setattr(
        _MODULE.socket, "create_connection", lambda address, timeout: dialled.append(address) or sentinel
    )

    connection = PinnedHTTPSConnection("host.example", "93.184.216.34", 443, 5.0, FakeContext())
    connection.connect()

    assert dialled == [("93.184.216.34", 443)], "the socket must dial the address preflight validated"
    assert wrapped == ["host.example"], "TLS must still validate the certificate against the name"


@pytest.mark.parametrize(
    "check_hostname,verify_mode",
    [(False, ssl.CERT_REQUIRED), (True, ssl.CERT_NONE), (False, ssl.CERT_NONE)],
)
def test_a_context_that_would_skip_validation_refuses_to_pin(
    monkeypatch: Any, check_hostname: bool, verify_mode: Any
) -> None:
    """Fail closed at construction. A context that would drop either half of the
    guarantee is not a connection to make; it is a locator to leave untested."""

    class Lax:
        pass

    context = Lax()
    context.check_hostname = check_hostname  # type: ignore[attr-defined]
    context.verify_mode = verify_mode  # type: ignore[attr-defined]
    monkeypatch.setattr(_MODULE.ssl, "create_default_context", lambda: context)

    approved = Approved(host="host.example", port=443, path="/a.bin", address="93.184.216.34")
    with pytest.raises(PinningUnavailable):
        pinned_connection(approved, 5.0)


def test_a_validated_address_that_cannot_be_pinned_issues_no_request(monkeypatch: Any, tmp_path: Path) -> None:
    """Required case 6, and the assertion that matters is the second one.

    A test checking only the reported value would pass against an implementation
    that fetched anyway, which is exactly the failure being guarded. The refusal
    is injected through the connection seam, so the probe's own request path runs.
    """
    dialled: list[Any] = []

    def refuse_to_pin(approved: Any, timeout: float) -> Any:
        raise PinningUnavailable("cannot pin the validated address with hostname validation intact")

    def forbidden(*args: Any, **kwargs: Any) -> None:
        dialled.append(args)
        raise AssertionError("a socket was opened after pinning was unavailable")

    monkeypatch.setattr(_MODULE.socket, "create_connection", forbidden)

    probe = NetworkProbe(tmp_path / "scratch", resolver=lambda _h, _p: ["93.184.216.34"], connect=refuse_to_pin)
    outcome = probe.fetch("https://host.example/a.bin")

    assert outcome.byte_observation == BYTES_LOCATOR_UNTESTED
    assert "pin the validated address" in (outcome.reason or "")
    assert dialled == []


def test_a_refused_redirect_hop_ends_the_attempt_as_untested(tmp_path: Path) -> None:
    """The first URL's approval says nothing about where it lands."""
    probe = NetworkProbe(
        tmp_path / "scratch",
        resolver=lambda _h, _p: ["93.184.216.34"],
        connect=lambda approved, timeout: _RedirectingConnection("http://a.example/two"),
    )
    outcome = probe.fetch("https://a.example/one")

    assert outcome.byte_observation == BYTES_LOCATOR_UNTESTED
    assert "scheme http is not approved" in (outcome.reason or "")
    assert "redirect hop" in (outcome.reason or "")


# ---------------------------------------------------------------------------
# Scratch safety, root identity, and the artifact
# ---------------------------------------------------------------------------


def test_a_scratch_root_inside_a_corpus_root_is_refused(tmp_path: Path) -> None:
    records = tmp_path / "records"
    payloads = tmp_path / "payloads"
    for path in (records, payloads):
        path.mkdir()

    for scratch in (records, records / "nested", payloads / "deep" / "nested"):
        with pytest.raises(SystemExit):
            validate_scratch(scratch, records, payloads)

    validate_scratch(tmp_path / "elsewhere", records, payloads)


def test_root_identity_moves_with_observed_content_and_not_with_location(
    tmp_path: Path,
) -> None:
    def build(where: Path, content: bytes) -> tuple[str, str]:
        records, payloads = where / "records", where / "payloads"
        for path in (records, payloads):
            path.mkdir(parents=True)
        write_record(records, "d", package={"resources": [{"path": "a.txt"}]})
        write_payload(payloads, "d", "a.txt", content)
        result = survey(records, payloads)
        return result.record_root_identity, result.payload_root_identity

    here = build(tmp_path / "here", b"abc")
    same_elsewhere = build(tmp_path / "there", b"abc")
    changed = build(tmp_path / "changed", b"different")

    assert here == same_elsewhere, "identity must not depend on where the roots sit"
    assert here[1] != changed[1], "identity must move when observed payload content moves"


def test_the_artifact_holds_every_unit_level_observation(roots: tuple[Path, Path, Path]) -> None:
    records, payloads, _ = roots
    write_record(records, "declared", package={"resources": [{"path": "a.txt"}]})
    write_payload(payloads, "declared", "a.txt", b"abc")
    write_record(records, "silent", frontmatter={"kind": "dataset"})
    write_payload(payloads, "silent", "stray.bin", b"abc")
    write_record(records, "broken", package="resources: [oh: [dear\n")

    artifact = to_artifact(survey(records, payloads))

    assert [d["dataset"] for d in artifact["datasets"]] == ["broken", "declared", "silent"]
    assert len(artifact["resources"]) == 1
    assert len(artifact["failures"]) == 1
    assert artifact["record_root_identity"].startswith("sha256:")
    assert artifact["probed"] is False


def test_the_report_renders_from_the_artifact(roots: tuple[Path, Path, Path]) -> None:
    """Rendering from the artifact is what keeps prose and data from drifting, so
    the report must reflect an artifact it is handed rather than a survey it re-runs."""
    records, payloads, _ = roots
    write_record(records, "d", package={"resources": [{"path": "a.txt", "hash": "sha256:" + "0" * 64}]})
    write_payload(payloads, "d", "a.txt", b"abc")

    artifact = to_artifact(survey(records, payloads))
    report = render_report(artifact)

    assert "Mismatches: 1" in report
    assert "d/a.txt" in report

    artifact["resources"] = []
    artifact["datasets"] = []
    assert "Mismatches: 0" in render_report(artifact)


class _RedirectingConnection:
    """A connection that answers every request with one relative redirect."""

    def __init__(self, location: str) -> None:
        self._location = location

    def request(self, method: str, path: str, headers: dict[str, str]) -> None:
        del method, path, headers

    def getresponse(self) -> Any:
        return _Response(302, {"Location": self._location})

    def close(self) -> None:
        pass


class _Response:
    def __init__(self, status: int, headers: dict[str, str]) -> None:
        self.status = status
        self._headers = headers

    def getheader(self, name: str) -> str | None:
        return self._headers.get(name)


def test_a_relative_redirect_is_resolved_before_it_is_revalidated(tmp_path: Path) -> None:
    """A bare `Location: /two` is not a URL. Revalidating it unjoined would test
    a string with no scheme and no host, so every relative redirect would look
    like an unapproved locator rather than being followed to its real target."""
    probe = NetworkProbe(
        tmp_path / "scratch",
        resolver=lambda _h, _p: ["93.184.216.34"],
        connect=lambda approved, timeout: _RedirectingConnection("/two"),
        max_redirects=1,
    )

    outcome = probe.fetch("https://a.example/one")

    # Joined against its origin the hop is https://a.example/two, which clears
    # preflight and is followed until the redirect budget runs out.
    assert outcome.byte_observation == BYTES_RETRIEVAL_FAILED
    assert outcome.reason == "too many redirects"
