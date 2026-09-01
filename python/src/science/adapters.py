"""Generate the Claude Code plugin from the command tree (spec §10)."""
from __future__ import annotations

import json
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


def build_adapter(decls, commands_root: Path, skills_root: Path, out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    (out / ".claude-plugin").mkdir(parents=True)
    (out / ".claude-plugin" / "plugin.json").write_text(json.dumps(PLUGIN, indent=2) + "\n")
    (out / ".mcp.json").write_text(json.dumps(MCP, indent=2) + "\n")
    preamble = (commands_root / "PREAMBLE.md").read_text()
    generated = set()
    for decl in decls:
        prompt = (decl.directory / "prompt.md").read_text()
        skill_dir = out / "skills" / decl.name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(_skill_md(decl, preamble, prompt))
        generated.add(decl.name)
    if skills_root.is_dir():
        for authored in sorted(path for path in skills_root.iterdir() if path.is_dir()):
            if authored.name in generated:
                raise DeclarationError(authored, "skill", "collides with a generated command skill")
            shutil.copytree(authored, out / "skills" / authored.name)
