"""run-output: read one declared output of a run after verifying its manifest digest."""
from __future__ import annotations

import errno
import os
import stat
from hashlib import sha256
from pathlib import Path, PurePosixPath

from beliefs import stored
from beliefs.errors import ScienceError
from beliefs.runrecord import decode_run_closure

from science.lookup import world_record
from science.refusal import Refusal, Refused, kernel_refusal
from science.report import KeyVals, Report, Text

_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC


def _unavailable(message: str, *, run_ref: str, output: str, digest: str, reason: str, **extra: object):
    raise Refused(Refusal(
        "read-unavailable",
        message,
        {"run": run_ref, "output": output, "digest": digest, "reason": reason, **extra},
    ))


def _scratch_parts(
    scratch_mapping: str,
    operations_root: Path,
    output: str,
    *,
    confined: bool,
    run_ref: str,
    digest: str,
) -> tuple[Path, tuple[str, ...]]:
    allowed_resolved = (operations_root / "scratch").resolve()
    allowed_raw = Path(os.path.abspath(operations_root / "scratch"))
    mapping = Path(scratch_mapping)
    if not mapping.is_absolute() or ".." in mapping.parts:
        _unavailable(
            f"{run_ref}: scratch location {scratch_mapping!r} lies outside operations scratch",
            run_ref=run_ref, output=output, digest=digest, reason="scratch-outside-operations-root",
        )
    rel_scratch: Path | None = None
    for anchor in (allowed_resolved, allowed_raw):
        if mapping.is_relative_to(anchor):
            rel_scratch = mapping.relative_to(anchor)
            break
    if rel_scratch is None or not rel_scratch.parts or any(p in ("", ".", "..") for p in rel_scratch.parts):
        _unavailable(
            f"{run_ref}: scratch location {scratch_mapping!r} lies outside operations scratch",
            run_ref=run_ref, output=output, digest=digest, reason="scratch-outside-operations-root",
        )
    if "\\" in output or output.startswith("/"):
        _unavailable(
            f"{run_ref}: declared output path {output!r} is not a relative path",
            run_ref=run_ref, output=output, digest=digest, reason="invalid-output-path",
        )
    out_parts = PurePosixPath(output).parts
    if not out_parts or any(p in ("", ".", "..") for p in out_parts):
        _unavailable(
            f"{run_ref}: declared output path {output!r} is not a relative path",
            run_ref=run_ref, output=output, digest=digest, reason="invalid-output-path",
        )
    middle = ("out",) if confined else ()
    return allowed_resolved, (*rel_scratch.parts, *middle, *out_parts)


def _read_confined_bytes(base: Path, parts: tuple[str, ...], *, run_ref: str, output: str, digest: str) -> bytes:
    opened: list[int] = []
    try:
        try:
            fd = os.open(base, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        except OSError as caught:
            _unavailable(
                f"{run_ref}: operations scratch is unavailable for {output!r}",
                run_ref=run_ref, output=output, digest=digest, reason="scratch-missing",
            )
            raise AssertionError from caught
        opened.append(fd)
        for segment in parts[:-1]:
            try:
                fd = os.open(segment, _DIR_FLAGS, dir_fd=fd)
            except OSError as caught:
                if caught.errno == errno.ENOENT:
                    _unavailable(
                        f"{run_ref}: output {output!r} is not present in operations scratch",
                        run_ref=run_ref, output=output, digest=digest, reason="scratch-missing",
                    )
                _unavailable(
                    f"{run_ref}: output {output!r} path in operations scratch is not a confined directory",
                    run_ref=run_ref, output=output, digest=digest, reason="scratch-unconfined",
                )
            opened.append(fd)
        try:
            final_fd = os.open(parts[-1], _FILE_FLAGS, dir_fd=fd)
        except OSError as caught:
            if caught.errno == errno.ENOENT:
                _unavailable(
                    f"{run_ref}: output {output!r} is not present in operations scratch",
                    run_ref=run_ref, output=output, digest=digest, reason="scratch-missing",
                )
            _unavailable(
                f"{run_ref}: output {output!r} in operations scratch is not a confined regular file",
                run_ref=run_ref, output=output, digest=digest, reason="scratch-unconfined",
            )
        opened.append(final_fd)
        info = os.fstat(final_fd)
        if not stat.S_ISREG(info.st_mode):
            _unavailable(
                f"{run_ref}: output {output!r} in operations scratch is not a regular file",
                run_ref=run_ref, output=output, digest=digest, reason="scratch-unconfined",
            )
        # Hand ownership of final_fd to fdopen by popping it from opened.
        opened.pop()
        with os.fdopen(final_fd, "rb") as stream:
            return stream.read()
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)


def handle(ctx, *, run, output) -> Report:
    located = world_record(ctx, run)
    if located is None:
        raise Refused(Refusal("invalid-input", f"{run} names no record in the configured corpora", {"run": run}))
    node = located.node
    if node.kind != "run":
        raise Refused(Refusal(
            "invalid-input",
            f"{located.address} is a {node.kind}, not a run",
            {"run": located.address, "kind": node.kind},
        ))
    if stored.RUN_CLOSURE_FACET not in node.facets:
        raise Refused(Refusal(
            "invalid-input",
            f"{located.address} carries no run-closure projection",
            {"run": located.address},
        ))
    try:
        closure = decode_run_closure(node)
    except ScienceError as caught:
        raise Refused(kernel_refusal(caught)) from caught

    outputs = dict(closure.result.outputs)
    if output not in outputs:
        raise Refused(Refusal(
            "invalid-input",
            f"{located.address} declares no output {output!r}",
            {"run": located.address, "output": output, "available": sorted(outputs)},
        ))
    expected_digest = outputs[output]
    execution = closure.occurrence.receipt.execution
    base, parts = _scratch_parts(
        execution.scratch_mapping,
        ctx.config.operations_root,
        output,
        confined=execution.instance is not None,
        run_ref=located.address,
        digest=expected_digest,
    )
    data = _read_confined_bytes(base, parts, run_ref=located.address, output=output, digest=expected_digest)
    actual_digest = "sha256:" + sha256(data).hexdigest()
    if actual_digest != expected_digest:
        _unavailable(
            f"{located.address}: output {output!r} digest {actual_digest} does not match manifest {expected_digest}",
            run_ref=located.address,
            output=output,
            digest=expected_digest,
            reason="digest-mismatch",
            actual=actual_digest,
        )
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as caught:
        raise Refused(Refusal(
            "invalid-input",
            f"{located.address}: output {output!r} is not valid UTF-8 text",
            {"run": located.address, "output": output, "digest": expected_digest, "reason": "non-utf8"},
        )) from caught

    return (
        KeyVals(
            "run output",
            (
                ("run", located.address),
                ("output", output),
                ("digest", expected_digest),
                ("bytes", str(len(data))),
            ),
        ),
        Text(text.removesuffix("\n")),
    )
