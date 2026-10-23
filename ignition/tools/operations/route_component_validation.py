#!/usr/bin/env python3
"""Select repository tests from an exact Git diff and declared component closure.

This router is deliberately repository-scoped. It consumes the existing path
registry and typed change-propagation graph, then resolves the affected closure
to a versioned R/O/G test map. Unmapped paths, unknown components, cycles, or
missing targets block selective validation instead of becoming an empty pass.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[2]
CHECKOUT_ROOT = ROOT.parent
sys.path.insert(0, str(ROOT))
from tools.operations.compute_change_propagation import (  # noqa: E402
    detect_tracked_symlink_escapes,
    load_json,
    matches_pattern,
    normalize_repo_path,
    relation_is_triggered,
    resolve_paths,
)

REGISTRY_PATH = ROOT / "data/operations/project-components.json"
TOPOLOGY_PATH = ROOT / "data/operations/change-propagation-topology.json"
PROFILES_PATH = ROOT / "data/operations/component-execution-profiles.json"
MAP_PATH = ROOT / "data/operations/component-validation-map-r1.json"
MAP_SCHEMA_PATH = ROOT / "schemas/operations/component-validation-map-r1.schema.json"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DOMAINS = ("R", "O", "G")
LEAN_VALIDATION_COMMANDS = {"validate_l4_lean_foundation"}

# Changes to the impact authority or its execution gate cross every domain.
# They require the existing full Foundation regression before selective routing
# may be trusted for later changes.
FULL_REGRESSION_PATHS = {
    ".github/workflows/foundation-validation.yml",
    ".github/workflows/component-release.yml",
    ".github/workflows/repository-path-accounting-preflight.yml",
    ".github/CODEOWNERS",
    "requirements-foundation.txt",
    "data/operations/project-components.json",
    "data/operations/change-propagation-topology.json",
    "data/operations/component-execution-profiles.json",
    "data/operations/component-execution-profile-policies.json",
    "data/operations/component-validation-map-r1.json",
    "data/operations/component-release-policy-r1.json",
    "schemas/operations/project-components.schema.json",
    "schemas/operations/change-propagation-topology.schema.json",
    "schemas/operations/component-execution-profile.schema.json",
    "schemas/operations/incremental-execution-plan.schema.json",
    "schemas/operations/non-impact-proof.schema.json",
    "schemas/operations/component-validation-map-r1.schema.json",
    "schemas/operations/component-release-policy-r1.schema.json",
    "schemas/operations/component-release-manifest-r1.schema.json",
    "tools/operations/compute_change_propagation.py",
    "tools/operations/generate_component_profiles.py",
    "tools/operations/plan_incremental_execution.py",
    "tools/operations/route_component_validation.py",
    "tools/operations/run_component_validation_targets.py",
    "tools/operations/verify_component_validation_evidence.py",
    "tools/operations/write_final_main_witness.py",
    "tools/operations/prepare_component_release.py",
    "tools/operations/release_authorization.py",
    "tests/test_component_validation_routing.py",
    "tests/test_component_validation_evidence.py",
    "tests/test_component_release_preparation.py",
    "tests/test_component_release_authorization.py",
    "tests/test_history_remediation_contract.py",
}


class RoutingBlocked(ValueError):
    """The evidence is insufficient to safely select component tests."""


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _component_docs(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = registry.get("components", [])
    result = {item.get("component_id"): item for item in items}
    if None in result or len(result) != len(items):
        raise RoutingBlocked("component registry has missing or duplicate component IDs")
    return result


def validate_validation_map(
    registry: dict[str, Any], topology: dict[str, Any], validation_map: dict[str, Any],
    schema: dict[str, Any],
) -> None:
    errors = sorted(Draft202012Validator(schema).iter_errors(validation_map), key=lambda e: list(e.path))
    if errors:
        raise RoutingBlocked(f"validation map schema error at {list(errors[0].path)}: {errors[0].message}")

    components = _component_docs(registry)
    targets = {item["target_id"]: item for item in validation_map["targets"]}
    if len(targets) != len(validation_map["targets"]):
        raise RoutingBlocked("validation map has duplicate target IDs")
    assignments = validation_map["components"]
    assignment_ids = [item["component_id"] for item in assignments]
    if len(assignment_ids) != len(set(assignment_ids)):
        raise RoutingBlocked("validation map has duplicate component assignments")

    for assignment in assignments:
        component_id = assignment["component_id"]
        if component_id not in components:
            raise RoutingBlocked(f"validation map references unregistered component: {component_id}")
        domains = set(assignment["domains"])
        target_ids = assignment["validation_targets"]
        change_classifications = set(assignment["change_classifications"])
        full = assignment.get("requires_full_regression", False)
        if not change_classifications:
            raise RoutingBlocked(f"changed-component effect classification is missing: {component_id}")
        if full:
            if len(domains) < 2:
                raise RoutingBlocked(f"full-regression component {component_id} must have reviewed cross-domain impact")
        elif not target_ids:
            raise RoutingBlocked(f"routable component lacks validation targets: {component_id}")
        for target_id in target_ids:
            target = targets.get(target_id)
            if target is None:
                raise RoutingBlocked(f"component {component_id} references unknown target {target_id}")
            if target["domain"] not in domains:
                raise RoutingBlocked(
                    f"target {target_id} domain {target['domain']} is outside component {component_id} domains"
                )
    command_ids = [command_id for target in validation_map["targets"] for command_id in target.get("command_ids", [])]
    if len(command_ids) != len(set(command_ids)):
        raise RoutingBlocked("validation command IDs must be unique across targets")

    component_ids = set(components)
    seen_relations: set[str] = set()
    for relation in topology.get("relations", []):
        if relation["relation_id"] in seen_relations:
            raise RoutingBlocked(f"duplicate topology relation ID: {relation['relation_id']}")
        seen_relations.add(relation["relation_id"])
        if relation["source"] not in component_ids or relation["target"] not in component_ids:
            raise RoutingBlocked(f"topology relation references unknown component: {relation['relation_id']}")


def _effect_closure(
    seeds: set[str], topology: dict[str, Any], assignments: dict[str, dict[str, Any]],
    profiles: dict[str, Any],
) -> tuple[set[str], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, str]], list[dict[str, Any]]]:
    """Walk only relations triggered by each changed component's registered effect.

    Existing component execution profiles provide change dimensions. The
    versioned validation map provides the reviewed change classifications for
    that component's path ownership. Each traversed edge narrows the effect
    carried to its consumer so an unrelated seed's dimensions cannot trigger
    another component's dependency edge.
    """
    profile_by_id = {item["component_id"]: item for item in profiles.get("profiles", [])}
    queue: deque[tuple[str, frozenset[str], frozenset[str]]] = deque()
    effects: list[dict[str, Any]] = []
    for component_id in sorted(seeds):
        assignment = assignments.get(component_id)
        profile = profile_by_id.get(component_id)
        if assignment is None:
            raise RoutingBlocked(f"changed component has no reviewed domain/effect assignment: {component_id}")
        if profile is None:
            raise RoutingBlocked(f"changed component has no registered execution profile: {component_id}")
        dimensions = frozenset(profile.get("trigger_dimensions", []))
        classifications = frozenset(assignment["change_classifications"])
        effects.append({
            "component_id": component_id,
            "dimensions": sorted(dimensions),
            "classifications": sorted(classifications),
            "evidence": assignment["evidence"],
        })
        queue.append((component_id, dimensions, classifications))

    affected = set(seeds)
    traversed: dict[str, dict[str, Any]] = {}
    excluded: dict[str, dict[str, Any]] = {}
    states_seen: set[tuple[str, frozenset[str], frozenset[str]]] = set()
    while queue:
        source, dimensions, classifications = queue.popleft()
        state = (source, dimensions, classifications)
        if state in states_seen:
            continue
        states_seen.add(state)
        for relation in topology["relations"]:
            if relation["source"] != source:
                continue
            if relation["relation_domain"] == "substantive_causal_candidate" or relation["propagation_mode"] == "informational_only":
                continue
            if not relation_is_triggered(relation, set(dimensions), set(classifications)):
                rejected = excluded.setdefault(relation["relation_id"], {
                    "relation_id": relation["relation_id"],
                    "source": source,
                    "target": relation["target"],
                    "missing_dimensions": [],
                    "missing_classifications": [],
                })
                rejected["missing_dimensions"] = sorted(set(rejected["missing_dimensions"]) | (set(relation["trigger_dimensions"]) - set(dimensions)))
                rejected["missing_classifications"] = sorted(set(rejected["missing_classifications"]) | (set(relation["trigger_classifications"]) - set(classifications)))
                continue

            next_dimensions = dimensions if not relation["trigger_dimensions"] else dimensions & frozenset(relation["trigger_dimensions"])
            next_classifications = classifications if not relation["trigger_classifications"] else classifications & frozenset(relation["trigger_classifications"])
            edge = traversed.setdefault(relation["relation_id"], {
                "relation_id": relation["relation_id"],
                "source": relation["source"],
                "target": relation["target"],
                "relation_class": relation["relation_class"],
                "relation_domain": relation["relation_domain"],
                "propagation_mode": relation["propagation_mode"],
                "creates_sync_obligation": relation["creates_sync_obligation"],
                "claim_ceiling": relation["claim_ceiling"],
                "activations": [],
            })
            activation = {
                "input_dimensions": sorted(dimensions),
                "input_classifications": sorted(classifications),
                "matched_dimensions": sorted(set(dimensions) & set(relation["trigger_dimensions"])) if relation["trigger_dimensions"] else [],
                "matched_classifications": sorted(set(classifications) & set(relation["trigger_classifications"])) if relation["trigger_classifications"] else [],
            }
            if activation not in edge["activations"]:
                edge["activations"].append(activation)
            affected.add(relation["target"])
            queue.append((relation["target"], next_dimensions, next_classifications))

    adjacency: dict[str, list[str]] = defaultdict(list)
    for relation in traversed.values():
        adjacency[relation["source"]].append(relation["target"])
    cycle_residue: list[dict[str, str]] = []
    visited: set[str] = set()
    active: list[str] = []

    def visit(node: str) -> None:
        if node in active:
            cycle_residue.append({"type": "propagation_cycle", "path": " -> ".join(active[active.index(node):] + [node])})
            return
        if node in visited:
            return
        active.append(node)
        for target in sorted(adjacency.get(node, [])):
            visit(target)
        active.pop()
        visited.add(node)

    for seed in sorted(seeds):
        visit(seed)
    excluded = {key: value for key, value in excluded.items() if key not in traversed}
    return (
        affected,
        [traversed[key] for key in sorted(traversed)],
        [excluded[key] for key in sorted(excluded)],
        cycle_residue,
        effects,
    )


def _path_for_module(repo_root: Path, module_name: str) -> Path:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)+", module_name):
        raise RoutingBlocked(f"unsafe or non-canonical Python test module: {module_name!r}")
    return repo_root.joinpath(*module_name.split(".")).with_suffix(".py")


def _path_without_symlink_components(repo_root: Path, candidate: Path, label: str) -> Path:
    """Return a checkout path only when every component is a real directory/file."""
    lexical_root = Path(os.path.abspath(repo_root))
    root = repo_root.resolve()
    raw = candidate if candidate.is_absolute() else repo_root / candidate
    lexical_candidate = Path(os.path.abspath(raw))
    if lexical_candidate.is_relative_to(root):
        lexical_root = root
    else:
        lexical_root = Path(os.path.abspath(repo_root))
    try:
        relative = lexical_candidate.relative_to(lexical_root)
    except ValueError as exc:
        raise RoutingBlocked(f"{label} escapes the selected checkout: {candidate}") from exc
    if any(part in {"", ".", ".."} for part in relative.parts):
        raise RoutingBlocked(f"{label} has a non-canonical checkout path: {candidate}")
    current = root
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise RoutingBlocked(f"{label} traverses a symlink in the selected checkout: {current.relative_to(root)}")
    return current


def validate_checkout_file(
    repo_root: Path, candidate: Path, *, label: str, validation_sha: str | None = None,
) -> Path:
    """Require a regular checkout file and, when supplied, exact Git-blob bytes."""
    path = _path_without_symlink_components(repo_root, candidate, label)
    if not path.is_file():
        raise RoutingBlocked(f"{label} is missing or is not a regular file: {candidate}")
    if validation_sha is None:
        return path

    relative = path.relative_to(repo_root.resolve()).as_posix()
    try:
        entries = _git(repo_root, "ls-tree", "-z", validation_sha, "--", relative).split(b"\0")
    except RoutingBlocked as exc:
        raise RoutingBlocked(f"cannot bind {label} to the exact Git tree: {exc}") from exc
    records = [entry for entry in entries if entry]
    if len(records) != 1:
        raise RoutingBlocked(f"{label} is not one regular file in validation commit {validation_sha}: {relative}")
    metadata, raw_path = records[0].split(b"\t", 1)
    mode, object_type, object_sha = metadata.decode("ascii").split(" ")
    if raw_path.decode("utf-8", errors="strict") != relative or mode not in {"100644", "100755"} or object_type != "blob":
        raise RoutingBlocked(f"{label} is not a regular Git blob at validation commit {validation_sha}: {relative}")
    expected = _git(repo_root, "cat-file", "blob", object_sha)
    if path.read_bytes() != expected:
        raise RoutingBlocked(f"{label} worktree bytes do not match validation commit {validation_sha}: {relative}")
    return path


def _module_file(
    repo_root: Path, module_name: str, import_roots: list[str] | None = None,
    *, validation_sha: str | None = None,
) -> Path:
    """Resolve a declared module to one unique, non-symlink checkout file."""
    roots = [repo_root]
    for relative in import_roots or []:
        root_path = Path(relative)
        if root_path.is_absolute() or any(part in {"", ".", ".."} for part in root_path.parts):
            raise RoutingBlocked(f"test import root is not a canonical checkout path: {relative!r}")
        roots.append(repo_root / root_path)
    candidates: list[Path] = []
    seen: set[str] = set()
    for root in roots:
        path = _path_for_module(root, module_name)
        checked = _path_without_symlink_components(repo_root, path, f"selected test module {module_name}")
        key = str(checked)
        if key in seen:
            continue
        seen.add(key)
        if checked.is_file():
            candidates.append(validate_checkout_file(
                repo_root, path, label=f"selected test module {module_name}", validation_sha=validation_sha
            ))
    if not candidates:
        raise RoutingBlocked(f"selected test module is missing from candidate checkout: {module_name}")
    if len(candidates) != 1:
        raise RoutingBlocked(
            f"selected test module resolves to multiple checkout files: {module_name}: "
            f"{[str(path.relative_to(repo_root.resolve())) for path in candidates]}"
        )
    return candidates[0]


def _git_toplevel(repo_root: Path) -> Path:
    raw = _git(repo_root, "rev-parse", "--show-toplevel").decode("utf-8", errors="strict").strip()
    return Path(raw).resolve()


def _normalize_project_path(raw: str) -> str:
    path = normalize_repo_path(raw)
    if path.startswith("ignition/"):
        return path[len("ignition/"):]
    return path


def _path_component_evidence(
    paths: list[str], components: dict[str, dict[str, Any]], full_paths: set[str],
    allowed_overlaps: list[dict[str, Any]], validation_test_targets: dict[str, list[str]],
) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for path in paths:
        if path in full_paths:
            evidence.append({
                "path": path,
                "components": ["component_validation_router"],
                "basis": "reviewed_shared_validation_authority_path",
            })
            continue
        if path in validation_test_targets:
            evidence.append({
                "path": path,
                "components": [],
                "validation_targets": validation_test_targets[path],
                "basis": "registered_validation_target_module",
            })
            continue
        matches = [
            {"component_id": component_id, "patterns": sorted(
                pattern for pattern in component["path_patterns"] if matches_pattern(path, pattern)
            )}
            for component_id, component in sorted(components.items())
            if any(matches_pattern(path, pattern) for pattern in component["path_patterns"])
        ]
        item: dict[str, Any] = {
            "path": path,
            "components": matches,
            "basis": "registered_component_path_patterns",
        }
        if len(matches) > 1:
            hit_ids = {entry["component_id"] for entry in matches}
            covering = [
                overlap for overlap in allowed_overlaps
                if hit_ids.issubset(set(overlap["component_ids"]))
                and (
                    not overlap.get("path_patterns")
                    or any(matches_pattern(path, pattern) for pattern in overlap["path_patterns"])
                )
            ]
            if not covering:
                raise RoutingBlocked(f"path evidence lacks a declared overlap authority: {path}")
            overlap = min(covering, key=lambda value: (len(value["component_ids"]), value["authority_source"], value["reason"]))
            item["authorized_overlap"] = {
                "component_ids": sorted(overlap["component_ids"]),
                "authority_source": overlap["authority_source"],
                "matched_patterns": sorted(
                    pattern for pattern in overlap.get("path_patterns", []) if matches_pattern(path, pattern)
                ),
                "reason": overlap["reason"],
            }
        evidence.append(item)
    return evidence


def plan_paths(
    changed_paths: list[str], *, registry: dict[str, Any] | None = None,
    topology: dict[str, Any] | None = None, validation_map: dict[str, Any] | None = None,
    schema: dict[str, Any] | None = None, profiles: dict[str, Any] | None = None, repo_root: Path = CHECKOUT_ROOT,
    verify_target_files: bool = True, source: dict[str, Any] | None = None,
) -> dict[str, Any]:
    registry = registry or load_json(REGISTRY_PATH)
    topology = topology or load_json(TOPOLOGY_PATH)
    validation_map = validation_map or load_json(MAP_PATH)
    schema = schema or load_json(MAP_SCHEMA_PATH)
    profiles = profiles or load_json(PROFILES_PATH)
    validate_validation_map(registry, topology, validation_map, schema)
    components = _component_docs(registry)
    assignments = {item["component_id"]: item for item in validation_map["components"]}
    targets = {item["target_id"]: item for item in validation_map["targets"]}

    normalized: list[str] = []
    path_errors: list[dict[str, str]] = []
    for raw in changed_paths:
        try:
            normalized.append(_normalize_project_path(raw))
        except ValueError as exc:
            path_errors.append({"path": str(raw), "reason": str(exc)})
    normalized = sorted(set(normalized))
    if not normalized:
        path_errors.append({"path": "", "reason": "empty Git diff cannot establish a validation sample"})

    full_paths = sorted(set(normalized) & FULL_REGRESSION_PATHS)
    validation_test_targets: dict[str, list[str]] = defaultdict(list)
    for target in validation_map["targets"]:
        for module in target["modules"]:
            validation_test_targets[module.replace(".", "/") + ".py"].append(target["target_id"])
    validation_test_targets = {
        path: sorted(set(target_ids)) for path, target_ids in validation_test_targets.items()
    }
    validation_test_paths = set(validation_test_targets)
    changed_validation_tests = sorted(set(normalized) & validation_test_paths)
    changed_validation_test_target_ids = sorted({
        target_id for path in changed_validation_tests for target_id in validation_test_targets[path]
    })
    ordinary_paths = [
        path for path in normalized
        if path not in FULL_REGRESSION_PATHS and path not in validation_test_paths
    ]
    seeds, residue = resolve_paths(
        ordinary_paths, components, registry.get("allowed_path_overlaps", [])
    )
    if full_paths:
        # These exact files are reviewed shared validation authority. Seed the
        # router component directly; they require full cross-domain validation
        # even if the path registry intentionally does not assign one owner.
        seeds.add("component_validation_router")
    # Unknown residue is investigated even if another changed file independently
    # requires the full suite; a broad run does not turn an unclassified change
    # into an authorized component change.
    if path_errors or residue:
        raise RoutingBlocked(json.dumps({
            "path_errors": path_errors,
            "unresolved_path_residue": residue,
        }, ensure_ascii=False, sort_keys=True))

    if not seeds and not changed_validation_test_target_ids:
        raise RoutingBlocked("changed paths resolved to no component seeds")

    if seeds:
        affected, traversed, excluded_relations, cycle_residue, effect_inputs = _effect_closure(
            seeds, topology, assignments, profiles
        )
    else:
        affected, traversed, excluded_relations, cycle_residue, effect_inputs = set(), [], [], [], []
    if cycle_residue:
        raise RoutingBlocked(f"impact closure contains a cycle requiring adjudication: {cycle_residue}")

    unknown_components = sorted(component_id for component_id in affected if component_id not in assignments)
    if unknown_components:
        raise RoutingBlocked(f"affected components lack reviewed R/O/G ownership or targets: {unknown_components}")

    all_domains = sorted(
        {domain for component_id in affected for domain in assignments[component_id]["domains"]}
        | {targets[target_id]["domain"] for target_id in changed_validation_test_target_ids}
    )
    requires_full = bool(full_paths or changed_validation_tests) or any(
        assignments[component_id].get("requires_full_regression", False) for component_id in affected
    )
    if requires_full:
        mode = "FULL"
        selected_targets = sorted({
            target_id
            for component_id in affected
            for target_id in assignments[component_id]["validation_targets"]
        } | set(changed_validation_test_target_ids))
        full_reasons = []
        if full_paths:
            full_reasons.append({
                "kind": "validation_authority_changed",
                "paths": full_paths,
                "claim": "the impact router, its authority inputs, schemas, or the workflow changed; cross-domain validation is required",
            })
        if changed_validation_tests:
            full_reasons.append({
                "kind": "validation_target_changed",
                "paths": changed_validation_tests,
                "claim": "a test module selected as consumer evidence changed in this candidate; run full Foundation regression as well as the selected target",
            })
        for component_id in sorted(affected):
            if assignments[component_id].get("requires_full_regression", False):
                full_reasons.append({"kind": "component_requires_full_regression", "component_id": component_id})
    else:
        mode = "TARGETED"
        full_reasons = []
        selected_targets = sorted({
            target_id
            for component_id in affected
            for target_id in assignments[component_id]["validation_targets"]
        } | set(changed_validation_test_target_ids))
        if not selected_targets:
            raise RoutingBlocked(f"affected closure has no executable validation targets: {sorted(affected)}")
    if verify_target_files:
        for target_id in selected_targets:
            target = targets[target_id]
            for module in target["modules"]:
                try:
                    validation_sha = source.get("validation_sha") if isinstance(source, dict) else None
                    _module_file(
                        repo_root, module, target.get("import_roots", []), validation_sha=validation_sha,
                    )
                except RoutingBlocked as exc:
                    raise RoutingBlocked(f"selected target {target_id} has missing module files or an unsafe module path: {exc}") from exc

    plan: dict[str, Any] = {
        "schema_version": "1.0.0",
        "mode": mode,
        "source": source or {},
        "validation_map_sha256": digest_json(validation_map),
        "changed_paths": normalized,
        "path_component_evidence": _path_component_evidence(
            normalized, components, set(full_paths), registry.get("allowed_path_overlaps", []),
            validation_test_targets,
        ),
        "seed_components": sorted(seeds),
        "affected_component_closure": sorted(affected),
        "traversed_relations": [item["relation_id"] for item in traversed],
        "traversed_relation_effects": traversed,
        "excluded_relations_by_effect": excluded_relations,
        "seed_effect_inputs": effect_inputs,
        "domains": all_domains,
        "cross_domain_impact": {
            "domains": all_domains,
            "direct_seed_domains": sorted({
                domain for component_id in seeds for domain in assignments[component_id]["domains"]
            }),
            "validation_test_domains": sorted({
                targets[target_id]["domain"] for target_id in changed_validation_test_target_ids
            }),
            "traversed_cross_domain_relations": [
                {
                    "relation_id": relation["relation_id"],
                    "source": relation["source"],
                    "target": relation["target"],
                    "source_domains": assignments[relation["source"]]["domains"],
                    "target_domains": assignments[relation["target"]]["domains"],
                }
                for relation in traversed
                if set(assignments[relation["source"]]["domains"])
                != set(assignments[relation["target"]]["domains"])
            ],
        },
        "selected_target_ids": selected_targets,
        "changed_validation_test_targets": changed_validation_test_target_ids,
        "full_regression_reasons": full_reasons,
        "excluded_substantive_causal_candidates": sorted(
            relation["relation_id"] for relation in topology["relations"]
            if relation["relation_domain"] == "substantive_causal_candidate"
            and relation["source"] in affected
        ),
        "claim_ceiling": validation_map["claim_ceiling"],
    }
    plan["plan_sha256"] = digest_json(plan)
    return plan


def _git(repo_root: Path, *args: str) -> bytes:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        check=False,
    )
    if completed.returncode:
        error = completed.stderr.decode("utf-8", errors="replace").strip()
        raise RoutingBlocked(f"git {' '.join(args[:2])} failed: {error}")
    return completed.stdout


def _validate_commit(repo_root: Path, value: str, label: str) -> str:
    if not SHA_RE.fullmatch(value):
        raise RoutingBlocked(f"{label} must be an exact lowercase 40-character commit SHA")
    resolved = _git(repo_root, "rev-parse", "--verify", f"{value}^{{commit}}").decode().strip()
    if resolved != value:
        raise RoutingBlocked(f"{label} does not resolve to the supplied exact commit SHA")
    return resolved


def changed_paths_for_diff(repo_root: Path, base_sha: str, head_sha: str) -> tuple[list[str], list[dict[str, str]]]:
    base_sha = _validate_commit(repo_root, base_sha, "base_sha")
    head_sha = _validate_commit(repo_root, head_sha, "head_sha")
    _git(repo_root, "merge-base", base_sha, head_sha)
    raw = _git(repo_root, "diff", "--name-status", "-z", "--no-renames", f"{base_sha}...{head_sha}", "--")
    fields = raw.split(b"\0")
    if fields and fields[-1] == b"":
        fields.pop()
    paths: list[str] = []
    statuses: list[dict[str, str]] = []
    cursor = 0
    while cursor < len(fields):
        status = fields[cursor].decode("ascii", errors="strict")
        cursor += 1
        if status.startswith(("R", "C")):
            raise RoutingBlocked("rename/copy status is unexpected with --no-renames")
        if cursor >= len(fields):
            raise RoutingBlocked("malformed NUL-delimited Git diff status output")
        path = fields[cursor].decode("utf-8", errors="strict")
        cursor += 1
        if status not in {"A", "M", "D", "T"}:
            raise RoutingBlocked(f"unsupported Git change status {status!r} for {path!r}")
        paths.append(path)
        statuses.append({"status": status, "path": path})
    return paths, statuses


def _validate_checkout_binding(
    repo_root: Path, base_sha: str, head_sha: str, validation_sha: str,
) -> tuple[str, str, str]:
    base_sha = _validate_commit(repo_root, base_sha, "base_sha")
    head_sha = _validate_commit(repo_root, head_sha, "head_sha")
    validation_sha = _validate_commit(repo_root, validation_sha, "validation_sha")
    checkout_root = _git_toplevel(repo_root)
    if repo_root.resolve() != checkout_root:
        raise RoutingBlocked(f"repo-root must be the Git checkout root, got {repo_root.resolve()} (root: {checkout_root})")
    current_head = _git(repo_root, "rev-parse", "HEAD").decode().strip()
    if current_head != validation_sha:
        raise RoutingBlocked(f"checkout HEAD {current_head} does not equal requested validation commit {validation_sha}")
    dirty = _git(repo_root, "status", "--porcelain", "--untracked-files=all").decode().strip()
    if dirty:
        raise RoutingBlocked(f"validation checkout contains tracked or untracked changes: {dirty}")
    try:
        symlink_escapes = detect_tracked_symlink_escapes(repo_root, revision=validation_sha)
    except ValueError as exc:
        raise RoutingBlocked(f"tracked symlink scan failed for exact validation commit: {exc}") from exc
    if symlink_escapes:
        raise RoutingBlocked(
            f"exact validation commit contains tracked symlinks that escape the checkout: {sorted(symlink_escapes)}"
        )
    if validation_sha != head_sha:
        parents = _git(repo_root, "rev-list", "--parents", "-n", "1", validation_sha).decode().strip().split()
        if parents != [validation_sha, base_sha, head_sha]:
            raise RoutingBlocked(
                "validation commit must be the GitHub pull-request merge commit with the declared base and head parents"
            )
    return base_sha, head_sha, validation_sha


def build_exact_plan(
    repo_root: Path, base_sha: str, head_sha: str, validation_sha: str | None = None,
) -> dict[str, Any]:
    expected_root = _git_toplevel(ROOT)
    if repo_root.resolve() != expected_root:
        raise RoutingBlocked(
            f"router authority files are not from the selected Git checkout: {ROOT} belongs to {expected_root}, "
            f"not {repo_root.resolve()}"
        )
    validation_sha = validation_sha or head_sha
    base_sha, head_sha, validation_sha = _validate_checkout_binding(
        repo_root, base_sha, head_sha, validation_sha
    )
    paths, statuses = changed_paths_for_diff(repo_root, base_sha, head_sha)
    return plan_paths(
        paths,
        repo_root=repo_root,
        source={
            "base_sha": base_sha,
            "head_sha": head_sha,
            "validation_sha": validation_sha,
            "changed_file_statuses": statuses,
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--validation-sha")
    parser.add_argument("--repo-root", type=Path, default=CHECKOUT_ROOT)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--github-output", type=Path)
    args = parser.parse_args()
    try:
        plan = build_exact_plan(args.repo_root.resolve(), args.base_sha, args.head_sha, args.validation_sha)
    except (RoutingBlocked, OSError, ValueError) as exc:
        failure = {"schema_version": "1.0.0", "mode": "BLOCKED", "reason": str(exc)}
        args.output.write_text(json.dumps(failure, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        if args.github_output:
            with args.github_output.open("a", encoding="utf-8") as stream:
                stream.write("mode=BLOCKED\n")
                stream.write("has_targets=false\n")
                stream.write("uses_lean=false\n")
        print(json.dumps(failure, ensure_ascii=False, sort_keys=True))
        return 2
    payload = json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.output.write_text(payload, encoding="utf-8")
    if args.github_output:
        target_docs = {target["target_id"]: target for target in load_json(MAP_PATH)["targets"]}
        uses_lean = any(
            LEAN_VALIDATION_COMMANDS.intersection(target_docs[target_id].get("command_ids", []))
            for target_id in plan["selected_target_ids"]
        )
        with args.github_output.open("a", encoding="utf-8") as stream:
            stream.write(f"mode={plan['mode']}\n")
            stream.write(f"has_targets={'true' if plan['selected_target_ids'] else 'false'}\n")
            stream.write(f"uses_lean={'true' if uses_lean else 'false'}\n")
    print(json.dumps({key: plan[key] for key in ("mode", "plan_sha256", "domains", "selected_target_ids", "full_regression_reasons")}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
