#!/usr/bin/env python3
"""Build the frozen Task229 blind evaluator packets from frozen R1 outputs."""
from __future__ import annotations

import copy
import hashlib
import json
import pathlib
import random
import re
import secrets
import sys
from datetime import datetime, timezone

try:
    import jsonschema
except ImportError as exc:
    raise SystemExit("TASK229_ANALYSIS_RUNTIME=INVALID jsonschema is unavailable") from exc


HERE = pathlib.Path(__file__).resolve().parent
BUNDLE = HERE.parents[1]
ROOT = HERE.parents[4]
RUN = BUNDLE / "run"
SESSION_ROOT = RUN / "sessions"
OUT = RUN / "blind-evaluation"
CASE_ROOT = ROOT / "ignition/reports/evaluations/ignition-225-cognitive-evolution-r0-1/families"
TARGET_CRITERIA = ROOT / "ignition/reports/evaluations/ignition-225-cognitive-evolution-r0-1/evaluator/criteria.md"
TASK227_CRITERIA = ROOT / "ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0/transfer/evaluator-criteria.md"
BLIND_SCHEMA_PATH = BUNDLE / "source-prereg/blind-evaluation-schema.json"
RESPONSE_SCHEMA_PATH = BUNDLE / "source-prereg/response-schema.json"
BINDING_PATH = RUN / "post-response-target-binding.json"
SESSION_FREEZE_PATH = RUN / "session-freeze-manifest.json"

EXPECTED_ASSET_HASHES = {
    "ignition/reports/evaluations/ignition-225-cognitive-evolution-r0-1/evaluator/criteria.md": "9cc185aaf688cd2649a321c80051b8cc69e78a0b93edb3deac5cea3abd86cbcf",
    "ignition/reports/evaluations/ignition-225-cognitive-evolution-r0-1/evaluator/schema.json": "5be015a0568a830ed753ff8ef65a3909d0cfb99dff03f9ed39cb48719850ef6d",
    "ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0/transfer/evaluator-criteria.md": "880ce3bc42d4bf122babbbd349f8b4a4360f8e238e1338c72765efbe114e3874",
    "ignition/reports/evaluations/ignition-227-cognitive-evolution-component-isolation-r0/transfer/evaluator-schema.json": "665fbee30e02a8761044cd94bfd2a9528aae16fefa5bafaed604efbcc54b3eac",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def read_json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_bytes(path: pathlib.Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    path.write_bytes(data)


def utc_now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def relative(path: pathlib.Path) -> str:
    return path.relative_to(ROOT).as_posix()


def check_hash(path: pathlib.Path, expected: str, label: str):
    actual = sha(path.read_bytes())
    if actual != expected:
        raise ValueError(f"{label} SHA-256 mismatch: {actual} != {expected}")
    return actual


def remove_sensitive_fields(value):
    if isinstance(value, list):
        return [remove_sensitive_fields(item) for item in value]
    if not isinstance(value, dict):
        return value
    removed_names = {
        "route_trace", "provenance", "evidence_provenance", "builder", "tool",
        "file_path", "source_locator", "artifact_id", "session_id", "policy_id",
        "lineage_id", "bundle_id", "condition", "condition_name",
    }
    return {
        key: remove_sensitive_fields(item)
        for key, item in value.items()
        if key.lower() not in removed_names
    }


def section(text: str, heading: str, next_heading: str) -> str:
    start = text.index(heading)
    end = text.index(next_heading, start + len(heading))
    return text[start:end].rstrip() + "\n"


def main():
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite existing output: {OUT}")

    session_freeze = read_json(SESSION_FREEZE_PATH)
    if (
        session_freeze.get("design_session_count") != 18
        or session_freeze.get("completed_session_count") != 18
        or session_freeze.get("missing_or_invalid_count") != 0
        or session_freeze.get("replacement_count") != 0
        or session_freeze.get("historical_attempt1_responses_used") is not False
        or session_freeze.get("post_exposure_tuning_permitted") is not False
        or session_freeze.get("target_criteria_opened_before_response_freeze") is not False
    ):
        raise ValueError("raw session freeze invariants are not satisfied")

    # Recheck every file in the frozen raw-session manifest before reading a response.
    frozen_raw = {}
    for record in session_freeze["files"]:
        path = BUNDLE / record["path"]
        data = path.read_bytes()
        if len(data) != record["byte_length"] or sha(data) != record["sha256"]:
            raise ValueError(f"frozen session file changed: {record['path']}")
        frozen_raw[pathlib.PurePosixPath(record["path"]).relative_to("run").as_posix()] = record["sha256"]
    run_index_record = session_freeze["session_run_index"]
    check_hash(BUNDLE / run_index_record["path"], run_index_record["sha256"], run_index_record["path"])

    binding = read_json(BINDING_PATH)
    if (
        binding.get("responses_frozen_before_target_binding") is not True
        or binding.get("historical_attempt1_responses_used") is not False
        or binding.get("post_exposure_tuning_permitted") is not False
    ):
        raise ValueError("post-response target binding invariants are not satisfied")
    assets = binding["verified_post_freeze_target_and_evaluator_assets"]
    asset_hashes = {item["path"]: item["sha256"] for item in assets}
    for asset_path, expected in EXPECTED_ASSET_HASHES.items():
        if asset_hashes.get(asset_path) != expected:
            raise ValueError(f"verified evaluator asset binding is missing or changed: {asset_path}")
        check_hash(ROOT / asset_path, expected, asset_path)

    family_data = {}
    case_assets = {}
    for asset in assets:
        match = re.fullmatch(
            r"ignition/reports/evaluations/ignition-225-cognitive-evolution-r0-1/families/(FAMILY0[1-3])/cases/([ABC])\.md",
            asset["path"],
        )
        if not match:
            continue
        family, case_id = match.groups()
        case_path = ROOT / asset["path"]
        check_hash(case_path, asset["sha256"], asset["path"])
        case_assets.setdefault(family, {})[case_id] = {
            "path": case_path,
            "bytes": case_path.read_bytes(),
            "sha256": asset["sha256"],
        }
    for family, cases in case_assets.items():
        if set(cases) != {"A", "B", "C"}:
            raise ValueError(f"incomplete frozen cases for {family}")
        target_path = CASE_ROOT / family / "sealed/targets.json"
        target_record = next(
            item for item in assets
            if item["path"] == relative(target_path)
        )
        check_hash(target_path, target_record["sha256"], relative(target_path))
        target_doc = read_json(target_path)
        if set(target_doc.get("cases", {})) != {"A", "B", "C"}:
            raise ValueError(f"frozen target case set is invalid for {family}")
        family_data[family] = {
            "cases": cases,
            "targets": target_doc,
            "target_path": target_path,
            "target_sha256": target_record["sha256"],
        }

    # The sanitizer deliberately does not read the condition manifest or use its
    # condition-to-lineage mapping. It binds outputs to source prompts by opaque
    # directory suffix, then binds family through exact frozen case bytes embedded
    # in each prompt.
    response_schema = read_json(RESPONSE_SCHEMA_PATH)
    response_validator = jsonschema.Draft202012Validator(response_schema)
    session_dirs = sorted(SESSION_ROOT.glob("[0-9][0-9]-*/attempt-01"))
    if len(session_dirs) != 18:
        raise ValueError(f"expected 18 frozen session attempts, found {len(session_dirs)}")

    # Build the exact disallowed-token scan set from the frozen binding and run
    # records. No mapping between conditions and lineages is consulted.
    deny_tokens = {
        "M0_ONLY", "M0_PLUS_E1", "REFERENCE_M1",
        "IGNITION-20260930-229-R1", "ignition-229-r1-cli-transfer-replication-r0",
        "L01", "L02", "L03", "L04", "L05", "L06",
        "POLICY_F01_A", "POLICY_F01_B", "POLICY_F02_A", "POLICY_F02_B", "POLICY_F03_A", "POLICY_F03_B",
    }
    path_tokens = {item["path"] for item in assets}
    path_tokens |= {str(ROOT / token) for token in path_tokens}
    source_locator_tokens = set()
    for data in family_data.values():
        for target_case in data["targets"].get("cases", {}).values():
            op = target_case.get("operational_policy", {})
            source_locator_tokens.update(op.get("evidence_provenance", []))
    deny_tokens |= source_locator_tokens
    deny_tokens |= path_tokens
    deny_tokens = sorted((token for token in deny_tokens if token), key=len, reverse=True)
    deny_patterns = [re.compile(re.escape(token)) for token in deny_tokens]
    deny_patterns += [
        re.compile(r"\bPOLICY_F0[1-3]_[AB]\b"),
        re.compile(r"\bL0[1-6]\b"),
        re.compile(r"\b(?:OBS|VAL)-\d{2}\b"),
        re.compile(r"\bTask\d{3}\b"),
        re.compile(r"(?:[A-Za-z]:\\[^\s\"'<>]+|(?<![A-Za-z0-9])/(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+)"),
        re.compile(r"\b(?:ignition|reports|evaluations|families|sealed|cases|transfer|evaluator|tools|run)/[A-Za-z0-9_./-]+"),
    ]
    runtime_ids_by_design_id = {}
    for attempt_dir in session_dirs:
        _, design_id = attempt_dir.parent.name.split("-", 1)
        receipt = read_json(attempt_dir / "dispatch-receipt.json")
        runtime_ids = receipt.get("process", {}).get("session_ids_observed", [])
        runtime_ids_by_design_id[design_id] = sorted(x for x in runtime_ids if isinstance(x, str))
        deny_patterns.extend(re.compile(re.escape(token)) for token in [design_id, *runtime_ids_by_design_id[design_id]] if token)

    def redact_string(value: str, counts: dict[str, int]) -> str:
        result = value
        for pattern in deny_patterns:
            result, count = pattern.subn("[REDACTED]", result)
            if count:
                counts[pattern.pattern] = counts.get(pattern.pattern, 0) + count
        return result

    def redact_values(value, counts):
        if isinstance(value, str):
            return redact_string(value, counts)
        if isinstance(value, list):
            return [redact_values(item, counts) for item in value]
        if isinstance(value, dict):
            return {key: redact_values(item, counts) for key, item in value.items()}
        return value

    prepared_sessions = []
    response_ids_seen = {"A": set(), "B": set()}
    for attempt_dir in session_dirs:
        folder_name = attempt_dir.parent.name
        order_prefix, design_session_id = folder_name.split("-", 1)
        session_id = design_session_id
        prompt_candidates = list((RUN / "prompts").glob(f"*-{session_id}.md"))
        if len(prompt_candidates) != 1:
            raise ValueError(f"prompt mapping is not unique for frozen session {session_id}")
        prompt_path = prompt_candidates[0]
        prompt_bytes = prompt_path.read_bytes()

        matches = []
        for family, data in family_data.items():
            if all(data["cases"][case_id]["bytes"] in prompt_bytes for case_id in "ABC"):
                matches.append(family)
        if len(matches) != 1:
            raise ValueError(f"exact prompt case bytes do not identify one family for session {session_id}")
        family = matches[0]

        raw_relative = (attempt_dir / "last-message.txt").relative_to(RUN).as_posix()
        if raw_relative not in frozen_raw:
            raise ValueError(f"response file absent from frozen raw manifest: {raw_relative}")
        raw_bytes = (RUN / raw_relative).read_bytes()
        raw_hash = sha(raw_bytes)
        try:
            raw_document = json.loads(raw_bytes.decode("utf-8", errors="strict"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raw_document = None
        valid = raw_document is not None and not list(response_validator.iter_errors(raw_document))
        if valid:
            responses = raw_document["responses"]
            valid = len(responses) == 3 and {item.get("case_id") for item in responses} == {"A", "B", "C"}
        response_by_case = {}
        if raw_document is not None and isinstance(raw_document, dict):
            raw_responses = raw_document.get("responses", [])
            if isinstance(raw_responses, list):
                for item in raw_responses:
                    if isinstance(item, dict) and item.get("case_id") in {"A", "B", "C"}:
                        response_by_case.setdefault(item["case_id"], item)

        runtime_session_ids = runtime_ids_by_design_id[session_id]
        session_id_tokens = {session_id, *runtime_session_ids}

        scored = []
        for case_id in "ABC":
            original = response_by_case.get(case_id)
            sanitized = remove_sensitive_fields(copy.deepcopy(original)) if original is not None else None
            redactions = {}
            if sanitized is not None:
                sanitized = redact_values(sanitized, redactions)
                required_fields = [
                    "case_id", "primary_action", "additional_actions", "reported_values",
                    "preserved_baseline_action_ids", "fallback", "scope", "rationale",
                ]
                if any(field not in sanitized for field in required_fields):
                    valid = False
                if original is not None:
                    for field in required_fields:
                        if field in original and field in sanitized:
                            expected = redact_values(copy.deepcopy(original[field]), {})
                            if sanitized[field] != expected:
                                raise ValueError(f"sanitization changed scored field beyond exact redaction: {session_id}/{case_id}/{field}")
            scored.append({
                "case_id": case_id,
                "response_schema_valid": bool(valid and sanitized is not None),
                "response": sanitized,
                "redaction_counts": redactions,
            })
        prepared_sessions.append({
            "order": int(order_prefix),
            "session_id": session_id,
            "runtime_session_ids": sorted(session_id_tokens - {session_id}),
            "prompt_path": prompt_path,
            "prompt_sha256": sha(prompt_bytes),
            "family": family,
            "raw_response_path": raw_relative,
            "raw_response_sha256": raw_hash,
            "response_schema_valid": bool(valid),
            "responses": {item["case_id"]: item for item in scored},
        })

    if len(prepared_sessions) != 18:
        raise ValueError("not all 18 session results were mapped")

    # Excerpts are copied verbatim from the fixed scoring sources. Revision-only
    # requirements and the incompatible historical evaluator-sheet envelope are
    # not in scope for this transfer-only, case-level sheet.
    task225_text = TARGET_CRITERIA.read_text(encoding="utf-8")
    task225_relevant = (
        section(task225_text, "## Transfer case outcomes", "## Critical errors")
        + section(task225_text, "## Critical errors", "## Sheet format")
    )
    task227_text = TASK227_CRITERIA.read_text(encoding="utf-8")
    blind_schema = read_json(BLIND_SCHEMA_PATH)
    schemas_bytes = {
        "Task229 blind output schema": BLIND_SCHEMA_PATH.read_bytes(),
        "Task229 full successor response schema": RESPONSE_SCHEMA_PATH.read_bytes(),
    }

    seeds = {"A": secrets.randbits(256), "B": secrets.randbits(256)}
    keys = {"A": [], "B": []}
    packet_orders = {"A": [], "B": []}
    prompts = {}
    audits = {"schema_version": "task229-blind-sanitization-audit-v1", "sessions": [], "evaluators": {}}
    OUT.mkdir(parents=True, exist_ok=False)
    for evaluator in ("A", "B"):
        packets = []
        for session in prepared_sessions:
            for case_id in "ABC":
                response_id = secrets.token_hex(16)
                if response_id in response_ids_seen[evaluator]:
                    raise ValueError("opaque response ID collision")
                response_ids_seen[evaluator].add(response_id)
                keys[evaluator].append({
                    "response_id": response_id,
                    "session_id": session["session_id"],
                    "case_id": case_id,
                })
                family = session["family"]
                data = family_data[family]
                case_bytes = data["cases"][case_id]["bytes"]
                target_case = copy.deepcopy(data["targets"]["cases"][case_id])
                target_case = remove_sensitive_fields(target_case)
                target_redactions = {}
                target_case = redact_values(target_case, target_redactions)
                response_record = session["responses"][case_id]
                packet = {
                    "response_id": response_id,
                    "case_id": case_id,
                    "response_schema_valid": response_record["response_schema_valid"],
                    "case_facts": case_bytes.decode("utf-8", errors="strict"),
                    "frozen_target_case": target_case,
                    "sanitized_response": response_record["response"],
                }
                packet_text = json.dumps(packet, ensure_ascii=False, sort_keys=True)
                matches = []
                for pattern in deny_patterns:
                    n = len(pattern.findall(packet_text))
                    if n:
                        matches.append({"pattern": pattern.pattern, "count": n})
                if matches:
                    raise ValueError(f"blind leakage scan failed for {evaluator} packet {response_id}: {matches}")
                if re.search(r"(?:[A-Za-z]:\\[^\s\"'<>]+|(?<![A-Za-z0-9])/(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+)", packet_text) or re.search(
                    r"\b(?:ignition|reports|evaluations|families|sealed|cases|transfer|evaluator|tools|run)/[A-Za-z0-9_./-]+",
                    packet_text,
                ):
                    raise ValueError(f"repository/file path leakage in {evaluator} packet {response_id}")
                packets.append(packet)
                packet_orders[evaluator].append({"response_id": response_id, "case_id": case_id})

        rng = random.Random(seeds[evaluator])
        rng.shuffle(packets)
        output_schema_text = json.dumps(blind_schema, ensure_ascii=False, indent=2)
        prompt = (
            "You are an independent blind evaluator. Use only the frozen scoring text and the 54 packets below. "
            "Do not use tools, browse, inspect files, or consult external sources. Do not infer or name a condition, "
            "policy, lineage, session, bundle, or sibling relationship. Do not compare packets or reconcile scores. "
            "Score only the case named by each packet. The full original three-case response was mechanically checked "
            "against the frozen response schema; if response_schema_valid is false, mark success false. "
            "A valid packet contains one sanitized case object, with the complete route_trace removed. Use the exact "
            "case facts and corresponding frozen target. Apply the full operational action and required reported values, "
            "not only the action label. Preserve applicable baseline routes; use the frozen fallback for unresolved or "
            "out-of-scope facts; do not impute missing information. A critical error overrides a correct terminal label. "
            "Do not invent values or actions. Return exactly one JSON object, no markdown fences, with one row for every "
            "packet and no extra fields. Missing or invalid rows remain false.\n\n"
            "## Frozen Task225 transfer scoring criteria (verbatim relevant sections)\n\n"
            + task225_relevant
            + "\n## Frozen Task227 transfer scoring criteria (verbatim)\n\n"
            + task227_text.rstrip()
            + "\n\n## Required case-level output schema\n\n"
            + output_schema_text
            + "\n\n## Randomized blind packets\n\n"
            + json.dumps({"packets": packets}, ensure_ascii=False, indent=2)
            + "\n"
        )
        prompt_path = OUT / f"evaluator-{evaluator.lower()}-prompt.md"
        prompt_bytes = prompt.encode("utf-8", errors="strict")
        write_bytes(prompt_path, prompt_bytes)
        prompts[evaluator] = {
            "path": relative(prompt_path),
            "sha256": sha(prompt_bytes),
            "byte_length": len(prompt_bytes),
            "packet_count": len(packets),
            "response_ids_unique": len({packet["response_id"] for packet in packets}) == 54,
            "packet_order": [packet["response_id"] for packet in packets],
        }
        key_path = OUT / f"evaluator-{evaluator.lower()}-response-key.json"
        key_doc = {"schema_version": "task229-blind-key-r0", "items": keys[evaluator]}
        write_bytes(key_path, canonical(key_doc))
        audits["evaluators"][evaluator] = {
            "seed": str(seeds[evaluator]),
            "prompt_path": relative(prompt_path),
            "prompt_sha256": sha(prompt_bytes),
            "prompt_byte_length": len(prompt_bytes),
            "packet_count": len(packets),
            "packet_order_response_ids": [packet["response_id"] for packet in packets],
            "response_key_path": relative(key_path),
            "response_key_sha256": sha(key_path.read_bytes()),
            "leak_matches": 0,
        }

    if set(prompts["A"]["packet_order"]) == set(prompts["B"]["packet_order"]):
        raise ValueError("independent evaluators unexpectedly share response IDs")
    if prompts["A"]["packet_order"] == prompts["B"]["packet_order"]:
        raise ValueError("independent packet orders unexpectedly match")

    audit_session_ids = {item["session_id"] for item in prepared_sessions}
    for session in prepared_sessions:
        for case_id in "ABC":
            response = session["responses"][case_id]
            audits["sessions"].append({
                "raw_response_path": session["raw_response_path"],
                "raw_response_sha256": session["raw_response_sha256"],
                "response_schema_valid": response["response_schema_valid"],
                "case_id": case_id,
                "family_case_sha256": family_data[session["family"]]["cases"][case_id]["sha256"],
                "target_sha256": family_data[session["family"]]["target_sha256"],
                "response_field_redactions": response["redaction_counts"],
            })
    audits["session_count"] = len(audit_session_ids)
    audits["case_packet_count"] = len(audits["sessions"])
    audit_path = OUT / "sanitization-audit.json"
    write_bytes(audit_path, canonical(audits))

    ledger = {
        "schema_version": "task229-blind-coordinator-ledger-v1",
        "generated_at_utc": utc_now(),
        "condition_map_read_by_sanitizer": False,
        "session_count": len(prepared_sessions),
        "case_packet_count_per_evaluator": 54,
        "evaluator_response_keys": {
            evaluator: {
                "path": prompts[evaluator]["path"].replace("-prompt.md", "-response-key.json"),
                "sha256": audits["evaluators"][evaluator]["response_key_sha256"],
            }
            for evaluator in ("A", "B")
        },
        "sessions": [
            {
                "session_id": session["session_id"],
                "raw_response_path": session["raw_response_path"],
                "raw_response_sha256": session["raw_response_sha256"],
                "prompt_sha256": session["prompt_sha256"],
                "family_inferred_from_exact_case_bytes": session["family"],
            }
            for session in prepared_sessions
        ],
        "packet_orders": {
            evaluator: prompts[evaluator]["packet_order"]
            for evaluator in ("A", "B")
        },
    }
    ledger_path = OUT / "coordinator-ledger.json"
    write_bytes(ledger_path, canonical(ledger))

    manifest = {
        "schema_version": "task229-blind-packet-freeze-v1",
        "experiment_id": "IGNITION-20260930-229-R1",
        "frozen_at_utc": utc_now(),
        "condition_map_read_by_sanitizer": False,
        "historical_attempt1_responses_used": False,
        "post_exposure_tuning_permitted": False,
        "session_freeze_manifest_sha256": sha(SESSION_FREEZE_PATH.read_bytes()),
        "post_response_target_binding_sha256": sha(BINDING_PATH.read_bytes()),
        "builder_path": relative(pathlib.Path(__file__).resolve()),
        "builder_sha256": sha(pathlib.Path(__file__).read_bytes()),
        "prompt_assets": prompts,
        "sanitization_audit": {"path": relative(audit_path), "sha256": sha(audit_path.read_bytes())},
        "coordinator_ledger": {"path": relative(ledger_path), "sha256": sha(ledger_path.read_bytes())},
        "frozen_scoring_assets": {
            path: {"sha256": expected, "byte_length": len((ROOT / path).read_bytes())}
            for path, expected in EXPECTED_ASSET_HASHES.items()
        },
        "packet_schema_assets": {
            name: {"sha256": sha(data), "byte_length": len(data)}
            for name, data in schemas_bytes.items()
        },
        "independent_randomization_seeds": {key: str(value) for key, value in seeds.items()},
        "packet_count_per_evaluator": 54,
        "leak_scan_matches": 0,
        "evaluator_dispatches_started": False,
    }
    manifest_path = OUT / "packet-freeze-manifest.json"
    write_bytes(manifest_path, canonical(manifest))

    print("TASK229_BLIND_PACKETS=PASS")
    print(f"SESSIONS={len(prepared_sessions)} PACKETS_PER_EVALUATOR=54")
    print(f"PROMPT_A_BYTES={prompts['A']['byte_length']} SHA256={prompts['A']['sha256']}")
    print(f"PROMPT_B_BYTES={prompts['B']['byte_length']} SHA256={prompts['B']['sha256']}")
    print("BLIND_LEAK_SCAN_MATCHES=0 CONDITION_MAP_READ=false")
    print(f"FREEZE_MANIFEST_SHA256={sha(manifest_path.read_bytes())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
