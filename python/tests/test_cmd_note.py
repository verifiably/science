"""Notes validate their body and every world citation before minting."""
import re

import pytest

from helpers.research import add_source, correct_source, research_rig
from helpers.world import build_two_corpus_world, mint_project
from science.refusal import Refused

NAMES = ("note", "record", "project", "project-select", "revise")


def selected(d):
    project = mint_project(d)
    d.invoke("project-select", {"target": str(project)})
    return project


def test_without_a_selection_refuses_and_replays(certified_work):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, _):
        for _ in range(2):
            with pytest.raises(Refused) as caught:
                d.invoke("note", {"name": "Discussion", "body": "Reasoning"}, invocation_id="N" * 8)
            assert caught.value.refusal.code == "no-current-project"


def test_without_coordination_refuses(certified_work):
    from dataclasses import replace
    from beliefs.coordination import CoordinationAddress
    cfg = replace(build_two_corpus_world(certified_work), coordination=None)
    with research_rig(cfg, NAMES) as (d, ctx):
        d._selection = CoordinationAddress.parse("coord:" + "a" * 32)
        with pytest.raises(Refused) as expected:
            ctx.coordination()
        with pytest.raises(Refused) as caught:
            d.invoke("note", {"name": "Discussion", "body": "Reasoning"})
        assert caught.value.refusal.code == expected.value.refusal.code


def test_a_note_is_minted_in_the_project(certified_work):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, _):
        project = selected(d)
        assert d.invoke("note", {"name": "Discussion", "body": "Reasoning"}).text.startswith(
            f"[note] note:{project.project}.")


@pytest.mark.parametrize("body", ["", "  ", "\n\n"])
def test_a_blank_body_refuses_before_any_act(certified_work, body):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, ctx):
        selected(d)
        before = ctx.coordination().standing("note")
        with pytest.raises(Refused) as caught:
            d.invoke("note", {"name": "Empty", "body": body})
        assert caught.value.refusal.code == "invalid-input"
        assert caught.value.refusal.data == {"field": "body"}
        assert ctx.coordination().standing("note") == before


def test_an_unresolved_about_lists_every_miss(certified_work):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, ctx):
        selected(d)
        missing = ["proposition:missing", "source:missing"]
        with pytest.raises(Refused) as caught:
            d.invoke("note", {"name": "Missing", "body": "Reasoning", "about": missing})
        assert caught.value.refusal.code == "invalid-input"
        assert caught.value.refusal.data == {"unresolved": missing}
        assert not ctx.coordination().standing("note")


def test_about_a_read_mount_record_is_accepted(certified_work):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, _):
        selected(d)
        assert "[note]" in d.invoke("note", {"name": "Archive", "body": "Reasoning",
                                               "about": ["proposition:archived"]}).text


def test_about_repeated_or_redirected_is_accepted_and_found_once(certified_work):
    cfg = build_two_corpus_world(certified_work)
    old = add_source(cfg, "corpus", "Paper", pmid="123")
    new = correct_source(cfg, old.id, pmid="123", doi="10.1234/abc")
    with research_rig(cfg, NAMES) as (d, _):
        selected(d)
        out = d.invoke("note", {"name": "Reading", "body": "Reasoning",
                                 "about": [old.id, old.id, new.id]}).text
        stored_id = re.search(r"note:[a-f0-9.]+", out)[0]
        text = d.invoke("record", {"address": stored_id}).text
        assert text.count(f"- {old.id}") == 1
        for address in (old.id, new.id):
            assert d.invoke("record", {"address": address}).text.count(": Reading\n") == 1


def test_revise_still_refuses_a_note(certified_work):
    with research_rig(build_two_corpus_world(certified_work), NAMES) as (d, _):
        selected(d)
        out = d.invoke("note", {"name": "Dated", "body": "Reasoning"}).text
        _, project, local, _ = re.split(r"[:.]", re.search(r"note:[a-f0-9.]+", out)[0])
        with pytest.raises(Refused, match="which `revise` does not edit"):
            d.invoke("revise", {"address": f"coord:{project}/{local}", "body": "Changed"})
