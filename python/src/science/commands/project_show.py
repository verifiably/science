"""project-show: one project and its subordinate records (spec §3.8)."""
from __future__ import annotations

import json

from beliefs import stored
from beliefs.view_query import stored_query

from science.coordination import selected_project, tip_nodes
from science.refusal import Refusal, Refused
from science.report import Heading, KeyVals, Report, Text

_VIEWS = (("question", "questions"), ("hypothesis", "hypotheses"), ("decision", "decisions"))


def _entries(resolver, kind: str, project) -> list:
    """(sort name, address, tips) for every address of `kind` under `project`,
    by name then address."""
    found = []
    for address, resolved in resolver.standing(kind, project=project).items():
        tips = tip_nodes(resolver, resolved)
        found.append((min((tip.title for tip in tips), default=""), str(address), tips))
    return sorted(found, key=lambda entry: entry[:2])


def _status(node) -> str:
    return node.facets[stored.COORDINATION_FACET]["status"]


def _label(tips, describe) -> str:
    if not tips:
        return "no standing revision"
    if len(tips) > 1:  # listed once, never dropped
        return "divergent: " + "; ".join(f"{tip.title} @{tip.uid}" for tip in tips)
    return describe(tips[0])


def _named(node) -> str:
    return node.title


def _task(node) -> str:
    return f"{_status(node)}: {node.title}"


def handle(ctx) -> Report:
    # First, before the selection is looked at: with `coordination = false`
    # nothing can be selected, and the refusal that says so must not be
    # pre-empted by `no-current-project`.
    resolver = ctx.coordination()
    project = selected_project(ctx)
    if project is None:
        raise Refused(Refusal(
            "no-current-project",
            "no project is selected; select one with `project-select`, or name one with `--project`",
        ))
    query = json.dumps(stored_query(project).projection(), sort_keys=True, separators=(",", ":"))
    blocks: list = [
        Heading(f"Project: {project.title}"),
        KeyVals("project", (("address", str(ctx.selection)), ("revision", project.uid),
                            ("name", project.title), ("query", query))),
    ]
    open_tasks, closed_tasks = [], []
    for entry in _entries(resolver, "task", ctx.selection):
        tips = entry[2]
        # A task with no one tip has no one status, and wants attention: open.
        closed = len(tips) == 1 and _status(tips[0]) != "open"
        (closed_tasks if closed else open_tasks).append(entry)
    sections = [("open tasks", open_tasks, _task)]
    sections += [(title, _entries(resolver, kind, ctx.selection), _named) for kind, title in _VIEWS]
    sections.append(("closed tasks", closed_tasks, _task))
    for title, entries, describe in sections:
        if entries:
            blocks.append(KeyVals(title, tuple((address, _label(tips, describe))
                                               for _, address, tips in entries)))
    if len(blocks) == 2:
        blocks.append(Text("No questions, hypotheses, tasks or decisions yet."))
    return tuple(blocks)
