"""Bounded retrieval into the locked set. The kernel owns every network hop."""

from __future__ import annotations

import hashlib
import os
import re
import stat
import time
from datetime import UTC, datetime

from beliefs.holdings.transport import Failed, NotAttempted, RetrievalBounds, Retrieved, UrlSeam, retrieve, url_seam
from science.acquisition.journal import Journal, sync_dir
from science.refusal import Refusal, Refused

__all__ = ["retrieve_set", "verified_members"]


def _stamp():
    return datetime.now(UTC).isoformat()


def verified_members(journal: Journal):
    """Reopen and rehash committed objects before trusting any progress."""
    members = {}
    checked = {}
    for seq, request in enumerate(journal.requests, 1):
        if request.state != "fetched":
            continue
        path = journal.path / "objects" / request.digest.split(":")[1]
        if path not in checked:
            try:
                fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                with os.fdopen(fd, "rb") as inp:
                    info = os.fstat(inp.fileno())
                    if not stat.S_ISREG(info.st_mode):
                        raise ValueError("not a regular file")
                    checked[path] = (info.st_size, "sha256:" + hashlib.file_digest(inp, "sha256").hexdigest())
            except (OSError, ValueError) as exc:
                raise Refused(Refusal("invalid-input", f"request {seq} cannot verify object {request.digest}")) from exc
        if checked[path] != (request.size, request.digest):
            raise Refused(Refusal("invalid-input", f"request {seq} has corrupt object {request.digest}"))
        members[request.seed.name] = path
    return members


def _clean_uncommitted(journal, members):
    committed = set(members.values())
    for directory, pattern in (("objects", r"[0-9a-f]{64}"), ("scratch", r"retrieve-[0-9]{8}T[0-9]{12}-[0-9]+")):
        parent = journal.path / directory
        for entry in parent.iterdir():
            if entry not in committed and re.fullmatch(pattern, entry.name) and stat.S_ISREG(entry.lstat().st_mode):
                entry.unlink()


def _install(directory, result):
    destination = directory / result.digest.split(":")[1]
    with result.path.open("rb") as inp:
        os.fchmod(inp.fileno(), 0o400)
        os.fsync(inp.fileno())
    # Each new copy has just been read and hashed by the kernel.
    os.replace(result.path, destination)
    sync_dir(directory)


def retrieve_set(journal, *, seam=None, monotonic=time.monotonic, sleep=time.sleep, stamp=_stamp):
    """The start/resume caller holds both nonblocking directory locks."""
    members = verified_members(journal)
    _clean_uncommitted(journal, members)
    policy = journal.bounds
    transport = seam if seam is not None else url_seam()
    deadlines = {}
    answering_host = None

    def connect(approved, timeout):
        nonlocal answering_host
        host = approved.host
        remaining = deadlines.get(host, 0) - monotonic()
        if remaining > 0:
            sleep(remaining)
        interval = max(policy.min_interval_ms / 1000, float(journal.plan.intervals.get(host, 0)))
        deadlines[host] = monotonic() + interval
        answering_host = host
        return transport.connect(approved, timeout)

    paced = UrlSeam(transport.resolve, connect)
    total = sum(r.size for r in journal.requests if r.state == "fetched")
    for seq, prior in enumerate(journal.requests, 1):
        if prior.state == "abandoned":
            continue
        if prior.state == "failed":
            journal.append("budget-renewed", seq=seq)
        while (request := journal.requests[seq - 1]).state == "pending":
            journal.append("attempt-open", seq=seq, started_at=stamp())
            bound = min(policy.max_response_bytes, policy.max_total_bytes - total)
            result = retrieve(request.seed.url, RetrievalBounds(60, bound, 5), paced, journal.path / "scratch")
            close = {}
            retry_after = 0
            if isinstance(result, Retrieved):
                close["status"] = result.status
                close["headers"] = dict(result.headers)
                if request.seed.expected is not None and result.digest != request.seed.expected:
                    result.path.unlink()
                    close.update(outcome="failed", failure="expected-mismatch")
                else:
                    _install(journal.path / "objects", result)
                    close.update(outcome="fetched", digest=result.digest, size=result.size)
                    total += result.size
            elif isinstance(result, NotAttempted):
                close.update(outcome="not-attempted", failure=result.reason)
            elif isinstance(result, Failed):
                close.update(outcome="failed", failure=result.category)
                if result.status is not None:
                    close["status"] = result.status
                if result.refusal is not None:
                    close["redirect_refusal"] = result.refusal
                if result.retry_after is not None:
                    retry_after = result.retry_after
                    deadlines[answering_host] = max(deadlines[answering_host], monotonic() + retry_after)
            journal.append("attempt-close", seq=seq, completed_at=stamp(), **close)
            after = journal.requests[seq - 1]
            if after.state == "pending":
                # For a positive integral millisecond base, 2**16 already exceeds the cap.
                delay_ms = min(60_000, policy.backoff_ms * 2 ** min(after.failures - 1, 16))
                sleep(max(delay_ms / 1000, retry_after))
        if journal.requests[seq - 1].state == "fetched" and not journal.requests[seq - 1].expanded:
            journal.append("expanded", seq=seq)
