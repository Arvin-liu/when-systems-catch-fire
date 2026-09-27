#!/usr/bin/env python3
"""Fail-closed structural validation for the frozen Task225 R0.1 design."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[5]
SUBTREE = REPO / "ignition/reports/evaluations/ignition-225-cognitive-evolution-r0-1"
REQUIRED_POLICY_FIELDS = {
    "selector_inputs",
    "applicability_rule",
    "action_mapping",
    "preserved_rule_ids",
    "unresolved_or_fallback_rule",
    "stop_conditions",
    "evidence_provenance",
    "scope_ceiling",
}


def fail(message: str) -> None:
    raise SystemExit(f"TASK225_R01_DESIGN_INVALID: {message}")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # includes parse and read errors
        fail(f"invalid JSON at {path.relative_to(REPO)}: {exc}")


def main() -> None:
    required = [
        SUBTREE / "README.md",
        SUBTREE / "PRE-FREEZE-DESIGN-GATE-FAILURE-01.md",
        SUBTREE / "revision/PROMPT.md",
        SUBTREE / "revision/schema.json",
        SUBTREE / "revision/sealed/revision-targets.json",
        SUBTREE / "transfer/PROMPT.md",
        SUBTREE / "transfer/schema.json",
        SUBTREE / "transfer/template.md",
        SUBTREE / "transfer/condition-map.schema.json",
        SUBTREE / "transfer/sealed/target-index.json",
        SUBTREE / "evaluator/criteria.md",
        SUBTREE / "evaluator/outcome-rule.json",
        SUBTREE / "evaluator/schema.json",
        SUBTREE / "design/repair-round-3/ROUND-3-ASSESSMENT.md",
    ]
    for path in required:
        if not path.is_file():
            fail(f"missing required file {path.relative_to(REPO)}")

    failure = (SUBTREE / "PRE-FREEZE-DESIGN-GATE-FAILURE-01.md").read_text(encoding="utf-8")
    for token in (
        "STOP_CODE=TASK225_R01_ANTIBYPASS_DESIGN_FAILED",
        "SCIENTIFIC_FREEZE_CREATED=false",
        "EXPERIMENTAL_OUTPUTS_CREATED=false",
    ):
        if token not in failure:
            fail(f"failure receipt missing {token}")

    assessment = (SUBTREE / "design/repair-round-3/ROUND-3-ASSESSMENT.md").read_text(encoding="utf-8")
    for token in (
        "FAMILY01=4/4",
        "FAMILY02=4/4",
        "FAMILY03=4/4",
        "M0_ONLY_TWO_WAY_AMBIGUITY_PROVEN=3/3",
        "FULL_A_CASE_VALIDITY_GATE=3/3",
    ):
        if token not in assessment:
            fail(f"round-3 gate receipt missing {token}")
    for role in ("A-case-designer-report.md", "B-m0-only-review.md", "C-e1-selector-review.md", "D-target-leakage-review.md"):
        if not (SUBTREE / "design/repair-round-3" / role).is_file():
            fail(f"missing frozen role report {role}")

    revision_schema = load_json(SUBTREE / "revision/schema.json")
    op_schema = revision_schema.get("properties", {}).get("operational_policy", {})
    if set(op_schema.get("required", [])) != REQUIRED_POLICY_FIELDS:
        fail("revision schema does not require the complete operational_policy field set")

    manifests = sorted((SUBTREE / "revision/manifests").glob("*.json"))
    if len(manifests) != 6:
        fail(f"expected six revision manifests, found {len(manifests)}")
    expected_ids = {f"RL-{i:03d}" for i in range(1, 7)}
    seen_ids = set()
    for manifest_path in manifests:
        manifest = load_json(manifest_path)
        task_id = manifest.get("opaque_task_id")
        if task_id in seen_ids:
            fail(f"duplicate revision task id {task_id}")
        seen_ids.add(task_id)
        if not isinstance(manifest.get("inputs"), list) or len(manifest["inputs"]) != 4:
            fail(f"{task_id} must have exactly four allowlisted inputs")
        input_paths = {item["path"] for item in manifest["inputs"]}
        prompt_path = (SUBTREE / "revision/PROMPT.md").relative_to(REPO).as_posix()
        schema_path = (SUBTREE / "revision/schema.json").relative_to(REPO).as_posix()
        m0_paths = [path for path in input_paths if path.endswith("/m0.md")]
        e1_paths = [path for path in input_paths if path.endswith("/revision-evidence-e1.md")]
        if prompt_path not in input_paths or schema_path not in input_paths or len(m0_paths) != 1 or len(e1_paths) != 1:
            fail(f"{task_id} has a changed or unexpected input allowlist")
        if m0_paths[0].rsplit("/", 1)[0] != e1_paths[0].rsplit("/", 1)[0]:
            fail(f"{task_id} M0 and E1 do not belong to the same family")
        for item in manifest["inputs"]:
            path = REPO / item["path"]
            if not path.is_file() or digest(path) != item.get("sha256"):
                fail(f"{task_id} input hash mismatch: {item.get('path')}")
            if "sealed" in item["path"] or "heldout" in item["path"].lower() or "target" in item["path"].lower():
                fail(f"{task_id} includes a prohibited sealed/heldout/target input")
    if seen_ids != expected_ids:
        fail(f"revision task IDs mismatch: {sorted(seen_ids)}")

    for family in ("FAMILY01", "FAMILY02", "FAMILY03"):
        family_dir = SUBTREE / "families" / family
        for case_id in ("A", "B", "C"):
            if not (family_dir / "cases" / f"{case_id}.md").is_file():
                fail(f"missing {family} visible case {case_id}")
        targets = load_json(family_dir / "sealed/targets.json")
        if set(targets.get("cases", {})) != {"A", "B", "C"}:
            fail(f"{family} sealed targets must define A/B/C")
        proof = family_dir / "control-dependency-proof.md"
        if not proof.is_file():
            fail(f"missing {family} control-dependency proof")

    transfer_manifest_dir = SUBTREE / "transfer/manifests"
    if transfer_manifest_dir.exists() and any(transfer_manifest_dir.iterdir()):
        fail("transfer manifests were instantiated before all revision tasks terminated")
    condition_map = SUBTREE / "transfer/sealed/condition-map.json"
    if condition_map.exists():
        fail("condition map was instantiated before transfer tasks were prepared")

    for output_name in ("revisions", "transfers", "evaluators"):
        out_dir = SUBTREE / "outputs" / output_name
        if out_dir.exists() and any(out_dir.iterdir()):
            fail(f"experimental outputs must be zero at freeze: {output_name}")

    rule = load_json(SUBTREE / "evaluator/outcome-rule.json")
    if rule.get("fixed_denominator") != 6:
        fail("outcome rule denominator must remain six")
    if rule.get("primary_chain") != "EVOLUTION_TRANSFER_SUCCESS = R AND E_A AND NOT O_A AND E_B AND E_C":
        fail("primary chain differs from the command")
    if rule.get("secondary_endpoint") != "EXPLICIT_ARTIFACT_ADVANTAGE_A = E_A AND NOT F_A":
        fail("secondary endpoint differs from the command")
    if rule.get("secondary_is_not_a_primary_gate") is not True:
        fail("F_A must remain outside the primary gate")

    manifest_path = SUBTREE / "freeze-manifest.json"
    sidecar_path = SUBTREE / "freeze.sha256"
    if not manifest_path.is_file() or not sidecar_path.is_file():
        fail("freeze manifest or sidecar missing")
    freeze = load_json(manifest_path)
    expected_frozen_paths = {
        entry.get("path") for entry in freeze.get("frozen_files", [])
    }
    actual_frozen_paths = {
        path.relative_to(REPO).as_posix()
        for path in SUBTREE.rglob("*")
        if path.is_file() and path not in (manifest_path, sidecar_path)
    }
    if expected_frozen_paths != actual_frozen_paths:
        missing = sorted(actual_frozen_paths - expected_frozen_paths)
        extra = sorted(expected_frozen_paths - actual_frozen_paths)
        fail(f"freeze file inventory mismatch; missing={missing}; extra={extra}")
    for entry in freeze.get("frozen_files", []):
        path = REPO / entry["path"]
        if not path.is_file() or digest(path) != entry.get("sha256"):
            fail(f"frozen file hash mismatch: {entry.get('path')}")
    external = freeze.get("external_evidence", [])
    if len(external) != 6:
        fail(f"expected six frozen external M0/E1 source hashes, found {len(external)}")
    for entry in external:
        path = REPO / entry["path"]
        if not path.is_file() or digest(path) != entry.get("sha256"):
            fail(f"external source hash mismatch: {entry.get('path')}")
    expected_sidecar = f"{digest(manifest_path)}  freeze-manifest.json\n"
    if sidecar_path.read_text(encoding="utf-8") != expected_sidecar:
        fail("freeze sidecar mismatch")
    frozen_counts = freeze.get("outputs_at_scientific_freeze", {})
    if frozen_counts != {"revision": 0, "transfer": 0, "evaluator": 0}:
        fail(f"outputs at freeze are not zero: {frozen_counts}")

    print("TASK225_R01_DESIGN_VALIDATION=PASS")
    print("REVISION_MANIFESTS=6")
    print("FAMILY_CASES=3x3")
    print("REVISION_OUTPUTS=0")
    print("TRANSFER_OUTPUTS=0")
    print("EVALUATOR_OUTPUTS=0")
    print(f"FROZEN_FILES={len(freeze.get('frozen_files', []))}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        fail(str(exc))
