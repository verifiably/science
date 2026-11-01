Run `recheck` when a store location is blocked `unsettled`: a holdings write
appended its intent and then the store refused or the write was interrupted,
so no observation followed. Give the location exactly as the blocked row names
it, `store:<store id>:<relative path>`, with nothing added or trimmed. The
location must be in this configuration's `store_root`; a location in a read
store refuses and names the recovery configuration. The re-check reads the
store and writes evidence to the governed corpus: it settles only intents in
this configuration's `write_root`, and on a live world it needs the person's
authorization first. The output is what the kernel observed. `found` with a
digest or `absent` publishes an observation and clears the block; an
inconclusive read (`retrieval-failed` or `byte-locator-untested` with the
kernel's reason) publishes none and leaves the block. Report the result as
given; never assume absent. A refusal changes nothing.
