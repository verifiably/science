Run `publish-preview` before `publish`, with the same `target` and `to`, to
see what the kernel would freeze: the selection by kind and every selected
record, whether its closure is complete, which records carry another
world's attribution, and which datasets' bytes the destination will not
carry. It refuses exactly where `publish` would refuse before writing,
naming the kernel's reason (for `closure-incomplete`, the missing records).
Nothing is written.
