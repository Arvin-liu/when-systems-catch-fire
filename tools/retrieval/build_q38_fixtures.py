#!/usr/bin/env python3
"""Build the deterministic Q38 pilot and attack fixture matrix."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data/retrieval"
FX = OUT / "fixtures"
HEAD = "c97959d56a41126fbdc1e69ce8fdbc38a43956c0"
Q37 = "927cae48f3c65d3c23543dac4b9262704fabb6f1"
AT = "2026-07-21T17:31:00Z"


def digest(text):
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


def evidence(eid, kind, family, locator, summary, status="INCLUDED"):
    negative = kind in {"COUNTEREXAMPLE", "NEGATIVE_RESULT", "FAILED_RETRIEVAL"}
    return {
        "evidence_id": eid, "kind": kind, "source_id": "source." + eid,
        "source_family": family, "source_locator": locator,
        "provenance": "bounded repository replay at the Q37 frozen checkpoint; no external factual promotion",
        "source_digest": digest(locator + summary), "accessed_at": AT,
        "rights_status": "CLEAR", "publication_mode": "METADATA_AND_SUMMARY",
        "evidence_grade": "FAILED" if kind == "FAILED_RETRIEVAL" else "A_PRIMARY",
        "freshness": {"time_sensitive": False, "as_of": AT, "status": "NOT_APPLICABLE", "valid_until": None},
        "representativeness": {"domain": "repository_governance", "population": "Q34-Q37 frozen candidate artifacts", "status": "BOUNDARY_ONLY", "limits": ["repository replay only", "not representative of external domains"]},
        "selection_status": status, "selection_criterion_ref": "include.traceable-relevant",
        "selection_reason": "traceable item directly exercises the bounded seed and preserves its relation to the claim ceiling",
        "summary": summary, "supports_claim_refs": ["q37.restricted_seed"] if kind == "SUPPORT" else [],
        "challenges_claim_refs": ["q37.restricted_seed"] if negative else [],
        "duplicate_of": None, "q39_export_required": negative, "exact_head": HEAD
    }


def base():
    stop = "Stop after all five evidence kinds are recorded from traceable repository families, every negative or failed item is exported to Q39, duplicate families are collapsed, and remaining external-validity gaps are explicit."
    items = [
        evidence("ev.support.q37", "SUPPORT", "repo:q37-contract", "docs/analogy/q37-i1-architecture-decision.md", "Q37 explicitly emits a restricted search seed and forbids mechanism promotion."),
        evidence("ev.counter.q34", "COUNTEREXAMPLE", "repo:q34-analogy-attack", "data/discovery/fixtures/05-analogy-as-mechanism.json", "A structurally tempting analogy fails when treated as a mechanism."),
        evidence("ev.boundary.q37", "BOUNDARY_CASE", "repo:q37-counteranalogy", "data/analogy/fixtures/09-counteranalogy-preserved-pass.json", "A preserved counteranalogy is admissible only as a bounded audit result."),
        evidence("ev.negative.q37", "NEGATIVE_RESULT", "repo:q37-mechanism-insufficient", "data/analogy/fixtures/07-mechanism-evidence-insufficient.json", "Independent mechanism evidence is insufficient despite structural mapping."),
        evidence("ev.failed.external", "FAILED_RETRIEVAL", "attempt:external-unneeded", "retrieval-attempt://external-search-not-required-for-repository-pilot", "No external retrieval was performed because the bounded repository pilot already covers the contract and no external fact is claimed.", "FAILED")
    ]
    queries = [
        {"query_id": "q.support", "target_kind": "SUPPORT", "query": "find Q37 restricted-seed contract support", "source_priority": "REPOSITORY_PRIMARY"},
        {"query_id": "q.counter", "target_kind": "COUNTEREXAMPLE", "query": "find a case that breaks mechanism promotion", "source_priority": "REPOSITORY_PRIMARY"},
        {"query_id": "q.boundary", "target_kind": "BOUNDARY_CASE", "query": "find a preserved boundary or counteranalogy", "source_priority": "REPOSITORY_PRIMARY"},
        {"query_id": "q.negative", "target_kind": "NEGATIVE_RESULT", "query": "find a negative mechanism-evidence result", "source_priority": "REPOSITORY_PRIMARY"},
        {"query_id": "q.failed", "target_kind": "FAILED_RETRIEVAL", "query": "record bounded failed or deliberately unperformed retrieval", "source_priority": "CITATION_ONLY"}
    ]
    logs = []
    for idx, item in enumerate(items, 1):
        action = {"INCLUDED": "INCLUDE", "EXCLUDED": "EXCLUDE", "FAILED": "RECORD_FAILED_RETRIEVAL"}[item["selection_status"]]
        logs.append({"log_id": f"log.{idx}", "evidence_id": item["evidence_id"], "action": action, "criterion_ref": item["selection_criterion_ref"], "reason": item["selection_reason"], "recorded_at": AT, "append_only": True})
    exports = []
    for idx, item in enumerate([i for i in items if i["kind"] in {"COUNTEREXAMPLE", "NEGATIVE_RESULT", "FAILED_RETRIEVAL"}], 1):
        exports.append({"export_id": f"q39.export.{idx}", "evidence_id": item["evidence_id"], "failure_class": "MECHANISM" if item["kind"] != "FAILED_RETRIEVAL" else "RETRIEVAL", "originating_task": "121Q38-I1", "originating_artifact": item["source_locator"], "originating_exact_head": HEAD, "observed_symptom": item["summary"], "negative_evidence_refs": [item["evidence_id"]], "affected_claims": ["q37.restricted_seed"], "retry_preconditions": ["new independent evidence or changed retrieval scope"], "prohibited_retry": ["repeat unchanged search and discard the negative result"], "claim_ceiling_impact": "HOLD"})
    return {
        "contract_version": "1.0.0", "task_id": "121Q38-I1",
        "audited_search_seed": {"seed_id": "q37.seed.analogy-audit", "q37_candidate_ref": "analogy.q34-commitment-boundary", "q37_decision_ref": "decision.q37-restricted-seed", "q37_exact_head": Q37, "q37_lifecycle": "audited", "q38_search_permission": "ALLOWED_AS_RESTRICTED_SEED", "q37_claim_ceiling": "candidate_only: bounded structural analogy and repository audit; no mechanism or universal causal proof", "purpose": "search_seed", "seed_digest": digest(Q37 + "decision.q37-restricted-seed")},
        "search_plan": {"plan_id": "q38.plan.repository-pilot", "question": "What repository cases support, challenge or bound the Q37 restricted analogy seed?", "scope": "Q34-Q37 frozen repository artifacts only", "query_plan": queries, "inclusion_criteria": ["traceable and relevant to the frozen seed"], "exclusion_criteria": ["untraceable, duplicate-only, rights-incompatible or outside scope"], "required_evidence_kinds": ["SUPPORT", "COUNTEREXAMPLE", "BOUNDARY_CASE", "NEGATIVE_RESULT", "FAILED_RETRIEVAL"], "duplicate_source_family_policy": "COUNT_FAMILY_ONCE_PRESERVE_ALL_RECORDS", "selection_policy": "NO_QUANTITY_VOTE_PRESERVE_NEGATIVE_AND_FAILED", "stop_condition": stop, "stop_condition_digest": digest(stop), "issued_by": "codex-full-build-single-writer", "q35_authority_ref": "q35.repository-builder", "issued_at": AT, "exact_head": HEAD},
        "evidence_items": items, "selection_log": logs,
        "stop_assessment": {"original_stop_condition": stop, "original_stop_condition_digest": digest(stop), "status": "BOUND_REACHED_WITH_GAPS", "category_coverage": ["SUPPORT", "COUNTEREXAMPLE", "BOUNDARY_CASE", "NEGATIVE_RESULT", "FAILED_RETRIEVAL"], "independent_source_family_count": 4, "stopped_at": AT, "post_hoc_rewrite": False, "saturation_rationale": "All contract categories are represented; the I1 repository pilot stops while preserving the explicit external-validity gap."},
        "unresolved_evidence_gaps": [{"gap_id": "gap.external-validity", "description": "No external population evidence was required or collected for this repository-only pilot.", "impact": "No real-world generalization is permitted.", "next_search": "Use official or primary sources only if a later scoped claim requires them.", "claim_ceiling_effect": "HOLD"}],
        "q39_failure_exports": exports,
        "conclusion": {"verdict": "BOUND_REACHED_WITH_GAPS", "statement": "The bounded repository retrieval preserves support, counterexample, boundary, negative and failed-retrieval records without voting by count or establishing a mechanism.", "claim_ceiling": "candidate_only: deterministic repository retrieval governance; no mechanism or causal proof", "q37_ceiling_preserved": True, "quantity_vote_used": False, "mechanism_proven": False, "negative_results_preserved": True, "unresolved_gap_refs": ["gap.external-validity"]}
    }


def mutation(code, fn):
    obj = copy.deepcopy(base()); fn(obj); return obj


def build():
    FX.mkdir(parents=True, exist_ok=True)
    for old in FX.glob("*.json"):
        old.unlink()
    cases = [(1, "valid-bounded-repository-pilot", 0, base())]
    muts = [
        (2, "schema-missing-plan", 2, lambda b: b.pop("search_plan")),
        (3, "unaudited-q37-seed", 3, lambda b: b["audited_search_seed"].update({"q37_exact_head": "0" * 40})),
        (4, "support-only-query-plan", 4, lambda b: b["search_plan"].update({"query_plan": [b["search_plan"]["query_plan"][0]] * 5})),
        (5, "negative-result-deleted", 5, lambda b: b["evidence_items"][3].update({"kind": "SUPPORT", "q39_export_required": False})),
        (6, "duplicate-family-counted", 6, lambda b: b["evidence_items"][1].update({"source_family": b["evidence_items"][0]["source_family"]})),
        (7, "unknown-rights-published", 7, lambda b: b["evidence_items"][0].update({"rights_status": "UNKNOWN"})),
        (8, "stale-time-sensitive-evidence", 8, lambda b: b["evidence_items"][0]["freshness"].update({"time_sensitive": True, "status": "STALE"})),
        (9, "representativeness-missing", 9, lambda b: b["conclusion"].update({"statement": "The result applies to all populations."})),
        (10, "quantity-vote", 10, lambda b: b["conclusion"].update({"statement": "Majority of cases proves the preferred conclusion."})),
        (11, "mechanism-upgrade", 11, lambda b: b["conclusion"].update({"statement": "Mechanism proven by similar cases."})),
        (12, "stop-condition-rewritten", 12, lambda b: b["stop_assessment"].update({"original_stop_condition": "rewritten after seeing results"})),
        (13, "selective-negative-exclusion", 13, lambda b: (b["evidence_items"][1].update({"selection_status": "EXCLUDED", "q39_export_required": False, "selection_criterion_ref": "exclude.negative-only", "selection_reason": "excluded only because it challenges the preferred result"}), b["stop_assessment"].update({"independent_source_family_count": 3}))),
        (14, "claim-ceiling-overreach", 14, lambda b: b["conclusion"].update({"claim_ceiling": "universal causal proof"})),
        (15, "bad-provenance-digest", 15, lambda b: b["evidence_items"][0].update({"source_digest": "sha256:" + "0" * 64})),
        (16, "selection-log-missing", 16, lambda b: b["selection_log"][0].update({"evidence_id": "ev.counter.q34"})),
        (17, "q39-export-missing", 17, lambda b: b["q39_failure_exports"][0].update({"evidence_id": "ev.support.q37"})),
        (18, "counterevidence-overridden", 18, lambda b: b["conclusion"].update({"statement": "Support grade cancels counterexample."})),
        (19, "future-as-of-time", 19, lambda b: b["evidence_items"][0]["freshness"].update({"as_of": "2026-07-22T17:31:00Z"})),
        (20, "unbounded-not-stopped", 20, lambda b: b["stop_assessment"].update({"status": "NOT_STOPPED", "stopped_at": None})),
        (21, "dangling-selection-evidence-ref", 21, lambda b: b["selection_log"].append({"log_id": "log.dangling", "evidence_id": "missing.evidence", "action": "EXCLUDE", "criterion_ref": "exclude.unresolvable", "reason": "attack fixture dangling reference", "recorded_at": AT, "append_only": True})),
        (22, "citation-only-body-publication", 7, lambda b: b["evidence_items"][0].update({"rights_status": "CITATION_ONLY", "publication_mode": "METADATA_AND_SUMMARY"})),
        (23, "q37-wrong-permission", 2, lambda b: b["audited_search_seed"].update({"q38_search_permission": "DENIED"})),
        (24, "case-count-proves-truth", 10, lambda b: b["conclusion"].update({"statement": "More cases therefore true."}))
    ]
    for n, name, expected, fn in muts:
        cases.append((n, name, expected, mutation(expected, fn)))
    for n, name, expected, obj in cases:
        path = FX / f"{n:02d}-{name}.json"
        path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")
    pilot = base(); (OUT / "pilot-q38-repository-evidence-retrieval.json").write_text(json.dumps(pilot, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    build()
