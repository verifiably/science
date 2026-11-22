"""The file and supervisor report carry exactly the same sealed evidence."""
from pathlib import Path

from beliefs.session.writer import ChainTip, SealedTips


def test_shared_seal_bytes_preserve_both_tips_even_when_basis_is_unavailable():
    from science.run_endpoint.control import seal_evidence, wire

    tips = SealedTips(ChainTip("a"*32, "1"*64, "1"*64), ChainTip("b"*32, "2"*64, "6"*64))
    document, report = seal_evidence("eof", tips, None)
    samples = Path(__file__).parents[1] / "fixtures/run_endpoint"
    assert wire(document) == (samples / "seal.json").read_bytes()
    assert wire(report) == (samples / "sealed.control.v1.jsonl").read_bytes()
