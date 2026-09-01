import pytest

from science.cursor import MAX_CURSOR_BYTES, MIN_OUTPUT_BUDGET
from science.render import (
    AuditViolation,
    audit_write_report,
    render_page,
    report_digest,
)
from science.report import Finding, Heading, KeyVals, RecordBlock, Text


def cursor_for(position, digest):
    return f"CUR-{position[0]}-{position[1]}"


def paginate(report, budget, cursor=cursor_for):
    pages, pos = [], (0, 0)
    while pos is not None:
        page = render_page(report, budget=budget, position=pos, cursor_for=cursor)
        pages.append(page)
        pos = page.next_position
    return pages


def test_fits_in_one_page_untruncated():
    report = (Heading("a"), Text("b"))
    page = render_page(report, budget=MIN_OUTPUT_BUDGET, position=(0, 0), cursor_for=cursor_for)
    assert page.next_position is None and "truncated" not in page.text


def test_near_budget_fit_is_not_truncated():
    """A report inside the budget but inside the marker reserve too: still whole."""
    from science.render import render_full

    report = (Text("x" * (MIN_OUTPUT_BUDGET * 2)),)
    exact = len(render_full(report).encode())
    page = render_page(report, budget=exact, position=(0, 0), cursor_for=cursor_for)
    assert page.next_position is None and "truncated" not in page.text
    assert len(page.text.encode()) == exact


def test_budget_enforced_and_pages_cover_everything():
    report = tuple(Text(f"line {i} " + "x" * 40) for i in range(50))
    budget = MIN_OUTPUT_BUDGET
    pages = paginate(report, budget)
    assert len(pages) > 1
    assert all(len(p.text.encode()) <= budget for p in pages)
    joined = "".join(p.text.split("\n… truncated")[0] for p in pages)
    full = render_page(report, budget=10**9, position=(0, 0), cursor_for=cursor_for).text
    assert joined == full


def test_oversized_single_block_still_progresses():
    report = (Text("y" * (MIN_OUTPUT_BUDGET * 3)),)
    pages = paginate(report, MIN_OUTPUT_BUDGET)
    assert len(pages) >= 3  # split inside the block, at character boundaries


def test_multibyte_never_split():
    report = (Text("é" * MIN_OUTPUT_BUDGET),)
    for page in paginate(report, MIN_OUTPUT_BUDGET):
        page.text.encode()  # would raise if a char were split
        assert "�" not in page.text


def test_actual_cursor_bytes_are_counted_not_a_probe():
    def adversarial_cursor(position, digest):
        if position == (2**64 - 1, 2**64 - 1):
            return ""
        return "é" * (MAX_CURSOR_BYTES // 2)

    page = render_page(
        (Text("x" * MIN_OUTPUT_BUDGET),),
        budget=MIN_OUTPUT_BUDGET,
        cursor_for=adversarial_cursor,
    )
    assert page.next_position is not None
    assert len(page.text.encode()) <= MIN_OUTPUT_BUDGET


def test_cursor_that_cannot_fit_refuses_instead_of_overflowing():
    with pytest.raises(ValueError, match="cursor marker"):
        render_page(
            (Text("x" * MIN_OUTPUT_BUDGET),),
            budget=MIN_OUTPUT_BUDGET,
            cursor_for=lambda position, digest: "x" * MIN_OUTPUT_BUDGET,
        )


def test_digest_stable():
    report = (Heading("a"), Finding("f"))
    assert report_digest(report) == report_digest((Heading("a"), Finding("f")))
    assert report_digest(report) != report_digest((Heading("a"),))


def test_write_audit_rules():
    minted = frozenset({("u" * 32, "note:n1")})
    audit_write_report((RecordBlock("u" * 32, "note:n1", "note", "t"),), minted)
    class SubclassedRecord(RecordBlock):
        pass

    with pytest.raises(AuditViolation):  # closed reports reject record subclasses
        audit_write_report((SubclassedRecord("u" * 32, "note:n1", "note", "t"),), minted)
    with pytest.raises(AuditViolation):  # foreign record id
        audit_write_report((RecordBlock("u" * 32, "note:other", "note", "t"),), minted)
    with pytest.raises(AuditViolation):  # right id, wrong uid — both must match
        audit_write_report((RecordBlock("v" * 32, "note:n1", "note", "t"),), minted)
    for block in (Heading("h"), KeyVals("k", ()), Finding("f"), Text("t")):
        with pytest.raises(AuditViolation):  # every non-record block kind
            audit_write_report((block,), minted)
