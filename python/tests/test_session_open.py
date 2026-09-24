from pathlib import Path

import pytest

from helpers.world import build_fixture_world, build_world_without_coordination
from science.cursor import MIN_OUTPUT_BUDGET
from science.refusal import Refused
from science.schema import Declaration, WriteClass

MINT_PROJECT = Declaration("mint-project", "fixture", WriteClass("coordination"),
                           MIN_OUTPUT_BUDGET, (), (), Path("."))


def mint_project_handler(ctx, writer):
    from science.report import record_block
    node = writer.mint_coordination("project", project=None, content={
        "name": "health", "body": "", "author": writer.actor, "at": "2026-09-24T00:00:00Z",
        "query": {"version": "science.view-query.v1", "clauses": []}})
    return (record_block(node),)


def _dispatch(cfg):
    from science.config import ReadContext
    from science.dispatch import Dispatcher
    from science.session import open_session
    session = open_session(cfg)
    return session, Dispatcher((MINT_PROJECT,), {"mint-project": mint_project_handler},
                               ReadContext.open(cfg), session=session)


def test_session_opened_by_science_can_mint_a_project(certified_work):
    session, d = _dispatch(build_fixture_world(certified_work))
    try:
        assert "[project] project:" in d.invoke("mint-project", {}).text
    finally:
        session.close()


def test_without_coordination_a_project_mint_is_unavailable(certified_work):
    session, d = _dispatch(build_world_without_coordination(certified_work))
    try:
        with pytest.raises(Refused) as caught:
            d.invoke("mint-project", {})
    finally:
        session.close()
    assert caught.value.refusal.code == "kernel-refused"
    assert caught.value.refusal.data["kind"] == "CoordinationUnavailable"


def test_coordination_asked_of_a_corpus_that_does_not_pin_it_refuses_at_open(certified_work):
    """Spec §6: every pre-coordination config takes this path once it is
    upgraded with `coordination = 2`, so the refusal names the root and the
    remedy, before any session exists."""
    from dataclasses import replace

    from helpers.world import PROFILE
    from science.session import open_session

    bare = build_world_without_coordination(certified_work)
    with pytest.raises(Refused) as caught:
        open_session(replace(bare, profile=PROFILE, coordination=2))
    refusal = caught.value.refusal
    assert refusal.code == "invalid-input"
    assert str(bare.world.corpus_roots[0]) in refusal.message
    assert "asks for coordination the corpus at" in refusal.message
    assert "coordination = false" in refusal.message
    assert not (bare.operations_root / "sessions").exists()


def test_coordination_pinned_at_another_version_refuses_at_open(certified_work):
    """A root that pins a coordination contract other than the one the
    configuration compiles is refused by name too, not left to the kernel's
    bare pin mismatch."""
    from beliefs.consulted import CorpusPins
    from beliefs.profile import compile_profile, shipped_base_contract, shipped_coordination, shipped_domain_contract
    from beliefs.root import init_corpus_root, init_store_root, init_world_root, open_corpus, open_world
    from beliefs.world import Fresh, WorldConfig
    import secrets

    from helpers.world import DOMAINS, FIXTURE_AUTHORITY, PROFILE
    from science.config import ScienceConfig
    from science.session import open_session

    v1 = compile_profile(shipped_base_contract(), [shipped_domain_contract(ns) for ns in DOMAINS],
                         coordination=shipped_coordination(1))
    root = certified_work / "corpus"
    world = WorldConfig(certified_work / "world", secrets.token_hex(16), (root,))
    init_world_root(world, authority=FIXTURE_AUTHORITY)
    init_corpus_root(root, authority=FIXTURE_AUTHORITY)
    open_corpus(root, authority=FIXTURE_AUTHORITY, profile=v1).adopt_manifest(profile=CorpusPins(
        science_contract="science:" + v1.base_contract_identity,
        domains={ns: f"{ns}:{identity}" for ns, identity in v1.activated_contracts.items()},
    ))
    open_world(world, authority=FIXTURE_AUTHORITY).admit(root, provenance=Fresh())
    init_store_root(certified_work / "store", authority=FIXTURE_AUTHORITY)
    cfg = ScienceConfig(world=world, operations_root=certified_work / "ops", profile=PROFILE,
                        service_socket=certified_work / "ops" / "service.sock",
                        store_root=certified_work / "store", coordination=2)
    with pytest.raises(Refused) as caught:
        open_session(cfg)
    refusal = caught.value.refusal
    assert refusal.code == "invalid-input"
    assert str(root) in refusal.message
    assert "coordination = 2" in refusal.message


def test_read_context_resolver_needs_coordination(certified_work):
    from science.config import ReadContext

    ctx = ReadContext.open(build_world_without_coordination(certified_work))
    with pytest.raises(Refused) as caught:
        ctx.coordination()
    assert caught.value.refusal.code == "invalid-input"
    assert "coordination = false" in caught.value.refusal.message
