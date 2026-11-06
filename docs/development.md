# Developing science

Type: guide; document types 1. For maintainers adding commands, changing transports
or working with certified-world fixtures. [Commands](commands.md) is declaration
and handler authority; [sessions](sessions.md) is invocation authority. The
[configuration](configuration.md) and [sharing](sharing.md) contracts explain state.

## Set up and add a command

Use sibling atoms, nodes and beliefs source checkouts and the README's frozen
install. Install hooks with `git config core.hooksPath .githooks`; keep worktree
editable dependency paths resolving to the intended sibling revisions. Never
substitute an unrelated environment to make a failing setup appear hydrated.

1. Add the parser-surface row to `tools/cli.toml` through its producer ownership
   route, then adopt the reviewed source as [tools](../tools/README.md) describes.
   The conformance test compares the actual parser with this inventory.
2. Add `commands/<name>/command.toml` and `prompt.md`, then its handler module.
   Choose the smallest existing kernel requirement that covers its effects.
   Science does not construct full permits or write scientific files directly.
3. Validate inputs before acting. Refuse with structured code/message/data.
   Preserve committed evidence when a later act fails. Use canonical record blocks
   derived from stored records; the dispatcher audits and rebuilds write reports.
4. Add focused behavior tests using the production dispatcher/declarations where
   appropriate. A fake seam should expose the refusal/order being tested, not
   replace the behavior whose result the test asserts.
5. From `python/`, run `uv run science build`, then
   `uv run science adapters build --out <owned-output-directory>`. Adapter generation
   consumes authored command prompts and skills; generated files are never the
   authority. Regenerate committed adapters only when authored changes require it.

Kernel operator-time setup and scientific command-time authority are distinct.
Test bootstraps may initialize/admit worlds and install rules using explicit
fixture authority; production commands obtain scoped authority from their session.
Read mounts use their own pinned profiles. Mutation stays in the write root;
equal copies may resolve but differing content must refuse.

## Tests and mandatory checks

Run every test through the just front door; never invoke pytest directly.
Paths below are relative to `python/`:

```sh
just test-one tests/test_cmd_show.py
just test-one tests/test_cmd_fetch.py::test_fetch_under_records_only_refuses_naming_the_policy
just check-hygiene
```

`test-one` is the protected focused route. `check-hygiene` always runs ops-check,
ops-docs and tasks checks; the task tooling intentionally needs the maintainer's
registry/records. That requirement is separate from application install/build/use,
which needs no private records. `just docs` regenerates root identity/family regions.
No formatter, linter or typechecker is configured here.

The root `.tt.toml`, validated by `tools/tt`, controls broad execution. Absent means
enabled; invalid means error. With `automatic_broad = false`, ordinary `test`,
`test-fast` and `ci-python` record a policy-disabled skip; it is not a passing suite.
Always run fresh focused checks for changed behavior and hygiene. A deliberate
broad run is `TT_FORCE=1 just test` or `just test-full`.

Every branch touching Python requires `TT_FORCE=1 just test-fast` on a certified
host before merge. Shared fixtures/helpers, session/dispatch/store lifecycle or
locked sibling dependency changes additionally require `just test-full`; the exact
paths and hook/CI routing are listed in [AGENTS.md](../AGENTS.md#gates).
Hosted CI runs forced Python checks but converts only named certified-tuple or
confinement unavailability to skips; it proves the portable surface only. Record
real passes, failures and skips separately. A local correctness failure needs
resolution; uncertified mode is not a way to relabel it green.

## Certified fixtures and snapshot lineages

Tests use certified volume storage, not tmpfs. By default conftest resolves the
main checkout through Git's common directory and uses its ignored `.framework-test`
root, even from a worktree; `SCIENCE_TEST_ROOT` can name another certified root.
Each fixture directory is disposable and owned. Close launchers, sessions, sockets
and threads before it is restored or removed.

`helpers.snapshot.Root(name, build)` declares an independent world.
`Derived(name, base, step)` derives one by restoring its base image and applying
one step in the root's directory. `materialize(work_base, declaration)` lazily
builds each ancestor once per worker. Existing call sites also use
`snapshot(work_base, name, builder)`; repeated names require the same builder.
Declaration identity, not an equal-looking dataclass value, identifies a world.

Worlds contain absolute paths in engine metadata and run records. Restore into the
same directory, never relocate a snapshot or share it between workers. Image
construction, a step's internal `restore_tree`, and a test's live `restore()` are
different operations: only the last records a live world. One lineage may have
only one live declaration per test. Requesting or restoring another refuses
before altering its files or lazily building new images. Conftest clears live
tracking between tests; it does not silently allow mid-test replacement.

Snapshot values contain only data: `ScienceConfig`, `Path`, strings, integers,
booleans, None, and plain tuple/list/dict containers. Namedtuples and live readers,
sessions, dispatchers, contexts or sockets are not supported values. `copy_value`
rebuilds containers while sharing trusted leaves, preventing a descendant step
from mutating an ancestor's cached containers. Reopen readers after restore;
restoring evicts beliefs' process registries but cannot rewrite a reader already
held by a test. Live sockets under the world (including its short service socket)
block restore explicitly.

Shared lazy ancestors reduce repeated construction but reduce testmon's coverage
precision: the first test pays for a step, later descendants may not be recorded
as dependent on its production code. Use focused affected integration modules and
the mandated forced final checks for shared changes. Do not assume a small fast
selection covers a changed lineage. The snapshot/helper tests cover cold deep
construction, dirty-base isolation, data copy, declaration collisions and both
halves of the live-world refusal.
