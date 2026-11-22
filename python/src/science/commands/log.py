"""Read a bounded interval of a mounted chain."""
from science.run_endpoint.evidence import chain_log


def handle(ctx, *, chain, after, through=None):
    return chain_log(ctx.config, chain=chain, after=after, through=through)
