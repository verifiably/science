"""recheck: re-check one store location through the kernel's session route,
settling an unmatched holdings intent (sci-409235)."""
from dataclasses import replace
from hashlib import sha256
from uuid import uuid4

import pytest

from beliefs import stored
from beliefs.holdings.records import Absent, Found
from beliefs.root import LifecycleState, read_lifecycle_state, store_identity

from helpers.world import build_belief_world, build_two_corpus_world, open_rig
from science.refusal import Refused
from test_stores import replicate_store, tree_snapshot


def blocked_reasons(cfg) -> dict[str, list[str]]:
    """The holdings reduction's blocked rows over every read view, by location."""
    from science.config import ReadContext
    from science.holdings import reduced_heads
    ctx = ReadContext.open(cfg)
    _, blocked = reduced_heads(ctx.world, frozenset(cid for cid, _ in ctx.read_views()))
    return {row["location"]: list(row["reasons"]) for row in blocked}


def active_heads(cfg, location: str) -> list[dict]:
    from science.config import ReadContext
    from science.holdings import reduced_heads
    ctx = ReadContext.open(cfg)
    active, _ = reduced_heads(ctx.world, frozenset(cid for cid, _ in ctx.read_views()))
    return [row for row in active if row["location"] == location]


def hold_with_dataset(cfg, tmp_path, name: str, content: bytes) -> str:
    """Hold `content` through the `dataset` command; its canonical location."""
    source = tmp_path / name
    source.write_bytes(content)
    with open_rig(cfg, ("dataset",)) as (d, _):
        d.invoke("dataset", {"path": str(source), "title": name})
    return f"store:{store_identity(cfg.store_root)}:{sha256(content).hexdigest()}/{name}"


def refused_write(cfg, work, tmp_path):
    """The incident: `dataset` against a restored read-only-serviceable replica
    bound as `store_root` appends its holdings intent, then the store refuses.
    Returns that configuration and the location left unsettled."""
    restored = replicate_store(cfg, work / "restored", admit=True)
    assert read_lifecycle_state(restored) is LifecycleState.READ_ONLY_SERVICEABLE
    cfg = replace(cfg, store_root=restored)
    content = b"gene\tv\nPHF19\t1\n"
    source = tmp_path / "matrix.txt"
    source.write_bytes(content)
    with open_rig(cfg, ("dataset",)) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("dataset", {"path": str(source), "title": "expression"})
    assert caught.value.refusal.data["kind"] == "StoreWriteRefused"
    return cfg, f"store:{store_identity(restored)}:{sha256(content).hexdigest()}/matrix.txt"


def minted(ctx, session, iid):
    """The records an invocation minted, by kind."""
    out = {}
    for act in session.invocation_acts(iid):
        for uid, record_id in act.record_ids:
            node = ctx.write_view().get(record_id)
            assert node.uid == uid
            out.setdefault(node.kind, []).append(node)
    return out


def recheck(cfg, location, iid):
    """Run `recheck` in its own session; the minted records by kind."""
    with open_rig(cfg, ("recheck",)) as (d, ctx):
        d.invoke("recheck", {"location": location}, invocation_id=iid)
        return minted(ctx, d._session, iid)


def refuses_before_effect(cfg, location, iid="R" * 8):
    """`recheck` refuses `invalid-input` with no act and no corpus change."""
    before = tree_snapshot(cfg.write_root)
    with open_rig(cfg, ("recheck",)) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke("recheck", {"location": location}, invocation_id=iid)
        assert d._session.invocation_acts(iid) == ()
    assert tree_snapshot(cfg.write_root) == before
    assert caught.value.refusal.code == "invalid-input"
    return caught.value.refusal


@pytest.fixture
def incident(certified_work, tmp_path):
    cfg = build_belief_world(certified_work)
    other = hold_with_dataset(cfg, tmp_path, "other.txt", b"other\n")
    cfg, location = refused_write(cfg, certified_work, tmp_path)
    return cfg, location, other


def test_recheck_settles_a_refused_write(incident):
    cfg, location, other = incident
    assert blocked_reasons(cfg)[location] == ["unsettled"]
    assert other not in blocked_reasons(cfg)
    other_heads = active_heads(cfg, other)
    records = recheck(cfg, location, "C" * 8)
    (observation,) = records["holdings-observation"]
    value = stored.holdings_observation_value(observation)
    assert value.location.canonical() == location
    assert value.outcome == Absent()
    (report,) = records["act-report"]
    assert stored.act_report_facet(report)["operation"] == "re-check"
    assert location not in blocked_reasons(cfg)
    assert other not in blocked_reasons(cfg)
    assert active_heads(cfg, other) == other_heads


def test_recheck_finds_held_bytes(certified_work, tmp_path):
    cfg = build_belief_world(certified_work)
    content = b"held\n"
    location = hold_with_dataset(cfg, tmp_path, "held.txt", content)
    (earlier,) = [row["head"] for row in active_heads(cfg, location)]
    (observation,) = recheck(cfg, location, "F" * 8)["holdings-observation"]
    value = stored.holdings_observation_value(observation)
    assert value.outcome == Found("sha256:" + sha256(content).hexdigest())
    assert earlier.removeprefix("holdings-observation:") in value.supersedes


def test_second_recheck_supersedes_the_first(certified_work, tmp_path):
    cfg = build_belief_world(certified_work)
    location = hold_with_dataset(cfg, tmp_path, "twice.txt", b"twice\n")
    recheck(cfg, location, "A" * 8)
    (second,) = recheck(cfg, location, "B" * 8)["holdings-observation"]
    (head,) = active_heads(cfg, location)
    assert head["head"].removeprefix("holdings-observation:") == stored.holdings_observation_value(second).identity()


def test_inherited_head_is_superseded(certified_work):
    """The two-corpus world: the archive mount holds the concept list in the
    one store. A re-check from the write corpus supersedes the archive's head,
    so the location keeps one head and is not contested."""
    cfg = build_two_corpus_world(certified_work)
    from science.config import ReadContext
    ctx = ReadContext.open(cfg)
    (location,) = {stored.holdings_observation_value(node).location.canonical()
                   for _, view in ctx.read_views() for node in view.iter_stored()
                   if node.kind == "holdings-observation"
                   and stored.holdings_observation_value(node).location.relative_path.endswith("/concepts.txt")}
    (inherited,) = active_heads(cfg, location)
    (observation,) = recheck(cfg, location, "I" * 8)["holdings-observation"]
    value = stored.holdings_observation_value(observation)
    assert inherited["head"].removeprefix("holdings-observation:") in value.supersedes
    (head,) = active_heads(cfg, location)
    assert head["head"].removeprefix("holdings-observation:") == value.identity()
    assert location not in blocked_reasons(cfg)


def test_never_written_location_reads_absent(certified_work):
    cfg = build_belief_world(certified_work)
    location = f"store:{store_identity(cfg.store_root)}:never/written.txt"
    (observation,) = recheck(cfg, location, "N" * 8)["holdings-observation"]
    assert stored.holdings_observation_value(observation).outcome == Absent()


def test_inconclusive_read_keeps_the_block(incident, monkeypatch):
    """The session binds `holdings_seam()` at open; a seam whose read is
    unestablished stands in for an unserviceable store."""
    import beliefs.session as session_module
    from beliefs.holdings.seam import ReadUnestablishedView
    from beliefs.root import holdings_seam
    cfg, location, _ = incident
    seam = replace(holdings_seam(), read_path=lambda root, path: ReadUnestablishedView("io-error", "injected"))
    monkeypatch.setattr(session_module, "holdings_seam", lambda: seam)
    records = recheck(cfg, location, "U" * 8)
    assert "holdings-observation" not in records
    (report,) = records["act-report"]
    (entry,) = stored.act_report_facet(report)["entries"]
    assert entry["outcome"]["type"] == "retrieval-failed"
    assert blocked_reasons(cfg)[location] == ["unsettled"]


@pytest.mark.parametrize("location", [
    "", "store:", "store:abc:x.txt", "uppercase-id", "bound:../escape", "bound:/abs",
    "url:https://example.org/x", "https://example.org/x",
])
def test_malformed_location_refuses(certified_work, location):
    cfg = build_belief_world(certified_work)
    bound = store_identity(cfg.store_root)
    location = {"uppercase-id": "store:" + "A" * 32 + ":x.txt"}.get(location, location)
    location = location.replace("bound:", f"store:{bound}:", 1) if location.startswith("bound:") else location
    refuses_before_effect(cfg, location)


def test_url_location_names_the_scope(certified_work):
    cfg = build_belief_world(certified_work)
    assert "URL" in refuses_before_effect(cfg, "url:https://example.org/x").message


def test_padded_location_refuses(certified_work):
    cfg = build_belief_world(certified_work)
    location = f"store:{store_identity(cfg.store_root)}:never/written.txt"
    refuses_before_effect(cfg, " " + location, "P" * 8)
    refuses_before_effect(cfg, location + "\n", "Q" * 8)


def test_unconfigured_store_refuses(certified_work):
    cfg = build_belief_world(certified_work)
    refusal = refuses_before_effect(cfg, f"store:{uuid4().hex}:x.txt")
    assert store_identity(cfg.store_root) in refusal.message


def test_read_store_location_refuses_with_the_route(certified_work):
    from beliefs.root import init_store_root
    from helpers.world import FIXTURE_AUTHORITY
    cfg = build_belief_world(certified_work)
    extra = certified_work / "read-store"
    init_store_root(extra, authority=FIXTURE_AUTHORITY)
    cfg = replace(cfg, read_store_roots=(extra,))
    refusal = refuses_before_effect(cfg, f"store:{store_identity(extra)}:x.txt")
    assert str(extra) in refusal.message
    assert "store_root" in refusal.message and "read_store_roots" in refusal.message


@pytest.mark.parametrize("dropped", ["holdings-observation", "act-report"])
def test_insufficient_permit_refuses_before_effect(certified_work, dropped):
    """An attended session holds the full permit, so the narrower authority is
    the invocation's: a declaration whose routes omit one of the two families
    the kernel route requires refuses `permit-exceeded` with no act."""
    from science.dispatch import Dispatcher
    from science.loader import production_tree, resolve_handlers
    from science.config import ReadContext
    from science.schema import WriteClass
    from science.session import open_session
    cfg = build_belief_world(certified_work)
    (decl,) = [d for d in production_tree() if d.name == "recheck"]
    kinds = tuple(k for k in decl.write_class.kinds if k != dropped)
    narrow = replace(decl, write_class=WriteClass(
        "mints", kinds, {k: v for k, v in decl.write_class.routes.items() if k != dropped}))
    location = f"store:{store_identity(cfg.store_root)}:never/written.txt"
    before = tree_snapshot(cfg.write_root)
    session = open_session(cfg)
    try:
        d = Dispatcher((narrow,), resolve_handlers((decl,)), ReadContext.open(cfg), session=session)
        with pytest.raises(Refused) as caught:
            d.invoke("recheck", {"location": location}, invocation_id="W" * 8)
        assert session.invocation_acts("W" * 8) == ()
    finally:
        session.close()
    assert caught.value.refusal.code == "permit-exceeded"
    assert tree_snapshot(cfg.write_root) == before


def test_rendered_report_states_absent(incident):
    cfg, location, _ = incident
    with open_rig(cfg, ("recheck",)) as (d, _):
        text = d.invoke("recheck", {"location": location}).text
    assert f"absent at {location}" in text
    assert f"{location}: observed holdings-observation:" in text


def pages(d, first: str) -> str:
    """Every page of a truncated write report, cursor markers dropped."""
    text, out = first, []
    while "continue with cursor " in text:
        body, _, tail = text.rpartition("\n… truncated at ")
        out.append(body)
        text = d.invoke("recheck", {}, cursor=tail.rsplit("cursor ", 1)[1].strip()).text
    return "".join(out) + text


def test_replay_renders_the_same_detail(incident):
    from science.cursor import MIN_OUTPUT_BUDGET
    cfg, location, _ = incident
    with open_rig(cfg, ("recheck",)) as (d, _):
        first = d.invoke("recheck", {"location": location}, invocation_id="Y" * 8)
        acts = d._session.invocation_acts("Y" * 8)
        again = d.invoke("recheck", {"location": location}, invocation_id="Y" * 8)
        assert again.text == first.text
        assert d._session.invocation_acts("Y" * 8) == acts
        d._decls["recheck"] = replace(d._decls["recheck"], output_budget=MIN_OUTPUT_BUDGET)
        paged = d.invoke("recheck", {"location": location}, invocation_id="Y" * 8).text
        assert "continue with cursor " in paged
        assert pages(d, paged) == first.text
    assert f"absent at {location}" in first.text


def test_recovery_configuration_settles_a_read_store_location(certified_work, tmp_path):
    """docs/stores.md's route: after relocation the blocked location is in a
    read store, so the working configuration refuses; a recovery configuration
    binding that store as `store_root`, with the same `write_root`, settles it."""
    from science.config import ReadContext
    from test_stores import run_store_recipe
    cfg, location = refused_write(build_belief_world(certified_work), certified_work, tmp_path)
    restored = cfg.store_root
    fresh = certified_work / "store-working"
    created = run_store_recipe(fresh, certified_work / "recipe-home")
    assert created.returncode == 0, created.stderr
    working = replace(cfg, store_root=fresh, read_store_roots=(restored,))
    source = tmp_path / "new.txt"
    source.write_bytes(b"new expression\n")
    with open_rig(working, ("dataset",)) as (d, _):
        out = d.invoke("dataset", {"path": str(source), "title": "new"})
    new_address = next(word for word in out.text.split() if word.startswith("dataset:"))
    refusal = refuses_before_effect(working, location)
    assert str(restored) in refusal.message and "recovery configuration" in refusal.message
    assert blocked_reasons(working)[location] == ["unsettled"]
    recovery = replace(cfg, store_root=restored, read_store_roots=(fresh,))
    (observation,) = recheck(recovery, location, "V" * 8)["holdings-observation"]
    assert stored.holdings_observation_value(observation).outcome == Absent()
    assert location not in blocked_reasons(working)
    held = ReadContext.open(working).held_path(new_address)
    assert held.is_relative_to(fresh) and held.read_bytes() == source.read_bytes()
