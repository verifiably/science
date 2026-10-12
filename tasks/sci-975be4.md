---
id: sci-975be4
title: "spec prompt: method, assumptions and falsification are the person's words verbatim"
status: todo
priority: 3
size: xs
complexity: low
process: direct
created: 2026-10-12T10:44:06Z
updated: 2026-10-12T10:44:17Z
depends: []
tags: [harness]
source: sci-b40b23
agent: claude-code/claude-opus-5-5
---

In the attended pi probe (docs/records/2026-10-12-pi-attended-probe.md, F5, Q7) the agent capitalised and re-punctuated the person's prose before freezing the spec, so its identity differed from a verbatim entry of the same plan. commands/spec/prompt.md says 'in the user's words', which a model reads loosely. Every adapter reads this prompt, so the fix belongs here rather than in one harness's system prompt. Done: the prompt says the three prose fields are copied verbatim, unedited, and the adapter output is regenerated.

## Notes

- 2026-10-12T10:44:17Z (main): concerns: sci-b40b23 extension — the probe's F5 belongs in the shared spec prompt, not one harness
