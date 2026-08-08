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
HEADING = re.compile(r"^#{1,6}\s+(.*?)\s*$", re.MULTILINE)
DEFAULT_GUIDE = Path(__file__).resolve().parents[2] / "docs" / "guide"


def heading_slugs(text: str) -> set[str]:
    """The anchors GitHub mints for a document's headings.

    Lowercase, drop everything that is not a word character, whitespace or a
    hyphen, then replace each space with a hyphen — *each*, not each run, which
    is why `## 6. M — the calculus` anchors as `6-m--the-calculus`.
    """
    slugs = set()
    for heading in HEADING.findall(text):
        stripped = re.sub(r"[`*_]", "", heading).lower()
        slugs.add(re.sub(r"[^\w\s-]", "", stripped).replace(" ", "-"))
    return slugs


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
            if parsed.scheme or parsed.netloc:
                continue
            if parsed.path.startswith("/"):
                errors.append(f"{path}: absolute link is not allowed: {target}")
                continue
            resolved = path if not parsed.path else path.parent / unquote(parsed.path)
            if not resolved.exists():
                errors.append(f"{path}: missing link target: {target}")
            elif parsed.fragment and resolved.suffix == ".md":
                # A section link that survives its section is the guide's most
                # likely rot: the file still resolves, so only the anchor tells.
                anchors = heading_slugs(resolved.read_text(encoding="utf-8"))
                if unquote(parsed.fragment) not in anchors:
                    errors.append(f"{path}: link resolves but its anchor does not: {target}")
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
