from __future__ import annotations

import hashlib
import json


def stable_hash(data: dict) -> str:
    blob = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _by(items: list[dict], key: str) -> dict[str, dict]:
    return {item[key]: item for item in items}


def _changed(before: dict[str, dict], after: dict[str, dict], fields: list[str]) -> list[dict]:
    changes = []
    for key in sorted(set(before) & set(after)):
        field_changes = {field: {"before": before[key].get(field), "after": after[key].get(field)} for field in fields if before[key].get(field) != after[key].get(field)}
        if field_changes:
            changes.append({"id": key, "fields": field_changes})
    return changes


def network_diff(before: dict, after: dict) -> dict:
    bn, an = _by(before.get("nodes", []), "node_id"), _by(after.get("nodes", []), "node_id")
    br, ar = _by(before.get("relations", []), "relation_id"), _by(after.get("relations", []), "relation_id")
    bh, ah = _by(before.get("hyper_relations", []), "hyper_id"), _by(after.get("hyper_relations", []), "hyper_id")
    be, ae = _by(before.get("embedding_evidence", []), "record_id"), _by(after.get("embedding_evidence", []), "record_id")
    bi, ai = _by(before.get("integration_responses", []), "response_id"), _by(after.get("integration_responses", []), "response_id")
    bt, at = _by(before.get("temporal_activations", []), "activation_id"), _by(after.get("temporal_activations", []), "activation_id")
    diff = {
        "from_ref": before["network_spec"]["as_of_commit"],
        "to_ref": after["network_spec"]["as_of_commit"],
        "external_refs": [
            {"ref_id": before["network_spec"]["as_of_commit"], "ref_type": "git_commit", "claim_ceiling": "external git commit reference only"},
            {"ref_id": after["network_spec"]["as_of_commit"], "ref_type": "git_commit", "claim_ceiling": "external git commit reference only"}
        ],
        "source_change": before["network_spec"]["as_of_commit"] != after["network_spec"]["as_of_commit"],
        "projection_change": before["network_spec"].get("purpose") != after["network_spec"].get("purpose"),
        "unresolved_change": [],
        "added_nodes": sorted(set(an) - set(bn)),
        "removed_nodes": sorted(set(bn) - set(an)),
        "changed_node_attributes": _changed(bn, an, ["label", "node_type", "layers", "uncertainty", "claim_ceiling"]),
        "added_relations": sorted(set(ar) - set(br)),
        "removed_relations": sorted(set(br) - set(ar)),
        "changed_relations": _changed(br, ar, ["relation_class", "direction", "sign", "weight", "conditions", "layer", "temporal_bounds", "claim_ceiling"]),
        "added_hyper_relations": sorted(set(ah) - set(bh)),
        "removed_hyper_relations": sorted(set(bh) - set(ah)),
        "changed_hyper_relations": _changed(bh, ah, ["members", "relation_class", "preserve_as_higher_order", "pairwise_projection_allowed", "residue_if_projected", "claim_ceiling"]),
        "changed_temporal_activations": _changed(bt, at, ["target_ref", "start", "end", "activation_state"]),
        "changed_integration_responses": _changed(bi, ai, ["response_type", "evidence_ref", "alternative_explanations", "claim_ceiling"]),
        "changed_embedding_evidence": _changed(be, ae, ["external_availability", "retrieval", "relational_linkage", "conflict_exposure", "judgment_change", "action_change", "transfer", "delayed_stability", "alternatives", "claim_ceiling"]),
        "residue_changes": {
            "before": before.get("unmapped_residue", []),
            "after": after.get("unmapped_residue", [])
        },
        "claim_ceiling": "NetworkDiff is representation diff only, not proof that reality changed."
    }
    diff["deterministic_hash"] = stable_hash(diff)
    return diff


def pairwise_projection_with_residue(network: dict) -> dict:
    edges = []
    residue = []
    for hyper in network.get("hyper_relations", []):
        members = hyper["members"]
        for idx, source in enumerate(members):
            for target in members[idx + 1:]:
                edges.append({"source": source, "target": target, "derived_from": hyper["hyper_id"]})
        residue.append({"hyper_id": hyper["hyper_id"], "information_loss": hyper["residue_if_projected"]})
    return {"pairwise_edges": edges, "residue": residue, "claim_ceiling": "Pairwise projection is derived and lossy."}
