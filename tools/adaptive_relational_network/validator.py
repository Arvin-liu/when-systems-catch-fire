from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from .diff import network_diff
from .renderer import render_summary
from .temporal import parse_interval, time_respecting, time_respecting_graph_path, time_respecting_sequence


ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_DIR = ROOT / "data" / "architecture" / "adaptive-relational-network" / "examples"
SCHEMA_PATH = ROOT / "schemas" / "architecture" / "adaptive-relational-network.schema.json"
EMBEDDING_PROBE_SCHEMA_PATH = ROOT / "schemas" / "architecture" / "adaptive-relational-network-embedding-probe.schema.json"


def load_network(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_network_paths() -> list[Path]:
    return sorted(p for p in EXAMPLE_DIR.glob("*.json") if p.name != "embedding-probe.json")


def load_schema(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def strict_schema(schema: dict) -> dict:
    cloned = json.loads(json.dumps(schema))

    def visit(node: object) -> None:
        if isinstance(node, dict):
            if node.get("type") == "object" and "additionalProperties" not in node:
                node["additionalProperties"] = False
            for value in node.values():
                visit(value)
        elif isinstance(node, list):
            for value in node:
                visit(value)

    visit(cloned)
    return cloned


def validate_schema_contract(network: dict) -> list[str]:
    validator = jsonschema.Draft202012Validator(strict_schema(load_schema(SCHEMA_PATH)))
    return [error.message for error in sorted(validator.iter_errors(network), key=lambda e: list(e.path))]


def validate_embedding_probe_contract(probe: dict) -> list[str]:
    validator = jsonschema.Draft202012Validator(strict_schema(load_schema(EMBEDDING_PROBE_SCHEMA_PATH)))
    return [error.message for error in sorted(validator.iter_errors(probe), key=lambda e: list(e.path))]


def _ids(items: list[dict], key: str, namespace: str, nid: str, errors: list[str]) -> set[str]:
    seen: set[str] = set()
    ids: set[str] = set()
    for item in items:
        value = item.get(key)
        if not value:
            continue
        if value in seen:
            errors.append(f"{nid}: duplicate {namespace} id {value}")
        seen.add(value)
        ids.add(value)
    return ids


def _is_blank(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, list):
        return not value or all(_is_blank(item) for item in value)
    if isinstance(value, dict):
        return not value
    return False


def _require_non_empty(nid: str, owner: str, item: dict, fields: tuple[str, ...], errors: list[str]) -> None:
    for field in fields:
        value = item.get(field)
        if _is_blank(value):
            errors.append(f"{nid}: {owner} missing non-empty {field}")


def _check_refs(nid: str, owner: str, refs: list[str], allowed: set[str], errors: list[str]) -> None:
    for ref in refs:
        if ref not in allowed:
            errors.append(f"{nid}: {owner} dangling reference {ref}")


def _external_ref_ids(item: dict) -> set[str]:
    refs = item.get("external_refs", [])
    return {ref.get("ref_id") for ref in refs if ref.get("ref_id")}


def _check_no_cross_namespace_collisions(nid: str, namespaces: dict[str, set[str]], errors: list[str]) -> None:
    owners: dict[str, list[str]] = {}
    for namespace, values in namespaces.items():
        for value in values:
            if value:
                owners.setdefault(value, []).append(namespace)
    for value, places in sorted(owners.items()):
        if len(places) > 1:
            errors.append(f"{nid}: diff reference namespace collision {value} in {', '.join(places)}")


def _validate_external_refs(nid: str, diff: dict, local_domain: set[str], errors: list[str]) -> set[str]:
    seen: dict[str, str] = {}
    ids: set[str] = set()
    for ref in diff.get("external_refs", []):
        ref_id = ref.get("ref_id")
        ref_type = ref.get("ref_type")
        owner = f"diff {diff.get('diff_id')} external_ref {ref_id}"
        _require_non_empty(nid, owner, ref, ("ref_id", "ref_type", "claim_ceiling"), errors)
        if not ref_id:
            continue
        if ref_id in local_domain:
            errors.append(f"{nid}: diff {diff.get('diff_id')} external_ref {ref_id} collides with local diff reference")
        if ref_id in seen:
            if seen[ref_id] != ref_type:
                errors.append(f"{nid}: conflicting external ref {ref_id} types {seen[ref_id]} and {ref_type}")
            else:
                errors.append(f"{nid}: duplicate external ref id {ref_id}")
        seen[ref_id] = ref_type
        ids.add(ref_id)
    return ids


def validate_network(network: dict) -> list[str]:
    errors: list[str] = []
    nid = network.get("network_spec", {}).get("network_id", "<missing>")
    errors.extend(f"{nid}: schema {message}" for message in validate_schema_contract(network))
    if network.get("network_spec", {}).get("not_truth_layer") is not True:
        errors.append(f"{nid}: missing not_truth_layer")
    _require_non_empty(nid, "network_spec", network.get("network_spec", {}), ("network_id", "as_of_commit", "purpose", "canonical_authority", "claim_ceiling"), errors)
    node_ids = _ids(network.get("nodes", []), "node_id", "node", nid, errors)
    rel_ids = _ids(network.get("relations", []), "relation_id", "relation", nid, errors)
    layer_ids = _ids(network.get("layers", []), "layer_id", "layer", nid, errors)
    hyper_ids = _ids(network.get("hyper_relations", []), "hyper_id", "hyperrelation", nid, errors)
    coupling_ids = _ids(network.get("interlayer_couplings", []), "coupling_id", "coupling", nid, errors)
    activation_ids = _ids(network.get("temporal_activations", []), "activation_id", "activation", nid, errors)
    state_ids = _ids(network.get("network_states", []), "state_id", "state", nid, errors)
    perturbation_ids = _ids(network.get("perturbations", []), "perturbation_id", "perturbation", nid, errors)
    response_ids = _ids(network.get("integration_responses", []), "response_id", "integration response", nid, errors)
    episode_ids = _ids(network.get("reconfiguration_episodes", []), "episode_id", "reconfiguration episode", nid, errors)
    evidence_ids = _ids(network.get("embedding_evidence", []), "record_id", "embedding evidence", nid, errors)
    projection_ids = _ids(network.get("projections", []), "projection_id", "projection", nid, errors)
    diff_ids = _ids(network.get("diffs", []), "diff_id", "diff", nid, errors)
    residue_ids = _ids(network.get("unmapped_residue", []), "residue_id", "residue", nid, errors)
    attractor_ids = _ids(network.get("attractor_or_oscillation", []), "record_id", "attractor", nid, errors)
    cascade_ids = _ids(network.get("cascade_or_spillover", []), "record_id", "cascade", nid, errors)
    _ = (hyper_ids, coupling_ids, activation_ids, response_ids, episode_ids, diff_ids, residue_ids, attractor_ids, cascade_ids)
    network_ids = {network.get("network_spec", {}).get("network_id", "")}
    _check_no_cross_namespace_collisions(
        nid,
        {"network_id": network_ids, "state_id": state_ids, "projection_id": projection_ids},
        errors,
    )
    diff_ref_domain = network_ids | state_ids | projection_ids
    for node in network.get("nodes", []):
        _check_refs(nid, f"node {node.get('node_id')} layer", node.get("layers", []), layer_ids, errors)
        _require_non_empty(nid, f"node {node.get('node_id')}", node, ("provenance", "uncertainty", "claim_ceiling"), errors)
    for rel in network.get("relations", []):
        rid = rel.get("relation_id")
        if rel.get("source") not in node_ids or rel.get("target") not in node_ids:
            errors.append(f"{nid}: {rid} dangling endpoint")
        if rel.get("layer") not in layer_ids:
            errors.append(f"{nid}: {rid} dangling layer")
        _require_non_empty(nid, f"relation {rid}", rel, ("provenance", "uncertainty", "claim_ceiling", "temporal_bounds"), errors)
        try:
            parse_interval(rel["temporal_bounds"])
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"{nid}: {rid} invalid interval {exc}")
        text = json.dumps(rel, ensure_ascii=False).lower()
        if rel.get("relation_class") != "causal_delegated_to_mcf" and "causal proof" in text:
            errors.append(f"{nid}: relation upgraded to causality")
        if any(term in text for term in ("centrality proves", "similarity proves", "community proves", "adjacency proves")):
            errors.append(f"{nid}: network metric overclaim")
    for hyper in network.get("hyper_relations", []):
        if len(hyper.get("members", [])) < 3 or hyper.get("preserve_as_higher_order") is not True:
            errors.append(f"{nid}: hyper relation silently collapsed")
        if len(hyper.get("members", [])) != len(list(dict.fromkeys(hyper.get("members", [])))):
            errors.append(f"{nid}: hyper relation {hyper.get('hyper_id')} repeated member")
        _check_refs(nid, f"hyper relation {hyper.get('hyper_id')}", hyper.get("members", []), node_ids | rel_ids, errors)
        _require_non_empty(nid, f"hyper relation {hyper.get('hyper_id')}", hyper, ("residue_if_projected", "provenance", "claim_ceiling"), errors)
    for coupling in network.get("interlayer_couplings", []):
        _check_refs(nid, f"coupling {coupling.get('coupling_id')}", [coupling.get("from_layer"), coupling.get("to_layer")], layer_ids, errors)
        _require_non_empty(nid, f"coupling {coupling.get('coupling_id')}", coupling, ("provenance", "claim_ceiling"), errors)
    for activation in network.get("temporal_activations", []):
        _check_refs(nid, f"activation {activation.get('activation_id')}", [activation.get("target_ref")], node_ids | rel_ids, errors)
        try:
            parse_interval({"start": activation["start"], "end": activation["end"]})
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"{nid}: activation {activation.get('activation_id')} invalid interval {exc}")
    for state in network.get("network_states", []):
        _check_refs(nid, f"state {state.get('state_id')} active_nodes", state.get("active_nodes", []), node_ids, errors)
        _check_refs(nid, f"state {state.get('state_id')} active_relations", state.get("active_relations", []), rel_ids, errors)
        _require_non_empty(nid, f"state {state.get('state_id')}", state, ("unknowns",), errors)
    for perturbation in network.get("perturbations", []):
        _check_refs(nid, f"perturbation {perturbation.get('perturbation_id')}", perturbation.get("target_nodes", []), node_ids, errors)
        _require_non_empty(nid, f"perturbation {perturbation.get('perturbation_id')}", perturbation, ("provenance", "claim_ceiling"), errors)
    for response in network.get("integration_responses", []):
        _check_refs(nid, f"response {response.get('response_id')} perturbation", [response.get("perturbation_ref")], perturbation_ids, errors)
        _check_refs(nid, f"response {response.get('response_id')} evidence", [response.get("evidence_ref")], evidence_ids, errors)
        _require_non_empty(nid, f"response {response.get('response_id')}", response, ("alternative_explanations", "claim_ceiling"), errors)
    for episode in network.get("reconfiguration_episodes", []):
        _check_refs(nid, f"episode {episode.get('episode_id')} states", [episode.get("baseline_state"), episode.get("post_state")], state_ids, errors)
        _check_refs(nid, f"episode {episode.get('episode_id')} changed_nodes", episode.get("changed_nodes", []), node_ids, errors)
        _check_refs(nid, f"episode {episode.get('episode_id')} unchanged_nodes", episode.get("unchanged_nodes", []), node_ids, errors)
        _check_refs(nid, f"episode {episode.get('episode_id')} changed_relations", episode.get("changed_relations", []), rel_ids, errors)
        _check_refs(nid, f"episode {episode.get('episode_id')} unchanged_relations", episode.get("unchanged_relations", []), rel_ids, errors)
        if set(episode.get("changed_nodes", [])) & set(episode.get("unchanged_nodes", [])):
            errors.append(f"{nid}: episode {episode.get('episode_id')} overlaps changed/unchanged nodes")
        if set(episode.get("changed_relations", [])) & set(episode.get("unchanged_relations", [])):
            errors.append(f"{nid}: episode {episode.get('episode_id')} overlaps changed/unchanged relations")
        _require_non_empty(nid, f"episode {episode.get('episode_id')}", episode, ("residue", "claim_ceiling"), errors)
    for attractor in network.get("attractor_or_oscillation", []):
        _require_non_empty(nid, f"attractor {attractor.get('record_id')}", attractor, ("loop_pattern", "claim_ceiling"), errors)
    for cascade in network.get("cascade_or_spillover", []):
        path = cascade.get("path", [])
        if not all(rid in rel_ids for rid in path):
            errors.append(f"{nid}: cascade path missing relation")
        if cascade.get("time_respecting") is True and not time_respecting_graph_path(network, path):
            errors.append(f"{nid}: cascade claims graph path but fails topology-aware temporal semantics")
        if cascade.get("not_causality") is not True:
            errors.append(f"{nid}: cascade treated as causality")
        _require_non_empty(nid, f"cascade {cascade.get('record_id')}", cascade, ("path", "claim_ceiling"), errors)
    for projection in network.get("projections", []):
        if projection.get("not_canonical") is not True:
            errors.append(f"{nid}: projection may replace canonical source")
        if projection.get("source_network") not in {network.get("network_spec", {}).get("network_id")} | projection_ids:
            errors.append(f"{nid}: projection {projection.get('projection_id')} dangling source_network")
        _require_non_empty(nid, f"projection {projection.get('projection_id')}", projection, ("projection_rules", "omitted_dimensions", "claim_ceiling"), errors)
    for diff in network.get("diffs", []):
        _require_non_empty(nid, f"diff {diff.get('diff_id')}", diff, ("from_ref", "to_ref", "claim_ceiling"), errors)
        external_ids = _validate_external_refs(nid, diff, diff_ref_domain, errors)
        local_or_external = diff_ref_domain | external_ids
        _check_refs(nid, f"diff {diff.get('diff_id')} from_ref", [diff.get("from_ref")], local_or_external, errors)
        _check_refs(nid, f"diff {diff.get('diff_id')} to_ref", [diff.get("to_ref")], local_or_external, errors)
    for evidence in network.get("embedding_evidence", []):
        required = ("external_availability", "retrieval", "relational_linkage", "conflict_exposure", "judgment_change", "action_change", "transfer", "delayed_stability", "alternatives", "evidence", "claim_ceiling")
        _require_non_empty(nid, f"embedding evidence {evidence.get('record_id')}", evidence, required, errors)
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
    for residue in network.get("unmapped_residue", []):
        _require_non_empty(nid, f"residue {residue.get('residue_id')}", residue, ("description", "claim_ceiling"), errors)
    return errors


def validate_all() -> dict:
    failures = {}
    paths = iter_network_paths()
    for path in paths:
        errors = validate_network(load_network(path))
        if errors:
            failures[str(path)] = errors
    probe_path = EXAMPLE_DIR / "embedding-probe.json"
    probe_errors = validate_embedding_probe_contract(load_network(probe_path))
    if probe_errors:
        failures[str(probe_path)] = [f"schema {message}" for message in probe_errors]
    return {"checked": len(paths), "failures": failures, "status": "PASS" if not failures else "FAIL"}


def main() -> int:
    result = validate_all()
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
