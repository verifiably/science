---
id: sci-f8a0cf
title: "Task 10: `publish` and `publish-preview` — the retired-corpus guard and the ambiguous-attribution detail"
status: done
priority: 1
size: s
complexity: mid
process: direct
owner: commons-1b
created: 2026-10-29T01:50:51Z
updated: 2026-10-29T05:19:13Z
started: 2026-10-29T05:02:54Z
completed: 2026-10-29T05:19:13Z
closed: 2026-10-29T05:19:13Z
depends: []
parent: sci-9104fb
tags: [commons]
agent: claude-code/claude-fable-5-1
origin: agent
plan: docs/plans/2026-10-28-science-commons-1b.md
step: "Task 10: `publish` and `publish-preview` — the retired-corpus guard and the ambiguous-attribution detail"
---

## Notes

- 2026-10-29T01:50:51Z (add): created
  provenance: {"harness_session":"claude-code:f666f956-1928-4c06-8bf1-80cd5a586d90","harness_session_source":"CLAUDE_CODE_SESSION_ID","origin":"agent"}
- 2026-10-29T05:02:54Z (commons-1b): started
  provenance: {"harness_session":"codex:01a18609-985e-78b1-87f9-3fb87a45222b","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-29T05:18:27Z (commons-1b): Implemented Task 10 in 1773f7bfb3093689108acda178e73bf2181c1748. Shared explicit nonlive-session guard covers publish, resume and preview; shared ambiguity detail preserves kernel claims and walks exact held corpus/marker ancestry. Focused: 31 passed, 2 strict xfails (68.34s); fast: 118 passed, 2 strict xfails (408.25s), using recorded one-worker testmon workaround. Remaining xfails require Task 11 late_link fixture; report task-10-report.md documents its exact shape. Existing resume and unread-mount tests were narrowed to their actual behavior boundaries, controller accepted. No formal self-review; controller owns fresh review.
- 2026-10-29T05:18:44Z (commons-1b): retained: {"host":"titan","state":"kept","verification":"verified","next_owner":"task:sci-9104fb","cleanup_trigger":"After independent review and planned integration, inspect evidence and run the required worktree removal checks","kind":"worktree","path":".worktrees/commons-1b","purpose":"Locked commons-1b branch at Task 10 commit 1773f7b; controller owns fresh review and later plan execution/integration"}
- 2026-10-29T05:18:46Z (commons-1b): retained: {"host":"titan","state":"kept","verification":"verified","next_owner":"task:sci-9104fb","cleanup_trigger":"After independent review and planned integration, inspect evidence and run the required worktree removal checks","kind":"evidence","path":".worktrees/commons-1b/.superpowers/sdd/2026-10-28-science-commons-1b/task-10-commit.log","purpose":"Task 10 implementation report or RED/GREEN/fast/commit evidence for independent review","sha256":"75efdfe77e1c53622e19646a2bc16affb3ecc3a66ab117b2788915181582eec3"}
- 2026-10-29T05:18:47Z (commons-1b): retained: {"host":"titan","state":"kept","verification":"verified","next_owner":"task:sci-9104fb","cleanup_trigger":"After independent review and planned integration, inspect evidence and run the required worktree removal checks","kind":"evidence","path":".worktrees/commons-1b/.superpowers/sdd/2026-10-28-science-commons-1b/task-10-corrected-red.log","purpose":"Task 10 implementation report or RED/GREEN/fast/commit evidence for independent review","sha256":"ea94f0454049fc46d710af58e7737d70f28679c5abf7e82e15cf673ffce906a1"}
- 2026-10-29T05:18:48Z (commons-1b): retained: {"host":"titan","state":"kept","verification":"verified","next_owner":"task:sci-9104fb","cleanup_trigger":"After independent review and planned integration, inspect evidence and run the required worktree removal checks","kind":"evidence","path":".worktrees/commons-1b/.superpowers/sdd/2026-10-28-science-commons-1b/task-10-fast.log","purpose":"Task 10 implementation report or RED/GREEN/fast/commit evidence for independent review","sha256":"ff1f4d70f3056dc4efc15562c8ad65ceaf6c569ba170ff72401f11dd97bc87c8"}
- 2026-10-29T05:18:50Z (commons-1b): retained: {"host":"titan","state":"kept","verification":"verified","next_owner":"task:sci-9104fb","cleanup_trigger":"After independent review and planned integration, inspect evidence and run the required worktree removal checks","kind":"evidence","path":".worktrees/commons-1b/.superpowers/sdd/2026-10-28-science-commons-1b/task-10-focused.log","purpose":"Task 10 implementation report or RED/GREEN/fast/commit evidence for independent review","sha256":"7b313ae9bc5a93cddf931e26cd0288f8a4a7af3b0f42a070806de8e6925eb768"}
- 2026-10-29T05:18:51Z (commons-1b): retained: {"host":"titan","state":"kept","verification":"verified","next_owner":"task:sci-9104fb","cleanup_trigger":"After independent review and planned integration, inspect evidence and run the required worktree removal checks","kind":"evidence","path":".worktrees/commons-1b/.superpowers/sdd/2026-10-28-science-commons-1b/task-10-green.log","purpose":"Task 10 implementation report or RED/GREEN/fast/commit evidence for independent review","sha256":"0627bbf9c5760a6e8c7afd1e8f28516035233ad94e2151b973e737991b2ec489"}
- 2026-10-29T05:18:52Z (commons-1b): retained: {"host":"titan","state":"kept","verification":"verified","next_owner":"task:sci-9104fb","cleanup_trigger":"After independent review and planned integration, inspect evidence and run the required worktree removal checks","kind":"evidence","path":".worktrees/commons-1b/.superpowers/sdd/2026-10-28-science-commons-1b/task-10-red.log","purpose":"Task 10 implementation report or RED/GREEN/fast/commit evidence for independent review","sha256":"428d6b86e7de19fe6842542c4b2c7945605ace6d2f49f095052e57c373822b5d"}
- 2026-10-29T05:18:54Z (commons-1b): retained: {"host":"titan","state":"kept","verification":"verified","next_owner":"task:sci-9104fb","cleanup_trigger":"After independent review and planned integration, inspect evidence and run the required worktree removal checks","kind":"evidence","path":".worktrees/commons-1b/.superpowers/sdd/2026-10-28-science-commons-1b/task-10-report.md","purpose":"Task 10 implementation report or RED/GREEN/fast/commit evidence for independent review","sha256":"d596655d2d48de58241ed057c1720cd915189feaf7a3bdb0a242f05765df50df"}
- 2026-10-29T05:19:13Z (commons-1b): done
  provenance: {"harness_session":"codex:01a18609-985e-78b1-87f9-3fb87a45222b","harness_session_source":"CODEX_THREAD_ID"}
- 2026-10-29T05:19:13Z (commons-1b): Implemented in 1773f7b: shared nonlive-session guard and exact-pair ambiguous-attribution remedies on publish/preview, including resume. Focused 31 passed/2 strict xfails; required fast 118 passed/2 strict xfails. Task 11 owns the late_link fixture gates; controller owns fresh review and retained worktree/evidence under sci-9104fb. No push, merge, host change or surviving session process.
  provenance: {"harness_session":"codex:01a18609-985e-78b1-87f9-3fb87a45222b","harness_session_source":"CODEX_THREAD_ID"}
