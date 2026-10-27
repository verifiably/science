"""Genesis (milestone design §4.3, §5.2): the concrete mm30 contract chain, the
world's `science.toml`, and a fresh working corpus admitted beside the mm30 corpus.

    genesis.py <state> <data root> <world id> <beliefs> <mm30 corpus>

Kernel-level: no science command creates a corpus (design C2, filed). Each step is
journaled in `<state>/genesis-progress.json`; a rerun reports what exists and stops.
"""
from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

import yaml

from common import AUTHORITY, State, now, read_json, stop, write_json

VOCABULARIES = {
    "mm30 concept vocabulary": "CONCEPTS",
    "mm30 stage-level vocabulary": "LEVELS",
    "mm30 measure vocabulary": "MEASURES",
    "mm30 identification vocabulary": "IDENTIFICATIONS",
}
CHAIN = ("mm30-cut22.yaml", "mm30-cut31.yaml", "mm30.yaml")
CONFIG = """\
world_root = "worlds/{world_id}/world"
world_id = "{world_id}"
corpus_roots = ["worlds/{world_id}/corpora/mm30",
                "worlds/{world_id}/corpora/working"]
write_root = "worlds/{world_id}/corpora/working"
operations_root = "worlds/{world_id}/ops"
store_root = "worlds/{world_id}/store"
domains = ["biology"]
contracts = [{{ document = "contracts/mm30/mm30.yaml", predecessors = ["contracts/mm30/mm30-cut22.yaml", "contracts/mm30/mm30-cut31.yaml"] }}]
coordination = 2
"""


def front_matter(path: Path) -> dict:
    text = path.read_text()
    if not text.startswith("---\n"):
        stop(f"{path} has no front matter")
    return yaml.safe_load(text.split("---\n", 2)[1])


def records(corpus: Path, kind: str) -> list[dict]:
    return [front_matter(path) for path in sorted((corpus / kind).glob("*.md"))]


def vocabulary_addresses(mm30_corpus: Path) -> dict[str, str]:
    found: dict[str, list[str]] = {token: [] for token in VOCABULARIES.values()}
    for record in records(mm30_corpus, "dataset"):
        token = VOCABULARIES.get(record["title"])
        if token is not None:
            found[token].append(record["id"].removeprefix("dataset:"))
    if any(len(ids) != 1 for ids in found.values()):
        stop(f"vocabulary records not found exactly once in {mm30_corpus}: {found}")
    return {token: ids[0] for token, ids in found.items()}


def concrete_documents(beliefs: Path, out: Path, addresses: dict[str, str]) -> list[Path]:
    if out.exists():
        stop(f"{out} exists; the contract copies are written once")
    source = beliefs / "python" / "tools" / "reproduction"
    texts = {}
    for name in CHAIN:
        lines = (source / name).read_text().splitlines(keepends=True)
        also = [line for line in lines if line.startswith("also:")]
        if len(also) != 1:
            stop(f"{source / name}: expected one top-level `also:` line, found {len(also)}")
        text = "".join(line for line in lines if not line.startswith("also:"))
        for token, address in addresses.items():
            text = text.replace("{{" + token + "}}", address)
        if "{{" in text:
            stop(f"{source / name}: a vocabulary token is left after substitution")
        texts[name] = text
    out.mkdir(parents=True)
    paths = []
    for name in CHAIN:
        (out / name).write_text(texts[name])
        paths.append(out / name)
    return paths


def pinned_identity(mm30_corpus: Path) -> str:
    manifest = yaml.safe_load((mm30_corpus / "corpus.yaml").read_text())
    return manifest["profile"]["domains"]["mm30"].removeprefix("mm30:")


def write_config(data_root: Path, world_id: str) -> Path:
    path = data_root / "science.toml"
    if path.exists():
        stop(f"{path} exists; genesis writes it once")
    path.write_text(CONFIG.format(world_id=world_id))
    return path


def make_working_corpus(cfg, authority) -> str:
    from beliefs.consulted import CorpusPins
    from beliefs.root import init_corpus_root, open_corpus, open_world
    from beliefs.world import Fresh

    if cfg.write_root.exists():
        stop(f"{cfg.write_root} exists; the working corpus is created once")
    init_corpus_root(cfg.write_root, authority=authority)
    open_corpus(cfg.write_root, authority=authority, profile=cfg.profile).adopt_manifest(profile=CorpusPins(
        science_contract="science:" + cfg.profile.base_contract_identity,
        domains={ns: f"{ns}:{identity}" for ns, identity in cfg.profile.activated_contracts.items()},
    ))
    open_world(cfg.world, authority=authority).admit(cfg.write_root, provenance=Fresh())
    return yaml.safe_load((cfg.write_root / "corpus.yaml").read_text())["corpus_id"]


def install_holdings_reducer(cfg, authority) -> dict:
    """The holdings reducer, a rule the world holds, installed as the mm30 record's
    world creation and science's fixture worlds install it. A world reconstructed by
    relocation holds none, `science epoch` installs only the four enumeration rules,
    and no science command installs it (a finding): without it every read of holdings,
    so every citing write, fails `RuleNotHeld`. Re-running over unchanged content
    submits nothing."""
    from beliefs.holdings.reduce import holdings_rule_bundle
    from beliefs.root import open_world
    from beliefs.world.rules import install_rule_binding

    binding = install_rule_binding(open_world(cfg.world, authority=authority), holdings_rule_bundle())
    return {"symbol": holdings_rule_bundle().symbol, "binding": repr(binding)}


class Progress:
    def __init__(self, state: State):
        self.path = state.path / "genesis-progress.json"
        self.value = read_json(self.path) if self.path.exists() else {
            "world_id": state.world["world_id"], "steps": {}}
        if self.value["world_id"] != state.world["world_id"]:
            stop(f"{self.path} is bound to world {self.value['world_id']}")

    def done(self, step: str, result) -> None:
        self.value["steps"][step] = {"at": now(), "result": result}
        write_json(self.path, self.value)


def expected_pins(mm30_corpus: Path) -> dict[str, str]:
    """The writer's pins as the mm30 corpus's own manifest names them, plus the
    shipped coordination v2 the config activates (design §5.2)."""
    from beliefs.profile import shipped_coordination

    profile = yaml.safe_load((mm30_corpus / "corpus.yaml").read_text())["profile"]
    return {
        "science": profile["science_contract"].removeprefix("science:"),
        **{ns: value.split(":", 1)[1] for ns, value in profile["domains"].items()},
        "coordination": shipped_coordination(2).content_identity,
    }


def rehearse(beliefs: Path, addresses: dict, world_id: str, mm30_corpus: Path) -> tuple[str, dict]:
    """The documents, the chain and the config, built and loaded in a temporary data
    root before anything is written to the real one."""
    from beliefs.profile import shipped_base_contract
    from science.config import load_config
    from science.contracts import load_contract_chain

    scratch = Path(tempfile.mkdtemp(prefix="sci-0d00d2-genesis-"))
    try:
        documents = concrete_documents(beliefs, scratch / "contracts" / "mm30", addresses)
        chain = load_contract_chain(documents[-1], documents[:-1], shipped_base_contract())[0].content_identity
        cfg = load_config(write_config(scratch, world_id))
        pins = {"science": cfg.profile.base_contract_identity, **dict(cfg.profile.activated_contracts)}
    finally:
        shutil.rmtree(scratch)
    pinned = pinned_identity(mm30_corpus)
    if chain != pinned:
        stop(f"the chain compiles to {chain}; the mm30 corpus pins {pinned}")
    expected = expected_pins(mm30_corpus)
    if pins != expected:
        stop(f"the config compiles pins {pins}; expected {expected}")
    return chain, pins


def existing_world(data_root: Path, world_id: str, mm30_corpus: Path) -> None:
    from beliefs.root import open_world_read
    from beliefs.world import WorldConfig

    home = data_root / "worlds" / world_id
    if mm30_corpus != home / "corpora" / "mm30":
        stop(f"{mm30_corpus} is not {home}/corpora/mm30")
    open_world_read(WorldConfig(home / "world", world_id, (mm30_corpus,)))
    for path in (home / "corpora" / "working", home / "corpora" / "working.metadata", data_root / "science.toml",
                 data_root / "contracts" / "mm30"):
        if path.exists():
            stop(f"{path} exists before genesis")


def cleanup_list(state: State) -> list[str]:
    home = state.data_root / "worlds" / state.world["world_id"]
    return [str(p) for p in (state.data_root / "contracts" / "mm30", state.data_root / "science.toml",
                             home / "corpora" / "working", home / "corpora" / "working.metadata",
                             home / "ops", state.path) if p.exists()]


def main(argv: list[str]) -> int:
    if len(argv) != 6:
        print(__doc__)
        return 2
    state_path, data_root, world_id, beliefs, mm30_corpus = (
        Path(argv[1]).resolve(), Path(argv[2]).resolve(), argv[3], Path(argv[4]).resolve(), Path(argv[5]).resolve())
    if (state_path / "genesis-progress.json").exists():
        progress = read_json(state_path / "genesis-progress.json")
        print(yaml.safe_dump(progress, sort_keys=False))
        if "holdings_reducer" in progress["steps"]:
            print("genesis is complete; nothing re-created")
            return 0
        if "working_corpus" in progress["steps"]:
            print("genesis stopped after the working corpus, before the holdings reducer; installing it "
                  "(idempotent: unchanged content submits nothing)")
            state = State(state_path)
            reducer = install_holdings_reducer(state.load_config(), AUTHORITY)
            Progress(state).done("holdings_reducer", reducer)
            return 0
        print("genesis stopped partway. What it wrote, to inspect before anything else:")
        for path in cleanup_list(State(state_path)):
            print(f"  {path}")
        if "working_corpus_attempt" in progress["steps"]:
            print("  the corpus init/adopt/admit was attempted: read the world registry for an admission of "
                  "corpora/working before removing anything")
        return 3

    # Everything is checked before the first write to the data root.
    existing_world(data_root, world_id, mm30_corpus)
    addresses = vocabulary_addresses(mm30_corpus)
    chain, pins = rehearse(beliefs, addresses, world_id, mm30_corpus)

    config_path = data_root / "science.toml"
    state = State.create(state_path, world_id=world_id, data_root=data_root, config=config_path)
    progress = Progress(state)
    progress.done("addresses", addresses)
    progress.done("checked", {"chain": chain, "pins": pins})
    documents = concrete_documents(beliefs, data_root / "contracts" / "mm30", addresses)
    progress.done("documents", [str(path) for path in documents])
    write_config(data_root, world_id)
    progress.done("config", str(config_path))
    cfg = state.load_config()
    loaded = {"science": cfg.profile.base_contract_identity, **dict(cfg.profile.activated_contracts)}
    if loaded != pins:
        stop(f"the written config compiles {loaded}, the checked one {pins}")
    progress.done("working_corpus_attempt", str(cfg.write_root))
    corpus_id = make_working_corpus(cfg, AUTHORITY)
    progress.done("working_corpus", {"corpus_id": corpus_id, "pins": pins})
    reducer = install_holdings_reducer(cfg, AUTHORITY)
    progress.done("holdings_reducer", reducer)
    print(f"chain: mm30:{chain}")
    for namespace, identity in pins.items():
        print(f"pin: {namespace}:{identity}")
    print(f"working corpus: {corpus_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
