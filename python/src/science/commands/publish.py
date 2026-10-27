"""publish: a project's view to a local directory or a git remote, through the kernel's session publish door
(commons 1a; beliefs writer-session design, sharing and publish doors amendment)."""
from __future__ import annotations

from beliefs.errors import EpochUnknown, PublicationRefused, SelectionRefused
from beliefs.publish import Published, PublishRefused, PublishUnresolved
from beliefs.session import KernelRefusalValue

from science import publication
from science.acceptance import acceptance_inputs
from science.coordination import resolve_project_ref
from science.report import Report, record_block
from science.transport_git import GitTransportFault
from science.world_belief import REMEDY


def _run(ctx, writer, *, target, to, resume):
    # `publication.transport_for`, read at call time: a test replaces it by assignment.
    config = ctx.config
    if resume is not None:
        # The token's attempt carries its own view and destination; `to` chooses the transport.
        destination = publication.parse_destination(to)
        return writer.resume_publish(event_token=resume, operations_root=config.operations_root,
                                     staging_profile=config.profile,
                                     transport=publication.transport_for(config, destination))
    view = resolve_project_ref(ctx, target)
    destination = publication.parse_destination(to)
    return writer.publish(view=view, destination=destination, operations_root=config.operations_root,
                          staging_profile=config.profile, transport=publication.transport_for(config, destination),
                          own_corpora=acceptance_inputs(ctx).own_roots)


def _refused(reason: str, detail: str) -> KernelRefusalValue:
    return KernelRefusalValue(publication.PublishRefusedValue(reason=reason, detail=detail))


def handle(ctx, writer, *, target, to, resume=None) -> Report:
    try:
        outcome = _run(ctx, writer, target=target, to=to, resume=resume)
    except GitTransportFault as fault:
        # The kernel's attempt stays unfinished with its mark; `resume` continues it.
        raise KernelRefusalValue(publication.TransportFault(reason="transport-fault", detail=str(fault))) from fault
    except PublicationRefused as caught:
        raise _refused(caught.reason, str(caught)) from caught
    # Step 0 reads the current epoch and evaluates the view there before the intent: nothing was written.
    except EpochUnknown as caught:
        raise _refused("no-epoch", f"this world has published no epoch; {REMEDY}") from caught
    except SelectionRefused as caught:
        raise _refused(caught.reason, publication.selection_detail(caught)) from caught
    if type(outcome) is PublishRefused:
        raise _refused(outcome.outcome, outcome.event_token)
    if type(outcome) is PublishUnresolved:
        raise _refused(outcome.reason, outcome.event_token)
    assert type(outcome) is Published, outcome
    # The binding's own uid: a resumed attempt names its view and destination only in its intent.
    view = ctx.write_view()
    return (record_block(view.get(view.live_id(outcome.binding))),)
