"""Exposure and reservation records over the configured live mounts, as one kernel record view."""
from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace

from beliefs.errors import ScienceError
from nodes.core.errors import NodesError, RefError
from nodes.core.node import Node

from science.config import Mount, ReadContext
from science.lookup import captured_mounts, located_among
from science.refusal import Refused, kernel_refusal

__all__ = ["LiveRecords", "kernel_reads"]

@dataclass(frozen=True)
class LiveRecords:
    """A kernel `RecordView` of one kind over every configured non-retired mount, captured once. Agreeing
    copies of an address are one record and differing copies refuse, naming their holders. `SessionRecords`
    is the other boundary: it selects accepted records among what the session mounts."""
    ctx: ReadContext
    mounts: tuple[Mount, ...]
    kind: str

    @classmethod
    def capture(cls, ctx: ReadContext, kind: str) -> LiveRecords:
        return cls(ctx, captured_mounts(ctx), kind)

    def of(self, kind: str) -> LiveRecords:
        """The same capture, enumerating another kind."""
        return replace(self, kind=kind)

    def get(self, ref: str) -> Node:
        found = located_among(self.ctx, self.mounts, ref)
        if found is None:
            raise RefError(f"{ref}: no configured live corpus holds it")
        return found.node

    def iter_stored(self) -> Iterator[Node]:
        addresses = {node.id for mount in self.mounts for node in mount.view.iter_stored() if node.kind == self.kind}
        for ref in sorted(addresses):
            yield self.get(ref)


@contextmanager
def kernel_reads():
    """Kernel and record-store errors of a read become structured refusals; one already raised passes through."""
    try:
        yield
    except (ScienceError, NodesError, OSError) as caught:
        raise Refused(kernel_refusal(caught)) from caught
