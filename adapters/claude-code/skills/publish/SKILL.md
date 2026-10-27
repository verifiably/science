---
name: "publish"
description: "Publish a project's view to a local directory or a git remote, or resume a stranded attempt."
---

You are working over one world of governed records through the `science`
commands. The current project is chosen with `project-select`. A command
that enumerates the world reads through the selected project's query, and
sees the whole world when none is selected; a command given an identity
answers for that identity whatever is selected. A question or any
coordination record needs a selected project, except a project itself; a
fact does not. Corpus writes are kernel acts that return their own records;
session writes return the selection they recorded. Report refusals verbatim,
and never retry with altered inputs, repair, or write around one. Results are
budgeted: a truncated result ends with a cursor, and continuing with that
cursor is the only way to see the rest. A command's declared inputs are its
whole interface; there is nothing to reach around.

Run `publish` to share a project's view: `target` names the project (its
name, or its `coord:<project>` address when two share a name) and `to` the
destination, an absolute directory on this host or an `https://` git remote.
The kernel freezes the records the view selects at the current epoch into a
new publication corpus, reveals it at the destination, and binds it in this
world. A new attempt declares configured markerless roots as the installation's
own, including restored replicas; sharing-registry roots and roots holding a
publication marker remain carried inputs. Ownership classification reads every
configured mount, refuses duplicate claimed carriers, and requires exactly one
write mount; errors reading these inputs propagate. Run `publish-preview` first
to see what would be frozen. The output
is the records the act wrote: the `[publication-binding]`, naming the
corpus, its marker and its head artifact, and the kernel's `[act-report]`. A
world with no current epoch, or one written to since it (an earlier
publish's binding included), refuses naming `science epoch`; run it first. A
`transport-fault` refusal leaves the attempt unfinished, and a new publish
to the same remote then refuses `publish-unfinished` naming its token: run
`publish` again with the same `target` and `to` and that token as `resume`,
which continues the attempt from where it stopped using its frozen selection
and attributions, without recomputing ownership. The kernel resumes an
attempt only under the session that began it, so `resume` works within the
service session that made the attempt; a later session finds the pair
blocked `publish-unfinished`.
