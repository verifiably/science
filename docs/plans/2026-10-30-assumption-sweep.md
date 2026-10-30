# Assumption Sweep Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. The controller implements inline; fresh agents supply the writing-skills controls, guided runs and read-only reviews. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship one reusable assumption-sweep skill and a bounded mm pilot yielding an inspectable inventory, three explained questions and concrete representation gaps.

**Architecture:** An authored Markdown skill and report template are copied by the existing adapter builder. A manual synthetic rehearsal establishes the workflow before a real survey; the pilot's report and frozen inventory are task attachments, never world records or a new scientific store.

**Tech Stack:** Markdown, existing Python adapter/tests, `just`, `uv`, `tasks`, existing quarry PubMed metadata reads and available section-isolating retrieval tools. No new dependency, handler, command or service.

**Spec:** [Assumption-sweep design](../specs/2026-10-30-assumption-sweep-design.md), accepted at spec round 4 from `c2f3a885d622fe97f21ec34ddd3eb1a9a2506dd6`, with the permitted review-navigation clarification committed with this plan. Read the frozen plan and spec from the same review commit.

## Global constraints

- Invocation: `/science:sweep-assumptions`. No `/sci:` alias or plugin rename.
- Discovery precedes impact and feasibility assessment. Important questions without suitable data remain in the inventory.
- Pilot caps: 24 search queries, 80 unique bibliographic screens, 18 full-text primary research articles. Abstracts require the spec §4 screening permission.
- Preserve exact statements, revisions, scope, provenance and counterevidence. Proposed reliance is distinct from stored relations and biological causation.
- No aggregate score or expected-information-gain claim; explain reach, consequence, remaining uncertainty and feasibility separately.
- No world writes, new biological analyses, patient-level reads, protected result reads, kernel changes, scheduling, raw-paper attachment or persistent service.
- Titles and isolated reference lists are the only navigation reads of reviews. Do not display a review body to find its references.
- A result-bearing abstract is exposure regardless of whether its cohort is mapped. Unknown/mixed/protected mappings receive metadata-only treatment; an incidental result read stops that source, not the whole screen.
- Missing capabilities and insufficient yield are findings. Fewer than three defensible candidates means the pilot is incomplete, not permission to manufacture one.
- New files and commands below are relative to this worktree; reports to the user prefix them with `.worktrees/sci-b2755f/`.

## Review focus

These five failure classes require the manual checks assigned below; adapter tests cannot establish them:

1. A paper maps to one discovery cohort but also uses an unresolved cohort: do not grant blanket abstract/results access (Task 1 controls, Task 2 rehearsal).
2. A retrieval tool returns result text while asked for metadata, or cannot isolate a review's references: record the incident or skip; never scan the body for a section (Task 2 retrieval log).
3. Empty applicability plus a contrast restriction, and target-only falsification: preserve the restriction and label the connecting judgment; infer neither pooling nor premise falsification mechanically (Tasks 1–2).
4. Duplicate deposits, repeated paths, cycles and inferred consequences: reach counts unique endpoints and the report keeps attribution and unevaluated items visible (Tasks 1–2).
5. A high-impact candidate lacks suitable data, or source restrictions yield fewer than three candidates: retain the candidate/shortfall, with no substituted score or invented feasibility (Task 2, then Task 3 acceptance).

## Files and existing behavior

| Path | Responsibility |
|---|---|
| `skills/sweep-assumptions/SKILL.md` | Trigger, workflow, read boundaries, discovery freeze and comparative judgments |
| `skills/sweep-assumptions/report-template.md` | Eight report sections and required row fields; copied with the skill |
| `python/tests/fixtures/sweep-assumptions/scenario.md` | Synthetic input inventory and bounded read scenarios; no world records |
| `python/tests/fixtures/sweep-assumptions/expected-review.md` | Independent manual oracle for those scenarios |
| `python/tests/test_adapters.py` | One inclusion test plus existing full generated-tree equality check |
| `adapters/claude-code/skills/sweep-assumptions/` | Generated skill/template copies; never hand-edit |
| `README.md` | Short authored-skill invocation and limits entry |

The adapter already copies regular authored files recursively, rejects symlinks
and name collisions, and does not prepend the command preamble. The new skill
therefore states its own read/write boundaries. sci-cc4fb9 is still open with no
authored skill present at planning: recheck its landing before writing, follow
an established convention if one exists, and record the revision used.

The inspected quarry adapter `src/quarry/adapters/pubmed.py` maps ESummary to
title, PMID, DOI/PMC cross-references, date and journal name, without an abstract.
Its documented route is `quarry search --in pubmed ...` or `quarry show pubmed:<id>`;
search supports `-n` and reports limited coverage. Check the resolved executable
and installed behavior before the pilot. This is code-read evidence, not a live
retrieval test. No section-only article route has yet been demonstrated.

## Evidence and review convention

Use `$WORK_ROOT/science/sci-b2755f/` for persistent run inputs and outputs; record
creation immediately and checkpoint retained items at park/done. No raw paper
bytes go into Git. Reports and source ledgers carry only permitted excerpts,
locators and attributed summaries. Keep report-local IDs (`S`, `Q`, `P`, `L`, `C`)
separate from stored addresses, and keep every stored address bound to its
corpus/state/revision. Use versioned attachment names; never overwrite a freeze.

Attach every authoritative report, review and inventory to sci-b2755f via the CLI.
Verify its `tasks show` entry and SHA-256 equality before removing a working copy.
Children record their validation and link the parent attachment names. Reviewers
return full text and remain read-only; the controller saves reports in the plan
workspace before attachment and records each review note before acting on it.

### Task 1: Author and package the sweep skill

**Files:** create both skill files and both fixture documents above; modify
`python/tests/test_adapters.py`, generated adapter files and `README.md`.

**Interfaces:** consumes the accepted spec and current adapter convention.
Produces a self-contained skill/template, synthetic scenario/oracle, recorded
no-skill versus guided outputs, and generated copies accepted by adapter tests.

- [ ] **Step 1: Re-enter execution Setup before changing product files.** Reuse
  `.worktrees/sci-b2755f`; inspect its cleanliness, dependencies and hook path.
  Hydration already ran successfully; repeat the documented setup only if needed.
  Recheck test policy through this checkout's `tools/tt`. At planning `.tt.toml`
  is absent, so run `just test` as the deferred full baseline and record the
  actual test count. A valid policy-off file landed meanwhile changes this to
  `just test-one tests/test_adapters.py` plus `just check`, with the broad omission
  explicit. Zero selected tests is not a passing baseline. Investigate failures
  under the existing test policy; never run pytest directly.

- [ ] **Step 2: Write the two synthetic fixture documents before the skill.**
  Include three neutral question families (measurement, generalization, temporal
  mechanism), with at least four candidate questions. Define a premise P1 with
  dependent claims C1 and C2, question Q1 relying on C1 and C2, and Q2 relying on
  C2; two paths to Q1 yield one reached question. Repeated deposits assert the
  same C1 and do not create another claim. Add a P1/P2 cycle with no extra claim
  or question; expected reach from P1 remains claims `{C1,C2}` and questions
  `{Q1,Q2}`. Mark one edge inferred and one C2 consequence unevaluated. Add empty
  applicability with scope restricted by contrast, falsification about the target
  only, and an important candidate whose required longitudinal assay is unavailable.
  Give source excerpts exact synthetic text and locators. Include absent/invalid
  record inputs and refuse unsupported source attribution.

  Include publication records for: a resolved PMID; a DOI-only match; conflicting
  identifiers; no match resolved by a separately available data-availability
  section; discovery plus unresolved cohorts in one paper; inaccessible sections;
  an isolated review reference list; and a metadata response with incidental
  result text. Represent allowed section responses as separate blocks/files in
  the fixture, so a worker requests them without first reading a forbidden body.
  The oracle states allowed reads and source-local stop/skip outcomes for each.

- [ ] **Step 3: Observe a writing-skills baseline before authoring.** Read
  `superpowers:writing-skills` and its required testing guidance. Give fresh
  read-only workers the same compact scenario and research request without the
  new skill or expected-review oracle. Keep real cohort/data access out of these
  runs. The pressure is to provide a brief top-three answer promptly from an
  apparently prepared inventory despite missing mappings and a popular candidate
  lacking data; it never authorizes fabrication. Run five fresh-context samples
  of this one scenario as the no-guidance control. Save full returned text and
  manually score it against the oracle, retaining exact observed failure text.
  Do not call correct control behavior a failure. If the control never exhibits
  a problem, record that result and reassess the proposed guidance before writing
  it; do not manufacture a RED result or silently waive the skill-writing gate.

- [ ] **Step 4: Add the failing packaging test.** In `test_adapters.py` add:

  ```python
  def test_assumption_sweep_authored_files_are_packaged(tmp_path):
      from science.adapters import build_adapter

      build_adapter(production_tree(), COMMANDS_ROOT, REPO_ROOT / "skills", tmp_path)
      source = REPO_ROOT / "skills" / "sweep-assumptions"
      packaged = tmp_path / "skills" / "sweep-assumptions"
      for name in ("SKILL.md", "report-template.md"):
          assert (packaged / name).is_file()
          assert (packaged / name).read_bytes() == (source / name).read_bytes()
  ```

  Run `just test-one tests/test_adapters.py::test_assumption_sweep_authored_files_are_packaged`.
  Expected RED: the packaged skill is absent. The assertion guards loss of the
  authored skill/template in generation; it does not grade scientific content.

- [ ] **Step 5: Write the smallest complete skill and template.** Frontmatter name
  is `sweep-assumptions`; description begins “Use when…” and describes the trigger
  (finding premises behind epistemic records or choosing questions that could
  clarify several unknowns), not the workflow. The body covers spec §§4–6 and
  links the template relatively. State budgets as pilot defaults, not universal
  limits for every topic. Make topic, explicit input locations, budget and output
  destination run inputs; missing data is unknown, not an invented corpus.
  Include one concise example of an inferred premise and its dependent inference.
  Use the observed control failures to shape guidance without omitting any
  accepted spec requirement. Keep mm cohort policy in the mm run setup; the
  reusable skill requires the active program's read/exposure policy before reads.

  Template sections are exactly coverage, premise inventory, dependency paths,
  reach, consequences, tractability, three candidate questions, representation
  gaps. Include all spec §7 fields, row IDs, authors, source locators/revisions,
  provenance counts, unevaluated items and sensitivity to inferred links. Add a
  discovery-freeze attachment/hash slot before the phase-B tables. No persistent
  graph or additional deterministic endpoint is created.

- [ ] **Step 6: Verify guided behavior and generate adapters.** Run five fresh
  samples of the same compact scenario with the skill and template. Manually read
  all outputs and compare with the control/oracle. Every guided sample must
  preserve the counted endpoint sets, source permissions, provenance and missing
  feasibility; report variation rather than selecting the best answer. A new
  failure gets a focused wording correction and another recorded guided check.
  Attach `skill-controls-v1-report.md` with prompts, outputs, scoring, identities
  and limitations. This bounded check is not the full rehearsal in Task 2.

  From this worktree's `python/`, run `uv run science adapters build`; it writes
  only the worktree's committed adapter tree. Run `just test-one tests/test_adapters.py`
  from the worktree root: inclusion and fresh-tree equality must pass. Update
  README with the invocation, eight-part output and the read-only report boundary.

- [ ] **Step 7: Verify and commit the deliverable.** With policy enabled/absent,
  run `just test-fast` and `just check`; with valid policy-off use the fresh focused
  adapter evidence and `just check`. Inspect generated changes for unrelated
  command drift. Commit only the named source, fixture, test, adapter and README
  paths with `feat: add assumption sweep research skill`. Record actual check
  counts and control results on the child before closing it.

### Task 2: Rehearse the complete report and retrieval boundary

**Files:** consume Task 1's committed skill and fixtures; correction edits remain
in those files. Produce versioned task attachments, not a new runtime subsystem.

**Interfaces:** consumes the packaged skill/template and oracle. Produces an
accepted manual dry-run report, read log, frozen synthetic inventory and full
fresh review; includes the decision whether a usable section-only route exists.

- [ ] **Step 1: Run one complete synthetic sweep.** Give a fresh worker the skill,
  scenario and a fixture-only source interface, keeping the oracle with the
  controller/reviewer. The worker requests permitted sections and returns its
  complete report and read log as text; the controller serves only the requested
  fixture block and records the requests. This prevents “isolation” from meaning
  reading a whole fixture body first and then omitting it from the report.
  Pause the worker after discovery and have it return the inventory before
  comparative assessment. The controller freezes/attaches
  `rehearsal-discovery-v1.md`, then resumes the worker with that attachment's
  identity/hash for phase B. Finally attach `rehearsal-v1-report.md` and
  `rehearsal-v1-read-log.md`.

- [ ] **Step 2: Demonstrate the retrieval mechanism on synthetic content.** Use
  an available tool's explicit field/section projection, or a run-local standard
  library XML section extractor if needed; keep its exact invocation/source in
  the read log. This is a disposable research aid, not a shipped command or
  adapter. Exercise separate abstract, methods/data-availability and reference
  sections with sentinel result text in the abstract/body. Before it handles real
  input, an assert-based self-check must show selected-section output excludes
  the sentinel, extracts requested accessions/reference identities, and fails
  closed for absent/ambiguous sections or malformed input. No whole-document
  fallback. A worker that extracts by semantically reading the full paper has
  already crossed the boundary and fails this check.

  Record tool availability honestly: the fixture proves selection mechanics,
  not the live provider's output shape. The live route gets one bounded probe
  within Task 3's source budget, using a source whose relevant cohorts are
  already permitted; if it cannot isolate sections, mark that route unavailable
  and skip sources requiring it. Metadata-first quarry reads remain usable.

- [ ] **Step 3: Obtain a fresh read-only rehearsal review.** Freeze the skill,
  fixture and report revisions/hashes. The reviewer reads the oracle and full
  returned outputs, checks all five Review Focus cases, verifies the reach sets
  by hand, and checks all eight sections and retention of the unavailable-data
  candidate. It explicitly checks review navigation, multi-cohort attribution,
  actual versus possible exposure, and that an incident stops only its source.
  Record the review note and attach its full report before acting. Any Important
  failure blocks the real pilot; correct its demonstrated cause and rerun the
  affected scenario plus full dry-run contract check. Do not call a document
  review alone proof that the skill was exercised.

- [ ] **Step 4: Close the rehearsal step only on acceptance.** Attach the accepted
  report/read log/review and source hashes; note which live capabilities remain
  unverified. Any skill change regenerates adapters and repeats focused adapter
  checks; apply the same policy-appropriate pre-commit checks as Task 1. Commit
  corrections as `fix: clarify assumption sweep rehearsal failures` when needed;
  evidence-only closure needs no invented product change.

### Task 3: Run and review the bounded mm pilot

**Files:** read the spec's named mm/beliefs/science inputs; produce parent task
attachments `pilot-source-ledger-v1.md`, `discovery-inventory-v1.md`,
`pilot-v1-report.md`, and `pilot-v1-review-report.md`. Working material remains in
the retained task directory. No edits to mm policy, records or reservations.

**Interfaces:** consumes Task 2 acceptance, the skill, explicit world/config
locations, current mm roster/policy/assignment metadata and bounded literature
retrieval. Produces the eight-part pilot report with a preserved broad inventory
and three justified candidates, or an explicit incomplete result with its cause.

- [ ] **Step 1: Freeze the run setup before extraction.** Inspect current paths,
  revisions, contract dimensions, world coverage and read capabilities; verify
  retained input hashes before reuse. Use supported science reads where available,
  label raw record-file inspection as unvalidated, and treat the old reproduction
  as separate from the configured world. No dataset holdings claim follows from
  a file existing. Record current exposure/assignment evidence, the broad question
  families, search selection rules, exact budgets and output version. Resolve the
  installed quarry executable and inspect its current metadata output contract
  before querying. Record source/record availability rather than manufacturing
  missing hypotheses or source assertions.

- [ ] **Step 2: Screen sources under the frozen bounds.** Start with a broad
  PubMed metadata query and coverage across the six spec families, reserving
  capacity for counterexamples and uncovered families. Use `quarry search --in
  pubmed -n <remaining-screen-budget> <query>` with the actual query and service
  ordering recorded. Do not use an unrestricted biology default search or display
  abstract-bearing generic search snippets. Count every literature search attempt
  toward 24, unique screened identities toward 80, and every primary article
  deliberately opened for full-text content toward 18 (including unsuccessful
  attempts); log failed/partial access separately. Identity resolution and section
  fetches are logged even when they do not add a unique source. Stop at the first
  exhausted applicable cap; no invisible retries or unrecorded replacement papers.

  Match PMID/DOI and aliases before results; check all implicated cohorts and
  exposure groups. Attempt isolated data-availability/methods or reference-list
  reads only by the rehearsed mechanism, proving its live response shape on one
  permitted source first. Lack of a usable route leaves sources metadata-only.
  Seek the spec's two primary sources per family and up to six extra sources,
  without treating this as a promised yield or choosing papers around attractors.
  Retain metadata-only candidates and uncovered families in the source ledger.
  An incident gets a task note with what was seen and known/unknown mapping;
  route a bounded follow-up to mm's existing exposure/assignment work, without
  changing that policy or claiming disposition. Continue other permitted sources.

- [ ] **Step 3: Freeze the broad discovery inventory.** Extract exact authored
  premises and separate inferred/adopted proposals, classify scope using all
  recorded locations, retain question alternatives and explicit omissions, and
  deduplicate source identities without collapsing distinct meanings or scopes.
  Record corpus/record revisions, query membership and proposed reliance links
  separately. Save the self-contained inventory, compute SHA-256, attach it and
  verify `tasks show` lists it before any available-data feasibility comparison.
  Attach the source ledger too. Later additions require a new version and changed
  comparison; never edit the frozen attachment.

- [ ] **Step 4: Assess and write the eight-part report.** Count distinct direct
  and transitive downstream questions/claims; list source and judgment provenance
  and unevaluated consequences. Judge reverse/narrow/reinterpret/refine effects
  per dependent with alternatives and supporting material. Assess remaining
  uncertainty and inspect roster/package schema/design metadata for required
  assays, population, timing, access, actual holding evidence or unknown, overlap
  and identification limits. Do not open matrices, patient rows, private report
  outputs or mask keys. Quote relevant spec falsification verbatim as an authored
  lead, with a separate premise-linking judgment.

  Compare three finalists and nearest alternatives without a score; retain
  high-impact infeasible questions and test sensitivity to inferred links.
  Explain coverage bias toward metadata and previously exposed publications.
  Classify concrete representation gaps, including whether a proposition plus
  reliance relation suffices or scope/vocabulary/read surfaces fail first. Attach
  the report with frozen input references. If fewer than three candidates are
  defensible, attach the incomplete report and park with the actual missing
  capability or scope decision; the task remains open.

- [ ] **Step 5: Obtain final review and integrate completed work.** A fresh
  read-only reviewer checks the whole branch, synthetic evidence and report
  against the accepted spec, tracing each shortlisted judgment to evidence
  already permitted/read and verifying arithmetic and inventory attachments.
  Review does not grant access to omitted/protected source results. Record its
  full report and outcome note. Apply the governing corrective-round rule to
  Critical/Important findings; preserve any deferred minors and rulings in the
  ledger and final report. Corrections that change discovery require a new
  inventory version, not retroactive editing of phase A.

  Run policy-appropriate checks for any resulting code/skill changes and mandatory
  hygiene. When accepted, close the child and parent with evidence/retention
  accounted for; in this personal repository merge the finished reviewed branch
  locally. Pushes remain permission-gated. Before worktree removal run `tt-report`,
  inspect ignored contents and host pointers, retain needed evidence through
  verified attachments, then unlock/remove under the project's rules. If the
  pilot is incomplete, keep its task and worktree with a concrete next action.

## Plan self-review and handoff

Spec coverage: §§1–4 constrain every task; §5 discovery/freeze is rehearsed in
Task 2 and performed in Task 3; §§6–7 judgments/report are implemented in Task 1
and reviewed in Tasks 2–3; §8 packaging, behavioral checks and real acceptance
have distinct evidence; §9 gates remain explicit. All five Review Focus cases
have manual fixture outcomes and final-review obligations. No new runtime API
needs signature coordination. Each task produces an independently reviewable
deliverable; implementation and evidence stay distinct.

This plan requires user review before execution. Approval authorizes the bounded
repository work and pilot within these read limits, not external publication,
paid access, policy amendments or protected data reads. The default is inline
implementation with fresh behavioral/review workers where the skills and spec
require them; no implementation agent fan-out is needed.
