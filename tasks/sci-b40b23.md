---
id: sci-b40b23
title: "Attended pi probe: a pi agent runs the mm30 path (next, run, verify, assess) over science mcp serve in a disposable world"
status: todo
priority: 2
size: m
complexity: mid
process: direct
created: 2026-10-11T20:43:00Z
updated: 2026-10-11T20:45:01Z
depends: []
tags: [harness, probe]
agent: claude-code
---

Piece of the science-harness-on-pi goal (ops, filed 2026-10-11 with this task). Spike: the output is a record and a recommendation, not kept code.

Runtime named: pi at the version hq pins, driven interactively through its CLI, with science's existing MCP server connected by pi mcp add (no generated adapter: the adapter generator's pi target is built only for something the MCP surface cannot carry). Attended: the writer session is the one python/src/science/session.py opens today; nothing here claims an unattended boundary.

Question: can a pi agent, given science's commands as MCP tools, a system prompt, and the command prompts, carry the §8 success criterion of the governing design (https://github.com/verifiably/beliefs/blob/main/docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md#8-sub-projects-and-order) over a disposable world holding the mm30 corpus: next ranks the proposition, run executes under confinement, verify reaches clean-environment, assess admits the result, every step a governed record?

Expected evidence, written before the run: the same records docs/records/2026-09-23-mm30-through-the-commands.md shows, ending in the belief NoBelief(no-directional-outcome). That inconclusive belief is the data's answer and is the success condition; a refusal or an unknown outcome caused by the integration (a tool the agent could not find, a budget the renderer truncated into uselessness, a session it could not open) is a failure of the probe, not an eligible outcome. The record separates the two.

Also record: which prompts and context the agent needed beyond the command prompts, where it stalled, token and wall-time cost, and the model used. Pin the model.

Done: a record under docs/records/ with the expected evidence stated first and the outcome against it; a note on the ops goal with the recommendation (what the harness must supply that pi plus science did not).

## Notes

- 2026-10-11T20:45:01Z (main): Goal: ops-3f5aa6 (a science harness on pi). Report the done note there.
