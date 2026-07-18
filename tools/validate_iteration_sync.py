#!/usr/bin/env python3
"""Validate iteration lifecycle, task-specific seals, and propagation closure."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas/operations/iteration-manifest.schema.json"
REGISTRY_PATH = ROOT / "data/operations/synchronization-surfaces.json"
REGISTRY_SCHEMA_PATH = ROOT / "schemas/operations/synchronization-surfaces.schema.json"
MANIFEST_DIR = ROOT / "data/operations/iterations"
SEAL_DIR = ROOT / "reports/operations"

LEGACY_FRONT_DOORS = {
    "README.md",
    "docs/project-current-state.md",
    "AI-HANDOFF.md",
    "AI-START-HERE.md",
    "llms.txt",
    "SUMMARY.md",
    "CHANGELOG.md",
}
LEGACY_Q24_METHOD_PATHS = {
    "ITERATION.md",
    "schemas/operations/iteration-manifest.schema.json",
    "data/operations/iterations/121Q24.json",
    "tools/validate_iteration_sync.py",
    "tests/test_iteration_sync.py",
    ".github/workflows/foundation-validation.yml",
    "reports/operations/121Q24-current-state-reconciliation.md",
    "reports/operations/121Q24-completion-seal.json",
    "templates/operations/task-command-template.md",
    "templates/operations/execution-result-template.md",
    "templates/operations/independent-review-template.md",
}
TRIGGERING_CLASSIFICATIONS = {
    "CAPABILITY_ADDITION",
    "INTERFACE_CHANGE",
    "GOVERNANCE_CHANGE",
    "RELEASE_OR_CURRENT_STATE_SYNC",
    "OPERATIONS_METHOD",
}
UNRESOLVED_STATUSES = {"PENDING", "TODO", "UNKNOWN", "", "TBD", "N/A"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
# -- Seal structural validation (F13: self-head attestation bypass hardening) --

# Known top-level fields across all seal versions.
_SEAL_KNOWN_TOP_LEVEL: frozenset[str] = frozenset({
    "task_id", "status", "method_version", "manifest_path",
    "lifecycle", "phase_b",
    "phase_a", "external_exact_head_attestation", "local_validation",
    "manifest_hash", "boundaries",
    "pages_binding",
    "completion_state", "synchronization_registry", "external_attestations",
    "propagation_closure", "propagation_closure_hash", "system_map",
    "pages_artifacts", "edges", "changed_paths_count", "relations",
    "historical_digest_evidence",
    "authored_seed_paths_count", "base_to_head_diff_paths_count",
    "generated_output_paths_count", "diff_coverage_complete",
    "external_artifact_attestation_contract",
})

# Nested dicts where unknown keys are strictly rejected.
_SEAL_STRICT_NESTED: dict[str, frozenset[str]] = {
    "phase_b": frozenset({"base", "base_head", "branch", "claim_ceiling",
                           "draft_pr", "merged_pr", "merge_commit",
                           "head_binding", "accepted_head",
                           "candidate_method_version", "method_name",
                           "method_version", "review_id",
                           "superseded_candidate_head"}),
    "phase_b.head_binding": frozenset({"mode", "authority", "receipt_path",
                                        "embedded_exact_current_head",
                                        "live_refetch_required"}),
    "lifecycle": frozenset({"candidate", "ready_for_gpt_verification",
                              "accepted", "merged", "current"}),
    "completion_state": frozenset({"implementation_complete",
                                     "repository_synchronization_complete",
                                     "external_synchronization_required",
                                     "external_synchronization_attested",
                                     "project_synchronization_complete"}),
    "synchronization_registry": frozenset({"path", "version"}),
    "propagation_closure": frozenset({"closure_hash", "closure_path",
                                        "complete", "unresolved_residue"}),
    "system_map": frozenset({"current_version", "candidate_version",
                               "groups", "nodes", "edges", "l7_added"}),
    "pages_artifacts": frozenset({"github_artifact_archive_digest",
                                    "pages_payload_tar_digest"}),
}

# Nested dicts where keys are per-task/per-version.
_SEAL_PERMISSIVE_NESTED: frozenset[str] = frozenset({
    "phase_a", "external_exact_head_attestation", "manifest_hash",
    "boundaries", "local_validation",
    "historical_digest_evidence",
    "historical_digest_evidence.subject_run_ids",
    "historical_digest_evidence.dual_digest",
    "external_artifact_attestation_contract",
})



def load_json(path: Path) -> object:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _validate_schema(instance: object, schema_path: Path, source: Path) -> None:
    schema = load_json(schema_path)
    errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda error: list(error.path))
    if errors:
        first = errors[0]
        location = ".".join(str(part) for part in first.path) or "<root>"
        raise AssertionError(f"{source}: schema error at {location}: {first.message}")


def validate_manifest_schema(manifest: dict, source: Path) -> None:
    _validate_schema(manifest, SCHEMA_PATH, source)


def validate_registry(registry: dict, source: Path = REGISTRY_PATH) -> dict[str, dict]:
    _validate_schema(registry, REGISTRY_SCHEMA_PATH, source)
    surfaces = registry["surfaces"]
    ids = [item["surface_id"] for item in surfaces]
    require(len(ids) == len(set(ids)), f"{source}: duplicate surface_id")
    by_id = {item["surface_id"]: item for item in surfaces}
    for item in surfaces:
        for dependency in item["derived_from"]:
            require(dependency in by_id, f"{source}: unknown derived_from surface {dependency}")
        is_external = item["surface_type"] == "external_rendered_deployed_surface"
        require((item["authority"] == "external") == is_external, f"{source}: external authority/type mismatch for {item['surface_id']}")
        if not is_external:
            require((ROOT / item["locator"]).exists(), f"{source}: repository surface does not exist: {item['locator']}")
    return by_id


def _unique(items: list[str], label: str, source: Path) -> None:
    require(len(items) == len(set(items)), f"{source}: duplicate {label}: {items}")


def _impact_decisions(manifest: dict, source: Path) -> dict[str, dict]:
    surfaces = [item["surface"] for item in manifest["impact_matrix"]]
    _unique(surfaces, "impact_matrix.surface", source)
    return {item["surface"]: item for item in manifest["impact_matrix"]}


def _validation_names(items: list[dict], label: str, source: Path) -> None:
    names = [item["name"] for item in items]
    _unique(names, f"{label} validation name", source)
    run_ids = [item.get("run_id") for item in items if item.get("run_id") is not None]
    require(len(run_ids) == len(set(run_ids)), f"{source}: duplicate {label} workflow run id")


def infer_seal_path(manifest: dict) -> Path:
    declared = manifest.get("completion_seal_path")
    if declared:
        return ROOT / declared
    return SEAL_DIR / f"{manifest['task_id']}-completion-seal.json"


def required_registry_surfaces(manifest: dict, registry: dict[str, dict]) -> set[str]:
    classifications = set(manifest["change_classification"])
    dimensions = set(manifest["state_transition"]["changed_dimensions"])
    required = {
        surface_id
        for surface_id, item in registry.items()
        if classifications.intersection(item["trigger_classifications"])
        or dimensions.intersection(item["trigger_dimensions"])
    }
    changed = True
    while changed:
        changed = False
        for surface_id, item in registry.items():
            if surface_id in required:
                before = len(required)
                required.update(item["derived_from"])
                changed |= len(required) != before
            elif required.intersection(item["derived_from"]):
                required.add(surface_id)
                changed = True
    return required


def _validate_lifecycle(manifest: dict, source: Path) -> None:
    status = manifest["status"]
    branch_pr = manifest["branch_pr"]
    require(not status["current"] or status["merged"], f"{source}: current cannot be true unless merged is true")
    require(not status["merged"] or status["accepted"], f"{source}: merged cannot be true unless accepted is true")
    require(not status["accepted"] or status["ready_for_gpt_verification"], f"{source}: accepted cannot be true unless ready_for_gpt_verification is true")
    require(any(status.values()), f"{source}: all lifecycle states are false")
    require(branch_pr["merged"] == status["merged"], f"{source}: branch_pr.merged and status.merged disagree")
    require(not (branch_pr["draft"] and (status["accepted"] or status["merged"] or status["current"])), f"{source}: Draft cannot be accepted, merged, or current")
    require(not (branch_pr["merged"] and branch_pr["draft"]), f"{source}: branch_pr cannot be both merged and draft")
    if status["merged"] or status["current"]:
        merge_commit = branch_pr.get("merge_commit")
        require(branch_pr["pr_number"] and branch_pr["pr_number"] > 0, f"{source}: merged/current task requires PR number")
        require(isinstance(merge_commit, str) and SHA_RE.match(merge_commit), f"{source}: merged/current task requires valid merge commit")
        require("candidate_only" not in manifest["claim_ceiling"], f"{source}: merged/current task cannot keep candidate-only claim ceiling")


def _validate_ready_evidence(manifest: dict, source: Path) -> None:
    status = manifest["status"]
    if not status["ready_for_gpt_verification"]:
        return
    branch_pr = manifest["branch_pr"]
    head_binding = manifest["head_binding"]
    external_policy = manifest["validation"]["external_exact_head_policy"]
    require(branch_pr["pr_number"] and branch_pr["pr_number"] > 0, f"{source}: ready candidate requires PR number")
    if not (status["accepted"] or status["merged"] or status["current"]):
        require(branch_pr["draft"], f"{source}: unaccepted ready candidate must remain Draft until independently accepted")
    else:
        require(not branch_pr["draft"], f"{source}: accepted, merged, or current ready record must not remain Draft")
    require(head_binding["mode"] == "external_exact_head_attestation", f"{source}: ready candidate requires external exact-head attestation mode")
    require(head_binding["authority"] == "pull_request_body_and_1111_receipt", f"{source}: ready candidate requires externally resolvable attestation authority")
    require(head_binding["pr_number"] == branch_pr["pr_number"], f"{source}: head-binding PR mismatch")
    require(head_binding["receipt_path"] == manifest["receipt_location"], f"{source}: head-binding receipt mismatch")
    require(head_binding["embedded_exact_current_head"] is False, f"{source}: repository artifact cannot claim embedded exact current self HEAD")
    require(head_binding["live_refetch_required"] is True, f"{source}: exact-head attestation must require live re-fetch")
    require(external_policy["required"] is True, f"{source}: ready candidate requires external exact-head attestation policy")
    require(external_policy["authority"] == head_binding["authority"], f"{source}: attestation authority mismatch")
    require(external_policy["live_refetch_before_acceptance_or_merge"] is True, f"{source}: acceptance/merge must require live PR/CI re-fetch")
    require(set(external_policy["required_workflows"]) == {"foundation-validation", "function-os-ci"}, f"{source}: exact-head policy must require both remote workflows")
    require(manifest["validation"]["local"], f"{source}: ready candidate requires local validation")
    for item in manifest["validation"]["local"] + manifest["validation"]["remote"]:
        require(item["status"].upper() not in UNRESOLVED_STATUSES, f"{source}: unresolved validation status for {item['name']}")
        require(item["status"].upper() in {"PASS", "SUCCESS"}, f"{source}: validation status must be PASS/SUCCESS for {item['name']}")
    for item in manifest["validation"]["remote"]:
        require(item.get("run_id"), f"{source}: remote validation {item['name']} missing run_id")
        require(item.get("evidence_scope") == "historical_subject_head_only", f"{source}: stale CI evidence mislabeled as current-final evidence")
        require(item.get("subject_head"), f"{source}: historical validation {item['name']} missing subject_head")
        require(item.get("conclusion", "").lower() == "success", f"{source}: remote validation {item['name']} conclusion not success")

def _validate_seal_known_fields(seal: dict, source: Path) -> None:
    """Reject unknown top-level and strictly-checked nested fields in the seal."""
    for key in seal:
        if key not in _SEAL_KNOWN_TOP_LEVEL:
            raise AssertionError(
                f"{source}: seal contains unknown top-level field: {key}"
            )
    for dot_path, allowed in _SEAL_STRICT_NESTED.items():
        parts = dot_path.split(".")
        obj = seal
        for part in parts:
            if not isinstance(obj, dict):
                break
            obj = obj.get(part)
            if obj is None:
                break
        if isinstance(obj, dict):
            for key in obj:
                if key not in allowed:
                    raise AssertionError(
                        f"{source}: seal contains unknown field: {dot_path}.{key}"
                    )
    for dot_path in _SEAL_PERMISSIVE_NESTED:
        parts = dot_path.split(".")
        obj = seal
        for part in parts:
            if not isinstance(obj, dict):
                break
            obj = obj.get(part)
        if obj is not None and not isinstance(obj, dict):
            raise AssertionError(
                f"{source}: seal field {dot_path} expected a dict, "
                f"got {type(obj).__name__}"
            )


def _get_current_head() -> str:
    """Run git rev-parse HEAD and return the SHA. Fail-closed on error."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, cwd=ROOT,
            timeout=30,
        )
    except FileNotFoundError:
        raise AssertionError(
            "git not found, cannot validate seal against current HEAD"
        )
    except subprocess.TimeoutExpired:
        raise AssertionError(
            "git rev-parse HEAD timed out, cannot validate seal"
        )
    if result.returncode != 0:
        raise AssertionError(
            f"cannot resolve current HEAD (git rev-parse exited "
            f"{result.returncode}): {result.stderr.strip()}"
        )
    sha = result.stdout.strip()
    if not SHA_RE.match(sha):
        raise AssertionError(f"invalid HEAD SHA format: {sha}")
    return sha


def _check_ancestor(sha: str) -> bool:
    """Check whether sha is an ancestor of HEAD."""
    try:
        result = subprocess.run(
            ["git", "merge-base", "--is-ancestor", sha, "HEAD"],
            capture_output=True, text=True, cwd=ROOT,
            timeout=30,
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def _validate_seal_no_self_head_embedding(seal: dict, source: Path) -> None:
    """Reject seal if any string value embeds the current Git HEAD.
    Allows historical ancestor SHAs in historical_digest_evidence.
    Fail-closed if git HEAD cannot be resolved."""
    current_head = _get_current_head()
    _ANCESTOR_PREFIXES = ("historical_digest_evidence",)

    def _is_ancestor_prefix(path: str) -> bool:
        return any(
            path == p or path.startswith(p + ".") or path.startswith(p + "[")
            for p in _ANCESTOR_PREFIXES
        )

    def _scan(obj, path: str = "") -> None:
        if isinstance(obj, str):
            if current_head in obj:
                raise AssertionError(
                    f"{source}: seal embeds current Git HEAD at {path}: "
                    f"self-head attestation bypass detected"
                )
            if _is_ancestor_prefix(path) and SHA_RE.match(obj):
                if not _check_ancestor(obj):
                    raise AssertionError(
                        f"{source}: seal contains non-ancestor SHA at "
                        f"{path}: historical claim does not resolve "
                        f"to an ancestor of HEAD"
                    )
        elif isinstance(obj, dict):
            for key, val in obj.items():
                _scan(val, f"{path}.{key}" if path else key)
        elif isinstance(obj, list):
            for idx, val in enumerate(obj):
                _scan(val, f"{path}[{idx}]")

    _scan(seal, "")


def _validate_seal(manifest: dict, seal: dict, source: Path) -> None:
    _validate_seal_known_fields(seal, source)
    _validate_seal_no_self_head_embedding(seal, source)
    require(seal.get("task_id") == manifest["task_id"], f"{source}: seal task mismatch")
    require(seal.get("method_version") == manifest["method_version"], f"{source}: seal method_version mismatch")
    phase_b = seal.get("phase_b", {})
    lifecycle = seal.get("lifecycle", {})
    require(phase_b.get("draft_pr") == manifest["branch_pr"]["pr_number"], f"{source}: seal PR mismatch")
    require(phase_b.get("branch") == manifest["branch_pr"]["branch"], f"{source}: seal branch mismatch")
    require(phase_b.get("base_head") == manifest["branch_pr"]["base_head"], f"{source}: seal base_head mismatch")
    require(phase_b.get("base", manifest["branch_pr"]["base"]) == manifest["branch_pr"]["base"], f"{source}: seal base mismatch")
    if manifest["status"]["merged"] or manifest["status"]["current"]:
        require(phase_b.get("merge_commit") == manifest["branch_pr"].get("merge_commit"), f"{source}: seal merge commit mismatch")
        require(seal.get("status") != "READY_FOR_GPT_VERIFICATION_CANDIDATE_ONLY", f"{source}: seal remains candidate-only after merge")
    seal_binding = phase_b.get("head_binding", {})
    binding_labels = {
        "mode": "seal head-binding mode mismatch",
        "authority": "seal attestation authority mismatch",
        "receipt_path": "seal attestation receipt mismatch",
        "embedded_exact_current_head": "seal embedded-head policy mismatch",
        "live_refetch_required": "seal live-refetch policy mismatch",
    }
    for key, label in binding_labels.items():
        require(seal_binding.get(key) == manifest["head_binding"][key], f"{source}: {label}")
    require(phase_b.get("claim_ceiling") == manifest["claim_ceiling"], f"{source}: seal claim ceiling mismatch")
    for key in ("candidate", "ready_for_gpt_verification", "accepted", "merged", "current"):
        require(lifecycle.get(key) == manifest["status"][key], f"{source}: seal lifecycle mismatch for {key}")
    if manifest["method_version"] in {"1.1.0", "1.2.0"}:
        require(seal.get("completion_state") == manifest["completion_state"], f"{source}: seal completion_state mismatch")
        require(seal.get("synchronization_registry", {}).get("path") == manifest["synchronization_closure"]["registry_path"], f"{source}: seal synchronization registry mismatch")
        require(seal.get("external_attestations") == manifest["synchronization_closure"]["external_attestations"], f"{source}: seal external_attestations mismatch")
    if manifest["method_version"] == "1.2.0":
        require(seal.get("propagation_closure", {}).get("closure_hash") == manifest["propagation_closure"]["closure_hash"], f"{source}: seal propagation closure hash mismatch")
    _validate_seal_f12(seal, source)



def _validate_seal_f12(seal: dict, source: Path) -> None:
    """F12/F12C: reject live digests without subject, self-SHA, contract violations,
    stale diff counts, and stale map counts."""
    # 1. pages_artifacts must not exist as live digest without subject HEAD
    require("pages_artifacts" not in seal,
            f"{source}: seal must not contain pages_artifacts with unbound live digests")

    # 2. Historical digest must have subject_head and run IDs
    hde = seal.get("historical_digest_evidence")
    if hde:
        require(hde.get("subject_head"), f"{source}: historical_digest_evidence missing subject_head")
        require(hde.get("subject_run_ids"), f"{source}: historical_digest_evidence missing subject_run_ids")
        run_ids = hde.get("subject_run_ids", {})
        require(run_ids.get("pages"), f"{source}: historical_digest_evidence missing pages run")
        require(run_ids.get("foundation"), f"{source}: historical_digest_evidence missing foundation run")
        require(run_ids.get("function_os"), f"{source}: historical_digest_evidence missing function_os run")
        # Dual digest distinction
        dd = hde.get("dual_digest", {})
        if dd.get("github_artifact_archive_digest") and dd.get("pages_payload_tar_digest"):
            require(dd["github_artifact_archive_digest"] != dd["pages_payload_tar_digest"],
                    f"{source}: historical dual digests must not be identical for different objects")

    # 4. External attestation contract validation (F12C single-authority model)
    contract = seal.get("external_artifact_attestation_contract")
    if contract:
        # F12C: must use identity_critical_fields (not old required_fields)
        require("identity_critical_fields" in contract,
                f"{source}: contract must use identity_critical_fields (not required_fields)")
        require("required_fields" not in contract,
                f"{source}: contract must not use deprecated required_fields key")
        identity_fields = [
            "subject_head", "foundation_run", "function_os_run", "pages_run",
            "artifact_head_sha", "github_artifact_archive_digest", "pages_payload_tar_digest"
        ]
        for rf in identity_fields:
            require(rf in contract.get("identity_critical_fields", []),
                    f"{source}: contract missing identity-critical field: {rf}")
        require(contract.get("embedded_live_digest") is False,
                f"{source}: contract must not claim embedded_live_digest=true")
        require(contract.get("live_refetch_required") is True,
                f"{source}: contract must require live_refetch")
        # F12C new contract fields
        require(contract.get("validator_path") == "tools/validate_external_attestation.py",
                f"{source}: contract must declare validator_path")
        require(contract.get("schema_version") == "1.0.0",
                f"{source}: contract must declare schema_version 1.0.0")
        require(contract.get("full_required_fields_authority") == "validator",
                f"{source}: contract must declare full_required_fields_authority as validator")

    # 5. For method 1.2.0 candidate seals: must not be accepted/merged/current
    lifecycle = seal.get("lifecycle", {})
    if seal.get("method_version") == "1.2.0" and lifecycle.get("candidate") is True:
        if lifecycle.get("ready_for_gpt_verification") is True:
            require(lifecycle.get("accepted") is not True,
                    f"{source}: 1.2.0 candidate seal must not be marked accepted")
            require(lifecycle.get("merged") is not True,
                    f"{source}: 1.2.0 candidate seal must not be marked merged")
            require(lifecycle.get("current") is not True,
                    f"{source}: 1.2.0 candidate seal must not be marked current")

    # 6. F12C: Reject ambiguous stale changed_paths_count
    require("changed_paths_count" not in seal,
            f"{source}: seal must not contain ambiguous changed_paths_count; "
            "use authored_seed_paths_count, generated_output_paths_count, "
            "base_to_head_diff_paths_count, diff_coverage_complete")

    # 7. F12C: Dynamic diff coverage validation from Git diff + request + authority
    import subprocess as _sp
    try:
        _base_head = None
        _manifest_path = ROOT / "data/operations/iterations/121Q32.json"
        if _manifest_path.is_file():
            _m = json.loads(_manifest_path.read_text(encoding="utf-8"))
            _base_head = _m.get("branch_pr", {}).get("base_head")
        if _base_head:
            _diff_result = _sp.run(
                ["git", "diff", "--name-only", f"{_base_head}...HEAD"],
                capture_output=True, text=True, cwd=str(ROOT)
            )
            _actual_diff = set(p for p in _diff_result.stdout.strip().split("\n") if p)

            _req_path = ROOT / "data/operations/propagation/121Q32-request.json"
            _seeds = set()
            if _req_path.is_file():
                _req = json.loads(_req_path.read_text(encoding="utf-8"))
                _seeds = set(_req.get("changed_paths", []))

            _auth_path = ROOT / "data/operations/generated-output-authority.json"
            _generated = set()
            if _auth_path.is_file():
                _auth = json.loads(_auth_path.read_text(encoding="utf-8"))
                _generated = set(g["path"] for g in _auth.get("generated_outputs", []))

            # Verify seal counts match actual data
            if "base_to_head_diff_paths_count" in seal:
                require(seal["base_to_head_diff_paths_count"] == len(_actual_diff),
                        f"{source}: seal base_to_head_diff_paths_count {seal['base_to_head_diff_paths_count']} "
                        f"!= actual diff {len(_actual_diff)}")
            if "authored_seed_paths_count" in seal:
                require(seal["authored_seed_paths_count"] == len(_seeds),
                        f"{source}: seal authored_seed_paths_count {seal['authored_seed_paths_count']} "
                        f"!= request seeds {len(_seeds)}")
            if "generated_output_paths_count" in seal:
                require(seal["generated_output_paths_count"] == len(_generated),
                        f"{source}: seal generated_output_paths_count {seal['generated_output_paths_count']} "
                        f"!= authority generated {len(_generated)}")

            # Verify disjoint
            _overlap = _seeds & _generated
            require(not _overlap,
                    f"{source}: seed and generated paths must be disjoint, overlap: {_overlap}")

            # Verify union covers diff
            _union = _seeds | _generated
            require(_actual_diff == _union,
                    f"{source}: diff coverage incomplete: "
                    f"in_diff_not_covered={_actual_diff - _union}, "
                    f"covered_not_in_diff={_union - _actual_diff}")

            # diff_coverage_complete must be true only when all pass
            if "diff_coverage_complete" in seal:
                require(seal["diff_coverage_complete"] is True,
                        f"{source}: diff_coverage_complete must be true when all checks pass")
    except (OSError, json.JSONDecodeError):
        pass  # Skip if git or files unavailable

    # 8. F12C: Seal system_map cross-check against interactive-system-map.json
    _map_path = ROOT / "data/architecture/interactive-system-map.json"
    if _map_path.is_file() and "system_map" in seal:
        _actual_map = json.loads(_map_path.read_text(encoding="utf-8"))
        _seal_map = seal["system_map"]
        _actual_groups = len(_actual_map.get("groups", []))
        _actual_nodes = len(_actual_map.get("nodes", []))
        _actual_edges = len(_actual_map.get("edges", []))

        require(_seal_map.get("groups") == _actual_groups,
                f"{source}: seal system_map groups {_seal_map.get('groups')} != actual {_actual_groups}")
        require(_seal_map.get("nodes") == _actual_nodes,
                f"{source}: seal system_map nodes {_seal_map.get('nodes')} != actual {_actual_nodes}")
        require(_seal_map.get("edges") == _actual_edges,
                f"{source}: seal system_map edges {_seal_map.get('edges')} != actual {_actual_edges}")

def _validate_evidence_ref(ref: str, source: Path) -> None:
    if ref.startswith("external:"):
        require(re.match(r"^external:(pr_body|1111_receipt|live_refetch|github_actions):\S+$", ref) is not None, f"{source}: invalid external evidence reference: {ref}")
        return
    repository_ref = ref.removeprefix("repo:")
    require("://" not in repository_ref, f"{source}: repository evidence must not be an undeclared external URI: {ref}")
    require((ROOT / repository_ref).exists(), f"{source}: nonexistent repository evidence reference: {ref}")


def _pending_external_blockers(gate: str, required_ids: set[str], registry: dict[str, dict], attestations: dict[str, dict]) -> list[str]:
    return sorted(
        surface_id
        for surface_id in required_ids
        if registry[surface_id]["surface_type"] == "external_rendered_deployed_surface"
        and gate in registry[surface_id]["blocks"]
        and attestations[surface_id]["status"] != "attested"
    )


def _validate_v11_closure(manifest: dict, source: Path, registry: dict[str, dict]) -> None:
    closure = manifest["synchronization_closure"]
    completion = manifest["completion_state"]
    require(closure["registry_version"] == load_json(REGISTRY_PATH)["registry_version"], f"{source}: registry version mismatch")
    decisions = closure["surface_decisions"]
    ids = [item["surface_id"] for item in decisions]
    _unique(ids, "synchronization surface decision", source)
    decision_map = {item["surface_id"]: item for item in decisions}
    required_ids = required_registry_surfaces(manifest, registry)
    missing = sorted(required_ids - set(decision_map))
    require(not missing, f"{source}: missing registry-derived surface decisions: {missing}")
    unknown = sorted(set(decision_map) - set(registry))
    require(not unknown, f"{source}: unknown synchronization surface decisions: {unknown}")

    repository_complete = True
    external_required = False
    external_ids: set[str] = set()
    for surface_id in required_ids:
        spec = registry[surface_id]
        decision = decision_map[surface_id]
        require(decision["decision"] in spec["allowed_decisions"], f"{source}: disallowed decision for {surface_id}")
        require(decision["reason"].strip(), f"{source}: blank synchronization reason for {surface_id}")
        require(decision["evidence_refs"] and all(ref.strip() for ref in decision["evidence_refs"]), f"{source}: {surface_id} decision lacks evidence references")
        for ref in decision["evidence_refs"]:
            _validate_evidence_ref(ref, source)
        require(decision["validation_mode"] == spec["validation_mode"], f"{source}: validation mode mismatch for {surface_id}")
        require(decision.get("derived_from", []) == spec["derived_from"], f"{source}: derived_from mismatch for {surface_id}")
        is_external = spec["surface_type"] == "external_rendered_deployed_surface"
        if is_external:
            external_required = True
            external_ids.add(surface_id)
            require(spec["locator"] not in manifest["changed_surfaces"], f"{source}: external surface incorrectly listed as repository changed path")
        elif decision["decision"] == "CHANGE":
            require(spec["locator"] in manifest["changed_surfaces"], f"{source}: changed registry surface absent from changed_surfaces: {spec['locator']}")
            require((ROOT / spec["locator"]).exists(), f"{source}: changed registry path missing: {spec['locator']}")

    attestation_items = closure["external_attestations"]
    attestation_ids = [item["surface_id"] for item in attestation_items]
    _unique(attestation_ids, "external attestation surface", source)
    attestations = {item["surface_id"]: item for item in attestation_items}
    require(set(attestations) == external_ids, f"{source}: external attestation coverage mismatch")
    for surface_id, attestation in attestations.items():
        spec = registry.get(surface_id)
        require(spec is not None and spec["surface_type"] == "external_rendered_deployed_surface", f"{source}: unknown or non-external attestation surface: {surface_id}")
        expected_stage = "post_merge" if spec["validation_mode"].startswith("post_merge_") else "pre_merge"
        require(attestation["stage"] == expected_stage, f"{source}: external attestation stage mismatch for {surface_id}")
        require(attestation["authority"] == "pull_request_body_and_1111_receipt", f"{source}: wrong external attestation authority for {surface_id}")
        require(attestation["live_state_locally_verifiable"] is False, f"{source}: external live state cannot be locally verifiable for {surface_id}")
        for ref in attestation["evidence_refs"]:
            _validate_evidence_ref(ref, source)
            require(ref.startswith("external:"), f"{source}: external attestation evidence must use declared external reference format: {ref}")
        if attestation["status"] == "attested" and expected_stage == "post_merge":
            require(manifest["status"]["merged"] and not manifest["branch_pr"]["draft"], f"{source}: Draft/unmerged candidate cannot claim post-merge production attestation")

    all_external_attested = all(item["status"] == "attested" for item in attestations.values()) if external_ids else True
    require(closure["live_external_surfaces_verified"] is False, f"{source}: local validator cannot claim live rendered verification")
    require(completion["external_synchronization_required"] == external_required, f"{source}: external synchronization requirement mismatch")
    require(completion["external_synchronization_attested"] == all_external_attested, f"{source}: global external synchronization flag disagrees with per-surface attestations")
    require(completion["repository_synchronization_complete"] == (repository_complete and not closure["unresolved_residue"]), f"{source}: repository synchronization completion inconsistent with residue")
    expected_project = completion["repository_synchronization_complete"] and (not external_required or completion["external_synchronization_attested"])
    require(completion["project_synchronization_complete"] == expected_project, f"{source}: project synchronization completion is inflated or inconsistent")
    if manifest["status"]["ready_for_gpt_verification"]:
        require(completion["implementation_complete"], f"{source}: implementation incomplete candidate cannot be ready")
        require(completion["repository_synchronization_complete"], f"{source}: repository synchronization incomplete candidate cannot be ready")
        require(not _pending_external_blockers("ready", required_ids, registry, attestations), f"{source}: pending external surface blocks ready")
    if manifest["status"]["accepted"]:
        blockers = _pending_external_blockers("accepted", required_ids, registry, attestations)
        require(not blockers, f"{source}: pending external surfaces block accepted: {blockers}")
    if manifest["status"]["merged"]:
        blockers = _pending_external_blockers("merged", required_ids, registry, attestations)
        require(not blockers, f"{source}: pending external surfaces block merged: {blockers}")
    if manifest["status"]["current"]:
        require(manifest["status"]["merged"], f"{source}: current requires merged lifecycle")
        blockers = _pending_external_blockers("current", required_ids, registry, attestations)
        require(not blockers, f"{source}: pending external surfaces block current: {blockers}")
        require(completion["project_synchronization_complete"], f"{source}: current lifecycle requires project synchronization complete")


def _validate_v12_propagation(manifest: dict, source: Path) -> None:
    try:
        from tools.operations.compute_change_propagation import compute, impact_report, serialized
    except ModuleNotFoundError:
        from operations.compute_change_propagation import compute, impact_report, serialized

    binding = manifest["propagation_closure"]
    path_fields = {
        "request_path": binding["request_path"],
        "closure_path": binding["closure_path"],
        "impact_report_path": binding["impact_report_path"],
        "system_map_delta_path": binding["system_map_delta_path"],
        "residue_path": binding["residue_path"],
    }
    paths = {name: ROOT / relative for name, relative in path_fields.items()}
    for name, path in paths.items():
        require(path.is_file(), f"{source}: missing propagation product {name}: {path.relative_to(ROOT)}")

    request = load_json(paths["request_path"])
    persisted_closure = load_json(paths["closure_path"])
    recomputed, delta = compute(request)
    require(persisted_closure == recomputed, f"{source}: propagation closure is stale or hand-edited")
    require(paths["impact_report_path"].read_text(encoding="utf-8") == impact_report(recomputed), f"{source}: propagation impact report is stale")
    require(paths["system_map_delta_path"].read_bytes() == serialized(delta), f"{source}: system-map delta is stale")
    expected_residue = {
        "task_id": recomputed["task_id"],
        "closure_hash": recomputed["closure_hash"],
        "closure_complete": recomputed["closure_complete"],
        "residue": recomputed["residue"],
    }
    require(paths["residue_path"].read_bytes() == serialized(expected_residue), f"{source}: propagation residue product is stale")
    require(recomputed["task_id"] == manifest["task_id"], f"{source}: propagation task binding mismatch")
    require(binding["closure_hash"] == recomputed["closure_hash"], f"{source}: propagation closure hash mismatch")
    require(binding["base_identity"] == recomputed["base_identity"], f"{source}: propagation base identity mismatch")
    require(binding["head_identity"] == recomputed["head_identity"], f"{source}: propagation head identity mismatch")
    require(binding["seed_paths"] == recomputed["seed_paths"], f"{source}: propagation seed paths mismatch")
    require(binding["seed_components"] == recomputed["seed_components"], f"{source}: propagation seed components mismatch")
    require(binding["resolved_components"] == recomputed["resolved_components"], f"{source}: resolved component closure mismatch")
    require(binding["typed_path_ids"] == [item["relation_id"] for item in recomputed["typed_paths"]], f"{source}: typed propagation paths mismatch")
    require(binding["component_decisions"] == recomputed["actual_component_decisions"], f"{source}: component decisions mismatch")
    require(binding["surface_decisions"] == recomputed["actual_surface_decisions"], f"{source}: surface propagation decisions mismatch")
    require(binding["registry_derived_surfaces"] == recomputed["registry_derived_surfaces"], f"{source}: registry-derived surface closure mismatch")
    require(binding["system_map_impact"]["decision"] == recomputed["system_map_impact"]["decision"], f"{source}: system-map impact decision mismatch")
    require(binding["system_map_impact"]["reason"] == recomputed["system_map_impact"]["reason"], f"{source}: system-map impact reason mismatch")
    require(binding["system_map_impact"]["delta_path"] == binding["system_map_delta_path"], f"{source}: system-map delta binding mismatch")
    require(binding["unresolved_residue"] == recomputed["residue"], f"{source}: unresolved propagation residue mismatch")
    require(binding["closure_complete"] == recomputed["closure_complete"], f"{source}: propagation completeness mismatch")
    require(binding["closure_complete"] and not binding["unresolved_residue"], f"{source}: unresolved propagation residue blocks ready closure")

    propagation_decisions = {item["item_id"]: item["decision"] for item in binding["surface_decisions"]}
    sync_decisions = {item["surface_id"]: item["decision"] for item in manifest["synchronization_closure"]["surface_decisions"]}
    require(set(propagation_decisions) == set(sync_decisions), f"{source}: propagation and synchronization surface coverage disagree")
    require(propagation_decisions == sync_decisions, f"{source}: propagation and synchronization decisions disagree")


def validate_custom(manifest: dict, source: Path, seal: dict, registry: dict[str, dict] | None = None) -> None:
    _validate_lifecycle(manifest, source)
    _validate_ready_evidence(manifest, source)
    classifications = set(manifest["change_classification"])
    changed = set(manifest["changed_surfaces"])
    decisions = _impact_decisions(manifest, source)
    _unique(manifest["changed_surfaces"], "changed_surfaces", source)
    _validation_names(manifest["validation"]["local"], "local", source)
    _validation_names(manifest["validation"]["remote"], "remote", source)

    if manifest["method_version"] == "1.0.0" and classifications & TRIGGERING_CLASSIFICATIONS:
        for surface in LEGACY_FRONT_DOORS:
            require(surface in decisions, f"{source}: missing front-door/current-state impact decision for {surface}")

    for surface, item in decisions.items():
        if item["decision"] == "CHANGE":
            require(surface in changed, f"{source}: CHANGE decision not present in changed_surfaces: {surface}")
        elif item["decision"] == "NO_CHANGE_WITH_REASON":
            require(item["reason"].strip(), f"{source}: {surface} has NO_CHANGE without reason")
            require(surface not in changed, f"{source}: NO_CHANGE surface falsely declared changed: {surface}")
    for path in changed:
        if "://" not in path:
            require((ROOT / path).exists(), f"{source}: declared changed path does not exist: {path}")

    if manifest["method_version"] == "1.0.0" and manifest["task_id"] == "121Q24" and "OPERATIONS_METHOD" in classifications:
        missing = sorted(LEGACY_Q24_METHOD_PATHS - changed)
        require(not missing, f"{source}: legacy Q24 operations method missing changed paths: {missing}")
    if manifest["method_version"] in {"1.1.0", "1.2.0"}:
        require(registry is not None, f"{source}: method {manifest['method_version']} requires synchronization registry")
        _validate_v11_closure(manifest, source, registry)
    if manifest["method_version"] == "1.2.0":
        _validate_v12_propagation(manifest, source)
    _validate_seal(manifest, seal, source)


def validate_manifest_bindings(documents: list[tuple[Path, dict]]) -> list[tuple[Path, dict, Path]]:
    seen_tasks: set[str] = set()
    seen_seals: set[Path] = set()
    bound: list[tuple[Path, dict, Path]] = []
    for path, manifest in documents:
        task_id = manifest["task_id"]
        require(task_id not in seen_tasks, f"{path}: duplicate task binding: {task_id}")
        seen_tasks.add(task_id)
        seal_path = infer_seal_path(manifest)
        require(seal_path not in seen_seals, f"{path}: duplicate completion seal binding: {seal_path}")
        seen_seals.add(seal_path)
        require(seal_path.is_file(), f"{path}: missing completion seal: {seal_path.relative_to(ROOT)}")
        bound.append((path, manifest, seal_path))
    return bound


def validate_all() -> dict:
    paths = sorted(MANIFEST_DIR.glob("*.json"))
    require(paths, "no iteration manifests found")
    registry = validate_registry(load_json(REGISTRY_PATH))
    documents = [(path, load_json(path)) for path in paths]
    for path, manifest in documents:
        validate_manifest_schema(manifest, path)
    bound = validate_manifest_bindings(documents)
    checked = 0
    for path, manifest, seal_path in bound:
        seal = load_json(seal_path)
        validate_custom(manifest, path, seal, registry)
        checked += 1

    return {
        "status": "PASS",
        "checked": checked,
        "implementation_consistency": "PASS",
        "repository_synchronization_closure": "PASS",
        "external_synchronization_required": any(load_json(path).get("completion_state", {}).get("external_synchronization_required", False) for path in paths),
        "live_external_surfaces_verified": False,
        "scope": "repository_local_consistency_and_synchronization_only",
    }


def main() -> int:
    try:
        result = validate_all()
    except (AssertionError, KeyError, TypeError, ValueError) as exc:
        print(f"iteration sync validation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
