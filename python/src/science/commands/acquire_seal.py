"""Accept a fetched set through the attended writer."""

from science.acquisition.seal import seal_set


def handle(ctx, writer, *, set, accept_partial=None):
    return seal_set(ctx, writer, set, accept_partial)
