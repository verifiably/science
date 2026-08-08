---
title: Computation and reproducibility
status: living
created: 2026-08-08
updated: 2026-08-08
sources:
  - ../designs/2026-08-02-epistemic-kernel-design.md
  - ../designs/2026-08-02-world-addressing-design.md
  - ../designs/2026-08-02-computation-reproducibility-design.md
  - ../designs/2026-08-03-normative-contract-design.md
  - ../designs/2026-08-03-tamper-evident-log-design.md
---

# Computation and reproducibility

## TL;DR

A run is an immutable, complete execution closure; reproduction compares two
runs under a frozen equivalence rule, and only a passing clean-environment
verification can admit an assessment to empirical belief.

## Why it matters

A command, lockfile, output checksum, or claim that code “runs again” is not
enough to reproduce a scientific computation. The redesign records what was
planned, the exact executable closure, what happened, and how two occurrences
were compared. It also separates the ability to attempt a replay from a
successful verification and from the later epistemic use of its result.

## Key ideas

### The analysis spec freezes the scientific plan

An assessment run begins from an immutable analysis spec that names the target
proposition, estimand, interpretation rule, inputs, parameter contract,
nondeterminism contract, and equivalence rule. Those fields are projected into
the run recipe and cannot be overridden at execution time.

Freezing a spec before execution is preregistration only when chronology is
independently observable. A content hash proves content identity, not when the
content existed. A boundary-mediated `intent` entry and an external anchor can
strengthen that chronology, within the mutation log's observer limits.

### A run has three complete parts

| Part | Records |
|---|---|
| Execution recipe | Run shape; spec identity where applicable; code bundle, environment artifact manifest, and workflow identities; structural invocation; role-partitioned inputs; parameters; nondeterminism, boundary, and rule bindings. |
| Result | A boundary-built manifest of the declared output bytes. |
| Occurrence | A random event token, actor/time/host facts, execution trace, realized seeds, and boundary receipt. |

If one part is missing, the object is not a run. Recipe identity answers
“same declared computation”; occurrence identity distinguishes two executions
of that recipe.

### Capture includes the executable closure

The code bundle includes the actual tracked and untracked files used by the
execution, and execution is confined to that captured closure. The environment
is a manifest of held artifacts, not merely a dependency name or lockfile.
Inputs are content-addressed and role-typed; outputs are admitted from the
boundary's observed manifest rather than trusted from an authored declaration.

These constraints are meant to fail early. An uncaptured dependency,
unavailable input, recipe/spec mismatch, or output outside the declared boundary
refuses run construction instead of producing a lower-quality run.

### One run kind has two shapes

An **assessment run** is bound to an analysis spec, observes empirical inputs,
and may produce one assessment through the assessment constructor. The
assessment copies its target, estimand, and interpretation from the frozen
spec; an authored assessment record is invalid.

A **dataset-production run** transforms inputs and produces one dataset. It has
no proposition, analysis spec, or assessment, and its v1 equivalence rule is
bitwise content equality. This captures lineage without turning every data
preparation step into evidence about a proposition.

### Workflows are imported, not redrawn

The workflow definition is itself a held artifact. Science imports a minimal
normalized DAG from executable workflow content and binds invocation to named
steps. The initial design needs one normalized schema and one Snakemake adapter,
not a general plugin framework. A diagram or manually transcribed DAG is useful
documentation but not execution authority.

### Replay, verification, and belief are different decisions

- **Replay eligibility** asks whether this environment holds enough closure to
  attempt the recipe.
- **Verification** records the comparison of two completed runs under the
  equivalence rule frozen in the spec.
- **Epistemic admission** asks whether a passing verification has the required
  scope to make an assessment eligible for belief.

Verification scope is derived from evidence, not selected by the author:
`same-environment`, `clean-environment`, `independent-implementation`, or
`not-certified`. Clean-environment scope requires equal recipes plus qualifying
fresh-environment and confinement receipts for both runs. Independent
implementation is valuable corroboration of a result but is not a second
observation and does not create another assessment.

The immutable verification record names the ordered run pair, equivalence-rule
identity, comparison report, scope derivation, scope, and verdict. Only
`clean-environment` plus `passed` can admit an assessment under the kernel.
Dataset-production verification establishes reproducibility of a derived
dataset but gates no belief-bearing assessment.

## How it connects

- [Foundations](foundations.md) supplies held artifacts, role-typed relations,
  immutable records, and the closed assessment route.
- [Claims and belief](claims-and-belief.md) consumes admitted assessments and
  never treats replay or verification as an evidence weight.
- [Identity, world, and change](identity-world-and-change.md) distinguishes
  recipe identity from occurrence identity and supplies mutation-log anchors.
- [Contracts and adoption](contracts-and-adoption.md) maps the R1–R23 guarantees
  to the adoption ledger and executable conformance surface.

## Current state

The run model, verification scopes, and guarantees are banked designs. The
current conformance cut shares their identity and profile foundations but does
not implement analysis-spec persistence, closure capture, confined execution,
run construction, verification, or assessment admission.

## Open edges

See [Computation and reproducibility](open-questions.md#computation-and-reproducibility)
for unresolved environment, workflow, nondeterminism, comparison, and external
anchor questions.

## References

- [Run closure and frozen guarantees R1–R23](../designs/2026-08-02-computation-reproducibility-design.md#11-frozen-guarantees)
- [Normative run, verification, and assessment contracts](../designs/2026-08-03-normative-contract-design.md#7-run-construction)
- [Kernel reproduction rule G5](../designs/2026-08-02-epistemic-kernel-design.md#521-reproduction-means-a-separate-execution)
- [World identity and occurrence tokens](../designs/2026-08-02-world-addressing-design.md#45-occurrence-identity)
- [Pre-mutation intent and anchoring](../designs/2026-08-03-tamper-evident-log-design.md#6-pre-mutation-registration)
