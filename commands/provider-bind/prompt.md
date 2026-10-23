Run `provider-bind` to record that a location speaks for a world:
`location` is the `https://` git remote, `corpus_id` a publication there,
and `world` the world id you confirm, as `provider-inspect` reported it.
The confirmation is the argument: it fetches and verifies the publication
into scratch, and binds the location only when `world` is the world its
marker claims, refusing `world-mismatch` (with the `claimed` and `given`
ids) otherwise. `world` must be another world's id, not this one's. The
output is one `[pin]` block for the `bound` sharing line: the corpus, its
marker, the artifact identity, the world, the view and the verdict. Pins
learned from a bound location are origin-confirmed, which an `accept`
policy requires. Binding needs `sharing_root` configured. A location that
does not hold the corpus or a copy that does not validate refuses
`invalid-input` naming the location, and nothing is recorded.
