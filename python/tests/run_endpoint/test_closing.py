"""Read a run through the public evidence CLI and the pinned closing check."""
from dataclasses import replace
import json
from pathlib import Path
import re
import threading

import pytest

from science import cli
from science.config import ReadContext
from science.cursor import MIN_OUTPUT_BUDGET
from science.dispatch import Dispatcher
from science.loader import production_tree, resolve_handlers
from science.run_endpoint.control import seal_evidence
from science.run_endpoint.launch import open_run, read_launch
from science.run_endpoint.paths import Scratch

_TRAILER = re.compile(r"\n… truncated at \d+ bytes; continue with cursor (scur1\.\S+)\n$")


def _rows(capsys, config, *arguments):
    args = [*arguments, "--config", str(config)]
    fragments = []
    continuation = []
    while True:
        assert cli.main([*args, *continuation]) == 0
        out = capsys.readouterr().out
        trailer = _TRAILER.search(out)
        if trailer is None:
            fragments.append(out)
            return [json.loads(line) for line in "".join(fragments).splitlines()], len(fragments)
        fragments.append(out[:trailer.start()])
        continuation = ["--continue", trailer[1]]


def _paths(surface):
    from atoms.chain.model import state_from_json

    names = []
    for path, facts in surface:
        assert type(path) is str
        state_from_json(tuple(tuple(pair) for pair in facts))
        names.append(path)
    assert names == sorted(set(names))
    return names


def _hex(value, width):
    if type(value) is not str or re.fullmatch(rf"[0-9a-f]{{{width}}}", value) is None:
        raise ValueError("invalid digest or transaction id")
    return value


def _text(value, *, nullable=False):
    if nullable and value is None:
        return None
    if type(value) is not str or not value:
        raise ValueError("expected nonempty text")
    return value


def _decode(header, rows, chain, after, through):
    from autonomy.evidence import Chain, Intent, Registration, Settlement

    if header != {"version": "log.v1", "role": chain["role"], "id": chain["id"], "root": chain["root"],
                  "genesis": chain["genesis"], "after": after, "through": through}:
        raise ValueError("inconsistent log interval header")
    entries = []
    for r in rows:
        digest = _hex(r["digest"], 64)
        if r["type"] == "intent":
            kind, actor = _text(r["kind"], nullable=True), _text(r["actor"], nullable=True)
            holding = kind == "holdings"
            if holding:
                if r["store_id"] is not None:
                    _hex(r["store_id"], 32)
            entries.append(Intent(digest, actor, kind, _text(r["holdings_act"]) if holding else None,
                                  _text(r["location"]) if holding else None))
        elif r["type"] == "registration":
            paths = frozenset((*_paths(r["initial"]), *_paths(r["final"])))
            fulfills = r["fulfills"]
            if fulfills is not None:
                _hex(fulfills, 64)
            entries.append(Registration(digest, _hex(r["txid"], 32), fulfills, _text(r["consumer_tag"], nullable=True), paths))
        elif r["type"] == "settlement":
            if type(r["committed"]) is not bool:
                raise ValueError("invalid settlement flag")
            entries.append(Settlement(digest, _hex(r["txid"], 32), _hex(r["registration"], 64), r["committed"]))
        else:
            raise ValueError("unexpected log row")
    return Chain(chain["id"], chain["role"], True, tuple(entries))


@pytest.mark.parametrize("cut", ["complete", "store-ledger", "publication", "corpus-ledger"])
def test_dataset_interval_reaches_real_closing_check(autonomy_source, launch_file, capsys, monkeypatch, cut):
    from autonomy.closing import close
    from autonomy.evidence import RunEvidence
    from autonomy.ledger import read_ledger
    from autonomy.tiers import Permit
    from beliefs.errors import SessionLedgerFailed
    from beliefs.holdings import boundary
    from beliefs.root import store_identity

    source, doc = launch_file
    config = Path(doc["config"])
    cfg = cli.load_config(config)
    declarations = production_tree()
    monkeypatch.setattr(cli, "production_tree", lambda: tuple(
        replace(d, output_budget=MIN_OUTPUT_BUDGET) if d.name == "log" else d for d in declarations))
    dataset = next(d for d in declarations if d.name == "dataset")
    doc["permit"] = {"kinds": sorted(dataset.write_class.kinds),
                     "act_families": sorted(set(dataset.write_class.routes.values())), "ungoverned": False}
    doc["written_chains"].append({"role": "store", "id": store_identity(cfg.store_root), "root": str(cfg.store_root)})
    source.write_text(json.dumps(doc))
    launch = read_launch(source)
    (baseline,), _ = _rows(capsys, config, "heads", "--resolve")
    opened = open_run(launch)
    session = opened.session
    report = opened.open_report()
    raw_ledger = Path(report["ledger_path"])
    scratch_file = launch.scratch_dir / "data.txt"
    scratch_file.write_text("example measurement")
    inputs = {"title": "fixture", "path": str(scratch_file)}

    def interrupt(*args, **kwargs):
        raise OSError("fixture interrupted the local publication")

    try:
        with Scratch(launch.scratch_dir, cfg.operations_root, threading.Event()) as scratch:
            d = Dispatcher(declarations, resolve_handlers(declarations), ReadContext.open_detached(cfg),
                           session=session, run_inputs=scratch)
            if cut == "complete":
                d.invoke("dataset", inputs, invocation_id="fixture")
                tips = session.seal(3)
                sealed, _ = seal_evidence("stop", tips, opened.basis.digest)
                session.close()
            else:
                owner, method = {"store-ledger": (session, "_record_store_act"),
                                 "publication": (boundary, "_publish_record"),
                                 "corpus-ledger": (session, "_record_committed")}[cut]
                with monkeypatch.context() as fault:
                    fault.setattr(owner, method, interrupt)
                    with pytest.raises(OSError, match="interrupted"):
                        d.invoke("dataset", inputs, invocation_id="fixture")
                sealed = None
            ledger = read_ledger(session.session_id, raw_ledger.read_bytes())
            (closing,), _ = _rows(capsys, config, "heads")
            assert ledger.closed == (cut == "complete")
    finally:
        if cut == "store-ledger":
            with pytest.raises(SessionLedgerFailed):
                session.close()
        else:
            session.close()

    pages = 0
    chains = []
    samples = []
    for chain in baseline["chains"]:
        ends = closing["chains"] if sealed is None else sealed["sealed_tips"]
        end = next(c["tip"] for c in ends if c["id"] == chain["id"])
        target = "store" if chain["role"] == "store" else chain["id"]
        rows, count = _rows(capsys, config, "log", "--chain", target, "--after", chain["tip"], "--through", end)
        chains.append(_decode(rows[0], rows[1:], chain, chain["tip"], end))
        samples.append((rows, chain, end))
        pages += count
    assert pages > len(chains)
    evidence = RunEvidence(run_actor=session.actor, tier_permit=Permit.from_json(doc["permit"]),
                           baseline_available=True, ledger=ledger, chains=tuple(chains),
                           sealed=sealed is not None, seal_timeout=False, orchestrator_lost=False,
                           world_baseline=baseline["world_head"], world_closing=closing["world_head"],
                           mounts_baseline={}, mounts_closing={}, basis_open=report["basis_open"],
                           basis_seal=sealed["basis_seal"] if sealed else None)
    verdict = close(evidence)
    expected_acts = {"complete": 3, "store-ledger": 0, "publication": 1, "corpus-ledger": 1}
    assert len(ledger.acts) == expected_acts[cut]
    codes = {finding.code for finding in verdict.findings}
    assert verdict.disposition == ("clean" if cut == "complete" else "unwired"), verdict.findings
    if cut == "complete":
        assert not codes and verdict.members
        rows, chain, end = next(sample for sample in samples if len(sample[0]) > 1)
        del rows[1]["digest"]
        with pytest.raises(KeyError, match="digest"):
            _decode(rows[0], rows[1:], chain, chain["tip"], end)
        unreadable = close(replace(evidence, chains=None))
        assert unreadable.disposition == "unwired"
        assert "read-unavailable" in {f.code for f in unreadable.findings}
    else:
        assert ledger.open_invocations == ("fixture",)
        interrupted_act = "intent-unfulfilled" if cut == "publication" else "outcome-unknown"
        assert codes == {"session-unclosed", "seal-missing", interrupted_act}
