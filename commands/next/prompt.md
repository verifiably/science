Run `next` when the user asks what to work on. It lists propositions in a
fixed order — ready (a spec targets it and every input is held), not ready,
assessed but not admitted, admitted — with each one's statement. With a
project selected, or named with `project` for this call only, it lists the
propositions that project's query selects, evaluated over the world as it
stands now, and opens with a `selection` block: the project, whether every
corpus was present (`complete`, `absent`), and the states it read. With no
project it lists the whole world. Nothing is stored; the ranking is
recomputed every time. It names no priority function; that is a later
sub-project's.
