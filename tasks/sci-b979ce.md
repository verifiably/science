---
id: sci-b979ce
title: "Commons 1a: a decisive belief verdict flip needs a clean-environment verification fixture"
status: idea
priority: 2
created: 2026-10-23T17:10:07Z
updated: 2026-10-23T17:10:07Z
depends: []
tags: [commons]
source: sci-13050a
agent: claude-code
---

test_commons_1a's belief case asserts inclusion and exclusion of A's assessment in the belief inputs and context under accept=[] and accept=[A], which spec §12 1a asks for, but the answer is NoBelief no-eligible-assessment under both: B's verification of A's assessment is same-environment because A's run is minted under the minimal policy by the portable fixture, and the kernel admits only clean-environment passes. A fixture that mints A's run through run under confinement would let the test show the verdict change too.
