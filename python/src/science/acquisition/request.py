"""Fold one static request's journal entries into its retry and log evidence."""

from __future__ import annotations

from dataclasses import dataclass, replace

from beliefs.holdings.acquisition_log import Attempt, RequestLine
from beliefs.holdings.acquire import ResourceRequest
from beliefs.holdings.transport import REFUSAL_CATEGORIES

__all__ = ["RequestState"]


@dataclass(frozen=True)
class RequestState:
    seed: ResourceRequest
    state: str = "pending"
    attempts: tuple[Attempt, ...] = ()
    opened: str | None = None
    failures: int = 0
    digest: str | None = None
    size: int | None = None
    expanded: bool = False

    def history(self) -> tuple[Attempt, ...]:
        if self.opened is None:
            return self.attempts
        return (*self.attempts, Attempt(self.opened, None, "interrupted", None, (), None))

    def line(self, seq: int) -> RequestLine:
        return RequestLine(seq, self.seed.url.url, None, self.seed.expected, self.history(), self.state,
                           self.digest, self.size, self.seed.name if self.state == "fetched" else None, None)

    def transition(self, event: str, payload: dict, limit: int) -> RequestState:
        if event == "budget-renewed" and self.state == "failed" and not payload:
            return replace(self, state="pending", failures=0)
        if event == "expanded" and self.state == "fetched" and not self.expanded and not payload:
            return replace(self, expanded=True)
        if self.state != "pending":
            raise ValueError(f"{event} is invalid while {self.state}")
        if event == "attempt-open" and payload.keys() == {"started_at"}:
            start = payload["started_at"]
            if not isinstance(start, str) or not start:
                raise ValueError("attempt-open needs a start time")
            return replace(self, attempts=self.history(), opened=start)
        if event == "abandoned" and not payload:
            return replace(self, state="abandoned", attempts=self.history(), opened=None)
        if event != "attempt-close" or self.opened is None:
            raise ValueError(f"unexpected {event} or no matching attempt-open")
        outcome = payload["outcome"]
        required = {"completed_at", "outcome"} | ({"digest", "size"} if outcome == "fetched" else {"failure"})
        fields = payload.keys()
        if (not required <= fields or fields - required - {"headers", "status", "redirect_refusal"}
                or outcome not in {"fetched", "failed", "not-attempted"}):
            raise ValueError("invalid attempt-close fields")
        closed = payload["completed_at"]
        headers = payload.get("headers", {})
        if not isinstance(closed, str) or not closed or not isinstance(headers, dict):
            raise ValueError("invalid attempt close time or headers")
        failure = payload.get("failure")
        redirect = payload.get("redirect_refusal")
        if failure == "redirect-refused":
            if redirect not in REFUSAL_CATEGORIES:
                raise ValueError("missing redirect refusal category")
        elif "redirect_refusal" in payload:
            raise ValueError("unexpected redirect refusal")
        attempt = Attempt(self.opened, closed, outcome, payload.get("status"), tuple(sorted(headers.items())), failure)
        result = replace(self, attempts=(*self.attempts, attempt), opened=None)
        if outcome == "fetched":
            result = replace(result, state="fetched", digest=payload["digest"], size=payload["size"])
            result.line(1)  # validate held fields using the kernel log contract
            if self.seed.expected and result.digest != self.seed.expected:
                raise ValueError("fetched digest differs from expected")
            return result
        deterministic = (outcome == "not-attempted" and failure != "unresolvable"
                         or failure == "redirect-refused" and redirect != "unresolvable")
        failures = self.failures + 1
        return replace(result, failures=failures, state="failed" if deterministic or failures >= limit else "pending")
