---
id: sci-b1c777
title: Adopt cross-corpus dataset inputs once beliefs-9ce6e4 lands
status: done
priority: 2
size: m
complexity: high
process: planned
created: 2026-09-30T22:07:29Z
updated: 2026-10-02T02:01:19Z
completed: 2026-10-02T02:01:19Z
depends: [beliefs-9ce6e4]
tags: [projects]
agent: claude-code/claude-opus-5-5
---

Coordination part 3 fenced two behaviours on the kernel's single-corpus eligibility and lineage: spec and run refuse a dataset only a read mount declares (ReadContext.not_held), and belief/next refuse an assessment whose run reads a dataset its own corpus does not declare (ReadContext._refuse_foreign_observations), because the lineage snapshot is per corpus (a WorldReadView needs a published epoch). When beliefs-9ce6e4 gives eligibility and gathering across mounts, lift both refusals, build lineage across mounts, and amend coordination spec §5.5's part 3 paragraphs. sci-0d00d2 (the mm30 milestone) needs this to use an mm30 dataset from the working corpus.

## Notes

- 2026-09-30T22:07:29Z (main): concerns: sci-923d3a extension — part 3 refuses cross-corpus dataset inputs and foreign lineage pending beliefs-9ce6e4
- 2026-10-01T21:17:58Z (main): folded into sci-dc0381: both lift the same refusals over beliefs-9ce6e4; closes with it
- 2026-10-02T02:01:19Z (feat/dc0381-mount-citations): done
  provenance: {"harness_session":"claude-code:6051398c-8f0e-4511-a835-e90a0c6e83e9","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-02T02:01:19Z (feat/dc0381-mount-citations): landed in sci-dc0381: both part 3 refusals lifted, cross-mount lineage read at the epoch, coordination §5.5 amended
  provenance: {"harness_session":"claude-code:6051398c-8f0e-4511-a835-e90a0c6e83e9","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
