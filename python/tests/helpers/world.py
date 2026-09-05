import secrets
from pathlib import Path

from beliefs import stored
from beliefs.consulted import CorpusPins
from beliefs.permit import Authority, WritePermit
from beliefs.root import init_corpus_root, init_world_root, open_corpus, open_world
from beliefs.world import Fresh, WorldConfig

from science.config import ScienceConfig

# Fixture worlds are built by tests, which hold the full permit the way the beliefs
# test helper does; science code itself never constructs one (design §4.2).
FIXTURE_AUTHORITY = Authority(WritePermit.full(), "fixture")

PINS = CorpusPins(
    science_contract="science:" + "a" * 64,
    domains={"biology": "biology:" + "b" * 64},
)


def fixture_proposition_node(slug: str):
    return stored.proposition_node(slug, title=slug, claim={"operator": "affects"})


def fixture_source_node(slug: str):
    return stored.source_node(slug, title=slug, identifiers={"doi": "10.1/" + slug})


def build_fixture_world(work: Path) -> ScienceConfig:
    corpus_root = work / "corpus"
    config = WorldConfig(work / "world", secrets.token_hex(16), (corpus_root,))
    init_world_root(config, authority=FIXTURE_AUTHORITY)
    init_corpus_root(corpus_root, authority=FIXTURE_AUTHORITY)
    writer = open_corpus(corpus_root, authority=FIXTURE_AUTHORITY)
    writer.adopt_manifest(profile=PINS)
    world = open_world(config, authority=FIXTURE_AUTHORITY)
    world.admit(corpus_root, provenance=Fresh())
    writer.add(fixture_proposition_node("p1"))
    return ScienceConfig(world=config, operations_root=work / "ops")


def write_cli_config(work: Path) -> Path:
    cfg = build_fixture_world(work)
    path = work / "science.toml"
    path.write_text(f'''\
world_root = "{cfg.world.world_root}"
world_id = "{cfg.world.world_id}"
corpus_roots = ["{cfg.world.corpus_roots[0]}"]
operations_root = "{cfg.operations_root}"
''')
    return path


def add_one_more_record(cfg: ScienceConfig) -> None:
    open_corpus(cfg.world.corpus_roots[0], authority=FIXTURE_AUTHORITY).add(fixture_proposition_node("p2"))
