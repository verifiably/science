"""Fixture authority and dispatchers for research command tests."""
from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from beliefs import stored
from beliefs.corpus import CorpusWriter, mark_root_unresolved
from beliefs.root import durable_executor_factory, durable_operation_port, open_corpus
from beliefs.source_assertion import Bearing, Reading, Representation, SourceAssertion, Span
from helpers.world import FIXTURE_AUTHORITY, archive_config
from nodes.core.frontmatter import node_to_markdown
from nodes.core.ids import NodeId
from nodes.core.node import Node
from science.config import ReadContext
from science.coordination import now, parse_query_text
from science.cursor import MIN_OUTPUT_BUDGET
from science.dispatch import Dispatcher
from science.loader import production_tree, resolve_handlers
from science.report import record_block
from science.schema import Declaration, InputSpec, WriteClass
from science.session import open_session

__all__ = [
    "MINT_COORDINATION",
    "add_shared_source",
    "add_source",
    "add_source_assertion",
    "correct_source",
    "mint_coordination_handler",
    "raw_write_node",
    "research_rig",
]


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


def add_source_assertion(
    cfg,
    where: str,
    *,
    source: str,
    proposition: str,
    sign: str = "asserts",
    quote: str = "Quoted span.",
    locator: str = "Results, [1]",
    sha256: str = "a" * 64,
    media_type: str = "text/markdown",
    extent: str = "full",
    extracted_by: str = "agent:reader",
    attributed_to: str | None = None,
    title: str = "Paraphrase.",
    body: str = "",
) -> Node:
    """Mint a stored `source-assertion` in `"corpus"` or `"archive"` with
    `FIXTURE_AUTHORITY` (`recorded_by = FIXTURE_AUTHORITY.actor`)."""
    target = {"corpus": cfg, "archive": archive_config(cfg)}[where]
    root = target.write_root.resolve()
    read_mounts = tuple(r.resolve() for r in target.world.corpus_roots if r.resolve() != root)
    value = SourceAssertion(
        source=source,
        read=Reading(
            representation=Representation(sha256=sha256, media_type=media_type, extent=extent),
            span=Span(quote=quote, locator=locator),
            extracted_by=extracted_by,
            attributed_to=attributed_to,
        ),
        bears_on=Bearing(sign=sign, proposition=proposition),
        recorded_by=FIXTURE_AUTHORITY.actor,
    )
    node = stored.source_assertion_node(value, title=title, body=body)
    writer = CorpusWriter(
        root,
        durable_executor_factory(),
        authority=FIXTURE_AUTHORITY,
        profile=target.profile,
        operation_port=durable_operation_port(root, FIXTURE_AUTHORITY, profile=target.profile),
        read_mounts=read_mounts,
    )
    return writer.add(node)


def raw_write_node(root: Path, node: Node) -> Path:
    """Write `node_to_markdown(node)` directly to
    `root / parsed.kind / f"{parsed.slug.replace(':', '__')}.md"` (`NodeId.parse`),
    bypassing writer preflight so readback/occupancy tests can seed damaged or
    `deprecated_ids` records before opening `ReadContext`."""
    parsed = NodeId.parse(node.id)
    path = Path(root) / parsed.kind / f"{parsed.slug.replace(':', '__')}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(node_to_markdown(node), encoding="utf-8")
    mark_root_unresolved(Path(root))
    return path


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
