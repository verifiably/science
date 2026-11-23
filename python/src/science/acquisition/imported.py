"""Verify a converted log and hand its bytes and original journals to the scoped seal."""

from __future__ import annotations

import errno
import hashlib
import os
import tempfile
from pathlib import Path

from beliefs.durable import write_create_only
from beliefs.holdings.acquisition_log import log_tree, parse_acquisition_log, render_acquisition_log
from beliefs.holdings.records import require_store_relative_path
from beliefs.holdings.seal import LOG_NAME, SealRequest
from beliefs.identity import v1
from science.acquisition.journal import locked_directory, prepare_root, set_directory, sync_dir
from science.acquisition.seal import accept
from science.acquisition.staging import copy_regular, read_regular, stage_tree
from science.config import corpus_id_at
from science.refusal import Refusal, Refused

__all__ = ["import_log", "import_status"]


def _invalid(message):
    raise Refused(Refusal("invalid-input", message))


def _load(path):
    if path.is_symlink():
        _invalid(f"unexpected link in imported set at {path.name}")
    return v1.decode(path.read_bytes()) if path.exists() else None


def import_status(path):
    return _load(path / "import.json"), _load(path / "receipt.json")


def _binding(path, value):
    with tempfile.NamedTemporaryFile(dir=path, delete=False) as tmp:
        tmp.write(v1.encode(value))
        tmp.flush()
        os.fsync(tmp.fileno())
    os.replace(tmp.name, path / "binding.json")
    sync_dir(path)


def import_log(ctx, writer, file, members, originals, title, locator, partial):
    cfg = ctx.config
    policy = cfg.acquire
    raw = read_regular(file)
    log = parse_acquisition_log(raw)
    if log.header.origin != "imported" or render_acquisition_log(log) != raw:
        _invalid("import requires a canonical imported acquisition log")
    if len(log.lines) > policy.max_requests:
        _invalid("import exceeds max_requests")
    if not partial and any(line.result != "fetched" for line in log.lines):
        _invalid("incomplete import requires explicit partial acceptance")
    tree = log_tree(log)
    if any(m.size > policy.max_response_bytes for m in tree.members) or sum(m.size for m in tree.members) > policy.max_total_bytes:
        _invalid("imported member sizes exceed the acquisition bounds")
    metadata = dict(log="sha256:" + hashlib.sha256(raw).hexdigest(), title=title, locator=locator,
                    fetched=len(tree.members), failed=sum(r.result == "failed" for r in log.lines),
                    abandoned=sum(r.result == "abandoned" for r in log.lines), bytes=sum(m.size for m in tree.members))
    root = prepare_root(*cfg.acquisition_roots())
    path = root / log.header.set
    with tempfile.TemporaryDirectory(prefix=".import-", dir=root) as directory:
        private = Path(directory)

        def stage():
            copied, files = stage_tree(members, private, policy)
            if copied != tree:
                _invalid("member names, sizes or digests differ from the converted log")
            log_file = private / LOG_NAME
            log_file.write_bytes(raw)
            names = [name for name, _ in log.header.source_journals]
            if len(set(names)) != len(names) or LOG_NAME in names:
                _invalid("duplicate or reserved source journal name")
            # Each path is opened relative to the supplied journal directory.
            staged_originals = []
            for i, (name, digest) in enumerate(log.header.source_journals):
                require_store_relative_path(name)
                dest = private / f"source-{i}"
                with dest.open("xb") as output:
                    actual = copy_regular(originals / name, output)
                if actual != digest:
                    _invalid(f"source journal {name!r} differs from its declared digest")
                staged_originals.append((name, dest))
            return log_file, files, tuple(staged_originals)

        staged = None
        if not path.exists():
            staged = stage()
            log_file, files, journals = staged
            SealRequest(title, locator, "data", files, log_file, "imported", log.header.fetched_by, journals)
            new_set = private / "set"
            new_set.mkdir(mode=0o700)
            write_create_only(new_set / "import.json", v1.encode(metadata))
            try:
                new_set.rename(path)
            except OSError as exc:
                if exc.errno not in (errno.EEXIST, errno.ENOTEMPTY):
                    raise
            sync_dir(root)
        path = set_directory(cfg.operations_root, log.header.set)
        with locked_directory(path, "set-busy"):
            original_meta, receipt = import_status(path)
            if original_meta != metadata:
                _invalid("set token collision: different operation, log, title or locator")
            binding = _load(path / "binding.json")
            if receipt:
                if not binding or binding["corpus"] != corpus_id_at(cfg.write_root) or binding["store"] != writer.store_id:
                    _invalid("this set was bound to another destination")
                _invalid(f"already sealed as {receipt['dataset']} with {receipt['report']}; see acquire status")
            return accept(ctx, writer, log, title, locator, binding,
                          lambda value: _binding(path, value),
                          lambda value: write_create_only(path / "receipt.json", v1.encode(value)),
                          lambda: staged if staged is not None else stage())
