#!/usr/bin/env python3
"""Non-mutating exhaustive Task227 policy diagnostics for Task228.

Inputs are only the six immutable Task227 raw reference policies, the exact
Task227 schema/validator, and the family's frozen M0/E1 source files. The
official validator is run unchanged to cross-check each first-failure result.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[5]
TASK227 = ROOT / "ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0"
TASK228 = ROOT / "ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0"
PACKET_DEFAULT = Path("/tmp/ignition-227-component-isolation-r0/FINAL-OWNER-PACKET")
VALIDATOR_PATH = TASK227 / "tools/validate_policy.py"
SCHEMA_PATH = TASK227 / "reference/policy-schema.json"
FAMILIES = {
    "REF-01": "FAMILY01", "REF-02": "FAMILY01",
    "REF-03": "FAMILY02", "REF-04": "FAMILY02",
    "REF-05": "FAMILY03", "REF-06": "FAMILY03",
}
CATEGORIES = {
    "SCHEMA_JSON": "JSON Schema, required-field, or type failure",
    "UNSUPPORTED_OR_DANGLING_IDENTIFIER": "Duplicate, unsupported, or dangling identifier",
    "SELECTOR_ACTION_ONE_TO_ONE": "Selector/action one-to-one mapping",
    "SELECTOR_ACTION_CONDITION_EQUALITY": "Selector/action condition equality",
    "LICENSED_REGION_RULE_MAPPING": "Licensed-region/rule mapping",
    "LICENSED_REGION_CONDITION_EQUALITY": "Licensed-region exact-condition equality",
    "REGION_COVERAGE_COMPLEMENT": "Region coverage/complement semantics",
    "EVIDENCE_REFERENCE_INTEGRITY": "Evidence-reference integrity",
    "FAMILY_SOURCE_LOCATOR_BINDING": "Family source-locator binding",
    "PRESERVATION_MODE_SEMANTICS": "Preservation-mode semantics",
    "M0_RETIREMENT_PROHIBITED": "Prohibited M0 retirement",
    "FALLBACK_UNIVERSALITY": "Fallback universality",
    "STOP_CONDITION_STRUCTURE": "Stop-condition structure",
    "TYPED_PARAMETER_INPUT_MISMATCH": "Typed parameter/input mismatch, including selector-condition typing",
    "SCOPE_CEILING_REGION_LICENSING": "Scope-ceiling region licensing",
    "PROVENANCE_TYPED_LINK_COVERAGE": "Provenance completeness and typed-link coverage",
    "OTHER_VALIDATOR_SPECIFIC": "Other validator-specific constraint",
}
CATEGORY_ORDER = list(CATEGORIES)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_validator():
    spec = importlib.util.spec_from_file_location("frozen_task227_validate_policy", VALIDATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load exact frozen Task227 validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    manifest = json.loads((TASK227 / "freeze/freeze-manifest.json").read_text(encoding="utf-8"))
    frozen = {x["path"]: x["sha256"] for x in manifest["frozen_files"]}
    for path in (VALIDATOR_PATH, SCHEMA_PATH):
        rel = path.relative_to(ROOT).as_posix()
        if frozen.get(rel) != sha256(path.read_bytes()):
            raise RuntimeError(f"frozen Task227 source hash mismatch: {rel}")
    for item in manifest.get("external_m0_e1_inputs", []):
        source = ROOT / item["path"]
        if not source.is_file() or sha256(source.read_bytes()) != item["sha256"]:
            raise RuntimeError(f"frozen Task220 M0/E1 input hash mismatch: {item['path']}")
    module.verify_schema()
    return module


def official_first_failure(policy_path: Path, family: str) -> str | None:
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR_PATH), "--family", family, str(policy_path)],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    combined = proc.stdout + "\n" + proc.stderr
    found = re.search(r"TASK227_POLICY_INVALID: (.+)", combined)
    if found:
        return found.group(1).strip()
    if proc.returncode == 0 and "TASK227_POLICY_VALID=PASS" in combined:
        return None
    return "UNPARSEABLE_OFFICIAL_VALIDATOR_RESULT: " + combined.strip()


def diagnose(ref: str, packet: Path, official) -> dict[str, Any]:
    policy_path = packet / "reference-m1" / f"{ref}.json"
    raw = policy_path.read_bytes()
    before_hash = sha256(raw)
    policy = json.loads(raw)
    family = FAMILIES[ref]
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    issues: list[dict[str, Any]] = []

    def add(rule_id: str, category: str, location: str, detail: str) -> None:
        issues.append({
            "rule_id": rule_id, "category": category,
            "location": location, "detail": detail,
        })

    def exact(value: Any, keys: set[str], where: str) -> None:
        if isinstance(value, dict) and set(value) != keys:
            add("EXACT_OBJECT_KEYS", "SCHEMA_JSON", where,
                f"keys mismatch: expected {sorted(keys)} got {sorted(value)}")

    def refs(values: Any, where: str, evidence_by_id: dict[str, dict], source_type: str | None = None) -> None:
        if not isinstance(values, list):
            return
        for value in values:
            if value not in evidence_by_id:
                add("EVIDENCE_REF_KNOWN", "EVIDENCE_REFERENCE_INTEGRITY", where,
                    f"{where} references unknown evidence {value}")
            elif source_type and evidence_by_id[value].get("source_type") != source_type:
                add("PRESERVED_RULE_SOURCE_M0", "PRESERVATION_MODE_SEMANTICS", where,
                    f"{where} must reference {source_type}")

    schema_errors = sorted(
        official.Draft202012Validator(schema).iter_errors(policy),
        key=lambda e: (list(map(str, e.absolute_path)), e.message),
    )
    for error in schema_errors:
        add("SCHEMA_DRAFT202012", "SCHEMA_JSON",
            "/".join(map(str, error.absolute_path)) or "$", error.message)

    # The following checks mirror the frozen validator's guard sequence, but
    # append failures and continue over the original bytes instead of exiting.
    top_keys = {"policy_id", "evidence_basis", "selector", "applicability",
                "action_table", "preserved_rules", "fallback", "stop_conditions",
                "scope_ceiling", "provenance"}
    exact(policy, top_keys, "$")
    evidence = policy.get("evidence_basis", [])
    evidence_by_id: dict[str, dict] = {}
    evidence_ids = []
    if isinstance(evidence, list):
        for i, item in enumerate(evidence):
            where = f"evidence_basis[{i}]"
            if not isinstance(item, dict):
                continue
            exact(item, {"evidence_id", "source_type", "source_locator", "supports", "claim_type"}, where)
            eid = item.get("evidence_id")
            if isinstance(eid, str):
                evidence_ids.append(eid)
                if eid not in evidence_by_id:
                    evidence_by_id[eid] = item
            if item.get("source_type") not in {"M0", "E1"}:
                add("EVIDENCE_SOURCE_TYPE", "EVIDENCE_REFERENCE_INTEGRITY", where, "source_type must be M0 or E1")
            if item.get("claim_type") not in {"observed", "derived", "method_rule"}:
                add("EVIDENCE_CLAIM_TYPE", "EVIDENCE_REFERENCE_INTEGRITY", where, "claim_type unsupported")
    if len(evidence_ids) != len(set(evidence_ids)):
        add("EVIDENCE_IDS_UNIQUE", "UNSUPPORTED_OR_DANGLING_IDENTIFIER", "evidence_basis",
            "evidence IDs must be unique")

    selector = policy.get("selector", {})
    if isinstance(selector, dict):
        exact(selector, {"required_inputs", "rule"}, "selector")
    inputs = selector.get("required_inputs", []) if isinstance(selector, dict) else []
    input_by_id: dict[str, dict] = {}
    input_ids = []
    if isinstance(inputs, list):
        for i, item in enumerate(inputs):
            where = f"required_inputs[{i}]"
            if not isinstance(item, dict):
                continue
            exact(item, {"input_id", "description", "value_type", "unit", "source_refs"}, where)
            iid = item.get("input_id")
            if isinstance(iid, str):
                input_ids.append(iid)
                input_by_id.setdefault(iid, item)
            refs(item.get("source_refs"), f"input {iid} source_refs", evidence_by_id)
            if item.get("value_type") not in {"number", "string", "boolean"}:
                add("INPUT_VALUE_TYPE", "TYPED_PARAMETER_INPUT_MISMATCH", where, "input value_type unsupported")
    if len(input_ids) != len(set(input_ids)):
        add("INPUT_IDS_UNIQUE", "UNSUPPORTED_OR_DANGLING_IDENTIFIER", "selector.required_inputs",
            "input IDs must be unique")

    ops = official.OPS
    typed = official.typed

    def conditions(values: Any, where: str, allow_empty: bool = False) -> None:
        if not isinstance(values, list):
            return
        if not values and not allow_empty:
            add("CONDITIONS_NONEMPTY", "TYPED_PARAMETER_INPUT_MISMATCH", where, f"{where} must be nonempty array")
        for i, condition in enumerate(values):
            loc = f"{where}[{i}]"
            if not isinstance(condition, dict):
                continue
            exact(condition, {"input_id", "operator", "value", "unit"}, loc)
            iid = condition.get("input_id")
            if iid not in input_by_id:
                add("CONDITION_INPUT_DECLARED", "UNSUPPORTED_OR_DANGLING_IDENTIFIER", loc,
                    f"{loc} uses undeclared input {iid}")
                continue
            declared = input_by_id[iid]
            op = condition.get("operator")
            value = condition.get("value")
            kind = declared.get("value_type")
            if op not in ops:
                add("CONDITION_OPERATOR", "TYPED_PARAMETER_INPUT_MISMATCH", loc, f"{loc} has unsupported operator {op}")
                continue
            if condition.get("unit") != declared.get("unit"):
                add("CONDITION_UNIT", "TYPED_PARAMETER_INPUT_MISMATCH", loc, f"{loc} unit differs from input declaration")
            if op in {"present", "absent", "stable", "complete", "reproducible"}:
                if value is not None:
                    add("CONDITION_NULL_VALUE", "TYPED_PARAMETER_INPUT_MISMATCH", loc, f"{loc} {op} requires null value")
            elif op == "between":
                good = (kind == "number" and isinstance(value, list) and len(value) == 2
                        and all(typed(v, "number") for v in value) and value[0] <= value[1])
                if not good:
                    add("CONDITION_BETWEEN_TYPE", "TYPED_PARAMETER_INPUT_MISMATCH", loc,
                        f"{loc} between requires two ordered numbers")
            elif op in {"in", "not_in"}:
                if not isinstance(value, list) or not value or any(not typed(v, kind) for v in value):
                    add("CONDITION_ENUM_TYPE", "TYPED_PARAMETER_INPUT_MISMATCH", loc,
                        f"{loc} {op} values must match declared input type")
            elif op == "matches":
                if kind != "string" or not isinstance(value, str) or not value:
                    add("CONDITION_MATCHES_TYPE", "TYPED_PARAMETER_INPUT_MISMATCH", loc,
                        f"{loc} matches requires a nonempty string input pattern")
            else:
                if not typed(value, kind):
                    add("CONDITION_VALUE_TYPE", "TYPED_PARAMETER_INPUT_MISMATCH", loc,
                        f"{loc} value does not match declared input type {kind}")
                if op in {"lt", "lte", "gt", "gte"} and kind != "number":
                    add("CONDITION_COMPARISON_TYPE", "TYPED_PARAMETER_INPUT_MISMATCH", loc,
                        f"{loc} numeric comparison requires number input")

    rules = selector.get("rule", []) if isinstance(selector, dict) else []
    rule_by_id: dict[str, dict] = {}
    rule_ids = []
    if isinstance(rules, list):
        for i, item in enumerate(rules):
            where = f"selector.rule[{i}]"
            if not isinstance(item, dict):
                continue
            exact(item, {"rule_id", "when", "action_ref"}, where)
            rid = item.get("rule_id")
            if isinstance(rid, str):
                rule_ids.append(rid)
                rule_by_id.setdefault(rid, item)
            conditions(item.get("when"), f"{where}.when")
    if len(rule_ids) != len(set(rule_ids)):
        add("SELECTOR_IDS_UNIQUE", "UNSUPPORTED_OR_DANGLING_IDENTIFIER", "selector.rule",
            "selector rule IDs must be unique")

    actions = policy.get("action_table", [])
    action_by_id: dict[str, dict] = {}
    action_ids = []
    if isinstance(actions, list):
        for i, item in enumerate(actions):
            where = f"action_table[{i}]"
            if not isinstance(item, dict):
                continue
            exact(item, {"action_id", "when", "action", "required_report_fields", "evidence_refs"}, where)
            aid = item.get("action_id")
            if isinstance(aid, str):
                action_ids.append(aid)
                action_by_id.setdefault(aid, item)
            conditions(item.get("when"), f"action {aid}.when")
            refs(item.get("evidence_refs"), f"action {aid} evidence_refs", evidence_by_id)
            fields = item.get("required_report_fields", [])
            if isinstance(fields, list):
                for j, field in enumerate(fields):
                    loc = f"required_report_fields[{j}]"
                    if isinstance(field, dict):
                        exact(field, {"field_id", "description", "unit", "evidence_refs"}, f"{aid}.{loc}")
                        refs(field.get("evidence_refs"), f"report field {aid}[{j}] evidence_refs", evidence_by_id)
    if len(action_ids) != len(set(action_ids)):
        add("ACTION_IDS_UNIQUE", "UNSUPPORTED_OR_DANGLING_IDENTIFIER", "action_table",
            "action IDs must be unique")

    selector_action_refs = [r.get("action_ref") for r in rules if isinstance(r, dict)]
    if (len(rules) != len(actions) or len(selector_action_refs) != len(set(selector_action_refs))
            or set(selector_action_refs) != set(action_ids)):
        add("SELECTOR_ACTION_ONE_TO_ONE", "SELECTOR_ACTION_ONE_TO_ONE", "selector.rule/action_table",
            "selector and action mappings must be one-to-one")
    for rule in rules if isinstance(rules, list) else []:
        if not isinstance(rule, dict):
            continue
        aid = rule.get("action_ref")
        if aid not in action_by_id:
            add("SELECTOR_ACTION_REF_KNOWN", "UNSUPPORTED_OR_DANGLING_IDENTIFIER",
                f"selector.rule[{rule.get('rule_id')}].action_ref",
                f"unknown action reference {aid}")
        elif rule.get("when") != action_by_id[aid].get("when"):
            add("SELECTOR_ACTION_CONDITIONS_EQUAL", "SELECTOR_ACTION_CONDITION_EQUALITY",
                f"selector.rule[{rule.get('rule_id')}].when",
                f"selector/action conditions differ for {aid}")

    applicability = policy.get("applicability", {})
    if isinstance(applicability, dict):
        exact(applicability, {"licensed_region", "out_of_scope"}, "applicability")
    licensed = applicability.get("licensed_region", []) if isinstance(applicability, dict) else []
    outside = applicability.get("out_of_scope", []) if isinstance(applicability, dict) else []
    licensed_ids, outside_ids, mapped_rule_ids = [], [], []
    for i, item in enumerate(licensed if isinstance(licensed, list) else []):
        where = f"licensed_region[{i}]"
        if not isinstance(item, dict):
            continue
        exact(item, {"region_id", "conditions", "rule_refs"}, where)
        ridlist = item.get("rule_refs", [])
        conditions(item.get("conditions"), f"licensed region {item.get('region_id')}")
        if not isinstance(ridlist, list) or len(ridlist) != 1 or ridlist[0] not in rule_by_id:
            add("LICENSED_REGION_ONE_RULE", "LICENSED_REGION_RULE_MAPPING", where,
                f"licensed region {item.get('region_id')} must reference exactly one known selector rule")
        else:
            mapped_rule_ids.append(ridlist[0])
            if item.get("conditions") != rule_by_id[ridlist[0]].get("when"):
                add("LICENSED_REGION_CONDITIONS_EQUAL", "LICENSED_REGION_CONDITION_EQUALITY", where,
                    f"licensed region {item.get('region_id')} conditions differ from referenced selector rule")
        licensed_ids.append(item.get("region_id"))
    if len(mapped_rule_ids) != len(set(mapped_rule_ids)):
        add("LICENSED_RULE_MAPPING_UNIQUE", "LICENSED_REGION_RULE_MAPPING", "applicability.licensed_region",
            "licensed-region selector mapping must be unique")
    if set(mapped_rule_ids) != set(rule_ids):
        add("LICENSED_RULE_COVERAGE", "REGION_COVERAGE_COMPLEMENT", "applicability.licensed_region",
            "every selector rule must map to exactly one licensed region")

    empty_outside = []
    for i, item in enumerate(outside if isinstance(outside, list) else []):
        where = f"out_of_scope[{i}]"
        if not isinstance(item, dict):
            continue
        exact(item, {"region_id", "conditions", "fallback_ref"}, where)
        conditions(item.get("conditions"), f"out-of-scope region {item.get('region_id')}", True)
        if item.get("fallback_ref") != "fallback":
            add("OUT_OF_SCOPE_FALLBACK_REF", "UNSUPPORTED_OR_DANGLING_IDENTIFIER", where,
                f"out-of-scope region {item.get('region_id')} must route to fallback")
        if item.get("conditions") == []:
            empty_outside.append(item)
        outside_ids.append(item.get("region_id"))
    region_ids = licensed_ids + outside_ids
    if len(region_ids) != len(set(region_ids)):
        add("REGION_IDS_UNIQUE", "UNSUPPORTED_OR_DANGLING_IDENTIFIER", "applicability",
            "applicability region IDs must be unique")
    if empty_outside and len(outside) != 1:
        add("COMPLEMENT_ROW_SOLE", "REGION_COVERAGE_COMPLEMENT", "applicability.out_of_scope",
            "an empty out-of-scope condition list denotes the entire complement and must be the sole out-of-scope region")

    preserved = policy.get("preserved_rules", [])
    preserved_ids = []
    for i, item in enumerate(preserved if isinstance(preserved, list) else []):
        where = f"preserved_rules[{i}]"
        if not isinstance(item, dict):
            continue
        exact(item, {"preservation_id", "when", "baseline_action", "preservation_mode",
                     "m0_action_retired", "evidence_refs"}, where)
        pid, mode = item.get("preservation_id"), item.get("preservation_mode")
        if isinstance(pid, str):
            preserved_ids.append(pid)
        conditions(item.get("when"), f"preserved rule {pid}", True)
        if mode in {"unconditional", "selector_miss"} and item.get("when"):
            add("PRESERVATION_EMPTY_WHEN", "PRESERVATION_MODE_SEMANTICS", where,
                f"preserved rule {pid} must have an empty when list for {mode} coverage")
        if mode == "additive_coexistence" and (
            not item.get("when") or not any(r.get("when") == item.get("when")
                                            for r in rules if isinstance(r, dict))
        ):
            add("PRESERVATION_ADDITIVE_MATCH", "PRESERVATION_MODE_SEMANTICS", where,
                f"preserved rule {pid} additive_coexistence must match a selector rule condition set")
        if item.get("m0_action_retired") is not False:
            add("M0_RETIREMENT_PROHIBITED", "M0_RETIREMENT_PROHIBITED", where, "M0 retirement is prohibited")
        refs(item.get("evidence_refs"), "preserved-rule evidence_refs", evidence_by_id, "M0")
    if len(preserved_ids) != len(set(preserved_ids)):
        add("PRESERVATION_IDS_UNIQUE", "UNSUPPORTED_OR_DANGLING_IDENTIFIER", "preserved_rules",
            "preserved rule IDs must be unique")

    fallback = policy.get("fallback", {})
    if isinstance(fallback, dict):
        exact(fallback, {"when", "action", "evidence_refs"}, "fallback")
        conditions(fallback.get("when"), "fallback.when", True)
        if fallback.get("when"):
            add("FALLBACK_UNIVERSAL", "FALLBACK_UNIVERSALITY", "fallback.when",
                "fallback.when must be [] to declare unconditional coverage of every out-of-scope or unresolved input")
        refs(fallback.get("evidence_refs"), "fallback evidence refs", evidence_by_id)
    stops = policy.get("stop_conditions", [])
    stop_ids = []
    for i, item in enumerate(stops if isinstance(stops, list) else []):
        where = f"stop_conditions[{i}]"
        if not isinstance(item, dict):
            continue
        exact(item, {"stop_id", "when", "outcome", "instruction"}, where)
        sid = item.get("stop_id")
        if isinstance(sid, str):
            stop_ids.append(sid)
        conditions(item.get("when"), f"stop {sid}.when")
        if item.get("outcome") not in {"STOP", "UNSCORABLE", "RECONCILE", "REACQUIRE", "ESCALATE"}:
            add("STOP_OUTCOME", "STOP_CONDITION_STRUCTURE", where, "stop outcome invalid")
    if len(stop_ids) != len(set(stop_ids)):
        add("STOP_IDS_UNIQUE", "UNSUPPORTED_OR_DANGLING_IDENTIFIER", "stop_conditions", "stop IDs must be unique")

    ceiling = policy.get("scope_ceiling", {})
    if isinstance(ceiling, dict):
        exact(ceiling, {"licensed_claims", "not_established", "statement"}, "scope_ceiling")
    licensed_claim_ids, excluded_claim_ids, claim_ids = [], [], []
    if isinstance(ceiling, dict):
        for key, ids, allowed in (
            ("licensed_claims", licensed_claim_ids, set(licensed_ids)),
            ("not_established", excluded_claim_ids, set(region_ids)),
        ):
            claims = ceiling.get(key, [])
            for i, claim in enumerate(claims if isinstance(claims, list) else []):
                where = f"scope_ceiling.{key}[{i}]"
                if not isinstance(claim, dict):
                    continue
                exact(claim, {"claim_id", "statement", "region_refs", "evidence_refs"}, where)
                cid = claim.get("claim_id")
                ids.append(cid)
                if isinstance(cid, str):
                    claim_ids.append(cid)
                region_refs = claim.get("region_refs", [])
                if isinstance(region_refs, list) and not set(region_refs).issubset(allowed):
                    add("SCOPE_REGION_LICENSED", "SCOPE_CEILING_REGION_LICENSING", where,
                        f"scope claim {cid} has dangling or non-licensed region")
                refs(claim.get("evidence_refs"), f"scope claim {cid} evidence_refs", evidence_by_id)
    if len(claim_ids) != len(set(claim_ids)):
        add("SCOPE_CLAIM_IDS_UNIQUE", "UNSUPPORTED_OR_DANGLING_IDENTIFIER", "scope_ceiling",
            "scope claim IDs must be unique")

    type_map = {
        "selector_rule": set(rule_ids), "action": set(action_ids),
        "licensed_region": set(licensed_ids), "out_of_scope": set(outside_ids),
        "preserved_rule": set(preserved_ids), "fallback": {"fallback"},
        "stop_condition": set(stop_ids), "scope_claim": set(licensed_claim_ids),
        "scope_exclusion": set(excluded_claim_ids),
    }
    provenance = policy.get("provenance", [])
    pairs = []
    for i, item in enumerate(provenance if isinstance(provenance, list) else []):
        where = f"provenance[{i}]"
        if not isinstance(item, dict):
            continue
        exact(item, {"element_type", "element_id", "evidence_refs", "locator_detail"}, where)
        et, eid = item.get("element_type"), item.get("element_id")
        if et not in type_map or eid not in type_map.get(et, set()):
            add("PROVENANCE_TYPED_LINK", "PROVENANCE_TYPED_LINK_COVERAGE", where,
                f"unknown provenance link {et}:{eid}")
        pairs.append((et, eid))
        refs(item.get("evidence_refs"), "provenance evidence_refs", evidence_by_id)
    if len(pairs) != len(set(pairs)):
        add("PROVENANCE_LINKS_UNIQUE", "UNSUPPORTED_OR_DANGLING_IDENTIFIER", "provenance",
            "provenance IDs must be unique")
    expected = {(kind, eid) for kind, ids in type_map.items() for eid in ids}
    if not expected.issubset(set(pairs)):
        missing = sorted(expected - set(pairs), key=lambda x: (x[0], x[1]))
        add("PROVENANCE_TYPED_COVERAGE", "PROVENANCE_TYPED_LINK_COVERAGE", "provenance",
            f"provenance omits typed links: {missing}")

    # The official validator binds evidence locators by literal presence in the
    # frozen family M0/E1 files; this does not claim semantic support.
    family_root = ROOT / "ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families" / family
    m0_path, e1_path = family_root / "m0.md", family_root / "revision-evidence-e1.md"
    m0 = m0_path.read_text(encoding="utf-8")
    e1 = e1_path.read_text(encoding="utf-8")
    for item in evidence if isinstance(evidence, list) else []:
        if not isinstance(item, dict):
            continue
        source = m0 if item.get("source_type") == "M0" else e1
        locator = item.get("source_locator")
        if isinstance(locator, str) and locator not in source:
            add("FAMILY_LOCATOR_LITERAL", "FAMILY_SOURCE_LOCATOR_BINDING",
                f"evidence_basis.{item.get('evidence_id')}",
                f"source locator missing from family inputs for {item.get('evidence_id')}")

    official_first = official_first_failure(policy_path, family)
    first_diag = issues[0]["detail"] if issues else None
    first_match = first_diag == official_first
    after_hash = sha256(policy_path.read_bytes())
    return {
        "ref_id": ref, "family_id": family, "policy_path": str(policy_path),
        "policy_sha256": before_hash, "policy_sha256_after": after_hash,
        "input_unchanged": before_hash == after_hash,
        "official_first_failure": official_first,
        "diagnostic_first_failure": first_diag,
        "first_failure_matches_official": first_match,
        "diagnostic_pass": not issues,
        "validator_pass": official_first is None,
        "pass_fail_matches_official": (not issues) == (official_first is None),
        "failures": issues,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--packet", type=Path, default=PACKET_DEFAULT)
    args = ap.parse_args()
    packet = args.packet.resolve()
    official = load_validator()
    results = [diagnose(ref, packet, official) for ref in FAMILIES]
    summary = {
        "task_id": "IGNITION-20260929-228",
        "task227_head": "7d979b1aa523030b16f773a973477cbfca1e4513",
        "diagnostic_mode": "read_only_exhaustive_no_input_mutation",
        "source_files": {
            "schema": str(SCHEMA_PATH.relative_to(ROOT)),
            "validator": str(VALIDATOR_PATH.relative_to(ROOT)),
            "frozen_manifest": str((TASK227 / "freeze/freeze-manifest.json").relative_to(ROOT)),
        },
        "policy_count": len(results),
        "validator_pass_count": sum(r["validator_pass"] for r in results),
        "first_failure_crosscheck_all_match": all(r["first_failure_matches_official"] for r in results),
        "pass_fail_crosscheck_all_match": all(r["pass_fail_matches_official"] for r in results),
        "all_policy_bytes_unchanged": all(r["input_unchanged"] for r in results),
        "categories": CATEGORIES,
        "predicates_not_defined_by_task227": [{
            "rule_id": "ACTION_PARAMETER_INPUT_BINDING",
            "category": "TYPED_PARAMETER_INPUT_MISMATCH",
            "status": "not_encoded",
            "detail": "Task227 has typed selector-condition checks, but action parameters are only name/value pairs and have no declared input-type link in schema or validator.",
        }],
        "results": results,
    }
    out = TASK228
    out.mkdir(parents=True, exist_ok=True)
    (out / "validator-failure-taxonomy.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    rows = []
    for result in results:
        for failure in result["failures"]:
            rows.append({
                "ref_id": result["ref_id"], "family_id": result["family_id"],
                "policy_sha256": result["policy_sha256"],
                "rule_id": failure["rule_id"], "category": failure["category"],
                "location": failure["location"], "detail": failure["detail"],
                "official_first_failure": result["official_first_failure"],
                "first_failure_matches_official": str(result["first_failure_matches_official"]).lower(),
            })
    with (out / "validator-failure-taxonomy.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else [
            "ref_id", "family_id", "policy_sha256", "rule_id", "category",
            "location", "detail", "official_first_failure", "first_failure_matches_official"])
        writer.writeheader()
        writer.writerows(rows)
    lines = [
        "# Per-policy Task227 validator audit",
        "",
        "Inputs were the six immutable raw reference-policy bytes only. The diagnostic",
        "harness loaded the frozen Task227 schema and validator, enumerated all custom",
        "predicates without modifying policy inputs, and ran the official validator",
        "unchanged for first-failure comparison.",
        "",
        f"- Frozen Task227 head: `{summary['task227_head']}`",
        f"- Official validator pass: {summary['validator_pass_count']}/6",
        f"- First-failure cross-check: {summary['first_failure_crosscheck_all_match']}",
        f"- Pass/fail cross-check: {summary['pass_fail_crosscheck_all_match']}",
        f"- Input bytes unchanged: {summary['all_policy_bytes_unchanged']}",
        "",
    ]
    for result in results:
        lines.extend([
            f"## {result['ref_id']} ({result['family_id']})",
            "",
            f"- SHA256: `{result['policy_sha256']}`",
            f"- Official first failure: `{result['official_first_failure']}`",
            f"- Exhaustive failures: {len(result['failures'])}",
            f"- First failure matches official: {result['first_failure_matches_official']}",
            f"- Input unchanged: {result['input_unchanged']}",
        ])
        if result["failures"]:
            for item in result["failures"]:
                lines.append(f"  - `{item['rule_id']}` [{item['category']}] {item['location']}: {item['detail']}")
        else:
            lines.append("- No failures.")
        lines.append("")
    (out / "per-policy-validator-audit.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "policies": len(results), "validator_pass": summary["validator_pass_count"],
        "first_failure_crosscheck_all_match": summary["first_failure_crosscheck_all_match"],
        "pass_fail_crosscheck_all_match": summary["pass_fail_crosscheck_all_match"],
        "all_policy_bytes_unchanged": summary["all_policy_bytes_unchanged"],
        "failures_per_policy": {r["ref_id"]: len(r["failures"]) for r in results},
    }, ensure_ascii=False))
    return 0 if (summary["first_failure_crosscheck_all_match"]
                 and summary["pass_fail_crosscheck_all_match"]
                 and summary["all_policy_bytes_unchanged"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
