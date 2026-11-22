"""Disposable source-checkout example: explicit kernel bootstrap, then science commands.

`create ROOT` builds a fresh world and stops before any analysis act: the world a
harness probe hands to its agent. `walk ROOT` creates the same world and runs the
production dataset -> claim -> spec -> run -> assess -> verify -> belief -> next path.
`readback CONFIG` prints what a world's write root records, at any point of that path.
It opens the world detached: it never settles an interrupted world transaction, and
refuses (exit 3) while one is pending.

Run from python/ with PYTHONPATH=tests. The helpers hold explicit fixture authority
only for bootstrap; every analysis act uses the production attended session.
"""
import argparse
import json
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from shutil import copyfile

from beliefs import stored
from beliefs.decode import claim_from_stored
from beliefs.estimand import estimand_projection
from beliefs.identity import v1
from beliefs.projection import claim_identity
from beliefs.runrecord import decode_run_closure
from helpers.analysis import analysis_nodes, bootstrap_analysis
from helpers.world import build_fixture_world_with_contract, fixture_bundle, write_config_for
from science.config import ReadContext, load_config
from science.dispatch import Dispatcher
from science.loader import production_tree, resolve_handlers
from science.refusal import Refused
from science.session import open_session

INTERPRETATION_RULE = "beliefs/outcome-file/v1"
EQUIVALENCE_RULE = "beliefs/content-identity-equality/v1"


@dataclass(frozen=True)
class World:
    """What `create` leaves in ROOT: the inputs an agent's commands name."""
    config: Path
    estimand: Path
    data: Path
    code: Path
    entrypoint: str
    targets: tuple[str, ...]
    rule_procedure: str


def create(root: Path) -> World:
    if not root.is_absolute():
        raise ValueError("choose an absolute new directory on certified storage")
    root.mkdir()  # exclusive: never overwrite or reuse another world
    cfg = build_fixture_world_with_contract(root)
    bootstrap_analysis(cfg)
    config = write_config_for(cfg)
    estimand = root / "estimand.json"
    copyfile(Path(__file__).with_name("estimand.json"), estimand)
    code, entrypoint, targets = fixture_bundle(root, "supported")
    data = root / "data.txt"
    data.write_bytes(b"x\n")
    held = analysis_nodes(cfg.profile)
    world = World(config, estimand, data, code, entrypoint, targets,
                  f"{INTERPRETATION_RULE}={held[2].id}")
    print("CONFIGURATION", world.config)
    for node in held:
        print("HELD PREREQUISITE", node.id)
    print("RULE PROCEDURE", world.rule_procedure)
    print("ESTIMAND", world.estimand)
    print("DATA", world.data)
    print("CODE", world.code)
    print("ENTRYPOINT", world.entrypoint)
    print("TARGETS", " ".join(world.targets))
    return world


def walk(world: World):
    cfg = load_config(world.config)
    declarations = production_tree()
    session = open_session(cfg)
    context = ReadContext.open(cfg)
    dispatcher = Dispatcher(declarations, resolve_handlers(declarations), context, session=session)

    def invoke(name, inputs):
        print("COMMAND", name, json.dumps(inputs, sort_keys=True))
        result = dispatcher.invoke(name, inputs)
        print("INVOCATION", result.invocation_id)
        print(result.text)
        return result.text

    def record(text, kind):
        return next(word for word in text.split() if word.startswith(kind + ":"))

    try:
        dataset = record(invoke("dataset", {"path": str(world.data), "title": "synthetic observations",
                         "locator": "accession:GSE-FIXTURE"}), "dataset")
        proposition = record(invoke("claim", {"subject": "concept:disease-stage", "predicate": "affects",
                             "object": "protein:PHF19", "layer": "causal", "polarity": "positive"}), "proposition")
        spec = record(invoke("spec", {"target": proposition, "dataset": dataset, "estimand": str(world.estimand),
            "standing": "empirical", "evidence_mode": "observation",
            "rule_procedures": [world.rule_procedure],
            "method": "synthetic rank comparison", "assumptions": "independent synthetic samples",
            "falsification": "explicit unsupported verdict", "interpretation_rule": INTERPRETATION_RULE,
            "equivalence_rule": EQUIVALENCE_RULE}), "analysis-spec")
        run = record(invoke("run", {"spec": spec, "dataset": dataset, "code": str(world.code),
                     "entrypoint": world.entrypoint, "targets": list(world.targets)}), "run")
        assessment = record(invoke("assess", {"run": run}), "assessment")
        invoke("verify", {"assessment": assessment, "code": str(world.code), "entrypoint": world.entrypoint})
        key = stored.assessment_value(context.write_view().get(assessment), profile=cfg.profile).key()
        invoke("belief", {"proposition": proposition, "key": key})
        invoke("next", {})
    finally:
        session.close()
    return cfg, proposition


def readback(config: Path) -> dict:
    """The write root's records as a probe compares them with its expected evidence:
    every proposition, spec, run, assessment and verification, and the count by kind.
    Detached, so reading never performs the recovery a resuming agent would."""
    cfg = load_config(config)
    context = ReadContext.open_detached(cfg)
    view = context.write_view()
    nodes = sorted(view.iter_stored(), key=lambda node: (node.kind, node.id))
    snapshot = context.snapshot(nodes=nodes, observations=context.observations())
    by_kind = dict(sorted(Counter(node.kind for node in nodes).items()))
    result = {"records": {"total": len(nodes), "by_kind": by_kind}, "propositions": [], "specs": [],
              "runs": [], "assessments": [], "verifications": []}
    for node in nodes:
        if node.kind == "proposition":
            claim, _ = claim_from_stored(node, profile=cfg.profile, snapshot=snapshot)
            result["propositions"].append({"id": node.id, "claim_identity": claim_identity(claim)})
        elif node.kind == "analysis-spec":
            spec = stored.analysis_spec_value(node, profile=cfg.profile)
            result["specs"].append({"id": node.id, "identity": spec.identity, "target": spec.target,
                                    "estimand": v1.encode(estimand_projection(spec.estimand)).decode()})
        elif node.kind == "run":
            closure = decode_run_closure(node)
            result["runs"].append({"id": node.id, "spec_identity": closure.recipe.spec_identity,
                                   "policy": closure.recipe.boundary_policy.identity,
                                   "capabilities": list(closure.occurrence.receipt.execution.capabilities),
                                   "outputs": [list(output) for output in closure.result.outputs]})
        elif node.kind == "assessment":
            value = stored.assessment_value(node, profile=cfg.profile)
            result["assessments"].append({"id": node.id, "run": value.run, "outcome": value.outcome})
        elif node.kind == "verification":
            value = stored.verification_value(node)
            result["verifications"].append({"id": node.id, "assessment": value.assessment,
                                             "scope": value.scope, "verdict": value.verdict})
    return result


def render(found: dict) -> str:
    counts = ", ".join(f"{kind} {count}" for kind, count in found["records"]["by_kind"].items())
    lines = [f"records {found['records']['total']}: {counts}"]
    for item in found["propositions"]:
        lines.append(f"proposition {item['id']} claim {item['claim_identity']}")
    for item in found["specs"]:
        lines.append(f"analysis-spec {item['id']} identity {item['identity']} target {item['target']}")
        lines.append(f"  estimand {item['estimand']}")
    for item in found["runs"]:
        lines.append(f"run {item['id']} spec {item['spec_identity']} policy {item['policy']} "
                     f"capabilities {','.join(item['capabilities'])}")
        lines.extend(f"  output {name} {digest}" for name, digest in item["outputs"])
    for item in found["assessments"]:
        lines.append(f"assessment {item['id']} run {item['run']} outcome {item['outcome']}")
    for item in found["verifications"]:
        lines.append(f"verification {item['id']} assessment {item['assessment']} "
                     f"scope {item['scope']} verdict {item['verdict']}")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("create", help="build a fresh world in a new directory").add_argument("root", type=Path)
    commands.add_parser("walk", help="build a fresh world and run the command path").add_argument("root", type=Path)
    commands.add_parser("readback", help="print a world's records").add_argument("config", type=Path)
    arguments = parser.parse_args()
    if arguments.command == "create":
        create(arguments.root)
    elif arguments.command == "walk":
        walk(create(arguments.root))
    else:
        try:
            print(render(readback(arguments.config)))
        except Refused as refused:
            print(f"readback refused: {refused}", file=sys.stderr)
            sys.exit(3)
