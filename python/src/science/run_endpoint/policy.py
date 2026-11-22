"""Actor command admission in addition to the kernel's scoped act check."""
from science.refusal import Refusal, Refused

ORDINARY = frozenset({
    "assess", "belief", "claim", "decide", "heads", "hypothesis", "log", "next", "note",
    "project", "projects", "project-select", "project-show", "question", "recheck", "record",
    "reuse", "revise", "run-output", "source", "source-assertion", "source-coreference", "source-correct",
    "status", "task", "topic",
})
CONFINED = frozenset({"dataset", "derive", "fetch", "run", "spec"})
REFUSED = frozenset({
    "adopt", "provider-bind", "provider-inspect", "publish", "publish-preview", "show", "verify",
})


def admit(command, inputs):
    if command not in ORDINARY and command not in CONFINED:
        raise Refused(Refusal("permit-exceeded", "This command is unavailable through a run handle"))
    if command == "heads" and inputs.get("resolve"):
        raise Refused(Refusal("permit-exceeded", "Resolving pending transactions requires the supervisor"))
    if command == "fetch" and str(inputs.get("source", "")).lower().startswith(("https:", "http:")):
        raise Refused(Refusal("permit-exceeded", "A run handle can fetch only from its scratch directory"))
