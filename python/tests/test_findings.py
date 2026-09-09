import io

from beliefs.corpus import Finding


def test_findings_exact_wire_and_flush():
    """Preserve fields and order, compact sorted JSON, newlines, and one flush."""
    from science.findings import report_findings

    calls = []

    class RecordingStream(io.StringIO):
        def write(self, text):
            calls.append(("write", text))
            return super().write(text)

        def flush(self):
            calls.append(("flush",))
            super().flush()

    findings = (
        Finding("warning", "session-unclosed", "peer", "", "no close"),
        Finding("error", "session-ledger-malformed", "other", "bad\nline", "unreadable"),
    )
    expected = (
        '{"code":"session-unclosed","detail":"","message":"no close",'
        '"ref":"peer","reported_by":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","severity":"warning"}\n'
        '{"code":"session-ledger-malformed","detail":"bad\\nline","message":"unreadable",'
        '"ref":"other","reported_by":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","severity":"error"}\n'
    )
    stream = RecordingStream()
    report_findings(findings, reported_by="a" * 32, stream=stream)
    assert stream.getvalue() == expected
    assert calls == [("write", line) for line in expected.splitlines(keepends=True)] + [("flush",)]

    stream = RecordingStream()
    calls.clear()
    report_findings((), reported_by="a" * 32, stream=stream)
    assert stream.getvalue() == ""
    assert calls == []

    class WriteOnly:
        def write(self, text):
            calls.append(("write", text))

    report_findings(findings, reported_by="a" * 32, stream=WriteOnly())
    assert calls == [("write", line) for line in expected.splitlines(keepends=True)]
