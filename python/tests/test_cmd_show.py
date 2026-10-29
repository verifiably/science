"""`show` (commons 1a, Task 11): one pin's state, source, kernel status, acceptance and verification picture,
reading B's registry, the kernel's registry and the session's records; it writes nothing."""
from dataclasses import replace

from helpers.commons import LOC_A, a_identity, read_rig, refused, write_commons_config
from helpers.world import (
    LEVELS, WORKING_FIELDS, _minted_ref, concept_list_address, level_list_address, open_rig,
)

from science.config import ReadContext, load_config
from science.sharing import SharingRegistry

LAG = "registry lags the kernel: `adopt` reconciles it"


def _show(cfg, corpus_id: str) -> str:
    return read_rig(cfg, "show").invoke("show", {"corpus_id": corpus_id}).text


def test_show_is_read_only_over_its_declared_reads():
    from science.loader import production_tree
    decl = next(d for d in production_tree() if d.name == "show")
    assert decl.write_class.kind == "read-only"
    assert set(decl.reads) == {"registry", "corpus-stored"}


def test_show_a_mounted_origin_confirmed_pin(adopted):
    ids = a_identity(adopted.a)
    pin = SharingRegistry(adopted.b.sharing_root).pin(ids["corpus_id"])
    text = _show(adopted.b, ids["corpus_id"])
    for line in (f"## Pin: {ids['corpus_id']}", "state: mounted", f"world: {ids['world']}",
                 f"marker: {ids['marker']}", f"artifact: {ids['artifact']}", f"view: {pin.view}", "keep: no",
                 "kind: provider", f"reference: {LOC_A}", "confirmation: origin-confirmed",
                 f"location: {LOC_A}", f"at: {pin.fetch.at}", f"verdict: {pin.fetch.verdict}",
                 # B opened before the adopt: the kernel admitted the corpus, B's configuration carries no root of it.
                 "known: yes", "live: yes", "present: no",
                 "independence: not exposed by the kernel's inputs (Deviation 8)"):
        assert line in text, line
    assert LAG not in text


def test_show_distinguishes_accepted_evidence_from_confirmed_origin(reopened):
    ids = a_identity(reopened.a)
    unaccepted = _show(reopened.b, ids["corpus_id"])
    assert "confirmation: origin-confirmed" in unaccepted and "world accepted: no" in unaccepted
    assert "counts as evidence: no" in unaccepted and "present: yes" in unaccepted
    assert (f"{ids['assessment']}: counts no; verifications 0 from worlds none, 0 count under the policy"
            in unaccepted)
    accepted = _show(replace(reopened.b, accept=(ids["world"],)), ids["corpus_id"])
    assert "world accepted: yes" in accepted and "counts as evidence: yes" in accepted
    assert f"{ids['assessment']}: counts yes; verifications 0" in accepted


def test_show_keep_row_reads_the_configuration(reopened):
    corpus_id = a_identity(reopened.a)["corpus_id"]
    configured = replace(reopened.b, keep=(corpus_id,))
    loaded = load_config(write_commons_config(configured))
    assert "keep: yes" in _show(loaded, corpus_id)


def test_b_resolves_the_vocabulary_from_fetched_bytes_without_redeclaring(verified):
    ids = a_identity(verified.a)
    ctx = ReadContext.open(verified.b)
    assert ctx.cited(concept_list_address()).corpus_id == ids["corpus_id"]
    assert ctx.cited(level_list_address()).corpus_id == ids["corpus_id"]
    assert ctx.held_path(level_list_address()).read_bytes() == LEVELS
    assert not any(node.kind == "dataset" for node in ctx.write_view().iter_stored())
    with open_rig(verified.b, ("spec",)) as (d, _):
        text = d.invoke("spec", dict(WORKING_FIELDS, target=ids["proposition"], dataset=ids["dataset"])).text
    spec_b = _minted_ref(text, "analysis-spec")
    assert ReadContext.open(verified.b).own(spec_b)


def test_show_lists_bs_verification_of_as_assessment_once_minted(verified):
    # accept=(): A's assessment does not count, B's own verification of it does; both facts show
    ids = a_identity(verified.a)
    text = _show(verified.b, ids["corpus_id"])
    assert (f"{ids['assessment']}: counts no; verifications 1 from worlds {verified.b.world.world_id}, "
            "1 count under the policy") in text


def test_show_reports_a_registry_that_lags_the_kernel(adopted):
    ids = a_identity(adopted.a)
    registry = SharingRegistry(adopted.b.sharing_root)
    registry.write_pin(replace(registry.pin(ids["corpus_id"]), state="admitted"))
    text = _show(adopted.b, ids["corpus_id"])
    assert "state: admitted" in text and "known: yes" in text and "live: yes" in text
    assert f"! {LAG}" in text


def test_show_of_an_unknown_pin_refuses(adopted):
    refusal = refused(lambda: _show(adopted.b, "0" * 32))
    assert refusal.code == "invalid-input" and "0" * 32 in refusal.message
