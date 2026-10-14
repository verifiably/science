---
id: sci-877abd
title: Separate context and skills from user commands and interaction machinery
status: idea
priority: 2
created: 2026-10-09T23:03:08Z
updated: 2026-10-14T09:32:52Z
depends: []
tags: []
source: "mindful:thought:f8e2cd302278b9f9e78bbebab8cd4390"
agent: claude-code/claude-fable-5-1
---

Split, simplify, or recreate science along one seam: context and skills (knowledge representations) on one side, user commands such as /research-paper and the machinery for interacting with users (flows and the like) on the other. An open design question captured 2026-10-02; scope it before any work.

## Open questions

- Does the seam already drawn answer this, or do you want science itself split further? Evidence (2026-10-14): the command framework (docs/specs/2026-08-31-command-framework-design.md §2.2) makes every command one deterministic handler plus one harness-neutral prompt, and calls any orchestration-only unit a skill, not a command; `skills/` (authored skills) is empty, and the Claude Code adapter skills are generated from `commands/`. Since the thought was captured, the other half has its own owners: lore (instruction corpus, skills, context assembly), flows (task states and gates), crew (agent harness), autonomy (envelope and orchestrator); knowledge representations live in beliefs, lit, quarry's domain lenses and nodes. A `/research-paper`-style workflow would land as an authored skill under `skills/`. Lean: drop as realized, unless you meant a distinct science knowledge layer (domain context an agent loads, apart from commands), which would be a new idea in lore or science.
