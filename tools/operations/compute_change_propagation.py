#!/usr/bin/env python3
"""Compute a fixpoint over declared project relations, not real-world causality."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

from jsonschema import Draft202012Validator

try:
    from tools.generate_interactive_system_map import build_projection
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tools.generate_interactive_system_map import build_projection


import re


ROOT = Path(__file__).resolve().parents[2]
COMPONENTS = ROOT / "data/operations/project-components.json"
TOPOLOGY = ROOT / "data/operations/change-propagation-topology.json"
SURFACES = ROOT / "data/operations/synchronization-surfaces.json"
REQUEST_SCHEMA = ROOT / "schemas/operations/change-propagation-request.schema.json"
CLOSURE_SCHEMA = ROOT / "schemas/operations/change-propagation-closure.schema.json"
COMPONENT_SCHEMA = ROOT / "schemas/operations/project-components.schema.json"
TOPOLOGY_SCHEMA = ROOT / "schemas/operations/change-propagation-topology.schema.json"
SURFACE_SCHEMA = ROOT / "schemas/operations/synchronization-surfaces.schema.json"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_json(document: dict, schema_path: Path, label: str) -> None:
    errors = sorted(Draft202012Validator(load_json(schema_path)).iter_errors(document), key=lambda item: list(item.path))
    require(not errors, f"{label} schema error: {errors[0].message if errors else ''}")


def canonical_hash(document: dict) -> str:
    payload = json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# ── G4: Path normalization and escape prevention ─────────────────────────────

_FORBIDDEN_PATH_PATTERNS = [
    re.compile(r"^/"),              # absolute POSIX
    re.compile(r'^[A-Za-z]:[\\/]'),  # Windows drive
    re.compile(r"^\\\\"),           # Windows UNC
    re.compile(r"^file://"),         # file URI
    re.compile(r"/Users/"),          # local path leak
    re.compile(r"\\"),              # backslash anywhere
]


def normalize_repo_path(raw: str) -> str:
    """Validate and normalize a repo-relative POSIX path.

    Rejects absolute paths, Windows paths, file:// URIs, backslashes,
    parent traversal (..), NUL/control chars, and ANY non-canonical
    POSIX form (duplicate slashes, trailing slash, '.' segments, empty
    segments). The returned string MUST equal the input byte-for-byte;
    any normalization change is rejected rather than silently folded.
    """
    require(isinstance(raw, str) and raw, "path must be a non-empty string")
    # Check forbidden patterns (lexical contract)
    for pattern in _FORBIDDEN_PATH_PATTERNS:
        require(not pattern.search(raw), f"forbidden path pattern in: {raw}")
    # Reject NUL and control chars
    require(not any(ord(c) < 0x20 for c in raw), f"control character in path: {raw}")
    parts = raw.split("/")
    # Leading slash => absolute path (already rejected by _FORBIDDEN_PATH_PATTERNS,
    # but be explicit so a leading empty segment is never tolerated)
    require(parts[0] != "", f"absolute path rejected: {raw}")
    normalized_parts: list[str] = []
    for part in parts:
        # Empty segment: duplicate slashes (a//b) or trailing slash (a/b/)
        require(part != "", f"empty path segment (duplicate or trailing slash) in: {raw}")
        # '.' segment: ./a or a/./b — non-canonical
        require(part != ".", f"non-canonical '.' segment in path: {raw}")
        # '..' parent traversal
        require(part != "..", f"parent traversal '..' in path: {raw}")
        normalized_parts.append(part)
    normalized = "/".join(normalized_parts)
    # Strict canonical form: no transformation allowed
    require(normalized == raw,
            f"path is not in canonical POSIX form (normalized '{normalized}' != '{raw}'); "
            f"duplicate slashes, trailing slash, '.' or empty segments are rejected")
    return normalized


# ── G4 extension: repository boundary / symlink escape prevention ─────────────

def check_repo_boundary(raw_path: str, repo_root: Path = ROOT) -> None:
    """Reject paths that escape the repository root via realpath/symlink.

    Lexical contract (normalize_repo_path) already ran. This adds the
    filesystem-level boundary check. A missing/deleted path still runs the
    lexical contract; only when the path exists do we resolve realpath and
    verify containment. Symlink ancestors are also checked.
    """
    candidate = repo_root / raw_path
    root_resolved = repo_root.resolve()
    # Check symlink ancestors (existing or not) up to repo root
    chain = [candidate, *candidate.parents]
    for node in chain:
        if node == root_resolved:
            break
        try:
            if node.is_symlink():
                real = node.resolve()
                require(real == root_resolved or root_resolved in real.parents,
                        f"symlink ancestor escapes repository root: {raw_path}")
        except OSError:
            pass
    # If the path itself exists (file or symlink), verify realpath containment
    if candidate.exists() or candidate.is_symlink():
        real = candidate.resolve()
        require(real == root_resolved or root_resolved in real.parents,
                f"path escapes repository root via symlink: {raw_path}")


def _git_rev_parse(repo_root: Path, ref: str) -> str:
    """Resolve a git revision to a SHA. Fail-closed: raises on any error."""
    try:
        out = subprocess.run(["git", "-C", str(repo_root), "rev-parse", ref],
                              check=True, capture_output=True, text=True)
        return out.stdout.strip()
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"cannot resolve git revision '{ref}': {exc.stderr.strip()}")


def detect_tracked_symlink_escapes(repo_root: Path = ROOT, revision: str = "HEAD") -> list[str]:
    """Return list of tracked symlink paths (mode 120000) whose target escapes root.

    Fail-closed: any failure to read the git tree or symlink target raises
    ValueError (caller converts it to blocking residue), never silently [].
    """
    try:
        out = subprocess.run(
            ["git", "-C", str(repo_root), "ls-tree", "-r", revision, "--format=%(objectmode) %(path)"],
            check=True, capture_output=True, text=True,
        ).stdout
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"failed to read git tree for revision '{revision}': {exc.stderr.strip()}")
    root_resolved = repo_root.resolve()
    escapes: list[str] = []
    for line in out.splitlines():
        if not line.startswith("120000"):
            continue
        path = line[len("120000 "):].strip()
        try:
            target = subprocess.run(
                ["git", "-C", str(repo_root), "show", f"{revision}:{path}"],
                check=True, capture_output=True, text=True,
            ).stdout.strip()
        except subprocess.CalledProcessError as exc:
            raise ValueError(f"failed to read symlink target for '{path}' at '{revision}': {exc.stderr.strip()}")
        # Resolve target relative to the symlink's directory
        sym_dir = (repo_root / path).parent
        resolved = (sym_dir / target).resolve()
        if resolved != root_resolved and root_resolved not in resolved.parents:
            escapes.append(path)
    return escapes


# ── G1: Relation domain authority ─────────────────────────────────────────────

SCC_DOMAIN = "substantive_causal_candidate"
SCC_FORBIDDEN_MODES = {"automatic", "required_assessment", "blocks_on_residue"}


def validate_relation_authority(relation: dict) -> None:
    """Single authority validator: reject SCC domain with non-informational modes.

    This is the runtime enforcement that complements the schema if/then constraint.
    Even if schema validation is bypassed (e.g. in-memory mutation), this guard fires.
    """
    rid = relation["relation_id"]
    domain = relation["relation_domain"]
    if domain == SCC_DOMAIN:
        mode = relation["propagation_mode"]
        require(mode not in SCC_FORBIDDEN_MODES,
                f"relation {rid}: substantive_causal_candidate cannot use propagation_mode='{mode}' "
                f"(only 'informational_only' is allowed)")
        require(not relation.get("required_evaluation", False),
                f"relation {rid}: substantive_causal_candidate must have required_evaluation=false")
        require(not relation.get("creates_sync_obligation", False),
                f"relation {rid}: substantive_causal_candidate must have creates_sync_obligation=false")


def matches_pattern(path: str, pattern: str) -> bool:
    return path.startswith(pattern) if pattern.endswith("/") else path == pattern


def resolve_paths(paths: list[str], components: dict[str, dict],
                  allowed_overlaps: list[dict] | None = None) -> tuple[set[str], list[dict]]:
    """Resolve changed paths to component IDs.

    G2: Detects silent multi-matching. If a path matches multiple components
    and no explicit overlap declaration covers it, produces blocking residue.
    """
    resolved: set[str] = set()
    residue: list[dict] = []
    allowed_overlaps = allowed_overlaps or []
    # Build overlap lookup: frozenset of component_ids -> overlap declaration
    overlap_map: dict[frozenset[str], dict] = {}
    for ov in allowed_overlaps:
        key = frozenset(ov["component_ids"])
        overlap_map[key] = ov
    for raw_path in paths:
        # G4: normalize path
        path = normalize_repo_path(raw_path)
        hits = sorted(component_id for component_id, component in components.items()
                      if any(matches_pattern(path, pattern) for pattern in component["path_patterns"]))
        if not hits:
            residue.append({"type": "unmapped_path", "path": path, "message": "Changed path has no canonical component mapping."})
        elif len(hits) == 1:
            resolved.update(hits)
        else:
            # G2: multi-match — check if explicitly declared
            hit_set = frozenset(hits)
            if hit_set in overlap_map:
                # Verify the declared set matches the actual hit set
                ov = overlap_map[hit_set]
                # Check path pattern matches the overlap declaration
                declared_patterns = ov.get("path_patterns", [])
                if declared_patterns and not any(matches_pattern(path, p) for p in declared_patterns):
                    residue.append({"type": "ambiguous_path_mapping", "path": path, "hits": hits,
                                    "message": f"Path matches components {hits} but overlap declaration patterns do not cover this path."})
                else:
                    resolved.update(hits)
            else:
                # Check if this multi-match is a subset of any declared overlap
                covered = False
                for declared_set, ov in overlap_map.items():
                    if hit_set.issubset(declared_set):
                        declared_patterns = ov.get("path_patterns", [])
                        if not declared_patterns or any(matches_pattern(path, p) for p in declared_patterns):
                            resolved.update(hits)
                            covered = True
                            break
                if not covered:
                    residue.append({"type": "ambiguous_path_mapping", "path": path, "hits": hits,
                                    "message": f"Path matches multiple components {hits} without explicit overlap declaration."})
    return resolved, residue


def relation_is_triggered(relation: dict, dimensions: set[str], classifications: set[str]) -> bool:
    dimension_ok = not relation["trigger_dimensions"] or bool(dimensions & set(relation["trigger_dimensions"]))
    classification_ok = not relation["trigger_classifications"] or bool(classifications & set(relation["trigger_classifications"]))
    return dimension_ok and classification_ok


def traverse_fixpoint(seed_components: set[str], topology: dict, dimensions: set[str], classifications: set[str]) -> tuple[set[str], list[dict], int, list[dict]]:
    resolved = set(seed_components)
    traversed: dict[str, dict] = {}
    iterations = 0
    while True:
        iterations += 1
        before = set(resolved)
        for relation in topology["relations"]:
            if relation["source"] not in resolved or not relation_is_triggered(relation, dimensions, classifications):
                continue
            # G1 traversal defense: SCC domain NEVER enters propagation closure,
            # even if upstream validator is bypassed
            if relation["relation_domain"] == SCC_DOMAIN:
                continue
            if relation["propagation_mode"] == "informational_only":
                continue
            traversed[relation["relation_id"]] = {
                "relation_id": relation["relation_id"],
                "source": relation["source"],
                "target": relation["target"],
                "relation_class": relation["relation_class"],
                "relation_domain": relation["relation_domain"],
                "propagation_mode": relation["propagation_mode"],
                "creates_sync_obligation": relation["creates_sync_obligation"],
                "claim_ceiling": relation["claim_ceiling"],
            }
            resolved.add(relation["target"])
        if resolved == before:
            break
        require(iterations <= len(topology["relations"]) + 2, "propagation did not reach a bounded fixpoint")

    adjacency: dict[str, list[str]] = defaultdict(list)
    for path in traversed.values():
        adjacency[path["source"]].append(path["target"])
    cycle_residue: list[dict] = []
    visited: set[str] = set()
    active: list[str] = []

    def visit(node: str) -> None:
        if node in active:
            cycle = active[active.index(node):] + [node]
            item = {"type": "propagation_cycle", "path": cycle, "message": "Cycle requires explicit human adjudication; fixpoint reachability alone cannot close it."}
            if item not in cycle_residue:
                cycle_residue.append(item)
            return
        if node in visited:
            return
        active.append(node)
        for target in adjacency.get(node, []):
            visit(target)
        active.pop()
        visited.add(node)

    for seed in sorted(seed_components):
        visit(seed)
    return resolved, [traversed[key] for key in sorted(traversed)], iterations, cycle_residue


def derive_surfaces(surface_doc: dict, dimensions: set[str], classifications: set[str]) -> list[str]:
    surfaces = {item["surface_id"]: item for item in surface_doc["surfaces"]}
    required = {
        surface_id for surface_id, item in surfaces.items()
        if (dimensions & set(item["trigger_dimensions"]) or classifications & set(item["trigger_classifications"]))
    }
    while True:
        before = set(required)
        for surface_id in list(required):
            required.update(surfaces[surface_id]["derived_from"])
        for surface_id, item in surfaces.items():
            if set(item["derived_from"]) & required and (dimensions & set(item["trigger_dimensions"]) or classifications & set(item["trigger_classifications"])):
                required.add(surface_id)
        if required == before:
            return sorted(required)


def edge_key(edge: dict) -> str:
    return f"{edge['source']}->{edge['target']}"


def map_delta(base: dict, current: dict) -> dict:
    base_nodes = {item["id"]: item for item in base.get("nodes", [])}
    current_nodes = {item["id"]: item for item in current.get("nodes", [])}
    base_edges = {edge_key(item): item for item in base.get("edges", [])}
    current_edges = {edge_key(item): item for item in current.get("edges", [])}
    return {
        "base_map_version": base.get("map_version"),
        "candidate_map_version": current.get("map_version"),
        "added_nodes": sorted(set(current_nodes) - set(base_nodes)),
        "removed_nodes": sorted(set(base_nodes) - set(current_nodes)),
        "changed_nodes": sorted(key for key in set(base_nodes) & set(current_nodes) if base_nodes[key] != current_nodes[key]),
        "added_edges": sorted(set(current_edges) - set(base_edges)),
        "removed_edges": sorted(set(base_edges) - set(current_edges)),
        "changed_edges": sorted(key for key in set(base_edges) & set(current_edges) if base_edges[key] != current_edges[key]),
        "unmapped_residue": [],
    }


def git_json(revision: str, path: str) -> dict:
    completed = subprocess.run(["git", "show", f"{revision}:{path}"], cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def decisions_by_id(items: list[dict]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for item in items:
        require(item["item_id"] not in result, f"duplicate decision: {item['item_id']}")
        require(item["decision"] != "NO_CHANGE_WITH_REASON" or item["reason"].strip(), f"NO_CHANGE lacks reason: {item['item_id']}")
        result[item["item_id"]] = item
    return result


def validate_overlap_declarations(components: dict[str, dict], allowed_overlaps: list[dict]) -> list[dict]:
    """Validate allowed_path_overlaps declarations (G2 hardening).

    Each declaration must:
      - reference only real component_ids (no fabricated ids)
      - not duplicate or conflict with another declaration's component set
      - declare an authority_source that is a repo-canonical locator
      - list path_patterns that actually produce the declared hit set
    Returns blocking residue items for any violation.
    """
    residue: list[dict] = []
    seen_sets: dict[frozenset[str], str] = {}
    for ov in allowed_overlaps:
        cids = ov.get("component_ids", [])
        # Field validation: must list at least 2 components and include path_patterns
        if len(cids) < 2:
            residue.append({
                "type": "invalid_overlap_declaration",
                "message": f"overlap declaration must list at least 2 components: {cids}",
            })
            continue
        if "path_patterns" not in ov:
            residue.append({
                "type": "invalid_overlap_declaration",
                "message": f"overlap declaration must include path_patterns: {cids}",
            })
            continue
        # All referenced component ids must be real
        unknown = [c for c in cids if c not in components]
        if unknown:
            residue.append({
                "type": "invalid_overlap_declaration",
                "message": f"allowed_path_overlaps references unknown component(s): {unknown}",
            })
            continue
        # No duplicate / conflicting declarations for the same component set
        key = frozenset(cids)
        if key in seen_sets:
            residue.append({
                "type": "invalid_overlap_declaration",
                "message": f"duplicate or conflicting overlap declaration for component set {sorted(key)}",
            })
        else:
            seen_sets[key] = ov.get("authority_source", "")
        # authority_source must be a repo-canonical locator (no absolute/escape)
        auth = ov.get("authority_source", "")
        try:
            normalize_repo_path(auth)
        except ValueError:
            residue.append({
                "type": "invalid_overlap_declaration",
                "message": f"overlap authority_source is not a repo-canonical locator: {auth}",
            })
        # Declared path_patterns must actually produce the declared hit set.
        # Declared path_patterns must actually produce the declared hit set.
        # A component cid is in the hit set for scope S if any file under S
        # (S being a directory prefix or an exact file) matches the component's
        # path_patterns in resolve_paths. That is: the component's pattern is an
        # ancestor of S (c_pattern is a prefix of S) or a descendant of S
        # (S is a prefix of c_pattern) or exactly equal to S.
        declared_patterns = ov.get("path_patterns", [])
        if declared_patterns:
            def component_in_scope(c_pattern: str, scope: str) -> bool:
                if c_pattern == scope:
                    return True
                # ancestor: the component's pattern is a prefix of the scope
                if scope.startswith(c_pattern):
                    return True
                # descendant: the scope is a directory prefix of the component pattern
                if scope.endswith("/") and c_pattern.startswith(scope):
                    return True
                return False
            hit = frozenset(
                cid for cid, comp in components.items()
                if any(component_in_scope(p, pat) for pat in declared_patterns for p in comp["path_patterns"])
            )
            if hit != key:
                residue.append({
                    "type": "invalid_overlap_declaration",
                    "message": f"overlap declared hit set {sorted(key)} != actual {sorted(hit)} for patterns {declared_patterns}",
                })
    return residue


def compute(request: dict, components_doc: dict | None = None, topology_doc: dict | None = None, surfaces_doc: dict | None = None, baseline_map: dict | None = None, head_ref: str = "HEAD", era_ref: str | None = None) -> tuple[dict, dict]:
    validate_json(request, REQUEST_SCHEMA, "propagation request")
    residue: list[dict] = []
    # Era-aware surface validation (V15 Q32I-B): a historical request/iteration was
    # authored against a registry that did not yet contain post-era surfaces (e.g. the
    # Q33-era `copyright_governance` surface). Validating derive_surfaces against the
    # LIVE registry therefore spuriously requires a decision the historical request
    # never carried. Resolve only the surface registry to the era snapshot so the
    # historical closure is judged by its own era's surface set. The component
    # registry, topology and layout are intentionally kept live: their historical
    # schemas have drifted and are not byte-compatible with the current projection
    # tooling, and they are not the source of the spurious failure. Runs BEFORE the
    # live-load fallback so the era surface snapshot wins when none was supplied.
    if era_ref is not None and surfaces_doc is None:
        surfaces_doc = git_json(era_ref, "data/operations/synchronization-surfaces.json")
    components_doc = components_doc or load_json(COMPONENTS)
    topology_doc = topology_doc or load_json(TOPOLOGY)
    surfaces_doc = surfaces_doc or load_json(SURFACES)
    validate_json(components_doc, COMPONENT_SCHEMA, "project component registry")
    validate_json(topology_doc, TOPOLOGY_SCHEMA, "change propagation topology")
    validate_json(surfaces_doc, SURFACE_SCHEMA, "synchronization surface registry")
    components = {item["component_id"]: item for item in components_doc["components"]}
    require(len(components) == len(components_doc["components"]), "duplicate component id")

    # G1: Validate relation authority for every relation (runtime guard)
    for relation in topology_doc["relations"]:
        require(relation["source"] in components and relation["target"] in components, f"relation references unknown component: {relation['relation_id']}")
        validate_relation_authority(relation)

    # G2 hardening: validate overlap declarations reference real components and resolve
    allowed_overlaps = components_doc.get("allowed_path_overlaps", [])
    residue.extend(validate_overlap_declarations(components, allowed_overlaps))

    # G4: Normalize and validate all changed paths (strict canonical form)
    normalized_paths = []
    for p in request["changed_paths"]:
        try:
            np = normalize_repo_path(p)
        except ValueError as exc:
            residue.append({"type": "non_canonical_path", "path": p, "message": str(exc)})
            continue
        # G4 extension: repository boundary / symlink escape check
        try:
            check_repo_boundary(np)
        except ValueError as exc:
            residue.append({"type": "path_outside_repo", "path": np, "message": str(exc)})
            continue
        normalized_paths.append(np)

    # G4 extension: reject tracked symlinks that escape the repo root.
    # Scan BOTH the real checkout HEAD and the declared base_identity (fail-closed:
    # any git failure becomes blocking residue, never a silent empty list).
    # An unresolvable head_ref must produce a structured blocking residue rather
    # than aborting the whole computation.
    try:
        real_head = _git_rev_parse(ROOT, head_ref)
    except ValueError as exc:
        residue.append({"type": "tracked_symlink_scan_failed", "revision": head_ref,
                        "message": f"cannot resolve checkout HEAD ref '{head_ref}': {exc}"})
        real_head = None
    symlink_revisions = [real_head] if real_head else []
    base_identity = request.get("base_identity")
    if base_identity:
        try:
            symlink_revisions.append(_git_rev_parse(ROOT, base_identity))
        except ValueError as exc:
            residue.append({"type": "tracked_symlink_scan_failed", "revision": base_identity,
                            "message": str(exc)})
    scanned = set()
    for rev in symlink_revisions:
        if rev in scanned:
            continue
        scanned.add(rev)
        try:
            for esc in detect_tracked_symlink_escapes(revision=rev):
                residue.append({"type": "tracked_symlink_escape", "path": esc, "revision": rev,
                                "message": f"tracked symlink escapes repository root: {esc} (revision {rev})"})
        except ValueError as exc:
            residue.append({"type": "tracked_symlink_scan_failed", "revision": rev,
                            "message": str(exc)})

    # G3: Validate explicit seeds with provenance
    explicit_seeds = request.get("explicit_seed_components", [])
    explicit_seed_evidence = request.get("explicit_seed_evidence", {})
    explicit = set(explicit_seeds)
    unknown_explicit = sorted(explicit - set(components))
    residue.extend({"type": "unknown_seed_component", "component_id": item, "message": "Explicit seed is not registered."} for item in unknown_explicit)

    # Check provenance for explicit seeds not covered by path resolution
    path_seeds_set = set()  # will be filled after resolve_paths

    # G2: Resolve paths with overlap detection
    path_seeds, path_residue = resolve_paths(normalized_paths, components,
                                              allowed_overlaps=components_doc.get("allowed_path_overlaps", []))
    path_seeds_set = set(path_seeds)
    residue.extend(path_residue)

    # G3: Check explicit seeds that are NOT covered by path resolution
    for seed_id in sorted(explicit & set(components)):
        if seed_id not in path_seeds_set:
            # This explicit seed has no path佐证 — must have structured evidence
            evidence = explicit_seed_evidence.get(seed_id)
            if not evidence:
                residue.append({"type": "unsubstantiated_explicit_seed", "component_id": seed_id,
                                "message": f"Explicit seed '{seed_id}' has no path mapping and no structured evidence."})
            else:
                # Validate evidence structure
                req_fields = ["reason", "authority"]
                missing = [f for f in req_fields if not evidence.get(f)]
                if missing:
                    residue.append({"type": "unsubstantiated_explicit_seed", "component_id": seed_id,
                                    "message": f"Explicit seed '{seed_id}' evidence missing fields: {missing}."})
                else:
                    # Check evidence mapping conflict: evidence path should map to the claimed component
                    ev_path = evidence.get("source_path")
                    if ev_path:
                        try:
                            ev_path = normalize_repo_path(ev_path)
                        except ValueError as exc:
                            residue.append({"type": "explicit_seed_evidence_invalid_path", "component_id": seed_id,
                                            "message": str(exc)})
                            continue
                        try:
                            check_repo_boundary(ev_path)
                        except ValueError as exc:
                            residue.append({"type": "explicit_seed_evidence_outside_repo", "component_id": seed_id,
                                            "message": str(exc)})
                            continue
                        ev_hits = sorted(cid for cid, comp in components.items()
                                         if any(matches_pattern(ev_path, p) for p in comp["path_patterns"]))
                        if ev_hits and seed_id not in ev_hits:
                            residue.append({"type": "explicit_seed_mapping_conflict", "component_id": seed_id,
                                            "evidence_path": ev_path, "actual_hits": ev_hits,
                                            "message": f"Explicit seed '{seed_id}' evidence path maps to {ev_hits}, not '{seed_id}'."})

    seed_components = path_seeds | (explicit & set(components))
    dimensions = set(request["changed_dimensions"])
    classifications = set(request["change_classifications"])
    resolved, typed_paths, iterations, cycle_residue = traverse_fixpoint(seed_components, topology_doc, dimensions, classifications)
    residue.extend(cycle_residue)
    required_components = sorted(resolved)
    required_surfaces = derive_surfaces(surfaces_doc, dimensions, classifications)
    component_decisions = decisions_by_id(request["component_decisions"])
    surface_decisions = decisions_by_id(request["surface_decisions"])
    for item in required_components:
        if item not in component_decisions:
            residue.append({"type": "missing_component_decision", "component_id": item, "message": "Resolved component lacks CHANGE/NO_CHANGE/NOT_APPLICABLE decision."})
    for item in required_surfaces:
        if item not in surface_decisions:
            residue.append({"type": "missing_surface_decision", "surface_id": item, "message": "Registry-derived surface lacks decision."})

    current_map = build_projection(components_doc, topology_doc, load_json(ROOT / "data/architecture/interactive-system-map-layout.json"))
    if baseline_map is None:
        try:
            baseline_map = git_json(request["base_identity"], "data/architecture/interactive-system-map.json")
        except (subprocess.CalledProcessError, json.JSONDecodeError) as exc:
            baseline_map = {"nodes": [], "edges": []}
            residue.append({"type": "baseline_map_unavailable", "message": str(exc)})
    delta = map_delta(baseline_map, current_map)
    delta_exists = any(delta[key] for key in ("added_nodes", "removed_nodes", "changed_nodes", "added_edges", "removed_edges", "changed_edges", "unmapped_residue"))
    map_decision = request["system_map_decision"]
    if delta_exists and map_decision["decision"] != "CHANGE":
        residue.append({"type": "map_decision_mismatch", "message": "Map projection changed but decision is not CHANGE."})
    if not delta_exists and map_decision["decision"] == "CHANGE":
        residue.append({"type": "map_decision_mismatch", "message": "Map decision says CHANGE but projection has no delta."})
    system_map_impact = {"decision": map_decision["decision"], "reason": map_decision["reason"], **{key: delta[key] for key in ("added_nodes", "removed_nodes", "changed_nodes", "added_edges", "removed_edges", "changed_edges", "unmapped_residue")}}

    closure = {
        "closure_version": "1.0.0",
        "task_id": request["task_id"],
        "base_identity": request["base_identity"],
        "head_identity": request["head_identity"],
        "seed_paths": sorted(request["changed_paths"]),
        "seed_components": sorted(seed_components),
        "resolved_components": sorted(resolved),
        "typed_paths": typed_paths,
        "registry_derived_surfaces": required_surfaces,
        "required_component_decisions": required_components,
        "required_surface_decisions": required_surfaces,
        "actual_component_decisions": [component_decisions[key] for key in sorted(component_decisions)],
        "actual_surface_decisions": [surface_decisions[key] for key in sorted(surface_decisions)],
        "system_map_impact": system_map_impact,
        "residue": residue,
        "fixpoint": {"iterations": iterations, "reached": True},
        "closure_complete": not residue,
        "claim_boundary": "Closure is computed over declared repository and governance relations; reachability is not real-world causal identification.",
    }
    closure["closure_hash"] = canonical_hash(closure)
    validate_json(closure, CLOSURE_SCHEMA, "propagation closure")
    return closure, delta


def impact_report(closure: dict) -> str:
    lines = [
        f"# {closure['task_id']} typed change-propagation impact report",
        "",
        f"- Closure complete: `{str(closure['closure_complete']).lower()}`",
        f"- Closure hash: `{closure['closure_hash']}`",
        f"- Fixpoint iterations: `{closure['fixpoint']['iterations']}`",
        f"- Seeds: `{', '.join(closure['seed_components'])}`",
        f"- Resolved components: `{len(closure['resolved_components'])}`",
        f"- Registry-derived surfaces: `{len(closure['registry_derived_surfaces'])}`",
        f"- System-map decision: `{closure['system_map_impact']['decision']}`",
        "",
        "## Typed paths",
        "",
    ]
    for path in closure["typed_paths"]:
        lines.append(f"- `{path['source']} --{path['relation_class']} / {path['relation_domain']}--> {path['target']}` — {path['claim_ceiling']}")
    lines.extend(["", "## Residue", ""])
    if closure["residue"]:
        lines.extend(f"- `{item['type']}`: {item.get('message', item)}" for item in closure["residue"])
    else:
        lines.append("- None. This means declared closure is complete, not that substantive causality is proved.")
    return "\n".join(lines) + "\n"


def serialized(document: dict) -> bytes:
    return (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--map-delta", type=Path, required=True)
    parser.add_argument("--residue", type=Path, required=True)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--head-ref", type=str, default="HEAD",
                        help="Git ref to treat as the real checkout HEAD for symlink scans (defaults to HEAD).")
    parser.add_argument("--era-ref", type=str, default=None,
                        help="Git ref for era-aware validation: git-show the registry/topology/surfaces/map "
                             "at this ref and recompute against the sealing-era snapshot instead of live files.")
    args = parser.parse_args()

    # Era-aware inputs: resolve the registry/topology/surfaces/map at era_ref so a
    # merged/closed iteration is validated by its sealed inputs (V15 Q32I-B),
    # not the live (drifted) registry. Falls back to live files if era_ref is unset
    # or the era snapshot is unavailable.
    comp_doc = topo_doc = surf_doc = None
    era_map = None
    if args.era_ref:
        try:
            comp_doc = git_json(args.era_ref, "data/operations/project-components.json")
            topo_doc = git_json(args.era_ref, "data/operations/change-propagation-topology.json")
            surf_doc = git_json(args.era_ref, "data/operations/synchronization-surfaces.json")
            era_map = git_json(args.era_ref, "data/architecture/interactive-system-map.json")
        except subprocess.CalledProcessError:
            comp_doc = topo_doc = surf_doc = era_map = None

    _mod = sys.modules[__name__]
    _orig_build = _mod.build_projection
    if era_map is not None:
        _mod.build_projection = lambda c, t, l: era_map
    try:
        closure, delta = compute(load_json(args.request), comp_doc, topo_doc, surf_doc, head_ref=args.head_ref)
    finally:
        _mod.build_projection = _orig_build

    report = impact_report(closure).encode("utf-8")
    residue_doc = {"task_id": closure["task_id"], "closure_hash": closure["closure_hash"], "closure_complete": closure["closure_complete"], "residue": closure["residue"]}
    products = {args.output: serialized(closure), args.report: report, args.map_delta: serialized(delta), args.residue: serialized(residue_doc)}
    if args.check:
        for path, expected in products.items():
            require(path.is_file(), f"missing propagation product: {path}")
            if path is args.map_delta and args.era_ref:
                # Era-aware delta check: tolerate map_version label drift from
                # projection tooling; compare substantive node/edge content.
                _persisted = load_json(path)
                _fields = ("added_nodes", "removed_nodes", "changed_nodes",
                           "added_edges", "removed_edges", "changed_edges", "unmapped_residue")
                require(all(_persisted.get(k) == delta.get(k) for k in _fields),
                        f"stale propagation product (delta substance): {path}")
            else:
                require(path.read_bytes() == expected, f"stale propagation product: {path}")
        require(closure["closure_complete"], "propagation closure has unresolved residue")
        print(json.dumps({"status": "PASS", "closure_hash": closure["closure_hash"], "resolved_components": len(closure["resolved_components"]), "required_surfaces": len(closure["registry_derived_surfaces"]), "fixpoint_iterations": closure["fixpoint"]["iterations"], "claim_scope": "declared_relation_closure_only"}, sort_keys=True))
        return 0
    for path, payload in products.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    print(json.dumps({"closure_complete": closure["closure_complete"], "closure_hash": closure["closure_hash"], "residue": len(closure["residue"])}, sort_keys=True))
    return 0 if closure["closure_complete"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
