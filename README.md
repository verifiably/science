# science

The daily surface of **Science** — the layer people and agents use: harness-neutral
commands and skills, generated harness adapters (Claude Code first), the CLI and
MCP over `beliefs`, the derived work queue, and publish.

This repository is the `science` layer of the five-layer stack
(`atoms` → `nodes` → `beliefs` → `science` → `autonomy`). It owns no kinds and
no storage: every durable thing is a governed record in a `beliefs` corpus, and
every write is a kernel act through the permit-bound writer endpoint.

The governing design is the kernel repository's
[user and autonomy layer design](../beliefs/docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md)
(§5 is this layer; §8 orders the sub-projects). Sub-project **#2, the command
framework**, is implemented: the declaration schema and write classes, the
budgeted renderer, the shared preamble, the dispatcher over both the read and
write paths, the CLI and MCP surfaces, the Unix-socket writer service, the
Claude Code adapter generator, and the one shipped command, `status`. Writes
run as kernel acts through an attended `beliefs` session, permit-checked per
act and deduplicated through its ledger. See the
[command-framework design](docs/specs/2026-08-31-command-framework-design.md).
