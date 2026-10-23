"""`fetch` (commons 1a, Task 9): B holds a mounted dataset's bytes from a path or URL, only after the bytes match the
declared digest; every refusal comes before the one act. Nothing here touches the network: `retrieve` is mocked."""
from dataclasses import replace
from hashlib import sha256

import pytest
from helpers.commons import DATA_A, a_identity, read_rig, refused
from helpers.world import open_rig

import science.commands.fetch as fetch_module
from science.config import FetchPolicy, ReadContext
from beliefs.holdings.transport import Failed, Retrieved

DECLARED = "sha256:" + sha256(DATA_A).hexdigest()
URL = "https://data.test/a.txt"


@pytest.fixture
def fetching(reopened):
    """`(rig_for, dataset, cfg)`: B's installation, A's dataset address, and a way to invoke `fetch` on B."""
    dataset = a_identity(reopened.a)["dataset"]
    cfg = reopened.b

    def invoke(source: str, config=cfg):
        with open_rig(config, ("fetch",)) as (d, _):
            return d.invoke("fetch", {"dataset": dataset, "source": source})
    return invoke, dataset, cfg


def _not_held(cfg, dataset):
    assert refused(lambda: ReadContext.open(cfg).held_path(dataset)).code == "invalid-input"


def _retrieved(path, content: bytes) -> Retrieved:
    return Retrieved(digest="sha256:" + sha256(content).hexdigest(), size=len(content), path=path)


def test_fetch_from_a_path_holds_the_mounted_dataset_bytes(reopened, fetching, tmp_path):
    invoke, dataset, cfg = fetching
    _not_held(cfg, dataset)
    outcome = invoke(str(reopened.data_a_path()))
    assert "[holdings-observation]" in outcome.text
    assert ReadContext.open(cfg).held_path(dataset).read_bytes() == DATA_A


def test_fetch_with_mismatching_path_bytes_refuses_and_writes_nothing(reopened, fetching, tmp_path):
    invoke, dataset, cfg = fetching
    wrong = tmp_path / "wrong.txt"
    wrong.write_bytes(b"wrong")
    refusal = refused(lambda: invoke(str(wrong)))
    assert refusal.code == "invalid-input" and DECLARED in refusal.message
    _not_held(cfg, dataset)


def test_fetch_with_mismatching_url_bytes_refuses_and_writes_nothing(reopened, fetching, tmp_path, monkeypatch):
    invoke, dataset, cfg = fetching
    wrong_file = tmp_path / "wrong.bin"
    wrong_file.write_bytes(b"wrong")
    monkeypatch.setattr(fetch_module, "retrieve", lambda *a, **k: _retrieved(wrong_file, b"wrong"))
    refusal = refused(lambda: invoke(URL))
    assert refusal.code == "invalid-input" and DECLARED in refusal.message and not wrong_file.exists()
    _not_held(cfg, dataset)


def test_fetch_from_a_url_stores_matching_bytes(reopened, fetching, tmp_path, monkeypatch):
    invoke, dataset, cfg = fetching
    got_file = tmp_path / "got.bin"
    got_file.write_bytes(DATA_A)
    seen = {}

    def fake(locator, bounds, seam, scratch):
        seen.update(url=locator.url, bounds=bounds)
        return _retrieved(got_file, DATA_A)
    monkeypatch.setattr(fetch_module, "retrieve", fake)
    invoke(URL)
    assert seen["url"] == URL and seen["bounds"].max_bytes > 10**12  # max_bytes 0 is no bound
    assert not got_file.exists()
    assert ReadContext.open(cfg).held_path(dataset).read_bytes() == DATA_A


def test_fetch_from_a_url_that_fails_refuses_with_the_reason(reopened, fetching, monkeypatch):
    invoke, dataset, cfg = fetching
    monkeypatch.setattr(fetch_module, "retrieve", lambda *a, **k: Failed("timeout"))
    refusal = refused(lambda: invoke(URL))
    assert refusal.code == "invalid-input" and "timeout" in refusal.message
    _not_held(cfg, dataset)


def test_fetch_under_records_only_refuses_naming_the_policy(reopened, fetching):
    invoke, dataset, cfg = fetching
    records_only = replace(cfg, fetch=FetchPolicy("records-only", 0))
    refusal = refused(lambda: invoke(str(reopened.data_a_path()), records_only))
    assert refusal.code == "invalid-input" and "[fetch] policy" in refusal.message
    _not_held(cfg, dataset)


def test_fetch_over_max_bytes_refuses(reopened, fetching):
    invoke, dataset, cfg = fetching
    bounded = replace(cfg, fetch=FetchPolicy("fetch", len(DATA_A) - 1))
    refusal = refused(lambda: invoke(str(reopened.data_a_path()), bounded))
    assert refusal.code == "invalid-input" and "max_bytes" in refusal.message
    _not_held(cfg, dataset)


def test_fetch_never_redeclares_the_dataset(reopened, fetching):
    invoke, dataset, cfg = fetching
    corpus_id = a_identity(reopened.a)["corpus_id"]
    invoke(str(reopened.data_a_path()))
    assert ReadContext.open(cfg).cited(dataset).corpus_id == corpus_id
