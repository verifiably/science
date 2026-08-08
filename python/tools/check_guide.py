"""Validate contributor-guide metadata and local Markdown links."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

import yaml

REQUIRED = frozenset({"title", "status", "created", "updated", "sources"})
LINK = re.compile(r"(?<!!)\[[^]]+]\(([^)]+)\)")
REFERENCE_LINK = re.compile(r"(?<!!)\[[^]]+]\[[^]]*]")
DEFAULT_GUIDE = Path(__file__).resolve().parents[2] / "docs" / "guide"


def check(root: Path) -> list[str]:
    if not root.is_dir():
        return [f"{root}: not a directory"]

    errors: list[str] = []
    for path in sorted(root.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        body = text
        metadata = None
        if not text.startswith("---\n"):
            errors.append(f"{path}: missing YAML front matter")
        else:
            parts = text.split("---", 2)
            if len(parts) != 3:
                errors.append(f"{path}: unterminated YAML front matter")
            else:
                body = parts[2]
                try:
                    metadata = yaml.safe_load(parts[1])
                except yaml.YAMLError as exc:
                    errors.append(f"{path}: malformed YAML front matter: {exc}")

        if metadata is not None and not isinstance(metadata, dict):
            errors.append(f"{path}: YAML front matter is not a mapping")
        elif isinstance(metadata, dict):
            missing = sorted(REQUIRED - metadata.keys())
            if missing:
                errors.append(f"{path}: missing metadata: {', '.join(missing)}")
            if "sources" in metadata:
                sources = metadata["sources"]
                if not isinstance(sources, list) or not sources:
                    errors.append(f"{path}: sources must be a non-empty list")
                else:
                    for source in sources:
                        if not isinstance(source, str) or not source or source.startswith("/"):
                            errors.append(f"{path}: source must be a relative path: {source!r}")
                        elif not (path.parent / source).exists():
                            errors.append(f"{path}: missing source: {source}")

        for raw in LINK.findall(body):
            target = raw.split()[0].strip("<>")
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            if parsed.path.startswith("/"):
                errors.append(f"{path}: absolute link is not allowed: {target}")
            elif not (path.parent / unquote(parsed.path)).exists():
                errors.append(f"{path}: missing link target: {target}")
        if REFERENCE_LINK.search(body):
            errors.append(f"{path}: reference-style links are unsupported")

    return errors


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    errors = check(Path(args[0]) if args else DEFAULT_GUIDE)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
