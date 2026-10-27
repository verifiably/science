"""Compare two runs on fresh replicas by their invariants (milestone plan Task 5 Step 3a).

    invariants.py <state A> <run dir A> <state B> <run dir B>

A fresh replica has its own project addresses, revisions, epoch identities and
selection headers, so runs are compared on what must agree: per view, the set of
selected world-record addresses and `equivalent`/`complete`; per `next-*.txt`, the
proposition ids, their classes and their order. Each run is first validated on its
own: every journaled identity resolves in its world, and every `selections.json` row's
address is the one journaled for its key.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from common import State, read_json, stop, write_json

NEXT_FILES = ("next-multiple-myeloma.txt", "next-cancer.txt", "next-health.txt", "next-unselected.txt")


def next_rows(path: Path) -> list[tuple[str, str]]:
    """(proposition id, class) in rendered order, from the `propositions:` block."""
    rows, inside = [], False
    for line in path.read_text().splitlines():
        if line == "propositions:":
            inside = True
            continue
        if inside and line.startswith("  "):
            ident, rest = line.strip().split(": ", 1)
            rows.append((ident, rest.split(": ", 1)[0]))
        elif inside:
            inside = False
    return rows


def journal_rows(run_dir: Path) -> list[dict]:
    return [json.loads(line) for line in (run_dir / "progress.json").read_text().splitlines()
            if line.strip() and "key" in json.loads(line)]


def validate(state: State, run_dir: Path) -> dict:
    from science.config import ReadContext
    from science.coordination import parse_unpinned, resolve_one

    cfg = state.load_config()
    ctx = ReadContext.open(cfg)
    stored = {node.id for _, view in ctx.read_views() for node in view.iter_stored()}
    identities = {}
    for row in journal_rows(run_dir):
        if row["phase"] in {"record", "reconcile"} and row["key"].startswith("W") and row.get("identity"):
            identities[row["key"]] = row["identity"]
    for key, identity in identities.items():
        if identity.startswith("coord:"):
            resolve_one(ctx, parse_unpinned(identity))
        elif identity not in stored:
            stop(f"{run_dir}: {key} identity {identity} does not resolve")
    keyed = {"R1." + k.removeprefix("W2.project."): v for k, v in identities.items() if k.startswith("W2.project.")}
    keyed |= {"R3.question.health": identities.get("W3.question.health"), "R3.reuse": identities.get("W3.reuse"),
              "R3.question.evidence-bound-terms": identities.get("W3.question.evidence-bound-terms")}
    for row in read_json(run_dir / "selections.json"):
        if keyed.get(row["key"]) != row["address"]:
            stop(f"{run_dir}: selections row {row['key']} names {row['address']}, journaled {keyed.get(row['key'])}")
    return {"identities_resolved": len(identities), "selection_rows_checked": len(read_json(run_dir / "selections.json"))}


def invariants(run_dir: Path) -> dict:
    views = {}
    for row in read_json(run_dir / "selections.json"):
        views[row["key"]] = {"selected": sorted(a for a in row["selected"] if not a.startswith(("project:", "question:"))),
                             "equivalent": row["equivalent"], "complete": row["complete"]}
    nexts = {name: next_rows(run_dir / name) for name in NEXT_FILES if (run_dir / name).exists()}
    return {"views": views, "next": nexts}


def main(argv: list[str]) -> int:
    if len(argv) != 5:
        print(__doc__)
        return 2
    state_a, run_a, state_b, run_b = State(Path(argv[1])), Path(argv[2]), State(Path(argv[3])), Path(argv[4])
    report = {"a": {"run": str(run_a), **validate(state_a, run_a)},
              "b": {"run": str(run_b), **validate(state_b, run_b)}}
    left, right = invariants(run_a), invariants(run_b)
    report["views_equal"] = left["views"] == right["views"]
    report["next_equal"] = left["next"] == right["next"]
    report["differences"] = {
        section: {key: {"a": left[section].get(key), "b": right[section].get(key)}
                  for key in sorted(set(left[section]) | set(right[section]))
                  if left[section].get(key) != right[section].get(key)}
        for section in ("views", "next")}
    write_json(run_b / f"invariants-vs-{state_a.name}.json", report)
    print(json.dumps(report, indent=2))
    return 0 if report["views_equal"] and report["next_equal"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
