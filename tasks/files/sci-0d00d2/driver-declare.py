"""The two unheld datasets the health question needs (milestone design §4.1, §5.5 step 1).

    declare.py <state>

Kernel-level: `science dataset` always holds bytes, and the kernel's `Declared` state
is reachable only by adding a dataset node through the writer (design C2, filed).
Each input is downloaded into its own empty directory, checked against its published
md5, digested, and discarded; nothing is held.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import shutil
import sys
import urllib.request
from collections import Counter
from pathlib import Path

from common import AUTHORITY, TASK_DIR, State, read_json, stop, write_json

SOURCES = {
    "counts": ("https://zenodo.org/records/22399365/files/mm_counts.csv.gz?download=1",
               "mm_counts.csv.gz", "e18dc9b72619d6473e2274cf3823b395"),
    "metadata": ("https://zenodo.org/records/22399365/files/mm_metadata.csv?download=1",
                 "mm_metadata.csv", "9201e47ffb0e3900b01fd96a913b56f6"),
    "annotation": ("https://ftp.ebi.ac.uk/pub/databases/gencode/Gencode_human/release_36/gencode.v36.annotation.gtf.gz",
                   "gencode.v36.annotation.gtf.gz", "c03931958d4572148650d62eb6dec41a"),
}
COHORT_TITLE = "MMRF-CoMMpass teaching counts, 30 diagnosis and 30 relapse (Zenodo 22399365)"
# The empirical-observation locator declares the schemes accession, url and instrument;
# the design's `doi:` form is refused (a finding), so the DOI is given as its resolver URL.
COHORT_LOCATOR = "url:https://doi.org/10.5281/zenodo.22399365"
ANNOTATION_TITLE = "GENCODE release 36 primary annotation (gencode.v36.annotation.gtf.gz)"
CONDITIONS = {"ndmm": "diagnostico", "pd": "recidiva"}


def fetch(url: str, into: Path, name: str, md5: str) -> Path:
    if into.exists():
        stop(f"{into} exists; each download gets a fresh empty directory")
    into.mkdir(parents=True)
    target = into / name
    with urllib.request.urlopen(url, timeout=300) as response, target.open("wb") as out:
        shutil.copyfileobj(response, out, length=1 << 20)
    actual = hashlib.md5(target.read_bytes()).hexdigest()
    if actual != md5:
        stop(f"{url}: md5 {actual}, published {md5}")
    return target


def resource(path: Path) -> dict:
    data = path.read_bytes()
    return {"name": path.name, "bytes": len(data), "md5": hashlib.md5(data).hexdigest(),
            "sha256": hashlib.sha256(data).hexdigest()}


def condition_values(metadata: Path) -> dict[str, str]:
    with metadata.open(newline="") as handle:
        counts = Counter(row["condition"] for row in csv.DictReader(handle))
    expected = {value: 30 for value in CONDITIONS.values()}
    if dict(counts) != expected:
        stop(f"{metadata}: condition counts {dict(counts)}, expected {expected}")
    return dict(CONDITIONS)


def node(title: str, resources: list[dict], locator: str, domain_facets=None):
    from beliefs import stored

    return stored.dataset_node(
        title=title,
        resources=[{"name": r["name"], "digest": "sha256:" + r["sha256"]} for r in resources],
        empirical_observation={"locator": locator, "attested_by": AUTHORITY.actor},
        domain_facets=domain_facets,
    )


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    state = State(Path(argv[1]))
    if (state.path / "declared.json").exists():
        stop(f"{state.path}/declared.json exists; the declarations are made once")
    cfg = state.load_config()
    inputs = TASK_DIR / "inputs" / state.name
    progress_path = state.path / "declare-progress.json"
    progress = read_json(progress_path) if progress_path.exists() else {
        "world_id": state.world["world_id"], "added": {}}
    if progress["added"] or progress.get("attempted"):
        stop(f"{progress_path} records adds {progress['added']} (attempted {progress.get('attempted')}) "
             "without declared.json; inspect the working corpus before anything else")

    try:
        files = {key: fetch(url, inputs / key, name, md5) for key, (url, name, md5) in SOURCES.items()}
        with gzip.open(files["counts"]) as handle:
            header = handle.readline().decode()
        conditions = condition_values(files["metadata"])
        cohort_resources = [resource(files["counts"]), resource(files["metadata"])]
        annotation_resources = [resource(files["annotation"])]
    finally:
        # The bytes are digested and discarded, never held, whatever happened.
        shutil.rmtree(inputs, ignore_errors=True)

    cohort = node(COHORT_TITLE, cohort_resources, COHORT_LOCATOR,
                  {"biology/gene-axis": {"axis": "rows", "namespace": "Ensembl"}})
    annotation = node(ANNOTATION_TITLE, annotation_resources, "url:" + SOURCES["annotation"][0])

    from beliefs.root import open_corpus
    from science.config import ReadContext

    ctx = ReadContext.open(cfg)
    from beliefs.facets import validate_payload

    for candidate in (cohort, annotation):
        violations = cfg.profile.document_violations(candidate)
        if violations:
            stop(f"{candidate.id}: {violations}")
        # The writer's own view-free checks (registry membership, every facet payload's
        # shape), so that neither write starts unless both would pass them.
        try:
            cfg.profile.validate_document(candidate)
            for key, payload in candidate.facets.items():
                facet = cfg.profile.facets.get(key)
                if facet is not None:
                    validate_payload(facet, payload, where=candidate.id)
        except Exception as caught:  # noqa: BLE001 -- refused by name before any write
            stop(f"{candidate.id}: {type(caught).__name__}: {caught}")
        if ctx.dataset_at(candidate.id) is not None:
            stop(f"{candidate.id} is already declared in this world")
    writer = open_corpus(cfg.write_root, authority=AUTHORITY, profile=cfg.profile)
    progress["attempted"] = {}
    for key, candidate in (("cohort", cohort), ("annotation", annotation)):
        progress["attempted"][key] = candidate.id
        write_json(progress_path, progress)
        writer.add(candidate)
        progress["added"][key] = candidate.id
        write_json(progress_path, progress)
        print(f"{key}: {candidate.id}")

    write_json(state.path / "declared.json", {
        "cohort": cohort.id, "annotation": annotation.id,
        "cohort_resources": cohort_resources, "annotation_resources": annotation_resources,
        "condition_values": conditions, "counts_header_prefix": header[:80],
    })
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
