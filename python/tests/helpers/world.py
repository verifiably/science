import secrets
from pathlib import Path

from beliefs import stored
from beliefs.consulted import CorpusPins
from beliefs.permit import Authority, WritePermit
from beliefs.profile import compile_profile, shipped_base_contract, shipped_domain_contract
from beliefs.root import init_corpus_root, init_world_root, open_corpus, open_world
from beliefs.world import Fresh, WorldConfig

from science.config import ScienceConfig

# Fixture worlds are built by tests, which hold the full permit the way the beliefs
# test helper does; science code itself never constructs one (design §4.2).
FIXTURE_AUTHORITY = Authority(WritePermit.full(), "fixture")

DOMAINS = ("biology",)
PROFILE = compile_profile(
    shipped_base_contract(),
    [shipped_domain_contract(namespace) for namespace in DOMAINS],
)
# Derived, never authored: `require_pins_agree` refuses a manifest whose pins do
# not name exactly the identities this profile compiled from.
PINS = CorpusPins(
    science_contract="science:" + PROFILE.base_contract_identity,
    domains={
        namespace: f"{namespace}:{identity}"
        for namespace, identity in PROFILE.activated_contracts.items()
    },
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
    writer = open_corpus(corpus_root, authority=FIXTURE_AUTHORITY, profile=PROFILE)
    writer.adopt_manifest(profile=PINS)
    world = open_world(config, authority=FIXTURE_AUTHORITY)
    world.admit(corpus_root, provenance=Fresh())
    writer.add(fixture_proposition_node("p1"))
    return ScienceConfig(
        world=config,
        operations_root=work / "ops",
        profile=PROFILE,
        service_socket=work / "ops" / "service.sock",
    )


def write_cli_config(
    work: Path, operations_root: Path | None = None, service_socket: Path | None = None
) -> Path:
    """`operations_root` overrides where the session ledger lives and, absent
    `service_socket`, the socket beside it. Tests that bind a socket need a
    short path: the AF_UNIX limit is 107 bytes and the certified work root
    eats most of that."""
    cfg = build_fixture_world(work)
    ops = cfg.operations_root if operations_root is None else operations_root
    socket_line = "" if service_socket is None else f'service_socket = "{service_socket}"\n'
    path = work / "science.toml"
    path.write_text(f'''\
world_root = "{cfg.world.world_root}"
world_id = "{cfg.world.world_id}"
corpus_roots = ["{cfg.world.corpus_roots[0]}"]
operations_root = "{ops}"
domains = {list(DOMAINS)!r}
{socket_line}''')
    return path


def add_one_more_record(cfg: ScienceConfig) -> None:
    open_corpus(
        cfg.world.corpus_roots[0], authority=FIXTURE_AUTHORITY, profile=PROFILE
    ).add(fixture_proposition_node("p2"))
