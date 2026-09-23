Run `run` to execute a frozen spec's analysis once under confinement: name
the spec, the dataset it observes, the code directory holding the workflow,
the entrypoint and the targets. It needs bubblewrap on this host and refuses
otherwise before touching anything. The minted run record is the output; a
refusal names the kernel's reason and nothing was written.
