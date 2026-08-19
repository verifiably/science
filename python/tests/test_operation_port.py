"""The engine-agnostic operation port and its durable composition-root binding."""

from __future__ import annotations

from typing import ClassVar

import pytest
from atoms.chain.errors import ChainStateInvalid
from atoms.core.errors import (
    CapabilityUnavailable,
    PreconditionRefused,
    ProjectApprovalRefused,
    ProtocolError,
    SpecValidationError,
    TransactionHalted,
)
from atoms.fs.platform import select_backend
from atoms.store.errors import MetadataStoreInvalid
from nodes.core.errors import ExecutionError
from nodes.core.write_plan import CreateOp, WritePlan

from science import root as science_root
from science.corpus import CorpusWriter, OperationPort
from science.root import PRODUCTION_STORAGE, DurableOperationPort, open_corpus

FULFILLS = "ab" * 32
PAYLOAD = b"\x00opaque intent\xff"


class Recorder:
    def __init__(self, _root) -> None:
        pass

    def execute(self, plan: WritePlan) -> None:
        pass


class FakePort:
    intents: ClassVar[list[bytes]] = []
    fulfilling: ClassVar[list[tuple[WritePlan, str]]] = []

    def append_intent(self, payload: bytes) -> str:
        self.intents.append(payload)
        return FULFILLS

    def execute_fulfilling(self, plan: WritePlan, fulfills: str) -> None:
        self.fulfilling.append((plan, fulfills))


def durable_port(tmp_path) -> DurableOperationPort:
    return DurableOperationPort(
        tmp_path,
        backend=select_backend(),
        storage=PRODUCTION_STORAGE,
        metadata_root=tmp_path.with_name(tmp_path.name + ".metadata"),
    )


class TestTheStructuralPort:
    def test_a_fake_records_the_two_real_boundary_calls(self, tmp_path):
        FakePort.intents = []
        FakePort.fulfilling = []
        port: OperationPort = FakePort()
        writer = CorpusWriter(tmp_path, Recorder, operation_port=port)
        plan = [CreateOp(path="p.md", content=b"record")]

        configured = writer._operation_port
        assert configured is port
        assert configured is not None
        digest = configured.append_intent(PAYLOAD)
        configured.execute_fulfilling(plan, digest)

        assert FakePort.intents == [PAYLOAD]
        assert FakePort.fulfilling == [(plan, FULFILLS)]

    def test_the_port_defaults_to_none_without_changing_portable_construction(self, tmp_path):
        assert CorpusWriter(tmp_path, Recorder)._operation_port is None

    def test_ports_do_not_change_the_stable_shared_executor_factory(self, tmp_path):
        with_port = CorpusWriter(tmp_path, Recorder, operation_port=FakePort())
        without_port = CorpusWriter(tmp_path, Recorder)

        assert with_port._state is without_port._state


class TestTheDurablePort:
    def test_open_corpus_wires_the_durable_port(self, tmp_path):
        assert isinstance(open_corpus(tmp_path)._operation_port, DurableOperationPort)

    def test_append_intent_forwards_the_opaque_payload_unchanged(self, tmp_path, monkeypatch):
        calls: list[tuple] = []

        def capture(backend, project_root, metadata_root, storage, payload):
            calls.append((backend, project_root, metadata_root, storage, payload))
            return FULFILLS

        monkeypatch.setattr(science_root, "append_intent", capture)
        port = durable_port(tmp_path)

        assert port.append_intent(PAYLOAD) == FULFILLS
        backend, project_root, metadata_root, storage, payload = calls[0]
        assert backend is port._backend
        assert project_root == str(tmp_path)
        assert metadata_root == str(tmp_path) + ".metadata"
        assert storage is PRODUCTION_STORAGE
        assert payload is PAYLOAD

    def test_execute_fulfilling_threads_the_exact_digest_into_the_spec(self, tmp_path, monkeypatch):
        submitted = []

        def capture(_backend, _project_root, _metadata_root, _storage, spec, _payloads):
            submitted.append(spec)

        monkeypatch.setattr(science_root, "run_transaction", capture)

        durable_port(tmp_path).execute_fulfilling(
            [CreateOp(path="p.md", content=b"record")],
            FULFILLS,
        )

        assert submitted[0].fulfills == FULFILLS

    @pytest.mark.parametrize(
        ("raised", "applied"),
        [
            (ProjectApprovalRefused("rooted proof"), 0),
            (PreconditionRefused("clean refusal"), 0),
            (CapabilityUnavailable("not certified"), 0),
            (SpecValidationError("engine validation"), None),
            (MetadataStoreInvalid("stop and preserve"), None),
            (ChainStateInvalid("stop and preserve"), None),
            (TransactionHalted("unattributable"), None),
            (ProtocolError("engine contract"), None),
            (RuntimeError("unrecognized"), None),
        ],
    )
    def test_each_append_failure_maps_to_its_arm(self, tmp_path, monkeypatch, raised, applied):
        def fail(*_args, **_kwargs):
            raise raised

        monkeypatch.setattr(science_root, "append_intent", fail)

        with pytest.raises(ExecutionError) as mapped:
            durable_port(tmp_path).append_intent(PAYLOAD)

        assert (mapped.value.index, mapped.value.applied) == (None, applied)
        assert mapped.value.__cause__ is raised
