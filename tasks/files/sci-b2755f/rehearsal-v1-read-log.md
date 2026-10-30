# Complete synthetic rehearsal read log v1

Date: 2026-10-30; worker freshly verified codex/gpt-6.1-sol; controller Codex.
Skill and fixtures frozen at science commit 461f407. Worker used git show to read
only SKILL.md, report-template.md and scenario.md; controller alone read oracle.
Scenario includes D1 metadata, encountered before phase A; no feasibility comparison
or candidate ordering was performed before the actual inventory attachment.

10 source entries; S1/S2/S3 one confirmed study identity; other seven tentative
identities include unresolved S4. Eight provisional screen groups; no assertion
of eight independently verified publications. Zero live searches/full-text reads.

## Served requests, in order

First segment requested five independently addressed blocks. The controller
served exactly those five, without exposing any source body. Second segment
reported those reads and requested S5:abstract only after ACC-A-only mapping;
controller then served that block. All six actual responses follow verbatim.

### S1:abstract
Synthetic S1 abstract:r1. "The late-versus-early signal contrast is positive in
calibrated samples." Cohort ACC-A only. No claim of causal identification.

### S4:data-availability
Synthetic S4 data-availability:r1. "Data are deposited under ACC-A."
The bibliographic PMID/DOI conflict remains unresolved by this text.

### S5:data-availability
Synthetic S5 data-availability:r1. "This article uses only ACC-A."

### S5:methods
Synthetic S5 methods:r1. "Calibrated samples from early and late visits were
compared; no longitudinal perturbation or recovery experiment was performed."

### S8:references
Synthetic S8 references:r1. S1, PMID 90000001, DOI 10.0000/a; S5, PMID 90000005,
DOI 10.0000/e. Navigation only; assertions require those sources to be read.

### S5:abstract
Synthetic S5 abstract:r1. "The bulk proxy distinguishes the compared groups."
Cohort ACC-A only. This supports a proxy question, not premise P3 as authored fact.

## Refusals and incidents

S2/S3 aliases: no extra retrieval. S4 still conflicting PMID/DOI; no abstract.
S6 mixed A/B results inseparable, no abstract; S7 isolation unavailable, no whole
body; S8 isolated references only, no review body; S10 reserved C, no abstract.
S9 was supplied in the scenario itself: “In the late group, signal doubled.”
Worker actually saw it, mapping unknown, confirmed synthetic result exposure;
source stopped, omitted from ranking/consequence evidence. Retained here as a
synthetic incident, not filed as a real mm exposure. The title “Temporal
observations” is separately possible exposure of uncertain meaning. Remaining
sources continued. No source-scientific attribution comes from unread sections.

## Phase-A freeze and phase-B gate

Exact worker phase-A bytes attached and verified in tasks show as sci-b2755f
rehearsal-discovery-v1.md, 22985 bytes; SHA-256
6ff8278b0006bf470b16894f47b2c09f45ac648310451b4b7c8b9ca2f5b6e310.
Byte equality with attachment confirmed before the controller authorized phase B.
No new source reads are authorized for phase B.

# Rehearsal section isolation

Run-local standard-library JATS extractor, not shipped.
Exact invocation (WORK_ROOT resolves on this host):

```sh
python3 "$WORK_ROOT/science/sci-b2755f/select-section.py" --self-check
python3 "$WORK_ROOT/science/sci-b2755f/select-section.py" <input.xml> <section>
```

Observed exit status: 0.

PASS: isolated abstract/methods/data-availability/references; sentinels excluded; missing/ambiguous/malformed inputs refused

No whole-document fallback; source bytes are parsed before selected text is printed.
Synthetic proof only; live response shape requires one permitted-source probe.

## Exact source

```python
"""Run-local JATS projection; prints only a uniquely addressed section."""
from pathlib import Path
import sys
from xml.etree import ElementTree as ET


def select_section(data: bytes, section: str) -> str:
    root = ET.fromstring(data)
    if root.tag != 'article':
        raise ValueError('expected unnamespaced JATS article')
    if section == 'abstract':
        nodes = root.findall('./front/article-meta/abstract')
    elif section == 'references':
        nodes = root.findall('./back/ref-list')
    elif section in ('data-availability', 'methods'):
        titles = {'data-availability': {'data availability', 'data availability statement'},
                  'methods': {'methods', 'materials and methods'}}[section]
        nodes = [n for n in root.iter('sec') if n.get('sec-type') == section
                 or ' '.join(n.findtext('title', '').lower().split()) in titles]
    else:
        raise ValueError('unsupported section')
    if len(nodes) != 1:
        raise ValueError(f'expected one {section} section, found {len(nodes)}')
    text = ' '.join(' '.join(nodes[0].itertext()).split())
    if not text:
        raise ValueError('empty section')
    return text


def self_check():
    data = b'<article><front><article-meta><abstract>RESULT_SENTINEL</abstract></article-meta></front><body><sec><title>Results</title><p>RESULT_SENTINEL</p></sec><sec sec-type="methods"><p>calibrated design</p></sec></body><back><sec sec-type="data-availability"><p>ACC-A only</p></sec><ref-list><ref><pub-id pub-id-type="pmid">90000001</pub-id></ref></ref-list></back></article>'
    assert select_section(data, 'abstract') == 'RESULT_SENTINEL'
    assert select_section(data, 'methods') == 'calibrated design'
    assert select_section(data, 'data-availability') == 'ACC-A only'
    assert select_section(data, 'references') == '90000001'
    for section in ('methods', 'data-availability', 'references'):
        assert 'RESULT_SENTINEL' not in select_section(data, section)
    for bad, section in ((b'<article/>', 'methods'),
                         (b'<article><sec sec-type="methods">a</sec><sec sec-type="methods">b</sec></article>', 'methods'),
                         (b'<article>', 'methods'), (b'<other/>', 'methods')):
        try:
            select_section(bad, section)
        except (ValueError, ET.ParseError):
            pass
        else:
            raise AssertionError('ambiguous/missing/malformed input accepted')
    print('PASS: isolated abstract/methods/data-availability/references; sentinels excluded; missing/ambiguous/malformed inputs refused')


if __name__ == '__main__':
    if sys.argv[1:] == ['--self-check']:
        self_check()
    else:
        print(select_section(Path(sys.argv[1]).read_bytes(), sys.argv[2]))
```
