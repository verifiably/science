"""The dispatcher: the one path every invocation takes (spec §6.1, §7.3)."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from science.canonical import canonicalize, input_digest
from science.cursor import ReadCursor, WriteCursor, decode, encode
from science.refusal import INVOCATION_ID_RE, Refusal, Refused, mint_token
from science.render import render_page, report_digest
from science.report import Report, serialize_block
from science.schema import Declaration


@dataclass(frozen=True)
class Outcome:
    text: str
    invocation_id: str


class Dispatcher:
    def __init__(self, declarations, handlers: Mapping[str, Callable], read_context, session=None) -> None:
        self._decls = {decl.name: decl for decl in declarations}
        self._handlers = dict(handlers)
        self._ctx = read_context
        self._session = session

    def invoke(
        self,
        command: str,
        inputs: Mapping[str, object],
        *,
        invocation_id: str | None = None,
        cursor: str | None = None,
    ) -> Outcome:
        valid_iid = type(invocation_id) is str and INVOCATION_ID_RE.fullmatch(invocation_id) is not None
        iid = invocation_id if valid_iid else mint_token()
        try:
            if invocation_id is not None and not valid_iid:
                raise Refused(Refusal("invalid-input", "invocation_id outside its grammar"))
            if type(command) is not str:
                raise Refused(Refusal("invalid-input", "command must be a string"))
            if not isinstance(inputs, Mapping):
                raise Refused(Refusal("invalid-input", "inputs must be a mapping"))
            if cursor is not None:
                return self._continue(command, inputs, decode(cursor), iid)
            decl = self._decls.get(command)
            if decl is None:
                raise Refused(Refusal("unknown-command", f"no command {command!r}"))
            canonical = canonicalize(decl, inputs)
            if decl.write_class.kind != "read-only":
                raise NotImplementedError("write dispatch lands with the beliefs session API")
            report = self._handlers[decl.name](self._ctx, **canonical)
            return Outcome(self._render(decl, canonical, report, (0, 0)), iid)
        except Refused as error:
            if error.invocation_id is None:
                raise Refused(error.refusal, iid) from None
            raise

    def _render(
        self,
        decl: Declaration,
        canonical: Mapping[str, object],
        report: Report,
        position: tuple[int, int],
    ) -> str:
        digest = input_digest(canonical)

        def cursor_for(next_position: tuple[int, int], report_hash: str) -> str:
            return encode(ReadCursor(decl.name, digest, report_hash, *next_position))

        return render_page(
            report,
            budget=decl.output_budget,
            position=position,
            cursor_for=cursor_for,
        ).text

    def _continue(
        self,
        command: str,
        inputs: Mapping[str, object],
        cursor: ReadCursor | WriteCursor,
        iid: str,
    ) -> Outcome:
        if isinstance(cursor, WriteCursor):
            raise NotImplementedError("write continuation lands with the beliefs session API")
        decl = self._decls.get(cursor.command)
        if decl is None:
            raise Refused(Refusal("unknown-cursor", f"cursor names unknown command {cursor.command!r}"))
        if command != cursor.command:
            raise Refused(Refusal("input-mismatch", "cursor was issued for a different command"))
        canonical = canonicalize(decl, inputs)
        if input_digest(canonical) != cursor.input_digest:
            raise Refused(Refusal("input-mismatch", "cursor was issued for different inputs"))
        report = self._handlers[decl.name](self._ctx, **canonical)
        if report_digest(report) != cursor.report_digest:
            raise Refused(Refusal("stale-cursor", "the world moved; re-run the command"))
        self._check_position(report, cursor.block, cursor.offset)
        return Outcome(self._render(decl, canonical, report, (cursor.block, cursor.offset)), iid)

    @staticmethod
    def _check_position(report: Report, block: int, offset: int) -> None:
        if block >= len(report):
            raise Refused(Refusal("stale-cursor", "cursor position is outside the report"))
        data = serialize_block(report[block]).encode()
        if offset >= len(data) or (data[offset] & 0xC0) == 0x80:
            raise Refused(Refusal("stale-cursor", "cursor position is not a boundary"))
