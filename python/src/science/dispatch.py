"""The dispatcher: the one path every invocation takes (spec §6.1, §7.3)."""
from __future__ import annotations

import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from science.canonical import canonicalize, input_digest
from science.cursor import ReadCursor, WriteCursor, decode, encode
from science.refusal import INVOCATION_ID_RE, Refusal, Refused, mint_token
from science.render import render_page, report_digest
from science.report import Report, serialize_block
from science.schema import Declaration


class HandlerContractViolation(RuntimeError):
    """A write handler raised a surface refusal after it had already acted.

    Validation precedes the first act (belief-path design §6.3). The acts
    committed are truth, so the invocation closes `done` with them; the
    refusal is not a refusal any more but a defect in the handler.
    """


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
        self._lock = threading.Lock()  # serializes write-class steps 4-7

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
            decl = None
            if cursor is None:
                decl = self._decls.get(command)
                if decl is None:
                    raise Refused(Refusal("unknown-command", f"no command {command!r}"))
            if not isinstance(inputs, Mapping):
                raise Refused(Refusal("invalid-input", "inputs must be a mapping"))
            if cursor is not None:
                return self._continue(command, inputs, decode(cursor), iid)
            assert decl is not None
            canonical = canonicalize(decl, inputs)
            if decl.write_class.kind != "read-only":
                return self._invoke_write(decl, canonical, iid)
            report = self._handlers[decl.name](self._ctx, **canonical)
            return Outcome(self._render(decl, canonical, report, (0, 0)), iid)
        except Refused as error:
            raise Refused(error.refusal, iid) from None

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
            return self._continue_write(command, cursor, iid)
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

    def _required(self, decl: Declaration):
        from beliefs.permit import RequiredCapabilities

        write_class = decl.write_class
        match write_class.kind:
            case "read-only":
                return RequiredCapabilities.none()
            case "coordination":
                return RequiredCapabilities.coordination()
            case "mints":
                return RequiredCapabilities.for_kinds(write_class.kinds, write_class.routes)
            case "publishes":
                # The publish act family arrives with sub-project 5 (spec
                # §4.1, §4.4); until then `RequiredCapabilities.publishes()`
                # raises rather than returning an uncoverable requirement, so
                # the class refuses here. `invoke` binds the invocation id.
                raise Refused(Refusal(
                    "permit-exceeded",
                    "publishes commands need the publish act family, "
                    "which arrives with sub-project 5",
                ))
        raise AssertionError(write_class.kind)

    @staticmethod
    def _kernel_refusal(error) -> Refusal:
        """The one normalization path for every kernel refusal shape."""
        from beliefs.permit import PermitExceeded
        from beliefs.session import KernelRefusalValue

        if isinstance(error, PermitExceeded):
            return Refusal(
                "permit-exceeded",
                str(error),
                {"requirement": str(error.requirement), "capability": str(error.capability)},
            )
        if isinstance(error, KernelRefusalValue):
            value = error.value
            return Refusal(
                "kernel-refused",
                str(value.reason),
                {"kind": type(value).__name__, "reason": str(value.reason)},
            )
        return Refusal("kernel-refused", str(error), {"kind": type(error).__name__})

    def _invoke_write(self, decl: Declaration, canonical: Mapping[str, object], iid: str) -> Outcome:
        from beliefs.errors import WriteRefused
        from beliefs.permit import PermitExceeded
        from beliefs.session import (
            ClaimDone,
            ClaimFresh,
            ClaimMismatch,
            ClaimOpen,
            KernelRefusalValue,
        )

        from science.render import audit_write_report

        # iid was minted at the top of `invoke`; every refusal here names it.
        if self._session is None:
            raise Refused(Refusal("permit-exceeded", "no writer session on this surface"), iid)
        # The requirement is computed before the session is touched: a write
        # class the framework cannot express refuses ahead of any session work.
        required = self._required(decl)
        try:
            writer = self._session.scoped(required, iid)
        except PermitExceeded as caught:
            raise Refused(self._kernel_refusal(caught), iid) from None
        with self._lock:
            claim = self._session.claim_invocation(iid, decl.name, input_digest(canonical))
            if isinstance(claim, ClaimDone):
                return Outcome(self._replay_outcome(decl, claim.outcome, iid, (0, 0)), iid)
            if isinstance(claim, ClaimOpen):
                raise Refused(
                    Refusal("outcome-unknown", "a prior attempt is open; its outcome is unknown"),
                    iid,
                )
            if isinstance(claim, ClaimMismatch):
                raise Refused(
                    Refusal("input-mismatch", "invocation_id was used with a different payload"),
                    iid,
                )
            if not isinstance(claim, ClaimFresh):  # fail closed, never execute
                raise TypeError(f"unknown claim type from the session: {claim!r}")
            try:
                report = self._handlers[decl.name](self._ctx, writer, **canonical)
            except (PermitExceeded, KernelRefusalValue, WriteRefused) as caught:
                return self._close_refused(iid, self._kernel_refusal(caught))
            except Refused as caught:
                acted = self._session.invocation_acts(iid)
                if not acted:
                    return self._close_refused(iid, caught.refusal)
                minted = frozenset(tuple(pair) for act in acted for pair in act.record_ids)
                self._session.close_invocation(
                    iid, {"done": [list(pair) for pair in sorted(minted)]}
                )
                raise HandlerContractViolation(
                    f"{decl.name} refused {caught.refusal.code!r} after {len(acted)} act(s); "
                    "a write handler validates before its first act"
                ) from caught
            minted = frozenset(
                tuple(pair)
                for act in self._session.invocation_acts(iid)
                for pair in act.record_ids
            )
            try:
                audit_write_report(report, minted)
            finally:
                # Close FIRST in every case: the ledger records act truth, and
                # the acts committed whether or not the report survives audit.
                # The ledger's outcome shape is `[uid, id]` lists, not tuples.
                self._session.close_invocation(
                    iid, {"done": [list(pair) for pair in sorted(minted)]}
                )
            # An AuditViolation has propagated past the close above as an
            # internal error; the echoed report is never rendered. Even on
            # success the handler's report is only the audited *claim* — what
            # renders is the canonical ledger-rebuilt report, first response
            # and replay alike, so authored text around a real identity pair
            # has no path out (spec §7.4).
            canonical_report = self._minted_report(sorted(minted))
            return Outcome(
                self._render_write(decl.output_budget, canonical_report, iid, (0, 0)), iid
            )

    def _close_refused(self, iid: str, refusal: Refusal) -> Outcome:
        from science.refusal import envelope

        self._session.close_invocation(iid, {"refusal": envelope(refusal)})
        raise Refused(refusal, iid)

    def _render_write(
        self, budget: int, report: Report, iid: str, position: tuple[int, int]
    ) -> str:
        def cursor_for(next_position: tuple[int, int], report_hash: str) -> str:
            return encode(
                WriteCursor(self._session.session_id, iid, report_hash, *next_position)
            )

        return render_page(
            report, budget=budget, position=position, cursor_for=cursor_for
        ).text

    def _minted_report(self, pairs) -> Report:
        """The canonical write report: record blocks rebuilt from ledger pairs."""
        from science.report import record_block

        return tuple(
            record_block(self._ctx.load_record(uid, record_id)) for uid, record_id in pairs
        )

    def _replay_outcome(
        self, decl: Declaration, outcome: Mapping[str, object], iid: str, position: tuple[int, int]
    ) -> str:
        if "refusal" in outcome:
            refusal = outcome["refusal"]
            raise Refused(
                Refusal(refusal["code"], refusal["message"], refusal.get("data", {})), iid
            )
        report = self._minted_report(outcome["done"])
        return self._render_write(decl.output_budget, report, iid, position)

    def _continue_write(self, command: str, cursor: WriteCursor, iid: str) -> Outcome:
        """Re-render from the ledger: never a handler call, never canonicalization."""
        from beliefs.session import open_ledger_reader

        decl = self._decls.get(command)
        if decl is None:
            raise Refused(Refusal("unknown-command", f"no command {command!r}"))
        operations_root = self._ctx.config.operations_root
        try:
            reader = open_ledger_reader(operations_root, cursor.session_id)
        except FileNotFoundError:
            raise Refused(Refusal("unknown-cursor", "no such session ledger")) from None
        record = reader.invocation(cursor.invocation_id)
        if record is None:
            raise Refused(Refusal("unknown-cursor", "no such invocation in that session"))
        if record.command != command:  # the cursor is bound to its command
            raise Refused(
                Refusal("input-mismatch", "cursor was issued for a different command")
            )
        if "refusal" in record.outcome:
            raise Refused(
                Refusal("unknown-cursor", "that invocation refused; nothing to page")
            )
        report = self._minted_report(record.outcome["done"])
        if report_digest(report) != cursor.report_digest:
            raise Refused(Refusal("stale-cursor", "the records changed; re-run"))
        self._check_position(report, cursor.block, cursor.offset)
        page = render_page(
            report,
            budget=decl.output_budget,
            position=(cursor.block, cursor.offset),
            cursor_for=lambda next_position, report_hash: encode(
                WriteCursor(
                    cursor.session_id, cursor.invocation_id, report_hash, *next_position
                )
            ),
        )
        return Outcome(page.text, iid)

    @staticmethod
    def _check_position(report: Report, block: int, offset: int) -> None:
        if block >= len(report):
            raise Refused(Refusal("stale-cursor", "cursor position is outside the report"))
        data = serialize_block(report[block]).encode()
        if offset >= len(data) or (data[offset] & 0xC0) == 0x80:
            raise Refused(Refusal("stale-cursor", "cursor position is not a boundary"))
