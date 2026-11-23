import hashlib

import pytest

from helpers.world import build_belief_world, open_rig
from science.acquisition.bounds import AcquisitionBounds
from science.acquisition.journal import Journal, locked_directory
from science.refusal import Refused

RAW = b'{"title":"local","locator":"instrument:test","resources":[{"name":"good","url":"https://example.org/g"},{"name":"later","url":"https://example.org/l"}]}'


def ready(config):
    j = Journal.create(config.operations_root, RAW, AcquisitionBounds(), protected=(config.write_root, config.store_root))
    with locked_directory(j.path, "set-busy"):
        digest = hashlib.sha256(b"data").hexdigest()
        (j.path / "objects" / digest).write_bytes(b"data")
        j.append("attempt-open", seq=1, started_at="start")
        j.append("attempt-close", seq=1, completed_at="end", outcome="fetched", digest="sha256:" + digest, size=4)
        j.append("expanded", seq=1)
    return j


def test_partial_seal_and_lost_receipt_recover_one_report(certified_work):
    cfg = build_belief_world(certified_work)
    j = ready(cfg)
    with open_rig(cfg, ("acquire-seal",)) as (dispatcher, ctx):
        with locked_directory(j.path, "set-busy"), pytest.raises(Refused, match="set-busy"):
            dispatcher.invoke("acquire-seal", {"set": j.path.name, "accept_partial": True})
        with pytest.raises(Refused, match="partial"):
            dispatcher.invoke("acquire-seal", {"set": j.path.name})
        assert Journal.open(cfg.operations_root, j.path.name).requests[1].state == "pending"
        dispatcher.invoke("acquire-seal", {"set": j.path.name, "accept_partial": True}, invocation_id="first-seal")
        closed = Journal.open(cfg.operations_root, j.path.name)
        assert closed.receipt["report"].startswith("act-report:")
        assert ctx.write_view().holds(closed.receipt["report"])
        assert not list((j.path / "objects").iterdir())
        journal = j.path / "journal.v1"
        rows = journal.read_bytes().splitlines(keepends=True)
        assert b'"event":"sealed"' in rows[-1]
        journal.write_bytes(b"".join(rows[:-1]))
        with pytest.raises(Refused, match="already sealed"):
            dispatcher.invoke("acquire-seal", {"set": j.path.name, "accept_partial": True})
        assert Journal.open(cfg.operations_root, j.path.name).receipt == closed.receipt
        assert len([node for node in ctx.write_view().iter_stored() if node.kind == "act-report"]) == 1


def test_import_preserves_original_journal_and_absent_attempt_fields(certified_work):
    from beliefs.holdings.acquisition_log import AcquisitionLog, LogHeader, Recorded, RequestLine, render_acquisition_log
    from beliefs import stored
    cfg = build_belief_world(certified_work)
    inputs = certified_work / "external"
    members, journals = inputs / "files", inputs / "journals"
    members.mkdir(parents=True)
    journals.mkdir()
    original = b'{"file":"a"}\n'
    (journals / "original.jsonl").write_bytes(original)
    (members / "a").write_bytes(b"file")
    sha = lambda b: "sha256:" + hashlib.sha256(b).hexdigest()
    header = LogHeader("2" * 32, "imported", "recorded/v1", None, (("original.jsonl", sha(original)),))
    line = RequestLine(1, "https://example.org/a", None, None, (), "fetched", sha(b"file"), 4, "a", Recorded(0, 1, None))
    raw = render_acquisition_log(AcquisitionLog(header, (line,)))
    file = inputs / "log.jsonl"
    file.write_bytes(raw)
    args = dict(log=str(file), members=str(members), journals=str(journals), title="Imported", locator="instrument:original")
    with open_rig(cfg, ("acquire-import",)) as (dispatcher, ctx):
        (members / "extra").write_bytes(b"undeclared")
        with pytest.raises(Refused):
            dispatcher.invoke("acquire-import", args | {"title": "discarded"})
        assert not (cfg.operations_root / "acquisitions" / header.set).exists()
        (members / "extra").unlink()
        dispatcher.invoke("acquire-import", args)
        with pytest.raises(Refused, match="already sealed"):
            dispatcher.invoke("acquire-import", args)
        with pytest.raises(Refused, match="bound|collision"):
            dispatcher.invoke("acquire-import", args | {"title":"conflict"})
        reports = [stored.act_report_facet(n) for n in ctx.write_view().iter_stored() if n.kind == "act-report"]
        assert len(reports) == 1
        summary = next(e["outcome"] for e in reports[0]["entries"] if e["kind"] == "acquisition-set")
        assert summary["log"] == sha(raw) and summary["fetched_by"] == "recorded/v1"
    assert (journals / "original.jsonl").read_bytes() == original


def test_bad_import_and_wrong_roots_are_structured_refusals(certified_work):
    cfg = build_belief_world(certified_work)
    log = certified_work / "bad"
    log.write_bytes(b'{}\n')
    with open_rig(cfg, ("acquire-import",)) as (dispatcher, _):
        with pytest.raises(Refused) as error:
            dispatcher.invoke("acquire-import", dict(log=str(log), members=str(certified_work),
                              journals=str(certified_work), title="t", locator="accession:x"), invocation_id="bad")
        assert error.value.refusal.code == "invalid-input" and not dispatcher._session.invocation_acts("bad")


def test_log_metadata_does_not_consume_member_budget(certified_work):
    from dataclasses import replace
    from beliefs.holdings.acquisition_log import AcquisitionLog, LogHeader, Recorded, RequestLine, render_acquisition_log
    cfg = replace(build_belief_world(certified_work), acquire=AcquisitionBounds(max_total_bytes=1))
    journal_dir = certified_work / "originals"
    source_dir = certified_work / "members"
    journal_dir.mkdir()
    source_dir.mkdir()
    journal_bytes = b"original journal line\n"
    (journal_dir / "original").write_bytes(journal_bytes)
    (source_dir / "a").write_bytes(b"a")
    sha = lambda data: "sha256:" + hashlib.sha256(data).hexdigest()
    header = LogHeader("3" * 32, "imported", "recorder", None, (("original", sha(journal_bytes)),))
    line = RequestLine(1, "https://example.org", None, None, (), "fetched", sha(b"a"), 1, "a", Recorded(0, 1, None))
    log = certified_work / "log.jsonl"
    log.write_bytes(render_acquisition_log(AcquisitionLog(header, (line,))))
    with open_rig(cfg, ("acquire-import",)) as (d, _):
        assert "act-report:" in d.invoke("acquire-import", dict(log=str(log), members=str(source_dir),
                    journals=str(journal_dir), title="one", locator="accession:a")).text


@pytest.mark.parametrize("unclosed", [False, True])
def test_seal_renewed_budget_digest_and_governed_counts(certified_work, unclosed):
    import json
    from beliefs import stored
    from beliefs.identity import v1
    from science.acquisition.operator import _status
    cfg = build_belief_world(certified_work)
    j = ready(cfg)
    with locked_directory(j.path, "set-busy"):
        for i in range(4):
            if i == 3:
                j.append("budget-renewed", seq=2)
            j.append("attempt-open", seq=2, started_at=f"start-{i}")
            j.append("attempt-close", seq=2, completed_at=f"end-{i}", outcome="failed", failure="timeout")
        if unclosed:
            j.append("attempt-open", seq=2, started_at="lost")
    assert _status(cfg.operations_root, j.path.name)["pending"] == 1
    with open_rig(cfg, ("acquire-seal",)) as (dispatcher, ctx):
        dispatcher.invoke("acquire-seal", {"set": j.path.name, "accept_partial": True})
        sealed = Journal.open(cfg.operations_root, j.path.name)
        report = stored.act_report_facet(ctx.write_view().get(sealed.receipt["report"]))
    summary = next(entry["outcome"] for entry in report["entries"] if entry["kind"] == "acquisition-set")
    assert (summary["fetched"], summary["failed"], summary["abandoned"]) == (1, 0, 1)
    attempts = [dict(started_at=f"start-{i}", completed_at=f"end-{i}", outcome="failed", failure="timeout") for i in range(4)]
    if unclosed:
        attempts.append(dict(started_at="lost", outcome="interrupted"))
    rows = [dict(format="science.acquisition-log.v1", set=j.path.name, origin="fetched",
                 fetched_by="science/acquire.v1 (beliefs transport)", plan=json.loads(RAW)),
            dict(seq=1, request=dict(method="GET", url="https://example.org/g"), result="fetched", member="good",
                 digest="sha256:" + hashlib.sha256(b"data").hexdigest(), size=4,
                 attempts=[dict(started_at="start", completed_at="end", outcome="fetched")]),
            dict(seq=2, request=dict(method="GET", url="https://example.org/l"), result="abandoned", attempts=attempts)]
    expected = b"".join(v1.encode(row) + b"\n" for row in rows)
    assert (j.path / "acquisition-log.jsonl").read_bytes() == expected
    assert summary["log"] == "sha256:" + hashlib.sha256(expected).hexdigest()


def test_identical_sets_get_separate_reports_with_shared_dataset(certified_work):
    cfg = build_belief_world(certified_work)
    sets = [ready(cfg), ready(cfg)]
    with open_rig(cfg, ("acquire-seal",)) as (dispatcher, _):
        for j in sets:
            dispatcher.invoke("acquire-seal", {"set": j.path.name, "accept_partial": True})
    receipts = [Journal.open(cfg.operations_root, j.path.name).receipt for j in sets]
    assert receipts[0]["report"] != receipts[1]["report"]
    assert receipts[0]["dataset"] == receipts[1]["dataset"]


@pytest.mark.parametrize("directory,name", [
    ("scratch", "retrieve-20261123T120000000000-1234"),
    ("objects", hashlib.sha256(b"uncommitted").hexdigest()),
])
def test_partial_seal_cleans_interrupted_download(certified_work, directory, name):
    cfg = build_belief_world(certified_work)
    journal = ready(cfg)
    journal.append("attempt-open", seq=2, started_at="interrupted")
    private = journal.path / directory
    orphan = private / name
    orphan.write_bytes(b"uncommitted")
    other = private / "operator-notes"
    other.write_bytes(b"keep")
    link = journal.path / "objects" / ("f" * 64)
    link.symlink_to(other)
    with open_rig(cfg, ("acquire-seal",)) as (dispatcher, _):
        args = {"set": journal.path.name, "accept_partial": True}
        dispatcher.invoke("acquire-seal", args)
        assert not orphan.exists()
        assert link.is_symlink() and other.read_bytes() == b"keep"
        orphan.write_bytes(b"cleanup interrupted")
        with pytest.raises(Refused, match="already sealed"):
            dispatcher.invoke("acquire-seal", args)
        assert not orphan.exists()


@pytest.mark.parametrize("allowance", ["below-log", "below-total", "exact"])
def test_import_evidence_admission(certified_work, allowance):
    from dataclasses import replace
    from beliefs.holdings.acquisition_log import AcquisitionLog, LogHeader, Recorded, RequestLine, render_acquisition_log

    originals = certified_work / "journals"
    members = certified_work / "members"
    originals.mkdir()
    members.mkdir()
    (members / "a").write_bytes(b"a")
    def sha(data):
        return "sha256:" + hashlib.sha256(data).hexdigest()
    sources = []
    for name in ("first", "second"):
        (originals / name).write_bytes(b"journal")
        sources.append((name, sha(b"journal")))
    header = LogHeader("4" * 32, "imported", "recorder", None, tuple(sources))
    line = RequestLine(1, "https://example.org", None, None, (), "fetched", sha(b"a"), 1, "a", Recorded(0, 1, None))
    raw = render_acquisition_log(AcquisitionLog(header, (line,)))
    log = certified_work / "log.jsonl"
    log.write_bytes(raw)
    limit = len(raw) + {"below-log": -1, "below-total": 13, "exact": 14}[allowance]
    cfg = replace(build_belief_world(certified_work), max_import_evidence_bytes=limit,
                  acquire=AcquisitionBounds(max_total_bytes=1))
    args = dict(log=str(log), members=str(members), journals=str(originals), title="one", locator="accession:a")
    with open_rig(cfg, ("acquire-import",)) as (dispatcher, _):
        if allowance == "exact":
            assert "act-report:" in dispatcher.invoke("acquire-import", args).text
        else:
            with pytest.raises(Refused, match="max_import_evidence_bytes"):
                dispatcher.invoke("acquire-import", args, invocation_id="over-limit")
            assert not dispatcher._session.invocation_acts("over-limit")
            assert not (cfg.operations_root / "acquisitions" / header.set).exists()
