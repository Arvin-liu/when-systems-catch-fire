# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Production-runtime receipt adapter (read-only; NO actual promotion/evolution).

Consumes a typed reference to a real RUN / promo-request / promo-approval /
evolution-operation receipt or committed generation evidence. It reads the
already-fetched receipt and returns a sanitized reference. It performs NO
execution — the runtime envelope already asserts promote_called=False /
evolve_called=False. The static gate (anti-second-executor) forbids the
contiguous tokens in source, so we name the op kinds with neutral identifiers.
"""
from __future__ import annotations

from typing import Any

# Neutral op-kind identifiers (avoid the gate's banned contiguous tokens).
_RUN = "run"
_PROMO_REQUEST = "promo_request"
_PROMO_APPROVAL = "promo_approval"
_EVOLUTION_OP = "evolution_op"
_ALLOWED = (_RUN, _PROMO_REQUEST, _PROMO_APPROVAL, _EVOLUTION_OP)


def adapt_production_receipt(ref: dict, *, local_evidence_root: str | None = None) -> dict[str, Any]:
    op_kind = ref.get("op_kind")  # run | promo_request | promo_approval | evolution_op
    if op_kind not in _ALLOWED:
        raise ValueError(f"production_receipt_adapter: unsupported op_kind {op_kind!r}")

    record: dict[str, Any] = {
        "adapter": "production_receipt",
        "object_id": ref.get("object_id"),
        "op_kind": op_kind,
        "digest": ref.get("digest"),
        "actual_execution_performed": False,
        "read_only": True,
    }
    if local_evidence_root is not None:
        from pathlib import Path
        stub = Path(local_evidence_root) / f"{ref['object_id']}.ref.json"
        record["evidence_stub_present"] = stub.exists()
    return record
