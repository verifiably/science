"""Accept an externally recorded acquisition through the attended writer."""

from pathlib import Path

from beliefs.errors import MalformedRecord
from science.refusal import Refusal, Refused
from science.acquisition.imported import import_log


def handle(ctx, writer, *, log, members, journals, title, locator, accept_partial=None):
    try:
        return import_log(ctx, writer, Path(log), Path(members), Path(journals), title, locator, accept_partial)
    except MalformedRecord as exc:
        raise Refused(Refusal("invalid-input", str(exc))) from exc
