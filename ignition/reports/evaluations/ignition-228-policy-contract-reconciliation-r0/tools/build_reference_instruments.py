#!/usr/bin/env python3
"""Compile explicit Task228 target-blind mapping declarations into canonical policy JSON."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

TASK228 = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[5]
DECLARATION = TASK228 / "mappings/reference-mapping-declarations.json"
POLICY_DIR = TASK228 / "policies"
MANIFEST_PATH = TASK228 / "build/candidate-build-manifest.json"
COMPILER_VERSION = "task228-reference-instrument-compiler-r1"
EXPECTED_FAMILIES = {"FAMILY01", "FAMILY02", "FAMILY03"}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n").encode("utf-8")


def source_lines_lf(data: bytes) -> list[bytes]:
    parts = data.split(b"\n")
    lines = [part + b"\n" for part in parts[:-1]]
    if parts[-1]:
        lines.append(parts[-1])
    return lines


def unique_refs(rows: list[str]) -> list[str]:
    return list(dict.fromkeys(rows))


def compile_all() -> tuple[dict[Path, bytes], dict[str, Any]]:
    declaration_bytes = DECLARATION.read_bytes()
    declaration = json.loads(declaration_bytes.decode("utf-8", errors="strict"))
    if declaration.get("schema_version") != "task228-researcher-mappings-r1":
        raise ValueError("unsupported researcher mapping declaration version")
    sources = declaration.get("sources")
    candidates = declaration.get("candidates")
    if not isinstance(sources, dict) or set(sources) != EXPECTED_FAMILIES or not isinstance(candidates, list) or len(candidates) != 6:
        raise ValueError("declaration must bind exactly three families and six candidates")

    # Read only the six source paths named in this declaration. No target directory is enumerated.
    source_bytes: dict[tuple[str, str], bytes] = {}
    source_hashes: dict[str, str] = {}
    for family in sorted(EXPECTED_FAMILIES):
        family_source = sources[family]
        if set(family_source) != {"M0", "E1", "baseline_actions", "baseline_actions_evidence"}:
            raise ValueError(f"{family}: source declaration has unexpected keys")
        for source_type in ("M0", "E1"):
            spec = family_source[source_type]
            if set(spec) != {"path", "sha256"}:
                raise ValueError(f"{family}/{source_type}: source binding is malformed")
            path = spec["path"]
            expected_prefix = f"ignition/reports/evaluations/ignition-220-cognitive-evolution-r0/families/{family}/"
            expected_name = "m0.md" if source_type == "M0" else "revision-evidence-e1.md"
            if path != expected_prefix + expected_name:
                raise ValueError(f"{family}/{source_type}: source path is outside the exact M0/E1 allowlist")
            raw = (REPO / path).read_bytes()
            if digest(raw) != spec["sha256"]:
                raise ValueError(f"{family}/{source_type}: source bytes do not match declared frozen SHA-256")
            raw.decode("utf-8", errors="strict")
            source_bytes[(family, source_type)] = raw
            source_hashes[path] = spec["sha256"]
        if not family_source["baseline_actions"] or not family_source["baseline_actions_evidence"]:
            raise ValueError(f"{family}: baseline preservation declaration is empty")

    declaration_hash = digest(declaration_bytes)
    compiled: dict[Path, bytes] = {}
    policy_hashes: dict[str, str] = {}
    seen_policy_ids: set[str] = set()
    seen_mapping_ids: set[str] = set()
    for candidate in candidates:
        family = candidate["family"]
        if family not in EXPECTED_FAMILIES:
            raise ValueError(f"unknown family {family}")
        if candidate.get("authorship") != "researcher-authored target-blind mapping" or not candidate.get("mapping_statement", "").strip():
            raise ValueError(f"{candidate.get('mapping_id', '<unknown>')}: explicit researcher-authored mapping statement is required")
        if candidate["policy_id"] in seen_policy_ids or candidate["mapping_id"] in seen_mapping_ids:
            raise ValueError("policy and mapping identifiers must be unique")
        seen_policy_ids.add(candidate["policy_id"])
        seen_mapping_ids.add(candidate["mapping_id"])
        evidence_ids = [item["evidence_id"] for item in candidate["evidence"]]
        if len(evidence_ids) != len(set(evidence_ids)):
            raise ValueError(f"{candidate['mapping_id']}: evidence IDs are not unique")
        evidence_by_id = {item["evidence_id"]: item for item in candidate["evidence"]}
        family_source = sources[family]
        evidence_basis = []
        for item in candidate["evidence"]:
            source_type = item["source_type"]
            if source_type not in {"M0", "E1"}:
                raise ValueError(f"{candidate['mapping_id']}: unsupported evidence source type")
            source_spec = family_source[source_type]
            raw = source_bytes[(family, source_type)]
            start, end = item["start_line"], item["end_line"]
            lines = source_lines_lf(raw)
            if not isinstance(start, int) or not isinstance(end, int) or start < 1 or end < start or end > len(lines):
                raise ValueError(f"{candidate['mapping_id']}/{item['evidence_id']}: source line range is invalid")
            excerpt = b"".join(lines[start - 1:end])
            evidence_basis.append({
                "evidence_id": item["evidence_id"], "source_type": source_type,
                "source_path": source_spec["path"], "source_sha256": source_spec["sha256"],
                "locator": {"start_line": start, "end_line": end, "excerpt_sha256": digest(excerpt)},
                "display_excerpt": excerpt.decode("utf-8", errors="strict"),
                "supports": item["supports"], "claim_type": item["claim_type"],
            })

        inputs = candidate["inputs"]
        rule_conditions = candidate["conditions"]
        rule_evidence = unique_refs(candidate["rule_evidence"])
        out_region_id = candidate["policy_id"] + "_OUTSIDE_COMPLEMENT"
        licensed_region_id = candidate["policy_id"] + "_LICENSED_PATTERN"
        fallback_evidence = unique_refs(candidate["fallback_evidence"])
        stop_evidence = unique_refs(candidate["stop_evidence"])
        preservation_evidence = unique_refs(family_source["baseline_actions_evidence"])

        policy: dict[str, Any] = {
            "contract_version": "task228-policy-contract-r1",
            "policy_id": candidate["policy_id"], "family": family, "mapping_id": candidate["mapping_id"],
            "evidence_basis": evidence_basis,
            "selector": {
                "required_inputs": inputs,
                "rule": [{"rule_id": candidate["rule_id"], "when": rule_conditions, "action_ref": candidate["action_id"], "evidence_refs": rule_evidence}],
            },
            "applicability": {
                "licensed_region": [{"region_id": licensed_region_id, "conditions": rule_conditions, "rule_refs": [candidate["rule_id"]], "evidence_refs": rule_evidence}],
                "out_of_scope": [{"region_id": out_region_id, "conditions": [], "fallback_ref": "fallback", "evidence_refs": unique_refs(candidate["out_of_scope_evidence"])}],
            },
            "action_table": [{
                "action_id": candidate["action_id"], "when": rule_conditions,
                "action": {"category": candidate["action_category"], "name": candidate["action_name"], "parameters": candidate["parameters"]},
                "required_report_fields": candidate["report_fields"], "evidence_refs": unique_refs(candidate["action_evidence"]),
            }],
            "preserved_rules": [{
                "preservation_id": f"{candidate['policy_id']}_PRESERVE_{index + 1}", "when": [], "baseline_action": action,
                "preservation_mode": "unconditional", "m0_action_retired": False, "evidence_refs": preservation_evidence,
            } for index, action in enumerate(family_source["baseline_actions"])],
            "fallback": {
                "when": [], "action": {
                    "outcome": "RECONCILE",
                    "instruction": "Record the supplied values and reason for missing, excluded, zero-match, or multiple-match routing; preserve the M0 pathway and request independent review when needed.",
                    "required_report_fields": ["supplied_inputs", "fallback_reason", "M0_pathway_status"],
                },
                "evidence_refs": fallback_evidence,
            },
            "stop_conditions": [{
                "stop_id": candidate["policy_id"] + "_INVALID_MEASUREMENT_STOP",
                "when": [{"input_id": inputs[0]["input_id"], "operator": "eq", "value": False, "unit": inputs[0]["unit"]}],
                "outcome": "REACQUIRE", "instruction": "Stop this candidate route; restore or reacquire required M0 setup and measurement-quality inputs before classifying.",
                "evidence_refs": stop_evidence,
            }],
            "scope_ceiling": {
                "licensed_claims": [{"claim_id": candidate["policy_id"] + "_BOUNDED_CLAIM", "statement": candidate["licensed_claim"], "region_refs": [licensed_region_id], "evidence_refs": unique_refs(candidate["licensed_claim_evidence"])}],
                "not_established": [{"claim_id": candidate["policy_id"] + "_LIMITS", "statement": candidate["not_established"], "region_refs": [licensed_region_id, out_region_id], "evidence_refs": unique_refs(candidate["not_established_evidence"])}],
                "statement": "This is a bounded reference-instrument candidate from one family’s M0 and E1 only. It is not a transfer, revision-generation, causal-effect, general-inheritance, Cognitive Evolution, cross-model, R1, Model-RSI, or training-benefit result.",
            },
        }

        provenance_specs: list[tuple[str, str, list[str]]] = []
        provenance_specs += [("required_input", row["input_id"], row["source_refs"]) for row in inputs]
        provenance_specs.append(("selector_rule", candidate["rule_id"], rule_evidence))
        provenance_specs.append(("action", candidate["action_id"], unique_refs(candidate["action_evidence"])))
        provenance_specs.append(("licensed_region", licensed_region_id, rule_evidence))
        provenance_specs.append(("out_of_scope", out_region_id, unique_refs(candidate["out_of_scope_evidence"])))
        provenance_specs += [("preserved_rule", row["preservation_id"], preservation_evidence) for row in policy["preserved_rules"]]
        provenance_specs.append(("fallback", "fallback", fallback_evidence))
        provenance_specs.append(("stop_condition", policy["stop_conditions"][0]["stop_id"], stop_evidence))
        provenance_specs.append(("licensed_claim", policy["scope_ceiling"]["licensed_claims"][0]["claim_id"], unique_refs(candidate["licensed_claim_evidence"])))
        provenance_specs.append(("not_established_claim", policy["scope_ceiling"]["not_established"][0]["claim_id"], unique_refs(candidate["not_established_evidence"])))
        policy["provenance"] = {
            "declaration_sha256": declaration_hash,
            "compiler": COMPILER_VERSION,
            "links": [{
                "element_type": kind, "element_id": element_id, "evidence_refs": unique_refs(refs),
                "locator_detail": f"{candidate['mapping_id']} declaration; evidence refs: {', '.join(unique_refs(refs))}",
            } for kind, element_id, refs in provenance_specs],
        }

        out_path = POLICY_DIR / f"{candidate['policy_id']}.json"
        policy_bytes = canonical_json(policy)
        compiled[out_path] = policy_bytes
        policy_hashes[str(out_path.relative_to(TASK228))] = digest(policy_bytes)

    if len(seen_policy_ids) != 6:
        raise ValueError("exactly six unique policy candidates are required")
    compiler_hash = digest(Path(__file__).read_bytes())
    manifest = {
        "manifest_version": "task228-candidate-build-manifest-r1",
        "mapping_declaration": str(DECLARATION.relative_to(TASK228)),
        "mapping_declaration_sha256": declaration_hash,
        "compiler": COMPILER_VERSION,
        "compiler_sha256": compiler_hash,
        "candidate_count": len(policy_hashes),
        "mapping_declarations": {
            row["mapping_id"]: {"authorship": row["authorship"], "mapping_statement": row["mapping_statement"]}
            for row in sorted(candidates, key=lambda item: item["mapping_id"])
        },
        "candidate_sha256": dict(sorted(policy_hashes.items())),
        "source_sha256": dict(sorted(source_hashes.items())),
        "target_access_during_build": False,
        "transfer_experiment_run": False,
        "revision_experiment_run": False,
    }
    compiled[MANIFEST_PATH] = canonical_json(manifest)
    return compiled, manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="rebuild in memory and compare bytes without writing")
    args = parser.parse_args()
    try:
        outputs, _ = compile_all()
    except Exception as exc:
        print(f"TASK228_REFERENCE_BUILD_INVALID: {exc}", file=sys.stderr)
        return 2
    mismatches = []
    for path, expected in outputs.items():
        if args.check:
            if not path.exists() or path.read_bytes() != expected:
                mismatches.append(str(path))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    if args.check:
        if mismatches:
            for path in mismatches:
                print(f"TASK228_REFERENCE_BUILD_MISMATCH={path}")
            return 1
        print("TASK228_REFERENCE_REBUILD=BYTE_IDENTICAL")
    else:
        print(f"TASK228_REFERENCE_BUILD=PASS candidates=6 manifest={MANIFEST_PATH}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
