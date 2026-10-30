Reviewer: claude-code/claude-opus-5-5
Source: full review relayed by the user in this session
Artifact: docs/specs/2026-10-30-readable-stores-design.md
Revision: 915409e42b540287e3fce9f062a097cca1bda100

Full returned review:

I'd revise this spec before planning. One finding matters: read stores are accepted on genesis identity alone, so a store copied but never admitted can serve unverified bytes as inherited holdings. The rest are clarifications. The task stays parked waiting on you. If you agree, the session that owns sci-300dab revises the spec as a new frozen revision for the next round. I changed nothing.

**What I reviewed:** commit 915409e, `docs/specs/2026-10-30-readable-stores-design.md` in `.worktrees/sci-300dab-stores` (sha256 `6ec91aeb…ff96`). I checked its claims against the science worktree and against beliefs at 405f249 and atoms on disk.

**Claims that hold up**
- Only one store is bound today. `session.py:26` passes only `config.store_root`, and `held_path_for` matches only that store's id. `dataset` and `fetch` build their locations from `writer.store_id`.
- `store_identity` matches the spec's description. It returns `None` for a missing or malformed chain and raises `CorpusRootRefused` for a genesis that isn't a store's. The "translate at this boundary" contract covers both.
- The runbook recipe is valid. `lifecycle` is a real act family that commands can't reach, `"operator"` is an acceptable actor, and `init_store_root` refuses a copied genesis as the spec says.
- Run staging (`boundary._stage_inputs`) accepts any file path, so inherited inputs from a read store can reach `run` and `verify` without kernel changes.
- Option 1 (add `read_store_roots`, keep `store_root`) is the right choice. It is purely additive and adds no compatibility layer.

**Important**

1. **Read stores are never checked for read admission.** A read store is accepted once its genesis names an identity. The spec says this on purpose ("not a new claim of lifecycle serviceability"), but restored replicas are the reason the role exists, and atoms makes read admission the boundary for them.
   - **Failure case:** someone `rsync`s the old store instead of running `restore_root`, or a restore is interrupted. `store_identity` still reads the copied genesis, and science serves those bytes as inherited holdings.
   - **Where it bites:** vocabulary reads recheck the digest, but run staging only records the staged file's digest (`boundary.py:483`); I found no comparison to the declared digest. A run would then record evidence from bytes that aren't the declared dataset.
   - **Fix:** a non-mutating check is already available. atoms' `read_lifecycle_state` "never creates or upgrades a root, metadata directory, lock…", so calling it doesn't break the spec's no-recovery rule. Have the identity helper refuse any read store whose state, from `beliefs.root.read_lifecycle_state`, is not `WRITABLE` or `READ_ONLY_SERVICEABLE`. `WRITABLE` has to be allowed so a previous write store can become a read store after a later relocation.
   - **Cost of skipping it:** silent wrong-input runs from unadmitted copies.
   - **Out of scope here:** whether run should also compare staged digests to the declaration. If that matters, it belongs in its own task.

**Minor**

2. **Pin down what `vocabulary.snapshot` does with an unresolvable observation.** Today `held_path_for` raises inside `snapshot`, so every `evaluate` and `gather_inputs` read refuses (`config.py:654–673`). Its docstring, though, says a dataset that isn't held is listed unreadable. With several stores this case is more likely: a forgotten read store, or mounted corpora whose observations name a foreign store. The spec should choose refuse or unreadable for snapshot specifically, and the acceptance list should test it. At the moment the tests cover only `held_path`.
3. **"Reducer order" is lexicographic.** `dataset_observations` sorts by (digest, location), so when a dataset is held in both stores, the read comes from whichever store id sorts first, not from the write store. That is fine, but the spec should say so, so nobody expects the write store to win. It also means a corrupt inherited copy can be chosen over a good fresh one, with no fallback. That follows from the spec's "no retry after an I/O error" and should be stated.
4. **A blocked location blocks the whole dataset.** If any location is blocked for the declared digest, `dataset_observations` returns `DatasetBlocked` for the entire address. So a fresh store cannot route around a blocked holding of the same bytes. The spec's "adding a store grants no repair" covers this, but the runbook should say it outright, since it bears on whether this route alone unblocks mm-62e2da. I didn't check whether the failed key holding actually shows up as blocked; that sits with sci-409235.
5. **The runbook's paths are inconsistent.** It says "fresh sibling path", but the example `stores/working` is not a sibling of `store`. Per `metadata_root_for`, the new metadata lands at `stores/working.metadata`. Naming that rule turns "outside the old store and its metadata tree" into a concrete check.
6. **The "helpers that serialize `ScienceConfig`" are all test helpers.** No production serializer exists; the only writers are `tests/helpers/world.py`, `tests/helpers/commons.py` and `write_config` in `test_config.py`. The spec should say so, so the plan doesn't go looking for a production one.

**Review note for the controller to record (I wrote no note):** `review: spec round 2 — verdict: revise; findings: Important 1, Minor 5; reviewer: claude-code/claude-opus-5-5`. Round 1 was codex's acceptance, already recorded.
