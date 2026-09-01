# science

The daily surface of **Science** — the layer people and agents use: harness-neutral
commands and skills, generated harness adapters (Claude Code first), the CLI and
MCP over `beliefs`, the derived work queue, and publish.

This repository is the `science` layer of the five-layer stack
(`atoms` → `nodes` → `beliefs` → `science` → `autonomy`). It owns no kinds and
no storage: every durable thing is a governed record in a `beliefs` corpus, and
every write is a kernel act through the permit-bound writer endpoint.

The governing design is the kernel repository's
[`docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md`](../beliefs/docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md)
(§5 is this layer; §8 orders the sub-projects). The read path of sub-project
**#2, the command framework**, is implemented: declaration schema, budgeted
renderer, preamble, adapter generator, CLI/MCP over `beliefs` reads, and the
`status` command. Write dispatch and the local writer service remain gated on
the beliefs permit/session deliverables. See the
[command-framework design](docs/specs/2026-08-31-command-framework-design.md).
