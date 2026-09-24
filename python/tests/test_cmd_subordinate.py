import pytest

from helpers.synthetic import MINT_CLAIM, mint_claim_handler
from helpers.world import QUERY, coordination_rig, mint_project
from science.refusal import Refused

NAMES = ("project", "question", "hypothesis", "task", "decide")
INPUTS = {
    "question": {"name": "Does PHF19 track stage?", "query": QUERY},
    "hypothesis": {"name": "PHF19 rises with stage", "query": QUERY},
    "task": {"name": "Hold GSE179929"},
    "decide": {"name": "Use the coarse query", "body": "No disease vocabulary is bound yet."},
}
KIND = {"question": "question", "hypothesis": "hypothesis", "task": "task", "decide": "decision"}


@pytest.mark.parametrize("command", sorted(INPUTS))
def test_without_a_selection_refuses_before_any_act_and_replays(certified_work, command):
    """P2's subordinate arm."""
    with coordination_rig(certified_work, NAMES) as (d, _):
        for _ in range(2):
            with pytest.raises(Refused) as caught:
                d.invoke(command, INPUTS[command], invocation_id="N" * 8)
            assert caught.value.refusal.code == "no-current-project"


def test_a_world_kind_write_needs_no_selection(certified_work):
    """P2's world-kind arm."""
    with coordination_rig(certified_work, NAMES, extra=((MINT_CLAIM, mint_claim_handler),)) as (d, _):
        assert "proposition:free" in d.invoke("mint-claim", {"slug": "free"}).text


@pytest.mark.parametrize("command", sorted(INPUTS))
def test_under_a_selection_mints_the_kind_in_that_project(certified_work, command):
    with coordination_rig(certified_work, NAMES) as (d, ctx):
        project = mint_project(d)
        d._selection = project  # part 2's project-select sets this through the session port
        out = d.invoke(command, INPUTS[command])
    assert f"[{KIND[command]}] {KIND[command]}:{project.project}." in out.text


def test_task_depends_on_another_task(certified_work):
    import re
    with coordination_rig(certified_work, NAMES) as (d, _):
        d._selection = mint_project(d)
        first = d.invoke("task", {"name": "hold"})
        project, local = re.search(r"task:([0-9a-f]{32})\.([0-9a-f]{32})\.", first.text).groups()
        second = d.invoke("task", {"name": "run", "depends": [f"coord:{project}/{local}"]})
    assert "[task]" in second.text


def test_decide_requires_its_reasoning(certified_work):
    with coordination_rig(certified_work, NAMES) as (d, _):
        d._selection = mint_project(d)
        with pytest.raises(Refused) as caught:
            d.invoke("decide", {"name": "no body"})
    assert caught.value.refusal.code == "invalid-input"  # canonicalization: body is required
