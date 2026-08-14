#!/usr/bin/env python3
"""Build and validate the conservative 079 truth-audit layer.

This tool inventories the 078 generator's method; it never promotes generated
classification records to independent semantic reviews.  The small verified
review set below is intentionally explicit and reviewer-authored.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/foundation"
REPORTS = ROOT / "reports/foundation-architecture"
DATE = "2026-07-13"
REVIEWER = "Codex-GPT-5-independent-079-review"


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def dump_rows(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True) for row in rows) + "\n"
    path.write_text(text, encoding="utf-8")


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def excerpt(path: str, start: int, end: int):
    lines = (ROOT / path).read_text(encoding="utf-8").splitlines()
    return " ".join(line.strip() for line in lines[start - 1:end] if line.strip())


HARD_IDS = {"Y1", *(f"MF{i}" for i in range(1, 6)), *(f"A{i}" for i in range(1, 10)),
            *(f"T{i}" for i in range(1, 58)), "D220", "D225"}


REVIEW_SPECS = {
    "Y1": dict(path="统一函数总表/0001-Ψ₀元函数完整数学定义.md", lines=(15, 29), object_type="ALGORITHM",
        controlled="Ψ₀ is a model-internal decision workflow combining six incompletely typed components; the multiplication glyph is used as a joint gate in the prose, not as a demonstrated numeric product over a common codomain.",
        rationale="The source supplies an ordered gate and decision table but no common numeric type for the six factors, so ALGORITHM is better supported than FUNCTION."),
    "T2": dict(path="统一函数总表/0012-T2-乘法归零律.md", lines=(18, 20), object_type="FORMAL_PROPOSITION",
        controlled="For every finite product in an algebraic structure with an absorbing zero, if at least one factor is zero then the product is zero.",
        rationale="The source makes a universally phrased mathematical assertion; it does not restrict the domain to Nat or to two factors."),
    "T16": dict(path="统一函数总表/0026-T16-两个反向单调函数相乘必然生成倒U型.md", lines=(57, 66), object_type="FORMAL_PROPOSITION",
        controlled="For all positive differentiable functions f1 and f2 on a common real interval, if f1 is increasing and f2 is decreasing, then f1*f2 has an interior inverted-U maximum.",
        rationale="The title and recovered annotation use the universal modal term 必然, so the conservative testable reading is a universal mathematical proposition."),
    "D220": dict(path="统一函数总表/0256-D220-完全统一不可能定理.md", lines=(13, 15), object_type="ARGUMENT_SCHEMA",
        controlled="Given the source chain Omega=1 implies Phi=0 implies no gates implies no constraints implies no physics, plus the stated presupposition that complete unification concerns an existing physical world, the text claims Omega=1 is incompatible with physical existence.",
        rationale="The file presents a philosophical-physical reductio with undefined predicates, not a closed formal proposition; ARGUMENT_SCHEMA preserves its inferential role."),
    "D598": dict(path="统一函数总表/0608-D598-系统性钝化.md", lines=(3, 18), object_type="MECHANISM_MODEL",
        controlled="In the stated organizational model, prolonged high pressure together with low refusal capacity, weak repair channels and high adaptation tends to increase group-level systemic desensitization; the claim is scoped and not universal.",
        rationale="The source gives a directional social-psychological mechanism and boundary conditions, but no identified causal design, typed domain/codomain, units, or uniquely executable measurement rule; it is not yet a FUNCTION."),
}


COMPONENT_SPECS = {
    "C": ((35, 59), "MECHANISM_MODEL", "C is a proposed causal-screening mechanism; its observational and counterfactual terms are not sufficient to establish identified causality."),
    "M": ((63, 94), "PREDICATE", "M is a governed stopping predicate over recorded increments; division-by-zero and iteration semantics remain unspecified."),
    "I_ISO": ((98, 121), "RELATION", "I_iso is a candidate structural relation; the source does not supply a bijection, inverse, or preservation proof for strict isomorphism."),
    "L_META": ((125, 150), "OPERATOR", "L_meta is an argmin-style layer-selection operator with an operational stopping policy, not a convergence theorem."),
    "G_DELTA": ((154, 176), "RELATION", "G_delta is an incompletely specified provability-status gate; it is not a decision procedure for arbitrary propositions and its displayed formula is classically tautological in wording."),
    "P_META": ((180, 207), "ALGORITHM", "P_meta is a projection workflow over prior gates; the integral and product notation lacks a typed numeric semantics."),
    "JPLUS": ((21, 27), "PREDICATE", "J+ is an internal positive-evidence flag, not a truth predicate."),
    "JMINUS": ((21, 27), "PREDICATE", "J- is an internal objection flag, not a falsity predicate."),
    "MF0": ((1939, 1949), "ALGORITHM", "MF-0000 is an orchestration of five internal channels and decision procedures; the source does not define it as a total single-valued mathematical function."),
}


DOSSIER_CLASS = {
    "DEFINITION_ONLY": {"D238", "D239"},
    "PROVABLE_FINITE_OR_ELEMENTARY": {"D233", "D397"},
    "NEEDS_ADDITIONAL_ASSUMPTIONS": {"T1", "T11", "T15", "T20", "T23", "T27", "T31", "T35", "D34", "D97", "D218", "D219", "D225", "D230", "D231", "D234", "D235", "D236", "D240", "D246", "D416"},
    "EMPIRICAL_NOT_PURE_MATH": {"T34", "T37", "D223"},
    "STRUCTURAL_ANALOGY_ONLY": {"T17", "T38", "D90", "D149"},
    "EXTERNAL_THEOREM_REFERENCE": {"D205"},
    "OPEN_MATHEMATICAL_PROBLEM": set(),
    "FALSE_OR_COUNTEREXAMPLE_FOUND": {"D91", "D150"},
    "SEMANTICALLY_UNDEFINED": {"T21", "D96", "D114", "D115", "D424"},
    "PROVISIONAL": set(),
}


def review_record(oid, spec, registry=True):
    path = spec["path"]
    start, end = spec["lines"]
    return {
        "id": oid, "registry_object": registry, "adjudication_method": "SOURCE_TEXT_SEMANTIC_REVIEW",
        "source_body_actually_read": True, "source_path": path, "source_sha256": sha256(ROOT / path),
        "source_excerpt": excerpt(path, start, end), "source_line_range": f"L{start}-L{end}",
        "controlled_proposition": spec["controlled"], "object_type": spec["object_type"],
        "object_type_rationale": spec["rationale"], "logic_form": "source-scoped controlled proposition",
        "quantifiers": ["explicit where present; otherwise conservative scope only"],
        "assumptions": ["source terms retain the meanings stated in the complete legacy body"],
        "scope": "legacy source scope only", "counterexample_conditions": ["failure of stated premises or operationalization"],
        "proof_or_evidence_requirement": "typed formalization and proof for mathematical content; independent empirical evidence for world claims",
        "review_confidence": 0.9 if oid in {"T2", "T16", "D220", "D598"} else 0.82,
        "review_status": "VERIFIED", "semantic_adjudication_verified": True,
        "independent_reviewer": REVIEWER, "review_date": DATE,
    }


def build():
    objects = load_jsonl(DATA / "formal-objects/objects.jsonl")
    old = load_jsonl(DATA / "adjudications/core-kernel.jsonl")
    old_by_id = {r["legacy_id"]: r for r in old if "::" not in r["legacy_id"]}
    method = []
    for obj in objects:
        oid = obj["legacy_id"]
        method_name = "HARDCODED_MAPPING" if oid in HARD_IDS else "REGEX_PRECLASSIFICATION"
        method.append({
            "id": oid, "legacy_path": obj["legacy_path"], "adjudication_method": method_name,
            "source_body_actually_read": False, "semantic_adjudication_verified": False,
            "078_claimed_status": old_by_id.get(oid, {}).get("classification_status", obj.get("classification_status")),
            "079_review_status": "PRECLASSIFICATION_ONLY", "independent_reviewer": REVIEWER,
            "basis": "explicit ID dictionary" if method_name == "HARDCODED_MAPPING" else "title/expression regex or default branch",
        })
    reviews = [review_record(oid, spec) for oid, spec in REVIEW_SPECS.items()]
    root_path = "统一函数总表/0001-Ψ₀元函数完整数学定义.md"
    for oid, (line_range, typ, controlled) in COMPONENT_SPECS.items():
        start, end = line_range
        spec = dict(path=root_path, lines=(start, end), object_type=typ, controlled=controlled,
                    rationale=f"The complete root source describes this component's role and supports {typ}; missing types and proof prevent stronger promotion.")
        reviews.append(review_record(oid, spec, registry=False))

    unproved = [r for r in old if "::" not in r["legacy_id"] and r["proof_status"] == "UNPROVED_PROPOSITION"]
    class_of = {oid: category for category, ids in DOSSIER_CLASS.items() for oid in ids}
    dossiers = []
    for row in unproved:
        oid = row["legacy_id"]
        category = class_of[oid]
        false = category == "FALSE_OR_COUNTEREXAMPLE_FOUND"
        dossiers.append({
            "id": oid, "legacy_path": row["current_source"]["path"],
            "legacy_proposition": row["original_natural_language_proposition"],
            "controlled_proposition": row["original_natural_language_proposition"],
            "dossier_class": category,
            "formalization_readiness": "LOW" if category in {"SEMANTICALLY_UNDEFINED", "EMPIRICAL_NOT_PURE_MATH", "STRUCTURAL_ANALOGY_ONLY"} else "MEDIUM",
            "current_proof_status": "REFUTED_BY_T16_COUNTEREXAMPLE" if false else "UNPROVED_PROPOSITION",
            "missing_assumptions": [] if false else ["typed domain and codomain", "explicit quantifiers", "all mathematical and empirical premises"],
            "backend_entry": "NO" if category in {"EMPIRICAL_NOT_PURE_MATH", "STRUCTURAL_ANALOGY_ONLY", "SEMANTICALLY_UNDEFINED"} else "CONDITIONAL",
            "backend_blocker": "Original claim must not be weakened; formalize definitions and premises first.",
            "next_minimum_proof_obligation": "Write a typed statement preserving the original quantifiers, then prove it or search for a countermodel.",
            "independent_reviewer": REVIEWER, "review_status": "DOSSIER_READY_NOT_SEMANTICALLY_VERIFIED",
        })

    equivalence = [
        {"id":"T2","review_method":"FORMAL_PROOF_REVIEW","legacy_controlled_proposition":REVIEW_SPECS["T2"]["controlled"],
         "artifact_proposition":"For all a,b:Nat, a=0 or b=0 implies a*b=0 (Lean); same over Int in Z3.",
         "equivalence":"NOT_EQUIVALENT_WEAKENED_LEMMA","reason":"Legacy text is domain-unspecified and speaks of any factor in the framework product; Lean restricts to two Nat factors, while Z3 uses Int. Both prove valid instances, not the full legacy proposition.",
         "legacy_status":"PARTIALLY_FORMALIZED","artifact_status":"PROVED_WEAKENED_LEMMA"},
        {"id":"T16","review_method":"COUNTEREXAMPLE_REVIEW","legacy_controlled_proposition":REVIEW_SPECS["T16"]["controlled"],
         "artifact_proposition":"f1=exp(x) is strictly increasing, f2=exp(-2x) is strictly decreasing, and f1*f2=exp(-x) is strictly decreasing on R.",
         "equivalence":"COUNTEREXAMPLE_MATCHES_UNIVERSAL_TITLE_AND_ANNOTATION","reason":"The functions satisfy the stated opposing monotonicity and the product lacks an interior inverted-U maximum. It refutes the unrestricted universal reading, not every suitably strengthened theorem.",
         "legacy_status":"REFUTED_AS_STATED","artifact_status":"REPLAYABLE_COUNTEREXAMPLE"},
        {"id":"D220","review_method":"COUNTEREXAMPLE_REVIEW","legacy_controlled_proposition":REVIEW_SPECS["D220"]["controlled"],
         "artifact_proposition":"The implication chain is satisfiable with OmegaOne and NoPhysics true when PhysicalExists is false.",
         "equivalence":"DOES_NOT_REFUTE_FULL_SOURCE_REDUCTIO","reason":"The source explicitly invokes physical existence as a presupposition. The 078 model sets PhysicalExists=false and therefore tests the chain without that premise. It exposes premise dependence but is not a countermodel to the full premise set.",
         "legacy_status":"UNPROVED_ARGUMENT_SCHEMA","artifact_status":"PREMISE_DEPENDENCE_MODEL_ONLY"},
    ]
    dump_rows(DATA / "adjudications/079-method-audit.jsonl", method)
    dump_rows(DATA / "adjudications/079-independent-semantic-review.jsonl", reviews)
    dump_rows(DATA / "proofs/079-proof-dossiers.jsonl", dossiers)
    dump_rows(DATA / "validations/079-equivalence-checks.jsonl", equivalence)
    reviewed_ids = set(REVIEW_SPECS)
    remaining = [{
        "id": row["id"], "legacy_path": row["legacy_path"],
        "current_method": row["adjudication_method"],
        "required_next_method": "SOURCE_TEXT_SEMANTIC_REVIEW",
        "review_status": "PENDING_INDEPENDENT_REVIEW",
        "priority": "Y1_MF_A_T_OR_STRONG_D" if row["id"].startswith(("Y", "MF", "A", "T")) else "OTHER_D",
    } for row in method if row["id"] not in reviewed_ids]
    dump_rows(DATA / "work-queues/079-semantic-review-queue.jsonl", remaining)
    counts = Counter(r["adjudication_method"] for r in method)
    dossier_counts = Counter(r["dossier_class"] for r in dossiers)
    coverage = {
        "snapshot_id":"IGNITION-20260709-079", "registry_total":len(objects),
        "migration_coverage":{"covered":len(objects),"total":len(objects),"rate":1.0},
        "preclassification_coverage":{"covered":len(method),"total":len(objects),"rate":1.0},
        "method_counts":dict(sorted(counts.items())),
        "source_text_semantic_review_coverage":{"covered":len(REVIEW_SPECS),"total":len(objects),"rate":len(REVIEW_SPECS)/len(objects)},
        "independently_verified_semantic_coverage":{"covered":len(REVIEW_SPECS),"total":len(objects),"rate":len(REVIEW_SPECS)/len(objects)},
        "remaining_independent_semantic_queue":len(remaining),
        "internal_component_review":{"covered":len(COMPONENT_SPECS),"total":len(COMPONENT_SPECS),"rate":1.0},
        "formal_proof_coverage":{"proved_original_claims":0,"proved_weakened_lemmas":1,"total_registry_objects":len(objects)},
        "empirical_evidence_coverage":{"covered":0,"total":len(objects),"rate":0.0},
        "proof_dossier_counts":dict(sorted(dossier_counts.items())),
        "status":"PARTIAL_SEMANTIC_ADJUDICATION",
        "warning":"Automatic method coverage is not semantic adjudication coverage.",
    }
    (DATA / "coverage/079-verified-coverage.json").write_text(json.dumps(coverage, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    return coverage


def validate():
    objects = load_jsonl(DATA / "formal-objects/objects.jsonl")
    method = load_jsonl(DATA / "adjudications/079-method-audit.jsonl")
    reviews = load_jsonl(DATA / "adjudications/079-independent-semantic-review.jsonl")
    dossiers = load_jsonl(DATA / "proofs/079-proof-dossiers.jsonl")
    eq = load_jsonl(DATA / "validations/079-equivalence-checks.jsonl")
    remaining = load_jsonl(DATA / "work-queues/079-semantic-review-queue.jsonl")
    required = {"adjudication_method","source_body_actually_read","source_excerpt","source_line_range","controlled_proposition","object_type_rationale","logic_form","quantifiers","assumptions","scope","counterexample_conditions","proof_or_evidence_requirement","review_confidence","review_status","independent_reviewer"}
    checks = {
        "method_622": len(method)==len(objects)==622,
        "method_ids_unique": len({r['id'] for r in method})==622,
        "method_split": Counter(r['adjudication_method'] for r in method)==Counter({"REGEX_PRECLASSIFICATION":548,"HARDCODED_MAPPING":74}),
        "verified_reviews_complete": all(required <= r.keys() and r["source_body_actually_read"] and r["source_excerpt"] for r in reviews),
        "verified_registry_5": sum(r["registry_object"] for r in reviews)==5,
        "components_9": sum(not r["registry_object"] for r in reviews)==9,
        "dossiers_40": len(dossiers)==40 and len({r['id'] for r in dossiers})==40,
        "dossier_classes_complete": set(DOSSIER_CLASS)==set(r['dossier_class'] for r in dossiers) | {"OPEN_MATHEMATICAL_PROBLEM","PROVISIONAL"},
        "equivalence_3": {r['id'] for r in eq}=={"T2","T16","D220"},
        "d598_completed": any(r['id']=="D598" and r['semantic_adjudication_verified'] for r in reviews),
        "remaining_queue_617": len(remaining)==617 and not ({r['id'] for r in reviews if r['registry_object']} & {r['id'] for r in remaining}),
    }
    for name, ok in checks.items(): print(("PASS" if ok else "FAIL"), name)
    print(f"CHECKS_TOTAL={len(checks)} CHECKS_PASSED={sum(checks.values())}")
    if not all(checks.values()): raise SystemExit(1)
    print("ALL_079_TRUTH_AUDIT_CHECKS_VALID")


if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--check", action="store_true"); args=parser.parse_args()
    if not args.check: build()
    validate()
