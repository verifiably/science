"""Source assertion writes validate text, cross-corpus occupancy, anchor identity, and targets before acting."""
from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

import pytest
from beliefs import stored
from beliefs.confinement import host_prerequisites
from beliefs.corpus import CorpusWriter
from beliefs.permit import Authority, WritePermit
from beliefs.root import durable_executor_factory, durable_operation_port, open_corpus
from beliefs.source import source_address
from beliefs.source_assertion import Bearing, Reading, Representation, SourceAssertion, Span
from helpers.research import add_source, add_source_assertion, raw_write_node, research_rig
from helpers.snapshot import snapshot
from helpers.world import (
    FIXTURE_AUTHORITY,
    archive_config,
    build_belief_world,
    build_two_corpus_world,
    fixture_proposition_node,
    mint_project,
    walk_belief_path_confined,
)
from nodes.core.relations import Relation
from science.config import ReadContext, corpus_id_at
from science.coordination import live_selection, resolve_one
from science.refusal import Refused

NAMES = ("source", "source-assertion", "source-correct", "record", "project", "project-select")


def _subworld(base: Path, name: str) -> Path:
    sub = base / name
    sub.mkdir()
    return sub


def _assertion_inputs(
    *,
    source: str,
    proposition: str = "proposition:archived",
    sign: str = "asserts",
    quote: str = "Exact NFC quote from the source.",
    locator: str = "Results, [1]",
    sha256: str = "b" * 64,
    media_type: str = "text/markdown",
    extent: str = "full",
    extracted_by: str = "codex/gpt-6.1-sol",
    title: str = "One-line summary of the statement.",
    attributed_to: str | None = None,
    body: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "source": source,
        "proposition": proposition,
        "sign": sign,
        "quote": quote,
        "locator": locator,
        "sha256": sha256,
        "media_type": media_type,
        "extent": extent,
        "extracted_by": extracted_by,
        "title": title,
    }
    if attributed_to is not None:
        payload["attributed_to"] = attributed_to
    if body is not None:
        payload["body"] = body
    return payload


def _expected_value(inputs: dict[str, object], *, recorded_by: str = "fixture") -> SourceAssertion:
    return SourceAssertion(
        source=str(inputs["source"]),
        read=Reading(
            representation=Representation(
                sha256=str(inputs["sha256"]),
                media_type=str(inputs["media_type"]),
                extent=str(inputs["extent"]),
            ),
            span=Span(quote=str(inputs["quote"]), locator=str(inputs["locator"])),
            extracted_by=str(inputs["extracted_by"]),
            attributed_to=inputs.get("attributed_to"),  # type: ignore[arg-type]
        ),
        bears_on=Bearing(sign=str(inputs["sign"]), proposition=str(inputs["proposition"])),
        recorded_by=recorded_by,
    )


def test_mints_without_selection_and_preserves_actors_and_fields(certified_work):
    cfg = build_two_corpus_world(certified_work)
    corpus_src = add_source(cfg, "corpus", "Corpus paper", pmid="123")
    archive_src = add_source(cfg, "archive", "Archive paper", pmid="456")
    open_corpus(cfg.write_root, authority=FIXTURE_AUTHORITY, profile=cfg.profile).add(fixture_proposition_node("p1"))

    with research_rig(cfg, NAMES) as (d, ctx):
        d._selection = None
        assert d.selection is None

        # 1. attributed_to=None, body=None (omitted), proposition held only in "archive".
        args_a = _assertion_inputs(
            source=corpus_src.id,
            proposition="proposition:archived",
            locator="Results, [1]",
            title="Summary without attribution.",
        )
        reply_a = d.invoke("source-assertion", args_a, invocation_id="SA-MINT-01")
        match_a = re.fullmatch(
            r"\[source-assertion\] (source-assertion:[0-9a-f]{64}) uid=([0-9a-f]{32})\nSummary without attribution\.\n",
            reply_a.text,
        )
        assert match_a is not None, reply_a.text
        aid_a, uid_a = match_a.group(1), match_a.group(2)
        node_a = ctx.write_view().get(aid_a)
        assert node_a.uid == uid_a
        assert node_a.title == "Summary without attribution."
        assert node_a.body == ""
        facet_a = node_a.facets[stored.SOURCE_ASSERTION_FACET]
        assert facet_a["recorded_by"] == d._session.actor
        assert facet_a["read"]["extracted_by"] == "codex/gpt-6.1-sol"
        assert "attributed_to" not in facet_a["read"]

        # Re-invoking with the same invocation_id replays the identical reply rather than refusing.
        replayed = d.invoke("source-assertion", args_a, invocation_id="SA-MINT-01")
        assert replayed.text == reply_a.text

        # 2. attributed_to=None, explicit body="", source held only in "archive".
        args_b = _assertion_inputs(
            source=archive_src.id,
            proposition="proposition:p1",
            locator="Results, [2]",
            title="Summary with empty body.",
            body="",
        )
        reply_b = d.invoke("source-assertion", args_b, invocation_id="SA-MINT-02")
        aid_b = re.search(r"source-assertion:[0-9a-f]{64}", reply_b.text)[0]
        node_b = ctx.write_view().get(aid_b)
        assert node_b.body == ""
        assert "attributed_to" not in node_b.facets[stored.SOURCE_ASSERTION_FACET]["read"]
        assert node_b.relations == [Relation(source=aid_b, predicate="anchored_in", target=archive_src.id)]

        # 3. attributed_to="MSigDB curators", body="Context note.", both source and proposition only in "archive".
        args_c = _assertion_inputs(
            source=archive_src.id,
            proposition="proposition:archived",
            sign="hypothesizes",
            extent="abstract",
            locator="Abstract, [1]",
            attributed_to="MSigDB curators",
            title="Summary with curator attribution.",
            body="Context note.",
        )
        reply_c = d.invoke("source-assertion", args_c, invocation_id="SA-MINT-03")
        aid_c = re.search(r"source-assertion:[0-9a-f]{64}", reply_c.text)[0]
        node_c = ctx.write_view().get(aid_c)
        assert node_c.title == "Summary with curator attribution."
        assert node_c.body == "Context note."
        facet_c = node_c.facets[stored.SOURCE_ASSERTION_FACET]
        assert facet_c["recorded_by"] == d._session.actor
        assert facet_c["read"]["extracted_by"] == "codex/gpt-6.1-sol"
        assert facet_c["read"]["attributed_to"] == "MSigDB curators"
        assert facet_c["bears_on"] == {"sign": "hypothesizes", "proposition": "proposition:archived"}
        assert facet_c["read"]["representation"]["extent"] == "abstract"


@pytest.mark.parametrize(
    ("mode", "overrides", "expected_data"),
    [
        ("invoke", {"title": ""}, {"field": "title"}),
        ("invoke", {"title": "   "}, {"field": "title"}),
        ("invoke", {"title": "line1\nline2"}, {"field": "title"}),
        ("invoke", {"title": "line1\rline2"}, {"field": "title"}),
        ("invoke", {"title": "\ud800"}, {"field": "title"}),
        ("invoke", {"body": "\ud800"}, {"field": "body"}),
        ("invoke", {"sign": "supports"}, {"field": "sign"}),
        ("invoke", {"extent": "partial"}, {"field": "extent"}),
        ("direct", {"sign": "supports"}, {"kind": "SignatureRefused"}),
        ("direct", {"extent": "partial"}, {"kind": "MalformedRecord"}),
        ("invoke", {"sha256": "not-hex"}, {"kind": "MalformedRecord"}),
        ("invoke", {"sha256": "A" * 64}, {"kind": "MalformedRecord"}),
        ("invoke", {"quote": "cafe\u0301"}, {"kind": "MalformedRecord"}),
        ("invoke", {"locator": "Section 1, cafe\u0301"}, {"kind": "MalformedRecord"}),
        ("invoke", {"media_type": "text/cafe\u0301"}, {"kind": "MalformedRecord"}),
        ("invoke", {"source": "source:cafe\u0301"}, {"kind": "MalformedRecord"}),
        ("invoke", {"proposition": "proposition:cafe\u0301"}, {"kind": "MalformedRecord"}),
        ("invoke", {"attributed_to": "curato\u0301r"}, {"kind": "MalformedRecord"}),
        ("invoke", {"extracted_by": ""}, {"kind": "MalformedRecord"}),
        ("invoke", {"extracted_by": "agent:cafe\u0301"}, {"kind": "MalformedRecord"}),
        ("invoke", {"source": "10.1000/x"}, {"kind": "MalformedRecord"}),
        ("invoke", {"proposition": "p1"}, {"kind": "MalformedRecord"}),
    ],
)
def test_pre_act_input_refusals_leave_acts_empty(certified_work, mode, overrides, expected_data):
    cfg = build_two_corpus_world(certified_work)
    src = add_source(cfg, "corpus", "Paper", pmid="123")
    args = {**_assertion_inputs(source=src.id), **overrides}
    iid = "SA-PREACT-01"

    with research_rig(cfg, NAMES) as (d, ctx):
        if mode == "invoke":
            with pytest.raises(Refused) as caught:
                d.invoke("source-assertion", args, invocation_id=iid)
        else:
            from science.commands.source_assertion import handle as source_assertion_handle

            writer = d._session.scoped(d._required(d._decls["source-assertion"]), iid)
            with pytest.raises(Refused) as caught:
                source_assertion_handle(ctx, writer, **args)

        assert caught.value.refusal.code == "invalid-input"
        assert caught.value.refusal.data == expected_data
        assert d._session.invocation_acts(iid) == ()
        assert [n.id for n in ctx.write_view().iter_stored() if n.kind == "source-assertion"] == []


def test_same_source_duplicates_and_distinct_source_collisions_and_occupied(certified_work):
    # 1. Duplicate in "corpus" and in "archive", with coordination enabled and coordination=None, plus replay.
    for where in ("corpus", "archive"):
        sub = _subworld(certified_work, f"dup-{where}")
        cfg = build_two_corpus_world(sub)
        src = add_source(cfg, where, "Paper", pmid="123")
        existing = add_source_assertion(
            cfg,
            where,
            source=src.id,
            proposition="proposition:archived",
            quote="Exact NFC quote from the source.",
            locator="Results, [1]",
            sha256="b" * 64,
            media_type="text/markdown",
            extent="full",
            extracted_by="codex/gpt-6.1-sol",
        )
        holder_root = cfg.write_root if where == "corpus" else next(r for r in cfg.world.corpus_roots if r != cfg.write_root)
        expected_corpora = [corpus_id_at(holder_root)]
        args = _assertion_inputs(source=src.id, proposition="proposition:archived")

        for active_cfg, iid in ((cfg, "DUP-COORD"), (replace(cfg, coordination=None), "DUP-NOCOORD")):
            with research_rig(active_cfg, NAMES) as (d, _):
                with pytest.raises(Refused) as first:
                    d.invoke("source-assertion", args, invocation_id=iid)
                refusal = first.value.refusal
                assert refusal.code == "invalid-input"
                assert f"{existing.id} is already recorded" == refusal.message
                assert "anchor_conflict" not in refusal.data
                assert refusal.data == {
                    "existing": [
                        {
                            "address": existing.id,
                            "uid": existing.uid,
                            "source": src.id,
                            "corpora": expected_corpora,
                        }
                    ]
                }
                assert d._session.invocation_acts(iid) == ()
                with pytest.raises(Refused) as replayed:
                    d.invoke("source-assertion", args, invocation_id=iid)
                assert replayed.value.refusal == refusal

    # 2. Distinct-source collision (both across mounts and within write_root) + nonexistent source fallthrough.
    sub_col = _subworld(certified_work, "collision")
    cfg_col = build_two_corpus_world(sub_col)
    s1 = add_source(cfg_col, "corpus", "First", pmid="111")
    s2 = add_source(cfg_col, "archive", "Second", doi="10.1234/disjoint")
    s3 = add_source(cfg_col, "corpus", "Third in write root", pmid="222")
    corpus_cid = corpus_id_at(cfg_col.write_root)

    with research_rig(cfg_col, NAMES) as (d, ctx):
        minted = d.invoke("source-assertion", _assertion_inputs(source=s1.id), invocation_id="COL-MINT")
        aid = re.search(r"source-assertion:[0-9a-f]{64}", minted.text)[0]
        minted_node = ctx.write_view().get(aid)

        for other_src, iid in ((s2, "COL-ACROSS"), (s3, "COL-LOCAL")):
            with pytest.raises(Refused) as caught:
                d.invoke("source-assertion", _assertion_inputs(source=other_src.id), invocation_id=iid)
            refusal = caught.value.refusal
            assert refusal.code == "invalid-input"
            assert "existing" not in refusal.data
            assert refusal.data == {
                "anchor_conflict": {
                    "address": aid,
                    "uid": minted_node.uid,
                    "existing_source": s1.id,
                    "resolved_existing_source": s1.id,
                    "requested_source": other_src.id,
                    "resolved_requested_source": other_src.id,
                    "corpora": [corpus_cid],
                }
            }
            assert d._session.invocation_acts(iid) == ()

        # Nonexistent source falls through to step 4 unresolved check.
        missing_src = "source:" + "9" * 64
        with pytest.raises(Refused) as caught_missing:
            d.invoke("source-assertion", _assertion_inputs(source=missing_src), invocation_id="COL-MISSING")
        assert caught_missing.value.refusal.code == "invalid-input"
        assert caught_missing.value.refusal.data == {"unresolved": [missing_src]}
        assert d._session.invocation_acts("COL-MISSING") == ()

    # 3. Wrong-kind occupancy at value.id via deprecated_ids on a dataset.
    sub_occ = _subworld(certified_work, "occupied")
    cfg_occ = build_two_corpus_world(sub_occ)
    src_occ = add_source(cfg_occ, "corpus", "Paper", pmid="333")
    occ_args = _assertion_inputs(source=src_occ.id)
    precomputed = _expected_value(occ_args)
    occupying = stored.dataset_node(
        title="Occupying dataset",
        resources=[{"name": "occ.txt", "digest": "sha256:" + "0" * 64}],
    ).model_copy(update={"deprecated_ids": [precomputed.id]})
    raw_write_node(cfg_occ.write_root, occupying)
    occ_cid = corpus_id_at(cfg_occ.write_root)

    with research_rig(cfg_occ, NAMES) as (d, _):
        with pytest.raises(Refused) as caught_occ:
            d.invoke("source-assertion", occ_args, invocation_id="OCC-01")
        refusal_occ = caught_occ.value.refusal
        assert refusal_occ.code == "invalid-input"
        assert "existing" not in refusal_occ.data
        assert refusal_occ.data == {
            "occupied": {
                "address": occupying.id,
                "uid": occupying.uid,
                "kind": "dataset",
                "corpora": [occ_cid],
                "redirect": True,
            }
        }
        assert d._session.invocation_acts("OCC-01") == ()


@pytest.mark.parametrize(
    ("damage", "expected_kind"),
    [
        ("stale_stamp", "SemanticHashStale"),
        ("malformed_facet_restamped", "MalformedRecord"),
        ("extra_assesses_edge", "SourceAssertionRefused"),
    ],
)
def test_damaged_existing_source_assertion_closes_kernel_refused_cleanly(certified_work, damage, expected_kind):
    cfg = build_two_corpus_world(certified_work)
    src = add_source(cfg, "corpus", "Paper", pmid="123")
    args = _assertion_inputs(source=src.id)
    val = _expected_value(args)
    damaged = stored.source_assertion_node(val, title="Damaged assertion.")
    if damage == "stale_stamp":
        del damaged.facets[stored.SOURCE_ASSERTION_FACET]["recorded_by"]
    elif damage == "malformed_facet_restamped":
        del damaged.facets[stored.SOURCE_ASSERTION_FACET]["recorded_by"]
        stored.stamp_semantic_identity(damaged)
    elif damage == "extra_assesses_edge":
        damaged.relations.append(Relation(source=damaged.id, predicate="assesses", target="proposition:archived"))
        stored.stamp_semantic_identity(damaged)
    raw_write_node(cfg.write_root, damaged)

    with research_rig(cfg, NAMES) as (d, _):
        iid = f"DAMAGED-{damage.replace('_', '-')}"
        with pytest.raises(Refused) as first:
            d.invoke("source-assertion", args, invocation_id=iid)
        assert first.value.refusal.code == "kernel-refused"
        assert first.value.refusal.data == {"kind": expected_kind}
        assert d._session.invocation_acts(iid) == ()

        # Re-invoking with the same invocation_id replays kernel-refused rather than outcome-unknown.
        with pytest.raises(Refused) as replayed:
            d.invoke("source-assertion", args, invocation_id=iid)
        assert replayed.value.refusal.code == "kernel-refused"
        assert replayed.value.refusal.data == {"kind": expected_kind}


def test_unresolved_unmounted_and_wrong_kind_targets(certified_work):
    # 1. Both source and proposition missing reported together in (source, proposition) order.
    sub_miss = _subworld(certified_work, "missing")
    cfg_miss = build_two_corpus_world(sub_miss)
    bad_src = "source:" + "0" * 64
    bad_prop = "proposition:missing"
    with research_rig(cfg_miss, NAMES) as (d, _):
        with pytest.raises(Refused) as caught:
            d.invoke(
                "source-assertion",
                _assertion_inputs(source=bad_src, proposition=bad_prop),
                invocation_id="MISS-01",
            )
        assert caught.value.refusal.code == "invalid-input"
        assert caught.value.refusal.data == {"unresolved": [bad_src, bad_prop]}
        assert d._session.invocation_acts("MISS-01") == ()

    # 2. Under coordination=None, source and proposition held only in "archive" report unresolved + unmounted.
    sub_unm = _subworld(certified_work, "unmounted")
    cfg_unm = build_two_corpus_world(sub_unm)
    arch_src = add_source(cfg_unm, "archive", "Archive-only paper", pmid="456")
    archive_root = next(r for r in cfg_unm.world.corpus_roots if r != cfg_unm.write_root)
    archive_cid = corpus_id_at(archive_root)
    with research_rig(replace(cfg_unm, coordination=None), NAMES) as (d, _):
        with pytest.raises(Refused) as caught_unm:
            d.invoke(
                "source-assertion",
                _assertion_inputs(source=arch_src.id, proposition="proposition:archived"),
                invocation_id="UNMOUNT-01",
            )
        refusal_unm = caught_unm.value.refusal
        assert refusal_unm.code == "invalid-input"
        assert "coordination = false" in refusal_unm.message
        assert refusal_unm.data == {
            "unresolved": [arch_src.id, "proposition:archived"],
            "unmounted": {
                arch_src.id: [archive_cid],
                "proposition:archived": [archive_cid],
            },
        }
        assert d._session.invocation_acts("UNMOUNT-01") == ()

    # 3. deprecated_ids on a dataset aliasing source: or proposition: refuses wrong_kind.
    sub_wk = _subworld(certified_work, "wrong-kind")
    cfg_wk = build_two_corpus_world(sub_wk)
    valid_src = add_source(cfg_wk, "corpus", "Valid source", pmid="777")
    aliased_ds = stored.dataset_node(
        title="Aliased dataset",
        resources=[{"name": "wk.txt", "digest": "sha256:" + "1" * 64}],
    ).model_copy(update={"deprecated_ids": ["source:aliased-src", "proposition:aliased-prop"]})
    raw_write_node(cfg_wk.write_root, aliased_ds)

    with research_rig(cfg_wk, NAMES) as (d, _):
        with pytest.raises(Refused) as caught_src:
            d.invoke(
                "source-assertion",
                _assertion_inputs(source="source:aliased-src", proposition="proposition:archived"),
                invocation_id="WK-SRC",
            )
        assert caught_src.value.refusal.code == "invalid-input"
        assert caught_src.value.refusal.data == {
            "wrong_kind": [{"slot": "source", "address": aliased_ds.id, "kind": "dataset"}]
        }

        with pytest.raises(Refused) as caught_prop:
            d.invoke(
                "source-assertion",
                _assertion_inputs(source=valid_src.id, proposition="proposition:aliased-prop"),
                invocation_id="WK-PROP",
            )
        assert caught_prop.value.refusal.code == "invalid-input"
        assert caught_prop.value.refusal.data == {
            "wrong_kind": [{"slot": "proposition", "address": aliased_ds.id, "kind": "dataset"}]
        }

        with pytest.raises(Refused) as caught_both:
            d.invoke(
                "source-assertion",
                _assertion_inputs(source="source:aliased-src", proposition="proposition:aliased-prop"),
                invocation_id="WK-BOTH",
            )
        assert caught_both.value.refusal.code == "invalid-input"
        assert caught_both.value.refusal.data == {
            "wrong_kind": [
                {"slot": "source", "address": aliased_ds.id, "kind": "dataset"},
                {"slot": "proposition", "address": aliased_ds.id, "kind": "dataset"},
            ]
        }


def test_identifier_correction_redirect_sequence(certified_work):
    cfg = build_two_corpus_world(certified_work)
    addr_a = source_address({"pmid": "789"})
    addr_b = source_address({"doi": "10.1234/redirected", "pmid": "789"})

    with research_rig(cfg, NAMES) as (d, ctx):
        d.invoke("source", {"title": "Redirected paper", "pmid": "789"})
        d.invoke("source-correct", {"address": addr_a, "doi": "10.1234/redirected", "grounds": "publisher page"})

        args_a = _assertion_inputs(source=addr_a, proposition="proposition:archived", title="Redirected reading.")
        out = d.invoke("source-assertion", args_a, invocation_id="REDIR-MINT")
        aid = re.search(r"source-assertion:[0-9a-f]{64}", out.text)[0]
        minted_node = ctx.write_view().get(aid)
        assert minted_node.relations == [Relation(source=aid, predicate="anchored_in", target=addr_a)]
        assert aid == _expected_value(_assertion_inputs(source=addr_b, proposition="proposition:archived")).id

    # Copy equal assertion to "archive" as well to verify cross-mount deduplication and live_selection.
    archive = archive_config(cfg)
    archive_root = archive.write_root.resolve()
    read_mounts = tuple(r.resolve() for r in archive.world.corpus_roots if r.resolve() != archive_root)
    recorder_auth = Authority(
        WritePermit.full(),
        minted_node.facets[stored.SOURCE_ASSERTION_FACET]["recorded_by"],
    )
    CorpusWriter(
        archive_root,
        durable_executor_factory(),
        authority=recorder_auth,
        profile=archive.profile,
        operation_port=durable_operation_port(archive_root, recorder_auth, profile=archive.profile),
        read_mounts=read_mounts,
    ).add(minted_node)

    with research_rig(cfg, NAMES) as (d, ctx):
        args_b = _assertion_inputs(source=addr_b, proposition="proposition:archived", title="Redirected reading.")
        with pytest.raises(Refused) as caught:
            d.invoke("source-assertion", args_b, invocation_id="REDIR-DUP")
        refusal = caught.value.refusal
        assert refusal.code == "invalid-input"
        assert "anchor_conflict" not in refusal.data
        assert refusal.data == {
            "existing": [
                {
                    "address": aid,
                    "uid": minted_node.uid,
                    "source": addr_a,
                    "corpora": sorted(corpus_id_at(r) for r in cfg.world.corpus_roots),
                }
            ]
        }

        project = resolve_one(ctx, mint_project(d))
        live_selection(ctx, project)

        for record_args in (
            {"address": addr_a},
            {"address": addr_b},
            {"doi": "10.1234/redirected"},
            {"pmid": "789"},
            {"address": "proposition:archived"},
        ):
            text = d.invoke("record", record_args).text
            assert "source assertions:\n" in text
            assert text.count(f"  {aid}:") == 1


def test_source_assertions_are_inert_in_belief_evaluation(certified_work, certified_worker_work):
    # (a) Unassessed NoBelief world.
    cfg_a = build_belief_world(certified_work)
    with research_rig(cfg_a, ("source", "source-assertion", "belief")) as (d, _):
        before_a = d.invoke("belief", {"proposition": "proposition:p1"}).text
        assert "kind: NoBelief" in before_a

        src_out = d.invoke("source", {"title": "Literature paper", "pmid": "101010"}).text
        src_id = re.search(r"source:[0-9a-f]{64}", src_out)[0]
        for idx, sign in enumerate(("asserts", "denies", "hypothesizes"), start=1):
            d.invoke(
                "source-assertion",
                _assertion_inputs(
                    source=src_id,
                    proposition="proposition:p1",
                    sign=sign,
                    locator=f"Results, [{idx}]",
                    title=f"Statement {sign}.",
                ),
            )

        after_a = d.invoke("belief", {"proposition": "proposition:p1"}).text
        assert after_a == before_a

    # (b) Admitted Belief world under host confinement when available.
    if host_prerequisites() is None:
        snap = snapshot(certified_worker_work, "walked-confined", walk_belief_path_confined)
        snap.restore()
        cfg_b, prop = snap.value
        with research_rig(cfg_b, ("source", "source-assertion", "belief")) as (d, _):
            before_b = d.invoke("belief", {"proposition": prop}).text
            assert "kind: Belief" in before_b
            digest_before = ReadContext.open(cfg_b).evaluate(prop).belief_input_digest

            src_out = d.invoke("source", {"title": "Confined literature paper", "pmid": "202020"}).text
            src_id = re.search(r"source:[0-9a-f]{64}", src_out)[0]
            for idx, sign in enumerate(("asserts", "denies", "hypothesizes"), start=1):
                d.invoke(
                    "source-assertion",
                    _assertion_inputs(
                        source=src_id,
                        proposition=prop,
                        sign=sign,
                        locator=f"Discussion, [{idx}]",
                        title=f"Confined statement {sign}.",
                    ),
                )

            stored_assertions = [
                n.id for n in ReadContext.open(cfg_b).write_view().iter_stored() if n.kind == "source-assertion"
            ]
            assert len(stored_assertions) == 3

            after_b = d.invoke("belief", {"proposition": prop}).text
            digest_after = ReadContext.open(cfg_b).evaluate(prop).belief_input_digest
            assert after_b == before_b
            assert digest_after == digest_before


def test_positive_coreference_keeps_the_extractions_original_anchor(certified_work):
    cfg = build_two_corpus_world(certified_work)
    left = add_source(cfg, "corpus", "Publisher", doi="10.1234/here")
    right = add_source(cfg, "corpus", "Index", pmid="222")
    with research_rig(cfg, (*NAMES, "source-coreference")) as (dispatch, ctx):
        dispatch.invoke("source-coreference", {
            "left": left.id, "right": right.id, "stance": "same", "grounds": "Same journal version.",
        })
        assert "state: positive" in dispatch.invoke("record", {"address": right.id}).text
        dispatch.invoke("source-assertion", _assertion_inputs(source=left.id))
        with pytest.raises(Refused) as caught:
            dispatch.invoke("source-assertion", _assertion_inputs(source=right.id), invocation_id="linked-anchor")
        assert caught.value.refusal.code == "invalid-input"
        conflict = caught.value.refusal.data["anchor_conflict"]
        assert conflict["existing_source"] == left.id and conflict["requested_source"] == right.id
        assert dispatch._session.invocation_acts("linked-anchor") == ()
        assert ctx.write_view().get(conflict["address"]).uid == conflict["uid"]
