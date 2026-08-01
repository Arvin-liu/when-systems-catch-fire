#!/usr/bin/env python3
"""Emit remaining §9/§10 artifacts from the deterministic planner outputs."""
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "data/operations/iterations/109"

inv = json.load(open(OUT / "candidate_inventory.json"))
ranked = json.load(open(OUT / "ranked_queue.json"))
model = json.load(open(REPO / "data/operations/iterations/109/priority_model.json"))

by_id = {c["canonical_id"]: c for c in inv}
queue = [r for r in ranked["ranked"] if r["blocked_reason"] is None]
recommended_id = ranked["recommended_next"]
reserve_ids = ranked["reserves"]
rec = by_id[recommended_id]

# ---- factor schema (derived mirror of frozen model) ----
factor_schema = {
    "model_id": model["model_id"],
    "factors": [{"key": f["key"], "direction": f["direction"], "weight": f["weight"],
                 "missing_value": f["missing_value"]} for f in model["factors"]],
    "hard_gates": model["hard_gates"]["rules"],
    "tie_breaking": model["tie_breaking"],
    "missing_data": model["missing_data_behavior"],
    "anti_meta_rule": model["anti_meta_rule"],
}
(OUT / "factor_schema.json").write_text(json.dumps(factor_schema, ensure_ascii=False, indent=2))

# ---- per-candidate dossiers ----
dossier_dir = OUT / "dossiers"
dossier_dir.mkdir(exist_ok=True)
for c in inv:
    d = {
        "canonical_id": c["canonical_id"],
        "title": c["title"],
        "class": c["class"],
        "is_meta": c["is_meta"],
        "current_status": c["current_status"],
        "provenance": c["provenance"],
        "dependencies": c["dependencies"],
        "prerequisite_unresolved": c["prerequisite_unresolved"],
        "affected_surfaces": c["affected_surfaces"],
        "evidence_needs": c["evidence_needs"],
        "stop_conditions": c["stop_conditions"],
        "claim_ceiling": c["claim_ceiling"],
        "authority": c["authority"],
        "aggregate_score": c["aggregate_score"],
        "factor_vector": c["factor_vector"],
        "missing_fields": c["missing_fields"],
        "blocked_reason": c["blocked_reason"],
    }
    (dossier_dir / f"{c['canonical_id']}.json").write_text(json.dumps(d, ensure_ascii=False, indent=2))

# ---- decision log ----
def reasons_not_selected():
    # pick >=5 plausible alternatives and explain why not selected
    notes = []
    # 1. meta governance gaps
    meta_ids = [r["canonical_id"] for r in ranked["ranked"] if r["class"] == "GOVERNANCE_OR_PROPAGATION_DEFECT" and r["canonical_id"].startswith("GAP-")]
    notes.append({
        "candidate": meta_ids,
        "reason": "Meta-governance gaps (iteration delta, narrative provenance, project attractor, decision collapse, sample distribution, chunk integrity) are capped by the anti-meta rule (substantive_vs_meta <= 0.20) and require a concrete unresolved failure not addressable by existing systems before becoming a next iteration. They would expand governance, not produce evidence.",
        "not_selected_because": "anti-meta cap + no demonstrated concrete failure"
    })
    # 2. grand physics unification
    oq_unif = [r["canonical_id"] for r in ranked["ranked"] if r["canonical_id"].startswith("OQ-") and by_id[r["canonical_id"]]["title"] in ("四种基本相互作用统一", "量子引力")]
    notes.append({
        "candidate": oq_unif,
        "reason": "Four-force unification and quantum gravity are low-falsifiability (0.2), low data availability (0.2), high evidence cost (0.85). A grand untestable claim must not outrank a bounded falsifiable pilot merely due to rhetoric.",
        "not_selected_because": "low falsifiability + high cost + not-yet-executable"
    })
    # 3. quarantine adjudication A0..A08
    notes.append({
        "candidate": [r["canonical_id"] for r in ranked["ranked"] if r["canonical_id"].startswith("A")],
        "reason": "Quarantined function/nonfunction assets are governance adjudication work with high effort, missing data/oracle, and many blocked prerequisites. They are retained visibly but not promoted to the next substantive iteration.",
        "not_selected_because": "high effort + missing evidence + pending gates"
    })
    # 4. lower-ranked portfolio pilots C-02/C-04/C-07
    notes.append({
        "candidate": ["C-02", "C-04", "C-07"],
        "reason": "Strong reserve pilots, but scored below C-01 on dependency centrality / information gain / lower evidence cost. They remain recommended reserves for the following iterations.",
        "not_selected_because": "lower aggregate score than C-01"
    })
    # 5. MCF/ARN/PSD gaps
    notes.append({
        "candidate": [r["canonical_id"] for r in ranked["ranked"] if r["class"] == "MATHEMATICAL_FORMALIZATION"],
        "reason": "Architectural gaps are real and important, but several depend on upstream unified-object-set work (mcf-gap-001..004 block mcf-gap-005) and are mathematical-formalization work with medium evidence cost; they are staged after the bounded pilot.",
        "not_selected_because": "dependency on upstream gaps + medium cost"
    })
    return notes

decision_log = {
    "recommended_next_iteration": recommended_id,
    "recommended_title": rec["title"],
    "recommended_class": rec["class"],
    "recommended_score": rec["aggregate_score"],
    "recommended_is_auto_task_110": False,
    "reserves": reserve_ids,
    "substantive_work_ratio_top10": ranked["substantive_work_ratio_top10"] if "substantive_work_ratio_top10" in ranked else None,
    "anti_meta_applied": True,
    "reasons_not_selected": reasons_not_selected(),
    "note": "The recommended item is a reviewed proposal only; it is NOT automatically created or executed as task 110. Final authority remains with the repository owner."
}
(OUT / "decision_log.json").write_text(json.dumps(decision_log, ensure_ascii=False, indent=2))

# ---- next iteration recommendation (markdown) ----
rec_doc = f"""# Next Iteration Recommendation — Task 109

## Recommended next substantive iteration

- **canonical_id**: `{recommended_id}`
- **class**: {rec['class']}
- **aggregate_score**: {rec['aggregate_score']}
- **source**: `{rec['provenance'].get('upstream_source') or rec['source']}`
- **claim_id**: `{rec['provenance'].get('claim_id')}`
- **claim_ceiling**: {rec['claim_ceiling']}

### Why this one

C-01 is a bounded, falsifiable evidence-program reserve pilot: it asserts that 117
source records marked `crossref_verified:true` resolve via the Crossref REST API to
DOIs whose title/year match the registry, and are not retracted or duplicate. It has
a direct oracle (the Crossref API), high falsifiability (0.95), full data availability
(1.0) and low evidence cost. It produces real evidence (pass/fail) without creating a
new governance layer.

### This is NOT task 110

Per contract §2/§10, the recommendation is a reviewed proposal only. It is **not**
automatically created or executed as task 110.

## Reserves

1. `{reserve_ids[0]}` — {by_id[reserve_ids[0]]['class']}
2. `{reserve_ids[1]}` — {by_id[reserve_ids[1]]['class']}

## Dependency & evidence readiness

- C-01 dependencies: {rec['dependencies'] or 'none (self-contained pilot)'}
- evidence needs: {rec['evidence_needs']}
- stop conditions / claim ceiling enforced: {rec['stop_conditions'] or 'n/a'}

## Why plausible alternatives were not selected

See `decision_log.json` (>=5 explicit reasons: meta-governance gaps, grand untestable
physics, quarantine adjudication, lower-ranked pilots, upstream-dependent architectural gaps).
"""
(OUT / "next_iteration_recommendation.md").write_text(rec_doc)

# ---- owner decision packet ----
packet = f"""# Owner Decision Packet — Task 109

## What the planner recommends

The evidence-driven backlog ranks `{recommended_id}` as the next substantive iteration.
It is a bounded, falsifiable pilot with a clear oracle. Two reserves are proposed.

## What the planner deliberately did NOT do

- It did **not** create or execute task 110.
- It did **not** promote any item's maturity/disposition/claim ceiling merely for ranking high.
- It did **not** hide blocked, negative, or deferred work — see `blocked_register.json`
  and the visible-but-low-ranked quarantine items (A0..A08).
- It capped meta-governance gaps (anti-meta rule) so perpetual governance layers cannot
  dominate the near-term queue without a demonstrated concrete failure.

## Decisions required from the owner

1. Accept, modify, or reject the recommended next iteration (`{recommended_id}`).
2. Decide whether any meta-governance gap (GAP-*) should be promoted despite the anti-meta cap,
   and if so, supply the concrete unresolved failure it addresses.
3. Confirm the claim ceilings and stop conditions attached to the recommended item.

## Authority

The ranking is a decision-support projection, not truth and not owner authorization.
The final authority to schedule work remains with the repository owner.
"""
(OUT / "owner_decision_packet.md").write_text(packet)

print("emitted: factor_schema.json, dossiers/", len(inv), "files, decision_log.json,",
      "next_iteration_recommendation.md, owner_decision_packet.md")
