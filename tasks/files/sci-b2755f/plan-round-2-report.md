Review of the implementation plan at science commit 1ecfa34, .worktrees/sci-b2755f/docs/plans/2026-10-30-assumption-sweep.md, with the clarified spec at the same revision, for task sci-b2755f. Read from git, not the working file.

Verdict: accept, with two minors the executing agent can fold into Task 1 Setup without another review round. The plan covers every spec section, its three steps are independently reviewable, its code references resolve, and the step tasks are correctly linked. The navigation ruling in the spec is applied as stated. Next actor is you: approve the plan, after which the parked agent unblocks sci-7b3829 and starts inline execution in the retained worktree. I changed nothing, wrote no note and ran no tests.

Verified against the code:
- The Task 1 test snippet uses names that exist in the science loader and the existing adapter tests, and the adapter builder's signature matches the call.
- The science adapters build command exists and defaults its output to the package's own checkout, so running it from the worktree writes the worktree's adapter tree.
- No test policy file is present, so the plan's choice of the full suite as the deferred baseline is the correct route under the Tests rule.
- The quarry PubMed adapter reads ESummary fields only, with no abstract, as the plan says.
- The three children carry the plan link and step headings that match the plan's ### Task N: lines, with the dependency chain 1 to 2 to 3, and tasks check is clean. sci-7b3829 is blocked on your plan approval, not on a dependency.
- The five-sample control and guided runs in Task 1 match the writing-skills skill's own "5+ reps per variant" guidance, so that cost is the skill's, not the plan's invention.

Minor 1: name the quarry invocation route. Task 3 says to resolve the installed quarry executable, but no quarry is on this host's PATH. It exists only as the quarry checkout's own environment, run with uv run quarry from that checkout. The plan should say that route so the pilot does not stall at Setup or pick up a stray install. Record the quarry revision used alongside it.

Minor 2: align full-text slot accounting with the spec. The plan counts every deliberate full-text attempt toward the cap of 18, including failed access. The spec says an inaccessible full text is "never a completed full-text read", which reads as not consuming a slot. Either reading is defensible. Pick one and state it in both documents, since it changes how many sources the pilot can actually read.

One thing to approve knowingly. Task 3 Step 5 has the final child close the parent, merge the branch locally and remove the worktree. That is allowed under this personal checkout, but it means a single step owns integration and cleanup, with the retained-item and host-pointer checks as its only brakes.

Reviewer identity for the note writer: claude-code/claude-fable-5-1, plan round 2. Limits: read-only plan review; no tests, builds or retrieval probes ran.

Keith: approved after the noting or fixing the minors. After marking the plan approved, let's park it so that inline execution can begin in a fresh session.
