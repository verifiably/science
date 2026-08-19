"""The composition root's portable half: the metadata rule, the genesis
constant, and the write-intent encoding.

The **durable** half — registering a real root through the engine — is not here
and cannot be: it runs only on a certified volume, so it lives in the cut-4
acceptance command, which errors rather than skips when the tuple is not
certified. A test that quietly passed off a certified volume would be reporting
green for a guarantee it never exercised.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from nodes.core.write_plan import CreateOp, DeleteOp, ReplaceOp

from science import root
from science.errors import CorpusRootRefused
from science.identity import v1


class TestTheMetadataRule:
    def test_the_metadata_root_is_the_sibling_of_the_corpus_root(self):
        assert root.metadata_root_for(Path("/corpora/mm30")) == Path("/corpora/mm30.metadata")

    def test_the_sibling_sits_outside_the_corpus_root(self):
        # A metadata store *inside* the corpus would be swept up by every copy
        # of it, which is exactly what makes the two cold-arrival cases
        # indistinguishable.
        corpus = Path("/corpora/mm30")
        assert corpus not in root.metadata_root_for(corpus).parents


class TestTheGenesisPayload:
    def test_it_is_the_canonical_bytes_of_the_constant_domain_object(self):
        assert root.GENESIS_PAYLOAD == v1.encode({"domain": "science.corpus-root.v1"})

    def test_it_carries_no_corpus_identity(self):
        # Corpus manifests and `corpus_id` minting are unbuilt; identity binds
        # through a later chain entry, never by rewriting genesis.
        assert root.GENESIS_PAYLOAD == b'{"domain":"science.corpus-root.v1"}'


class TestTheInitActRefusesANonDirectory:
    def test_a_file_at_the_corpus_root_path_is_refused(self, tmp_path):
        occupied = tmp_path / "corpus"
        occupied.write_text("not a corpus", encoding="utf-8")
        with pytest.raises(CorpusRootRefused):
            root.init_corpus_root(occupied)

    def test_a_symlink_root_is_registered_under_its_resolved_path(self, tmp_path, monkeypatch):
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        link.symlink_to(real, target_is_directory=True)
        calls = []
        monkeypatch.setattr(root, "register_root", lambda *args: calls.append(args))

        root.init_corpus_root(link)

        _, project_root, metadata_root, *_ = calls[0]
        assert project_root == str(real.resolve())
        assert metadata_root == str(real.resolve()) + ".metadata"


class TestTheCompositionRoot:
    def test_a_symlink_root_binds_every_writer_component_to_the_resolved_path(self, tmp_path):
        real = tmp_path / "real"
        real.mkdir()
        link = tmp_path / "link"
        link.symlink_to(real, target_is_directory=True)

        writer = root.open_corpus(link)
        executor = writer._corpus.executor
        port = writer._operation_port
        assert isinstance(executor, root.DurableExecutor)
        assert isinstance(port, root.DurableOperationPort)

        assert writer._corpus.store.root == real.resolve()
        assert executor.root == real.resolve()
        assert executor._metadata_root == real.resolve().with_name("real.metadata")
        assert port.root == real.resolve()
        assert port._metadata_root == real.resolve().with_name("real.metadata")


class TestTheWriteIntentEncoding:
    def test_each_operation_kind_projects_its_own_discriminated_shape(self):
        plan = [
            CreateOp(path="proposition/p.md", content=b"created"),
            ReplaceOp(path="run/r.md", content=b"replaced", expected_digest="ab" * 32),
            DeleteOp(path="dataset/d.md", expected_digest="cd" * 32),
        ]
        assert root.write_intent_projection(plan) == [
            {
                "op": "create",
                "path": "proposition/p.md",
                "content_sha256": "406effb1e9c59672c66a598c2b21e331b23b16c54024e96d6df3e7c173549791",
            },
            {
                "op": "replace",
                "path": "run/r.md",
                "expected_digest": "ab" * 32,
                "content_sha256": "6c1aa50442a93e42c0eb2907cf4e017cd19547891fa190f3ea473582b0479290",
            },
            {"op": "delete", "path": "dataset/d.md", "expected_digest": "cd" * 32},
        ]

    def test_a_create_omits_the_expected_digest_and_a_delete_the_content(self):
        # Omission, not a placeholder: the identity encoding refuses `null`, and
        # a present-and-empty stand-in would collide with a genuinely empty one.
        create, delete = root.write_intent_projection(
            [CreateOp(path="a.md", content=b""), DeleteOp(path="b.md", expected_digest="ef" * 32)]
        )
        assert "expected_digest" not in create
        assert "content_sha256" not in delete

    def test_the_digest_carries_the_mandatory_sha256_prefix(self):
        plan = [CreateOp(path="a.md", content=b"x")]
        assert root.write_intent_digest(plan) == "sha256:" + v1.digest(
            "science.corpus-write-intent.v1", root.write_intent_projection(plan)
        )

    def test_the_intent_is_domain_separated_from_a_bare_projection_digest(self):
        plan = [CreateOp(path="a.md", content=b"x")]
        projection = root.write_intent_projection(plan)
        assert root.write_intent_digest(plan)[len("sha256:") :] != v1.encode(projection).hex()

    def test_reordering_two_operations_moves_the_intent(self):
        first = CreateOp(path="a.md", content=b"x")
        second = CreateOp(path="b.md", content=b"y")
        assert root.write_intent_digest([first, second]) != root.write_intent_digest([second, first])

    def test_the_same_path_written_with_different_content_moves_the_intent(self):
        assert root.write_intent_digest([CreateOp(path="a.md", content=b"x")]) != root.write_intent_digest(
            [CreateOp(path="a.md", content=b"y")]
        )

    def test_an_empty_plan_projects_nothing(self):
        assert root.write_intent_projection([]) == []
