Run `revise` to change a project, question, hypothesis, task, decision or topic
by unpinned address. A topic must retain a non-empty body; a new query must
name at least one resolving address and have every closure anchor resolve.
Carried queries are not rechecked when renaming or editing prose. Fields not given carry over from the current revision; a
field the record's kind lacks refuses. Closing a task is `status` `done`
or `dropped`; `depends` replaces a task's dependencies and `clear_depends`
empties them. An address whose record has diverged into several standing
revisions refuses and names them; `repair` reconciles them into one, and
then every field must be given, since there is no single revision to
carry over from. Report the minted revision.
