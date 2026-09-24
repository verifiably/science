import pytest

from science.refusal import Refused


def _refused(call, code="invalid-input"):
    with pytest.raises(Refused) as caught:
        call()
    assert caught.value.refusal.code == code
    return caught.value.refusal


@pytest.mark.parametrize("text", [
    "version: science.view-query.v1\nclauses: []\n",
    '{"version": "science.view-query.v1", "clauses": []}',
])
def test_query_text_parses_yaml_or_json_to_a_mapping(text):
    from science.coordination import parse_query_text
    assert parse_query_text(text) == {"version": "science.view-query.v1", "clauses": []}


@pytest.mark.parametrize("text", ["- a\n", "3", "", "{unclosed"])
def test_query_text_that_is_not_a_mapping_refuses(text):
    from science.coordination import parse_query_text
    _refused(lambda: parse_query_text(text))


def test_addresses_parse_by_shape():
    from science.coordination import parse_address
    project, local = "a" * 32, "b" * 32
    assert str(parse_address(f"coord:{project}", subordinate=False)) == f"coord:{project}"
    assert str(parse_address(f"coord:{project}/{local}", subordinate=True)) == f"coord:{project}/{local}"
    _refused(lambda: parse_address(f"coord:{project}", subordinate=True))
    _refused(lambda: parse_address(f"coord:{project}/{local}@{'c' * 32}", subordinate=True))
    _refused(lambda: parse_address("health", subordinate=False))


def test_current_project_refuses_without_a_selection(certified_work):
    from helpers.world import build_fixture_world
    from science.config import ReadContext
    refusal = _refused(lambda: ReadContext.open(build_fixture_world(certified_work)).current_project(),
                       code="no-current-project")
    assert "project-select" in refusal.message and "reuse" in refusal.message
