# One complete causal-analysis workflow — brief

**Date:** 2026-10-24 · **Goal:** sci-35af80 · **Design:** sci-4e0f7f

## 1. Problem

Answer one real causal question from an authored graph through identification,
analysis and interpretation, with reproducible inputs and returned results.
Composite presentation (sci-33eb94), scope comparison (sci-87c165) and tool
integration (sci-1fa085) are parts of that first milestone. Structural sensitivity
(sci-434b9c) and model criticism (sci-37f0c3) build on it later.

## 2. Current behaviour and evidence

Checked science at `6d936f3`. `tools/cli.toml` declares `spec`, `run`, `assess` and
`verify`, but no composite author/read or causal-identification command.
`python/src/science/commands/spec.py` builds typed estimands and applicability;
`python/src/science/commands/next.py` classifies propositions into five readiness classes without
reading composites. No science handler reads `read_composite`, `commensurable`
or `co_scoped`. The typed-spec command landed in `7babc47`.

The built beliefs designs, read through `tasks doc beliefs-d6060a composites`
and `tasks doc beliefs-d6060a estimand`, place composite presentation and scope
comparison here. Their limitations distinguish member belief from structural
directness, closed node sets from sketches, authored identification from computed
verdicts, and typed equality from semantic measurement correspondence. The
historical report at `tasks doc beliefs-8060d0 context` records exporter-only
integration failures; its statement that science had no tasks is superseded by
the existing goal and design task. No workflow draft is attached or present yet;
`docs/specs/causal-analysis-workflow-design.md` is a declared future output.

## 3. Constraints

Follow `docs/specs/2026-08-31-command-framework-design.md`: declare new commands
in `tools/cli.toml`, use deterministic handlers, and put durable writes through
the permit-bound kernel. Keep structure, estimator and generator separate.
Science owns presentation and orchestration; beliefs owns semantics, identity,
provenance and admission; autonomy owns execution priorities.

The first example must bind graph revision, estimand, observed variables,
measurement units/time/population/selection, assumptions and tool version.
Distinguish identified, no valid adjustment set, proven non-identifiability
under stated assumptions, and unsupported/incomplete inputs. Exercise persisted
input/output round trips and independently checked success/refusal cases.
Graph authorship and diagnostics alone never strengthen belief. Weighted-belief
research and the later sensitivity, criticism and `next` ideas do not gate this
milestone. Preserve the selected ideas' detailed acceptance cases.

## 4. Alternatives

- **One worked workflow using one established causal implementation — lean.**
  Reuse sci-4e0f7f to select the question, supported semantics and narrow command
  sequence after the existing semantic research. It provides a concrete check
  on all three first-milestone components.
- **Build authoring, comparison and exporters independently.** Rejected as the
  default: it can finish surfaces without answering a question or consuming a
  returned result, repeating the historical integration gap.
- **Wait for general graph semantics and aggregation policy.** Rejected as a
  prerequisite: the captured milestone deliberately bounds the first example
  and leaves richer semantics and policy changes to their owners.

## 5. Unanswered questions

- What semantic prerequisites does the first observed-data DAG actually need?
  **beliefs-d6060a**, already open under the aggregation research goal, answers
  this without making that broader goal a prerequisite.
- Which real question, available data and estimand exercise those boundaries?
  **sci-4e0f7f** selects and checks a candidate; the user reviews the written
  design before implementation planning.
- Which backend and governed input/result contract can support that example
  and its outcome distinctions? **sci-4e0f7f** compares candidates against the
  semantic report; no dependency or interface is selected by this brief.
- Can fitted artifacts be distinguished at the empirical-input boundary?
  **beliefs-72b6f6** already records that question. The workflow design consumes
  its finding or files a demonstrated prerequisite; no unconditional new wait.
- Which graph alternatives and diagnostic methods are useful after the first
  result? **sci-434b9c** and **sci-37f0c3** are re-scoped after sci-35af80,
  retaining diagnostic computation/storage separately from claim admission.

## 6. Proposed decomposition

- Reuse **sci-35af80**, unchanged, for the first workflow's closure. Do not
  parent later work beneath it: those ideas already depend on its completion.
- Reuse **beliefs-d6060a** for semantic research. It gates sci-4e0f7f and
  sci-37f0c3; its existing completion instructions carry the findings forward.
- Reuse **sci-4e0f7f** (priority 2, medium size, high complexity, planned) for
  the reviewed design, then the normal implementation-plan review. It wakes
  **sci-33eb94**, **sci-87c165** and **sci-1fa085** with the approved revision;
  each waits directly on that design. Integration retains its component waits.
- Keep **sci-434b9c** and **sci-37f0c3** as reviewed follow-on ideas waiting on
  **sci-35af80**. Its closure automatically readmits them; the completed
  example is the evidence for their next scope pass. **sci-171ad1** is related
  context, outside this five-member pass. No new goal or research task is needed.
