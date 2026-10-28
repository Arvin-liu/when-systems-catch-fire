"""Typed, provider-neutral admission rules for the Knowledge Pack.

The generic Agent Platform may record platform provenance, but platform code is
not an implicit Knowledge source.  This module is deliberately small so the
Foundation and nonfunction builders share one path policy instead of carrying
near-identical exclusion lists.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = ROOT / "data/foundation/knowledge-corpus-admission-policy.json"


@dataclass(frozen=True)
class Admission:
    path: str
    classification: str
    auto_discovery: bool
    provenance_only: bool
    explicit: bool
    reason: str


def load_policy() -> dict:
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def _normalized(path: str) -> str:
    normalized = str(path).replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def admission_for_path(path: str) -> Admission:
    normalized = _normalized(path)
    policy = load_policy()
    explicit = normalized in set(policy.get("explicit_allowlist", []))
    selected: dict | None = None
    selected_rank = -1
    for rule in policy.get("rules", []):
        exact = normalized in set(rule.get("exact_paths", []))
        prefix = any(normalized.startswith(prefix) for prefix in rule.get("prefixes", []))
        rank = 2 if exact else 1 if prefix else -1
        if rank > selected_rank:
            selected = rule if rank >= 0 else selected
            selected_rank = rank
    classification = (selected or {}).get("classification", policy["default_classification"])
    if explicit:
        classification = "KNOWLEDGE_SOURCE_ELIGIBLE"
    class_config = policy["classes"][classification]
    auto_discovery = bool(class_config.get("auto_discovery", False))
    if classification == "KNOWLEDGE_SOURCE_EXPLICIT_ONLY" and not explicit:
        auto_discovery = False
    return Admission(
        path=normalized,
        classification=classification,
        auto_discovery=auto_discovery,
        provenance_only=bool(class_config.get("provenance_only", False)),
        explicit=explicit,
        reason=class_config["meaning"],
    )


def is_auto_discovery_allowed(path: str) -> bool:
    return admission_for_path(path).auto_discovery


def is_platform_excluded(path: str) -> bool:
    return admission_for_path(path).classification == "PLATFORM_CODE_EXCLUDED"


def policy_summary() -> dict:
    policy = load_policy()
    return {
        "policy_id": policy["policy_id"],
        "schema_version": policy["schema_version"],
        "classes": sorted(policy["classes"]),
        "explicit_allowlist": sorted(policy.get("explicit_allowlist", [])),
        "rule_count": len(policy.get("rules", [])),
    }
