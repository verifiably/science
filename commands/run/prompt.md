Run `run` to execute a frozen spec's analysis once under confinement: name
the spec, the dataset it observes, the code directory holding the workflow,
the entrypoint and the targets. It needs bubblewrap on this host and refuses
otherwise before touching anything. The minted run record is the output and
carries its result manifest (output names and digests); read a declared output's
verified content with `run-output`. A refusal names the kernel's reason and
nothing was written.
