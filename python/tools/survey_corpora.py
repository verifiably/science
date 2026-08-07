"""Measure what proto-science corpora actually contain. **Run by hand, never by tests.**

    uv run python tools/survey_corpora.py <corpus-dir> [<corpus-dir> ...]

A corpus directory is one holding `entities/`, whose leaves are Markdown files
with YAML frontmatter. The corpora live outside this repository and are not
vendored into it, so nothing here can run in CI and nothing here is a
conformance oracle. This is an **instrument**: it reports what is there so a
design ruling can rest on a measurement instead of an impression.

Three decisions the reader should not have to reverse-engineer.

**The tool discovers enum-shaped fields; it is not given a list of them.**
Handing it the fields we already suspect would confirm the suspicion and find
nothing else — the shape of the answer would be chosen before the corpus was
read. Instead every scalar field above a floor is classified by two ratios it
computes, so a field nobody thought to name can still come back `free-text`.

**A parse failure is reported, never skipped.** A frontmatter block that PyYAML
refuses is counted and named. Silently dropping it would shrink a denominator
without saying so, and every share below is a fraction of a denominator.

**Raw values are kept alongside normalized ones.** Agreement between corpora is
computed over normalized values, because `literature` and `"literature"` are the
same term; drift *within* a corpus is computed over raw ones, because two
spellings of one term is the finding. Collapsing early would erase it.
"""

from __future__ import annotations

import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import yaml

FRONTMATTER = "---"

# A field must clear this many occurrences in a corpus before it is classified at
# all. Below it the two ratios are noise: three records with three values is not
# evidence of free text.
FLOOR = 20

# A scalar field whose distinct values outnumber this share of its occurrences is
# not a vocabulary, whatever its name promises.
FREE_TEXT_RATIO = 0.5

# A field whose most common value covers this share of its occurrences does not
# discriminate between the records that carry it.
COLLAPSE_SHARE = 0.9

# Cross-corpus agreement is only meaningful for a vocabulary. Nothing in the two
# ratios distinguishes a controlled term from a date or a commit hash, so the
# agreement section takes a ceiling on the combined value set and the classifier
# table does not — the table reports what is there, the ceiling reports what is
# comparable.
VOCABULARY_CEILING = 30

# Kinds that could carry a claim, used only for the share reported at the end.
# Deliberately over-inclusive — see the note printed above that table.
CLAIM_BEARING = frozenset({"proposition", "evidence-line", "hypothesis", "finding", "interpretation"})


# A value naming an entity looks like `<kind>:<id>`. Used only to tell link-bearing
# fields from scalar ones; the kind list is deliberately not closed, since a corpus
# may mint kinds this repository has never heard of.
def _looks_like_reference(value: str) -> bool:
    head, sep, tail = value.partition(":")
    return bool(sep) and head.replace("-", "").replace("_", "").isalnum() and bool(tail) and " " not in head


def _normalize(value: str) -> str:
    return unicodedata.normalize("NFC", value.strip().strip("\"'")).casefold()


@dataclass
class Corpus:
    name: str
    records: int = 0
    unparsed: list[str] = field(default_factory=list)
    kinds: Counter[str] = field(default_factory=Counter)
    scalars: defaultdict[str, Counter[str]] = field(default_factory=lambda: defaultdict(Counter))
    links: Counter[str] = field(default_factory=Counter)
    # Records carrying all three of subject, predicate and object. Counted per
    # record rather than inferred from three field totals, which would agree only
    # by coincidence and would state a conjunction it had not measured.
    triples: int = 0


def read_corpus(root: Path) -> Corpus:
    entities = root / "entities"
    if not entities.is_dir():
        raise SystemExit(f"{root} has no entities/ directory; it is not a corpus")
    corpus = Corpus(name=root.name)
    for path in sorted(entities.rglob("*.md")):
        text = path.read_text(errors="replace")
        if not text.startswith(FRONTMATTER):
            continue
        block = text.split(FRONTMATTER, 2)
        if len(block) < 3:
            corpus.unparsed.append(f"{path}: unterminated frontmatter")
            continue
        try:
            front = yaml.safe_load(block[1])
        except yaml.YAMLError as exc:
            corpus.unparsed.append(f"{path}: {type(exc).__name__}")
            continue
        if not isinstance(front, dict):
            corpus.unparsed.append(f"{path}: frontmatter is {type(front).__name__}, not a mapping")
            continue
        corpus.records += 1
        kind = front.get("kind")
        if isinstance(kind, str):
            corpus.kinds[kind] += 1
        if all(isinstance(front.get(part), str) and front[part].strip() for part in ("subject", "predicate", "object")):
            corpus.triples += 1
        for key, value in front.items():
            if not isinstance(key, str):
                continue
            if isinstance(value, list):
                if any(isinstance(v, str) and _looks_like_reference(v) for v in value):
                    corpus.links[key] += len(value)
            elif isinstance(value, str) and value.strip():
                if _looks_like_reference(value):
                    corpus.links[key] += 1
                else:
                    corpus.scalars[key][value] += 1
            elif isinstance(value, bool):
                corpus.scalars[key][str(value).lower()] += 1
    return corpus


def classify(values: Counter[str]) -> str:
    """`free-text`, `collapsed`, or `discriminating` — over raw occurrences."""
    total = sum(values.values())
    normalized = Counter()
    for raw, count in values.items():
        normalized[_normalize(raw)] += count
    if len(normalized) / total > FREE_TEXT_RATIO:
        return "free-text"
    if normalized.most_common(1)[0][1] / total >= COLLAPSE_SHARE:
        return "collapsed"
    return "discriminating"


def drift(values: Counter[str]) -> list[tuple[str, list[str]]]:
    """Raw spellings that normalize together — one term wearing several encodings."""
    groups: defaultdict[str, list[str]] = defaultdict(list)
    for raw in values:
        groups[_normalize(raw)].append(raw)
    return sorted((norm, sorted(raws)) for norm, raws in groups.items() if len(raws) > 1)


def report(corpora: list[Corpus]) -> None:
    names = [c.name for c in corpora]
    print("# Corpus survey\n")

    print("## Scale\n")
    print("| corpus | records | distinct kinds | unparsed frontmatter |")
    print("|---|---|---|---|")
    for c in corpora:
        print(f"| {c.name} | {c.records} | {len(c.kinds)} | {len(c.unparsed)} |")
    for c in corpora:
        for line in c.unparsed:
            print(f"\n> unparsed in {c.name}: {line}")

    print("\n## Kinds\n")
    everywhere = set.intersection(*(set(c.kinds) for c in corpora))
    print(f"In all {len(corpora)}: {len(everywhere)} — {', '.join(sorted(everywhere))}\n")
    for c in corpora:
        others = set().union(*(set(o.kinds) for o in corpora if o is not c))
        only = sorted(set(c.kinds) - others)
        carried = sum(c.kinds[k] for k in only)
        print(f"- **{c.name} only**: {len(only)} kinds, {carried} records — {', '.join(only) or '(none)'}")

    print("\n## Scalar fields, classified\n")
    print(
        f"Floor {FLOOR} occurrences. `free-text` = distinct/occurrences > {FREE_TEXT_RATIO}; "
        f"`collapsed` = top value >= {COLLAPSE_SHARE:.0%}.\n"
    )
    considered = sorted({k for c in corpora for k, v in c.scalars.items() if sum(v.values()) >= FLOOR})
    print("| field | " + " | ".join(names) + " |")
    print("|---" * (len(names) + 1) + "|")
    for key in considered:
        cells = []
        for c in corpora:
            values = c.scalars.get(key, Counter())
            total = sum(values.values())
            if total < FLOOR:
                cells.append(f"— ({total})" if total else "—")
                continue
            top, count = values.most_common(1)[0]
            cells.append(f"{classify(values)}, {len(values)}v/{total}n, top `{top}` {count / total:.0%}")
        print(f"| `{key}` | " + " | ".join(cells) + " |")

    print("\n## Cross-corpus vocabulary agreement\n")
    print(
        f"Normalized value sets, for fields clearing the floor in at least two corpora "
        f"with a combined vocabulary of at most {VOCABULARY_CEILING} values. The ceiling is what "
        f"separates a vocabulary from a date or an identifier, which the two ratios cannot.\n"
    )
    for key in considered:
        present = [c for c in corpora if sum(c.scalars.get(key, Counter()).values()) >= FLOOR]
        if len(present) < 2 or any(classify(c.scalars[key]) == "free-text" for c in present):
            continue
        sets = {c.name: {_normalize(v) for v in c.scalars[key]} for c in present}
        shared = set.intersection(*sets.values())
        union = set.union(*sets.values())
        if len(union) > VOCABULARY_CEILING:
            continue
        verdict = (
            "identical"
            if all(s == union for s in sets.values())
            else ("nested" if any(s == union for s in sets.values()) else "divergent")
        )
        print(f"- `{key}` — **{verdict}**; {len(shared)} shared of {len(union)}")
        for name, s in sets.items():
            extra = sorted(s - shared)
            print(f"    - {name}: {len(s)} values" + (f"; adds {', '.join(extra)}" if extra else ""))

    print("\n## Encoding drift inside one corpus\n")
    found = False
    for c in corpora:
        for key, values in sorted(c.scalars.items()):
            for norm, raws in drift(values):
                found = True
                spellings = ", ".join(f"`{r}` x{values[r]}" for r in raws)
                print(f"- {c.name} `{key}` = *{norm}* written {len(raws)} ways: {spellings}")
    if not found:
        print("(none)")

    print("\n## Link-bearing fields\n")
    union = set().union(*(set(c.links) for c in corpora))
    everywhere = set.intersection(*(set(c.links) for c in corpora))
    print(f"{len(union)} distinct across all corpora; {len(everywhere)} in every one.\n")
    print("| corpus | distinct link fields | links via `related` | links via all other fields |")
    print("|---|---|---|---|")
    for c in corpora:
        rel = c.links.get("related", 0)
        other = sum(v for k, v in c.links.items() if k not in ("related", "id", "title"))
        print(f"| {c.name} | {len(c.links)} | {rel} | {other} |")

    print("\n## Structured claims\n")
    print(
        "The claim-bearing share is generous on purpose: it counts "
        f"{', '.join(sorted(CLAIM_BEARING))} — every kind that could plausibly carry a claim, "
        "including `interpretation`, which mostly does not. A low share under this "
        "definition is therefore a floor on how much of the corpus is narrative.\n"
    )
    print("| corpus | propositions | carrying subject+predicate+object | distinct predicates | claim-bearing share |")
    print("|---|---|---|---|---|")
    for c in corpora:
        props = c.kinds.get("proposition", 0)
        preds = c.scalars.get("predicate", Counter())
        bearing = sum(v for k, v in c.kinds.items() if k in CLAIM_BEARING)
        share = f"{bearing}/{c.records} ({bearing / c.records:.0%})" if c.records else "—"
        print(f"| {c.name} | {props} | {c.triples} | {len(preds)} | {share} |")
    for c in corpora:
        preds = c.scalars.get("predicate", Counter())
        if preds:
            print(f"\n- {c.name}: " + ", ".join(f"`{k}` {v}" for k, v in preds.most_common()))


USAGE = "usage: survey_corpora.py <corpus-dir> <corpus-dir> [<corpus-dir> ...]"

if __name__ == "__main__":
    # Two corpora is the floor, not a convenience: every finding below is a
    # comparison, and a single corpus can only ever agree with itself.
    if len(sys.argv) < 3:
        raise SystemExit(USAGE)
    report([read_corpus(Path(a).expanduser()) for a in sys.argv[1:]])
