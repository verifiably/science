import hashlib

import pytest

from beliefs.holdings.acquisition_log import log_summary, render_acquisition_log
from science.acquisition.bounds import AcquisitionBounds
from science.acquisition.journal import Journal, locked_directory
from science.refusal import Refused

RAW = b'{"title":"test","locator":"instrument:fixture","resources":[{"name":"ok","url":"https://host/a"},{"name":"b","url":"https://host/b"}]}'
DIGEST = "sha256:" + hashlib.sha256(b"hello").hexdigest()


def create(work):
    return Journal.create(work, RAW, AcquisitionBounds(), protected=())


def failure(j):
    j.append("attempt-open", seq=2, started_at="start")
    j.append("attempt-close", seq=2, completed_at="end", outcome="failed", failure="timeout")


@pytest.mark.parametrize("cut_open", [True, False])
def test_renewed_budget_and_exact_partial_history(certified_work, cut_open):
    j = create(certified_work)
    with locked_directory(j.path, "set-busy"):
        j.append("attempt-open", seq=1, started_at="start")
        j.append("attempt-close", seq=1, completed_at="end", outcome="fetched", digest=DIGEST, size=5)
        for _ in range(3):
            failure(j)
        assert j.requests[1].state == "failed"
        j.append("budget-renewed", seq=2)
        assert Journal.open(certified_work, j.path.name).requests[1].state == "pending"
        with pytest.raises(Refused):
            j.append("budget-renewed", seq=2)
        failure(j)
        if cut_open:
            j.append("attempt-open", seq=2, started_at="last")
    for _ in range(2):
        j = Journal.open(certified_work, j.path.name)
        assert j.requests[1].state == "pending"
    with locked_directory(j.path, "set-busy"):
        j.append("abandoned", seq=2)
    log = j.acquisition_log()
    assert [a.outcome for a in log.lines[1].attempts] == ["failed"] * 4 + (["interrupted"] if cut_open else [])
    summary = log_summary(log)
    assert (summary.fetched, summary.abandoned, summary.failed) == (1, 1, 0)
    assert summary.log == "sha256:" + hashlib.sha256(render_acquisition_log(log)).hexdigest()


def test_torn_tail_and_committed_corruption(certified_work):
    j = create(certified_work)
    journal = j.path / "journal.v1"
    before = journal.read_bytes()
    with journal.open("ab") as handle:
        handle.write(b'{"event"')
    assert Journal.open(certified_work, j.path.name).requests[0].state == "pending"
    assert journal.read_bytes() != before
    with locked_directory(j.path, "set-busy"):
        Journal.open(certified_work, j.path.name, repair=True)
    assert journal.read_bytes() == before
    with journal.open("ab") as handle:
        handle.write(b'bad\n')
    with pytest.raises(Refused, match="line 4"):
        Journal.open(certified_work, j.path.name)


def test_busy_lock_and_tampered_inputs(certified_work):
    j = create(certified_work)
    with locked_directory(j.path, "set-busy"), pytest.raises(Refused, match="set-busy"):
        with locked_directory(j.path, "set-busy"):
            pass
    (j.path / "plan.json").write_bytes(RAW.replace(b'"test"', b'"changed"'))
    with pytest.raises(Refused, match="digest"):
        Journal.open(certified_work, j.path.name)


def test_invalid_set_and_overlap_refused_before_creation(certified_work):
    with pytest.raises(Refused, match="token"):
        Journal.open(certified_work, "../escape")
    with pytest.raises(Refused, match="overlap"):
        Journal.create(certified_work / "store" / "ops", RAW, AcquisitionBounds(), protected=(certified_work / "store",))
    assert not (certified_work / "store").exists()
