#!/usr/bin/env python3
"""Record the provenance-preserving withdrawal of platform-only rows.

Step 01 changes future discovery inputs.  This migration is intentionally
append-only: it records the pre-policy row hash, source hashes, and Git
provenance for every function/nonfunction row whose sources were platform-only.
The row is removed from the current Knowledge projection by the generators,
not deleted from history or silently relabeled as a domain claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path

from knowledge_corpus_admission import admission_for_path, is_platform_excluded, policy_summary


ROOT = Path(__file__).resolve().parents[2]
MIGRATION_DIR = ROOT / "data/foundation/migrations"
REPORT = MIGRATION_DIR / "knowledge-corpus-admission-migration.jsonl"
SUMMARY = MIGRATION_DIR / "knowledge-corpus-admission-summary.json"

STEP00_BASELINE_COUNTS = {
    "function_census_records": 7588,
    "nonfunction_claim_records": 18476,
    "knowledge_experience_search_records": 26372,
    "fire_seed_candidate_entries": 64,
    "fire_seed_source_records": 369,
    "function_tracked_text_files_scanned": 3484,
    "nonfunction_tracked_files_accounted": 3802,
}
STEP00_BASELINE_COMMIT = "8cc9291c0af9d3df686628bfd7dbae365523e327"


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def row_hash(row: dict) -> str:
    return hashlib.sha256(canonical(row).encode("utf-8")).hexdigest()


def git_root() -> Path:
    return Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], cwd=ROOT, text=True).strip())


def git_tip() -> str:
    return STEP00_BASELINE_COMMIT


def git_path(path: str) -> str:
    return path if path.startswith(".github/") else f"ignition/{path}"


def source_hash(path: str, repository: Path, baseline_commit: str) -> str | None:
    result = subprocess.run(
        ["git", "show", f"{baseline_commit}:{git_path(path)}"],
        cwd=repository,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return hashlib.sha256(result.stdout).hexdigest()


def last_commit(path: str, repository: Path, baseline_commit: str) -> str | None:
    result = subprocess.run(
        ["git", "log", "-1", "--format=%H", baseline_commit, "--", git_path(path)],
        cwd=repository,
        text=True,
        capture_output=True,
        check=False,
    )
    value = result.stdout.strip()
    return value or None


def baseline_rows(path: Path, repository: Path, baseline_commit: str) -> list[dict]:
    relative = path.relative_to(ROOT).as_posix()
    raw = subprocess.check_output(["git", "show", f"{baseline_commit}:ignition/{relative}"], cwd=repository)
    return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]


def paths_for(kind: str, row: dict) -> list[str]:
    if kind == "FUNCTION_ASSET_CANDIDATE":
        evidence = row.get("source_evidence", {})
        return sorted(set(evidence.get("occurrence_paths", [])))
    values = []
    values.extend(item.get("path", "") for item in row.get("source_anchors", []))
    values.extend(item.get("path", "") for item in row.get("evidence_references", []) if item.get("kind") == "SOURCE_TEXT")
    return sorted(set(value for value in values if value))


def current_projection_counts() -> dict[str, int]:
    function_summary = json.loads((ROOT / "data/foundation/function-assets/census-summary.json").read_text(encoding="utf-8"))
    nonfunction_summary = json.loads((ROOT / "data/foundation/nonfunction-claims/closure-summary.json").read_text(encoding="utf-8"))
    fire_seeds = json.loads((ROOT / "data/publication/fire-seeds/seed-census.json").read_text(encoding="utf-8"))
    return {
        "function_census_records": sum(1 for line in (ROOT / "data/foundation/function-assets/census.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()),
        "nonfunction_claim_records": sum(1 for line in (ROOT / "data/foundation/nonfunction-claims/claim-registry.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()),
        "knowledge_experience_search_records": sum(1 for line in (ROOT / "data/governance/knowledge-experience/search-index.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()),
        "fire_seed_candidate_entries": int(fire_seeds["candidate_count"]),
        "fire_seed_source_records": int(fire_seeds["source_census_summary"]["source_count"]),
        "function_tracked_text_files_scanned": int(function_summary["tracked_text_files_scanned"]),
        "nonfunction_tracked_files_accounted": int(nonfunction_summary["tracked_files_accounted"]),
    }


def candidate_rows(repository: Path, baseline_commit: str) -> list[dict]:
    output: list[dict] = []
    source_hash_cache: dict[str, str | None] = {}
    commit_cache: dict[str, str | None] = {}
    inputs = (
        ("FUNCTION_ASSET_CANDIDATE", ROOT / "data/foundation/function-assets/census.jsonl"),
        ("NONFUNCTION_CLAIM_CANDIDATE", ROOT / "data/foundation/nonfunction-claims/claim-registry.jsonl"),
    )
    for kind, path in inputs:
        for row in baseline_rows(path, repository, baseline_commit):
            paths = paths_for(kind, row)
            platform_paths = [path for path in paths if is_platform_excluded(path)]
            if not platform_paths or not all(is_platform_excluded(path) for path in paths):
                continue
            identifier = row.get("stable_id") or row.get("canonical_id")
            for source in paths:
                if source not in source_hash_cache:
                    source_hash_cache[source] = source_hash(source, repository, baseline_commit)
                if source not in commit_cache:
                    commit_cache[source] = last_commit(source, repository, baseline_commit)
            item = {
                "migration_id": f"KCAP-121-{kind[:3]}-{identifier}",
                "task_id": "IGNITION-20260816-121",
                "record_kind": kind,
                "canonical_id": identifier,
                "baseline_commit": baseline_commit,
                "original_record_sha256": row_hash(row),
                "source_paths": paths,
                "source_hashes": {source: source_hash_cache[source] for source in paths},
                "git_provenance": {source: commit_cache[source] for source in paths},
                "admission_class": "PLATFORM_CODE_EXCLUDED",
                "migration_disposition": "PLATFORM_PROVENANCE_ONLY",
                "current_knowledge_status": "WITHDRAWN_FROM_CURRENT_KNOWLEDGE_SURFACE",
                "claim_ceiling_changed": False,
                "reason": "Platform code, tooling, schema, test, CI, or runtime-trace text is not an implicit Knowledge Pack source.",
            }
            output.append(item)
    return sorted(output, key=lambda item: (item["record_kind"], item["canonical_id"]))


def build_report() -> tuple[list[dict], dict]:
    repository = git_root()
    baseline = git_tip()
    rows = candidate_rows(repository, baseline)
    after_counts = current_projection_counts()
    summary = {
        "task_id": "IGNITION-20260816-121",
        "policy": policy_summary(),
        "baseline_commit": baseline,
        "migration_status": "PROVENANCE_PRESERVED",
        "row_count": len(rows),
        "function_rows": sum(row["record_kind"] == "FUNCTION_ASSET_CANDIDATE" for row in rows),
        "nonfunction_rows": sum(row["record_kind"] == "NONFUNCTION_CLAIM_CANDIDATE" for row in rows),
        "source_hashes_present": sum(all(value is not None for value in row["source_hashes"].values()) for row in rows),
        "claim_ceiling_changes": 0,
        "deletion": "none; current projection withdrawal only",
        "source_of_truth": "This append-only migration report plus the original baseline commit.",
        "before_counts": STEP00_BASELINE_COUNTS,
        "after_counts": after_counts,
        "projection_delta": {
            key: after_counts[key] - STEP00_BASELINE_COUNTS[key]
            for key in STEP00_BASELINE_COUNTS
        },
        "platform_only_withdrawals": {
            "function_rows": sum(row["record_kind"] == "FUNCTION_ASSET_CANDIDATE" for row in rows),
            "nonfunction_rows": sum(row["record_kind"] == "NONFUNCTION_CLAIM_CANDIDATE" for row in rows),
        },
    }
    return rows, summary


def validate() -> dict:
    if not REPORT.is_file() or not SUMMARY.is_file():
        raise SystemExit("knowledge corpus admission migration artifacts are missing")
    rows = [json.loads(line) for line in REPORT.read_text(encoding="utf-8").splitlines() if line.strip()]
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    required = {"migration_id", "task_id", "record_kind", "canonical_id", "baseline_commit", "original_record_sha256", "source_paths", "source_hashes", "git_provenance", "admission_class", "migration_disposition", "current_knowledge_status", "claim_ceiling_changed", "reason"}
    if any(set(row) != required for row in rows):
        raise SystemExit("migration row schema drift")
    if len(rows) != summary["row_count"]:
        raise SystemExit("migration summary count drift")
    if summary["claim_ceiling_changes"] != 0:
        raise SystemExit("migration must not change claim ceilings")
    if any(row["admission_class"] != "PLATFORM_CODE_EXCLUDED" or row["migration_disposition"] != "PLATFORM_PROVENANCE_ONLY" for row in rows):
        raise SystemExit("platform migration disposition drift")
    if any(row["claim_ceiling_changed"] is not False for row in rows):
        raise SystemExit("claim ceiling migration drift")
    return {"status": "PASS", "row_count": len(rows), "baseline_commit": summary["baseline_commit"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.write:
        rows, summary = build_report()
        MIGRATION_DIR.mkdir(parents=True, exist_ok=True)
        REPORT.write_text("".join(canonical(row) + "\n" for row in rows), encoding="utf-8")
        SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if args.check or args.write:
        print(canonical(validate()))
        return 0
    parser.error("choose --write or --check")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
