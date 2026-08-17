# Conformance Cut 4 Selection Document Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Author the draft cut-4 selection document — Science's first
persistence slice, drawn against the composition-root corpus-write
adapter — as `docs/designs/2026-08-17-conformance-cut-4.md`.

**Architecture:** One new design document following cut 3's structure
(drawn-against, boundary, arm-by-arm selection, deferred-group re-read,
accounting, freeze block), plus no code. Every task ends with the corpus
guard tests green and a docs-only commit. The selection *content* is
produced by reading banked guarantee cells against the boundary rule
below; the plan fixes the rule, the sources, and the cell format, never
the conclusions.

**Tech Stack:** Markdown; `uv run pytest tests/test_designs_corpus.py`
(the document guards); git.

**Spec:** `docs/superpowers/specs/2026-08-17-conformance-cut-4-scope-design.md`
— read it first; every boundary decision below is argued there.

## Global Constraints

- **The boundary (spec §1–§2), verbatim application.** In scope: durable
  minting of new corpus records through the write API's add path; refusal
  of every volume tuple outside the certified binding; compilation
  correctness at the Science boundary (`atoms`' physical certification is
  relied on, never re-run); stored-corpus traversal over the durable
  store. Out: family dialects (supersede, archive, import/cohort as
  *plan families*); the managed holdings root; the world index;
  retraction records; the rules store; the registry compile; the L rows
  and anchor carriage.
- **Selection rule.** An arm is selectable iff its check runs entirely
  inside the in-scope list — no edit, move, deletion, index, registry,
  holdings, retraction, rules-store, or anchor dependency. An arm that
  touches an excluded subsystem defers with that subsystem named in its
  cell. Any unrun arm leaves its row partial (never argue an arm
  "shouldn't count").
- **Chained but unanchored.** Registration is an engine facility; every
  committed transaction carries chain entries from the first commit. The
  limitation is the unbounded unanchored tail. Never write "pre-chain".
- **Frozen documents are never edited.** Cuts 1–3 and every guarantee
  table stay byte-identical. This plan only adds one document.
- **Status header** (exact): `**Status:** Draft — selection pending;
  freezes when the composition-root adapter design banks.` The freeze
  block is written but explicitly not in force.
- **Guard compliance.** Never pair a Plan A stage token (`A1`–`A8`) with
  gating vocabulary (await/block/gate/remain/still/until/wait) outside a
  blockquote. Spell stage and row ranges with an en-dash, never a
  hyphen. Cite `atoms` documents by description ("the `atoms` authority
  design §14"), never by dated filename — only
  `2026-08-03-nodes-under-the-system-redesign-design.md` is registered
  external. Add no guarantee table.
- **Accounting identity:** selected in full + selected in part + fully
  exercised by prior cuts (34) + part-exercised with untouched remainders
  + fully deferred = **151**. No count of arms is offered as a
  denominator.
- Conventional commits; no AI-attribution trailer. After every task:
  `cd python && uv run pytest tests/test_designs_corpus.py -q` → 12
  passed.

---

### Task 1: Scaffold the document — drawn-against and boundary

**Files:**
- Create: `docs/designs/2026-08-17-conformance-cut-4.md`
- Read first: the spec; `docs/designs/2026-08-11-conformance-cut-3.md:43-108`
  (its §1–§2, the structural model)

**Interfaces:**
- Produces: the document skeleton with section headings §1–§7 that Tasks
  2–6 fill; Task 6 renumbers nothing.

- [ ] **Step 1: Write the skeleton.** Title `# Conformance cut 4 — the
  first persistence slice`; the exact status header from Global
  Constraints; a `**Sources:**` line naming the spec path, cut 3, the
  adoption ledger, and (by description) the `atoms` authority design §14
  and Plan B §12.2. Then six empty headings: `## 1. What this cut is
  drawn against`, `## 2. The boundary`, `## 3. Step 1 — what the slice
  crosses`, `## 4. Step 2 — the selection, arm by arm` (with `### 4.1
  Selected in full`, `### 4.2 Selected in part`, `### 4.3 Standing from
  prior cuts`), `## 5. Step 3 — fully deferred rows, grouped by
  unblocking subsystem`, `## 6. Accounting, freeze, and amendment
  discipline`, `## 7. The second reader — reserved`.
- [ ] **Step 2: Write §1.** Three paragraphs from the spec: (a) the cut
  is drawn against the certified engine adopted at Science's composition
  root, compiling generic corpus writes into `TransactionSpec` against
  the certified Linux tuple, every other tuple failing closed; (b) the
  slice is **add-only** — edits, moves, and deletions are the family
  adapters' surface (Plan B item 2); (c) the draft freezes when the
  composition-root adapter design banks, which itself waits on the
  `nodes` write-plan/executor seam.
- [ ] **Step 3: Write §2.** The in/out lists from Global Constraints,
  each exclusion in one sentence naming where it waits. Close with the
  chained-but-unanchored paragraph: the engine appends registration
  entries inside every transaction; anchor carriage and Science-side
  verification are the next persistence cut; the unbounded unanchored
  tail is this cut's stated limitation.
- [ ] **Step 4: Run the guards.**
  Run: `cd python && uv run pytest tests/test_designs_corpus.py -q`
  Expected: 12 passed (the new document has a status header, no stale
  gate pairing, no unregistered filename citation).
- [ ] **Step 5: Commit.**
  `git add docs/designs/2026-08-17-conformance-cut-4.md && git commit -m "docs(cut4): scaffold the first persistence slice"`

### Task 2: The substrate reading — S1, S1a, S3, S7, S8 in; S2, S4, S5 recorded out

**Files:**
- Modify: `docs/designs/2026-08-17-conformance-cut-4.md` (§3, §4.1, §4.2)
- Read first: the S table,
  `docs/designs/2026-08-02-substrate-consolidation-design.md:548-556`

**Interfaces:**
- Consumes: Task 1's skeleton.
- Produces: §3's substrate paragraph; S-row cells in §4.1/§4.2 that Task
  5's group table and Task 6's accounting count.

- [ ] **Step 1: Read each candidate cell and adjudicate arm by arm.**
  For S1, S1a, S3, S7, S8, split the banked test cell under the
  Selection rule. Questions the reading must answer in the cell text:
  do S1/S1a's cross-corpus fixtures need only two durable corpus roots
  (in scope) or the world index (out)? Is S3's negative (fields *and*
  hash edited passes undetected) runnable as a raw write to a durable
  store, or does any half depend on an excluded subsystem? S7's raw
  eligibility-violation write and S8's static no-mutable-handle claim
  are candidates for full selection — say so or say why not.
- [ ] **Step 2: Write the cells.** Fully selected rows go in §4.1 as one
  row each with the complete banked test restated; split rows go in §4.2
  in cut 3's two-column format — selected arms in column 2, deferred
  arms in column 3 with the excluding subsystem bolded. Format, worked
  example (from cut 3 `:250`, the shape Task 3 reuses):

  ```markdown
  | row | selected arms | deferred arms |
  |---|---|---|
  | **T1** | the **import** arm — structurally-validated, unauthenticated, attributed, inert entry of another observer's report, now a **durable store operation** through the composition root | the **raw-write negative**, unchanged from cut 3 — it needs the tamper log's verification act and a valid **anchored observer set**, deferred with anchor carriage |
  ```
- [ ] **Step 3: Record the exclusions.** In §4.3, one line each for S2,
  S4, S5: S2's cell is pure edit (`:550`), S4 observes the
  semantic-change branch (`:552`), S5's remaining walk is a deletion
  (`:553`); each defers whole to the supersede family's cut.
- [ ] **Step 4: Run the guards.** Same command; expected 12 passed.
- [ ] **Step 5: Commit.**
  `git commit -am "docs(cut4): adjudicate the substrate group"`

### Task 3: The store-gated arm splits — T1, R19, R22

**Files:**
- Modify: `docs/designs/2026-08-17-conformance-cut-4.md` (§3, §4.2)
- Read first: cut 3's deferred cells for T1
  (`2026-08-11-conformance-cut-3.md:250`), R19 (`:261`), R22 (`:264`)

**Interfaces:**
- Consumes: Task 2's §4.2 table (rows append to it).
- Produces: T1/R19/R22 cells that Task 6's accounting counts as
  selected-in-part.

- [ ] **Step 1: Adjudicate each deferred cell.** T1: the import arm is
  the worked example in Task 2 Step 2 — use it verbatim; the raw-write
  negative stays deferred. R19: of "explicit import with its
  refusal-before-write, both availability transitions, the audit and its
  contradiction finding, and negatives (c)–(e)", select only what an
  add-only durable store reaches — the refusal-before-write is a
  candidate; the audit and world resolver are excluded subsystems; the
  availability transitions must be adjudicated against whether they need
  holdings (if so, name **holdings** in the deferred cell). R22: the
  raw-write half of negative (b) and negative (c)'s corpus paths are
  candidates; anything needing explicit import machinery beyond the add
  path, the audit, or the rules store defers with that name.
- [ ] **Step 2: Write the three §4.2 rows** in the Task 2 Step 2 format,
  and add one §3 paragraph stating what the run/report boundary gains
  from a durable store (records cut 3 could only hold as values now
  land and reload).
- [ ] **Step 3: Run the guards.** Expected: 12 passed.
- [ ] **Step 4: Commit.**
  `git commit -am "docs(cut4): split the store-gated T and R arms"`

### Task 4: The W sweep

**Files:**
- Modify: `docs/designs/2026-08-17-conformance-cut-4.md` (§3 or §5)
- Read first: the W table,
  `docs/designs/2026-08-02-world-addressing-design.md:1499-1517`
  (all 19 rows: W1–W16, W5a, W8a, W8b)

**Interfaces:**
- Consumes: Task 1's skeleton.
- Produces: either W cells for §4 or a justified unchanged group row
  that Task 5 places in §5.

- [ ] **Step 1: Read all 19 W rows against one question:** does any
  row's check fail at the write boundary alone — no index, no move, no
  consolidate, no redirect, add-only? Expected outcome per the spec: few
  or none; W rows about collision, consolidation, redirects, and uid
  survival all involve the index or a move. Do not force a selection.
- [ ] **Step 2: Write the conclusion.** If no row selects: one §3
  sentence — "no W row's check fails at the write boundary alone; the
  group defers unchanged" — and the group row stays in §5 with
  unblocker "the write boundary and the index, unchanged from cut 3".
  If a row selects: a §4 cell in the standard format naming exactly
  which arm runs add-only.
- [ ] **Step 3: Run the guards.** Expected: 12 passed. (The row-range
  guard checks `W1–W16` endpoints exist; keep the en-dash.)
- [ ] **Step 4: Commit.**
  `git commit -am "docs(cut4): sweep the world-addressing rows"`

### Task 5: Standing, exclusions, and the deferred-group re-read

**Files:**
- Modify: `docs/designs/2026-08-17-conformance-cut-4.md` (§4.3, §5)
- Read first: cut 3 §4.3 (`:268-281`) and §5 (`:283-304`)

**Interfaces:**
- Consumes: Tasks 2–4's selections (they determine which rows leave
  which group).
- Produces: the complete §4.3 and §5 that Task 6's accounting sums.

- [ ] **Step 1: Write §4.3.** Carry cut 3's fully-exercised list (34
  rows) forward verbatim. List every part-exercised row whose remainder
  this cut does not touch, each with its waiting place — start from cut
  3's ten (G2c, G8, G3, S5, S6, P1, D3, D6, D7, M5) plus cut 3's own
  part-selected rows, then add this cut's outright exclusions with their
  citations: G3 (the corpus-move negative — world persistence, kernel
  `:960`), G5 (the kind registry is where "no such kind exists" becomes
  checkable, cut 2 `:283`; the registry compile is out of scope, so the
  refusal would be vacuous under N2's sabotage doctrine), G7 (the walk
  is a semantic edit, kernel `:964`), M5 (the mint-and-edit walk is one
  scenario, carried whole, cut 3 `:280`), D7 (both remaining arms are
  moves needing the write boundary *and* the index, cut 2 `:253`).
- [ ] **Step 2: Write §5.** Reproduce cut 3's group table (`:292-304`)
  with every move stated inline: rows selected by Tasks 2–4 leave their
  groups (substrate becomes S2, S4 with unblocker "the supersede
  family's adapter"); the tamper-log group's unblocker becomes "anchor
  carriage and Science-side verification — the next persistence cut;
  the chain itself is engine-supplied at every commit"; the persistence
  seam (H1–H4, T7), correction lifecycle, normative-contract,
  domain-boundary, formal-model, confinement, packaging, and kernel
  groups carry forward with any wording the new boundary forces, each
  change named.
- [ ] **Step 3: Run the guards.** Expected: 12 passed.
- [ ] **Step 4: Commit.**
  `git commit -am "docs(cut4): standing and the deferred-group re-read"`

### Task 6: Accounting, freeze block, second reader, limitations

**Files:**
- Modify: `docs/designs/2026-08-17-conformance-cut-4.md` (§6, §7, and a
  final `## Limitations` list)

**Interfaces:**
- Consumes: every prior task's row placements.
- Produces: the finished draft.

- [ ] **Step 1: Compute the accounting.** Count the document's own
  placements: N_full (§4.1) + N_part (§4.2) + 34 (prior full) +
  N_standing (§4.3 untouched remainders) + N_deferred (§5) and assert
  the sum is 151 *in the text*, showing the addition as cut 3 §6 does.
  Cross-check mechanically:
  `grep -oE '\*\*[GSWRCXNLDMPHT][0-9]+[a-z]?\*\*' docs/designs/2026-08-17-conformance-cut-4.md | sort -u | wc -l`
  and reconcile any row appearing in two states (a row is classified
  into exactly one).
- [ ] **Step 2: Write the freeze block** in cut 3's form, prefixed:
  this block takes force when the composition-root adapter design
  banks; until then the selection is a draft and edits need no
  amendment. After freeze: results recorded separately, original
  selection preserved verbatim beside any amendment.
- [ ] **Step 3: Write §7 (reserved)** — one paragraph: a second reader
  is required at freeze, per cut 1 limitation 8's precedent; name what
  they check (arm splits against the Selection rule, the accounting,
  the group moves).
- [ ] **Step 4: Write Limitations.** At minimum: (1) the unbounded
  unanchored tail (chained but unanchored, anchor carriage deferred);
  (2) add-only — no edit, move, or deletion obligation is exercised;
  (3) the draft is prospective: the adapter design may move arms, and
  pre-freeze edits are ordinary; (4) durability claims rely on the
  certified tuple's binding, not on re-running the physical exerciser.
- [ ] **Step 5: Full verification.**
  Run: `cd python && uv run pytest -q` (whole suite) and
  `uv run ruff check .` — Expected: all pass, no changes outside the
  one new file plus this plan's checkboxes.
- [ ] **Step 6: Commit.**
  `git commit -am "docs(cut4): accounting, freeze discipline, and limitations"`
