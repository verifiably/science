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
                               "facets": ["testing/gene-axis=axis:rows,namespace:HGNC"]})
    assert "[dataset] dataset:sha256:" in out.text
    view = ctx.write_view()
    node = next(n for n in view.iter_stored() if n.kind == "dataset" and n.title == "expression")
    assert ctx.is_held(node)
    from beliefs import stored
    assert stored.is_empirical_observation(node)


def test_non_regular_path_refuses_before_any_act(rig, tmp_path):
    d, ctx = rig
    with pytest.raises(Refused) as caught:
        d.invoke("dataset", {"path": str(tmp_path), "title": "dir"})
    assert caught.value.refusal.code == "invalid-input"
    view = ctx.write_view()
    assert not any(n.kind == "dataset" and n.title == "dir" for n in view.iter_stored())


def test_same_bytes_twice_refuse_naming_the_record(rig, tmp_path):
    d, _ = rig
    data = tmp_path / "a.txt"
    data.write_bytes(b"same\n")
    first = d.invoke("dataset", {"path": str(data), "title": "one"})
    with pytest.raises(Refused) as caught:
        d.invoke("dataset", {"path": str(data), "title": "two"})
    assert "dataset:sha256:" in caught.value.refusal.message
    record = caught.value.refusal.message.split("already declared as ")[1].split()[0]
    assert record.startswith("dataset:sha256:") and record in first.text


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
    view = ctx.write_view()
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
    view = ctx.write_view()
    assert not any(n.kind == "dataset" and n.title == "l" for n in view.iter_stored())


def test_attested_by_is_the_session_actor(rig, tmp_path):
    d, ctx = rig
    data = tmp_path / "e.txt"
    data.write_bytes(b"E\n")
    d.invoke("dataset", {"path": str(data), "title": "e", "locator": "accession:X"})
    view = ctx.write_view()
    node = next(n for n in view.iter_stored() if n.kind == "dataset" and n.title == "e")
    facet = node.facets["empirical-observation"]
    assert facet["attested_by"].startswith("session:")


def test_bytes_held_with_no_record_are_re_held_superseding_the_earlier_observation(rig, tmp_path):
    """The crash-recovery path: the store write and its Found
    observation landed, the record did not. `dataset` re-holds the same bytes at
    the same content-derived location, the earlier observation standing, and
    mints the record; the reduction shows one head for the address (review
    finding 5)."""
    from hashlib import sha256
    from beliefs import stored
    from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
    from beliefs.holdings.boundary import ActContext, write
    from beliefs.holdings.records import StoreLocator
    from beliefs.root import holdings_seam
    from helpers.world import FIXTURE_AUTHORITY
    d, ctx = rig
    content = b"orphaned\n"
    data = tmp_path / "orphan.txt"
    data.write_bytes(content)
    digest = "sha256:" + sha256(content).hexdigest()
    (root,) = ctx.config.world.corpus_roots
    act = ActContext(root, ctx.config.store_root, "fixture", "fixture/hold.v1", FIXTURE_AUTHORITY,
                     holdings_seam(), profile=ctx.config.profile)
    write(act, StoreLocator(ctx.store_id(), f"{digest.removeprefix('sha256:')}/orphan.txt"), content, expected=digest)
    address = dataset_address(DatasetDeclaration(resources=(ResourceDeclaration(name="orphan.txt", digest=digest),)))
    view = ctx.write_view()
    assert not view.holds(address)
    d.invoke("dataset", {"path": str(data), "title": "orphan"})
    view = ctx.write_view()
    assert view.holds(address) and ctx.is_held(view.get(address))
    assert len(ctx.observations()[address]) == 1
    relative = f"{digest.removeprefix('sha256:')}/orphan.txt"
    at_location = [stored.holdings_observation_value(n) for n in view.iter_stored()
                   if n.kind == "holdings-observation"
                   and stored.holdings_observation_value(n).location.relative_path == relative]
    assert len(at_location) == 2 and any(o.supersedes for o in at_location)


def test_a_url_observation_in_the_write_root_does_not_block_holding_bytes(rig, tmp_path, monkeypatch):
    """`dataset` chooses the observations its store write supersedes by the whole store locator; a URL observation
    has no store path and is not one of them."""
    from helpers.world import record_url_observation
    d, ctx = rig
    content = b"gene\tv\nPHF19\t1\n"
    (root,) = ctx.config.world.corpus_roots
    record_url_observation(root, ctx.config.store_root, ctx.config.profile, content, "https://data.test/m.txt",
                           tmp_path / "look", monkeypatch)
    data = tmp_path / "matrix.txt"
    data.write_bytes(content)
    assert "[dataset] dataset:sha256:" in d.invoke("dataset", {"path": str(data), "title": "expression"}).text


def test_a_store_refused_write_closes_refused_and_replays(certified_work, tmp_path):
    """A read-only-serviceable store refuses the holdings write after its intent
    is appended. No act was published, so the invocation closes refused with
    the kernel's kind, and a retry under the same id replays that refusal
    rather than finding the invocation open."""
    from dataclasses import replace

    from beliefs.root import (LifecycleState, export_head_artifact, open_world, read_lifecycle_state,
                              replicate_root, restore_root, store_identity)
    from beliefs.world.anchors import StoreSubject
    from beliefs.world.verify import ArtifactCarrier, ObserverSet
    from helpers.world import FIXTURE_AUTHORITY

    cfg = build_belief_world(certified_work)
    subject = StoreSubject(store_identity(cfg.store_root))
    artifact = export_head_artifact(open_world(cfg.world, authority=FIXTURE_AUTHORITY), subject,
                                    store_root=cfg.store_root)
    restored = certified_work / "restored"
    replicate_root(cfg.store_root, restored, authority=FIXTURE_AUTHORITY)
    report = restore_root(restored, subject, ObserverSet((ArtifactCarrier.from_bytes(artifact),)),
                          authority=FIXTURE_AUTHORITY)
    assert report.outcome == "validated"
    assert read_lifecycle_state(restored) is LifecycleState.READ_ONLY_SERVICEABLE
    data = tmp_path / "matrix.txt"
    data.write_bytes(b"gene\tv\nPHF19\t1\n")
    payload = {"path": str(data), "title": "expression"}
    with open_rig(replace(cfg, store_root=restored), ("dataset",)) as (d, ctx):
        with pytest.raises(Refused) as first:
            d.invoke("dataset", payload, invocation_id="S" * 8)
        assert first.value.refusal.code == "kernel-refused"
        assert first.value.refusal.data["kind"] == "StoreWriteRefused"
        with pytest.raises(Refused) as again:
            d.invoke("dataset", payload, invocation_id="S" * 8)
        assert again.value.refusal == first.value.refusal
        view = ctx.write_view()
        assert not any(n.kind == "dataset" and n.title == "expression" for n in view.iter_stored())


def test_a_kernel_refused_record_after_held_bytes_closes_done_with_the_holding(rig, tmp_path, monkeypatch):
    """`dataset` acts twice: the holdings write publishes an observation, then
    `writer.add` mints the record. When the kernel refuses the second act, the
    published observation still committed, so the invocation closes done with
    it (an internal error, not a refusal that would drop the act), and a retry
    under the same id replays that act instead of re-running the handler."""
    from beliefs.errors import WriteRefused
    from beliefs.session.writer import ScopedWriter

    from science.dispatch import HandlerContractViolation

    def refused_add(self, node):
        raise WriteRefused(f"{node.id}: refused by the kernel")

    monkeypatch.setattr(ScopedWriter, "add", refused_add)
    d, ctx = rig
    data = tmp_path / "matrix.txt"
    data.write_bytes(b"gene\tv\nPHF19\t1\n")
    payload = {"path": str(data), "title": "expression"}
    with pytest.raises(HandlerContractViolation, match="kernel-refused"):
        d.invoke("dataset", payload, invocation_id="D" * 8)
    (stored, act) = d._session.invocation_acts("D" * 8)
    assert (stored.corpus, stored.intent, stored.record_ids) == (d._session.store_id, act.intent, ())
    assert act.corpus == d._session.corpus_id
    out = d.invoke("dataset", payload, invocation_id="D" * 8)
    assert "holdings-observation" in out.text
    view = ctx.write_view()
    assert not any(n.kind == "dataset" and n.title == "expression" for n in view.iter_stored())


def test_dataset_directory_auto_discovers_all_regular_files_including_datapackage_json(rig, tmp_path):
    from beliefs import stored

    d, ctx = rig
    pkg_dir = tmp_path / "pkg"
    (pkg_dir / "tables").mkdir(parents=True)
    files = {
        "datapackage.json": b'{"name": "gse24080"}\n',
        "tables/clinical.tsv": b"patient\tage\nP1\t62\n",
        "tables/expression.tsv": b"gene\tP1\nPHF19\t4.2\n",
    }
    for rel, content in files.items():
        (pkg_dir / rel).write_bytes(content)

    out = d.invoke("dataset", {"path": str(pkg_dir), "title": "GSE24080 curated"})
    assert "[dataset] dataset:sha256:" in out.text
    view = ctx.write_view()
    node = next(n for n in view.iter_stored() if n.kind == "dataset" and n.title == "GSE24080 curated")
    decl = stored.dataset_declaration(node)
    assert tuple(r.name for r in decl.resources) == (
        "datapackage.json",
        "tables/clinical.tsv",
        "tables/expression.tsv",
    )
    assert ctx.is_held(node)
    resolved = ctx.held_resources(node.id)
    assert set(resolved) == set(files)
    for rel, content in files.items():
        assert resolved[rel].read_bytes() == content


def test_dataset_directory_with_explicit_resources_admits_named_subset(rig, tmp_path):
    from beliefs import stored

    d, ctx = rig
    pkg_dir = tmp_path / "pkg_subset"
    (pkg_dir / "tables").mkdir(parents=True)
    (pkg_dir / "datapackage.json").write_bytes(b'{"name": "gse24080"}\n')
    (pkg_dir / "tables" / "expression.tsv").write_bytes(b"gene\tP1\nPHF19\t4.2\n")
    (pkg_dir / "tables" / "clinical.tsv").write_bytes(b"patient\tage\nP1\t62\n")

    out = d.invoke(
        "dataset",
        {
            "path": str(pkg_dir),
            "title": "GSE24080 tables only",
            "resources": ["tables/expression.tsv", "tables/clinical.tsv"],
        },
    )
    assert "[dataset] dataset:sha256:" in out.text
    view = ctx.write_view()
    node = next(n for n in view.iter_stored() if n.kind == "dataset" and n.title == "GSE24080 tables only")
    decl = stored.dataset_declaration(node)
    assert tuple(r.name for r in decl.resources) == (
        "tables/clinical.tsv",
        "tables/expression.tsv",
    )
    assert ctx.is_held(node)
    resolved = ctx.held_resources(node.id)
    assert set(resolved) == {"tables/clinical.tsv", "tables/expression.tsv"}


def test_dataset_directory_refuses_symlinks_scratch_sigils_empty_and_escaping_resources(rig, tmp_path):
    d, ctx = rig
    before_nodes = {n.id for n in ctx.write_view().iter_stored()}
    before_store_entries = set(ctx.config.store_root.iterdir())

    # 1. Empty directory
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    with pytest.raises(Refused) as caught:
        d.invoke("dataset", {"path": str(empty_dir), "title": "empty"})
    assert caught.value.refusal.code == "invalid-input"

    # 2. Directory with a symlink
    sym_dir = tmp_path / "sym_dir"
    sym_dir.mkdir()
    outside = tmp_path / "outside.tsv"
    outside.write_bytes(b"x\n")
    (sym_dir / "good.tsv").write_bytes(b"y\n")
    (sym_dir / "link.tsv").symlink_to(outside)
    with pytest.raises(Refused) as caught:
        d.invoke("dataset", {"path": str(sym_dir), "title": "sym"})
    assert caught.value.refusal.code == "invalid-input"

    # 3. Directory with .#~scratch file
    scratch_dir = tmp_path / "scratch_dir"
    scratch_dir.mkdir()
    (scratch_dir / ".#~scratch").write_bytes(b"s\n")
    with pytest.raises(Refused) as caught:
        d.invoke("dataset", {"path": str(scratch_dir), "title": "scratch"})
    assert caught.value.refusal.code == "invalid-input"

    # 4. --resources ["../escape.tsv"]
    valid_dir = tmp_path / "valid_dir"
    valid_dir.mkdir()
    (valid_dir / "dup.tsv").write_bytes(b"d\n")
    with pytest.raises(Refused) as caught:
        d.invoke(
            "dataset",
            {"path": str(valid_dir), "title": "escape", "resources": ["../outside.tsv"]},
        )
    assert caught.value.refusal.code == "invalid-input"

    # 5. --resources ["dup.tsv", "dup.tsv"]
    with pytest.raises(Refused) as caught:
        d.invoke(
            "dataset",
            {"path": str(valid_dir), "title": "dup", "resources": ["dup.tsv", "dup.tsv"]},
        )
    assert caught.value.refusal.code == "invalid-input"

    # 6. --path <file> --resources [...]
    with pytest.raises(Refused) as caught:
        d.invoke(
            "dataset",
            {"path": str(outside), "title": "file-with-resources", "resources": ["outside.tsv"]},
        )
    assert caught.value.refusal.code == "invalid-input"

    assert {n.id for n in ctx.write_view().iter_stored()} == before_nodes
    assert set(ctx.config.store_root.iterdir()) == before_store_entries


def test_dataset_reads_each_admitted_file_exactly_once(rig, tmp_path, monkeypatch):
    from hashlib import sha256
    from pathlib import Path
    from beliefs import stored

    d, ctx = rig
    single_file = tmp_path / "single.tsv"
    single_bytes = b"gene\tval\nPHF19\t1\n"
    single_file.write_bytes(single_bytes)

    pkg_dir = tmp_path / "pkg_once"
    (pkg_dir / "tables").mkdir(parents=True)
    file_a = pkg_dir / "datapackage.json"
    bytes_a = b'{"name": "once"}\n'
    file_a.write_bytes(bytes_a)
    file_b = pkg_dir / "tables" / "data.tsv"
    bytes_b = b"id\tx\n1\t2\n"
    file_b.write_bytes(bytes_b)

    tracked = {single_file.resolve(), file_a.resolve(), file_b.resolve()}
    counts: dict[Path, int] = {p: 0 for p in tracked}
    orig_read_bytes = Path.read_bytes

    def counting_read_bytes(self: Path) -> bytes:
        resolved = self.resolve()
        data = orig_read_bytes(self)
        if resolved in counts:
            counts[resolved] += 1
            if counts[resolved] > 1:
                return data + b"MUTATED"
        return data

    monkeypatch.setattr(Path, "read_bytes", counting_read_bytes)

    d.invoke("dataset", {"path": str(single_file), "title": "single once"})
    d.invoke("dataset", {"path": str(pkg_dir), "title": "pkg once"})

    assert counts == {p: 1 for p in tracked}
    view = ctx.write_view()
    single_node = next(n for n in view.iter_stored() if n.kind == "dataset" and n.title == "single once")
    (single_res,) = stored.dataset_declaration(single_node).resources
    assert single_res.digest == "sha256:" + sha256(single_bytes).hexdigest()
    assert orig_read_bytes(ctx.held_path(single_node.id)) == single_bytes

    pkg_node = next(n for n in view.iter_stored() if n.kind == "dataset" and n.title == "pkg once")
    pkg_decl = stored.dataset_declaration(pkg_node)
    expected_digests = {
        "datapackage.json": "sha256:" + sha256(bytes_a).hexdigest(),
        "tables/data.tsv": "sha256:" + sha256(bytes_b).hexdigest(),
    }
    assert {r.name: r.digest for r in pkg_decl.resources} == expected_digests
    held_map = ctx.held_resources(pkg_node.id)
    assert orig_read_bytes(held_map["datapackage.json"]) == bytes_a
    assert orig_read_bytes(held_map["tables/data.tsv"]) == bytes_b

