Run `show` to see why you hold an adopted publication and what it is worth
to you: `corpus_id` names its pin in the sharing registry. The `pin` block
gives its state (`fetched`, `admitted`, `mounted`, `retired`), the world
its marker claims, the marker, the artifact, the view it was published
from, and whether it is kept. The `source` block says where the pin came
from and its `confirmation`: `origin-confirmed` when its source is a
provider location bound to that world, `recommended` when a followed
catalog names it, `unsourced` when no source stands. `fetch` is the fetch
record; `kernel` is this world's registry status (`known`, `live`,
`present`). `acceptance` says whether your accept policy accepts the world
and whether the corpus's records count as evidence; `evidence` lists each
assessment the corpus holds, whether it counts, and the verifications of
it across the session's corpora with their worlds and how many count under
the policy. Independence is not shown. When the kernel admitted the corpus
and the pin is not yet `mounted`, a finding says so: run `adopt` again to
reconcile. An unknown pin refuses `invalid-input`. Nothing is written.
