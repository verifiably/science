# quarry foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the quarry project with its catalog, identifiers, HTTP runtime, search
framework and CLI, proven end to end on one biology repository (ENA).

**Architecture:** quarry is a Python package with a click CLI as a thin layer over a library.
The catalog is TOML data inside the package and is checked on every command. Identifiers are
CURIEs resolved against a pinned Bioregistry snapshot. One HTTP client owns throttling,
retries and redaction, and adapters compile a shared `Query` into each resource's native
request. Tests replay recorded HTTP exchanges and never reach the network.

**Tech Stack:** Python ≥ 3.13, uv, click ≥ 8.1, httpx ≥ 0.28, pytest ≥ 8.4 with
pytest-testmon, hatchling; ops' vendored `tt`, `ops-check`, `ops-docs`, `cli.toml`,
`cli_surface.py`.

**Spec:** `docs/specs/2026-10-10-quarry-domain-layers-design.md` in the science repository
(task `sci-ba7150`). Read it before any task; section numbers below are its sections.

## Scope of this plan and the ones after it

The spec's first version (§13) is built in three plans, each producing working software:

1. **This plan, the foundation:** the project, the catalog, identifiers, the HTTP runtime,
   the search framework, the catalog/id/search/show commands, and ENA as the one adapter.
2. **Repositories and acquisition:** GEO, BioStudies, Zenodo, figshare and PubMed; `files`
   and `files --acquisition` (§9). This plan fills `core`'s `search_default` with Zenodo
   and figshare.
3. **Terms and skills:** GO, UBERON and NCBITaxon over OLS with the `term` verbs; the
   `quarry` and `quarry-biology` skills, `skills build`, their hq links, and `just live`.

Filed when this plan is approved, not as tasks in it: the science task for
`science acquire` (spec §9), and the multiple-myeloma task to migrate the roster (§11).

## Paths

- `$TREE` is the shared tree that holds the science, lit and ops checkouts: run
  `dirname "$(tasks root sci-ba7150 | python3 -c 'import json,sys; print(json.load(sys.stdin)["root"])')"`.
- The new repository is `$TREE/quarry`. Every path in a task below is relative to it unless
  the task names ops (`$TREE/ops`) or lore (`$TREE/lore`).
- From Task 1, Step 3 on, all quarry work happens in the worktree `$TREE/quarry/.worktrees/foundation`
  (`$WT`); main holds only the seed commit until the branch is finished. Task 2 also works in an ops worktree, `$TREE/ops/.worktrees/quarry-cli`.

## Global Constraints

- Python `>=3.13`; dependencies `click>=8.1`, `httpx>=0.28`; dev `pytest>=8.4`, `pytest-testmon`.
- Every id quarry prints is a CURIE with Bioregistry's canonical prefix (§7).
- Roles are exactly `identifier-scheme`, `vocabulary`, `ontology`, `data-model`, `repository`, `knowledgebase`, `literature-index` (§4.1).
- Route kinds are exactly `rest`, `query-endpoint`, `bulk`, `local-tool` (§4.2).
- Output follows the ops CLI conventions: `--json` emits one JSON value on stdout; a failure under `--json` prints `{"error": {"kind", "detail"}}` on stderr and nothing on stdout; exits are 0 success, 1 failed, 2 usage error (§8).
- Environment variables are `QUARRY_<OPTION>`: `QUARRY_FORMAT`, `QUARRY_DOMAIN`, `QUARRY_TRACE`. Service key variables keep the service's own name (§9).
- `check` and `id check` print nothing and exit 0 when clean; findings go to stdout and exit 1 (§6, §7).
- A listing shorter than the resource's reported total is a failure, never a result (§8.3).
- Tests never reach the network; fixtures are recorded with `just record <resource>` (§12).
- A credential never reaches a trace line, an error detail, or a recorded fixture (§9).
- quarry makes no kernel acts and does not download files (§3, §9).
- Never call `pytest` directly: use `just test-one <args>`, `just test-fast`, `just test` (the recipes record runs through `tools/tt`).

## Review Focus

1. A search phrase containing a double quote or `*`: ENA's syntax cannot carry the first and reads the second as a wildcard, so the adapter refuses with `unsupported_filter` instead of sending a broken or wildcard query. Pinned in Task 8.
2. A search that matches nothing: ENA answers its search endpoint with an empty body. The result has zero rows and `complete: total`, with no JSON decode error. Pinned in Task 8.
3. A CURIE typed with an uppercase prefix or a synonym (`GEO:GSE1`, `PMID:123`) prints in canonical form (`geo:GSE1`, `pubmed:123`). Pinned in Task 4.
4. `--since` later than `--until`: a usage error (exit 2), not an empty search. Pinned in Task 7.
5. A `Retry-After` of an hour, or as an HTTP date: the client honours either form, and a delay beyond its 60 s budget fails at once with the delay named, rather than hanging or retrying early. Pinned in Task 6.

---

### Task 1: Create the quarry repository and its front door

**Files:**
- Create: `pyproject.toml`, `justfile`, `.gitignore`, `identity.toml`, `README.md`, `AGENTS.md`, `.githooks/pre-commit`, `.githooks/pre-push`, `src/quarry/__init__.py`, `src/quarry/output.py`, `src/quarry/cli.py`, `tests/__init__.py`, `tests/test_cli_basics.py`, `tasks/` (by `tasks init`), `tools/tt`, `tools/ops-check`, `tools/ops-docs`, `tools/README.md` (by `vendored adopt`)

**Interfaces:**
- Produces: `quarry.cli.main` (the click root group, class `Cli`); `quarry.output.CONTEXT`, `output_options(command)`, `mode(ctx) -> str`, `emit(ctx, report: dict, text: str) -> None`, `fail(ctx, kind: str, detail: str) -> NoReturn`.

- [ ] **Step 1: Create the directory, git and tasks**

```bash
mkdir "$TREE/quarry" && cd "$TREE/quarry"
git init -b main
tasks init --prefix quarry
```

Main receives only the seed (the task records and `identity.toml`, the project's registration
inputs, which ops reads from the main checkout in Task 2). Everything else is written in the
foundation worktree from Step 4 on.

- [ ] **Step 2: Write identity.toml**

`identity.toml`:

```toml
# What this project is. `tools/ops-docs write` renders it into the identity region of
# README.md and AGENTS.md; `tools/ops-docs check` refuses a commit while they differ.
# Design: ops docs/specs/2026-09-22-project-guides-design.md §3.
name = "quarry"
aliases = []
# At most 80 characters: this line sits in every agent session in every project.
purpose = "One CLI and skills over scientific resources, with domains as lenses"
# One to three sentences, at most 400 characters: what it does and for whom.
abstract = """
quarry gives people and agents one interface to scientific repositories, knowledgebases, \
identifiers and ontologies, with each resource's pitfalls handled once. Domains (core, \
biology, later chemistry, physics, astronomy) select what is searched; the commands and \
their options stay the same in every domain.
"""
authority = []
subsystems = []
```

- [ ] **Step 3: Seed main and create the foundation worktree**

```bash
git add tasks identity.toml
git commit -m "chore: start quarry"
work-link --ensure .worktrees
git worktree add -b foundation .worktrees/foundation
git worktree lock --reason "on WORK_ROOT storage (host: $(uname -n))" .worktrees/foundation
cd .worktrees/foundation
```

Expected: one commit on main; the worktree exists. Every later quarry step runs in
`$TREE/quarry/.worktrees/foundation`, written `$WT` below.

- [ ] **Step 4: Copy the front door from ops templates**

```bash
cp "$TREE/ops/templates/justfile" justfile
cp "$TREE/ops/templates/README.md" README.md
cp "$TREE/ops/templates/AGENTS.md" AGENTS.md
mkdir .githooks && cp "$TREE/ops/templates/githooks/"* .githooks/
cp "$TREE/ops/templates/gitignore" .gitignore
printf '.venv/\n__pycache__/\n.testmondata\n' >> .gitignore
git config core.hooksPath .githooks
(cd "$TREE/ops" && python3 bin/vendored adopt --into "$WT" tt ops-check ops-docs)
```

- [ ] **Step 5: Write pyproject.toml**

```toml
[project]
name = "quarry"
version = "0.1.0"
description = "One CLI and skills over scientific resources, with domains as lenses"
requires-python = ">=3.13"
dependencies = ["click>=8.1", "httpx>=0.28"]

[project.scripts]
quarry = "quarry.cli:main"

[dependency-groups]
dev = ["pytest>=8.4", "pytest-testmon>=2.1"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/quarry"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q"
```

- [ ] **Step 6: Fill the justfile's commands**

Edit the template's placeholder lines, leaving every recipe below them as copied:

```just
fast_cmd := "uv run pytest --testmon"
test_cmd := "uv run pytest"
check_cmd := "python3 tools/ops-check && python3 tools/ops-docs check && tasks check"
docs_paths := "*.md docs/* tasks/*"
docs_check_cmd := "python3 tools/ops-check && python3 tools/ops-docs check && tasks check"
ci_suite_refs := ""
ci_remote := "origin"
# testmon selects from its own dependency data, independent of the push base.
push_fast_cmd := fast_cmd
one_cmd := "uv run pytest"
setup_cmd := "just work-link .venv && uv sync --group dev"
```

Replace the template's comment above `fast_cmd` that says "With no affected-only
mechanism..." with: `# fast_cmd is affected-only through pytest-testmon.`

- [ ] **Step 7: Run setup**

Run: `just setup`
Expected: exits 0; `.venv` exists (a link into WORK_ROOT storage on a dotfiles host).

- [ ] **Step 8: Write the failing test**

`tests/__init__.py` is empty. `tests/test_cli_basics.py`:

```python
"""The root command: version, help, and the usage-error contract."""
import subprocess
import sys


def run(*args):
    return subprocess.run([sys.executable, "-m", "quarry.cli", *args], capture_output=True, text=True)


def test_version():
    for flag in ("--version", "-V"):
        out = run(flag)
        assert out.returncode == 0 and out.stdout.startswith("quarry 0.1.0")


def test_help():
    out = run("--help")
    assert out.returncode == 0 and "quarry" in out.stdout


def test_unknown_command_is_a_usage_error():
    out = run("bogus")
    assert out.returncode == 2 and out.stdout == ""
    assert out.stderr.splitlines()[-1] == "Run 'quarry --help'."
```

- [ ] **Step 9: Run it to see it fail**

Run: `just test-one tests/test_cli_basics.py`
Expected: FAIL with `No module named quarry.cli`.

- [ ] **Step 10: Write output.py and cli.py**

`src/quarry/__init__.py`:

```python
"""quarry: one CLI and skills over scientific resources, with domains as lenses."""
```

`src/quarry/output.py`:

```python
"""The CLI vocabulary's output mode for click: a decorator any command takes, the mode
resolved from flags then QUARRY_FORMAT, and the json failure object."""
import json
import os
import sys
from typing import NoReturn

import click

CONTEXT = {"help_option_names": ["-h", "--help"]}


def _choose(mode: str):
    def callback(ctx: click.Context, param: click.Parameter, value: bool) -> None:
        if not value:
            return
        seen = ctx.meta.get("quarry.mode")
        if seen is not None and seen != mode:
            raise click.UsageError("--json and --pretty are mutually exclusive", ctx)
        ctx.meta["quarry.mode"] = mode
    return callback


def output_options(command):
    """Two flags with their own destinations, so both callbacks run when both are given and
    the conflict is caught on one command and across the group/command boundary."""
    command = click.option("--json", "json_mode", is_flag=True, expose_value=False, callback=_choose("json"),
                           help="Emit one JSON value on stdout.")(command)
    return click.option("--pretty", "pretty_mode", is_flag=True, expose_value=False, callback=_choose("pretty"),
                        help="Emit text for a person (default; also QUARRY_FORMAT).")(command)


def mode(ctx: click.Context) -> str:
    chosen = ctx.meta.get("quarry.mode") or os.environ.get("QUARRY_FORMAT", "pretty")
    if chosen not in ("json", "pretty"):
        raise click.UsageError(f"QUARRY_FORMAT must be json or pretty, got {chosen!r}", ctx)
    return chosen


def emit(ctx: click.Context, report: dict, text: str) -> None:
    click.echo(json.dumps(report) if mode(ctx) == "json" else text)


def fail(ctx: click.Context, kind: str, detail: str) -> NoReturn:
    if mode(ctx) == "json":
        sys.stderr.write(json.dumps({"error": {"kind": kind, "detail": detail}}) + "\n")
    else:
        sys.stderr.write(f"quarry: {detail}\n")
    ctx.exit(1)
```

`src/quarry/cli.py`:

```python
"""The `quarry` command."""
import importlib.metadata
import sys

import click

from quarry.output import CONTEXT, output_options


class Cli(click.Group):
    """A usage error prints one line naming the problem and one pointing at --help, per the
    CLI vocabulary's exit-code and error contract."""

    def main(self, *args, **kwargs):
        kwargs.setdefault("prog_name", "quarry")
        kwargs.pop("standalone_mode", None)
        try:
            rv = super().main(*args, standalone_mode=False, **kwargs)
        except click.UsageError as error:
            prog = error.ctx.command_path if error.ctx else kwargs["prog_name"]
            click.echo(f"{prog}: {error.format_message()}", err=True)
            click.echo(f"Run '{kwargs['prog_name']} --help'.", err=True)
            sys.exit(2)
        except click.ClickException as error:
            error.show()
            sys.exit(error.exit_code)
        except click.Abort:
            click.echo("Aborted!", err=True)
            sys.exit(1)
        sys.exit(rv or 0)


@click.group(cls=Cli, context_settings=CONTEXT)
@click.version_option(importlib.metadata.version("quarry"), "-V", "--version", prog_name="quarry",
                      message="%(prog)s %(version)s")
@output_options
def main() -> None:
    """quarry: one CLI over scientific resources, with domains as lenses."""


@main.command("help", context_settings=CONTEXT)
@click.argument("words", nargs=-1)
@click.pass_context
def help_command(ctx: click.Context, words: tuple[str, ...]) -> None:
    """Print a command's help: `quarry help resources list`."""
    command, remaining = main, list(words)
    while remaining and isinstance(command, click.Group) and remaining[0] in command.commands:
        command = command.commands[remaining.pop(0)]
    if remaining:
        raise click.UsageError(f"unknown command {' '.join(words)}", ctx)
    click.echo(command.get_help(click.Context(command, info_name=" ".join(["quarry", *words]), **CONTEXT)))


if __name__ == "__main__":
    main()
```

- [ ] **Step 11: Run the tests**

Run: `just test-one tests/test_cli_basics.py`
Expected: 3 passed.

- [ ] **Step 12: Fill the guides and commit in the worktree**

Fill the template placeholders in `AGENTS.md`:

- Setup: `just setup` runs `uv sync --group dev` behind work-link.
- Gates: `just test-one <pytest args>` (a path under `tests/`, `path::name`, or `-k expr`); `just test-fast` (testmon); `just test`; `just check` (ops-check, ops-docs, tasks check); no CI, so the pre-push hook carries the full suite.
- Layout: `src/quarry/` (package; `catalog/` inside it), `tests/` (fixtures under `tests/fixtures/<resource>/`), `tools/` (vendored from ops).
- Rules: "Tests never reach the network: they replay `tests/fixtures/`, refreshed only by `just record <resource>`. A live call in a test makes the suite depend on services that fail (ENA's count endpoint returned 500 during the myeloma survey)."

Delete the README's status placeholder only if the template asks for it. Then:

```bash
just docs
just check
git add -A
git commit -m "chore: add quarry's front door and root command"
```

Expected: `just check` exits 0; the commit hook passes; the commit is on `foundation`, not main.

### Task 2: Register quarry in ops and add its CLI rows

**Files:**
- Modify: `$TREE/ops/identity-mirror.toml` (add `[quarry]`)
- Modify: `$TREE/ops/cli.toml` (add `[cli.quarry]` and its command rows)
- Generated by `ops-projects pull` in the ops worktree: the mirror's `name`/`purpose` for quarry and `$TREE/ops/instructions/fragments/projects.md`

**Interfaces:**
- Produces: the `[cli.quarry]` rows Task 9's conformance test compares with the live surface. Tasks 5 and 7 must build exactly these options, arguments and summaries.

- [ ] **Step 1: Create an ops worktree**

```bash
cd "$TREE/ops"
work-link --ensure .worktrees
git worktree add -b quarry-cli .worktrees/quarry-cli
git worktree lock --reason "on WORK_ROOT storage (host: $(uname -n))" .worktrees/quarry-cli
cd .worktrees/quarry-cli && just setup
```

- [ ] **Step 2: Add the identity-mirror entry**

Append to `identity-mirror.toml`, beside `[lit]`:

```toml
[quarry]
profiles = ["personal"]
path = "quarry"
```

Then generate what the mirror and the Projects fragment need, in this worktree, and read the
diff before going on:

```bash
python3 bin/ops-projects pull
git diff identity-mirror.toml instructions/fragments/projects.md
python3 bin/ops-projects check
```

Expected: the diff adds quarry's `name` and `purpose` to its mirror table and one quarry line
to the fragment, nothing else; `check` exits 0. `pull` reads quarry's `identity.toml` from its
main checkout, which Task 1, Step 3 committed.

- [ ] **Step 3: Add the CLI rows**

Append to `cli.toml` beside the other `[cli.*]` headers:

```toml
# quarry reads service credential variables under each service's own name (NCBI_API_KEY and
# the like): an exception to <NAME>_<OPTION>, recorded here because a CLI header has no
# `exception` field (ops-1aa74e).
[cli.quarry]
project = "quarry"
tier = "automation"
default_output = "pretty"
env = "QUARRY"
```

And in the commands section:

```toml
# ---- quarry

[[cli.quarry.commands]]
path = []
options = [
  { shared = "chdir", value = "path" },
  { shared = "config", value = "path" },
  { names = ["--trace"], value = "none" },
]

[[cli.quarry.commands]]
path = ["domains"]
summary = "The domains and their resources"

[[cli.quarry.commands]]
path = ["domains", "list"]
verb = "list"
summary = "List the domains, their resources and beliefs contracts"

[[cli.quarry.commands]]
path = ["resources"]
summary = "The catalog of resources"

[[cli.quarry.commands]]
path = ["resources", "list"]
verb = "list"
summary = "List the resources a domain selects"
options = [
  { names = ["--domain"], value = "string" },
  { names = ["--role"], value = "enum", values = ["identifier-scheme", "vocabulary", "ontology", "data-model", "repository", "knowledgebase", "literature-index"] },
  { names = ["--route"], value = "enum", values = ["rest", "query-endpoint", "bulk", "local-tool"] },
]

[[cli.quarry.commands]]
path = ["resources", "show"]
verb = "show"
summary = "Show one resource's roles, routes, limits and pitfalls"
args = [
  { name = "resource", value = "string", required = true },
]

[[cli.quarry.commands]]
path = ["id"]
summary = "Identifiers"

[[cli.quarry.commands]]
path = ["id", "check"]
verb = "check"
summary = "Check that identifiers are well formed for their prefixes"
args = [
  { name = "ids", value = "string", required = true, variadic = true },
]

[[cli.quarry.commands]]
path = ["id", "normalize"]
summary = "Print an identifier as a canonical CURIE"
args = [
  { name = "id", value = "string", required = true },
]

[[cli.quarry.commands]]
path = ["id", "resolve"]
summary = "Print the URLs that resolve a CURIE"
args = [
  { name = "curie", value = "string", required = true },
]

[[cli.quarry.commands]]
path = ["check"]
verb = "check"
summary = "Validate the catalog"

[[cli.quarry.commands]]
path = ["search"]
summary = "Search records across data-holding resources"
args = [
  { name = "phrases", value = "string", required = false, variadic = true },
]
options = [
  { names = ["--in"], value = "string", repeatable = true },
  { names = ["--domain"], value = "string" },
  { names = ["--organism"], value = "string" },
  { names = ["--exact"], value = "none" },
  { names = ["--native"], value = "string" },
  { names = ["--allow-partial"], value = "none" },
  { shared = "since", value = "when" },
  { shared = "until", value = "when" },
  { shared = "limit", value = "int" },
]

[[cli.quarry.commands]]
path = ["show"]
verb = "show"
summary = "Show one record"
args = [
  { name = "curie", value = "string", required = true },
]
```

- [ ] **Step 4: Validate and commit in ops**

Run the ops recipes that validate the table and the mirror: `just check` in the ops
worktree. Expected: exit 0. If the table validator rejects `verb` on a command whose name is
not that verb, remove that `verb` key and rerun.

```bash
git add identity-mirror.toml cli.toml instructions/fragments/projects.md
git commit -m "feat(cli): add quarry's rows and identity"
```

- [ ] **Step 5: Merge into ops main (personal checkout)**

```bash
cd "$TREE/ops" && git merge --ff-only quarry-cli
```

- [ ] **Step 6: Gate: deliver the Projects block (needs the user)**

The fragment is now on ops main, but nothing reads it until `just assemble` in lore delivers
it into every agent session's global instructions: a live global surface. Stop and ask the
user before running it, naming exactly this change (one line adding `quarry` to the Projects
list). On approval:

```bash
cd "$TREE/lore" && just assemble
```

Then commit lore's artifact and provenance manifest as `just assemble` reports. Without
approval, park this step and continue with Task 3: no later task depends on it.

- [ ] **Step 7: Remove the ops worktree**

```bash
cd "$TREE/ops"
git -C .worktrees/quarry-cli status --ignored --porcelain   # copy out anything still needed
tt-report
git worktree unlock .worktrees/quarry-cli && git worktree remove .worktrees/quarry-cli
git branch -d quarry-cli
```

### Task 3: The catalog: model, loader and check

**Files:**
- Create: `src/quarry/errors.py`, `src/quarry/catalog.py`, `src/quarry/adapters/__init__.py`, `src/quarry/catalog/domains/core.toml`, `src/quarry/catalog/domains/biology.toml`, `tests/test_catalog.py`

**Interfaces:**
- Produces: `quarry.errors.QuarryError(kind: str, detail: str)` with `.kind`, `.detail`.
- Produces: `quarry.catalog`: constants `ROLES`, `DATA_ROLES`, `ROUTE_KINDS`, `AUTH`, `CATALOG_ROOT`; dataclasses `Route`, `Pitfall`, `LocalPrefix`, `Resource` (method `owned_prefixes() -> tuple[str, ...]`), `Domain`, `Finding` (method `as_dict()`), `Catalog` (methods `lineage(domain_id) -> list[str]`, `effective_resources(domain_id) -> list[str]`, `search_set(domain_id) -> list[str]`, `domain_filters(domain_id) -> set[str]`, `owner(prefix) -> Resource | None`); `CatalogError(QuarryError)`; `load(root: Path = CATALOG_ROOT) -> Catalog`; `adapter_modules() -> list[str]`; `check(catalog: Catalog, registry: PrefixLookup, modules: list[str] | None = None) -> list[Finding]`, where `PrefixLookup` is any object with `canonical(prefix: str) -> str | None` and `is_upstream(prefix: str) -> bool`.

- [ ] **Step 1: Write the failing tests**

`tests/test_catalog.py`:

```python
"""The catalog loader refuses malformed files; check finds what a valid file can still get wrong."""
import textwrap

import pytest

from quarry import catalog
from quarry.catalog import CatalogError


class Lookup:
    """A stand-in registry: these prefixes are canonical, PMID is a synonym of pubmed."""
    CANONICAL = {"bioproject", "insdc.sra", "geo", "pubmed", "hgnc"}

    def canonical(self, prefix):
        p = prefix.lower()
        return "pubmed" if p == "pmid" else (p if p in self.CANONICAL else None)

    def is_upstream(self, prefix):
        return prefix in self.CANONICAL


ENA = """
id = "ena"
name = "European Nucleotide Archive"
roles = ["repository"]
prefixes = ["bioproject", "insdc.sra"]
adapter = "quarry.adapters"

[[routes]]
kind = "rest"
url = "https://www.ebi.ac.uk/ena/portal/api"
min_interval = 0.5
service = "ebi-ena"
auth = "none"
reports_total = true

[[pitfalls]]
summary = "wildcards cannot contain '-'"
handling = "equality clauses"
evidence = "mm-159cb7"
"""

BIOLOGY = """
id = "biology"
summary = "life sciences"
includes = ["core"]
resources = ["ena"]
search_default = ["ena"]
filters = ["organism"]
beliefs_contract = "biology"
beliefs_contract_version = 1

[facet_namespaces]
HGNC = "hgnc"
"""

CORE = """
id = "core"
summary = "shared"
resources = []
search_default = []
"""


def write(root, resources=None, domains=None):
    for sub, files in (("resources", resources or {}), ("domains", domains or {})):
        (root / sub).mkdir(parents=True, exist_ok=True)
        for name, text in files.items():
            (root / sub / f"{name}.toml").write_text(textwrap.dedent(text))
    return root


@pytest.fixture
def good(tmp_path):
    return write(tmp_path, {"ena": ENA}, {"core": CORE, "biology": BIOLOGY})


def test_load_reads_resources_and_domains(good):
    cat = catalog.load(good)
    ena = cat.resources["ena"]
    assert ena.roles == ("repository",) and ena.routes[0].service == "ebi-ena"
    assert ena.routes[0].min_interval == 0.5 and ena.routes[0].reports_total is True
    assert cat.domains["biology"].facet_namespaces == {"HGNC": "hgnc"}


def test_lens_merges_included_domains(good):
    cat = catalog.load(good)
    assert cat.lineage("biology") == ["biology", "core"]
    assert cat.effective_resources("biology") == ["ena"]
    assert cat.search_set("biology") == ["ena"] and cat.search_set("core") == []
    assert cat.domain_filters("biology") == {"organism"} and cat.domain_filters("core") == set()
    assert cat.owner("bioproject").id == "ena" and cat.owner("geo") is None


def test_unknown_domain_is_an_error(good):
    with pytest.raises(catalog.QuarryError) as caught:
        catalog.load(good).lineage("physics")
    assert caught.value.kind == "unknown_domain"


def check(root):
    return catalog.check(catalog.load(root), Lookup(), modules=[])


def test_clean_catalog_has_no_findings(good):
    assert check(good) == []


def test_check_finds_an_orphan_adapter(good):
    findings = catalog.check(catalog.load(good), Lookup(), modules=["quarry.adapters.zzz"])
    assert [f.kind for f in findings] == ["orphan_adapter"]


@pytest.mark.parametrize("text, detail", [
    (ENA.replace('name = "European Nucleotide Archive"\n', ""), "missing 'name'"),
    (ENA + 'colour = "blue"\n', "unknown keys ['colour']"),
    (ENA.replace("min_interval = 0.5", 'min_interval = "fast"'), "'min_interval' must be float"),
    (ENA.replace('roles = ["repository"]', "roles = [1]"), "'roles' must be a list of strings"),
])
def test_loader_refuses_malformed_files(tmp_path, text, detail):
    root = write(tmp_path, {"ena": text}, {"core": CORE})
    with pytest.raises(CatalogError) as caught:
        catalog.load(root)
    assert caught.value.kind == "catalog_invalid" and detail in caught.value.detail


def test_file_name_must_match_id(tmp_path):
    root = write(tmp_path, {"other": ENA}, {"core": CORE})
    with pytest.raises(CatalogError, match="differs from the file name"):
        catalog.load(root)


@pytest.mark.parametrize("edit, kind", [
    (lambda t: t.replace('roles = ["repository"]', 'roles = ["warehouse"]'), "unknown_role"),
    (lambda t: t.replace('kind = "rest"', 'kind = "carrier-pigeon"'), "unknown_route_kind"),
    (lambda t: t.replace('auth = "none"', 'auth = "optional-key"'), "missing_key_env"),
    (lambda t: t.replace('adapter = "quarry.adapters"', 'adapter = "quarry.adapters.nope"'), "missing_adapter"),
    (lambda t: t.replace('"insdc.sra"', '"sra"'), "unknown_prefix"),
    (lambda t: t.replace('handling = "equality clauses"', 'handling = ""'), "pitfall_incomplete"),
])
def test_check_findings_on_resources(tmp_path, edit, kind):
    root = write(tmp_path, {"ena": edit(ENA)}, {"core": CORE, "biology": BIOLOGY})
    kinds = [f.kind for f in check(root)]
    assert kind in kinds, kinds


def test_check_finds_a_prefix_owned_twice(tmp_path):
    twin = ENA.replace('id = "ena"', 'id = "twin"')
    root = write(tmp_path, {"ena": ENA, "twin": twin}, {"core": CORE})
    assert "prefix_owned_twice" in [f.kind for f in check(root)]


@pytest.mark.parametrize("edit, kind", [
    (lambda t: t.replace('resources = ["ena"]', 'resources = ["ena", "geo"]'), "missing_resource"),
    (lambda t: t.replace('includes = ["core"]', 'includes = ["chemistry"]'), "missing_domain"),
    (lambda t: t.replace('search_default = ["ena"]', 'search_default = ["ena", "x"]'), "search_default_outside"),
    (lambda t: t.replace('HGNC = "hgnc"', 'HGNC = "hugo"'), "unmapped_facet_namespace"),
])
def test_check_findings_on_domains(tmp_path, edit, kind):
    root = write(tmp_path, {"ena": ENA}, {"core": CORE, "biology": edit(BIOLOGY)})
    assert kind in [f.kind for f in check(root)]


def test_check_finds_an_include_cycle(tmp_path):
    core = CORE + 'includes = ["biology"]\n'
    root = write(tmp_path, {"ena": ENA}, {"core": core, "biology": BIOLOGY})
    assert "include_cycle" in [f.kind for f in check(root)]


def test_the_shipped_catalog_loads():
    cat = catalog.load()
    assert set(cat.domains) >= {"core", "biology"}
    assert cat.domains["biology"].beliefs_contract == "biology"
```

The test catalog points `adapter` at the package `quarry.adapters` itself so the
`missing_adapter` check has a real module to find; the shipped catalog names real adapter
modules from Task 8 on.

- [ ] **Step 2: Run them to see them fail**

Run: `just test-one tests/test_catalog.py`
Expected: FAIL with `cannot import name 'catalog' from 'quarry'`.

- [ ] **Step 3: Write errors.py and catalog.py**

`src/quarry/errors.py`:

```python
"""The one error type: a kind for the error object and a detail for a person."""


class QuarryError(Exception):
    def __init__(self, kind: str, detail: str):
        super().__init__(detail)
        self.kind = kind
        self.detail = detail
```

`src/quarry/adapters/__init__.py`:

```python
"""One module per resource, or per service several resources share; each exposes make(resource)."""
```

`src/quarry/catalog.py`:

```python
"""The catalog: every resource and domain quarry knows, loaded from TOML and checked.

Loading refuses a file whose shape is wrong (a missing or mistyped key, an unknown key);
`check` reports what a well-shaped catalog can still get wrong (spec §6)."""
from __future__ import annotations

import importlib.util
import pkgutil
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from quarry.errors import QuarryError

ROLES = ("identifier-scheme", "vocabulary", "ontology", "data-model",
         "repository", "knowledgebase", "literature-index")
DATA_ROLES = frozenset({"repository", "knowledgebase", "literature-index"})
ROUTE_KINDS = ("rest", "query-endpoint", "bulk", "local-tool")
AUTH = ("none", "optional-key", "required-key")
CATALOG_ROOT = Path(__file__).parent / "catalog"
NOT_ADAPTERS = frozenset({"base"})
_REQUIRED = object()


class CatalogError(QuarryError):
    def __init__(self, where: str, detail: str):
        super().__init__("catalog_invalid", f"{where}: {detail}")


class PrefixLookup(Protocol):
    def canonical(self, prefix: str) -> str | None: ...

    def is_upstream(self, prefix: str) -> bool: ...   # in Bioregistry itself, not a local prefix


@dataclass(frozen=True)
class Route:
    kind: str
    url: str
    min_interval: float
    service: str
    auth: str
    reports_total: bool
    key_env: str | None = None
    keyed_min_interval: float | None = None
    key_param: str | None = None
    key_header: str | None = None
    page_cap: int | None = None


@dataclass(frozen=True)
class Pitfall:
    summary: str
    handling: str
    evidence: str


@dataclass(frozen=True)
class LocalPrefix:
    pattern: str
    uri_format: str
    why: str


@dataclass(frozen=True)
class Resource:
    id: str
    name: str
    roles: tuple[str, ...]
    adapter: str
    routes: tuple[Route, ...]
    prefixes: tuple[str, ...] = ()
    local_prefixes: dict[str, LocalPrefix] = field(default_factory=dict)
    fairsharing: str | None = None
    pitfalls: tuple[Pitfall, ...] = ()

    def owned_prefixes(self) -> tuple[str, ...]:
        return self.prefixes + tuple(self.local_prefixes)


@dataclass(frozen=True)
class Domain:
    id: str
    summary: str
    resources: tuple[str, ...]
    search_default: tuple[str, ...]
    includes: tuple[str, ...] = ()
    filters: tuple[str, ...] = ()
    beliefs_contract: str | None = None
    beliefs_contract_version: int | None = None
    facet_namespaces: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Finding:
    kind: str
    where: str
    detail: str

    def as_dict(self) -> dict:
        return {"kind": self.kind, "where": self.where, "detail": self.detail}


@dataclass(frozen=True)
class Catalog:
    resources: dict[str, Resource]
    domains: dict[str, Domain]

    def lineage(self, domain_id: str) -> list[str]:
        """The domain, then everything it includes, depth first, each once."""
        if domain_id not in self.domains:
            raise QuarryError("unknown_domain", f"no domain {domain_id!r}; known: {', '.join(sorted(self.domains))}")
        seen: list[str] = []

        def visit(d: str) -> None:
            if d in seen or d not in self.domains:
                return
            seen.append(d)
            for inc in self.domains[d].includes:
                visit(inc)

        visit(domain_id)
        return seen

    def _union(self, domain_id: str, attr: str) -> list[str]:
        out: list[str] = []
        for d in self.lineage(domain_id):
            out += [r for r in getattr(self.domains[d], attr) if r not in out]
        return out

    def effective_resources(self, domain_id: str) -> list[str]:
        return self._union(domain_id, "resources")

    def search_set(self, domain_id: str) -> list[str]:
        return self._union(domain_id, "search_default")

    def domain_filters(self, domain_id: str) -> set[str]:
        return set(self._union(domain_id, "filters"))

    def owner(self, prefix: str) -> Resource | None:
        return next((r for r in self.resources.values() if prefix in r.owned_prefixes()), None)


def _table(path: Path, where: str) -> dict:
    try:
        return tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as error:
        raise CatalogError(where, f"not valid TOML: {error}") from error


def _only(table: dict, where: str, allowed: set[str]) -> None:
    extra = set(table) - allowed
    if extra:
        raise CatalogError(where, f"unknown keys {sorted(extra)}")


def _get(table: dict, where: str, key: str, kind: type, default=_REQUIRED):
    if key not in table:
        if default is _REQUIRED:
            raise CatalogError(where, f"missing {key!r}")
        return default
    value = table[key]
    if kind is float and type(value) is int:
        value = float(value)
    if type(value) is not kind:
        raise CatalogError(where, f"{key!r} must be {kind.__name__}")
    return value


def _strs(table: dict, where: str, key: str, required: bool = False) -> tuple[str, ...]:
    value = _get(table, where, key, list, _REQUIRED if required else [])
    if any(type(item) is not str for item in value):
        raise CatalogError(where, f"{key!r} must be a list of strings")
    return tuple(value)


ROUTE_KEYS = {"kind", "url", "min_interval", "service", "auth", "reports_total", "key_env",
              "keyed_min_interval", "key_param", "key_header", "page_cap"}
RESOURCE_KEYS = {"id", "name", "roles", "prefixes", "local_prefixes", "fairsharing", "adapter", "routes", "pitfalls"}
DOMAIN_KEYS = {"id", "summary", "includes", "resources", "search_default", "filters", "beliefs_contract",
               "beliefs_contract_version", "facet_namespaces"}


def _route(t: dict, where: str) -> Route:
    _only(t, where, ROUTE_KEYS)
    return Route(
        kind=_get(t, where, "kind", str), url=_get(t, where, "url", str),
        min_interval=_get(t, where, "min_interval", float), service=_get(t, where, "service", str),
        auth=_get(t, where, "auth", str), reports_total=_get(t, where, "reports_total", bool),
        key_env=_get(t, where, "key_env", str, None),
        keyed_min_interval=_get(t, where, "keyed_min_interval", float, None),
        key_param=_get(t, where, "key_param", str, None), key_header=_get(t, where, "key_header", str, None),
        page_cap=_get(t, where, "page_cap", int, None))


def _pitfall(t: dict, where: str) -> Pitfall:
    _only(t, where, {"summary", "handling", "evidence"})
    return Pitfall(_get(t, where, "summary", str), _get(t, where, "handling", str), _get(t, where, "evidence", str))


def _resource(t: dict, where: str) -> Resource:
    _only(t, where, RESOURCE_KEYS)
    routes = _get(t, where, "routes", list)
    if not routes or any(type(r) is not dict for r in routes):
        raise CatalogError(where, "'routes' must be one or more [[routes]] tables")
    local = _get(t, where, "local_prefixes", dict, {})
    locals_: dict[str, LocalPrefix] = {}
    for prefix, body in local.items():
        w = f"{where} local_prefixes.{prefix}"
        if type(body) is not dict:
            raise CatalogError(w, "must be a table")
        _only(body, w, {"pattern", "uri_format", "why"})
        locals_[prefix] = LocalPrefix(_get(body, w, "pattern", str), _get(body, w, "uri_format", str), _get(body, w, "why", str))
    return Resource(
        id=_get(t, where, "id", str), name=_get(t, where, "name", str), roles=_strs(t, where, "roles", True),
        adapter=_get(t, where, "adapter", str),
        routes=tuple(_route(r, f"{where} routes[{i}]") for i, r in enumerate(routes)),
        prefixes=_strs(t, where, "prefixes"), local_prefixes=locals_,
        fairsharing=_get(t, where, "fairsharing", str, None),
        pitfalls=tuple(_pitfall(p, f"{where} pitfalls[{i}]") for i, p in enumerate(_get(t, where, "pitfalls", list, []))))


def _domain(t: dict, where: str) -> Domain:
    _only(t, where, DOMAIN_KEYS)
    namespaces = _get(t, where, "facet_namespaces", dict, {})
    if any(type(v) is not str for v in namespaces.values()):
        raise CatalogError(where, "'facet_namespaces' values must be strings")
    return Domain(
        id=_get(t, where, "id", str), summary=_get(t, where, "summary", str),
        resources=_strs(t, where, "resources", True), search_default=_strs(t, where, "search_default", True),
        includes=_strs(t, where, "includes"), filters=_strs(t, where, "filters"),
        beliefs_contract=_get(t, where, "beliefs_contract", str, None),
        beliefs_contract_version=_get(t, where, "beliefs_contract_version", int, None),
        facet_namespaces=dict(namespaces))


def _read(root: Path, sub: str, parse) -> dict:
    out = {}
    for path in sorted((root / sub).glob("*.toml")):
        where = f"{sub}/{path.name}"
        item = parse(_table(path, where), where)
        if item.id != path.stem:
            raise CatalogError(where, f"id {item.id!r} differs from the file name")
        out[item.id] = item
    return out


def load(root: Path = CATALOG_ROOT) -> Catalog:
    return Catalog(_read(root, "resources", _resource), _read(root, "domains", _domain))


def _adapter_exists(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


def adapter_modules() -> list[str]:
    """Every adapter module the package ships."""
    import quarry.adapters
    return [f"quarry.adapters.{m.name}" for m in pkgutil.iter_modules(quarry.adapters.__path__)
            if m.name not in NOT_ADAPTERS]


def check(catalog: Catalog, registry: PrefixLookup, modules: list[str] | None = None) -> list[Finding]:
    """`modules` are the adapter modules to hold against the catalog; None means every one the
    package ships. A test catalog passes its own list."""
    found: list[Finding] = []

    def add(kind: str, where: str, detail: str) -> None:
        found.append(Finding(kind, where, detail))

    owners: dict[str, str] = {}
    for r in catalog.resources.values():
        where = f"resources/{r.id}.toml"
        if not r.roles:
            add("unknown_role", where, "a resource has at least one role")
        for role in r.roles:
            if role not in ROLES:
                add("unknown_role", where, f"{role!r} is not one of {', '.join(ROLES)}")
        for route in r.routes:
            if route.kind not in ROUTE_KINDS:
                add("unknown_route_kind", where, f"{route.kind!r} is not one of {', '.join(ROUTE_KINDS)}")
            if route.auth not in AUTH:
                add("unknown_auth", where, f"{route.auth!r} is not one of {', '.join(AUTH)}")
            if route.auth != "none" and not route.key_env:
                add("missing_key_env", where, f"auth {route.auth!r} needs key_env")
            if route.key_env and not (route.key_param or route.key_header):
                add("missing_key_location", where, "a route with key_env names key_param or key_header")
        if not _adapter_exists(r.adapter):
            add("missing_adapter", where, f"no module {r.adapter!r}")
        for p in r.prefixes:
            if not registry.is_upstream(p) or registry.canonical(p) != p:
                add("unknown_prefix", where, f"{p!r} is not a canonical Bioregistry prefix")
        for p in r.local_prefixes:
            if registry.is_upstream(p):
                add("local_prefix_in_bioregistry", where, f"{p!r} is in Bioregistry; list it under prefixes")
        for p in r.owned_prefixes():
            if p in owners:
                add("prefix_owned_twice", where, f"{p!r} is already owned by {owners[p]}")
            owners.setdefault(p, r.id)
        for pit in r.pitfalls:
            if not (pit.summary and pit.handling and pit.evidence):
                add("pitfall_incomplete", where, f"pitfall {pit.summary!r} needs summary, handling and evidence")

    referenced = {r.adapter for r in catalog.resources.values()}
    for name in adapter_modules() if modules is None else modules:
        if name not in referenced:
            add("orphan_adapter", name, "no resource names this adapter")

    for d in catalog.domains.values():
        where = f"domains/{d.id}.toml"
        for rid in d.resources:
            if rid not in catalog.resources:
                add("missing_resource", where, f"no resource {rid!r}")
        for rid in d.search_default:
            if rid not in d.resources:
                add("search_default_outside", where, f"{rid!r} is searched by default but not listed in resources")
        for inc in d.includes:
            if inc not in catalog.domains:
                add("missing_domain", where, f"no domain {inc!r}")
        for ns, prefix in d.facet_namespaces.items():
            if registry.canonical(prefix) is None:
                add("unmapped_facet_namespace", where, f"{ns} maps to {prefix!r}, which is not a known prefix")
        if _cycles(catalog, d.id):
            add("include_cycle", where, f"{d.id} includes itself through {', '.join(d.includes)}")
    return found


def _cycles(catalog: Catalog, start: str) -> bool:
    stack = list(catalog.domains[start].includes)
    seen: set[str] = set()
    while stack:
        d = stack.pop()
        if d == start:
            return True
        if d in seen or d not in catalog.domains:
            continue
        seen.add(d)
        stack += catalog.domains[d].includes
    return False
```

- [ ] **Step 4: Write the shipped domain files**

`src/quarry/catalog/domains/core.toml`:

```toml
id = "core"
summary = "Resources every science shares: general repositories, literature, identifiers"
resources = []
search_default = []
```

`src/quarry/catalog/domains/biology.toml`:

```toml
id = "biology"
summary = "Life-science repositories, knowledgebases, identifiers and ontologies"
includes = ["core"]
resources = []
search_default = []
filters = ["organism"]
beliefs_contract = "biology"           # the contract science activates by this name
beliefs_contract_version = 1           # the version this domain was written against

[facet_namespaces]                     # the contract's facet namespaces, as Bioregistry prefixes
HGNC = "hgnc"
```

- [ ] **Step 5: Run the tests**

Run: `just test-one tests/test_catalog.py`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
just test-fast
git add src/quarry tests/test_catalog.py
git commit -m "feat(catalog): load and check resources and domains"
```

### Task 4: The Bioregistry snapshot and identifiers

**Files:**
- Create: `tools/vendor_bioregistry.py`, `src/quarry/catalog/bioregistry.json` (generated), `src/quarry/catalog/SOURCES.toml` (generated), `src/quarry/ids.py`, `tests/test_ids.py`
- Modify: `justfile` (add `bioregistry-vendor`)

**Interfaces:**
- Consumes: `quarry.catalog.Catalog`, `Resource.local_prefixes`, `CATALOG_ROOT`, `Finding`; `quarry.errors.QuarryError`.
- Produces: `quarry.ids`: `REGISTRY_PATH`; `Scheme(prefix, name, pattern: re.Pattern | None, uri_format: str | None)`; `Curie(prefix: str, local: str)` with `__str__`; `Registry` with `load(path=REGISTRY_PATH) -> Registry` (classmethod), `with_local(catalog) -> Registry`, `canonical(prefix) -> str | None`, `is_upstream(prefix) -> bool`, `scheme(prefix) -> Scheme`, `version: str`; `parse(text, registry) -> Curie`; `check_ids(texts, registry) -> list[Finding]`; `normalize(text, registry, owned: Iterable[str]) -> Curie`; `resolve(curie, registry) -> list[str]`.

- [ ] **Step 1: Write the vendoring script**

`tools/vendor_bioregistry.py`:

```python
"""Write src/quarry/catalog/bioregistry.json and SOURCES.toml from an installed bioregistry.

Run through `just bioregistry-vendor <version>`, which installs that exact version for this
one run. Only the fields quarry reads are kept: name, pattern, synonyms, uri_format."""
import datetime
import importlib.metadata
import json
import sys
from pathlib import Path

import bioregistry

CATALOG = Path(__file__).resolve().parents[1] / "src" / "quarry" / "catalog"


def main() -> None:
    version = importlib.metadata.version("bioregistry")
    prefixes = {}
    for prefix, resource in sorted(bioregistry.read_registry().items()):
        if resource.is_deprecated():
            continue
        prefixes[prefix] = {
            "name": resource.get_name(),
            "pattern": resource.get_pattern(),
            "synonyms": sorted(resource.get_synonyms()),
            "uri_format": resource.get_uri_format(),
        }
    (CATALOG / "bioregistry.json").write_text(
        json.dumps({"source": "bioregistry", "version": version, "prefixes": prefixes}, sort_keys=True, indent=1) + "\n")
    (CATALOG / "SOURCES.toml").write_text(
        f'[bioregistry]\nversion = "{version}"\nvendored = "{datetime.date.today().isoformat()}"\n'
        f'file = "bioregistry.json"\n')
    print(f"bioregistry {version}: {len(prefixes)} prefixes", file=sys.stderr)


if __name__ == "__main__":
    main()
```

Add to the justfile, after `docs`:

```just
# Refresh the pinned Bioregistry snapshot from one exact release (PyPI version).
bioregistry-vendor version:
    {{tt}} bioregistry-vendor -- uv run --no-project --with "bioregistry=={{version}}" python tools/vendor_bioregistry.py
```

- [ ] **Step 2: Vendor the current release**

Find the latest release: `uv pip index versions bioregistry` (or the PyPI page) and use its
newest non-pre-release version, then:

Run: `just bioregistry-vendor <that version>`
Expected: `bioregistry <version>: N prefixes` with N above 1500; `bioregistry.json` and
`SOURCES.toml` exist. If `get_synonyms` is missing on that version's `Resource`, the run
fails with AttributeError: stop and report it rather than reading private fields.

- [ ] **Step 3: Write the failing tests**

`tests/test_ids.py`:

```python
"""Identifiers: canonical CURIEs from the pinned snapshot (spec §7)."""
import pytest

from quarry import catalog, ids
from quarry.catalog import Catalog, LocalPrefix, Resource, Route
from quarry.errors import QuarryError

REG = ids.Registry.load()


def test_snapshot_is_pinned():
    assert REG.version and REG.canonical("geo") == "geo"


@pytest.mark.parametrize("text, expected", [
    ("geo:GSE24080", "geo:GSE24080"),
    ("GEO:GSE24080", "geo:GSE24080"),      # Review Focus 3: uppercase prefix
    ("PMID:21885717", "pubmed:21885717"),  # Review Focus 3: synonym
    ("pmid:21885717", "pubmed:21885717"),
    ("bioproject:PRJNA123456", "bioproject:PRJNA123456"),
])
def test_parse_prints_canonical(text, expected):
    assert str(ids.parse(text, REG)) == expected


@pytest.mark.parametrize("text, kind", [
    ("GSE24080", "not_a_curie"),
    ("geo:", "not_a_curie"),
    ("nosuchprefix:1", "unknown_prefix"),
    ("geo:XYZ1", "malformed"),
])
def test_parse_refusals(text, kind):
    with pytest.raises(QuarryError) as caught:
        ids.parse(text, REG)
    assert caught.value.kind == kind


def test_check_ids_reports_each_bad_id():
    findings = ids.check_ids(["geo:GSE1", "geo:XYZ", "nosuch:1"], REG)
    assert [f.kind for f in findings] == ["malformed", "unknown_prefix"]
    assert ids.check_ids(["geo:GSE1", "pubmed:1"], REG) == []


def test_bare_accession_matches_owned_prefixes_only():
    # ena.embl's pattern matches nearly any accession, so it is never owned (spec §7).
    assert str(ids.normalize("GSE24080", REG, ["geo", "bioproject", "insdc.sra"])) == "geo:GSE24080"
    assert str(ids.normalize("GEO:GSE24080", REG, [])) == "geo:GSE24080"


def test_bare_accession_ambiguity_names_candidates():
    with pytest.raises(QuarryError) as caught:
        ids.normalize("21885717", REG, ["pubmed", "ncbitaxon"])
    assert caught.value.kind == "ambiguous_id"
    assert "pubmed" in caught.value.detail and "ncbitaxon" in caught.value.detail


def test_bare_accession_with_no_match():
    with pytest.raises(QuarryError) as caught:
        ids.normalize("GSE24080", REG, ["pubmed"])
    assert caught.value.kind == "unknown_id"


def test_resolve_fills_the_uri_format():
    urls = ids.resolve(ids.parse("geo:GSE24080", REG), REG)
    assert urls and all("GSE24080" in u for u in urls)


def test_local_prefixes_join_the_registry():
    route = Route(kind="rest", url="https://api.figshare.com/v2", min_interval=0.5, service="figshare",
                  auth="none", reports_total=False)
    fig = Resource(id="figshare", name="figshare", roles=("repository",), adapter="quarry.adapters",
                   routes=(route,), local_prefixes={"figshare": LocalPrefix(r"^\d+$", "https://figshare.com/articles/$1",
                                                                            "Bioregistry has no figshare prefix")})
    cat = Catalog({"figshare": fig}, {})
    reg = REG.with_local(cat)
    assert str(ids.parse("FIGSHARE:34254439", reg)) == "figshare:34254439"
    assert ids.resolve(ids.parse("figshare:1", reg), reg) == ["https://figshare.com/articles/1"]
    assert reg.is_upstream("geo") and not reg.is_upstream("figshare")
    # a valid local prefix checks clean against the merged registry it joined
    assert catalog.check(cat, reg, modules=[]) == []


def test_the_shipped_catalog_checks_clean_against_the_snapshot():
    cat = catalog.load()
    assert catalog.check(cat, REG.with_local(cat)) == []
```

- [ ] **Step 4: Run them to see them fail**

Run: `just test-one tests/test_ids.py`
Expected: FAIL with `cannot import name 'ids' from 'quarry'`.

- [ ] **Step 5: Write ids.py**

`src/quarry/ids.py`:

```python
"""Identifiers as CURIEs with Bioregistry's canonical prefixes, from the pinned snapshot
(spec §7). Prefix lookup is case-insensitive and accepts synonyms; local ids are kept as
given and matched against the prefix's pattern."""
from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from quarry.catalog import CATALOG_ROOT, Catalog, Finding
from quarry.errors import QuarryError

REGISTRY_PATH = CATALOG_ROOT / "bioregistry.json"


@dataclass(frozen=True)
class Scheme:
    prefix: str
    name: str
    pattern: re.Pattern | None
    uri_format: str | None


@dataclass(frozen=True)
class Curie:
    prefix: str
    local: str

    def __str__(self) -> str:
        return f"{self.prefix}:{self.local}"


class Registry:
    def __init__(self, version: str, schemes: dict[str, Scheme], lookup: dict[str, str],
                 local: frozenset[str] = frozenset()):
        self.version = version
        self._schemes = schemes
        self._lookup = lookup
        self._local = local

    @classmethod
    def load(cls, path: Path = REGISTRY_PATH) -> Registry:
        doc = json.loads(path.read_text())
        schemes, lookup = {}, {}
        for prefix, body in doc["prefixes"].items():
            pattern = re.compile(body["pattern"]) if body.get("pattern") else None
            schemes[prefix] = Scheme(prefix, body.get("name") or prefix, pattern, body.get("uri_format"))
            lookup[prefix.lower()] = prefix
        for prefix, body in doc["prefixes"].items():
            for synonym in body.get("synonyms") or ():
                lookup.setdefault(synonym.lower(), prefix)  # a canonical prefix always wins
        return cls(doc["version"], schemes, lookup)

    def with_local(self, catalog: Catalog) -> Registry:
        schemes, lookup, added = dict(self._schemes), dict(self._lookup), set()
        for resource in catalog.resources.values():
            for prefix, local in resource.local_prefixes.items():
                if prefix in self._schemes:
                    continue        # already upstream: check() reports it; never shadow Bioregistry
                schemes[prefix] = Scheme(prefix, resource.name, re.compile(local.pattern), local.uri_format)
                lookup[prefix.lower()] = prefix
                added.add(prefix)
        return Registry(self.version, schemes, lookup, self._local | added)

    def canonical(self, prefix: str) -> str | None:
        return self._lookup.get(prefix.lower())

    def is_upstream(self, prefix: str) -> bool:
        return prefix in self._schemes and prefix not in self._local

    def scheme(self, prefix: str) -> Scheme:
        return self._schemes[prefix]


def parse(text: str, registry: Registry) -> Curie:
    prefix, separator, local = text.partition(":")
    if not separator or not prefix or not local:
        raise QuarryError("not_a_curie", f"{text!r} is not <prefix>:<id>; `quarry id normalize` takes a bare accession")
    canonical = registry.canonical(prefix)
    if canonical is None:
        raise QuarryError("unknown_prefix", f"{prefix!r} is not a known prefix")
    pattern = registry.scheme(canonical).pattern
    if pattern is not None and not pattern.fullmatch(local):
        raise QuarryError("malformed", f"{local!r} does not match {canonical}'s pattern {pattern.pattern}")
    return Curie(canonical, local)


def check_ids(texts: Iterable[str], registry: Registry) -> list[Finding]:
    findings = []
    for text in texts:
        try:
            parse(text, registry)
        except QuarryError as error:
            findings.append(Finding(error.kind, text, error.detail))
    return findings


def normalize(text: str, registry: Registry, owned: Iterable[str]) -> Curie:
    prefix, separator, _ = text.partition(":")
    if separator and registry.canonical(prefix) is not None:
        return parse(text, registry)
    matches = sorted(p for p in owned if (s := registry.scheme(p)).pattern is not None and s.pattern.fullmatch(text))
    if not matches:
        raise QuarryError("unknown_id", f"{text!r} matches no prefix a catalog resource owns")
    if len(matches) > 1:
        raise QuarryError("ambiguous_id", f"{text!r} matches {', '.join(matches)}; write it as <prefix>:{text}")
    return Curie(matches[0], text)


def resolve(curie: Curie, registry: Registry) -> list[str]:
    uri = registry.scheme(curie.prefix).uri_format
    return [uri.replace("$1", curie.local)] if uri else []
```

- [ ] **Step 6: Run the tests**

Run: `just test-one tests/test_ids.py`
Expected: all pass. If `ncbitaxon`'s pattern does not match `21885717`, replace it in
`test_bare_accession_ambiguity_names_candidates` with another owned-looking prefix from the
snapshot whose pattern is all digits (`grep -n '"pattern": "\^\\\\d+\$"' src/quarry/catalog/bioregistry.json`).

- [ ] **Step 7: Commit**

```bash
just test-fast
git add tools/vendor_bioregistry.py justfile src/quarry/catalog/bioregistry.json src/quarry/catalog/SOURCES.toml src/quarry/ids.py tests/test_ids.py
git commit -m "feat(ids): CURIEs against a pinned Bioregistry snapshot"
```

### Task 5: The lens, the catalog commands and the id commands

**Files:**
- Create: `src/quarry/lens.py`, `src/quarry/context.py`, `tests/conftest.py`, `tests/test_lens.py`, `tests/test_cli_catalog.py`
- Modify: `src/quarry/cli.py`, `justfile` (`check_cmd` gains `uv run quarry check`)

**Interfaces:**
- Consumes: `quarry.catalog.load`, `check`, `ROLES`, `ROUTE_KINDS`, `DATA_ROLES`, `CatalogError`, `Finding`; `quarry.ids.Registry`, `parse`, `check_ids`, `normalize`, `resolve`; `quarry.output.emit`, `fail`, `output_options`.
- Produces: `quarry.cli.hoist_globals(args: list[str]) -> list[str]`; `quarry.lens.CONFIG_NAME`, `find_config(start: Path) -> Path | None`, `resolve_domain(flag: str | None, environ: Mapping[str, str], config: Path | None, cwd: Path, catalog: Catalog) -> str`; `quarry.context.CATALOG_ROOT` (module global tests monkeypatch), `Env(catalog, registry)`, `open_env() -> Env`, `make_client(trace: bool)` (defined in Task 6); `quarry.cli.State(config: Path | None, trace: bool)` on `ctx.obj`; `quarry.cli.reports_errors` decorator. The test fixture `make_catalog(resources: dict[str, str], biology: list[str], search: list[str]) -> Path` (in `tests/conftest.py`), which Tasks 7 and 8 reuse.

- [ ] **Step 1: Write the failing tests**

`tests/conftest.py`:

```python
import json
import os
import shutil
import textwrap

import pytest

from quarry import context

CORE = 'id = "core"\nsummary = "test core"\nresources = []\nsearch_default = []\n'
BIOLOGY = '''id = "biology"
summary = "test biology"
includes = ["core"]
resources = {resources}
search_default = {search}
filters = ["organism"]
beliefs_contract = "biology"
beliefs_contract_version = 1
'''


@pytest.fixture
def make_catalog(tmp_path, monkeypatch):
    """Build a catalog for one test and point every command at it. The shipped resource files
    are copied in too, so every shipped adapter stays referenced and `check` stays clean."""
    def build(resources: dict[str, str], biology: list[str], search: list[str]):
        root = tmp_path / "catalog"
        shipped = context.CATALOG_ROOT / "resources"
        if shipped.is_dir():
            shutil.copytree(shipped, root / "resources")
        else:
            (root / "resources").mkdir(parents=True)
        (root / "domains").mkdir()
        for rid, text in resources.items():
            (root / "resources" / f"{rid}.toml").write_text(textwrap.dedent(text))
        (root / "domains" / "core.toml").write_text(CORE)
        (root / "domains" / "biology.toml").write_text(
            BIOLOGY.format(resources=json.dumps(biology), search=json.dumps(search)))
        monkeypatch.setattr(context, "CATALOG_ROOT", root)
        return root
    return build


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """No test sees the host's QUARRY_* settings or service keys."""
    for name in list(os.environ):
        if name.startswith("QUARRY_") or name.endswith("_API_KEY"):
            monkeypatch.delenv(name)
```

`tests/test_lens.py`:

```python
"""Which domain a command uses: flag, then QUARRY_DOMAIN, then quarry.toml, then core (spec §8.1)."""
import pytest

from quarry import catalog, lens
from quarry.errors import QuarryError

CAT = catalog.load()


def test_default_is_core(tmp_path):
    assert lens.resolve_domain(None, {}, None, tmp_path, CAT) == "core"


def test_precedence(tmp_path):
    (tmp_path / "quarry.toml").write_text('domain = "biology"\n')
    sub = tmp_path / "a" / "b"
    sub.mkdir(parents=True)
    assert lens.resolve_domain(None, {}, None, sub, CAT) == "biology"            # nearest file above
    assert lens.resolve_domain(None, {"QUARRY_DOMAIN": "core"}, None, sub, CAT) == "core"
    assert lens.resolve_domain("biology", {"QUARRY_DOMAIN": "core"}, None, sub, CAT) == "biology"


def test_explicit_config_wins_over_discovery(tmp_path):
    (tmp_path / "quarry.toml").write_text('domain = "biology"\n')
    other = tmp_path / "other.toml"
    other.write_text('domain = "core"\n')
    assert lens.resolve_domain(None, {}, other, tmp_path, CAT) == "core"


@pytest.mark.parametrize("setup, kind", [
    (lambda p: None, "config_not_found"),
    (lambda p: p.write_text('domain = "biology"\ncolour = 1\n'), "config_invalid"),
    (lambda p: p.write_text("domain = [\n"), "config_invalid"),
])
def test_bad_explicit_config(tmp_path, setup, kind):
    path = tmp_path / "q.toml"
    setup(path)
    with pytest.raises(QuarryError) as caught:
        lens.resolve_domain(None, {}, path, tmp_path, CAT)
    assert caught.value.kind == kind


def test_unknown_domain(tmp_path):
    with pytest.raises(QuarryError) as caught:
        lens.resolve_domain("physics", {}, None, tmp_path, CAT)
    assert caught.value.kind == "unknown_domain"
```

`tests/test_cli_catalog.py`:

```python
"""The catalog and id commands, in-process."""
import json

from click.testing import CliRunner

from quarry.cli import main

ALPHA = """
id = "alpha"
name = "Alpha archive"
roles = ["repository"]
prefixes = ["geo"]
adapter = "quarry.adapters"
[[routes]]
kind = "rest"
url = "https://alpha.example"
min_interval = 0.5
service = "alpha"
auth = "none"
reports_total = true
"""


def invoke(*args, env=None):
    return CliRunner().invoke(main, list(args), env=env, catch_exceptions=False)


def test_domains_list_json():
    out = invoke("--json", "domains", "list")
    assert out.exit_code == 0
    rows = {d["id"]: d for d in json.loads(out.stdout)["domains"]}
    assert rows["biology"]["includes"] == ["core"] and rows["biology"]["beliefs_contract"] == "biology"


def test_resources_list_filters_by_role(make_catalog):
    make_catalog({"alpha": ALPHA}, ["alpha"], [])
    listed = json.loads(invoke("--json", "resources", "list", "--domain", "biology").stdout)["resources"]
    assert [r["id"] for r in listed] == ["alpha"]
    assert json.loads(invoke("--json", "resources", "list", "--domain", "biology", "--role", "ontology").stdout)["resources"] == []
    shown = json.loads(invoke("--json", "resources", "show", "alpha").stdout)
    assert shown["roles"] == ["repository"] and shown["routes"][0]["service"] == "alpha"


def test_resources_show_unknown_is_an_error_object():
    out = invoke("--json", "resources", "show", "nope")
    assert out.exit_code == 1 and out.stdout == ""
    assert json.loads(out.stderr)["error"]["kind"] == "unknown_resource"


def test_check_is_silent_when_clean():
    out = invoke("check")
    assert (out.exit_code, out.stdout) == (0, "")


def test_check_reports_findings(make_catalog):
    make_catalog({}, ["ghost"], [])
    out = invoke("--json", "check")
    assert out.exit_code == 1
    assert [f["kind"] for f in json.loads(out.stdout)["findings"]] == ["missing_resource"]
    other = invoke("--json", "domains", "list")   # every other command refuses an invalid catalog
    assert other.exit_code == 1 and json.loads(other.stderr)["error"]["kind"] == "catalog_invalid"


def test_id_check():
    assert (invoke("id", "check", "geo:GSE1", "PMID:1").exit_code, invoke("id", "check", "geo:GSE1").stdout) == (0, "")
    out = invoke("--json", "id", "check", "geo:GSE1", "geo:XYZ")
    assert out.exit_code == 1 and [f["kind"] for f in json.loads(out.stdout)["findings"]] == ["malformed"]


def test_id_normalize_and_resolve():
    assert json.loads(invoke("--json", "id", "normalize", "GEO:GSE24080").stdout) == {"id": "geo:GSE24080"}
    resolved = json.loads(invoke("--json", "id", "resolve", "geo:GSE24080").stdout)
    assert resolved["id"] == "geo:GSE24080" and resolved["urls"]


def test_root_config_option_sets_the_domain(tmp_path):
    cfg = tmp_path / "q.toml"
    cfg.write_text('domain = "biology"\n')
    out = invoke("--json", "--config", str(cfg), "resources", "list")
    assert json.loads(out.stdout)["domain"] == "biology"
    assert json.loads(invoke("--json", "resources", "list", env={"QUARRY_DOMAIN": "biology"}).stdout)["domain"] == "biology"
```

- [ ] **Step 2: Run them to see them fail**

Run: `just test-one tests/test_lens.py tests/test_cli_catalog.py`
Expected: FAIL with `cannot import name 'lens' from 'quarry'`.

- [ ] **Step 3: Write lens.py and context.py**

`src/quarry/lens.py`:

```python
"""The lens: which domain a command uses (spec §8.1)."""
from __future__ import annotations

import tomllib
from collections.abc import Mapping
from pathlib import Path

from quarry.catalog import Catalog
from quarry.errors import QuarryError

CONFIG_NAME = "quarry.toml"
CONFIG_KEYS = {"domain"}


def find_config(start: Path) -> Path | None:
    for directory in (start, *start.parents):
        candidate = directory / CONFIG_NAME
        if candidate.is_file():
            return candidate
    return None


def _read(path: Path) -> dict:
    try:
        doc = tomllib.loads(path.read_text())
    except tomllib.TOMLDecodeError as error:
        raise QuarryError("config_invalid", f"{path}: not valid TOML: {error}") from error
    extra = set(doc) - CONFIG_KEYS
    if extra:
        raise QuarryError("config_invalid", f"{path}: unknown keys {sorted(extra)}")
    if "domain" in doc and type(doc["domain"]) is not str:
        raise QuarryError("config_invalid", f"{path}: 'domain' must be a string")
    return doc


def resolve_domain(flag: str | None, environ: Mapping[str, str], config: Path | None, cwd: Path,
                   catalog: Catalog) -> str:
    if config is not None and not config.is_file():
        raise QuarryError("config_not_found", f"config file not found: {config}")
    value = flag or environ.get("QUARRY_DOMAIN") or None
    if value is None:
        path = config if config is not None else find_config(cwd)
        if path is not None:
            value = _read(path).get("domain")
    elif config is not None:
        _read(config)                       # an explicit file is validated even when unused
    domain = value or "core"
    catalog.lineage(domain)                 # raises unknown_domain
    return domain
```

`src/quarry/context.py`:

```python
"""What every command opens: the checked catalog and the registry. Tests monkeypatch
CATALOG_ROOT to point a command at a catalog of their own."""
from __future__ import annotations

from dataclasses import dataclass

from quarry import catalog as catalog_mod
from quarry import ids
from quarry.errors import QuarryError

CATALOG_ROOT = catalog_mod.CATALOG_ROOT


@dataclass(frozen=True)
class Env:
    catalog: catalog_mod.Catalog
    registry: ids.Registry


def load_unchecked() -> Env:
    cat = catalog_mod.load(CATALOG_ROOT)
    return Env(cat, ids.Registry.load().with_local(cat))


def open_env() -> Env:
    env = load_unchecked()
    findings = catalog_mod.check(env.catalog, env.registry)
    if findings:
        detail = "; ".join(f"{f.where}: {f.detail}" for f in findings)
        raise QuarryError("catalog_invalid", f"{detail} (run `quarry check`)")
    return env
```

- [ ] **Step 4: Add the root options and commands to cli.py**

Replace the root `main` definition in `src/quarry/cli.py` and add the commands below it
(keep `Cli` and `help_command` as they are; add these imports at the top):

```python
import dataclasses
import functools
import os
from pathlib import Path

from quarry import context
from quarry import ids as idmod
from quarry.catalog import DATA_ROLES, ROLES, ROUTE_KINDS, CatalogError, Finding
from quarry.errors import QuarryError
from quarry.lens import resolve_domain
from quarry.output import CONTEXT, emit, fail, output_options


@dataclasses.dataclass(frozen=True)
class State:
    config: Path | None
    trace: bool


def reports_errors(f):
    """A QuarryError becomes the error object (json) or one line (pretty), exit 1."""
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except QuarryError as error:
            fail(click.get_current_context(), error.kind, error.detail)
    return wrapper


def state(ctx: click.Context) -> State:
    return ctx.find_object(State)


@click.group(cls=Cli, context_settings=CONTEXT)
@click.version_option(importlib.metadata.version("quarry"), "-V", "--version", prog_name="quarry",
                      message="%(prog)s %(version)s")
@output_options
@click.option("-C", "chdir", type=click.Path(file_okay=False, exists=True, path_type=Path),
              help="Run as if started in that directory.")
@click.option("--config", type=click.Path(dir_okay=False, path_type=Path),
              help="Read this file instead of the nearest quarry.toml.")
@click.option("--trace", is_flag=True, envvar="QUARRY_TRACE", help="Print every request to stderr (also QUARRY_TRACE).")
@click.pass_context
def main(ctx: click.Context, chdir: Path | None, config: Path | None, trace: bool) -> None:
    """quarry: one CLI over scientific resources, with domains as lenses."""
    if chdir is not None:
        os.chdir(chdir)
    ctx.obj = State(config=config.resolve() if config is not None else None, trace=trace)


def _findings(ctx: click.Context, findings: list[Finding]) -> None:
    if findings:
        emit(ctx, {"findings": [f.as_dict() for f in findings]},
             "\n".join(f"{f.where}: {f.kind}: {f.detail}" for f in findings))
        ctx.exit(1)


@main.group(context_settings=CONTEXT)
def domains() -> None:
    """The domains and their resources."""


@domains.command("list", context_settings=CONTEXT)
@output_options
@click.pass_context
@reports_errors
def domains_list(ctx: click.Context) -> None:
    """List the domains, their resources and beliefs contracts."""
    env = context.open_env()
    rows = [{"id": d.id, "summary": d.summary, "includes": list(d.includes),
             "resources": env.catalog.effective_resources(d.id), "beliefs_contract": d.beliefs_contract,
             "beliefs_contract_version": d.beliefs_contract_version}
            for d in sorted(env.catalog.domains.values(), key=lambda d: d.id)]
    emit(ctx, {"domains": rows},
         "\n".join(f"{r['id']}\t{', '.join(r['resources']) or '-'}\t{r['beliefs_contract'] or '-'}" for r in rows))


@main.group(context_settings=CONTEXT)
def resources() -> None:
    """The catalog of resources."""


@resources.command("list", context_settings=CONTEXT)
@output_options
@click.option("--domain", help="List this domain's resources (also QUARRY_DOMAIN).")
@click.option("--role", type=click.Choice(ROLES), help="Only resources with this role.")
@click.option("--route", type=click.Choice(ROUTE_KINDS), help="Only resources with a route of this kind.")
@click.pass_context
@reports_errors
def resources_list(ctx: click.Context, domain: str | None, role: str | None, route: str | None) -> None:
    """List the resources a domain selects."""
    env = context.open_env()
    chosen = resolve_domain(domain, os.environ, state(ctx).config, Path.cwd(), env.catalog)
    rows = []
    for rid in env.catalog.effective_resources(chosen):
        r = env.catalog.resources[rid]
        if role and role not in r.roles or route and route not in {x.kind for x in r.routes}:
            continue
        rows.append({"id": r.id, "name": r.name, "roles": list(r.roles), "prefixes": list(r.owned_prefixes())})
    emit(ctx, {"domain": chosen, "resources": rows},
         "\n".join(f"{r['id']}\t{', '.join(r['roles'])}\t{r['name']}" for r in rows) or f"({chosen}: no resources)")


@resources.command("show", context_settings=CONTEXT)
@output_options
@click.argument("resource")
@click.pass_context
@reports_errors
def resources_show(ctx: click.Context, resource: str) -> None:
    """Show one resource's roles, routes, limits and pitfalls."""
    env = context.open_env()
    r = env.catalog.resources.get(resource)
    if r is None:
        raise QuarryError("unknown_resource", f"no resource {resource!r}")
    report = dataclasses.asdict(r)
    report["local_prefixes"] = {k: dataclasses.asdict(v) for k, v in r.local_prefixes.items()}
    lines = [f"{r.name} ({r.id}): {', '.join(r.roles)}"]
    lines += [f"  route {x.kind} {x.url} (service {x.service}, every {x.min_interval}s)" for x in r.routes]
    lines += [f"  pitfall: {p.summary} -> {p.handling}" for p in r.pitfalls]
    emit(ctx, report, "\n".join(lines))


@main.group("id", context_settings=CONTEXT)
def id_group() -> None:
    """Identifiers."""


@id_group.command("check", context_settings=CONTEXT)
@output_options
@click.argument("ids", nargs=-1, required=True)
@click.pass_context
@reports_errors
def id_check(ctx: click.Context, ids: tuple[str, ...]) -> None:
    """Check that identifiers are well formed for their prefixes."""
    _findings(ctx, idmod.check_ids(ids, context.open_env().registry))


@id_group.command("normalize", context_settings=CONTEXT)
@output_options
@click.argument("id")
@click.pass_context
@reports_errors
def id_normalize(ctx: click.Context, id: str) -> None:
    """Print an identifier as a canonical CURIE."""
    env = context.open_env()
    owned = [p for r in env.catalog.resources.values() for p in r.owned_prefixes()]
    curie = idmod.normalize(id, env.registry, owned)
    emit(ctx, {"id": str(curie)}, str(curie))


@id_group.command("resolve", context_settings=CONTEXT)
@output_options
@click.argument("curie")
@click.pass_context
@reports_errors
def id_resolve(ctx: click.Context, curie: str) -> None:
    """Print the URLs that resolve a CURIE."""
    env = context.open_env()
    parsed = idmod.parse(curie, env.registry)
    urls = idmod.resolve(parsed, env.registry)
    if not urls:
        raise QuarryError("no_resolver", f"no URL format is known for {parsed.prefix}")
    emit(ctx, {"id": str(parsed), "urls": urls}, "\n".join(urls))


@main.command("check", context_settings=CONTEXT)
@output_options
@click.pass_context
@reports_errors
def check_command(ctx: click.Context) -> None:
    """Validate the catalog."""
    from quarry import catalog as catalog_mod
    try:
        env = context.load_unchecked()
    except CatalogError as error:
        _findings(ctx, [Finding("catalog_invalid", "catalog", error.detail)])
        return
    _findings(ctx, catalog_mod.check(env.catalog, env.registry))
```

The argument names (`ids`, `id`, `curie`, `resource`) are the names the conformance rows
(Task 2) give them: `cli_surface.click_rows` reads each parameter's name. That is why the
module is imported as `idmod`.

Then make the global options work in every position the conventions allow (`<name> [global
options] <command> [options]`, with global options "accepted before the command and after
it"). `-C`, `--config` and `--trace` are root options only, so their rows stay at the root of
the table; `Cli.main` moves them to the front of the arguments before click parses. Replace
the `Cli` class from Task 1 with:

```python
GLOBAL_VALUED = frozenset({"-C", "--config"})
GLOBAL_FLAGS = frozenset({"--trace"})


def hoist_globals(args: list[str]) -> list[str]:
    """Move root-only global options to the front, wherever they were written. `--` ends the
    options: nothing after it moves."""
    front, rest, i = [], [], 0
    while i < len(args):
        word = args[i]
        if word == "--":
            rest += args[i:]
            break
        if word in GLOBAL_FLAGS or word.split("=", 1)[0] == "--config" and "=" in word:
            front.append(word)
        elif word in GLOBAL_VALUED:
            front += args[i:i + 2]
            i += 1
        else:
            rest.append(word)
        i += 1
    return front + rest


class Cli(click.Group):
    """Global options are accepted before and after the command; a usage error prints one line
    naming the problem and one pointing at --help (the CLI vocabulary's exit-code contract)."""

    def main(self, args=None, **kwargs):
        kwargs.setdefault("prog_name", "quarry")
        kwargs.pop("standalone_mode", None)
        args = hoist_globals(list(sys.argv[1:] if args is None else args))
        try:
            rv = super().main(args, standalone_mode=False, **kwargs)
        except click.UsageError as error:
            prog = error.ctx.command_path if error.ctx else kwargs["prog_name"]
            click.echo(f"{prog}: {error.format_message()}", err=True)
            click.echo(f"Run '{kwargs['prog_name']} --help'.", err=True)
            sys.exit(2)
        except click.ClickException as error:
            error.show()
            sys.exit(error.exit_code)
        except click.Abort:
            click.echo("Aborted!", err=True)
            sys.exit(1)
        sys.exit(rv or 0)
```

`--json` and `--pretty` are accepted on the groups too: decorate `domains`, `resources` and
`id_group` with `@output_options` (after `@main.group(...)`), as every leaf already is.

Append to `tests/test_cli_catalog.py`:

```python
import os

import pytest

from quarry.cli import hoist_globals


def test_hoist_globals():
    assert hoist_globals(["resources", "list", "--config", "q.toml", "-C", "d", "--trace"]) == \
        ["--config", "q.toml", "-C", "d", "--trace", "resources", "list"]
    assert hoist_globals(["search", "--config=q.toml", "x"]) == ["--config=q.toml", "search", "x"]
    assert hoist_globals(["search", "--", "-C", "x"]) == ["search", "--", "-C", "x"]


@pytest.mark.parametrize("place", ["root", "group", "leaf"])
def test_config_in_every_position(tmp_path, place):
    cfg = tmp_path / "q.toml"
    cfg.write_text('domain = "biology"\n')
    args = {"root": ["--config", str(cfg), "resources", "list"],
            "group": ["resources", "--config", str(cfg), "list"],
            "leaf": ["resources", "list", "--config", str(cfg)]}[place]
    out = invoke("--json", *args)
    assert out.exit_code == 0 and json.loads(out.stdout)["domain"] == "biology"


def test_chdir_after_the_command(tmp_path, monkeypatch):
    monkeypatch.chdir(os.getcwd())                     # restored after the test
    (tmp_path / "quarry.toml").write_text('domain = "biology"\n')
    out = invoke("--json", "resources", "list", "-C", str(tmp_path))
    assert json.loads(out.stdout)["domain"] == "biology"


def test_output_flags_on_a_group():
    assert json.loads(invoke("domains", "--json", "list").stdout)["domains"]
```

`invoke` runs `main` through `CliRunner`, which calls `Cli.main(args=...)`, so these tests
exercise the hoist exactly as the binary does.

- [ ] **Step 5: Run the tests**

Run: `just test-one tests/test_lens.py tests/test_cli_catalog.py tests/test_cli_basics.py`
Expected: all pass.

- [ ] **Step 6: Add `quarry check` to the gate and commit**

In the justfile: `check_cmd := "python3 tools/ops-check && python3 tools/ops-docs check && uv run quarry check && tasks check"`.

```bash
just check && just test-fast
git add src/quarry tests justfile
git commit -m "feat(cli): domain lens, catalog and id commands"
```

### Task 6: The HTTP client and recorded fixtures

**Files:**
- Create: `src/quarry/http.py`, `src/quarry/testing.py`, `tests/test_http.py`
- Modify: `src/quarry/context.py` (add `make_client`)

**Interfaces:**
- Consumes: `quarry.catalog.Route`, `Catalog`; `quarry.errors.QuarryError`.
- Produces: `quarry.http`: `REDACTED = "REDACTED"`, `MAX_ATTEMPTS = 5`, `WAIT_BUDGET = 60.0`, `MAX_REDIRECTS = 5`, `SystemClock`, `Throttle(clock)` with `wait(service: str, key: str | None, interval: float)` and `.clock`, `PROCESS_THROTTLE` (the one throttle every client in a process shares by default), `UpstreamError(QuarryError)` (kind `upstream_failed`), `Client(*, transport=None, throttle=None, trace=None, environ=None)` with `request(route, method, url, *, params=None, json=None, data=None) -> httpx.Response`, `close()`, context-manager methods. `quarry.testing`: `KEPT_HEADERS = ("content-type", "retry-after", "location")`, `VirtualClock`, `replay_client(transport) -> Client`, `secret_params(catalog) -> frozenset[str]`, `exchange_key(request, secret_params) -> dict`, `exchange(method, url, params=None, *, status=200, body="", content_type="application/json", headers=None, json_body=None, form=None) -> dict`, `ReplayTransport(exchanges: list[dict], secret_params=frozenset())` (each recording answers once, in order), `ReplayTransport.from_files(paths, secret_params)`, `RecordingTransport(secret_params, secrets, inner=None)` with `exchanges` and `save(path)`. `quarry.context.make_client(trace: bool) -> Client`.

- [ ] **Step 1: Write the failing tests**

`tests/test_http.py`:

```python
"""The shared client: one throttle per service and key across the process, retries within a
wait budget, credentials that never leave their origin or reach a log (spec §9)."""
import email.utils
import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from quarry.catalog import Route
from quarry.http import Client, Throttle, UpstreamError
from quarry.testing import RecordingTransport, ReplayTransport, exchange, exchange_key


class FakeClock:
    def __init__(self):
        self.t = 0.0
        self.slept = []

    def monotonic(self):
        return self.t

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.t += seconds


def route(service="eutils", interval=0.34, **kw):
    return Route(kind="rest", url="https://eutils.example/entrez", min_interval=interval, service=service,
                 auth=kw.pop("auth", "none"), reports_total=True, **kw)


def keyed(**kw):
    return route(auth="optional-key", key_env="TEST_KEY", keyed_min_interval=0.1, **kw)


def mock(handler):
    return httpx.MockTransport(handler)


def client(handler, clock=None, **kw):
    return Client(transport=mock(handler), throttle=Throttle(clock or FakeClock()), **kw)


def test_one_throttle_per_service_across_routes_and_clients():
    clock, times = FakeClock(), []
    throttle = Throttle(clock)

    def ok(request):
        times.append(clock.t)
        return httpx.Response(200)
    first, second = Client(transport=mock(ok), throttle=throttle), Client(transport=mock(ok), throttle=throttle)
    geo, pubmed = route(), route()
    for c, r in ((first, geo), (second, pubmed), (first, pubmed), (second, geo)):
        c.request(r, "GET", "esearch.fcgi")
    assert all(b - a >= 0.34 - 1e-9 for a, b in zip(times, times[1:]))
    before = clock.t
    first.request(route(service="ebi-ena"), "GET", "x")        # another service waits on nothing
    assert clock.t == before


def test_clients_share_the_process_throttle_by_default():
    a, b = Client(transport=mock(lambda r: httpx.Response(200))), Client(transport=mock(lambda r: httpx.Response(200)))
    assert a._throttle is b._throttle


def test_keyed_interval_and_key_parameter():
    seen, clock = [], FakeClock()
    c = client(lambda r: (seen.append(r.url), httpx.Response(200))[1], clock, environ={"TEST_KEY": "k1"})
    c.request(keyed(key_param="api_key"), "GET", "a")
    c.request(keyed(key_param="api_key"), "GET", "a")
    assert seen[0].params["api_key"] == "k1" and clock.slept == [pytest.approx(0.1)]


def test_empty_key_variable_is_unset():
    seen = []
    client(lambda r: (seen.append(r.url), httpx.Response(200))[1], environ={"TEST_KEY": ""}).request(
        keyed(key_param="api_key"), "GET", "a")
    assert "api_key" not in seen[0].params


def statuses(*codes, headers=None):
    codes = list(codes)
    return lambda request: httpx.Response(codes.pop(0), headers=headers or {})


def test_retries_transient_statuses_with_backoff():
    clock = FakeClock()
    assert client(statuses(503, 429, 200), clock).request(route(interval=0), "GET", "x").status_code == 200
    assert clock.slept == [1, 2]


def test_retry_after_seconds_and_http_date():
    clock = FakeClock()
    client(statuses(429, 200, headers={"Retry-After": "3"}), clock).request(route(interval=0), "GET", "x")
    assert clock.slept == [3]
    when = email.utils.format_datetime(datetime.now(timezone.utc) + timedelta(seconds=20), usegmt=True)
    clock = FakeClock()
    client(statuses(503, 200, headers={"Retry-After": when}), clock).request(route(interval=0), "GET", "x")
    assert 15 <= clock.slept[0] <= 21


def test_retry_after_beyond_the_budget_fails_without_retrying_early():    # Review Focus 5
    clock = FakeClock()
    with pytest.raises(UpstreamError, match="asked to wait 3600 s"):
        client(statuses(429, 200, headers={"Retry-After": "3600"}), clock).request(route(interval=0), "GET", "x")
    assert clock.slept == []


def test_client_errors_fail_at_once_and_exhaustion_fails():
    with pytest.raises(UpstreamError, match="HTTP 404"):
        client(statuses(404)).request(route(), "GET", "x")
    with pytest.raises(UpstreamError, match="HTTP 503"):
        client(statuses(*[503] * 5)).request(route(interval=0), "GET", "x")


def test_transport_errors_retry_then_fail():
    def down(request):
        raise httpx.ConnectError("refused", request=request)
    clock = FakeClock()
    with pytest.raises(UpstreamError, match="ConnectError after 5 attempts"):
        client(down, clock).request(route(interval=0), "GET", "x")
    assert clock.slept == [1, 2, 4, 8]


def test_redirects_keep_credentials_on_their_origin_only():
    sentinel, seen = "SENTINEL-7f3a", []

    def hop(request):
        seen.append(request)
        if request.url.host == "eutils.example" and request.url.path.endswith("/start"):
            return httpx.Response(302, headers={"Location": "https://eutils.example/entrez/moved"})
        if request.url.path.endswith("/moved"):
            return httpx.Response(302, headers={"Location": f"https://elsewhere.example/x?api_key={sentinel}"})
        return httpx.Response(200)
    c = client(hop, environ={"TEST_KEY": sentinel})
    c.request(keyed(key_param="api_key", key_header="X-Api-Key"), "GET", "start")
    same, other = seen[1], seen[2]
    assert same.headers["X-Api-Key"] == sentinel                       # same origin keeps it
    assert other.url.host == "elsewhere.example"
    assert sentinel not in str(other.url) and "X-Api-Key" not in other.headers


def test_a_redirected_post_fails():
    with pytest.raises(UpstreamError, match="redirected"):
        client(lambda r: httpx.Response(307, headers={"Location": "https://eutils.example/y"})).request(
            route(), "POST", "x", data={"a": "1"})


def test_the_credential_never_leaks():
    sentinel, lines = "SENTINEL-7f3a", []

    def echo(request):
        return httpx.Response(500 if request.url.path.endswith("fail") else 200, text=f"echo {request.url}")
    recorder = RecordingTransport(frozenset({"api_key"}), [sentinel], inner=mock(echo))
    c = Client(transport=recorder, throttle=Throttle(FakeClock()), trace=lines.append, environ={"TEST_KEY": sentinel})
    c.request(keyed(key_param="api_key"), "GET", "ok", params={"term": "x"})
    with pytest.raises(UpstreamError) as caught:
        c.request(keyed(key_param="api_key"), "GET", "fail")
    recorded = json.dumps(recorder.exchanges)
    assert sentinel not in "\n".join(lines) and sentinel not in caught.value.detail and sentinel not in recorded
    assert "REDACTED" in "\n".join(lines)


def test_replay_answers_in_recorded_order_with_headers():
    first = exchange("GET", "https://eutils.example/entrez/x", status=503, headers={"retry-after": "1"})
    second = exchange("GET", "https://eutils.example/entrez/x", body='{"ok": true}')
    clock = FakeClock()
    c = Client(transport=ReplayTransport([first, second]), throttle=Throttle(clock))
    assert c.request(route(interval=0), "GET", "x").json() == {"ok": True} and clock.slept == [1]
    with pytest.raises(LookupError, match="no recorded exchange"):
        c.request(route(interval=0), "GET", "x")                       # each recording answers once


def test_replay_matches_method_url_sorted_query_and_body_but_not_the_key():
    ex = exchange("POST", "https://eutils.example/entrez/esummary.fcgi", {"db": "gds", "retmode": "json"},
                  form={"id": "1,2"}, body='{"ok": true}')
    http = httpx.Client(transport=ReplayTransport([ex], frozenset({"api_key"})))
    hit = http.post("https://eutils.example/entrez/esummary.fcgi",
                    params={"retmode": "json", "db": "gds", "api_key": "secret"}, data={"id": "1,2"})
    assert hit.json() == {"ok": True}
    with pytest.raises(LookupError, match="no recorded exchange"):
        http.post("https://eutils.example/entrez/esummary.fcgi", params={"db": "gds", "retmode": "json"},
                  data={"id": "3"})


def test_exchange_key_shape():
    request = httpx.Request("GET", "https://h.example/p", params={"b": "2", "a": "1"})
    assert exchange_key(request, frozenset()) == {"method": "GET", "url": "https://h.example/p",
                                                  "query": [["a", "1"], ["b", "2"]], "body": None}
```

- [ ] **Step 2: Run them to see them fail**

Run: `just test-one tests/test_http.py`
Expected: FAIL with `No module named 'quarry.http'`.

- [ ] **Step 3: Write http.py**

`src/quarry/http.py`:

```python
"""The one HTTP client (spec §9). A throttle per service and key is shared by every client in
the process; retries back off and honour Retry-After within a wait budget; redirects are
followed for GET only, and a credential never leaves its origin or reaches a trace line or an
error detail."""
from __future__ import annotations

import email.utils
import importlib.metadata
import os
import time
from collections.abc import Callable, Mapping
from datetime import datetime, timezone

import httpx

from quarry.catalog import Route
from quarry.errors import QuarryError

REDACTED = "REDACTED"
RETRY_STATUS = frozenset({408, 429, 500, 502, 503, 504})
MAX_ATTEMPTS = 5
WAIT_BUDGET = 60.0
MAX_REDIRECTS = 5
TIMEOUT = 60.0


class SystemClock:
    monotonic = staticmethod(time.monotonic)
    sleep = staticmethod(time.sleep)


class Throttle:
    """The minimum interval between requests to one service under one key."""

    def __init__(self, clock):
        self.clock = clock
        self._last: dict[tuple[str, str | None], float] = {}

    def wait(self, service: str, key: str | None, interval: float) -> None:
        last = self._last.get((service, key))
        if last is not None:
            gap = interval - (self.clock.monotonic() - last)
            if gap > 0:
                self.clock.sleep(gap)
        self._last[(service, key)] = self.clock.monotonic()


PROCESS_THROTTLE = Throttle(SystemClock())


class UpstreamError(QuarryError):
    def __init__(self, detail: str):
        super().__init__("upstream_failed", detail)


def _retry_after(response: httpx.Response) -> float | None:
    """Retry-After as seconds (RFC 9110 §10.2.3: delay-seconds or an HTTP-date), or None."""
    value = response.headers.get("Retry-After", "").strip()
    if not value:
        return None
    if value.isdigit():
        return float(value)
    try:
        when = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, (when - datetime.now(timezone.utc)).total_seconds())


def _origin(url: httpx.URL) -> tuple[str, str, int | None]:
    return (url.scheme, url.host, url.port)


class Client:
    def __init__(self, *, transport: httpx.BaseTransport | None = None, throttle: Throttle | None = None,
                 trace: Callable[[str], None] | None = None, environ: Mapping[str, str] | None = None):
        version = importlib.metadata.version("quarry")
        self._http = httpx.Client(transport=transport, timeout=TIMEOUT, follow_redirects=False,
                                  headers={"User-Agent": f"quarry/{version} (+https://github.com/khughitt/quarry)"})
        self._throttle = throttle or PROCESS_THROTTLE
        self._trace = trace
        self._environ = os.environ if environ is None else environ

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self._http.close()

    def _key(self, route: Route) -> str | None:
        return (self._environ.get(route.key_env) or None) if route.key_env else None

    def _shown(self, url: httpx.URL, route: Route) -> str:
        if route.key_param and route.key_param in url.params:
            url = url.copy_set_param(route.key_param, REDACTED)
        return str(url)

    def _log(self, line: str) -> None:
        if self._trace is not None:
            self._trace(line)

    def _send(self, route: Route, request: httpx.Request, shown: str, credentials: dict[str, str]) -> httpx.Response:
        """Send, following GET redirects. Each hop is a fresh request: it carries the credential
        headers only on the original origin, and a hop elsewhere loses the key parameter too."""
        origin = _origin(request.url)
        for _ in range(MAX_REDIRECTS + 1):
            response = self._http.send(request)
            if not response.is_redirect:
                return response
            if request.method != "GET":
                raise UpstreamError(f"{request.method} {shown}: redirected; quarry follows redirects for GET only")
            target = request.url.join(response.headers["Location"])
            same = _origin(target) == origin
            if not same and route.key_param:
                target = target.copy_remove_param(route.key_param)
            request = self._http.build_request("GET", target, headers=credentials if same else {})
        raise UpstreamError(f"{shown}: more than {MAX_REDIRECTS} redirects")

    def request(self, route: Route, method: str, url: str, *, params: Mapping | None = None,
                json: object = None, data: Mapping | None = None) -> httpx.Response:
        key = self._key(route)
        params = dict(params or {})
        headers = {}
        if key:
            if route.key_param:
                params[route.key_param] = key
            if route.key_header:
                headers[route.key_header] = key
        full = url if url.startswith(("http://", "https://")) else f"{route.url.rstrip('/')}/{url.lstrip('/')}"
        shown = self._shown(httpx.URL(full, params=params), route)
        interval = route.keyed_min_interval if key and route.keyed_min_interval is not None else route.min_interval
        sleep = self._throttle.clock.sleep
        for attempt in range(1, MAX_ATTEMPTS + 1):
            self._throttle.wait(route.service, key, interval)
            request = self._http.build_request(method, full, params=params, json=json, data=data, headers=headers)
            try:
                response = self._send(route, request, shown, headers)
            except httpx.TransportError as error:
                self._log(f"{method} {shown} -> {type(error).__name__}")
                if attempt == MAX_ATTEMPTS:
                    raise UpstreamError(f"{method} {shown}: {type(error).__name__} after {attempt} attempts") from None
                sleep(2 ** (attempt - 1))
                continue
            self._log(f"{method} {shown} -> {response.status_code}")
            if response.status_code in RETRY_STATUS and attempt < MAX_ATTEMPTS:
                delay = _retry_after(response)
                if delay is not None and delay > WAIT_BUDGET:
                    raise UpstreamError(f"{method} {shown}: HTTP {response.status_code}, asked to wait "
                                        f"{delay:.0f} s, beyond the {WAIT_BUDGET:.0f} s budget")
                sleep(delay if delay is not None else 2 ** (attempt - 1))
                continue
            if response.status_code >= 400:
                raise UpstreamError(f"{method} {shown}: HTTP {response.status_code}")
            return response
        raise AssertionError("unreachable: the last attempt returns or raises")
```

- [ ] **Step 4: Write testing.py**

`src/quarry/testing.py`:

```python
"""Recorded exchanges for tests (spec §12). A request key of method, URL, sorted query and
body, with credential parameters left out; a replaying transport that answers each recording
once, in recorded order, and refuses any request it has none left for; and a recording
transport that scrubs credentials before saving."""
from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

import httpx

from quarry.catalog import Catalog
from quarry.http import REDACTED, Client, Throttle

KEPT_HEADERS = ("content-type", "retry-after", "location")


class VirtualClock:
    """A clock that advances when slept on, without sleeping: replays wait for nothing."""

    def __init__(self):
        self.t = 0.0

    def monotonic(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        self.t += seconds


def replay_client(transport: httpx.BaseTransport) -> Client:
    """A client for tests: its own throttle on a virtual clock, never the process throttle."""
    return Client(transport=transport, throttle=Throttle(VirtualClock()))


def secret_params(catalog: Catalog) -> frozenset[str]:
    return frozenset(r.key_param for res in catalog.resources.values() for r in res.routes if r.key_param)


def exchange_key(request: httpx.Request, secrets: frozenset[str]) -> dict:
    url = request.url
    query = sorted([k, v] for k, v in url.params.multi_items() if k not in secrets)
    body = request.content.decode() if request.content else None
    return {"method": request.method, "url": f"{url.scheme}://{url.host}{url.path}", "query": query, "body": body}


def exchange(method: str, url: str, params: dict | None = None, *, status: int = 200, body: str = "",
             content_type: str = "application/json", headers: dict | None = None, json_body: object = None,
             form: dict | None = None) -> dict:
    """A hand-made exchange, keyed exactly as a live request with these arguments would be.
    `body` is the response body; `json_body` and `form` are the request's."""
    request = httpx.Request(method, url, params=params, json=json_body, data=form)
    return {"request": exchange_key(request, frozenset()),
            "response": {"status": status, "headers": {"content-type": content_type, **(headers or {})}, "body": body}}


class ReplayTransport(httpx.BaseTransport):
    def __init__(self, exchanges: list[dict], secrets: frozenset[str] = frozenset()):
        self.pending = list(exchanges)
        self.secrets = secrets

    @classmethod
    def from_files(cls, paths: Iterable[Path], secrets: frozenset[str] = frozenset()) -> ReplayTransport:
        return cls([e for p in paths for e in json.loads(Path(p).read_text())], secrets)

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        key = exchange_key(request, self.secrets)
        for index, ex in enumerate(self.pending):
            if ex["request"] == key:
                del self.pending[index]
                r = ex["response"]
                return httpx.Response(r["status"], headers=r["headers"], content=r["body"].encode(), request=request)
        raise LookupError(f"no recorded exchange left for {json.dumps(key)}")


class RecordingTransport(httpx.BaseTransport):
    def __init__(self, secrets: frozenset[str], secret_values: Iterable[str], inner: httpx.BaseTransport | None = None):
        self.secrets = secrets
        self.secret_values = [v for v in secret_values if v]
        self.inner = inner or httpx.HTTPTransport()
        self.exchanges: list[dict] = []

    def _scrub(self, text: str) -> str:
        for value in self.secret_values:
            text = text.replace(value, REDACTED)
        return text

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        response = self.inner.handle_request(request)
        content = response.read()
        self.exchanges.append({
            "request": exchange_key(request, self.secrets),
            "response": {"status": response.status_code,
                         "headers": {h: self._scrub(response.headers[h]) for h in KEPT_HEADERS if h in response.headers},
                         "body": self._scrub(content.decode(errors="replace"))},
        })
        return httpx.Response(response.status_code, headers=response.headers, content=content, request=request)

    def take(self) -> list[dict]:
        """The exchanges recorded since the last take, for one scenario's file."""
        taken, self.exchanges = self.exchanges, []
        return taken

    @staticmethod
    def save(exchanges: list[dict], path: Path) -> None:
        path.write_text(json.dumps(exchanges, indent=1, sort_keys=True) + "\n")
```

The `exchange_key` URL omits a non-default port, which no catalog route uses; a route that
needs one adds `url.port` to the key in the same change.

Add to `src/quarry/context.py`:

```python
import sys

from quarry.http import Client


def make_client(trace: bool) -> Client:
    """A client on the process throttle. Tests monkeypatch this to inject a ReplayTransport."""
    return Client(trace=(lambda line: print(line, file=sys.stderr)) if trace else None)
```

- [ ] **Step 5: Run the tests**

Run: `just test-one tests/test_http.py`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
just test-fast
git add src/quarry/http.py src/quarry/testing.py src/quarry/context.py tests/test_http.py
git commit -m "feat(http): shared throttle, bounded retries, origin-bound credentials and recorded exchanges"
```

### Task 7: The search framework and the search and show commands

**Files:**
- Create: `src/quarry/query.py`, `src/quarry/results.py`, `src/quarry/search.py`, `src/quarry/adapters/base.py`, `tests/fake_adapter.py`, `tests/test_query.py`, `tests/test_search.py`
- Modify: `src/quarry/cli.py` (add `search`, `show`)

**Interfaces:**
- Consumes: `Catalog`, `DATA_ROLES`, `Resource`; `ids.parse`, `Curie`; `http.Client`; `context.open_env`, `make_client`; `cli.reports_errors`, `state`.
- Produces: `quarry.query`: `Query(phrases=(), filters={}, since=None, until=None, limit=None, exact=False, native=None)` (raises `ValueError` on an invalid combination), `parse_when(text: str, today: date) -> date`, `WHEN` (a click ParamType named `when`). `quarry.results`: `Result(id, resource, kind, title, date=None, summary=None, xrefs=(), publication=None, domain_fields={})` with `as_dict()`; `Coverage(resource, native, match, total, returned, complete, error=None)` with `as_dict()`. `quarry.search`: `completeness(*, total: int | None, returned: int, limit: int | None, short_page: bool) -> str`; `run(*, catalog, client, query, resource_ids, domain, allow_partial, make=adapters.base.make) -> dict`. `quarry.adapters.base`: `Adapter` protocol (`resource`, `match`, `filters`, `search(client, query) -> tuple[Coverage, list[Result]]`, `show(client, curie) -> Result`), `make(resource) -> Adapter`.

- [ ] **Step 1: Write the failing tests**

`tests/fake_adapter.py`:

```python
"""An adapter that needs no network, for framework tests."""
from quarry.errors import QuarryError
from quarry.results import Coverage, Result
from quarry.search import completeness


class Fake:
    match = "exact"
    filters = frozenset({"organism"})

    def __init__(self, resource):
        self.resource = resource

    def search(self, client, query):
        if "fail" in query.phrases:
            raise QuarryError("upstream_failed", f"{self.resource.id} is down")
        rows = [Result(id=f"geo:GSE{i}", resource=self.resource.id, kind="dataset", title=f"row {i}") for i in (1, 2, 3)]
        rows = rows[: query.limit] if query.limit else rows
        native = query.native or " OR ".join(query.phrases)
        match = "native" if query.native is not None else self.match
        return (Coverage(self.resource.id, native, match, 3, len(rows),
                         completeness(total=3, returned=len(rows), limit=query.limit, short_page=False)), rows)

    def show(self, client, curie):
        return Result(id=str(curie), resource=self.resource.id, kind="dataset", title="shown")


class Expanding(Fake):
    match = "expanded"
    filters = frozenset()


def make(resource):
    return Expanding(resource) if resource.id.startswith("expanding") else Fake(resource)
```

`tests/test_query.py`:

```python
"""The shared query: phrases OR, filters AND, --native instead of both (spec §8.2)."""
from datetime import date

import pytest

from quarry.query import Query, parse_when
from quarry.search import completeness
from quarry.errors import QuarryError


def test_valid_queries():
    Query(phrases=("myeloma", "plasmacytoma"), filters={"organism": "ncbitaxon:9606"}, limit=10)
    Query(native="cancer[Title]", limit=10)          # -n stays allowed beside --native


@pytest.mark.parametrize("kwargs, message", [
    ({}, "needs phrases or --native"),
    ({"native": "x", "phrases": ("a",)}, "--native replaces phrases"),
    ({"native": "x", "filters": {"organism": "y"}}, "--native replaces phrases"),
    ({"native": "x", "exact": True}, "--native replaces phrases"),
    ({"native": "x", "since": date(2020, 1, 1)}, "dates belong in the native query"),
    ({"phrases": ("a",), "limit": 0}, "-n must be at least 1"),
    ({"phrases": ("a",), "since": date(2021, 1, 1), "until": date(2020, 1, 1)}, "--since is after --until"),  # Review Focus 4
    ({"phrases": ("",)}, "a phrase is empty"),
])
def test_invalid_queries(kwargs, message):
    with pytest.raises(ValueError, match=message):
        Query(**kwargs)


def test_parse_when():
    today = date(2026, 10, 10)
    assert parse_when("2024-01-31", today) == date(2024, 1, 31)
    assert parse_when("10d", today) == date(2026, 9, 30)
    assert parse_when("2w", today) == date(2026, 9, 26)
    with pytest.raises(ValueError):
        parse_when("yesterday", today)


@pytest.mark.parametrize("args, expected", [
    (dict(total=3, returned=3, limit=None, short_page=False), "total"),
    (dict(total=3, returned=3, limit=5, short_page=False), "total"),
    (dict(total=9, returned=5, limit=5, short_page=False), "limited"),
    (dict(total=None, returned=5, limit=5, short_page=False), "limited"),
    (dict(total=None, returned=7, limit=None, short_page=True), "short-page"),
])
def test_completeness(args, expected):
    assert completeness(**args) == expected


@pytest.mark.parametrize("args", [
    dict(total=9, returned=7, limit=None, short_page=False),
    dict(total=9, returned=4, limit=5, short_page=False),
    dict(total=None, returned=7, limit=None, short_page=False),
])
def test_incomplete_listing_is_a_failure(args):
    with pytest.raises(QuarryError) as caught:
        completeness(**args)
    assert caught.value.kind == "incomplete_listing"
```

`tests/test_search.py`:

```python
"""search and show over fake adapters, through the CLI in-process."""
import json

import pytest
from click.testing import CliRunner

from quarry.cli import main

FAKE = """
id = "{id}"
name = "{id}"
roles = ["{role}"]
prefixes = [{prefixes}]
adapter = "tests.fake_adapter"
[[routes]]
kind = "rest"
url = "https://{id}.example"
min_interval = 0
service = "{id}"
auth = "none"
reports_total = true
"""


@pytest.fixture
def catalog(make_catalog):
    fakes = {rid: FAKE.format(id=rid, role=role, prefixes=prefixes)
             for rid, role, prefixes in (("alpha", "repository", '"geo"'), ("beta", "repository", ""),
                                         ("expanding", "repository", ""), ("onto", "ontology", '"go"'))}
    return make_catalog(fakes, ["alpha", "beta", "expanding", "onto"], ["alpha", "beta"])


def invoke(*args):
    return CliRunner().invoke(main, ["--json", *args], catch_exceptions=False)


def test_search_covers_the_domain_default_set(catalog):
    out = invoke("search", "--domain", "biology", "myeloma", "plasmacytoma")
    assert out.exit_code == 0, out.stderr
    report = json.loads(out.stdout)
    assert report["domain"] == "biology"
    assert [c["resource"] for c in report["coverage"]] == ["alpha", "beta"]
    assert report["coverage"][0] == {"resource": "alpha", "native": "myeloma OR plasmacytoma", "match": "exact",
                                     "total": 3, "returned": 3, "complete": "total"}
    assert len(report["results"]) == 6 and report["warnings"] == []


def test_limit_caps_each_resource(catalog):
    report = json.loads(invoke("search", "--domain", "biology", "-n", "2", "x").stdout)
    assert [c["complete"] for c in report["coverage"]] == ["limited", "limited"] and len(report["results"]) == 4


def test_in_overrides_the_default_set(catalog):
    report = json.loads(invoke("search", "--domain", "biology", "--in", "beta", "x").stdout)
    assert [c["resource"] for c in report["coverage"]] == ["beta"]


def test_one_failure_fails_the_command(catalog):
    out = invoke("search", "--domain", "biology", "fail")
    assert out.exit_code == 1 and out.stdout == "" and json.loads(out.stderr)["error"]["kind"] == "upstream_failed"


def test_allow_partial_records_the_failure_and_exits_zero(catalog):
    out = CliRunner().invoke(main, ["--json", "search", "--domain", "biology", "--in", "alpha", "--allow-partial", "fail"])
    report = json.loads(out.stdout)
    assert out.exit_code == 0
    assert report["coverage"][0]["complete"] == "failed" and report["coverage"][0]["error"]["kind"] == "upstream_failed"
    assert report["warnings"] == ["alpha failed: alpha is down"]


@pytest.mark.parametrize("args, kind", [
    (["--in", "expanding", "--exact", "x"], "unsupported_filter"),
    (["--in", "expanding", "--organism", "ncbitaxon:9606", "x"], "unsupported_filter"),
    (["--in", "onto", "x"], "unsupported_role"),
    (["--in", "nope", "x"], "unknown_resource"),
])
def test_refusals_happen_before_any_request(catalog, args, kind):
    out = invoke("search", "--domain", "biology", *args)
    assert out.exit_code == 1 and json.loads(out.stderr)["error"]["kind"] == kind


def test_domain_filter_outside_its_domain(catalog):
    out = invoke("search", "--domain", "core", "--in", "alpha", "--organism", "ncbitaxon:9606", "x")
    assert out.exit_code == 1 and json.loads(out.stderr)["error"]["kind"] == "unsupported_filter"


@pytest.mark.parametrize("args", [
    ["--native", "q"],                                   # no --in
    ["--in", "alpha", "--in", "beta", "--native", "q"],  # two --in
    ["--in", "alpha", "--native", "q", "x"],             # phrases beside --native
    ["--in", "alpha", "--native", "q", "--since", "2020-01-01"],
    ["--since", "2021-01-01", "--until", "2020-01-01", "x"],
    [],
])
def test_usage_errors_exit_two(catalog, args):
    assert invoke("search", "--domain", "biology", *args).exit_code == 2


def test_native_with_limit(catalog):
    report = json.loads(invoke("search", "--domain", "biology", "--in", "alpha", "--native", "q", "-n", "1").stdout)
    assert report["coverage"][0]["native"] == "q" and report["coverage"][0]["complete"] == "limited"
    assert report["coverage"][0]["match"] == "native"


def test_show_routes_by_prefix_owner(catalog):
    out = invoke("show", "GEO:GSE5")
    assert out.exit_code == 0 and json.loads(out.stdout)["id"] == "geo:GSE5"


@pytest.mark.parametrize("curie, kind", [("pubmed:1", "no_owner"), ("go:0008150", "unsupported_role"), ("GSE5", "not_a_curie")])
def test_show_refusals(catalog, curie, kind):
    out = invoke("show", curie)
    assert out.exit_code == 1 and json.loads(out.stderr)["error"]["kind"] == kind
```

- [ ] **Step 2: Run them to see them fail**

Run: `just test-one tests/test_query.py tests/test_search.py`
Expected: FAIL with `No module named 'quarry.query'`.

- [ ] **Step 3: Write query.py, results.py, search.py and adapters/base.py**

`src/quarry/query.py`:

```python
"""The shared query (spec §8.2): phrases combine with OR, filters with AND; --native replaces
both and carries its own dates, while -n stays quarry's."""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import date, timedelta

import click

RELATIVE = re.compile(r"^(\d+)([dw])$")


@dataclass(frozen=True)
class Query:
    phrases: tuple[str, ...] = ()
    filters: Mapping[str, str] = field(default_factory=dict)
    since: date | None = None
    until: date | None = None
    limit: int | None = None
    exact: bool = False
    native: str | None = None

    def __post_init__(self) -> None:
        if self.native is not None:
            if self.phrases or self.filters or self.exact:
                raise ValueError("--native replaces phrases, filters and --exact; give it alone")
            if self.since or self.until:
                raise ValueError("--since and --until are refused beside --native: dates belong in the native query")
        elif not self.phrases:
            raise ValueError("search needs phrases or --native")
        if any(not p.strip() for p in self.phrases):
            raise ValueError("a phrase is empty")
        if self.limit is not None and self.limit < 1:
            raise ValueError("-n must be at least 1")
        if self.since and self.until and self.since > self.until:
            raise ValueError("--since is after --until")


def parse_when(text: str, today: date) -> date:
    match = RELATIVE.match(text)
    if match:
        n, unit = int(match.group(1)), match.group(2)
        return today - timedelta(days=n if unit == "d" else 7 * n)
    return date.fromisoformat(text)


class When(click.ParamType):
    name = "when"

    def convert(self, value, param, ctx):
        if isinstance(value, date):
            return value
        try:
            return parse_when(value, date.today())
        except ValueError:
            self.fail(f"{value!r} is not YYYY-MM-DD, <n>d or <n>w", param, ctx)


WHEN = When()
```

`src/quarry/results.py`:

```python
"""What a search returns (spec §8.3): rows with the fields every domain shares, and one
coverage entry per resource saying what was sent and how complete the answer is."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Result:
    id: str
    resource: str
    kind: str                           # dataset | record | publication
    title: str
    date: str | None = None
    summary: str | None = None
    xrefs: tuple[str, ...] = ()
    publication: str | None = None
    domain_fields: Mapping[str, Mapping[str, str]] = field(default_factory=dict)

    def as_dict(self) -> dict:
        out = {"id": self.id, "resource": self.resource, "kind": self.kind, "title": self.title}
        for key in ("date", "summary", "publication"):
            if getattr(self, key) is not None:
                out[key] = getattr(self, key)
        out["xrefs"] = list(self.xrefs)
        out["domain_fields"] = {k: dict(v) for k, v in self.domain_fields.items()}
        return out


@dataclass(frozen=True)
class Coverage:
    resource: str
    native: str | None
    match: str                          # exact | expanded | native (sent as written, not compiled)
    total: int | None
    returned: int
    complete: str                       # total | short-page | limited | failed
    error: Mapping[str, str] | None = None

    def as_dict(self) -> dict:
        out = {"resource": self.resource, "native": self.native, "match": self.match, "total": self.total,
               "returned": self.returned, "complete": self.complete}
        if self.error is not None:
            out["error"] = dict(self.error)
        return out
```

`src/quarry/adapters/base.py`:

```python
"""The adapter contract: what search and show need from a resource's module."""
from __future__ import annotations

import importlib
from typing import Protocol

from quarry.catalog import Resource
from quarry.http import Client
from quarry.ids import Curie
from quarry.query import Query
from quarry.results import Coverage, Result


class Adapter(Protocol):
    resource: Resource
    match: str                 # "exact" or "expanded": how phrases match (spec §8.2)
    filters: frozenset[str]    # the domain filters this adapter can express

    def search(self, client: Client, query: Query) -> tuple[Coverage, list[Result]]: ...

    def show(self, client: Client, curie: Curie) -> Result: ...


def make(resource: Resource) -> Adapter:
    return importlib.import_module(resource.adapter).make(resource)
```

`src/quarry/search.py`:

```python
"""Running one search across resources (spec §8.2, §8.3). Every refusal that needs no network
happens before the first request."""
from __future__ import annotations

from quarry.adapters import base
from quarry.catalog import DATA_ROLES, Catalog
from quarry.errors import QuarryError
from quarry.http import Client
from quarry.query import Query
from quarry.results import Coverage


def completeness(*, total: int | None, returned: int, limit: int | None, short_page: bool) -> str:
    if total is not None:
        if returned == total:
            return "total"
        if limit is not None and returned == limit and total > limit:
            return "limited"
        raise QuarryError("incomplete_listing", f"the resource returned {returned} of {total} records")
    if limit is not None and returned == limit:
        return "limited"
    if short_page:
        return "short-page"
    raise QuarryError("incomplete_listing", f"the resource reports no total and paging ended without a short page "
                                            f"after {returned} records")


def run(*, catalog: Catalog, client: Client, query: Query, resource_ids: list[str], domain: str,
        allow_partial: bool, make=base.make) -> dict:
    adapters = []
    for rid in resource_ids:
        resource = catalog.resources.get(rid)
        if resource is None:
            raise QuarryError("unknown_resource", f"no resource {rid!r}")
        if not set(resource.roles) & DATA_ROLES:
            raise QuarryError("unsupported_role", f"{rid} holds no searchable records ({', '.join(resource.roles)})")
        adapter = make(resource)
        missing = set(query.filters) - adapter.filters
        if missing:
            raise QuarryError("unsupported_filter", f"{rid} cannot filter by {', '.join(sorted(missing))}")
        if query.exact and adapter.match != "exact":
            raise QuarryError("unsupported_filter", f"{rid} expands phrases and cannot match exactly; leave it out with --in")
        adapters.append(adapter)
    coverage, results, warnings = [], [], []
    for adapter in adapters:
        try:
            cov, rows = adapter.search(client, query)
        except QuarryError as error:
            if not allow_partial:
                raise
            coverage.append(Coverage(adapter.resource.id, None, adapter.match, None, 0, "failed",
                                     {"kind": error.kind, "detail": error.detail}))
            warnings.append(f"{adapter.resource.id} failed: {error.detail}")
            continue
        coverage.append(cov)
        results += rows
    return {"domain": domain, "coverage": [c.as_dict() for c in coverage],
            "results": [r.as_dict() for r in results], "warnings": warnings}
```

- [ ] **Step 4: Add `search` and `show` to cli.py**

```python
from quarry import search as search_mod
from quarry.adapters import base as adapter_base
from quarry.query import WHEN, Query


def _pretty_search(report: dict) -> str:
    lines = [f"{r['id']}\t{r.get('date', '-')}\t{r['title']}" for r in report["results"]]
    lines += [f"# {c['resource']}: {c['returned']} of {c['total'] if c['total'] is not None else '?'} ({c['complete']}, {c['match']})"
              for c in report["coverage"]]
    lines += [f"warning: {w}" for w in report["warnings"]]
    return "\n".join(lines)


@main.command("search", context_settings=CONTEXT)
@output_options
@click.argument("phrases", nargs=-1)
@click.option("--in", "in_", multiple=True, help="Search this resource; repeatable. Replaces the domain's default set.")
@click.option("--domain", help="Search this domain's default resources (also QUARRY_DOMAIN).")
@click.option("--organism", help="Biology: a taxon name or an ncbitaxon: CURIE.")
@click.option("--exact", is_flag=True, help="Require exact phrase matching from every resource searched.")
@click.option("--native", help="One resource's own query, sent unchanged; needs exactly one --in.")
@click.option("--allow-partial", is_flag=True, help="Report a failed resource in coverage instead of failing.")
@click.option("--since", type=WHEN, help="Records released on or after this date (YYYY-MM-DD, <n>d, <n>w).")
@click.option("--until", type=WHEN, help="Records released on or before this date.")
@click.option("-n", "--limit", type=int, help="At most this many records from each resource.")
@click.pass_context
@reports_errors
def search_command(ctx, phrases, in_, domain, organism, exact, native, allow_partial, since, until, limit):
    """Search records across data-holding resources."""
    if native is not None and len(in_) != 1:
        raise click.UsageError("--native needs exactly one --in", ctx)
    try:
        query = Query(phrases=tuple(phrases), filters={"organism": organism} if organism else {}, since=since,
                      until=until, limit=limit, exact=exact, native=native)
    except ValueError as error:
        raise click.UsageError(str(error), ctx) from None
    env = context.open_env()
    chosen = resolve_domain(domain, os.environ, state(ctx).config, Path.cwd(), env.catalog)
    for name in query.filters:
        if name not in env.catalog.domain_filters(chosen):
            raise QuarryError("unsupported_filter", f"--{name} is not a filter of the {chosen} domain")
    resource_ids = list(in_) or env.catalog.search_set(chosen)
    if not resource_ids:
        raise QuarryError("nothing_to_search", f"the {chosen} domain searches nothing by default; name resources with --in")
    with context.make_client(state(ctx).trace) as client:
        report = search_mod.run(catalog=env.catalog, client=client, query=query, resource_ids=resource_ids,
                                domain=chosen, allow_partial=allow_partial)
    emit(ctx, report, _pretty_search(report))


@main.command("show", context_settings=CONTEXT)
@output_options
@click.argument("curie")
@click.pass_context
@reports_errors
def show_command(ctx: click.Context, curie: str) -> None:
    """Show one record."""
    env = context.open_env()
    parsed = idmod.parse(curie, env.registry)
    owner = env.catalog.owner(parsed.prefix)
    if owner is None:
        raise QuarryError("no_owner", f"no catalog resource owns {parsed.prefix}: ids under it are cross-references only")
    if not set(owner.roles) & DATA_ROLES:
        raise QuarryError("unsupported_role", f"{owner.id} holds no records to show")
    with context.make_client(state(ctx).trace) as client:
        result = adapter_base.make(owner).show(client, parsed)
    emit(ctx, result.as_dict(), f"{result.id}\t{result.date or '-'}\t{result.title}")
```

The usage checks run before `open_env()`, so a usage error never waits on the catalog. The
`UsageError` raised inside `reports_errors` propagates past it (it is not a `QuarryError`)
to `Cli.main`, which exits 2.

- [ ] **Step 5: Run the tests**

Run: `just test-one tests/test_query.py tests/test_search.py`
Expected: all pass.

- [ ] **Step 6: Commit**

```bash
just test-fast
git add src/quarry tests
git commit -m "feat(search): shared query, coverage and the search and show commands"
```

### Task 8: ENA, the first adapter

**Files:**
- Create: `src/quarry/adapters/ena.py`, `src/quarry/catalog/resources/ena.toml`, `tests/recordings/__init__.py`, `tests/recordings/__main__.py`, `tests/recordings/ena.py`, `tests/fixtures/ena/*.json` (recorded), `tests/test_ena.py`
- Modify: `src/quarry/catalog/domains/biology.toml` (list ENA), `justfile` (add `record`)

**Interfaces:**
- Consumes: `Query`, `Result`, `Coverage`, `completeness`, `Client.request`, `Curie`, `QuarryError`, `testing.ReplayTransport`, `RecordingTransport`, `exchange`, `secret_params`, `context.make_client`.
- Produces: `quarry.adapters.ena`: `compile_query(query: Query) -> str`, class `Ena` (`match = "exact"`, `filters = frozenset({"organism"})`), `make(resource) -> Ena`. Plan 2's adapters follow this module's shape.

- [ ] **Step 1: Write the resource file and list it in biology**

`src/quarry/catalog/resources/ena.toml`:

```toml
id = "ena"
name = "European Nucleotide Archive"
roles = ["repository"]
prefixes = ["bioproject", "insdc.sra"]  # Bioregistry prefixes this resource owns (spec §7)
adapter = "quarry.adapters.ena"

[[routes]]
kind = "rest"
url = "https://www.ebi.ac.uk/ena/portal/api"
min_interval = 0.5
service = "ebi-ena"
auth = "none"
reports_total = true

[[pitfalls]]
summary = "a wildcard cannot contain '-', '.' or a space, and matches substrings (ARP1 finds PARP1)"
handling = "phrases compile to exact-equality clauses on study_title and study_description; no wildcard is generated"
evidence = "mm-159cb7: 22 of 38 cell-line terms returned 0 under wildcards"

[[pitfalls]]
summary = "the search endpoint can answer an incomplete listing during an outage"
handling = "every search also asks the count endpoint and fails when the listing is shorter"
evidence = "mm-159cb7: a re-harvest saw a short listing beside HTTP 500s"

[[pitfalls]]
summary = "the count endpoint returns HTTP 500 under load"
handling = "the client retries 5xx with backoff, then the search fails rather than report no count"
evidence = "mm-159cb7: HTTP 500 on the count endpoint during a re-harvest"
```

In `src/quarry/catalog/domains/biology.toml`: `resources = ["ena"]` and `search_default = ["ena"]`.

- [ ] **Step 2: Write the failing compile tests**

`tests/test_ena.py` (first part; Step 7 appends the replay tests):

```python
"""ENA: query compilation, recorded searches, and the listing guard (spec §8.2, §8.3)."""
import json
from datetime import date
from pathlib import Path

import pytest
from click.testing import CliRunner

from quarry import catalog as catalog_mod
from quarry import context
from quarry.adapters import ena
from quarry.cli import main
from quarry.errors import QuarryError
from quarry.http import Client
from quarry.ids import Curie
from quarry.query import Query
from quarry.testing import ReplayTransport, exchange, replay_client

FX = Path(__file__).parent / "fixtures" / "ena"
CAT = catalog_mod.load()
ENA = ena.make(CAT.resources["ena"])
BASE = "https://www.ebi.ac.uk/ena/portal/api"


def test_phrases_or_filters_and():
    q = Query(phrases=("myeloma", "plasmacytoma"), filters={"organism": "ncbitaxon:9606"},
              since=date(2024, 1, 1), until=date(2024, 3, 31))
    assert ena.compile_query(q) == (
        '(study_title="myeloma" OR study_description="myeloma" OR '
        'study_title="plasmacytoma" OR study_description="plasmacytoma") '
        'AND tax_eq(9606) AND first_public>=2024-01-01 AND first_public<=2024-03-31')


def test_hyphenated_terms_are_equality_not_wildcards():
    compiled = ena.compile_query(Query(phrases=("RPMI-8226",)))
    assert compiled == '(study_title="RPMI-8226" OR study_description="RPMI-8226")' and "*" not in compiled


def test_organism_by_name_and_native_passthrough():
    assert ena.compile_query(Query(phrases=("x",), filters={"organism": "Homo sapiens"})).endswith(
        'AND scientific_name="Homo sapiens"')
    assert ena.compile_query(Query(native='study_title="a*"')) == 'study_title="a*"'


@pytest.mark.parametrize("phrase", ['the "MM" cohort', "ARP1*"])   # Review Focus 1
def test_quotes_and_wildcards_are_refused(phrase):
    with pytest.raises(QuarryError) as caught:
        ena.compile_query(Query(phrases=(phrase,)))
    assert caught.value.kind == "unsupported_filter"
```

- [ ] **Step 3: Run them to see them fail**

Run: `just test-one tests/test_ena.py`
Expected: FAIL with `No module named 'quarry.adapters.ena'`; also `just check` now reports
`missing_adapter` for `quarry.adapters.ena`.

- [ ] **Step 4: Write the adapter**

`src/quarry/adapters/ena.py`:

```python
"""ENA portal API, result=study (spec §13). Phrases compile to exact-equality clauses: a
wildcard cannot contain '-', '.' or a space and matches substrings. Every search asks the
count endpoint too, and a listing shorter than the count fails."""
from __future__ import annotations

import json
import re

from quarry.catalog import Resource
from quarry.errors import QuarryError
from quarry.http import Client, UpstreamError
from quarry.ids import Curie
from quarry.query import Query
from quarry.results import Coverage, Result
from quarry.search import completeness

FIELDS = ("study_accession,secondary_study_accession,study_alias,study_title,study_description,"
          "tax_id,scientific_name,first_public")
GSE = re.compile(r"^GSE\d+$")
TAXON = re.compile(r"^ncbitaxon:(\d+)$", re.IGNORECASE)
SHOW_FIELD = {"bioproject": "study_accession", "insdc.sra": "secondary_study_accession"}


def _quote(text: str) -> str:
    """Shared phrases are literal. ENA reads `*` as a wildcard and cannot carry a double quote,
    and documents no escape for either, so both are refused; --native sends ENA syntax as is."""
    for char, what in (('"', "a double quote"), ("*", "`*`, ENA's wildcard")):
        if char in text:
            raise QuarryError("unsupported_filter", f"an ENA phrase cannot contain {what}: {text!r}; use --native")
    return f'"{text}"'


def compile_query(query: Query) -> str:
    if query.native is not None:
        return query.native
    terms = " OR ".join(f"study_title={q} OR study_description={q}" for q in map(_quote, query.phrases))
    clauses = [f"({terms})"]
    organism = query.filters.get("organism")
    if organism:
        taxon = TAXON.match(organism)
        clauses.append(f"tax_eq({taxon.group(1)})" if taxon else f"scientific_name={_quote(organism)}")
    if query.since:
        clauses.append(f"first_public>={query.since.isoformat()}")
    if query.until:
        clauses.append(f"first_public<={query.until.isoformat()}")
    return " AND ".join(clauses)


def _row(d: dict) -> Result:
    xrefs = [f"insdc.sra:{s}" for s in (d.get("secondary_study_accession") or "").split(";") if s]
    if GSE.match(d.get("study_alias") or ""):
        xrefs.append(f"geo:{d['study_alias']}")
    biology = {}
    if d.get("scientific_name"):
        biology["organism"] = d["scientific_name"]
    if d.get("tax_id"):
        biology["taxon"] = f"ncbitaxon:{d['tax_id']}"
    return Result(id=f"bioproject:{d['study_accession']}", resource="ena", kind="dataset",
                  title=d.get("study_title") or "", date=d.get("first_public") or None,
                  summary=d.get("study_description") or None, xrefs=tuple(xrefs),
                  domain_fields={"biology": biology} if biology else {})


def _count(text: str) -> int:
    """The count endpoint answers `count\\n<n>`."""
    words = text.split()
    if len(words) != 2 or words[0] != "count" or not words[1].isdigit():
        raise UpstreamError(f"ena count: expected 'count <n>', got {text[:80]!r}")
    return int(words[1])


def _rows(text: str) -> list[dict]:
    if not text.strip():
        return []                                      # no matches: ENA answers an empty body
    try:
        data = json.loads(text)
    except ValueError:
        raise UpstreamError(f"ena search: not JSON: {text[:80]!r}") from None
    if type(data) is not list or any(type(d) is not dict or "study_accession" not in d for d in data):
        raise UpstreamError("ena search: expected a list of studies with study_accession")
    return data


class Ena:
    match = "exact"
    filters = frozenset({"organism"})

    def __init__(self, resource: Resource):
        self.resource = resource
        self.route = resource.routes[0]

    def search(self, client: Client, query: Query) -> tuple[Coverage, list[Result]]:
        q = compile_query(query)
        total = _count(client.request(self.route, "GET", "count", params={"result": "study", "query": q}).text)
        listing = client.request(self.route, "GET", "search", params={
            "result": "study", "query": q, "fields": FIELDS, "format": "json", "limit": query.limit or 0}).text
        rows = [_row(d) for d in _rows(listing)]
        complete = completeness(total=total, returned=len(rows), limit=query.limit, short_page=False)
        match = "native" if query.native is not None else self.match
        return Coverage(self.resource.id, q, match, total, len(rows), complete), rows

    def show(self, client: Client, curie: Curie) -> Result:
        field = SHOW_FIELD[curie.prefix]
        listing = client.request(self.route, "GET", "search", params={
            "result": "study", "query": f'{field}="{curie.local}"', "fields": FIELDS, "format": "json", "limit": 2}).text
        rows = _rows(listing)
        if not rows:
            raise QuarryError("not_found", f"{curie} is not in ENA")
        return _row(rows[0])


def make(resource: Resource) -> Ena:
    return Ena(resource)
```

- [ ] **Step 5: Run the compile tests**

Run: `just test-one tests/test_ena.py`
Expected: 5 passed. `uv run quarry check` prints nothing.

- [ ] **Step 6: Record the live fixtures**

`tests/recordings/__init__.py` is empty. `tests/recordings/__main__.py`:

```python
"""Record live exchanges for one resource: `just record <resource>`. A deliberate act of a
person or agent, never part of a test run (spec §12)."""
import importlib
import os
import sys
from pathlib import Path

from quarry import catalog as catalog_mod
from quarry.adapters import base
from quarry.http import Client
from quarry.testing import RecordingTransport, secret_params


def main(resource_id: str) -> None:
    cat = catalog_mod.load()
    resource = cat.resources[resource_id]
    scenarios = importlib.import_module(f"tests.recordings.{resource_id}").SCENARIOS
    out = Path(__file__).parents[1] / "fixtures" / resource_id
    out.mkdir(parents=True, exist_ok=True)
    values = [os.environ[r.key_env] for r in resource.routes if r.key_env and os.environ.get(r.key_env)]
    recorder = RecordingTransport(secret_params(cat), values)
    adapter = base.make(resource)
    with Client(transport=recorder) as client:          # one client: one throttle across scenarios
        for name, scenario in scenarios.items():
            scenario(adapter, client)
            taken = recorder.take()
            RecordingTransport.save(taken, out / f"{name}.json")
            print(f"recorded {resource_id}/{name}: {len(taken)} exchanges", file=sys.stderr)


if __name__ == "__main__":
    main(sys.argv[1])
```

`tests/recordings/ena.py`:

```python
"""The ENA exchanges tests/test_ena.py replays."""
from datetime import date

from quarry.ids import Curie
from quarry.query import Query

MYELOMA = Query(phrases=("myeloma",), filters={"organism": "ncbitaxon:9606"},
                since=date(2024, 1, 1), until=date(2024, 3, 31))
HYPHEN = Query(phrases=("RPMI-8226",), filters={"organism": "ncbitaxon:9606"})


def show_first(adapter, client):
    _, rows = adapter.search(client, MYELOMA)
    prefix, local = rows[0].id.split(":", 1)
    adapter.show(client, Curie(prefix, local))


SCENARIOS = {
    "search-myeloma": lambda adapter, client: adapter.search(client, MYELOMA),
    "search-hyphen": lambda adapter, client: adapter.search(client, HYPHEN),
    "show-first": show_first,
}
```

Add to the justfile:

```just
# Refresh one resource's recorded exchanges against the live service.
record resource:
    {{tt}} record -- uv run python -m tests.recordings {{resource}}
```

Run: `just record ena`
Expected: three lines `recorded ena/<name>: N exchanges` (2, 2 and 3); three files under
`tests/fixtures/ena/`. Open `search-myeloma.json` and confirm it holds at least one study;
if the window returned none, widen `MYELOMA`'s dates in `tests/recordings/ena.py` and record
again. Fixtures are recorded once here and committed.

- [ ] **Step 7: Append the replay tests**

Append to `tests/test_ena.py`:

```python
from tests.recordings.ena import HYPHEN, MYELOMA


def replay(*names):
    return replay_client(ReplayTransport.from_files([FX / f"{n}.json" for n in names]))


def test_recorded_search_is_complete_and_canonical():
    with replay("search-myeloma") as client:
        cov, rows = ENA.search(client, MYELOMA)
    assert cov.complete == "total" and cov.returned == cov.total == len(rows) > 0
    assert all(r.id.startswith("bioproject:PRJ") for r in rows)
    assert all(x.split(":")[0] in {"insdc.sra", "geo"} for r in rows for x in r.xrefs)
    assert all(r.domain_fields["biology"]["taxon"] == "ncbitaxon:9606" for r in rows)


def test_recorded_hyphen_search_sends_equality():
    with replay("search-hyphen") as client:
        cov, _ = ENA.search(client, HYPHEN)
    assert 'study_title="RPMI-8226"' in cov.native and cov.complete == "total"


def test_recorded_show():
    with replay("show-first") as client:
        _, rows = ENA.search(client, MYELOMA)
        prefix, local = rows[0].id.split(":", 1)
        shown = ENA.show(client, Curie(prefix, local))
    assert shown.id == rows[0].id


def synthetic(total, listing, limit=0, query=Query(phrases=("x",))):
    q = ena.compile_query(query)
    return replay_client(ReplayTransport([
        exchange("GET", f"{BASE}/count", {"result": "study", "query": q}, body=f"count\n{total}\n",
                 content_type="text/plain"),
        exchange("GET", f"{BASE}/search", {"result": "study", "query": q, "fields": ena.FIELDS, "format": "json",
                                           "limit": limit}, body=listing),
    ]))


STUDY = {"study_accession": "PRJNA1", "secondary_study_accession": "SRP1;SRP2", "study_alias": "GSE7",
         "study_title": "t", "study_description": "d", "tax_id": "9606", "scientific_name": "Homo sapiens",
         "first_public": "2024-02-01"}


def test_a_short_listing_fails():
    with synthetic(5, json.dumps([STUDY] * 3)) as client, pytest.raises(QuarryError) as caught:
        ENA.search(client, Query(phrases=("x",)))
    assert caught.value.kind == "incomplete_listing"


def test_no_matches_is_an_empty_complete_answer():             # Review Focus 2
    with synthetic(0, "") as client:
        cov, rows = ENA.search(client, Query(phrases=("x",)))
    assert (rows, cov.complete, cov.total) == ([], "total", 0)


@pytest.mark.parametrize("count, listing", [
    ("<html>busy</html>", "[]"),
    ("count\n2\n", "<html>busy</html>"),
    ("count\n1\n", '{"error": "x"}'),
])
def test_malformed_answers_are_upstream_errors(count, listing):
    q = ena.compile_query(Query(phrases=("x",)))
    transport = ReplayTransport([
        exchange("GET", f"{BASE}/count", {"result": "study", "query": q}, body=count, content_type="text/html"),
        exchange("GET", f"{BASE}/search", {"result": "study", "query": q, "fields": ena.FIELDS, "format": "json",
                                           "limit": 0}, body=listing, content_type="text/html"),
    ])
    with replay_client(transport) as client, pytest.raises(QuarryError) as caught:
        ENA.search(client, Query(phrases=("x",)))
    assert caught.value.kind == "upstream_failed"


def test_native_coverage_says_native():
    query = Query(native='study_title="ARP1*"')
    with synthetic(1, json.dumps([STUDY]), query=query) as client:
        cov, _ = ENA.search(client, query)
    assert cov.match == "native" and cov.native == 'study_title="ARP1*"'


def test_limit_reports_limited():
    query = Query(phrases=("x",), limit=2)
    with synthetic(10, json.dumps([STUDY] * 2), limit=2, query=query) as client:
        cov, rows = ENA.search(client, query)
    assert cov.complete == "limited" and len(rows) == 2


def test_row_cross_references():
    with synthetic(1, json.dumps([STUDY])) as client:
        _, rows = ENA.search(client, Query(phrases=("x",)))
    assert rows[0].xrefs == ("insdc.sra:SRP1", "insdc.sra:SRP2", "geo:GSE7")


def test_cli_search_through_replay(monkeypatch):
    monkeypatch.setattr(context, "make_client", lambda trace: replay("search-myeloma"))
    out = CliRunner().invoke(main, ["--json", "search", "--domain", "biology", "--organism", "ncbitaxon:9606",
                                    "--since", "2024-01-01", "--until", "2024-03-31", "myeloma"],
                             catch_exceptions=False)
    report = json.loads(out.stdout)
    assert out.exit_code == 0 and report["coverage"][0]["resource"] == "ena"
    assert report["coverage"][0]["complete"] == "total"
```

- [ ] **Step 8: Run the tests**

Run: `just test-one tests/test_ena.py`
Expected: all pass.

- [ ] **Step 9: Commit**

```bash
just check && just test-fast
git add src/quarry tests justfile
git commit -m "feat(ena): the first adapter, with recorded exchanges and the listing guard"
```

### Task 9: Conformance with the CLI table

**Files:**
- Create: `tools/cli.toml`, `tools/cli_surface.py` (by `vendored adopt`), `tests/test_cli_surface.py`
- Modify: `AGENTS.md` (Layout and Rules), `README.md` (Usage)

**Interfaces:**
- Consumes: Task 2's `[cli.quarry]` rows on ops main; every command from Tasks 5 and 7.

- [ ] **Step 1: Adopt the table**

```bash
(cd "$TREE/ops" && python3 bin/vendored adopt --into "$WT" cli.toml cli_surface.py)
```

Expected: `tools/cli.toml` holds `[cli.quarry]`.

- [ ] **Step 2: Write the conformance test**

`tests/test_cli_surface.py`:

```python
"""quarry's click surface equals its rows in tools/cli.toml, and the binary follows the CLI
vocabulary's output and exit rules."""
import importlib.util
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest
from click.testing import CliRunner

from quarry import context
from quarry.cli import main
from quarry.testing import ReplayTransport, replay_client

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("cli_surface", ROOT / "tools" / "cli_surface.py")
cli_surface = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli_surface)
TABLE = ROOT / "tools" / "cli.toml"
COMMANDS = sorted(row[1] for row in cli_surface.table_rows(TABLE, "quarry") if row[0] == "command")


def run(*args, env=None, cwd=None):
    environ = {k: v for k, v in os.environ.items() if not k.startswith("QUARRY_")}
    return subprocess.run([sys.executable, "-m", "quarry.cli", *args], capture_output=True, text=True,
                          env={**environ, **(env or {})}, cwd=cwd)


def test_surface_equals_table():
    assert cli_surface.diff(cli_surface.click_rows(main), cli_surface.table_rows(TABLE, "quarry")) == []


@pytest.mark.parametrize("path", [()] + COMMANDS, ids=lambda p: " ".join(p) or "root")
def test_help_on_every_command(path, tmp_path):
    for flag in ("--help", "-h"):
        out = run(*path, flag, cwd=tmp_path)
        assert (out.returncode, out.stderr) == (0, "") and out.stdout, (path, flag)
    if path:
        assert run("help", *path, cwd=tmp_path).stdout == run(*path, "--help", cwd=tmp_path).stdout


@pytest.mark.parametrize("args", [["bogus"], ["resources", "list", "--bogus"], ["resources", "list", "--role", "warehouse"],
                                  ["show"], ["help", "bogus"]])
def test_usage_errors_exit_two(args, tmp_path):
    out = run(*args, cwd=tmp_path)
    assert out.returncode == 2 and out.stdout == "" and 0 < len(out.stderr.strip().splitlines()) <= 2


def test_json_failure_object_and_format_precedence(tmp_path):
    for args in (["--json", "resources", "show", "nope"], ["resources", "show", "nope", "--json"]):
        out = run(*args)
        assert out.returncode == 1 and out.stdout == ""
        error = json.loads(out.stderr)["error"]
        assert isinstance(error["kind"], str) and isinstance(error["detail"], str)
    assert run("--json", "resources", "show", "nope", "--pretty").returncode == 2
    assert run("resources", "show", "nope").stderr.startswith("quarry: ")
    assert json.loads(run("resources", "show", "nope", env={"QUARRY_FORMAT": "json"}).stderr)["error"]
    assert run("--pretty", "resources", "show", "nope", env={"QUARRY_FORMAT": "json"}).stderr.startswith("quarry: ")


def _leaf_rows():
    commands = tomllib.loads(TABLE.read_text())["cli"]["quarry"]["commands"]
    paths = [tuple(c["path"]) for c in commands]
    return sorted(tuple(c["path"]) for c in commands
                  if c["path"] and not any(p[: len(c["path"])] == tuple(c["path"]) and len(p) > len(c["path"]) for p in paths)
                  and "output" not in c)


def test_json_is_honoured_by_every_leaf_command(monkeypatch):
    fx = ROOT / "tests" / "fixtures" / "ena"
    monkeypatch.setattr(context, "make_client", lambda trace: replay_client(
        ReplayTransport.from_files([fx / "search-myeloma.json", fx / "show-first.json"])))
    first = json.loads((fx / "show-first.json").read_text())[-1]["request"]["query"]
    shown = next(v for k, v in first if k == "query").split('"')[1]
    invocations = {
        ("domains", "list"): ["domains", "list"],
        ("resources", "list"): ["resources", "list", "--domain", "biology"],
        ("resources", "show"): ["resources", "show", "ena"],
        ("id", "check"): ["id", "check", "geo:GSE1"],
        ("id", "normalize"): ["id", "normalize", "PRJNA123456"],   # owned by ENA (bioproject)
        ("id", "resolve"): ["id", "resolve", "geo:GSE24080"],
        ("check",): ["check"],
        ("search",): ["search", "--domain", "biology", "--organism", "ncbitaxon:9606", "--since", "2024-01-01",
                      "--until", "2024-03-31", "myeloma"],
        ("show",): ["show", f"bioproject:{shown}"],
    }
    assert sorted(invocations) == _leaf_rows(), "every leaf row needs an invocation"
    for path, args in invocations.items():
        result = CliRunner().invoke(main, ["--json", *args], catch_exceptions=False)
        assert result.exit_code == 0, (path, result.stderr)
        if path[-1] == "check":
            assert result.stdout == "", "a clean check is silent in either mode"
            continue
        assert isinstance(json.loads(result.stdout), dict), (path, result.stdout)
```

- [ ] **Step 3: Run it**

Run: `just test-one tests/test_cli_surface.py`
Expected: all pass. A `test_surface_equals_table` failure prints the rows missing from
either side: fix the code to match the table (the table is the authority), or, when the
table is wrong, fix it in ops first (a worktree, a commit, a merge, as Task 2) and rerun
Step 1.

- [ ] **Step 4: Document and gate**

In `AGENTS.md` Layout, add: `src/quarry/catalog/` (resources, domains, the Bioregistry
snapshot); `src/quarry/adapters/` (one module per resource); `tests/recordings/` (what
`just record` captures). In Rules, add: "A new command or option is a row in ops `cli.toml`
first, then `vendored adopt cli.toml`; the conformance test fails on any difference." In
`README.md` Usage, show three commands: `quarry resources list --domain biology`,
`quarry search --domain biology --organism ncbitaxon:9606 myeloma`, `quarry show bioproject:<id>`.

```bash
just docs && just gate
```

Expected: `just gate` (check, then the full suite) exits 0.

- [ ] **Step 5: Commit**

```bash
git add tools tests/test_cli_surface.py AGENTS.md README.md
git commit -m "test(cli): conform to the shared CLI table"
```

- [ ] **Step 6: Finish the branch**

Use superpowers:finishing-a-development-branch. quarry is a personal-profile repository, so
the local merge of `foundation` into `main` is the default; a GitHub remote and its first
push are outside this plan and need the user.
