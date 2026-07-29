#!/usr/bin/env python3
"""Fail-closed validation for task-100 non-function claim closure."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import jsonschema

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/foundation/nonfunction-claims"
AUDITS = {
    "definition_audit", "quantifier_audit", "proof_audit", "counterexample_audit",
    "type_dimension_audit", "internal_external_audit", "model_class_audit",
    "cross_domain_audit", "evidence_audit", "novelty_audit", "prediction_audit",
    "conclusion_rebound_audit", "public_surface_audit",
}
QUARANTINE = {
    "PENDING_PROOF", "PENDING_EMPIRICAL_TEST", "PENDING_LITERATURE_ADJUDICATION",
    "REWRITE_AND_RETEST", "QUARANTINED_AMBIGUOUS", "WITHDRAWN_UNSUPPORTED",
    "REJECTED_FALSE_OR_INVALID",
}


def rows(name: str) -> list[dict]:
    return [json.loads(line) for line in (OUT / name).read_text(encoding="utf-8").splitlines() if line.strip()]


def canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def record_hash(row: dict) -> str:
    payload = dict(row)
    payload.pop("record_sha256", None)
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def main() -> int:
    checks: list[tuple[str, bool, str]] = []

    def check(name: str, condition: bool, detail: str = "") -> None:
        checks.append((name, bool(condition), detail))

    claims = rows("claim-registry.jsonl")
    discovery = rows("source-discovery.jsonl")
    ledger = rows("adjudication-ledger.jsonl")
    evidence = rows("evidence-lineage.jsonl")
    graph = rows("dependency-graph.jsonl")
    risks = rows("inference-risk-report.jsonl")
    rebounds = rows("conclusion-rebound-report.jsonl")
    public = rows("public-surface-report.jsonl")
    quarantine = rows("unresolved-quarantine.jsonl")
    supersession = rows("supersession-lineage.jsonl")
    summary = json.loads((OUT / "closure-summary.json").read_text(encoding="utf-8"))
    coverage = json.loads((OUT / "discovery-coverage.json").read_text(encoding="utf-8"))
    schema = json.loads((ROOT / "schemas/foundation/nonfunction-claim.schema.json").read_text(encoding="utf-8"))
    mirror = json.loads((ROOT / "data/foundation/schemas/nonfunction-claim.schema.json").read_text(encoding="utf-8"))

    schema_errors = []
    validator = jsonschema.Draft202012Validator(schema)
    for index, row in enumerate(claims):
        error = next(validator.iter_errors(row), None)
        if error:
            schema_errors.append(f"row={index} id={row.get('canonical_id')} {error.message}")
            break
    check("schema:claim-registry", not schema_errors, schema_errors[0] if schema_errors else f"rows={len(claims)}")
    check("schema:mirrors-identical", schema == mirror)

    ids = [row["canonical_id"] for row in claims]
    id_set = set(ids)
    check("closure:unique-canonical-ids", len(ids) == len(id_set))
    check("closure:coverage-not-regressed", len(claims) >= 15000, f"claims={len(claims)}")
    check("closure:existing-claims-mapped", sum(row["canonical_id"].startswith("CLAIM-") for row in claims) == 678)
    check("closure:one-ledger-per-claim", [row["canonical_id"] for row in ledger] == ids)
    check("closure:one-evidence-lineage-per-claim", [row["canonical_id"] for row in evidence] == ids)
    check("closure:one-graph-record-per-claim", [row["canonical_id"] for row in graph] == ids)
    check("closure:source-anchor-present", all(row["source_anchors"] for row in claims))
    check("closure:source-files-exist", all((ROOT / anchor["path"]).is_file() for row in claims for anchor in row["source_anchors"]))
    check("closure:source-lines-valid", all(anchor["first_line"] >= 1 and anchor["last_line"] >= anchor["first_line"] for row in claims for anchor in row["source_anchors"]))
    check("closure:record-hashes", all(row["record_sha256"] == record_hash(row) for row in claims))
    check("closure:all-thirteen-audits", all(set(row["audit_gates"]) == AUDITS for row in claims))
    check("closure:registry-closed", summary["registry_closed"] is True)

    listed_paths = [row["path"] for row in discovery]
    tracked_raw = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT)
    tracked_paths = sorted(item.decode("utf-8") for item in tracked_raw.split(b"\0") if item)
    check("discovery:every-repository-path-accounted", sorted(listed_paths) == tracked_paths and len(listed_paths) == len(set(listed_paths)), f"listed={len(listed_paths)} tracked={len(tracked_paths)}")
    check("discovery:every-candidate-maps", all(set(row["canonical_claim_ids"]) <= id_set for row in discovery))
    check("discovery:no-silent-exclusion", all(not row["coverage_status"].startswith("EXCLUDED") or row["exclusion_reason"] for row in discovery))
    check("discovery:coverage-assertions", all(coverage["assertions"].values()))

    check("maturity:axes-present", all(row["mathematical_maturity"].startswith("M") and row["external_evidence_maturity"].startswith("E") for row in claims))
    check("maturity:auto-never-high-external", all(row["external_evidence_maturity"] not in {"E5", "E6", "E7"} for row in claims if row["reviewer_state"] != "TASK98_99_AUTHORITY_INHERITED"))
    check("maturity:established-external-gated", all(row["external_evidence_maturity"] >= "E4" and row["replication_status"] == "EXTERNAL_REPLICATION_DOCUMENTED" for row in claims if row["final_disposition"] == "ACCEPTED_AS_ESTABLISHED_EXTERNAL_FACT"))
    check("maturity:proved-math-gated", all(row["mathematical_maturity"] >= "M4" and row["audit_gates"]["proof_audit"] == "PASS" for row in claims if row["final_disposition"] == "ACCEPTED_AS_PROVED_MATHEMATICAL_RESULT"))
    check("maturity:empirical-has-status", all(row["external_evidence_maturity"] and row["replication_status"] for row in claims if row["assertion_type"] == "EMPIRICAL"))
    check("maturity:no-local-test-external-promotion", all(row["final_disposition"] != "ACCEPTED_AS_ESTABLISHED_EXTERNAL_FACT" for row in claims if row["external_evidence_maturity"] in {"E0", "E1", "E2"}))

    by_id = {row["canonical_id"]: row for row in claims}
    check("authority:T2-carrier-scoped-math", by_id["CLAIM-T2"]["mathematical_maturity"] == "M6" and by_id["CLAIM-T2"]["external_evidence_maturity"] == "E0" and by_id["CLAIM-T2"]["final_disposition"] == "ACCEPTED_AS_PROVED_MATHEMATICAL_RESULT")
    check("authority:D127-metaphor", by_id["CLAIM-D127"]["final_disposition"] == "RETAINED_AS_STRUCTURAL_METAPHOR")
    check("authority:D182-D190-no-physical-unification", all(by_id[f"CLAIM-D{i}"]["final_disposition"] not in {"ACCEPTED_AS_PROVED_MATHEMATICAL_RESULT", "ACCEPTED_AS_ESTABLISHED_EXTERNAL_FACT"} for i in range(182, 191)))
    check("authority:D190-open-problem", "remains open" in by_id["CLAIM-D190"]["claim_ceiling"])
    check("authority:D260-no-real-world-threshold", "not a real-world" in by_id["CLAIM-D260"]["claim_ceiling"])

    check("dependency:records-declare-closure", all(row["all_edges_resolved_or_explicit"] for row in graph))
    check("dependency:targets-resolve-or-explicit", all(edge["resolution"] in {"RESOLVED", "EXPLICITLY_UNRESOLVED"} for row in graph for edge in row["outgoing"]))
    check("dependency:registered-claim-targets-exist", all(edge["target"] in id_set for row in graph for edge in row["outgoing"] if edge["target_kind"] == "REGISTERED_CLAIM"))

    quarantine_ids = {row["canonical_id"] for row in quarantine}
    expected_quarantine = {row["canonical_id"] for row in claims if row["final_disposition"] in QUARANTINE}
    check("quarantine:complete", quarantine_ids == expected_quarantine)
    check("quarantine:resume-keys", all(row["resume_key"] == f"task100:{row['canonical_id']}" for row in quarantine))
    check("quarantine:unresolved-not-current", all(by_id[cid]["final_disposition"] in QUARANTINE for cid in quarantine_ids))

    check("rebound:withdrawn-lineage-present", any(row["lineage"] == "PHYSICS_UNIFICATION_NOGO" for row in rebounds))
    check("rebound:no-active-alias", summary["active_conclusion_rebounds"] == 0)
    check("rebound:candidates-blocked", all(row["status"] == "BLOCKED_BY_DISPOSITION" and row["final_disposition"] == "WITHDRAWN_UNSUPPORTED" for row in rebounds if row["candidate"]))
    check("inference:model-failure-not-universal-proof", all(row["final_disposition"] not in {"ACCEPTED_AS_PROVED_MATHEMATICAL_RESULT", "ACCEPTED_AS_ESTABLISHED_EXTERNAL_FACT"} for row in claims if row["audit_gates"]["model_class_audit"] == "FAIL"))
    check("inference:analogy-not-isomorphism", all(row["final_disposition"] not in {"ACCEPTED_AS_PROVED_MATHEMATICAL_RESULT", "ACCEPTED_AS_ESTABLISHED_EXTERNAL_FACT"} for row in claims if row["audit_gates"]["cross_domain_audit"] == "FAIL"))
    check("inference:risk-records-blocked", all(row["blocked_by_disposition"] for row in risks if any(value == "FAIL" for value in row["risk_gates"].values())))

    check("public:front-doors-traceable", all((ROOT / row["source_path"]).is_file() and row["line"] >= 1 for row in public))
    check("public:no-claim-ceiling-violations", not any(row["current_violation"] for row in public))
    check("public:summary-agrees", summary["public_surface_violations"] == 0)
    check("history:supersession-preserved", bool(supersession) and all(row["source_anchors"] for row in supersession))

    check("summary:class-accounting", sum(summary["claim_class_distribution"].values()) == len(claims))
    check("summary:type-accounting", sum(summary["assertion_type_distribution"].values()) == len(claims))
    check("summary:disposition-accounting", sum(summary["disposition_distribution"].values()) == len(claims))
    check("summary:m-accounting", sum(summary["mathematical_maturity_distribution"].values()) == len(claims))
    check("summary:e-accounting", sum(summary["external_evidence_distribution"].values()) == len(claims))
    check("summary:counts", summary["canonical_claims"] == len(claims) and summary["explicit_quarantine_or_pending"] == len(quarantine))

    fixture_rows = [json.loads(line) for line in (ROOT / "tests/foundation/fixtures/nonfunction_claim_gate_cases.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    check("fixtures:physics-and-nonphysics", len(fixture_rows) >= 8 and {row["domain"] for row in fixture_rows} >= {"physics", "mathematics", "society", "consciousness", "AI"})
    check("fixtures:four-regressions", {row["expected_gate"] for row in fixture_rows} >= {"model_class_audit", "quantifier_audit", "cross_domain_audit", "evidence_audit", "conclusion_rebound_audit"})

    generator = subprocess.run([sys.executable, "tools/foundation/adjudicate_nonfunction_claims.py", "--check"], cwd=ROOT, text=True, capture_output=True)
    check("generator:deterministic", generator.returncode == 0, generator.stdout + generator.stderr)

    for name, ok, detail in checks:
        print(("PASS" if ok else "FAIL") + " " + name + (" " + detail if detail else ""))
    passed = sum(ok for _, ok, _ in checks)
    print(f"CHECKS_TOTAL={len(checks)} CHECKS_PASSED={passed} CHECKS_FAILED={len(checks) - passed}")
    if passed == len(checks):
        print("NONFUNCTION_CLAIM_EVIDENCE_LINEAGE_CLOSURE_VALID")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
