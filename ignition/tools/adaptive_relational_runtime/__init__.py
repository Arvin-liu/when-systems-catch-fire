# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Adaptive Relational Runtime R1 scaffold -- deterministic runtime skeleton.

This package adapts the existing Function OS and the production runtime receipt.
It creates NO second executor: it contains validators, adapters, a planner and
deterministic stubs only, and it emits receipts rather than performing actions.
Tools under this directory are licensed under the Business Source License 1.1
(PointFire scope); they convert to AGPL-3.0-or-later on the applicable Change Date.
"""
from . import canonical
from . import runtime
from . import mechanism_adapter
from . import production_receipt_adapter
from . import static_gate

__all__ = [
    "canonical",
    "runtime",
    "mechanism_adapter",
    "production_receipt_adapter",
    "static_gate",
]
