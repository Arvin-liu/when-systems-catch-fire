#!/usr/bin/env python3
"""Fail-closed validation for the task-99 function-asset registry closure."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import jsonschema

from legacy_table_migration import source_exists as migrated_source_exists

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "data/foundation/function-assets"
EXPECTED_TASK98 = {"T2", "D127", *(f"D{i}" for i in range(182, 191)), "D260"}


def rows(name: str) -> list[dict]:
    path = ASSETS / name
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def record_hash(row: dict) -> str:
    payload = dict(row)
    payload.pop("record_sha256", None)
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


source_exists = lambda path: (ROOT / path).is_file() or migrated_source_exists(path)


def load_generator():
    path = ROOT / "tools/foundation/adjudicate_function_assets.py"
    spec = importlib.util.spec_from_file_location("task99_adjudicator", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, condition: bool, detail: str = "") -> None:
        checks.append((name, bool(condition), detail))

    census = rows("census.jsonl")
    cards = rows("identity-cards.jsonl")
    ledger = rows("adjudication-ledger.jsonl")
    obligations = rows("proof-empirical-obligations.jsonl")
    counterexamples = rows("counterexample-registry.jsonl")
    quarantine = rows("unresolved-quarantine.jsonl")
    dependency = rows("dependency-closure.jsonl")
    public_claims = rows("public-claim-lineage.jsonl")
    rebounds = rows("semantic-rebound-report.jsonl")
    withdrawn = rows("withdrawn-historical-claims.jsonl")
    summary = json.loads((ASSETS / "closure-summary.json").read_text(encoding="utf-8"))
    coverage = json.loads((ASSETS / "discovery-coverage.json").read_text(encoding="utf-8"))
    math_checks = json.loads((ASSETS / "math-checks.json").read_text(encoding="utf-8"))
    sage_checks = json.loads((ASSETS / "sage-math-checks.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schemas/foundation/function-asset-identity-card.schema.json").read_text(encoding="utf-8"))
    mirror = json.loads((ROOT / "data/foundation/schemas/function-asset-identity-card.schema.json").read_text(encoding="utf-8"))

    schema_errors = []
    validator = jsonschema.Draft202012Validator(schema)
    for index, row in enumerate(cards):
        error = next(validator.iter_errors(row), None)
        if error:
            schema_errors.append(f"row={index} id={row.get('canonical_id')} {error.message}")
            break
    check("schema:identity-cards", not schema_errors, schema_errors[0] if schema_errors else f"rows={len(cards)}")
    check("schema:mirrors-identical", schema == mirror)

    census_ids = [row["stable_id"] for row in census]
    card_ids = [row["canonical_id"] for row in cards]
    ledger_ids = [row["canonical_id"] for row in ledger]
    obligation_ids = [row["canonical_id"] for row in obligations]
    dependency_ids = [row["canonical_id"] for row in dependency]
    check("closure:unique-census", len(census_ids) == len(set(census_ids)))
    check("closure:unique-cards", len(card_ids) == len(set(card_ids)))
    check("closure:one-card-per-discovery", set(card_ids) == set(census_ids) and len(card_ids) == len(census_ids))
    check("closure:one-ledger-per-card", ledger_ids == card_ids)
    check("closure:one-obligation-record-per-card", obligation_ids == card_ids)
    check("closure:one-dependency-record-per-card", dependency_ids == card_ids)
    check("closure:summary-closed", summary["registry_closed"] is True)
    check("closure:coverage-not-regressed", len(cards) >= 2033, f"cards={len(cards)}")
    check("closure:source-anchor-present", all(card["source_anchors"] for card in cards))
    check("closure:source-files-exist", all(source_exists(anchor["path"]) for card in cards for anchor in card["source_anchors"]))
    check("closure:line-ranges-valid", all(anchor["first_line"] <= anchor["last_line"] for card in cards for anchor in card["source_anchors"]))
    check("closure:record-hashes", all(card["record_sha256"] == record_hash(card) for card in cards))

    card_by_id = {row["canonical_id"]: row for row in cards}
    task98_ids = {row["canonical_id"] for row in cards if row["reviewer_state"] == "TASK98_HUMAN_ADJUDICATION_RECONFIRMED"}
    check("authority:task98-exact-targets", task98_ids == EXPECTED_TASK98, f"actual={sorted(task98_ids)}")
    check("authority:auto-never-external-truth", all(not row["external_evidence_maturity"] in {"E5", "E6", "E7"} for row in cards if row["reviewer_state"] != "TASK98_HUMAN_ADJUDICATION_RECONFIRMED"))
    check("authority:m-e-independent", card_by_id["T2"]["mathematical_maturity"] == "M6" and card_by_id["T2"]["external_evidence_maturity"] == "E0")
    check("authority:unresolved-quarantined", all(row["final_disposition"] == "QUARANTINE_UNTIL_DEFINED" for row in cards if row["primary_identity"] == "UNRESOLVED_IDENTITY"))
    check("authority:low-maturity-theorems-not-established", all(not row["final_disposition"] == "KEEP_AS_ESTABLISHED_MATH" for row in cards if row["primary_identity"] == "CONJECTURE_OR_RESEARCH_CANDIDATE" and row["mathematical_maturity"] < "M4"))
    check("authority:algorithms-have-spec", all(row["definition"]["exact_expression_or_executable_specification"] != "UNSPECIFIED_IN_SOURCE" for row in cards if row["final_disposition"] == "KEEP_AS_ALGORITHM"))
    check("authority:every-record-has-ceiling", all(row["claim_ceiling"].strip() for row in cards))
    check("authority:every-record-has-allowed-and-prohibited-uses", all(row["allowed_uses"] and row["prohibited_uses"] for row in cards))

    all_ids = set(card_ids)
    check("dependency:no-dangling-parent", all(not row["dangling_parents"] for row in dependency))
    check("dependency:all-links-resolve", all(set(row["parents"] + row["children"] + row["transitive_children"]) <= all_ids for row in dependency))
    check("dependency:direct-symmetry", all(parent in card_by_id[child]["dependencies"]["parents"] for parent, card in card_by_id.items() for child in card["dependencies"]["children"]))

    quarantine_ids = {row["canonical_id"] for row in quarantine}
    expected_quarantine = {row["canonical_id"] for row in cards if row["final_disposition"] in {"QUARANTINE_UNTIL_DEFINED", "DOWNGRADE_TO_CONJECTURE", "DOWNGRADE_TO_PENDING", "REWRITE_AND_RETEST"}}
    check("quarantine:complete", quarantine_ids == expected_quarantine)
    check("quarantine:reasons-and-resume-keys", all(row["reason"] and row["resume_key"] == f"task99:{row['canonical_id']}" for row in quarantine))

    check("public:every-claim-traceable", all(source_exists(row["source_path"]) and row["line"] >= 1 for row in public_claims))
    check("public:withdrawn-lineage-present", any(row["lineage"] == "PHYSICS_UNIFICATION_NOGO" for row in withdrawn))
    check("public:no-blocked-rebound", all(row["status"] != "BLOCKED_REBOUND" for row in rebounds), canonical_json([row for row in rebounds if row["status"] == "BLOCKED_REBOUND"]))
    check("public:open-unification-boundary", "remains open" in card_by_id["D190"]["claim_ceiling"])

    check("summary:identity-accounting", sum(summary["identity_distribution"].values()) == len(cards))
    check("summary:maturity-accounting", sum(summary["mathematical_maturity_distribution"].values()) == len(cards))
    check("summary:evidence-accounting", sum(summary["external_evidence_distribution"].values()) == len(cards))
    check("summary:disposition-accounting", sum(summary["disposition_distribution"].values()) == len(cards))
    check("summary:counts", summary["canonical_identity_cards"] == len(cards) and summary["counterexample_records"] == len(counterexamples) and summary["explicit_quarantine_or_pending"] == len(quarantine))
    check("math:sympy-python-scoped-checks", math_checks["status"] == "PASS" and math_checks["checks_total"] == math_checks["checks_passed"] == 7)
    check("math:sage-independent-checks", sage_checks["status"] == "PASS" and sage_checks["checks_total"] == sage_checks["checks_passed"] == 5)
    check("math:scope-does-not-claim-physics", all("no external physics claim" in item["scope"] for item in (math_checks, sage_checks)))
    check("coverage:every-discovery-has-card", coverage["coverage_assertions"]["every_discovery_has_card"] is True)
    check("coverage:every-card-has-anchor", coverage["coverage_assertions"]["every_card_has_source_anchor"] is True)

    examples = [
        json.loads(line) for line in (ROOT / "tests/foundation/fixtures/function_asset_identity_task99.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    check("fixtures:twelve-identities", len(examples) == 12 and len({row["primary_identity"] for row in examples}) == 12)
    discovery_fixture = (ROOT / "tests/foundation/fixtures/function_asset_discovery_v2.txt").read_text(encoding="utf-8")
    check("fixtures:discovery-explicit-id", "D9999" in discovery_fixture)
    check("fixtures:discovery-code", "def bounded_transform" in discovery_fixture)
    check("fixtures:discovery-expression", "Φ(x)" in discovery_fixture)

    generator = subprocess.run([sys.executable, "tools/foundation/adjudicate_function_assets.py", "--check"], cwd=ROOT, text=True, capture_output=True)
    check("generator:deterministic", generator.returncode == 0, generator.stdout + generator.stderr)

    for name, ok, detail in checks:
        print(("PASS" if ok else "FAIL") + " " + name + (" " + detail if detail else ""))
    passed = sum(ok for _, ok, _ in checks)
    print(f"CHECKS_TOTAL={len(checks)} CHECKS_PASSED={passed} CHECKS_FAILED={len(checks) - passed}")
    if passed == len(checks):
        print("FUNCTION_ASSET_REGISTRY_CLOSURE_VALID")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
