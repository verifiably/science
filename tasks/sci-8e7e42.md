---
id: sci-8e7e42
title: "Adopt host-budget: test and test-fast under host-budget run with -n auto"
status: todo
priority: 2
size: s
complexity: low
process: direct
created: 2026-09-24T19:38:54Z
updated: 2026-09-24T19:38:54Z
depends: []
tags: []
source: ops-6d19bb
agent: claude-code/claude-opus-5-5
---

ops docs/specs/2026-09-24-host-budget-design.md, Consumers. -n 8 becomes -n auto (PYTEST_XDIST_AUTO_NUM_WORKERS comes from the budget) under host-budget run, tt outside. Nothing else changes: atoms probes are sequential and science does not call the certification runner. Lands before ops-eb9f2d's acceptance runs.
