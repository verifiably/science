"""The frozen queries (milestone design §5.4), written once per state as templates.

    terms.py <state>

Every address is read from a record: the closure anchor from the mm30 GSE179929
dataset record, the spec from the one mm30 analysis-spec, the assessment from the one
mm30 assessment, the evidence-bound concept from the stage -> PHF19 proposition's
arguments, the declared addresses from `declared.json`, and the 285 concepts from the
held concept list, whose sha256 is the mm30 record's P4. `PLACEHOLDER` stands for the
EZH2 spec until the walk mints it; the walk substitutes copies, never these files.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml

from common import State, stop
from genesis import records

PLACEHOLDER = "analysis-spec:<minted>"
CONCEPTS_SHA256 = "c7e45f81f02effe2cdded3261257fb1a45af1ca87c988e45b0d1706abd7e981e"
EZH2 = "proposition:concept-disease-stage-affects-protein-ezh2"
PHF19 = "proposition:concept-disease-stage-affects-protein-phf19"
NAMES = ("multiple-myeloma", "cancer", "health", "multiple-myeloma-findings", "evidence-bound-terms",
         "health-question")


def concept_terms(store_root: Path, mm30_corpus: Path) -> list[str]:
    (record,) = [r for r in records(mm30_corpus, "dataset") if r["title"] == "mm30 concept vocabulary"]
    (resource,) = record["facets"]["dataset"]["resources"]
    if resource["digest"] != "sha256:" + CONCEPTS_SHA256:
        stop(f"the concept vocabulary record pins {resource['digest']}, not the P4 digest")
    candidates = [path for path in Path(store_root).rglob(resource["name"])
                  if not any(part.startswith(".") for part in path.relative_to(store_root).parts)
                  and hashlib.sha256(path.read_bytes()).hexdigest() == CONCEPTS_SHA256]
    if len(candidates) != 1:
        stop(f"{resource['name']} with sha256 {CONCEPTS_SHA256} found {len(candidates)} times in {store_root}")
    return [line for line in candidates[0].read_text().splitlines() if line]


def _one(mm30_corpus: Path, kind: str, title: str | None = None) -> dict:
    found = [r for r in records(mm30_corpus, kind) if title is None or r["title"] == title]
    if len(found) != 1:
        stop(f"{len(found)} {kind} records{f' titled {title!r}' if title else ''} in {mm30_corpus}")
    return found[0]


def write_queries(state: State) -> None:
    if state.queries.exists():
        stop(f"{state.queries} exists; the templates are written once per state")
    declared = state.declared
    if declared is None:
        stop(f"{state.path} has no declared.json")
    cfg = state.load_config()
    (mm30_corpus,) = [root for root in cfg.world.corpus_roots if root != cfg.write_root]
    anchor = _one(mm30_corpus, "dataset", "dataset:gse179929")["id"]
    spec = _one(mm30_corpus, "analysis-spec")["id"]
    assessment = _one(mm30_corpus, "assessment")["id"]
    phf19 = [r for r in records(mm30_corpus, "proposition") if r["id"] == PHF19]
    if len(phf19) != 1:
        stop(f"{PHF19} not found once in {mm30_corpus}")
    stage_concept = phf19[0]["facets"]["proposition"]["args"][0]
    terms = concept_terms(cfg.store_root, mm30_corpus)
    if len(terms) != 285:
        stop(f"the concept list has {len(terms)} terms, not 285")

    closure = {"all": [{"closure": {"anchor": anchor, "predicates": ["observes", "produced_by", "assesses", "verifies"],
                                    "direction": "both"}}]}
    spec_clause = {"all": [{"addresses": [spec]}]}
    term_clauses = [{"all": [{"references-term": term}]} for term in terms]
    health_clause = {"all": [{"addresses": [EZH2, PLACEHOLDER, declared["cohort"], declared["annotation"]]}]}

    def query(clauses: list) -> dict:
        return {"version": "science.view-query.v1", "clauses": clauses}

    myeloma = query([closure, spec_clause, *term_clauses])
    queries = {
        "multiple-myeloma": myeloma,
        "cancer": myeloma,
        "health": query([closure, spec_clause, *term_clauses, health_clause]),
        "multiple-myeloma-findings": query([
            {"all": [{"closure": {"anchor": assessment,
                                  "predicates": ["assesses", "produced_by", "observes", "reads", "transforms", "produces"],
                                  "direction": "out"}}]},
            spec_clause]),
        "evidence-bound-terms": query([closure, spec_clause, {"all": [{"references-term": stage_concept}]}]),
        "health-question": query([closure, health_clause]),
    }
    state.queries.mkdir()
    manifest = []
    for name in NAMES:
        text = yaml.safe_dump(queries[name], sort_keys=False)
        (state.queries / f"{name}.yaml").write_text(text)
        manifest.append(f"{hashlib.sha256(text.encode()).hexdigest()}  {name}.yaml")
    (state.queries / "MANIFEST").write_text("\n".join(manifest) + "\n")
    print((state.queries / "MANIFEST").read_text(), end="")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    write_queries(State(Path(argv[1])))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
