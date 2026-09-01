# Task 3 report: Report model

## RED evidence

Added `python/tests/test_report.py` before implementation and ran:

```text
uv run --group dev pytest tests/test_report.py -q
```

Result: collection failed with `ModuleNotFoundError: No module named 'science.report'`.

## GREEN evidence

Implemented the immutable report blocks, kernel-derived `record_block` factory,
`Block` and `Report` aliases, and deterministic newline-terminated
`serialize_block`. Focused test result:

```text
2 passed in 0.01s
```

## Final verification

- `uv run --group dev pytest tests/test_report.py -q`: 2 passed
- `uv run --group dev pytest -q`: 43 passed
- `tasks check --pretty`: ok
- `git diff --check`: clean

## Files

- Added `python/src/science/report.py`.
- Added `python/tests/test_report.py`.
- Updated tracker record `tasks/sci-ba22f9.md` through `tasks done`.

## Self-review

The implementation follows the brief exactly, uses frozen dataclasses, derives
record fields only from the supplied node attributes, rejects unknown blocks
with `TypeError`, and introduces no dependencies or compatibility layer.
