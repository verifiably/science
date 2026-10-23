"""The accept policy (commons spec §9, plan Task 10): which mounted records count toward the reader's belief.

`counts` is first applicable branch decides: Own (the write root, and a configured root holding no marker), then
no carrier, then Carried, then Own adopted back through a binding, then the carrier's own. The `INPUTS_*` values
below are plain `AcceptanceInputs`; the last test reads B with A's publication adopted and mounted."""
from __future__ import annotations

import json
import shutil
from dataclasses import replace

import pytest
from beliefs.belief import AcceptancePolicy
from beliefs.identity import v1
from beliefs.root import metadata_root_for
from beliefs.world import WorldConfig
from helpers.commons import a_identity

from science.acceptance import AcceptanceInputs, Carrier, acceptance_inputs, counts, statement
from science.commands.next import classify
from science.config import ReadContext, corpus_id_at
from science.refusal import Refused
from science.sharing import FetchRecord, Pin, PinSource, ProviderBinding, SharingRegistry

W_SELF, W_A, W_B, W_H = "1" * 32, "a" * 32, "b" * 32, "c" * 32
CID_SELF, CID_LOCAL, CID_A, CID_B, CID_H, CID_BACK, CID_FAKE = (f"{n}" * 32 for n in "0123456")
MARKER_A, MARKER_A_OLD, MARKER_B, MARKER_H, MARKER_BACK, MARKER_FAKE = (
    "marker-a", "marker-a-old", "marker-b", "marker-h", "marker-back", "marker-fake")
LOC_A, LOC_B, LOC_BACK, LOC_FAKE = (f"https://remote.test/{n}" for n in ("a", "b", "back", "fake"))
AT = "2026-10-22T09:00:00Z"

A_ASSESSMENT, A_DATASET = "assessment:a1", "dataset:sha256:" + "d" * 64
B_OWN_ASSESSMENT, H_OWN_ASSESSMENT, OWN_ASSESSMENT = "assessment:b1", "assessment:h1", "assessment:own1"


def pin(corpus: str, world: str, marker: str, location: str, *, source: PinSource | None = None) -> Pin:
    return Pin(corpus, marker, f"artifact-{corpus[:4]}", world, "view:x",
               PinSource("provider", location) if source is None else source,
               FetchRecord(location, AT, "validated"), "mounted")


def binding(world: str, location: str, *, confirmed: bool = True) -> ProviderBinding:
    return ProviderBinding(world, (location,), AT, confirmed)


PIN_A, PIN_B = pin(CID_A, W_A, MARKER_A, LOC_A), pin(CID_B, W_B, MARKER_B, LOC_B)
BIND_A, BIND_B = binding(W_A, LOC_A), binding(W_B, LOC_B)
CARRIER_A = Carrier(CID_A, W_A, MARKER_A, frozenset({A_ASSESSMENT, A_DATASET}), {})
# B carries A's assessment, attributed to A's publication, plus a forged attribution of a record A does not hold.
CARRIER_B = Carrier(CID_B, W_B, MARKER_B, frozenset({B_OWN_ASSESSMENT, A_ASSESSMENT, "assessment:invented"}),
                    {A_ASSESSMENT: (CID_A, MARKER_A), "assessment:invented": (CID_A, MARKER_A)})
# A hand-listed root carrying a marker: H's own assessment, and A's dataset carried.
CARRIER_H = Carrier(CID_H, W_H, MARKER_H, frozenset({H_OWN_ASSESSMENT, A_DATASET}), {A_DATASET: (CID_A, MARKER_A)})

INPUTS_EMPTY = AcceptanceInputs(
    own_corpus=CID_SELF, own_roots=frozenset({CID_SELF, CID_LOCAL}), verifiers=frozenset({W_SELF}),
    pins={}, bindings={}, own_bindings=frozenset(), carriers={})
INPUTS_HAND_LISTED_PUBLICATION = replace(
    INPUTS_EMPTY, own_roots=frozenset({CID_SELF}), verifiers=frozenset({W_SELF, W_H}),
    bindings={W_A: BIND_A}, carriers={CID_A: CARRIER_A, CID_H: CARRIER_H})
# B origin-confirmed and accepted; A mounted by hand, unpinned and unaccepted.
INPUTS_ACCEPT_B = replace(
    INPUTS_EMPTY, verifiers=frozenset({W_SELF, W_B}), pins={CID_B: PIN_B}, bindings={W_A: BIND_A, W_B: BIND_B},
    carriers={CID_A: CARRIER_A, CID_B: CARRIER_B})
INPUTS_ACCEPT_A_AND_PIN_A = replace(INPUTS_ACCEPT_B, verifiers=frozenset({W_SELF, W_A}),
                                    pins={CID_A: PIN_A, CID_B: PIN_B})


def test_own_write_root_and_markerless_configured_roots_count_under_an_empty_policy():
    assert counts(INPUTS_EMPTY, CID_SELF, OWN_ASSESSMENT)
    assert counts(INPUTS_EMPTY, CID_LOCAL, "assessment:local")
    # A root that is neither ours nor a publication (a registry root with no marker) never counts.
    assert not counts(INPUTS_EMPTY, CID_A, A_ASSESSMENT)


def test_a_hand_listed_root_carrying_a_marker_is_a_carrier_not_own():
    # a configured root with a marker but no pin: its own records fail branch 5; a carried record takes branch 3
    assert not counts(INPUTS_HAND_LISTED_PUBLICATION, CID_H, H_OWN_ASSESSMENT)
    assert not counts(INPUTS_HAND_LISTED_PUBLICATION, CID_H, A_DATASET)
    assert counts(replace(INPUTS_HAND_LISTED_PUBLICATION, verifiers=frozenset({W_SELF, W_A}), pins={CID_A: PIN_A}),
                  CID_H, A_DATASET)


def test_a_carriers_own_record_counts_only_when_accepted_and_origin_confirmed():
    accepted = replace(INPUTS_ACCEPT_A_AND_PIN_A, verifiers=frozenset({W_SELF, W_A, W_B}))
    assert counts(accepted, CID_A, A_ASSESSMENT)
    assert counts(accepted, CID_B, B_OWN_ASSESSMENT)
    assert not counts(INPUTS_ACCEPT_A_AND_PIN_A, CID_B, B_OWN_ASSESSMENT)  # B's world is not accepted
    unconfirmed = replace(accepted, bindings={W_A: BIND_A, W_B: binding(W_B, LOC_B, confirmed=False)})
    assert not counts(unconfirmed, CID_B, B_OWN_ASSESSMENT)
    elsewhere = replace(accepted, bindings={W_A: BIND_A, W_B: binding(W_B, "https://remote.test/other")})
    assert not counts(elsewhere, CID_B, B_OWN_ASSESSMENT)  # the pin's source is not a bound location
    catalogued = replace(accepted, pins={CID_A: PIN_A, CID_B: pin(CID_B, W_B, MARKER_B, LOC_B,
                                                                  source=PinSource("catalog", "artifact-cat"))})
    assert not counts(catalogued, CID_B, B_OWN_ASSESSMENT)
    unpinned = replace(accepted, pins={CID_A: PIN_A})
    assert not counts(unpinned, CID_B, B_OWN_ASSESSMENT)


def test_a_carried_record_is_decided_by_its_origin_even_in_an_accepted_confirmed_carrier():
    # INPUTS_ACCEPT_B: B origin-confirmed and accepted; A unaccepted. B carries A's assessment.
    assert counts(INPUTS_ACCEPT_B, CID_B, B_OWN_ASSESSMENT)
    assert not counts(INPUTS_ACCEPT_B, CID_B, A_ASSESSMENT)
    # A pinned and origin-confirmed but still unaccepted: not counted.
    assert not counts(replace(INPUTS_ACCEPT_B, pins={CID_A: PIN_A, CID_B: PIN_B}), CID_B, A_ASSESSMENT)
    assert counts(INPUTS_ACCEPT_A_AND_PIN_A, CID_B, A_ASSESSMENT)
    # Accepted A, but its pin is not origin-confirmed: the carrier's word is not taken.
    assert not counts(replace(INPUTS_ACCEPT_A_AND_PIN_A, bindings={W_A: binding(W_A, LOC_A, confirmed=False),
                                                                   W_B: BIND_B}), CID_B, A_ASSESSMENT)
    # Accepted and confirmed A, but A's publication is not mounted: nothing shows A holds the record.
    assert not counts(replace(INPUTS_ACCEPT_A_AND_PIN_A, carriers={CID_B: CARRIER_B}), CID_B, A_ASSESSMENT)


def test_a_pinned_carriers_record_outside_its_selection_never_counts():
    accepted = replace(INPUTS_ACCEPT_B, verifiers=frozenset({W_SELF, W_B}))
    assert counts(accepted, CID_B, B_OWN_ASSESSMENT)
    assert not counts(accepted, CID_B, "assessment:unselected")
    # Branch 4 alike: our own publication adopted back vouches only for what its marker selects.
    assert not counts(INPUTS_ADOPTED_BACK, CID_BACK, "assessment:unselected")


def test_a_carrier_whose_marker_is_not_the_pinned_marker_never_counts_as_its_own():
    forged = replace(INPUTS_ACCEPT_B, carriers={CID_A: CARRIER_A, CID_B: replace(CARRIER_B, marker="marker-forged")})
    assert not counts(forged, CID_B, B_OWN_ASSESSMENT)
    back = replace(INPUTS_ADOPTED_BACK, carriers={CID_A: CARRIER_A,
                                                  CID_BACK: replace(CARRIER_BACK, marker="marker-forged")},
                   own_bindings=frozenset({(CID_BACK, "marker-forged", "artifact-back")}))
    assert not counts(back, CID_BACK, OWN_ASSESSMENT)


def test_an_attribution_naming_an_intermediary_never_counts():
    """B attributes X to A, but A holds X only as a record it carries from C: the named origin must hold it as its
    own, as `counts(A, X)` would require."""
    cid_c, carried = "7" * 32, "assessment:c1"
    a_carrying = replace(CARRIER_A, selection=CARRIER_A.selection | {carried},
                         attributions={carried: (cid_c, "marker-c")})
    b_naming_a = replace(CARRIER_B, selection=CARRIER_B.selection | {carried},
                         attributions={**CARRIER_B.attributions, carried: (CID_A, MARKER_A)})
    inputs = replace(INPUTS_ACCEPT_A_AND_PIN_A, carriers={CID_A: a_carrying, CID_B: b_naming_a})
    assert not counts(inputs, CID_A, carried)
    assert not counts(inputs, CID_B, carried)
    assert counts(inputs, CID_B, A_ASSESSMENT)


def test_a_forged_attribution_to_a_record_the_origin_does_not_hold_never_counts():
    # carrier B attributes "assessment:invented" to (CID_A, MARKER_A); A's selection lacks it
    assert not counts(INPUTS_ACCEPT_A_AND_PIN_A, CID_B, "assessment:invented")
    # Even with B accepted and confirmed: the Carried branch decides, never the carrier's own standing.
    assert not counts(replace(INPUTS_ACCEPT_A_AND_PIN_A, verifiers=frozenset({W_SELF, W_A, W_B})),
                      CID_B, "assessment:invented")


def test_an_attribution_naming_another_marker_of_the_origin_never_counts():
    stale = replace(CARRIER_B, attributions={A_ASSESSMENT: (CID_A, MARKER_A_OLD)})
    inputs = replace(INPUTS_ACCEPT_A_AND_PIN_A, carriers={CID_A: CARRIER_A, CID_B: stale})
    assert PIN_A.marker != MARKER_A_OLD
    assert not counts(inputs, CID_B, A_ASSESSMENT)


PIN_BACK = replace(pin(CID_BACK, W_SELF, MARKER_BACK, LOC_BACK), artifact="artifact-back")
# Our own publication adopted back: our assessment, and A's assessment we had carried, attributed to A.
CARRIER_BACK = Carrier(CID_BACK, W_SELF, MARKER_BACK, frozenset({OWN_ASSESSMENT, A_ASSESSMENT}),
                       {A_ASSESSMENT: (CID_A, MARKER_A)})
INPUTS_ADOPTED_BACK = replace(
    INPUTS_EMPTY, pins={CID_A: PIN_A, CID_BACK: PIN_BACK}, bindings={W_A: BIND_A},
    own_bindings=frozenset({(CID_BACK, MARKER_BACK, "artifact-back")}),
    carriers={CID_A: CARRIER_A, CID_BACK: CARRIER_BACK})


def test_own_records_adopted_back_count_through_the_binding():
    assert counts(INPUTS_ADOPTED_BACK, CID_BACK, OWN_ASSESSMENT)
    # Foreign attribution survives re-adoption: A's assessment does not count under accept = [].
    assert not counts(INPUTS_ADOPTED_BACK, CID_BACK, A_ASSESSMENT)
    # A binding naming another artifact is not this publication.
    other = replace(INPUTS_ADOPTED_BACK, own_bindings=frozenset({(CID_BACK, MARKER_BACK, "artifact-other")}))
    assert not counts(other, CID_BACK, OWN_ASSESSMENT)


def test_a_marker_merely_claiming_our_world_never_takes_the_own_branch():
    claiming = Carrier(CID_FAKE, W_SELF, MARKER_FAKE, frozenset({"assessment:fake"}), {})
    inputs = replace(INPUTS_EMPTY, pins={CID_FAKE: pin(CID_FAKE, W_SELF, MARKER_FAKE, LOC_FAKE)},
                     carriers={CID_FAKE: claiming})
    assert W_SELF in inputs.verifiers
    assert not counts(inputs, CID_FAKE, "assessment:fake")


def test_statement_is_canonical_json_and_encodes():
    text = statement(INPUTS_ACCEPT_A_AND_PIN_A)
    decoded = json.loads(text)
    assert text == json.dumps(decoded, sort_keys=True, separators=(",", ":"))
    assert decoded["policy"] == "science.accept.v1"
    assert decoded["verifiers"] == sorted({W_SELF, W_A})
    assert decoded["own_roots"] == [CID_SELF, CID_LOCAL]
    assert decoded["pins"] == [
        {"corpus": CID_A, "world": W_A, "marker": MARKER_A, "source": f"provider:{LOC_A}", "confirmed": True,
         "state": "mounted"},
        {"corpus": CID_B, "world": W_B, "marker": MARKER_B, "source": f"provider:{LOC_B}", "confirmed": True,
         "state": "mounted"},
    ]
    assert decoded["own_bindings"] == []
    assert decoded["carriers"] == [
        {"corpus": CID_A, "world": W_A, "marker": MARKER_A, "selected": 2, "attributed": 0},
        {"corpus": CID_B, "world": W_B, "marker": MARKER_B, "selected": 3, "attributed": 2},
    ]
    v1.encode(text)
    AcceptancePolicy(counts=lambda corpus_id, address: True, statement=text)
    # Deterministic for a context: insertion order never reaches it; a different policy is a different statement.
    reordered = replace(INPUTS_ACCEPT_A_AND_PIN_A, pins={CID_B: PIN_B, CID_A: PIN_A},
                        carriers={CID_B: CARRIER_B, CID_A: CARRIER_A})
    assert statement(reordered) == text
    assert statement(INPUTS_ACCEPT_B) != text
    assert json.loads(statement(INPUTS_ADOPTED_BACK))["own_bindings"] == [[CID_BACK, MARKER_BACK, "artifact-back"]]


def test_accept_naming_an_unpinned_world_changes_nothing(reopened):
    """Review Focus 5: belief answers, the context carries the policy, nothing extra is excluded."""
    proposition, unpinned = a_identity(reopened.a)["proposition"], "e" * 32
    answer = ReadContext.open(reopened.b).evaluate(proposition)
    widened = ReadContext.open(replace(reopened.b, accept=(unpinned,))).evaluate(proposition)
    assert (type(widened), widened.reason) == (type(answer), answer.reason)
    assert unpinned in json.loads(widened.acceptance.statement)["verifiers"]
    assert widened.acceptance.complete and answer.acceptance.complete
    assert widened.acceptance.excluded == answer.acceptance.excluded != ()


def test_next_counts_only_the_assessments_the_policy_accepts(reopened):
    """`next` reads the policy as belief does: an excluded assessment leaves its proposition unassessed."""
    ids = a_identity(reopened.a)
    assert classify(ReadContext.open(reopened.b), ids["proposition"]) in ("ready", "not-ready")
    accepted = replace(reopened.b, accept=(ids["world"],))
    assert classify(ReadContext.open(accepted), ids["proposition"]) == "assessed-not-admitted"


def _with_extra_root(cfg, root):
    return replace(cfg, world=WorldConfig(cfg.world.world_root, cfg.world.world_id,
                                          tuple(sorted((*cfg.world.corpus_roots, root)))))


def _copy_corpus(source, target):
    """A byte copy of the corpus at `source`, with its metadata sibling: one corpus id at two roots."""
    shutil.copytree(source, target)
    if metadata_root_for(source).exists():
        shutil.copytree(metadata_root_for(source), metadata_root_for(target))


def test_a_hand_listed_root_claiming_the_adopted_corpus_id_refuses(reopened):
    cid = a_identity(reopened.a)["corpus_id"]
    adopted = SharingRegistry(reopened.b.sharing_root).root_for(cid).resolve()
    claimant = reopened.b.world.world_root.parent / "claimant" / cid
    _copy_corpus(adopted, claimant)
    with pytest.raises(Refused) as caught:
        acceptance_inputs(ReadContext.open(_with_extra_root(reopened.b, claimant)))
    refusal = caught.value.refusal
    assert refusal.code == "invalid-input"
    assert cid in refusal.message and str(adopted) in refusal.message and str(claimant) in refusal.message


def test_two_markerless_unpinned_roots_sharing_an_id_stay_own(reopened):
    own = reopened.b.write_root
    twin = reopened.b.world.world_root.parent / "twin" / "corpus"
    _copy_corpus(own, twin)
    inputs = acceptance_inputs(ReadContext.open(_with_extra_root(reopened.b, twin)))
    assert corpus_id_at(own) in inputs.own_roots
