#!/usr/bin/env python3
"""Fail-closed semantic projection for the historical residual ledger.

R1 remains the historical source record.  R2 may classify its unchanged
observations, but cannot shrink, expand, or rewrite the R1 fingerprints.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
R1_PATH = ROOT / "data/operations/residual-ledger-r1.json"
R2_PATH = ROOT / "data/operations/iterations/135/step13-residual-ledger-r2.json"
SCHEMA_PATH = ROOT / "schemas/operations/residual-ledger-r2.schema.json"

EXPECTED_R1_SHA256 = "3dc7291912b53e6042c1ca7d65afc842616e7b2a6a80b558defd8e7520bb1783"
EXPECTED_IDS = {
    "CURRENT_PATH_MANIFEST_UNACCOUNTED",
    "HUMAN_SURFACE_SOURCE_HASH_DRIFT",
    "PROPAGATION_TASK104_106_MISMATCH",
    "T16_SYMPY_COUNTEREXAMPLE",
    "FULL_UNITTEST_DISCOVERY_TERMINAL_STATE",
    "FULL_UNITTEST_DISCOVERY_TERMINAL_FAILURES",
}
EXPECTED_SEMANTICS = {
    "CURRENT_PATH_MANIFEST_UNACCOUNTED": "RESOLVED_CURRENT_RESIDUAL",
    "HUMAN_SURFACE_SOURCE_HASH_DRIFT": "RESOLVED_CURRENT_RESIDUAL",
    "PROPAGATION_TASK104_106_MISMATCH": "SEALED_HISTORICAL_RESIDUAL_ASSERTED",
    "T16_SYMPY_COUNTEREXAMPLE": "OBSERVATION_ONLY",
    "FULL_UNITTEST_DISCOVERY_TERMINAL_STATE": "RESOLVED_CURRENT_RESIDUAL",
    "FULL_UNITTEST_DISCOVERY_TERMINAL_FAILURES": "RESOLVED_CURRENT_RESIDUAL",
}
EXPECTED_OBSERVED = {
    "CURRENT_PATH_MANIFEST_UNACCOUNTED": (0, "04d9f07e4f115bda1851e07bd02455df651a8e26a38a03dcd119ab83a731f587"),
    "HUMAN_SURFACE_SOURCE_HASH_DRIFT": (0, "04d9f07e4f115bda1851e07bd02455df651a8e26a38a03dcd119ab83a731f587"),
    "PROPAGATION_TASK104_106_MISMATCH": (27, "e6904502753987540abcfb8653c0b53627e435455e10a34f1b22bf4417a289ac"),
    "T16_SYMPY_COUNTEREXAMPLE": (1, "3b78be31c06ad48b2cb24c50b9af34137d5c4dd13dc06ea30bbff1a472c00d8d"),
    "FULL_UNITTEST_DISCOVERY_TERMINAL_STATE": (0, "04d9f07e4f115bda1851e07bd02455df651a8e26a38a03dcd119ab83a731f587"),
    "FULL_UNITTEST_DISCOVERY_TERMINAL_FAILURES": (0, "04d9f07e4f115bda1851e07bd02455df651a8e26a38a03dcd119ab83a731f587"),
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate() -> list[str]:
    r1 = load(R1_PATH)
    r2 = load(R2_PATH)
    errors: list[str] = []
    errors.extend(error.json_path + ": " + error.message for error in Draft202012Validator(load(SCHEMA_PATH)).iter_errors(r2))
    if sha256(R1_PATH) != EXPECTED_R1_SHA256:
        errors.append("HISTORICAL_LEDGER_CHANGED")
    if r2.get("historical_ledger", {}).get("sha256") != EXPECTED_R1_SHA256:
        errors.append("HISTORICAL_LEDGER_PIN_MISMATCH")

    r1_rows = {row.get("residual_id"): row for row in r1.get("residuals", [])}
    r2_rows = {row.get("residual_id"): row for row in r2.get("residuals", [])}
    if set(r1_rows) != EXPECTED_IDS or set(r2_rows) != EXPECTED_IDS:
        errors.append("RESIDUAL_ID_SET_MISMATCH")
    if set(r1_rows) != set(r2_rows):
        errors.append("R1_R2_RESIDUAL_ID_SET_MISMATCH")

    for residual_id in sorted(EXPECTED_IDS):
        old = r1_rows.get(residual_id, {})
        new = r2_rows.get(residual_id, {})
        for field in ("baseline_count", "baseline_fingerprint"):
            if new.get(field) != old.get(field):
                errors.append(f"{residual_id}:{field}_CHANGED")
        if new.get("historical_current_count") != old.get("current_count"):
            errors.append(f"{residual_id}:historical_current_count_CHANGED")
        if new.get("historical_current_fingerprint") != old.get("current_fingerprint"):
            errors.append(f"{residual_id}:historical_current_fingerprint_CHANGED")
        expected_observed_count, expected_observed_fingerprint = EXPECTED_OBSERVED[residual_id]
        if new.get("observed_current_count") != expected_observed_count or new.get("observed_current_fingerprint") != expected_observed_fingerprint:
            errors.append(f"{residual_id}:observed_current_state_MISMATCH")
        expected_semantic = EXPECTED_SEMANTICS[residual_id]
        if new.get("semantic_classification") != expected_semantic:
            errors.append(f"{residual_id}:SEMANTIC_CLASSIFICATION_MISMATCH")
        if new.get("non_growth") != "PASS":
            errors.append(f"{residual_id}:NON_GROWTH_NOT_PASS")
        if new.get("current_blocker") is not False:
            errors.append(f"{residual_id}:CURRENT_BLOCKER_NOT_FALSE")

    sealed = r2_rows.get("PROPAGATION_TASK104_106_MISMATCH", {})
    if sealed.get("historical_current_fingerprint") != sealed.get("observed_current_fingerprint"):
        errors.append("SEALED_HISTORICAL_FINGERPRINT_CHANGED")
    sympy = r2_rows.get("T16_SYMPY_COUNTEREXAMPLE", {})
    if sympy.get("environment_requirement") != "ENVIRONMENT_REQUIREMENT":
        errors.append("SYMPY_ENVIRONMENT_REQUIREMENT_LABEL_MISSING")
    if sympy.get("status") != "HISTORICAL_OBSERVATION":
        errors.append("SYMPY_OBSERVATION_STATUS_MISMATCH")
    for residual_id, row in r2_rows.items():
        if row.get("semantic_classification") == "RESOLVED_CURRENT_RESIDUAL" and row.get("observed_current_count") != 0:
            errors.append(f"{residual_id}:RESOLVED_CURRENT_HAS_LIVE_OBSERVATION")
    summary = r2.get("summary", {})
    if summary.get("current_failure_count") != 0 or summary.get("environment_blocker_count") != 0:
        errors.append("CURRENT_OR_ENVIRONMENT_BLOCKER_PRESENT")
    if r2.get("checks", {}).get("no_residual_growth") is not True:
        errors.append("RESIDUAL_NON_GROWTH_CHECK_FAILED")
    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    errors = validate()
    if errors:
        print("RESIDUAL_LEDGER_R2_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("RESIDUAL_LEDGER_R2_OK sealed=1 observation_only=1 resolved_current=4 current_failures=0 environment_blockers=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
