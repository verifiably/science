---
id: sci-7ffb18
title: Create the public verifiably/science repo and push
status: todo
priority: 2
size: s
created: 2026-09-07T15:29:34Z
updated: 2026-09-07T15:29:34Z
depends: []
tags: [hygiene]
---

The science checkout has commits and active work but no git remote at all, and no repository exists for it. It is the only layer of the five-layer stack with nowhere to push: atoms, nodes, beliefs and autonomy are all public under verifiably as of 2026-09-07.

One wrinkle to handle deliberately. verifiably/science is not free: it is the old name of verifiably/beliefs, which was renamed (beliefs-3a07e4), and GitHub still redirects it — gh repo view verifiably/science resolves to verifiably/beliefs today. Creating a repository called science in that org would break that redirect, so any existing link or clone URL pointing at verifiably/science would stop reaching beliefs and start reaching this instead. Decide whether that redirect is still load-bearing before taking the name, and consider verifiably-science or another name if it is.

Same precondition as the other publications: audit the whole history for secrets, credentials and home-directory paths before the first push, since the initial push publishes every commit at once. gitleaks found nothing in atoms or autonomy; science has not been scanned.

Public also means GitHub Actions on standard runners is free here, as recorded in beliefs AGENTS.md. Related but separate: sci-052b71 is about PyPI, not the git remote.
