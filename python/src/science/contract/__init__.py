"""Contracts — the normative source of truth.

D §6 is explicit that the contracts are the normative SSOT and ``ProfileSpec`` is
the sole *compiled* runtime profile. Nothing here is authored beside a contract.
"""

from science.contract.base import BaseContract, ClaimGrammar, load_base_contract, parse_base_contract

__all__ = ["BaseContract", "ClaimGrammar", "load_base_contract", "parse_base_contract"]
