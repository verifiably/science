Run `run-output` to read one declared output file from a run's result manifest:
name `run` (the run ref) and `output` (the logical output path from the run's
manifest). Bytes are read from local operations scratch and verified against the
manifest's SHA-256 digest before rendering. The reply prints the run ref, output
path, verified digest and byte length ahead of the UTF-8 content, paged within
the output budget; continue with the cursor if truncated. Missing or reclaimed
scratch copies, digest mismatches and non-UTF-8 outputs refuse.
