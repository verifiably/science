"""Job-only client of the supervisor's synchronous allowance.v1 channel."""
import json
import socket
import threading
from contextlib import contextmanager

from science.refusal import Refusal, Refused

__all__ = ["JobAdmission", "JOB_CODES"]

JOB_CODES = frozenset({"allowance-scope", "allowance-exhausted", "allowance-expired", "allowance-closed",
                       "allowance-unavailable"})
_UNITS = {"attempts", "input_tokens", "output_tokens", "micro_usd", "job_starts"}
_LIMIT = 16384


def _closed(pairs):
    obj = dict(pairs)
    if len(obj) != len(pairs):
        raise ValueError("duplicate allowance field")
    return obj


class JobAdmission:
    def __init__(self, stream):
        if stream.family != socket.AF_UNIX or stream.getsockopt(socket.SOL_SOCKET, socket.SO_TYPE) != socket.SOCK_SEQPACKET:
            raise ValueError("job admissions require a Unix sequenced-packet peer")
        self.stream = stream
        self.stream.settimeout(2)
        self.sequence = 0
        self.lock = threading.Lock()

    def reserve(self, invocation, phase):
        self._call("reserve-job", {"invocation_id": invocation, "phase": phase})

    def settle(self, invocation, phase, status, ledger_ref):
        self._call("settle-job", {"invocation_id": invocation, "phase": phase, "status": status,
                                  "ledger_ref": ledger_ref})

    @contextmanager
    def execution(self, session, iid, phase):
        from beliefs.errors import SessionSealed
        from beliefs.session import KernelRefusalValue
        self.reserve(iid, phase)
        status = "unknown"
        try:
            session.govern_job(iid, phase)
            yield
            status = "completed"
        except SessionSealed:
            if any(ref.startswith("run:") for act in session.invocation_acts(iid) for _, ref in act.record_ids):
                # Replay already committed before the subsequent verification mint was cut.
                status = "completed"
            raise
        except KernelRefusalValue as caught:
            reason = caught.value.reason
            status = reason if reason in ("run-cancelled", "execution-failed") else "refused"
            raise
        finally:
            terminal = [act for act in session.invocation_acts(iid) if any(
                ref.startswith(("run:", "act-report:")) for _, ref in act.record_ids)]
            reference = None
            if len(terminal) == 1 and status != "unknown":
                reference = {"session_id": session.session_id, "invocation_id": iid, "entry": terminal[0].entry}
            self.settle(iid, phase, status if reference else "unknown", reference)

    def _call(self, op, args):
        with self.lock:
            try:
                self.sequence += 1
                request = {"version": "allowance.v1", "id": self.sequence, "op": op, "args": args}
                packet = json.dumps(request, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
                if len(packet) > _LIMIT or self.stream.send(packet) != len(packet):
                    raise ValueError("incomplete job request")
                data, _, flags, _ = self.stream.recvmsg(_LIMIT)
                if flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC):
                    raise ValueError("oversized job reply")
                value = json.loads(data.decode("utf-8"), object_pairs_hook=_closed)
                if not isinstance(value, dict) or value.pop("version", None) != "allowance.v1":
                    raise ValueError("invalid version")
                correlation = value.pop("id", None)
                if type(correlation) is not int or correlation != self.sequence:
                    raise ValueError("unmatched reply")
                if value == {"result": "admitted" if op == "reserve-job" else "settled"}:
                    return
                if (op == "reserve-job" and set(value) == {"result", "state"} and
                        value["result"] == "already-recorded" and value["state"] in ("reserved", "settled")):
                    raise Refused(Refusal("allowance-scope", "The job was already admitted"))
                if value.pop("result", None) != "refused":
                    raise ValueError("invalid result")
                code = value.pop("code")
                if code not in JOB_CODES or set(value) - {"remaining", "dimension"}:
                    raise ValueError("invalid refusal")
                if ("dimension" in value) != (code == "allowance-exhausted") or (
                        "dimension" in value and value["dimension"] not in _UNITS):
                    raise ValueError("invalid refusal dimension")
                if "remaining" in value:
                    units = value["remaining"]
                    if type(units) is not dict or units.keys() != _UNITS or any(
                            type(n) is not int or n < 0 for n in units.values()):
                        raise ValueError("invalid remaining units")
                raise Refused(Refusal(code, "The host refused job admission or settlement", value))
            except (OSError, ValueError, TypeError, KeyError, RecursionError) as error:
                raise Refused(Refusal("allowance-unavailable", "Unusable host admission reply")) from error
