from collections import deque
from dataclasses import replace
from io import BytesIO

import pytest

from beliefs.holdings.transport import UrlSeam
from science.acquisition.bounds import AcquisitionBounds
from science.acquisition.journal import Journal, locked_directory
from science.acquisition.retrieve import retrieve_set
from science.refusal import Refused


class Clock:
    def __init__(self):
        self.t = 0.0

    def sleep(self, seconds):
        self.t += seconds


class Response(BytesIO):
    def __init__(self, status, data, headers):
        super().__init__(data)
        self.status = status
        self.headers = headers

    def getheader(self, name):
        return self.headers.get(name)


class Connection:
    def __init__(self, response):
        self.response = response

    def request(self, method, target, headers):
        assert method == "GET"

    def getresponse(self):
        return self.response

    def close(self):
        self.response.close()


RAW = b'{"title":"t","locator":"accession:x","resources":[{"name":"a","url":"https://a.org/start"}]}'


def run(journal, script, clock):
    contacts = []
    replies = deque(script)

    def connect(hop, timeout):
        contacts.append((hop.host, clock.t))
        return Connection(Response(*replies.popleft()))

    seam = UrlSeam(lambda host, port: ["1.1.1.1"], connect)
    with locked_directory(journal.path, "set-busy"):
        retrieve_set(journal, seam=seam, monotonic=lambda: clock.t, sleep=clock.sleep)
    assert not replies
    return contacts


def test_redirected_retry_after_and_rehash(certified_work):
    j = Journal.create(certified_work, RAW, AcquisitionBounds(), protected=())
    clock = Clock()
    redirect = (302, b"", {"Location": "https://b.org/file"})
    replies = [redirect, (429, b"", {"Retry-After": "4"}), redirect, (200, b"xy", {})]
    assert run(j, replies, clock) == [("a.org", 0), ("b.org", 0), ("a.org", 4), ("b.org", 4)]
    assert j.requests[0].size == 2 and j.requests[0].expanded
    assert run(j, [], clock) == []
    digest = j.requests[0].digest.split(":")[1]
    obj = j.path / "objects" / digest
    obj.chmod(0o600)
    obj.write_bytes(b"zz")
    with pytest.raises(Refused, match=digest):
        run(j, [], clock)


def test_deterministic_redirect_ends_budget_and_resume_renews_once(certified_work):
    j = Journal.create(certified_work, RAW, AcquisitionBounds(), protected=())
    clock = Clock()
    assert run(j, [(302, b"", {"Location": "http://a.org/data"})], clock) == [("a.org", 0)]
    assert j.requests[0].state == "failed" and clock.t == 0
    assert run(j, [(200, b"ok", {})], clock) == [("a.org", 0)]
    assert [a.outcome for a in j.requests[0].attempts] == ["failed", "fetched"]


def test_bound_and_expected_digest_are_recorded(certified_work):
    bad = RAW.replace(b'"name":"a"', b'"name":"a","expected":"sha256:' + b"0" * 64 + b'"')
    bounds = replace(AcquisitionBounds(), attempts=2, max_total_bytes=1)
    j = Journal.create(certified_work, bad, bounds, protected=())
    run(j, [(200, b"12", {}), (200, b"1", {})], Clock())
    assert [a.failure for a in j.requests[0].attempts] == ["byte-bound", "expected-mismatch"]
    assert not list((j.path / "objects").iterdir())
