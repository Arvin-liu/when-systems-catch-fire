#!/usr/bin/env python3
"""Validate Task217 R1 endpoint, controls, packet secrecy, repository closure, and freeze."""

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
PATH_MANIFEST_REL = "ignition/data/foundation/repository-path-classification/classification-manifest.jsonl"
CONDITIONS = ["FACTS_ONLY", "SKILL_ONLY", "METHOD", "LINKLESS_METHOD_CONTROL"]
CASES = [f"CASE{i:02d}" for i in range(1, 7)]
EXPECTED_CUTS = {
    "CASE01": {"R01"},
    "CASE02": {"R02"},
    "CASE03": {"R02"},
    "CASE04": {"R01", "R04"},
    "CASE05": {"R01"},
    "CASE06": {"R04"},
}
GENERATED_NONFUNCTION_OUTPUTS = {
    "ignition/data/foundation/nonfunction-claims/source-discovery.jsonl",
    "ignition/data/foundation/nonfunction-claims/closure-summary.json",
    "ignition/data/foundation/nonfunction-claims/discovery-coverage.json",
    "ignition/docs/foundation/nonfunction-claim-adjudication-index.md",
}
GENERATED_HUMAN_RESULTS_OUTPUTS = {
    "ignition/RESULTS/CHRONOLOGY.md",
    "ignition/data/governance/human-results/census.json",
    "ignition/data/governance/human-results/result-ledger.jsonl",
}
GENERATED_SELF_CORRECTION_OUTPUTS = {
    "ignition/data/governance/self-correction/audit-findings.jsonl",
    "ignition/RESULTS/SELF-CORRECTION-AUDIT.md",
}
SOURCE_FIRST_SEEN_REL = "ignition/data/governance/knowledge-experience/source-first-seen.json"
KNOWLEDGE_EXPERIENCE_MANIFEST_REL = "ignition/data/governance/knowledge-experience/manifest.json"


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"FAIL_TASK217_R1_VALIDATION: {message}")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"FAIL_TASK217_R1_VALIDATION: invalid JSON {path}: {exc}") from exc


def relation_rows(text: str) -> dict[str, dict[str, str]]:
    rows: dict[str, dict[str, str]] = {}
    pattern = re.compile(r"^\[(R\d+)\] (A\d+) --([A-Z_]+)--> (A\d+) :: (.+)$", re.M)
    for match in pattern.finditer(text):
        rid, source, edge, target, body = match.groups()
        require(rid not in rows, f"duplicate relation id {rid}")
        rows[rid] = {"source": source, "type": edge, "target": target, "body": body, "line": match.group(0)}
    return rows


def atom_block(text: str, case: str, condition: str) -> bytes:
    matches = re.findall(r"<!-- ATOM_BLOCK_BEGIN -->.*?<!-- ATOM_BLOCK_END -->", text, re.S)
    require(len(matches) == 1, f"{condition}/{case} must contain one delimited atom block")
    return matches[0].encode("utf-8")


def normalized_tokens(text: str) -> set[str]:
    stop = {"a", "an", "and", "are", "as", "at", "before", "by", "for", "from", "in", "of", "or", "the", "to", "under", "with", "without", "current", "every", "all", "one", "any", "after"}
    return {word for word in re.findall(r"[a-z0-9]+", text.casefold()) if word not in stop}


def primary_text_has_locator_gate(endpoint: dict) -> bool:
    true_iff = endpoint.get("true_iff", [])
    searchable = " ".join(str(item).casefold() for item in true_iff)
    return bool(re.search(r"method.only|method relation locator|required_method_links|cite every.*relation|relation locator required|source path required", searchable))


def check_primary_endpoint(criteria: dict, targets: dict, outcome: dict) -> None:
    primary = criteria.get("primary_endpoint", {})
    require(primary.get("name") == "TARGET_DECISION_SUCCESS", "criteria primary endpoint is not TARGET_DECISION_SUCCESS")
    require(primary.get("type") == "condition_neutral_binary_per_case", "primary endpoint type is not condition-neutral binary")
    require(primary.get("scored_identically_in_all_conditions") is True, "primary endpoint is not identical across conditions")
    require(primary.get("conditions") == CONDITIONS, "primary endpoint condition set/order differs")
    require(primary.get("requires_method_only_source_paths") is False, "primary endpoint requires a METHOD-only path")
    require(primary.get("requires_method_relation_locator") is False, "primary endpoint requires a METHOD relation locator")
    require(primary.get("source_locator_required_for_primary") is False, "primary endpoint requires a source locator")
    require(not primary_text_has_locator_gate(primary), "primary endpoint wording contains a locator/citation gate")

    target_primary = targets.get("primary_endpoint", {})
    require(target_primary.get("name") == "TARGET_DECISION_SUCCESS", "sealed-target primary endpoint differs")
    require(target_primary.get("scored_identically_in_all_conditions") is True, "sealed-target endpoint is not condition-neutral")
    require(target_primary.get("conditions") == CONDITIONS, "sealed-target condition set/order differs")
    require(target_primary.get("requires_method_only_source_paths") is False, "sealed target requires METHOD-only paths")
    require(target_primary.get("requires_method_relation_locator") is False, "sealed target requires METHOD relation locators")
    require(not primary_text_has_locator_gate(target_primary), "sealed primary endpoint wording contains a locator/citation gate")

    for case in targets.get("cases", []):
        rubric = case.get("target_decision_success_rubric", {})
        require(rubric.get("condition_neutral") is True, f"{case.get('case_id')} rubric is not condition-neutral")
        require(rubric.get("requires_method_relation_locator") is False, f"{case.get('case_id')} primary rubric requires a relation locator")
        require(rubric.get("requires_method_only_source_path") is False, f"{case.get('case_id')} primary rubric requires a METHOD-only path")
        require(rubric.get("requires_source_locator") is False, f"{case.get('case_id')} primary rubric requires a source locator")
        require(not primary_text_has_locator_gate(rubric), f"{case.get('case_id')} primary rubric contains a locator/citation gate")

    secondary = criteria.get("secondary_endpoint", {})
    require(secondary.get("name") == "METHOD_TRACE_USE_SUCCESS", "secondary endpoint is not METHOD_TRACE_USE_SUCCESS")
    require(secondary.get("affects_primary_endpoint") is False, "method-trace endpoint affects primary scoring")
    domains = criteria.get("domains", {})
    require(set(domains) == {"FACTUAL_FIDELITY", "EVIDENCE_BOUNDARY", "DECISION_QUALITY", "REFERENCE_INTEGRATION"}, "secondary domain set differs")
    require(all(domains[name].get("scale") == [0, 1, 2] and domains[name].get("descriptive_only") is True for name in domains), "the four 0–2 domains are not secondary descriptive measures")

    require(outcome.get("primary_endpoint") == "TARGET_DECISION_SUCCESS" and outcome.get("condition_neutral") is True, "outcome rule does not use the condition-neutral endpoint")
    require(outcome.get("outputs_present_at_freeze") is False, "outcome rule says outputs existed at freeze")
    require(outcome.get("successors_launched") is False and outcome.get("evaluators_launched") is False, "a launch is recorded in the preregistration")
    require(outcome.get("condition_map_released") is False and outcome.get("runtime_selected_by_task") is False, "map release/runtime selection is recorded")
    definitions = outcome.get("definitions", {})
    require(definitions.get("M") == "METHOD TARGET_DECISION_SUCCESS for the matched case family and replicate", "M definition differs")
    require(definitions.get("L") == "LINKLESS_METHOD_CONTROL TARGET_DECISION_SUCCESS for the matched case family and replicate", "L definition differs")
    require(definitions.get("F") == "FACTS_ONLY TARGET_DECISION_SUCCESS for the matched case family and replicate", "F definition differs")
    require(definitions.get("S") == "SKILL_ONLY TARGET_DECISION_SUCCESS for the matched case family and replicate", "S definition differs")
    require(definitions.get("METHOD_LINKLESS_WIN") == "M and not L", "METHOD_LINKLESS_WIN formula differs")
    require(definitions.get("METHOD_CONTRAST_SUCCESS") == "M and not L and (not F or not S)", "METHOD_CONTRAST_SUCCESS formula differs")
    require(definitions.get("FAMILY_DEPENDENCY_REPLICATED") == "METHOD_CONTRAST_SUCCESS in >=2 of 3 replicates", "family replication formula differs")
    require(outcome.get("case_families") == 6 and outcome.get("conditions") == 4 and outcome.get("replicates_per_condition") == 3, "frozen design counts differ")
    require(outcome.get("matched_contrasts_per_evaluator") == 18 and outcome.get("records_per_evaluator") == 72, "frozen denominator differs")
    disposition = outcome.get("benchmark_disposition", {})
    supported = disposition.get("SUPPORTED", {}).get("both_evaluators_must_independently_meet_all", [])
    partial = disposition.get("PARTIAL", {}).get("applies_only_if_SUPPORTED_not_met_and_both_evaluators_independently_meet_all", [])
    require(any("METHOD TARGET_DECISION_SUCCESS >=16/18" in item for item in supported), "SUPPORTED threshold does not use primary endpoint")
    require(any("FAMILY_DEPENDENCY_REPLICATED in >=5/6 families" in item for item in supported), "SUPPORTED family threshold differs")
    require(any("METHOD_LINKLESS_WIN in all three replicates for >=4/6 families" in item for item in supported), "SUPPORTED direct-win threshold differs")
    require(any("METHOD TARGET_DECISION_SUCCESS >=14/18" in item for item in partial), "PARTIAL threshold does not use primary endpoint")
    require(any("FAMILY_DEPENDENCY_REPLICATED in >=3/6 families" in item for item in partial), "PARTIAL family threshold differs")
    require(any("METHOD_LINKLESS_WIN in >=10/18" in item for item in partial), "PARTIAL direct-win threshold differs")


def check_case_controls(targets: dict) -> None:
    case_root = TASK / "benchmark" / "case-families"
    conditions_root = TASK / "benchmark" / "conditions"
    control_root = TASK / "benchmark" / "control-equivalence"
    require(sorted(p.name for p in case_root.iterdir() if p.is_dir()) == CASES, "case-family set is not exactly CASE01..CASE06")
    for condition in CONDITIONS:
        files = sorted((conditions_root / condition).glob("CASE*.md"))
        require([p.stem for p in files] == CASES, f"{condition} does not contain exactly six cases")

    target_by_case = {item["case_id"]: item for item in targets["cases"]}
    require(set(target_by_case) == set(CASES), "sealed target case set differs")
    for case in CASES:
        facts_path = case_root / case / "facts.md"
        facts = facts_path.read_bytes()
        provenance = read_json(case_root / case / "provenance.json")
        require(provenance.get("facts_sha256") == sha(facts), f"facts provenance hash mismatch for {case}")

        method_text = (conditions_root / "METHOD" / f"{case}.md").read_text(encoding="utf-8")
        linkless_text = (conditions_root / "LINKLESS_METHOD_CONTROL" / f"{case}.md").read_text(encoding="utf-8")
        method_atoms = atom_block(method_text, case, "METHOD")
        linkless_atoms = atom_block(linkless_text, case, "LINKLESS_METHOD_CONTROL")
        # Hard gate 3: atoms have identical bytes.
        require(method_atoms == linkless_atoms, f"METHOD/LINKLESS atom blocks differ for {case}")
        atom_lines = re.findall(rb"^\[A\d+\].*$", method_atoms, re.M)
        require(len(atom_lines) == 7, f"{case} must have seven stable atoms")

        method_relations = relation_rows(method_text)
        linkless_relations = relation_rows(linkless_text)
        require(list(method_relations) == [f"R{i:02d}" for i in range(1, 6)], f"METHOD relation set/order differs for {case}")
        target = target_by_case[case]
        cut_ids = set(target.get("decisive_relation_ids", []))
        require(cut_ids == EXPECTED_CUTS[case], f"{case} decisive relation set differs from preregistration")
        signatures = target.get("decisive_relation_signatures", [])
        signature_set = {(item.get("from_id"), item.get("relation_type"), item.get("to_id")) for item in signatures}
        require(len(signature_set) == len(cut_ids) and signature_set == {(method_relations[rid]["source"], method_relations[rid]["type"], method_relations[rid]["target"]) for rid in cut_ids}, f"{case} decisive signatures do not match the sealed relations")
        retained_ids = [rid for rid in method_relations if rid not in cut_ids]
        require(list(linkless_relations) == retained_ids, f"LINKLESS relation cut or retained relation set differs for {case}")
        for rid in retained_ids:
            require(linkless_relations[rid]["line"] == method_relations[rid]["line"], f"retained relation {rid} changed for {case}")
        # Hard gate 4: the deleted structured relation cannot survive under another ID.
        for rid, row in linkless_relations.items():
            signature = (row["source"], row["type"], row["target"])
            require(signature not in signature_set, f"{case} removed relation signature survives as {rid}")
        note = (control_root / f"{case}-control-equivalence-note.md").read_text(encoding="utf-8")
        proof_path = control_root / f"{case}-ambiguity-proof.md"
        require(proof_path.is_file(), f"ambiguity proof missing for {case}")  # Hard gate 6
        proof = proof_path.read_text(encoding="utf-8")
        require("TWO_WAY_AMBIGUITY_DEMONSTRATED=YES" in proof, f"two-way ambiguity is not asserted for {case}")
        require("FACTS" in proof and "atoms" in proof.casefold() and "retained" in proof.casefold(), f"{case} proof omits facts/atoms/retained-relations basis")
        require(all(rid in proof for rid in cut_ids), f"{case} ambiguity proof omits a missing decisive relation ID")
        section = re.search(r"## Two materially different licensed actions(.*?)(?:\n## |\Z)", proof, re.S)
        require(section is not None, f"licensed-alternatives section missing for {case}")
        alternatives = re.findall(r"^\d+\. (.+)$", section.group(1), re.M)
        # Hard gate 7: two licensed alternatives must be materially distinct by their action terms.
        require(len(alternatives) >= 2, f"{case} ambiguity proof names fewer than two possibilities")
        left = normalized_tokens(alternatives[0]); right = normalized_tokens(alternatives[1])
        union = left | right
        similarity = len(left & right) / len(union) if union else 1.0
        require(len(left.symmetric_difference(right)) >= 2 and similarity < 0.82, f"{case} alternatives are not materially distinct by action wording")
        note_lower = note.casefold()
        require("removed decisive relation" in note_lower or "complete removed decision-bearing relation set" in note_lower, f"control note does not name the removed relation for {case}")
        for rid in cut_ids:
            require(rid in note, f"control note omits removed relation {rid} for {case}")

        skill_text = (conditions_root / "SKILL_ONLY" / f"{case}.md").read_text(encoding="utf-8")
        require(re.search(r"^\d+\. \[S01\]", skill_text, re.M) is not None, f"stable skill source locators missing for {case}")
        phrases = target.get("atom_forbidden_phrases", [])
        require(len(phrases) >= 3, f"{case} target-bearing atom phrase guard is missing/incomplete")
        lower_atoms = method_atoms.decode("utf-8").casefold()
        for phrase in phrases:
            require(str(phrase).casefold() not in lower_atoms, f"target-bearing wording duplicated in {case} atoms: {phrase}")
        # Hard gate 5: catch common target disposition forms even if the phrase list is incomplete.
        generic_disposition_patterns = [
            r"\bdisposition record\b",
            r"\bwithhold\s+(?:the\s+)?(?:purge|route|action|feed|procedure)\b",
            r"\bapply\s+(?:revision|procedure|v\d+)\b",
            r"\breconcile\s+(?:the\s+)?(?:key|request)\s+first\b",
            r"\brequest\s+.+\s+and\s+(?:remain|keep)\s+unresolved\b",
            r"\broute\s+.+\s+to\s+(?:procedure|station)\s+[a-z0-9]+\b",
            r"\bdo\s+not\s+.+\s+until\s+terminal\b",
        ]
        for pattern in generic_disposition_patterns:
            require(not re.search(pattern, lower_atoms), f"target-bearing disposition pattern duplicated in {case} atoms: {pattern}")
        for phrase in target.get("skill_forbidden_target_phrases", []):
            require(str(phrase).casefold() not in skill_text.casefold(), f"target-bearing wording leaked into {case} SKILL record: {phrase}")

    # Hard gate 5 human review companion: six rows, three explicit NO leakage calls and YES ambiguity each.
    review = (TASK / "validation" / "CONTROL-VALIDITY-REVIEW.md").read_text(encoding="utf-8")
    rows = [line for line in review.splitlines() if re.match(r"^\| CASE\d\d \|", line)]
    require(len(rows) == 6, "human control-validity review does not have exactly six case rows")
    for case, line in zip(CASES, rows):
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        require(cells[0] == case and len(cells) == 8, f"human review table row malformed for {case}")
        require(all(cells[index].startswith("No —") for index in (3, 4, 5)), f"human review reports leakage or omits a reason for {case}")
        require(cells[7] == "YES", f"human review does not demonstrate two-way ambiguity for {case}")


def check_packet_secrecy(targets: dict) -> None:
    prompt_path = TASK / "benchmark" / "neutral-task-prompt.md"
    prompt_bytes = prompt_path.read_bytes()
    prompt_hash = sha(prompt_bytes)
    prompt_text = prompt_bytes.decode("utf-8")
    require(not re.search(r"FACTS_ONLY|SKILL_ONLY|LINKLESS_METHOD_CONTROL|\bMETHOD\b|condition-map|sealed-r[02]", prompt_text), "neutral prompt exposes condition or evaluator labels")
    schema = TASK / "benchmark" / "successor-output-r0.1.json"
    task207_schema = ROOT / "ignition/reports/evaluations/ignition-207-prompt-neutral-skill-method-disentanglement-r0/packets/PKT-B6092E/output-schema.json"
    require(schema.read_bytes() == task207_schema.read_bytes(), "Task207 output schema was not reused byte-for-byte")

    future = TASK / "future-tasks"
    index = read_json(future / "FUTURE-TASK-INDEX.json")
    sealed = read_json(TASK / "evaluator" / "sealed-r2" / "condition-map.json")
    require(index.get("schema_version") == "ignition-217-future-task-index-r2", "future-task index is not R2")
    require(index.get("successors_authorized_or_launched") is False, "future-task index authorizes or records a launch")
    require(index.get("task_count") == 12 and len(index.get("tasks", [])) == 12, "future task index is not 12 entries")
    manifests = sorted((future / "manifests").glob("*.json"))
    payloads = sorted((future / "payloads").glob("*.md"))
    require(len(manifests) == 12 and len(payloads) == 12, "expected twelve R2 manifests and payloads")
    require(sealed.get("schema_version") == "ignition-217-sealed-condition-map-r2", "wrong sealed map schema")
    require(sealed.get("sealed") is True and sealed.get("successors_may_read") is False and sealed.get("released") is False, "condition map is not sealed/unreleased")
    entries = sealed.get("entries", [])
    require(len(entries) == 12 and {entry["condition"] for entry in entries} == set(CONDITIONS), "sealed map condition set/count differs")
    require(all(sum(1 for entry in entries if entry["condition"] == condition) == 3 for condition in CONDITIONS), "sealed map does not have three tasks per condition")
    entry_by_id = {entry["future_task_id"]: entry for entry in entries}
    require({row["future_task_id"] for row in index["tasks"]} == set(entry_by_id), "opaque index and sealed map task IDs differ")
    require({row["packet_id"] for row in index["tasks"]} == {entry["packet_id"] for entry in entries}, "opaque index and sealed map packet IDs differ")

    prompt_hashes: set[str] = set()
    orders_by_replicate: dict[int, set[tuple[str, ...]]] = {1: set(), 2: set(), 3: set()}
    payload_sources_by_condition: dict[str, set[str]] = {condition: set() for condition in CONDITIONS}
    manifest_label_patterns = ["FACTS_ONLY", "SKILL_ONLY", "METHOD", "LINKLESS_METHOD_CONTROL"]
    for manifest_path in manifests:
        manifest = read_json(manifest_path)
        require(manifest.get("schema_version") == "ignition-217-future-task-manifest-r2", f"manifest is not R2: {manifest_path.name}")
        future_id = manifest.get("future_task_id")
        map_entry = entry_by_id.get(future_id)
        require(map_entry is not None and manifest.get("packet_id") == map_entry["packet_id"], f"manifest does not match sealed map: {manifest_path.name}")
        # Hard gate 9: dispatch metadata cannot expose a condition label.
        require(not any(key in manifest for key in ("condition", "replicate", "case_order")), f"manifest exposes condition metadata: {manifest_path.name}")
        manifest_text = json.dumps(manifest, ensure_ascii=False)
        require(not any(label in manifest_text for label in manifest_label_patterns), f"manifest exposes a condition label: {manifest_path.name}")
        require(manifest.get("conversation_replication_unit") is True and manifest.get("fresh_conversation_required") is True, "fresh independent conversation requirement missing")
        require(manifest.get("prompt_sha256") == prompt_hash, "neutral prompt hash differs across manifests")
        require(manifest.get("prompt_path") == "ignition/reports/evaluations/ignition-217-method-dependency-benchmark-r0/benchmark/neutral-task-prompt.md", "manifest prompt path differs")
        prompt_hashes.add(manifest["prompt_sha256"])
        require(manifest.get("output_schema_sha256") == sha(schema.read_bytes()), "output schema hash mismatch")
        allow = manifest.get("read_allowlist", [])
        require(len(allow) == 3, "successor allowlist must expose exactly prompt, payload, and schema")
        require({item["path"] for item in allow} == {manifest["prompt_path"], manifest["payload_path"], manifest["output_schema_path"]}, "successor allowlist contains a non-prompt/payload/schema path")
        require(all("evaluator/" not in item["path"] and "targets" not in item["path"] and "condition-map" not in item["path"] for item in allow), "successor allowlist exposes sealed evaluation data")
        for item in allow:
            require(sha((ROOT / item["path"]).read_bytes()) == item["sha256"], f"read-allowlist hash mismatch: {item['path']}")

        payload_path = ROOT / manifest["payload_path"]
        payload_bytes = payload_path.read_bytes()
        payload = payload_bytes.decode("utf-8")
        require(sha(payload_bytes) == manifest.get("payload_sha256") == map_entry.get("payload_sha256"), f"payload hash mismatch: {payload_path.name}")
        # Hard gate 9 also covers the successor-visible packet itself.
        require(not re.search(r"FACTS_ONLY|SKILL_ONLY|LINKLESS_METHOD_CONTROL|\bMETHOD\b|condition-map|sealed-r[02]", payload), f"payload exposes an exact condition/evaluator label: {payload_path.name}")
        order = tuple(re.findall(r"^## Record (CASE\d\d)$", payload, re.M))
        require(len(order) == 6 and set(order) == set(CASES), f"packet case set invalid: {payload_path.name}")
        require(list(order) == map_entry["case_order"], f"packet order differs from sealed map: {payload_path.name}")
        orders_by_replicate[map_entry["replicate"]].add(order)
        payload_sources_by_condition[map_entry["condition"]].add(json.dumps(manifest["case_source_sha256"], sort_keys=True))
        for case in CASES:
            facts = (TASK / "benchmark" / "case-families" / case / "facts.md").read_bytes()
            supplement = (TASK / "benchmark" / "conditions" / map_entry["condition"] / f"{case}.md").read_bytes()
            expected_hash = sha(facts + b"\n\n" + supplement)
            require(manifest["case_source_sha256"].get(case) == expected_hash, f"case source hash mismatch for {case} in {manifest_path.name}")
            require(f"Source SHA-256: {expected_hash}" in payload, f"packet omits displayed source hash for {case}")
            require(facts.decode("utf-8") in payload and supplement.decode("utf-8") in payload, f"packet content differs from its source files for {case}")

    require(prompt_hashes == {prompt_hash}, "neutral prompt differs across manifests")  # Hard gate 8
    require(all(len(orders_by_replicate[replicate]) == 1 for replicate in (1, 2, 3)), "matched conditions do not share order within replicate")
    require(len({next(iter(orders_by_replicate[replicate])) for replicate in (1, 2, 3)}) == 3, "replicates do not use three distinct case orders")
    require(all(len(payload_sources_by_condition[condition]) == 1 for condition in CONDITIONS), "condition semantics differ across its three replicates")


def check_no_outputs(targets: dict, outcome: dict) -> None:
    # The output-schema JSON is an interface contract, not an output record.
    schema_rel = "benchmark/successor-output-r0.1.json"
    require((TASK / schema_rel).is_file(), "successor output schema missing")
    require(outcome.get("outputs_present_at_freeze") is False, "preregistration says outputs were present")
    require(targets.get("successors_launched") is False and targets.get("evaluators_launched") is False, "sealed targets record a launch")
    for dirname in ("outputs", "results", "successor-runs", "evaluator-runs"):
        for path in TASK.rglob(dirname):
            if path.is_dir():
                require(not any(child.is_file() for child in path.rglob("*")), f"output/run directory is nonempty: {path.relative_to(TASK)}")
    output_name = re.compile(r"(?:successor|evaluator).*?(?:response|result|output)(?:s)?(?:[._-]|$)", re.I)
    for path in TASK.rglob("*"):
        if not path.is_file() or path.relative_to(TASK).as_posix() == schema_rel:
            continue
        require(not output_name.search(path.name), f"Successor/Evaluator output-like artifact exists: {path.relative_to(TASK)}")


def check_repository_closure_and_freeze(report: str) -> None:
    changed = subprocess.check_output(["git", "diff", "--name-only", BASE, "HEAD"], cwd=ROOT, text=True).splitlines()
    generated_knowledge_paths = {
        path for path in changed
        if path == SOURCE_FIRST_SEEN_REL
        or path.startswith("ignition/KNOWLEDGE/")
        or path.startswith("ignition/data/governance/knowledge-experience/")
    }
    allowed_external = {PATH_MANIFEST_REL} | GENERATED_NONFUNCTION_OUTPUTS | GENERATED_HUMAN_RESULTS_OUTPUTS | GENERATED_SELF_CORRECTION_OUTPUTS | generated_knowledge_paths
    require(changed and all(path.startswith(TASK_REL.as_posix() + "/") or path in allowed_external for path in changed), "changes extend outside Task217 and prescribed generated projections")
    require(not any(path.startswith("ignition/reports/evaluations/ignition-207-") for path in changed), "frozen Task207 subtree changed")
    knowledge_manifest = read_json(ROOT / KNOWLEDGE_EXPERIENCE_MANIFEST_REL)
    generated_knowledge_outputs = {"ignition/" + path for path in knowledge_manifest.get("generated_outputs", {})}
    expected_knowledge_paths = generated_knowledge_outputs | {SOURCE_FIRST_SEEN_REL, KNOWLEDGE_EXPERIENCE_MANIFEST_REL}
    require(generated_knowledge_paths <= expected_knowledge_paths, "knowledge-experience external path is not declared by its generated manifest")

    path_manifest_path = ROOT / PATH_MANIFEST_REL
    path_rows = [json.loads(line) for line in path_manifest_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    path_row_by_name = {row["path"]: row for row in path_rows}
    task_paths = subprocess.check_output(["git", "ls-files", TASK_REL.as_posix()], cwd=ROOT, text=True).splitlines()
    require(task_paths, "no tracked Task217 paths found")
    require(all(path in path_row_by_name and path_row_by_name[path].get("category") == "EVALUATION_EVIDENCE" for path in task_paths), "Task217 path missing/misclassified in generated path index")
    task_rows = [row for row in path_rows if row.get("path", "").startswith(TASK_REL.as_posix() + "/")]
    require(len(task_rows) == len(task_paths), "generated path index Task217 entry count differs from tracked inventory")

    freeze_path = TASK / "freeze" / "FREEZE-MANIFEST.json"
    sidecar_path = TASK / "freeze" / "FREEZE-MANIFEST.sha256"
    freeze = read_json(freeze_path)
    external = freeze.get("external_generated_path_index", {})
    require(external.get("path") == PATH_MANIFEST_REL, "external generated path-index reference missing")
    require(external.get("sha256") == sha(path_manifest_path.read_bytes()), "external path-index hash mismatch")
    require(external.get("task217_entry_count") == len(task_paths) and external.get("category") == "EVALUATION_EVIDENCE", "external Task217 path-index count/category mismatch")
    human_results = freeze.get("external_generated_human_results", {})
    human_result_files = human_results.get("files", [])
    human_result_hashes = {item.get("path"): item.get("sha256") for item in human_result_files}
    require(set(human_result_hashes) == GENERATED_HUMAN_RESULTS_OUTPUTS, "external generated human-results inventory differs")
    require(human_results.get("generator") == "python3 tools/governance/build_human_results.py", "external generated human-results generator differs")
    require(human_results.get("new_task217_source_documents") == 80, "external generated human-results Task217 source count differs")
    for path, expected in human_result_hashes.items():
        require((ROOT / path).is_file() and sha((ROOT / path).read_bytes()) == expected, f"external generated human-results SHA-256 mismatch: {path}")
    self_correction = freeze.get("external_generated_self_correction", {})
    self_correction_files = self_correction.get("files", [])
    self_correction_hashes = {item.get("path"): item.get("sha256") for item in self_correction_files}
    require(set(self_correction_hashes) == GENERATED_SELF_CORRECTION_OUTPUTS, "external generated self-correction inventory differs")
    require(self_correction.get("generator") == "python3 tools/governance/run_self_correction.py", "self-correction generator record differs")
    for path, expected in self_correction_hashes.items():
        require((ROOT / path).is_file() and sha((ROOT / path).read_bytes()) == expected, f"external generated self-correction SHA-256 mismatch: {path}")
    nonfunction_files = freeze.get("external_generated_nonfunction_claim_files", [])
    nonfunction_hashes = {item.get("path"): item.get("sha256") for item in nonfunction_files}
    require(set(nonfunction_hashes) == GENERATED_NONFUNCTION_OUTPUTS, "external generated nonfunction-claim inventory differs")
    for path, expected in nonfunction_hashes.items():
        require((ROOT / path).is_file() and sha((ROOT / path).read_bytes()) == expected, f"external generated nonfunction-claim SHA-256 mismatch: {path}")
    knowledge = freeze.get("external_generated_knowledge_experience", {})
    knowledge_files = knowledge.get("files", [])
    knowledge_hashes = {item.get("path"): item.get("sha256") for item in knowledge_files}
    require(set(knowledge_hashes) == generated_knowledge_paths, "external generated knowledge-experience inventory differs from changed paths")
    require(knowledge.get("source_first_seen_path") == SOURCE_FIRST_SEEN_REL, "source-first-seen registry reference differs")
    require(knowledge.get("new_task217_source_documents") == 80, "knowledge-experience Task217 source count differs")
    require(knowledge.get("generators") == ["python3 tools/governance/gen_source_first_seen.py", "python3 tools/governance/build_knowledge_experience.py"], "knowledge-experience generator record differs")
    for path, expected in knowledge_hashes.items():
        require((ROOT / path).is_file() and sha((ROOT / path).read_bytes()) == expected, f"external generated knowledge-experience SHA-256 mismatch: {path}")
    first_seen_hash = sha((ROOT / SOURCE_FIRST_SEEN_REL).read_bytes())
    require(knowledge_manifest.get("source_inputs", {}).get("data/governance/knowledge-experience/source-first-seen.json") == first_seen_hash, "knowledge-experience manifest source-first-seen hash differs")
    output_hashes = knowledge_manifest.get("generated_outputs", {})
    for path, expected in knowledge_hashes.items():
        if path == SOURCE_FIRST_SEEN_REL or path == KNOWLEDGE_EXPERIENCE_MANIFEST_REL:
            continue
        relative = path.removeprefix("ignition/")
        require(output_hashes.get(relative) == expected, f"knowledge-experience manifest output hash differs: {path}")
    excluded = {freeze_path.relative_to(ROOT).as_posix(), sidecar_path.relative_to(ROOT).as_posix()}
    actual_files = {path.relative_to(ROOT).as_posix() for path in TASK.rglob("*") if path.is_file()} - excluded
    inventory = {item["path"]: item["sha256"] for item in freeze.get("files", [])}
    require(set(inventory) == actual_files, "freeze inventory does not cover exactly all Task217 artifacts except itself/sidecar")
    require(freeze.get("file_count") == len(inventory), "freeze file count differs")
    for path, expected in inventory.items():
        require(sha((ROOT / path).read_bytes()) == expected, f"freeze SHA-256 mismatch: {path}")
    digest = sha(freeze_path.read_bytes())
    expected_sidecar = f"{digest}  {freeze_path.relative_to(ROOT).as_posix()}\n"
    require(sidecar_path.read_text(encoding="utf-8") == expected_sidecar, "freeze manifest sidecar mismatch")
    status = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
    require(status == "", "worktree is not clean")

    report_lines = set(line.strip() for line in report.splitlines())
    required_report_lines = {
        "PRIMARY_ENDPOINT=TARGET_DECISION_SUCCESS",
        "PRIMARY_ENDPOINT_CONDITION_NEUTRAL=true",
        "METHOD_RELATION_CITATION_REQUIRED_FOR_PRIMARY=false",
        "METHOD_TRACE_USE_ENDPOINT=SECONDARY",
        "METHOD_LINKLESS_ATOMS_BYTE_IDENTICAL_PER_CASE=true",
        "LINKLESS_TWO_WAY_AMBIGUITY_PROVEN=6/6",
        "CASE_FAMILIES=6",
        "CONDITIONS=4",
        "FUTURE_SUCCESSORS=12",
        "SUCCESSORS_LAUNCHED=0",
        "EVALUATORS_LAUNCHED=0",
        "CONDITION_MAP_RELEASED=false",
        "RUNTIME_CHOSEN_BY_TASK=false",
        "REPOSITORY_PATH_ACCOUNTING=PASS",
        "ARCHITECTURE_PAGES=PASS",
        "FOUNDATION_VALIDATION=PASS",
        "R1_NOT_AUTHORIZED",
        "CROSS_MODEL_NOT_AUTHORIZED",
        "PR_STATE=OPEN_DRAFT_UNMERGED",
    }
    require(required_report_lines <= report_lines, "validation report omits required final R1 status lines")
    print(f"TASK217_R1_VALIDATION_PASS tracked_paths={len(task_paths)} task_files={len(inventory)} change_paths={len(changed)}")


def main() -> int:
    require(TASK.is_dir(), "Task217 subtree missing")
    targets = read_json(TASK / "evaluator" / "sealed-r2" / "targets.json")
    criteria = read_json(TASK / "evaluator" / "criteria-r2.json")
    outcome = read_json(TASK / "evaluator" / "preregistered-outcome-rule-r2.json")
    require(len(targets.get("cases", [])) == 6, "sealed target count differs from six")
    check_primary_endpoint(criteria, targets, outcome)
    check_case_controls(targets)
    check_packet_secrecy(targets)
    check_no_outputs(targets, outcome)  # Hard gate 10
    report_path = TASK / "validation" / "VALIDATION-REPORT.md"
    check_repository_closure_and_freeze(report_path.read_text(encoding="utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
