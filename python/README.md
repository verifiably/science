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

Everything else in the design corpus is unbuilt. `docs/designs/` is the authority
on what this is for; the adoption ledger's §1 and §3 are the entry point for what
is built and what waits on what.
