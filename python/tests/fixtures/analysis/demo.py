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
from fractions import Fraction
from hashlib import sha256
from pathlib import Path
from shutil import copyfile

import beliefs
import yaml
from beliefs import stored
from beliefs.classification_rule import ClassificationRule
from beliefs.decode import claim_from_stored
from beliefs.estimand import estimand_projection
from beliefs.identity import v1
from beliefs.profile import shipped_assumptions_register
from beliefs.procedure import Implementation, Procedure, Scale
from beliefs.projection import claim_identity
from beliefs.referent_mapping import ReferentMapping
from beliefs.register import register_from_projection
from beliefs.root import open_corpus
from beliefs.runrecord import decode_run_closure
from helpers.analysis import analysis_nodes, bootstrap_analysis
from helpers.world import (
    FIXTURE_AUTHORITY, build_contract_world, build_fixture_world_with_contract,
    fixture_bundle, hold_fixture_dataset, write_config_for,
)
from science.config import ReadContext, load_config
from science.dispatch import Dispatcher
from science.loader import production_tree, resolve_handlers
from science.refusal import Refused
from science.session import open_session

INTERPRETATION_RULE = "beliefs/outcome-file/v1"
EQUIVALENCE_RULE = "beliefs/content-identity-equality/v1"
PHF19_ASSETS = {
    "phf19-inputs.json": "581f2c31b787f12058ec63e7fb240c47e962b7191631734c4a969eec3e61fa11",
    "mm30-phf19.yaml": "0ea492b8fcd7681cbd6d2ac4e874dc00be4f50657694611728d0b55931e2bcaa",
    "mm30-phf19-register.json": "df474e157913a8ed0e0d12d666e1265a80d5bb16cd91d50df2fb8f32737b50cf",
    "phf19-vocabulary/clinical-factors.txt": "576a04dff964f639813fd9132e015605a8d4ca0ea609fa5b3f4689a6584b9f1d",
    "phf19-vocabulary/cohorts.txt": "80a46661c240173025d0e44180b60fea560d1c48c9376b2fb74972ef5dc49260",
    "phf19-vocabulary/stage-levels.txt": "d77b182f993b076fba60b8848e79fada70d8f425d7c6eb03f714458880f18281",
    "analysis/labels.py": "5485791e56ae315056354146b4c24e42960884f8935cd98a88796f3bf38e39dc",
    "analysis/assoc.py": "76a874be4e063e8003e316ea7ea5891dc92f70a997521fb8c25d3d22dea9142b",
    "Snakefile.template": "0444d06a3c86ea949b3c8d40c225f56f84a78b437fb677bda2752456701091a7",
}


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
    dataset_options: dict
    claim_inputs: dict
    spec_options: dict

    def authoring_inputs(self) -> dict:
        return {
            "dataset": {"path": str(self.data), **self.dataset_options},
            "claim": self.claim_inputs,
            "spec": {"estimand": str(self.estimand), "standing": "empirical", "evidence_mode": "observation",
                     "rule_procedures": [self.rule_procedure], "interpretation_rule": INTERPRETATION_RULE,
                     "equivalence_rule": EQUIVALENCE_RULE, **self.spec_options},
            "run": {"code": str(self.code), "entrypoint": self.entrypoint, "targets": list(self.targets)},
            "verify": {"code": str(self.code), "entrypoint": self.entrypoint},
        }


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
                  f"{INTERPRETATION_RULE}={held[2].id}",
                  {"title": "synthetic observations", "locator": "accession:GSE-FIXTURE"},
                  {"subject": "concept:disease-stage", "predicate": "affects", "object": "protein:PHF19",
                   "layer": "causal", "polarity": "positive"},
                  {"method": "synthetic rank comparison", "assumptions": "independent synthetic samples",
                   "falsification": "explicit unsupported verdict"})
    _print_world(world, (node.id for node in held))
    return world


def _print_world(world: World, held):
    print("CONFIGURATION", world.config)
    for address in held:
        print("HELD PREREQUISITE", address)
    print("RULE PROCEDURE", world.rule_procedure)
    print("ESTIMAND", world.estimand)
    print("DATA", world.data)
    print("CODE", world.code)
    print("ENTRYPOINT", world.entrypoint)
    print("TARGETS", " ".join(world.targets))


def _kernel_asset_path() -> Path:
    return Path(beliefs.__file__).resolve().parents[2] / "tools/reproduction"


def _checked_bytes(path: Path, pin: str, label: str) -> bytes:
    content = path.read_bytes()
    if sha256(content).hexdigest() != pin:
        raise ValueError(f"{label} digest mismatch at {path}")
    return content


def create_phf19(root: Path, paths: dict[str, Path], *, input_digests=None) -> World:
    """Check the frozen input bytes, then hold operator prerequisites in a new world."""
    if not root.is_absolute():
        raise ValueError("choose an absolute new directory on certified storage")
    asset_root = _kernel_asset_path()
    assets = {name: _checked_bytes(asset_root / name, digest, name) for name, digest in PHF19_ASSETS.items()}
    declaration = json.loads(assets["phf19-inputs.json"])
    pins = declaration["digests"] if input_digests is None else input_digests
    if paths.keys() != pins.keys() or pins.keys() != declaration["digests"].keys():
        raise ValueError("name all six PHF19 inputs and their digest pins")
    sources = {name: _checked_bytes(paths[name], pins[name], name) for name in paths}

    root.mkdir()
    contract = root / "mm30.yaml"
    contract.write_text(yaml.safe_dump({
        "contract": yaml.safe_load(assets["mm30-phf19.yaml"]),
        "plan": {
            "sorts": {"concept": "clinical-factor", "hgnc": "biology/gene"},
            "layers": {"statistical": "statistical"},
            "polarities": {"positive": "positive"},
            "operators": [{"predicate": "covaries-with", "subject": "concept", "object": "hgnc",
                           "operator": "general/covaries-with", "roles": {"subject": "parties", "object": "parties"}}],
        },
    }))
    domains = ("general", "biology")
    cfg = build_contract_world(root, contract, domains=domains)
    config = write_config_for(cfg, document=contract, domains=domains)
    held = {
        name: hold_fixture_dataset(cfg, paths[name].name, content, f"PHF19 source evidence: {name}")
        for name, content in sources.items() if name != "matrix"
    }
    for name, content in assets.items():
        if name.startswith("phf19-vocabulary/"):
            filename = Path(name).name
            held[filename] = hold_fixture_dataset(cfg, filename, content, filename)

    evidence = declaration["evidence"] if input_digests is None else "synthetic"
    members = b"ensembl:ENSG00000119403\thgnc:24566\n"
    held["mapping-members"] = hold_fixture_dataset(cfg, "mapping-members.tsv", members, "PHF19 mapping members")
    mapping = stored.referent_mapping_node(ReferentMapping(
        "biology/ensembl-gene", "biology/gene",
        {"hgnc_release": declaration["hgnc_release"], "ensembl_release": declaration["ensembl_release"],
         "assembly": declaration["assembly"], "evidence": evidence,
         **{f"{key}_sha256": pins[key] for key in ("hgnc", "ensembl", "crosswalk")},
         **{f"{key}_dataset": held[key] for key in ("hgnc", "ensembl", "crosswalk", "mapping-members")}},
        "one-to-one", None, "sha256:" + sha256(members).hexdigest(),
    ))
    parser = Implementation("analysis/labels.py", "sha256:" + PHF19_ASSETS["analysis/labels.py"])
    estimator = Implementation("analysis/assoc.py", "sha256:" + PHF19_ASSETS["analysis/assoc.py"])
    assay, estimate, grouping, estimand_document = _phf19_measurement(pins, held, mapping.id, parser, estimator)
    writer = open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile)
    for node in (mapping, assay, estimate, grouping):
        writer.add(node)
    registers = [shipped_assumptions_register(domain) for domain in domains]
    registers.append(register_from_projection(json.loads(assets["mm30-phf19-register.json"]), source="mm30 PHF19"))
    register_ids = [writer.add(stored.assumptions_register_node(register)).id for register in registers]

    data = root / "GSE179929_gene_tpm.txt.gz"
    data.write_bytes(sources["matrix"])
    estimand = root / "estimand.json"
    estimand.write_text(json.dumps(estimand_document, indent=2) + "\n")
    code = root / "analysis"
    entrypoint = "analysis/workflow/Snakefile"
    snakefile = root / entrypoint
    snakefile.parent.mkdir(parents=True)
    for name in ("analysis/assoc.py", "analysis/labels.py"):
        (root / name).write_bytes(assets[name])
    workflow = assets["Snakefile.template"].decode()
    values = {"HELD_INPUT": repr(f"inputs/{data.name}"), "VALUE_ROW": repr(declaration["feature"]),
              "GROUP_SEPARATOR": repr(declaration["separator"]), "POSITIVE_LEVEL": repr("PD")}
    for key, value in values.items():
        workflow = workflow.replace("{" + key + "}", value)
    snakefile.write_text(workflow)
    world = World(config, estimand, data, code, entrypoint, ("outputs/stats.tsv", "outputs/outcome.txt"),
                  f"{INTERPRETATION_RULE}={estimate.id}",
                  {"title": "GSE179929 gene TPM", "locator": "accession:GSE179929"},
                  {"subject": declaration["factor"], "predicate": "covaries-with", "object": declaration["gene"],
                   "layer": "statistical", "polarity": "positive", "slug": "phf19-rna-pd-vs-ndmm"},
                  {"method": "Unpaired half-tie probability of superiority, PD versus NDMM.",
                   "assumptions": "Source pairing is unmodeled. Independence and assay validity are unestablished.",
                   "falsification": "No directional outcome at alpha 0.05, or an opposite-direction result.",
                   "registers": register_ids, "applicability": ["mm30/cohort=generic:cohort:gse179929"],
                   "parameters": ["alpha=0.05"]})
    instructions = root / "authoring.json"
    instructions.write_text(json.dumps(world.authoring_inputs(), indent=2) + "\n")
    print("KERNEL ASSETS", asset_root)
    for name, path in paths.items():
        print("CHECKED INPUT", name, path)
    print("AUTHORING", instructions)
    _print_world(world, (*held.values(), mapping.id, assay.id, estimate.id, grouping.id, *register_ids))
    return world


def _phf19_measurement(pins, held, mapping, parser, estimator):
    from beliefs.measurement import Aspect, Observable

    observable = Observable("general/relative-abundance", "biology/gene",
                            Aspect("biology/molecular-aspect", "biology-aspect:rna"))
    assay = stored.procedure_node(Procedure(
        kind="general/assay", name="PHF19 matrix gene RNA interpretation",
        definition="Gene-level RNA in the held matrix. Historical quantifier, annotation and aggregation are unknown.",
        yields=(observable,), scale=Scale(Fraction(0), Fraction(1000000), "higher-is-more"),
        validated_in="unknown", compatible_with=(), evidence=(), implementation=None, inputs=None,
        parameters={"matrix_sha256": pins["matrix"], "mapping": mapping,
                    "source_dataset": held["dataset"], "source_proposition": held["proposition"]}, external=None,
    ))
    estimate = stored.procedure_node(Procedure(
        kind="general/estimator", name="PHF19 unpaired midrank estimator",
        definition="Independent-groups Mann-Whitney U with half ties, no tie correction or computed interval.",
        yields=(), scale=None, validated_in="unknown", compatible_with=(), evidence=(),
        implementation=estimator, inputs=None, external=None,
        parameters={"label_parser": parser.digest, "comparison": "PD", "baseline": "NDMM", "alpha": "0.05"},
    ))
    grouping = stored.classification_rule_node(ClassificationRule(
        classes="mm30/stage-level", reads=(), external=None, implementation=parser, annotator=None,
        definition="Classify the final underscore token as NDMM or PD. Refuse other tokens.",
    ))
    estimand = {
        "schema_version": 1, "form": "contrast", "functional": "general/probability-of-superiority",
        "bindings": {
            "response": {"role": "parties", "member": {"sort": "biology/gene", "term": "hgnc:24566"},
                         "mapping": mapping, "measure": {
                             "observable": {"quantity_kind": "general/relative-abundance", "bearer_sort": "biology/gene",
                                            "aspect": {"sort": "biology/molecular-aspect", "term": "biology-aspect:rna"}},
                             "procedure": assay.id, "scale": assay.id, "level": "ratio",
                             "value_type": "level", "transformation": "general/identity",
                         }},
            "grouping": {"source": "rule-classes", "rule": grouping.id,
                         "classes": [{"sort": "mm30/stage-level", "term": term} for term in ("level:ndmm", "level:pd")]},
        },
        "outputs": {"estimate": {"typing": "dimensionless", "domain": "unit-interval"}},
        "reference": {"kind": "value", "value": 0.5},
        "control": {"identification": "general/observational", "conditioning": [],
                    "design": "general/independent-groups", "selection": "general/cohort-enrolment"},
        "uncertainty": "interval", "assumptions": [],
    }
    return assay, estimate, grouping, estimand


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
        inputs = world.authoring_inputs()
        dataset = record(invoke("dataset", inputs["dataset"]), "dataset")
        proposition = record(invoke("claim", inputs["claim"]), "proposition")
        spec = record(invoke("spec", {"target": proposition, "dataset": dataset, **inputs["spec"]}), "analysis-spec")
        run = record(invoke("run", {"spec": spec, "dataset": dataset, **inputs["run"]}), "run")
        assessment = record(invoke("assess", {"run": run}), "assessment")
        invoke("verify", {"assessment": assessment, **inputs["verify"]})
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
    for name in ("create-phf19", "walk-phf19"):
        command = commands.add_parser(name, help="build a PHF19 probe on pinned GSE179929 inputs")
        command.add_argument("root", type=Path)
        command.add_argument("--predecessor", type=Path, required=True)
        command.add_argument("--hgnc", type=Path, required=True)
        command.add_argument("--ensembl", type=Path, required=True)
    commands.add_parser("readback", help="print a world's records").add_argument("config", type=Path)
    arguments = parser.parse_args()
    if arguments.command == "create":
        create(arguments.root)
    elif arguments.command == "walk":
        walk(create(arguments.root))
    elif arguments.command in ("create-phf19", "walk-phf19"):
        declaration = json.loads(_checked_bytes(
            _kernel_asset_path() / "phf19-inputs.json", PHF19_ASSETS["phf19-inputs.json"], "PHF19 declaration"
        ))
        paths = {name: arguments.predecessor / path for name, path in declaration["paths"].items()}
        paths.update(hgnc=arguments.hgnc, ensembl=arguments.ensembl)
        try:
            world = create_phf19(arguments.root, paths)
            if arguments.command == "walk-phf19":
                walk(world)
        except (OSError, ValueError, Refused) as error:
            parser.exit(3, f"PHF19 probe refused: {error}\n")
    else:
        try:
            print(render(readback(arguments.config)))
        except Refused as refused:
            print(f"readback refused: {refused}", file=sys.stderr)
            sys.exit(3)
