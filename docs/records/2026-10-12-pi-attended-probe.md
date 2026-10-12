# Attended pi probe: mm30 through science mcp serve — record

**Date:** 2026-10-12
**Status:** preflight and predictions written before the run; the run, its marks and the
recommendation follow in §4–§6.
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
  (`.work/pi-probe/mcp-shim.py`, about 60 lines) between pi and science. It answers
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

The first and only unprompted message, verbatim in `.work/pi-probe/brief.md`. It names
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
