"""Strict, dependency-free validation for the Step 00 executor inventory."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping


HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
STATUSES = {"AVAILABLE", "UNAVAILABLE_NOT_INSTALLED", "UNKNOWN"}
FORMAL_BASELINE_SHA = "277ea6c17883d9fe7661a92175a02c3cdfabac9d"


class InventoryValidationError(ValueError):
    """Raised when the inventory is missing a required bounded fact."""


def _require(mapping: Mapping[str, Any], key: str, context: str) -> Any:
    if key not in mapping:
        raise InventoryValidationError(f"{context} missing required key: {key}")
    return mapping[key]


def _object(value: Any, context: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise InventoryValidationError(f"{context} must be an object")
    return value


def _array(value: Any, context: str) -> list[Any]:
    if not isinstance(value, list):
        raise InventoryValidationError(f"{context} must be an array")
    return value


def _sha(value: Any, length: int, context: str) -> None:
    if not isinstance(value, str) or not (HEX40.fullmatch(value) if length == 40 else HEX64.fullmatch(value)):
        raise InventoryValidationError(f"{context} must be a lowercase sha{length * 4} value")


def validate_inventory(data: Mapping[str, Any]) -> dict[str, Any]:
    """Validate the inventory and return a small deterministic summary."""

    if not isinstance(data, Mapping):
        raise InventoryValidationError("inventory must be an object")
    required = {
        "schema_version", "inventory_id", "task_id", "accessed_at", "formal_baseline",
        "repository_audit", "executors", "official_sources", "safety_notes",
    }
    if set(data) != required:
        raise InventoryValidationError(f"top-level keys must be exactly {sorted(required)}")
    if data["schema_version"] != "executor-inventory-r1":
        raise InventoryValidationError("unsupported inventory schema")
    if data["task_id"] != "IGNITION-20260816-122":
        raise InventoryValidationError("inventory task_id is not IGNITION-20260816-122")

    baseline = _object(data["formal_baseline"], "formal_baseline")
    if _require(baseline, "repository", "formal_baseline") != "Arvin-liu/when-systems-catch-fire":
        raise InventoryValidationError("formal_baseline.repository is not canonical")
    origin_main_sha = _require(baseline, "origin_main_sha", "formal_baseline")
    _sha(origin_main_sha, 40, "formal_baseline.origin_main_sha")
    if origin_main_sha != FORMAL_BASELINE_SHA:
        raise InventoryValidationError(
            "formal_baseline.origin_main_sha must match the execution-time verified Task 121 main tip"
        )
    for key in ("task_branch", "worktree"):
        if not isinstance(_require(baseline, key, "formal_baseline"), str) or not baseline[key]:
            raise InventoryValidationError(f"formal_baseline.{key} must be non-empty")
    for key in ("clean", "main_divergence"):
        if not isinstance(_require(baseline, key, "formal_baseline"), bool):
            raise InventoryValidationError(f"formal_baseline.{key} must be boolean")

    audit = _object(data["repository_audit"], "repository_audit")
    for key in ("prior_task", "components", "reference_executor", "surfaces", "generator_state", "residuals"):
        _require(audit, key, "repository_audit")
    if not all(isinstance(item, str) and item for item in _array(audit["residuals"], "repository_audit.residuals")):
        raise InventoryValidationError("repository_audit.residuals must contain non-empty strings")

    executors = _array(data["executors"], "executors")
    if len(executors) < 3:
        raise InventoryValidationError("inventory must include OpenClaw, Hermes and Codex observations")
    seen: set[str] = set()
    for index, raw in enumerate(executors):
        executor = _object(raw, f"executors[{index}]")
        executor_id = _require(executor, "executor_id", f"executors[{index}]")
        if not isinstance(executor_id, str) or not executor_id or executor_id in seen:
            raise InventoryValidationError(f"executors[{index}].executor_id must be unique and non-empty")
        seen.add(executor_id)
        status = _require(executor, "status", f"executors[{index}]")
        if status not in STATUSES:
            raise InventoryValidationError(f"executors[{index}].status is invalid: {status}")
        for key in ("binary_path", "version", "help_surface", "help_sha256", "transport_kinds", "interfaces", "config_presence", "live_smoke"):
            _require(executor, key, f"executors[{index}]")
        if status == "AVAILABLE":
            for key in ("binary_path", "version", "help_surface", "help_sha256"):
                if not isinstance(executor[key], str) or not executor[key]:
                    raise InventoryValidationError(f"available executor {executor_id} requires {key}")
            _sha(executor["help_sha256"], 64, f"executors[{index}].help_sha256")
        if not isinstance(executor["transport_kinds"], list) or not executor["transport_kinds"]:
            raise InventoryValidationError(f"executors[{index}].transport_kinds must be non-empty")
        if not isinstance(executor["interfaces"], Mapping):
            raise InventoryValidationError(f"executors[{index}].interfaces must be an object")
        if not isinstance(executor["config_presence"], Mapping):
            raise InventoryValidationError(f"executors[{index}].config_presence must be an object")
        smoke = _object(executor["live_smoke"], f"executors[{index}].live_smoke")
        if _require(smoke, "status", f"executors[{index}].live_smoke") != "NOT_RUN_STEP_00":
            raise InventoryValidationError("Step 00 must not run a live executor smoke")

    sources = _array(data["official_sources"], "official_sources")
    if len(sources) < 4:
        raise InventoryValidationError("official_sources must cover three repositories and Codex documentation")
    for index, raw in enumerate(sources):
        source = _object(raw, f"official_sources[{index}]")
        for key in ("source_id", "project", "url", "source_type", "observed_ref", "commit", "accessed_at", "notes"):
            _require(source, key, f"official_sources[{index}]")
        _sha(source["commit"], 40, f"official_sources[{index}].commit")

    safety = _object(data["safety_notes"], "safety_notes")
    for key in ("secret_content_read", "external_configuration_changed", "install_or_upgrade_performed", "live_smoke_performed"):
        if _require(safety, key, "safety_notes") is not False:
            raise InventoryValidationError(f"safety_notes.{key} must be false")

    return {
        "inventory_id": data["inventory_id"],
        "executor_count": len(executors),
        "available_executors": sorted(item["executor_id"] for item in executors if item["status"] == "AVAILABLE"),
        "official_source_count": len(sources),
        "safe": True,
    }


def validate_path(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InventoryValidationError(f"cannot read JSON inventory {path}: {exc}") from exc
    return validate_inventory(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", type=Path, default=Path("data/agent-federation/executor-inventory-r1.json"))
    args = parser.parse_args(argv)
    try:
        summary = validate_path(args.path)
    except InventoryValidationError as exc:
        parser.error(str(exc))
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
