"""Bind a scheduled research action to the prepared records and captured workflow."""
import hashlib
import json
from pathlib import Path
import re
import stat
from uuid import UUID

from beliefs import stored
from beliefs.dataset import dataset_address
from beliefs.tree import TreeMember, make_tree, tree_digest

from science.refusal import Refusal, Refused

__all__ = ["ResearchAction", "workflow_digest"]

COMMANDS = ["next", "run", "assess", "verify", "belief"]
_COORDINATION = {"decision", "hypothesis", "note", "project", "question", "task", "theme", "topic"}


def require(condition, message):
    if not condition:
        raise Refused(Refusal("allowance-scope", message))


def _relative(value):
    return type(value) is str and all(part not in ("", ".", "..") for part in value.split("/")) and "\\" not in value


def workflow_digest(root):
    root = Path(root)
    require(stat.S_ISDIR(root.lstat().st_mode), "Expected a workflow directory")
    members = []
    for path in sorted(root.rglob("*")):
        info = path.lstat()
        if stat.S_ISDIR(info.st_mode):
            require(any(path.iterdir()), "An empty workflow directory has no content identity")
            continue
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and not info.st_mode & 0o111,
                "Workflow files must be regular, single-link and non-executable")
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        members.append(TreeMember(path.relative_to(root).as_posix(), "sha256:" + digest, info.st_size))
    require(members, "Empty workflow")
    return tree_digest(make_tree(members))


class ResearchAction:
    def __init__(self, action, permit):
        require(type(action) is dict and set(action) == {"campaign_id", "member_id", "conversation_id",
                "proposition", "spec", "dataset", "commands", "workflow"}, "Invalid research action fields")
        for key in ("campaign_id", "member_id"):
            require(type(action[key]) is str and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", action[key]), "Invalid grant name")
        try:
            require(str(UUID(action["conversation_id"])) == action["conversation_id"], "Invalid conversation")
        except (ValueError, TypeError, AttributeError):
            require(False, "Invalid conversation UUID")
        for key, prefix in (("proposition", "proposition:"), ("spec", "analysis-spec:"), ("dataset", "dataset:")):
            require(type(action[key]) is str and action[key].startswith(prefix) and len(action[key]) > len(prefix),
                    "Expected a typed " + key)
        require(action["commands"] == COMMANDS, "Unexpected research command set")
        workflow = action["workflow"]
        require(type(workflow) is dict and set(workflow) == {"tree_digest", "entrypoint", "targets", "cores"},
                "Invalid workflow fields")
        require(type(workflow["tree_digest"]) is str and re.fullmatch(r"sha256-tree:[0-9a-f]{64}", workflow["tree_digest"])
                and _relative(workflow["entrypoint"]) and type(workflow["targets"]) is list and workflow["targets"]
                and all(_relative(path) for path in workflow["targets"])
                and type(workflow["cores"]) is int and workflow["cores"] > 0, "Invalid workflow binding")
        require(not permit.ungoverned and permit.kinds == _COORDINATION | {"run", "act-report", "assessment", "verification"}
                and permit.act_families == {"run", "corpus-write"}, "Unexpected research writer ceiling")
        self.action = action
        self.digest = hashlib.sha256(json.dumps(action, sort_keys=True, separators=(",", ":"),
                                               ensure_ascii=False).encode()).hexdigest()
        self.records = {}

    def check_preparation(self, ctx):
        a = self.action
        view = ctx.write_view()
        require(all(view.holds(a[k]) for k in ("proposition", "spec", "dataset")), "Prepared target is missing")
        spec = stored.analysis_spec_value(view.get(a["spec"]), profile=ctx.config.profile)
        address = dataset_address(stored.dataset_declaration(view.get(a["dataset"])))
        require(spec.target == a["proposition"] and address and
                [r.dataset for r in spec.input_roles if r.role == "observes"] == [address], "Prepared spec/inputs differ")

    def admit(self, command, inputs):
        a = self.action
        require(command in COMMANDS and "workflow_environment" not in inputs, "Command outside the research grant")
        if command == "run":
            require(inputs.get("spec") == a["spec"] and inputs.get("dataset") == a["dataset"], "Unbound run inputs")
        elif command == "verify":
            require("run" not in inputs and self.records.get("assessment") and
                    inputs.get("assessment") == self.records["assessment"], "Verification requires the bound assessment")
        elif command == "assess":
            require(self.records.get("run") and inputs.get("run") == self.records["run"], "Assessment requires the bound run")
        elif command == "belief":
            require(self.records.get("assessment") and inputs.get("proposition") == a["proposition"],
                    "Belief requires the assessed proposition")

    def prepare_job(self, command, inputs, ctx):
        workflow = self.action["workflow"]
        require(inputs["entrypoint"] == workflow["entrypoint"] and inputs.get("cores", 1) == workflow["cores"],
                "Workflow entrypoint or cores differ")
        require(workflow_digest(inputs["code"]) == workflow["tree_digest"], "Captured workflow bytes differ")
        targets = inputs.get("targets")
        if command == "verify":
            from beliefs.runrecord import decode_run_closure
            original = decode_run_closure(ctx.write_view().get(self.records["run"]))
            targets = original.recipe.invocation.targets
        require(list(targets) == workflow["targets"], "Job targets differ from the prepared workflow")

    def restore(self, launch, ctx):
        from science.run_endpoint.history import restore
        try:
            restore(self, launch, ctx)
        except (OSError, ValueError, TypeError, AttributeError, KeyError) as error:
            raise Refused(Refusal("allowance-unavailable", "Unusable predecessor evidence")) from error

    def fresh(self, command):
        kind = {"run": "run", "assess": "assessment", "verify": "verification"}[command]
        require(kind not in self.records, "The member already completed " + command)

    def record(self, command, pairs, ctx):
        from beliefs.runrecord import decode_run_closure
        kind = {"run": "run", "assess": "assessment", "verify": "verification"}.get(command)
        require(kind is not None, "Unbound historical command")
        self.fresh(command)
        view = ctx.write_view()
        nodes = []
        for uid, ref in pairs:
            node = view.get(ref)
            require(node.uid == uid, "Substituted record")
            nodes.append(node)
        produced = [node for node in nodes if node.kind == kind]
        if command == "verify" and not produced and all(node.kind in ("run", "act-report") for node in nodes):
            # A partial multi-act invocation does not prove verification.
            return
        require(len(produced) == 1, "Expected exactly one " + kind)
        node = produced[0]
        if command == "run":
            recipe = decode_run_closure(node).recipe
            require(stored.typed_ref("analysis-spec", recipe.spec_identity) == self.action["spec"]
                    and list(recipe.invocation.targets) == self.action["workflow"]["targets"], "Original recipe differs")
        elif command == "assess":
            value = stored.assessment_value(node, profile=ctx.config.profile)
            require(stored.typed_ref("run", value.run) == self.records.get("run")
                    and stored.typed_ref("analysis-spec", value.spec) == self.action["spec"], "Assessment lineage differs")
        else:
            value = stored.verification_value(node)
            require(stored.typed_ref("assessment", value.assessment) == self.records.get("assessment"),
                    "Verification lineage differs")
        self.records[kind] = node.id

    def assessment_key(self, ctx):
        node = ctx.write_view().get(self.records["assessment"])
        return stored.assessment_value(node, profile=ctx.config.profile).key()
