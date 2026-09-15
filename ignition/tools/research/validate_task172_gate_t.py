#!/usr/bin/env python3
"""Fail-closed validator for the Task172 UNESCO Gate T authority lock."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path


DATA_REL = Path("data/research/task172-gate-t-unesco-1988")
EXPECTED_FORMAL_HEAD = "9dc446517ccc02b5e5d8ca383f0aed28ab7e4afc"
EXPECTED_COMMAND = {
    "repository": "Arvin-liu/1111",
    "ref": "b1fc45fb",
    "path": "agent-commands/IGNITION-20260913-176.md",
    "blob_sha": "98fd25bd1886cf8675992413d6c55d1e09b4502f",
}
EXPECTED_FIELDS = {
    "11", "12", "21", "22", "23", "24", "25", "31", "32", "33",
    "51", "52", "53", "54", "55", "56", "57", "58", "59", "61",
    "62", "63", "71", "72",
}
EXPECTED_DISCIPLINE_DIFFS = {
    "skos_minus_primary_exact": ["2290", "2390", "2490"],
    "primary_minus_skos_exact": [],
    "local_minus_primary_exact": ["2290", "2390", "2391", "2490", "6115", "7100"],
    "primary_minus_local_exact": ["6101"],
}
EXPECTED_PRIMARY_ONLY = ["2205.11", "3206.14", "3206.15"]
EXPECTED_SOURCE_ABSENT = ["1210.99", "2415.01", "2415.02", "3206.12", "3206.13"]
EXPECTED_BLOCKS = ["2290.01", "2390.01", "2490.01", "2490.02"]
EXPECTED_NON_SUFFIX = ["2205.09"]
EXPECTED_SUFFIX = [
    "2207.90", "2209.90", "2210.90", "2210.91", "2210.93", "2211.90",
    "2211.91", "2302.90", "2302.91", "2306.90", "2306.91", "2401.90",
    "2401.91", "2407.90", "2409.90", "2409.91", "2409.92", "2414.90",
    "2417.90", "2417.91", "2417.92", "2420.91", "2510.90", "2510.91",
    "2510.92", "3103.90", "3103.91", "3104.90",
    "3302.90", "3303.90", "3305.90", "3307.90", "3307.91", "3307.92",
    "3307.93", "3309.90", "3309.91", "3309.92", "3309.93", "3309.95",
    "3315.90", "3321.90", "5310.90", "5310.91", "5312.90", "5506.90",
    "5907.90",
]
EXPECTED_MIRROR_ONLY = sorted(EXPECTED_SOURCE_ABSENT + EXPECTED_BLOCKS + EXPECTED_NON_SUFFIX + EXPECTED_SUFFIX)
EXPECTED_REPAIRS = {
    (5, "right", 1929, "2307.07", "2302.07"),
    (8, "right", 2427, "2310.09", "2510.09"),
    (15, "left", 753, "3310.09", "5310.09"),
    (15, "left", 3945, "3401.02", "5401.02"),
    (15, "left", 6460, "3502.99", "5502.99"),
    (15, "right", 643, "3503.99", "5503.99"),
    (16, "left", 473, "5601.02", "5604.02"),
    (18, "left", 2969, "5301.05", "6301.05"),
}
EXPECTED_MANUAL_ANCHORS = [
    "2302.02", "2302.07", "2509.04", "2510.09", "3101.08", "3305.16",
    "5302.02", "5310.04", "5310.09", "5401.02", "5502.99", "5503.99",
    "5604.02", "6301.05", "7201.99",
]
EXPECTED_ANOMALIES = {
    ("2303.02", "2302.02"), ("2307.07", "2302.07"), ("2506", "2507"),
    ("2310.09", "2510.09"), ("3108.08", "3101.08"), ("3310.09", "5310.09"),
    ("3401.02", "5401.02"), ("5301.05", "6301.05"), ("5601.02", "5604.02"),
    ("3303.16", "3305.16"), ("3311.06", "5311.06"),
    ("3502.99", "5502.99"), ("3503.99", "5503.99"),
}


def canonical_hash(values: list[str]) -> str:
    return hashlib.sha256(("\n".join(sorted(values)) + "\n").encode()).hexdigest()


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - diagnostic path
        raise AssertionError(f"cannot read {path}: {exc}") from exc


def validate(repo_root: Path) -> None:
    task_dir = repo_root / DATA_REL
    parse = read_json(task_dir / "primary-1988-parse.json")
    ledger = read_json(task_dir / "discrepancy-ledger.json")
    receipt = read_json(task_dir / "build-receipt.json")
    freeze = read_json(task_dir / "source-freeze.json")

    assert parse.get("schema") == "task172-gate-t-primary-unesco-parse-v2", "wrong parse schema"
    assert ledger.get("schema") == "task172-gate-t-discrepancy-ledger-v2", "wrong ledger schema"
    assert receipt.get("schema") == "task172-gate-t-build-receipt-v2", "wrong receipt schema"
    assert freeze.get("schema") == "task172-gate-t-source-freeze-v1", "wrong freeze schema"
    assert freeze.get("freeze_event") == "SCAN_INPUT_FREEZE", "scan inputs were not frozen"
    assert freeze.get("command_source") == EXPECTED_COMMAND, "command provenance drift"
    formal = freeze.get("formal_pre_freeze", {})
    assert formal.get("head") == EXPECTED_FORMAL_HEAD, "pre-freeze Formal head drift"
    assert formal.get("pull_request") == 218, "wrong Draft PR binding"
    assert formal.get("state") == "OPEN + DRAFT + unmerged", "PR lifecycle ceiling drift"

    # The Formal tree must contain only the minimum derived code/hierarchy
    # products, never the recovered scan or bulk OCR.
    forbidden_suffixes = {".pdf", ".txt"}
    actual_names = {path.name for path in task_dir.rglob("*") if path.is_file()}
    assert not any(path.suffix in forbidden_suffixes for path in task_dir.rglob("*") if path.is_file()), "scan/OCR persisted"
    assert not any("primary-ocr" in name or "wayback" in name for name in actual_names), "primary scan persisted"

    hierarchy = parse.get("hierarchy", {})
    fields = hierarchy.get("fields", [])
    assert len(fields) == 24 and {item.get("code") for item in fields} == EXPECTED_FIELDS, "field census drift"
    records = parse.get("discipline_records", [])
    codes = [item.get("code") for item in records]
    assert len(records) == 245 and len(set(codes)) == 245, "discipline census drift"
    assert all(re.fullmatch(r"\d{4}", str(code)) for code in codes), "malformed discipline code"
    assert all(item.get("parent_field_code") == item.get("code", "")[:2] for item in records), "discipline parent drift"
    assert all(item.get("parent_field_code") in EXPECTED_FIELDS for item in records), "discipline field drift"
    assert all(item.get("label") for item in records), "blank discipline label"
    assert all(item.get("source_document_id") and item.get("source_page") and item.get("source_text_anchor") for item in records), "missing source anchor"
    assert not any(item.get("primary_status", "").startswith("PRIMARY_PAGE_ANCHOR_PENDING") for item in records), "pending source anchor"

    sub = parse.get("subdiscipline_census", {})
    subcodes = sub.get("codes_sorted", [])
    assert len(subcodes) == 2178 and len(set(subcodes)) == 2178, "six-digit primary census drift"
    assert all(re.fullmatch(r"\d{4}\.\d{2}", str(code)) for code in subcodes), "malformed six-digit code"
    assert all(code[:4] in set(codes) for code in subcodes), "six-digit parent drift"
    assert sub.get("code_set_sha256") == canonical_hash(subcodes), "six-digit hash drift"
    assert hierarchy.get("discipline_count") == 245 and hierarchy.get("subdiscipline_count") == 2178, "hierarchy counts drift"

    evidence = sub.get("source_normalization_evidence", {})
    assert evidence.get("dynamic_input_file") == "vision-ocr-dynamic-custom.json", "wrong row OCR input"
    assert evidence.get("dynamic_row_count") == 2220, "row OCR count drift"
    assert evidence.get("normalized_code_count") == 2178, "normalized row count drift"
    repairs = {
        (item.get("source_page"), item.get("column"), item.get("y_start"), item.get("raw_code"), item.get("normalized_code"))
        for item in evidence.get("coordinate_bound_repairs", [])
    }
    assert repairs == EXPECTED_REPAIRS, "coordinate-bound repair drift"
    assert [item.get("code") for item in evidence.get("manual_source_row_anchors", [])] == EXPECTED_MANUAL_ANCHORS, "manual anchor drift"
    assert evidence.get("secondary_mirror_not_used_for_fill") is True, "secondary mirror filled primary census"

    assert ledger.get("authority_order", [])[0] == {"rank": 1, "source": "1988 UNESCO primary scan", "role": "canonical authority for Task172"}, "authority order drift"
    counts = ledger.get("counts", {})
    assert counts.get("primary_1988_scan") == {"fields": 24, "disciplines": 245, "subdisciplines": 2178, "specialties": 0}, "primary counts drift"
    assert counts.get("skos_mirror_observed") == {"fields": 24, "disciplines": 248, "subdisciplines": 2232}, "SKOS counts drift"
    assert counts.get("formal_local_inventory") == {"fields": 24, "disciplines": 250}, "local counts drift"
    assert counts.get("cyta_secondary_mirror") == {"subdisciplines": 2232}, "CyTA count drift"
    assert counts.get("secondary_evidence_corroboration", {}).get("primary_1988_subdisciplines") == 2183, "secondary 2183 not retained"
    assert counts.get("primary_scan_vs_historical_secondary") == {
        "primary_scan_normalized_subdisciplines": 2178,
        "historical_secondary_reported_subdisciplines": 2183,
        "delta_primary_minus_secondary": -5,
        "status": "SECONDARY_COUNT_NOT_PRIMARY_CLOSURE",
        "source_absent_from_primary_scan_exact": EXPECTED_SOURCE_ABSENT,
        "decision": "do not force the secondary 2183 into the primary set; retain the five-row discrepancy for audit",
    }, "2183 reconciliation drift"

    discipline_diffs = ledger.get("discipline_differences", {})
    for key, expected in EXPECTED_DISCIPLINE_DIFFS.items():
        assert discipline_diffs.get(key) == expected, f"discipline discrepancy drift: {key}"

    subdiff = ledger.get("subdiscipline_differences_against_cyta", {})
    assert subdiff.get("primary_minus_mirror_exact") == EXPECTED_PRIMARY_ONLY, "primary-only six-digit list drift"
    assert subdiff.get("mirror_minus_primary_exact") == EXPECTED_MIRROR_ONLY, "mirror-only six-digit list drift"
    assert subdiff.get("mirror_only_suffix_variants") == EXPECTED_SUFFIX, "suffix discrepancy drift"
    assert subdiff.get("mirror_only_discipline_blocks") == EXPECTED_BLOCKS, "discipline-block discrepancy drift"
    assert subdiff.get("mirror_only_non_suffix") == EXPECTED_NON_SUFFIX, "non-suffix discrepancy drift"
    assert subdiff.get("mirror_only_source_absent_verified") == EXPECTED_SOURCE_ABSENT, "source-absent discrepancy drift"

    observed_anomalies = {(item.get("raw_code"), item.get("normalized_code")) for item in parse.get("raw_print_anomalies", [])}
    assert EXPECTED_ANOMALIES.issubset(observed_anomalies), "raw anomaly ledger incomplete"
    assert parse.get("source_integrity", {}).get("primary_pdf_persisted_in_repository") is False, "PDF rights boundary drift"
    assert parse.get("source_integrity", {}).get("ocr_persisted_in_repository") is False, "OCR rights boundary drift"
    assert ledger.get("decision") == "GATE_T_PASS_FOR_AUTHORITY_LOCK; MASS_INGESTION_REMAINS_GATED_BY_GATE_R_AND_GATE_C", "Gate T decision drift"
    assert receipt.get("output_counts") == {"fields": 24, "disciplines": 245, "subdisciplines": 2178}, "receipt count drift"
    assert receipt.get("output_hashes", {}).get("subdiscipline_codes_sha256") == sub.get("code_set_sha256"), "receipt hash drift"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    try:
        validate(args.repo_root.resolve())
    except AssertionError as exc:
        raise SystemExit(f"TASK172_GATE_T_VALIDATION_FAILED: {exc}") from exc
    print("TASK172_GATE_T_VALIDATION_OK fields=24 disciplines=245 subdisciplines=2178; secondary_report=2183; mirror=2232; local=250")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
