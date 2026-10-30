# Compact control dispatches v2 — readable controller reconstruction

This version supersedes the **exact readable prompt claim** in
controls-prompts-v1.md. V1 is preserved as historical evidence: its ten captured
message fields are opaque archive tokens, not readable dispatches. They must not
be treated as decoded plaintext or as reproducible prompt text.

Source of this version: the controller's actual visible spawn_agent calls in this
conversation, transcribed by the same controller. This is **controller
reconstruction**, not an independently verified recovery/decryption of the archive.
No independent historical replay is claimed. The completed workers' full returned
texts and scores remain unchanged in skill-controls-v1-report.md; no sample was
rerun or substituted. Its disclosed prompt differences remain a limitation on
causal attribution of effects to the skill.

Only literal resource locations are replaced below:

- `SCENARIO`: the synthetic-v1 scenario bytes in the committed fixture
  python/tests/fixtures/sweep-assumptions/scenario.md and controls-discovery-v1.md,
  SHA-256 47a11e63b4b26e085dfe296a3f9337636389661b1129a55dc3e158d3bced24b1.
  The worker calls originally pointed to the controller's identical persistent
  scenario-draft.md copy. Its byte equality was checked.
- `SKILL`: skills/sweep-assumptions/ containing the authored SKILL.md and
  report-template.md. The original call spelled its absolute worktree directory.

The scenario and Research request were the same across both arms. The two distinct
message bodies and their sample mapping follow in full. Actual model identities
were separately reported by each worker; preset gpt-6.1-sol was dispatched with
reasoning_effort medium and fork_turns none for every sample.

## Sample-to-message mapping

| Task name | Full message body below | Inputs/replies |
|---|---|---|
| control_1 | Control | SCENARIO; no source replies |
| control_2 | Control | SCENARIO; no source replies |
| control_3 | Control | SCENARIO; no source replies |
| control_4 | Control | SCENARIO; no source replies |
| control_5 | Control | SCENARIO; no source replies |
| guided_1 | Guided | SCENARIO, SKILL, actual controller-confirmed freeze; no source replies |
| guided_2 | Guided | SCENARIO, SKILL, actual controller-confirmed freeze; no source replies |
| guided_3 | Guided | SCENARIO, SKILL, actual controller-confirmed freeze; no source replies |
| guided_4 | Guided | SCENARIO, SKILL, actual controller-confirmed freeze; no source replies |
| guided_5 | Guided | SCENARIO, SKILL, actual controller-confirmed freeze; no source replies |

## Control — complete reconstructed message

```text
Read-only behavioral sample, no edits, network or task claims. Read ONLY SCENARIO. This is a compact research exercise: execute its Research request from the supplied evidence. Do not read any new sweep skill, plan, oracle or other files. Return your actual concise top-three research answer, exact reach endpoint sets and source-read decisions/requests, preserving whatever qualifications you judge necessary. No controller replies are available in this compact run; offered but unread sections remain unread. Do not return a review of instructions. At end run `timeout 2 relay model --harness codex --pretty` and report printed reviewer identity or codex with failure reason. Return full text only, no files.
```

## Guided — complete reconstructed message

```text
Read-only behavioral sample, no edits/network/task claims. Read ONLY SCENARIO and the authored skill/template at SKILL. Use that skill to execute the scenario's Research request. Do not read plan/oracle/other files. Return actual compact research answer with reach endpoint sets, three candidates and source-read decisions/requests, preserving required qualifications and sensitivity. No source replies are available; offered sections remain unread. The controller has actually attached and verified the complete supplied synthetic inventory as sci-b2755f controls-discovery-v1.md, SHA256 47a11e63b4b26e085dfe296a3f9337636389661b1129a55dc3e158d3bced24b1; use that phase-A freeze for this compact control, not a full rehearsal. Do not claim new attachments. At end run `timeout 2 relay model --harness codex --pretty`; report printed identity or codex with error reason. Full text only.
```

## Audit limits

The guided message explicitly mentions sensitivity and a controller-confirmed
freeze, in addition to supplying the skill/template. The control message supplies
neither. Outcome differences therefore do not isolate a causal skill effect.
These compact samples do not replace the separately exercised complete rehearsal.

V2 restores readable instructions and per-sample mapping, with honest provenance.
It does not make the archive tokens decodable, establish a new experiment, or
alter any scientific source, record, result, sample output or original freeze.
