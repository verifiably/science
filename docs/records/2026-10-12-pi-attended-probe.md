# Attended pi probe: mm30 through science mcp serve — record

**Date:** 2026-10-12
**Status:** run 2026-10-12, complete. The preflight and predictions (§1–§3) were committed
before the run (`2e3b674`). Unmodified, pi 1.1.0 cannot open science's MCP server
(F1, a probe failure). With a disclosed protocol shim and a corrected tool allowlist, the
agent carried the path to the expected evidence, `NoBelief(no-directional-outcome)` over
16 governed records, with two replies from the attended person after the brief and nothing written around
(§4, §5). The recommendation is §6.
**Scope:** `sci-b40b23`, one piece of the ops goal `ops-3f5aa6` (a science harness on pi).
A spike: its output is this record and a recommendation, not kept code. The question is
whether a pi agent, given science's commands as MCP tools, a system prompt and the
command prompts, carries the success criterion of the governing design (§8 of
`beliefs` `docs/superpowers/specs/2026-08-29-user-and-autonomy-layer-design.md`) over a
disposable world holding the mm30 corpus: `next` ranks the proposition, `run` executes
under confinement, `verify` reaches clean-environment, `assess` admits the result, and
every step is a governed record. The baseline is the scripted walk of
`docs/records/2026-09-23-mm30-through-the-commands.md` (the "2026-09-23 walk").

## 1. Expected evidence

Written before the run.

The same records the 2026-09-23 walk shows: one proposition
(`proposition:concept-disease-stage-affects-protein-phf19`), five datasets with five
holdings observations, one analysis spec, two runs (the original and `verify`'s replay),
one assessment (`inconclusive`) and one verification (`clean-environment`, `passed`),
16 records, ending in the belief `NoBelief(no-directional-outcome)` with `next`
classifying the proposition `admitted`.

That inconclusive belief is the data's answer and is the success condition. A refusal or
an unknown outcome caused by the integration (a tool the agent could not find, a budget
the renderer truncated into uselessness, a session it could not open) is a failure of
the probe, not an eligible outcome. §4 keeps the two apart.

## 2. Preflight

Written before the run.

- **Runtime:** pi 1.1.0, the version hq pins (`hq-57132d`), driven through its CLI in RPC
  mode (`pi --mode rpc`), the path hq recommends for this probe. One pi process for the
  whole walk, so one MCP connection to one `science mcp serve` process, which opens the
  attended writer session `python/src/science/session.py` opens today. Nothing here
  claims an unattended boundary.
- **Model, pinned:** `anthropic/claude-sonnet-5-5`, thinking `medium`. Chosen over Opus
  5.5 because a harness should carry a mid-tier model, and the spend is lower.
- **pi home:** an isolated `PI_CODING_AGENT_DIR` in the work directory; the host's
  `~/.pi/agent` is untouched. Skills, context files (`AGENTS.md`) and prompt templates
  are off, so nothing from the host's development instructions reaches the agent.
- **Tools:** pi's read-only built-ins (`read`, `ls`, `grep`, `find`) and the 19 science
  tools; no `bash`, `write` or `edit`, so the only way to write is a science command.
- **Context given to the agent:** a system prompt replacing pi's coding-assistant
  default: two sentences of role (an analyst acting on the record only through the
  science tools, for a person who is present), then `commands/PREAMBLE.md`, then every
  `commands/<name>/prompt.md` under its name. The MCP tools carry each command's
  `purpose` and input docs as their schema. The first user message is a research brief
  (§3.2), the hand-off a person would give: the question, the files, the analysis plan
  in their words.
- **The world:** a fresh world, corpus and store under `.work/pi-probe/` (gitignored),
  made by the 2026-09-23 walk's operator recipe unchanged, over copies of the same
  inputs: the expression matrix, the four vocabulary lists, the analysis bundle and the
  contract document. Two operator-time adjustments the code has needed since that walk,
  neither touching the commands: the contract document's `also: [biology]` line is
  removed (the loader now refuses unknown top-level keys, the fix for that walk's F5,
  `sci-3a01b3`), and `coordination = false` is appended to `science.toml` (now a
  required key). `science status` showed one corpus, known, live and present, no
  records, no epoch; world `ed5afd38134c72f3c4c1b3edeb459e89`, store
  `33da6c66036f877ebd493f3422bc39f2`. The four list addresses are the 2026-09-23 walk's.
- **Confinement:** `beliefs.confinement.host_prerequisites()` is `None` on this host, so
  `run` and `verify` execute under the confined policy.
- **Integration, found before the run (finding F1):** pi 1.1.0 cannot open
  `science mcp serve` unmodified. pi's bundled MCP client speaks protocol revisions up
  to 2025-11-25 (an `initialize` handshake); science serves only 2026-07-28 (stateless,
  `_meta` with the protocol version on every request, `server/discover` in place of
  `initialize`). `pi mcp list` reports the server `failed`: `Request _meta is required`.
  hq-57132d's capability fact "MCP stdio: yes" held because its probe server speaks the
  older protocol. Upstream: `earendil-works/pi#10416` ("Support Stateless MCP
  (2026-07-28)") is open with no maintainer reply; 1.1.0 is the latest release; the
  TypeScript MCP SDK's latest (1.32.1) also tops out at 2025-11-25. This is a probe
  failure by §1's rule, recorded as the unmodified outcome.
- **The shim, so the rest of the question can be answered:** a throwaway stdio proxy
  (`.work/pi-probe-ctl/mcp-shim.py`, about 60 lines) between pi and science. It answers
  `initialize` from science's `server/discover`, drops `notifications/initialized`,
  answers `ping`, and adds the 2026-07-28 `_meta` to every request it forwards; replies
  pass through unchanged, and every frame is logged. With it, `pi mcp list` shows the
  server connected with all 19 tools. Everything after this point is "pi plus science
  plus this shim", and the recommendation counts the shim as something the harness must
  supply.
- **The MCP server's working directory** is the work directory, so a relative path the
  agent passes resolves where the files are.

## 3. Predictions and the attended answers

### 3.1 Predictions

Written before the run. Each is marked in §5.

| # | record value or behaviour | predicted |
|---|---|---|
| Q1 | proposition id | `proposition:concept-disease-stage-affects-protein-phf19`, as the 2026-09-23 walk |
| Q2 | dataset addresses | the five the walk minted (concepts `be3bf183…`, matrix `a6bf229e…`, levels `85b5e347…`, measures `08027c2e…`, identifications `79e30710…`): content addresses of the same bytes |
| Q3 | the claim's arguments | the agent finds `concept:disease-stage`, `protein:PHF19`, `affects`, from the vocabularies and contract; `causal_effect` and `positive` from the brief's wording or by asking |
| Q4 | ordering | the concept list is held before `claim` succeeds; if the agent claims first and is refused, it reports the refusal and does not write around it (the preamble's rule) |
| Q5 | rule identities | the agent cannot discover `beliefs/outcome-file/v1` and `beliefs/content-identity-equality/v1` from the tool docs or prompts, and asks |
| Q6 | reference and scale | the agent asks rather than guesses, as the `spec` prompt tells it, unless it reads them from the contract |
| Q7 | spec identity | `analysis-spec:b617f5d8…`, the walk's, if every field equals the walk's; any field that differs is named |
| Q8 | run | confined, `stats.tsv` z = 1.159, p = 0.246, n = 51 |
| Q9 | assessment | `inconclusive` |
| Q10 | verification | `clean-environment`, `passed` |
| Q11 | belief | `NoBelief(no-directional-outcome)` |
| Q12 | `next` | the proposition classified `admitted` |
| Q13 | corpus | 16 records, as §1 |
| Q14 | cost | under 1 M input tokens and under US$5; under 30 minutes wall time including the attended answers |

### 3.2 The brief

The first and only unprompted message, verbatim in `.work/pi-probe-ctl/brief.md`. It names
the question (does PHF19 expression rise from NDMM to PD in multiple myeloma), the files
by name, the workflow entrypoint and its two targets, and the analysis plan: the
method, assumptions and falsification sentences of the 2026-09-23 walk's spec, and
alpha 0.05. It does not give the claim's layer or polarity, the estimand's terms, the
reference, the scale or the rule identities.

### 3.3 The answer key

Written before the run, so the attended person answers the same way whatever the agent
asks. Each answer is given only when asked, and §4 lists every question and answer.

- layer `causal_effect`, polarity `positive`
- contrast `levels`, slot 0, baseline `level:ndmm`, comparison `level:pd`
- measure `measure:rna-seq-tpm`, scale `additive`, reference `0`
- identification `identification:observational`; no conditioning; no applicability
- interpretation rule `beliefs/outcome-file/v1`, equivalence rule
  `beliefs/content-identity-equality/v1`
- parameters `alpha=0.05`
- a question outside this key ("which locator", "what title") gets "your choice", or the
  matching value from the 2026-09-23 walk when there is one.

## 4. The run

Driver and logs are in `.work/pi-probe-ctl/` (gitignored), outside the agent's working
directory: `driver.py` holds one `pi --mode rpc` process and forwards the attended
person's messages; `events.jsonl` is every pi record, `transcript.md` a readable account,
`shim.jsonl` every MCP frame both ways, `stats.jsonl` pi's session statistics.

### 4.1 Attempt 1: aborted, no records

Launched with `--tools read,ls,grep,find`. The MCP server connected and listed its 19
tools (the shim log shows `initialize`, `server/discover` and `tools/list` answered
before the first prompt), but the model was given none of them: it read the inputs,
found a `__pi_deferred_placeholder__` where it expected tools, and stopped to say the
science tools were not available and that it had not worked around that. Cause
(finding F2): an MCP tool that no `--tools` entry matches "is never declared directly,
whatever its exposure" (pi `docs/cli.md`), while `pi --help` says `--tools` "keeps MCP
tools unless an entry starts with mcp__". An operator configuration error that the help
text invites, not an agent failure. 79 k tokens, US$0.08, 40 s. The attempt also showed
the agent reading the driver's own transcript in its working directory, so attempt 2
moved every control file out of it. Nothing was written: `science status` still showed
no records.

### 4.2 Attempt 2: the path

Relaunched with `--tools read,ls,grep,find,mcp__science__*`, a fresh conversation, the
same world, system prompt and brief. 2026-10-12, first prompt 09:32:43Z, last reply
09:35:07Z; three runs of 34, 17 and 70 s of agent time; model
`anthropic/claude-sonnet-5-5` on every message. 20 tool calls: `status`, three file
reads and three searches, then the science commands below. `science mcp serve` wrote
nothing to stderr.

| # | command | outcome |
|---|---|---|
| 1 | `status` | one corpus, no records |
| 2–6 | `dataset` ×5 (the four lists, then the matrix with `locator = accession:GSE179929`) | the five addresses the 2026-09-23 walk minted, each with its holdings observation; the agent checked them against the contract's bindings |
| 7 | `claim`, `layer = causal` | refused: `invalid-input: layer 'causal' is not in the plan`. The agent reported it verbatim, did not resubmit, and asked which layer (it had taken `causal` from the operator row's layer list; the plan names `causal_effect`) |
| — | person: layer and polarity, confirming the terms the agent proposed | |
| 8 | `claim`, `layer = causal_effect`, `polarity = positive` | `proposition:concept-disease-stage-affects-protein-phf19` |
| — | the agent asked for the two rule identities, which no file, prompt or tool doc names, and confirmed identification, conditioning, applicability and alpha | person: the rule identities |
| 9 | `spec` | `analysis-spec:bdac964a…` |
| 10 | `run` | `run:5c40956c…`, `boundary-policy/confined-v1`, capabilities `closure-confined-filesystem`, `from-bundle`, `network-denied` |
| 11 | `assess` | `assessment:f36394d4403bbd73` |
| 12 | `verify` | `verification:59046378…` and the replayed `run:4d5b39c4…` (same policy and capabilities) |
| 13 | `belief` | nothing minted; `NoBelief(no-directional-outcome)` |
| 14 | `next` | nothing minted; the proposition classified `admitted` |

The attended person replied twice after the brief, both times from the §3.3 key:
(1) "Use layer causal_effect, polarity positive", confirming the claim and estimand terms
the agent had listed (subject, predicate, object, levels, measure, additive scale,
reference 0); (2) the two rule identities, confirming identification observational, no
conditioning, no applicability, alpha 0.05. After the second reply the agent ran `spec`
through `next` without stopping.

The agent's closing report stated the belief and the record ids, said it could not see
the assessment's outcome or the run's statistics because no tool returned them, called
`inconclusive` the likely reason and labelled it as inference, and declined to state
z, p or n. That is right: no command reply carries them (F3).

The readback, through the kernel after the session closed (`.work/pi-probe-ctl/readback.out`,
the 2026-09-23 walk's script adapted to the current `ReadContext`), and the CLI against
the same config: claim identity `780ace5964c8ab83…` under operator
`mm30/affects-concept-molecular-entity`; the estimand projection equal to the walk's;
both runs confined, their result manifests equal; `stats.tsv` z = 1.1589, p = 0.2465,
n = 51, byte-identical to the walk's (`sha256:3a992dc8…`); assessment `inconclusive`;
verification `clean-environment`, `passed`; 16 records (one proposition, five datasets,
five holdings observations, one spec, two runs, one assessment, one verification).
`science belief` and `science next` render byte-identically to the MCP replies.

### 4.3 Cost

| attempt | tokens (input / output / cache read / cache write) | US$ | agent time |
|---|---|---|---|
| 1 | 14 / 2,691 / 60,807 / 15,270 | 0.08 | 40 s |
| 2 | 34 / 4,991 / 262,743 / 24,067 | 0.14 | 120 s |

Context in use at the end of attempt 2: 25 k tokens of a 1 M window. The system prompt
(role, preamble and the 19 command prompts) is 9.3 kB.

## 5. Predictions, marked

| # | observed | mark |
|---|---|---|
| Q1 | `proposition:concept-disease-stage-affects-protein-phf19` | confirmed |
| Q2 | the five addresses, equal | confirmed |
| Q3 | subject, predicate and object found from the vocabularies and contract; `layer` first tried as `causal`, refused, then asked; polarity proposed by the agent and confirmed | confirmed, with one guess: the agent filled `layer` from the operator row before asking, which the `claim` prompt does not forbid, and the refusal caught it |
| Q4 | every dataset held before the first `claim` | confirmed |
| Q5 | the agent asked for both rule identities after searching the files for them | confirmed |
| Q6 | the agent proposed `additive` and `0` and asked for confirmation before `spec`; it wrote nothing on the guess | confirmed |
| Q7 | `bdac964a…`, not the walk's `b617f5d8…`. Every field equals the walk's except the three prose fields: the agent capitalised the first letter of the method, assumptions and falsification sentences, and kept the trailing periods the brief's bullets carried | refuted, by prose formatting alone (F5); the estimand, rules, inputs and parameters are equal |
| Q8 | confined, z = 1.1589, p = 0.2465, n = 51 | confirmed |
| Q9 | `inconclusive` | confirmed |
| Q10 | `clean-environment`, `passed` | confirmed |
| Q11 | `NoBelief(no-directional-outcome)` | confirmed |
| Q12 | `admitted` | confirmed |
| Q13 | 16 records | confirmed |
| Q14 | 371 k tokens, US$0.21 over both attempts, under 3 minutes for attempt 2 including the answers | confirmed |

Against §1: unmodified, the probe fails (F1: the session cannot open). With the shim, the
criterion is met: `run` executed under confinement, `verify` reached clean-environment,
`assess` admitted the result, `next` ranks the proposition admitted, and every step is a
governed record. The inconclusive belief is the data's answer, the same one the
2026-09-23 walk and the kernel's rebuild run reached. The one refusal (step 7) was a
wrong input the kernel caught, not an integration failure, and the agent handled it by
the preamble's rule.

## 6. Findings and recommendation

| # | finding | class | where |
|---|---|---|---|
| F1 | pi 1.1.0's MCP client speaks up to 2025-11-25; `science mcp serve` only 2026-07-28. No session opens without a bridge | integration failure | upstream `earendil-works/pi#10416` (open); `hq-501726` corrects hq's capability fact |
| F2 | `--tools` with plain names hides every MCP tool no entry matches; `pi --help` says the opposite of `docs/cli.md` | operator configuration; upstream doc defect | the harness's pi configuration must name `mcp__science__*`; `hq-501726`; no upstream report exists (searched), one can be prepared for approval |
| F3 | No command reply carries the result it minted: `assess` omits the outcome, `verify` the scope and verdict, `run` the result manifest; the run's outputs exist only in operations scratch. The agent could report the belief but not why | surface gap | `sci-bef251` |
| F4 | Values the agent needs are not discoverable through the surface: the kernel-shipped rule identities appear in no prompt or tool doc, and the `claim` refusal does not name the plan's layers. Attended, the agent asked; unattended, it would stop | surface gap | `sci-a45f10` |
| F5 | The agent normalised the person's prose before freezing it, so the spec identity differs from a verbatim entry. The `spec` prompt says "in the user's words", which the agent read loosely | harness context | the harness's system prompt should say that prose is copied verbatim |
| F6 | The 2026-09-23 operator recipe and readback needed adjusting for code drift (`also:` refused, `coordination` required, `ReadContext.single_view` gone) | corpus-work | this record (§2, §4.2); nothing to file |

**Recommendation for `ops-3f5aa6`: what the harness must supply that pi plus science did
not.**

1. *A protocol bridge* until pi speaks MCP 2026-07-28: the shim here (about 60 lines:
   answer `initialize` from `server/discover`, add `_meta` to each request), carried by
   the harness as a stdio wrapper and retired when `earendil-works/pi#10416` lands. The
   alternative, science also serving the 2025-11-25 handshake, puts a second protocol
   in the kernel's one seam for a client-side gap; rejected for now.
2. *Tool declaration in the pi home*: `--tools` (or `defaultTools`) naming
   `mcp__science__*` beside the read-only built-ins, under hq's pi home rather than
   each invocation.
3. *Context beyond the command prompts*: the kernel's rule identities (until F4 makes
   them discoverable), and one line that the person's prose is entered verbatim (F5).
   The preamble and the command prompts were otherwise enough: the agent held data
   before claiming, reported the refusal verbatim, asked rather than guessed on
   reference and scale, and wrote around nothing.
4. *For any unattended step* (sub-project 6 onward): F3 and F4 are blockers, not
   conveniences. An unattended agent cannot ask for a rule identity, and cannot report
   why the record says what it says while no reply carries the outcome or verdict.

Cost is not a constraint at this scale: the whole attended path is about US$0.15 and
2 minutes of agent time on a mid-tier model, with 2.5 % of its context window used.
