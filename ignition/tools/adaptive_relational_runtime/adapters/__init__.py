# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Read-only adapters for the R2 real-object pilot.

Every adapter consumes a TYPED REFERENCE (digest + location) and reads only
already-fetched local files or declared repository evidence. None performs a
real-world action, network call, or external write. The static gate
(tools/adaptive_relational_runtime/static_gate.py) re-verifies zero violations.
No promotion or evolution execution is performed by any adapter.
"""
from __future__ import annotations

from .text_ref_adapter import adapt_text_ref
from .git_pr_ci_adapter import adapt_git_pr_ci
from .structured_data_adapter import adapt_structured_data
from .production_receipt_adapter_r2 import adapt_production_receipt
from .temporal_sequence_adapter import adapt_temporal_sequence
from .mechanism_state_adapter import adapt_mechanism_state

__all__ = [
    "adapt_text_ref", "adapt_git_pr_ci", "adapt_structured_data",
    "adapt_production_receipt", "adapt_temporal_sequence", "adapt_mechanism_state",
]
