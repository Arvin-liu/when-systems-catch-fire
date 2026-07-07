#!/usr/bin/env python3
"""
Validate P1 machine-readable data.

This validator checks:
- expected files exist
- JSON syntax and row counts
- CSV syntax and row counts
- JSON and CSV id/order consistency
- schema shallow structure
- required fields from schema
- additionalProperties=false at row level
- id ranges for CP / SB / PEND / RISK / FAIL / EVID
- cross references between datasets
- basic status / level / decision enums

It intentionally avoids external dependencies.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SCHEMAS = DATA / "schemas"


DATASETS: dict[str, dict[str, Any]] = {
    "classic_problems_benchmark": {
        "json": DATA / "classic_problems_benchmark.json",
        "csv": DATA / "classic_problems_benchmark.csv",
        "schema": SCHEMAS / "classic_problems_benchmark.schema.json",
        "expected_count": 34,
        "id_pattern": r"^CP-\d{3}$",
        "expected_ids": [f"CP-{i:03d}" for i in range(1, 35)],
    },
    "storytelling_backlog": {
        "json": DATA / "storytelling_backlog.json",
        "csv": DATA / "storytelling_backlog.csv",
        "schema": SCHEMAS / "storytelling_backlog.schema.json",
        "expected_count": 30,
        "id_pattern": r"^SB-\d{3}$",
        "expected_ids": [f"SB-{i:03d}" for i in range(1, 31)],
    },
    "pending_claims": {
        "json": DATA / "pending_claims.json",
        "csv": DATA / "pending_claims.csv",
        "schema": SCHEMAS / "pending_claims.schema.json",
        "expected_count": 34,
        "id_pattern": r"^PEND-\d{3}$",
        "expected_ids": [f"PEND-{i:03d}" for i in range(1, 35)],
    },
    "publication_risk_rules": {
        "json": DATA / "publication_risk_rules.json",
        "csv": DATA / "publication_risk_rules.csv",
        "schema": SCHEMAS / "publication_risk_rules.schema.json",
        "expected_count": 8,
        "id_pattern": r"^RISK-\d{3}$",
        "expected_ids": [f"RISK-{i:03d}" for i in range(1, 9)],
    },
    "failure_typology": {
        "json": DATA / "failure_typology.json",
        "csv": DATA / "failure_typology.csv",
        "schema": SCHEMAS / "failure_typology.schema.json",
        "expected_count": 12,
        "id_pattern": r"^FAIL-\d{3}$",
        "expected_ids": [f"FAIL-{i:03d}" for i in range(1, 13)],
    },
    "evidence_regimes": {
        "json": DATA / "evidence_regimes.json",
        "csv": DATA / "evidence_regimes.csv",
        "schema": SCHEMAS / "evidence_regimes.schema.json",
        "expected_count": 12,
        "min_count": 12,
        "id_pattern": r"^EVID-\d{3}$",
    },
    "function_dependency": {
        "json": DATA / "function_dependency.json",
        "csv": DATA / "function_dependency.csv",
        "schema": SCHEMAS / "function_dependency.schema.json",
        "expected_count": 13,
        "min_count": 13,
        "id_pattern": r"^FUNC-.+",
    },
}


ALLOWED_STATUS = {"active", "pending", "deprecated", "draft", "review"}
ALLOWED_CLAIM_LEVELS = {"L0", "L1", "L2", "L3", "L4", "L5", "pending"}
ALLOWED_EVIDENCE_LEVELS = {"L0", "L1", "L2", "L3", "pending"}
ALLOWED_DECISIONS = {"PASS", "REVISE", "HOLD", "pending"}
ALLOWED_RISK_DECISIONS = {"PASS", "REVISE", "HOLD"}
ALLOWED_LAYERS = {"L0", "L1", "L2", "L3", "L4", "L5", "L6"}


class ValidationError(Exception):
    pass


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValidationError(f"{rel(path)} JSON_LOAD_FAILED: {exc}") from exc


def load_csv(path: Path) -> list[dict[str, str]]:
    try:
        with path.open("r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))
    except Exception as exc:
        raise ValidationError(f"{rel(path)} CSV_LOAD_FAILED: {exc}") from exc


def ensure_file(path: Path) -> None:
    if not path.exists():
        raise ValidationError(f"FILE_MISSING {rel(path)}")
    if not path.is_file():
        raise ValidationError(f"NOT_A_FILE {rel(path)}")


def json_list(path: Path) -> list[dict[str, Any]]:
    data = load_json(path)
    if not isinstance(data, list):
        raise ValidationError(f"{rel(path)} must be a JSON array")
    for i, row in enumerate(data):
        if not isinstance(row, dict):
            raise ValidationError(f"{rel(path)} row {i} must be object")
    return data


def schema_required_and_props(schema_path: Path) -> tuple[set[str], set[str], bool]:
    schema = load_json(schema_path)
    if schema.get("type") != "array":
        raise ValidationError(f"{rel(schema_path)} schema root type must be array")
    items = schema.get("items")
    if not isinstance(items, dict):
        raise ValidationError(f"{rel(schema_path)} schema items missing")
    required = set(items.get("required", []))
    props = set((items.get("properties") or {}).keys())
    additional = items.get("additionalProperties", True)
    if not required:
        raise ValidationError(f"{rel(schema_path)} schema items.required missing")
    if not props:
        raise ValidationError(f"{rel(schema_path)} schema items.properties missing")
    return required, props, additional is False


def validate_required_and_extra(name: str, rows: list[dict[str, Any]], schema_path: Path) -> None:
    required, props, no_extra = schema_required_and_props(schema_path)
    for row in rows:
        rid = row.get("id", "<missing id>")
        missing = sorted(k for k in required if k not in row)
        if missing:
            raise ValidationError(f"{name} {rid} missing required fields: {missing}")
        if no_extra:
            extra = sorted(k for k in row if k not in props)
            if extra:
                raise ValidationError(f"{name} {rid} extra fields: {extra}")


def validate_ids(name: str, rows: list[dict[str, Any]], config: dict[str, Any]) -> None:
    ids = [row.get("id") for row in rows]
    if any(not isinstance(x, str) or not x for x in ids):
        raise ValidationError(f"{name} has empty or non-string id")
    if len(ids) != len(set(ids)):
        raise ValidationError(f"{name} has duplicate ids")
    pat = re.compile(config["id_pattern"])
    bad = [x for x in ids if not pat.match(x)]
    if bad:
        raise ValidationError(f"{name} has bad ids: {bad}")
    expected_ids = config.get("expected_ids")
    if expected_ids and ids != expected_ids:
        raise ValidationError(f"{name} id range/order mismatch: first={ids[:3]} last={ids[-3:]}")


def validate_count(name: str, rows: list[dict[str, Any]], csv_rows: list[dict[str, str]], config: dict[str, Any]) -> None:
    expected = config.get("expected_count")
    minimum = config.get("min_count")

    if expected is not None and len(rows) != expected:
        raise ValidationError(f"{name} JSON expected {expected}, got {len(rows)}")
    if expected is not None and len(csv_rows) != expected:
        raise ValidationError(f"{name} CSV expected {expected}, got {len(csv_rows)}")

    if minimum is not None and len(rows) < minimum:
        raise ValidationError(f"{name} JSON expected at least {minimum}, got {len(rows)}")
    if minimum is not None and len(csv_rows) < minimum:
        raise ValidationError(f"{name} CSV expected at least {minimum}, got {len(csv_rows)}")


def validate_csv_json_ids(name: str, rows: list[dict[str, Any]], csv_rows: list[dict[str, str]]) -> None:
    json_ids = [row.get("id") for row in rows]
    csv_ids = [row.get("id") for row in csv_rows]
    if json_ids != csv_ids:
        raise ValidationError(f"{name} JSON/CSV id mismatch")


def validate_common_fields(name: str, rows: list[dict[str, Any]]) -> None:
    for row in rows:
        rid = row.get("id")
        status = row.get("status")
        if status not in ALLOWED_STATUS:
            raise ValidationError(f"{name} {rid} bad status: {status}")
        if row.get("created_in") != "v0.2":
            raise ValidationError(f"{name} {rid} created_in must be v0.2")


def validate_dataset(name: str, config: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ["json", "csv", "schema"]:
        ensure_file(config[key])

    rows = json_list(config["json"])
    csv_rows = load_csv(config["csv"])

    validate_count(name, rows, csv_rows, config)
    validate_ids(name, rows, config)
    validate_csv_json_ids(name, rows, csv_rows)
    validate_required_and_extra(name, rows, config["schema"])
    validate_common_fields(name, rows)

    print(f"OK {name}: json={len(rows)} csv={len(csv_rows)}")
    return rows


def validate_specific(all_rows: dict[str, list[dict[str, Any]]]) -> None:
    cp_ids = {r["id"] for r in all_rows["classic_problems_benchmark"]}
    sb_ids = {r["id"] for r in all_rows["storytelling_backlog"]}
    pend_ids = {r["id"] for r in all_rows["pending_claims"]}
    risk_ids = {r["id"] for r in all_rows["publication_risk_rules"]}
    fail_ids = {r["id"] for r in all_rows["failure_typology"]}
    evid_ids = {r["id"] for r in all_rows["evidence_regimes"]}
    func_ids = {r["id"] for r in all_rows["function_dependency"]}

    # CP
    for row in all_rows["classic_problems_benchmark"]:
        if row["claim_level_max"] not in ALLOWED_CLAIM_LEVELS:
            raise ValidationError(f"{row['id']} bad claim_level_max")
        for x in row.get("related_pend_ids", []):
            if x not in pend_ids:
                raise ValidationError(f"{row['id']} bad related_pend_id {x}")
        for x in row.get("related_failure_types", []):
            if x not in fail_ids:
                raise ValidationError(f"{row['id']} bad related_failure_type {x}")
        source_file = row.get("source_file")
        if source_file and not (ROOT / source_file).exists():
            raise ValidationError(f"{row['id']} missing source_file {source_file}")

    # SB
    for row in all_rows["storytelling_backlog"]:
        if row["priority"] not in {"高", "中", "暂缓"}:
            raise ValidationError(f"{row['id']} bad priority")
        if row["publish_status"] not in {"draft", "hold", "ready"}:
            raise ValidationError(f"{row['id']} bad publish_status")
        if row["priority"] == "暂缓" and row["publish_status"] != "hold":
            raise ValidationError(f"{row['id']} priority 暂缓 should be hold")
        for x in row.get("related_cp_ids", []):
            if x not in cp_ids:
                raise ValidationError(f"{row['id']} bad related_cp_id {x}")
        for x in row.get("related_pend_ids", []):
            if x not in pend_ids:
                raise ValidationError(f"{row['id']} bad related_pend_id {x}")

    # Pending
    for row in all_rows["pending_claims"]:
        if row["default_decision"] not in ALLOWED_DECISIONS:
            raise ValidationError(f"{row['id']} bad default_decision")
        for x in row.get("related_cp_ids", []):
            if x not in cp_ids:
                raise ValidationError(f"{row['id']} bad related_cp_id {x}")
        for x in row.get("related_sb_ids", []):
            if x not in sb_ids:
                raise ValidationError(f"{row['id']} bad related_sb_id {x}")

    # Risk
    for row in all_rows["publication_risk_rules"]:
        if row["decision"] not in ALLOWED_RISK_DECISIONS:
            raise ValidationError(f"{row['id']} bad decision")
        ft = row.get("related_failure_type")
        if ft and ft not in fail_ids:
            raise ValidationError(f"{row['id']} bad related_failure_type {ft}")
        for x in row.get("related_pend_ids", []):
            if x not in pend_ids:
                raise ValidationError(f"{row['id']} bad related_pend_id {x}")

    # Failure
    for row in all_rows["failure_typology"]:
        for x in row.get("related_risk_rules", []):
            if x not in risk_ids:
                raise ValidationError(f"{row['id']} bad related_risk_rule {x}")
        for x in row.get("related_pend_ids", []):
            if x not in pend_ids:
                raise ValidationError(f"{row['id']} bad related_pend_id {x}")

    # Evidence
    for row in all_rows["evidence_regimes"]:
        if row["max_claim_level_without_external_evidence"] not in ALLOWED_EVIDENCE_LEVELS:
            raise ValidationError(f"{row['id']} bad max_claim_level_without_external_evidence")
        if not row.get("domain"):
            raise ValidationError(f"{row['id']} missing domain")
        if not row.get("evidence_required"):
            raise ValidationError(f"{row['id']} missing evidence_required")

    # Function dependency
    for row in all_rows["function_dependency"]:
        if row["layer"] not in ALLOWED_LAYERS:
            raise ValidationError(f"{row['id']} bad layer")
        for x in row.get("depends_on", []):
            if x not in func_ids:
                raise ValidationError(f"{row['id']} bad depends_on {x}")
        for x in row.get("used_by", []):
            if x not in func_ids:
                raise ValidationError(f"{row['id']} bad used_by {x}")

    print("OK cross-references and dataset-specific checks")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate P1 machine-readable data")
    parser.add_argument("--quiet", action="store_true", help="Only print final result")
    args = parser.parse_args()

    all_rows: dict[str, list[dict[str, Any]]] = {}

    try:
        for name, config in DATASETS.items():
            rows = validate_dataset(name, config)
            all_rows[name] = rows

        validate_specific(all_rows)

    except ValidationError as exc:
        print(f"VALIDATION_FAILED: {exc}", file=sys.stderr)
        return 1

    print("ALL_P1_DATA_VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
