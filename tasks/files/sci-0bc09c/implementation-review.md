What this change does: Corrects the selected-next regression test to distinguish conflicting copies from identical copies. The change stays within sci-0bc09c and changes only tests.

Reviewed the working diff against HEAD 303feaa5d81f02c554f597bdf8a4873f35e92cdd.

- Critical: none.
- Important: none.
- Minor: none.

The tests exercise the intended cases. `_twice` preserves the record’s address and uid; changing its title changes `registry.content_identity`. The fixture holds `proposition:archived`, so the unrelated query is valid. Kernel live evaluation builds the address map before evaluating that query. The refusal test also verifies the conflicting address and both corpus identities; the success test verifies the exact selected row. All three helper callers retain their intended behavior.

Declined to judge: selecting or citing the duplicated address itself, and broader holder-set acceptance. Those behaviors belong to sci-73c80e; this change neither implements nor claims them.

Ready to merge: Yes, once the controller’s focused and fast checks pass. `git diff --check` passed. Reviewer identity: codex/gpt-6.1-sol.

Not checked: I ran no tests, as instructed; test results remain the controller’s responsibility. No files changed or processes left running.
