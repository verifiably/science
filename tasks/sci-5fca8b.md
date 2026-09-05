---
id: sci-5fca8b
title: "Read path cannot open a world: beliefs open_world requires an Authority"
status: idea
priority: 2
created: 2026-09-05T08:22:08Z
updated: 2026-09-05T08:22:08Z
depends: []
tags: [command-framework]
---

Since beliefs a1f7408 (2026-09-04, root lifecycle acts require the lifecycle permit) open_world, open_corpus, init_world_root and init_corpus_root take a keyword-only authority. science ReadContext.open (python/src/science/config.py) calls open_world(config.world) with none, so every CLI, MCP and status test fails with TypeError (15 of 226 on 2026-09-05). The command-framework design section 4.2 says science never constructs a permit, and the plan's read tasks consume open_world(config) -> World, so the fix is a contract amendment: a permit-free read open in beliefs or an agreed read-only authority, then update tests/helpers/world.py alongside. Belongs with sci-c3f0bb / beliefs-afbbff rather than the test audit piece.
