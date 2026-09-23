Run `verify` after `assess`: name the assessment and the same code directory
and entrypoint the run used. The original run is replayed, the two are
compared under the spec's equivalence rule, and the verification is minted
with its scope and verdict. `clean-environment` with `passed` is what admits
the assessment to belief; ask `belief` to see whether it did.
