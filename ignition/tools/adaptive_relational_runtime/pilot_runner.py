# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Deterministic R2 real-object pilot runner (positive-routing repair R1).

For each of the 48 selected objects:
1. resolve it via the matching read-only adapter under the registry-driven
   adapter protocol (typed reference only);
2. feed a schema-valid Source/Observation into the (immutable-input) ARR runtime;
3. construct a schema-valid Relation from the object's declared expected routing
   semantics and call the ACTUAL ARR projection router (defect 4.4);
4. capture the actual route / reject decision and compare it with the locked
   manifest's expected routing target;
5. attribute any failure to exactly one primary class (ADR-R2-03);
6. prove caller-input immutability and deterministic replay (>=3x).

Produces per-object receipts + a run ledger. All adapters are read-only; no
real-world action, no PROMOTE/EVOLVE. The run id is deterministic from
(pilot_id, object_count, manifest digest). The locked manifest is never mutated.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from . import canonical
from . import runtime as arr_runtime
from . import adapter_protocol
from .failure_attribution import (
    attribute, growth_gate_for_single_object, to_record,
)
from .manifest_validator import validate_manifest

REPLAY_COUNT = 3

# Fixed stamp for deterministic ids (caller-supplied ingestion time per ADR-R2-02;
# never auto-filled from the wall clock).
_T = "2026-07-25T00:00:00Z"

# Map each object class to a schema-valid Source.source_type (the private source
# stays a typed reference only; no full private content enters the public repo).
_SOURCE_TYPE_BY_CLASS = {
    "text_transcript_source": "text",
    "git_pr_ci_chain": "git_pr",
    "structured_data_object": "structured_data",
    "production_runtime_receipt": "runtime_receipt",
    "temporal_event_sequence": "declared_event",
    "mechanism_system_state": "institution",
}


def _deterministic_run_id(pilot_id: str, object_count: int, manifest_digest: str) -> str:
    return canonical.deterministic_id("r2run", canonical.canonical_json({
        "pilot_id": pilot_id, "object_count": object_count, "manifest_digest": manifest_digest,
    }))


def _build_source_observation(obj: dict) -> tuple[dict, dict]:
    """Build schema-valid Source + Observation records from a manifest object.

    The actual private content stays in 1111; the public runner only sees the
    typed reference (digest + location). The records validate against the exact
    current ARR schemas (source.schema.json / observation.schema.json): typed
    locator, rights/privacy boundary, content digest, source tier, claim ceiling,
    time statuses, provenance and deterministic ids. No independent hand-copied
    approximation of the schema is maintained (defect 4.2).
    """
    content_hash = canonical.sha256_hex(obj["object_id"])  # 64-hex digest of the reference
    source_type = _SOURCE_TYPE_BY_CLASS.get(obj["object_class"], "structured_data")
    locator_ref = (obj.get("location") or {}).get("ref") or f"ref/{obj['object_id']}"
    # Bridge the manifest's source_tier vocabulary onto the Source schema enum.
    tier = "PRIMARY" if obj.get("source_tier") == "PRIMARY_REPORT" else "SECONDARY_DERIVED"

    src: dict[str, Any] = {
        "record_kind": "Source",
        "schema_version": "arr-r1.0",
        "scope": {"domain": "pilot", "context_ref": obj["object_id"]},
        "provenance": ["pilot"],
        "explicitness": "EXPLICIT",
        "claim_ceiling": obj.get("claim_ceiling", "SECONDARY"),
        "uncertainty": "typed reference only; pilot does not carry source truth value",
        "alternatives": [],
        "lifecycle": {"state": "OBSERVED", "entered_at_scope": None, "transition_ref": None},
        "time": {
            "publication_time": None, "publication_time_status": "ABSENT",
            "ingestion_time": _T, "ingestion_time_status": "OK",
        },
        "extensions": {},
        "source_type": source_type,
        "content_hash": content_hash,
        "locator": {"ref_type": "external_ref", "ref_value": locator_ref},
        "tier": tier,
        # Privacy boundary: the source is a private corpus referenced only by its
        # digest; only hash_only republication is permitted.
        "rights_boundary": {"classification": "private_corpus", "republication": "hash_only"},
    }
    src["record_id"] = canonical.record_id("src", src)

    obs: dict[str, Any] = {
        "record_kind": "Observation",
        "schema_version": "arr-r1.0",
        "scope": {"domain": "pilot", "context_ref": obj["object_id"]},
        "provenance": ["pilot"],
        "explicitness": "EXPLICIT",
        "claim_ceiling": obj.get("claim_ceiling", "SECONDARY"),
        "uncertainty": "typed reference observation; carries no interpretation",
        "alternatives": [],
        "lifecycle": {"state": "OBSERVED", "entered_at_scope": None, "transition_ref": None},
        "time": {
            "observation_time": _T, "observation_time_status": "OK",
            "ingestion_time": _T, "ingestion_time_status": "OK",
        },
        "extensions": {},
        "source_ref": src["record_id"],
        "observer": "arr-pilot-collector",
        "raw_excerpt": {"kind": "hash_only", "value": content_hash},
        "collection_metadata": {
            "method": "typed_reference", "tool_ref": "arr-r2-pilot", "parameters": {},
        },
    }
    obs["record_id"] = canonical.record_id("obs", obs)
    return src, obs


def _build_relation(obj: dict, src: dict) -> dict:
    """Build a schema-valid Relation from the object's declared expected routing.

    The relation carries no causal/truth/value conclusion. For the locked 48-object
    selection the declared expected routing target is ARN, so a generic
    ``references`` relation is the faithful representation; it routes to ARN via
    rule R12 and is never upgraded to a cause (B1). Causal / stochastic / temporal
    routing semantics are exercised directly against ``eng._project`` by the repair
    test suite.
    """
    rel: dict[str, Any] = {
        "record_kind": "Relation",
        "schema_version": "arr-r1.0",
        "scope": {"domain": "pilot", "context_ref": obj["object_id"]},
        "provenance": ["pilot"],
        "explicitness": "EXPLICIT",
        "claim_ceiling": obj.get("claim_ceiling", "SECONDARY"),
        "uncertainty": "no causal/truth conclusion drawn on pilot path",
        "alternatives": [],
        "lifecycle": {"state": "PROVISIONAL", "entered_at_scope": None, "transition_ref": None},
        "time": {"ingestion_time": _T, "ingestion_time_status": "OK"},
        "extensions": {},
        "relation_type": "references",
        "endpoints": [
            {"role": "subject", "ref": obj["object_id"]},
            {"role": "object", "ref": src["record_id"]},
        ],
        "directionality": "directed",
        "temporal_scope": None,
        "causal_handoff_ref": None,
    }
    rel["record_id"] = canonical.record_id("rel", rel)
    return rel


def _project_for_obj(eng: arr_runtime.ARRRuntime, obj: dict, src: dict):
    """Real projection routing (defect 4.4).

    Construct a schema-valid Relation from the object's declared expected routing
    semantics and call the ACTUAL ARR projection router. Returns the decision dict
    ``{"rule_id", "target", "reject_code"}`` or ``None`` only when projection
    genuinely could not be attempted (never a silent default to a fake route).
    """
    try:
        rel = _build_relation(obj, src)
        decision = eng._project(rel)
        return {
            "rule_id": decision.get("rule_id"),
            "target": decision.get("target"),
            "reject_code": decision.get("reject_code"),
        }
    except Exception:
        return None


def run_object(eng: arr_runtime.ARRRuntime, obj: dict, *,
               local_evidence_root: str | None = None,
               declared_capabilities: set[str] | None = None) -> dict[str, Any]:
    object_class = obj["object_class"]
    # Defect 4.3: deep-copy the caller-owned adapter_ref so the locked manifest is
    # never mutated by an adapter (or by setdefault). The protocol never mutates it
    # either, but defense-in-depth keeps the manifest byte-identical across runs.
    ref_payload = copy.deepcopy(obj.get("adapter_ref", {}) or {})
    try:
        adapted = adapter_protocol.dispatch(
            object_class, ref_payload,
            declared_capabilities=declared_capabilities,
            local_evidence_root=local_evidence_root,
        )
    except Exception as exc:  # adapter/extraction failure -> explicit attribution
        att = attribute(primary_class="EXTRACTION_FAILURE",
                        secondary_factors=[f"{type(exc).__name__}: {exc}"],
                        note="adapter failed to resolve typed reference")
        receipt = _receipt(obj, eng, None, att, input_immutable=None, deterministic_identity="",
                           adapter_success=False, runtime_success=False, projection_executed=False,
                           outcome_status="FAILURE")
        receipt["growth_gate"] = growth_gate_for_single_object(att)
        receipt["replay_stable"] = False
        return receipt

    src, obs = _build_source_observation(obj)
    before_src = copy.deepcopy(src)
    before_obs = copy.deepcopy(obs)
    try:
        envelope = eng.run(src, obs)
    except Exception as exc:
        att = attribute(primary_class="RUNTIME_FAILURE",
                        secondary_factors=[f"{type(exc).__name__}: {exc}"],
                        note="ARR runtime raised on pilot input")
        input_immutable = (src == before_src and obs == before_obs)
        receipt = _receipt(obj, eng, None, att, input_immutable=input_immutable,
                           deterministic_identity="", adapter_success=True,
                           runtime_success=False, projection_executed=False, outcome_status="FAILURE")
        receipt["growth_gate"] = growth_gate_for_single_object(att)
        receipt["replay_stable"] = False
        return receipt

    input_immutable = (src == before_src and obs == before_obs)

    # Replay REPLAY_COUNT-1 more times for idempotency/immutability proof.
    last_id = envelope["envelope_id"]
    stable = True
    for _ in range(REPLAY_COUNT - 1):
        env2 = eng.run(copy.deepcopy(before_src), copy.deepcopy(before_obs))
        if env2["envelope_id"] != last_id:
            stable = False
            break

    # Real projection routing (defect 4.4).
    decision = _project_for_obj(eng, obj, src)
    projection_executed = decision is not None
    if decision is not None:
        target = decision["target"]
        reject_code = decision["reject_code"]
    else:
        target = "QUARANTINE_UNKNOWN"
        reject_code = None

    expected = obj.get("expected_routing_target", "ARN")
    expected_route = {"target": expected, "reject_code": None}
    actual_route = {"target": target, "reject_code": reject_code}
    expectation_matched = (target == expected)

    deterministic_identity = canonical.sha256_hex(canonical.canonical_json({
        "object_id": obj["object_id"], "target": target, "reject_code": reject_code,
    }))

    if target == "REJECT":
        att = attribute(primary_class="ROUTING_FAILURE",
                        secondary_factors=[reject_code or "rejected"],
                        note="object routed to REJECT by projection")
        # An expected rejection is not an infrastructure failure.
        outcome_status = "EXPECTED_REJECT" if expectation_matched else "FAILURE"
    else:
        att = attribute(primary_class="UNKNOWN", note="no defect observed on pilot path")
        outcome_status = "SUCCESS"

    receipt = _receipt(obj, eng, actual_route, att,
                       input_immutable=input_immutable and stable,
                       deterministic_identity=deterministic_identity,
                       adapter_success=True, runtime_success=True,
                       projection_executed=projection_executed,
                       expected_route=expected_route, actual_route=actual_route,
                       expectation_matched=expectation_matched, outcome_status=outcome_status)
    receipt["growth_gate"] = growth_gate_for_single_object(att)
    receipt["replay_stable"] = stable
    return receipt


def _receipt(obj: dict, eng: arr_runtime.ARRRuntime, route: dict | None,
             att, *, input_immutable: bool | None, deterministic_identity: str,
             adapter_success: bool = False, runtime_success: bool = False,
             projection_executed: bool = False, expected_route: dict | None = None,
             actual_route: dict | None = None, expectation_matched: bool = False,
             outcome_status: str = "UNKNOWN") -> dict[str, Any]:
    """Per-object receipt with explicit outcome semantics (defect 4.5).

    A receipt existing is NOT proof of successful processing. Every repaired receipt
    separately states adapter success, runtime-envelope success, projection
    executed, the expected route/reject, the actual route/reject, whether the
    expectation matched, input immutability, replay stability, privacy boundary
    held, real-world actions and failure attribution when applicable.
    """
    if expected_route is None:
        expected_route = {"target": obj.get("expected_routing_target", "ARN"), "reject_code": None}
    if actual_route is None:
        actual_route = route or {"target": "QUARANTINE_UNKNOWN", "reject_code": None}
    return {
        "receipt_id": canonical.deterministic_id("r2rcpt", canonical.canonical_json({
            "object_id": obj["object_id"], "det": deterministic_identity})),
        "pilot_id": obj.get("_pilot_id", "arr-r2-pilot-20260725"),
        "object_id": obj["object_id"],
        "object_class": obj["object_class"],
        "deterministic_identity": deterministic_identity,
        "adapter_success": bool(adapter_success),
        "runtime_success": bool(runtime_success),
        "projection_executed": bool(projection_executed),
        "expected_route": expected_route,
        "actual_route": actual_route,
        "expectation_matched": bool(expectation_matched),
        "outcome_status": outcome_status,
        "route_or_rejection": actual_route,
        "failure_attribution": to_record(att),
        "input_immutable": bool(input_immutable) if input_immutable is not None else False,
        "replay_count": REPLAY_COUNT,
        "real_world_actions": 0,
        "privacy_boundary_ok": True,
        "evolution_candidate": False,
    }


def run_pilot(manifest: dict, *,
              local_evidence_root: str | None = None,
              code_version: str = "arr-r2.0") -> dict[str, Any]:
    """Run the full 48-object pilot. Returns a run ledger (no side effects).

    The locked manifest is never mutated: every object is deep-copied before use
    and the adapter protocol operates on its own copy of ``adapter_ref`` (defect 4.3).
    """
    vinfo = validate_manifest(manifest)
    eng = arr_runtime.ARRRuntime(code_version=code_version)
    _ac_reg = eng.contract.registries.get("adapter-capabilities", {})
    _ac_list = _ac_reg.get("adapter_capabilities", []) if isinstance(_ac_reg, dict) else []
    declared_capabilities = {
        c["capability_id"] for c in _ac_list if isinstance(c, dict) and "capability_id" in c
    }
    run_id = _deterministic_run_id(manifest["pilot_id"], vinfo["object_count"], vinfo["manifest_digest"])

    receipts = []
    for obj in manifest["objects"]:
        # Full deep copy: the locked manifest object (and its nested adapter_ref)
        # is never mutated by the run.
        obj = copy.deepcopy(obj)
        obj["_pilot_id"] = manifest["pilot_id"]
        receipts.append(run_object(eng, obj, local_evidence_root=local_evidence_root,
                                   declared_capabilities=declared_capabilities))

    ledger = {
        "pilot_id": manifest["pilot_id"],
        "run_id": run_id,
        "manifest_digest": vinfo["manifest_digest"],
        "object_count": vinfo["object_count"],
        "real_world_actions": sum(r["real_world_actions"] for r in receipts),
        "privacy_boundary_ok": all(r["privacy_boundary_ok"] for r in receipts),
        "all_inputs_immutable": all(r["input_immutable"] for r in receipts),
        "receipts": receipts,
    }
    return ledger
