"""Deep Research Capability — canonical schema generator (Round 1).

Generates the machine schemas for the 13 Deep Research Capability records
defined in TASK.md Round 1 / Qwen TASK.md Round 1. The generator is the single
source of truth: never hand-edit the emitted JSON. It reuses the inherited
Research OS vocabularies (obligation classes, action codes, claim ceilings,
episode states, gate names) so the capability contracts stay consistent with
the kernel without duplicating authority.

Run from the repository root:
    python3 tools/deep_research/generate_schemas.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_DIR = REPO_ROOT / "schemas" / "deep-research"
OUT_VERSION = "deep-research/0.1"

# ---------------------------------------------------------------------------
# Pull inherited vocabularies from the Research OS kernel (fail soft if absent)
# ---------------------------------------------------------------------------
_OBLIGATION_CLASSES: list[str] = []
_ACTION_CODES: list[str] = []
_CLAIM_CEILINGS: list[str] = []
_EPISODE_STATES: list[str] = []
_GATE_NAMES: list[str] = []

try:
    sys.path.insert(0, str(REPO_ROOT / "tools"))
    from research_os import registries as R  # type: ignore

    _OBLIGATION_CLASSES = list(R.OBLIGATION_CLASS_CODES)
    _ACTION_CODES = list(R.ACTION_CODES)
    _CLAIM_CEILINGS = list(R.CLAIM_CEILING_ENUM)
    _EPISODE_STATES = list(R.STATE_CODES)
    try:
        from research_os import gates as G  # type: ignore

        _GATE_NAMES = list(G.GATE_NAMES)
    except Exception:
        _GATE_NAMES = []
except Exception:
    # Fallback vocabularies (must match data/research-os/*.json)
    _OBLIGATION_CLASSES = [
        "PRIMARY_SOURCE", "FULL_TEXT_OR_METHODS_OR_SUPPLEMENT", "DATA_OR_TABLE_ACCESS",
        "NUMERIC_RECOMPUTATION", "CONSTRUCT_AND_OUTCOME_DEFINITION", "SOURCE_INDEPENDENCE_CHECK",
        "REPLICATION_NULL_CONTRADICTORY", "CAUSAL_IDENTIFICATION", "POPULATION_JURISDICTION_TIME_SCOPE",
        "MECHANISM_ALTERNATIVE", "ADVERSE_EFFECT_COST_HARMED", "EXTERNAL_HUMAN_OR_DOMAIN_REVIEW",
    ]
    _ACTION_CODES = [
        "FREEZE_OR_NARROW_QUESTION", "SEARCH_PRIMARY_SOURCE", "FETCH_FULL_TEXT", "READ_METHODS",
        "READ_SUPPLEMENT", "LOCATE_RAW_DATA", "LOCATE_ANALYSIS_CODE", "RECOMPUTE_RESULT",
        "REPRODUCE_ANALYSIS", "BUILD_DEFINITION_CROSSWALK", "CHECK_SOURCE_DEPENDENCE", "SEEK_REPLICATION",
        "SEEK_NULL_OR_CONTRADICTORY_RESULT", "SEEK_METHODOLOGICAL_CRITIQUE", "COMPARE_POPULATIONS_OR_JURISDICTIONS",
        "COMPARE_OUTCOMES_OR_DENOMINATORS", "TEST_ALTERNATIVE_MECHANISM", "RUN_ADVERSARIAL_REVIEW",
        "DOWNGRADE_CLAIM", "BRANCH_QUESTION", "PAUSE_AND_CHECKPOINT", "ESCALATE_TO_GPT_OWNER",
        "STOP_WITH_INSUFFICIENT_EVIDENCE", "PUBLISH_CANDIDATE_PACKET",
    ]
    _CLAIM_CEILINGS = ["SPECULATIVE", "TENTATIVE", "QUALIFIED", "BOUNDED_STRONG", "NOT_ASSERTED"]
    _EPISODE_STATES = [
        "INTAKE", "QUESTION_FROZEN", "EVIDENCE_GATHERING", "ANALYSIS", "CHALLENGE", "REVISION",
        "CANDIDATE_COMPLETE", "BLOCKED", "INSUFFICIENT_EVIDENCE_COMPLETE", "ESCALATED_TO_GPT_OWNER",
        "PAUSED_RESUMABLE", "REOPENED",
    ]
    _GATE_NAMES = [
        "SOURCE_PROVENANCE", "METHOD_CALCULATION", "SOURCE_DEPENDENCE", "ADVERSARIAL_CLAIM",
        "CLAIM_CEILING", "HIGH_STAKES_ESCALATION", "OWNER_GPT_ACCEPTANCE",
    ]

ACCESS_LEVELS = [
    "DISCOVERED", "OPENED", "FULL_TEXT", "METHODS_ONLY", "ABSTRACT_ONLY",
    "METADATA_ONLY", "COMPUTED", "NONE",
]
SUFFICIENCY_DECISIONS = [
    "CONTINUE_RESEARCH", "STOP_SUFFICIENT_CANDIDATE", "STOP_INSUFFICIENT_EVIDENCE",
    "PAUSE_BUDGET_RESUMABLE", "BLOCKED_WITH_EVIDENCE", "ESCALATE_GPT_OWNER",
]
OBLIGATION_STATUS = [
    "OPEN", "PARTIAL", "SATISFIED", "WAIVED_WITH_REASON",
    "BLOCKED_WITH_EVIDENCE", "NOT_APPLICABLE",
]
SEED_SOURCES = ["OWNER_SEED", "PROJECT_GAP", "PREVIOUS_BLOCKER", "TRUSTED_RECENT_SIGNAL"]
QUEUE_ITEM_STATUS = ["QUEUED", "ACTIVE", "COMPLETED", "BLOCKED", "SKIPPED"]

# Executor-neutral capability federation vocabulary (Round 1) -----------------
# Needs/actions are expressed as CAPABILITY tokens + PERMISSION scopes, NEVER as
# brand/model names. Provider/model brand names may appear ONLY as telemetry
# inside the records and must never become a required action dependency.
_CAPABILITY_TOKENS = [
    "READ_FILE", "WRITE_FILE", "RUN_SHELL", "FETCH_URL", "CALL_TOOL",
    "COMPUTE_NUMERIC", "GENERATE_TEXT", "PARSE_DOCUMENT", "RUN_TEST",
    "CLONE_REPO", "COMMIT_CHANGES", "PUSH_CHANGES", "QUERY_API",
    "EMBED_TEXT", "SEARCH_INDEX", "READ_ENV", "WRITE_ENV",
]
_PERMISSION_LEVELS = ["ALLOWED", "DENIED", "CONDITIONAL"]
# Terminal execution states reused from the CONTINUOUS-SUPERVISOR-AMENDMENT.
_EXECUTION_STOP_STATES = [
    "SUCCESS", "FAILED_WITH_EVIDENCE", "WAITING_HUMAN_APPROVAL",
    "PAUSED_BUDGET_RESUMABLE", "BLOCKED_UNRECOVERABLE",
]
_LEASE_STATUSES = ["ACTIVE", "EXPIRED", "REVOKED", "RELEASED"]


def _req(*fields: str) -> dict:
    return {"type": "object", "required": list(fields), "additionalProperties": True}


def build_schemas() -> dict[str, dict]:
    S: dict[str, dict] = {}

    # 1. ResearchTopicCandidate -------------------------------------------------
    S["research-topic-candidate"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/research-topic-candidate",
        "title": "ResearchTopicCandidate",
        "description": "A proposed research topic for the serial queue. Materiality/info-gain/risk are executor-proposed rankings; owner/GPT acceptance is separate.",
        "type": "object",
        "required": ["candidate_id", "proposed_question", "source_of_seed", "proposed_strategy_pack"],
        "additionalProperties": False,
        "properties": {
            "candidate_id": {"type": "string"},
            "proposed_question": {"type": "string", "minLength": 1},
            "proposed_scope": {"type": "object", "additionalProperties": True},
            "source_of_seed": {"type": "string", "enum": SEED_SOURCES},
            "materiality": {"type": "number", "minimum": 0, "maximum": 1},
            "expected_information_gain": {"type": "number", "minimum": 0, "maximum": 1},
            "tractability": {"type": "number", "minimum": 0, "maximum": 1},
            "access": {"type": "number", "minimum": 0, "maximum": 1},
            "freshness": {"type": "number", "minimum": 0, "maximum": 1},
            "cost": {"type": "number", "minimum": 0},
            "risk": {"type": "number", "minimum": 0, "maximum": 1},
            "diversity": {"type": "number", "minimum": 0, "maximum": 1},
            "proposed_strategy_pack": {"type": "string"},
            "status": {"type": "string", "enum": ["CANDIDATE", "SELECTED", "REJECTED"]},
            "provenance": {"type": "object", "additionalProperties": True},
        },
    }

    # 2. ResearchBrief ---------------------------------------------------------
    S["research-brief"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/research-brief",
        "title": "ResearchBrief",
        "description": "A frozen research brief. Fails closed on missing question, scope or strategy pack. Once frozen it is immutable for the episode.",
        "type": "object",
        "required": ["brief_id", "question_version", "question", "scope", "strategy_pack", "frozen"],
        "additionalProperties": False,
        "properties": {
            "brief_id": {"type": "string"},
            "question_version": {"type": "string"},
            "question": {"type": "string", "minLength": 1},
            "scope": {
                "type": "object",
                "required": ["population", "object", "timeframe", "outcomes"],
                "additionalProperties": True,
                "properties": {
                    "population": {"type": "string"},
                    "object": {"type": "string"},
                    "timeframe": {"type": "string"},
                    "outcomes": {"type": "array", "items": {"type": "string"}},
                    "prohibited_overreach": {"type": "array", "items": {"type": "string"}},
                },
            },
            "strategy_pack": {"type": "string"},
            "source_family_priorities": {"type": "array", "items": {"type": "string"}},
            "frozen": {"type": "boolean"},
            "created_at": {"type": "string"},
            "provenance": {"type": "object", "additionalProperties": True},
        },
    }

    # 3. ResearchPlan ----------------------------------------------------------
    S["research-plan"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/research-plan",
        "title": "ResearchPlan",
        "description": "Planned evidence obligations and subquestions derived from the frozen brief and strategy pack.",
        "type": "object",
        "required": ["plan_id", "brief_id", "obligations"],
        "additionalProperties": False,
        "properties": {
            "plan_id": {"type": "string"},
            "brief_id": {"type": "string"},
            "obligations": {"type": "array", "items": {"type": "object"}},
            "subquestions": {"type": "array", "items": {"type": "string"}},
            "search_strategy": {"type": "string"},
            "stop_criteria": {"type": "array", "items": {"type": "string"}},
            "created_at": {"type": "string"},
        },
    }

    # 4. EvidenceObligation ----------------------------------------------------
    S["evidence-obligation"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/evidence-obligation",
        "title": "EvidenceObligation",
        "description": "One material evidence obligation tied to a claim. obligation_class must be a valid Research OS obligation class; claim_id is mandatory (claim relation).",
        "type": "object",
        "required": ["obligation_id", "claim_id", "obligation_class", "status"],
        "additionalProperties": False,
        "properties": {
            "obligation_id": {"type": "string"},
            "claim_id": {"type": "string", "minLength": 1},
            "obligation_class": {"type": "string", "enum": _OBLIGATION_CLASSES},
            "status": {"type": "string", "enum": OBLIGATION_STATUS},
            "severity": {"type": "string", "enum": ["INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"]},
            "required_source_family": {"type": "string"},
            "satisfied_by": {"type": "array", "items": {"type": "string"}},
            "ceiling_impact": {"type": "string", "enum": _CLAIM_CEILINGS},
            "notes": {"type": "string"},
        },
    }

    # 5. SourceRecord ----------------------------------------------------------
    S["source-record"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/source-record",
        "title": "SourceRecord",
        "description": "Distinguishes source DISCOVERY, OPENING, actual inspected scope and derived inference. Fails closed: source_id + access_level required; if opened, inspected_scope required.",
        "type": "object",
        "required": ["source_id", "access_level"],
        "additionalProperties": False,
        "properties": {
            "source_id": {"type": "string", "minLength": 1},
            "kind": {"type": "string"},
            "source_family": {"type": "string"},
            "discovery_method": {"type": "string"},
            "opened": {"type": "boolean"},
            "access_level": {"type": "string", "enum": ACCESS_LEVELS},
            "inspected_scope": {"type": "string"},
            "claimed_vs_actual_scope": {"type": "object", "additionalProperties": True},
            "opened_at": {"type": ["string", "null"]},
            "independence_group": {"type": "string"},
            "trust_flags": {"type": "object", "additionalProperties": True},
            "provenance": {"type": "object", "additionalProperties": True},
        },
        "allOf": [
            {
                # `required` inside `if` ensures the rule fires ONLY when `opened`
                # is present; without it the `if` matches vacuously when `opened`
                # is absent and would wrongly demand inspected_scope.
                "if": {"required": ["opened"], "properties": {"opened": {"const": True}}},
                "then": {"required": ["inspected_scope"]},
            }
        ],
    }

    # 6. ResearchAction ---------------------------------------------------------
    S["research-action"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/research-action",
        "title": "ResearchAction",
        "description": "One bounded action from the Research OS action vocabulary. action_code must be a valid kernel action code.",
        "type": "object",
        "required": ["action_id", "action_code"],
        "additionalProperties": False,
        "properties": {
            "action_id": {"type": "string"},
            "action_code": {"type": "string", "enum": _ACTION_CODES},
            "objective": {"type": "string"},
            "inputs": {"type": "object", "additionalProperties": True},
            "expected_output": {"type": "string"},
            "prohibited_claims": {"type": "array", "items": {"type": "string"}},
            "budget": {"type": "object", "additionalProperties": True},
            "stop_condition": {"type": "string"},
        },
    }

    # 7. ExecutorObservation ---------------------------------------------------
    S["executor-observation"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/executor-observation",
        "title": "ExecutorObservation",
        "description": "Executor return under contract. Reuses the Research OS executor-return contract: required fields plus prohibition of self_approved / mark_episode_complete / claim_ceiling / owner_acceptance / round_complete. An executor may never self-approve, mark an episode/round complete, raise a claim ceiling, or assert owner acceptance.",
        "type": "object",
        "required": ["observation_id", "action_id", "observations", "source_identities", "access_level", "provenance", "timestamps"],
        "additionalProperties": False,
        "properties": {
            "observation_id": {"type": "string"},
            "action_id": {"type": "string"},
            "observations": {"type": "array", "items": {"type": ["string", "object"]}},
            "source_identities": {"type": "array", "items": {"type": "object"}},
            "access_level": {"type": "string", "enum": ACCESS_LEVELS},
            "calculation_result": {"type": ["object", "null"]},
            "errors": {"type": "array", "items": {"type": ["string", "object"]}},
            "provenance": {"type": "array", "items": {"type": "object"}},
            "timestamps": {"type": "object", "additionalProperties": True},
            "self_approved": {"type": "null"},
            "mark_episode_complete": {"type": "null"},
            "claim_ceiling": {"type": "null"},
            "owner_acceptance": {"type": "null"},
            "round_complete": {"type": "null"},
        },
        "allOf": [
            {
                "not": {
                    "anyOf": [
                        {"required": ["self_approved"]},
                        {"required": ["mark_episode_complete"]},
                        {"required": ["claim_ceiling"]},
                        {"required": ["owner_acceptance"]},
                        {"required": ["round_complete"]},
                    ]
                }
            }
        ],
    }

    # 8. ClaimEvidenceRecord ---------------------------------------------------
    S["claim-evidence-record"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/claim-evidence-record",
        "title": "ClaimEvidenceRecord",
        "description": "A material claim and its supporting evidence relation. Fails closed: claim_text + claim_ceiling + source_relations required; ceiling must be a valid Research OS ceiling.",
        "type": "object",
        "required": ["claim_id", "claim_text", "claim_ceiling", "source_relations"],
        "additionalProperties": False,
        "properties": {
            "claim_id": {"type": "string"},
            "claim_text": {"type": "string", "minLength": 1},
            "claim_ceiling": {"type": "string", "enum": _CLAIM_CEILINGS},
            "supporting_obligations": {"type": "array", "items": {"type": "string"}},
            "source_relations": {"type": "array", "items": {"type": "object"}},
            "entailed_by_source": {"type": ["boolean", "null"]},
            "faithfulness": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
            "groundedness": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
            "status": {"type": "string", "enum": ["CANDIDATE", "UNDER_REVIEW", "ACCEPTED", "REJECTED"]},
        },
    }

    # 9. ResearchTraceEvent ----------------------------------------------------
    S["research-trace-event"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/research-trace-event",
        "title": "ResearchTraceEvent",
        "description": "Append-only, SHA-256 identified event extending the Research OS kernel event log.",
        "type": "object",
        "required": ["event_id", "timestamp", "type", "actor", "payload_sha256"],
        "additionalProperties": False,
        "properties": {
            "event_id": {"type": "string"},
            "timestamp": {"type": "string"},
            "type": {"type": "string"},
            "actor": {"type": "string"},
            "payload_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "round": {"type": ["integer", "null"]},
            "phase": {"type": ["string", "null"]},
        },
    }

    # 10. ResearchSufficiencyDecision -----------------------------------------
    S["research-sufficiency-decision"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/research-sufficiency-decision",
        "title": "ResearchSufficiencyDecision",
        "description": "Transparent stopping decision. Fails closed: decision required; if STOP_SUFFICIENT_CANDIDATE, hard_gates_passed must be true.",
        "type": "object",
        "required": ["decision_id", "episode_id", "decision"],
        "additionalProperties": False,
        "properties": {
            "decision_id": {"type": "string"},
            "episode_id": {"type": "string"},
            "hard_gates_passed": {"type": "boolean"},
            "failed_hard_gates": {"type": "array", "items": {"type": "string"}},
            "sufficiency_vector": {"type": "object", "additionalProperties": True},
            "decision": {"type": "string", "enum": SUFFICIENCY_DECISIONS},
            "rationale": {"type": "string"},
            "deterministic_inputs": {"type": "boolean"},
            "model_proposed": {"type": "boolean"},
        },
        "allOf": [
            {
                # `required` inside `if` ensures this fires only when `decision`
                # is present; otherwise the `if` matches vacuously and would
                # wrongly demand hard_gates_passed=true on every decision.
                "if": {"required": ["decision"], "properties": {"decision": {"const": "STOP_SUFFICIENT_CANDIDATE"}}},
                "then": {"required": ["hard_gates_passed"], "properties": {"hard_gates_passed": {"const": True}}},
            }
        ],
    }

    # 11. ResearchEpisodeResult -----------------------------------------------
    S["research-episode-result"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/research-episode-result",
        "title": "ResearchEpisodeResult",
        "description": "Ingested result of one completed (or blocked) episode for queue continuation.",
        "type": "object",
        "required": ["result_id", "episode_id", "final_state"],
        "additionalProperties": False,
        "properties": {
            "result_id": {"type": "string"},
            "episode_id": {"type": "string"},
            "brief_id": {"type": "string"},
            "final_state": {"type": "string", "enum": _EPISODE_STATES},
            "claims": {"type": "array", "items": {"type": "object"}},
            "source_records": {"type": "array", "items": {"type": "object"}},
            "obligations_status": {"type": "object", "additionalProperties": True},
            "sufficiency_decision": {"type": "object", "additionalProperties": True},
            "report_ref": {"type": ["string", "null"]},
            "machine_trace_ref": {"type": ["string", "null"]},
            "created_at": {"type": "string"},
        },
    }

    # 12. ResearchQueueItem ----------------------------------------------------
    S["research-queue-item"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/research-queue-item",
        "title": "ResearchQueueItem",
        "description": "One queue item with optional lease (owner/expiry/idempotent claim) and resumable checkpoint commit metadata.",
        "type": "object",
        "required": ["queue_item_id", "status"],
        "additionalProperties": False,
        "properties": {
            "queue_item_id": {"type": "string"},
            "topic_candidate": {"type": "object", "additionalProperties": True},
            "brief": {"type": "object", "additionalProperties": True},
            "episode_id": {"type": ["string", "null"]},
            "lease": {
                "type": ["object", "null"],
                "additionalProperties": True,
                "properties": {
                    "owner": {"type": "string"},
                    "expiry": {"type": ["string", "null"]},
                    "claim_id": {"type": "string"},
                },
            },
            "status": {"type": "string", "enum": QUEUE_ITEM_STATUS},
            "checkpoint_commit": {"type": ["string", "null"]},
            "priority_factors": {"type": "object", "additionalProperties": True},
            "created_at": {"type": "string"},
        },
    }

    # 13. ResearchCampaign -----------------------------------------------------
    S["research-campaign"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/research-campaign",
        "title": "ResearchCampaign",
        "description": "A campaign of queue items with independent campaign-level stop conditions.",
        "type": "object",
        "required": ["campaign_id", "stop_conditions"],
        "additionalProperties": False,
        "properties": {
            "campaign_id": {"type": "string"},
            "items": {"type": "array", "items": {"type": "object"}},
            "stop_conditions": {
                "type": "object",
                "properties": {
                    "deadline": {"type": ["string", "null"]},
                    "max_episodes": {"type": ["integer", "null"]},
                    "max_attempts": {"type": ["integer", "null"]},
                    "budget": {"type": ["number", "null"]},
                    "queue_empty_stops": {"type": "boolean"},
                    "owner_stop": {"type": "boolean"},
                    "low_information_stops": {"type": "boolean"},
                    "safety_blocker_stops": {"type": "boolean"},
                },
                "additionalProperties": True,
            },
            "status": {"type": "string", "enum": ["RUNNING", "STOPPED", "PAUSED"]},
            "created_at": {"type": "string"},
        },
    }

    # 14. ExecutorCapabilityDeclaration --------------------------------------
    S["executor-capability-declaration"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/executor-capability-declaration",
        "title": "ExecutorCapabilityDeclaration",
        "description": "Neutral declaration of what an executor is capable of, expressed ONLY via capability tokens + permission scopes. Provider/model brand names may appear ONLY as telemetry and must never become a required action dependency.",
        "type": "object",
        "required": ["declaration_id", "executor_id", "declared_capabilities"],
        "additionalProperties": False,
        "properties": {
            "declaration_id": {"type": "string"},
            "executor_id": {"type": "string"},
            "declared_capabilities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["capability", "permission"],
                    "additionalProperties": False,
                    "properties": {
                        "capability": {"type": "string", "enum": _CAPABILITY_TOKENS},
                        "scope": {"type": "string"},
                        "permission": {"type": "string", "enum": _PERMISSION_LEVELS},
                        "conditions": {"type": "object", "additionalProperties": True},
                    },
                },
            },
            "capability_proof": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
            "model_telemetry": {"type": "object", "additionalProperties": True},
            "provider_telemetry": {"type": "object", "additionalProperties": True},
            "declared_at": {"type": ["string", "null"]},
            "expires_at": {"type": ["string", "null"]},
            # Prohibited: a brand name can never become a required capability dependency.
            "required_provider": {"type": "null"},
            "required_model": {"type": "null"},
        },
        "allOf": [
            {
                "not": {
                    "anyOf": [
                        {"required": ["required_provider"]},
                        {"required": ["required_model"]},
                    ]
                }
            }
        ],
    }

    # 15. ExecutionPacket ----------------------------------------------------
    S["execution-packet"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/execution-packet",
        "title": "ExecutionPacket",
        "description": "Immutable, self-contained instruction set handed to an executor. Uses precise refs/hashes, capability-based permissions, and declares allowed reads/writes/network, output schema, validation commands, stop states and forbidden actions. No brand-name requirement.",
        "type": "object",
        "required": [
            "packet_id", "episode_id", "target_ref", "target_ref_sha256",
            "allowed_reads", "allowed_writes", "allowed_network",
            "validation_commands", "stop_states", "forbidden_actions",
        ],
        "additionalProperties": False,
        "properties": {
            "packet_id": {"type": "string"},
            "episode_id": {"type": "string"},
            "target_repo": {"type": "string"},
            "target_ref": {"type": "string"},
            "target_ref_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "requested_capabilities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["capability"],
                    "additionalProperties": False,
                    "properties": {
                        "capability": {"type": "string", "enum": _CAPABILITY_TOKENS},
                        "scope": {"type": "string"},
                        "permission": {"type": "string", "enum": _PERMISSION_LEVELS},
                    },
                },
            },
            "allowed_reads": {"type": "array", "items": {"type": "string"}},
            "allowed_writes": {"type": "array", "items": {"type": "string"}},
            "allowed_network": {"type": "array", "items": {"type": "string"}},
            "output_schema_ref": {"type": ["string", "null"]},
            "validation_commands": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["command"],
                    "additionalProperties": False,
                    "properties": {
                        "command": {"type": "string"},
                        "expected_exit_code": {"type": "integer"},
                        "timeout_seconds": {"type": "number"},
                    },
                },
            },
            "stop_states": {"type": "array", "items": {"type": "string", "enum": _EXECUTION_STOP_STATES}},
            "forbidden_actions": {"type": "array", "items": {"type": "string"}},
            "model_telemetry_hint": {"type": "object", "additionalProperties": True},
            "created_at": {"type": ["string", "null"]},
            # Prohibited: the packet must not require a specific brand/model.
            "required_provider": {"type": "null"},
            "required_model": {"type": "null"},
        },
        "allOf": [
            {
                "not": {
                    "anyOf": [
                        {"required": ["required_provider"]},
                        {"required": ["required_model"]},
                    ]
                }
            }
        ],
    }

    # 16. ExecutionLease -----------------------------------------------------
    S["execution-lease"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/execution-lease",
        "title": "ExecutionLease",
        "description": "Idempotent claim over an execution slot. Reuses the queue-item lease concept (owner/expiry/claim_id) and binds a granted capability set to a specific executor_id. Fails closed on owner + claim_id.",
        "type": "object",
        "required": ["lease_id", "owner", "claim_id"],
        "additionalProperties": False,
        "properties": {
            "lease_id": {"type": "string"},
            "owner": {"type": "string"},
            "claim_id": {"type": "string"},
            "executor_id": {"type": ["string", "null"]},
            "expiry": {"type": ["string", "null"]},
            "granted_capabilities": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["capability", "permission"],
                    "additionalProperties": False,
                    "properties": {
                        "capability": {"type": "string", "enum": _CAPABILITY_TOKENS},
                        "scope": {"type": "string"},
                        "permission": {"type": "string", "enum": _PERMISSION_LEVELS},
                    },
                },
            },
            "status": {"type": "string", "enum": _LEASE_STATUSES},
            "granted_at": {"type": ["string", "null"]},
            "revoked": {"type": "boolean"},
        },
    }

    # 17. ApprovalRequest ----------------------------------------------------
    S["approval-request"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/approval-request",
        "title": "ApprovalRequest",
        "description": "Executor-raised request for an owner/GPT decision. The executor may NOT self-approve and may NOT pre-fill the decision; brand names cannot be a required dependency.",
        "type": "object",
        "required": ["request_id", "episode_id", "requested_by", "action_code", "reason"],
        "additionalProperties": False,
        "properties": {
            "request_id": {"type": "string"},
            "episode_id": {"type": "string"},
            "requested_by": {"type": "string"},
            "action_code": {"type": "string", "enum": _ACTION_CODES},
            "reason": {"type": "string", "minLength": 1},
            "requested_capabilities": {
                "type": "array",
                "items": {"type": "string", "enum": _CAPABILITY_TOKENS},
            },
            "raised_at": {"type": ["string", "null"]},
            "urgency": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "BLOCKING"]},
            "context_refs": {"type": "array", "items": {"type": "string"}},
            # Prohibited: executor must not self-approve or pre-fill the decision.
            "self_approved": {"type": "null"},
            "decision": {"type": "null"},
            "required_provider": {"type": "null"},
            "required_model": {"type": "null"},
        },
        "allOf": [
            {
                "not": {
                    "anyOf": [
                        {"required": ["self_approved"]},
                        {"required": ["decision"]},
                        {"required": ["required_provider"]},
                        {"required": ["required_model"]},
                    ]
                }
            }
        ],
    }

    # 18. ExecutionCheckpoint ------------------------------------------------
    S["execution-checkpoint"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/execution-checkpoint",
        "title": "ExecutionCheckpoint",
        "description": "Resumable progress checkpoint recording completed/pending steps and the precise state ref. Fails closed on episode_id + state_ref + state_ref_sha256.",
        "type": "object",
        "required": ["checkpoint_id", "episode_id", "state_ref", "state_ref_sha256"],
        "additionalProperties": False,
        "properties": {
            "checkpoint_id": {"type": "string"},
            "episode_id": {"type": "string"},
            "step_index": {"type": "integer"},
            "completed_steps": {"type": "array", "items": {"type": "string"}},
            "pending_steps": {"type": "array", "items": {"type": "string"}},
            "state_ref": {"type": "string"},
            "state_ref_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "status": {"type": "string", "enum": ["IN_PROGRESS", "PAUSED_RESUMABLE", "COMPLETED"]},
            "taken_at": {"type": ["string", "null"]},
        },
    }

    # 19. ResumeCapsule ------------------------------------------------------
    S["resume-capsule"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/resume-capsule",
        "title": "ResumeCapsule",
        "description": "Self-contained handoff so a DIFFERENT executor (with no chat history) can resume. Needs are expressed as capability tokens, not brand names; includes a precise resume-point sha256.",
        "type": "object",
        "required": [
            "capsule_id", "episode_id", "objective", "frozen_brief_ref",
            "completed_summary", "pending_tasks", "known_blockers",
            "required_capabilities", "resume_point_sha256", "validation_state",
        ],
        "additionalProperties": False,
        "properties": {
            "capsule_id": {"type": "string"},
            "episode_id": {"type": "string"},
            "objective": {"type": "string", "minLength": 1},
            "frozen_brief_ref": {"type": "string"},
            "completed_summary": {"type": "string"},
            "pending_tasks": {"type": "array", "items": {"type": "string"}},
            "known_blockers": {"type": "array", "items": {"type": "string"}},
            "required_capabilities": {
                "type": "array",
                "items": {"type": "string", "enum": _CAPABILITY_TOKENS},
            },
            "resume_point_ref": {"type": "string"},
            "resume_point_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "validation_state": {"type": "object", "additionalProperties": True},
            "model_telemetry": {"type": "object", "additionalProperties": True},
            # Prohibited: a resume handoff must not require a specific brand/model.
            "required_provider": {"type": "null"},
            "required_model": {"type": "null"},
        },
        "allOf": [
            {
                "not": {
                    "anyOf": [
                        {"required": ["required_provider"]},
                        {"required": ["required_model"]},
                    ]
                }
            }
        ],
    }

    # 20. ExecutionValidationResult ------------------------------------------
    S["execution-validation-result"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/execution-validation-result",
        "title": "ExecutionValidationResult",
        "description": "Evidence from running the packet's validation commands. The validator may NOT self-approve; model/provider are telemetry only.",
        "type": "object",
        "required": ["result_id", "packet_id", "checks", "all_passed"],
        "additionalProperties": False,
        "properties": {
            "result_id": {"type": "string"},
            "packet_id": {"type": "string"},
            "checks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["command", "exit_code", "passed"],
                    "additionalProperties": False,
                    "properties": {
                        "command": {"type": "string"},
                        "exit_code": {"type": "integer"},
                        "passed": {"type": "boolean"},
                        "output_sha256": {"type": ["string", "null"], "pattern": "^[0-9a-f]{64}$"},
                    },
                },
            },
            "all_passed": {"type": "boolean"},
            "validated_by": {"type": "string"},
            "model_telemetry": {"type": "object", "additionalProperties": True},
            "validated_at": {"type": ["string", "null"]},
            # Prohibited: validation is evidence, never self-approval.
            "self_approved": {"type": "null"},
        },
        "allOf": [
            {
                "not": {"anyOf": [{"required": ["self_approved"]}]}
            }
        ],
    }

    # 21. RuntimeTelemetry ---------------------------------------------------
    S["runtime-telemetry"] = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{OUT_VERSION}/runtime-telemetry",
        "title": "RuntimeTelemetry",
        "description": "Telemetry-only record. Model/provider names appear here as telemetry ONLY and must never be interpreted as a control input or required dependency.",
        "type": "object",
        "required": ["telemetry_id", "episode_id"],
        "additionalProperties": False,
        "properties": {
            "telemetry_id": {"type": "string"},
            "episode_id": {"type": "string"},
            "model_telemetry": {"type": "object", "additionalProperties": True},
            "provider_telemetry": {"type": "object", "additionalProperties": True},
            "duration_ms": {"type": "number"},
            "token_counts": {"type": "object", "additionalProperties": True},
            "step_count": {"type": "integer"},
            "captured_at": {"type": ["string", "null"]},
        },
    }

    return S


def write_all() -> int:
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    S = build_schemas()
    index = {"version": OUT_VERSION, "records": sorted(S.keys()), "generated_by": "tools/deep_research/generate_schemas.py"}
    for name, schema in S.items():
        with open(SCHEMA_DIR / f"{name}.schema.json", "w", encoding="utf-8") as fh:
            json.dump(schema, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
    with open(SCHEMA_DIR / "index.json", "w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return len(S)


if __name__ == "__main__":
    n = write_all()
    print(f"wrote {n} deep-research schemas to {SCHEMA_DIR}")
