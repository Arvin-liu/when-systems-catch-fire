#!/usr/bin/env python3
"""Validate and render a bounded, provenance-preserving object collision run."""

from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "tools/foundation"))
import resolve_current_canonical_asset as canonical_resolver  # noqa: E402


SCHEMA_PATH = ROOT / "schemas/operations/ignition-object-collision-run-r1.schema.json"
FIXTURE_PATH = ROOT / "tests/fixtures/ignition-operating-method/object-collision-r1.json"
FUNCTION_REGISTRY_PATH = ROOT / "data/foundation/function-assets/identity-cards.jsonl"
NONFUNCTION_REGISTRY_PATH = ROOT / "data/foundation/nonfunction-claims/claim-registry.jsonl"

FUNCTION_AUTHORITY = "ignition/data/foundation/function-assets/identity-cards.jsonl"
NONFUNCTION_AUTHORITY = "ignition/data/foundation/nonfunction-claims/claim-registry.jsonl"
REQUIRED_REGISTRIES = {FUNCTION_AUTHORITY, NONFUNCTION_AUTHORITY}
MATCH_REQUIRED_RELATIONSHIPS = {
    "DUPLICATE_OF",
    "EXTENSION_OF",
    "COMBINATION_OF",
    "CONFLICT_WITH",
}


class ObjectCollisionError(ValueError):
    """Raised when a collision run does not satisfy the R1 contract."""


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _duplicates(values: list[str]) -> list[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
        seen.add(value)
    return sorted(duplicates)


def _canonical_maps() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    function_rows = load_jsonl(FUNCTION_REGISTRY_PATH)
    claim_rows = load_jsonl(NONFUNCTION_REGISTRY_PATH)
    functions = {row["canonical_id"]: row for row in function_rows}
    claims = {row["canonical_id"]: row for row in claim_rows}
    if len(functions) != len(function_rows):
        raise ObjectCollisionError("Current function registry contains duplicate canonical IDs")
    if len(claims) != len(claim_rows):
        raise ObjectCollisionError("Current non-function registry contains duplicate canonical IDs")
    return functions, claims


def _record_title(kind: str, record: dict[str, Any]) -> str:
    return record["title"] if kind == "FUNCTION_ASSET" else record["canonical_title"]


def validate_run(run: dict[str, Any]) -> list[str]:
    errors = [
        f"{error.json_path}: {error.message}"
        for error in Draft202012Validator(load_json(SCHEMA_PATH)).iter_errors(run)
    ]
    if errors:
        return errors

    functions, claims = _canonical_maps()
    units = run["normalized_units"]
    unit_ids = [row["unit_id"] for row in units]
    duplicate_units = _duplicates(unit_ids)
    if duplicate_units:
        errors.append(f"duplicate normalized unit IDs: {duplicate_units}")
    unit_id_set = set(unit_ids)
    source_texts = {_normalize_text(row["text"]) for row in units}

    searched = set(run["canonical_search"]["registries_searched"])
    if searched != REQUIRED_REGISTRIES:
        errors.append(
            "canonical search must query exactly the Current function identity cards and non-function claim registry"
        )

    matches = run["canonical_search"]["matches"]
    match_ids = [row["match_id"] for row in matches]
    duplicate_matches = _duplicates(match_ids)
    if duplicate_matches:
        errors.append(f"duplicate canonical match IDs: {duplicate_matches}")
    match_id_set = set(match_ids)
    for match in matches:
        missing_units = sorted(set(match["unit_ids"]) - unit_id_set)
        if missing_units:
            errors.append(f"{match['match_id']}: unknown normalized unit IDs: {missing_units}")
        records = functions if match["registry_kind"] == "FUNCTION_ASSET" else claims
        record = records.get(match["canonical_id"])
        if record is None:
            errors.append(
                f"{match['match_id']}: canonical ID not present in Current {match['registry_kind']} registry: {match['canonical_id']}"
            )
            continue
        basis = match["match_basis"]
        query = match["query_reference"].strip()
        if basis == "EXACT_ID" and query != match["canonical_id"]:
            errors.append(f"{match['match_id']}: EXACT_ID query does not equal canonical ID")
        elif basis == "EXACT_TITLE" and query != _record_title(match["registry_kind"], record):
            errors.append(f"{match['match_id']}: EXACT_TITLE query does not equal Current canonical title")
        elif basis == "CURRENT_ALIAS":
            if match["registry_kind"] != "FUNCTION_ASSET":
                errors.append(f"{match['match_id']}: CURRENT_ALIAS is only admitted through the function identity resolver")
            else:
                resolution = canonical_resolver.resolve_reference(query)
                if (
                    resolution["resolution_status"] != canonical_resolver.RESOLVED
                    or resolution["canonical_id"] != match["canonical_id"]
                ):
                    errors.append(f"{match['match_id']}: CURRENT_ALIAS does not resolve to the declared Current identity")
        elif basis == "REVIEWED_MAPPING" and "mapping_review" not in match:
            errors.append(f"{match['match_id']}: REVIEWED_MAPPING requires an explicit non-authoritative mapping review")
        if basis != "REVIEWED_MAPPING" and "mapping_review" in match:
            errors.append(f"{match['match_id']}: mapping_review is only valid for REVIEWED_MAPPING")

    finding_ids = [row["finding_id"] for row in run["findings"]]
    duplicate_findings = _duplicates(finding_ids)
    if duplicate_findings:
        errors.append(f"duplicate finding IDs: {duplicate_findings}")
    for finding in run["findings"]:
        missing_units = sorted(set(finding["unit_ids"]) - unit_id_set)
        missing_matches = sorted(set(finding["canonical_match_ids"]) - match_id_set)
        if missing_units:
            errors.append(f"{finding['finding_id']}: unknown normalized unit IDs: {missing_units}")
        if missing_matches:
            errors.append(f"{finding['finding_id']}: unknown canonical match IDs: {missing_matches}")
        relation = finding["relationship"]
        if relation in MATCH_REQUIRED_RELATIONSHIPS and not finding["canonical_match_ids"]:
            errors.append(f"{finding['finding_id']}: {relation} requires actual canonical collision evidence")
        if relation in {"SOURCE_DERIVED", "UNRESOLVED"} and finding["post_collision_increment"]:
            errors.append(f"{finding['finding_id']}: {relation} cannot be represented as an Ignition increment")
        if _normalize_text(finding["statement"]) in source_texts and relation != "SOURCE_DERIVED":
            errors.append(
                f"{finding['finding_id']}: an input-explicit viewpoint must remain SOURCE_DERIVED, not an Ignition discovery"
            )

    candidate_ids = [row["candidate_id"] for row in run["candidate_new"]]
    duplicate_candidates = _duplicates(candidate_ids)
    if duplicate_candidates:
        errors.append(f"duplicate candidate IDs: {duplicate_candidates}")
    for candidate in run["candidate_new"]:
        missing_units = sorted(set(candidate["derived_from_unit_ids"]) - unit_id_set)
        missing_matches = sorted(set(candidate["nearest_canonical_match_ids"]) - match_id_set)
        reviewed_units = set(candidate["source_explicit_overlap_review"]["reviewed_unit_ids"])
        missing_reviewed_units = sorted(reviewed_units - unit_id_set)
        if missing_units:
            errors.append(f"{candidate['candidate_id']}: unknown normalized unit IDs: {missing_units}")
        if missing_matches:
            errors.append(f"{candidate['candidate_id']}: unknown nearest canonical match IDs: {missing_matches}")
        if missing_reviewed_units:
            errors.append(f"{candidate['candidate_id']}: overlap review contains unknown unit IDs: {missing_reviewed_units}")
        if not set(candidate["derived_from_unit_ids"]) <= reviewed_units:
            errors.append(
                f"{candidate['candidate_id']}: source-explicit overlap review must cover every derived source unit"
            )
        if not candidate["nearest_canonical_match_ids"]:
            errors.append(
                f"{candidate['candidate_id']}: CANDIDATE_NEW requires actual canonical nearest-match evidence"
            )
        if _normalize_text(candidate["statement"]) in source_texts:
            errors.append(
                f"{candidate['candidate_id']}: source-explicit input cannot be relabelled CANDIDATE_NEW"
            )

    return errors


def render_run(run: dict[str, Any]) -> dict[str, Any]:
    errors = validate_run(run)
    if errors:
        raise ObjectCollisionError("; ".join(errors))
    functions, claims = _canonical_maps()
    canonical_matches: list[dict[str, Any]] = []
    for match in run["canonical_search"]["matches"]:
        record = (functions if match["registry_kind"] == "FUNCTION_ASSET" else claims)[match["canonical_id"]]
        canonical_matches.append({
            "match_id": match["match_id"],
            "registry_kind": match["registry_kind"],
            "canonical_id": match["canonical_id"],
            "canonical_title": _record_title(match["registry_kind"], record),
            "final_disposition": record["final_disposition"],
            "claim_ceiling": record["claim_ceiling"],
            "record_sha256": record["record_sha256"],
            "match_basis": match["match_basis"],
            "query_reference": match["query_reference"],
            "collision_evidence": match["collision_evidence"],
            "authority_source": FUNCTION_AUTHORITY if match["registry_kind"] == "FUNCTION_ASSET" else NONFUNCTION_AUTHORITY,
        })
    input_derived = [row for row in run["findings"] if row["relationship"] == "SOURCE_DERIVED"]
    increments = [row for row in run["findings"] if row["post_collision_increment"]]
    unresolved = [row for row in run["findings"] if row["relationship"] == "UNRESOLVED"]
    return {
        "schema_version": "ignition-object-collision-result-r1",
        "result_status": "COLLISION_PROTOCOL_VALID",
        "run_id": run["run_id"],
        "operation_id": run["operation_id"],
        "run_mode": run["run_mode"],
        "current_ref": run["current_ref"],
        "input_object": run["input_object"],
        "normalized_units": run["normalized_units"],
        "input_derived_findings": input_derived,
        "existing_canonical_matches": canonical_matches,
        "ignition_increments": increments,
        "candidate_new": run["candidate_new"],
        "unresolved": unresolved,
        "quantitative_assessments": run["quantitative_assessments"],
        "candidate_registry_action": "NONE",
        "side_effects_authorized": False,
        "claim_ceiling": "Repository-local object decomposition and canonical collision relation only; no candidate registration, truth, evidence, proof, causality, novelty or epistemic acceptance is established.",
    }


def _pointer_parent(document: Any, pointer: str) -> tuple[Any, str]:
    if not pointer.startswith("/"):
        raise ObjectCollisionError(f"fixture mutation pointer must start with /: {pointer}")
    parts = [part.replace("~1", "/").replace("~0", "~") for part in pointer[1:].split("/")]
    value = document
    for part in parts[:-1]:
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value, parts[-1]


def apply_fixture_mutations(base: dict[str, Any], mutations: list[dict[str, Any]]) -> dict[str, Any]:
    result = copy.deepcopy(base)
    for mutation in mutations:
        parent, key = _pointer_parent(result, mutation["path"])
        operation = mutation["op"]
        if operation == "set":
            if isinstance(parent, list):
                parent[int(key)] = copy.deepcopy(mutation["value"])
            else:
                parent[key] = copy.deepcopy(mutation["value"])
        elif operation == "delete":
            if isinstance(parent, list):
                del parent[int(key)]
            else:
                del parent[key]
        elif operation == "append":
            target = parent[int(key)] if isinstance(parent, list) else parent[key]
            if not isinstance(target, list):
                raise ObjectCollisionError(f"append target is not a list: {mutation['path']}")
            target.append(copy.deepcopy(mutation["value"]))
        else:
            raise ObjectCollisionError(f"unsupported fixture mutation operation: {operation}")
    return result


def validate_fixtures(document: dict[str, Any] | None = None) -> list[str]:
    fixtures = document if document is not None else load_json(FIXTURE_PATH)
    base = fixtures.get("base_run") if isinstance(fixtures, dict) else None
    cases = fixtures.get("cases", []) if isinstance(fixtures, dict) else []
    if not isinstance(base, dict) or not isinstance(cases, list) or not cases:
        return ["object collision fixtures require a base_run and nonempty cases"]
    errors: list[str] = []
    case_ids: list[str] = []
    for case in cases:
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            errors.append("every object collision fixture must have a nonblank case_id")
            continue
        case_ids.append(case_id)
        try:
            run = apply_fixture_mutations(base, case.get("mutations", []))
            actual_errors = validate_run(run)
        except (KeyError, IndexError, TypeError, ObjectCollisionError) as exc:
            actual_errors = [f"fixture construction failed: {exc}"]
        expected_valid = case.get("expected_valid") is True
        if expected_valid and actual_errors:
            errors.append(f"{case_id}: expected valid, got {actual_errors}")
        if not expected_valid and not actual_errors:
            errors.append(f"{case_id}: expected fail-closed validation error")
        for fragment in case.get("expected_error_contains", []):
            if not any(fragment in error for error in actual_errors):
                errors.append(f"{case_id}: missing expected error fragment {fragment!r}; actual={actual_errors}")
        if expected_valid and not actual_errors:
            result = render_run(run)
            for key, expected in case.get("expected_result", {}).items():
                if result.get(key) != expected:
                    errors.append(f"{case_id}: result {key} expected {expected!r}, got {result.get(key)!r}")
    if len(case_ids) != len(set(case_ids)):
        errors.append("object collision fixture case ids must be unique")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check-fixtures", action="store_true")
    group.add_argument("--input", type=Path)
    args = parser.parse_args()
    if args.check_fixtures:
        errors = validate_fixtures()
        if errors:
            print("IGNITION_OBJECT_COLLISION_FIXTURES_INVALID")
            for error in errors:
                print(f"- {error}")
            return 1
        cases = load_json(FIXTURE_PATH)["cases"]
        print(f"IGNITION_OBJECT_COLLISION_FIXTURES_OK cases={len(cases)}")
        return 0
    run = load_json(args.input)
    errors = validate_run(run)
    if errors:
        print("IGNITION_OBJECT_COLLISION_RUN_INVALID")
        for error in errors:
            print(f"- {error}")
        return 1
    print(json.dumps(render_run(run), ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
