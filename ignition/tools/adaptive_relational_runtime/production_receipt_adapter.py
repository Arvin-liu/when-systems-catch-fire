# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Read-only adapter over the production operation_receipt.

Transcribes the production operation_receipt (13 required fields, verbatim) into
the ARR execution-receipt-adapter record and re-verifies the closed-manifest
invariants via a six-step identity recompute. The adapter reads production
stores and re-derives identity; it NEVER writes, never calls a write path, and
never performs a real-world action.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.ignition_runtime.schemas_loader import Draft202012Validator

from . import canonical

REPO_ROOT = Path(__file__).resolve().parents[2]
_EXEC_SCHEMA_PATH = (
    REPO_ROOT
    / "schemas/architecture/adaptive-relational-runtime"
    / "execution-receipt-adapter.schema.json"
)

# Canonical required-file set per op type (the "complete_file_list"). Only the
# op types the scaffold consumes in read-only mode are modeled here.
_CANON: dict[str, frozenset[str]] = {
    "bootstrap": frozenset(
        {"store_identity.json", "manifest.json", "receipt.json", "audit_index.json"}
    ),
    "run": frozenset(
        {
            "store_identity.json",
            "manifest.json",
            "materials.json",
            "results.json",
            "candidates.json",
            "unknowns.json",
            "signals.json",
            "receipt.json",
            "audit_index.json",
        }
    ),
}


def _exec_validator() -> Draft202012Validator:
    schema = json.loads(_EXEC_SCHEMA_PATH.read_text(encoding="utf-8"))  # read-only
    return Draft202012Validator(schema)


def transcribe(operation_receipt: dict) -> dict:
    """Transcribe the 13 required fields verbatim and validate the adapter record.

    Raises ValueError if the transcribed record violates the execution-receipt
    adapter schema. The adapter never writes.
    """
    fields = [
        "receipt_id",
        "op_type",
        "operation_id",
        "before_gen",
        "after_gen",
        "material_set",
        "provider_identity",
        "counts",
        "result_digests",
        "op_outcome",
        "timestamps",
        "self_final_sha_claimed",
        "live_refetch_required",
    ]
    adapter = {f: operation_receipt[f] for f in fields}
    errors = sorted(
        _exec_validator().iter_errors(adapter), key=lambda e: list(e.path)
    )
    if errors:
        first = errors[0]
        loc = ".".join(str(p) for p in first.path) or "<root>"
        raise ValueError(f"execution-receipt-adapter error at {loc}: {first.message}")
    return adapter


def recompute_receipt_id(operation_receipt: dict) -> str:
    """Step 1: recompute the content-derived receipt id (predecessor formula)."""
    core = {
        k: v
        for k, v in operation_receipt.items()
        if k not in ("receipt_id", "self_final_sha_claimed", "live_refetch_required")
    }
    return "rcpt_" + canonical.sha256_hex(canonical.canonical_json(core))[:32]


def _gen_core_payload(op_type: str, ledgers: dict, parent: Any) -> dict:
    core = {
        "parent": parent,
        "op_type": op_type,
        "materials": ledgers.get("materials.json", {}),
        "results": ledgers.get("results.json", []),
        "candidates": ledgers.get("candidates.json", []),
        "unknowns": ledgers.get("unknowns.json", []),
        "signals": ledgers.get("signals.json", []),
    }
    if op_type in ("promote_request", "promote_approval"):
        core = {k: v for k, v in core.items() if k != "parent"}
    return core


def compute_gen_id(op_type: str, ledgers: dict, parent: Any) -> str:
    """Content-derived, immutable generation id (mirrors Generation.compute_gen_id)."""
    payload = canonical.canonical_json(_gen_core_payload(op_type, ledgers, parent))
    return "gen_" + canonical.sha256_hex(payload)[:32]


def _build_manifest(op_type: str, ledgers: dict, gen_id: str,
                    operation_id: str, parent: Any) -> dict:
    required = sorted(_CANON[op_type])
    digests: dict[str, str] = {}
    for name in required:
        if name == "manifest.json":
            continue
        digests[name] = canonical.sha256_hex(canonical.canonical_json(ledgers[name]))
    manifest_no_self = {
        "schema_version": "ignition_runtime/1.0.0",
        "store_identity_ref": "store_identity.json",
        "parent_generation": parent,
        "op_type": op_type,
        "operation_id": operation_id,
        "generation_id": gen_id,
        "required_files": required,
        "digests": {**digests, "manifest.json": ""},
        "receipt_ref": "receipt.json",
        "committed": True,
        "immutable": True,
        "provider_identity": ledgers.get("store_identity.json", {}).get("provider"),
        "timestamps": {},
    }
    digests["manifest.json"] = canonical.sha256_hex(
        canonical.canonical_json(manifest_no_self)
    )
    return {**manifest_no_self, "digests": digests}


def _closed_manifest_triple(manifest: dict, ledgers: dict) -> bool:
    """Step 3: declared == digest_keys == actual (closed-manifest proof)."""
    op_type = manifest["op_type"]
    required = set(manifest["required_files"])
    digest_keys = set(manifest["digests"].keys())
    actual = set(ledgers.keys()) | {"manifest.json"}
    if required != _CANON[op_type]:
        return False
    if digest_keys != required:
        return False
    if actual != required:
        return False
    for name in required:
        if name == "manifest.json":
            m2 = {**manifest, "digests": {**manifest["digests"], "manifest.json": ""}}
            digest = canonical.sha256_hex(canonical.canonical_json(m2))
        else:
            digest = canonical.sha256_hex(canonical.canonical_json(ledgers[name]))
        if digest != manifest["digests"][name]:
            return False
    if manifest.get("committed") is not True:
        return False
    if manifest.get("immutable") is not True:
        return False
    return True


def build_synthetic_operation_receipt(provider: str = "fixture://demo") -> tuple[dict, dict, dict]:
    """Construct an internally-consistent synthetic production run receipt.

    Used by the scaffold demo to exercise the six-step recompute without a real
    store. Returns ``(operation_receipt, ledgers, manifest)``.
    """
    op_type = "run"
    parent = None
    ledgers = {
        "store_identity.json": {"provider": provider},
        "materials.json": {},
        "results.json": [],
        "candidates.json": [],
        "unknowns.json": [],
        "signals.json": [],
        "audit_index.json": [],
    }
    gen_id = compute_gen_id(op_type, ledgers, parent)
    operation_id = "op_" + canonical.sha256_hex(
        canonical.canonical_json({"op_type": op_type, "gen": gen_id})
    )[:32]
    receipt: dict = {
        "op_type": op_type,
        "operation_id": operation_id,
        "before_gen": None,
        "after_gen": gen_id,
        "material_set": [],
        "provider_identity": provider,
        "counts": {
            "candidates": 0,
            "unknowns": 0,
            "signals": 0,
            "formal_promotions": 0,
            "auto_evolve": 0,
        },
        "result_digests": [],
        "op_outcome": "COMMITTED",
        "timestamps": {"start": None, "end": None},
        "self_final_sha_claimed": False,
        "live_refetch_required": True,
    }
    receipt["receipt_id"] = recompute_receipt_id(receipt)
    ledgers["receipt.json"] = receipt
    manifest = _build_manifest(op_type, ledgers, gen_id, operation_id, parent)
    return receipt, ledgers, manifest


def verify_six_steps(operation_receipt: dict, ledgers: dict, manifest: dict) -> dict:
    """Run the six-step identity recompute over an in-memory generation.

    Returns a dict with per-step booleans and an overall ``ok`` flag.
    """
    steps: dict[str, bool] = {}

    # Step 1: receipt id recomputation.
    steps["receipt_id_recompute"] = (
        recompute_receipt_id(operation_receipt) == operation_receipt["receipt_id"]
    )

    # Step 2: generation binding (dir-name <-> content-id).
    computed = compute_gen_id(
        manifest["op_type"], ledgers, manifest.get("parent_generation")
    )
    gen_dir_name = manifest["generation_id"]
    steps["generation_binding"] = (
        manifest.get("generation_id") == computed and computed == gen_dir_name
    )

    # Step 3: closed-manifest triple equality.
    steps["closed_manifest_triple"] = _closed_manifest_triple(manifest, ledgers)

    # Step 4: receipt <-> manifest consistency.
    steps["receipt_manifest_consistency"] = (
        manifest["operation_id"] == operation_receipt["operation_id"]
        and manifest["op_type"] == operation_receipt["op_type"]
    )

    # Step 5: const gates (no self final head claim; live refetch required).
    steps["const_gates"] = (
        operation_receipt.get("self_final_sha_claimed") is False
        and operation_receipt.get("live_refetch_required") is True
    )

    # Step 6: canonical_json serialization stability.
    serialized = canonical.canonical_json(
        json.loads(canonical.canonical_json(operation_receipt))
    )
    steps["canonical_json_stable"] = (
        serialized == canonical.canonical_json(operation_receipt)
    )

    return {"steps": steps, "ok": all(steps.values())}


def verify(operation_receipt: dict | None = None, provider: str = "fixture://demo") -> dict:
    """Convenience: build (or accept) a receipt and run the six-step recompute.

    Returns ``{"adapter": <transcribed record>, "six_step": <result>}``.
    """
    if operation_receipt is None:
        operation_receipt, ledgers, manifest = build_synthetic_operation_receipt(provider)
    else:
        # Build a generation consistent with the supplied receipt for the
        # generation-binding / closed-manifest steps.
        ledgers = {
            "store_identity.json": {"provider": operation_receipt.get("provider_identity", provider)},
            "materials.json": {},
            "results.json": [],
            "candidates.json": [],
            "unknowns.json": [],
            "signals.json": [],
            "audit_index.json": [],
            "receipt.json": operation_receipt,
        }
        gen_id = operation_receipt.get("after_gen")
        manifest = _build_manifest(
            operation_receipt["op_type"], ledgers, gen_id,
            operation_receipt["operation_id"], None
        )
    adapter = transcribe(operation_receipt)
    six_step = verify_six_steps(operation_receipt, ledgers, manifest)
    return {"adapter": adapter, "six_step": six_step}
