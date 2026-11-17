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


def test_research_topic_is_packaged_byte_for_byte(tmp_path):
    from science.adapters import build_adapter
    build_adapter(production_tree(), COMMANDS_ROOT, REPO_ROOT / "skills", tmp_path)
    for name in ("SKILL.md", "literature-evaluation.md"):
        source = REPO_ROOT / "skills" / "research-topic" / name
        packaged = tmp_path / "skills" / "research-topic" / name
        assert source.is_file() and packaged.is_file()
        assert source.read_bytes() == packaged.read_bytes()


def test_research_paper_is_packaged_byte_for_byte(tmp_path):
    from science.adapters import build_adapter
    build_adapter(production_tree(), COMMANDS_ROOT, REPO_ROOT / "skills", tmp_path)
    for name in ("SKILL.md", "literature-evaluation.md", "statement-extraction.md"):
        source = REPO_ROOT / "skills" / "research-paper" / name
        packaged = tmp_path / "skills" / "research-paper" / name
        assert source.is_file() and packaged.is_file()
        assert source.read_bytes() == packaged.read_bytes()


def test_shared_rule_files_are_byte_equal():
    root = REPO_ROOT / "skills"
    assert (root / "research-topic/literature-evaluation.md").read_bytes() == (
        root / "research-paper/literature-evaluation.md").read_bytes()


def test_no_skill_links_into_another_skill():
    import re
    for path in (REPO_ROOT / "skills").glob("*/*.md"):
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text()):
            assert not target.startswith("../") and "/../" not in target, (path, target)


def test_the_fixture_paper_states_one_identifier():
    import re
    from science.lookup import identifiers
    path = REPO_ROOT / "python/tests/fixtures/research/synthetic-paper.md"
    assert path.is_file()
    text = path.read_text()
    doi = re.search(r"^DOI: (\S+)$", text, re.MULTILINE).group(1)
    assert identifiers(doi=doi) == {"doi": "10.99999/synthetic.research-paper.1"}
    assert re.findall(r"10\.\d{4,9}/[^\s]+", text) == [doi]
    assert not re.search(r"\b(?:PMID|PMCID|ISBN|accession|GSE\d+|GSM\d+|SRR\d+|PRJNA\d+)\b", text, re.IGNORECASE)
