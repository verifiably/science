"""Fixture authority and dispatchers for research command tests."""
from contextlib import contextmanager
from pathlib import Path

from beliefs import stored
from beliefs.root import open_corpus
from helpers.world import FIXTURE_AUTHORITY, archive_config
from science.config import ReadContext
from science.coordination import now, parse_query_text
from science.cursor import MIN_OUTPUT_BUDGET
from science.dispatch import Dispatcher
from science.loader import production_tree, resolve_handlers
from science.report import record_block
from science.schema import Declaration, InputSpec, WriteClass
from science.session import open_session


def add_source(cfg, where: str, title: str, **identifiers):
    target = {"corpus": cfg, "archive": archive_config(cfg)}[where]
    node = stored.source_node(title=title, identifiers=identifiers)
    open_corpus(target.write_root, authority=FIXTURE_AUTHORITY, profile=target.profile).add(node)
    return node


def add_shared_source(cfg, title: str, **identifiers):
    node = add_source(cfg, "corpus", title, **identifiers)
    archive = archive_config(cfg)
    open_corpus(archive.write_root, authority=FIXTURE_AUTHORITY, profile=archive.profile).add(node)
    return node


def correct_source(cfg, address: str, *, grounds: str = "fixture", **identifiers):
    return open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile).correct_identifier(
        address, identifiers, grounds=grounds)


MINT_COORDINATION = Declaration("mint-coordination", "fixture", WriteClass("coordination"),
                               MIN_OUTPUT_BUDGET, (
                                   InputSpec("kind", "enum", True, "Kind", choices=("note", "topic")),
                                   InputSpec("name", "string", True, "Name"),
                                   InputSpec("body", "string", True, "Body"),
                                   InputSpec("about", "list-of-string", False, "Cited addresses"),
                                   InputSpec("query", "string", False, "Query YAML"),
                               ), (), Path("."))


def mint_coordination_handler(ctx, writer, *, kind, name, body, about=None, query=None):
    content = {"name": name, "body": body, "author": writer.actor, "at": now()}
    if about is not None:
        content["about"] = about
    if query is not None:
        content["query"] = parse_query_text(query)
    node = writer.mint_coordination(kind, project=ctx.current_project(), content=content)
    return (record_block(node),)


@contextmanager
def research_rig(cfg, names, *, extra=()):
    decls = tuple(decl for decl in production_tree() if decl.name in names)
    handlers = resolve_handlers(decls)
    for decl, handler in extra:
        decls += (decl,)
        handlers[decl.name] = handler
    session = open_session(cfg)
    ctx = ReadContext.open(cfg)
    try:
        yield Dispatcher(decls, handlers, ctx, session=session), ctx
    finally:
        session.close()
