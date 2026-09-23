import secrets
from contextlib import contextmanager
from pathlib import Path

from beliefs import stored
from beliefs.consulted import CorpusPins
from beliefs.permit import Authority, WritePermit
from beliefs.profile import compile_profile, shipped_base_contract, shipped_domain_contract
from beliefs.root import init_corpus_root, init_store_root, init_world_root, open_corpus, open_world
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
STORE_IDS: dict[Path, str] = {}


def fixture_proposition_node(slug: str):
    return stored.proposition_node(slug, title=slug, claim={"operator": "affects"})


# A source has no slug: beliefs derives its address from the identifiers, so the slug
# reaches the id only through the DOI it names.
def fixture_source_node(slug: str):
    return stored.source_node(title=slug, identifiers={"doi": "10.1234/" + slug})


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
    store_root = work / "store"
    STORE_IDS[work] = init_store_root(store_root, authority=FIXTURE_AUTHORITY)
    _install_holdings_reducer(world)
    return ScienceConfig(
        world=config,
        operations_root=work / "ops",
        profile=PROFILE,
        service_socket=work / "ops" / "service.sock",
        store_root=store_root,
    )


def _install_holdings_reducer(world) -> None:
    # The holdings reducer is a rule the world holds (an epoch-family act, so
    # operator-time): reads derive active and blocked heads through it.
    from beliefs.holdings.reduce import holdings_rule_bundle
    from beliefs.world.rules import install_rule_binding
    install_rule_binding(world, holdings_rule_bundle())


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
contracts = []
store_root = "{cfg.store_root}"
{socket_line}''')
    return path


def add_one_more_record(cfg: ScienceConfig) -> None:
    open_corpus(
        cfg.world.corpus_roots[0], authority=FIXTURE_AUTHORITY, profile=PROFILE
    ).add(fixture_proposition_node("p2"))


TEST_CONTRACT = '''\
contract:
  contract: testing
  version: 1
  lineage: genesis
  sorts:
    concept:
      vocabulary: "dataset:%(concepts)s"
    protein:
      vocabulary: {namespace: HGNC, release: "2026-07-01"}
  dimensions: {}
  operators:
    affects-concept-protein:
      arity: 2
      arg_sorts: [concept, protein]
      sign_apt: true
      layers: [causal]
      dimensions: []
    affects-concept-concept:
      arity: 2
      arg_sorts: [concept, concept]
      sign_apt: true
      layers: [causal]
      dimensions: []
plan:
  sorts: {concept: concept, protein: protein}
  layers: {causal: causal}
  polarities: {positive: positive, negative: negative, not_applicable: null}
  operators:
    - {predicate: affects, subject: concept, object: protein, operator: affects-concept-protein}
    - {predicate: affects, subject: concept, object: concept, operator: affects-concept-concept}
'''
CONCEPTS = b"concept:disease-stage\nconcept:remission\n"


def concept_list_address() -> str:
    from hashlib import sha256
    from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
    digest = "sha256:" + sha256(CONCEPTS).hexdigest()
    return dataset_address(DatasetDeclaration(resources=(ResourceDeclaration(name="concepts.txt", digest=digest),)))


def fixture_contract_document(work: Path) -> Path:
    path = work / "testing.yaml"
    path.write_text(TEST_CONTRACT % {"concepts": concept_list_address().removeprefix("dataset:")})
    return path


def build_fixture_world_with_contract(work: Path, *, hold_concepts: bool = True) -> ScienceConfig:
    """A world whose profile compiles the test contract; the concept list held
    (or not), one proposition minted under the plan's first row."""
    from beliefs.profile import shipped_base_contract
    from science.contracts import load_contract_document
    base = shipped_base_contract()
    contract, plan = load_contract_document(fixture_contract_document(work), base)
    profile = compile_profile(base, [shipped_domain_contract(ns) for ns in DOMAINS] + [contract])
    pins = CorpusPins(
        science_contract="science:" + profile.base_contract_identity,
        domains={ns: f"{ns}:{identity}" for ns, identity in profile.activated_contracts.items()},
    )
    corpus_root = work / "corpus"
    config = WorldConfig(work / "world", secrets.token_hex(16), (corpus_root,))
    init_world_root(config, authority=FIXTURE_AUTHORITY)
    init_corpus_root(corpus_root, authority=FIXTURE_AUTHORITY)
    store_id = init_store_root(work / "store", authority=FIXTURE_AUTHORITY)
    STORE_IDS[work] = store_id
    writer = open_corpus(corpus_root, authority=FIXTURE_AUTHORITY, profile=profile)
    writer.adopt_manifest(profile=pins)
    world = open_world(config, authority=FIXTURE_AUTHORITY)
    world.admit(corpus_root, provenance=Fresh())
    _install_holdings_reducer(world)
    cfg = ScienceConfig(world=config, operations_root=work / "ops", profile=profile,
                        service_socket=work / "ops" / "service.sock", store_root=work / "store",
                        plans=(plan,))
    if hold_concepts:
        hold_fixture_dataset(cfg, "concepts.txt", CONCEPTS, "concept vocabulary")
    return cfg


def hold_fixture_dataset(cfg: ScienceConfig, name: str, content: bytes, title: str, **facets) -> str:
    """Hold bytes the way the `dataset` command will: content-derived location,
    Found observation, dataset record under the content address. Tests hold the
    full authority; the command goes through the scoped writer."""
    from hashlib import sha256
    from beliefs import stored
    from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
    from beliefs.holdings.boundary import ActContext, write
    from beliefs.holdings.records import StoreLocator
    from beliefs.root import holdings_seam
    digest = "sha256:" + sha256(content).hexdigest()
    (root,) = cfg.world.corpus_roots
    ctx = ActContext(root, cfg.store_root, "fixture", "fixture/hold.v1", FIXTURE_AUTHORITY,
                     holdings_seam(), profile=cfg.profile)
    write(ctx, StoreLocator(STORE_IDS[root.parent], f"{digest.removeprefix('sha256:')}/{name}"),
          content, expected=digest)
    address = dataset_address(DatasetDeclaration(resources=(ResourceDeclaration(name=name, digest=digest),)))
    node = stored.dataset_node(title=title, resources=[{"name": name, "digest": digest}], **facets)
    assert dataset_address(stored.dataset_declaration(node)) == address
    return open_corpus(root, authority=FIXTURE_AUTHORITY, profile=cfg.profile).add(node).id


def unhold_fixture_dataset(cfg: ScienceConfig, ref: str) -> None:
    """Delete the held bytes and publish the Absent observation that supersedes
    the Found: the state a later re-check would leave."""
    from beliefs import stored
    from beliefs.holdings.boundary import ActContext, delete
    from beliefs.root import holdings_seam
    from science.config import ReadContext
    (root,) = cfg.world.corpus_roots
    _, view = ReadContext.open(cfg).single_view()
    (resource,) = stored.dataset_declaration(view.get(ref)).resources
    relative = f"{resource.digest.removeprefix('sha256:')}/{resource.name}"
    standing = tuple(stored.holdings_observation_value(n) for n in view.iter_stored()
                     if n.kind == "holdings-observation"
                     and stored.holdings_observation_value(n).location.relative_path == relative)
    ctx = ActContext(root, cfg.store_root, "fixture", "fixture/hold.v1", FIXTURE_AUTHORITY,
                     holdings_seam(), profile=cfg.profile)
    delete(ctx, standing[0].location, standing=standing)


SPEC_FIELDS = {"estimand": "difference in PHF19 expression", "method": "rank comparison",
               "assumptions": "independent samples", "falsification": "no difference at alpha",
               "applicability": "samples with a stage token",
               "interpretation_rule": "beliefs/outcome-file/v1",
               "equivalence_rule": "beliefs/content-identity-equality/v1"}


@contextmanager
def open_rig(cfg: ScienceConfig, names: tuple[str, ...]):
    """A dispatcher over the production declarations named, with an attended
    session over `cfg`; yields (dispatcher, read context). Task 4 adds
    `store_root=cfg.store_root` to the session call once the seam lands."""
    from beliefs.session import open_attended_session
    from science.config import ReadContext
    from science.dispatch import Dispatcher
    from science.loader import production_tree, resolve_handlers
    decls = tuple(d for d in production_tree() if d.name in names)
    session = open_attended_session(cfg.world, cfg.operations_root, profile=cfg.profile)
    ctx = ReadContext.open(cfg)
    try:
        yield Dispatcher(decls, resolve_handlers(decls), ctx, session=session), ctx
    finally:
        session.close()


def build_belief_world(work: Path) -> ScienceConfig:
    """The contract world plus one proposition typed under the plan: the
    starting state for claim/spec/run/assess/verify/belief/next tests."""
    from beliefs import stored
    from beliefs.claim import Referent, build_claim
    from beliefs.projection import project_claim
    cfg = build_fixture_world_with_contract(work)
    (plan,) = cfg.plans
    claim = build_claim(cfg.profile, operator=plan.operator_for("affects", "concept", "protein"),
                        args=(Referent(sort=plan.sort_for("concept"), term="concept:disease-stage"),
                              Referent(sort=plan.sort_for("protein"), term="protein:PHF19")),
                        layer="causal", polarity="positive")
    node = stored.proposition_node("p1", title="p1", claim=project_claim(claim),
                                   display_statement="concept:disease-stage affects protein:PHF19")
    open_corpus(cfg.world.corpus_roots[0], authority=FIXTURE_AUTHORITY, profile=cfg.profile).add(node)
    return cfg


FIXTURE_SNAKEFILE = '''\
rule outcome:
    input: "inputs/data.txt"
    output: "outputs/stats.tsv", "outputs/outcome.txt"
    run:
        import pathlib
        pathlib.Path(input[0]).read_text()
        pathlib.Path(output[0]).write_text("n\\t1\\n")
        pathlib.Path(output[1]).write_text("%(outcome)s\\n")
'''


def fixture_bundle(work: Path, outcome: str = "supported") -> tuple[Path, str, tuple[str, ...]]:
    code = work / "analysis"
    (code / "workflow").mkdir(parents=True, exist_ok=True)
    (code / "workflow" / "Snakefile").write_text(FIXTURE_SNAKEFILE % {"outcome": outcome})
    return code, "analysis/workflow/Snakefile", ("outputs/stats.tsv", "outputs/outcome.txt")


def mint_fixture_run(cfg: ScienceConfig, spec_ref: str, dataset_ref: str, bundle) -> str:
    """One assessment run under MINIMAL_POLICY through the kernel library, so
    assess/verify/belief/next tests have a run on hosts without bubblewrap."""
    import socket
    from datetime import UTC, datetime
    from beliefs import stored
    from beliefs.adapter import WorkflowDefinition
    from beliefs.boundary import RunMinted, execute_assessment_run
    from beliefs.dataset import dataset_address
    from beliefs.recipe import MINIMAL_POLICY
    from beliefs.root import durable_operation_port
    from beliefs.runrecord import run_ref
    from science.config import ReadContext
    code, entrypoint, targets = bundle
    ctx = ReadContext.open(cfg)
    _, view = ctx.single_view()
    spec = stored.analysis_spec_value(view.get(spec_ref), profile=cfg.profile)
    address = dataset_address(stored.dataset_declaration(view.get(dataset_ref)))
    (root,) = cfg.world.corpus_roots
    outcome = execute_assessment_run(
        spec=spec, port=durable_operation_port(root, FIXTURE_AUTHORITY, profile=cfg.profile),
        boundary_policy=MINIMAL_POLICY,
        definition=WorkflowDefinition(snakefile=(code / "workflow" / "Snakefile").read_bytes(), family_streams={}),
        code_roots=(code,), held_inputs={address: ctx.held_path(address)}, entrypoint=entrypoint,
        targets=targets, declared_outputs=targets, observer="fixture",
        started_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        host_realization=socket.gethostname(), scratch_base=cfg.operations_root / "scratch" / "fixture")
    assert isinstance(outcome, RunMinted), outcome
    return run_ref(outcome.run.address())
