---
id: sci-498acb
title: Retire the publishes declaration-time refusal when sub-project 5 lands
status: idea
priority: 2
created: 2026-09-09T10:22:34Z
updated: 2026-09-09T10:22:55Z
depends: []
tags: [command-framework]
---

science.dispatch.Dispatcher._required's 'publishes' arm raises Refused(permit-exceeded, 'publishes commands need the publish act family, which arrives with sub-project 5') instead of calling beliefs.permit.RequiredCapabilities.publishes(), because that constructor raises ValueError('publish is not an act family'): ACT_FAMILIES holds no publish yet.

When sub-project 5 supplies the publish act family, the arm becomes 'return RequiredCapabilities.publishes()' and the permit does the refusing, as every other write class already works. The 2026-09-09 amendment to spec §4.4 comes back out with it, and tests/test_dispatch.py::test_publishes_class_refuses_until_the_publish_family_exists is replaced by whatever the real publish path asserts.

Filed as an idea because no sub-project 5 task exists to depend on. Promote it to a todo and add the dependency when one does. sci-17851d is the same shape, waiting on sub-project 1.
