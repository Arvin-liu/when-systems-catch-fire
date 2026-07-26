# SPDX-License-Identifier: LicenseRef-BUSL-1.1-PointFire
"""Closed-set registries for the R5-A Life Integrity Charter Candidate.

This module is pure data plus membership / forbidden-transition helpers. It
contains NO runtime activation logic and raises no second-executor risk: it
only enumerates the exact closed sets that the R5-A contract mandates and
provides fail-closed predicates over them.

R5-A status: CANDIDATE_ONLY. Nothing here activates a charter, an executor, a
human-intervention path, a medical claim, the Modern Wuzhen domain pack, or a
federation runtime. See docs/governance/life-integrity-charter-candidate-r1.md.
"""

from __future__ import annotations

# --- Task / control identity (read-only constants) -------------------------
SCHEMA_VERSION = "r5a/v1.2-consolidated-contract-repair"
TASK_ID = "IGNITION-R5A-LIFE-INTEGRITY-CHARTER-CANDIDATE-R1-RELAY-20260725"
CONTROL_COMMIT = "d653c07ed6b108c98e16d111c014f87d7c7987f2"
FORMAL_PREDECESSOR = "f236543dadcaf79ba9dba750fa21bd8b5c65a33a"
CANDIDATE_FROZEN_HEAD = "0e9d1e5823b41b7e9375e5f634388371b9b024ac"

# --- Charter hierarchy (Life Community Value Charter remains supreme) ------
SUPREME_CHARTER = "LifeCommunityValueCharter"
CHARTER_HIERARCHY = (
    "LifeCommunityValueCharter",
    "LifeIntegrityAnnexCandidate",
    "LifeIntegrityGateCandidate",
    "FutureDomainPracticeProtocols",
)

# --- Embodied-agent view closed set (exactly seven) -------------------------
EMBODIED_VIEW_IDS = (
    "PhysiologicalView",
    "PhenomenologicalView",
    "CognitiveAffectiveView",
    "BehavioralView",
    "RelationalView",
    "EnvironmentalView",
    "MeaningView",
)

# --- Traditional / religious material claim-class closed set (exactly 8) ----
TRADITION_CLAIM_CLASS_IDS = (
    "HISTORICAL_SOURCE",
    "NORMATIVE_CLAIM",
    "METAPHYSICAL_CLAIM",
    "PHENOMENOLOGICAL_REPORT",
    "PRACTICE_PROTOCOL",
    "MECHANISM_HYPOTHESIS",
    "RITUAL_SOCIAL_TECHNOLOGY",
    "OUTCOME_OR_HARM_REPORT",
)

# --- Concept-mapping lifecycle closed set (exactly 8) -----------------------
CONCEPT_MAPPING_STATE_IDS = (
    "UNMAPPED",
    "SYMBOLIC_DESCRIPTION",
    "PHENOMENOLOGICAL_CANDIDATE",
    "PRACTICE_FUNCTION_CANDIDATE",
    "MECHANISM_HYPOTHESIS",
    "PARTIALLY_SUPPORTED",
    "CONTRADICTED",
    "UNKNOWN",
)

# --- Normative / empirical type-tag closed set (exactly 10) -----------------
# Every public artifact must explicitly tag content with one of these so that
# USER_AUTHORIZED_NORMATIVE_PRINCIPLE, HISTORICAL_SOURCE, AUTHOR_INTENT_CANDIDATE,
# LATER_INTERPRETATION, METAPHYSICAL_CLAIM, PHENOMENOLOGICAL_REPORT,
# PRACTICE_PROTOCOL, MECHANISM_HYPOTHESIS, EMPIRICALLY_SUPPORTED_MECHANISM and
# OUTCOME_OR_HARM_REPORT are never silently conflated.
NORMATIVE_EMPIRICAL_TYPE_TAGS = (
    "USER_AUTHORIZED_NORMATIVE_PRINCIPLE",
    "HISTORICAL_SOURCE",
    "AUTHOR_INTENT_CANDIDATE",
    "LATER_INTERPRETATION",
    "METAPHYSICAL_CLAIM",
    "PHENOMENOLOGICAL_REPORT",
    "PRACTICE_PROTOCOL",
    "MECHANISM_HYPOTHESIS",
    "EMPIRICALLY_SUPPORTED_MECHANISM",
    "OUTCOME_OR_HARM_REPORT",
)

# --- Forbidden tradition claim-class upgrades (fail-closed) -----------------
# A translated claim may NEVER silently upgrade across these boundaries without
# separately linked empirical evidence and independent review. Ordered pairs.
TRADITION_FORBIDDEN_TRANSITIONS = frozenset(
    {
        ("PHENOMENOLOGICAL_REPORT", "EMPIRICALLY_SUPPORTED_MECHANISM"),
        ("METAPHYSICAL_CLAIM", "SCIENTIFIC_FACT"),
        ("PRACTICE_PROTOCOL", "CLINICAL_EFFICACY"),
        ("LATER_INTERPRETATION", "AUTHOR_INTENT"),
        ("HISTORICAL_LONGEVITY", "EFFECTIVENESS"),
    }
)

TRADITION_UPGRADE_SOURCE_IDS = frozenset(
    set(TRADITION_CLAIM_CLASS_IDS)
    | {"LATER_INTERPRETATION", "HISTORICAL_LONGEVITY"}
)

TRADITION_MECHANISM_STATUS_IDS = (
    "NOT_ASSERTED",
    "MECHANISM_HYPOTHESIS",
    "EMPIRICALLY_SUPPORTED_MECHANISM",
    "SCIENTIFIC_FACT",
    "CLINICAL_EFFICACY",
    "EFFECTIVENESS",
)

TRADITION_INTERPRETATION_LAYER_IDS = (
    "SOURCE_LITERAL",
    "AUTHOR_INTENT_CANDIDATE",
    "LATER_INTERPRETATION",
    "MODERN_RECONSTRUCTION",
)

# Bounded aliases are fail-closed normalization targets.  This closes the
# concrete queue bypasses without claiming universal semantic understanding.
TRADITION_RISKY_TARGET_ALIASES = {
    "SCIENTIFICALLY_PROVEN": "SCIENTIFIC_FACT",
    "PROVEN_BY_SCIENCE": "SCIENTIFIC_FACT",
    "CLINICALLY_PROVEN": "CLINICAL_EFFICACY",
    "PROVEN_EFFECTIVE": "EFFECTIVENESS",
    "古人已证明是科学": "SCIENTIFIC_FACT",
}

# --- Concept-mapping allowed transition graph -------------------------------
# Each source state maps to allowed target states. The metadata records the
# required evidence class, reviewer role, reversibility and contradiction
# handling. UNKNOWN and CONTRADICTED remain first-class reachable outcomes from
# any state. Direct jumps UNMAPPED/SYMBOLIC_DESCRIPTION -> PARTIALLY_SUPPORTED
# are intentionally ABSENT (forbidden).
CONCEPT_MAPPING_TRANSITIONS: dict[str, dict[str, dict[str, object]]] = {
    "UNMAPPED": {
        "SYMBOLIC_DESCRIPTION": {
            "required_evidence_class": "source_identification",
            "reviewer_role": "C",
            "reversible": True,
            "contradiction_handling": "none_yet",
        },
    },
    "SYMBOLIC_DESCRIPTION": {
        "PHENOMENOLOGICAL_CANDIDATE": {
            "required_evidence_class": "phenomenology_report",
            "reviewer_role": "D",
            "reversible": True,
            "contradiction_handling": "surface",
        },
        "PRACTICE_FUNCTION_CANDIDATE": {
            "required_evidence_class": "practice_function_analysis",
            "reviewer_role": "D",
            "reversible": True,
            "contradiction_handling": "surface",
        },
    },
    "PHENOMENOLOGICAL_CANDIDATE": {
        "MECHANISM_HYPOTHESIS": {
            "required_evidence_class": "mechanism_hypothesis",
            "reviewer_role": "F",
            "reversible": True,
            "contradiction_handling": "surface",
        },
    },
    "PRACTICE_FUNCTION_CANDIDATE": {
        "MECHANISM_HYPOTHESIS": {
            "required_evidence_class": "mechanism_hypothesis",
            "reviewer_role": "F",
            "reversible": True,
            "contradiction_handling": "surface",
        },
    },
    "MECHANISM_HYPOTHESIS": {
        "PARTIALLY_SUPPORTED": {
            "required_evidence_class": "empirical_support",
            "reviewer_role": "F",
            "reversible": True,
            "contradiction_handling": "surface",
        },
        "CONTRADICTED": {
            "required_evidence_class": "contradiction_evidence",
            "reviewer_role": "F",
            "reversible": True,
            "contradiction_handling": "retain",
        },
        "UNKNOWN": {
            "required_evidence_class": "insufficient_evidence",
            "reviewer_role": "F",
            "reversible": True,
            "contradiction_handling": "retain",
        },
    },
    "PARTIALLY_SUPPORTED": {
        "CONTRADICTED": {
            "required_evidence_class": "contradiction_evidence",
            "reviewer_role": "F",
            "reversible": True,
            "contradiction_handling": "retain",
        },
        "UNKNOWN": {
            "required_evidence_class": "insufficient_evidence",
            "reviewer_role": "F",
            "reversible": True,
            "contradiction_handling": "retain",
        },
    },
    # UNKNOWN and CONTRADICTED are terminal-but-first-class: they may be
    # re-opened to MECHANISM_HYPOTHESIS if new evidence arrives, but never
    # silently upgraded to PARTIALLY_SUPPORTED without the full chain.
    "CONTRADICTED": {
        "MECHANISM_HYPOTHESIS": {
            "required_evidence_class": "new_evidence",
            "reviewer_role": "F",
            "reversible": True,
            "contradiction_handling": "retain_note",
        },
        "UNKNOWN": {
            "required_evidence_class": "insufficient_evidence",
            "reviewer_role": "F",
            "reversible": True,
            "contradiction_handling": "retain",
        },
    },
    "UNKNOWN": {
        "MECHANISM_HYPOTHESIS": {
            "required_evidence_class": "new_evidence",
            "reviewer_role": "F",
            "reversible": True,
            "contradiction_handling": "retain_note",
        },
        "CONTRADICTED": {
            "required_evidence_class": "contradiction_evidence",
            "reviewer_role": "F",
            "reversible": True,
            "contradiction_handling": "retain",
        },
    },
}


# --- Pure membership / forbidden predicates (no stub, always available) -----
def is_valid_embodied_view(view_id: str) -> bool:
    return view_id in EMBODIED_VIEW_IDS


def is_valid_claim_class(claim_class: str) -> bool:
    return claim_class in TRADITION_CLAIM_CLASS_IDS


def is_valid_concept_state(state: str) -> bool:
    return state in CONCEPT_MAPPING_STATE_IDS


def is_valid_type_tag(tag: str) -> bool:
    return tag in NORMATIVE_EMPIRICAL_TYPE_TAGS


def is_forbidden_tradition_upgrade(from_status: str, to_status: str) -> bool:
    normalized_target = TRADITION_RISKY_TARGET_ALIASES.get(to_status, to_status)
    return (from_status, normalized_target) in TRADITION_FORBIDDEN_TRANSITIONS


def allowed_concept_transition(from_state: str, to_state: str) -> bool:
    if from_state == to_state:
        return True
    return to_state in CONCEPT_MAPPING_TRANSITIONS.get(from_state, {})


def is_supreme_charter(node: str) -> bool:
    return node == SUPREME_CHARTER


def charter_hierarchy_respects_supremacy() -> bool:
    """The Life Community Value Charter must be the first (supreme) node and no
    R5-A artifact may insert a competing supreme node above it."""
    return (
        CHARTER_HIERARCHY[0] == SUPREME_CHARTER
        and CHARTER_HIERARCHY.count(SUPREME_CHARTER) == 1
    )


class CharterHierarchyError(ValueError):
    """Raised when a candidate hierarchy or future protocol challenges supremacy."""


def validate_charter_hierarchy(nodes: tuple[str, ...] | list[str]) -> None:
    if tuple(nodes) != CHARTER_HIERARCHY:
        raise CharterHierarchyError(
            "candidate hierarchy must equal the closed R5-A hierarchy with "
            "LifeCommunityValueCharter as its sole supreme node"
        )


def validate_future_protocol_declaration(
    *, protocol_id: str, parent: str, claims_supremacy: bool
) -> None:
    if not isinstance(protocol_id, str) or not protocol_id.strip():
        raise CharterHierarchyError("future protocol id must be non-blank")
    if parent != "LifeIntegrityGateCandidate":
        raise CharterHierarchyError(
            "future domain/practice protocols must remain beneath LifeIntegrityGateCandidate"
        )
    if claims_supremacy:
        raise CharterHierarchyError("future protocols may not claim charter supremacy")
