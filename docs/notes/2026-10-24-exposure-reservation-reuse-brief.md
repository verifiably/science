# Exposure and reservation across programs — brief

Date: 2026-10-24. Ideas: sci-b5c2e9, sci-861d8f.

## Problem

A second program using public cohorts should consume shared exposure and reservation mechanisms rather than rebuild a local ledger and roster. Establish what state the shared stack must represent before choosing a breast-cancer workspace as the next consumer. This is a bounded handoff within the existing research-protocol and workspace work, not authorization to launch another program.

## Current behaviour and evidence

- Science at d94ab77 declares no exposure or reservation command in tools/cli.toml. python/src/science/commands/dataset.py holds bytes, declares datasets and optionally records empirical standing; it does not record which findings influenced selection or a group's reservation role. No exposure/reservation consumer was found under python/src/science, commands or skills.
- sci-b5c2e9 reports a markdown exposure ledger with 592 dated entries and reservation snapshots with frozen input digests. Those are the filing's historical observations, not fresh counts. The external protocol, roster and ledgers were not inspected in this fixed-checkout pass.
- mm-0f5df1 records approval of protocol version 3 at b428d66; mm-69f82e records later clearance-basis and frozen-input invalidation work. These task records establish relevant work to inspect, not the current program's measured reservation result.
- sci-3eb5ef already owns a reusable research-protocol skill; sci-0c9e0f owns guidance to build general components upstream. Neither settles the representation of exposure events and assignments.
- docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md §§9.1–9.3 chooses health over existing mm30 facts first. Its measurement task sci-0d00d2 remains open. A second view over existing facts and a second program over new cohorts test different things.
- sci-861d8f names METABRIC, TCGA-BRCA, SCAN-B and GEO as candidate inputs, and reports no proto-science breast-cancer exposure. Their suitability, access and exposure history were not verified here; no inherited ledger does not establish independence from model or literature priors.

## Constraints

Every durable thing is a beliefs-governed record, written through the permit-bound endpoint; science provides commands and derived views and owns no parallel store. Preserve event evidence, assignment inputs and digests, supersession history and explicit unknowns. Reservation is not by itself independence certification, and participant disjointness does not establish absence of selection exposure.

Existing beliefs-9bf498 and beliefs-5e66ba own the information-loss inventory and aggregation recommendation, including exposure versus ancestry; beliefs-a91959 and beliefs-6cd85f own the confirmation/participant-overlap ideas waiting on them. Do not duplicate that research or make a weighted belief policy a prerequisite for recording state. mm-af6b59 owns reservation-preserving participant-matching feasibility; mm-245d2f owns model-originated hypothesis attribution. Program-specific reservation reading remains with its existing owners.

## Alternatives

1. Govern exposure events and frozen reservation assignments in beliefs, with science authoring and reading them. Current lean: investigate this route, preserving the kernel boundary and making a second consumer possible.
2. Keep the program's existing ledgers as an explicitly temporary mechanism while sci-3eb5ef documents the rules and gaps. Retains working controls, but leaves state outside shared reads; any stopgap must name its upstream owner and retirement condition.
3. Start breast cancer now and extract common code from two implementations later. Rejected as the default: it repeats the locally built machinery before its ownership and semantics are settled.

Keep the existing health milestone first. The brief does not decide which new scientific program deserves priority once the shared requirements are known.

## Unanswered questions

- Which minimal exposure event, assignment, evidence and supersession fields require governed representation, and which existing writer/reader seams can serve them? The bounded science follow-up inspects one example of each and reports the smallest missing owner; no new storage implementation.
- Which overlap and confirmation semantics should belief computation consume? Existing beliefs-9bf498 and beliefs-5e66ba, followed by their waiting ideas; separate from the write/read seam question.
- Which reservation assumptions and input changes must invalidate an assignment? Inspect the program's current protocol and tests in the follow-up; this pass has only task-record evidence.
- After health's milestone and the shared-state recommendation, does a breast-cancer workspace merit the next program slot, and what first question would it answer? The user decides scientific priority then. No cohort survey, downloads or workspace creation are authorized by this pass.

## Proposed decomposition

Goal sci-8f15d4 groups the two ideas and bounded research sci-1fd5e5 (priority 2, size s, complexity mid, process direct). Existing sci-3eb5ef and sci-0c9e0f remain separate owners. This is a bounded prerequisite within the existing shared-protocol work, not a new program lane.

- sci-b5c2e9 stays an idea waiting on sci-1fd5e5's exposure/assignment write-read seam recommendation.
- sci-861d8f stays an idea waiting on sci-1fd5e5 and sci-0d00d2. Reconsider the consumer and sequencing with those results; do not create a workspace meanwhile.
- sci-1fd5e5 must record findings on both waiting ideas with --no-reviewed before its result branch merges, and update this brief. Its scope excludes aggregation research and participant-matching feasibility already owned elsewhere.

