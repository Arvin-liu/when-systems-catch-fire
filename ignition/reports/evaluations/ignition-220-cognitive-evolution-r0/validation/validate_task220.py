#!/usr/bin/env python3
"""Mechanically validate the frozen, no-output Task220 R0 preparation."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[5]
TASK_ROOT_REL = Path("ignition/reports/evaluations/ignition-220-cognitive-evolution-r0")
TASK_ID = "IGNITION-20260926-220"
FORMAL_BASE = "1f7286515768347a2a3a131dd0f6de87f631676c"
BRANCH = "work/IGNITION-20260926-220-cognitive-evolution-r0"
TASK217_SUBTREE = Path("ignition/reports/evaluations/ignition-217-method-dependency-benchmark-r0")
FAMILIES = {
    "FAMILY01": "BOUNDARY_NARROWING",
    "FAMILY02": "SPLIT_COEXIST",
    "FAMILY03": "RETIRE_REPLACE_BOUNDED",
}
CONDITIONS = {"M0_ONLY", "M0_PLUS_E1", "EVOLVED_M1"}
EXPECTED_CLASSES = {
    "A-revised-boundary.md": "REVISED_BOUNDARY_CASE",
    "B-preserved-old-scope.md": "PRESERVED_OLD_SCOPE_CASE",
    "C-edge-unresolved.md": "EDGE_UNRESOLVED_CASE",
}
MANIFEST_REL = TASK_ROOT_REL / "freeze/FREEZE-MANIFEST.json"
SIDECAR_REL = TASK_ROOT_REL / "freeze/FREEZE-MANIFEST.sha256"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class ValidationFailure(Exception):
    """Raised for a concise fail-closed validation result."""


def require(ok: bool, message: str) -> None:
    if not ok:
        raise ValidationFailure(message)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationFailure(f"cannot read JSON {path}: {exc}") from exc


def git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=repo_root, text=True, capture_output=True, check=False
    )
    require(result.returncode == 0, f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def validate_anchor(repo_root: Path) -> None:
    require(git(repo_root, "branch", "--show-current") == BRANCH, "Task220 branch differs")
    require(git(repo_root, "merge-base", "HEAD", FORMAL_BASE) == FORMAL_BASE, "Task220 base is not the required exact head")
    require(git(repo_root, "cat-file", "-t", FORMAL_BASE) == "commit", "required Task217 base commit is unavailable")
    changed_217 = git(repo_root, "diff", "--name-only", f"{FORMAL_BASE}...HEAD", "--", TASK217_SUBTREE.as_posix())
    require(not changed_217, f"Task217 frozen subtree changed: {changed_217.splitlines()}")


def expected_case_ids(family_id: str) -> set[str]:
    family_number = family_id[-2:]
    return {f"CE-F{family_number}-HO-{letter}-R0" for letter in "ABC"}


def validate_families(task_root: Path) -> dict[str, set[str]]:
    family_root = task_root / "families"
    require({p.name for p in family_root.iterdir() if p.is_dir()} == set(FAMILIES), "family inventory is not exactly FAMILY01..03")
    case_ids: dict[str, set[str]] = {}
    for family_id, operation in FAMILIES.items():
        family = family_root / family_id
        required_files = {
            "m0.md",
            "revision-evidence-e1.md",
            "provenance.json",
            "heldout/A-revised-boundary.md",
            "heldout/B-preserved-old-scope.md",
            "heldout/C-edge-unresolved.md",
        }
        present = {p.relative_to(family).as_posix() for p in family.rglob("*") if p.is_file()}
        require(present == required_files, f"{family_id} artifact inventory differs: {sorted(present ^ required_files)}")

        m0 = (family / "m0.md").read_text(encoding="utf-8")
        e1 = (family / "revision-evidence-e1.md").read_text(encoding="utf-8")
        m0_lower = m0.lower()
        require("candidate" in m0_lower and "selection" in m0_lower and "discriminating" in m0_lower and "failure interpretation" in m0_lower, f"{family_id} M0 lacks complete method elements")
        require("source locator" in e1.lower() and "Exact observations" in e1, f"{family_id} E1 lacks source-bound exact observations")
        e1_lower = e1.lower()
        require(("no revised" in e1_lower or "no replacement" in e1_lower), f"{family_id} E1 does not explicitly withhold the revised answer")

        provenance = read_json(family / "provenance.json")
        require(provenance.get("family_id") == family_id, f"{family_id} provenance identity differs")
        require(provenance.get("family_operation_class") == operation, f"{family_id} operation differs")
        require(provenance.get("synthetic_only") is True and provenance.get("external_truth_claim") == "NONE", f"{family_id} source ceiling differs")
        require(provenance.get("evidence_locators") and provenance.get("provenance_relations"), f"{family_id} provenance links are missing")

        found: set[str] = set()
        for name, expected_class in EXPECTED_CLASSES.items():
            content = (family / "heldout" / name).read_text(encoding="utf-8")
            match = re.search(r"\*\*Case ID:\*\*\s*(\S+)", content)
            require(match is not None, f"{family_id}/{name} lacks a case ID")
            case_id = match.group(1)
            found.add(case_id)
            require(f"**Case class:** {expected_class}" in content, f"{family_id}/{name} class differs")
        require(found == expected_case_ids(family_id), f"{family_id} held-out case IDs differ")
        case_ids[family_id] = found
    return case_ids


def validate_revision_tasks(repo_root: Path, task_root: Path) -> tuple[list[dict[str, Any]], set[str]]:
    sealed_targets = read_json(task_root / "revision/sealed-r0/revision-targets.json")
    require(sealed_targets.get("sealed") is True and sealed_targets.get("read_allowlist_excluded") is True, "revision targets are not sealed from revision manifests")
    require(sealed_targets.get("future_outputs_present") is False, "revision target records future outputs")
    targets = sealed_targets.get("targets", [])
    require({item.get("family_id") for item in targets} == set(FAMILIES) and len(targets) == 3, "sealed revision targets do not cover the exact three families")
    target_operations = {"FAMILY01": "NARROW", "FAMILY02": "SPLIT_COEXIST", "FAMILY03": "RETIRE_REPLACE_BOUNDED"}
    for target in targets:
        family_id = target["family_id"]
        require(target.get("revision_operation") == target_operations[family_id], f"{family_id} sealed operation differs")
        require(all(target.get(key) for key in ("licensed_change", "preserved_scope", "changed_scope", "required_uncertainty", "forbidden_overreaction", "required_lineage", "claim_ceiling")), f"{family_id} sealed revision target is incomplete")
    revision_schema = read_json(task_root / "revision/revision-output-schema.json")
    required_revision_fields = {
        "schema_version", "m0_id", "revision_id", "evidence_locators", "revision_operation", "preserved_scope",
        "changed_scope", "new_or_revised_relations", "rejected_overreaction", "uncertainties",
        "lineage_edges", "claim_ceiling",
    }
    require(set(revision_schema.get("required", [])) == required_revision_fields, "revision output schema required fields differ")

    index = read_json(task_root / "revision/future-tasks/FUTURE-TASK-INDEX.json")
    manifests_dir = task_root / "revision/future-tasks/manifests"
    files = sorted(manifests_dir.glob("*.json"))
    require(index.get("task_count") == 6 and len(files) == 6, "revision task count is not six")
    require(index.get("revision_agents_authorized_or_launched") is False, "revision dispatch is authorized or launched")
    tasks = index.get("tasks", [])
    ids = [item.get("future_task_id") for item in tasks]
    require(len(ids) == 6 and len(set(ids)) == 6, "revision task IDs are not six unique opaque IDs")
    require({Path(item.get("manifest_path", "")).name for item in tasks} == {p.name for p in files}, "revision index and manifest files differ")

    prompt_rel = "ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/revision/neutral-revision-prompt.md"
    schema_rel = "ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/revision/revision-output-schema.json"
    prompt_sha = sha256((repo_root / prompt_rel).read_bytes())
    schema_sha = sha256((repo_root / schema_rel).read_bytes())
    expected_ids: set[str] = set()
    output: list[dict[str, Any]] = []
    for manifest_path in files:
        manifest = read_json(manifest_path)
        task_id = manifest.get("future_task_id")
        require(task_id in ids and task_id not in expected_ids, f"unexpected or duplicate revision task ID: {task_id}")
        expected_ids.add(task_id)
        require(manifest_path.name == f"{task_id}.json", f"revision manifest filename differs for {task_id}")
        require(manifest.get("same_prompt_and_schema_for_all_tasks") is True, f"{task_id} prompt/schema identity flag differs")
        require(manifest.get("execution_state") == "NOT_LAUNCHED" and manifest.get("dispatch_authorized_by_task220") is False and manifest.get("output_present") is False, f"{task_id} has an execution/output state")
        require(manifest.get("neutral_prompt_path") == prompt_rel and manifest.get("neutral_prompt_sha256") == prompt_sha, f"{task_id} prompt binding differs")
        require(manifest.get("output_schema_path") == schema_rel and manifest.get("output_schema_sha256") == schema_sha, f"{task_id} schema binding differs")
        allowlist = manifest.get("read_allowlist", [])
        require(len(allowlist) == 4, f"{task_id} read allowlist is not exactly four files")
        paths = [item.get("path") for item in allowlist]
        require(len(set(paths)) == 4, f"{task_id} read allowlist has duplicate paths")
        require(all("heldout/" not in path and "/sealed-r0/" not in path and "transfer/" not in path and "/evaluator/" not in path for path in paths), f"{task_id} exposes a held-out or sealed/evaluation input")
        require(set(paths) == {manifest.get("m0_path"), manifest.get("e1_path"), prompt_rel, schema_rel}, f"{task_id} allowlist contains an unexpected input")
        for item in allowlist:
            artifact = repo_root / item["path"]
            require(artifact.is_file() and sha256(artifact.read_bytes()) == item.get("sha256"), f"{task_id} allowlist hash mismatch: {item.get('path')}")
        require(manifest.get("m0_sha256") == next(item["sha256"] for item in allowlist if item["path"] == manifest.get("m0_path")), f"{task_id} M0 hash alias differs")
        require(manifest.get("e1_sha256") == next(item["sha256"] for item in allowlist if item["path"] == manifest.get("e1_path")), f"{task_id} E1 hash alias differs")
        require(manifest.get("access_scope"), f"{task_id} access scope is absent")
        output.append(manifest)
    require(expected_ids == set(ids), "revision task index contains an unmaterialized task")
    family_task_counts = {family_id: 0 for family_id in FAMILIES}
    for manifest in output:
        path = manifest["m0_path"]
        family_id = next((key for key in FAMILIES if f"/families/{key}/" in path), None)
        require(family_id is not None, f"revision task does not bind an expected family: {path}")
        family_task_counts[family_id] += 1
    require(family_task_counts == {family_id: 2 for family_id in FAMILIES}, f"revision replicates per family differ: {family_task_counts}")
    return output, set(ids)


def validate_transfer(task_root: Path, case_ids: dict[str, set[str]], revision_ids: set[str]) -> None:
    targets = read_json(task_root / "transfer/sealed-r0/transfer-targets.json")
    require(targets.get("sealed") is True and targets.get("condition_neutral") is True, "transfer target seal or condition neutrality differs")
    require(targets.get("primary_endpoint", {}).get("name") == "TRANSFER_TARGET_SUCCESS", "transfer primary endpoint differs")
    require(targets["primary_endpoint"].get("requires_m1_only_relation_locators") is False, "primary transfer endpoint requires M1-only locators")
    target_cases = targets.get("cases", [])
    require(len(target_cases) == 9, "transfer target count is not nine")
    all_ids = {case.get("case_id") for case in target_cases}
    require(all_ids == set().union(*case_ids.values()), "transfer targets do not cover the exact nine held-out cases")
    require(targets.get("future_outputs_present") is False and targets.get("condition_map_released") is False, "transfer outputs or map have been released")
    for case in target_cases:
        require(case.get("visible_to_successor") is not True, f"sealed evaluator reference is marked successor-visible: {case.get('case_id')}")

    condition_map = read_json(task_root / "transfer/sealed-r0/condition-map-template.json")
    require(condition_map.get("status") == "SEALED_TEMPLATE_NOT_RELEASED" and condition_map.get("condition_map_released") is False, "transfer map is released")
    require(condition_map.get("template_only") is True and condition_map.get("dispatch_authorized") is False and condition_map.get("evaluators_launched") is False, "transfer map template permits dispatch/evaluation")
    lineages = condition_map.get("future_lineages", [])
    require(len(lineages) == 6 and condition_map.get("lineage_count") == 6, "transfer map does not contain six lineages")
    require(condition_map.get("planned_conversation_count") == 18 and condition_map.get("matched_assignments_per_lineage") == 3, "transfer conversation design is not 18")
    seen_revision_ids: set[str] = set()
    for lineage in lineages:
        family_id = lineage.get("family_id")
        revision_id = lineage.get("revision_task_id")
        require(family_id in FAMILIES and revision_id in revision_ids and revision_id not in seen_revision_ids, "transfer lineage identity is invalid")
        seen_revision_ids.add(revision_id)
        require(lineage.get("case_order") and set(lineage["case_order"]) == case_ids[family_id] and len(lineage["case_order"]) == 3, f"{revision_id} does not use its family held-out set")
        assignments = lineage.get("matched_assignments", [])
        require(len(assignments) == 3 and {item.get("condition") for item in assignments} == CONDITIONS, f"{revision_id} matched conditions differ")
    require(seen_revision_ids == revision_ids, "transfer map omits a revision lineage")

    successor_manifest = read_json(task_root / "transfer/future-task-template/successor-visible-manifest-template.json")
    successor_text = json.dumps(successor_manifest, ensure_ascii=False).upper()
    require(not any(label in successor_text for label in CONDITIONS), "condition label leaks into successor-visible template")
    require(not any("condition" in str(key).lower() for key in successor_manifest), "condition field leaks into successor-visible template")
    packet_template = read_json(task_root / "transfer/future-task-template/packet-construction-template.json")
    require(packet_template.get("template_only") is True and packet_template.get("instantiate_final_packets") is False, "final transfer packets were instantiated")
    require(packet_template.get("runtime_policy", {}).get("selected_by_task220") is False, "Task220 selected a runtime")
    require(packet_template.get("current_state", {}).get("transfer_successors_launched") is False, "transfer successors were launched")


def validate_evaluation_design(task_root: Path) -> None:
    criteria = read_json(task_root / "evaluator/criteria-r0.json")
    require(criteria.get("evaluators", {}).get("independent_count") == 2, "evaluator count differs from two")
    require(criteria["evaluators"].get("third_adjudicator_added") is False and criteria["evaluators"].get("hidden_chain_of_thought_requested_or_scored") is False, "evaluation protocol added a third evaluator or CoT scoring")
    require(criteria.get("primary_revision_endpoint", {}).get("name") == "REVISION_VALIDITY_SUCCESS", "revision endpoint differs")
    require(criteria.get("primary_transfer_endpoint", {}).get("name") == "TRANSFER_TARGET_SUCCESS", "transfer endpoint differs")
    require(criteria["primary_transfer_endpoint"].get("scored_identically_in_all_conditions") is True, "transfer endpoint is not condition-neutral")

    rule = read_json(task_root / "evaluator/preregistered-outcome-rule-r0.json")
    require(rule.get("frozen_before_outputs") is True, "outcome rule is not frozen before outputs")
    require(all(rule.get(key) is False for key in ("revision_outputs_present", "transfer_outputs_present", "evaluator_outputs_present")), "an output exists before registration")
    design = rule.get("design", {})
    require((design.get("families"), design.get("revision_replicates_per_family"), design.get("lineages"), design.get("future_transfer_conversations_if_all_revision_outputs_usable")) == (3, 2, 6, 18), "preregistered design counts differ")
    require(set(rule.get("conditions", [])) == CONDITIONS, "preregistered conditions differ")
    endpoints = rule.get("lineage_endpoints", {})
    require(endpoints.get("REVISED_BOUNDARY_GAIN") == "E_A AND NOT O_A AND NOT F_A", "revised-boundary counterfactual formula differs")
    require(endpoints.get("EVOLUTION_CHAIN_SUCCESS") == "R AND REVISED_BOUNDARY_GAIN AND PRESERVATION_SUCCESS AND EDGE_BOUNDARY_SUCCESS", "evolution-chain formula differs")
    dispositions = rule.get("per_evaluator_disposition", {})
    supported = set(dispositions.get("SUPPORTED", {}).get("all_required", []))
    require(supported == {
        "REVISION_VALIDITY_SUCCESS >= 5/6",
        "EVOLUTION_CHAIN_SUCCESS >= 5/6",
        "each of 3 families has >=1 successful lineage",
        "at least 2/3 families have both revision replicates successful",
        "zero UNSUPPORTED_GLOBAL_RETIREMENT errors in successful EVOLVED_M1 lineages",
        "zero PRESERVED_SCOPE_LOST errors in successful EVOLVED_M1 lineages",
    }, "SUPPORTED disposition threshold differs")
    partial = set(dispositions.get("PARTIAL", {}).get("all_required", []))
    require(partial == {
        "REVISION_VALIDITY_SUCCESS >= 4/6",
        "EVOLUTION_CHAIN_SUCCESS >= 3/6",
        "at least 2/3 families have >=1 successful lineage",
        "sum(E_A) > sum(O_A) across the six matched lineages",
        "sum(E_A) > sum(F_A) across the six matched lineages",
    } and dispositions["PARTIAL"].get("only_if_SUPPORTED_not_met") is True, "PARTIAL disposition threshold differs")
    require(rule.get("statistical_claim") == "Descriptive counts only; no population inference or statistical-significance claim.", "outcome rule makes an inferential statistical claim")
    require(rule.get("revision_agents_launched") == 0 and rule.get("transfer_successors_launched") == 0 and rule.get("evaluators_launched") == 0, "revision, transfer, or evaluator work was launched")
    require(rule.get("runtime_chosen_by_task") is False and rule.get("r1_authorized") is False and rule.get("cross_model_transfer_authorized") is False, "runtime or later phase was authorized")


def validate_freeze(repo_root: Path, task_root: Path, require_closure: bool) -> dict[str, Any]:
    manifest_path = repo_root / MANIFEST_REL
    sidecar_path = repo_root / SIDECAR_REL
    require(manifest_path.is_file() and sidecar_path.is_file(), "freeze manifest or SHA-256 sidecar is missing")
    raw = manifest_path.read_bytes()
    expected_sidecar = f"{sha256(raw)}  {MANIFEST_REL.as_posix()}\n"
    require(sidecar_path.read_text(encoding="utf-8") == expected_sidecar, "freeze sidecar does not bind exact manifest bytes")
    manifest = read_json(manifest_path)
    require(manifest.get("task_id") == TASK_ID and manifest.get("formal_base") == FORMAL_BASE and manifest.get("branch") == BRANCH, "freeze anchor metadata differs")
    excluded = {manifest_path.relative_to(repo_root).as_posix(), sidecar_path.relative_to(repo_root).as_posix()}
    actual = {path.relative_to(repo_root).as_posix() for path in task_root.rglob("*") if path.is_file()} - excluded
    inventory = {item.get("path"): item.get("sha256") for item in manifest.get("files", [])}
    require(len(inventory) == len(manifest.get("files", [])), "freeze inventory has duplicate paths")
    require(set(inventory) == actual, f"freeze does not cover exact Task220 tree: missing={sorted(actual-set(inventory))}; extra={sorted(set(inventory)-actual)}")
    require(manifest.get("file_count") == len(inventory), "freeze file count differs")
    for path, digest in inventory.items():
        require(isinstance(digest, str) and SHA256_RE.fullmatch(digest), f"invalid SHA-256 in freeze inventory: {path}")
        require(sha256((repo_root / path).read_bytes()) == digest, f"freeze SHA-256 mismatch: {path}")
    if require_closure:
        external = manifest.get("external_generated_projections", {})
        require(external.get("repository_path_accounting") == "PASS", "repository path accounting is not recorded PASS")
        require(external.get("generator_closure") == "PASS", "generated projection closure is not recorded PASS")
        files = external.get("files", [])
        require(files, "generated projection closure file inventory is missing")
        paths: set[str] = set()
        for item in files:
            path, digest = item.get("path"), item.get("sha256")
            require(isinstance(path, str) and path not in paths, f"duplicate external generated path: {path}")
            paths.add(path)
            require(isinstance(digest, str) and SHA256_RE.fullmatch(digest), f"invalid external SHA-256: {path}")
            artifact = repo_root / path
            require(artifact.is_file() and sha256(artifact.read_bytes()) == digest, f"external generated SHA-256 mismatch: {path}")
        require(external.get("r0_compatibility_inventory") == "PASS", "legacy R0 compatibility closure is not recorded PASS")

        knowledge = manifest.get("external_generated_knowledge_experience", {})
        knowledge_files = knowledge.get("files", [])
        require(str(knowledge.get("audit_status", "")).startswith("PASS ") and str(knowledge.get("build_check", "")).startswith("PASS "), "Knowledge Experience build/audit is not recorded PASS")
        require(knowledge_files, "Knowledge Experience output inventory is missing")
        for item in knowledge_files:
            path, digest = item.get("path"), item.get("sha256")
            require(path in paths and next(row["sha256"] for row in files if row["path"] == path) == digest, f"Knowledge Experience output is not bound by the generated projection inventory: {path}")

        fire_seeds = manifest.get("external_generated_fire_seed_census", {})
        fire_files = fire_seeds.get("files", [])
        require(str(fire_seeds.get("validator_status", "")).startswith("PASS "), "Fire Seeds validation is not recorded PASS")
        require({item.get("path") for item in fire_files} == {
            "ignition/data/publication/fire-seeds/seed-census.json",
            "ignition/data/publication/fire-seeds/CHANGELOG.jsonl",
        }, "Fire Seeds projection inventory differs")
        for item in fire_files:
            path, digest = item.get("path"), item.get("sha256")
            require(path in paths and next(row["sha256"] for row in files if row["path"] == path) == digest, f"Fire Seeds output is not bound by the generated projection inventory: {path}")

        compatibility = manifest.get("external_generated_cognitive_inheritance_r0_compatibility", {})
        compat_files = compatibility.get("files", [])
        compat_hashes = {item.get("path"): item.get("sha256") for item in compat_files}
        require(set(compat_hashes) == {
            "ignition/tools/validate_cognitive_inheritance_r0.py",
            "ignition/tests/test_cognitive_inheritance_r0.py",
        }, "legacy R0 compatibility inventory differs")
        for path, digest in compat_hashes.items():
            require(SHA256_RE.fullmatch(str(digest)) is not None and sha256((repo_root / path).read_bytes()) == digest, f"legacy R0 compatibility hash mismatch: {path}")

        classification_path = repo_root / "ignition/data/foundation/repository-path-classification/classification-manifest.jsonl"
        classification = {}
        for line in classification_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                row = json.loads(line)
                classification[row.get("path")] = row.get("category")
        tracked = git(repo_root, "ls-files", "--", TASK_ROOT_REL.as_posix()).splitlines()
        task_files = {path for path in tracked if path}
        require(task_files and all(classification.get(path) == "EVALUATION_EVIDENCE" for path in task_files), "repository path accounting does not classify every Task220 artifact as EVALUATION_EVIDENCE")
        require(external.get("task220_evaluation_evidence_paths") == len(task_files), "Task220 path-accounting entry count differs")
    return manifest


def write_freeze(repo_root: Path, task_root: Path, status: str) -> None:
    manifest_path = repo_root / MANIFEST_REL
    sidecar_path = repo_root / SIDECAR_REL
    old: dict[str, Any] = read_json(manifest_path) if manifest_path.exists() else {}
    excluded = {manifest_path, sidecar_path}
    files = []
    for path in sorted((p for p in task_root.rglob("*") if p.is_file() and p not in excluded), key=lambda p: p.relative_to(repo_root).as_posix()):
        files.append({"path": path.relative_to(repo_root).as_posix(), "sha256": sha256(path.read_bytes())})
    manifest = {
        "schema_version": "ignition-220-freeze-r0",
        "task_id": TASK_ID,
        "formal_base": FORMAL_BASE,
        "branch": BRANCH,
        "freeze_status": status,
        "files": files,
        "file_count": len(files),
    }
    for key in ("external_generated_projections", "external_generated_knowledge_experience", "external_generated_fire_seed_census", "external_generated_cognitive_inheritance_r0_compatibility"):
        if key in old:
            manifest[key] = old[key]
    data = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_bytes(data)
    sidecar_path.write_text(f"{sha256(data)}  {MANIFEST_REL.as_posix()}\n", encoding="utf-8")


def validate(repo_root: Path, require_closure: bool) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    task_root = repo_root / TASK_ROOT_REL
    require(task_root.is_dir(), f"missing Task220 artifact root: {task_root}")
    validate_anchor(repo_root)
    case_ids = validate_families(task_root)
    _, revision_ids = validate_revision_tasks(repo_root, task_root)
    validate_transfer(task_root, case_ids, revision_ids)
    validate_evaluation_design(task_root)
    freeze = validate_freeze(repo_root, task_root, require_closure)
    expected_family_dirs = {"FAMILY01", "FAMILY02", "FAMILY03"}
    forbidden = [p.relative_to(task_root).as_posix() for p in task_root.rglob("*") if p.is_file() and (p.parent.name == "outputs" or "output-record" in p.name.lower())]
    require(not forbidden, f"output material exists under the Task220 root: {forbidden}")
    return {
        "status": "PASS",
        "task_id": TASK_ID,
        "formal_base": FORMAL_BASE,
        "family_count": len(expected_family_dirs),
        "revision_replicates_per_family": 2,
        "future_revision_agents": len(revision_ids),
        "future_transfer_conversations": 18,
        "heldout_cases": sum(len(ids) for ids in case_ids.values()),
        "primary_revision_endpoint": "REVISION_VALIDITY_SUCCESS",
        "primary_transfer_endpoint": "TRANSFER_TARGET_SUCCESS",
        "primary_chain_endpoint": "EVOLUTION_CHAIN_SUCCESS",
        "revision_agents_launched": 0,
        "transfer_successors_launched": 0,
        "evaluators_launched": 0,
        "runtime_chosen_by_task": False,
        "task217_subtree_changed": False,
        "repository_path_accounting": freeze.get("external_generated_projections", {}).get("repository_path_accounting", "PENDING"),
        "generated_projection_closure": freeze.get("external_generated_projections", {}).get("generator_closure", "PENDING"),
        "freeze_file_count": freeze.get("file_count"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT, help="Formal repository root")
    parser.add_argument("--write-freeze", action="store_true", help="refresh task tree SHA-256 inventory and sidecar")
    parser.add_argument("--freeze-status", default="STEP07_FROZEN_REPOSITORY_CLOSURE_PENDING")
    parser.add_argument("--skip-repository-closure", action="store_true", help="only for the Step07 pre-closure validation")
    args = parser.parse_args()
    try:
        if args.write_freeze:
            write_freeze(args.repo_root.resolve(), args.repo_root.resolve() / TASK_ROOT_REL, args.freeze_status)
        result = validate(args.repo_root, require_closure=not args.skip_repository_closure)
    except ValidationFailure as exc:
        print(json.dumps({"status": "FAIL", "task_id": TASK_ID, "error": str(exc)}, ensure_ascii=False, sort_keys=True))
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
