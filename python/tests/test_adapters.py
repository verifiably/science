import json
from dataclasses import replace
from pathlib import Path

import pytest

from science.loader import COMMANDS_ROOT, REPO_ROOT, production_tree
from science.schema import DeclarationError


def _tree_files(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_generated_tree_matches_committed(tmp_path):
    from science.adapters import build_adapter

    build_adapter(production_tree(), COMMANDS_ROOT, REPO_ROOT / "skills", tmp_path)
    assert _tree_files(tmp_path) == _tree_files(REPO_ROOT / "adapters" / "claude-code")


def test_skill_carries_preamble_and_prompt(tmp_path):
    from science.adapters import build_adapter

    build_adapter(production_tree(), COMMANDS_ROOT, REPO_ROOT / "skills", tmp_path)
    skill = (tmp_path / "skills" / "status" / "SKILL.md").read_text()
    assert "one world" in skill
    assert "Run `status`" in skill
    assert skill.startswith("---\n")


def test_mcp_json_has_no_machine_paths(tmp_path):
    from science.adapters import build_adapter

    build_adapter(production_tree(), COMMANDS_ROOT, REPO_ROOT / "skills", tmp_path)
    server = json.loads((tmp_path / ".mcp.json").read_text())["mcpServers"]["science"]
    assert server == {"command": "science", "args": ["mcp", "serve"]}
    assert "/home/" not in json.dumps(server) and "/mnt/" not in json.dumps(server)


def test_authored_skill_collision_refuses(tmp_path):
    from science.adapters import build_adapter

    skills = tmp_path / "authored"
    (skills / "status").mkdir(parents=True)
    with pytest.raises(DeclarationError, match="collides with a generated command skill"):
        build_adapter(production_tree(), COMMANDS_ROOT, skills, tmp_path / "out")


def test_collision_refusal_preserves_existing_output(tmp_path):
    from science.adapters import build_adapter

    skills = tmp_path / "authored"
    (skills / "status").mkdir(parents=True)
    out = tmp_path / "out"
    out.mkdir()
    sentinel = out / "sentinel"
    sentinel.write_text("keep")

    with pytest.raises(DeclarationError, match="collides with a generated command skill"):
        build_adapter(production_tree(), COMMANDS_ROOT, skills, out)

    assert sentinel.read_text() == "keep"


def test_authored_skill_symlink_refusal_preserves_existing_output(tmp_path):
    from science.adapters import build_adapter

    skills = tmp_path / "authored"
    skill = skills / "extra"
    skill.mkdir(parents=True)
    target = tmp_path / "outside"
    target.write_text("outside")
    (skill / "linked").symlink_to(target)
    out = tmp_path / "out"
    out.mkdir()
    sentinel = out / "sentinel"
    sentinel.write_text("keep")

    with pytest.raises(DeclarationError, match="symlink"):
        build_adapter(production_tree(), COMMANDS_ROOT, skills, out)

    assert sentinel.read_text() == "keep"


def _existing_output(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    sentinel = out / "sentinel"
    sentinel.write_text("keep")
    return out, sentinel


def test_preamble_symlink_refusal_preserves_existing_output(tmp_path):
    import shutil

    from science.adapters import build_adapter

    commands = tmp_path / "commands"
    shutil.copytree(COMMANDS_ROOT, commands)
    preamble = commands / "PREAMBLE.md"
    target = tmp_path / "outside-preamble"
    preamble.replace(target)
    preamble.symlink_to(target)
    declarations = tuple(
        replace(declaration, directory=commands / declaration.name)
        for declaration in production_tree()
    )
    out, sentinel = _existing_output(tmp_path)

    with pytest.raises(DeclarationError, match="symlink"):
        build_adapter(declarations, commands, REPO_ROOT / "skills", out)

    assert sentinel.read_text() == "keep"


def test_handler_validation_precedes_output_mutation(tmp_path):
    from science.adapters import build_adapter

    declaration = replace(production_tree()[0], name="missing-handler-module")
    out, sentinel = _existing_output(tmp_path)

    with pytest.raises(DeclarationError, match="cannot import"):
        build_adapter((declaration,), COMMANDS_ROOT, REPO_ROOT / "skills", out)

    assert sentinel.read_text() == "keep"


def test_command_source_must_be_contained_by_commands_root(tmp_path):
    import shutil

    from science.adapters import build_adapter

    outside = tmp_path / "outside" / "status"
    shutil.copytree(COMMANDS_ROOT / "status", outside)
    declaration = replace(production_tree()[0], directory=outside)
    out, sentinel = _existing_output(tmp_path)

    with pytest.raises(DeclarationError, match="contained"):
        build_adapter((declaration,), COMMANDS_ROOT, REPO_ROOT / "skills", out)

    assert sentinel.read_text() == "keep"


def test_missing_prompt_refusal_preserves_existing_output(tmp_path):
    import shutil

    from science.adapters import build_adapter

    commands = tmp_path / "commands"
    shutil.copytree(COMMANDS_ROOT, commands)
    declarations = tuple(
        replace(declaration, directory=commands / declaration.name)
        for declaration in production_tree()
    )
    (commands / "status" / "prompt.md").unlink()
    out, sentinel = _existing_output(tmp_path)

    with pytest.raises(DeclarationError, match="prompt"):
        build_adapter(declarations, commands, REPO_ROOT / "skills", out)

    assert sentinel.read_text() == "keep"
