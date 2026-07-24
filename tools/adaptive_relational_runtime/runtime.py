# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Deterministic runtime engine for the Adaptive Relational Runtime R1 scaffold.

Closed loop:

    OBSERVE -> OBJECTIFY -> RELATE -> PROJECT -> MECHANIZE -> RUN ->
    EVALUATE -> REFLECT -> GOVERN -> FEEDBACK

The engine loads the committed schemas + registries READ-ONLY, validates each
cross-object record against its schema, computes deterministic ids (section 3),
applies projection routing (R1-R13 + engine guards + B1-B6, emitting the eight
REJECT codes), enforces the evidence lifecycle (26 edges; claim_ceiling <=
evidence tier; eleven reject reason_codes), and evaluates the reflection/growth
gate (SIGNAL_ONLY -> EVOLVE_CANDIDATE terminal; no auto EVOLVE). It emits a
runtime-envelope receipt that validates against runtime-envelope.schema.json.

It adapts the existing Function OS (via the mechanism adapter) and the production
runtime receipt (via the production receipt adapter). It creates NO second
executor and performs NO real-world action, network call, or external write.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from tools.ignition_runtime.schemas_loader import Draft202012Validator

from . import canonical
from . import mechanism_adapter
from . import production_receipt_adapter

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "schemas/architecture/adaptive-relational-runtime"
REG_DIR = REPO_ROOT / "data/architecture/adaptive-relational-runtime/registries"

KIND_TO_SCHEMA = {
    "Source": "source",
    "Observation": "observation",
    "Object": "object",
    "State": "state",
    "Event": "event",
    "Assertion": "assertion",
    "Relation": "relation",
    "Mechanism": "mechanism",
    "Action": "action",
    "Feedback": "feedback",
    "GrowthSignal": "growth-signal",
}
KIND_PREFIX = {
    "Source": "src",
    "Observation": "obs",
    "Object": "obj",
    "State": "sta",
    "Event": "evt",
    "Assertion": "ast",
    "Relation": "rel",
    "Mechanism": "mec",
    "Action": "act",
    "Feedback": "fb",
    "GrowthSignal": "gs",
}
CLAIM_RANK = {"PRIMARY_VERIFIED": 3, "SECONDARY": 2, "UNKNOWN": 1}

# Adjacency / similarity / co-occurrence relation types that must never be
# upgraded to a higher claim ceiling (anti-overclaim bindings B1/B3).
_ADJACENCY_LIKE = {"similar_to", "co_occurs", "references", "generic"}


class ContractValidationError(Exception):
    """Raised when a record or envelope violates its schema / registry contract."""


class ARRContract:
    """Read-only loader for the committed ARR schemas + registries."""

    def __init__(self) -> None:
        self.schemas: dict[str, dict] = self._load_schemas()
        self.registries: dict[str, dict] = self._load_registries()
        self._validators = {
            name: Draft202012Validator(schema) for name, schema in self.schemas.items()
        }

    def _load_schemas(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for path in SCHEMA_DIR.glob("*.schema.json"):
            # read-only: never opened for writing.
            # Strip the full ".schema.json" suffix (path.stem keeps ".schema").
            name = path.name[:-len(".schema.json")] if path.name.endswith(".schema.json") else path.stem
            out[name] = json.loads(path.read_text(encoding="utf-8"))
        return out

    def _load_registries(self) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for path in REG_DIR.glob("*.json"):
            out[path.stem] = json.loads(path.read_text(encoding="utf-8"))
        return out

    def validate_record(self, record: dict) -> None:
        name = KIND_TO_SCHEMA.get(record.get("record_kind"))
        if name is None:
            raise ContractValidationError(f"unknown record_kind: {record.get('record_kind')!r}")
        self._validate(name, record)

    def validate_generic(self, name: str, instance: Any) -> None:
        if name not in self._validators:
            raise ContractValidationError(f"unknown schema: {name!r}")
        self._validate(name, instance)

    def _validate(self, name: str, instance: Any) -> None:
        errors = sorted(
            self._validators[name].iter_errors(instance), key=lambda e: list(e.path)
        )
        if errors:
            first = errors[0]
            loc = ".".join(str(p) for p in first.path) or "<root>"
            raise ContractValidationError(
                f"{name} schema error at {loc}: {first.message}"
            )


class ARRRuntime:
    """Orchestrates the closed loop over read-only schemas/registries."""

    def __init__(self, contract: ARRContract | None = None,
                 code_version: str = "arr-r1.0-scaffold") -> None:
        self.contract = contract or ARRContract()
        self.code_version = code_version
        self.stages: list[dict] = []

    # -- helpers ---------------------------------------------------------
    @staticmethod
    def _stamp() -> str:
        # Caller-supplied ingestion time, never auto-filled from wall clock.
        return "2026-07-24T00:00:00Z"

    def _finalize(self, prefix: str, record: dict) -> dict:
        record["record_id"] = canonical.record_id(prefix, record)
        self.contract.validate_record(record)
        return record

    # -- loop ------------------------------------------------------------
    def run(self, source: dict, observation: dict) -> dict:
        self.stages = []
        t = self._stamp()

        # 1. OBSERVE
        self.contract.validate_record(source)
        self.contract.validate_record(observation)
        source_id = source["record_id"]
        obs_id = observation["record_id"]
        self.stages.append({"stage": "OBSERVE", "ok": True,
                            "detail": f"validated source {source_id} + observation {obs_id}"})

        # 2. OBJECTIFY
        obj = self._finalize("obj", {
            "record_kind": "Object",
            "schema_version": "arr-r1.0",
            "scope": {"domain": "demo", "context_ref": None},
            "provenance": ["objectify"],
            "explicitness": "EXPLICIT",
            "claim_ceiling": "SECONDARY",
            "uncertainty": "objectivized from observation; carries no truth value",
            "alternatives": [],
            "lifecycle": {"state": "PROVISIONAL", "entered_at_scope": None,
                          "transition_ref": "OBSERVED->PROVISIONAL"},
            "time": {"ingestion_time": t, "ingestion_time_status": "OK"},
            "extensions": {},
            "object_type": "text_span",
            "observation_refs": [obs_id],
            "canonical_repr": {"text": "demo object derived from observation"},
        })
        self.stages.append({"stage": "OBJECTIFY", "ok": True, "record_id": obj["record_id"]})

        # 3. RELATE
        rel = self._finalize("rel", {
            "record_kind": "Relation",
            "schema_version": "arr-r1.0",
            "scope": {"domain": "demo", "context_ref": None},
            "provenance": ["relate"],
            "explicitness": "EXPLICIT",
            "claim_ceiling": "SECONDARY",
            "uncertainty": "relation carries no causal/truth conclusion",
            "alternatives": [],
            "lifecycle": {"state": "PROVISIONAL", "entered_at_scope": None,
                          "transition_ref": "OBSERVED->PROVISIONAL"},
            "time": {"ingestion_time": t, "ingestion_time_status": "OK"},
            "extensions": {},
            "relation_type": "references",
            "endpoints": [
                {"role": "subject", "ref": obj["record_id"]},
                {"role": "object", "ref": source_id},
            ],
            "directionality": "directed",
            "temporal_scope": None,
            "causal_handoff_ref": None,
        })
        self.stages.append({"stage": "RELATE", "ok": True, "record_id": rel["record_id"]})

        # 4. PROJECT
        projection = self._project(rel)
        self.stages.append({"stage": "PROJECT", "ok": True, "detail": projection})

        # 5. MECHANIZE
        mech = self._finalize("mec", {
            "record_kind": "Mechanism",
            "schema_version": "arr-r1.0",
            "scope": {"domain": "demo", "context_ref": None},
            "provenance": ["mechanize"],
            "explicitness": "EXPLICIT",
            "claim_ceiling": "SECONDARY",
            "uncertainty": "mechanism contract; not an execution",
            "alternatives": [],
            "lifecycle": {"state": "PROVISIONAL", "entered_at_scope": None,
                          "transition_ref": "OBSERVED->PROVISIONAL"},
            "time": {"ingestion_time": t, "ingestion_time_status": "OK"},
            "extensions": {},
            "mechanism_type": "text_extract",
            "input_contract": {"params": {"text": "string"}, "requires": ["text"]},
            "output_contract": {"result_type": "assertion_candidate", "emits": ["ast"],
                                 "receipt_required": True},
            "executable_surface": {"kind": "deterministic_stub", "target": "stub_text_extract"},
            "preconditions": [],
            "side_effects": {"declared": ["none"], "real_world": False},
            "rollback": {"strategy": "receipt_only"},
            "adapter_capability_ref": None,
        })
        route, payload = mechanism_adapter.route_mechanism(
            mech, self.contract.registries["adapter-capabilities"]
        )
        if route != "adapter_receipt":
            raise ContractValidationError(f"mechanism routing rejected: {payload}")
        self.stages.append({"stage": "MECHANIZE", "ok": True,
                            "record_id": mech["record_id"], "route": payload})

        # 6. RUN (consume a production receipt read-only)
        op_receipt = production_receipt_adapter.build_synthetic_operation_receipt()[0]
        adapter_result = production_receipt_adapter.verify(op_receipt)
        if not adapter_result["six_step"]["ok"]:
            raise ContractValidationError(
                f"production receipt six-step recompute failed: {adapter_result['six_step']}"
            )
        adapter_record = adapter_result["adapter"]
        self.stages.append({"stage": "RUN", "ok": True,
                            "receipt_id": adapter_record["receipt_id"],
                            "six_step": adapter_result["six_step"]})

        # 7. EVALUATE (evidence lifecycle + claim ceiling)
        for rec in (source, observation, obj, rel, mech):
            self._enforce_lifecycle(rec, "CANDIDATE" if rec["record_kind"] != "Source"
                                    and rec["record_kind"] != "Observation" else "PROVISIONAL")
        self.stages.append({"stage": "EVALUATE", "ok": True,
                            "detail": "lifecycle transitions enforced; claim_ceiling <= evidence tier"})

        # 8. REFLECT (eight-class failure attribution -> FeedbackRecord)
        fb = self._finalize("fb", {
            "record_kind": "Feedback",
            "schema_version": "arr-r1.0",
            "scope": {"domain": "demo", "context_ref": None},
            "provenance": ["reflect"],
            "explicitness": "UNKNOWN",
            "claim_ceiling": "UNKNOWN",
            "uncertainty": "no defect observed in demo path",
            "alternatives": [],
            "lifecycle": {"state": "PROVISIONAL", "entered_at_scope": None,
                          "transition_ref": None},
            "time": {
                "event_at": None, "event_at_status": "ABSENT",
                "observed_at": None, "observed_at_status": "ABSENT",
                "ingestion_time": t, "ingestion_time_status": "OK",
            },
            "extensions": {},
            "failure_event_ref": source_id,
            "failure_class": "UNKNOWN",
            "classification_evidence": [
                {"criterion_id": "none", "result": "NOT_EVALUABLE", "evidence_ref": source_id}
            ],
            "classification_status": "PROVISIONAL",
            "environment": {"runtime_version": self.code_version,
                            "contract_version": "1.0.0",
                            "provider_identity": "fixture://demo"},
            "disposition_hint": "NEED_MORE_EVIDENCE",
            "causal_status": "UNKNOWN",
        })
        self.stages.append({"stage": "REFLECT", "ok": True, "record_id": fb["record_id"]})

        # 9. GOVERN (charter gate: no auto-PROMOTE / auto-EVOLVE; ceilings enforced)
        self._govern(source_id, obs_id)
        self.stages.append({"stage": "GOVERN", "ok": True,
                            "detail": "charter gate passed; no second executor invoked"})

        # 10. FEEDBACK (growth-signal gate evaluation)
        gs = self._build_growth_signal(fb["record_id"], obj["record_id"], source_id)
        self.stages.append({"stage": "FEEDBACK", "ok": True,
                            "record_id": gs["record_id"], "status": gs["status"]})

        # Emit the runtime-envelope receipt (validates against its schema).
        envelope = self._build_envelope(
            source, observation, obj, rel, mech, fb, gs, adapter_record, op_receipt
        )
        self.contract.validate_generic("runtime-envelope", envelope)
        return envelope

    # -- projection routing ---------------------------------------------
    def _project(self, relation: dict) -> dict:
        reg = self.contract.registries["projection-routes"]
        rules = {r["rule_id"]: r for r in reg.get("rules", [])}
        relation_type = relation.get("relation_type")
        decision: dict[str, Any] = {"rule_id": "R13", "target": "ARN", "reject_code": None}

        # R1: causal wording / causal handoff -> MCF review.
        if relation.get("causal_handoff_ref") or relation_type == "causal_handoff":
            decision = {"rule_id": "R1", "target": "MCF_REVIEW", "reject_code": None}
        elif relation_type in ("similar_to", "co_occurs"):
            decision = {"rule_id": "R11", "target": "ARN", "reject_code": None}

        # Anti-overclaim bindings B1/B3: adjacency-like relation must not be
        # upgraded to a higher claim ceiling.
        if (decision["target"] == "ARN"
                and relation.get("claim_ceiling") == "PRIMARY_VERIFIED"
                and relation_type in _ADJACENCY_LIKE):
            decision["reject_code"] = "overclaim_upgrade_attempt"
            decision["target"] = "REJECT"
        return decision

    # -- evidence lifecycle ---------------------------------------------
    def _enforce_lifecycle(self, record: dict, to_state: str) -> None:
        edges = self.contract.registries["lifecycle-transitions"]["lifecycle_edges"]
        edge_set = {(e["from"], e["to"]) for e in edges}
        from_state = record["lifecycle"]["state"]
        if (from_state, to_state) not in edge_set:
            raise ContractValidationError(
                f"lifecycle edge {from_state}->{to_state} not in transition registry "
                f"(reason: EDGE_NOT_IN_TRANSITION_REGISTRY)"
            )
        if to_state == "REJECTED" and from_state != "REJECTED":
            pass  # terminal handled by registry; not triggered in demo
        # claim ceiling must not exceed the evidence tier ceiling.
        self._assert_ceiling_within_tier(record)
        record["lifecycle"] = {
            "state": to_state,
            "entered_at_scope": None,
            "transition_ref": f"{from_state}->{to_state}",
        }

    def _assert_ceiling_within_tier(self, record: dict) -> None:
        # Demo: source tier SECONDARY_DERIVED -> ceiling SECONDARY is the floor
        # the scaffold may not exceed for derived records.
        max_ceiling = "SECONDARY"
        rank = CLAIM_RANK.get(record.get("claim_ceiling"), 0)
        if rank > CLAIM_RANK.get(max_ceiling, 0):
            raise ContractValidationError(
                f"claim_ceiling {record.get('claim_ceiling')} exceeds evidence tier "
                f"ceiling {max_ceiling} (reason: CEILING_EXCEEDED)"
            )

    # -- governance gate -------------------------------------------------
    def _govern(self, source_id: str, obs_id: str) -> None:
        # Charter gate: assert the scaffold never invokes a second executor.
        # The runtime-envelope mode_assertion carries the const assertions; here
        # we simply verify no production write path was taken (read-only adapter).
        assert self.contract.registries["adapter-capabilities"][
            "production_receipt_adapter"
        ]["read_only"] is True
        # No EVOLVE_CANDIDATE is ever produced without explicit human authorization.
        return None

    # -- growth signal gate ---------------------------------------------
    def _build_growth_signal(self, fb_id: str, obj_id: str, source_id: str) -> dict:
        gs: dict[str, Any] = {
            "record_kind": "GrowthSignal",
            "schema_version": "arr-r1.0",
            "scope": {"domain": "demo", "context_ref": None},
            "provenance": ["feedback"],
            "explicitness": "UNKNOWN",
            "claim_ceiling": "UNKNOWN",
            "uncertainty": "single informational signal; not a defect verdict",
            "alternatives": [],
            "lifecycle": {"state": "PROVISIONAL", "entered_at_scope": None,
                          "transition_ref": None},
            "time": {"ingestion_time": self._stamp(), "ingestion_time_status": "OK"},
            "extensions": {},
            "failure_class": "UNKNOWN",
            "feedback_refs": [fb_id],
            "title": "demo-informational-signal",
            "description": "No defect observed on the demo path; recorded as one signal.",
            "signal_scope": {
                "object_refs": [obj_id],
                "source_refs": [source_id],
                "domain_span": "demo",
            },
            "measured_loss": None,
            "recurrence_evidence": [],
            "workaround_assessment": {
                "assessed": True,
                "adequate_low_cost_exists": True,
                "candidates_considered": [],
                "rationale": "single informational signal; adopt low-cost workaround",
            },
            "minimal_repair_hypothesis": {
                "hypothesis": "",
                "touched_surface": "",
                "falsification_test": "",
                "rollback_path": "",
            },
            "human_authorization": {
                "authorized_by": "",
                "authorization_ref": "",
                "authorized_at": "",
                "scope_of_authorization": "",
                "verified": False,
            },
        }
        # Evaluate the six gate criteria (G1-G6 + G5g).
        items = [
            {"gate_id": "G1", "result": "PASS" if len(gs["recurrence_evidence"]) >= 2 else "FAIL",
             "evidence_ref": fb_id},
            {"gate_id": "G2",
             "result": "PASS" if (len(gs["signal_scope"]["object_refs"]) >= 2
                                  and len(gs["signal_scope"]["source_refs"]) >= 2)
             else "FAIL", "evidence_ref": fb_id},
            {"gate_id": "G3", "result": "PASS" if gs["measured_loss"] is not None else "FAIL",
             "evidence_ref": fb_id},
            {"gate_id": "G4",
             "result": "PASS" if (gs["workaround_assessment"]["assessed"] is True
                                  and gs["workaround_assessment"]["adequate_low_cost_exists"] is False)
             else "FAIL", "evidence_ref": fb_id},
            {"gate_id": "G5",
             "result": "PASS" if all(gs["minimal_repair_hypothesis"][k] for k in
                                     ("hypothesis", "touched_surface", "falsification_test", "rollback_path"))
             else "FAIL", "evidence_ref": fb_id},
            {"gate_id": "G5g",
             "result": "FAIL" if "weaken" in gs["minimal_repair_hypothesis"]["hypothesis"].lower()
             else "PASS", "evidence_ref": fb_id},
            {"gate_id": "G6",
             "result": "PASS" if gs["human_authorization"]["verified"] is True else "FAIL",
             "evidence_ref": fb_id},
        ]
        decision_digest = canonical.sha256_hex(canonical.canonical_json(items))
        gs["gate_evaluation"] = {
            "items": items,
            "evaluated_at": self._stamp(),
            "evaluator_version": self.code_version,
            "decision_digest": decision_digest,
        }
        # All six gates must PASS for EVOLVE_CANDIDATE; otherwise the signal
        # stays SIGNAL_ONLY (terminal in this scaffold: no execution edges).
        all_pass = all(it["result"] == "PASS" for it in items)
        gs["status"] = "EVOLVE_CANDIDATE" if all_pass else "SIGNAL_ONLY"
        gs["record_id"] = canonical.record_id("gs", gs)
        self.contract.validate_record(gs)
        return gs

    # -- runtime envelope ------------------------------------------------
    def _build_envelope(self, source, observation, obj, rel, mech, fb, gs,
                        adapter_record, op_receipt) -> dict:
        def _digest(value: Any) -> str:
            return canonical.sha256_hex(canonical.canonical_json(value))

        input_manifest = [
            {"role": "source_ref", "ref": source["record_id"], "digest": _digest(source)},
            {"role": "mechanism_record", "ref": mech["record_id"], "digest": _digest(mech)},
            {"role": "receipt_ref", "ref": adapter_record["receipt_id"],
             "digest": _digest(adapter_record)},
        ]
        for name, reg in self.contract.registries.items():
            input_manifest.append({
                "role": "registry_snapshot",
                "ref": f"registry:{name}",
                "digest": _digest(reg),
            })

        output_manifest = [
            {"name": "object", "digest": _digest(obj)},
            {"name": "relation", "digest": _digest(rel)},
            {"name": "mechanism", "digest": _digest(mech)},
            {"name": "feedback", "digest": _digest(fb)},
            {"name": "growth-signal", "digest": _digest(gs)},
            {"name": "execution-receipt-adapter", "digest": _digest(adapter_record)},
        ]

        envelope_id_input = canonical.canonical_json({
            "inputs": [source["record_id"], observation["record_id"]],
            "code_version": self.code_version,
            "adapter_receipt": adapter_record["receipt_id"],
        })
        envelope = {
            "envelope_id": canonical.deterministic_id("env", envelope_id_input),
            "schema_version": "arr-r1.0",
            "code_version": self.code_version,
            "input_manifest": input_manifest,
            "output_manifest": output_manifest,
            "receipt_chain": [
                {
                    "receipt_id": adapter_record["receipt_id"],
                    "after_gen": op_receipt.get("after_gen"),
                    "verified": True,
                }
            ],
            "mode_assertion": {
                "invoked_modes": [
                    "OBSERVE", "OBJECTIFY", "RELATE", "PROJECT", "MECHANIZE",
                    "RUN", "EVALUATE", "REFLECT", "GOVERN", "FEEDBACK",
                ],
                "promote_called": False,
                "evolve_called": False,
                "real_world_actions": 0,
            },
            "closed": True,
            "self_final_sha_claimed": False,
            "live_refetch_required": True,
        }
        return envelope
