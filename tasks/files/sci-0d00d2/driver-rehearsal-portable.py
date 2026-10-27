"""Rehearsal on a disposable replica of the live world (milestone plan Task 5).

    rehearsal.py <wt> <beliefs> <task dir> <name> [--build-only] [--replicas <dir>]

Builds a replica under `<replicas>/<name>/` (its data root; by default the main
checkout's `.work/sci-0d00d2/`, on a volume the kernel's durability allowlist admits,
which `<task dir>`'s is not) by the kernel's
own route, as `beliefs` `python/tools/reproduction/relocate.py` does, with the live
world as the source: the mm30 corpus and the store replicated and restored against the
live world's exported head artifacts, a fresh world initialized, and the corpus
admitted `replica-of`. The live world tree is hashed before and after replication and
must not change. Then genesis, declare and terms run against `<task dir>/state/<name>/`
and, unless `--build-only`, the walk and the arms.
"""
from __future__ import annotations

import argparse
import hashlib
import secrets
import shutil
import subprocess
import sys
from pathlib import Path

from common import AUTHORITY, stop, write_json

LIVE_WORLD = Path("<data root>/worlds/aec951bc6becacced13df8f7ae6f8abf")
REPLICAS = Path("<replicas>")


def tree_manifest(root: Path) -> dict[str, str]:
    return {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(root.rglob("*")) if path.is_file()}


def replicate(home: Path, world_id: str) -> dict:
    from beliefs.root import (LifecycleState, admit_arrival, init_world_root, open_world, read_lifecycle_state,
                              replicate_root, restore_root)
    from beliefs.world import WorldConfig, anchors, registry, verify

    (corpus_head_path,) = sorted((LIVE_WORLD / "anchors").glob("corpus-*.head"))
    (store_head_path,) = sorted((LIVE_WORLD / "anchors").glob("store-*.head"))
    corpus_id = corpus_head_path.stem.removeprefix("corpus-")
    store_id = store_head_path.stem.removeprefix("store-")
    corpus_head, store_head = corpus_head_path.read_bytes(), store_head_path.read_bytes()
    (home / "anchors").mkdir(parents=True)
    shutil.copy2(corpus_head_path, home / "anchors" / corpus_head_path.name)
    shutil.copy2(store_head_path, home / "anchors" / store_head_path.name)

    def restore(source: Path, dest: Path, subject, artifact: bytes) -> str:
        dest.parent.mkdir(parents=True, exist_ok=True)
        replicate_root(source, dest, authority=AUTHORITY)
        report = restore_root(dest, subject, verify.ObserverSet((verify.ArtifactCarrier.from_bytes(artifact),)),
                              authority=AUTHORITY)
        lifecycle = read_lifecycle_state(dest)
        if report.outcome != "validated" or lifecycle is not LifecycleState.READ_ONLY_SERVICEABLE:
            stop(f"{dest}: restore answered {report.outcome!r}, lifecycle {lifecycle.name}")
        return report.outcome

    corpus_root, store_root = home / "corpora" / "mm30", home / "store"
    before = tree_manifest(LIVE_WORLD)
    corpus_outcome = restore(LIVE_WORLD / "corpora" / "mm30", corpus_root, anchors.CorpusSubject(corpus_id),
                             corpus_head)
    store_outcome = restore(LIVE_WORLD / "store", store_root, anchors.StoreSubject(store_id), store_head)
    after = tree_manifest(LIVE_WORLD)
    if before != after:
        changed = sorted(set(before.items()) ^ set(after.items()))
        stop(f"replication changed the live world: {changed}")

    config = WorldConfig(home / "world", world_id, (corpus_root,))
    init_world_root(config, authority=AUTHORITY)
    record, arrival = admit_arrival(open_world(config, authority=AUTHORITY), corpus_root,
                                    registry.ReplicaOf(corpus_id),
                                    verify.ObserverSet((verify.ArtifactCarrier.from_bytes(corpus_head),)))
    if arrival.outcome != "validated":
        stop(f"{corpus_root}: arrival answered {arrival.outcome!r}")
    return {"world_id": world_id, "home": str(home), "corpus_id": record.corpus_id, "store_id": store_id,
            "restore": {"corpus": corpus_outcome, "store": store_outcome}, "arrival": arrival.outcome,
            "admission": registry.provenance_projection(record.provenance),
            "live_world_files": len(before), "live_world_unchanged": True}


def run(script: str, *args: str) -> None:
    command = [sys.executable, str(Path(__file__).resolve().parent / script), *args]
    print(f"$ {' '.join(command[1:])}", flush=True)
    done = subprocess.run(command)
    if done.returncode != 0:
        stop(f"{script} exited {done.returncode}", done.returncode)


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("wt", type=Path)
    parser.add_argument("beliefs", type=Path)
    parser.add_argument("task_dir", type=Path)
    parser.add_argument("name")
    parser.add_argument("--build-only", action="store_true")
    parser.add_argument("--replicas", type=Path, default=REPLICAS)
    args = parser.parse_args(argv[1:])
    if Path(sys.executable).parents[3].resolve() != args.wt.resolve():
        stop(f"run with {args.wt}/python/.venv/bin/python, not {sys.executable}")
    data_root = (args.replicas / args.name).resolve()
    state = (args.task_dir / "state" / args.name).resolve()
    if data_root.exists() or state.exists():
        stop(f"{data_root} or {state} exists; each rehearsal starts from a fresh replica")
    world_id = secrets.token_hex(16)
    home = data_root / "worlds" / world_id
    replica = replicate(home, world_id)
    write_json(data_root / "replica.json", replica)
    print(f"replica {world_id}: {replica}")
    run("genesis.py", str(state), str(data_root), world_id, str(args.beliefs.resolve()),
        str(home / "corpora" / "mm30"))
    run("declare.py", str(state))
    run("terms.py", str(state))
    if args.build_only:
        return 0
    run("walk.py", str(state))
    (latest,) = sorted((state / "runs").iterdir())[-1:]
    run("arms.py", str(state), str(latest))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
