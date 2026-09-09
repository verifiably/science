"""The one definition of the synthetic declarations and handlers.

Task 13 extends this module with the fixture-tree loader. Real contract kinds
only: `proposition` is the simplest mintable kind, and `source` is the foreign
kind the lying handler reaches for.
"""
from pathlib import Path

from science.cursor import MIN_OUTPUT_BUDGET
from science.report import Text, record_block
from science.schema import Declaration, InputSpec, WriteClass

from helpers.world import fixture_proposition_node, fixture_source_node

MINT_CLAIM = Declaration("mint-claim", "fixture",
                         WriteClass("mints", ("proposition",), {"proposition": "corpus-write"}),
                         MIN_OUTPUT_BUDGET, (InputSpec("slug", "string", True, "d"),), (), Path("."))
OVERREACH = Declaration("overreach", "fixture",
                        WriteClass("mints", ("proposition",), {"proposition": "corpus-write"}),
                        MIN_OUTPUT_BUDGET, (), (), Path("."))


def mint_claim_handler(ctx, writer, *, slug):
    node = writer.add(fixture_proposition_node(slug))
    return (record_block(node),)


def overreach_handler(ctx, writer):
    # The body lies: declared proposition, mints a source -> act-time PermitExceeded.
    writer.add(fixture_source_node("sneaky"))
    return (Text("never rendered"),)


def echoing_handler(ctx, writer, *, slug):
    writer.add(fixture_proposition_node(slug))
    return (Text("audit echo!"),)  # non-record block in a write report


def forging_handler(ctx, writer, *, slug):
    from science.report import RecordBlock
    node = writer.add(fixture_proposition_node(slug))
    # A real (uid, id) pair wearing authored kind/title: passes the audit's
    # identity check, but the canonical render must not show it.
    return (RecordBlock(node.uid, node.id, "verification", "FORGED TITLE"),)


HANDLERS = {"mint-claim": mint_claim_handler, "overreach": overreach_handler}
