"""Strict local executor census and deterministic admission selection."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import hashlib
import json
from pathlib import Path
from typing import Any


CENSUS_SCHEMA = "local-executor-census-r1"
TASK_ID = "IGNITION-20260824-138"
KINDS = {"AGENTIC_EXECUTOR", "REASONER_RUNTIME", "TOOL_ONLY", "UI_OR_NONAUTOMATABLE"}
ADMISSION_STATUSES = {"ADMITTED", "BLOCKED", "NOT_APPLICABLE"}
REQUIRED_ADMISSION_CHECKS = (
    "disposable_workspace",
    "explicit_read_only_ceiling",
    "noninteractive_one_shot",
    "structured_result",
    "public_auth_status",
    "no_new_billing",
    "timeout_and_process_cleanup",
    "no_channel_browser_side_effect",
    "independent_os_validation",
    "auth_source_separation",
)


class LocalExecutorCensusError(ValueError):
    """Raised when a census violates the executor-neutral admission contract."""


def _require(mapping: Mapping[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise LocalExecutorCensusError(f"{context} missing required key: {key}")
    return mapping[key]


def _sha(value: Any, field: str, *, optional: bool = False) -> None:
    if value is None and optional:
        return
    if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise LocalExecutorCensusError(f"{field} must be a lowercase SHA-256 digest")


def _sha40(value: Any, field: str) -> None:
    if not isinstance(value, str) or len(value) != 40 or any(char not in "0123456789abcdef" for char in value):
        raise LocalExecutorCensusError(f"{field} must be a lowercase SHA-1 object id")


def _strings(value: Any, field: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise LocalExecutorCensusError(f"{field} must be an array of non-empty strings")
    if nonempty and not value:
        raise LocalExecutorCensusError(f"{field} must not be empty")
    if len(value) != len(set(value)):
        raise LocalExecutorCensusError(f"{field} must not contain duplicates")
    return value


def _public_map(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise LocalExecutorCensusError(f"{field} must be an object")
    for key in value:
        normalized = str(key).casefold()
        if any(marker in normalized for marker in ("secret", "token", "api_key", "password", "cookie", "authorization", "credential")):
            raise LocalExecutorCensusError(f"{field} contains a secret-like key: {key}")
    return value


def admission_score(candidate: Mapping[str, Any]) -> int:
    checks = _public_map(_require(candidate, "admission_checks", "candidate"), "candidate.admission_checks")
    return sum(checks.get(key) is True for key in REQUIRED_ADMISSION_CHECKS)


def admitted_candidates(data: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    candidates = _require(data, "candidates", "census")
    if not isinstance(candidates, list):
        raise LocalExecutorCensusError("census.candidates must be an array")
    eligible = [
        item for item in candidates
        if isinstance(item, Mapping)
        and item.get("kind") == "AGENTIC_EXECUTOR"
        and item.get("installed") is True
        and item.get("admission_status") == "ADMITTED"
        and all(_public_map(item.get("admission_checks", {}), "candidate.admission_checks").get(key) is True for key in REQUIRED_ADMISSION_CHECKS)
    ]
    return sorted(eligible, key=lambda item: (-admission_score(item), str(item["family"]), str(item["executor_id"])))


def deterministic_selection(data: Mapping[str, Any]) -> dict[str, Any]:
    candidates = _require(data, "candidates", "census")
    if not isinstance(candidates, list):
        raise LocalExecutorCensusError("census.candidates must be an array")
    ranking = [
        item["executor_id"]
        for item in sorted(
            (item for item in candidates if isinstance(item, Mapping) and item.get("kind") == "AGENTIC_EXECUTOR"),
            key=lambda item: (-admission_score(item), str(item["family"]), str(item["executor_id"])),
        )
    ]
    eligible = admitted_candidates(data)
    if not eligible:
        return {
            "status": "NO_SAFE_CANDIDATE",
            "selected_executor_id": None,
            "selected_family": None,
            "ranking": ranking,
        }
    selected = eligible[0]
    return {
        "status": "SELECTED",
        "selected_executor_id": selected["executor_id"],
        "selected_family": selected["family"],
        "ranking": ranking,
    }


def validate_census(
    data: Mapping[str, Any],
    *,
    expected_task_id: str | None = None,
    expected_step: str | None = None,
) -> dict[str, Any]:
    if not isinstance(data, Mapping):
        raise LocalExecutorCensusError("census must be an object")
    required = {"schema_version", "census_id", "task_id", "step", "observed_at", "control", "formal_candidate", "scope", "candidates", "selection", "safety", "claim_ceiling"}
    if set(data) != required:
        raise LocalExecutorCensusError(f"census top-level keys must be exactly {sorted(required)}")
    task_id = TASK_ID if expected_task_id is None else expected_task_id
    step = "00" if expected_step is None else expected_step
    if data["schema_version"] != CENSUS_SCHEMA or data["task_id"] != task_id or data["step"] != step:
        raise LocalExecutorCensusError("census schema/task/step binding is invalid")
    control = _public_map(_require(data, "control", "census"), "census.control")
    if control.get("repository") != "Arvin-liu/1111" or control.get("ref") != "origin/relay/current":
        raise LocalExecutorCensusError("census control ref is not canonical")
    _sha40(control.get("tip"), "census.control.tip")
    formal = _public_map(_require(data, "formal_candidate", "census"), "census.formal_candidate")
    if formal.get("repository") != "Arvin-liu/when-systems-catch-fire":
        raise LocalExecutorCensusError("census formal repository is not canonical")
    _sha40(formal.get("sha"), "census.formal_candidate.sha")
    scope = _public_map(_require(data, "scope", "census"), "census.scope")
    for key in ("search_domains", "explicit_names", "install_sources"):
        _strings(_require(scope, key, "census.scope"), f"census.scope.{key}", nonempty=True)
    if scope.get("observation_policy") != "PATH_VERSION_HELP_PUBLIC_AUTH_PRESENCE_ONLY_NO_SECRET_NO_INFERENCE":
        raise LocalExecutorCensusError("census observation policy is too broad")

    candidates = _require(data, "candidates", "census")
    if not isinstance(candidates, list) or not candidates:
        raise LocalExecutorCensusError("census.candidates must be a non-empty array")
    seen: set[str] = set()
    for index, candidate in enumerate(candidates):
        if not isinstance(candidate, Mapping):
            raise LocalExecutorCensusError(f"candidate {index} must be an object")
        context = f"candidates[{index}]"
        executor_id = _require(candidate, "executor_id", context)
        if not isinstance(executor_id, str) or not executor_id or executor_id in seen:
            raise LocalExecutorCensusError(f"{context}.executor_id must be unique and non-empty")
        seen.add(executor_id)
        kind = _require(candidate, "kind", context)
        if kind not in KINDS:
            raise LocalExecutorCensusError(f"{context}.kind is invalid: {kind}")
        if not isinstance(_require(candidate, "installed", context), bool):
            raise LocalExecutorCensusError(f"{context}.installed must be boolean")
        _sha(_require(candidate, "binary_sha256", context), f"{context}.binary_sha256", optional=True)
        _sha(_require(candidate, "help_sha256", context), f"{context}.help_sha256", optional=True)
        _strings(_require(candidate, "install_sources", context), f"{context}.install_sources")
        auth = _public_map(_require(candidate, "auth", context), f"{context}.auth")
        for key in ("content_read", "copied", "mutated"):
            if auth.get(key) is not False:
                raise LocalExecutorCensusError(f"{context}.auth.{key} must be false")
        checks = _public_map(_require(candidate, "admission_checks", context), f"{context}.admission_checks")
        if set(checks) != set(REQUIRED_ADMISSION_CHECKS):
            raise LocalExecutorCensusError(f"{context}.admission_checks must contain exactly the admission checks")
        if any(type(value) is not bool for value in checks.values()):
            raise LocalExecutorCensusError(f"{context}.admission_checks values must be boolean")
        status = _require(candidate, "admission_status", context)
        if status not in ADMISSION_STATUSES:
            raise LocalExecutorCensusError(f"{context}.admission_status is invalid")
        if kind == "AGENTIC_EXECUTOR":
            expected = "ADMITTED" if all(checks.values()) and candidate["installed"] else "BLOCKED"
            if status != expected:
                raise LocalExecutorCensusError(f"{context}.admission_status does not match safety checks")
        elif status != "NOT_APPLICABLE":
            raise LocalExecutorCensusError(f"{context}.non-agentic candidate must be NOT_APPLICABLE")
        live = _public_map(_require(candidate, "live", context), f"{context}.live")
        if live.get("status") != "NOT_RUN_CENSUS" or live.get("inference_started") is not False:
            raise LocalExecutorCensusError(f"{context}.live must prove census-only observation")

    safety = _require(data, "safety", "census")
    if not isinstance(safety, Mapping):
        raise LocalExecutorCensusError("census.safety must be an object")
    for key in ("secret_content_read", "auth_content_copied", "configuration_changed", "billing_changed", "install_or_upgrade_performed", "live_inference_started", "workspace_modified"):
        if safety.get(key) is not False:
            raise LocalExecutorCensusError(f"census.safety.{key} must be false")

    selection = _public_map(_require(data, "selection", "census"), "census.selection")
    expected = deterministic_selection(data)
    for key in ("status", "selected_executor_id", "selected_family", "ranking"):
        if selection.get(key) != expected[key]:
            raise LocalExecutorCensusError(f"census.selection.{key} is not deterministic from candidates")
    if selection.get("status") == "SELECTED" and not isinstance(selection.get("why_executor"), str):
        raise LocalExecutorCensusError("selected census requires why_executor")
    if selection.get("status") == "NO_SAFE_CANDIDATE" and selection.get("selected_executor_id") is not None:
        raise LocalExecutorCensusError("no-safe-candidate selection cannot name an executor")
    _strings(selection.get("ranking"), "census.selection.ranking")
    if not isinstance(selection.get("excluded"), list):
        raise LocalExecutorCensusError("census.selection.excluded must be an array")

    return {
        "census_id": data["census_id"],
        "candidate_count": len(candidates),
        "agentic_executor_count": sum(item["kind"] == "AGENTIC_EXECUTOR" for item in candidates),
        "admitted_executor_count": len(admitted_candidates(data)),
        "selected_executor_id": selection["selected_executor_id"],
        "selection_status": selection["status"],
        "safe": True,
    }


def validate_path(
    path: Path,
    *,
    expected_task_id: str | None = None,
    expected_step: str | None = None,
) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LocalExecutorCensusError(f"cannot read census {path}: {exc}") from exc
    return validate_census(data, expected_task_id=expected_task_id, expected_step=expected_step)


__all__ = [
    "CENSUS_SCHEMA", "REQUIRED_ADMISSION_CHECKS", "LocalExecutorCensusError",
    "admission_score", "admitted_candidates", "deterministic_selection",
    "validate_census", "validate_path",
]
