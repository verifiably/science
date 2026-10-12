---
id: sci-bef251
title: "Command replies carry what they minted: assess its outcome, verify its scope and verdict, run its result manifest"
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-12T09:39:39Z
updated: 2026-10-12T10:17:42Z
depends: []
tags: [harness]
source: sci-b40b23
agent: claude-code/claude-opus-5-5
---

Found by the attended pi probe (docs/records/2026-10-12-pi-attended-probe.md, F3). The agent walked mm30 to NoBelief(no-directional-outcome) but could not say why: the assess reply names only the assessment ref, verify only the verification and replay refs, run only the run ref; the run's outputs live only in operations scratch. It had to infer 'inconclusive' and declined to state z, p, n. An unattended agent cannot report the basis of a belief at all. Done: each of the three replies renders the outcome, the verification scope and verdict, and the result manifest (output names and digests) within its output budget; CLI and MCP renderings stay byte-identical.

## Notes

- 2026-10-12T10:17:42Z (main): Review of sci-b40b23: returning a result manifest (output names and digests) alone does not let the agent report the run statistics. Acceptance should include a governed way to read the referenced output content, sufficient to report z, p and n for the mm30 case, with source identity preserved and output budgets respected.
