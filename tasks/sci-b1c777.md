---
id: sci-b1c777
title: Adopt cross-corpus dataset inputs once beliefs-9ce6e4 lands
status: todo
priority: 2
size: m
complexity: high
process: planned
created: 2026-09-30T22:07:29Z
updated: 2026-09-30T22:07:30Z
depends: [beliefs-9ce6e4]
tags: [projects]
agent: claude-code/claude-opus-5-5
---

Coordination part 3 fenced two behaviours on the kernel's single-corpus eligibility and lineage: spec and run refuse a dataset only a read mount declares (ReadContext.not_held), and belief/next refuse an assessment whose run reads a dataset its own corpus does not declare (ReadContext._refuse_foreign_observations), because the lineage snapshot is per corpus (a WorldReadView needs a published epoch). When beliefs-9ce6e4 gives eligibility and gathering across mounts, lift both refusals, build lineage across mounts, and amend coordination spec §5.5's part 3 paragraphs. sci-0d00d2 (the mm30 milestone) needs this to use an mm30 dataset from the working corpus.

## Notes

- 2026-09-30T22:07:29Z (main): concerns: sci-923d3a extension — part 3 refuses cross-corpus dataset inputs and foreign lineage pending beliefs-9ce6e4
