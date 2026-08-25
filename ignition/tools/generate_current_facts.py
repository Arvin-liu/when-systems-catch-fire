#!/usr/bin/env python3
"""Build and check the deterministic current-facts projection.

The projection is a bounded derived view.  Canonical registries, manifests,
topology, pack declarations and the federation inventory remain authoritative;
this file records their current, reproducible facts and source fingerprints.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import validate_current_state_sync as sync

from agent_federation.live_current_projection import validate_projection

try:
    from tools import iteration_boundary, task_identity
except ImportError:
    import iteration_boundary
    import task_identity


HERE = Path(__file__).resolve()
ROOT = HERE.parents[1]
REPO_ROOT = ROOT.parent
CONTRACT_PATH = ROOT / "data/architecture/current-system-identity.json"
FACTS_PATH = ROOT / "data/architecture/current-facts.json"
FACTS_MARKDOWN_PATH = ROOT / "docs/architecture/current-facts.md"
SCHEMA_PATH = ROOT / "schemas/architecture/current-facts.schema.json"
STEERING_PATH = ROOT / "data/operations/steering/current-state-r1.json"
SEMANTICS_PATH = ROOT / "data/operations/iteration-boundary-semantics-r1.json"
LIFECYCLE_PATH = ROOT / "data/operations/current-release-lifecycle-r1.json"
MATERIALITY_PATH = ROOT / "data/governance/human-surface/materiality-manifest.json"
KNOWLEDGE_MANIFEST_PATH = ROOT / "data/governance/knowledge-experience/manifest.json"
FIRE_SEEDS_PATH = ROOT / "data/publication/fire-seeds/seed-census.json"
LIVE_CURRENT_PROJECTION_PATH = ROOT / "data/operations/iterations/140/live-current-projection-r2.json"
LIVE_ATTEMPT_LEDGER_PATH = ROOT / "data/operations/iterations/139/live-attempt-ledger.jsonl"
LIVE_RECONCILIATION_EVENTS_PATH = ROOT / "data/operations/iterations/140/live-reconciliation-events-r1.jsonl"
LIVE_OBSERVATION_EVENTS_PATH = ROOT / "data/operations/iterations/140/live-observation-events-r1.jsonl"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def materiality_fingerprint(document: dict[str, Any]) -> str:
    """Fingerprint materiality selection without reciprocal bookkeeping hashes.

    The manifest records ``machine_record_sha256`` and ``source_sha256`` for
    selected Human Surface entries. Those fields are checked by the Human
    Surface contract, but they are derived bookkeeping: the Current Facts
    projection consumes the manifest, while the Current Surface compiler
    changes the very sources named by it. Excluding only these two reciprocal
    fields keeps the canonical selection/count projection observable without
    making manifest -> facts -> snapshot -> surface -> manifest a cycle.
    """
    normalized = json.loads(json.dumps(document, ensure_ascii=False))
    for entry in normalized.get("entries", []):
        entry.pop("machine_record_sha256", None)
        entry.pop("source_sha256", None)
    payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def knowledge_manifest_fingerprint(document: dict[str, Any]) -> str:
    """Fingerprint Knowledge inputs/counts without generated-output feedback.

    ``generated_outputs`` contains hashes of the human Knowledge projection.
    Those projections include source fingerprints for Current Human Surfaces;
    feeding their output digests into Current Facts would create a reciprocal
    Current Facts -> Snapshot -> Human Surface -> Knowledge -> Current Facts
    cycle.  Counts, policy, machine/human pairing and canonical source inputs
    remain authoritative here; generated-output hashes have their own
    Knowledge determinism gate.
    """
    normalized = json.loads(json.dumps(document, ensure_ascii=False))
    normalized.pop("generated_outputs", None)
    payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def fire_seed_fingerprint(document: dict[str, Any]) -> str:
    """Fingerprint Fire Seeds without source-hash feedback from Human Surfaces.

    The Fire Seeds validator owns the 393 per-source hashes.  Current Facts
    consumes the stable seed/disposition projection and its counts, but must
    not feed those source hashes back into the Current Snapshot: a legitimate
    Current Surface refresh would otherwise create the same reciprocal cycle
    through Knowledge and Fire Seeds.
    """
    normalized = json.loads(json.dumps(document, ensure_ascii=False))
    for row in normalized.get("source_census", []):
        row.pop("source_sha256", None)
    payload = json.dumps(normalized, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def source_fingerprint(path: Path) -> str:
    if path.resolve() == MATERIALITY_PATH.resolve():
        return materiality_fingerprint(load_json(path))
    if path.resolve() == KNOWLEDGE_MANIFEST_PATH.resolve():
        return knowledge_manifest_fingerprint(load_json(path))
    if path.resolve() == FIRE_SEEDS_PATH.resolve():
        return fire_seed_fingerprint(load_json(path))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_paths(contract: dict[str, Any]) -> list[Path]:
    paths: set[Path] = {
        CONTRACT_PATH,
        HERE,
        SCHEMA_PATH,
        sync.SCHEMA_PATH,
        sync.resolve_repo_path(contract["current_map"]["source_path"]),
        sync.resolve_repo_path(contract["current_method"]["source_path"]),
        sync.resolve_repo_path("ignition/data/operations/project-components.json"),
        sync.resolve_repo_path("ignition/data/operations/change-propagation-topology.json"),
        sync.resolve_repo_path("ignition/data/agent-federation/executor-inventory-r1.json"),
        sync.resolve_repo_path("ignition/data/governance/human-surface/materiality-manifest.json"),
        sync.resolve_repo_path("ignition/data/governance/human-results/config.json"),
        sync.resolve_repo_path("ignition/data/operations/synchronization-surfaces.json"),
        sync.resolve_repo_path(contract["current_task_lineage"]["source_path"]),
        sync.resolve_repo_path(contract["current_task_lineage"]["schema_path"]),
        sync.resolve_repo_path(contract["current_task_lineage"]["validator_path"]),
        STEERING_PATH,
        SEMANTICS_PATH,
        iteration_boundary.HERE,
        Path(task_identity.__file__).resolve(),
        LIFECYCLE_PATH,
        LIVE_ATTEMPT_LEDGER_PATH,
        LIVE_RECONCILIATION_EVENTS_PATH,
        LIVE_OBSERVATION_EVENTS_PATH,
        LIVE_CURRENT_PROJECTION_PATH,
    }
    for metric in contract["derived_metrics"]:
        paths.add(sync.resolve_repo_path(metric["source_path"]))
    for pack_path in sorted((ROOT / "packs").glob("*/manifest.json")):
        paths.add(pack_path)
    lineage = load_json(sync.resolve_repo_path(contract["current_task_lineage"]["source_path"]))
    try:
        current_ordinal = task_identity.parse_task_id(lineage["task_identity"]["current_formal_task"])["ordinal"]
        architecture_ordinal = task_identity.parse_task_id(lineage["task_identity"]["latest_architecture_changing_task"])["ordinal"]
    except (KeyError, task_identity.TaskIdentityError) as exc:
        raise ValueError(f"cannot derive current live-evidence ordinal: {exc}") from exc
    for relative_path in (
        # Task136 used the generic preflight/receipt names; Task137 records
        # its current-cli eligibility and bounded attempt under explicit
        # step names.  Keep both forms so historical current projections can
        # still be regenerated without importing a newer task's vocabulary.
        f"ignition/data/operations/iterations/{current_ordinal}/step03-codex-live-eligibility.json",
        f"ignition/data/operations/iterations/{current_ordinal}/step09-live-codex-attempt.json",
        f"ignition/data/operations/iterations/{architecture_ordinal}/step11-live-preflight.json",
        f"ignition/data/operations/iterations/{architecture_ordinal}/step13-live-execution-receipt.json",
    ):
        candidate = sync.resolve_repo_path(relative_path)
        if candidate.is_file():
            paths.add(candidate)
    ordered = sorted(paths, key=relative)
    relative_paths = [relative(path) for path in ordered]
    if relative_paths != sorted(relative_paths) or len(relative_paths) != len(set(relative_paths)):
        raise ValueError("current-facts source paths must be sorted and unique")
    return ordered


def build_projection(contract: dict[str, Any] | None = None) -> dict[str, Any]:
    contract = contract or load_json(CONTRACT_PATH)
    iteration = iteration_boundary.derive()
    for key in (
        "current_formal_task_id",
        "current_formal_task_ordinal",
        "latest_architecture_changing_task_id",
        "latest_architecture_task_ordinal",
        "current_iteration_boundary",
    ):
        if contract.get(key) != iteration[key]:
            raise ValueError(f"identity contract {key} is not the canonical derived value")
    metrics, errors = sync.derive_metrics(contract)
    if errors:
        raise ValueError("cannot derive current facts: " + "; ".join(errors))

    map_layout = load_json(sync.resolve_repo_path(contract["current_map"]["source_path"]))
    inventory = load_json(sync.resolve_repo_path("ignition/data/agent-federation/executor-inventory-r1.json"))
    pack_paths = sorted((ROOT / "packs").glob("*/manifest.json"), key=relative)
    packs = [load_json(path) for path in pack_paths]
    materiality = load_json(sync.resolve_repo_path("ignition/data/governance/human-surface/materiality-manifest.json"))
    human_config = load_json(sync.resolve_repo_path("ignition/data/governance/human-results/config.json"))
    sync_registry = load_json(sync.resolve_repo_path("ignition/data/operations/synchronization-surfaces.json"))
    task_lineage = load_json(sync.resolve_repo_path(contract["current_task_lineage"]["source_path"]))
    steering = load_json(STEERING_PATH)
    live_projection = validate_projection(load_json(LIVE_CURRENT_PROJECTION_PATH))
    sync_surfaces = sync_registry.get("surfaces", [])
    role_counts = Counter(role for row in sync_surfaces for role in row.get("roles", []))
    executors = inventory.get("executors", [])
    live_statuses = {row["executor_id"]: row.get("live_smoke", {}).get("status", "UNDECLARED") for row in executors}
    live_ceiling = live_projection["current_live_ceiling"]
    current_ordinal = iteration["current_formal_task_ordinal"]
    architecture_ordinal = iteration["latest_architecture_task_ordinal"]
    live_evidence_paths = [
        ROOT / f"data/operations/iterations/{current_ordinal}/step03-codex-live-eligibility.json",
        ROOT / f"data/operations/iterations/{architecture_ordinal}/step11-live-preflight.json",
    ]
    for preflight_path in live_evidence_paths:
        if not preflight_path.is_file():
            continue
        preflight = load_json(preflight_path)
        entries = list(preflight.get("entries", []))
        executor = preflight.get("executor")
        lease = preflight.get("capability_lease")
        if isinstance(executor, dict):
            entries.append(executor)
        if isinstance(lease, dict) and isinstance(executor, dict):
            entries.append({"executor_id": executor.get("executor_id"), "eligibility": lease.get("live_eligibility")})
        for entry in entries:
            executor_id = entry.get("executor_id")
            eligibility = entry.get("eligibility") or entry.get("live_eligibility")
            if executor_id and eligibility:
                live_statuses[executor_id] = eligibility
    live_receipt_paths = [
        ROOT / f"data/operations/iterations/{current_ordinal}/step09-live-codex-attempt.json",
        ROOT / f"data/operations/iterations/{architecture_ordinal}/step13-live-execution-receipt.json",
    ]
    for live_receipt_path in live_receipt_paths:
        if not live_receipt_path.is_file():
            continue
        live_execution = load_json(live_receipt_path)
        receipt = live_execution.get("receipt", {}) or live_execution.get("executor_receipt", {})
        executor_id = receipt.get("executor_id")
        receipt_state = receipt.get("state") or live_execution.get("status")
        if executor_id and receipt_state:
            live_statuses[executor_id] = receipt_state
        # Historical receipt state is retained for provenance, but the live
        # Current ceiling is always ledger-derived.  A stale historical result
        # must never overwrite the durable attempt projection.
    for executor_id, summary in live_projection["latest_attempt_per_executor"].items():
        live_statuses[executor_id] = summary["state"]
    residuals = inventory.get("repository_audit", {}).get("residuals", [])
    method_text = sync.resolve_repo_path(contract["current_method"]["source_path"]).read_text(encoding="utf-8")
    method_match = re.search(r"^Current:\s*`([^`]+)`", method_text, re.MULTILINE)
    if not method_match:
        raise ValueError("cannot derive current method version")

    facts = {
        "architecture": {
            "registry_components": metrics["registry_components"],
            "visible_map_nodes": metrics["visible_map_nodes"],
            "hidden_components": metrics["hidden_components"],
            "typed_topology_relations": metrics["typed_topology_relations"],
            "visible_typed_edges": metrics["visible_typed_edges"],
            "current_map_version": map_layout["current_map_version"],
            "historical_map_version": map_layout["historical_map_version"],
            "layout_version": map_layout["layout_version"],
            "semantic_trunk_version": map_layout["semantic_trunk"]["schema_version"],
            "semantic_trunk_route_steps": len(map_layout["semantic_trunk"]["route"]),
        },
        "packs": {
            "count": len(packs),
            "capability_route_count": sum(len(pack.get("capabilities_provided", [])) for pack in packs),
            "pack_ids": sorted(pack["pack_id"] for pack in packs),
        },
        "federation": {
            "adapter_inventory_count": len(executors),
            "adapter_ids": sorted(row["executor_id"] for row in executors),
            "live_status_by_executor": dict(sorted(live_statuses.items())),
            "live_invocation_ceiling": live_ceiling,
            "live_attempt_projection": {
                "source_path": relative(LIVE_CURRENT_PROJECTION_PATH),
                "projection_digest": live_projection["projection_digest"],
                "total_attempts": live_projection["counts"]["total_attempts"],
                "validated_completion_count": live_projection["counts"]["validated_completion_count"],
                "unreconciled_count": live_projection["counts"]["unreconciled_count"],
                "observation_incomplete_count": live_projection["counts"]["observation_incomplete_count"],
                "current_live_ceiling": live_projection["current_live_ceiling"],
                "obligation_state": live_projection["obligation"]["state"],
                "unreconciled_attempt_ids": live_projection["obligation"]["unreconciled_attempt_ids"],
                "next_action_status": live_projection["next_eligible_action"]["status"],
                "next_action": live_projection["next_eligible_action"]["action"],
            },
            "reference_executor_identity": "REFERENCE_EXECUTOR / CONFORMANCE_EXECUTOR / FALLBACK_MINIMAL",
        },
        "foundation": {
            "function_identity_cards": metrics["function_identity_cards"],
            "function_quarantine_or_pending": metrics["function_quarantine_or_pending"],
            "nonfunction_claims": metrics["nonfunction_claims"],
            "nonfunction_quarantine_or_pending": metrics["nonfunction_quarantine_or_pending"],
        },
        "knowledge_experience": {
            "cards": metrics["knowledge_cards"],
            "changes": metrics["knowledge_changes"],
            "layered_readings": metrics["knowledge_layered_readings"],
            "search_records": metrics["knowledge_search_records"],
            "aliases": metrics["knowledge_aliases"],
        },
        "fire_seeds": {
            "seed_count": metrics["fire_seeds"],
            "source_census_count": metrics["fire_seed_sources"],
        },
        "human_surface": {
            "materiality_entries": len(materiality.get("entries", [])),
            "function_human_entries": materiality.get("counts", {}).get("function_human", 0),
            "nonfunction_human_entries": materiality.get("counts", {}).get("nonfunction_human", 0),
            "registered_synchronization_surfaces": len(sync_surfaces),
            "machine_human_pairs": len(human_config.get("machine_human_pairs", [])),
            "surface_role_counts": dict(sorted(role_counts.items())),
        },
        "iteration": {
            "current_formal_task_id": iteration["current_formal_task_id"],
            "current_formal_task_ordinal": iteration["current_formal_task_ordinal"],
            "latest_architecture_changing_task_id": iteration["latest_architecture_changing_task_id"],
            "latest_architecture_task_ordinal": iteration["latest_architecture_task_ordinal"],
            "current_iteration_boundary": iteration["current_iteration_boundary"],
            "current_iteration_boundary_semantics": iteration["current_iteration_boundary_semantics"],
            "method_version": iteration["current_method_version"],
            "method_status": contract["current_method"]["status"],
            "current_map_version": map_layout["current_map_version"],
        },
        "task_lineage": {
            "current_task_id": task_lineage["current_task"]["task_id"],
            "current_task_status": task_lineage["current_task"]["execution_status"],
            "task125_file_status": task_lineage["lineages"][0]["predecessor"]["task_file_status"],
            "task125_requirement_lineage_status": task_lineage["lineages"][0]["predecessor"]["requirement_lineage_status"],
            "task125_canonical_status": task_lineage["lineages"][0]["predecessor"]["canonical_status"],
            "task127_status": task_lineage["lineages"][0]["successor"]["execution_status"],
        },
        "steering": {
            "current_status": steering["current_status"],
            "invariant_ids": steering["identity_invariants"],
            "module_count": len(steering["modules"]),
            "integration_surface_count": len(steering["integration_surfaces"]),
            "pilot_status": steering["pilot_status"],
            "completion_boundary": steering["completion_boundary"],
        },
        "environmental_residuals": sorted(str(item) for item in residuals),
    }
    projection = {
        "schema_version": "current-facts-r1",
        "contract_id": contract["contract_id"],
        "identity_epoch": contract["identity_epoch"],
        "current_formal_task_id": iteration["current_formal_task_id"],
        "current_formal_task_ordinal": iteration["current_formal_task_ordinal"],
        "latest_architecture_changing_task_id": iteration["latest_architecture_changing_task_id"],
        "latest_architecture_task_ordinal": iteration["latest_architecture_task_ordinal"],
        "current_iteration_boundary": iteration["current_iteration_boundary"],
        "current_iteration_boundary_semantics": iteration["current_iteration_boundary_semantics"],
        "facts": facts,
        "source_fingerprints": [{"path": relative(path), "sha256": source_fingerprint(path)} for path in source_paths(contract)],
        "claim_ceiling": "Deterministic repository-derived current facts and navigation support only; no external truth, Owner acceptance, production safety or epistemic upgrade.",
    }
    return projection


def render_json(projection: dict[str, Any]) -> bytes:
    return (json.dumps(projection, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def render_markdown(projection: dict[str, Any]) -> bytes:
    facts = projection["facts"]
    architecture = facts["architecture"]
    packs = facts["packs"]
    federation = facts["federation"]
    foundation = facts["foundation"]
    knowledge = facts["knowledge_experience"]
    fire_seeds = facts["fire_seeds"]
    human = facts["human_surface"]
    iteration = facts["iteration"]
    steering = facts["steering"]
    residuals = facts["environmental_residuals"]
    lines = [
        "<!-- BEGIN GENERATED CURRENT-FACTS r1; DO NOT EDIT -->",
        "# Current Facts（机器推导事实）",
        "",
        f"- Iteration identity: current formal task `{iteration['current_formal_task_id']}` (ordinal `{iteration['current_formal_task_ordinal']}`)；latest architecture-changing task `{iteration['latest_architecture_changing_task_id']}` (ordinal `{iteration['latest_architecture_task_ordinal']}`)；`current_iteration_boundary` `{projection['current_iteration_boundary']}` is a deprecated compatibility alias of the formal ordinal。",
        f"- Architecture registry: `{architecture['registry_components']}` components；`{architecture['visible_map_nodes']}` visible map nodes；`{architecture['hidden_components']}` hidden represented components；`{architecture['typed_topology_relations']}` typed relations；`{architecture['visible_typed_edges']}` visible typed edges。",
        f"- Map/method: map `{architecture['current_map_version']}` Current（historical `{architecture['historical_map_version']}`）；layout `{architecture['layout_version']}`；semantic trunk `{architecture['semantic_trunk_version']}` with `{architecture['semantic_trunk_route_steps']}` bounded route stages；method `{iteration['method_version']}` `{iteration['method_status']}`。",
        f"- Packs: `{packs['count']}` packs；`{packs['capability_route_count']}` declared capability routes。",
        f"- Federation: `{federation['adapter_inventory_count']}` adapter inventory entries；live ceiling `{federation['live_invocation_ceiling']}`；local boundary `{federation['reference_executor_identity']}`。",
        f"- Live attempts: total `{federation['live_attempt_projection']['total_attempts']}`；validated `{federation['live_attempt_projection']['validated_completion_count']}`；unreconciled `{federation['live_attempt_projection']['unreconciled_count']}`；observation-incomplete `{federation['live_attempt_projection']['observation_incomplete_count']}`；obligation `{federation['live_attempt_projection']['obligation_state']}`；next action `{federation['live_attempt_projection']['next_action']}`；source `{federation['live_attempt_projection']['source_path']}`。",
        f"- Foundation: function identity cards `{foundation['function_identity_cards']}`；function quarantine/pending `{foundation['function_quarantine_or_pending']}`；non-function claims `{foundation['nonfunction_claims']}`；non-function quarantine/pending `{foundation['nonfunction_quarantine_or_pending']}`。",
        f"- Knowledge Experience: cards `{knowledge['cards']}`；changes `{knowledge['changes']}`；layered readings `{knowledge['layered_readings']}`；search records `{knowledge['search_records']}`；aliases `{knowledge['aliases']}`。",
        f"- Fire Seeds: `{fire_seeds['seed_count']}` seeds/clusters；`{fire_seeds['source_census_count']}` source-census records。",
        f"- Human Surface: `{human['materiality_entries']}` materiality entries（function `{human['function_human_entries']}` + non-function `{human['nonfunction_human_entries']}`）；`{human['registered_synchronization_surfaces']}` registered sync surfaces；`{human['machine_human_pairs']}` machine/human pairs。",
        f"- Task lineage: current `{facts['task_lineage']['current_task_id']}` `{facts['task_lineage']['current_task_status']}`；125 file `{facts['task_lineage']['task125_file_status']}`, requirements `{facts['task_lineage']['task125_requirement_lineage_status']}`, canonical `{facts['task_lineage']['task125_canonical_status']}`；127 `{facts['task_lineage']['task127_status']}`。",
        f"- Steering: `{steering['current_status']}`；`{steering['module_count']}` bounded modules；`{steering['integration_surface_count']}` integration surfaces；pilot `{steering['pilot_status']}`；completion boundary `{steering['completion_boundary']}`。",
        "- Current environmental residuals: " + ("；".join(residuals) if residuals else "none declared") + "。",
        "",
        "Source authority: the JSON projection records SHA-256 fingerprints for the canonical registries, manifests, topology, pack declarations, federation inventory and generator/schema inputs. For the Human Surface materiality manifest, the fingerprint intentionally excludes only reciprocal machine/source hash fields; the selection, counts and policy remain included. Human prose may explain these facts but is not a second numeric authority.",
        "Claim ceiling: " + projection["claim_ceiling"],
        "",
        "Machine source: [`current-facts.json`](../../data/architecture/current-facts.json).",
        "<!-- END GENERATED CURRENT-FACTS r1 -->",
        "",
    ]
    return "\n".join(lines).encode("utf-8")


def check() -> list[str]:
    contract = load_json(CONTRACT_PATH)
    expected_json = render_json(build_projection(contract))
    expected_markdown = render_markdown(build_projection(contract))
    errors: list[str] = []
    if not FACTS_PATH.is_file() or FACTS_PATH.read_bytes() != expected_json:
        errors.append(f"stale or missing generated projection: {relative(FACTS_PATH)}")
    if not FACTS_MARKDOWN_PATH.is_file() or FACTS_MARKDOWN_PATH.read_bytes() != expected_markdown:
        errors.append(f"stale or missing generated facts block: {relative(FACTS_MARKDOWN_PATH)}")
    return errors


def write() -> None:
    contract = load_json(CONTRACT_PATH)
    projection = build_projection(contract)
    FACTS_PATH.write_bytes(render_json(projection))
    FACTS_MARKDOWN_PATH.write_bytes(render_markdown(projection))
    print(f"CURRENT_FACTS_WRITTEN json={relative(FACTS_PATH)} markdown={relative(FACTS_MARKDOWN_PATH)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write == args.check:
        parser.error("choose exactly one of --write or --check")
    if args.write:
        write()
        return 0
    errors = check()
    if errors:
        print("CURRENT_FACTS_INVALID", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print("CURRENT_FACTS_DETERMINISTIC_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
