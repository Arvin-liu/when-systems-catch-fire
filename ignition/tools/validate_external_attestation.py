"""External attestation JSON proof validator.

Validates the machine-readable F12 receipt that 1111 writes.
This schema/validator lives in the formal repo but must NOT contain live F12 values.
"""
import json
import sys
from pathlib import Path

REQUIRED_FIELDS = [
    "schema_version",
    "task_id",
    "repository",
    "pr_number",
    "base_head",
    "subject_head",
    "pr_state",
    "draft",
    "merged",
    "closure_hash",
    "map_counts",
    "changed_files",
    "foundation_run",
    "function_os_run",
    "pages_run",
    "artifact_id",
    "artifact_head_sha",
    "github_artifact_archive_digest",
    "github_artifact_archive_bytes",
    "pages_payload_tar_digest",
    "pages_payload_tar_bytes",
    "deploy_conclusion",
    "q29r_sha256",
    "lifecycle",
    "external_attestation_status",
    "generated_at",
    "evidence_sources",
    "claim_ceiling",
]


def validate_attestation_schema(doc: dict, source: str = "attestation") -> list[str]:
    """Validate an external attestation JSON document against the schema.

    Returns a list of error messages. Empty list means valid.
    """
    errors = []

    # Check all required fields exist
    for field in REQUIRED_FIELDS:
        if field not in doc:
            errors.append(f"{source}: missing required field: {field}")

    if errors:
        return errors  # Can't validate further without fields

    # Type checks
    if not isinstance(doc["schema_version"], str):
        errors.append(f"{source}: schema_version must be string")
    if not isinstance(doc["task_id"], str):
        errors.append(f"{source}: task_id must be string")
    if not isinstance(doc["pr_number"], int):
        errors.append(f"{source}: pr_number must be int")
    if not isinstance(doc["draft"], bool):
        errors.append(f"{source}: draft must be bool")
    if not isinstance(doc["merged"], bool):
        errors.append(f"{source}: merged must be bool")
    if not isinstance(doc["changed_files"], int):
        errors.append(f"{source}: changed_files must be int")
    if not isinstance(doc["github_artifact_archive_bytes"], int):
        errors.append(f"{source}: github_artifact_archive_bytes must be int")
    if not isinstance(doc["pages_payload_tar_bytes"], int):
        errors.append(f"{source}: pages_payload_tar_bytes must be int")

    # SHA format checks (40-char hex)
    for sha_field in ("subject_head", "base_head", "artifact_head_sha"):
        val = doc.get(sha_field, "")
        if not (isinstance(val, str) and len(val) == 40 and all(c in "0123456789abcdef" for c in val)):
            errors.append(f"{source}: {sha_field} must be 40-char lowercase hex SHA")

    # Digest format checks
    for digest_field in ("github_artifact_archive_digest", "pages_payload_tar_digest", "q29r_sha256"):
        val = doc.get(digest_field, "")
        if isinstance(val, str) and val.startswith("sha256:"):
            val = val[7:]
        if not (isinstance(val, str) and len(val) == 64 and all(c in "0123456789abcdef" for c in val)):
            errors.append(f"{source}: {digest_field} must be valid SHA-256 hex")

    # Dual digest must differ unconditionally (they represent different objects)
    ga = doc.get("github_artifact_archive_digest", "")
    pt = doc.get("pages_payload_tar_digest", "")
    if ga and pt:
        # Strip sha256: prefix if present
        ga_clean = ga.removeprefix("sha256:")
        pt_clean = pt.removeprefix("sha256:")
        if ga_clean == pt_clean:
            errors.append(f"{source}: dual digests must not be identical — ZIP and tar are separate objects")

    # Lifecycle consistency
    lc = doc.get("lifecycle", {})
    if isinstance(lc, dict):
        if lc.get("accepted") is True or lc.get("merged") is True or lc.get("current") is True:
            if doc.get("draft") is True:
                errors.append(f"{source}: draft PR must not have accepted/merged/current lifecycle")

    # PR state
    if doc.get("pr_state") not in ("OPEN", "CLOSED", "MERGED"):
        errors.append(f"{source}: pr_state must be OPEN, CLOSED, or MERGED")

    # Deploy conclusion
    if doc.get("deploy_conclusion") not in ("skipped", "success", "failure", "pending"):
        errors.append(f"{source}: deploy_conclusion must be skipped/success/failure/pending")

    # Subject HEAD must equal artifact head SHA
    if doc.get("subject_head") != doc.get("artifact_head_sha"):
        errors.append(f"{source}: subject_head must equal artifact_head_sha")

    # claim_ceiling
    if "candidate" not in doc.get("claim_ceiling", "").lower() and "only" not in doc.get("claim_ceiling", "").lower():
        errors.append(f"{source}: claim_ceiling should indicate candidate/only status")

    return errors


def validate_attestation_file(path: Path) -> dict:
    """Validate an attestation JSON file. Returns result dict."""
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, FileNotFoundError) as e:
        return {"status": "FAIL", "errors": [f"{path}: cannot read/parse: {e}"]}

    errors = validate_attestation_schema(doc, str(path))
    if errors:
        return {"status": "FAIL", "errors": errors}
    return {"status": "PASS", "errors": []}


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: validate_external_attestation.py <attestation.json>", file=sys.stderr)
        return 1
    path = Path(sys.argv[1])
    result = validate_attestation_file(path)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
