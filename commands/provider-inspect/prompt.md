Run `provider-inspect` before binding a provider: `location` is the
`https://` git remote a publication was published to and `corpus_id` the
publication's corpus id. It fetches that corpus into a scratch copy,
verifies its chain against its head artifact, reads its publication
marker, and deletes the copy. The output is the `publication` block: the
`world` id the marker claims, the `marker` uid, the `artifact` identity
(the SHA-256 of the head artifact), the revision-pinned `view` it was
published from, and the `verdict`, always `validated`. The world id is the
publisher's claim, not proof of who controls that world; confirm it with
the publisher, then run `provider-bind` with it as `world`. Nothing is
recorded. A location that does not hold the corpus, cannot be reached, or
holds a copy that does not validate refuses `invalid-input` naming the
location.
