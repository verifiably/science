# Projects, corpora and workspaces — implementation plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Land the two things the projects design makes true of this repository today — a preamble that states the one-world-through-a-selected-project rule, and a test that pins configuration independence from the working directory — and map every gated remainder to the task that unblocks it.

**Architecture:** The design (`docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md`) mostly constrains other specs: the coordination command set (sci-c5528e), the attended session in `beliefs` (beliefs-fe7149), the mm30 relocation (beliefs-c08725), and the second-project milestone (sci-0d00d2). What this repository owns unconditionally is §11's first bullet (the framework preamble and spec say views do not exist, and they do) and guarantee P1 (no configuration is discovered from `cwd`). Both are small and independent of every gated item, so they land now; nothing else in this plan writes code.

**Tech Stack:** Python 3 under `python/` (`uv run`), pytest through `just test`; the adapter generator `science adapters build` regenerates the committed `adapters/claude-code` tree, which `test_generated_tree_matches_committed` compares byte-for-byte.

**Spec:** `docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md`

## Global Constraints

- Run tests only through `just test` (or `just test-fast` for the inner loop); never `pytest` directly (AGENTS.md).
- `tasks check` before every commit; `tasks start`/`tasks done` bracket each task's commit.
- The committed adapter tree must equal the generated one: any change to `commands/PREAMBLE.md` is followed by `cd python && uv run science adapters build` before tests run.
- The preamble is "kept short enough to be read every time" (framework §8): the amended text stays at one paragraph.
- No configuration discovery from the working directory (design §5.2): the launcher takes the world from `--config` or `SCIENCE_CONFIG` only.
- Design docs are committed under `docs/specs/` and `docs/plans/` (profile: personal).

## Review Focus

Inputs the design implies that no task here tests, most likely to bite first. Each is pinned to the task that owns it, or named as gated.

1. A `SCIENCE_CONFIG` that names a relative path is resolved against the process's `cwd` by `Path()` — which is not discovery, but a person will read a wrong-world refusal as one. Task 2 asserts the relative form resolves against `cwd` and says so in the test name, so the behaviour is documented rather than accidental.
2. A predecessor `science.yaml` in `cwd` with a `peers:` block pointing at a real corpus root must not become a corpus root. Task 2's fixture includes one.
3. An agent reading the amended preamble may try to select a project before the coordination command set exists. Task 1's text says selection is not yet possible, and the skill test asserts that sentence is present.
4. The preamble change alters every emitted skill body; a stale committed adapter tree fails `test_generated_tree_matches_committed`. Task 1 regenerates and asserts the tree matches.
5. Gated, not tested here: a session opened with two `corpus_roots` still refuses in `beliefs` (beliefs-fe7149). The milestone (sci-0d00d2) is where that is exercised.

---

### Task 1: The preamble states the selected-project rule

**Files:**
- Modify: `commands/PREAMBLE.md`
- Regenerate: `adapters/claude-code/skills/status/SKILL.md` (via `science adapters build`)
- Modify: `docs/specs/2026-08-31-command-framework-design.md` (§8 at lines 589–599, §12.2 at lines 822–825)
- Test: `python/tests/test_adapters.py`

**Interfaces:**
- Consumes: `science.adapters.build_adapter(tree, commands_root, skills_root, out_dir)` and `science.loader.production_tree()`, both existing.
- Produces: nothing code-level; the preamble text below is what later specs quote.

- [ ] **Step 0: Start the task**

Run: `tasks start sci-fde62a`
Expected: `{"id":"sci-fde62a", ...}` with no `claimed` error.

- [ ] **Step 1: Write the failing test**

Append to `python/tests/test_adapters.py`, after `test_skill_carries_preamble_and_prompt`:

```python
def test_preamble_states_the_selected_project_rule(tmp_path):
    """Design 2026-09-23 §11: sub-project 1 landed, so the preamble no longer
    says no view exists. It states §5's rule and that selection is not yet
    possible."""
    from science.adapters import build_adapter

    build_adapter(production_tree(), COMMANDS_ROOT, REPO_ROOT / "skills", tmp_path)
    skill = (tmp_path / "skills" / "status" / "SKILL.md").read_text()
    # The adapter preserves the preamble's line breaks; the prose assertions
    # are about sentences, so compare with whitespace normalized. The
    # byte-for-byte check stays in test_generated_tree_matches_committed.
    prose = " ".join(skill.split())
    assert "Until the coordination layer lands there is no current view" not in prose
    assert "read through the selected project's query when one is selected" in prose
    assert "no project can be selected yet" in prose
    assert "A question or task needs a selected project; a fact does not." in prose
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `just test`
Expected: one failure, `test_preamble_states_the_selected_project_rule`, on the first `assert` (the old sentence is still present).

- [ ] **Step 3: Rewrite the preamble**

Replace the whole of `commands/PREAMBLE.md` with:

```markdown
You are working over one world of governed records through the `science`
commands. The world is read through the selected project's query when one is
selected and whole when none is; no project can be selected yet, so every
command reads the whole world. A question or task needs a selected project;
a fact does not. Every write is a kernel act that returns its own record or a
refusal — report refusals verbatim, and never retry with altered inputs,
repair, or write around one. Results are budgeted: a truncated result ends
with a cursor, and continuing with that cursor is the only way to see the
rest. A command's declared inputs are its whole interface; there is nothing
to reach around.
```

- [ ] **Step 4: Regenerate the committed adapter tree**

Run: `cd python && uv run science adapters build && cd ..`
Expected: `adapters/claude-code/skills/status/SKILL.md` changes and nothing else under `adapters/` does (`git status --short adapters/` shows exactly that one file).

- [ ] **Step 5: Run the suite and confirm it passes**

Run: `just test`
Expected: all pass, including `test_generated_tree_matches_committed` and `test_skill_carries_preamble_and_prompt` (which still finds "one world").

- [ ] **Step 6: Amend the framework spec in place**

In `docs/specs/2026-08-31-command-framework-design.md`, append to §8 (after the paragraph ending "there is nothing to reach around."):

```markdown
> **Amended 2026-09-23** (`docs/specs/2026-09-23-projects-corpora-and-workspaces-design.md`
> §5, §11). Sub-project 1 landed at cut 14, so the exception above is
> retired. The preamble now states the rule: the world is read through the
> selected project's query when one is selected and whole when none is; a
> question or task needs a selected project, a fact does not. Selection
> itself arrives with the coordination command set (`sci-c5528e`), and until
> then the preamble says no project can be selected yet.
```

and append to §12 item 2 (after "no command in this sub-project takes a project or view input."):

```markdown
   *Amended 2026-09-23:* the selection rule is the projects design's §5 —
   a session fact, never derived from the working directory, whole-world
   when unselected — and the slot is populated by the coordination command
   set (`sci-c5528e`).
```

- [ ] **Step 7: Close the task, check, and commit together**

Run:

```bash
tasks done sci-fde62a "Preamble states the selected-project rule; framework spec §8 and §12.2 amended; adapter tree regenerated" \
  && tasks check \
  && git add commands/PREAMBLE.md adapters/claude-code docs/specs/2026-08-31-command-framework-design.md python/tests/test_adapters.py tasks/sci-fde62a.md \
  && git commit -m "docs(preamble): state the selected-project rule now that views exist"
```

Expected: `tasks check` prints only the pre-existing `sci-4eeda7` process warning; the commit contains the task record beside the change and succeeds through the pre-commit hook.

### Task 2: Configuration is never discovered from the working directory (P1)

**Files:**
- Test: `python/tests/test_config.py`

**Interfaces:**
- Consumes: `science.config.resolve_config_path(cli_value, env)` and `science.config.load_config(path)`, both existing, and the test module's `write_config(tmp_path, ...)` helper.
- Produces: the guarantee P1 as a test other tasks (the coordination command set) extend to session open.

This is a pinning test: the behaviour already holds, because `resolve_config_path` reads only its argument and `SCIENCE_CONFIG`, and `load_config` reads only the file it is given. The test exists so that a future convenience (a `science.toml` found upward from `cwd`) fails a named test rather than landing quietly.

- [ ] **Step 0: Start the task**

Run: `tasks start sci-a3d191`
Expected: `{"id":"sci-a3d191", ...}` with no `claimed` error.

- [ ] **Step 1: Write the test**

Append to `python/tests/test_config.py`:

```python
def test_nothing_is_discovered_from_the_working_directory(tmp_path, monkeypatch):
    """Design 2026-09-23 §5.2, guarantee P1: the launcher takes the world from
    --config or SCIENCE_CONFIG only. A predecessor manifest, a workspace
    config and a stray corpus manifest in cwd change nothing."""
    explicit_dir = tmp_path / "explicit"
    explicit_dir.mkdir()
    cfg = write_config(explicit_dir)

    workdir = tmp_path / "workdir"
    workdir.mkdir()
    decoy_corpus = tmp_path / "decoy-corpus"
    decoy_corpus.mkdir()
    (workdir / "science.yaml").write_text(
        f"name: decoy\nid: decoy\nlayout_version: 3\npeers:\n- id: other\n  path: {decoy_corpus}\n"
    )
    (workdir / "science.toml").write_text(
        f'world_root = "{tmp_path / "decoy-world"}"\nworld_id = "{"cafebabe" * 4}"\n'
        f'corpus_roots = ["{decoy_corpus}"]\noperations_root = "{tmp_path / "decoy-ops"}"\ndomains = []\n'
    )
    (workdir / "corpus.yaml").write_text("manifest_version: 2\ncorpus_id: " + "0" * 32 + "\n")
    monkeypatch.chdir(workdir)

    # --config wins and names exactly the explicit world.
    loaded = load_config(resolve_config_path(str(cfg), {}))
    assert loaded.world.world_root == explicit_dir / "world"
    assert loaded.world.corpus_roots == (explicit_dir / "corpora" / "one",)
    assert decoy_corpus not in loaded.world.corpus_roots

    # SCIENCE_CONFIG wins the same way.
    loaded = load_config(resolve_config_path(None, {"SCIENCE_CONFIG": str(cfg)}))
    assert loaded.world.corpus_roots == (explicit_dir / "corpora" / "one",)

    # With neither, cwd's files do not rescue the launcher: it refuses.
    with pytest.raises(Refused) as caught:
        resolve_config_path(None, {})
    assert caught.value.refusal.code == "invalid-input"


def test_relative_science_config_resolves_against_cwd_and_is_not_discovery(tmp_path, monkeypatch):
    """A relative SCIENCE_CONFIG is a path the person gave, resolved where the
    process runs; that is ordinary path resolution, not discovery, and it is
    named here so a wrong-world refusal is not read as one."""
    cfg = write_config(tmp_path)
    monkeypatch.chdir(tmp_path)
    assert resolve_config_path(None, {"SCIENCE_CONFIG": "science.toml"}) == Path("science.toml")
    loaded = load_config(resolve_config_path(None, {"SCIENCE_CONFIG": "science.toml"}))
    assert loaded.world.corpus_roots == (tmp_path / "corpora" / "one",)
```

- [ ] **Step 2: Run the two tests and confirm they pass**

Run: `just test`
Expected: both new tests pass on first run (pinning tests), and nothing else changes.

- [ ] **Step 3: Confirm the test can fail**

Temporarily add, at the top of `resolve_config_path` in `python/src/science/config.py`:

```python
    if Path("science.toml").exists():
        return Path("science.toml")
```

Run: `just test`
Expected: `test_nothing_is_discovered_from_the_working_directory` fails on the `--config` arm (the decoy `science.toml` is loaded; `corpus_roots` names `decoy-corpus`). Then remove the two lines and run `just test` again: all pass.

- [ ] **Step 4: Close the task, check, and commit together**

Run:

```bash
tasks done sci-a3d191 "P1 pinned: nothing is discovered from the working directory; relative SCIENCE_CONFIG named as path resolution" \
  && tasks check \
  && git add python/tests/test_config.py tasks/sci-a3d191.md \
  && git commit -m "test(config): pin that nothing is discovered from the working directory"
```

Expected: the commit contains the task record beside the test and succeeds.

---

## Gated remainder, mapped

Nothing below is a task in this plan; each is a filed task whose own spec or plan carries the steps. They are listed so that the design's §9.2 milestone can be read as a dependency graph.

| design section | what | task | blocked on |
|---|---|---|---|
| §3.1 | attended session with one write root and N mounted read corpora; coordination resolution over all | `beliefs-fe7149` | nothing |
| §3.1 | relocate the reproduced mm30 corpus to the user's world root | `beliefs-c08725` | nothing |
| §5, §7, P1–P5, P8 | coordination command set spec: `project` (genesis, `select`), `question`, `hypothesis`, `task`, `decide`, the same-query mint, `no-current-project`, the read-side selection query on `service_socket` bound by both launchers, `default_project` and `write_root` config keys, sci-17851d folded in | `sci-c5528e` | the belief path measurement (`dogfood-commands` branch) |
| §9.2 | second-project milestone: measurement plan and record | `sci-0d00d2` | `beliefs-fe7149`, `beliefs-c08725`, `sci-c5528e`; criterion 5 additionally on `beliefs-1a5157` |
| §3.3, decision 4 | attach natural-systems to the world | `ns-ed9c53` | `sci-c5528e` |
| §8.2, §8.1 | publish: holdings transport is the destination's; coordination trail deferred | note on `beliefs-1a5157` | — |
| §6.2, §11 | store `executes`, `targets` and spec-input edges as relations | `beliefs-7c98bc` (idea) | the milestone's `addresses` count |

When `sci-c5528e` is written it takes this design as its inherited document, and when `sci-0d00d2` is planned it takes §9.2's seven criteria as its predictions table.
