"""Inspect the configured world's chain heads."""
from science.run_endpoint.evidence import heads


def handle(ctx, *, resolve=False):
    return heads(ctx.config, resolve=resolve)
