#!/usr/bin/env python3
"""Fail-closed boundary between generated editorial material and Owner authority."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "data/governance/owner-editorial-authority-r1.json"
SCHEMA_PATH = ROOT / "schemas/governance/owner-editorial-authority-r1.schema.json"
FIXTURES_PATH = ROOT / "data/governance/owner-editorial-authority-negative-fixtures-r1.json"
INVENTORY_PATH = ROOT / "data/operations/iterations/144/task143-smoke-output-inventory-r1.json"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_contract(contract: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    errors = [error.json_path + ": " + error.message for error in Draft202012Validator(schema).iter_errors(contract)]
    states = contract.get("state_machine", {})
    if set(states.get("terminal_states", [])) != {"ACCEPTED", "REVISE", "PARKED", "REJECTED"}:
        errors.append("terminal states must preserve the four Owner decision outcomes")
    if "CANDIDATE" not in states.get("allowed_states", []):
        errors.append("CANDIDATE must be the initial production state")
    expected_transitions = {
        ("CANDIDATE", "OWNER_SELECTED"),
        ("OWNER_SELECTED", "DRAFTING"),
        ("DRAFTING", "OWNER_REVIEW"),
        ("OWNER_REVIEW", "ACCEPTED"),
        ("OWNER_REVIEW", "REVISE"),
        ("OWNER_REVIEW", "PARKED"),
        ("OWNER_REVIEW", "REJECTED"),
    }
    observed_transitions = {(row.get("from"), row.get("to")) for row in states.get("allowed_transitions", [])}
    if observed_transitions != expected_transitions:
        errors.append("allowed transitions must be the minimal Owner editorial state path")
    rules = contract.get("rules", {})
    if not set(rules.get("owner_authority_sources", [])) == {"OWNER_EXPLICIT_PRODUCTION_BRIEF", "OWNER_EXPLICIT_SELECTION"}:
        errors.append("Owner authority sources are incomplete")
    required_non_equivalences = {
        "DRAFT_GENERATED_NOT_OWNER_SELECTED",
        "DRAFT_GENERATED_NOT_PUBLICATION_ACCEPTED",
        "RESULT_REGISTRY_NOT_OWNER_ACCEPTANCE",
        "FIRE_SEED_SCORE_NOT_OWNER_SELECTION",
        "MODEL_RANKING_NOT_OWNER_SELECTION",
    }
    if not required_non_equivalences <= set(rules.get("non_equivalences", [])):
        errors.append("non-equivalence rules are incomplete")
    return sorted(set(errors))


def validate_item(item: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    fields = contract["fields"]
    required = ("kind", "source_origin", "owner_selection", "draft_status", "production_state", "publication_acceptance", "authority_source")
    for field in required:
        if field not in item:
            errors.append(f"MISSING_{field.upper()}")
        elif item[field] not in fields[field]:
            errors.append(f"INVALID_{field.upper()}")

    if errors:
        return sorted(set(errors))

    origin = item["source_origin"]
    owner_selection = item["owner_selection"]
    authority = item["authority_source"]
    state = item["production_state"]
    acceptance = item["publication_acceptance"]

    if item.get("smoke_test"):
        defaults = contract["rules"]["smoke_test_defaults"]
        for field, expected in defaults.items():
            if item.get(field) != expected:
                errors.append(f"SMOKE_TEST_DEFAULT_{field.upper()}_VIOLATION")

    if item.get("draft_status") == "DRAFT_GENERATED" and acceptance == "PUBLICATION_ACCEPTED" and owner_selection != "OWNER_SELECTED":
        errors.append("DRAFT_GENERATED_NOT_PUBLICATION_ACCEPTED")

    if origin in {"MODEL_RANKING", "AUTO_CLUSTER"} and owner_selection == "OWNER_SELECTED":
        errors.append(f"{origin}_NOT_OWNER_SELECTION")
    if origin == "DRAFT" and state == "ACCEPTED":
        errors.append("DRAFT_GENERATED_NOT_OWNER_SELECTED")
    if origin == "RESULT_REGISTRY" and acceptance == "PUBLICATION_ACCEPTED":
        errors.append("RESULT_REGISTRY_NOT_OWNER_ACCEPTANCE")
    if origin == "FIRE_SEED_SCORE" and item.get("fire_seed_score", 0) >= 4 and owner_selection == "OWNER_SELECTED":
        errors.append("FIRE_SEED_SCORE_NOT_OWNER_SELECTION")

    owner_sources = set(contract["rules"]["owner_authority_sources"])
    if owner_selection == "OWNER_SELECTED":
        if authority not in owner_sources:
            errors.append("OWNER_SELECTED_REQUIRES_OWNER_AUTHORITY")
        if state == "CANDIDATE":
            errors.append("OWNER_SELECTED_STATE_MISMATCH")
    elif authority != "NONE":
        errors.append("UNSELECTED_ITEM_CANNOT_CARRY_OWNER_AUTHORITY")

    if state != "CANDIDATE" and owner_selection != "OWNER_SELECTED":
        errors.append("NON_CANDIDATE_REQUIRES_OWNER_SELECTION")
    if state == "ACCEPTED":
        if owner_selection != "OWNER_SELECTED" or authority not in owner_sources:
            errors.append("ACCEPTED_REQUIRES_OWNER_AUTHORITY")
        if acceptance != "PUBLICATION_ACCEPTED":
            errors.append("ACCEPTED_STATE_REQUIRES_PUBLICATION_ACCEPTANCE")
    if acceptance == "PUBLICATION_ACCEPTED" and (owner_selection != "OWNER_SELECTED" or authority not in owner_sources):
        errors.append("PUBLICATION_ACCEPTED_REQUIRES_OWNER_AUTHORITY")
    return sorted(set(errors))


def validate_smoke_inventory(inventory: dict[str, Any], contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for artifact in inventory.get("artifacts", []):
        item = {
            "kind": "book" if artifact["kind"] in {"book_project", "book_sample"} else "article",
            "source_origin": "RESULT_REGISTRY",
            "owner_selection": artifact["owner_selection"],
            "draft_status": "DRAFT_GENERATED",
            "production_state": "CANDIDATE",
            "publication_acceptance": artifact["publication_acceptance"],
            "authority_source": "NONE",
            "smoke_test": artifact["smoke_test"],
        }
        item_errors = validate_item(item, contract)
        errors.extend(f"{artifact.get('artifact_id', 'UNKNOWN')}: {error}" for error in item_errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    parser.add_argument("--contract", type=Path, default=CONTRACT_PATH)
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH)
    parser.add_argument("--fixtures", type=Path, default=FIXTURES_PATH)
    parser.add_argument("--inventory", type=Path, default=INVENTORY_PATH)
    args = parser.parse_args()
    contract = load_json(args.contract)
    schema = load_json(args.schema)
    errors = validate_contract(contract, schema)
    fixtures = load_json(args.fixtures)
    checked = 0
    for fixture in fixtures:
        checked += 1
        fixture_errors = validate_item(fixture, contract)
        expected = fixture.get("expected_error_code")
        if expected not in fixture_errors:
            errors.append(f"{fixture.get('fixture_id', 'UNKNOWN')}: expected {expected}, got {fixture_errors}")
    inventory = load_json(args.inventory)
    errors.extend(validate_smoke_inventory(inventory, contract))
    if errors:
        print("OWNER_EDITORIAL_AUTHORITY_INVALID")
        for error in sorted(set(errors)):
            print(f"- {error}")
        return 1
    print(f"OWNER_EDITORIAL_AUTHORITY_OK negative_fixtures={checked} smoke_outputs={len(inventory.get('artifacts', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
