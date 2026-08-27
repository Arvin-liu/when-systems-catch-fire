"""Minimal qualification state for the IGNITION-143 executor campaign."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Any


CAMPAIGN_SCHEMA = "executor-qualification-campaign-r1"
TASK_ID = "IGNITION-20260827-143"
ALLOWED_STATES = {
    "NOT_INSTALLED",
    "BLOCKED",
    "QUALIFYING",
    "LIVE_SELECTABLE",
    "ATTEMPTED",
    "VALIDATED",
    "TERMINAL_BLOCKED",
}
AGENTIC_EXECUTORS = {
    "external.codex",
    "external.gemini",
    "external.hermes",
    "external.openclaw",
    "external.github-copilot-cli",
}
TARGET_EXECUTORS = {
    "external.gemini",
    "external.hermes",
    "external.openclaw",
}


class QualificationCampaignError(ValueError):
    """Raised when qualification state is missing, ambiguous or unsafe."""


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def blocker_fingerprint(blockers: list[str]) -> str:
    if any(not isinstance(item, str) or not item.strip() for item in blockers):
        raise QualificationCampaignError("blockers must contain non-empty strings")
    if len(blockers) != len(set(blockers)):
        raise QualificationCampaignError("blockers must not contain duplicates")
    return hashlib.sha256(canonical_json(sorted(blockers))).hexdigest()


def _require(mapping: Mapping[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise QualificationCampaignError(f"{context} missing required key: {key}")
    return mapping[key]


def _strings(value: Any, field: str, *, nonempty: bool = False) -> None:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise QualificationCampaignError(f"{field} must be an array of non-empty strings")
    if nonempty and not value:
        raise QualificationCampaignError(f"{field} must not be empty")
    if len(value) != len(set(value)):
        raise QualificationCampaignError(f"{field} must not contain duplicates")


def _public_only(value: Any, field: str) -> None:
    if not isinstance(value, Mapping):
        raise QualificationCampaignError(f"{field} must be an object")
    forbidden = ("secret", "token", "api_key", "password", "cookie", "authorization", "credential", "oauth")
    for key, child in value.items():
        if any(marker in str(key).casefold() for marker in forbidden):
            raise QualificationCampaignError(f"{field} contains secret-like key: {key}")
        if isinstance(child, Mapping):
            _public_only(child, f"{field}.{key}")
        elif isinstance(child, list):
            for index, item in enumerate(child):
                if isinstance(item, Mapping):
                    _public_only(item, f"{field}.{key}[{index}]")


def validate_campaign(document: Mapping[str, Any], *, expected_task_id: str = TASK_ID) -> dict[str, Any]:
    if not isinstance(document, Mapping):
        raise QualificationCampaignError("campaign must be an object")
    required = {
        "schema_version", "campaign_id", "task_id", "campaign_status", "qualification_scope",
        "policy", "families", "safety", "evidence_refs", "claim_ceiling",
    }
    if set(document) != required:
        raise QualificationCampaignError(f"campaign top-level keys must be exactly {sorted(required)}")
    if document["schema_version"] != CAMPAIGN_SCHEMA or document["task_id"] != expected_task_id:
        raise QualificationCampaignError("campaign schema/task binding is invalid")
    if document["campaign_status"] not in {"QUALIFICATION_OPEN", "LIVE_EXECUTION_IN_PROGRESS", "TERMINAL"}:
        raise QualificationCampaignError("campaign_status is invalid")
    _strings(document["qualification_scope"], "campaign.qualification_scope", nonempty=True)
    policy = _require(document, "policy", "campaign")
    _public_only(policy, "campaign.policy")
    if policy.get("max_families") != 3 or policy.get("max_attempts_per_family") != 1:
        raise QualificationCampaignError("campaign attempt policy must be three families and one attempt per family")
    if policy.get("stop_on_first_validated_completion") is not True:
        raise QualificationCampaignError("campaign must stop on first validated completion")
    if policy.get("no_blind_retry") is not True or policy.get("codex_same_family_retry") != "FORBIDDEN_UNLESS_NEW_ROOT_CAUSE_EVIDENCE":
        raise QualificationCampaignError("campaign no-blind-retry policy is incomplete")
    families = _require(document, "families", "campaign")
    if not isinstance(families, list) or not families:
        raise QualificationCampaignError("campaign.families must be a non-empty array")
    seen: set[str] = set()
    qualifying_targets = 0
    for index, family in enumerate(families):
        context = f"campaign.families[{index}]"
        if not isinstance(family, Mapping):
            raise QualificationCampaignError(f"{context} must be an object")
        _public_only(family, context)
        executor_id = _require(family, "executor_id", context)
        if executor_id in seen or executor_id not in AGENTIC_EXECUTORS:
            raise QualificationCampaignError(f"{context}.executor_id is duplicate or outside Agentic Executor scope")
        seen.add(executor_id)
        state = _require(family, "state", context)
        if state not in ALLOWED_STATES:
            raise QualificationCampaignError(f"{context}.state is invalid")
        installed = _require(family, "installed", context)
        if not isinstance(installed, bool):
            raise QualificationCampaignError(f"{context}.installed must be boolean")
        blockers = _require(family, "blockers", context)
        _strings(blockers, f"{context}.blockers")
        if family.get("blocker_fingerprint") != blocker_fingerprint(blockers):
            raise QualificationCampaignError(f"{context}.blocker_fingerprint does not match blockers")
        evidence_refs = _require(family, "evidence_refs", context)
        _strings(evidence_refs, f"{context}.evidence_refs", nonempty=True)
        attempt_count = _require(family, "attempt_count", context)
        if type(attempt_count) is not int or not 0 <= attempt_count <= 1:
            raise QualificationCampaignError(f"{context}.attempt_count must be 0 or 1")
        if state == "NOT_INSTALLED" and installed:
            raise QualificationCampaignError(f"{context} cannot be NOT_INSTALLED when installed")
        if state in {"LIVE_SELECTABLE", "ATTEMPTED", "VALIDATED"} and blockers:
            raise QualificationCampaignError(f"{context} cannot be selectable/attempted/validated with blockers")
        if state == "VALIDATED" and attempt_count != 1:
            raise QualificationCampaignError(f"{context} validated state requires one attempt")
        if executor_id in TARGET_EXECUTORS and state == "QUALIFYING":
            qualifying_targets += 1
        if executor_id == "external.codex" and state != "TERMINAL_BLOCKED":
            raise QualificationCampaignError("Codex must remain terminally blocked in the initial campaign ledger")
    if not TARGET_EXECUTORS.issubset(seen):
        raise QualificationCampaignError("campaign must include all three target families")
    safety = _require(document, "safety", "campaign")
    if not isinstance(safety, Mapping):
        raise QualificationCampaignError("campaign.safety must be an object")
    for key in (
        "secret_content_read", "auth_content_copied", "configuration_changed", "billing_changed",
        "executor_installed_or_upgraded", "live_inference_started", "channel_or_browser_used",
        "task_workspace_modified",
    ):
        if safety.get(key) is not False:
            raise QualificationCampaignError(f"campaign.safety.{key} must be false")
    _strings(document["evidence_refs"], "campaign.evidence_refs", nonempty=True)
    if not isinstance(document["claim_ceiling"], str) or not document["claim_ceiling"].strip():
        raise QualificationCampaignError("campaign.claim_ceiling must be non-empty")
    return {
        "campaign_id": document["campaign_id"],
        "family_count": len(families),
        "target_families_qualifying": qualifying_targets,
        "attempt_budget": policy["max_families"],
        "safe": True,
    }


__all__ = [
    "AGENTIC_EXECUTORS", "ALLOWED_STATES", "CAMPAIGN_SCHEMA", "QualificationCampaignError",
    "blocker_fingerprint", "canonical_json", "validate_campaign",
]
