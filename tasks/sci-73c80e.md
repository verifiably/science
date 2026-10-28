---
id: sci-73c80e
title: "Adopt cut 48's overlap contract: content check, adopt checklist, holder-set acceptance and the v2 rebinding"
status: todo
priority: 1
created: 2026-10-28T17:14:33Z
updated: 2026-10-28T20:03:11Z
depends: [beliefs-918fd2]
parent: sci-9104fb
tags: [commons]
source: beliefs-918fd2
agent: claude-code/claude-fable-5-1
origin: agent
---

From the overlapping-publications design (beliefs repo, docs/superpowers/specs/2026-10-28-overlapping-publications-design.md §8), landed by beliefs-918fd2 as conformance cut 48. The kernel now lets a world hold one address in several live corpora when the copies have equal content identity; science's side of commons milestone 1b is this task. Science gets from the cut: registry.content_identity(node) as the one equality contract; the per-holder counts(corpus_id, address) calls of §6 (a record is accepted iff any holder's branch says so, and every holder's decision is reported in excluded); and the admission checklist its adopt conflict rule must run before admission, since the kernel offers no exit once a conflicting corpus is admitted and its predecessor is dependency-kept. A candidate is admissible iff, against every live corpus and every candidate this session already admitted: (1) every key, live or deprecated, that the candidate shares with a live record belongs to a record of equal content identity (§4.2 rules 2 and 3; content includes the id, so a live address meeting another record's deprecated id, or two differing records sharing a deprecated id, refuses, and differing content at a shared live address is commons §10.5's case); (2) no candidate uid is held live under a different canonical address (uid-corruption, §4.2 rule 1; an ordinary §4.4 identifier correction published as a successor produces this against the predecessor, and the candidate's live ids alone do not reveal it). Science must also amend, with the same equality contract: the Carrier content check (sci-4a3543: compare the kernel's content_identity of the carrier's copy with the origin's); its session-holder resolution (science/config.py mount_holding and cited, which refuse any address two mounts hold, content aside, before the kernel is consulted); its explain wording for a rejected copy of a record that counted (copy excluded, not record excluded); its pins, which must cover every mounted holder a world read may attribute (§5.4); a surface rule refusing any in-place content change on an address a mounted carrier holds (§4.1); the chain-retention rule of §7 (while a predecessor is dependency-kept, every publication on the supersession chain from it to the current tip of the same (view, destination) stays mounted, a keep the surface sets rather than the user); show's naming of the marker whose adoption would order an attribution-ambiguous refusal's claims (§7, §10 item 3); and the rebinding of §4.5: science/world_belief.py build_over installs every shipped bundle and maps rule symbols to DerivationBindings fields through SYMBOL_FIELDS, a dict keyed by symbol, so the change there REPLACES the v1 symbol's entry with enumerate_retractions_v2 (adding it beside v1's would rebind silently by the dict's iteration order), after which every new epoch science builds carries v2's fold and v1 stays installed for the epochs that name it. The kernel's 1b fixture to copy is python/tests/acceptance/test_overlapping_publications_acceptance.py in the beliefs repo.

## Notes

- 2026-10-28T17:14:33Z (add): created
  provenance: {"harness_session":"claude-code:66da2a5f-ff6b-4b60-8d2a-cff7ba4e9cae","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
