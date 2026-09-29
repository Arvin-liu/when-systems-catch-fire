#!/usr/bin/env python3
"""Fail-closed Task228 policy validator for the reconciled contract R1."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

try:
    from jsonschema import Draft202012Validator
except ImportError as exc:  # pragma: no cover - exercised by CLI packaging
    raise SystemExit("TASK228_POLICY_INVALID: jsonschema 4.x is required") from exc

REPO = Path(__file__).resolve().parents[5]
TASK228 = REPO / "ignition/reports/evaluations/ignition-228-policy-contract-reconciliation-r0"
SCHEMA_PATH = TASK228 / "reference/policy-schema.json"
FREEZE_MANIFEST = REPO / "ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0/freeze/freeze-manifest.json"
FAMILIES = ("FAMILY01", "FAMILY02", "FAMILY03")
SOURCE_TYPES = {"m0.md": "M0", "revision-evidence-e1.md": "E1"}
OPERATORS = {"eq", "neq", "lt", "lte", "gt", "gte", "in", "not_in", "between", "present", "absent"}
PARAM_TYPES = {"number", "string", "boolean"}
PROVENANCE_TYPES = {
    "required_input", "selector_rule", "action", "licensed_region", "out_of_scope",
    "preserved_rule", "fallback", "stop_condition", "licensed_claim", "not_established_claim",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as stream:
        return json.load(stream)


def expected_sources(repo_root: Path) -> dict[str, str]:
    """Read only the six M0/E1 source bindings from the frozen Task227 manifest."""
    manifest = load_json(repo_root / FREEZE_MANIFEST.relative_to(REPO))
    entries = manifest.get("external_m0_e1_inputs")
    if not isinstance(entries, list):
        raise ValueError("freeze manifest lacks external_m0_e1_inputs")
    result: dict[str, str] = {}
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("path"), str) and isinstance(entry.get("sha256"), str):
            result[entry["path"]] = entry["sha256"]
    if len(result) != 6:
        raise ValueError("freeze manifest must bind exactly six M0/E1 inputs")
    for family in FAMILIES:
        directory = f"ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families/{family}/"
        for name in SOURCE_TYPES:
            if directory + name not in result:
                raise ValueError(f"freeze manifest missing {family}/{name}")
    return result


def source_lines_lf(data: bytes) -> list[bytes]:
    """Return LF-delimited byte lines with LF retained; preserve CR bytes."""
    parts = data.split(b"\n")
    lines = [part + b"\n" for part in parts[:-1]]
    if parts[-1]:
        lines.append(parts[-1])
    return lines


def is_typed(value: Any, kind: str) -> bool:
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    if kind == "string":
        return isinstance(value, str)
    if kind == "boolean":
        return isinstance(value, bool)
    return False


def _finding(code: str, path: str, message: str) -> dict[str, str]:
    return {"rule_id": code, "path": path, "message": message}


def validate_policy(
    policy: Any,
    *,
    repo_root: Path = REPO,
    schema: dict[str, Any] | None = None,
    source_catalog: dict[str, str] | None = None,
    source_bytes: dict[str, bytes] | None = None,
) -> list[dict[str, str]]:
    """Return all contract findings. Optional source maps are for offline conformance fixtures."""
    findings: list[dict[str, str]] = []

    def add(code: str, path: str, message: str) -> None:
        findings.append(_finding(code, path, message))

    schema_obj = schema if schema is not None else load_json(TASK228 / "reference/policy-schema.json")
    try:
        Draft202012Validator.check_schema(schema_obj)
        schema_errors = sorted(Draft202012Validator(schema_obj).iter_errors(policy), key=lambda error: list(error.absolute_path))
    except Exception as exc:
        add("SCHEMA_VALIDITY", "$schema", f"schema validation could not complete: {exc}")
        return findings
    if schema_errors:
        for error in schema_errors:
            path = "$" + "".join(f"/{part}" for part in error.absolute_path)
            add("SCHEMA_VALIDITY", path, error.message)
        return findings

    try:
        if source_catalog is None:
            source_catalog = expected_sources(repo_root)
        if source_bytes is None:
            source_bytes = {path: (repo_root / path).read_bytes() for path in source_catalog}
    except Exception as exc:
        add("FAMILY_SOURCE_BINDING", "$sources", f"cannot load frozen M0/E1 bindings: {exc}")
        return findings

    family = policy["family"]
    family_dir = f"ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families/{family}/"
    source_type_by_path = {family_dir + name: kind for name, kind in SOURCE_TYPES.items()}
    evidence = policy["evidence_basis"]
    evidence_ids = [item["evidence_id"] for item in evidence]
    evidence_by_id = {item["evidence_id"]: item for item in evidence}

    # Uniqueness is checked per declared identifier type; typed provenance pairs are unique.
    identifier_groups: list[tuple[str, list[str]]] = [
        ("evidence", evidence_ids),
        ("required input", [item["input_id"] for item in policy["selector"]["required_inputs"]]),
        ("selector rule", [item["rule_id"] for item in policy["selector"]["rule"]]),
        ("action", [item["action_id"] for item in policy["action_table"]]),
        ("region", [item["region_id"] for item in policy["applicability"]["licensed_region"] + policy["applicability"]["out_of_scope"]]),
        ("preserved rule", [item["preservation_id"] for item in policy["preserved_rules"]]),
        ("stop condition", [item["stop_id"] for item in policy["stop_conditions"]]),
        ("scope claim", [item["claim_id"] for item in policy["scope_ceiling"]["licensed_claims"] + policy["scope_ceiling"]["not_established"]]),
    ]
    for label, values in identifier_groups:
        if len(values) != len(set(values)):
            add("UNIQUE_IDENTIFIERS", "$", f"{label} identifiers are not unique")

    # Frozen source SHA and exact structured line-slice verification.
    for index, item in enumerate(evidence):
        path = item["source_path"]
        source_type = item["source_type"]
        expected_type = source_type_by_path.get(path)
        expected_sha = source_catalog.get(path)
        raw = source_bytes.get(path)
        epath = f"/evidence_basis/{index}"
        if path not in source_catalog or expected_type != source_type or not path.startswith(family_dir):
            add("FAMILY_SOURCE_BINDING", epath + "/source_path", "source must be the exact M0 or E1 path for this policy family")
            continue
        if expected_sha is None or item["source_sha256"] != expected_sha:
            add("FAMILY_SOURCE_BINDING", epath + "/source_sha256", "declared source hash differs from the frozen manifest")
            continue
        if raw is None or sha256(raw) != expected_sha:
            add("FAMILY_SOURCE_BINDING", epath + "/source_path", "source bytes do not match the frozen manifest hash")
            continue
        try:
            raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            add("FAMILY_SOURCE_BINDING", epath + "/source_path", "frozen source is not strict UTF-8")
            continue
        start = item["locator"]["start_line"]
        end = item["locator"]["end_line"]
        lines = source_lines_lf(raw)
        if end < start or end > len(lines):
            add("FAMILY_SOURCE_BINDING", epath + "/locator", "inclusive line range is outside the frozen source")
            continue
        excerpt = b"".join(lines[start - 1:end])
        if sha256(excerpt) != item["locator"]["excerpt_sha256"]:
            add("FAMILY_SOURCE_BINDING", epath + "/locator/excerpt_sha256", "excerpt hash does not match exact LF-delimited source bytes")
            continue
        if "display_excerpt" in item:
            try:
                display = item["display_excerpt"].encode("utf-8", errors="strict")
            except UnicodeEncodeError:
                add("FAMILY_SOURCE_BINDING", epath + "/display_excerpt", "display excerpt cannot be encoded as strict UTF-8")
            else:
                if display != excerpt:
                    add("FAMILY_SOURCE_BINDING", epath + "/display_excerpt", "display excerpt differs from authoritative byte slice")

    inputs = policy["selector"]["required_inputs"]
    input_by_id = {item["input_id"]: item for item in inputs}

    def check_conditions(conditions: list[dict[str, Any]], path: str, allow_empty: bool) -> None:
        if not allow_empty and not conditions:
            add("TYPED_CONDITIONS", path, "condition list must be nonempty")
        for offset, condition in enumerate(conditions):
            cpath = f"{path}/{offset}"
            inp = input_by_id.get(condition["input_id"])
            if inp is None:
                add("TYPED_CONDITIONS", cpath + "/input_id", "condition refers to an undeclared input")
                continue
            kind = inp["value_type"]
            op = condition["operator"]
            value = condition["value"]
            if op not in OPERATORS:
                add("TYPED_CONDITIONS", cpath + "/operator", "operator is outside the normative operator set")
                continue
            if condition["unit"] != inp["unit"]:
                add("TYPED_CONDITIONS", cpath + "/unit", "condition unit must exactly equal its input unit")
            if op in {"present", "absent"}:
                if value is not None:
                    add("TYPED_CONDITIONS", cpath + "/value", "present/absent requires null value")
            elif op in {"in", "not_in"}:
                if not isinstance(value, list) or not value or any(not is_typed(v, kind) for v in value):
                    add("TYPED_CONDITIONS", cpath + "/value", f"{op} requires a nonempty list matching {kind}")
            elif op == "between":
                if kind != "number" or not isinstance(value, list) or len(value) != 2 or any(not is_typed(v, "number") for v in value) or (isinstance(value, list) and len(value) == 2 and all(is_typed(v, "number") for v in value) and value[0] > value[1]):
                    add("TYPED_CONDITIONS", cpath + "/value", "between requires ordered inclusive numeric bounds")
            else:
                if value is None or not is_typed(value, kind):
                    add("TYPED_CONDITIONS", cpath + "/value", f"value must be a non-null {kind} scalar")
                if op in {"lt", "lte", "gt", "gte"} and kind != "number":
                    add("TYPED_CONDITIONS", cpath + "/operator", "ordered comparisons are defined only for numeric inputs")

    for i, rule in enumerate(policy["selector"]["rule"]):
        check_conditions(rule["when"], f"/selector/rule/{i}/when", False)
    for i, action in enumerate(policy["action_table"]):
        check_conditions(action["when"], f"/action_table/{i}/when", False)
    for i, region in enumerate(policy["applicability"]["licensed_region"]):
        check_conditions(region["conditions"], f"/applicability/licensed_region/{i}/conditions", False)
    for i, region in enumerate(policy["applicability"]["out_of_scope"]):
        check_conditions(region["conditions"], f"/applicability/out_of_scope/{i}/conditions", True)
    for i, preserved in enumerate(policy["preserved_rules"]):
        check_conditions(preserved["when"], f"/preserved_rules/{i}/when", True)
    for i, stop in enumerate(policy["stop_conditions"]):
        check_conditions(stop["when"], f"/stop_conditions/{i}/when", False)

    # Every reference resolves; all declared evidence participates in at least one element.
    all_refs: list[str] = []
    def walk_refs(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key in {"source_refs", "evidence_refs"} and isinstance(child, list):
                    all_refs.extend(child)
                else:
                    walk_refs(child)
        elif isinstance(value, list):
            for child in value:
                walk_refs(child)
    walk_refs(policy)
    known_evidence = set(evidence_ids)
    for ref in all_refs:
        if ref not in known_evidence:
            add("EVIDENCE_REFERENCES", "$", f"unknown evidence reference {ref}")
    unused = known_evidence - set(all_refs)
    if unused:
        add("EVIDENCE_REFERENCES", "/evidence_basis", f"unused evidence identifiers: {sorted(unused)}")

    rules = policy["selector"]["rule"]
    actions = policy["action_table"]
    rules_by_id = {row["rule_id"]: row for row in rules}
    actions_by_id = {row["action_id"]: row for row in actions}
    action_refs = [row["action_ref"] for row in rules]
    if len(rules) != len(actions) or len(action_refs) != len(set(action_refs)) or set(action_refs) != set(actions_by_id):
        add("SELECTOR_ACTION_BIJECTION", "/selector/rule", "selector rules and action rows must form a one-to-one mapping")
    for index, rule in enumerate(rules):
        action = actions_by_id.get(rule["action_ref"])
        if action is not None and rule["when"] != action["when"]:
            add("SELECTOR_ACTION_BIJECTION", f"/selector/rule/{index}/when", "rule and linked action conditions differ")

    licensed = policy["applicability"]["licensed_region"]
    outside = policy["applicability"]["out_of_scope"]
    regions_by_id = {row["region_id"]: row for row in licensed + outside}
    mapped_rules: list[str] = []
    for index, region in enumerate(licensed):
        refs = region["rule_refs"]
        if len(refs) != 1 or refs[0] not in rules_by_id:
            add("LICENSED_REGION_BIJECTION", f"/applicability/licensed_region/{index}/rule_refs", "licensed region must reference exactly one known selector rule")
            continue
        mapped_rules.append(refs[0])
        if region["conditions"] != rules_by_id[refs[0]]["when"]:
            add("LICENSED_REGION_BIJECTION", f"/applicability/licensed_region/{index}/conditions", "region conditions differ from referenced rule")
    if len(mapped_rules) != len(set(mapped_rules)) or set(mapped_rules) != set(rules_by_id):
        add("LICENSED_REGION_BIJECTION", "/applicability/licensed_region", "selector rules and licensed regions must form a one-to-one mapping")
    empty_outside = [row for row in outside if not row["conditions"]]
    if empty_outside and len(outside) != 1:
        add("OUT_OF_SCOPE_COMPLEMENT", "/applicability/out_of_scope", "empty complement must be the sole out-of-scope row")
    if any(row["fallback_ref"] != "fallback" for row in outside):
        add("OUT_OF_SCOPE_COMPLEMENT", "/applicability/out_of_scope", "every out-of-scope route must target fallback")

    for index, preserved in enumerate(policy["preserved_rules"]):
        mode = preserved["preservation_mode"]
        if preserved["m0_action_retired"] is not False:
            add("PRESERVATION_SEMANTICS", f"/preserved_rules/{index}/m0_action_retired", "M0 action retirement is prohibited")
        if mode in {"unconditional", "selector_miss"} and preserved["when"]:
            add("PRESERVATION_SEMANTICS", f"/preserved_rules/{index}/when", f"{mode} requires an empty condition list")
        if mode == "additive_coexistence" and (not preserved["when"] or sum(row["when"] == preserved["when"] for row in rules) != 1):
            add("PRESERVATION_SEMANTICS", f"/preserved_rules/{index}/when", "additive coexistence must exactly match one selector rule")
        for ref in preserved["evidence_refs"]:
            ev = evidence_by_id.get(ref)
            if ev is None or ev["source_type"] != "M0":
                add("PRESERVED_EVIDENCE_M0_ONLY", f"/preserved_rules/{index}/evidence_refs", "preservation evidence must cite M0 only")
                break

    for ai, action in enumerate(actions):
        params = action["action"]["parameters"]
        names = [param["name"] for param in params]
        if len(names) != len(set(names)):
            add("UNIQUE_IDENTIFIERS", f"/action_table/{ai}/action/parameters", "parameter names must be unique within an action")
        if params and action["action"]["category"] in {"KEEP_BASELINE", "UNSCORABLE"}:
            pass
        if not params and action["action"]["category"] not in {"KEEP_BASELINE", "UNSCORABLE"}:
            add("TYPED_PARAMETER_BINDING", f"/action_table/{ai}/action/parameters", "empty parameters are allowed only for KEEP_BASELINE or UNSCORABLE")
        for pi, parameter in enumerate(params):
            ppath = f"/action_table/{ai}/action/parameters/{pi}"
            if parameter["binding"] == "literal":
                if not is_typed(parameter["value"], parameter["value_type"]):
                    add("TYPED_PARAMETER_BINDING", ppath + "/value", "literal value must match its declared scalar type")
            elif parameter["binding"] == "input_ref":
                inp = input_by_id.get(parameter["input_id"])
                if inp is None:
                    add("TYPED_PARAMETER_BINDING", ppath + "/input_id", "input_ref must name a required input")
                else:
                    if parameter["value_type"] != inp["value_type"] or parameter["unit"] != inp["unit"]:
                        add("TYPED_PARAMETER_BINDING", ppath, "input_ref type and unit must exactly match its required input")
                    if not set(inp["source_refs"]).issubset(set(parameter["evidence_refs"])):
                        add("TYPED_PARAMETER_BINDING", ppath + "/evidence_refs", "input_ref evidence must include all referenced input source_refs")

    if policy["fallback"]["when"]:
        add("FALLBACK_UNIVERSALITY", "/fallback/when", "fallback must have empty conditions to cover all unresolved and excluded inputs")
    if not policy["fallback"]["action"]["required_report_fields"]:
        add("FALLBACK_UNIVERSALITY", "/fallback/action/required_report_fields", "fallback must declare required reporting fields")
    for index, stop in enumerate(policy["stop_conditions"]):
        if not stop["when"] or not stop["instruction"].strip():
            add("STOP_CONDITION_STRUCTURE", f"/stop_conditions/{index}", "stop needs nonempty typed conditions and a safe instruction")

    licensed_ids = {row["region_id"] for row in licensed}
    all_region_ids = set(regions_by_id)
    licensed_claims = policy["scope_ceiling"]["licensed_claims"]
    exclusions = policy["scope_ceiling"]["not_established"]
    for index, claim in enumerate(licensed_claims):
        if not set(claim["region_refs"]).issubset(licensed_ids):
            add("SCOPE_REGION_LICENSING", f"/scope_ceiling/licensed_claims/{index}/region_refs", "licensed claim may reference only licensed regions")
    for index, claim in enumerate(exclusions):
        if not set(claim["region_refs"]).issubset(all_region_ids):
            add("SCOPE_REGION_LICENSING", f"/scope_ceiling/not_established/{index}/region_refs", "not-established claim has an unknown region")

    # Complete provenance coverage is exact for the normative list of typed semantic elements.
    expected_elements: dict[tuple[str, str], set[str]] = {}
    expected_elements.update({("required_input", row["input_id"]): set(row["source_refs"]) for row in inputs})
    expected_elements.update({("selector_rule", row["rule_id"]): set(row["evidence_refs"]) for row in rules})
    expected_elements.update({("action", row["action_id"]): set(row["evidence_refs"]) for row in actions})
    expected_elements.update({("licensed_region", row["region_id"]): set(row["evidence_refs"]) for row in licensed})
    expected_elements.update({("out_of_scope", row["region_id"]): set(row["evidence_refs"]) for row in outside})
    expected_elements.update({("preserved_rule", row["preservation_id"]): set(row["evidence_refs"]) for row in policy["preserved_rules"]})
    expected_elements[("fallback", "fallback")] = set(policy["fallback"]["evidence_refs"])
    expected_elements.update({("stop_condition", row["stop_id"]): set(row["evidence_refs"]) for row in policy["stop_conditions"]})
    expected_elements.update({("licensed_claim", row["claim_id"]): set(row["evidence_refs"]) for row in licensed_claims})
    expected_elements.update({("not_established_claim", row["claim_id"]): set(row["evidence_refs"]) for row in exclusions})
    provenance_rows = policy["provenance"]["links"]
    actual_elements: dict[tuple[str, str], set[str]] = {}
    for index, row in enumerate(provenance_rows):
        pair = (row["element_type"], row["element_id"])
        if pair in actual_elements:
            add("UNIQUE_IDENTIFIERS", f"/provenance/links/{index}", "typed provenance pair is duplicated")
        actual_elements[pair] = set(row["evidence_refs"])
        if pair not in expected_elements:
            add("PROVENANCE_COVERAGE", f"/provenance/links/{index}", "provenance link names an unknown typed element")
        elif actual_elements[pair] != expected_elements[pair]:
            add("PROVENANCE_COVERAGE", f"/provenance/links/{index}/evidence_refs", "provenance refs must exactly equal the element's direct refs")
    missing = set(expected_elements) - set(actual_elements)
    extra = set(actual_elements) - set(expected_elements)
    if missing or extra:
        add("PROVENANCE_COVERAGE", "/provenance/links", f"typed provenance coverage differs; missing={sorted(missing)}, extra={sorted(extra)}")

    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("policy", nargs="?", type=Path)
    parser.add_argument("--schema-only", action="store_true")
    args = parser.parse_args()
    try:
        schema = load_json(SCHEMA_PATH)
        Draft202012Validator.check_schema(schema)
        print("TASK228_POLICY_SCHEMA=PASS")
        if args.schema_only:
            return 0
        if args.policy is None:
            parser.error("provide a policy path or --schema-only")
        policy = load_json(args.policy)
        findings = validate_policy(policy)
    except SystemExit:
        raise
    except Exception as exc:
        print(f"TASK228_POLICY_INVALID: {exc}", file=sys.stderr)
        return 2
    if findings:
        for finding in findings:
            print(json.dumps(finding, ensure_ascii=False, sort_keys=True))
        return 1
    print(f"TASK228_POLICY_VALID=PASS {args.policy}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
