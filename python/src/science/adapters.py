"""Generate the Claude Code plugin from the command tree (spec §10)."""
from __future__ import annotations

import json
import stat
import shutil
from dataclasses import dataclass
from pathlib import Path

from science.loader import resolve_handlers
from science.schema import Declaration, DeclarationError

PLUGIN = {
    "name": "science",
    "description": "Science commands over a beliefs world.",
    "version": "0.1.0",
}
MCP = {"mcpServers": {"science": {"command": "science", "args": ["mcp", "serve"]}}}


@dataclass(frozen=True)
class _AuthoredSkill:
    name: str
    directories: tuple[Path, ...]
    files: tuple[tuple[Path, bytes], ...]


@dataclass(frozen=True)
class _BuildSources:
    declarations: tuple[Declaration, ...]
    preamble: str
    prompts: tuple[str, ...]
    authored: tuple[_AuthoredSkill, ...]


def _skill_md(decl: Declaration, preamble: str, prompt: str) -> str:
    frontmatter = (
        f"---\nname: {json.dumps(decl.name)}\n"
        f"description: {json.dumps(decl.purpose)}\n---\n\n"
    )
    return frontmatter + preamble.strip() + "\n\n" + prompt.strip() + "\n"


def _mode(path: Path, field_name: str, missing: str) -> int:
    try:
        return path.lstat().st_mode
    except FileNotFoundError:
        raise DeclarationError(path, field_name, missing) from None
    except OSError as error:
        raise DeclarationError(path, field_name, f"cannot inspect source: {error}") from error


def _real_directory(path: Path, field_name: str) -> None:
    mode = _mode(path, field_name, "missing directory")
    if stat.S_ISLNK(mode):
        raise DeclarationError(path, field_name, "symlink directories are not allowed")
    if not stat.S_ISDIR(mode):
        raise DeclarationError(path, field_name, "must be a real directory")


def _contained(path: Path, root: Path, field_name: str) -> None:
    try:
        path.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError):
        raise DeclarationError(path, field_name, f"source must be contained by {root}") from None


def _read_text(path: Path, root: Path, field_name: str) -> str:
    mode = _mode(path, field_name, "missing source")
    if stat.S_ISLNK(mode):
        raise DeclarationError(path, field_name, "symlink files are not allowed")
    if not stat.S_ISREG(mode):
        raise DeclarationError(path, field_name, "must be a regular file")
    _contained(path, root, field_name)
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise DeclarationError(path, field_name, f"cannot read source: {error}") from error


def _read_bytes(path: Path, root: Path) -> bytes:
    mode = _mode(path, "skill", "missing source")
    if stat.S_ISLNK(mode):
        raise DeclarationError(path, "skill", "symlink entries are not allowed")
    if not stat.S_ISREG(mode):
        raise DeclarationError(path, "skill", "must be a regular file")
    _contained(path, root, "skill")
    try:
        return path.read_bytes()
    except OSError as error:
        raise DeclarationError(path, "skill", f"cannot read source: {error}") from error


def _authored_skills(skills_root: Path, generated: set[str]) -> tuple[_AuthoredSkill, ...]:
    try:
        skills_mode = skills_root.lstat().st_mode
    except FileNotFoundError:
        return ()
    if stat.S_ISLNK(skills_mode) or not stat.S_ISDIR(skills_mode):
        raise DeclarationError(skills_root, "skill", "skills root must be a real directory")
    authored = []
    for path in sorted(skills_root.iterdir()):
        if path.name == ".gitkeep":
            _read_bytes(path, skills_root)
            continue
        _real_directory(path, "skill")
        _contained(path, skills_root, "skill")
        if path.name in generated:
            raise DeclarationError(path, "skill", "collides with a generated command skill")
        directories = []
        files = []
        for source in sorted(path.rglob("*")):
            mode = _mode(source, "skill", "missing source")
            if stat.S_ISLNK(mode):
                raise DeclarationError(source, "skill", "symlink entries are not allowed")
            relative = source.relative_to(path)
            if stat.S_ISDIR(mode):
                _contained(source, skills_root, "skill")
                directories.append(relative)
            elif stat.S_ISREG(mode):
                files.append((relative, _read_bytes(source, skills_root)))
            else:
                raise DeclarationError(
                    source, "skill", "only directories and regular files are allowed"
                )
        authored.append(_AuthoredSkill(path.name, tuple(directories), tuple(files)))
    return tuple(authored)


def preflight_build(decls, commands_root: Path, skills_root: Path) -> _BuildSources:
    declarations = tuple(decls)
    resolve_handlers(declarations)
    _real_directory(commands_root, "commands")
    preamble = _read_text(commands_root / "PREAMBLE.md", commands_root, "preamble")
    prompts = []
    for declaration in declarations:
        _real_directory(declaration.directory, "directory")
        _contained(declaration.directory, commands_root, "directory")
        _read_text(
            declaration.directory / "command.toml", commands_root, "command.toml"
        )
        prompts.append(
            _read_text(declaration.directory / "prompt.md", commands_root, "prompt.md")
        )
    authored = _authored_skills(
        skills_root, {declaration.name for declaration in declarations}
    )
    return _BuildSources(declarations, preamble, tuple(prompts), authored)


def build_adapter(decls, commands_root: Path, skills_root: Path, out: Path) -> None:
    sources = preflight_build(decls, commands_root, skills_root)
    if out.exists():
        shutil.rmtree(out)
    (out / ".claude-plugin").mkdir(parents=True)
    (out / ".claude-plugin" / "plugin.json").write_text(json.dumps(PLUGIN, indent=2) + "\n")
    (out / ".mcp.json").write_text(json.dumps(MCP, indent=2) + "\n")
    for decl, prompt in zip(sources.declarations, sources.prompts, strict=True):
        skill_dir = out / "skills" / decl.name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            _skill_md(decl, sources.preamble, prompt), encoding="utf-8"
        )
    for skill in sources.authored:
        skill_dir = out / "skills" / skill.name
        skill_dir.mkdir(parents=True)
        for directory in skill.directories:
            (skill_dir / directory).mkdir(parents=True)
        for relative, content in skill.files:
            destination = skill_dir / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
