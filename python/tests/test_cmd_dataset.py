import pytest

from science.refusal import Refused
from helpers.world import build_belief_world, open_rig


@pytest.fixture
def rig(certified_work):
    with open_rig(build_belief_world(certified_work), ("dataset",)) as pair:
        yield pair


def test_dataset_holds_bytes_and_mints_the_record(rig, tmp_path):
    d, ctx = rig
    data = tmp_path / "matrix.txt"
    data.write_bytes(b"gene\tv\nPHF19\t1\n")
    out = d.invoke("dataset", {"path": str(data), "title": "expression", "locator": "accession:GSE1",
                               "facets": ["biology/gene-axis=axis:rows,namespace:HGNC"]})
    assert "[dataset] dataset:sha256:" in out.text
    _, view = ctx.single_view()
    node = next(n for n in view.iter_stored() if n.kind == "dataset" and n.title == "expression")
    assert ctx.is_held(node)
    from beliefs import stored
    assert stored.is_empirical_observation(node)


def test_non_regular_path_refuses_before_any_act(rig, tmp_path):
    d, ctx = rig
    with pytest.raises(Refused) as caught:
        d.invoke("dataset", {"path": str(tmp_path), "title": "dir"})
    assert caught.value.refusal.code == "invalid-input"
    _, view = ctx.single_view()
    assert not any(n.kind == "dataset" and n.title == "dir" for n in view.iter_stored())


def test_same_bytes_twice_refuse_naming_the_record(rig, tmp_path):
    d, _ = rig
    data = tmp_path / "a.txt"
    data.write_bytes(b"same\n")
    first = d.invoke("dataset", {"path": str(data), "title": "one"})
    with pytest.raises(Refused) as caught:
        d.invoke("dataset", {"path": str(data), "title": "two"})
    assert "dataset:sha256:" in caught.value.refusal.message
    assert caught.value.refusal.message.split()[-1] in first.text


def test_two_files_with_one_title_and_basename_land_apart(rig, tmp_path):
    d, ctx = rig
    a, b = tmp_path / "x" / "data.txt", tmp_path / "y" / "data.txt"
    a.parent.mkdir(); b.parent.mkdir()
    a.write_bytes(b"A\n"); b.write_bytes(b"B\n")
    d.invoke("dataset", {"path": str(a), "title": "t"})
    d.invoke("dataset", {"path": str(b), "title": "t"})
    assert len(ctx.observations()) >= 3  # concepts + two held files


def test_malformed_metadata_leaves_no_acts(rig, tmp_path):
    """`oops` is not a facet the profile declares: the refusal comes before
    the holdings write, so neither bytes nor an observation exist afterward."""
    d, ctx = rig
    data = tmp_path / "m.txt"
    data.write_bytes(b"M\n")
    with pytest.raises(Refused) as caught:
        d.invoke("dataset", {"path": str(data), "title": "m", "facets": ["oops=k:v"]}, invocation_id="M" * 8)
    assert caught.value.refusal.code == "invalid-input"
    assert "oops" in caught.value.refusal.message
    from hashlib import sha256
    from beliefs import stored
    digest = sha256(b"M\n").hexdigest()
    assert not (ctx.config.store_root / digest).exists()  # no bytes were written
    _, view = ctx.single_view()
    assert not any(n.kind == "dataset" and n.title == "m" for n in view.iter_stored())
    assert not any(n.kind == "holdings-observation"
                   and stored.holdings_observation_value(n).location.relative_path.startswith(digest)
                   for n in view.iter_stored())


def test_malformed_locator_leaves_no_acts(rig, tmp_path):
    """The empirical-observation payload is validated before the holdings
    write, not by the writer after it."""
    d, ctx = rig
    data = tmp_path / "l.txt"
    data.write_bytes(b"L\n")
    with pytest.raises(Refused) as caught:
        d.invoke("dataset", {"path": str(data), "title": "l", "locator": "not-a-locator"})
    assert caught.value.refusal.code == "invalid-input"
    from hashlib import sha256
    assert not (ctx.config.store_root / sha256(b"L\n").hexdigest()).exists()
    _, view = ctx.single_view()
    assert not any(n.kind == "dataset" and n.title == "l" for n in view.iter_stored())


def test_attested_by_is_the_session_actor(rig, tmp_path):
    d, ctx = rig
    data = tmp_path / "e.txt"
    data.write_bytes(b"E\n")
    d.invoke("dataset", {"path": str(data), "title": "e", "locator": "accession:X"})
    _, view = ctx.single_view()
    node = next(n for n in view.iter_stored() if n.kind == "dataset" and n.title == "e")
    facet = node.facets["empirical-observation"]
    assert facet["attested_by"].startswith("session:")
