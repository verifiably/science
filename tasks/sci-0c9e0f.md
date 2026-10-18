---
id: sci-0c9e0f
title: "Workspace guide: build general epistemic components upstream, not in the program"
status: todo
priority: 2
size: s
complexity: mid
process: direct
created: 2026-10-18T20:28:55Z
updated: 2026-10-18T20:28:55Z
depends: []
tags: []
agent: claude-code
---

Keith, 2026-10-18. The multiple-myeloma workspace defined and implemented cohort nodes, overlap groups, prior exposure, validation reservation, catchments and assumed disjointness locally (its phase-1 protocol and a ~3,000-line roster package) because neither beliefs nor science had them; lifting them out now takes sci-3eb5ef, sci-b5c2e9, beliefs-6cd85f and beliefs-a91959. Add to the guidance every science workspace inherits (the workspace section of the projects spec and whatever AGENTS.md template or skill science ships to a workspace) an explicit rule: before a program builds an epistemic or methodological component, ask whether the problem is general to the domain or to every program; if it is, file it upstream (beliefs for record kinds and policy, science for the surface and skills, quarry for resource access) and build there or consume a stopgap that names the upstream task and the release retiring it. Record the mm case as the example. Coordinate with the lore feedback filed the same day so the global and the science-level text say the same thing.
