"""next: the derived queue of layer §4.4, computed at read time (§4.8)."""
from __future__ import annotations

from beliefs import stored
from beliefs.admission import Admitted, admit
from beliefs.dataset import Held, admission_state, dataset_address

from science.coordination import live_selection, selected_project
from science.report import Heading, KeyVals, Report

CLASSES = ("ready", "not-ready", "assessed-not-admitted", "admitted")


def _targeting_specs(view, proposition, profile):
    specs = (stored.analysis_spec_value(n, profile=profile) for n in view.iter_stored() if n.kind == "analysis-spec")
    return [spec for spec in specs if spec.target == proposition]


def _inputs_held(ctx, view, spec) -> bool:
    observations = ctx.observations()
    for role in spec.input_roles:
        node = next((n for n in view.iter_stored() if n.kind == "dataset"
                     and dataset_address(stored.dataset_declaration(n)) == role.dataset), None)
        if node is None:
            return False
        if not isinstance(admission_state(stored.dataset_declaration(node), observations.get(role.dataset, ())), Held):
            return False
    return True


def classify(ctx, proposition: str) -> str:
    _, view = ctx.single_view()
    profile = ctx.config.profile
    assessed = any(n.kind == "assessment" and stored.assessment_value(n, profile=profile).proposition == proposition
                   for n in view.iter_stored())
    if not assessed:
        return "ready" if any(_inputs_held(ctx, view, s) for s in _targeting_specs(view, proposition, profile)) else "not-ready"
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


def handle(ctx, *, limit=None) -> Report:
    project = selected_project(ctx)
    blocks: list = [Heading("Next")]
    if project is None:
        _, view = ctx.single_view()
        nodes = [node for node in view.iter_stored() if node.kind == "proposition"]
    else:
        # The project's query, denoted over the world as it stands: no epoch
        # mediates seeing a proposition just minted (coordination design
        # decision 3).
        live = live_selection(ctx, project)
        # Opened after the capture, never before it: a read view indexes the
        # corpus as it stood when it was opened, so an earlier one would not hold
        # a proposition minted in between, and its row would vanish under
        # `complete: true`.
        _, view = ctx.single_view()
        unheld = [ref for ref in live.selected if not view.holds(ref)]
        if unheld:
            # With one configured root, the capture reads no corpus but this
            # one, so a selected record it does not hold is an invariant broken,
            # not an outcome: fail rather than render a queue missing rows. Part
            # 3 replaces this with the lookup across mounted corpora.
            raise RuntimeError(
                "the live capture selected records the configured corpus does not hold: "
                + ", ".join(unheld))
        blocks.append(KeyVals("selection", _selection_pairs(ctx.selection, project, live)))
        # A selected record that is not a proposition is not a row.
        nodes = [node for node in map(view.get, live.selected) if node.kind == "proposition"]
    rows = sorted((CLASSES.index(classify(ctx, node.id)), node.id,
                   stored.display_statement(node) or node.title) for node in nodes)
    shown = rows[: (limit or 10)]
    blocks.append(KeyVals("propositions",
                          tuple((pid, f"{CLASSES[c]}: {statement}") for c, pid, statement in shown)
                          or (("none", "no propositions"),)))
    return tuple(blocks)
