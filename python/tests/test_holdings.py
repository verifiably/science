from hashlib import sha256
from pathlib import Path

from beliefs import stored
from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
from beliefs.holdings.boundary import ActContext, write
from beliefs.holdings.records import StoreLocator
from beliefs.root import holdings_seam, init_store_root, open_corpus

from helpers.world import FIXTURE_AUTHORITY, STORE_IDS, build_fixture_world
from science.config import ReadContext
from science.holdings import held_resources


def _sha256(data: bytes) -> tuple[str, str]:
    hex_digest = sha256(data).hexdigest()
    return f"sha256:{hex_digest}", hex_digest


def test_held_resources_resolves_each_member_by_digest(certified_work: Path) -> None:
    cfg = build_fixture_world(certified_work)
    store_id = STORE_IDS[certified_work]
    act = ActContext(
        cfg.write_root,
        cfg.store_root,
        "fixture",
        "fixture/hold.v1",
        FIXTURE_AUTHORITY,
        holdings_seam(),
        profile=cfg.profile,
    )
    members = {
        "datapackage.json": b'{"name": "gse24080"}\n',
        "tables/clinical.tsv": b"patient\tage\nP1\t62\n",
        "tables/expression.tsv": b"gene\tP1\nPHF19\t4.2\n",
    }
    resource_dicts = []
    resource_decls = []
    for name, content in sorted(members.items()):
        digest, hex_digest = _sha256(content)
        write(act, StoreLocator(store_id, f"{hex_digest}/{name}"), content, expected=digest)
        resource_dicts.append({"name": name, "digest": digest})
        resource_decls.append(ResourceDeclaration(name=name, digest=digest))

    declaration = DatasetDeclaration(resources=tuple(resource_decls))
    address = dataset_address(declaration)
    assert address is not None
    node = stored.dataset_node(title="GSE24080 package", resources=resource_dicts)
    open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile).add(node)

    ctx = ReadContext.open(cfg)
    resolved = ctx.held_resources(address)
    assert resolved == held_resources(ctx.read_views(), ctx.world, ctx._stores, address)
    assert set(resolved) == set(members)
    for name, expected_bytes in members.items():
        assert resolved[name].is_file()
        assert resolved[name].read_bytes() == expected_bytes


def test_held_resources_filters_configured_stores_before_filename_preference(
    certified_work: Path,
) -> None:
    cfg = build_fixture_world(certified_work)
    configured_id = STORE_IDS[certified_work]
    unconfigured_root = certified_work / "unconfigured_store"
    unconfigured_id = init_store_root(unconfigured_root, authority=FIXTURE_AUTHORITY)

    content = b"patient\tage\nP1\t62\n"
    digest, hex_digest = _sha256(content)

    # Observation 1: in an unconfigured store, matching f"/{resource.name}"
    act_unconfigured = ActContext(
        cfg.write_root,
        unconfigured_root,
        "fixture",
        "fixture/hold.v1",
        FIXTURE_AUTHORITY,
        holdings_seam(),
        profile=cfg.profile,
    )
    write(
        act_unconfigured,
        StoreLocator(unconfigured_id, f"{hex_digest}/tables/clinical.tsv"),
        content,
        expected=digest,
    )

    # Observation 2: in the configured store, same digest, different filename
    act_configured = ActContext(
        cfg.write_root,
        cfg.store_root,
        "fixture",
        "fixture/hold.v1",
        FIXTURE_AUTHORITY,
        holdings_seam(),
        profile=cfg.profile,
    )
    write(
        act_configured,
        StoreLocator(configured_id, f"{hex_digest}/other_name.tsv"),
        content,
        expected=digest,
    )

    declaration = DatasetDeclaration(
        resources=(ResourceDeclaration(name="tables/clinical.tsv", digest=digest),)
    )
    address = dataset_address(declaration)
    assert address is not None
    node = stored.dataset_node(
        title="clinical",
        resources=[{"name": "tables/clinical.tsv", "digest": digest}],
    )
    open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile).add(node)

    ctx = ReadContext.open(cfg)
    resolved = ctx.held_resources(address)
    assert resolved == {
        "tables/clinical.tsv": cfg.store_root / f"{hex_digest}/other_name.tsv"
    }
    assert resolved["tables/clinical.tsv"].read_bytes() == content


def test_held_resources_prefers_filename_match_within_configured_stores(
    certified_work: Path,
) -> None:
    cfg = build_fixture_world(certified_work)
    configured_id = STORE_IDS[certified_work]
    content = b"patient\tage\nP1\t62\n"
    digest, hex_digest = _sha256(content)

    act = ActContext(
        cfg.write_root,
        cfg.store_root,
        "fixture",
        "fixture/hold.v1",
        FIXTURE_AUTHORITY,
        holdings_seam(),
        profile=cfg.profile,
    )
    # 00_other.tsv sorts before tables/clinical.tsv in reducer order, so without
    # filename preference within configured stores it would be chosen first.
    write(
        act,
        StoreLocator(configured_id, f"{hex_digest}/00_other.tsv"),
        content,
        expected=digest,
    )
    write(
        act,
        StoreLocator(configured_id, f"{hex_digest}/tables/clinical.tsv"),
        content,
        expected=digest,
    )

    declaration = DatasetDeclaration(
        resources=(ResourceDeclaration(name="tables/clinical.tsv", digest=digest),)
    )
    address = dataset_address(declaration)
    assert address is not None
    node = stored.dataset_node(
        title="clinical",
        resources=[{"name": "tables/clinical.tsv", "digest": digest}],
    )
    open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile).add(node)

    ctx = ReadContext.open(cfg)
    resolved = ctx.held_resources(address)
    assert resolved == {
        "tables/clinical.tsv": cfg.store_root / f"{hex_digest}/tables/clinical.tsv"
    }
    assert resolved["tables/clinical.tsv"].read_bytes() == content
