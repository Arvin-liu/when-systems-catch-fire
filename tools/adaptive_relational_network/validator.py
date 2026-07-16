from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = ROOT / "data" / "architecture" / "adaptive-relational-network" / "examples"


def load_network(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_network_paths() -> list[Path]:
    return sorted(p for p in EXAMPLE_DIR.glob("*.json") if p.name != "embedding-probe.json")


def time_respecting(network: dict, relation_path: list[str]) -> bool:
    rels = {r["relation_id"]: r for r in network.get("relations", [])}
    end = None
    for rid in relation_path:
        rel = rels[rid]
        start = rel["temporal_bounds"]["start"]
        if end is not None and start < end:
            return False
        end = rel["temporal_bounds"]["end"]
    return True


def network_diff(before: dict, after: dict) -> dict:
    bn = {n["node_id"] for n in before.get("nodes", [])}
    an = {n["node_id"] for n in after.get("nodes", [])}
    br = {r["relation_id"] for r in before.get("relations", [])}
    ar = {r["relation_id"] for r in after.get("relations", [])}
    return {
        "added_nodes": sorted(an - bn),
        "removed_nodes": sorted(bn - an),
        "added_relations": sorted(ar - br),
        "removed_relations": sorted(br - ar),
        "claim_ceiling": "NetworkDiff is representation diff only, not proof that reality changed."
    }


def render_summary(network: dict) -> str:
    spec = network["network_spec"]
    return f"{spec['network_id']}: {len(network['nodes'])} nodes, {len(network['relations'])} relations, claim ceiling: {spec['claim_ceiling']}"


def validate_network(network: dict) -> list[str]:
    errors: list[str] = []
    nid = network.get("network_spec", {}).get("network_id", "<missing>")
    if network.get("network_spec", {}).get("not_truth_layer") is not True:
        errors.append(f"{nid}: missing not_truth_layer")
    node_ids = {n.get("node_id") for n in network.get("nodes", [])}
    rel_ids = {r.get("relation_id") for r in network.get("relations", [])}
    for node in network.get("nodes", []):
        for field in ("provenance", "uncertainty", "claim_ceiling"):
            if not node.get(field):
                errors.append(f"{nid}: node {node.get('node_id')} missing {field}")
    for rel in network.get("relations", []):
        rid = rel.get("relation_id")
        if rel.get("source") not in node_ids or rel.get("target") not in node_ids:
            errors.append(f"{nid}: {rid} dangling endpoint")
        for field in ("provenance", "uncertainty", "claim_ceiling", "temporal_bounds"):
            if not rel.get(field):
                errors.append(f"{nid}: {rid} missing {field}")
        text = json.dumps(rel, ensure_ascii=False).lower()
        if rel.get("relation_class") != "causal_delegated_to_mcf" and "causal proof" in text:
            errors.append(f"{nid}: relation upgraded to causality")
        if any(term in text for term in ("centrality proves", "similarity proves", "community proves", "adjacency proves")):
            errors.append(f"{nid}: network metric overclaim")
    for hyper in network.get("hyper_relations", []):
        if len(hyper.get("members", [])) < 3 or hyper.get("preserve_as_higher_order") is not True:
            errors.append(f"{nid}: hyper relation silently collapsed")
    for cascade in network.get("cascade_or_spillover", []):
        path = cascade.get("path", [])
        if not all(rid in rel_ids for rid in path):
            errors.append(f"{nid}: cascade path missing relation")
        if cascade.get("time_respecting") is True and not time_respecting(network, path):
            errors.append(f"{nid}: static temporal fallacy")
        if cascade.get("not_causality") is not True:
            errors.append(f"{nid}: cascade treated as causality")
    for projection in network.get("projections", []):
        if projection.get("not_canonical") is not True:
            errors.append(f"{nid}: projection may replace canonical source")
    for evidence in network.get("embedding_evidence", []):
        required = ("external_availability", "retrieval", "relational_linkage", "conflict_exposure", "judgment_change", "action_change", "transfer", "delayed_stability", "alternatives", "evidence", "claim_ceiling")
        for field in required:
            if not evidence.get(field):
                errors.append(f"{nid}: embedding evidence missing {field}")
        blob = json.dumps(evidence, ensure_ascii=False).lower()
        if "retrieval proves integration" in blob or "self-report proves behavior" in blob:
            errors.append(f"{nid}: embedding evidence overclaim")
    if len({r["response_type"] for r in network.get("integration_responses", [])}) > 0:
        allowed = {"SURFACE_ASSIMILATION","BOUNDARY_REJECTION","LOCAL_RECONFIGURATION","PARTIAL_INTEGRATION","CONTEXT_GATED","COMPARTMENTALIZED","DEFERRED_UPDATE","UNKNOWN_RESPONSE"}
        for r in network["integration_responses"]:
            if r["response_type"] not in allowed:
                errors.append(f"{nid}: invalid response type")
            if not r.get("alternative_explanations"):
                errors.append(f"{nid}: missing alternatives")
    if not network.get("unmapped_residue"):
        errors.append(f"{nid}: missing residue")
    return errors


def validate_all() -> dict:
    failures = {}
    paths = iter_network_paths()
    for path in paths:
        errors = validate_network(load_network(path))
        if errors:
            failures[str(path)] = errors
    return {"checked": len(paths), "failures": failures, "status": "PASS" if not failures else "FAIL"}


def main() -> int:
    result = validate_all()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

