Run `revise` to change a project, question, hypothesis, task or decision
by address. Fields not given carry over from the current revision; a
field the record's kind lacks refuses. Closing a task is `status` `done`
or `dropped`; `depends` replaces a task's dependencies and `clear_depends`
empties them. An address whose record has diverged into several standing
revisions refuses and names them; `repair` reconciles them into one, and
then every field must be given, since there is no single revision to
carry over from. Report the minted revision.
