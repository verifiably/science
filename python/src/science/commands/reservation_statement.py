"""Check a chain's checked-in statement against the configured live corpora, or write it."""
from __future__ import annotations

from pathlib import Path

from beliefs.publication import MARKER_KIND
from beliefs.reservation import exposure_events

from science.config import Mount
from science.coordination import selected_project
from science.refusal import Refusal, Refused
from science.report import KeyVals, Report
from science.reservation import (
    LiveRecords,
    Statement,
    gate_of,
    kernel_reads,
    read_claims,
    read_statement,
    require_chain,
    require_current,
    require_reference,
    statement_digest,
    statement_paths,
    unconsidered_blocks,
    unconsidered_events,
    write_files,
)

__all__ = ["handle", "write"]


def _asked(chain: str, scope: str | None, as_of: str | None) -> None:
    require_chain(chain)
    require_reference("scope", scope, ("proposition:",))
    require_reference("as_of", as_of, ("reservation-assignment:",))


def _directory(text: str, field: str) -> Path:
    directory = Path(text)
    if not directory.is_absolute():
        raise Refused(Refusal("invalid-input", f"{field} {text!r} is not an absolute path", {"field": field}))
    return directory


def _corpus(mount: Mount, head: str) -> str:
    markers = sorted(node.uid for node in mount.view.iter_stored() if node.kind == MARKER_KIND)
    return (f"{'publication marker ' + ', '.join(markers) if markers else 'no publication marker'}; "
            f"{'holds' if mount.view.holds(head) else 'does not hold'} the head")


def _examined(records: LiveRecords, statement: Statement, project: object) -> KeyVals:
    """Every live corpus read, whether or not it holds the head: the gate reads events from all of them."""
    return KeyVals("examined", (
        ("project", "none" if project is None else str(project)),
        *((f"corpus {mount.corpus_id}", _corpus(mount, statement.head.id)) for mount in records.mounts)))


def _summary(statement: Statement, paths: tuple[Path, Path], as_of: str | None) -> KeyVals:
    head = statement.head
    return KeyVals("reservation statement", (
        ("chain", head.chain), ("scope", head.scope or "none"),
        ("head" if as_of is None else "as of", head.id),
        (paths[0].name, statement_digest(statement.json)), (paths[1].name, statement_digest(statement.page))))


def handle(ctx, *, chain: str, check: str, scope: str | None = None, as_of: str | None = None,
           block_on: list[str] | None = None, all_considered: bool | None = None) -> Report:
    _asked(chain, scope, as_of)
    gate = gate_of(block_on or (), bool(all_considered))
    if as_of is not None and (block_on or all_considered):
        raise Refused(Refusal("invalid-input", "as_of checks an earlier statement; the gate options apply to the "
                                               "current head only", {"field": "as_of"}))
    directory = _directory(check, "check")
    paths = statement_paths(directory, chain, scope)
    with kernel_reads():
        records = LiveRecords.capture(ctx, "reservation-assignment")
        statement = read_statement(records, chain, scope, as_of)
        require_current(statement, directory, paths)
        claims = read_claims(ctx)
        outstanding = () if as_of is not None else unconsidered_events(
            statement.head, exposure_events(records.of("exposure-event")), claims)
    gate.require(statement.head, outstanding)
    blocks = (_summary(statement, paths, as_of), _examined(records, statement, claims.project))
    return blocks if as_of is not None else (*blocks, *unconsidered_blocks(outstanding))


def write(ctx, *, chain: str, directory: Path, scope: str | None = None, as_of: str | None = None) -> Report:
    """The attended CLI's `--write`: replace the two files. Nothing is written to the world."""
    _asked(chain, scope, as_of)
    paths = statement_paths(_directory(str(directory), "write"), chain, scope)
    with kernel_reads():
        records = LiveRecords.capture(ctx, "reservation-assignment")
        statement = read_statement(records, chain, scope, as_of)
        project = selected_project(ctx)
    write_files(statement, paths)
    return (_summary(statement, paths, as_of),
            _examined(records, statement, None if project is None else ctx.selection.pinned(project.uid)))
