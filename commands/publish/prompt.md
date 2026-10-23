Run `publish` to share a project's view: `target` names the project (its
name, or its `coord:<project>` address when two share a name) and `to` the
destination, an absolute directory on this host or an `https://` git remote.
The kernel freezes the records the view selects at the current epoch into a
new publication corpus, reveals it at the destination, and binds it in this
world. Run `publish-preview` first to see what would be frozen. The output
is the records the act wrote: the `[publication-binding]`, naming the
corpus, its marker and its head artifact, and the kernel's `[act-report]`. A
world with no current epoch, or one written to since it (an earlier
publish's binding included), refuses naming `science epoch`; run it first. A
`transport-fault` refusal leaves the attempt unfinished, and a new publish
to the same remote then refuses `publish-unfinished` naming its token: run
`publish` again with the same `target` and `to` and that token as `resume`,
which continues the attempt from where it stopped. The kernel resumes an
attempt only under the session that began it, so `resume` works within the
service session that made the attempt; a later session finds the pair
blocked `publish-unfinished`.
