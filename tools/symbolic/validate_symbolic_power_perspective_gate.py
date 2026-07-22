#!/usr/bin/env python3
"""Fail-closed SYMBOLIC-SPHERE-I1 repair-r1 validator.

Repository references are resolved from local Git history. Task semantics are
recomputed from typed records; caller-supplied pass booleans are not accepted.
"""
import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
SCHEMA = ROOT / "schemas/symbolic/symbolic_power_perspective-contract.schema.json"
PARENT_TASK = "121Q39-REPAIR-R1"
PARENT_HEAD = "99ab601a48dd45972b238e468bc8e3002d648c98"

EXIT_NAMES = {
    0: "GATE_PASS",
    2: "MISSING_REQUIRED_RECORD",
    3: "PARENT_BINDING_INVALID",
    4: "UNRESOLVED_REPOSITORY_REFERENCE",
    5: "BLOB_MISMATCH",
    6: "DIGEST_MISMATCH",
    7: "UNSUPPORTED_REFERENCE_RECORD_TYPE",
    8: "DECLARED_ROLE_MISMATCH",
    9: "UNSUPPORTED_RECORD_TYPE",
    10: "INCONSISTENT_ACTOR_POSITION",
    11: "INCONSISTENT_MEANING_PROJECTION",
    12: "UNSUPPORTED_POWER_MODALITY",
    13: "INVALID_FACE_DISTINCTION",
    14: "INCOMPLETE_BENEFIT_COST_DISTRIBUTION",
    15: "INVALID_COUNTER_READING",
    16: "MISSING_MATERIAL_EVIDENCE",
    17: "TRUTH_UPGRADE_FORBIDDEN",
    18: "CAUSAL_OVERCLAIM",
    19: "EXTERNAL_ACTION_FORBIDDEN",
    20: "INVALID_SYMBOLIC_OBJECT",
}
HEAD_RE = re.compile(r"^[0-9a-f]{40}$")
DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
PLACEHOLDERS = {
    "", "null", "none", "todo", "tbd", "unknown", "placeholder",
    "pending", "n/a", "na", "not_checked", "not_checked_local_only",
}
REFERENCE_RECORD_TYPE = "SYMBOLIC_EVIDENCE_OBJECT"
RECORD_TYPES = {"COMMUNITY_FOOTBALL_FIELD", "SCHOOL_DATA_POLICY"}
POWER_MODALITIES = {
    "ACCESS_CONTROL",
    "RESOURCE_ALLOCATION",
    "INSTITUTIONAL_AUTHORITY",
    "NAMING_AUTHORITY",
    "OWNERSHIP",
    "POPULARITY",
}


def result(code, errors):
    return {
        "gate": "symbolic_power_perspective_gate",
        "exit_code": code,
        "exit_name": EXIT_NAMES[code],
        "errors": errors,
        "boundary": (
            "repository-local bounded symbolic analysis only; ownership, "
            "popularity, naming authority and symbolic interpretation do not "
            "establish truth, legitimacy or complete causality"
        ),
    }


def placeholder(value):
    if value is None or not isinstance(value, str):
        return True
    normalized = value.strip().lower()
    if normalized in PLACEHOLDERS:
        return True
    if HEAD_RE.fullmatch(normalized) and len(set(normalized)) == 1:
        return True
    if DIGEST_RE.fullmatch(normalized) and len(set(normalized[7:])) == 1:
        return True
    return False


def repository_relative_path(raw):
    if placeholder(raw) or "\\" in raw:
        return None
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        return None
    return path.as_posix() if path.as_posix() == raw else None


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)


def schema_errors(bundle):
    try:
        import jsonschema
        validator = jsonschema.Draft202012Validator(json.loads(SCHEMA.read_text()))
        errors = []
        for issue in sorted(
            validator.iter_errors(bundle),
            key=lambda item: tuple(str(part) for part in item.absolute_path),
        ):
            path = ".".join(str(part) for part in issue.absolute_path) or "<root>"
            errors.append(f"{path}: {issue.message}")
            if len(errors) == 25:
                break
        return errors
    except ImportError:
        required = (
            "contract_version", "task_id", "capability_id", "parent_binding",
            "reference_records", "records", "conclusion",
        )
        return [f"missing {key}" for key in required if key not in bundle]


def parse_tree_entry(commit, path):
    entry = git("ls-tree", "-z", commit, "--", path)
    matches = []
    for row in (part for part in entry.stdout.split(b"\0") if part):
        try:
            metadata, raw_path = row.split(b"\t", 1)
            mode, object_type, object_sha = metadata.decode("ascii").split()
            if raw_path.decode("utf-8") == path:
                matches.append((mode, object_type, object_sha))
        except (ValueError, UnicodeDecodeError):
            continue
    return matches


def resolve_reference_records(bundle):
    records = bundle["reference_records"]
    indexed = {item["reference_id"]: item for item in records}
    if len(indexed) != len(records):
        return 4, ["duplicate reference_id"], None, None

    for item in records:
        if item["record_type"] != REFERENCE_RECORD_TYPE:
            return 7, [f"{item['reference_id']}: unsupported reference record_type"], None, None

    resolved = {}
    documents = {}
    for item in records:
        reference_id = item["reference_id"]
        required = (
            "reference_id", "repository_relative_path", "commit_sha", "blob_sha",
            "sha256", "record_type", "declared_role", "object_id",
        )
        empty = [field for field in required if placeholder(item.get(field))]
        if empty:
            return 4, [f"{reference_id}: empty, all-zero, or placeholder fields {empty}"], None, None
        path = repository_relative_path(item["repository_relative_path"])
        commit = item["commit_sha"]
        if path is None or not HEAD_RE.fullmatch(commit) or not HEAD_RE.fullmatch(item["blob_sha"]):
            return 4, [f"{reference_id}: path or Git object identifier is invalid"], None, None
        if not DIGEST_RE.fullmatch(item["sha256"]):
            return 4, [f"{reference_id}: sha256 is malformed"], None, None
        commit_kind = git("cat-file", "-t", commit)
        if commit_kind.returncode or commit_kind.stdout.strip() != b"commit":
            return 4, [f"{reference_id}: commit cannot be resolved"], None, None
        matches = parse_tree_entry(commit, path)
        if len(matches) != 1 or matches[0][0] == "120000" or matches[0][1] != "blob":
            return 4, [f"{reference_id}: target path is absent, ambiguous, symlinked, or non-blob"], None, None
        actual_blob = matches[0][2]
        if item["blob_sha"] != actual_blob:
            return 5, [f"{reference_id}: declared blob does not match commit tree"], None, None
        content = git("cat-file", "blob", actual_blob)
        if content.returncode:
            return 4, [f"{reference_id}: repository blob cannot be read"], None, None
        actual_digest = "sha256:" + hashlib.sha256(content.stdout).hexdigest()
        if item["sha256"] != actual_digest:
            return 6, [f"{reference_id}: sha256 does not match actual repository bytes"], None, None
        document_key = (commit, path, actual_blob)
        if document_key not in documents:
            try:
                document = json.loads(content.stdout)
                objects = document["objects"]
                documents[document_key] = {
                    obj["object_id"]: obj for obj in objects
                    if isinstance(obj, dict) and obj.get("object_id")
                }
            except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError):
                return 4, [f"{reference_id}: referenced repository object registry is invalid"], None, None
        actual = documents[document_key].get(item["object_id"])
        if not actual:
            return 4, [f"{reference_id}: object_id is absent from referenced bytes"], None, None
        if item["declared_role"] != actual.get("object_type"):
            return 8, [f"{reference_id}: declared_role disagrees with actual object_type"], None, None
        resolved[reference_id] = actual
    return 0, [], indexed, resolved


def referenced_role(reference_id, role, scope, references, resolved):
    item = references.get(reference_id)
    actual = resolved.get(reference_id)
    return bool(
        item and actual
        and item.get("declared_role") == role
        and actual.get("object_type") == role
        and actual.get("record_scope") == scope
    )


def refs_have_role(reference_ids, role, scope, references, resolved):
    return bool(reference_ids) and all(
        referenced_role(reference_id, role, scope, references, resolved)
        for reference_id in reference_ids
    )


def check_record_coverage(bundle):
    record_types = [record["record_type"] for record in bundle["records"]]
    unsupported = sorted(set(record_types) - RECORD_TYPES)
    if unsupported:
        return 9, [f"unsupported symbolic record_type: {unsupported}"]
    if len(record_types) != len(set(record_types)) or set(record_types) != RECORD_TYPES:
        return 2, ["exactly one record of each required symbolic record_type is required"]
    return 0, []


def check_symbolic_objects(bundle, references, resolved):
    errors = []
    for record in bundle["records"]:
        if not referenced_role(
            record["symbolic_object_ref"], "MATERIAL_OBJECT", record["record_type"], references, resolved
        ):
            errors.append(f"{record['record_id']}: symbolic_object does not resolve to a material object")
    return errors


def check_actor_positions(bundle, references, resolved):
    errors = []
    for record in bundle["records"]:
        scope = record["record_type"]
        positions = record["actor_positions"]
        ids = [item["position_id"] for item in positions]
        if len(ids) != len(set(ids)):
            errors.append(f"{record['record_id']}: duplicate actor position")
        for position in positions:
            if not referenced_role(position["actor_ref"], "ACTOR", scope, references, resolved):
                errors.append(f"{position['position_id']}: actor_ref does not resolve to an explicit actor")
            if not refs_have_role(position["evidence_refs"], "MEANING_EVIDENCE", scope, references, resolved):
                errors.append(f"{position['position_id']}: actor position lacks meaning evidence")
    return errors


def check_meaning_projections(bundle, references, resolved):
    errors = []
    for record in bundle["records"]:
        scope = record["record_type"]
        position_ids = {item["position_id"] for item in record["actor_positions"]}
        projection_ids = [item["projection_id"] for item in record["meaning_projections"]]
        if len(projection_ids) != len(set(projection_ids)):
            errors.append(f"{record['record_id']}: duplicate meaning projection")
        covered_positions = set()
        for projection in record["meaning_projections"]:
            position_id = projection["actor_position_id"]
            if position_id not in position_ids:
                errors.append(f"{projection['projection_id']}: actor_position_id is unresolved")
            else:
                covered_positions.add(position_id)
            if projection["symbolic_object_ref"] != record["symbolic_object_ref"]:
                errors.append(f"{projection['projection_id']}: symbolic object does not match its record")
            if not refs_have_role(projection["evidence_refs"], "MEANING_EVIDENCE", scope, references, resolved):
                errors.append(f"{projection['projection_id']}: meaning evidence is invalid")
        if covered_positions != position_ids:
            errors.append(f"{record['record_id']}: every actor position needs a corresponding meaning projection")
    return errors


def check_power_modalities(bundle, references, resolved):
    errors = []
    for record in bundle["records"]:
        scope = record["record_type"]
        position_ids = {item["position_id"] for item in record["actor_positions"]}
        for power in record["power_modalities"]:
            if power["modality"] not in POWER_MODALITIES:
                errors.append(f"{record['record_id']}: unsupported power modality {power['modality']}")
            if power["actor_position_id"] not in position_ids:
                errors.append(f"{record['record_id']}: power modality has unresolved actor position")
            if not refs_have_role(power["evidence_refs"], "POWER_EVIDENCE", scope, references, resolved):
                errors.append(f"{record['record_id']}: power modality lacks typed evidence")
    return errors


def check_faces(bundle, references, resolved):
    errors = []
    for record in bundle["records"]:
        scope = record["record_type"]
        positions = {item["position_id"] for item in record["actor_positions"]}
        front = record["front_face"]
        suppressed = record["suppressed_face"]
        if (
            front["face_id"] == suppressed["face_id"]
            or front["statement"].strip().casefold() == suppressed["statement"].strip().casefold()
            or set(front["actor_position_ids"]) == set(suppressed["actor_position_ids"])
        ):
            errors.append(f"{record['record_id']}: front_face and suppressed_face impersonate each other")
        for label, face in (("front_face", front), ("suppressed_face", suppressed)):
            if not set(face["actor_position_ids"]).issubset(positions):
                errors.append(f"{record['record_id']}.{label}: unresolved actor position")
            if not refs_have_role(face["evidence_refs"], "FACE_EVIDENCE", scope, references, resolved):
                errors.append(f"{record['record_id']}.{label}: face evidence is invalid")
    return errors


def check_distribution(bundle, references, resolved):
    errors = []
    for record in bundle["records"]:
        scope = record["record_type"]
        positions = {item["position_id"] for item in record["actor_positions"]}
        distribution = record["benefit_cost_distribution"]
        parties = distribution["beneficiaries"] + distribution["cost_bearers"]
        if not distribution["beneficiaries"] or not distribution["cost_bearers"]:
            errors.append(f"{record['record_id']}: beneficiaries and cost bearers are both required")
        if not refs_have_role(distribution["evidence_refs"], "DISTRIBUTION_EVIDENCE", scope, references, resolved):
            errors.append(f"{record['record_id']}: distribution lacks its evidence source")
        for party in parties:
            if party["actor_position_id"] not in positions:
                errors.append(f"{record['record_id']}: distribution party is unresolved")
            if not refs_have_role(party["evidence_refs"], "DISTRIBUTION_EVIDENCE", scope, references, resolved):
                errors.append(f"{record['record_id']}: distribution party lacks evidence")
    return errors


def check_counter_readings(bundle, references, resolved):
    errors = []
    for record in bundle["records"]:
        scope = record["record_type"]
        projections = {item["projection_id"]: item for item in record["meaning_projections"]}
        ids = [item["counter_reading_id"] for item in record["counter_readings"]]
        if len(ids) != len(set(ids)):
            errors.append(f"{record['record_id']}: duplicate counter reading")
        for counter in record["counter_readings"]:
            target = projections.get(counter["target_projection_id"])
            if not target:
                errors.append(f"{counter['counter_reading_id']}: target projection is unresolved")
                continue
            if not refs_have_role(counter["evidence_refs"], "COUNTER_READING_EVIDENCE", scope, references, resolved):
                errors.append(f"{counter['counter_reading_id']}: counter reading lacks its own typed evidence")
            if set(counter["evidence_refs"]) & set(target["evidence_refs"]):
                errors.append(f"{counter['counter_reading_id']}: counter reading reuses target assertion evidence as its sole declaration")
    return errors


def check_material_evidence(bundle, references, resolved):
    errors = []
    conclusion = bundle["conclusion"]
    for record in bundle["records"]:
        scope = record["record_type"]
        constraint = record["material_evidence_constraint"]
        satisfied = (
            constraint["status"] == "SATISFIED"
            and not constraint["unmet_requirements"]
            and refs_have_role(
                constraint["material_evidence_refs"], "MATERIAL_EVIDENCE", scope, references, resolved
            )
        )
        if not satisfied:
            errors.append(f"{record['record_id']}: material evidence constraint is not satisfied")
    if errors and not (
        conclusion["analysis_status"] == "DOWNGRADED"
        and conclusion["claim_ceiling"] == "INSUFFICIENT_MATERIAL_EVIDENCE"
    ):
        errors.append("unsatisfied material evidence did not downgrade the conclusion")
    return errors


def check_truth_ceiling(bundle):
    conclusion = bundle["conclusion"]
    text = f"{conclusion['statement']} {conclusion['claim_ceiling']}".casefold()
    forbidden = (
        "truth established", "proves truth", "ownership therefore true",
        "popularity therefore true", "naming authority therefore true",
    )
    if (
        conclusion["analysis_status"] != "BOUNDED_INTERPRETATION"
        or conclusion["claim_ceiling"] != "BOUNDED_SYMBOLIC_INTERPRETATION"
        or conclusion["truth_status"] != "NOT_ESTABLISHED"
        or any(token in text for token in forbidden)
    ):
        return ["ownership, popularity, naming authority, or symbolic interpretation was upgraded to truth"]
    return []


def check_causal_ceiling(bundle):
    conclusion = bundle["conclusion"]
    text = f"{conclusion['statement']} {conclusion['claim_ceiling']}".casefold()
    forbidden = ("causal proof", "causality established", "complete causal", "proves the cause")
    if conclusion["causal_status"] != "NOT_ESTABLISHED" or any(token in text for token in forbidden):
        return ["symbolic analysis was upgraded to complete causal proof"]
    return []


def validate(bundle):
    errors = schema_errors(bundle)
    if errors:
        return 2, errors
    parent = bundle["parent_binding"]
    if parent["task_id"] != PARENT_TASK or parent["exact_head"] != PARENT_HEAD:
        return 3, ["parent binding must name the exact local Q39 repair-r1 frozen head"]
    code, errors, references, resolved = resolve_reference_records(bundle)
    if code:
        return code, errors
    code, errors = check_record_coverage(bundle)
    if code:
        return code, errors
    checks = (
        (20, check_symbolic_objects(bundle, references, resolved)),
        (10, check_actor_positions(bundle, references, resolved)),
        (11, check_meaning_projections(bundle, references, resolved)),
        (12, check_power_modalities(bundle, references, resolved)),
        (13, check_faces(bundle, references, resolved)),
        (14, check_distribution(bundle, references, resolved)),
        (15, check_counter_readings(bundle, references, resolved)),
        (16, check_material_evidence(bundle, references, resolved)),
        (17, check_truth_ceiling(bundle)),
        (18, check_causal_ceiling(bundle)),
    )
    for check_code, check_errors in checks:
        if check_errors:
            return check_code, check_errors
    if bundle["conclusion"]["external_action_performed"]:
        return 19, ["repository-local symbolic analysis cannot perform external action"]
    return 0, []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", required=True)
    args = parser.parse_args()
    try:
        bundle = json.loads(Path(args.bundle).read_text())
    except Exception as exc:
        code, errors = 2, [str(exc)]
    else:
        code, errors = validate(bundle)
    print(json.dumps(result(code, errors), ensure_ascii=False, sort_keys=True))
    return code


if __name__ == "__main__":
    sys.exit(main())
