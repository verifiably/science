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
        j.append("partial")
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


def test_an_unmatched_open_during_seal_is_pending(certified_work):
    from science.acquisition.operator import _status
    j = create(certified_work)
    with locked_directory(j.path, "set-busy"):
        j.append("attempt-open", seq=1, started_at="lost")
    with locked_directory(j.path, "set-busy"):
        status = _status(certified_work, j.path.name)
        assert status["active"] == 0 and status["pending"] == 2


def test_redirected_config_root_refuses_before_creating_set(certified_work, monkeypatch):
    from science.acquisition.operator import operate
    monkeypatch.setattr("science.acquisition.operator.retrieve_set", lambda *_: pytest.fail("entered retrieval"))
    from argparse import Namespace
    from test_config import write_config
    true_root = certified_work / "other"
    true_root.mkdir()
    alias = certified_work / "alias"
    alias.symlink_to(true_root)
    config = write_config(certified_work, operations_root=alias)
    plan = certified_work / "plan"
    plan.write_bytes(RAW)
    args = Namespace(command="acquire-start", config=config, plan=plan,
                     **dict.fromkeys(AcquisitionBounds.__dataclass_fields__))
    with pytest.raises(Refused, match="redirect"):
        operate(args)
    assert not (true_root / "acquisitions").exists()


@pytest.mark.parametrize("invalid", [
    "all-pending", "partial-pending", "failed-without-partial", "no-fetched",
    "log", "tree", "dataset", "origin", "title", "locator",
])
def test_reopen_refuses_invalid_sealing_row_at_its_position(certified_work, invalid):
    from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
    from beliefs.identity import v1

    j = create(certified_work)
    if invalid not in ("all-pending", "no-fetched"):
        j.append("attempt-open", seq=1, started_at="start")
        j.append("attempt-close", seq=1, completed_at="end", outcome="fetched", digest=DIGEST, size=5)
    if invalid == "no-fetched":
        for seq in (1, 2):
            j.append("attempt-open", seq=seq, started_at="start")
            j.append("attempt-close", seq=seq, completed_at="refused", outcome="not-attempted", failure="scheme")
    elif invalid == "partial-pending":
        j.append("partial")
    elif invalid != "all-pending":
        for _ in range(3):
            failure(j)
        if invalid != "failed-without-partial":
            j.append("partial")
    row = dict(event="sealing", store="1" * 32, corpus="2" * 32, invocation="seal", session="3" * 32,
               log=DIGEST, tree="sha256-tree:" + "4" * 64, dataset="dataset:" + "5" * 64,
               origin="fetched", title="test", locator="instrument:fixture")
    if invalid in ("log", "tree", "dataset", "origin", "title", "locator", "failed-without-partial"):
        summary = log_summary(j.acquisition_log())
        row.update(log=summary.log, tree=summary.tree,
                   dataset=dataset_address(DatasetDeclaration((ResourceDeclaration("data", summary.tree),))))
        if invalid != "failed-without-partial":
            row[invalid] += "-changed"
    path = j.path / "journal.v1"
    with path.open("ab") as handle:
        handle.write(v1.encode(row) + b"\n")
    before = path.read_bytes()
    with pytest.raises(Refused, match=f"journal line {j.position + 1}:"):
        Journal.open(certified_work, j.path.name, repair=True)
    assert path.read_bytes() == before
