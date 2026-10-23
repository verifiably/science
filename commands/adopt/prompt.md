Run `adopt` to hold another world's publication: `location` is the
`https://` git remote it was published to and `corpus_id` the publication
there. It fetches the corpus, verifies its chain against the head artifact
published beside it, and sources it: the location must be bound, with
`provider-bind`, to the world the publication's marker claims. Unbound, it
refuses `pin-unsourced` naming that world and the remedies, `provider-bind`
or `follow`; bound to another world, `world-mismatch`. Either way the copy
is deleted and nothing is recorded. A copy that shares an address with a
corpus this world already holds refuses `adopt-conflict` with the shared
addresses, and stays `fetched`. A clean copy is admitted to the world and
marked mounted. The output is one `[pin]` block per sharing step this run
took (`fetched`, `admitted`, `mounted`). The mount takes effect when the
session next opens; until then the corpus is live but unmounted, so
`publish` refuses `selection-incomplete` naming it: reopen first. A run
interrupted after admission is completed by the next `adopt` of the same
corpus; adopting a mounted corpus again refuses as already adopted.
Adopting needs `sharing_root` configured.
