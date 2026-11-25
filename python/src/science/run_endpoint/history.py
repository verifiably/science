"""Verify the supervisor's resume handoff against the original closed sessions."""
import json
import re

from beliefs.session import open_ledger_reader

from science.config import corpus_id_at
from science.run_endpoint.launch import _closed, _private_bytes, _private_dir
from science.run_endpoint.research import require

__all__ = ["restore"]


def _record(path):
    return json.loads(_private_bytes(path, 1 << 20), object_pairs_hook=_closed)


def _predecessors(launch, ids):
    result = {}
    for directory in launch.run_dir.parent.iterdir():
        if directory == launch.run_dir or not re.fullmatch(r"[0-9a-f]{32}", directory.name):
            continue
        if directory.is_symlink():
            continue
        _private_dir(directory)
        try:
            grant = _record(directory / "allowance.json")
        except FileNotFoundError:
            continue
        if any(grant.get(k) != launch.research.action[k] for k in ("campaign_id", "member_id", "conversation_id")):
            continue
        prior_launch = _record(directory / "launch.json")
        require(prior_launch.get("research_action") == launch.research.action, "Historical action differs")
        raw = _private_bytes(directory / "events.jsonl", 8 << 20)
        require(raw.endswith(b"\n"), "Torn predecessor journal")
        sessions = [row["session_id"] for line in raw.splitlines()
                    if (row := json.loads(line, object_pairs_hook=_closed)).get("event") == "session-open"]
        require(len(sessions) == 1 and sessions[0] in ids and sessions[0] not in result,
                "Missing or substituted predecessor")
        seal, disposition = _record(directory / "seal.json"), _record(directory / "disposition.json")
        require(set(seal) == {"cause", "sealed_tips", "basis_seal"} and seal["cause"] in ("stop", "lease", "term", "eof")
                and disposition["run"] == directory.name and disposition["disposition"] == "clean",
                "Predecessor requires recovery")
        selection_file = directory / "selection.json"
        try:
            row = _record(selection_file)
        except FileNotFoundError:
            pass
        else:
            require(set(row) == {"session_id", "proposition", "class"} and row["session_id"] == sessions[0]
                    and row["proposition"] == launch.research.action["proposition"]
                    and row["class"] in ("ready", "not-ready", "assessed-unevaluated", "assessed-not-admitted", "admitted")
                    and launch.research.selection is None, "Substituted or duplicate queue selection")
            launch.research.selection = row["class"]
        result[sessions[0]] = disposition["members"]
    require(set(result) == set(ids), "Missing predecessor evidence")
    return result


def restore(action, launch, ctx):
    sessions = launch.resume_handoff["sessions"]
    ids = []
    for prior in sessions:
        require(type(prior) is dict and set(prior) == {"session_id", "outcomes"} and type(prior["session_id"]) is str
                and re.fullmatch(r"[a-f0-9]{32}", prior["session_id"]) and prior["session_id"] not in ids,
                "Invalid predecessor session")
        ids.append(prior["session_id"])
    members = _predecessors(launch, ids)
    corpus_id = corpus_id_at(ctx.config.write_root)
    for prior in sessions:
        sid = prior["session_id"]
        ledger = open_ledger_reader(ctx.config.operations_root, sid)
        require(ledger.closed and not ledger.torn_tail and not ledger.open_invocations and
                ledger.world_id == ctx.config.world.world_id and ledger.actor == "session:" + sid,
                "Invalid previous writer ledger")
        expected = []
        for inv in ledger.invocations():
            if inv.outcome is None or "done" not in inv.outcome:
                continue
            pairs = sorted({pair for act in inv.acts for pair in act.record_ids})
            require(all(act.corpus == corpus_id and act.entry in members[sid].get(corpus_id, ())
                        for act in inv.acts), "Prior write is outside the closed interval")
            require([list(pair) for pair in pairs] == inv.outcome["done"], "Prior ledger outcome differs from acts")
            expected.append({"invocation": inv.invocation, "command": inv.command, "input_digest": inv.input_digest,
                             "records": inv.outcome["done"]})
        require(prior["outcomes"] == expected, "Substituted invocation or input digest in resume handoff")
        for inv in expected:
            action.record(inv["command"], inv["records"], ctx)
