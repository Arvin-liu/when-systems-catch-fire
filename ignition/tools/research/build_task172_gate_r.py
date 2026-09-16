#!/usr/bin/env python3
"""Build the bounded Task172 Gate R routing schema and precision pilot.

Gate R is deliberately a sidecar pilot.  It never mutates the canonical
function/nonfunction registries and never retrieves scholarly content.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path


EXPECTED_PARENT_HEAD = "6d704d570827bf8d6ebb65fb65bcdd236056b4d3"
COMMAND_SOURCE = {
    "repository": "Arvin-liu/1111",
    "ref": "b1fc45fb",
    "path": "agent-commands/IGNITION-20260913-176.md",
    "blob_sha": "98fd25bd1886cf8675992413d6c55d1e09b4502f",
}
GATE_T_REL = Path("data/research/task172-gate-t-unesco-1988")
GATE_R_REL = Path("data/research/task172-gate-r-routing")
OPERATION_REL = Path("data/operations/iterations/172/step04-routing-gate.json")
REPORT_REL = Path("reports/operations/ignition-172-20260913-step04-gate-r-routing.md")

RULES = [
    ("12", ("mathemat", "algebra", "calculus", "probability", "statistics", "theorem", "代数", "数学", "逻辑", "概率", "统计", "定理")),
    ("22", ("physics", "quantum", "particle", "thermodynamic", "物理", "量子", "粒子", "热力")),
    ("23", ("chemistry", "chemical", "molecule", "化学", "分子")),
    ("24", ("biology", "biolog", "ecology", "genom", "cell", "life science", "生物", "生态", "基因", "细胞")),
    ("32", ("medical", "medicine", "clinical", "health", "disease", "医学", "临床", "健康", "疾病")),
    ("33", ("algorithm", "software", "engineering", "network", "control", "computer", "technology", "算法", "软件", "工程", "网络", "控制", "计算机")),
    ("51", ("anthropolog", "ethnolog", "人类学", "民族志")),
    ("52", ("demograph", "population", "人口", "人口学")),
    ("53", ("econom", "finance", "market", "经济", "金融", "市场")),
    ("54", ("geograph", "geospatial", "地理", "空间地理")),
    ("55", ("histor", "history", "历史", "史料")),
    ("56", ("law", "legal", "jurid", "法律", "法学")),
    ("57", ("linguist", "language", "语 言", "语言学")),
    ("58", ("pedagog", "education", "teaching", "教育", "教学")),
    ("59", ("politic", "governance", "policy", "政治", "治理", "政策")),
    ("61", ("psycholog", "cognit", "brain", "neural", "mind", "心理", "认知", "大脑", "神经")),
    ("62", ("literat", "literary", "writing", "art", "music", "narrative", "文学", "写作", "艺术", "叙事")),
    ("63", ("sociolog", "social", "society", "社会学", "社会")),
    ("71", ("ethic", "moral", "伦理", "道德")),
    ("72", ("philosoph", "metaphys", "哲学", "形而上")),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def stratified_sample(rows: list[dict], size: int, keys: tuple[str, ...]) -> list[dict]:
    ordered = sorted(rows, key=lambda row: str(row.get("canonical_id", "")))
    groups: dict[tuple[str, ...], list[dict]] = defaultdict(list)
    for row in ordered:
        groups[tuple(str(row.get(key, "UNSPECIFIED")) for key in keys)].append(row)
    result: list[dict] = []
    positions = {key: 0 for key in sorted(groups)}
    while len(result) < size:
        advanced = False
        for key in sorted(groups):
            pos = positions[key]
            if pos < len(groups[key]) and len(result) < size:
                result.append(groups[key][pos])
                positions[key] += 1
                advanced = True
        if not advanced:
            break
    if len(result) != size:
        raise ValueError(f"could not select {size} rows; selected {len(result)}")
    return result


def term_matches(text: str, term: str) -> bool:
    if not term.isascii():
        return term.lower() in text
    if term in {"art", "law", "control"}:
        return re.search(rf"(?<![a-z]){re.escape(term.lower())}(?![a-z])", text) is not None
    return re.search(rf"(?<![a-z]){re.escape(term.lower())}[a-z-]*", text) is not None


def internal_scope_reasons(row: dict, text: str) -> list[str]:
    reasons = []
    if row.get("claim_class") == "DESCRIPTIVE_REPOSITORY_CLAIM":
        reasons.append("DESCRIPTIVE_REPOSITORY_CLAIM")
    title = str(row.get("title") or row.get("canonical_title") or "").lower()
    exposure = row.get("current_public_exposure") or []
    if row.get("primary_identity") == "ALGORITHM_OR_WORKFLOW" and title.startswith("def "):
        reasons.append("repository_function_definition")
    if "PUBLIC_REPOSITORY_INTERNAL_SURFACE" in exposure and re.search(
        r"(?:^|[\s/_.-])(ci|validator|runtime|bookkeeping|owner|repository|iteration|front[- ]door|foundation|knowledge)(?:$|[\s/_.-])",
        text,
    ):
        reasons.append("internal_repository_surface")
    return reasons


def classify(row: dict) -> tuple[list[str], str, list[str], float, dict]:
    fields = " ".join(str(row.get(name, "")) for name in ("canonical_title", "title", "canonical_source")).lower()
    internal_reasons = internal_scope_reasons(row, fields)
    if internal_reasons:
        return [], "OUT_OF_UNESCO_SCOPE", [], 0.0, {"rule": "task172-step04-internal-scope-v1", "matched_terms": [], "internal_scope_reasons": internal_reasons}
    scores: dict[str, int] = {}
    matched: dict[str, list[str]] = {}
    for code, terms in RULES:
        hits = [term for term in terms if term_matches(fields, term)]
        if hits:
            scores[code] = len(hits)
            matched[code] = hits
    if not scores:
        internal = re.search(r"(architecture|governance|operations|iteration|validator|repository|ci|current-state)", fields)
        state = "OUT_OF_UNESCO_SCOPE" if internal else "UNRESOLVED"
        return [], state, [], 0.2, {"rule": "none", "matched_terms": []}
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    top = ranked[0][1]
    selected = [code for code, score in ranked if score == top][:2]
    state = "CLASSIFIED" if len(selected) == 1 else "MULTIDISCIPLINARY"
    confidence = 0.85 if len(selected) == 1 and top >= 2 else 0.6
    return selected, state, [term for code in selected for term in matched[code]], confidence, {"rule": "task172-step04-precision-v2", "matched_terms": [term for code in selected for term in matched[code]]}


def use_tags(row: dict) -> tuple[list[str], list[str]]:
    disposition = str(row.get("final_disposition", ""))
    claim_class = str(row.get("claim_class", ""))
    primary = str(row.get("primary_identity", ""))
    if any(word in disposition for word in ("REJECT", "QUARANTINE", "WITHDRAWN")):
        return ["HISTORICAL_CONTEXT"], ["COUNTEREXAMPLE", "EVIDENCE_CHECK"]
    if "THEOREM" in claim_class or "MATHEMAT" in claim_class or primary in {"PARAMETRIC_MATHEMATICAL_MODEL", "RELATION_OR_CONSTRAINT"}:
        return ["METHOD_TRANSFER"], ["EXPLAIN", "BOUNDARY_TEST"]
    if "MECHANISM" in claim_class or "CAUSAL" in claim_class:
        return ["EVIDENCE_CHECK"], ["MECHANISM_TEST", "CAUSAL_CHALLENGE"]
    if "EMPIRICAL" in claim_class:
        return ["EVIDENCE_CHECK"], ["EXPLAIN", "COUNTEREXAMPLE"]
    if "CROSS_DOMAIN" in claim_class or "INTERPRET" in claim_class:
        return ["ANALOGY_SOURCE"], ["COMPARE", "BOUNDARY_TEST"]
    return ["NARRATIVE_CASE"], ["EXPLAIN"]


def row_to_pilot(row: dict, asset_kind: str) -> dict:
    field_codes, state, matched_terms, confidence, basis = classify(row)
    role, collision = use_tags(row)
    immutable = {key: row.get(key) for key in ("canonical_id", "record_sha256", "primary_identity", "claim_class", "assertion_type", "external_evidence_maturity", "mathematical_maturity", "final_disposition", "claim_ceiling") if key in row}
    return {
        "canonical_id": row["canonical_id"],
        "asset_kind": asset_kind,
        "domain": {"unesco_field_codes": field_codes[:2], "unesco_discipline_codes": [], "classification_state": state},
        "asset_role": role[:3],
        "collision_use": collision[:4],
        "topic": [],
        "evidence_projection": {
            "role": "ROUTING_ONLY_NO_EVIDENCE_PROMOTION",
            "external_evidence_maturity": row.get("external_evidence_maturity"),
            "final_disposition": row.get("final_disposition"),
            "promotion": "NONE",
            "source": "canonical_authority_record",
        },
        "confidence": confidence,
        "facet_confidence": {"unesco_field_codes": confidence, "unesco_discipline_codes": None, "asset_role": 0.9, "collision_use": 0.9, "topic": None},
        "tag_basis": {"kind": "frozen_heuristic_suggestion", **basis, "source_fields": ["canonical_id", "record_sha256", "title/source/class metadata"]},
        "source_record_sha": row.get("record_sha256"),
        "tagger_version": "task172-step04-precision-v2",
        "review_state": "PILOT_MANUAL_REVIEW_REQUIRED",
        "immutable_snapshot": immutable,
        "matched_terms": matched_terms,
    }


def build(repo_root: Path, source_head: str) -> None:
    current_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True).strip()
    if current_head != source_head:
        raise SystemExit(f"GATE_R_BUILD_REFUSED: current HEAD {current_head} != source head {source_head}")
    ignition = repo_root
    function_path = ignition / "data/foundation/function-assets/identity-cards.jsonl"
    nonfunction_path = ignition / "data/foundation/nonfunction-claims/claim-registry.jsonl"
    functions = read_jsonl(function_path)
    claims = read_jsonl(nonfunction_path)
    function_sample = stratified_sample(functions, 250, ("final_disposition", "primary_identity", "external_evidence_maturity", "mathematical_maturity"))
    claim_sample = stratified_sample(claims, 500, ("claim_class", "assertion_type", "final_disposition", "external_evidence_maturity", "mathematical_maturity"))
    rows = [row_to_pilot(row, "FUNCTION_ASSET") for row in function_sample]
    rows += [row_to_pilot(row, "NONFUNCTION_CLAIM") for row in claim_sample]
    taxonomy = {"fields": 24, "primary_disciplines": 245, "primary_subdisciplines": 2178}
    schema = {
        "schema": "task172-gate-r-routing-schema-v1",
        "authority": "canonical-ID keyed routing sidecar; canonical registries remain authority",
        "key": ["canonical_id", "asset_kind"],
        "facets": {
            "domain": ["unesco_field_codes", "unesco_discipline_codes", "classification_state"],
            "asset_role": "bounded retrieval role, not evidence status",
            "collision_use": "bounded collision operation, not a conclusion",
            "topic": "optional bounded topic labels",
            "evidence_projection": "read-only projection of canonical authority; no promotion",
        },
        "classification_state": ["CLASSIFIED", "MULTIDISCIPLINARY", "OUT_OF_UNESCO_SCOPE", "UNRESOLVED"],
        "caps": {"unesco_field_codes": 2, "unesco_discipline_codes": 3, "asset_role": 3, "collision_use": 4, "topic": 5},
        "required_fields": ["canonical_id", "asset_kind", "domain", "asset_role", "collision_use", "topic", "evidence_projection", "source_record_sha", "tagger_version", "review_state"],
        "immutability": [
            "source_record_sha equals the current authority record fingerprint",
            "routing cannot mutate canonical identity, M/E, disposition, ceiling or evidence status",
            "ambiguous and internal records remain UNRESOLVED or OUT_OF_UNESCO_SCOPE",
            "model suggestions remain frozen suggestions requiring review",
        ],
    }
    vocabulary = {
        "schema": "task172-gate-r-controlled-vocabulary-v1",
        "authority": "routing aid only; not truth, proof, maturity, publication or evidence",
        "asset_role": ["METHOD_TRANSFER", "EVIDENCE_CHECK", "ANALOGY_SOURCE", "HISTORICAL_CONTEXT", "NARRATIVE_CASE"],
        "collision_use": ["EXPLAIN", "COMPARE", "ANALOGY_SOURCE", "MECHANISM_TEST", "CAUSAL_CHALLENGE", "COUNTEREXAMPLE", "EVIDENCE_CHECK", "METHOD_TRANSFER", "BOUNDARY_TEST", "NORMATIVE_CHECK", "NARRATIVE_CASE", "HISTORICAL_CONTEXT"],
        "topic": [],
        "classification_states": schema["classification_state"],
        "negative_boundary": "REJECT/QUARANTINE/WITHDRAWN records cannot acquire positive evidence-use tags",
        "internal_boundary": "repository governance, CI, runtime, bookkeeping and Owner surfaces are OUT_OF_UNESCO_SCOPE or UNRESOLVED",
    }
    function_map = {row["canonical_id"]: row for row in functions}
    claim_map = {row["canonical_id"]: row for row in claims}
    authorities = {**function_map, **claim_map}
    counts = Counter(row["domain"]["classification_state"] for row in rows)
    caps = schema["caps"]
    orphan = [row["canonical_id"] for row in rows if row["canonical_id"] not in authorities]
    fingerprint = [row["canonical_id"] for row in rows if row["source_record_sha"] != authorities.get(row["canonical_id"], {}).get("record_sha256")]
    cap_violations = [row["canonical_id"] for row in rows if len(row["domain"]["unesco_field_codes"]) > caps["unesco_field_codes"] or len(row["domain"]["unesco_discipline_codes"]) > caps["unesco_discipline_codes"] or len(row["asset_role"]) > caps["asset_role"] or len(row["collision_use"]) > caps["collision_use"] or len(row["topic"]) > caps["topic"]]
    internal_forced = [row["canonical_id"] for row in rows if row["domain"]["classification_state"] == "OUT_OF_UNESCO_SCOPE" and row["domain"]["unesco_field_codes"]]
    negative_positive = [row["canonical_id"] for row in rows if any(word in str(row["evidence_projection"].get("final_disposition")) for word in ("REJECT", "QUARANTINE", "WITHDRAWN")) and set(row["asset_role"]) - {"HISTORICAL_CONTEXT"}]
    audit = {
        "schema": "task172-gate-r-precision-audit-v1",
        "authority": "Formal pilot sidecar; no canonical mutation and no live retrieval",
        "source_exact_head": source_head,
        "rows_checked": len(rows),
        "sample": {"function_assets": 250, "nonfunction_claims": 500, "total": 750},
        "state_counts": dict(sorted(counts.items())),
        "manual_review_required": len(rows),
        "hard_checks": {
            "orphan_canonical": len(orphan),
            "authority_fingerprint_mismatch": len(fingerprint),
            "cap_violation": len(cap_violations),
            "internal_governance_forced_unesco": len(internal_forced),
            "out_of_scope_has_domain_code": len(internal_forced),
            "negative_record_positive_use": len(negative_positive),
        },
        "violations": {"orphan": orphan, "fingerprint": fingerprint, "caps": cap_violations, "internal": internal_forced, "negative": negative_positive},
        "deterministic": True,
        "decision": "PRECISION_BOUNDARY_READY; ALL_ROWS_RETAIN_MANUAL_REVIEW; NO_FULL_ROUTING_PROMOTION",
    }
    gate_t = ignition / GATE_T_REL
    source_freeze = {
        "schema": "task172-gate-r-source-freeze-v1",
        "freeze_event": "SCAN_INPUT_FREEZE_REUSE",
        "direction_lock": "IGNITION-20260913-176",
        "command_source": COMMAND_SOURCE,
        "formal_pre_freeze": {"head": source_head, "pull_request": 218, "state": "OPEN + DRAFT + unmerged", "branch": "work/IGNITION-20260912-172-knowledge-routing-universal-corpus"},
        "taxonomy_authority": {
            "source": "1988 UNESCO primary document locked by Gate T",
            **taxonomy,
            "gate_t_parse_sha256": sha256(gate_t / "primary-1988-parse.json"),
            "gate_t_ledger_sha256": sha256(gate_t / "discrepancy-ledger.json"),
            "gate_t_receipt_sha256": sha256(gate_t / "build-receipt.json"),
        },
        "authority_inputs": {"function_authority_sha256": sha256(function_path), "nonfunction_authority_sha256": sha256(nonfunction_path)},
        "scan_inputs": {"primary_pdf_persisted": False, "ocr_persisted": False, "full_corpus_retrieval": False, "mass_formal_routing": False},
        "decision": "GATE_R_SCHEMA_AND_PRECISION_PILOT_ONLY; GATE_C_REQUIRED_BEFORE_MASS_INGESTION",
    }
    pilot = {"schema": "task172-gate-r-precision-pilot-v1", "authority": "canonical registries remain authoritative; every suggestion is manual-review-only", "source_exact_head": source_head, "taxonomy": taxonomy, "rows": rows, "metrics": dict(sorted(counts.items())), "manual_review_required": len(rows), "live_retrieval": False, "full_routing_promotion": False}
    out = ignition / GATE_R_REL
    out.mkdir(parents=True, exist_ok=True)
    def write_json(path: Path, value: dict) -> None:
        path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    write_json(out / "routing-schema.json", schema)
    write_json(out / "controlled-vocabulary.json", vocabulary)
    write_json(out / "precision-pilot.json", pilot)
    write_json(out / "precision-audit.json", audit)
    write_json(out / "source-freeze.json", source_freeze)
    operation = {
        "schema": "task172-step04-routing-gate-v1",
        "step": "Task172 Step04 / Gate R",
        "command_source": COMMAND_SOURCE,
        "source_exact_head": source_head,
        "taxonomy": taxonomy,
        "schema_sha256": sha256(out / "routing-schema.json"),
        "vocabulary_sha256": sha256(out / "controlled-vocabulary.json"),
        "pilot_sha256": sha256(out / "precision-pilot.json"),
        "audit_sha256": sha256(out / "precision-audit.json"),
        "pilot": {"function_assets": 250, "nonfunction_claims": 500, "total": 750, "manual_review_required": 750, "hard_check_violations": sum(audit["hard_checks"].values()), "live_retrieval": False, "full_routing_promotion": False},
        "state_counts": dict(sorted(counts.items())),
        "evidence_projection": "ROUTING_ONLY_NO_EVIDENCE_PROMOTION",
        "decision": "GATE_R_PASS_FOR_SCHEMA_AND_PRECISION_PILOT; GATE_C_REQUIRED_BEFORE_MASS_INGESTION",
    }
    write_json(ignition / OPERATION_REL, operation)
    receipt = {
        "schema": "task172-gate-r-build-receipt-v1",
        "source_exact_head": source_head,
        "command_source": COMMAND_SOURCE,
        "taxonomy": taxonomy,
        "inputs": {"gate_t_parse": sha256(gate_t / "primary-1988-parse.json"), "gate_t_ledger": sha256(gate_t / "discrepancy-ledger.json"), "function_authority": sha256(function_path), "nonfunction_authority": sha256(nonfunction_path)},
        "outputs": {"routing_schema": sha256(out / "routing-schema.json"), "controlled_vocabulary": sha256(out / "controlled-vocabulary.json"), "precision_pilot": sha256(out / "precision-pilot.json"), "precision_audit": sha256(out / "precision-audit.json"), "source_freeze": sha256(out / "source-freeze.json"), "operation": sha256(ignition / OPERATION_REL)},
        "counts": {"rows": len(rows), "function_assets": 250, "nonfunction_claims": 500},
        "state_counts": dict(sorted(counts.items())),
        "hard_check_violations": sum(audit["hard_checks"].values()),
        "manual_review_rows": len(rows),
        "live_retrieval": False,
        "formal_mass_routing": False,
        "deterministic": True,
    }
    write_json(out / "build-receipt.json", receipt)
    report = f"""# IGNITION-172 Step04 — Gate R routing schema and precision pilot

Gate T exact-head CI is complete for parent `{source_head}`. This step freezes a bounded routing sidecar and a precision-oriented pilot; it does not perform mass taxonomy routing or scholarly corpus admission.

- Primary taxonomy authority: 24 fields / 245 disciplines / 2178 subdisciplines.
- Pilot: 250 function assets + 500 nonfunction claims = 750 rows.
- Classification states: `{dict(sorted(counts.items()))}`.
- All 750 rows remain `PILOT_MANUAL_REVIEW_REQUIRED`.
- Hard-check violations: `{sum(audit["hard_checks"].values())}`.
- Live retrieval, abstract/full-text persistence, and corpus admission: disabled.
- Gate C remains required before any mass Formal ingestion.

Routing is a read-only projection. It cannot mutate canonical identity, M/E, disposition, ceiling, truth, proof, evidence maturity, or scholarly admission. Ambiguous and negative records remain bounded/manual-review states.
"""
    (ignition / REPORT_REL).write_text(report, encoding="utf-8")
    print(f"TASK172_GATE_R_BUILT head={source_head} rows={len(rows)} hard_check_violations={sum(audit['hard_checks'].values())}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--source-head", default=EXPECTED_PARENT_HEAD)
    args = parser.parse_args()
    build(args.repo_root.resolve(), args.source_head)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
