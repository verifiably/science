# science — Python

The Python implementation. Substrate §11 puts the composition root here, so this
tree is the system; `../ts/` carries only the one shared encoding (formal model
limitation 9: **M10 is the only cross-implementation row**).

## Gates

```
uv run --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen pyright src
```

## What is here

| module | what it owns | authority |
|---|---|---|
| `science.identity.v1` | the canonical value contract — injective, domain-separated per kind | computation §4.3 |

Cuts 1–6 have landed their selected slices. The
[`adoption ledger`](../docs/designs/2026-08-03-redesign-adoption-ledger.md) is the
authority for what is built and what still waits on another artifact.
