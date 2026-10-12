---
id: sci-a45f10
title: "Make the values a command needs discoverable: kernel-shipped rule identities in spec's inputs, the plan's layers in claim's"
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-12T09:39:40Z
updated: 2026-10-12T09:39:40Z
depends: []
tags: [harness]
source: sci-b40b23
agent: claude-code/claude-opus-5-5
---

Found by the attended pi probe (docs/records/2026-10-12-pi-attended-probe.md, F4). spec's interpretation_rule and equivalence_rule docs say only 'a rule identity the kernel ships'; no prompt, doc or file names beliefs/outcome-file/v1 or beliefs/content-identity-equality/v1, so the agent had to ask. claim refused layer 'causal' with 'not in the plan' without naming the plan's layers (causal_effect, ...); the agent found them by reading the contract document. Attended this costs a question; unattended it stops the run. Done: the rule inputs list the shipped identities (choices, or the doc naming them), and the claim layer refusal or input doc names the accepted layers; the conformance test still matches tools/cli.toml.
