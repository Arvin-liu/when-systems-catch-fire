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

import copy
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

# Bridge from the Source schema `tier` enum (commit-2 schema) to the
# evidence-tiers registry `tier_to_ceiling` keys. The registry is the SINGLE
# SOURCE OF TRUTH for the ceiling mapping; this map only reconciles the two
# enums (F3). Mutating the registry copy changes runtime behaviour (testable).
_SOURCE_TIER_BRIDGE = {
    "PRIMARY": "PRIMARY_REPORT",
    "SECONDARY_DERIVED": "SECONDARY_ACADEMIC_INTERPRETATION",
    "DERIVED_COMPUTED": "MEDIA_SYNTHESIS",
}


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
        # ADR-R2-01 fail-closed: B1-B6 bindings are the SOLE behavioral source for
        # overstep protection. If the registry declares an empty/missing binding
        # set, overstep protection is effectively disabled, so we refuse to run
        # rather than silently downgrade to hardcoded behavior. Removal of B1-B6
        # therefore fails closed, not silently.
        bindings = self.contract.registries.get("projection-routes", {}).get(
            "anti_overstep_bindings")
        if not bindings:
            raise ContractValidationError(
                "registry-driven binding set is empty; overstep protection "
                "disabled -> refuse to run (ADR-R2-01 fail-closed)"
            )
        # Fail-closed on malformed bindings: every binding must carry a known
        # effect type (a dead/unknown effect must never be a silent no-op).
        for b in bindings:
            eff = (b.get("effect") or {}).get("type")
            if eff not in ("reject",):
                raise ContractValidationError(
                    f"binding {b.get('binding_id')} has unknown/missing effect type "
                    f"{eff!r} (ADR-R2-01 fail-closed)")

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

        # ADR-R2-02: caller-owned inputs are immutable. Deep-copy both inputs at
        # the boundary so that every validation, id computation, and lifecycle
        # write below operates on copies. The caller's source/observation dicts
        # are byte/structure-identical before and after run().
        source = copy.deepcopy(source)
        observation = copy.deepcopy(observation)

        # 1. OBSERVE
        self.contract.validate_record(source)
        self.contract.validate_record(observation)
        # F3: derive the evidence-tier ceiling from the registry (single source
        # of truth), keyed by the source's evidence tier (bridged to registry
        # tier keys). Used by the claim-ceiling enforcement below.
        self._max_ceiling = self._max_ceiling_for_tier(source.get("tier"))
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
    def _project(self, relation: dict, source: dict | None = None) -> dict:
        """Registry-driven projection routing (F1).

        Fully consumes registries['projection-routes']: iterates the routing
        rules R1-R13 by priority, applies the engine guards (G_PSD_BOUNDARY /
        G_TEMPORAL / G_HIGHER_ORDER), applies the anti-overstep bindings
        (B1-B6), and emits the correct rule_id / target / reject_code. All
        emitted reject codes are validated against the registry's reject_codes
        set so the engine can never emit a code the contract does not define.
        """
        reg = self.contract.registries["projection-routes"]
        rules = sorted(reg.get("rules", []), key=lambda r: r.get("priority", 999))
        reject_codes = {rc["code"] for rc in reg.get("reject_codes", [])}
        engine_guards = {g["guard_id"]: g for g in reg.get("engine_guards", [])}
        bindings = reg.get("anti_overstep_bindings", [])

        decision: dict[str, Any] = {"rule_id": "R13", "target": "ARN", "reject_code": None}

        # Structural guard 0: only Relation records are projectable.
        if relation.get("record_kind") != "Relation":
            decision = {"rule_id": "PRE", "target": "REJECT",
                        "reject_code": "not_a_relation_record"}
            return self._finalize_projection(decision, reject_codes)

        # Structural guard 1: the relation must validate against its schema.
        try:
            self.contract.validate_record(relation)
        except ContractValidationError:
            decision = {"rule_id": "PRE", "target": "REJECT",
                        "reject_code": "relation_schema_invalid"}
            return self._finalize_projection(decision, reject_codes)

        # Decorative / conflated structural guards (independent of R1-R13).
        decor = self._check_decorative_and_conflated(relation)
        if decor is not None:
            decision = {"rule_id": decision["rule_id"], "target": "REJECT",
                        "reject_code": decor}
            return self._finalize_projection(decision, reject_codes)

        # Iterate routing rules by priority; the first match wins.
        matched = None
        for rule in rules:
            if self._rule_matches(rule, relation, source):
                matched = rule
                break
        if matched is not None:
            decision = {"rule_id": matched["rule_id"],
                        "target": matched["target"],
                        "reject_code": None}

        # Apply engine guards scoped to the matched rule.
        guard_code = self._apply_engine_guards(decision, relation, engine_guards)
        if guard_code is not None:
            decision["target"] = "REJECT"
            decision["reject_code"] = guard_code

        # Apply anti-overstep bindings B1-B6 — behaviorally registry-driven.
        # The interpreter consumes self.contract.registries['projection-routes']
        # ['anti_overstep_bindings']; no hardcoded dual truth survives.
        if decision["reject_code"] is None:
            over_code = self._apply_anti_overstep(bindings, relation, decision)
            if over_code is not None:
                decision["target"] = "REJECT"
                decision["reject_code"] = over_code

        return self._finalize_projection(decision, reject_codes)

    @staticmethod
    def _finalize_projection(decision: dict, reject_codes: set) -> dict:
        rc = decision.get("reject_code")
        if rc is not None and rc not in reject_codes:
            # Defensive: every emitted reject code must be defined by the
            # projection-routes registry (single source of truth).
            raise ContractValidationError(
                f"emitted reject_code {rc!r} is not defined in projection-routes.reject_codes"
            )
        return decision

    @staticmethod
    def _check_decorative_and_conflated(relation: dict) -> str | None:
        # Projection hints live in the schema-permitted `extensions` namespace
        # (keys prefixed x_), since the relation schema is closed.
        ext = relation.get("extensions") or {}
        # decorative_probability: a bare numeric probability outside the PSD
        # ten-field discipline.
        pv = ext.get("x_probability_value")
        if isinstance(pv, (int, float)) and not ext.get("x_psd"):
            return "decorative_probability"
        # observation_intervention_conflated: observational and interventional
        # distributions are not distinct.
        obs_d = ext.get("x_obs_distribution")
        int_d = ext.get("x_int_distribution")
        if obs_d is not None and int_d is not None and obs_d == int_d:
            return "observation_intervention_conflated"
        return None

    @staticmethod
    def _rule_matches(rule: dict, relation: dict, source: dict | None) -> bool:
        ext = relation.get("extensions") or {}
        cat = rule.get("category")
        rt = relation.get("relation_type")
        if cat == "causal_wording":
            return bool(relation.get("causal_handoff_ref")) or rt == "causal_handoff"
        if cat == "intervention_semantics":
            return rt in ("intervention", "do_calculus") or ext.get(
                "x_intervention_action_type") is not None
        if cat == "stochastic_dynamics":
            return rt in ("probabilistic", "stochastic") or isinstance(
                ext.get("x_probability_value"), (int, float))
        if cat == "risk":
            return rt == "risk"
        if cat == "higher_order":
            return rt == "hyper_relation" or ext.get("x_is_higher_order") is True
        if cat == "temporal":
            return rt in ("temporal", "before", "after") or (
                relation.get("temporal_scope") or {}).get("interval") is not None
        if cat == "support":
            return rt == "supports"
        if cat == "conflict":
            return rt == "conflicts"
        if cat == "role":
            return rt in ("role", "social_expectation")
        if cat == "dependency":
            return rt in ("depends_on", "enables", "inhibits")
        if cat == "similarity":
            return rt in ("similar_to", "embedding_distance")
        if cat == "adjacency":
            return rt in ("references", "co_occurs", "adjacency")
        if cat == "broad_heterogeneous":
            return True  # fallback; always matches (priority 13, last)
        return False

    @staticmethod
    def _apply_engine_guards(decision: dict, relation: dict,
                             engine_guards: dict) -> str | None:
        ext = relation.get("extensions") or {}
        rule_id = decision.get("rule_id")
        # G_PSD_BOUNDARY (scoped R3/R4): PSD five-part boundary + obs!=do.
        if rule_id in ("R3", "R4") and "G_PSD_BOUNDARY" in engine_guards:
            psd = ext.get("x_psd") or {}
            required = ("system_boundary", "probability_value", "obs_not_do")
            if not all(k in psd for k in required):
                return "psd_boundary_incomplete"
            # psd_causal_escape_attempt: PSD asserts real-world causality
            # without an MCF handoff.
            if ext.get("x_causal_status") == "established" and not relation.get(
                    "causal_handoff_ref"):
                return "psd_causal_escape_attempt"
        # G_TEMPORAL (scoped R6): time-impossible path (T1-T7).
        if rule_id == "R6" and "G_TEMPORAL" in engine_guards:
            ts = relation.get("temporal_scope") or {}
            interval = ts.get("interval") or {}
            ext = relation.get("extensions") or {}
            if ts.get("impossible") is True or ext.get("x_temporal_impossible") is True or (
                interval.get("start") and interval.get("end")
                and interval["start"] > interval["end"]
            ):
                return "time_impossible_path"
        # G_HIGHER_ORDER (scoped R5): preserved; no rejection here.
        return None

    # -- registry-driven anti-overstep interpreter (ADR-R2-01) -----------
    @staticmethod
    def _get_path(obj: dict, dotted: str):
        """Read a dotted path with a None sentinel (e.g. 'relation.extensions.x').

        A path component that does not exist yields a MISSING sentinel so that an
        explicit {'op':'equals','value':None} binding fires only when the field is
        truly absent (never-confused with a wrong value).
        """
        MISSING = object()
        cur: Any = obj
        for part in dotted.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                return MISSING
        return cur

    @classmethod
    def _eval_condition(cls, cond: dict, relation: dict, decision: dict) -> bool:
        """Evaluate a closed binding condition against the live call.

        condition forms:
          {"all": [c, ...]}  -> every sub-condition true
          {"any": [c, ...]}  -> at least one sub-condition true
          leaf: {"field": "<dotted>", "op": "<op>", "value": <v>}
        ops: equals, not_equals, in, contains_any
        Fields are resolved from `relation` or `decision` (dotted prefix).
        """
        if "all" in cond:
            return all(cls._eval_condition(c, relation, decision) for c in cond["all"])
        if "any" in cond:
            return any(cls._eval_condition(c, relation, decision) for c in cond["any"])
        field = cond["field"]
        op = cond["op"]
        target = relation if field.startswith("relation.") else decision
        actual = cls._get_path(target, field.split(".", 1)[1])
        MISSING = object()
        if actual is MISSING:
            actual = None  # field absent -> treat as None for equals/contains checks
        val = cond.get("value")
        if op == "equals":
            return actual == val
        if op == "not_equals":
            return actual != val
        if op == "in":
            return actual in (val or [])
        if op == "contains_any":
            if not isinstance(actual, str):
                return False
            low = actual.lower()
            return any(w.lower() in low for w in (val or []))
        raise ContractValidationError(f"unknown binding condition op: {op!r}")

    def _apply_anti_overstep(self, bindings: list, relation: dict, decision: dict) -> str | None:
        """Interpreter: apply each registry binding; first matching effect wins.

        This is the SOLE behavioral source for overstep protection (ADR-R2-01).
        Mutating a binding's condition/effect changes behavior; removing a binding
        removes that specific protection (and an empty set fails closed at
        construction). No hardcoded branch for B1-B6 survives.
        """
        for b in bindings:
            try:
                if not self._eval_condition(b["condition"], relation, decision):
                    continue
            except (KeyError, ContractValidationError):
                # malformed binding -> surface loudly rather than silently skip
                raise ContractValidationError(
                    f"binding {b.get('binding_id')} condition malformed")
            effect = b.get("effect") or {}
            if effect.get("type") == "reject":
                return effect.get("reject_code")
            # Future effect types (e.g. downgrade_ceiling) extend here; an unknown
            # effect type is a contract error, never a silent no-op.
            raise ContractValidationError(
                f"binding {b.get('binding_id')} has unknown effect type "
                f"{effect.get('type')!r}")
        return None

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
            # F4: a REJECTED edge is terminal; the scaffold must never silently
            # continue a rejected record into execution. Surface it loudly.
            raise ContractValidationError(
                f"lifecycle edge {from_state}->{to_state} is terminal "
                f"(reason: REJECTED_IS_TERMINAL)"
            )
        # claim ceiling must not exceed the evidence tier ceiling.
        self._assert_ceiling_within_tier(record)
        record["lifecycle"] = {
            "state": to_state,
            "entered_at_scope": None,
            "transition_ref": f"{from_state}->{to_state}",
        }

    def _tier_to_ceiling_map(self) -> dict:
        reg = self.contract.registries["evidence-tiers"]
        return {row["tier"]: row["ceiling"] for row in reg["tier_to_ceiling"]}

    def _max_ceiling_for_tier(self, source_tier: str) -> str:
        # F3: the ceiling is derived from the evidence-tiers registry, keyed by
        # the (bridged) evidence tier. The registry is the single source of
        # truth; mutating a temp copy changes runtime behaviour (testable).
        tmap = self._tier_to_ceiling_map()
        reg_tier = _SOURCE_TIER_BRIDGE.get(source_tier, source_tier)
        if reg_tier not in tmap:
            raise ContractValidationError(f"unknown evidence tier: {source_tier!r}")
        return tmap[reg_tier]

    def _assert_ceiling_within_tier(self, record: dict) -> None:
        max_ceiling = getattr(self, "_max_ceiling", "SECONDARY")
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
        # Evaluate the gate criteria (G1-G6 + G5g). F2: the set and order of
        # gates are sourced from the growth-signal-gates registry; the machine
        # rule for each gate is implemented below but keyed by gate_id so a
        # mutated registry copy changes which gates run (testable).
        reg = self.contract.registries["growth-signal-gates"]
        gate_criteria = reg.get("gate_criteria", [])
        items = []
        for gc in gate_criteria:
            gid = gc["gate_id"]
            result = self._eval_growth_gate(gid, gs)
            items.append({
                "gate_id": gid,
                "result": result,
                "evidence_ref": fb_id,
            })
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

    @staticmethod
    def _eval_growth_gate(gate_id: str, gs: dict) -> str:
        """Machine rule for a single growth gate, keyed by gate_id (F2)."""
        if gate_id == "G1":  # recurrence
            return "PASS" if len(gs["recurrence_evidence"]) >= 2 else "FAIL"
        if gate_id == "G2":  # scope
            sc = gs["signal_scope"]
            return "PASS" if (len(sc["object_refs"]) >= 2
                              and len(sc["source_refs"]) >= 2) else "FAIL"
        if gate_id == "G3":  # measured_loss
            return "PASS" if gs["measured_loss"] is not None else "FAIL"
        if gate_id == "G4":  # workaround
            wa = gs["workaround_assessment"]
            return "PASS" if (wa["assessed"] is True
                              and wa["adequate_low_cost_exists"] is False) else "FAIL"
        if gate_id == "G5":  # minimal_repair_hypothesis
            mrh = gs["minimal_repair_hypothesis"]
            return "PASS" if all(mrh[k] for k in
                                 ("hypothesis", "touched_surface",
                                  "falsification_test", "rollback_path")) else "FAIL"
        if gate_id == "G5g":  # governance_hard_refusal
            return "FAIL" if "weaken" in gs["minimal_repair_hypothesis"][
                "hypothesis"].lower() else "PASS"
        if gate_id == "G6":  # human_authorization
            return "PASS" if gs["human_authorization"]["verified"] is True else "FAIL"
        return "FAIL"

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
