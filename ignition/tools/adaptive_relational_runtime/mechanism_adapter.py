# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Function OS adapter (dual-route) for the Adaptive Relational Runtime.

Validates a seven-element mechanism contract and routes it to exactly one of:
  * an existing registered Function OS capability (``function_os_capability``),
  * a deterministic stub (``deterministic_stub``).

The scaffold is not a second general executor: this adapter only validates and
emits an adapter receipt declaring which registered capability *should* carry
the mechanism. Real execution remains the predecessor Function OS flow; stubs
emit receipts with ``real_world_action=False`` and no realized side effects.
"""
from __future__ import annotations

from typing import Any

from . import canonical

# Allowed declared side-effect vocabulary (schema-enforced enum subset).
_ALLOWED_DECLARED_EFFECTS = frozenset(
    {"none", "read_local_store", "emit_receipt", "write_bounded_output"}
)


class MechanismContractRejected(Exception):
    """Raised when a mechanism contract fails validation (treated as rollback)."""


def _seven_element_keys() -> tuple[str, ...]:
    return (
        "mechanism_type",
        "input_contract",
        "output_contract",
        "executable_surface",
        "preconditions",
        "side_effects",
        "rollback",
    )


def _lookup_capability(adapter_caps: dict, capability_id: str) -> dict | None:
    for cap in adapter_caps.get("adapter_capabilities", []):
        if cap.get("capability_id") == capability_id:
            return cap
    return None


def validate_mechanism_contract(mechanism: dict, adapter_caps: dict) -> dict:
    """Validate the seven-element mechanism contract and resolve the dual-route.

    Returns an adapter receipt dict on success. Raises ``MechanismContractRejected``
    (rollback) on any contract violation: missing input contract, undeclared or
    real-world side effect, or an unregistered/inactive/incompatible execution
    surface target.
    """
    for key in _seven_element_keys():
        if key not in mechanism:
            raise MechanismContractRejected(f"missing required contract field: {key}")
    if "adapter_capability_ref" not in mechanism:
        raise MechanismContractRejected("missing adapter_capability_ref field")

    # input_contract: declared params (>=1) and requires array.
    input_contract = mechanism["input_contract"]
    if not isinstance(input_contract.get("params"), dict) or len(input_contract["params"]) < 1:
        raise MechanismContractRejected("input_contract.params must be a non-empty object")
    if not isinstance(input_contract.get("requires"), list):
        raise MechanismContractRejected("input_contract.requires must be an array")

    # output_contract: receipt_required const True.
    output_contract = mechanism["output_contract"]
    if output_contract.get("receipt_required") is not True:
        raise MechanismContractRejected("output_contract.receipt_required must be true")

    # side_effects: real_world const False; declared within vocabulary.
    side_effects = mechanism["side_effects"]
    if side_effects.get("real_world") is not False:
        raise MechanismContractRejected("side_effects.real_world must be false (no real-world effect)")
    declared = side_effects.get("declared")
    if not isinstance(declared, list):
        raise MechanismContractRejected("side_effects.declared must be an array")
    for effect in declared:
        if effect not in _ALLOWED_DECLARED_EFFECTS:
            raise MechanismContractRejected(f"undeclared side effect: {effect!r}")

    # executable_surface dual-route.
    surface = mechanism["executable_surface"]
    kind = surface.get("kind")
    target = surface.get("target")
    if kind not in ("function_os_capability", "deterministic_stub"):
        raise MechanismContractRejected(f"unsupported executable_surface.kind: {kind!r}")
    cap = _lookup_capability(adapter_caps, target)
    if cap is None:
        raise MechanismContractRejected(f"unregistered capability target: {target!r}")
    if cap.get("status") != "active":
        raise MechanismContractRejected(f"inactive capability target: {target!r}")
    if cap.get("kind") != kind:
        raise MechanismContractRejected(
            f"capability {target!r} kind {cap.get('kind')!r} != surface kind {kind!r}"
        )

    receipt = {
        "receipt_id": canonical.deterministic_id(
            "mrec", canonical.canonical_json({"mechanism": mechanism, "capability": cap})
        ),
        "mechanism_id": mechanism.get("record_id"),
        "route": kind,
        "capability_id": target,
        "stub": kind == "deterministic_stub",
        "side_effects_realized": [],
        "real_world_action": False,
        "claim_ceiling_max": cap.get("claim_ceiling_max"),
        "validated_at": mechanism.get("time", {}).get("ingestion_time"),
    }
    return receipt


def route_mechanism(mechanism: dict, adapter_caps: dict) -> tuple[str, Any]:
    """Resolve a mechanism to a route.

    Returns ``("adapter_receipt", receipt)`` on success or
    ``("rejected", reason)`` on failure (caller treats rejection as rollback).
    """
    try:
        receipt = validate_mechanism_contract(mechanism, adapter_caps)
    except MechanismContractRejected as exc:
        return "rejected", str(exc)
    return "adapter_receipt", receipt
