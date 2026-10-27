---
id: sci-0d00d2
title: "Second-project milestone: health over mm30, measurement plan and record"
status: doing
priority: 1
size: m
complexity: high
process: planned
owner: second-project-milestone
created: 2026-09-23T11:40:35Z
updated: 2026-10-27T01:57:44Z
started: 2026-10-27T00:22:44Z
depends: [sci-b1c777, beliefs-fe7149, beliefs-c08725, sci-c5528e, sci-923d3a, beliefs-9ce6e4, sci-dc0381, sci-7079e3]
tags: [projects]
agent: claude-code/claude-fable-5-1
spec: docs/specs/2026-10-26-second-project-milestone-design.md
---

The milestone of docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md §9.2: one world root at the user's data location holding the relocated mm30 corpus and a fresh working corpus, opened as one session; health, cancer and multiple-myeloma project views with the §6.2 queries; one health question introducing a proposition with an unheld dataset and a same-query view under cancer; next checked against each view's expected selection (equality legitimate where selections coincide); a findings-level publish dry run when sub-project 5 exists; cwd independence; MCP-select then CLI-read. Predictions before, findings classified after, every refusal filed to its owning lane; the record lands under docs/plans/. Its findings decide whether §7's single-home fence needs a beliefs request and scope beliefs-7c98bc.

## Notes

- 2026-09-24T14:26:54Z (main): The mm30-commands world under .work/ carries coordination = false (added at part 1's merge) but still refuses to load: its mm30.yaml has the top-level 'also: [biology]' key that sci-3a01b3 made a refusal. Drop the key (config domains supplies biology) before the milestone uses that world.
- 2026-09-30T21:26:10Z (coordination-part3): criterion 4's dependency sci-923d3a landed: write_root, read_contracts, per-mount profiles, next and belief across mounts
- 2026-10-09T22:29:07Z (main): criterion 1 prerequisite: SCIENCE_CONFIG is exported as /mnt/ssd/science/science.toml (dotfiles titan.env.zsh) but the file does not exist; the relocated world is at /mnt/ssd/science/worlds/aec951bc…/ (world, corpora/mm30, store). The multiple-myeloma program (mm-a32d58) holds its phase-1 datasets into this world after this milestone.
- 2026-10-14T08:56:20Z (main): Measurement request from beliefs (2026-10-14): when recording epoch builds (mount-citations consumer spec limitation 1), tag each forced science epoch with the class of write that triggered it: coordination (project, question, hypothesis) or evidence. Limitation 2's coordination-write staleness is otherwise unmeasured, and beliefs-655c10 (a mapped-content witness that would exempt coordination-only drift) is shelved until this record shows whether coordination-only rebuilds cost enough to justify it. On completion, note beliefs-655c10 with the coordination-only rebuild count and cost.
- 2026-10-27T00:22:44Z (main): started
  provenance: {"harness_session":"claude-code:74a061f4-8320-41fa-a2a3-a3ce105dd286","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-27T00:23:11Z (second-project-milestone): resumed
  provenance: {"harness_session":"claude-code:74a061f4-8320-41fa-a2a3-a3ce105dd286","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-27T00:29:27Z (second-project-milestone): brainstorm: world root has mm30 but no working corpus or science.toml; no science/beliefs command creates a corpus or mints a declared-unheld dataset (driver steps + gap finding); health proposition must be biology protein-protein; predecessor health/meta q0167 (p53/RP-MDM2) is the candidate first health question
- 2026-10-27T00:29:28Z (second-project-milestone): parked (waiting on user, decision): user answers which health/meta question is the first health question (recommended: q0167, proposition protein:RPL11 regulates protein:MDM2, dataset declared by digest, unheld); then the agent lays out approaches and drafts the design spec in .worktrees/second-project-milestone
  provenance: {"harness_session":"claude-code:74a061f4-8320-41fa-a2a3-a3ce105dd286","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-27T00:49:26Z (second-project-milestone): resumed
  provenance: {"harness_session":"claude-code:74a061f4-8320-41fa-a2a3-a3ce105dd286","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-27T00:49:31Z (second-project-milestone): design review (pre-spec, reviewer codex gpt-6-astra, relayed by user): ground the health question in the live PHF19 records, not q0167's ungoverned TP53 result; RPL11->MDM2 would be a narrower subclaim; the unheld dataset needs an honest digest source; state selection predictions explicitly (cancer==mm; health and world add the proposition as not-ready; source preserved, copied query equal); measure beyond epochs: explicit address entries per view (beliefs-7c98bc), reuse count and repair burden (§7), citing-write cost, epoch classes (initial, coordination-only, evidence, unchanged reuse) for beliefs-655c10; include §9.1's read of multiple-myeloma and the overlap inventory
- 2026-10-27T01:23:48Z (second-project-milestone): design spec drafted at ea3591d (docs/specs/2026-10-26-second-project-milestone-design.md); builder check (claude-code subagent) raised 3 questions, all settled in the draft: criterion 5 refuses on attribution (replica-of mm30) and is predicted as such, world facts mint before the projects (address-unknown), kernel-level driver steps run before the server opens; corrections folded: 18 live records, SuccessionViolation uncaught by the loader, closure cannot miss projection-held inputs
- 2026-10-27T01:23:50Z (second-project-milestone): parked (waiting on user, review): user reviews the design spec at ea3591d (git show ea3591d:docs/specs/2026-10-26-second-project-milestone-design.md in .worktrees/second-project-milestone); on acceptance the agent files the chain-loader task as a dependency and invokes writing-plans; on revise the agent amends as a new revision
  provenance: {"harness_session":"claude-code:74a061f4-8320-41fa-a2a3-a3ce105dd286","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-27T01:44:58Z (second-project-milestone): resumed
  provenance: {"harness_session":"claude-code:74a061f4-8320-41fa-a2a3-a3ce105dd286","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-27T01:44:59Z (second-project-milestone): review: spec round 1 — verdict: revise; findings: P1 2, P2 4; reviewer: codex/gpt-6-astra
- 2026-10-27T01:48:49Z (second-project-milestone): revision 2 at 1f65730: criterion 3 partly met and 5 unmet by prediction (C5, C7) with no acceptance condition relaxed; §6.2 term-clause amendment proposed and measured via an evidence-bound question; findings-level view as a project (surface gap); frozen epoch schedule E1-E5; annotation declared as a second dataset with the TPM rule, id mapping and condition mapping stated; C6 as two sequential launcher arms; scratch at WORK_ROOT task dir with attachments; docs/records amendment applied to the authority
- 2026-10-27T01:48:50Z (second-project-milestone): parked (waiting on user, review): user reviews revision 2 at 1f65730 (git show 1f65730:docs/specs/2026-10-26-second-project-milestone-design.md in .worktrees/second-project-milestone); on acceptance the agent files the chain-loader task as a dependency and invokes writing-plans; on revise the agent amends as a new revision
  provenance: {"harness_session":"claude-code:74a061f4-8320-41fa-a2a3-a3ce105dd286","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-27T01:56:37Z (second-project-milestone): resumed
  provenance: {"harness_session":"claude-code:74a061f4-8320-41fa-a2a3-a3ce105dd286","harness_session_source":"CLAUDE_CODE_SESSION_ID"}
- 2026-10-27T01:56:38Z (second-project-milestone): review: spec round 2 — verdict: accept; findings: Minor 2; reviewer: codex/gpt-6-astra
