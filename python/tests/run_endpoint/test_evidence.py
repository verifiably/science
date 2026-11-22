"""Run evidence as observed through the command dispatcher."""
import json
from pathlib import Path

import pytest

from beliefs.root import log_seam
from science.config import ReadContext
from science.dispatch import Dispatcher
from science.refusal import Refused
from science.schema import Declaration, InputSpec, WriteClass
from helpers.world import build_fixture_world


@pytest.fixture
def evidence(certified_work):
    from science.commands import heads, log
    cfg = build_fixture_world(certified_work)
    handlers = {"heads": heads.handle, "log": log.handle}
    inputs = {
        "heads": (InputSpec("resolve", "bool", False, "resolve", False),),
        "log": tuple(InputSpec(k, "string", k != "through", k) for k in ("chain", "after", "through")),
    }
    decls = tuple(Declaration(k, k, WriteClass("read-only"), 100_000, v, (), Path(".")) for k, v in inputs.items())
    return cfg, Dispatcher(decls, handlers, ReadContext.open(cfg))


def test_heads_and_log_agree_with_the_mounted_chains(evidence):
    cfg, dispatcher = evidence
    heads = json.loads(dispatcher.invoke("heads", {}).text)
    assert heads["version"] == "heads.v1"
    assert heads["world_head"] == log_seam().inspect_detached(cfg.world.world_root).tip
    assert {c["root"] for c in heads["chains"]} == {str(cfg.write_root), str(cfg.store_root)}
    for chain in heads["chains"]:
        observed = log_seam().inspect_detached(Path(chain["root"]))
        assert chain["genesis"] == observed.genesis.digest
        assert chain["tip"] == observed.tip
        assert chain["pending"] == []
        selector = chain["id"] if chain["role"] == "corpus" else "store"
        args = {"chain": selector, "after": chain["genesis"], "through": chain["tip"]}
        lines = [json.loads(line) for line in dispatcher.invoke("log", args).text.splitlines()]
        assert lines[0] == {
            "version": "log.v1", "role": chain["role"], "id": chain["id"], "root": chain["root"],
            "genesis": chain["genesis"], "after": args["after"], "through": args["through"],
        }
        assert [r["digest"] for r in lines[1:]] == [e.digest for e in observed.entries[1:]]
        args["after"] = chain["tip"]
        assert len(dispatcher.invoke("log", args).text.splitlines()) == 1
        args["through"] = "f" * 64
        with pytest.raises(Refused) as caught:
            dispatcher.invoke("log", args)
        assert caught.value.refusal.code == "tip-unknown"


@pytest.mark.parametrize(("locator", "act", "location", "store"), [
    ({"type": "store", "store_id": "a" * 32, "relative_path": "incoming/a:b"}, "move-source", "incoming/a:b", "a" * 32),
    ({"type": "store", "store_id": "a" * 32, "relative_path": "incoming/new"}, "move-destination", "incoming/new", "a" * 32),
    ({"type": "store-tree", "store_id": "a" * 32, "tree": "b" * 64}, "tree-write", "b" * 64, "a" * 32),
    ({"type": "url", "url": "https://example.org:8443/data"}, "re-check", "https://example.org:8443/data", None),
])
def test_holdings_intents_keep_their_kernel_identity(locator, act, location, store):
    from beliefs.intents.holdings import HOLDINGS_INTENT_DOMAIN
    from beliefs.world.logmodel import IntentEntryView
    from science.run_endpoint.evidence import _entry

    payload = {"domain": HOLDINGS_INTENT_DOMAIN, "actor": "session:test", "event_token": "1" * 32,
               "kind": act, "location": locator}
    row = _entry(IntentEntryView("2" * 64, json.dumps(payload).encode()))
    assert row == {"digest": "2" * 64, "type": "intent", "kind": "holdings", "actor": "session:test",
                   "holdings_act": act, "location": location, "store_id": store}


def test_detached_pending_corpus_is_only_settled_by_resolving_heads(evidence, monkeypatch):
    from atoms.coordinator import execute
    from atoms.core.recovery import CommitDecision, TransactionState
    from nodes.core.errors import ExecutionError
    from beliefs.root import open_corpus
    from helpers.world import FIXTURE_AUTHORITY, fixture_proposition_node

    cfg, dispatcher = evidence
    root = cfg.write_root
    writer = open_corpus(root, authority=FIXTURE_AUTHORITY, profile=cfg.profile)

    def interrupt_after_commit(lease, approved, table, chain_fd):
        with lease._store.transaction() as txn:
            txn.set_commit_decision(approved.txid, CommitDecision.COMMITTED)
            txn.set_transaction_state(approved.txid, TransactionState.COMMITTED)
        raise RuntimeError("interrupted before settlement")

    with monkeypatch.context() as fault:
        fault.setattr(execute, "finalize_commit", interrupt_after_commit)
        with pytest.raises(ExecutionError, match="interrupted before settlement"):
            writer.add(fixture_proposition_node("interrupted"))
    pending = log_seam().inspect_detached(root)
    assert pending.pending

    def corpus(resolve):
        report = json.loads(dispatcher.invoke("heads", {"resolve": resolve}).text)
        return next(c for c in report["chains"] if c["role"] == "corpus")

    assert corpus(False)["pending"] == [list(pair) for pair in pending.pending]
    assert log_seam().inspect_detached(root).tip == pending.tip
    assert corpus(True)["pending"] == []
    assert not log_seam().inspect_detached(root).pending


def test_heads_and_log_match_the_shared_wire_examples(monkeypatch):
    from types import SimpleNamespace
    from beliefs.after import AfterEntries
    from beliefs.world.logmodel import GenesisEntryView, RegisteredEntryView, SettledEntryView, WellFormedView
    from science.render import render_full
    from science.run_endpoint import evidence as reads

    prefix = Path("/run/example")
    corpus, store = reads._Chain("corpus", "a" * 32, prefix / "corpus"), reads._Chain("store", "b" * 32, prefix / "store")
    cfg = SimpleNamespace(world=SimpleNamespace(world_root=prefix / "world"), store_root=store.root)
    monkeypatch.setattr(reads, "_chains", lambda config: (corpus, store))
    surface = (("incoming/a", log_seam().absent_state),)
    registration = RegisteredEntryView("5" * 64, "3" * 32, surface, surface, None)
    end = SettledEntryView("6" * 64, "3" * 32, registration.digest, False)
    def view(root, resolve):
        genesis = {corpus.root: "1", store.root: "2", cfg.world.world_root: "f"}[root] * 64
        return WellFormedView(GenesisEntryView(genesis, b"", ()), (), end.digest if root == store.root else genesis, ())
    monkeypatch.setattr(reads, "_view", view)
    monkeypatch.setattr(reads, "read_after", lambda *a, **kw: AfterEntries((registration, end), end.digest, ()))
    fixtures = Path(__file__).resolve().parents[1] / "fixtures/run_endpoint"
    assert render_full(reads.heads(cfg, resolve=False)).encode() == (fixtures / "heads.v1.jsonl").read_bytes()
    result = reads.chain_log(cfg, chain="store", after="2" * 64, through=end.digest)
    assert render_full(result).encode() == (fixtures / "log.v1.jsonl").read_bytes()


def test_explicit_end_pages_while_chain_grows_and_open_end_goes_stale(evidence):
    import re
    from dataclasses import replace
    from beliefs.root import open_corpus
    from science.cursor import MIN_OUTPUT_BUDGET
    from helpers.world import FIXTURE_AUTHORITY, fixture_proposition_node

    cfg, full = evidence
    original = json.loads(full.invoke("heads", {}).text)["chains"][0]
    selector = original["id"]
    fixed = {"chain": selector, "after": original["genesis"], "through": original["tip"]}
    unbounded = {"chain": selector, "after": original["genesis"]}
    expected = full.invoke("log", fixed).text
    paged = Dispatcher([replace(full._decls["log"], output_budget=MIN_OUTPUT_BUDGET)], full._handlers,
                       ReadContext.open(cfg))
    marker = re.compile(r"\n… truncated at \d+ bytes; continue with cursor (scur1\.\S+)\n$")
    first = paged.invoke("log", fixed).text
    first_unbounded = paged.invoke("log", unbounded).text
    stale = marker.search(first_unbounded)
    assert stale and marker.search(first)
    writer = open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile)
    writer.add(fixture_proposition_node("later"))
    with pytest.raises(Refused) as caught:
        paged.invoke("log", unbounded, cursor=stale[1])
    assert caught.value.refusal.code == "stale-cursor"
    chunks = []
    page = first
    while match := marker.search(page):
        chunks.append(page[:match.start()])
        page = paged.invoke("log", fixed, cursor=match[1]).text
    assert "".join([*chunks, page]) == expected
    with pytest.raises(Refused):
        full.invoke("log", {**fixed, "after": original["tip"], "through": original["genesis"]})
    with pytest.raises(Refused, match="Unknown chain"):
        full.invoke("log", {**fixed, "chain": "absent"})


def test_heads_include_the_read_mount(certified_work):
    from helpers.world import build_two_corpus_world
    from science.commands.heads import handle
    from science.render import render_full
    cfg = build_two_corpus_world(certified_work)
    document = json.loads(render_full(handle(ReadContext.open(cfg))))
    assert {Path(c["root"]) for c in document["chains"] if c["role"] == "corpus"} == set(cfg.world.corpus_roots)


def test_substituted_genesis_is_rejected_by_the_interval_read(evidence, monkeypatch):
    from dataclasses import replace
    from science.run_endpoint import evidence as reads
    cfg, dispatcher = evidence
    view = log_seam().inspect_detached(cfg.store_root)
    wrong = "0" * 64
    assert wrong != view.genesis.digest
    monkeypatch.setattr(reads, "_view", lambda path, resolve: replace(view, genesis=replace(view.genesis, digest=wrong)))
    with pytest.raises(Refused) as caught:
        dispatcher.invoke("log", {"chain": "store", "after": view.tip})
    assert caught.value.refusal.code == "read-unavailable"
    assert caught.value.refusal.data["reason"] == "genesis-mismatch"
