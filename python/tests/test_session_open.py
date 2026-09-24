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
    from dataclasses import replace

    from beliefs.errors import ContractMismatch
    from helpers.world import PROFILE
    from science.session import open_session

    bare = build_world_without_coordination(certified_work)
    with pytest.raises(ContractMismatch):
        open_session(replace(bare, profile=PROFILE, coordination=2))


def test_read_context_resolver_needs_coordination(certified_work):
    from science.config import ReadContext

    ctx = ReadContext.open(build_world_without_coordination(certified_work))
    with pytest.raises(Refused) as caught:
        ctx.coordination()
    assert caught.value.refusal.code == "invalid-input"
    assert "coordination = false" in caught.value.refusal.message
