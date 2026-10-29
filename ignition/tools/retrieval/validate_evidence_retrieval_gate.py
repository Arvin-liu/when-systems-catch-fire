#!/usr/bin/env python3
"""Fail-closed 121Q38-I1 evidence-retrieval validator."""
import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from tools.observation.validate_observation_prediction_gate import _verify_git_binding
SCHEMA = ROOT / "schemas/retrieval/evidence-retrieval-contract.schema.json"
Q37_REPAIR_HEAD = "7a01b1958c3f6b6eff559be85ec5e47eecff313c"
Q37_SEED_PATH = "data/analogy/fixtures/06-transportability-candidate-pass.json"
NAMES = {
    0: "GATE_PASS", 2: "SCHEMA_ERROR", 3: "Q37_SEED_UNAUDITED",
    4: "SUPPORT_ONLY_SEARCH", 5: "NEGATIVE_RESULT_DELETED",
    6: "DUPLICATE_SOURCE_FAMILY_COUNTED", 7: "RIGHTS_BYPASS",
    8: "STALE_EVIDENCE", 9: "REPRESENTATIVENESS_MISSING",
    10: "QUANTITY_VOTE_FORBIDDEN", 11: "MECHANISM_UPGRADE_FORBIDDEN",
    12: "STOP_CONDITION_REWRITTEN", 13: "SELECTIVE_EXCLUSION",
    14: "CLAIM_CEILING_OVERREACH", 15: "PROVENANCE_OR_DIGEST_INVALID",
    16: "SELECTION_LOG_INCOMPLETE", 17: "Q39_EXPORT_MISSING",
    18: "COUNTEREVIDENCE_OVERRIDDEN", 19: "TEMPORAL_METADATA_INVALID",
    20: "UNBOUNDED_SEARCH", 21: "REFERENCE_INTEGRITY_ERROR"
}
KINDS = {"SUPPORT", "COUNTEREXAMPLE", "BOUNDARY_CASE", "NEGATIVE_RESULT", "FAILED_RETRIEVAL"}
NEGATIVE_KINDS = {"COUNTEREXAMPLE", "NEGATIVE_RESULT", "FAILED_RETRIEVAL"}
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
OVERCLAIM = ("proves shared mechanism", "mechanism proven", "universal law proven", "causal proof established", "same mechanism in both domains")


def result(code, errors):
    return {"gate": "q38_i1_evidence_retrieval_gate", "exit_code": code,
            "exit_name": NAMES[code], "errors": errors,
            "boundary": "repository retrieval governance only; no mechanism or causal proof"}


def schema_errors(bundle):
    try:
        import jsonschema
        validator = jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text()))
        return [f"{'.'.join(map(str, e.absolute_path)) or '<root>'}: {e.message}"
                for e in sorted(validator.iter_errors(bundle), key=lambda x: list(x.absolute_path))][:25]
    except ImportError:
        required = ("audited_search_seed", "search_plan", "evidence_items", "selection_log",
                    "stop_assessment", "q39_failure_exports", "conclusion")
        return [f"missing {key}" for key in required if key not in bundle]


def check_seed(b):
    s = b["audited_search_seed"]
    errors = []
    if s.get("q37_lifecycle") != "audited" or s.get("q38_search_permission") != "ALLOWED_AS_RESTRICTED_SEED" or s.get("purpose") != "search_seed":
        errors.append("seed is not an audited Q37 restricted search seed")
    binding = b.get("q37_seed_binding")
    content, binding_error = _verify_git_binding(binding)
    if binding_error:
        errors.append(f"Q37 seed binding invalid: {binding_error}")
        return errors
    if binding.get("path") != Q37_SEED_PATH or binding.get("exact_commit") != Q37_REPAIR_HEAD:
        errors.append("seed does not bind the canonical Q37 repair restricted-seed artifact")
        return errors
    if s.get("q37_exact_head") != binding.get("exact_commit") or s.get("seed_digest") != binding.get("sha256"):
        errors.append("seed head/digest does not match canonical Q37 bytes")
    try:
        source = json.loads(content)
    except (TypeError, json.JSONDecodeError):
        errors.append("canonical Q37 seed bytes are not JSON")
        return errors
    candidates = {item.get("analogy_id"): item for item in source.get("analogy_candidates", [])}
    decisions = {item.get("decision_id"): item for item in source.get("audit_decisions", [])}
    candidate = candidates.get(s.get("q37_candidate_ref"))
    decision = decisions.get(s.get("q37_decision_ref"))
    if not candidate or candidate.get("lifecycle", {}).get("status") != "audited":
        errors.append("seed candidate does not resolve to canonical audited Q37 bytes")
    if not decision or decision.get("analogy_id") != s.get("q37_candidate_ref") or decision.get("q38_search_permission") != "ALLOWED_AS_RESTRICTED_SEED":
        errors.append("seed decision does not resolve to canonical restricted-search permission")
    return errors


def check_balanced_plan(b):
    plan = b["search_plan"]
    targets = {q.get("target_kind") for q in plan.get("query_plan", [])}
    required = set(plan.get("required_evidence_kinds", []))
    if targets != KINDS or required != KINDS:
        return [f"balanced plan requires exactly {sorted(KINDS)}; targets={sorted(targets)} required={sorted(required)}"]
    return []


def check_negative_preservation(b):
    items = b["evidence_items"]
    present = {i.get("kind") for i in items}
    errors = []
    if not NEGATIVE_KINDS.issubset(present):
        errors.append("counterexample, negative result and failed retrieval must all be preserved")
    if b["conclusion"].get("negative_results_preserved") is not True:
        errors.append("conclusion deletes or denies negative results")
    return errors


def check_duplicate_families(b):
    seen = {}
    errors = []
    for item in b["evidence_items"]:
        if item.get("selection_status") != "INCLUDED":
            continue
        family = item.get("source_family")
        if family in seen and not item.get("duplicate_of"):
            errors.append(f"{item.get('evidence_id')}: included source family {family} already counted by {seen[family]}")
        else:
            seen.setdefault(family, item.get("evidence_id"))
    if b["stop_assessment"].get("independent_source_family_count") != len(seen):
        errors.append("independent_source_family_count does not equal deduplicated included families")
    return errors


def check_rights(b):
    errors = []
    for item in b["evidence_items"]:
        rights = item.get("rights_status")
        mode = item.get("publication_mode")
        if rights in {"UNKNOWN", "PENDING", "REJECTED"} and mode != "NOT_PUBLISHABLE":
            errors.append(f"{item.get('evidence_id')}: {rights} material cannot be published")
        if rights == "CITATION_ONLY" and mode not in {"CITATION_ONLY", "NOT_PUBLISHABLE"}:
            errors.append(f"{item.get('evidence_id')}: citation-only rights exceeded")
    return errors


def check_freshness(b):
    return [f"{i.get('evidence_id')}: stale time-sensitive evidence"
            for i in b["evidence_items"]
            if i.get("freshness", {}).get("time_sensitive") and i.get("freshness", {}).get("status") == "STALE"]


def check_representativeness(b):
    errors = []
    statement = b["conclusion"].get("statement", "").lower()
    generalizes = any(t in statement for t in ("all populations", "all domains", "generally proves", "universal"))
    for item in b["evidence_items"]:
        rep = item.get("representativeness", {})
        if not rep.get("domain") or not rep.get("population"):
            errors.append(f"{item.get('evidence_id')}: representativeness metadata missing")
        if generalizes and rep.get("status") not in {"REPRESENTATIVE_WITHIN_SCOPE", "NOT_APPLICABLE"}:
            errors.append(f"{item.get('evidence_id')}: generalization exceeds representativeness")
    return errors


def check_quantity_vote(b):
    c = b["conclusion"]
    text = c.get("statement", "").lower()
    if c.get("quantity_vote_used") or any(x in text for x in ("majority of cases proves", "more cases therefore true", "case count proves")):
        return ["case quantity was used as a truth or mechanism vote"]
    return []


def check_mechanism_upgrade(b):
    text = " ".join([b["conclusion"].get("statement", ""), b["conclusion"].get("claim_ceiling", "")]).lower()
    if b["conclusion"].get("mechanism_proven") or any(t in text for t in OVERCLAIM):
        return ["case similarity or retrieval result upgraded to mechanism/causal proof"]
    return []


def expected_digest(text):
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


def check_stop(b):
    p, s = b["search_plan"], b["stop_assessment"]
    errors = []
    if p.get("stop_condition_digest") != expected_digest(p.get("stop_condition", "")):
        errors.append("plan stop_condition_digest does not match frozen stop condition")
    if s.get("original_stop_condition") != p.get("stop_condition") or s.get("original_stop_condition_digest") != p.get("stop_condition_digest") or s.get("post_hoc_rewrite"):
        errors.append("stop condition was rewritten after retrieval")
    return errors


def check_exclusion(b):
    errors = []
    for item in b["evidence_items"]:
        if item.get("selection_status") == "EXCLUDED" and (not item.get("selection_criterion_ref") or not item.get("selection_reason")):
            errors.append(f"{item.get('evidence_id')}: selective exclusion lacks criterion/reason")
        if item.get("kind") in NEGATIVE_KINDS and item.get("selection_status") == "EXCLUDED" and not item.get("q39_export_required"):
            errors.append(f"{item.get('evidence_id')}: excluded negative evidence not retained for Q39")
    return errors


def check_ceiling(b):
    c = b["conclusion"]
    if not c.get("q37_ceiling_preserved"):
        return ["Q37 claim ceiling was not preserved"]
    q37 = b["audited_search_seed"].get("q37_claim_ceiling", "").lower()
    q38 = c.get("claim_ceiling", "").lower()
    positive_overclaim = any(token in q38 for token in ("universal law proven", "causal proof established", "mechanism equivalence proven")) or q38.strip() == "universal causal proof"
    if positive_overclaim or ("candidate_only" in q37 and "candidate_only" not in q38):
        return ["Q38 claim ceiling exceeds Q37"]
    return []


def check_provenance(b):
    errors = []
    if not DIGEST_RE.match(str(b["audited_search_seed"].get("seed_digest", ""))):
        errors.append("seed digest malformed")
    for item in b["evidence_items"]:
        eid = item.get("evidence_id")
        if not item.get("source_locator") or not item.get("provenance"):
            errors.append(f"{eid}: provenance/locator invalid")
            continue
        if item.get("kind") == "FAILED_RETRIEVAL" or item.get("retrieval_status") == "FAILED_UNPERFORMED":
            if item.get("kind") != "FAILED_RETRIEVAL" or item.get("retrieval_status") != "FAILED_UNPERFORMED" or item.get("selection_status") != "FAILED":
                errors.append(f"{eid}: failed/unperformed retrieval state is inconsistent")
            if item.get("source_binding") is not None or item.get("source_digest") is not None:
                errors.append(f"{eid}: failed/unperformed retrieval must not invent retrieved-byte evidence")
            if item.get("exact_head") != Q37_REPAIR_HEAD:
                errors.append(f"{eid}: failed retrieval context must bind the Q37 repair head")
            continue
        if item.get("retrieval_status") != "RETRIEVED_REPOSITORY_BYTES":
            errors.append(f"{eid}: successful evidence lacks retrieved-byte status")
            continue
        binding = item.get("source_binding")
        content, binding_error = _verify_git_binding(binding)
        if binding_error:
            errors.append(f"{eid}: retrieved-byte binding invalid: {binding_error}")
            continue
        if item.get("source_locator") != binding.get("path"):
            errors.append(f"{eid}: locator does not equal the bound repository path")
        if item.get("source_digest") != binding.get("sha256") or item.get("exact_head") != binding.get("exact_commit"):
            errors.append(f"{eid}: digest/head does not bind the actual retrieved bytes")
    return errors


def check_selection_log(b):
    items = {i.get("evidence_id"): i for i in b["evidence_items"]}
    logs = {l.get("evidence_id"): l for l in b["selection_log"]}
    errors = []
    for eid, item in items.items():
        log = logs.get(eid)
        if not log:
            errors.append(f"{eid}: missing selection log")
            continue
        expected = {"INCLUDED": "INCLUDE", "EXCLUDED": "EXCLUDE", "FAILED": "RECORD_FAILED_RETRIEVAL"}[item.get("selection_status")]
        if log.get("action") != expected or not log.get("append_only"):
            errors.append(f"{eid}: selection log inconsistent")
    return errors


def check_q39_exports(b):
    exports = {e.get("evidence_id") for e in b["q39_failure_exports"]}
    return [f"{i.get('evidence_id')}: required Q39 failure export missing"
            for i in b["evidence_items"] if i.get("kind") in NEGATIVE_KINDS and i.get("q39_export_required") and i.get("evidence_id") not in exports]


def check_counter_override(b):
    text = b["conclusion"].get("statement", "").lower()
    if "counterexample overridden" in text or "support grade cancels counterexample" in text:
        return ["support evidence was used to erase counterevidence"]
    return []


def parse_time(value):
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def check_temporal(b):
    errors = []
    for item in b["evidence_items"]:
        accessed = parse_time(item.get("accessed_at", ""))
        as_of = parse_time(item.get("freshness", {}).get("as_of", ""))
        if not accessed or not as_of or as_of > accessed:
            errors.append(f"{item.get('evidence_id')}: access/as-of time invalid")
    return errors


def check_bound(b):
    p, s = b["search_plan"], b["stop_assessment"]
    if not p.get("stop_condition") or s.get("status") == "NOT_STOPPED" or not s.get("stopped_at"):
        return ["search has no satisfied bounded stop condition"]
    return []


def check_refs(b):
    items = {i.get("evidence_id") for i in b["evidence_items"]}
    gaps = {g.get("gap_id") for g in b["unresolved_evidence_gaps"]}
    errors = []
    for log in b["selection_log"]:
        if log.get("evidence_id") not in items:
            errors.append(f"selection log references missing evidence {log.get('evidence_id')}")
    for exp in b["q39_failure_exports"]:
        if exp.get("evidence_id") not in items:
            errors.append(f"Q39 export references missing evidence {exp.get('evidence_id')}")
    for ref in b["conclusion"].get("unresolved_gap_refs", []):
        if ref not in gaps:
            errors.append(f"conclusion references missing gap {ref}")
    return errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", required=True)
    ap.add_argument("--report")
    args = ap.parse_args()
    try:
        bundle = json.loads(Path(args.bundle).read_text())
    except Exception as exc:
        out = result(2, [f"cannot load bundle: {exc}"])
        print(json.dumps(out, indent=2)); sys.exit(2)
    checks = [
        (2, lambda: schema_errors(bundle)), (3, lambda: check_seed(bundle)),
        (4, lambda: check_balanced_plan(bundle)), (5, lambda: check_negative_preservation(bundle)),
        (6, lambda: check_duplicate_families(bundle)), (7, lambda: check_rights(bundle)),
        (8, lambda: check_freshness(bundle)), (9, lambda: check_representativeness(bundle)),
        (10, lambda: check_quantity_vote(bundle)), (11, lambda: check_mechanism_upgrade(bundle)),
        (12, lambda: check_stop(bundle)), (13, lambda: check_exclusion(bundle)),
        (14, lambda: check_ceiling(bundle)), (15, lambda: check_provenance(bundle)),
        (16, lambda: check_selection_log(bundle)), (17, lambda: check_q39_exports(bundle)),
        (18, lambda: check_counter_override(bundle)), (19, lambda: check_temporal(bundle)),
        (20, lambda: check_bound(bundle)), (21, lambda: check_refs(bundle))]
    for code, check in checks:
        errors = check()
        if errors:
            out = result(code, errors)
            text = json.dumps(out, indent=2, ensure_ascii=False)
            print(text)
            if args.report: Path(args.report).write_text(text + "\n")
            sys.exit(code)
    out = result(0, [])
    text = json.dumps(out, indent=2, ensure_ascii=False)
    print(text)
    if args.report: Path(args.report).write_text(text + "\n")
    sys.exit(0)


if __name__ == "__main__":
    main()
