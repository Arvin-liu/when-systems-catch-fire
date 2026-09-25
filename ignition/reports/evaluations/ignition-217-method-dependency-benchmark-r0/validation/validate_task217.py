#!/usr/bin/env python3
"""Validate the frozen Task217 benchmark, secrecy boundary, and file inventory."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
TASK_REL = Path("ignition/reports/evaluations/ignition-217-method-dependency-benchmark-r0")
TASK = ROOT / TASK_REL
BASE = "24198effb2e2d94c19fe212244bbfcf47f995b2a"
CONDITIONS = ["FACTS_ONLY", "SKILL_ONLY", "METHOD", "LINKLESS_METHOD_CONTROL"]
CASES = [f"CASE{i:02d}" for i in range(1, 7)]
CUTS = {"CASE01": "R01", "CASE02": "R02", "CASE03": "R02", "CASE04": "R01", "CASE05": "R02", "CASE06": "R04"}


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"FAIL_TASK217_VALIDATION: {message}")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def relation_rows(text: str) -> list[tuple[str, str]]:
    return re.findall(r"^\[(R\d+)\] (.+)$", text, re.M)


def main() -> int:
    require(TASK.is_dir(), "Task217 subtree missing")
    case_root = TASK / "benchmark" / "case-families"
    condition_root = TASK / "benchmark" / "conditions"
    control_root = TASK / "benchmark" / "control-equivalence"
    require(sorted(p.name for p in case_root.iterdir() if p.is_dir()) == CASES, "case-family set is not exactly CASE01..CASE06")

    for condition in CONDITIONS:
        paths = sorted((condition_root / condition).glob("CASE*.md"))
        require([p.stem for p in paths] == CASES, f"{condition} does not contain exactly six cases")

    for case in CASES:
        facts = (case_root / case / "facts.md").read_bytes()
        provenance = read_json(case_root / case / "provenance.json")
        require(provenance.get("facts_sha256") == sha(facts), f"facts provenance hash mismatch for {case}")
        method_text = (condition_root / "METHOD" / f"{case}.md").read_text(encoding="utf-8")
        control_text = (condition_root / "LINKLESS_METHOD_CONTROL" / f"{case}.md").read_text(encoding="utf-8")
        method_atoms = re.findall(r"^\[A\d+\].*$", method_text, re.M)
        control_atoms = re.findall(r"^\[A\d+\].*$", control_text, re.M)
        require(len(method_atoms) == 7 and method_atoms == control_atoms, f"atomic content differs in link-broken control for {case}")
        method_relations = relation_rows(method_text)
        control_relations = relation_rows(control_text)
        require(len(method_relations) == 5, f"METHOD relation count is not five for {case}")
        expected_retained = [(rid, statement) for rid, statement in method_relations if rid != CUTS[case]]
        require(len(expected_retained) == 4 and control_relations == expected_retained, f"control relation cut or retained relations mismatch for {case}")
        note = (control_root / f"{case}-control-equivalence-note.md").read_text(encoding="utf-8")
        require(f"Removed relation: {CUTS[case]}." in note, f"control-equivalence note cut mismatch for {case}")
        skill = (condition_root / "SKILL_ONLY" / f"{case}.md").read_text(encoding="utf-8")
        require(re.search(r"^\d+\. \[S01\]", skill, re.M) is not None, f"stable skill source locators missing for {case}")

    prompt_path = TASK / "benchmark" / "neutral-task-prompt.md"
    prompt = prompt_path.read_bytes()
    prompt_sha = sha(prompt)
    prompt_text = prompt.decode("utf-8")
    require(not re.search(r"facts_only|skill_only|linkless_method_control|\bmethod\b|\bskill\b|\bbroken\b", prompt_text, re.I), "neutral prompt contains a condition label or name")
    schema = TASK / "benchmark" / "successor-output-r0.1.json"
    task207_schema = ROOT / "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0/packets/PKT-B6092E/output-schema.json"
    require(schema.read_bytes() == task207_schema.read_bytes(), "Task207 successor output schema was not reused byte-for-byte")

    future = TASK / "future-tasks"
    index = read_json(future / "FUTURE-TASK-INDEX.json")
    sealed = read_json(TASK / "evaluator" / "sealed-r0" / "condition-map.json")
    manifests = sorted((future / "manifests").glob("*.json"))
    payloads = sorted((future / "payloads").glob("*.md"))
    require(index.get("task_count") == 12 and len(index.get("tasks", [])) == 12, "future task index is not 12 entries")
    require(len(manifests) == 12 and len(payloads) == 12, "expected twelve manifests and twelve payloads")
    require(sealed.get("sealed") is True and sealed.get("successors_may_read") is False, "condition map is not sealed")
    entries = sealed.get("entries", [])
    require(len(entries) == 12, "sealed condition map is not 12 entries")
    require({entry["condition"] for entry in entries} == set(CONDITIONS), "sealed map condition set differs")
    require(all(sum(1 for entry in entries if entry["condition"] == condition) == 3 for condition in CONDITIONS), "sealed map does not have three tasks per condition")
    entry_by_id = {entry["future_task_id"]: entry for entry in entries}
    index_ids = {row["future_task_id"] for row in index["tasks"]}
    require(index_ids == set(entry_by_id), "opaque index and sealed map task IDs differ")
    orders_by_replicate: dict[int, set[tuple[str, ...]]] = {1: set(), 2: set(), 3: set()}
    hashes_by_condition: dict[str, set[str]] = {condition: set() for condition in CONDITIONS}
    maps = []

    for manifest_path in manifests:
        manifest = read_json(manifest_path)
        require("condition" not in manifest and "replicate" not in manifest and "case_order" not in manifest, f"manifest exposes condition metadata: {manifest_path.name}")
        require(manifest["fresh_conversation_required"] is True and manifest["conversation_replication_unit"] is True, "conversation independence missing")
        require(manifest["prompt_sha256"] == prompt_sha, "prompt hash mismatch across task manifest")
        require(manifest["output_schema_sha256"] == sha(schema.read_bytes()), "output schema hash mismatch")
        allow = manifest["read_allowlist"]
        require(len(allow) == 3, "successor allowlist must expose exactly prompt, payload, and schema")
        require(all("evaluator/" not in item["path"] and "targets" not in item["path"] and "condition-map" not in item["path"] for item in allow), "successor allowlist exposes sealed evaluation data")
        for item in allow:
            require(sha((ROOT / item["path"]).read_bytes()) == item["sha256"], f"read-allowlist hash mismatch: {item['path']}")
        payload_path = ROOT / manifest["payload_path"]
        payload_bytes = payload_path.read_bytes()
        payload = payload_bytes.decode("utf-8")
        require(sha(payload_bytes) == manifest["payload_sha256"], f"payload hash mismatch: {payload_path.name}")
        require(not re.search(r"FACTS_ONLY|SKILL_ONLY|LINKLESS_METHOD_CONTROL|\bMETHOD\b", payload), f"payload exposes an exact condition label: {payload_path.name}")
        order = tuple(re.findall(r"^## Record (CASE\d\d)$", payload, re.M))
        require(len(order) == 6 and set(order) == set(CASES), f"packet case order invalid: {payload_path.name}")
        map_entry = entry_by_id.get(manifest["future_task_id"])
        require(map_entry is not None and map_entry["packet_id"] == manifest["packet_id"], "manifest does not match sealed map")
        require(list(order) == map_entry["case_order"], "packet order differs from sealed map")
        orders_by_replicate[map_entry["replicate"]].add(order)
        hashes_by_condition[map_entry["condition"]].add(json.dumps(manifest["case_source_sha256"], sort_keys=True))
        for case in CASES:
            fact_bytes = (case_root / case / "facts.md").read_bytes()
            supplement = (condition_root / map_entry["condition"] / f"{case}.md").read_bytes()
            expected_hash = sha(fact_bytes + b"\n\n" + supplement)
            require(manifest["case_source_sha256"][case] == expected_hash, f"case source hash mismatch for {case}")
            require(f"Source SHA-256: {expected_hash}" in payload, f"packet omits displayed source hash for {case}")
        maps.append(map_entry)

    require(all(len(orders_by_replicate[r]) == 1 for r in (1, 2, 3)), "matched conditions do not share order within replicate")
    require(len({next(iter(orders_by_replicate[r])) for r in (1, 2, 3)}) == 3, "replicates do not use three distinct case orders")
    require(all(len(hashes_by_condition[c]) == 1 for c in CONDITIONS), "condition semantics differ across its three replicates")

    targets = read_json(TASK / "evaluator" / "sealed-r0" / "targets.json")
    criteria = read_json(TASK / "evaluator" / "criteria-r1.json")
    outcome = read_json(TASK / "evaluator" / "preregistered-outcome-rule.json")
    require(len(targets.get("cases", [])) == 6, "sealed target count differs from six")
    for target in targets["cases"]:
        require([link["id"] for link in target["required_method_links"]] == [f"R{i:02d}" for i in range(1, 6)], f"required method links incomplete for {target['case_id']}")
    require(criteria["primary_endpoint"]["name"] == "METHOD_DEPENDENCY_SUCCESS", "wrong primary endpoint")
    require(set(criteria["domains"]) == {"FACTUAL_FIDELITY", "EVIDENCE_BOUNDARY", "DECISION_QUALITY", "REFERENCE_INTEGRATION"}, "legacy score domains differ")
    require(all(criteria["domains"][domain]["scale"] == [0, 1, 2] for domain in criteria["domains"]), "legacy score scale differs")
    require(outcome["matched_contrasts_per_evaluator"] == 18, "matched denominator differs")
    require(outcome["definitions"]["METHOD_CONTRAST_SUCCESS"] == "true iff M is true, L is false, and at least one of F or S is false.", "full contrast definition differs")
    require(outcome["benchmark_disposition"]["PARTIAL"]["both_evaluators_must_independently_meet_all"][2].startswith("METHOD_LINKLESS_WIN in at least 10/18"), "PARTIAL threshold differs from command wording")
    require(outcome["outputs_present_at_freeze"] is False and outcome["successors_launched"] is False and outcome["evaluators_launched"] is False, "future outputs or runs are marked present")

    changed = subprocess.check_output(["git", "diff", "--name-only", BASE, "HEAD"], cwd=ROOT, text=True).splitlines()
    require(changed and all(path.startswith(TASK_REL.as_posix() + "/") for path in changed), "changes extend outside isolated Task217 subtree")
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
    require(status == "", "worktree is not clean")

    freeze = TASK / "freeze" / "FREEZE-MANIFEST.json"
    sidecar = TASK / "freeze" / "FREEZE-MANIFEST.sha256"
    manifest = read_json(freeze)
    excluded = {freeze.relative_to(ROOT).as_posix(), sidecar.relative_to(ROOT).as_posix()}
    actual_files = {p.relative_to(ROOT).as_posix() for p in TASK.rglob("*") if p.is_file()} - excluded
    inventory = {entry["path"]: entry["sha256"] for entry in manifest["files"]}
    require(set(inventory) == actual_files, "freeze inventory does not cover exactly all non-recursive task artifacts")
    require(manifest["file_count"] == len(inventory), "freeze file count mismatch")
    for path, expected in inventory.items():
        require(sha((ROOT / path).read_bytes()) == expected, f"freeze SHA256 mismatch: {path}")
    digest = sha(freeze.read_bytes())
    expected_sidecar = f"{digest}  {freeze.relative_to(ROOT).as_posix()}\n"
    require(sidecar.read_text(encoding="utf-8") == expected_sidecar, "freeze manifest sidecar mismatch")
    print(f"TASK217_STEP06_VALIDATION_PASS files={len(inventory)} prompt_sha256={prompt_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
