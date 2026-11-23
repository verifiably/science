"""Seal fields determined by the acquisition evidence and its declaration."""

from beliefs.dataset import DatasetDeclaration, ResourceDeclaration, dataset_address
from beliefs.holdings.acquisition_log import log_summary

__all__ = ["seal_identity"]


def seal_identity(log, title, locator):
    summary = log_summary(log)
    declaration = DatasetDeclaration((ResourceDeclaration("data", summary.tree),))
    return dict(log=summary.log, tree=summary.tree, dataset=dataset_address(declaration),
                origin=log.header.origin, title=title, locator=locator)
