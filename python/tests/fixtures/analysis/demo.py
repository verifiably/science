"""Disposable source-checkout example: explicit kernel bootstrap, then science commands.

Run from python/ with PYTHONPATH=tests. The helpers hold explicit fixture authority
only for bootstrap; every analysis act uses the production attended session.
"""
import argparse
import json
from pathlib import Path
from shutil import copyfile

from beliefs import stored
from helpers.analysis import analysis_nodes, bootstrap_analysis
from helpers.world import build_fixture_world_with_contract, fixture_bundle, write_config_for
from science.config import ReadContext, load_config
from science.dispatch import Dispatcher
from science.loader import production_tree, resolve_handlers
from science.session import open_session


def run_demo(root: Path):
    if not root.is_absolute():
        raise ValueError("choose an absolute new directory on certified storage")
    root.mkdir()  # exclusive: never overwrite or reuse another world
    cfg = build_fixture_world_with_contract(root)
    bootstrap_analysis(cfg)
    config_path = write_config_for(cfg)
    cfg = load_config(config_path)
    print("CONFIGURATION", config_path)
    for node in analysis_nodes(cfg.profile):
        print("HELD PREREQUISITE", node.id)
    estimand = root / "estimand.json"
    copyfile(Path(__file__).with_name("estimand.json"), estimand)
    code, entrypoint, targets = fixture_bundle(root, "supported")
    data = root / "data.txt"
    data.write_bytes(b"x\n")
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
        dataset = record(invoke("dataset", {"path": str(data), "title": "synthetic observations",
                         "locator": "accession:GSE-FIXTURE"}), "dataset")
        proposition = record(invoke("claim", {"subject": "concept:disease-stage", "predicate": "affects",
                             "object": "protein:PHF19", "layer": "causal", "polarity": "positive"}), "proposition")
        spec = record(invoke("spec", {"target": proposition, "dataset": dataset, "estimand": str(estimand),
            "standing": "empirical", "evidence_mode": "observation",
            "rule_procedures": ["beliefs/outcome-file/v1=" + analysis_nodes(cfg.profile)[2].id],
            "method": "synthetic rank comparison", "assumptions": "independent synthetic samples",
            "falsification": "explicit unsupported verdict", "interpretation_rule": "beliefs/outcome-file/v1",
            "equivalence_rule": "beliefs/content-identity-equality/v1"}), "analysis-spec")
        run = record(invoke("run", {"spec": spec, "dataset": dataset, "code": str(code),
                     "entrypoint": entrypoint, "targets": list(targets)}), "run")
        assessment = record(invoke("assess", {"run": run}), "assessment")
        invoke("verify", {"assessment": assessment, "code": str(code), "entrypoint": entrypoint})
        key = stored.assessment_value(context.write_view().get(assessment), profile=cfg.profile).key()
        invoke("belief", {"proposition": proposition, "key": key})
        invoke("next", {})
    finally:
        session.close()
    return cfg, proposition


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    run_demo(parser.parse_args().root)
