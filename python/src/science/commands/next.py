"""next: the derived queue of layer §4.4, computed at read time (§4.8)."""
from __future__ import annotations

from beliefs import stored
from beliefs.admission import Admitted, admit
from beliefs.dataset import Held, admission_state, dataset_address

from science.coordination import live_selection, selected_project
from science.refusal import Refusal, Refused
from science.report import Heading, KeyVals, Report

CLASSES = ("ready", "not-ready", "assessed-not-admitted", "admitted")


def _targeting_specs(view, proposition, profile):
    specs = (stored.analysis_spec_value(n, profile=profile) for n in view.iter_stored() if n.kind == "analysis-spec")
    return [spec for spec in specs if spec.target == proposition]


def _dataset_node(mounts, address):
    return next((node for mount in mounts for node in mount.view.iter_stored() if node.kind == "dataset"
                 and dataset_address(stored.dataset_declaration(node)) == address), None)


def _inputs_held(ctx, mounts, spec) -> bool:
    observations = ctx.observations()
    for role in spec.input_roles:
        # One world record, in whichever mount declared it (spec §5.5).
        node = _dataset_node(mounts, role.dataset)
        if node is None:
            return False
        if not isinstance(admission_state(stored.dataset_declaration(node), observations.get(role.dataset, ())), Held):
            return False
    return True


def classify(ctx, proposition: str) -> str:
    """The four-class rule over the evidence in the proposition's own corpus,
    decoded under that corpus's profile (spec §5.5)."""
    mount = ctx.mount_holding(proposition)
    view, profile = mount.view, mount.profile
    assessed = any(n.kind == "assessment" and stored.assessment_value(n, profile=profile).proposition == proposition
                   for n in view.iter_stored())
    if not assessed:
        mounts = ctx.mounts()
        return ("ready" if any(_inputs_held(ctx, mounts, s) for s in _targeting_specs(view, proposition, profile))
                else "not-ready")
    inputs = ctx.gather_inputs(proposition)
    observations = ctx.observations()
    for assessment in inputs.assessments:
        run = inputs.runs.get(assessment.run)
        if run is not None and isinstance(admit(assessment, run, observations, inputs.verifications), Admitted):
            return "admitted"
    return "assessed-not-admitted"


def _selection_pairs(selection, project, live) -> tuple:
    """What the rows were read through: the project's pinned address and name,
    and the live capture's completeness and stamp."""
    pairs = [
        ("project", str(selection.pinned(project.uid))),
        ("name", project.title),
        ("complete", "true" if live.complete else "false"),
        ("absent", ", ".join(live.absent) or "none"),
        ("world", live.stamp.world_id),
    ]
    pairs += [(f"corpus {corpus_id}", state) for corpus_id, state in live.stamp.coverage]
    return tuple(pairs)


def _unmounted_corpora(world) -> list[str]:
    """The live admitted corpora with no configured carrier, from the world's
    own registry and status: what `corpus_roots` leaves unmounted."""
    admitted = sorted({record.corpus_id for record in world.registry().admissions})
    return [corpus_id for corpus_id in admitted
            if (status := world.status(corpus_id)).live and not status.present]


def _unmounted(ctx, refs) -> Refused:
    corpora = _unmounted_corpora(ctx.world)
    where = f"; the world admits {', '.join(corpora)}, which corpus_roots does not mount" if corpora else ""
    return Refused(Refusal("invalid-input",
                           f"the selection names {', '.join(refs)}, which no corpus in corpus_roots holds{where}"))


def _capture(ctx, project):
    """The live selection. The capture reads the world through the configured
    roots, so an address in an admitted corpus `corpus_roots` does not mount is
    unknown to it: that refusal is the configuration's, and says so (spec §5.5).
    Every other kernel refusal passes through."""
    try:
        return live_selection(ctx, project)
    except Refused as caught:
        data = caught.refusal.data
        if (caught.refusal.code == "kernel-refused" and data.get("kind") == "SelectionRefused"
                and data.get("reason") == "address-unknown" and _unmounted_corpora(ctx.world)):
            raise _unmounted(ctx, data["refs"]) from None
        raise


def handle(ctx, *, limit=None) -> Report:
    project = selected_project(ctx)
    blocks: list = [Heading("Next")]
    if project is None:
        nodes = [node for mount in ctx.mounts() for node in mount.view.iter_stored() if node.kind == "proposition"]
    else:
        # The project's query, denoted over the world as it stands: no epoch
        # mediates seeing a proposition just minted (coordination design
        # decision 3).
        live = _capture(ctx, project)
        # Opened after the capture, never before it: a read view indexes the
        # corpus as it stood when it was opened, so an earlier one would not hold
        # a proposition minted in between, and its row would vanish under
        # `complete: true`.
        mounts = ctx.mounts()
        unmounted = [ref for ref in live.selected if not any(m.view.holds(ref) for m in mounts)]
        if unmounted:
            # A capture naming a record no mounted corpus holds (one wider than
            # corpus_roots, or a view opened short of it) leaves a row this
            # read cannot classify: refused by name, never dropped.
            raise _unmounted(ctx, unmounted)
        blocks.append(KeyVals("selection", _selection_pairs(ctx.selection, project, live)))
        # A selected record that is not a proposition is not a row.
        nodes = [node for node in (next(m.view.get(ref) for m in mounts if m.view.holds(ref))
                                   for ref in live.selected) if node.kind == "proposition"]
    rows = sorted((CLASSES.index(classify(ctx, node.id)), node.id,
                   stored.display_statement(node) or node.title) for node in nodes)
    shown = rows[: (limit or 10)]
    blocks.append(KeyVals("propositions",
                          tuple((pid, f"{CLASSES[c]}: {statement}") for c, pid, statement in shown)
                          or (("none", "no propositions"),)))
    return tuple(blocks)
