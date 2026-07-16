from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _node(node_id: str, label: str, node_type: str, layer: str, source: str, commit: str) -> dict:
    return {
        "node_id": node_id,
        "label": label,
        "node_type": node_type,
        "layers": [layer],
        "provenance": [source],
        "uncertainty": "derived from declared repository source",
        "claim_ceiling": f"projection from {commit}; not canonical truth"
    }


def _relation(relation_id: str, source: str, target: str, relation_class: str, layer: str, source_path: str, commit: str, start: int, end: int) -> dict:
    return {
        "relation_id": relation_id,
        "source": source,
        "target": target,
        "relation_class": relation_class,
        "direction": "directed",
        "sign": "neutral",
        "weight": 1.0,
        "conditions": ["repository projection"],
        "layer": layer,
        "temporal_bounds": {"start": start, "end": end},
        "provenance": [source_path],
        "uncertainty": "projection uncertainty",
        "claim_ceiling": f"relation projected from {commit}; not causality or truth"
    }


def project_from_sources(commit: str, source_paths: list[str], purpose: str) -> dict:
    nodes: list[dict] = []
    relations: list[dict] = []
    residue: list[dict] = []
    layers = [
        {"layer_id": "source", "label": "Source", "boundary_rule": "declared source files", "model_choice": True},
        {"layer_id": "architecture", "label": "Architecture", "boundary_rule": "architecture docs and schemas", "model_choice": True},
        {"layer_id": "evidence", "label": "Evidence", "boundary_rule": "validation and evidence status", "model_choice": True},
        {"layer_id": "operations", "label": "Operations", "boundary_rule": "tools and tests", "model_choice": True}
    ]
    nodes.append(_node("repo", "Repository state", "repository", "source", "git commit", commit))
    for idx, rel_path in enumerate(sorted(source_paths), start=1):
        path = ROOT / rel_path
        node_id = "src-" + rel_path.replace("/", "-").replace(".", "-")
        layer = "architecture" if rel_path.startswith(("docs/", "schemas/", "data/architecture")) else "operations" if rel_path.startswith(("tools/", "tests/")) else "evidence"
        if path.exists():
            label = rel_path
            nodes.append(_node(node_id, label, "source_file", layer, rel_path, commit))
            relations.append(_relation(f"rel-repo-{idx}", "repo", node_id, "resource_reference", layer, rel_path, commit, idx, idx + 1))
        else:
            residue.append({"residue_id": f"missing-{idx}", "residue_type": "missing_bridge", "description": f"Source path not present in checked-out tree: {rel_path}", "claim_ceiling": "missing source residue"})
    if len(nodes) >= 4:
        members = [n["node_id"] for n in nodes[:4]]
    else:
        members = [n["node_id"] for n in nodes] + ["repo"] * (4 - len(nodes))
    hyper = [{
        "hyper_id": "hyper-repo-architecture-tooling",
        "members": members[:4],
        "relation_class": "dependency",
        "preserve_as_higher_order": True,
        "pairwise_projection_allowed": True,
        "residue_if_projected": "Pairwise view loses joint repository/source/tooling context.",
        "provenance": source_paths[:3] or ["projection input"],
        "claim_ceiling": "higher-order projection only"
    }]
    return {
        "network_spec": {
            "network_id": f"arn-projection-{commit[:8]}",
            "as_of_commit": commit,
            "purpose": purpose,
            "canonical_authority": "Source files and Foundation remain authoritative; this is a derived projection.",
            "not_truth_layer": True,
            "claim_ceiling": "deterministic ARN projection only"
        },
        "nodes": nodes,
        "relations": relations,
        "hyper_relations": hyper,
        "layers": layers,
        "interlayer_couplings": [{
            "coupling_id": "couple-source-architecture",
            "from_layer": "source",
            "to_layer": "architecture",
            "coupling_type": "declared projection",
            "provenance": source_paths[:1] or ["projection input"],
            "claim_ceiling": "layer coupling is a model choice"
        }],
        "temporal_activations": [
            {"activation_id": f"act-{r['relation_id']}", "target_ref": r["relation_id"], "start": r["temporal_bounds"]["start"], "end": r["temporal_bounds"]["end"], "activation_state": "active", "not_integration_proof": True}
            for r in relations
        ],
        "network_states": [
            {"state_id": "state-projected", "active_nodes": [n["node_id"] for n in nodes], "active_relations": [r["relation_id"] for r in relations], "unknowns": ["real-world integration"], "as_of_time": len(relations) + 1}
        ],
        "perturbations": [{
            "perturbation_id": "projection-input",
            "input_type": "repository_state",
            "content_ref": commit,
            "target_nodes": [n["node_id"] for n in nodes],
            "provenance": ["git commit"],
            "claim_ceiling": "projection perturbation only"
        }],
        "integration_responses": [{
            "response_id": "projection-response",
            "perturbation_ref": "projection-input",
            "response_type": "UNKNOWN_RESPONSE",
            "evidence_ref": "embedding-summary",
            "alternative_explanations": ["source file exists", "projection rule selected it"],
            "claim_ceiling": "projection response, not learning proof"
        }],
        "reconfiguration_episodes": [{
            "episode_id": "projection-episode",
            "baseline_state": "source-list",
            "post_state": "state-projected",
            "changed_nodes": [n["node_id"] for n in nodes if n["node_id"] != "repo"],
            "unchanged_nodes": ["repo"],
            "changed_relations": [r["relation_id"] for r in relations],
            "unchanged_relations": [],
            "delay": "repository order only",
            "oscillation": "not assessed",
            "residue": ["projection cannot prove integration"],
            "claim_ceiling": "projection episode only"
        }],
        "attractor_or_oscillation": [{
            "record_id": "projection-loop-boundary",
            "loop_pattern": ["project", "render", "validate"],
            "not_clinical_claim": True,
            "claim_ceiling": "workflow loop only"
        }],
        "cascade_or_spillover": [{
            "record_id": "projection-path",
            "path": [r["relation_id"] for r in relations[:2]],
            "time_respecting": True,
            "not_causality": True,
            "claim_ceiling": "time-respecting projection path, not causality"
        }],
        "embedding_evidence": [{
            "record_id": "embedding-summary",
            "external_availability": "source files available in repository checkout",
            "retrieval": "read by deterministic projector",
            "relational_linkage": "resource_reference relations to repo node",
            "conflict_exposure": "not assessed by projection",
            "judgment_change": "not measured",
            "action_change": "not measured",
            "transfer": "not measured",
            "delayed_stability": "not measured",
            "alternatives": ["file existence", "selection by source list"],
            "evidence": source_paths,
            "claim_ceiling": "availability/retrieval/linkage only"
        }],
        "projections": [{
            "projection_id": "projection-self",
            "source_network": f"arn-projection-{commit[:8]}",
            "projection_rules": ["declared source paths become source_file nodes", "repo points to each source"],
            "omitted_dimensions": ["private cognition", "real-world learning", "unstated relations"],
            "not_canonical": True,
            "claim_ceiling": "projection only"
        }],
        "diffs": [],
        "unmapped_residue": residue or [{
            "residue_id": "projection-residue",
            "residue_type": "unverified_integration",
            "description": "Projection does not prove integration, truth, value or causality.",
            "claim_ceiling": "residue"
        }]
    }

