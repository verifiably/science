"""`publish` and `publish-preview` (commons 1a, Task 6): A publishes its project's view to a git remote through
the kernel's session publish door; the preview is the same step 0, read-only."""
import secrets

import pytest

from beliefs.intents.publish import Destination
from beliefs.permit import RequiredCapabilities, scoped_authority
from beliefs.publish import pending_publishes
from beliefs.publish_request import decode_snapshot
from beliefs.root import moment_seam, open_corpus, open_world
from helpers.commons import (
    LOC_A,
    Remotes,
    a_identity,
    binding_ref,
    commit_count,
    read_rig,
    refused,
    transport_with,
    with_remotes,
)
from helpers.world import FIXTURE_AUTHORITY, concept_list_address, level_list_address, open_rig
import science.publication as publication
from science.publication import binding_fields, marker_fields, marker_of
from science.world_belief import publish_session_epoch


def _pending(cfg) -> tuple[str, ...]:
    """The unfinished publish attempts under `cfg`'s operations root, read through a corpus writer that may
    write nothing."""
    reader = open_corpus(cfg.write_root, authority=scoped_authority(RequiredCapabilities.none(), "test"),
                         profile=cfg.profile)
    return pending_publishes(reader, operations_root=cfg.operations_root, seam=moment_seam())


def _section(text: str, title: str) -> list[str]:
    """The indented `key: value` lines under a KeyVals block titled `title`."""
    lines = text.splitlines()
    start = lines.index(f"{title}:") + 1
    body = []
    for line in lines[start:]:
        if not line.startswith("  "):
            break
        body.append(line.strip())
    return body


def test_preview_lists_selection_closure_and_uncarried_inputs(fresh):
    ids = a_identity(fresh.a)
    text = read_rig(fresh.a, "publish-preview").invoke("publish-preview", {"target": "a", "to": LOC_A}).text
    # A's vocabulary lists are datasets too: the query selects all three.
    datasets = sorted((ids["dataset"], concept_list_address(), level_list_address()))
    selection = _section(text, "selection")
    assert selection[:5] == ["analysis-spec: 1", "assessment: 1", "dataset: 3", "proposition: 1", "run: 1"]
    assert sorted(selection[5:]) == sorted(
        f"record: {ref}" for ref in (*datasets, *(ids[key] for key in ("proposition", "spec", "run", "assessment"))))
    assert _section(text, "closure") == ["status: complete"]
    assert "attribution: every selected record is this world's own" in text
    assert sorted(_section(text, "inputs the destination will not carry")) == [
        f"{ref}: bytes held; redistribution unknown" for ref in datasets]


def test_preview_of_an_unresolvable_target_refuses(fresh):
    r = refused(lambda: read_rig(fresh.a, "publish-preview").invoke(
        "publish-preview", {"target": "no-such-project", "to": LOC_A}))
    assert r.code == "unknown-project"


def test_preview_without_a_current_epoch_refuses_no_epoch(fresh_no_epoch):
    r = refused(lambda: read_rig(fresh_no_epoch.a, "publish-preview").invoke(
        "publish-preview", {"target": "a", "to": LOC_A}))
    assert r.code == "no-epoch" and "science epoch" in r.message


def test_publish_to_a_git_remote_mints_the_binding_and_the_remote_lists_the_corpus(fresh):
    with with_remotes(fresh), open_rig(fresh.a, ("publish",)) as (d, ctx):
        text = d.invoke("publish", {"target": "a", "to": LOC_A}).text
        binding = binding_fields(ctx.write_view().get(binding_ref(text)))
    assert "[publication-binding]" in text and "[publication]" not in text
    assert binding.destination == Destination.remote(LOC_A)
    listing = transport_with(fresh).listing(Destination.remote(LOC_A), binding.corpus_id)
    assert f"{binding.corpus_id}.head-artifact.v1" in listing
    assert any(name.startswith(f"{binding.corpus_id}/") for name in listing)
    assert commit_count(Remotes(fresh.remotes).bare("a")) == 1


def test_publish_without_a_current_epoch_refuses_naming_the_remedy(fresh_no_epoch):
    with with_remotes(fresh_no_epoch), open_rig(fresh_no_epoch.a, ("publish",)) as (d, _):
        r = refused(lambda: d.invoke("publish", {"target": "a", "to": LOC_A}))
    assert r.code == "kernel-refused" and r.data["reason"] == "no-epoch"
    assert "epoch" in r.message and "science epoch" in r.message
    assert commit_count(Remotes(fresh_no_epoch.remotes).bare("a")) == 0


def test_publish_to_a_relative_path_is_invalid_input(fresh):
    with open_rig(fresh.a, ("publish",)) as (d, _):
        r = refused(lambda: d.invoke("publish", {"target": "a", "to": "relative/dir"}))
    assert r.code == "invalid-input" and "relative/dir" in r.message


def test_a_transport_fault_closes_kernel_refused_and_a_fresh_attempt_is_blocked_until_resume(fresh, monkeypatch):
    saved = publication.transport_for
    try:
        with with_remotes(fresh), open_rig(fresh.a, ("publish",)) as (d, _):
            fault = transport_with(fresh, fail_after_push=True)
            publication.transport_for = lambda config, destination: fault
            r1 = refused(lambda: d.invoke("publish", {"target": "a", "to": LOC_A}, invocation_id="p1"))
            assert r1.code == "kernel-refused" and r1.data["reason"] == "transport-fault"
            assert "injected failure after push" in r1.message
            r2 = refused(lambda: d.invoke("publish", {"target": "a", "to": LOC_A}, invocation_id="p2"))
            assert r2.code == "kernel-refused" and r2.data["reason"] == "publish-unfinished"
            (token,) = _pending(fresh.a)
            assert token in r2.message
            fault.fail_after_push = False
            (snapshot_path,) = (fresh.a.operations_root / "publish").glob("*/selection.v1")
            frozen = decode_snapshot(snapshot_path.read_bytes())
            def no_reclassification(ctx):
                pytest.fail("resume recomputed ownership from current mounts")
            monkeypatch.setattr("science.commands.publish.acceptance_inputs", no_reclassification)
            text = d.invoke("publish", {"target": "a", "to": LOC_A, "resume": token}, invocation_id="p3").text
            assert decode_snapshot(snapshot_path.read_bytes()) == frozen
    finally:
        publication.transport_for = saved
    assert "[publication-binding]" in text
    assert commit_count(Remotes(fresh.remotes).bare("a")) == 1
    assert _pending(fresh.a) == ()


def test_after_a_write_since_the_epoch_both_commands_refuse_naming_the_remedy(published):
    # The binding A's publish wrote moved A's corpus past its epoch.
    r = refused(lambda: read_rig(published.a, "publish-preview").invoke(
        "publish-preview", {"target": "a", "to": LOC_A}))
    assert r.code == "kernel-refused" and r.data["reason"] == "corpus-drifted" and "science epoch" in r.message
    with with_remotes(published), open_rig(published.a, ("publish",)) as (d, _):
        r = refused(lambda: d.invoke("publish", {"target": "a", "to": LOC_A}))
    assert r.code == "kernel-refused" and r.data["reason"] == "corpus-drifted" and "science epoch" in r.message
    assert commit_count(Remotes(published.remotes).bare("a")) == 1


def test_preview_matches_what_publish_froze(published):
    ids = a_identity(published.a)
    publish_session_epoch(published.a)   # the binding moved A past the epoch the publish froze at
    text = read_rig(published.a, "publish-preview").invoke("publish-preview", {"target": "a", "to": LOC_A}).text
    previewed = {line.removeprefix("record: ") for line in _section(text, "selection") if line.startswith("record: ")}
    into = published.remotes.parent / "fetched" / secrets.token_hex(8)
    root, sibling = transport_with(published).fetch_corpus(Destination.remote(LOC_A), ids["corpus_id"], into)
    fields = marker_fields(marker_of(root))
    assert fields.selection == previewed and fields.uid == ids["marker"]
    assert fields.world == published.a.world.world_id and fields.attributions == {}
    assert publication.artifact_identity(sibling) == ids["artifact"]


@pytest.mark.parametrize("terminal", ["retire", "depart"])
@pytest.mark.parametrize("command,resume", [("publish-preview", None), ("publish", None), ("publish", "f" * 32)])
def test_publication_refuses_any_nonlive_session_corpus_before_the_kernel(reopened, terminal, command, resume):
    cfg = reopened.b
    cid = a_identity(reopened.a)["corpus_id"]
    destination = cfg.world.world_root.parent / "refused-publication"
    params = {"target": "b", "to": str(destination)}
    if resume is not None:
        params["resume"] = resume
    with open_rig(cfg, (command,)) as (d, ctx):
        assert cid in ctx.session_ids()
        before = tuple(ctx.write_view().iter_stored())
        getattr(open_world(cfg.world, authority=FIXTURE_AUTHORITY), terminal)(cid)
        refusal = refused(lambda: d.invoke(command, params))
        assert tuple(ctx.write_view().iter_stored()) == before
    assert refusal.code == "corpus-retired" and refusal.data == {"corpus": cid}
    assert cid in refusal.message and "reopen the session" in refusal.message
    assert not destination.exists() and _pending(cfg) == ()
