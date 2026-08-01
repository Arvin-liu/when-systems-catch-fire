#!/usr/bin/env python3
"""Task 109 — deterministic evidence-driven iteration planner.

Reads REAL governed sources at origin/main, builds a candidate inventory with
provenance, classifies each candidate into exactly one of 10 classes, scores with
the FROZEN priority model (data/operations/iterations/109/priority_model.json),
and emits deterministic ranked outputs. No generated output is fed back as an
authoritative discovery input. All randomness avoided; tie-break is deterministic.
"""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import completion_state as CS

REPO = Path(__file__).resolve().parents[2]
MODEL_PATH = REPO / "data/operations/iterations/109/priority_model.json"


def _resolve_out():
    # Task 110 §5: when a reconciliation ledger exists, reconciled planner outputs go to
    # that task's own iterations dir (e.g. 110), so the immutable task-109 historical
    # artifacts are never overwritten. Otherwise fall back to the original 109 dir.
    if CS.LEDGER_PATH.exists():
        return CS.LEDGER_PATH.parent
    env = os.environ.get("ITERATION_OUT_DIR")
    if env:
        return REPO / "data/operations/iterations" / env
    return REPO / "data/operations/iterations/109"


OUT = _resolve_out()

META_CLASSES = {"GOVERNANCE_OR_PROPAGATION_DEFECT", "MAINTENANCE_OR_DEPENDENCY", "OWNER_DECISION_REQUIRED"}
SUBSTANTIVE_CLASSES = {"SCIENTIFIC_EVIDENCE", "MATHEMATICAL_FORMALIZATION",
                       "CORE_CAPABILITY_VALIDATION", "IMPLEMENTATION_DEFECT"}


def git_show(path):
    r = subprocess.run(["git", "show", f"origin/main:{path}"], cwd=str(REPO),
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout


def load_model():
    with open(MODEL_PATH) as f:
        return json.load(f)


def blank_candidate(canonical_id, source, title):
    return {
        "canonical_id": canonical_id,
        "source": source,
        "title": title,
        "provenance": {"source_file": source, "canonical_id": canonical_id},
        "current_status": None,
        "dependencies": [],
        "prerequisite_unresolved": False,
        "affected_surfaces": [],
        "evidence_needs": [],
        "stop_conditions": [],
        "claim_ceiling": None,
        "authority": "REPO_OWNER",
        "class": None,
        "is_meta": False,
        "missing_fields": [],
        "factor_inputs": {},
    }


# ---------- source readers ----------

def read_open_questions():
    txt = git_show("RESULTS/OPEN-QUESTIONS.md") or ""
    out = []
    for line in txt.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        if cells[0] in ("问题", "") or set(cells[0]) <= set("- "):
            continue
        q, gap, ev, stop = cells[0], cells[1], cells[2], cells[3]
        c = blank_candidate(f"OQ-{int(hashlib.md5(q.encode('utf-8')).hexdigest(), 16) % 100000:05d}", "RESULTS/OPEN-QUESTIONS.md", q)
        c["current_status"] = "OPEN_QUESTION"
        c["factor_inputs"] = {
            "harm_if_wrong": 0.8 if "统一" in q or "量子引力" in q else 0.6,
            "falsifiability": 0.2 if ("统一" in q or "量子引力" in q or "量子测量" in q) else 0.5,
            "data_availability": 0.2 if ("统一" in q or "量子引力" in q) else 0.5,
            "expected_information_gain": 0.9 if "统一" in q else 0.6,
            "evidence_cost": 0.85 if ("统一" in q or "量子引力" in q) else 0.6,
            "risk_inverted": 0.5,
            "maturity_gap": 0.85 if ("统一" in q or "量子引力" in q) else 0.6,
            "owner_relevance": 0.7,
            "duplication_inverted": 0.6,
            "substantive_score": 0.92,
        }
        c["evidence_needs"] = [ev]
        c["stop_conditions"] = [stop]
        c["claim_ceiling"] = "Open research question; not a promised roadmap item."
        c["affected_surfaces"] = ["articles", "research-program"]
        out.append(c)
    return out


def read_candidate_portfolio():
    txt = git_show("evidence-program/registry/candidate-portfolio.jsonl") or ""
    out = []
    for ln in txt.splitlines():
        ln = ln.strip()
        if not ln:
            continue
        d = json.loads(ln)
        c = blank_candidate(d["candidate_id"], "evidence-program/registry/candidate-portfolio.jsonl",
                            d.get("current_claim", d["candidate_id"])[:120])
        c["provenance"]["upstream_source"] = d.get("source")
        c["current_status"] = d.get("selection_decision", "RESERVE_PILOT")
        c["claim_ceiling"] = d.get("claim_ceiling")
        c["provenance"]["claim_id"] = d.get("claim_id")
        fi = {}
        for k in ["harm_if_wrong", "dependency_centrality", "falsifiability",
                  "data_availability", "evidence_cost", "blast_radius"]:
            if k in d:
                fi[k] = float(d[k])
        fi.setdefault("expected_information_gain", 0.7)
        fi.setdefault("risk_inverted", 0.7)
        fi.setdefault("maturity_gap", 1.0 - {"M0":0.0,"M1":0.2,"M2":0.4,"M3":0.6,"M4":0.8}.get(d.get("current_M_level","M1"),0.2))
        fi.setdefault("owner_relevance", 0.7)
        fi.setdefault("duplication_inverted", 0.6)
        fi.setdefault("substantive_score", 0.95)
        c["factor_inputs"] = fi
        c["evidence_needs"] = ["preregistration", "independent replication", "oracle/baseline"]
        c["affected_surfaces"] = ["evidence-program", "claims-registry"]
        c["dependencies"] = [d.get("claim_id")] if d.get("claim_id") else []
        out.append(c)
    return out


def _gap_candidates_from_json(obj, source_file, label):
    out = []
    gaps = obj.get("matrix") or obj.get("gaps") or []
    for g in gaps:
        gid = g.get("gap_id") or g.get("id") or label
        c = blank_candidate(gid, source_file, g.get("description", gid)[:140])
        sev = (g.get("severity") or "").lower()
        c["current_status"] = "DECLARED_GAP"
        c["claim_ceiling"] = obj.get("claim_ceiling") or g.get("claim_ceiling")
        is_meta = gid in ("GAP-ITERATION-DELTA", "GAP-NARRATIVE-PROVENANCE",
                          "GAP-PROJECT-ATTRACTOR", "GAP-DECISION-COLLAPSE",
                          "GAP-SAMPLE-DISTRIBUTION", "GAP-CHUNK-INTEGRITY")
        c["factor_inputs"] = {
            "harm_if_wrong": 0.9 if "blocking" in sev else 0.7,
            "dependency_centrality": 0.8 if "blocking" in sev else 0.5,
            "falsifiability": 0.4 if is_meta else 0.6,
            "data_availability": 0.5,
            "expected_information_gain": 0.5 if is_meta else 0.7,
            "evidence_cost": 0.7 if is_meta else 0.5,
            "risk_inverted": 0.6,
            "maturity_gap": 0.7,
            "owner_relevance": 0.6,
            "duplication_inverted": 0.9 if g.get("not_duplicate") else 0.5,
            "substantive_score": 0.20 if is_meta else 0.7,
        }
        c["evidence_needs"] = ["architectural representation", "validator/diff tooling"] if not is_meta else ["governance layer decision"]
        c["stop_conditions"] = ["no new layer without concrete unresolved failure"] if is_meta else []
        c["affected_surfaces"] = ["architecture", "system-map"]
        out.append(c)
    return out


def read_gap_ledgers():
    out = []
    specs = [
        ("data/architecture/121q13-gap-matrix.json", "121q13-gap-matrix"),
        ("data/architecture/causal-gap-ledger.json", "causal-gap-ledger"),
        ("data/architecture/adaptive-relational-network/network-gap-ledger.json", "arn-network-gap"),
        ("data/architecture/probabilistic-system-dynamics/gap-ledger.json", "psd-gap-ledger"),
        ("data/operations/121q24-gap-ledger.json", "121q24-gap-ledger"),
    ]
    for path, label in specs:
        txt = git_show(path)
        if not txt:
            continue
        try:
            obj = json.loads(txt)
        except Exception:
            continue
        out.extend(_gap_candidates_from_json(obj, path, label))
    return out


def read_quarantine(sample_per_file=12):
    out = []
    totals = {}
    for path, kind in [("data/foundation/function-assets/unresolved-quarantine.jsonl", "function-asset"),
                       ("data/foundation/nonfunction-claims/unresolved-quarantine.jsonl", "nonfunction-claim")]:
        txt = git_show(path)
        if not txt:
            continue
        count = 0
        taken = 0
        disp_hist = {}
        for ln in txt.splitlines():
            ln = ln.strip()
            if not ln:
                continue
            count += 1
            try:
                d = json.loads(ln)
            except Exception:
                continue
            disp = d.get("final_disposition", "UNKNOWN")
            disp_hist[disp] = disp_hist.get(disp, 0) + 1
            pending = any(k in disp for k in ("PENDING", "QUARANTINE", "OPEN", "EMPIRICAL_TEST"))
            if pending and taken < sample_per_file:
                taken += 1
                cid = d.get("canonical_id", f"{kind}-{taken}")
                c = blank_candidate(cid, path, f"{kind} {cid}")
                c["current_status"] = disp
                c["provenance"]["resume_key"] = d.get("resume_key")
                c["factor_inputs"] = {
                    "harm_if_wrong": 0.4, "dependency_centrality": 0.4,
                    "falsifiability": 0.5, "data_availability": 0.4,
                    "expected_information_gain": 0.4, "evidence_cost": 0.7,
                    "risk_inverted": 0.6, "maturity_gap": 0.6,
                    "owner_relevance": 0.5, "duplication_inverted": 0.7,
                    "substantive_score": 0.5,
                }
                c["evidence_needs"] = d.get("required_obligations", {}).get("empirical", []) or d.get("empirical_obligations", [])
                c["claim_ceiling"] = "Quarantined; not an established claim."
                c["affected_surfaces"] = ["claims-registry", "foundation"]
                if "DO_NOT_SCHEDULE" in disp:
                    c["class"] = "DO_NOT_SCHEDULE"
                out.append(c)
        totals[path] = {"total_records": count, "disposition_histogram": disp_hist, "sampled": taken}
    return out, totals


def read_case_failures():
    out = []
    import os
    base = "case_failures/examples"
    txt = git_show("case_failures/README.md") or ""
    # enumerate example files via ls-tree
    r = subprocess.run(["git", "ls-tree", "-r", "--name-only", "origin/main", "case_failures/examples"],
                       cwd=str(REPO), capture_output=True, text=True)
    for p in r.stdout.splitlines():
        if not p.endswith(".md") or p.endswith("README.md"):
            continue
        body = git_show(p) or ""
        title = body.splitlines()[0].lstrip("# ").strip() if body else p
        cid = "CF-" + Path(p).stem
        c = blank_candidate(cid, p, title[:120])
        c["current_status"] = "KNOWN_DEFECT_CASE"
        c["factor_inputs"] = {
            "harm_if_wrong": 0.7, "dependency_centrality": 0.5,
            "falsifiability": 0.8, "data_availability": 0.8,
            "expected_information_gain": 0.6, "evidence_cost": 0.4,
            "risk_inverted": 0.8, "maturity_gap": 0.5,
            "owner_relevance": 0.6, "duplication_inverted": 0.6,
            "substantive_score": 0.85,
        }
        c["claim_ceiling"] = "Documented failure mode; not a claim of system correctness."
        c["affected_surfaces"] = ["function-os", "case-library"]
        c["evidence_needs"] = ["regression guard", "bounded-domain test"]
        out.append(c)
    return out


# ---------- classification ----------

def classify(c):
    if c.get("class") == "DO_NOT_SCHEDULE":
        c["is_meta"] = False
        return
    src = c["source"]
    fi = c["factor_inputs"]
    if "OPEN-QUESTIONS" in src:
        cls = "SCIENTIFIC_EVIDENCE"
    elif "candidate-portfolio" in src:
        cls = "CORE_CAPABILITY_VALIDATION"
    elif "gap" in src or "gap-ledger" in src or "gap-matrix" in src:
        cls = "GOVERNANCE_OR_PROPAGATION_DEFECT" if fi.get("substantive_score", 0.5) <= 0.25 else "MATHEMATICAL_FORMALIZATION"
    elif "quarantine" in src:
        cls = "GOVERNANCE_OR_PROPAGATION_DEFECT"
    elif "case_failures" in src:
        cls = "IMPLEMENTATION_DEFECT"
    else:
        cls = "MAINTENANCE_OR_DEPENDENCY"
    c["class"] = cls
    c["is_meta"] = cls in META_CLASSES or fi.get("substantive_score", 0.5) <= 0.25


# ---------- scoring ----------

def score(c, model):
    factors = model["factors"]
    agg = 0.0
    vector = {}
    for f in factors:
        key = f["key"]
        sf = f["source_field"]
        raw = c["factor_inputs"].get(sf)
        if raw is None:
            val = f["missing_value"]
            if sf not in c["missing_fields"]:
                c["missing_fields"].append(sf)
        else:
            val = float(raw)
            if f["direction"] == "lower_better":
                val = 1.0 - val
        vector[key] = round(val, 4)
        agg += f["weight"] * val
    # anti-meta cap: reduce aggregate by the weight (0.02) times the capped delta
    if c["is_meta"] and c.get("class") in META_CLASSES:
        cap = model["anti_meta_rule"]["cap_value"]
        if vector.get("substantive_vs_meta", 0.5) > cap:
            delta = vector["substantive_vs_meta"] - cap
            vector["substantive_vs_meta"] = cap
            agg -= 0.02 * delta
    score100 = round(agg * 100, 2)
    # hard gates
    blocked = None
    if c["class"] == "DO_NOT_SCHEDULE":
        blocked = "DO_NOT_SCHEDULE"
    elif c.get("prerequisite_unresolved"):
        blocked = "UNRESOLVED_PREREQUISITE"
    elif c.get("authority") in (None, "MISSING"):
        blocked = "MISSING_AUTHORITY"
    c["factor_vector"] = vector
    c["aggregate_score"] = score100
    c["blocked_reason"] = blocked
    return score100


def main():
    model = load_model()
    candidates = []
    candidates += read_open_questions()
    candidates += read_candidate_portfolio()
    candidates += read_gap_ledgers()
    qc, qtotals = read_quarantine()
    candidates += qc
    candidates += read_case_failures()

    for c in candidates:
        classify(c)
        score(c, model)

    # --- Task 110 §5: generic completion-state reconciliation (no per-candidate hardcode) ---
    candidates, historical_register, validation_report, prev_invalidated = CS.reconcile(candidates)

    # deterministic rank: blocked forced last; within group by (score desc, id asc)
    def sort_key(c):
        blk = 0 if c["blocked_reason"] is None else 1
        return (blk, -c["aggregate_score"], c["canonical_id"])

    ranked = sorted(candidates, key=sort_key)

    OUT.mkdir(parents=True, exist_ok=True)
    inv = {c["canonical_id"]: c for c in candidates}
    # dependency graph
    dep_graph = {c["canonical_id"]: c["dependencies"] for c in candidates}
    blocked_reg = [{"canonical_id": c["canonical_id"], "class": c["class"],
                    "reason": c["blocked_reason"], "title": c["title"]}
                   for c in candidates if c["blocked_reason"]]

    # recommended queue = non-blocked AND not in a terminal (or unknown-review) lifecycle
    # state (§5.4: completed/superseded/withdrawn/do-not-schedule excluded; unknown
    # completion states blocked from the top until reviewed).
    queue = [c for c in ranked
             if c["blocked_reason"] is None
             and c.get("lifecycle_state") not in CS.LIFECYCLE_TERMINAL
             and c.get("lifecycle_state") != CS.UNKNOWN_STATE]
    recommended = queue[0] if queue else None
    reserves = queue[1:3]

    # substantive ratio over proposed top-10 queue
    top10 = queue[:10]
    sub = sum(1 for c in top10 if c["class"] in SUBSTANTIVE_CLASSES)
    ratio = round(sub / len(top10), 4) if top10 else 0.0

    out = {
        "model_id": model["model_id"],
        "total_candidates": len(candidates),
        "quarantine_totals": qtotals,
        "ranked": [{"canonical_id": c["canonical_id"], "class": c["class"],
                    "is_meta": c["is_meta"], "aggregate_score": c["aggregate_score"],
                    "blocked_reason": c["blocked_reason"],
                    "lifecycle_state": c.get("lifecycle_state"),
                    "factor_vector": c["factor_vector"],
                    "missing_fields": c["missing_fields"]} for c in ranked],
        "recommended_next": recommended["canonical_id"] if recommended else None,
        "reserves": [c["canonical_id"] for c in reserves],
        "substantive_work_ratio_top10": ratio,
        "prior_recommendation_invalidated": prev_invalidated,
        "completion_validation_report": validation_report,
        "lifecycle_terminal_excluded": [c["canonical_id"] for c in ranked
                                        if c.get("lifecycle_state") in CS.LIFECYCLE_TERMINAL],
    }
    (OUT / "candidate_inventory.json").write_text(json.dumps(candidates, ensure_ascii=False, indent=2))
    (OUT / "ranked_queue.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
    (OUT / "dependency_graph.json").write_text(json.dumps(dep_graph, ensure_ascii=False, indent=2))
    (OUT / "blocked_register.json").write_text(json.dumps(blocked_reg, ensure_ascii=False, indent=2))
    (OUT / "substantive_work_ratio.json").write_text(json.dumps(
        {"top10_ratio": ratio, "threshold": 0.70, "meets_threshold": ratio >= 0.70,
         "top10_classes": {c["canonical_id"]: c["class"] for c in top10}}, ensure_ascii=False, indent=2))
    # Task 110 §5 reconciliation artifacts
    (OUT / "completion_registry.json").write_text(json.dumps(
        {c["canonical_id"]: {"class": c["class"], "lifecycle_state": c.get("lifecycle_state"),
                             "reconciliation_evidence": c.get("reconciliation_evidence")}
         for c in candidates}, ensure_ascii=False, indent=2))
    (OUT / "completed_register.json").write_text(json.dumps(historical_register, ensure_ascii=False, indent=2))
    (OUT / "corrected_queue.json").write_text(json.dumps({
        "recommended_next": recommended["canonical_id"] if recommended else None,
        "reserves": [c["canonical_id"] for c in reserves],
        "active_queue_top10": [c["canonical_id"] for c in queue[:10]],
        "prior_recommendation_invalidated": prev_invalidated,
    }, ensure_ascii=False, indent=2))

    print(f"candidates={len(candidates)} recommended={out['recommended_next']} "
          f"reserves={out['reserves']} sub_ratio_top10={ratio}")
    if prev_invalidated:
        print(f"  PRIOR-REC INVALIDATED: {prev_invalidated.get('recommended_next')} -> {prev_invalidated.get('state')}")
    for c in ranked[:8]:
        print(f"  {c['aggregate_score']:6.2f}  {c['class']:32s} {c['canonical_id']:30s} "
              f"blk={c['blocked_reason']} life={c.get('lifecycle_state')}")


if __name__ == "__main__":
    main()
