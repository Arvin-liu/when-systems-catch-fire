from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = ROOT / "data" / "architecture" / "multiscale-causal-fabric" / "examples"

RELATION_CLASSES = {
    "physical_propagation",
    "experimentally_identified_causal",
    "intervention_supported",
    "mechanism_hypothesis",
    "structural_causal_model_edge",
    "dynamical_feedback",
    "enabling_condition",
    "constraint",
    "correlation_only",
    "analogy_only",
    "unknown_relation",
}


def load_fabric(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_example_paths() -> list[Path]:
    return sorted(EXAMPLE_DIR.glob("*.json"))


def _ids(fabric: dict) -> set[str]:
    ids = {e["event_id"] for e in fabric.get("events", [])}
    ids.update(s["state_id"] for s in fabric.get("states", []))
    return ids


def validate_fabric(fabric: dict) -> list[str]:
    errors: list[str] = []
    ids = _ids(fabric)

    for key in ("fabric_id", "as_of_commit", "claim_ceiling", "events", "relations", "unmapped_residue"):
        if key not in fabric:
            errors.append(f"missing {key}")

    if not fabric.get("unmapped_residue"):
        errors.append(f"{fabric.get('fabric_id')}: missing unmapped residue")

    for relation in fabric.get("relations", []):
        rid = relation.get("relation_id", "<missing>")
        if relation.get("source") not in ids:
            errors.append(f"{rid}: dangling source {relation.get('source')}")
        if relation.get("target") not in ids:
            errors.append(f"{rid}: dangling target {relation.get('target')}")
        if relation.get("relation_class") not in RELATION_CLASSES:
            errors.append(f"{rid}: invalid relation_class {relation.get('relation_class')}")
        for field in ("evidence_refs", "uncertainty", "claim_ceiling", "mechanism_status"):
            if not relation.get(field):
                errors.append(f"{rid}: missing {field}")
        text = json.dumps(relation, ensure_ascii=False).lower()
        if relation.get("relation_class") in {"correlation_only", "analogy_only"}:
            forbidden = ("identified causal", "proved causal", "actual causal proof")
            if any(term in text for term in forbidden):
                errors.append(f"{rid}: correlation/analogy upgraded to causal proof")
        if "light cone proves" in text or "光锥证明" in text:
            errors.append(f"{rid}: light cone reachability written as proof")
        if "entropy arrow equals causal" in text or "熵箭头等于因果" in text:
            errors.append(f"{rid}: entropy arrow collapsed into causal arrow")
        if "superluminal" in text and "no controllable" not in text and "not a physical channel" not in text:
            errors.append(f"{rid}: possible superluminal overclaim")

    for cone in fabric.get("cones_or_horizons", []):
        if "not" not in cone.get("horizon_or_boundary", "").lower() and "does not" not in cone.get("reachability_semantics", "").lower():
            errors.append(f"{fabric.get('fabric_id')}: cone/horizon lacks non-proof boundary")

    for record in fabric.get("entropy_and_irreversibility", []):
        relation = record.get("relation_to_causal_order", "").lower()
        if "not" not in relation and "separate" not in relation:
            errors.append(f"{fabric.get('fabric_id')}: entropy record does not separate causal order")

    for loop in fabric.get("feedback_dynamics", []):
        if not loop.get("open_loop_expansion"):
            errors.append(f"{loop.get('loop_id')}: feedback lacks open_loop_expansion")

    for transition in fabric.get("scale_transitions", []):
        bridge = transition.get("bridge_mechanism", "").lower()
        if not bridge or bridge == "none" and transition.get("claim_ceiling") != "analogy_only":
            errors.append(f"{fabric.get('fabric_id')}: scale transition lacks bridge mechanism")

    for projection in fabric.get("projections", []):
        if not projection.get("unmapped_residue"):
            errors.append(f"{projection.get('projection_id')}: projection lacks residue")
        rules = " ".join(projection.get("projection_rules", [])).lower()
        if "map position proves" in rules or "centrality proves" in rules:
            errors.append(f"{projection.get('projection_id')}: map/network proof overclaim")

    if "universe is" in json.dumps(fabric, ensure_ascii=False).lower():
        errors.append(f"{fabric.get('fabric_id')}: universe ontology overclaim")

    return errors


def validate_all(paths: list[Path] | None = None) -> dict:
    selected = paths or iter_example_paths()
    failures: dict[str, list[str]] = {}
    for path in selected:
        errors = validate_fabric(load_fabric(path))
        if errors:
            failures[str(path)] = errors
    return {
        "checked": len(selected),
        "failures": failures,
        "status": "PASS" if not failures else "FAIL",
    }


def main() -> int:
    result = validate_all()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

