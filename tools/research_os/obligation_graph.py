"""Claim and Evidence Obligation Graph (Checkpoint B).

Each material claim carries obligations drawn from the 12 obligation classes.
Statuses: OPEN / PARTIAL / SATISFIED / WAIVED_WITH_REASON / BLOCKED_WITH_EVIDENCE
/ NOT_APPLICABLE. A WAIVED_WITH_REASON obligation can NEVER raise a claim ceiling.
"""

from __future__ import annotations

from typing import Any

from . import kernel
from . import registries as R

VALID_CEILINGS = ["SPECULATIVE", "TENTATIVE", "QUALIFIED", "BOUNDED_STRONG", "NOT_ASSERTED"]
# Ceilings that assert a positive finding and therefore require satisfied obligations.
ASSERTIVE_CEILINGS = ["QUALIFIED", "BOUNDED_STRONG"]


def add_claim(
    ep: dict,
    claim_id: str,
    text: str,
    claim_ceiling: str,
    source_layer: str | None = None,
) -> dict:
    if claim_ceiling not in VALID_CEILINGS:
        raise ValueError(f"invalid claim_ceiling: {claim_ceiling}")
    ep.setdefault("candidate_claims", []).append(
        {
            "claim_id": claim_id,
            "text": text,
            "claim_ceiling": claim_ceiling,
            "source_layer": source_layer,
        }
    )
    kernel._append_event(ep, "diagnose", {"claim_added": claim_id}, actor="kernel")
    return ep


def add_obligation(
    ep: dict,
    obligation_id: str,
    claim_id: str,
    klass: str,
    status: str = "OPEN",
    evidence_refs: list[str] | None = None,
) -> dict:
    R.assert_obligation_class(klass)
    R.assert_status(status)
    if not any(c["claim_id"] == claim_id for c in ep.get("candidate_claims", [])):
        raise ValueError(f"obligation references unknown claim_id: {claim_id}")
    ep.setdefault("evidence_obligations", []).append(
        {
            "obligation_id": obligation_id,
            "claim_id": claim_id,
            "class": klass,
            "status": status,
            "evidence_refs": evidence_refs or [],
        }
    )
    kernel._append_event(ep, "diagnose", {"obligation_added": obligation_id}, actor="kernel")
    return ep


def set_status(
    ep: dict,
    obligation_id: str,
    status: str,
    waived_reason: str | None = None,
) -> dict:
    R.assert_status(status)
    for o in ep.get("evidence_obligations", []):
        if o["obligation_id"] == obligation_id:
            o["status"] = status
            if status == "WAIVED_WITH_REASON":
                if not waived_reason:
                    raise ValueError("WAIVED_WITH_REASON requires waived_reason")
                o["waived_reason"] = waived_reason
            return ep
    raise KeyError(f"obligation_id not found: {obligation_id}")


def obligations_for_claim(ep: dict, claim_id: str) -> list[dict]:
    return [o for o in ep.get("evidence_obligations", []) if o["claim_id"] == claim_id]


def open_obligations(ep: dict) -> list[dict]:
    return [
        o
        for o in ep.get("evidence_obligations", [])
        if o["status"] in ("OPEN", "PARTIAL")
    ]


def unsatisfied_for_claim(ep: dict, claim_id: str) -> list[dict]:
    """Obligations that are not SATISFIED and not NOT_APPLICABLE for a claim."""
    return [
        o
        for o in obligations_for_claim(ep, claim_id)
        if o["status"] not in ("SATISFIED", "NOT_APPLICABLE")
    ]


def waiver_raises_ceiling(ep: dict, claim_id: str) -> bool:
    """Enforce the contract rule: a waiver can never raise a claim ceiling.

    Returns True if a WAIVED_WITH_REASON obligation is being used to justify an
    assertive ceiling (QUALIFIED/BOUNDED_STRONG) while other obligations remain
    unsatisfied -> this is an illegal ceiling elevation.
    """
    claim = next(
        (c for c in ep.get("candidate_claims", []) if c["claim_id"] == claim_id), None
    )
    if claim is None:
        return False
    if claim["claim_ceiling"] not in ASSERTIVE_CEILINGS:
        return False
    obs = obligations_for_claim(ep, claim_id)
    has_waiver = any(o["status"] == "WAIVED_WITH_REASON" for o in obs)
    still_open = any(o["status"] in ("OPEN", "PARTIAL", "BLOCKED_WITH_EVIDENCE") for o in obs)
    return has_waiver and still_open
