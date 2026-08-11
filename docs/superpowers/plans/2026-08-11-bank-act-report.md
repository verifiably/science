# Banking the Act-Report Design Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply §7's amendment set of `docs/designs/2026-08-11-act-report-design.md` across the corpus, so the design banks and the three pre-banking corpus-suite failures resolve.

**Architecture:** Pure documentation-and-guards propagation — no runtime code. Each task edits one document cluster to match one group of §7 items, verified by the corpus suite (`python/tests/test_designs_corpus.py`) and the guide checker (`python/tools/check_guide.py`). The suite goes fully green only at the final task, which extends the guards themselves; every earlier task must leave exactly the three known failures (README count, README table, guide citation) and no new ones — except Task 7, after which the guide-citation failure resolves and exactly the two README failures remain.

**Tech Stack:** Markdown, pytest, `python/tools/check_guide.py`.

## Global Constraints

- The spec is `docs/designs/2026-08-11-act-report-design.md` **§7** ("What this changes elsewhere"). Every §7 item must be traceable to exactly one task below. §7 item 11 rules **cut 2 gets no edit at all** — `docs/designs/2026-08-09-conformance-cut-2.md` must be byte-unchanged at the end of this plan.
- Work on branch `run-boundary` in the worktree `.worktrees/run-boundary`. **Do not push.**
- Conventional commits. **No AI-attribution trailer or footer** on any commit.
- No absolute user paths (`/home/...`, `/mnt/...`) in any doc or comment.
- Banked designs are amended **in place with dated notes** citing this design — the form is `*(amended 2026-08-11, the act-report design §3)*`, section number per the edit (the corpus's italic dated-note style; see the tamper log's existing `*(amended 2026-08-10, the verified-holdings record design §8)*` notes for the shape).
- **Historical statements stay untouched.** The world address ruling's "an eleventh kernel kind" statements, the ramp/cut-2 "139 rows across eleven tables" statements, world addressing's §3 table cell "11 since 2026-08-08", and every "what this amendment changed" count in a banked doc record what was true at their writing. Only the sites a task enumerates change.
- Guarantee ids are never renamed or renumbered. The new table is **T**, rows `T1`–`T8`, owner `2026-08-11-act-report-design.md`. The letter A is not used — it denotes the `atoms` adoption arms.
- Never write an adoption-arm range ending at `A8` that starts anywhere but `A7` — the corpus guard `test_no_design_gates_on_an_implemented_atoms_stage` fails any other range. Prefer "`atoms` A7–A8" verbatim.
- Verification commands (run from `python/`, always in the frozen `uv` environment — never ambient `python`): `uv run --frozen pytest tests/test_designs_corpus.py -q` and `uv run --frozen python tools/check_guide.py; echo "exit=$?"` (exit 0 = pass; it prints nothing on success). Also `git diff --check` from the worktree root before every commit. The final task closes with the full gates from `python/README.md`: `uv run --frozen pytest -q`, `uv run --frozen ruff check .`, `uv run --frozen pyright src`.
- Line numbers below are approximate anchors — locate each edit by the quoted text, not the number.

---

### Task 1: Kernel kind count → thirteen across the exact inventory

§7 items 1 and 2 — the count sites are amended as an **exact inventory, not a sweep**. This task covers every non-guide count site (the guide's are Task 7's), plus the kernel's live table-count pointer: §10's "Where they stand" note.

**Files:**
- Modify: `docs/designs/2026-08-02-epistemic-kernel-design.md` (§4.4 ~line 923; §10 note ~line 1344)
- Modify: `docs/designs/2026-08-04-domain-extension-boundary-design.md` (~lines 34, 271)
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md` (docket note, ~line 59)
- Modify: `docs/designs/2026-08-09-admission-ramp-design.md` (§2.2, ~line 146)
- Modify: `docs/designs/2026-08-08-world-address-ruling.md` (§3, ~line 122)

**Interfaces:**
- Consumes: nothing from other tasks.
- Produces: the thirteen-kind claim later tasks may cite. Task 3 renames the formal-model §2.1 heading; Task 7 fixes the guide's anchor link to it.

- [ ] **Step 1: Kernel §4.4.** In the accounting table's first row (~line 923), change the destination cell header

  `**Kernel (8; 10 since 2026-08-03; 11 since 2026-08-08; 12 since 2026-08-10)**`

  to

  `**Kernel (8; 10 since 2026-08-03; 11 since 2026-08-08; 12 since 2026-08-10; 13 since 2026-08-11)**`

  and in the same cell's kinds list, change the tail

  ``then `holdings-observation` (verified-holdings record design §2, 2026-08-10), which absorb nothing``

  to

  ``then `holdings-observation` (verified-holdings record design §2, 2026-08-10) and `act-report` (act-report design §2, 2026-08-11), which absorb nothing``

- [ ] **Step 2: Kernel §10 table pointer.** In §10's `> **Where they stand**` note (~line 1344), three phrase edits in one sentence pair:

  `**Six later designs have no number in this list at all**` → `**Seven later designs have no number in this list at all**`

  `the belief policy (P), and the` `verified-holdings record (H) *(amended 2026-08-10, the verified-holdings record design §8)*.` → `the belief policy (P), the verified-holdings record (H) *(amended 2026-08-10, the verified-holdings record design §8)*, and the act-report (T) *(amended 2026-08-11, the act-report design §7)*.`

  `Six numbered sub-problems plus those six is where the twelve frozen tables come from;` → `Six numbered sub-problems plus those seven is where the thirteen frozen tables come from;`

  Re-wrap the blockquote to the file's hard-wrap width after editing, keeping the leading `> ` on every line.

- [ ] **Step 3: Domain extension, two clauses.** At ~line 34, change

  `(the twelve kernel kinds — ten until 2026-08-08, eleven until 2026-08-10)`

  to

  `(the thirteen kernel kinds — ten until 2026-08-08, eleven until 2026-08-10, twelve until 2026-08-11)`

  At ~line 271, change

  `` `science` owns the twelve kernel kinds (kernel §4.2; ten until 2026-08-08, eleven until 2026-08-10), ``

  to

  `` `science` owns the thirteen kernel kinds (kernel §4.2; ten until 2026-08-08, eleven until 2026-08-10, twelve until 2026-08-11), ``

- [ ] **Step 4: Adoption-ledger docket note.** At ~line 59, change

  ``(twelve since 2026-08-10 — `holdings-observation`, the verified-holdings record design §2)``

  to

  ``(twelve since 2026-08-10 — `holdings-observation`, the verified-holdings record design §2; thirteen since 2026-08-11 — `act-report`, the act-report design §2)``

- [ ] **Step 5: Ramp §2.2.** At ~line 146, change

  `binds all twelve kinds (eleven` `until 2026-08-10): every`

  to

  `binds all thirteen kinds (eleven until 2026-08-10, twelve until 2026-08-11): every`

  (the phrase spans a hard wrap; re-wrap after editing).

- [ ] **Step 6: World ruling §3.** At ~line 122, change

  ``Two clauses carry over unchanged from §4.2 and now bind all twelve kinds (eleven at this ruling; `holdings-observation` joined 2026-08-10): the refusal``

  to

  ``Two clauses carry over unchanged from §4.2 and now bind all thirteen kinds (eleven at this ruling; `holdings-observation` joined 2026-08-10, `act-report` 2026-08-11): the refusal``

- [ ] **Step 7: Verify.** From `python/`: `uv run --frozen pytest tests/test_designs_corpus.py -q` → exactly the three known failures, no new ones. `uv run --frozen python tools/check_guide.py; echo "exit=$?"` → exit 0. From the worktree root: `git diff --check` → clean.

- [ ] **Step 8: Commit.**

```bash
git add docs/designs/2026-08-02-epistemic-kernel-design.md docs/designs/2026-08-04-domain-extension-boundary-design.md docs/designs/2026-08-03-redesign-adoption-ledger.md docs/designs/2026-08-09-admission-ramp-design.md docs/designs/2026-08-08-world-address-ruling.md
git commit -m "docs(designs): take the kernel to thirteen kinds and thirteen tables across the exact inventory"
```

---

### Task 2: The tamper-evident log amendment

§7 item 4 — one amendment, applied across every site it names: §3's intent union, §6's qualification reduction, the boundary-built `fulfills` restatement, L7's width, and §9's ownership split, plus the audit-wrapper note. Read item 4 **in full** in the act-report design before starting — it is the specification; this task locates each site and states the insertion.

**Files:**
- Modify: `docs/designs/2026-08-03-tamper-evident-log-design.md`

**Interfaces:**
- Consumes: nothing.
- Produces: the operation-intent wording Task 6's ledger note cites.

- [ ] **Step 1: §3 intent union — the third consumer.** Anchor: the holdings-intent paragraph in the `**intent**` bullet (~lines 255–260), ending `*(amended 2026-08-10, the verified-holdings record design §8)*.` Append a sibling paragraph at the same indentation:

  ```markdown
  The **operation intent** is the union's third consumer — one per boundary
  operation (the act-report design §3): `acquisition`, `audit`, `import`,
  `re-check`, or `run-attempt` for a `dataset-production` run, which carries
  no `spec_identity` and is therefore outside the assessment-run intent.
  Payload: the operation kind, the boundary-minted **`event_token`** — the
  report occurrence's own, reused by no member act — and the actor. The
  boundary **freezes the observer-corpus root first**, then appends the
  intent under that root's lease **before any member act begins**; if the
  root selection or the append fails, **no act begins and no record is
  minted**. Assessment runs keep opening the assessment-run intent as
  built, and a run request refused pre-intent (no frozen `spec_identity`)
  opens nothing *(amended 2026-08-11, the act-report design §3)*.
  ```

- [ ] **Step 2: §6 qualification — operation-grain readings and the widened assessment-run qualification.** Anchor: the holdings-intent qualification paragraph (~lines 453–460), ending `never from a caller-supplied path *(amended 2026-08-10, the verified-holdings record design §8)*.` Append a sibling paragraph:

  ```markdown
  An **operation intent**'s qualifying fulfillment reads at its own shape,
  under the same reduction: for a non-run operation, a committed
  registration publishing the **act-report** carrying the intent's
  `event_token`; for a `dataset-production` operation, the minted `run` or,
  when none is minted, that act-report. The **assessment-run intent's
  qualification widens** to the same alternatives — the `run` as built, or
  an act-report of kind `run-attempt` carrying the intent's token, for a
  post-intent attempt that minted no run; a pre-intent refusal publishes an
  *unfulfilling* report and fulfills nothing. The `fulfills` construction
  rule is restated, not relaxed, for this consumer too: the boundary
  constructs the link from its own operation intent, never from a
  caller-supplied path *(amended 2026-08-11, the act-report design §3)*.
  ```

- [ ] **Step 3: L7 — the operation intent's width.** Anchor: the L7 row (~line 569), which currently ends `...exactly as stated *(amended 2026-08-10, the verified-holdings record design §8)*`. Before the row's closing `|`, extend the cell:

  `; the guarantee now quantifies over the **operation intent** too — instantiated for its shape, a report carrying another operation's token, a wrong-kind terminal (an act-report where a `run` was minted, a `run` where the operation takes a report), or a registration publishing no terminal record each **fails qualification**, and a kill between the operation intent's append and its first act reads attempt-without-recorded-outcome, exactly as stated *(amended 2026-08-11, the act-report design §3)*`

- [ ] **Step 4: §9 ownership split — the science side.** Anchor: the **science** obligations paragraph (~lines 532–541), ending `on the` `` `atoms` intent API as built (the verified-holdings record design §3)`` `*(amended 2026-08-10, the verified-holdings record design §8)*.` Extend the sentence before its dated note, or append a sibling clause after it:

  ```markdown
  The boundary also writes **operation intents** — the observer-corpus root
  frozen before the append, the append durable before any member act — and
  constructs their `fulfills` for the closing terminal record (the
  act-report, or the run where one is minted), on the same `atoms` intent
  API as built. An `audit` operation's intent is the **boundary
  wrapper's**, never the read-only evaluator's — the evaluator appends
  nothing *(amended 2026-08-11, the act-report design §3, §4)*.
  ```

- [ ] **Step 5: Verify + commit.** Same checks as Task 1 Step 7 (three known failures only; guide checker exit 0; `git diff --check` clean).

```bash
git add docs/designs/2026-08-03-tamper-evident-log-design.md
git commit -m "docs(designs): give the tamper log its third intent consumer, the operation intent"
```

---

### Task 3: World addressing §4.2 row + formal model

§7 items 8 and 3.

**Files:**
- Modify: `docs/designs/2026-08-02-world-addressing-design.md` (§4.2 identity-basis table; last row is `holdings-observation`, ~line 334)
- Modify: `docs/designs/2026-08-04-formal-model-and-claim-calculus-design.md` (§2.1 heading ~line 138, lead ~line 140, player table end ~line 160; §3.2 audit block ~lines 374–392; the transition table's `begin` (run) row ~line 456; §5.1 count notes ~lines 867–880; §5.2 after the **H** block, before `### 5.3`)

**Interfaces:**
- Consumes: nothing.
- Produces: the renamed §2.1 heading anchor `#21-rec--world-records-the-thirteen-kernel-kinds`, which Task 7's foundations link must match exactly (derive the anchor from the final heading text — lowercase, punctuation dropped, spaces to hyphens).

- [ ] **Step 1: Identity-basis row.** In world addressing §4.2's table, append after the `holdings-observation` row:

  ``| `act-report` | content identity of the whole canonical facet under **`science.act-report.v1`** — every field participating: the operation kind, the report occurrence's minted **event token**, actor, observer, instrument, `opened_at`/`closed_at`, and `entries` as a **canonical sequence**, order identity-bearing — added 2026-08-11, act-report design §2.3 | the `run` occurrence precedent: the event token keeps two operations with equal actors, timestamps and entries distinct (T8); the ordered `entries` encoding makes a permutation a different report (T6), because a finding is cited as **(act-report ref, entry index)** and position must therefore be identity-bearing |``

- [ ] **Step 2: Formal model §2.1 heading and lead.** Change the heading

  `` ### 2.1 `Rec` — world records (the twelve kernel kinds) ``

  to

  `` ### 2.1 `Rec` — world records (the thirteen kernel kinds) ``

  and in the lead sentence (~line 140) `All twelve` → `All thirteen`. After the existing note `*(Extended 2026-08-10: `holdings-observation` joined — the verified-holdings record design §2, §8.)*`, append a sibling: `*(Extended 2026-08-11: `act-report` joined — the act-report design §2, §7.)*`

- [ ] **Step 3: Formal model player row.** Append to the §2.1 table, after the `holdings-observation` row:

  ``| `act-report` | minted only by the boundary — the terminal record of one opened operation (`acquisition`, `audit`, `import`, `re-check`, or a run attempt that minted no `run`), or the pre-intent refusal record of a run request rejected before an operation can open (act-report design §2–§3); added 2026-08-11 | content identity over the whole facet under `science.act-report.v1` — operation kind, the report occurrence's minted **event token**, actor, observer, instrument, timestamps, and `entries` as a canonical sequence, order identity-bearing | immutable; **never superseded**, retained — no ordinary API edits, supersedes, or deletes one | records member acts and their outcomes in per-kind native vocabularies; a finding is citable as **(act-report ref, entry index)** | nothing — inert by type: no eligibility predicate, no admission derivation, no belief closure member, no coverage projection | everything in belief; `opened_at`/`closed_at` (recorded, never read by a derivation); referenced products retain their own semantics | act-report design §2–§5; **T1–T8** |``

- [ ] **Step 4: §3.2 audit note.** After the paragraph ending `Detection stays split from correction.` (~line 388), append:

  `*(Amended 2026-08-11, the act-report design §4: the type is unchanged and the evaluator still mints nothing — the `audit` operation's inert act-report is published by the boundary wrapper that ran the evaluator, under the wrapper's own operation intent.)*`

- [ ] **Step 5: The `begin` (run) transition row.** In the transition table (~line 456), change

  `| `begin` (run) | **refuses** without an already-frozen spec identity, and records it before any other observation | kernel **G2a** |`

  to

  `| `begin` (run) | for **assessment runs**: **refuses** without an already-frozen spec identity, and records it before any other observation; a `dataset-production` run carries no spec and opens the **operation intent** instead *(amended 2026-08-11, the act-report design §3.2)* | kernel **G2a** |`

- [ ] **Step 6: §5.1 count note.** After the existing note ending `The assertion count moves with H's arms; the classification is per assertion, as ever.)*` (~line 879), append a sibling note:

  `*(Extended 2026-08-11: the act-report design banked **T (8)** — the classified inventory is now **129 rows** across eleven tables and **180 assertions**. The assertion count moves with T's arms; the classification is per assertion, as ever.)*`

  Before writing the numbers, verify them: 121 + 8 = 129 rows; count the `/`-separated arms in Step 7's block (T1: 3, T2: 7, T3: 5, T4: 3, T5: 4, T6: 3, T7: 2, T8: 3 = 30) and confirm 150 + 30 = 180 against the block as actually written. If the block's arm decomposition changes in review, this note moves with it.

- [ ] **Step 7: §5.2 T block.** Between the **H — verified holdings record** block's last row and `### 5.3`, append (classes use §5.1's taxonomy — WD, OI, OInv, CS, WF, FC, DL — and §5.4's proposed `†` labels, as the existing blocks do):

  ```markdown
  **T — act-report** *(added 2026-08-11, the act-report design §5)*

  | id | assertions | classes |
  |---|---|---|
  | T1 | no construction path authors an act-report — boundary-minted only, no API takes report fields as input / an imported report enters structurally validated but not operation-authenticated, attributed and inert, with no validation state written / a raw-written self-consistent report is undetected on read, and an audit detects it only with the tamper log implemented and a valid anchored observer set | CA† + US† / **DL** / **DL** |
  | T2 | one started operation carries one intent and exactly one qualifying terminal — the `run` where one is minted, the act-report otherwise / a post-intent attempt minting no run closes through exactly one qualifying act-report / a second fulfilling registration on one intent is malformed / a root-selection or intent-append failure means no act began and no record was minted — an in-memory `event_token` carried by no intent and no record is not a mint / a pre-intent missing-spec refusal publishes an unfulfilling report that fulfills nothing, a crash there leaving no trace / a complete non-conforming execution mints a `run`, never an act-report / a dataset-production attempt opens the operation intent, the assessment-run intent unspellable without a `spec_identity` | **WD** + **CS** / **WD** / **ED†** / **FC** + EO† / **DL** + **FC** / **ED†** / US† |
  | T3 | an unmatched intent reads unfinished / an unreadable fulfillment pointer reads indeterminate, never collapsed into unfinished / a fulfilled intent reads closed / no status field is spellable on any record — report, intent payload, or run / deleting a published report moves its operation closed → indeterminate, not unfinished | **WD** / **WD** + **FC** / **WD** / US† / **CS** |
  | T4 | adding and removing reports and entries leaves the belief digest, admission, eligibility and the coverage projection byte-unchanged / an unfinished operation blocks nothing — a location with no unmatched holdings intent projects normally while its operation's intent stands unmatched / deleting an observation a report references has exactly the record-layer consequences, the report unchanged and conferring no protection | **OInv** / **OInv** / **OInv** + **DL** |
  | T5 | `byte-locator-untested` is unspellable on a managed-mutation, record-import, or subject-evaluation entry / it is refused on a locator act whose request began — `retrieval-failed`'s territory / a preflight refusal and a deliberate post-stop skip both spell it, with distinct reasons / no entry outcome constructs an observation — reports reference products and never mint them | US† / RF† / **ED†** / US† |
  | T6 | permuting two entries moves the report identity — order is identity-bearing / an (act-report ref, entry index) citation resolves to exactly one entry, an out-of-range index refused at the citing site / deleting the cited report leaves the verification unchanged and still valid, its embedded content intact — the R18 arm | **CS** / **WD** + RF† / **OInv** |
  | T7 | a successful acquisition's provenance reference and act-report publish in one registered transaction in one root, the split attempt refused, never half-ordered / mutating the report moves the dataset's record bytes — its node-content identity — and the corpus-state identity, while the dataset **address** is byte-unchanged (the §6.2 basis excludes provenance) | RF† + EO† / **CS** + **OInv** |
  | T8 | two operations with equal actors, timestamps and entries but distinct operation `event_token`s are two report identities / mutating each facet member in turn moves the identity every time / no ordinary API edits, supersedes, or deletes a report | **CS** / **CS** / US† |
  ```

  Each row follows the H precedent — one row, `/`-separated assertion arms, one class group per arm. Before committing, cross-check each row's arms against the T table in the act-report design §5 (every mutation-test clause must be represented; no arm invented) and confirm the arm counts match Step 6's note.

- [ ] **Step 8: Verify + commit.** Same checks (three known failures only; guide checker exit 0; diff-check clean). The suite's guarantee-range test cannot yet see `T1–T8` (the `_ROW_RANGE` class excludes T until Task 8) — confirm no new failure appears.

```bash
git add docs/designs/2026-08-02-world-addressing-design.md docs/designs/2026-08-04-formal-model-and-claim-calculus-design.md
git commit -m "docs(designs): add act-report to world addressing and the formal model"
```

---

### Task 4: The computation amendments

§7 item 5 — §4.7's provenance member, §7.3c's constructor argument, R18's embedding note, R19's widened-but-closed signature note, R12's cooperative-closure note, and the audit-wrapper note at §7.3c.

**Files:**
- Modify: `docs/designs/2026-08-02-computation-reproducibility-design.md` (§4.7 provenance blockquote ~line 1019; §7.3c constructor rule blockquote ~line 2129; the `audit mints nothing` blockquote sentence ~line 2187; R12 row ~line 2468; R18 row ~line 2474; R19 row ~line 2475)

**Interfaces:**
- Consumes: nothing.
- Produces: the constructor-argument wording Task 7's guide edits may summarize.

- [ ] **Step 1: §4.7 acquisition provenance member.** In the `> **Acquisition provenance record.**` blockquote, change the field list's tail

  `and the **resulting content identity**.`

  to

  `the **resulting content identity**, and — added 2026-08-11 (the act-report design §4) — a **reference to the acquiring operation's act-report**: operational detail and references, never a second acquisition-provenance object. The existing fields remain authoritative, and for a successful acquisition the reference and the report publish in the **same registered transaction, in the same root** (T7); cross-root publication is refused.`

- [ ] **Step 2: §7.3c constructor rule.** In the `> **Rule.** There is **one constructor** for a `verification`.` blockquote (~line 2129), change

  `the **ordered run refs**, an **optional code-lineage certification**, and — added 2026-08-03 (5b §7.6) — the **explicitly selected contract identity and epoch** for certification discovery — nothing else.`

  to

  `the **ordered run refs**, an **optional code-lineage certification**, an **optional acquisition report-position citation** — added 2026-08-11 (the act-report design §4): the cited finding's resolved content embeds inline in the comparison report with **(act-report ref, entry index)** as provenance, and the code-lineage certification remains the **only** authored claim input — and — added 2026-08-03 (5b §7.6) — the **explicitly selected contract identity and epoch** for certification discovery — nothing else.`

  Re-wrap the blockquote after editing.

- [ ] **Step 3: §7.3c audit note.** At the blockquote sentence `says so and the audit **mints nothing** (amended 2026-08-03, 5b §7.6: the ...)` (~line 2187), append to the end of that sentence's parenthetical or immediately after it:

  `*(and 2026-08-11, the act-report design §4: the finding is recorded as an entry in the boundary wrapper's inert act-report — the evaluator still mints nothing epistemic)*`

- [ ] **Step 4: R12 note.** At the end of the R12 row's mutation-test cell (~line 2468), before the closing `|`, append:

  ` *(Amended 2026-08-11, the act-report design §3: cooperative no-run closure now exists — a post-intent attempt that minted no run may close through a qualifying act-report — and the formal claim is unchanged: the out-of-band negative stands, and an unmatched intent still proves exactly an attempt with no qualifying recorded outcome.)*`

- [ ] **Step 5: R18 note.** At the end of the R18 row's mutation-test cell (~line 2474), before the closing `|`, append:

  ` *(Amended 2026-08-11, the act-report design §4: an acquisition report-position citation embeds on this same discipline — resolved content inline, **(act-report ref, entry index)** as provenance — and deleting the cited report leaves the verification unchanged and still valid, T6's R18 arm.)*`

- [ ] **Step 6: R19 note.** At the end of the R19 row's mutation-test cell (~line 2475), before the closing `|`, append:

  ` *(Amended 2026-08-11, the act-report design §4: the constructor's closed list gains one member — the optional acquisition report-position citation. Every other extra argument is still refused, deleting the cited report invalidates nothing, and the audit arm is unchanged: the evaluator mints nothing, its finding recorded as an entry in the boundary wrapper's inert act-report.)*`

- [ ] **Step 7: Verify + commit.** Same checks (three known failures only).

```bash
git add docs/designs/2026-08-02-computation-reproducibility-design.md
git commit -m "docs(designs): thread the act-report through provenance, the verification constructor and R12/R18/R19"
```

---

### Task 5: Closure notes — holdings design and ramp §6.6

§7 items 6 and 7.

**Files:**
- Modify: `docs/designs/2026-08-10-verified-holdings-record-design.md` (§3's two "owed to the run/report design" passages, ~lines 260 and ~404; §7 item 6, ~line 995)
- Modify: `docs/designs/2026-08-09-admission-ramp-design.md` (§6.6, ~line 904)

**Interfaces:** none.

- [ ] **Step 1: Holdings §3, first passage.** The paragraph at ~lines 255–270 says whether the acquisition has ended is `orchestration state, owed to the run/report design` and ends by naming the non-report as `precisely what the run/report seam exists to record`. At the end of that paragraph, append:

  `*(Designed 2026-08-11: the act-report design — the operation intent, the three-valued completion reading, and the act-report whose entries record the look's non-report.)*`

- [ ] **Step 2: Holdings §3, second passage.** The bullet at ~lines 400–405 ends `an act short of its terminus is what leaves it the unfinished acquisition §6.6 already names.` Append:

  `*(Designed 2026-08-11, the act-report design §3: whether the acquisition has ended is now the operation intent's derived three-valued reading.)*`

- [ ] **Step 3: Holdings §7 item 6.** Item 6 (`**Acquisition completion as orchestration state.**`, ~line 995) ends `alongside the act reports it owns.` Append:

  `*Closed 2026-08-11 by the act-report design: completion is the operation intent's derived three-valued reading (§3 there), and the look's non-report lands in the closing report's entries — or, operator-crashed, as the durable unmatched intent.*`

- [ ] **Step 4: Ramp §6.6.** After the sentence ending `is an unfinished acquisition, not a dataset in a third condition.` (~line 904), append:

  `*(Amended 2026-08-11, the act-report design §3.3: "unfinished acquisition" is now the acquisition operation intent's **unmatched** state under the three-valued completion reading — unfinished, indeterminate, closed.)*`

  §8's item statuses are untouched — nothing else in the ramp changes in this task.

- [ ] **Step 5: Verify + commit.** Same checks (three known failures only).

```bash
git add docs/designs/2026-08-10-verified-holdings-record-design.md docs/designs/2026-08-09-admission-ramp-design.md
git commit -m "docs(designs): close the holdings deferrals and ramp 6.6 at the act-report design"
```

---

### Task 6: Adoption ledger + normative contract

§7 items 10 and 9. The docket note's count site landed in Task 1; cut 2 gets no edit (item 11).

**Files:**
- Modify: `docs/designs/2026-08-03-redesign-adoption-ledger.md` (artifact 5 row, ~line 49; artifact 7 row, ~line 51)
- Modify: `docs/designs/2026-08-03-normative-contract-design.md` (§4's oracle inventory, ~lines 123–133; §7.6's detection/correction split, ~sentence `Audit therefore **emits the refutation finding and mints nothing**`; §11's first-cut note, ~lines 700–702)

**Interfaces:**
- Consumes: Task 2's operation-intent wording (the ledger note cites the same discipline).
- Produces: nothing later tasks read.

- [ ] **Step 1: Artifact 5 log-consumer note.** In the artifact 5 (tamper-evident mutation log) row's state cell (~line 49), before the closing `|`, append:

  ` **Log-consumer note (2026-08-11, act-report design §3):** the intent union gains its third consumer, the **operation intent** — science-side consumer rules amended: the boundary freezes the observer-corpus root, appends the intent before any member act, and constructs its `fulfills` for the closing terminal record; the `atoms` intent API is unchanged.`

- [ ] **Step 2: Artifact 7 row.** In the oracle-inventory cell (~line 51), extend

  `**H1–H4** (added 2026-08-10, the verified-holdings record design §6 — the H table joins the suite on the same rule that added N, L and D)`

  to

  `**H1–H4** (added 2026-08-10, the verified-holdings record design §6 — the H table joins the suite on the same rule that added N, L and D); **T1–T8** (added 2026-08-11, the act-report design §5 — the T table joins on the same rule)`

- [ ] **Step 3: Contract §4 inventory.** In the `**Oracles freeze by (contract identity, oracle id)**` enumeration (~lines 123–133), extend the same H clause with the same T clause as Step 2 (identical wording), keeping `: the exact current inventory, with no base G2 — are permanent names.` as the closing words.

- [ ] **Step 4: Contract §7.6 wrapper note.** After the sentence `Audit therefore **emits the refutation finding and mints nothing**; the superseding verification is a separate, explicit constructor act, supplied with its own cut and epoch selection like any other derivation (N7).` append:

  `*(Amended 2026-08-11, the act-report design §4: the evaluator is unchanged and still mints nothing — the finding's durable home is an entry in the boundary wrapper's inert act-report, published under the wrapper's own operation intent.)*`

- [ ] **Step 5: Contract §11 count.** In the first-cut note (~lines 700–702), change

  `The cut's scope is whatever the ledger's artifact-7 row inventories — twelve` `tables and 143 rows as of 2026-08-10, D, M, P and H having arrived since, and`

  to

  `The cut's scope is whatever the ledger's artifact-7 row inventories — thirteen tables and 151 rows as of 2026-08-11, D, M, P, H and T having arrived since, and`

  (the phrase spans a hard wrap; re-wrap after editing; the rest of the sentence stands).

- [ ] **Step 6: Verify + commit.** Same checks (three known failures only).

```bash
git add docs/designs/2026-08-03-redesign-adoption-ledger.md docs/designs/2026-08-03-normative-contract-design.md
git commit -m "docs(designs): record the operation intent and the T table in the ledger and contract"
```

---

### Task 7: Guide propagation

§7 item 12 — foundations, open-questions, glossary, contracts-and-adoption, with `updated:` frontmatter and `sources:` entries per convention. This task makes `test_the_guide_cites_every_design` pass.

**Files:**
- Modify: `docs/guide/foundations.md` (frontmatter; kinds heading/lead/table ~lines 79–90; References ~line 160)
- Modify: `docs/guide/open-questions.md` (third-cut entry ~lines 175–184; new residue entry; frontmatter)
- Modify: `docs/guide/glossary.md` (four insertions, alphabetical; frontmatter)
- Modify: `docs/guide/contracts-and-adoption.md` (~line 88; frontmatter)

**Interfaces:**
- Consumes: Task 3's renamed formal-model heading anchor (foundations' References link must match it exactly).

- [ ] **Step 1: foundations.md.** Four edits:
  1. Frontmatter: `updated: 2026-08-10` → `updated: 2026-08-11`; `sources:` gains `  - ../designs/2026-08-11-act-report-design.md` (keep the list's file order convention — append after the holdings entry).
  2. Heading `### The twelve world-record kinds` → `### The thirteen world-record kinds`; lead `The formal inventory contains twelve kernel kinds:` → `The formal inventory contains thirteen kernel kinds:`.
  3. In the kinds table, append after the `Identity` row:

     ``| Operations | `act-report` | Record, inertly, one boundary operation's member acts and their outcomes — the terminal record of an opened operation, or the refusal record of a run request rejected before one can open. |``
  4. References: `[Formal model: the twelve kinds and M1–M13](../designs/2026-08-04-formal-model-and-claim-calculus-design.md#21-rec--world-records-the-twelve-kernel-kinds)` → `[Formal model: the thirteen kinds and M1–M13](../designs/2026-08-04-formal-model-and-claim-calculus-design.md#21-rec--world-records-the-thirteen-kernel-kinds)` — the fragment must match Task 3's final heading exactly.

- [ ] **Step 2: open-questions.md — the third-cut entry.** In `- **The third conformance cut.**` change

  `run capture's holdings prerequisite was designed` `2026-08-10 (unblocked by the holdings design), world persistence waits on` `` `atoms` A7–A8 and the `nodes` contract deltas.``

  to

  `` run capture's seam is now fully designed — the holdings prerequisite 2026-08-10, and completion, act reports and the look's non-report 2026-08-11 (the act-report design) — while world persistence waits on `atoms` A7–A8 and the `nodes` contract deltas.``

  and add a link line `[act-report design](../designs/2026-08-11-act-report-design.md),` before the existing cut-2 links. Re-wrap the bullet.

- [ ] **Step 3: open-questions.md — the act-report residue entry.** After the rewritten third-cut entry (or in the page's section order beside the holdings residue entry — match the page's grouping), insert:

  ```markdown
  - **The act-report's residue.** The act-report design (2026-08-11) closed
    the run boundary's report seam: the boundary-minted terminal record of
    one operation, the operation intent's three-valued completion reading
    (unfinished, indeterminate, closed), and the durable home of a look's
    non-report. Five things stay open, deliberately: cross-root publication
    of a dataset's provenance reference and its acquiring report (refused
    today); a compaction protocol that must preserve intent-qualification
    resolvability and fulfillment evidence (the rule today is retain); new
    operation kinds (the enum is closed at five); the agentic surface —
    audit scheduling and liveness, kernel sub-problem 6; and the engine,
    with everything durable still waiting on `atoms` A7–A8.
    ([act-report design](../designs/2026-08-11-act-report-design.md),
    [what stays open](../designs/2026-08-11-act-report-design.md#6-what-this-unblocks-and-what-stays-open))
  ```

  Before writing the second link, confirm the design's §6 heading anchor by reading its actual heading text (`## 6. What this unblocks, and what stays open`); adjust the fragment to match. Update the frontmatter `updated:` date.

- [ ] **Step 4: glossary.md.** Four insertions, each in alphabetical position, plus frontmatter `updated:`:

  Before **Address**:

  ```markdown
  - **Act report** — The boundary-minted terminal record of one opened
    operation — acquisition, audit, import, re-check, or a run attempt that
    minted no run — or the refusal record of a run request rejected before
    an operation can open. Inert by type; its entries record each member
    act's subject, explicit instrument inputs, and outcome in that act
    kind's own vocabulary, citable as (act-report ref, entry index).
    ([act-report design](../designs/2026-08-11-act-report-design.md))
  ```

  After **Assessment**, before **Belief**:

  ```markdown
  - **Audit wrapper** — The boundary operation that runs the read-only
    audit evaluator and publishes its findings as entries in an inert act
    report, under the wrapper's own operation intent. The evaluator's
    contract is unchanged: it inspects any configuration, returns
    validation or findings, and mints nothing.
    ([act-report design](../designs/2026-08-11-act-report-design.md))
  ```

  Before **Conformance cut**:

  ```markdown
  - **Completion reading** — The three-valued, derived, never stored state
    of a boundary operation, read per root from its operation intent under
    the log's reduction: unfinished (unmatched intent), indeterminate
    (qualification unresolved — never collapsed into unfinished), and
    closed (fulfilled).
    ([act-report design](../designs/2026-08-11-act-report-design.md))
  ```

  After **NoBelief**, before **Operator**:

  ```markdown
  - **Operation intent** — The tamper log's third intent consumer: appended
    once per boundary operation, after the observer-corpus root freezes and
    before any member act, carrying the operation kind, the minted event
    token, and the actor. It blocks nothing — completion visibility only —
    and its qualifying fulfillment is the operation's terminal record.
    ([act-report design](../designs/2026-08-11-act-report-design.md))
  ```

  Check each stated neighbor still matches the file's actual alphabetical order before inserting; the file's order governs.

- [ ] **Step 5: contracts-and-adoption.md.** Two edits plus frontmatter:
  1. ~Line 88: change `The corpus now` `holds 143 rows across twelve frozen tables: the belief policy's P1–P9 banked the` `day the cut was drawn, the admission ramp appended G9 on 2026-08-09 while` `narrowing W3's dataset arm, and the verified-holdings record design banked` `H1–H4 on 2026-08-10.` to

     `The corpus now holds 151 rows across thirteen frozen tables: the belief policy's P1–P9 banked the day the cut was drawn, the admission ramp appended G9 on 2026-08-09 while narrowing W3's dataset arm, the verified-holdings record design banked H1–H4 on 2026-08-10, and the act-report design banked T1–T8 on 2026-08-11.`

     Re-wrap to the file's hard-wrap width.
  2. Frontmatter: `updated: 2026-08-10` → `updated: 2026-08-11`; `sources:` gains `  - ../designs/2026-08-11-act-report-design.md`.
  3. Confirm no other sentence on the page claims the run/report seam is undesigned (`rg -n "run capture|run/report" docs/guide/contracts-and-adoption.md`) — the "remain outside both cuts" sentence is about cut selection, not design state, and stands unchanged.

- [ ] **Step 6: Verify.** From `python/`: `uv run --frozen python tools/check_guide.py; echo "exit=$?"` → exit 0. `uv run --frozen pytest tests/test_designs_corpus.py -q` → now exactly **two** failures (the README pair); `test_the_guide_cites_every_design` passes. `git diff --check` clean.

- [ ] **Step 7: Commit.**

```bash
git add docs/guide/foundations.md docs/guide/open-questions.md docs/guide/glossary.md docs/guide/contracts-and-adoption.md
git commit -m "docs(guide): propagate the act-report across the guide"
```

---

### Task 8: Corpus guards, README, and the Status flip

§7 item 13 — plus the user rule that a landed design's Status is corrected in the same change. This task takes the suite fully green.

**Files:**
- Modify: `python/tests/test_designs_corpus.py` (module docstring ~line 11; `GUARANTEE_TABLES` ~line 49; `TABLE_OWNERS` ~line 66; `_ROW` ~line 90; `_ROW_RANGE` ~line 110; `_COUNT_WORDS` ~line 218)
- Modify: `README.md` (count sentence ~line 20; design table; row-total sentence ~lines 60–61)
- Modify: `docs/designs/2026-08-11-act-report-design.md` (Status header, lines 3–4)

**Interfaces:**
- Consumes: everything — this is the gate that proves the other seven tasks landed.

- [ ] **Step 1: Extend the guards (the failing test comes first).** Five edits in `python/tests/test_designs_corpus.py`:
  1. In `GUARANTEE_TABLES`, after the `"H"` entry add:

     ```python
     "T": ("T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8"),
     ```
  2. In `TABLE_OWNERS`, after the `"H"` entry add:

     ```python
     "T": "2026-08-11-act-report-design.md",
     ```
  3. Update the dict's leading comment `The twelve frozen guarantee tables` → `The thirteen frozen guarantee tables`, and the module docstring's inventory line (~line 11) — it currently reads `Eleven frozen tables carry the acceptance`, a drift left behind at an earlier banking — to `Thirteen frozen tables carry the acceptance`.
  4. Extend both row parsers' character classes `[GSWRCXNLDMPH]` → `[GSWRCXNLDMPHT]`:

     ```python
     _ROW = re.compile(r"^\|\s*\*{0,2}([GSWRCXNLDMPHT][0-9]+[a-z]?)\*{0,2}\s*\|", re.MULTILINE)
     ```

     ```python
     _ROW_RANGE = re.compile(r"\b([GSWRCXNLDMPHT])([0-9]+[a-z]?)–\1?([0-9]+[a-z]?)\b")
     ```

     Without this the T rows are invisible to the completeness test and `T1–T8` spans validate against nothing.
  5. In `_COUNT_WORDS`, after the `20: "Twenty",` entry add:

     ```python
     21: "Twenty-one",
     ```

     Capitalized: the dict's values open the README's count sentence, and the assertion matches the string verbatim. (§7 item 13 names this entry; the dict's existing convention fixes the capitalization.)

     `table_words[13] = "thirteen"` is already in place from the holdings banking — verify, don't re-add.

- [ ] **Step 2: Run the suite to see the guards bite.** `uv run --frozen pytest tests/test_designs_corpus.py -q` → the row-total test now demands `151 rows` and `thirteen frozen tables`; the README count and table tests still fail. Expected: 3 failures, all README-shaped; the completeness test finds `T1`–`T8` in the act-report design via the extended `_ROW` and passes; the range test validates every `T1–T8` span written in Tasks 3–7.

- [ ] **Step 3: README.** Three edits:
  1. ~Line 20: `Twenty documents in `docs/designs/`: …` → `Twenty-one documents in `docs/designs/`: …` and in the same sentence `2026-08-02 through 2026-08-10` → `2026-08-02 through 2026-08-11`.
  2. Design table: after the `2026-08-10-verified-holdings-record-design.md` row, append:

     ``| `2026-08-11-act-report-design.md` | the run boundary's report seam: the act-report, boundary-minted terminal record of one operation; the operation intent's derived three-valued completion reading; the durable home of a look's non-report — T1–T8 |``
  3. ~Lines 60–61: `There are **143 rows** across **twelve frozen` `tables** (G, S, W, R, C, X, N, L, D, M, P, H).` → `There are **151 rows** across **thirteen frozen tables** (G, S, W, R, C, X, N, L, D, M, P, H, T).` (T appends last, matching the guard's insertion order; keep the hard wrap.)

- [ ] **Step 4: Status flip.** In the act-report design's Status header, change

  `**Status:** approved 2026-08-11; not yet banked — §7's amendment set is` `unapplied.`

  to

  `**Status:** banked 2026-08-11; §7's amendment set applied in the banking change. Nothing here is implemented, and no conformance arm is claimed.`

- [ ] **Step 5: Full verification.** From `python/`, in the frozen `uv` environment — the full gate set from `python/README.md`, not just the corpus tests:
  - `uv run --frozen pytest -q` → **the whole suite passes**.
  - `uv run --frozen ruff check .` → clean.
  - `uv run --frozen pyright src` → clean.
  - `uv run --frozen python tools/check_guide.py; echo "exit=$?"` → exit 0.
  - From the worktree root: `git diff --check` → clean.
  - Cut 2 untouched: `git diff main -- docs/designs/2026-08-09-conformance-cut-2.md` → empty.
  - Sweep for stragglers: `rg -n "twelve frozen tables|143 rows" README.md docs/guide/ python/tests/` → no hits; `rg -n "twelve kernel kinds|twelve world-record kinds" docs/guide/` → no hits (historical "twelve" statements inside banked designs' dated notes remain, by design); `rg -n "owed to the run/report design" docs/guide/` → no hits (the design docs' occurrences now carry closure notes and stay).

- [ ] **Step 6: Commit.**

```bash
git add python/tests/test_designs_corpus.py README.md docs/designs/2026-08-11-act-report-design.md
git commit -m "docs: bank the act-report design and extend the corpus guards to thirteen tables"
```

---

## Completion criteria

1. Every §7 item of the act-report design maps to a landed edit (items 1–2 → Task 1; 4 → Task 2; 3 and 8 → Task 3; 5 → Task 4; 6–7 → Task 5; 9–10 → Task 6; 12 → Task 7; 13 → Task 8). Item 11 is the null edit: cut 2 byte-unchanged.
2. The full gates pass in the frozen environment: `uv run --frozen pytest -q` fully green, `uv run --frozen ruff check .` clean, `uv run --frozen pyright src` clean, `uv run --frozen python tools/check_guide.py` exit 0; `git diff --check` clean; worktree clean.
3. Nothing pushed. The branch is then ready for `superpowers:finishing-a-development-branch` (base: `main`).
