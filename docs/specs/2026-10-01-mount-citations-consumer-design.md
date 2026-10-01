# Consuming mount citations: write commands over the session's corpora, belief at an epoch

Status: draft for review, 2026-10-01. Task `sci-dc0381`, which absorbs `sci-b1c777` and
`sci-498acb`.

Sources: beliefs `docs/superpowers/specs/2026-10-01-mount-citations-design.md` (cut 44,
merged at beliefs `7932481`), §4 "What science gains and must change", decision 10 and
limitations 1–4; this repository's coordination command set design
(`docs/specs/2026-09-24-coordination-command-set-design.md`) §5.5 and its part 3
amendments; the command framework design §4.4; the science commons design §11.

## 1. What this is

Cut 43 gave a session one write root and N read mounts. Coordination part 3
(`sci-923d3a`) fenced every non-coordination command onto the write root, because the
kernel could not write a record citing a mount's record, and could not judge its
eligibility. Cut 44 lifts that: a session's writes may cite records in its read mounts,
and a corpus-local belief read now refuses `input-outside-corpus` itself.

This slice moves science onto that surface. It is the last thing the second-project
milestone (`sci-0d00d2`) waits on, and one of the four prerequisites of commons
milestone 1a (`sci-13050a`). Concretely:

1. `spec`, `run`, `assess` and `verify` resolve the records they cite over the session's
   corpora, not the write root alone.
2. Science's foreign-observation guard goes. The kernel now refuses that state.
3. Belief, and `next`'s admission check, read a session with read mounts as a world
   read at an epoch. An operator verb publishes that epoch.
4. The `publishes` declaration-time refusal is retired, because the publish act family
   has landed (`sci-498acb`).

Measured before writing (2026-10-01): the relocated mm30 corpus pins
`biology:24bcec43…` and base `science:52a43993…`, the identities the shipped `biology`
domain contract and base contract carry. A working corpus written under science's
shipped profile therefore cites mm30 without `CitationContractMismatch` (kernel
decision 3), which beliefs §4 asked to establish before `sci-0d00d2`.

## 2. Decisions

1. **The citation scope is the session's corpora.** A write command may cite a record
   held by exactly one session corpus. A session corpus is the write root plus every read
   mount, and read mounts exist only when coordination is on (`open_session` passes
   `mounts=None` otherwise). With coordination off, the scope is the write root alone,
   as today. Science's own check mirrors the kernel writer's scope: it never admits a
   ref the writer would then refuse as unresolved.
   *Rejected:* every configured `corpus_root` whatever coordination says. The writer
   would not hold those mounts, so science would accept refs the kernel then refuses.

2. **One resolver replaces `not_held()` at every citation.** `ReadContext.cited(ref)`
   returns the one session corpus holding `ref`, as a `Mount` (view and profile). It
   refuses `invalid-input` when no session corpus holds it, naming any configured
   corpus outside the session that does (the successor to `not_held`'s hint). It refuses
   `invalid-input` naming the corpora when more than one holds it, matching kernel
   decision 4's `duplicate-location`. Each command reads the cited record through the
   returned mount's view. It decodes the record under the **writer's** profile
   (`config.profile`), as the kernel's checks do (kernel decision 3).
   - A record whose content needs a namespace only the mount pins fails that decode, as
     it would in the kernel. For example, a claim operator declared only by mm30's
     corpus-local `mm30` contract. So the second-project working corpus must pin every
     namespace its citations use, at mm30's identity. mm30 pins `biology` and `mm30`.
     `sci-0d00d2` records which of them the working corpus pins.
   - `write_view()` stays, for reads of the write root's own records: the read-back of a
     record just minted (`run`, `verify`) and `dataset`'s standing holdings
     observations.

   *Rejected:* keeping each citation on `write_view()` and adding a fallback to the
   mounts. A fallback hides which corpus answered, and a write root holding a stale
   copy would shadow it.

3. **Mutation targets stay in the write root** (kernel decision 1). `spec --supersedes`
   and every target a command replaces, revises or corrects resolve through the write
   root alone. Those sites keep a write-root-only read, renamed `own(ref)`, which
   refuses `invalid-input` naming the mount that holds the ref when one does.

4. **`dataset` is unchanged.** It still refuses bytes a mount already declares. Two
   declarations of the same content are a `duplicate-location` that every world read
   refuses.

5. **Kernel refusals reach the person by name.** The writer's citation view raises three
   errors that are not `WriteRefused`: `CitationContractMismatch` (a `ContractError`),
   and `AddressMapConflict` and `BuildContended` (both bare `ScienceError`s). Today the
   dispatcher's write path catches only `PermitExceeded`, `KernelRefusalValue` and
   `WriteRefused`, so these three would escape as internal errors. The write path's
   catch gains them. `_kernel_refusal`'s existing generic arm already normalizes them to
   `kernel-refused` with `data.kind` set to the class name and the kernel's message,
   which names the mount and the namespace, the corpora, or the held lock. No new
   refusal code is needed. A `BuildContended` is retryable, and its message says so.

6. **`_refuse_foreign_observations` is removed.** A corpus-local `gather` now raises
   `InputOutsideCorpus`, and `_evaluate_over_inputs` returns it as
   `beliefs.belief.Refused("input-outside-corpus: …")`, a value and not an exception.
   The state is reachable without editing any corpus. Cross-corpus evidence is authored
   normally with coordination on, then read where the session has no read mounts:
   with coordination off, or under a configuration naming fewer roots.
   - `belief` already renders a returned `Refused` as `kind: Refused` with its reason.
   - `next` calls `gather` directly, where `InputOutsideCorpus` raises. `next`
     classifies that row `assessed-unevaluated (input-outside-corpus)` (decision 9). It
     neither lets the error escape as an internal error nor blanks every row.

   The `declared` filter in `_context` stays, because the lineage snapshot can walk
   only the mount's own datasets.

7. **Belief has two read modes, chosen by the session's shape, never by the evidence.**
   - **No read mounts** (coordination off, or a single corpus root): the live
     corpus-local read, as today, at the current epoch's identity or
     `NO_EPOCH_SNAPSHOT`.
   - **Read mounts present:** a world read at the current epoch, using the kernel's
     proven recipe (beliefs J20, `test_world_view.split_evaluation_world`):
     `open_world_view(world, current_epoch(world))`, `lineage_snapshot` over that view,
     `producer_snapshot_identity` from the view, and pins per covered corpus.

     The epoch is **current for the session** when two things hold. First, its coverage
     *equals* the session corpora's ids. Second, the view opened at it reports no drift
     for any of them, meaning no changed state and no unmapped records. The read
     answers only at a current epoch. Otherwise it refuses, with no answer:
     - `no-epoch`: the world has no current epoch.
     - `epoch-stale`: the coverage differs from the session corpora in either
       direction. A missing corpus would leave its evidence out. An extra one, from an
       epoch another configuration published, is one the kernel reads as absent, and
       belief then answers `NoBelief("unavailable-corpus-absent")` even when every
       session corpus is available. The refusal names the corpora missing and the
       corpora extra.
     - `epoch-stale`: the view reports drift for any session corpus, whatever moved.
       Coordination writes count too.
     - `kernel-refused` (`data.kind` `BuildContended`): opening the view needs every
       covered corpus's capture hold, and one is mid-write. This is retryable, and is
       the same normalization as decision 5.

     *Rejected (plan review round 1, P1):* treating drift as inert when every unmapped
     record is a coordination kind. `open_world_view` checks mapped addresses and uids,
     not content. A mapped dataset's facet revised alongside a new coordination record
     was served changed while the rule called the drift inert. The exception returns
     only when the kernel can prove mapped content and the manifest unchanged
     (limitation 2).

     Each refusal names the corpora and the remedy, `science epoch`. The check is one
     function, `epoch_currency(world, session_ids)`, in `science/world_belief.py`.
     Belief, `next` (decision 9) and `science epoch` (decision 8) all call it.

   *Rejected:* picking the mode from where the proposition's evidence lives. Belief
   depends on assessments, verifications, retractions and corrections, and any session
   corpus may hold one of them about the proposition. Deciding the evidence is local
   means reading every corpus for all of those relations, which is the world read
   itself. A wrong guess silently omits evidence.

   *Rejected:* reading the stale epoch and warning. The view holds only records the
   epoch mapped, so an assessment written after it would be absent from the answer,
   and the answer would not say so.

   *Rejected:* asking beliefs for a live multi-corpus belief read. Kernel decision 10
   refused it because it has no epoch identity in its reproducibility context. One
   operator command per change to the evidence is the cost of that identity, and the
   dogfood measures whether the cost is tolerable (§6, limitation 1).

8. **`science epoch` is an operator verb, not a command.** It is dispatched like
   `build` and `serve` (framework §4.4: epoch acts are launcher- and operator-time
   library operations), with no write class, no permit from the session, and no ledger
   entry. It:
   1. opens the world with an operator authority covering `epoch`;
   2. asks `epoch_currency` (decision 7). A `kernel-refused` contention from it
      propagates, and the verb exits 3 naming it. When the current epoch is already current for
      the session, it builds nothing and prints that epoch's packaging identity and
      coverage, marked `current`. Rebuilding is not an idempotent way to get there. An
      epoch's bytes include the world's chain head, publication advances that head, and
      a second build over unchanged corpora therefore yields a different packaging
      identity. The kernel's identical-rebuild tests hold only because they inject a
      fixed chain head;
   3. otherwise, installs the shipped rule bindings (`install_shipped_world_rules`), or
      reuses bindings already installed;
   4. builds one epoch whose coverage is exactly the session corpora's ids, under the
      configuration `--config` names;
   5. prints the new packaging identity and coverage, marked `built`.

   A `BuildContended` from a corpus mid-write exits non-zero, naming the corpus; it
   never waits. Framework §4.4 needs no amendment, because no write class maps to
   `epoch`. The plan confirms how an operator `Authority` is constructed and whether
   reinstalling a binding is idempotent, before writing the verb.

9. **`next` keeps its live attention read, and says when it cannot judge admission.**
   - Whether a proposition is *assessed* is a live scan of every session corpus for an
     assessment of it. Today `next` scans only the proposition's corpus, which misses a
     working corpus's assessment of an mm30 proposition.
   - Readiness, for a proposition no session corpus has assessed, is a live scan of
     every session corpus for specs targeting it. Each spec is decoded under its
     holder's profile, and its inputs are then judged held as today (`_inputs_held`).
     Today `_targeting_specs` reads only the proposition's corpus. A spec written in
     the write root against a mounted proposition, the first step of the
     second-project measurement, would therefore leave the row `not-ready` even with
     its inputs held.
   - With no read mounts (coordination off, or one configured root), classification
     is holder-local, exactly as today. The scans read the proposition's own corpus,
     so a mounted proposition keeps the specs and assessments its corpus holds.
     `InputOutsideCorpus` from that corpus-local read makes the row
     `assessed-unevaluated (input-outside-corpus)`.
   - With read mounts, admission is judged through decision 7's world read when the
     epoch is current. When it is absent or stale, the row is classified
     **`assessed-unevaluated`** and carries the reason (`no-epoch` or `epoch-stale`).
     Contention while opening the view (`kernel-refused`) refuses the whole `next`,
     as any kernel refusal does.
     This is a fifth class, and it amends the coordination design's four-class rule.

   *Rejected:* refusing the whole `next`. Its rows are attention over the live world
   (coordination §5.5), and one stale epoch would blank every row, including rows that
   need no admission judgment.

10. **The `publishes` arm calls the permit** (`sci-498acb`):
    `return RequiredCapabilities.publishes()`. The framework §4.4 amendment of
    2026-09-09 is struck by citation, with a dated note. No `publishes`-class command
    exists yet, so the effect is tested at the dispatcher with a declared fixture
    command: the permit decides, and no declaration-time refusal remains.

11. **`status` is unchanged.** It reports `world.status` findings, and `World.status`
    runs only the registry reduction, whose one finding is `duplicate-carrier`. It never
    runs `corpus_check`, so the `eligibility-unresolved` warning beliefs §4 anticipated
    does not reach `status`. `audit_world` is where a cross-mount assessment is judged.

12. **Two refusal codes are added**, `no-epoch` and `epoch-stale` (decision 7). They join
    `refusal.CODES` and the coordination design's list of refusal codes.

## 3. Surface

- `config.ReadContext`
  - gains `session_mounts()`: the write root's `Mount`, plus every read mount's when
    coordination is on.
  - gains `cited(ref) -> Mount` (decision 2) and `own(ref) -> ReadView` (decision 3).
  - loses `not_held()` and `_refuse_foreign_observations`. `write_view()` stays for
    reads of the write root's own records (decision 2).
  - `evaluate` and `gather_inputs` dispatch on decision 7's mode. The world mode lives
    in a new `science/world_belief.py`, which holds `epoch_currency`, builds the view,
    and builds the supplied context, so `config.py` does not grow a second evaluation path
    inline.
- `commands/spec.py`, `run.py`, `assess.py` and `verify.py`: every
  `write_view()`/`not_held()` site moves to `cited` or `own`, per decisions 2 and 3.
  `dataset.py` is unchanged: it reads `write_view()` for its own holdings, and its
  declared-elsewhere refusal stays.
- `commands/next.py`: `classify` per decision 9. Both the assessment scan and
  `_targeting_specs` read every session corpus.
- `dispatch.py`: the `publishes` arm (decision 10). The write path's catch adds the
  three citation errors (decision 5).
- `refusal.py`: `no-epoch` and `epoch-stale` (decision 12).
- `cli.py`: the `epoch` operator verb (decision 8), added to the framework-verb set and
  to the reserved names.
- Docs:
  - coordination design §5.5 gets a dated amendment, which lifts part 3's two refusals,
    adds the fifth class, and names this spec;
  - framework §4.4 gets the 2026-09-09 amendment struck with a dated note;
  - commons §11's "belief evaluating over a world read" gets a pointer here;
  - `docs/plans/2026-10-01-mount-citations-consumer.md` is the plan.

## 4. Testing

The full two-corpus fixture already exists (`test_two_corpora`; `sci-9b20ea` makes it
module-scoped, which is independent of this slice). Cases added to it:

- **Citation.**
  - `spec` against a mount's proposition and dataset; `run` and `assess` over them;
    `verify` of a mount's assessment. Each record is written to the write root, and
    every cited ref resolves into the mount.
  - The same refs with coordination off refuse `invalid-input`, naming the mount.
  - A ref held by two session corpora refuses, naming both.
  - `spec --supersedes` of a mount's spec refuses (decision 3).
- **Contract mismatch.** A mount pinning a different `biology` identity:
  `CitationContractMismatch` arrives as a named `invalid-input`, not an internal error.
- **Belief.**
  - Single corpus: unchanged answers. The existing belief tests are the oracle.
  - Mounted, with no epoch → `no-epoch`.
  - After `science epoch` → an answer that counts the working corpus's assessment of
    the mount's proposition.
  - After one more write → `epoch-stale`, naming the write root.
  - Coverage mismatch in each direction, each → `epoch-stale` naming the corpora. A
    published epoch covering a session corpus too few. A published epoch covering one
    extra admitted corpus, built directly through the kernel as another configuration
    would.
  - An edited corpus whose run reads a dataset it does not declare → the kernel's
    `input-outside-corpus`, replacing the removed guard's test.
- **`next`.**
  - Readiness, before any assessment exists: a spec in the write root that targets a
    mount's proposition, with its inputs held, makes the row `ready`. Without the
    spec, the row is `not-ready`.
  - Live scan: a working-corpus assessment of a mount proposition makes the row
    assessed.
  - With no epoch, the row is `assessed-unevaluated (no-epoch)`; after `science epoch`
    it is admitted or not by the world read.
- **`science epoch`.**
  - It builds over exactly the session corpora.
  - Rerunning it with no change builds nothing. It reports `current` with the same
    packaging identity, and the world's epoch pointer and chain head are byte-identical
    before and after. This is a production-backed check: no chain head is injected.
  - Rerunning it after a write builds a new epoch, reported `built`.
  - Rerunning it when the current epoch covers an extra corpus builds a new epoch over
    exactly the session corpora.
  - A corpus held mid-write exits non-zero, naming it.
- **`publishes`.** A declared fixture command reaches the permit; no declaration-time
  refusal.

Every case runs under `just test-one` while working, and `just test-fast` before each
commit. The pre-push hook carries the full suite (science has no CI).

## 5. What does not change

- Coordination citations and `CoordinationResolver` (cut 43, J14).
- `dataset`'s declared-elsewhere refusal.
- The live, unpublished view-query read `next` uses for selection (`beliefs-cc0aea`).
- What a session may write: no write class, act family or session ledger evidence
  changes. `epoch` is an operator verb outside the session.

## 6. Limitations

1. **Belief in a mounted session costs one `science epoch` per change to the
   evidence.** Each epoch build captures every session corpus. The second-project
   measurement records how often that happens and how long it takes. That record is
   the evidence for or against asking beliefs for a cheaper epoch, or a live read with
   a stated identity.
2. **Any write in a session corpus makes the epoch stale for every proposition**,
   including coordination writes (`project`, `question`, `hypothesis`) and writes
   unrelated to the one asked about.
   - In daily use, each of those writes is followed by `science epoch` before the next
     belief or admission read.
   - Exempting coordination drift needs a kernel witness that a world view's mapped
     content and manifests are unchanged since the epoch. Beliefs has none today;
     the follow-up is `beliefs-655c10`. Narrowing staleness to a proposition's
   evidence would need the evidence closure, which is the world read itself.
3. **Read mounts are opened per citing write** (kernel limitation 1), and per
   `cited()` call here. `sci-d92797` (open mounts once per read command) covers the
   read side. Write commands will be measured in `sci-0d00d2` before any caching.
4. **A read mount mid-write refuses a citing write** (kernel limitation 3), and it
   refuses `science epoch`. Both are immediate and retryable.

## 7. Task linkage

- `sci-dc0381`: this spec, its plan, and implementation. It closes with `sci-b1c777`
  (decision 6, plus the coordination §5.5 amendment) and `sci-498acb` (decision 10).
- `sci-0d00d2` (second-project milestone) is unblocked when this lands. It measures
  limitations 1 and 3.
- `sci-13050a` (commons 1a) still waits on `beliefs-f50596` and `beliefs-d9bc57`.
