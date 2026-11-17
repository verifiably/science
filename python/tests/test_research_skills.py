"""Authored research skills retain their exact packaged content."""
import yaml

from science.loader import COMMANDS_ROOT, REPO_ROOT, production_tree


def test_discuss_is_packaged_byte_for_byte(tmp_path):
    from science.adapters import build_adapter
    build_adapter(production_tree(), COMMANDS_ROOT, REPO_ROOT / "skills", tmp_path)
    for name in ("SKILL.md", "discussion-structure.md"):
        source = REPO_ROOT / "skills" / "discuss" / name
        packaged = tmp_path / "skills" / "discuss" / name
        assert source.is_file() and packaged.is_file()
        assert source.read_bytes() == packaged.read_bytes()


def test_skill_frontmatter_names_match_directories():
    for path in (REPO_ROOT / "skills").glob("*/SKILL.md"):
        text = path.read_text()
        assert text.startswith("---\n")
        assert yaml.safe_load(text.split("---", 2)[1])["name"] == path.parent.name
