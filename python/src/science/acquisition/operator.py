"""Sessionless local operations for starting, resuming and inspecting a set."""

import json
import sys
from collections import Counter
from dataclasses import fields, replace
from pathlib import Path

from science.acquisition.bounds import AcquisitionBounds
from science.acquisition.imported import import_status
from science.acquisition.journal import Journal, locked_directory, prepare_root, set_directory, validate_root
from science.acquisition.plan import parse_plan
from science.acquisition.retrieve import retrieve_set
from science.config import load_config, resolve_config_path
from science.refusal import Refusal, Refused

__all__ = ["add_local_parsers", "operate"]


def add_local_parsers(subparsers):
    summaries = {"start": "Retrieve a static acquisition plan into a new resumable set",
                 "resume": "Continue retrieval from a set journal",
                 "status": "Show request states and accepted dataset references"}
    for verb, summary in summaries.items():
        parser = subparsers.add_parser(verb, help=summary)
        parser.set_defaults(command="acquire-" + verb)
        parser.add_argument("--config", type=Path)
        if verb == "start":
            parser.add_argument("--plan", required=True, type=Path)
            for field in fields(AcquisitionBounds):
                parser.add_argument("--" + field.name.replace("_", "-"), type=int)
        else:
            parser.add_argument("--set", required=True)


def _status(ops, token):
    path = set_directory(ops, token)
    if (path / "import.json").is_file():
        meta, receipt = import_status(path)
        return {**{key: meta[key] for key in ("fetched", "failed", "abandoned", "bytes")},
                "set": token, "active": 0, "pending": 0, **(receipt or {})}
    j = Journal.open(ops, token)
    counts = Counter(dict.fromkeys(("active", "pending", "failed", "fetched", "abandoned"), 0))
    active_seq = j.active_seq()
    for seq, request in enumerate(j.requests, 1):
        state = "active" if seq == active_seq else request.state
        counts[state] += 1
    return {"set": token, **counts, "bytes": sum(r.size or 0 for r in j.requests), **(j.receipt or {})}


def operate(args):
    cfg = load_config(resolve_config_path(args.config))
    ops, protected = cfg.acquisition_roots()
    if args.command == "acquire-status":
        validate_root(ops, protected)
        print(json.dumps(_status(ops, args.set), sort_keys=True))
        return
    if args.command == "acquire-start":
        overrides = {f.name: getattr(args, f.name) for f in fields(AcquisitionBounds) if getattr(args, f.name) is not None}
        policy = replace(cfg.acquire, **overrides)
        try:
            raw = sys.stdin.buffer.read() if str(args.plan) == "-" else args.plan.read_bytes()
        except OSError as exc:
            raise Refused(Refusal("invalid-input", f"Cannot read acquisition plan: {exc}")) from exc
        parse_plan(raw, max_requests=policy.max_requests)
    root = prepare_root(ops, protected)
    with locked_directory(root, "retrieval-busy"):
        if args.command == "acquire-start":
            journal = Journal.create(ops, raw, policy, protected=protected)
            token = journal.path.name
        else:
            token = args.set
        path = set_directory(ops, token)
        with locked_directory(path, "set-busy"):
            if (path / "import.json").exists():
                raise Refused(Refusal("invalid-input", "an imported set has no retrieval to resume"))
            journal = Journal.open(ops, token, repair=True)
            if journal.partial or journal.binding or journal.receipt:
                raise Refused(Refusal("invalid-input", "acceptance has started; inspect this set with acquire status"))
            if args.command == "acquire-start":
                print(token, flush=True)
            retrieve_set(journal)
