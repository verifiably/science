"""Generate the Claude Code plugin from the command tree (spec §10)."""
from __future__ import annotations

import json
import stat
import shutil
from pathlib import Path

from science.schema import Declaration, DeclarationError

PLUGIN = {
    "name": "science",
    "description": "Science commands over a beliefs world.",
    "version": "0.1.0",
}
MCP = {"mcpServers": {"science": {"command": "science", "args": ["mcp", "serve"]}}}


def _skill_md(decl: Declaration, preamble: str, prompt: str) -> str:
    frontmatter = (
        f"---\nname: {json.dumps(decl.name)}\n"
        f"description: {json.dumps(decl.purpose)}\n---\n\n"
    )
    return frontmatter + preamble.strip() + "\n\n" + prompt.strip() + "\n"


def _authored_skills(skills_root: Path, generated: set[str]) -> tuple[Path, ...]:
    if not skills_root.exists():
        return ()
    if skills_root.is_symlink() or not skills_root.is_dir():
        raise DeclarationError(skills_root, "skill", "skills root must be a real directory")
    authored = []
    for path in sorted(skills_root.iterdir()):
        if path.name == ".gitkeep" and path.is_file() and not path.is_symlink():
            continue
        if path.is_symlink() or not path.is_dir():
            raise DeclarationError(path, "skill", "authored skill entries must be real directories")
        if path.name in generated:
            raise DeclarationError(path, "skill", "collides with a generated command skill")
        _validate_skill_tree(path)
        authored.append(path)
    return tuple(authored)


def _validate_skill_tree(path: Path) -> None:
    mode = path.lstat().st_mode
    if stat.S_ISLNK(mode):
        raise DeclarationError(path, "skill", "symlink entries are not allowed")
    if stat.S_ISREG(mode):
        return
    if not stat.S_ISDIR(mode):
        raise DeclarationError(path, "skill", "only directories and regular files are allowed")
    for child in path.iterdir():
        _validate_skill_tree(child)


def build_adapter(decls, commands_root: Path, skills_root: Path, out: Path) -> None:
    declarations = tuple(decls)
    authored = _authored_skills(skills_root, {decl.name for decl in declarations})
    if out.exists():
        shutil.rmtree(out)
    (out / ".claude-plugin").mkdir(parents=True)
    (out / ".claude-plugin" / "plugin.json").write_text(json.dumps(PLUGIN, indent=2) + "\n")
    (out / ".mcp.json").write_text(json.dumps(MCP, indent=2) + "\n")
    preamble = (commands_root / "PREAMBLE.md").read_text()
    for decl in declarations:
        prompt = (decl.directory / "prompt.md").read_text()
        skill_dir = out / "skills" / decl.name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(_skill_md(decl, preamble, prompt))
    for skill in authored:
        shutil.copytree(skill, out / "skills" / skill.name)
